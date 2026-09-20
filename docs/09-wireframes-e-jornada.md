# 09 — Wireframes e jornada H02

Estado: especificação de experiência, sem implementação da aplicação. Abrir [wireframes.html](wireframes.html) no navegador para percorrer as telas por links. O arquivo é um desenho navegável: não salva ações, não consulta IA e não gera relatórios. Controles futuros são apresentados como exemplos desabilitados.

**Atualização visual:** o [novo dashboard](prototipo/index.html) substitui a página longa como proposta de apresentação: gráficos, filtros funcionais, navegação por seção e detalhes em painel lateral. Consulte [interações e limites](11-prototipo-visual.md). Este documento preserva a especificação da jornada.

## Base do exemplo

**[DADO]** Valores recalculados a partir da cópia de trabalho, sem regravar CSVs. Fonte e fórmulas em [wireframe-metricas.json](evidencias/wireframe-metricas.json). População: pagamentos aprovados com medidas completas. Margem = receita líquida − custo do produto − frete.

| Período completo | Receita total | Margem total | Margem % total | Receita Marketplace | Margem % Marketplace |
|---|---:|---:|---:|---:|---:|
| 2023 | R$ 15.966.340,87 | R$ 8.675.612,00 | 54,34% | R$ 3.382.992,20 | 51,52% |
| Novembro/2023 | R$ 2.401.459,88 | R$ 1.277.841,73 | 53,21% | R$ 509.879,49 | 51,00% |
| Dezembro/2023 | R$ 1.979.978,33 | R$ 1.086.374,10 | 54,87% | R$ 450.846,24 | 52,44% |

O exemplo abre em **2023 completo**. Não confundir esses valores com o estudo que inclui janeiro/2024 parcial. A tela temporal demonstra dezembro versus novembro, com a mudança de contexto explícita. Marketplace melhora aproximadamente 1,44 p.p. entre esses meses, mas permanece abaixo do consolidado de dezembro em aproximadamente 2,43 p.p. Isso não refuta H02 nem comprova queda contínua.

**[PRODUTO]** A margem consolidada do mesmo recorte é referência diagnóstica no wireframe. Não é meta aprovada. Alertas, ações e oportunidades exemplificados são rascunhos de produto, não registros históricos de execução.

## Estrutura compartilhada

- Navegação: Visão executiva / Investigar / Oportunidades / Ações e resultados / Hipóteses e métricas.
- Cabeçalho: título, pergunta de negócio, período, população e indicação de dados históricos.
- Filtros: período, canal de venda, categoria de produto, SKU; opções reais e compatibilidade por domínio na aplicação futura.
- Conteúdo: indicador → evidência → próximo passo, com espaço visual para leitura.
- IA: painel contextual acessível a partir da tela, com contexto explícito.
- Relatório: saída acessível na visão executiva e no acompanhamento.
- Estados permanentes: fonte, cobertura, limitações e diferença entre dado observado e simulação.

## T01 — Visão executiva

**Pergunta:** como está o negócio e onde investigar?

Topo com cinco cards: receita líquida, margem absoluta, margem %, pedidos e ticket médio. Cada card abre o mesmo componente de detalhe: definição, população, comparação, série e evidências relacionadas. Como não há 2022, a comparação anual fica “indisponível”; não mostrar seta positiva ou zero artificial.

Abaixo: resumo de achados e referência para investigação. H02 entra como **achado histórico**, sem contador de alertas disparados. O bloco “Alertas prioritários” informa que as regras ainda aguardam calibração. Não usar cor de emergência apenas pela presença de um gap.

Próximos passos: abrir Marketplace; comparar períodos; consultar IA; abrir prévia do relatório. Atendimento será bloco operacional secundário na aplicação, com seu próprio contexto temporal; o wireframe H02 concentra-se na jornada comercial.

## T02 — Investigação de KPI e tendência

**Pergunta:** o que mudou e em qual recorte?

Breadcrumb: Visão executiva → Marketplace → Margem %. Contexto de exemplo: dezembro versus novembro/2023. Mostrar margem % junto de receita e margem absoluta, sem sugerir que melhorar uma taxa equivale a melhorar todo o resultado.

Comparação tabular e visual simples usa os valores verificados. Série longa e decomposição por categoria/SKU são componentes previstos, sem desenhar curvas fictícias. A aplicação deverá mostrar dados e amostra por ponto.

Abas futuras: Evolução / Segmentos / Componentes de margem / Evidências. Descer de canal para categoria mantém canal; descer a SKU mantém categoria. Benchmark mantém período, população e categoria, removendo só a dimensão comparada; nunca desaparece ou vira a própria célula por efeito do filtro.

Próximos passos: investigar componentes, consultar IA e criar rascunho de oportunidade. Ao voltar à tela inicial, restaurar contexto anterior ou oferecer ação explícita para aplicá-lo à visão geral.

## T03 — Detalhe do alerta

**Pergunta:** por que este sinal merece atenção?

Exemplo: “Marketplace abaixo da referência de margem”. Badge: **candidato de regra, não publicado**. Exibir regra A01, versão futura, recorte 2023, margem observada 51,52%, referência 54,34%, gap −2,82 p.p. e receita envolvida. Não atribuir prioridade alta, recorrência ou data de disparo inexistentes.

Checklist de elegibilidade: período completo e medidas disponíveis; materialidade, amostra mínima e persistência ainda pendentes. Mostrar “prioridade não calculada”. Se ativo futuramente: novo / em análise / ação definida / resolvido; descarte com motivo é alternativa.

Próximos passos: abrir série no contexto do sinal; abrir evidência; associar a oportunidade existente ou criar rascunho. A abertura do detalhe não muda status automaticamente.

