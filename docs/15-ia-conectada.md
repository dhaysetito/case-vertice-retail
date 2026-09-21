# 15 — Investigação com IA conectada

Estado: **implementada e conectada a um provedor real**. Complementa `07-ia-e-relatorio.md`,
que permanece como especificação; este documento registra o que foi construído, o que o
provedor em uso permite e o que continua pendente.

## O que a tela faz

Desde 2026-09-20 a investigação **é a seção Hipóteses e métricas**, não uma gaveta. O
botão "Investigar com IA", no cabeçalho, navega até ela; estando nela, rola até a caixa
de perguntas e põe o foco. A seção tem quatro abas:

| Aba | Conteúdo |
|---|---|
| **Perguntar** | Hipóteses sugeridas para o recorte atual e caixa de texto livre; a resposta vem do provedor |
| **Resumo** | Leitura determinística do KPI em foco, sem IA |
| **Canais** | Comparação por canal, sem IA |
| **Categorias** | Comparação por categoria, sem IA |

As três últimas são o roteiro determinístico anterior, preservado de propósito: `07` exige
que falha ou timeout preservem a navegação e permitam consultar evidências sem IA.

**O que a seção perdeu.** Os cartões de veredito H01/H02/H07 e o catálogo de indicadores
foram removidos a pedido do usuário em 2026-09-20. Eram a única exibição desses vereditos
e das definições de KPI na interface — as respostas da IA continuam citando ambos, que
seguem em `docs/01` e `docs/02` e no contexto enviado ao modelo.

**Duas armadilhas de CSS** apareceram na mudança e valem lembrar: `.fronts{display:flex}`
vencia o atributo `hidden`, deixando os chips de frente visíveis em toda seção; e a caixa
de perguntas estava estilizada por `dialog textarea#ai-question`, seletor que deixou de
casar quando ela saiu da gaveta. Verificação que olha só a propriedade `hidden` não pega
nem uma nem outra — é preciso conferir `offsetParent` ou a largura renderizada.

As hipóteses sugeridas **não são uma lista fixa**. Vêm de `Analytics.suggestions()` e
nomeiam o canal e a categoria de menor margem do recorte, a variação contra o período
anterior quando existe, e a concentração de receita. São perguntas, nunca conclusões.

## Modos de operação

`AI_MODE` decide como a aba "Perguntar" responde:

| Modo | Quando | Comportamento |
|---|---|---|
| `provider` (padrão, com `AI_API_KEY`) | uso normal | consulta o gateway; ~9 mil tokens de prompt injetado por pergunta |
| `offline` (`AI_MODE=offline`) | desenvolvimento e demonstração sem custo | resposta montada pela camada analítica; **nenhuma chamada de rede, zero token** |
| `unavailable` (sem chave) | credencial ausente | aba desabilitada, com o motivo na tela |

O modo offline existe porque o custo por pergunta é fixo e alto: o gateway injeta o
mesmo prompt gigante independentemente do tamanho do recorte. Fechar a interface exige
dezenas de iterações, e pagar por cada uma não faz sentido.

A resposta offline **não finge ser IA**. Traz os números reais do recorte nos mesmos
cinco blocos, um aviso em destaque, a etiqueta "Resposta local · sem IA" e a frase
"nenhum modelo interpretou a sua pergunta" no bloco de limitações. É o "modo
demonstrativo identificado" que `07` autoriza.

## Arquitetura da chamada

```text
navegador  --POST /api/ai/investigate-->  app/server.py
                                              |
                              app/analytics.py: investigation_context(query)
                                              |
                                   app/ai.py: monta prompt + chama provedor
                                              |
                                        gateway (HTTPS)
```

A credencial é lida de `AI_API_KEY` no ambiente do servidor. **Nunca chega ao navegador,
não é gravada em arquivo e não aparece em `/api/ai/status`.**

## Restrições do gateway em uso e o que elas impuseram

O provedor configurado é uma instância de Open WebUI. Três comportamentos foram medidos e
mudaram o desenho:

| Observado | Consequência |
|---|---|
| Ferramentas declaradas pelo cliente são descartadas; o gateway injeta as próprias (`web_search`, `view_skill`). Forçar `tool_choice` numa função própria retorna erro dizendo que ela não existe. | *Function calling* controlado, como `07` sugere, é inviável aqui. Os números precisam chegar prontos. |
| A mensagem `system` é sobreposta por um prompt injetado de ~9 mil tokens. Com os dados em `system`, os modelos responderam "não tenho acesso a dados específicos" ou especularam genericamente. | Instrução e dados vão na **mensagem do usuário**, onde o teste mostrou fidelidade aos valores. |
| O modelo pode chamar uma ferramenta do gateway e devolver conteúdo vazio. | Resposta vazia vira erro explícito na tela, não tela em branco. |

## Como a resposta é aterrada

`investigation_context()` entrega o recorte inteiro antes da pergunta: totais, período
anterior comparável **com abertura por canal e por categoria**, os sete canais, as quatro
categorias, os doze meses de 2023, a evidência descritiva com o gap contra o consolidado,
os vereditos preservados de H01/H02/H07 e as limitações conhecidas.

O recorte inteiro vai junto justamente porque a IA não pode consultar nada: sem isso, uma
pergunta sobre outro mês exigiria que o gestor mudasse o filtro antes de perguntar.

O prompt proíbe explicitamente: buscar na web, usar conhecimento externo, estimar valor,
afirmar causa, declarar lucro ou economia potencial, e tratar gap como valor recuperável.
Exige o formato de cinco blocos de `07` — Pergunta, Fatos, Inferências, Limitações,
Próxima investigação — e responder "não disponível neste recorte" quando for o caso.

## Verificação executada

Comparando a resposta do modelo com a camada canônica, no recorte
`novembro/2023 · Marketplace`:

| Categoria | Citado pela IA | `Analytics.categories()` |
|---|---:|---:|
| Lifestyle | 50,12% | 50,12% |
| Beleza | 50,67% | 50,67% |
| Moda | 50,94% | 50,94% |
| Acessórios | 52,97% | 52,97% |

Em `novembro/2023 · todos os canais`, a IA respondeu a "quais canais acompanham a queda?"
com os sete canais e a variação em p.p. contra outubro, todos batendo com a camada
analítica. Antes da inclusão do período anterior por canal, ela respondeu corretamente
"não disponível neste recorte" e nomeou o filtro que faltava — comportamento exigido
por `07`.

`tests/test_ai.py` cobre o contexto, as sugestões, o prompt, o modo offline e a falha do
provedor, com 24 testes que não tocam a rede. Um deles injeta uma exceção em
`urllib.request.urlopen` e verifica que o modo offline **não a dispara** nem mesmo com
credencial presente.

A tela foi verificada no Chrome headless nos dois modos — 21 checagens: painel abre,
sugestões carregam da API, pergunta livre responde, markdown vira títulos e tabelas, não
há injeção de HTML, as abas determinísticas seguem funcionando e o console fica limpo.

## Pendências

- **Ferramentas de leitura próprias** dependem de um provedor que não descarte o array
  `tools`, ou de acesso direto ao modelo sem o gateway.
- **Histórico de perguntas** não é persistido; recarregar a página perde a conversa.
- **Avaliação da IA** (`07`, "Avaliação mínima") não foi automatizada: não há suíte de
  perguntas adversariais medindo fidelidade e recusa apropriada.
- **Custo por pergunta** carrega ~9 mil tokens de prompt injetado pelo gateway,
  independentemente do tamanho do recorte.
- **Relatório executivo semanal** continua pendente e não usa esta camada ainda.
