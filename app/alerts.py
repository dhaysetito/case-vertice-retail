"""Motor de alertas determinístico, conforme docs/06-regras-decisao.md.

Seis famílias: A01 gap material de margem, A02 deterioração temporal, A03
perdas em pedidos, A04 demanda repetitiva em atendimento, A05 guardrail após
ação e Q01 qualidade e cobertura.

**Regra sem parâmetro não recebe valor silencioso.** `docs/06` é explícito: um
parâmetro obrigatório ausente desabilita a regra, com explicação na tela. Por
isso `evaluate()` devolve sempre o catálogo inteiro em ``rules``, com o estado
de cada família — ativa, sem caso material ou desabilitada e por quê. Uma
família que não aparece na lista de alertas não é uma família que passou: pode
ser uma que não pôde ser avaliada, e a diferença importa para quem decide.

Os parâmetros abaixo vieram de decisão do usuário em 2026-09-20, calibrados
sobre a distribuição real de 2023. **Não são política aprovada da empresa.**
"""
from __future__ import annotations

import json
import statistics
from decimal import Decimal
from typing import Any

from .analytics import MONTHS, Analytics, Query

# Impacto diagnóstico mínimo para publicar. Separa o achado real do ruído:
# com R$ 50 mil, só o Marketplace (R$ 95.334) é publicado; Lifestyle (R$ 7.483)
# e Beleza (R$ 1.321) ficam de fora, e os gaps deles são de 0,23 e 0,03 p.p.
MATERIALITY_BRL = 50_000.0

# Queda de margem percentual que caracteriza deterioração. O limiar anterior de
# 1 p.p. nunca disparava: a maior queda mensal de 2023 é de 0,89 p.p. e a
# mediana é de 0,18 p.p.
MARGIN_DROP_PP = -0.5

# Queda relativa de receita. Mantida do desenho anterior; a materialidade e a
# persistência é que filtram a reversão dos picos sintéticos de março, maio e
# novembro.
REVENUE_DROP_PCT = -5.0

# Participação mínima de um motivo de atendimento para virar candidato.
SUPPORT_SHARE_PCT = 25.0

# Piso técnico de amostra, para não publicar célula pequena com variação
# extrema. Não é decisão de negócio: é proteção contra ruído de denominador.
MIN_ORDERS = 100

# Base atípica: comparar contra um mês fora do padrão produz queda que é só
# reversão. Em 2023, março, maio e novembro concentram ~2x a receita dos demais;
# sem esta guarda, junho publicava "Crítica" por cair 56% contra maio.
ATYPICAL_BASE_FACTOR = 1.5

# Persistência: k de n períodos elegíveis. Por decisão do usuário a condição
# não bloqueia a publicação — ela distingue queda pontual de repetida e eleva a
# severidade, que é o que `docs/06` pede ("diferenciar queda pontual e repetida").
PERSISTENCE_WINDOW = 3
PERSISTENCE_MIN = 2

PARAMETERS = {
    "materialidade_brl": MATERIALITY_BRL,
    "queda_margem_pp": MARGIN_DROP_PP,
    "queda_receita_pct": REVENUE_DROP_PCT,
    "participacao_motivo_pct": SUPPORT_SHARE_PCT,
    "amostra_minima_pedidos": MIN_ORDERS,
    "persistencia": f"{PERSISTENCE_MIN} de {PERSISTENCE_WINDOW}",
    "base_atipica_fator": ATYPICAL_BASE_FACTOR,
    "origem": "decisão do usuário em 2026-09-20, calibrada sobre 2023; não é política aprovada da empresa",
}

CATALOG = [
    ("A01", "Gap material de margem", "Um corte comercial rende menos que o consolidado comparável, e a diferença é material."),
    ("A02", "Deterioração temporal", "Um KPI piorou contra o período anterior comparável, acima da tolerância."),
    ("A03", "Perdas em pedidos", "A soma das perdas em pedidos com margem negativa supera a materialidade."),
    ("A04", "Demanda repetitiva", "Um motivo de atendimento concentra volume e custo acima da referência."),
    ("A05", "Guardrail após ação", "Um KPI de proteção piorou além da tolerância definida no plano de uma ação."),
    ("Q01", "Qualidade e cobertura", "Truncamento, sentinela ou join incoerente que limita a leitura de alguma métrica."),
]

SEVERITIES = ["Crítica", "Alta", "Moderada", "Informativa"]


