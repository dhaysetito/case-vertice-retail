# 01 — Entendimento consolidado e escopo

Referência: definição do grupo recebida em 19/09/2026. Este documento substitui propostas anteriores de produto onde houver conflito, preservando os estudos e seus resultados.

## Problema e proposta

**[CASE]** A Vértice é uma marca digital de moda, beleza e lifestyle, com múltiplos canais, dados fragmentados e preparação manual de relatórios. O case apresenta problemas a investigar; a narrativa de receita crescendo e margem caindo não é prova de que esse comportamento exista em toda a base.

**[REQ]** Criar um dashboard executivo orientado à decisão que responda: como está o negócio, o que exige atenção, onde atuar, o que fazer e se a ação funcionou. Horizonte de até 90 dias. Todas as capacidades principais pertencem ao MVP, com profundidades distintas.

**[CASE]** O módulo C propõe priorizar iniciativas por impacto, esforço, risco e velocidade, com confiança e justificativas. O módulo D propõe um memo executivo recorrente. O case admite outras soluções com desejabilidade, factibilidade e viabilidade. A definição atual integra esses conceitos ao fluxo, sem exigir reproduzir os módulos como produtos separados.

## Continuidade com o estudo existente

| Referência | Situação preservada | Consequência para o produto |
|---|---|---|
| H01 — desconto e deterioração agregada de margem | Refutada no estudo | Não recomendar corte indiscriminado de descontos; exemplos de desconto na definição são ilustrativos |
| H02 — escala com menor margem percentual | Validada; Marketplace também lidera margem absoluta | Investigar eficiência preservando receita e margem absoluta |
| H07 — volume repetitivo de atendimento | Validada; causa raiz não demonstrada | Exibir concentração e custo; propor investigação, sem afirmar atraso logístico como causa |
| Solução anterior de margem + relatório | Base útil, porém mais estreita | Margem é a primeira trilha completa, não o limite estrutural do produto |
| Evidências de aprovados versus todos os status | Reconciliação já documentada e reproduzida nesta auditoria | Cada número identifica universo e período; não misturar valores |

**[PRODUTO]** A trilha inicial mais profunda será margem por canal/categoria/SKU. Atendimento terá visão descritiva, evidências H07 e investigação de oportunidades. Estoque e marketing terão detalhamento limitado aos dados disponíveis; não é necessário criar quatro aplicações verticais.

## Escopo funcional delimitado

| Classe | Entrega |
|---|---|
| MVP obrigatório | Saúde; filtros compatíveis com cada fonte; tendências; alertas explicáveis; ranking com justificativa; registro de decisão; plano simples; resultado observado ou simulação identificada; IA contextual; relatório semanal gerado a partir da mesma camada analítica |
| MVP obrigatório transversal | Catálogo de hipóteses e KPIs; vínculo com evidências; histórico mínimo de versões; população e janela explícitas; tratamento de ausência de dados; cópias segregadas; persistência de ações e decisões |
| MVP desejável | Exportação PDF refinada, comentários, edição administrativa de parâmetros, cenários de sensibilidade do ranking, anotação de eventos nos gráficos, comparações adicionais |
| Evolução posterior | Notificações externas, Slack/Teams, integrações corporativas, autenticação empresarial, perfis complexos, workflows amplos, regras avançadas, predição, streaming e atribuição de mídia |

A navegação deve permitir descobrir evidências e registrar hipóteses já no MVP. O cadastro pode ser simples e curado; não exige construtor visual de fórmulas. Responsável é opcional no registro da ação, conforme requisito; é recomendável defini-lo antes de iniciar uma intervenção real.

## Profundidade e disponibilidade

- **Real e calculável:** métricas descritivas, tendências suportadas, comparações, qualidade e evidências históricas.
- **Gerado por regras de produto:** alertas e gaps. Dependem de parâmetros documentados e calibrados; não são novos fatos de causalidade.
- **Registrado pelo usuário:** decisão, esforço, risco, meta, responsável, prazo e execução. Não existem nos CSVs, mas podem ser dados reais do uso futuro.
- **Simulado:** ações passadas e resultados pós-intervenção criados somente para demonstrar o ciclo. Identificar registro, tela e relatório como simulação; não integrar totais reais.
- **IA real:** depende de provedor/credenciais e ferramentas analíticas verificáveis. Na ausência deles, a interface pode demonstrar o comportamento, mas deve dizer “demonstração”, sem apresentar respostas fixas como investigação executada.

## Regras de escopo e pendências

**Fechado:** finalidade, capacidades do MVP, rastreabilidade, preservação das fontes, profundidade gradual, comparação explícita e decisão humana. O ranking não executa ações automaticamente. IA não calcula livremente métricas financeiras nem altera hipóteses validadas.

**Proposto:** stack, organização das telas, universo aprovado para visão comercial, famílias de alertas e método inicial de priorização.

**Pendente antes de ativar regras reais:** benchmark por granularidade; amostra mínima; materialidade monetária; persistência; tolerâncias; escalas de esforço/risco; pesos se adotados; método de mensuração; provedor de IA e acesso a novas fontes. Não há necessidade de aprovar novamente o backup ou a documentação.

## Fontes consultadas

- `../../Estudo do case/[Bootcamp Elogroup] CASE.pdf`: páginas 2, 4, 7 e 8, incluindo leitura visual das imagens incorporadas; extração textual isolada é incompleta.
- `../../Estudo do case/proximos_passos/00_auditoria_hipoteses.md`.
- `../../Estudo do case/relatorios/RELATORIO_DECISOES_SOLUCAO.md` e `relatorios/H02/relatorio_H02.md`.
- `../../Estudo do case/evidencias_solucao/RELATORIO_EVIDENCIAS.md`.
- `../../Estudo do case/solution/`: decisões, escopo, KPIs, ranking, contratos e roadmap.
- `../../Estudo do case/2.Data Room/dados_limpos/RELATORIO_LIMPEZA.md`.

Os caminhos com `../../Estudo do case` são relativos a este diretório `docs`. Os estudos não foram editados.
