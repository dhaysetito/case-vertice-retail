"""Adaptador de provedor de IA para a investigação contextual.

Somente biblioteca padrão, como o resto de ``app``. A credencial é lida do
ambiente e **nunca** sai do servidor: o navegador fala com esta API, e só esta
API fala com o provedor.

Restrições descobertas no gateway em uso (Open WebUI) e que moldam o desenho:

1. Ferramentas declaradas pelo cliente são descartadas — o gateway injeta as
   próprias (``web_search``, ``view_skill``). Function calling controlado é
   inviável, então os números precisam chegar prontos.
2. A mensagem ``system`` é sobreposta por um prompt injetado de ~9 mil tokens.
   Dado colocado em ``system`` não é visto pelo modelo. Por isso instrução e
   dados vão na mensagem do usuário, onde o teste mostrou fidelidade aos
   valores nos três modelos avaliados.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlsplit

BASE_URL = os.environ.get("AI_BASE_URL", "https://chat.eloagents.click").rstrip("/")
COMPLETIONS_PATH = os.environ.get("AI_PATH", "/api/chat/completions")
MODEL = os.environ.get("AI_MODEL", "gpt-55")
TIMEOUT = float(os.environ.get("AI_TIMEOUT", "60"))
MAX_QUESTION = 500

INSTRUCTION = """Você é o analista da Vértice Retail. Responda em português do Brasil.

REGRAS OBRIGATÓRIAS:
1. Use EXCLUSIVAMENTE os números do bloco DADOS. Não busque na web, não use
   conhecimento externo sobre varejo e não estime valor nenhum.
2. Se a resposta não estiver nos DADOS, escreva "não disponível neste recorte" e
   diga qual filtro o gestor precisaria mudar. Nunca preencha a lacuna supondo.
3. Nunca afirme causa. Os dados são observacionais. Diferença entre segmentos e
   variação entre períodos não demonstram causalidade.
4. Não declare lucro, saúde financeira ou economia potencial: a margem destes
   dados é receita líquida menos custo de produto e frete, sem comissões,
   impostos e demais custos econômicos.
5. Um gap contra o consolidado é diagnóstico, não valor recuperável.
6. Reproduza os números com a mesma unidade dos DADOS. Variação de margem
   percentual em pontos percentuais (p.p.); demais KPIs em porcentagem.

FORMATO DA RESPOSTA — use exatamente estes cinco títulos, nesta ordem:

## Pergunta
O que está sendo investigado, em uma linha.

## Fatos
Os valores calculados que sustentam a resposta, com período e população.

## Inferências
Explicações possíveis, marcadas como não comprovadas. Se não houver base para
nenhuma, diga isso.

## Limitações
O que estes dados não permitem afirmar neste recorte.

## Próxima investigação
Um passo concreto: qual corte olhar ou qual dado falta.

