# 16 — Frentes de negócio na Saúde do negócio

Estado: **implementado**. A navegação por frentes fica logo abaixo do cabeçalho:
`Geral · Vendas · Marketing · Estoque · Atendimento`. Não há página nova nem mudança na
navegação lateral — é a mesma tela mudando de lente.

Desde 2026-09-20 os chips valem em **duas seções**, listadas em `FRONT_SECTIONS`:

| Seção | O que a frente responde | O que renderiza |
|---|---|---|
| Saúde do negócio | como está | KPIs da frente e seus painéis de quebra |
| Evolução e tendências | como mudou | KPIs da frente e a série mensal de 2023, com seletor de KPI e tabela |

A frente escolhida acompanha a troca de seção: sair de Estoque na Saúde e ir para
Tendências mantém Estoque. Nas demais seções — alertas, oportunidades, ações, resultados
— os chips ficam ocultos, porque nenhuma delas trabalha o mesmo recorte.

**Estoque não tem série temporal.** Em Tendências, a frente diz isso e não desenha um
gráfico vazio; os quatro KPIs continuam visíveis. É a mesma limitação da fotografia sem
data de posição.

## Arquitetura

Configuração central, não uma página por frente:

| Camada | Onde | Papel |
|---|---|---|
| Catálogo de frentes | `Fronts.FRONTS` em `app/fronts.py` | rótulo, pergunta de negócio, filtros aplicáveis e ignorados |
| KPIs e painéis | `app/fronts.py`, um método por frente | monta `kpis[]` e `panels[]` a partir do snapshot tratado |
| Contrato do card | `fronts.kpi()` | id, valor, unidade, **direção**, anterior, variação, amostra, nota, bloqueio, série |
| Contrato do painel | `fronts.table()`, `fronts.bars()`, `fronts.metric_bars()` | três tipos genéricos, renderizados pelos componentes já existentes |
| Série mensal | campo `series` de cada KPI | doze valores de 2023; alimenta a faísca do card e o gráfico em Tendências |
| Rota | `GET /api/front/<id>` e `GET /api/fronts` | um caminho para todas |
| Estado na interface | `state.view` em `dashboard.js` | um único valor; `general` é o padrão |
| Renderização | `BUSINESS_VIEWS` + `frontView()` / `frontTrendView()` | dirigida por configuração, sem cadeia de `if` por frente |

Acrescentar um KPI é uma linha na configuração. Acrescentar uma frente é uma entrada em
`FRONTS` mais um método.

A aba **Geral** não passa por `fronts.py`: continua sendo `overview()`, intacta.

## Painel com seletor de KPI

O tipo `metric_bars` reproduz o painel por categoria da aba Geral: um seletor troca o KPI
exibido, e as barras se reordenam. Todos os valores vêm no mesmo payload, então a troca é
local — não dispara nova requisição.

Na frente Vendas, o painel **Desempenho por categoria** oferece os cinco KPIs da própria
frente: receita líquida, ticket médio, margem de contribuição, margem percentual e
desconto sobre receita bruta. O seletor reaproveita `buildMetricMenu()`, o mesmo
componente usado por canal, categoria e tendência na aba Geral.

Os rankings de SKU por margem (melhor e pior desempenho) foram **removidos** a pedido do
usuário em 2026-09-20.

## Semântica da variação

`direction` diz o que é bom, porque subir não é bom para tudo:

| Direção | KPIs |
|---|---|
| `up_good` | receita, margem, ticket, ROAS, conversão, CTR, CSAT, SLA |
| `down_good` | custo por conversão, taxa de ruptura, custo por ticket, volume de tickets, tempo de primeira resposta |
| `neutral` | desconto sobre receita bruta, investimento, SKUs descontinuados |

Desconto é `neutral` de propósito: `docs/02` registra que aumento de desconto não é
automaticamente ruim nem causa comprovada.

## Filtros que não se aplicam

Filtro silenciosamente ignorado é pior que filtro ausente. Cada frente declara o que
respeita, e a interface mostra um aviso âmbar quando algo é ignorado:

| Frente | Aplica | Ignora | Motivo |
|---|---|---|---|
| Vendas, Marketing | período, canal, categoria | — | |
| Estoque | categoria | período, canal | fotografia sem data de posição; canal de venda não existe na base |
| Atendimento | período | canal, categoria | o canal de atendimento (WhatsApp, E-mail, ChatBot, Telefone, Reclame Aqui) é outro universo, e `categoria_problema` não é categoria de produto |

## Parâmetros definidos pelo usuário em 2026-09-20