def _num(value: float, casas: int = 2) -> str:
    """Decimal com vírgula; o texto vai direto para a tela."""
    return f"{value:.{casas}f}".replace(".", ",")


def _brl(value: float) -> str:
    """R$ no formato brasileiro. O texto vai para a tela, lido por uma pessoa."""
    return "R$ " + f"{value:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _severity(impact: float, repeated: bool) -> str:
    """Materialidade e persistência, como pede docs/06 — nunca a magnitude sozinha."""
    grande = impact >= 2 * MATERIALITY_BRL
    if grande and repeated:
        return "Crítica"
    if grande or repeated:
        return "Alta"
    return "Moderada"


def _alert(rule: str, title: str, entity: str, severity: str, impact: float | None,
           evidence: list[dict[str, Any]], explanation: str, limitations: list[str],
           persistence: dict[str, Any] | None = None, navigate: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"rule": rule, "version": "v1", "title": title, "entity": entity, "severity": severity,
            "impact": impact, "evidence": evidence, "explanation": explanation,
            "limitations": limitations, "persistence": persistence, "navigate": navigate or {}}


class Alerts:
    def __init__(self, analytics: Analytics | None = None, fronts=None):
        self.analytics = analytics or Analytics()
        self.fronts = fronts
        self._cache: dict[Query, dict[str, Any]] = {}

    def _agg(self, query: Query) -> dict[str, Any]:
        """Agregado memoizado por avaliação.

        Persistência e mediana pedem o mesmo mês várias vezes; sem cache eram
        mais de 40 varreduras completas por requisição. ``Query`` é um dataclass
        congelado, então serve de chave.
        """
        if query not in self._cache:
            self._cache[query] = self.analytics._aggregate(self.analytics._rows(query))
        return self._cache[query]

    # ------------------------------------------------------------------ A01

    def _a01(self, query: Query) -> tuple[list[dict[str, Any]], str]:
        achados = []
        # Materialidade absoluta é mais severa em janela curta: o mesmo gap vale
        # R$ 95 mil no ano e R$ 11 mil num mês. Quando a regra reprova só por
        # isso, dizer qual foi o maior candidato evita a leitura de "não há gap".
        quase: tuple[float, str] | None = None
        for dimension, items, key, label in [
            ("canal", self.analytics.channels(query)["items"], "channel", "Canal"),
            ("categoria", self.analytics.categories(query)["items"], "category", "Categoria"),
        ]:
            comparison = Query(query.year, query.month,
                               None if dimension == "canal" else query.channel,
                               None if dimension == "categoria" else query.category,
                               query.grain, query.start, query.end)
            benchmark = self._agg(comparison)["margin_pct"]
            if benchmark is None:
                continue
            for item in items:
                if item["margin_pct"] is None or item["orders"] < MIN_ORDERS:
                    continue
                gap = benchmark - item["margin_pct"]
                impact = max(0.0, gap) / 100 * item["revenue"]
                if gap <= 0:
                    continue
                if impact < MATERIALITY_BRL:
                    if quase is None or impact > quase[0]:
                        quase = (impact, f"{item[key]} ({_num(gap)} p.p., {_brl(impact)})")
                    continue
                repeated, detail = self._a01_persistence(query, dimension, item[key])
                achados.append(_alert(
                    "A01", f"{item[key]} rende {_num(gap)} p.p. abaixo do consolidado", item[key],
                    _severity(impact, repeated), impact,
                    [{"rotulo": f"Margem de {item[key]}", "valor": item["margin_pct"], "unidade": "pct"},
                     {"rotulo": "Consolidado comparável", "valor": benchmark, "unidade": "pct"},
                     {"rotulo": "Gap", "valor": gap, "unidade": "pp"},
                     {"rotulo": "Receita do corte", "valor": item["revenue"], "unidade": "money"},
                     {"rotulo": "Pedidos", "valor": item["orders"], "unidade": "int"},
                     {"rotulo": "Impacto diagnóstico", "valor": impact, "unidade": "money"}],
                    f"A comparação remove {item[key]} do benchmark, para não comparar o corte consigo mesmo. "
                    f"O impacto diagnóstico é o gap aplicado sobre a receita do próprio corte.",
                    ["O impacto diagnóstico dimensiona a diferença observada; não é economia recuperável.",
                     "A margem aqui é receita líquida menos custo de produto e frete, sem comissões e impostos.",
                     "Diferença entre cortes não demonstra que o corte causa a diferença."],
                    detail,
                    {"section": "tendencias", "metric": "rate", **({"channel": item[key]} if dimension == "canal" else {"category": item[key]})}))
        if achados or quase is None:
            return achados, "ativa"
        return [], (f"maior candidato abaixo da materialidade de {_brl(MATERIALITY_BRL)}: {quase[1]}")

    def _a01_persistence(self, query: Query, dimension: str, entity: str) -> tuple[bool, dict[str, Any]]:
        """Em quantos dos últimos meses elegíveis o gap se repetiu."""
        anchor = self.analytics.calendar_month(query)
        if anchor is None:
            return False, {"estado": "não avaliada", "motivo": "o recorte anual não tem períodos anteriores para comparar"}
        meses = [m for m in range(anchor - PERSISTENCE_WINDOW + 1, anchor + 1) if m >= 1]
        ocorrencias = 0
        for month in meses:
            escopo = Query(query.year, month, query.channel, query.category, query.grain)
            alvo = Query(query.year, month,
                         entity if dimension == "canal" else query.channel,
                         entity if dimension == "categoria" else query.category, query.grain)
            comparacao = Query(query.year, month,
                               None if dimension == "canal" else query.channel,
                               None if dimension == "categoria" else query.category, query.grain)
            valor = self._agg(alvo)
            base = self._agg(comparacao)["margin_pct"]
            if valor["margin_pct"] is None or base is None or valor["orders"] < MIN_ORDERS:
                continue
            gap = base - valor["margin_pct"]
            if gap > 0 and max(0.0, gap) / 100 * valor["revenue"] >= MATERIALITY_BRL:
                ocorrencias += 1
        repetida = ocorrencias >= PERSISTENCE_MIN
        return repetida, {"estado": "repetida" if repetida else "pontual",
                          "ocorrencias": ocorrencias, "janela": len(meses),
                          "motivo": f"condição material em {ocorrencias} de {len(meses)} meses elegíveis"}

    # ------------------------------------------------------------------ A02

    def _a02(self, query: Query) -> tuple[list[dict[str, Any]], str]:
        pair = self.analytics._previous_query(query)
        if not pair:
            return [], "sem período anterior comparável neste recorte"
        previous_query, previous_label = pair
        atual = self._agg(query)
        anterior = self._agg(previous_query)
        if atual["orders"] < MIN_ORDERS or anterior["orders"] < MIN_ORDERS:
            return [], f"amostra abaixo do piso de {MIN_ORDERS} pedidos em um dos períodos"

        # Mediana dos doze meses do mesmo recorte, para reconhecer base atípica.
        mensais = {}
        for chave in ("revenue", "margin"):
            valores = [self._agg(
                Query(query.year, m, query.channel, query.category, query.grain))[chave] for m in range(1, 13)]
            validos = [v for v in valores if v]
            mensais[chave] = statistics.median(validos) if validos else None

        achados = []
        regras = [("margin_pct", "Margem percentual", "pp", MARGIN_DROP_PP),
                  ("revenue", "Receita líquida", "pct", REVENUE_DROP_PCT),
                  ("margin", "Margem absoluta", "pct", REVENUE_DROP_PCT)]
        for key, label, unidade, limite in regras:
            if atual[key] is None or anterior[key] is None or not anterior[key]:
                continue
            delta = atual[key] - anterior[key] if unidade == "pp" else (atual[key] - anterior[key]) / abs(anterior[key]) * 100
            if delta > limite:
                continue
            # Impacto: quanto de margem deixou de existir contra o período anterior.
            impact = abs(atual["margin"] - anterior["margin"]) if key != "margin_pct" else \
                abs(atual["margin_pct"] - anterior["margin_pct"]) / 100 * atual["revenue"]
            tipico = mensais.get(key)
            atipica = bool(tipico and anterior[key] > ATYPICAL_BASE_FACTOR * tipico)
            repetida, detalhe = self._a02_persistence(query, key, limite, unidade)
            severidade = "Moderada" if atipica else _severity(impact, repetida)
            limites = ["Queda observada não demonstra causa.",
                       "Períodos comparáveis não corrigem sazonalidade: 2023 tem um único ciclo anual.",
                       "A margem não inclui comissões, impostos e demais custos econômicos."]
            explicacao = f"Regra: queda de ao menos {_num(abs(limite), 1)} {'p.p.' if unidade == 'pp' else '%'} contra o período anterior comparável."
            if atipica:
                explicacao += (f" A base de comparação é atípica: {previous_label} ficou "
                               f"{_num(anterior[key] / tipico, 1)}× acima da mediana mensal do recorte, "
                               f"então parte da queda é reversão, não deterioração.")
                limites.insert(0, "Severidade limitada a Moderada porque a base de comparação é atípica.")
            achados.append(_alert(
                "A02", f"{label} caiu {_num(abs(delta))} {'p.p.' if unidade == 'pp' else '%'} contra {previous_label}",
                label, severidade, impact,
                [{"rotulo": "Valor atual", "valor": atual[key], "unidade": "pct" if key == "margin_pct" else "money"},
                 {"rotulo": f"Em {previous_label}", "valor": anterior[key], "unidade": "pct" if key == "margin_pct" else "money"},
                 {"rotulo": "Variação", "valor": delta, "unidade": unidade},
                 {"rotulo": "Pedidos no recorte", "valor": atual["orders"], "unidade": "int"},
                 {"rotulo": "Impacto diagnóstico", "valor": impact, "unidade": "money"}],
                explicacao, limites,
                detalhe, {"section": "tendencias", "metric": "rate" if key == "margin_pct" else "revenue"}))
        return achados, "ativa"

    def _a02_persistence(self, query: Query, key: str, limite: float, unidade: str) -> tuple[bool, dict[str, Any]]:
        anchor = self.analytics.calendar_month(query)
        if anchor is None:
            return False, {"estado": "não avaliada", "motivo": "persistência exige recorte mensal"}
        meses = [m for m in range(anchor - PERSISTENCE_WINDOW + 1, anchor + 1) if m >= 2]
        ocorrencias = 0
        for month in meses:
            atual = self._agg(Query(query.year, month, query.channel, query.category, query.grain))
            anterior = self._agg(Query(query.year, month - 1, query.channel, query.category, query.grain))
            if atual[key] is None or anterior[key] is None or not anterior[key]:
                continue
            delta = atual[key] - anterior[key] if unidade == "pp" else (atual[key] - anterior[key]) / abs(anterior[key]) * 100
            if delta <= limite:
                ocorrencias += 1
        repetida = ocorrencias >= PERSISTENCE_MIN
        return repetida, {"estado": "repetida" if repetida else "pontual",
                          "ocorrencias": ocorrencias, "janela": len(meses),
                          "motivo": f"condição em {ocorrencias} de {len(meses)} meses elegíveis"}

    # ------------------------------------------------------------------ A03

    def _a03(self, query: Query) -> tuple[list[dict[str, Any]], str]:
        rows = self.analytics._rows(query)
        negativos = [r for r in rows if Decimal(r["margem_contribuicao"]) < 0]
        perda = float(sum(-Decimal(r["margem_contribuicao"]) for r in negativos))
        if not negativos:
            return [], "nenhum pedido com margem negativa no recorte"
        if perda < MATERIALITY_BRL:
            return [], (f"{len(negativos)} pedidos com margem negativa somam {_brl(perda)}, "
                        f"abaixo da materialidade de {_brl(MATERIALITY_BRL)}")
        pedidos = len({r["order_id"] for r in negativos})
        return [_alert(
            "A03", f"Perdas observadas em {pedidos} pedidos somam {_brl(perda)}",
            "Pedidos com margem negativa", _severity(perda, False), perda,
            [{"rotulo": "Pedidos afetados", "valor": pedidos, "unidade": "int"},
             {"rotulo": "Perda observada", "valor": perda, "unidade": "money"},
             {"rotulo": "Participação nos pedidos", "valor": pedidos / max(1, len({r["order_id"] for r in rows})) * 100, "unidade": "pct"}],
            "Soma do valor absoluto das margens negativas dos pedidos do recorte.",
            ["Perda observada não é custo evitável: pode refletir frete, desconto ou preço de um pedido específico.",
             "A margem não inclui comissões e impostos."],
            {"estado": "não avaliada", "motivo": "a regra olha o acumulado do recorte, não a repetição"},
            {"section": "tendencias", "metric": "margin"})], "ativa"

    # ------------------------------------------------------------------ A04

    def _a04(self, query: Query) -> tuple[list[dict[str, Any]], str]:
        if self.fronts is None:
            return [], "camada de atendimento indisponível"
        tickets = self.fronts._tickets(query)
        if not tickets:
            return [], "nenhum ticket aberto no recorte"
        temas: dict[str, dict[str, float]] = {}
        for row in tickets:
            bucket = temas.setdefault(row["categoria_problema"], {"tickets": 0, "custo": 0.0})
            bucket["tickets"] += 1
            bucket["custo"] += float(row["custo_operacional_ticket"])
        achados = []
        for tema, bucket in sorted(temas.items(), key=lambda item: -item[1]["custo"]):
            share = bucket["tickets"] / len(tickets) * 100
            if share < SUPPORT_SHARE_PCT or bucket["custo"] < MATERIALITY_BRL:
                continue
            achados.append(_alert(
                "A04", f"“{tema}” concentra {_num(share, 1)}% dos tickets", tema,
                _severity(bucket["custo"], False), bucket["custo"],
                [{"rotulo": "Tickets", "valor": bucket["tickets"], "unidade": "int"},
                 {"rotulo": "Participação", "valor": share, "unidade": "pct"},
                 {"rotulo": "Custo registrado", "valor": bucket["custo"], "unidade": "money"},
                 {"rotulo": "Custo por ticket", "valor": bucket["custo"] / bucket["tickets"], "unidade": "money"}],
                f"Regra: participação de ao menos {SUPPORT_SHARE_PCT:.0f}% dos tickets e custo registrado acima da materialidade.",
                ["O custo registrado assume apenas R$ 2, R$ 15 ou R$ 45; não demonstra gasto marginal evitável.",
                 "Concentração de motivo não indica atraso nem falha operacional por si só.",
                 "23.436 tickets da base não encontram pedido correspondente; não cruzar com vendas sem verificar cobertura."],
                {"estado": "não avaliada", "motivo": "persistência de motivo exige referência calibrada com o time"},
                {"section": "saude", "view": "support"}))
        return achados, "ativa"

    # ------------------------------------------------------------------ Q01

    def _q01(self, query: Query) -> tuple[list[dict[str, Any]], str]:
        resumo = json.loads((self.analytics.snapshot / "resumo.json").read_text(encoding="utf-8"))
        flags = resumo.get("flags", {})
        quarentena = sum(d["quarantined_rows"] for d in resumo["datasets"].values())
        avisos = []
        if quarentena:
            avisos.append({"rotulo": "Registros em quarentena", "valor": quarentena, "unidade": "int"})
        for chave, rotulo in [("fechamento_provavel_sentinela", "Fechamentos com data sentinela"),
                              ("pedido_sem_correspondencia", "Tickets sem pedido correspondente"),
                              ("ticket_antes_pedido", "Tickets abertos antes do pedido")]:
            if flags.get(chave):
                avisos.append({"rotulo": rotulo, "valor": flags[chave], "unidade": "int"})
        if not avisos:
            return [], "nenhuma limitação de cobertura registrada no snapshot"
        return [_alert(
            "Q01", "Limitações de cobertura que restringem algumas métricas",
            "Qualidade do dado", "Informativa", None, avisos,
            "Vem do resumo do snapshot tratado; bloqueia métricas específicas, não a leitura comercial.",
            ["Aviso de confiabilidade, separado de oportunidade financeira.",
             "Tempo de resolução de atendimento não é publicado por causa dos fechamentos sentinela.",
             "Taxa de tickets por pedido não é calculável sobre a cobertura atual."],
            {"estado": "não se aplica", "motivo": "é uma condição do snapshot, não uma série temporal"},
            {"section": "hipoteses"})], "ativa"

    # -------------------------------------------------------------- despacho

    def evaluate(self, query: Query = Query()) -> dict[str, Any]:
        self._cache = {}
        alertas: list[dict[str, Any]] = []
        estados: dict[str, str] = {}
        for rule, avaliador in [("A01", self._a01), ("A02", self._a02), ("A03", self._a03),
                                ("A04", self._a04), ("Q01", self._q01)]:
            achados, estado = avaliador(query)
            alertas.extend(achados)
            estados[rule] = estado
        # A05 depende de ações registradas, que o produto ainda não persiste.
        estados["A05"] = "desabilitada: não há ações registradas com KPI-alvo, baseline e tolerância"

        ordem = {s: i for i, s in enumerate(SEVERITIES)}
        alertas.sort(key=lambda a: (ordem.get(a["severity"], 9), -(a["impact"] or 0)))
        return {
            "scope": {"snapshot": self.analytics.version, "label": self.analytics.scope_label(query),
                      "population": "Aprovado; medidas completas"},
            "parameters": PARAMETERS,
            "alerts": alertas,
            "rules": [{"id": rule, "name": nome, "purpose": proposito,
                       "state": estados.get(rule, "não avaliada"),
                       "published": sum(1 for a in alertas if a["rule"] == rule)}
                      for rule, nome, proposito in CATALOG],
        }
