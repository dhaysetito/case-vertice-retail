"""KPIs por frente de negócio: Vendas, Marketing, Cliente, Estoque e Atendimento.

A aba "Geral" não passa por aqui — continua sendo a visão comercial já existente
em ``Analytics``. Este módulo abre as outras quatro bases do snapshot tratado.

**Configuração central, não código por frente.** ``FRONTS`` declara os KPIs e os
painéis de cada frente; ``payload()`` monta qualquer uma pela mesma rota. Um KPI
novo é uma entrada na configuração, não um ramo de ``if``.

**Nem todo filtro global vale para toda frente.** Estoque é fotografia sem data
de posição, então período não se aplica; canal de venda não existe ali. O canal
de atendimento (WhatsApp, E-mail, ChatBot...) é outro universo, não os canais
comerciais. Cada frente declara o que respeita e o que ignora, e a interface
mostra isso — filtro silenciosamente ignorado é pior que filtro ausente.

Somente biblioteca padrão, como o resto de ``app``.
"""
from __future__ import annotations

import csv
import statistics
from datetime import date
from pathlib import Path
from typing import Any

from .analytics import Analytics, Query

# Metas de primeira resposta por canal, em minutos. Decisão do usuário em
# 2026-09-20: meta por canal, porque a expectativa do cliente muda com o meio.
# Calibradas para discriminar — uma meta que todo canal cumpre não informa nada.
# NÃO são compromisso contratual da empresa; substituir quando houver SLA oficial.
SLA_TARGETS_MIN = {"ChatBot": 2, "WhatsApp": 10, "Telefone": 15, "E-mail": 360, "Reclame Aqui": 960}

APPROVED = "Aprovado"


def _num(value: str | float) -> float:
    return float(value)


def _load(snapshot: Path, name: str) -> list[dict[str, str]]:
    with (snapshot / f"{name}.csv").open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _period(query: Query) -> tuple[str, str]:
    """Janela [início, fim) em ISO, derivada do recorte."""
    if query.start and query.end:
        return query.start, query.end
    if query.month:
        start = date(query.year, query.month, 1)
        end = date(query.year + 1, 1, 1) if query.month == 12 else date(query.year, query.month + 1, 1)
        return start.isoformat(), end.isoformat()
    return date(query.year, 1, 1).isoformat(), date(query.year + 1, 1, 1).isoformat()


def _ratio(numerator: float, denominator: float, scale: float = 1.0) -> float | None:
    """Razão de somas. Denominador zero devolve ``None``, nunca zero artificial."""
    return numerator / denominator * scale if denominator else None


def kpi(id: str, label: str, value: float | None, unit: str, direction: str,
        previous: float | None = None, sample: int | None = None,
        note: str | None = None, blocked: str | None = None) -> dict[str, Any]:
    """Um card. ``direction`` diz o que é bom: subir não é bom para custo nem ruptura."""
    delta = delta_unit = None
    if value is not None and previous not in (None, 0):
        if unit in {"pct", "pp"}:
            delta, delta_unit = value - previous, "pp"
        else:
            delta, delta_unit = (value - previous) / abs(previous) * 100, "pct"
    return {"id": id, "label": label, "value": value, "unit": unit, "direction": direction,
            "previous": previous, "delta": delta, "delta_unit": delta_unit,
            "sample": sample, "note": note, "blocked": blocked}


def table(id: str, title: str, subtitle: str, columns: list[dict[str, str]],
          rows: list[dict[str, Any]], note: str | None = None) -> dict[str, Any]:
    return {"id": id, "type": "table", "title": title, "subtitle": subtitle,
            "columns": columns, "rows": rows, "note": note}


def bars(id: str, title: str, subtitle: str, items: list[dict[str, Any]],
         unit: str, note: str | None = None) -> dict[str, Any]:
    return {"id": id, "type": "bars", "title": title, "subtitle": subtitle,
            "items": items, "unit": unit, "note": note}