## T04 — Ranking e detalhe de oportunidade

**Pergunta:** há evidência e informações suficientes para decidir onde atuar?

Lista com oportunidade, tipo, impacto/tipo de impacto, esforço, risco, tempo até benefício, confiança e faixa de prioridade. Exemplo: “Investigar a eficiência de custos do Marketplace”, ligado à H02 e à evidência do período.

Com esforço, risco e prazo desconhecidos, mostrar **aguardando avaliação**. Não inventar P1 para o único item. Impacto financeiro esperado fica “a estimar”; gap diagnóstico não preenche ganho esperado automaticamente. O detalhe explica campos faltantes e permite registrar premissas futuramente.

Próximos passos: completar avaliação, comparar iniciativas elegíveis, selecionar/adiar/descartar com justificativa e criar plano de ação. Ordenação por prioridade não substitui decisão humana.

## T05 — Plano de ação

**Pergunta:** o que faremos e como saberemos se atingimos o objetivo?

Exemplo de **rascunho de investigação**: revisar composição de custos e mapear comissões ausentes. KPI relacionado: margem %, com receita e margem absoluta como proteção. Baseline histórica de referência: Marketplace 2023, 51,52%; esse valor não é automaticamente baseline válida para uma futura intervenção em outro período.

Campos: oportunidade, hipótese vinculada, tipo, ação, justificativa, evidências, KPI-alvo, recorte/baseline, meta/impacto esperado, prazo, status, prioridade. Responsável/observações/datas são opcionais no cadastro. Prazo ou baseline pendentes permitem salvar rascunho, mas não iniciar intervenção real sem plano de medição.

Investigação pode concluir com evidência nova ou resultado inconclusivo. Não exigir ganho de margem para considerar concluída uma tarefa de levantamento. Intervenção posterior será outra ação, com baseline contemporânea, meta, janela e método definidos.

Próximos passos: salvar rascunho, planejar investigação, definir medição e abrir resultados. No wireframe, apenas links; nenhuma gravação ocorre.

## T06 — Resultado da ação

**Pergunta:** a ação funcionou e qual a força da evidência?

Estado real inicial: “aguardando execução e dados posteriores”; KPI antes, meta, KPI atual da janela pós-ação, variação, esperado/observado e guardrails ainda sem preenchimento indevido. A última venda histórica não é “KPI atual” de uma intervenção em 2026.

Subárea isolada: **simulação de interface, sem relação com ação real**. Baseline fictícia 50,0%; meta fictícia 52,0%; pós fictício 51,7%; esperado +2,0 p.p.; observado +1,7 p.p.; distância para meta −0,3 p.p. Todos os valores dessa área são fictícios, inclusive baseline. Não somar com os KPIs reais nem concluir causalidade. Sem dados de guardrails, não declarar sucesso global.

Próximos passos: revisar plano, manter acompanhamento, registrar conclusão ou abrir nova investigação. Concluir execução e concluir avaliação são ações diferentes.

## T07 — IA contextual

Exemplo de pergunta: “Por que a margem do Marketplace caiu em dezembro?” Contexto exibido: aprovados, Marketplace, dezembro versus novembro/2023.

Resposta ilustrativa esperada, identificada como roteiro não executado: **fato**: passou de 51,00% para 52,44%; a premissa de queda não se confirma. **Hipótese a investigar**: composição de custos/mix pode ajudar a explicar a variação e o gap. **Limitações**: comissão e outros custos ausentes, comparação observacional. **Próximo passo**: decompor os componentes disponíveis mantendo população e recorte.

A aplicação precisa realizar consultas reais antes de responder. Citar evidência clicável, sem gerar causalidade, score ou economia de memória. Permitir rascunho de oportunidade, com confirmação para salvar. Credenciais e provedor continuam pendentes.

## T08 — Catálogo de hipóteses e métricas

H01 refutada, H02 validada e H07 validada com limitações. Abrir hipótese apresenta formulação, veredito, universo original, evidências, KPIs e perguntas em aberto. Mostrar explicitamente que a visualização atual de aprovados é distinta do universo original H02. Nova hipótese começa como proposta; associá-la a KPI existente não a torna validada.

## T09 — Relatório semanal

Prévia com semana histórica escolhida, cobertura, KPIs, alertas elegíveis, oportunidades, ações/resultados e próximos passos. O wireframe apenas mostra a estrutura; não apresenta os números de 2023 como se fossem uma semana.

Antes de gerar, selecionar semana completa. Recorte anual/mensal exige essa seleção explícita ou outro título de relatório, sem mudança silenciosa. Reutilizar snapshot e serviços da aplicação. Separar apêndice de cenários demonstrativos; relatório real não inclui ganhos fictícios.

## Teste de percurso para revisão

1. Abrir a visão anual e explicar por que não há comparação com 2022.
2. Investigar Marketplace e identificar a melhora de novembro para dezembro.
3. Abrir candidato A01 e distinguir benchmark, meta e prioridade.
4. Acessar oportunidade e identificar os critérios ainda desconhecidos.
5. Consultar o plano e distinguir investigação de intervenção.
6. Abrir resultado sem dados reais e identificar todos os campos simulados.
7. Consultar o roteiro IA e reconhecer que ele corrige a premissa da pergunta.
8. Abrir H02 e verificar o universo original.
9. Abrir a estrutura de relatório sem confundir janela anual e semanal.

Critério de revisão: conseguir seguir a decisão sem inventar um alerta, uma causa, um peso ou uma ação executada. Identificar pontos de atrito na navegação antes do código da aplicação.