`docs/02` bloqueava três KPIs por falta de definição. O usuário forneceu as definições em
2026-09-20 e, no mesmo dia, **removeu a frente Cliente** — com ela saíram churn e valor
por cliente. Restou o SLA, em constante no topo de `app/fronts.py`. **Não é compromisso
contratual da empresa.**

**SLA — meta por canal de entrada**, em minutos:

| Canal | Meta | Mediana observada | Aderência |
|---|---:|---:|---:|
| ChatBot | 2 | 1 | 75% |
| WhatsApp | 10 | 8 | 64% |
| Telefone | 15 | 11 | 73% |
| E-mail | 360 | 269 | 71% |
| Reclame Aqui | 960 | 782 | 65% |
| **Consolidado** | | | **69,2%** |

Metas calibradas para discriminar. Metas frouxas (15 min / 60 min / 24 h) davam 100% em
todos os canais — um indicador que nunca acende não serve para decidir.

## Removido a pedido do usuário em 2026-09-20

| O que | Por quê |
|---|---|
| **Frente Cliente** inteira | os 23.388 pedidos de 2023 se concentram em 325 clientes, de 15.000 cadastrados; LTV, churn e recompra descreveriam 2,2% da carteira |
| **Giro de estoque** | era um card permanentemente bloqueado — `docs/02` registra que estoque sem histórico de posições não permite giro, dias em estoque nem venda perdida |

O mecanismo de bloqueio (`kpi(..., blocked="motivo")`) continua no contrato: um card sem
base aparece com `—`, rótulo "Aguardando definição" e o motivo ao clicar. Hoje nenhum KPI
o usa.

## Nomenclatura preservada

Os rótulos são exatamente `Geral`, `Vendas`, `Marketing`, `Estoque`, `Atendimento`. A página continua sendo **Saúde do negócio**. O termo *segmento* não é
usado para essas opções: elas são áreas do negócio, não segmentos de clientes.

## Onde o cálculo acontece

**Sob demanda, no servidor.** Ao trocar de frente ou de filtro, o navegador chama
`GET /api/front/<id>` e `app/fronts.py` calcula aquele recorte na hora, sobre o snapshot
tratado: 300 a 850 ms por frente. Não há pré-cálculo, não há combinação preparada de
antemão, e a lógica de KPI existe num lugar só.

## Limitação conhecida e decisão de 2026-09-20

As cinco frentes novas **exigem que `app.server` esteja no ar**. Abrir `index.html` sem
processo nenhum deixa apenas a aba Geral, que lê o `dados.js` estático; as demais mostram
um aviso explicando como subir a API. Isso contraria a promessa de `docs/11`, de que o
protótipo não exige servidor.

**Decidido não cobrir esse cenário.** As alternativas foram medidas:

| Caminho | Custo | Resultado |
|---|---|---|
| Pré-calcular todo o cruzamento período × canal × categoria | ~1.360 payloads, ~10 MB, 19 min de geração | inviável |
| Pré-calcular só por período | ~378 KB | filtro de canal/categoria continuaria sem resposta |
| Embarcar as linhas e calcular em JavaScript | +5,83 MB no `dados.js` (9,61 → 15,4 MB) e **lógica de KPI duplicada em Python e JS** | offline completo, ao custo de ampliar o risco 4 |

O uso real do projeto é com a API rodando, então nenhuma das três se paga. Reabrir esta
decisão exige um motivo novo — por exemplo, precisar entregar a pasta para alguém abrir
sem terminal.

**Não confundir com `AI_MODE=offline`**, que desliga apenas a chamada ao provedor de IA
para não consumir tokens. Com a API rodando nesse modo, as seis frentes funcionam
normalmente — o que muda é só a origem da resposta da aba Perguntar.

## Verificação

`tests/test_fronts.py` — 20 testes: reconciliação com a camada canônica, direção de cada
KPI, filtros declarados como ignorados, ausência de período anterior no estoque, frente e KPI removidos que
precisam continuar removidos, aderência de SLA conferida contra contagem manual,
os nomes de proxy que `docs/02` exige, e o painel por categoria — que oferece exatamente
os KPIs da frente e reconcilia com `Analytics.categories()` em receita, margem percentual
e ticket.

A interface foi verificada no Chrome headless — 34 checagens: as cinco abas na ordem e com
os nomes exatos, posição entre cabeçalho e filtros, Geral como padrão e preservada, KPIs e
painéis de cada frente, card bloqueado esmaecido, aviso de filtro inaplicável, filtro
global alterando o KPI da frente (R$ 15,97 mi → R$ 3,38 mi ao selecionar Marketplace) e
retorno para Geral sem resíduo, sem exceção no console.