def metric_bars(id: str, title: str, subtitle: str, metrics: list[dict[str, str]],
                items: list[dict[str, Any]], default: str, note: str | None = None) -> dict[str, Any]:
    """Barras com seletor de KPI, como o painel por categoria da aba Geral.

    Todos os valores vêm no mesmo payload: trocar de KPI é troca de série na
    tela, não uma nova requisição.
    """
    return {"id": id, "type": "metric_bars", "title": title, "subtitle": subtitle,
            "metrics": metrics, "items": items, "default": default, "note": note}


class Fronts:
    """Carrega as quatro bases extras uma vez e responde por frente."""

    @staticmethod
    def _attach_series(kpis: list[dict[str, Any]], series: dict[str, list[float | None]]) -> list[dict[str, Any]]:
        """Liga a série mensal ao card. Sem série, o card simplesmente não mostra faísca."""
        for card in kpis:
            card["series"] = series.get(card["id"])
        return kpis

    def __init__(self, analytics: Analytics | None = None):
        self.analytics = analytics or Analytics()
        snapshot = self.analytics.snapshot
        self.sales = self.analytics.sales
        self.inventory = _load(snapshot, "estoque")
        self.marketing = _load(snapshot, "marketing")
        self.support = _load(snapshot, "atendimento")

    # ---------------------------------------------------------------- vendas

    def _approved(self, query: Query) -> list[dict[str, str]]:
        return self.analytics._rows(query)

    def sales_front(self, query: Query, previous: Query | None) -> dict[str, Any]:
        rows = self._approved(query)
        current = self.analytics._aggregate(rows)
        prior = self.analytics._aggregate(self._approved(previous)) if previous else {}
        gross = sum(_num(row["receita_bruta"]) for row in rows)
        discount = sum(_num(row["desconto_reais"]) for row in rows)

        by_sku: dict[str, dict[str, Any]] = {}
        for row in rows:
            item = by_sku.setdefault(row["sku_id"], {
                "sku": row["sku_id"], "produto": row["produto"], "categoria": row["categoria"],
                "revenue": 0.0, "margin": 0.0, "orders": set(), "discount": 0.0, "gross": 0.0})
            item["revenue"] += _num(row["receita_liquida"])
            item["margin"] += _num(row["receita_liquida"]) - _num(row["custo_produto"]) - _num(row["custo_frete"])
            item["discount"] += _num(row["desconto_reais"])
            item["gross"] += _num(row["receita_bruta"])
            item["orders"].add(row["order_id"])
        skus = []
        for item in by_sku.values():
            item["orders"] = len(item["orders"])
            item["margin_pct"] = _ratio(item["margin"], item["revenue"], 100)
            item["discount_pct"] = _ratio(item["discount"], item["gross"], 100)
            skus.append(item)
        buckets = [("Sem desconto", 0.0, 0.001), ("Até 5%", 0.001, 5.0), ("5% a 10%", 5.0, 10.0),
                   ("10% a 20%", 10.0, 20.0), ("Acima de 20%", 20.0, 1e9)]
        discount_rows = []
        for label, low, high in buckets:
            selected = [i for i in skus if i["discount_pct"] is not None and low <= i["discount_pct"] < high]
            revenue = sum(i["revenue"] for i in selected)
            margin = sum(i["margin"] for i in selected)
            discount_rows.append({"faixa": label, "skus": len(selected), "revenue": revenue,
                                  "margin_pct": _ratio(margin, revenue, 100)})

        monthly = [self.analytics._aggregate(self._approved(
            Query(query.year, month, query.channel, query.category, query.grain))) for month in range(1, 13)]
        series = {"revenue": [m["revenue"] for m in monthly], "ticket": [m["ticket"] for m in monthly],
                  "margin": [m["margin"] for m in monthly], "margin_pct": [m["margin_pct"] for m in monthly]}

        by_category: dict[str, dict[str, Any]] = {}
        for row in rows:
            bucket = by_category.setdefault(row["categoria"], {
                "name": row["categoria"], "revenue": 0.0, "margin": 0.0, "orders": set(),
                "discount": 0.0, "gross": 0.0})
            bucket["revenue"] += _num(row["receita_liquida"])
            bucket["margin"] += _num(row["receita_liquida"]) - _num(row["custo_produto"]) - _num(row["custo_frete"])
            bucket["discount"] += _num(row["desconto_reais"])
            bucket["gross"] += _num(row["receita_bruta"])
            bucket["orders"].add(row["order_id"])
        category_items = []
        for bucket in by_category.values():
            pedidos = len(bucket["orders"])
            category_items.append({"name": bucket["name"], "values": {
                "revenue": bucket["revenue"], "margin": bucket["margin"],
                "margin_pct": _ratio(bucket["margin"], bucket["revenue"], 100),
                "ticket": _ratio(bucket["revenue"], pedidos),
                "discount_pct": _ratio(bucket["discount"], bucket["gross"], 100)}})
        category_items.sort(key=lambda item: item["values"]["revenue"] or 0, reverse=True)
        category_metrics = [{"id": "revenue", "label": "Receita líquida", "unit": "money"},
                            {"id": "ticket", "label": "Ticket médio", "unit": "money"},
                            {"id": "margin", "label": "Margem de contribuição", "unit": "money"},
                            {"id": "margin_pct", "label": "Margem percentual", "unit": "pct"},
                            {"id": "discount_pct", "label": "Desconto sobre receita bruta", "unit": "pct"}]
        return {
            "kpis": self._attach_series([
                kpi("revenue", "Receita líquida", current["revenue"], "money", "up_good", prior.get("revenue")),
                kpi("ticket", "Ticket médio", current["ticket"], "money", "up_good", prior.get("ticket")),
                kpi("margin", "Margem de contribuição", current["margin"], "money", "up_good", prior.get("margin"),
                    note="Receita líquida menos custo de produto e frete. Não inclui comissões nem impostos."),
                kpi("margin_pct", "Margem percentual", current["margin_pct"], "pct", "up_good", prior.get("margin_pct")),
                kpi("discount_pct", "Desconto sobre receita bruta", _ratio(discount, gross, 100), "pct", "neutral",
                    note="Desconto maior não é automaticamente ruim: pode sustentar volume."),
            ], series),
            "panels": [
                metric_bars("sales_category", "Desempenho por categoria",
                            "Selecione o KPI para comparar no recorte atual",
                            category_metrics, category_items, "revenue"),
                table("sales_discount", "Desconto e margem", "Agrupado por faixa de desconto do SKU",
                      [{"key": "faixa", "label": "FAIXA DE DESCONTO"},
                       {"key": "skus", "label": "SKUS", "format": "int"},
                       {"key": "revenue", "label": "RECEITA", "format": "money"},
                       {"key": "margin_pct", "label": "MARGEM", "format": "pct"}],
                      discount_rows,
                      note="Associação observada entre faixa de desconto e margem. Não demonstra que o desconto causou a margem."),
            ],
        }

    # ------------------------------------------------------------- marketing

    def _campaigns(self, query: Query) -> list[dict[str, str]]:
        """Campanhas inteiramente contidas na janela, como exige docs/02."""
        start, end = _period(query)
        selected = [row for row in self.marketing
                    if row["data_inicio"][:10] >= start and row["data_fim"][:10] < end]
        if query.channel:
            selected = [row for row in selected if row["canal"] == query.channel]
        if query.category:
            selected = [row for row in selected if row["categoria_foco"] in {query.category, "Geral"}]
        return selected

    @staticmethod
    def _campaign_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
        investment = sum(_num(r["investimento_reais"]) for r in rows)
        conversions = sum(_num(r["conversoes"]) for r in rows)
        clicks = sum(_num(r["cliques"]) for r in rows)
        impressions = sum(_num(r["impressoes"]) for r in rows)
        generated = sum(_num(r["receita_gerada"]) for r in rows)
        return {"campaigns": len(rows), "investment": investment, "conversions": conversions,
                "clicks": clicks, "impressions": impressions, "generated": generated,
                "cost_per_conversion": _ratio(investment, conversions),
                "roas": _ratio(generated, investment),
                "ctr": _ratio(clicks, impressions, 100),
                "click_conversion": _ratio(conversions, clicks, 100)}

    def marketing_front(self, query: Query, previous: Query | None) -> dict[str, Any]:
        current = self._campaign_metrics(self._campaigns(query))
        prior = self._campaign_metrics(self._campaigns(previous)) if previous else {}
        sales_by_channel = {item["channel"]: item for item in self.analytics.channels(query)["items"]}

        rows = []
        for channel in sorted({row["canal"] for row in self._campaigns(query)}):
            metrics = self._campaign_metrics([r for r in self._campaigns(query) if r["canal"] == channel])
            sale = sales_by_channel.get(channel, {})
            rows.append({"canal": channel, "investment": metrics["investment"],
                         "cost_per_conversion": metrics["cost_per_conversion"], "roas": metrics["roas"],
                         "click_conversion": metrics["click_conversion"],
                         "sales_revenue": sale.get("revenue"), "sales_margin_pct": sale.get("margin_pct")})
        rows.sort(key=lambda item: item["investment"], reverse=True)

        monthly = [self._campaign_metrics(self._campaigns(
            Query(query.year, month, query.channel, query.category, query.grain))) for month in range(1, 13)]
        series = {"investment": [m["investment"] for m in monthly], "roas": [m["roas"] for m in monthly],
                  "cost_per_conversion": [m["cost_per_conversion"] for m in monthly],
                  "click_conversion": [m["click_conversion"] for m in monthly],
                  "ctr": [m["ctr"] for m in monthly]}
        return {
            "kpis": self._attach_series([
                kpi("cost_per_conversion", "Custo por conversão", current["cost_per_conversion"], "money",
                    "down_good", prior.get("cost_per_conversion"), sample=current["campaigns"],
                    note="Campo original chamado CAC. É proxy: não há campanha nas vendas, então não representa aquisição comprovada."),
                kpi("roas", "ROAS atribuído", current["roas"], "ratio", "up_good", prior.get("roas"),
                    note="Receita declarada pela campanha sobre investimento. Sem incrementalidade: não prova receita adicional."),
                kpi("click_conversion", "Conversão por clique", current["click_conversion"], "pct", "up_good",
                    prior.get("click_conversion")),
                kpi("ctr", "CTR", current["ctr"], "pct", "up_good", prior.get("ctr")),
                kpi("investment", "Investimento", current["investment"], "money", "neutral",
                    prior.get("investment"), sample=current["campaigns"]),
            ], series),
            "panels": [
                table("mkt_channels", "Eficiência por canal",
                      "Investimento das campanhas contra o resultado comercial do mesmo canal",
                      [{"key": "canal", "label": "CANAL"},
                       {"key": "investment", "label": "INVESTIMENTO", "format": "money"},
                       {"key": "cost_per_conversion", "label": "CUSTO/CONV.", "format": "money"},
                       {"key": "roas", "label": "ROAS", "format": "ratio"},
                       {"key": "click_conversion", "label": "CONV./CLIQUE", "format": "pct"},
                       {"key": "sales_revenue", "label": "RECEITA EM VENDAS", "format": "money"},
                       {"key": "sales_margin_pct", "label": "MARGEM", "format": "pct"}],
                      rows,
                      note="As duas últimas colunas vêm de vendas e as demais de campanhas. Não há chave de pedido ligando as bases: a leitura é lado a lado, não atribuição."),
                bars("mkt_investment", "Investimento por canal", "Campanhas contidas na janela",
                     [{"name": row["canal"], "value": row["investment"]} for row in rows], "money"),
            ],
        }

    # --------------------------------------------------------------- estoque

    def inventory_front(self, query: Query, previous: Query | None) -> dict[str, Any]:
        items = self.inventory
        if query.category:
            items = [row for row in items if row["categoria"] == query.category]
        total = len(items)
        out = [row for row in items if _num(row["estoque_disponivel"]) <= 0]
        reorder = [row for row in items if 0 < _num(row["estoque_disponivel"]) <= _num(row["ponto_pedido"])]
        discontinued = [row for row in items if row["status_disponibilidade"] == "Descontinuado"]

        by_category: dict[str, dict[str, Any]] = {}
        for row in items:
            bucket = by_category.setdefault(row["categoria"], {"categoria": row["categoria"], "skus": 0, "ruptura": 0, "reposicao": 0})
            bucket["skus"] += 1
            if _num(row["estoque_disponivel"]) <= 0:
                bucket["ruptura"] += 1
            elif _num(row["estoque_disponivel"]) <= _num(row["ponto_pedido"]):
                bucket["reposicao"] += 1
        category_rows = sorted(by_category.values(), key=lambda b: b["ruptura"], reverse=True)
        for bucket in category_rows:
            bucket["ruptura_pct"] = _ratio(bucket["ruptura"], bucket["skus"], 100)

        critical = sorted(out + reorder, key=lambda row: _num(row["estoque_disponivel"]))[:12]
        critical_rows = [{"sku": row["sku_id"], "produto": row["nome_produto"], "categoria": row["categoria"],
                          "disponivel": _num(row["estoque_disponivel"]), "ponto_pedido": _num(row["ponto_pedido"]),
                          "lead_time": _num(row["lead_time_reposicao"]),
                          "status": row["status_disponibilidade"]} for row in critical]

        return {
            "kpis": [
                kpi("stockout_rate", "Taxa de ruptura", _ratio(len(out), total, 100), "pct", "down_good",
                    sample=total, note="SKUs com estoque disponível menor ou igual a zero, sobre os SKUs do recorte."),
                kpi("stockout_skus", "SKUs em ruptura", len(out), "int", "down_good", sample=total),
                kpi("reorder_skus", "SKUs no ponto de pedido", len(reorder), "int", "down_good", sample=total,
                    note="Disponível acima de zero e igual ou abaixo do ponto de pedido. Não somar com as rupturas."),
                kpi("discontinued", "SKUs descontinuados", len(discontinued), "int", "neutral", sample=total),
            ],
            "panels": [
                bars("inv_category", "Ruptura por categoria", "Percentual de SKUs indisponíveis na fotografia",
                     [{"name": row["categoria"], "value": row["ruptura_pct"]} for row in category_rows], "pct"),
                table("inv_critical", "Produtos críticos", "Menor disponibilidade no recorte",
                      [{"key": "produto", "label": "PRODUTO"}, {"key": "categoria", "label": "CATEGORIA"},
                       {"key": "disponivel", "label": "DISPONÍVEL", "format": "int"},
                       {"key": "ponto_pedido", "label": "PONTO DE PEDIDO", "format": "int"},
                       {"key": "lead_time", "label": "LEAD TIME (DIAS)", "format": "int"},
                       {"key": "status", "label": "STATUS"}],
                      critical_rows),
                table("inv_category_table", "Disponibilidade por categoria", "Fotografia atual",
                      [{"key": "categoria", "label": "CATEGORIA"},
                       {"key": "skus", "label": "SKUS", "format": "int"},
                       {"key": "ruptura", "label": "EM RUPTURA", "format": "int"},
                       {"key": "reposicao", "label": "NO PONTO DE PEDIDO", "format": "int"},
                       {"key": "ruptura_pct", "label": "RUPTURA", "format": "pct"}],
                      category_rows),
            ],
            "warnings": [
                "Esta frente é uma fotografia sem data de posição confirmada: o filtro de período não se aplica, "
                "não há comparação com período anterior e não existe série de evolução.",
            ],
        }

    # ----------------------------------------------------------- atendimento

    def _tickets(self, query: Query) -> list[dict[str, str]]:
        start, end = _period(query)
        return [row for row in self.support if start <= row["data_abertura"][:10] < end]

    @staticmethod
    def _sla(rows: list[dict[str, str]]) -> tuple[float | None, int]:
        """Aderência à meta de primeira resposta, por canal de entrada."""
        eligible = [row for row in rows if row["canal_entrada"] in SLA_TARGETS_MIN]
        within = sum(1 for row in eligible
                     if _num(row["tempo_primeira_resposta_minutos"]) <= SLA_TARGETS_MIN[row["canal_entrada"]])
        return _ratio(within, len(eligible), 100), len(eligible)

    def support_front(self, query: Query, previous: Query | None) -> dict[str, Any]:
        rows = self._tickets(query)
        prior_rows = self._tickets(previous) if previous else []
        sla, eligible = self._sla(rows)
        prior_sla = self._sla(prior_rows)[0] if prior_rows else None
        cost = sum(_num(row["custo_operacional_ticket"]) for row in rows)
        prior_cost = sum(_num(row["custo_operacional_ticket"]) for row in prior_rows)
        csat = [_num(row["nota_csat"]) for row in rows]
        response = sorted(_num(row["tempo_primeira_resposta_minutos"]) for row in rows)

        by_theme: dict[str, dict[str, Any]] = {}
        for row in rows:
            bucket = by_theme.setdefault(row["categoria_problema"], {"tema": row["categoria_problema"], "tickets": 0, "cost": 0.0, "csat": []})
            bucket["tickets"] += 1
            bucket["cost"] += _num(row["custo_operacional_ticket"])
            bucket["csat"].append(_num(row["nota_csat"]))
        theme_rows = sorted(by_theme.values(), key=lambda b: b["tickets"], reverse=True)
        for bucket in theme_rows:
            bucket["share"] = _ratio(bucket["tickets"], len(rows), 100)
            bucket["csat_medio"] = statistics.mean(bucket["csat"]) if bucket["csat"] else None
            bucket["cost_per_ticket"] = _ratio(bucket["cost"], bucket["tickets"])
            bucket.pop("csat")

        by_channel: dict[str, dict[str, Any]] = {}
        for row in rows:
            bucket = by_channel.setdefault(row["canal_entrada"], {"canal": row["canal_entrada"], "tickets": 0, "within": 0, "times": []})
            bucket["tickets"] += 1
            bucket["times"].append(_num(row["tempo_primeira_resposta_minutos"]))
            if _num(row["tempo_primeira_resposta_minutos"]) <= SLA_TARGETS_MIN.get(row["canal_entrada"], 1e9):
                bucket["within"] += 1
        channel_rows = sorted(by_channel.values(), key=lambda b: b["tickets"], reverse=True)
        for bucket in channel_rows:
            bucket["meta"] = SLA_TARGETS_MIN.get(bucket["canal"])
            bucket["mediana"] = statistics.median(bucket["times"]) if bucket["times"] else None
            bucket["sla"] = _ratio(bucket["within"], bucket["tickets"], 100)
            bucket.pop("times")
            bucket.pop("within")

        monthly_tickets = {month: self._tickets(Query(query.year, month)) for month in range(1, 13)}
        series = {
            "tickets": [len(v) for v in monthly_tickets.values()],
            "sla": [self._sla(v)[0] for v in monthly_tickets.values()],
            "cost_per_ticket": [_ratio(sum(_num(r["custo_operacional_ticket"]) for r in v), len(v))
                                for v in monthly_tickets.values()],
            "csat": [statistics.mean([_num(r["nota_csat"]) for r in v]) if v else None
                     for v in monthly_tickets.values()],
        }
        return {
            "kpis": self._attach_series([
                kpi("sla", "SLA de primeira resposta", sla, "pct", "up_good", prior_sla, sample=eligible,
                    note="Meta por canal de entrada, em minutos: " +
                         ", ".join(f"{c} {m}" for c, m in SLA_TARGETS_MIN.items()) +
                         ". Metas provisórias definidas para o protótipo, não compromisso contratual."),
                kpi("cost_per_ticket", "Custo por ticket", _ratio(cost, len(rows)), "money", "down_good",
                    _ratio(prior_cost, len(prior_rows)) if prior_rows else None, sample=len(rows),
                    note="O custo registrado assume apenas R$ 2, R$ 15 ou R$ 45. Não demonstra gasto marginal evitável."),
                kpi("tickets", "Volume de tickets", len(rows), "int", "down_good", len(prior_rows) or None),
                kpi("first_response", "Primeira resposta (mediana)",
                    statistics.median(response) if response else None, "min", "down_good", sample=len(rows),
                    note=f"p90 de {response[int(len(response) * 0.9)]:.0f} min no recorte." if response else None),
                kpi("csat", "CSAT médio", statistics.mean(csat) if csat else None, "score", "up_good",
                    sample=len(csat), note="Escala observada de 1 a 5. Não há meta definida."),
            ], series),
            "panels": [
                table("sup_channel", "Nível de serviço por canal de entrada",
                      "Cada canal tem meta própria de primeira resposta",
                      [{"key": "canal", "label": "CANAL"},
                       {"key": "tickets", "label": "TICKETS", "format": "int"},
                       {"key": "meta", "label": "META (MIN)", "format": "int"},
                       {"key": "mediana", "label": "MEDIANA (MIN)", "format": "int"},
                       {"key": "sla", "label": "ADERÊNCIA", "format": "pct"}],
                      channel_rows),
                table("sup_theme", "Volume por tema", "Onde a demanda se concentra",
                      [{"key": "tema", "label": "TEMA"},
                       {"key": "tickets", "label": "TICKETS", "format": "int"},
                       {"key": "share", "label": "PARTICIPAÇÃO", "format": "pct"},
                       {"key": "cost_per_ticket", "label": "CUSTO/TICKET", "format": "money"},
                       {"key": "csat_medio", "label": "CSAT", "format": "score"}],
                      theme_rows),
                bars("sup_theme_bars", "Participação por tema", "Tickets abertos no recorte",
                     [{"name": row["tema"], "value": row["share"]} for row in theme_rows], "pct"),
            ],
            "warnings": [
                "O canal de atendimento (WhatsApp, E-mail, ChatBot, Telefone, Reclame Aqui) é outro universo, "
                "não os canais de venda: o filtro global de canal não se aplica aqui.",
                "8.974 tickets da base têm fechamento em 2025-12-31 23:59, provável sentinela. "
                "Por isso nenhum indicador de tempo de resolução é publicado.",
            ],
        }

    # ------------------------------------------------------------- despacho

    FRONTS = {
        "sales": {"label": "Vendas", "question": "Estamos vendendo mais e com qualidade econômica?",
                  "filters": ["período", "canal", "categoria"], "ignored": []},
        "marketing": {"label": "Marketing", "question": "Quais canais geram crescimento rentável e quais geram apenas volume?",
                      "filters": ["período", "canal", "categoria"], "ignored": []},
        "inventory": {"label": "Estoque", "question": "Estamos perdendo oportunidades de venda por indisponibilidade de produtos?",
                      "filters": ["categoria"], "ignored": ["período", "canal"]},
        "support": {"label": "Atendimento", "question": "O atendimento está operando com eficiência e dentro do nível de serviço esperado?",
                    "filters": ["período"], "ignored": ["canal", "categoria"]},
    }

    def payload(self, front: str, query: Query = Query()) -> dict[str, Any]:
        if front not in self.FRONTS:
            raise ValueError(f"frente não disponível: {front}")
        spec = self.FRONTS[front]
        pair = self.analytics._previous_query(query)
        previous, previous_label = (pair[0], pair[1]) if pair else (None, None)
        if front == "inventory":
            previous, previous_label = None, None
        builder = {"sales": self.sales_front, "marketing": self.marketing_front,
                   "inventory": self.inventory_front, "support": self.support_front}[front]
        built = builder(query, previous)
        return {
            "front": front,
            "label": spec["label"],
            "question": spec["question"],
            "scope": {"snapshot": self.analytics.version,
                      "label": self.analytics.scope_label(query),
                      "population": "Aprovado; medidas completas" if front == "sales" else "base completa da frente",
                      "previous": previous_label,
                      "filters_applied": spec["filters"], "filters_ignored": spec["ignored"]},
            "kpis": built["kpis"],
            "panels": built["panels"],
            "warnings": built.get("warnings", []),
        }