Seja direto. Sem saudação, sem oferecer ajuda adicional."""


def available() -> bool:
    """Há credencial configurada? Não valida a chave, só a presença."""
    return bool(os.environ.get("AI_API_KEY", "").strip())


def mode() -> str:
    """``offline`` | ``provider`` | ``unavailable``.

    ``AI_MODE=offline`` responde com a camada analítica e **não** chama o
    provedor: serve para trabalhar na interface sem consumir tokens. Lido a cada
    chamada, e não na importação, para que trocar a variável não exija reimportar.
    """
    if os.environ.get("AI_MODE", "auto").strip().lower() == "offline":
        return "offline"
    return "provider" if available() else "unavailable"


def status() -> dict[str, Any]:
    """Diagnóstico para a interface. Nunca inclui a credencial."""
    current = mode()
    reason = {
        "offline": "AI_MODE=offline: resposta montada localmente, sem consumo de tokens",
        "unavailable": "AI_API_KEY não definida no ambiente do servidor",
    }.get(current)
    return {
        "available": current != "unavailable",
        "mode": current,
        "model": "camada analítica local" if current == "offline" else MODEL,
        "host": None if current == "offline" else urlsplit(BASE_URL).netloc,
        "reason": reason,
    }


def _money(value: float | None) -> str:
    return "indisponível" if value is None else f"R$ {value:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _pct(value: float | None) -> str:
    return "indisponível" if value is None else f"{value:.2f}%".replace(".", ",")


def _int(value: float | None) -> str:
    return "indisponível" if value is None else f"{int(value):,}".replace(",", ".")


def render_data_block(context: dict[str, Any]) -> str:
    """Serializa o contexto analítico em texto legível pelo modelo.

    Tabela em texto em vez de JSON: o teste mostrou citação mais fiel dos
    valores, e o modelo não precisa interpretar aninhamento.
    """
    scope, totals = context["scope"], context["totals"]
    lines = [
        "=== DADOS ===",
        f"Snapshot tratado: {scope['snapshot']} | População: {scope['population']}",
        f"Recorte: {scope['label']}",
        "",
        "TOTAIS DO RECORTE",
        f"  Receita líquida: {_money(totals['revenue'])}",
        f"  Margem absoluta: {_money(totals['margin'])}",
        f"  Margem percentual: {_pct(totals['margin_pct'])}",
        f"  Pedidos: {_int(totals['orders'])}",
        f"  Ticket médio: {_money(totals['ticket'])}",
    ]

    previous = context.get("previous")
    if previous:
        lines += [
            "",
            f"PERÍODO ANTERIOR COMPARÁVEL ({previous['label']})",
            f"  Receita líquida: {_money(previous['revenue'])} | Margem percentual: {_pct(previous['margin_pct'])}"
            f" | Pedidos: {_int(previous['orders'])} | Ticket médio: {_money(previous['ticket'])}",
            "  Margem percentual por canal no período anterior:",
        ]
        lines += [f"    {item['channel']}: {_pct(item['margin_pct'])} (receita {_money(item['revenue'])})"
                  for item in previous.get("channels", [])]
        lines.append("  Margem percentual por categoria no período anterior:")
        lines += [f"    {item['category']}: {_pct(item['margin_pct'])} (receita {_money(item['revenue'])})"
                  for item in previous.get("categories", [])]
    else:
        lines += ["", "PERÍODO ANTERIOR: não há base anterior comparável neste recorte."]

    lines += ["", "POR CANAL (mesmo período e categoria; a comparação mantém todos os canais)"]
    for item in context["channels"]:
        lines.append(
            f"  {item['channel']}: receita {_money(item['revenue'])} | margem {_pct(item['margin_pct'])}"
            f" | pedidos {_int(item['orders'])} | ticket {_money(item['ticket'])}"
            f" | participação na receita {_pct(item['revenue_share_pct'])}"
        )

    lines += ["", "POR CATEGORIA (mesmo período e canal)"]
    for item in context["categories"]:
        lines.append(
            f"  {item['category']}: receita {_money(item['revenue'])} | margem {_pct(item['margin_pct'])}"
            f" | pedidos {_int(item['orders'])} | ticket {_money(item['ticket'])}"
            f" | participação na receita {_pct(item['revenue_share_pct'])}"
        )

    lines += ["", "SÉRIE MENSAL DE 2023 (mesmo canal e categoria do recorte)"]
    for point in context["trend"]:
        lines.append(
            f"  Mês {point['month']:02d}: receita {_money(point['revenue'])} | margem {_pct(point['margin_pct'])}"
            f" | pedidos {_int(point['orders'])} | ticket {_money(point['ticket'])}"
        )

    evidence = context["evidence"]
    lines += [
        "",
        "EVIDÊNCIA DESCRITIVA",
        f"  Margem do consolidado comparável: {_pct(evidence['benchmark_margin_pct'])}",
        f"  Gap do recorte contra o consolidado: {_pct(evidence['gap_margin_pp']) if evidence['gap_margin_pp'] is not None else 'indisponível'} (em pontos percentuais)",
        "",
        "VEREDITOS DO ESTUDO (não recalculados aqui; não altere sem nova evidência)",
    ]
    for item in context["hypotheses"]:
        lines.append(f"  {item['id']} — {item['verdict']}: {item['statement']}")

    lines += [
        "",
        "LIMITAÇÕES CONHECIDAS",
    ]
    lines += [f"  - {item}" for item in evidence["limitations"]]
    lines.append("=== FIM DADOS ===")
    return "\n".join(lines)


def build_messages(question: str, context: dict[str, Any]) -> list[dict[str, str]]:
    """Monta a conversa. Tudo na mensagem do usuário — ver docstring do módulo."""
    body = "\n\n".join([INSTRUCTION, render_data_block(context), f"PERGUNTA DO GESTOR: {question}"])
    return [{"role": "user", "content": body}]


class AIError(RuntimeError):
    """Falha ao consultar o provedor. A mensagem é segura para exibir na tela."""


def offline_answer(question: str, context: dict[str, Any]) -> str:
    """Leitura descritiva do recorte, montada sem provedor nenhum.

    Não é IA e não finge ser: o texto diz isso, e a interface marca a resposta
    como local. Serve para trabalhar na tela sem consumir tokens, e para
    demonstrar a jornada quando não houver credencial. Os números são os mesmos
    que a IA receberia — vêm do mesmo ``investigation_context``.
    """
    totals, evidence = context["totals"], context["evidence"]
    channels = [item for item in context["channels"] if item["margin_pct"] is not None]
    categories = [item for item in context["categories"] if item["margin_pct"] is not None]
    previous = context.get("previous")

    fatos = [
        f"Recorte: {context['scope']['label']}. População: {context['scope']['population']}.",
        "",
        "| Indicador | Valor |",
        "|---|---:|",
        f"| Receita líquida | {_money(totals['revenue'])} |",
        f"| Margem absoluta | {_money(totals['margin'])} |",
        f"| Margem percentual | {_pct(totals['margin_pct'])} |",
        f"| Pedidos | {_int(totals['orders'])} |",
        f"| Ticket médio | {_money(totals['ticket'])} |",
    ]
    if channels:
        low, high = min(channels, key=lambda i: i["margin_pct"]), max(channels, key=lambda i: i["margin_pct"])
        fatos.append("")
        fatos.append(f"- Menor margem por canal: **{low['channel']}**, {_pct(low['margin_pct'])}. "
                     f"Maior: **{high['channel']}**, {_pct(high['margin_pct'])}.")
    if categories:
        low, high = min(categories, key=lambda i: i["margin_pct"]), max(categories, key=lambda i: i["margin_pct"])
        fatos.append(f"- Menor margem por categoria: **{low['category']}**, {_pct(low['margin_pct'])}. "
                     f"Maior: **{high['category']}**, {_pct(high['margin_pct'])}.")
    if previous and previous["margin_pct"] is not None and totals["margin_pct"] is not None:
        delta = f"{totals['margin_pct'] - previous['margin_pct']:+.2f}".replace(".", ",")
        fatos.append(f"- Contra {previous['label']}: margem percentual variou **{delta} p.p.**")
    else:
        fatos.append("- Não há período anterior comparável neste recorte.")
    # Sem filtro de canal ou categoria o recorte É o consolidado, e o gap é zero por
    # definição — exibi-lo só ensina o leitor a ignorar a linha.
    if evidence["gap_margin_pp"] is not None and (context["scope"]["channel"] or context["scope"]["category"]):
        gap = f"{evidence['gap_margin_pp']:+.2f}".replace(".", ",")
        fatos.append(f"- Gap contra o consolidado comparável "
                     f"({_pct(evidence['benchmark_margin_pct'])}): **{gap} p.p.**")

    limitacoes = ["- Esta leitura é local e descritiva: **nenhum modelo interpretou a sua pergunta**."]
    limitacoes += [f"- {item}" for item in evidence["limitations"]]

    return "\n".join([
        "## Pergunta",
        f"{question}",
        "",
        "> **Modo offline.** Resposta montada pela camada analítica, sem chamar a IA e sem "
        "consumir tokens. Os números são reais; a leitura da sua pergunta, não.",
        "",
        "## Fatos",
        *fatos,
        "",
        "## Inferências",
        "Nenhuma. O modo offline não formula hipóteses — para isso, defina `AI_API_KEY` e "
        "remova `AI_MODE=offline` do ambiente do servidor.",
        "",
        "## Limitações",
        *limitacoes,
        "",
        "## Próxima investigação",
        "Compare o canal e a categoria de menor margem acima contra o consolidado no mesmo "
        "período, e depois decomponha custo de produto, frete e desconto no segmento escolhido.",
    ])


def ask(question: str, context: dict[str, Any]) -> dict[str, Any]:
    """Consulta o provedor e devolve a resposta com rastreabilidade do recorte."""
    question = (question or "").strip()
    if not question:
        raise ValueError("pergunta vazia")
    if len(question) > MAX_QUESTION:
        raise ValueError(f"pergunta acima de {MAX_QUESTION} caracteres")

    current = mode()
    if current == "offline":
        return {"answer": offline_answer(question, context), "model": "camada analítica local",
                "mode": "offline", "question": question, "scope": context["scope"],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                "grounding": "resposta montada localmente; nenhum provedor foi chamado"}
    key = os.environ.get("AI_API_KEY", "").strip()
    if not key:
        raise AIError("IA indisponível: AI_API_KEY não está definida no ambiente do servidor.")

    payload = json.dumps(
        {"model": MODEL, "stream": False, "messages": build_messages(question, context)}
    ).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + COMPLETIONS_PATH,
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        # O corpo do provedor pode conter eco da requisição; não repassar à tela.
        raise AIError(f"provedor respondeu HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise AIError("provedor inacessível a partir do servidor") from error
    except TimeoutError as error:
        raise AIError(f"provedor não respondeu em {TIMEOUT:.0f}s") from error
    except json.JSONDecodeError as error:
        raise AIError("resposta do provedor não é JSON válido") from error

    try:
        message = body["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as error:
        raise AIError("resposta do provedor sem conteúdo utilizável") from error

    answer = (message.get("content") or "").strip()
    if not answer:
        # O gateway injeta ferramentas próprias; quando o modelo as chama, o
        # conteúdo volta vazio. Melhor dizer isso do que exibir uma tela em branco.
        raise AIError("o provedor devolveu resposta vazia; tente reformular a pergunta")

    usage = body.get("usage") or {}
    return {
        "answer": answer,
        "model": body.get("model") or MODEL,
        "mode": "provider",
        "question": question,
        "scope": context["scope"],
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
        },
        "grounding": "contexto pré-calculado pela camada analítica; o modelo não consulta dados por conta própria",
    }
