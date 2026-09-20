# 07 — IA contextual e relatório semanal

## Papel da IA

**[REQ]** A IA é parte do MVP e atua transversalmente. **[PRODUTO]** Começar com investigação limitada, mas real: responder a perguntas usando consultas e comparações disponíveis, citar a evidência e reconhecer quando a pergunta não pode ser respondida. Não basta um texto estático com aparência de chat.

O provedor/modelo não está definido. Sem credenciais, utilizar modo demonstrativo identificado ou explicar indisponibilidade. Não apresentar execução de ferramenta que não ocorreu. O funcionamento de KPIs, alertas e ranking não depende de uma chamada de LLM.

## Comportamento por seção

| Contexto | O que a IA pode fazer | Limite |
|---|---|---|
| Saúde | Resumir variações materiais, cobertura e indicadores em conflito | Não declarar lucro líquido ou saúde geral com custos incompletos |
| Tendências | Comparar períodos válidos e sugerir decomposição por canal/categoria/SKU | Não afirmar sazonalidade com apenas um ciclo anual nem prever sem modelo validado |
| Alertas | Explicar a regra acionada, localizar evidência e investigar recortes disponíveis | Regra disparada não prova causa; magnitude deve ser reproduzível |
| Oportunidades | Comparar critérios, explicitar premissas e sugerir dados/testes faltantes | Não preencher esforço, risco ou benefício como fatos se não informados |
| Ações | Propor rascunho de investigação/piloto e plano de medição | Gestor confirma gravação; sem alterações automáticas de preço, canal ou orçamento |
| Resultados | Comparar esperado/observado e examinar guardrails e fatores concorrentes | Não converter antes/depois em efeito causal; destacar simulação |
| Catálogo | Recuperar hipóteses, fontes, vereditos e propor novas perguntas | Não mudar H01/H02/H07 sem nova evidência e revisão explícita |

## Contrato da investigação

Entrada: pergunta, tela, domínio, período, comparação, filtros, IDs relacionados, snapshot, versões de métricas e limitações conhecidas. Mostrar ao usuário o contexto usado; permitir ajuste quando a pergunta exigir outro recorte.

Ferramentas iniciais sugeridas: consultar definição de KPI, calcular KPI permitido, comparar janelas/segmentos, decompor componentes de margem, consultar evidências/hipóteses, consultar cobertura e recuperar ação/plano de medição. Todas somente de leitura para investigação. Propostas de oportunidade/ação são rascunhos que o usuário pode salvar.

Não conceder SQL livre, execução de código arbitrário ou acesso irrestrito a arquivos. Templates parametrizados validam dimensão, janela e cardinalidade. Números vêm das ferramentas; a resposta referencia seus IDs. Texto livre dos CSVs é conteúdo não confiável, nunca instrução para a IA. Preferir agregados, sem nomes de clientes ou textos identificáveis desnecessários.

Estrutura da resposta:

1. **Hipótese/pergunta:** o que está sendo investigado; status da hipótese.
2. **Fatos e evidências:** valores calculados, comparação, período, população e fontes clicáveis.
3. **Inferências:** possíveis explicações, explicitamente não comprovadas.
4. **Limitações:** cobertura, custos ausentes, tamanho da amostra e relações não identificáveis.
5. **Próxima investigação/recomendação:** consulta adicional, dado faltante ou teste proposto.

Se o usuário perguntar “por que caiu?”, primeiro verificar se houve queda na janela. Pode responder “não há queda observada nesse recorte” ou “não há dados suficientes”. Se houver queda, decompor contabilmente custos/receita não autoriza afirmar causa comportamental.

## Avaliação mínima da IA

- Pergunta numérica deve reproduzir a camada canônica, com unidade e fonte.
- Pergunta sobre H01 não pode transformá-la em validada por influência de exemplo de produto.
- Pergunta sobre ROAS incremental deve explicar a ausência de identificação.
- Pergunta sobre giro/ruptura histórica deve reconhecer falta de snapshots.
- Filtros incompatíveis não podem ser aplicados silenciosamente.
- Cenário simulado deve permanecer identificado em todas as respostas.
- Falha/timeout deve preservar navegação e permitir consultar evidências sem IA.

Usar conjunto pequeno de perguntas de referência e adversariais, com revisão humana. Registrar ferramentas, fontes, latência, consumo e avaliação de fidelidade; orçamento e metas numéricas dependem de provedor e baseline.

## Relatório executivo semanal

**[REQ]** Saída do dashboard, inspirada no módulo D; nenhuma lógica analítica duplicada.

Conteúdo: contexto e cobertura → saúde/KPIs → mudanças materiais → alertas → oportunidades/decisões → ações → resultados → riscos/próximos passos. A IA pode redigir síntese, mas o template também deve funcionar com texto determinístico.

Cada edição conserva semana de referência, snapshot, filtros, versões, evidências, estado das ações no momento e marcação de simulações. O relatório não recalcula ou altera um score depois de publicado. Regeração gera nova edição identificada.

No MVP, botão “Gerar relatório semanal” monta automaticamente o documento com a mesma camada da interface. Revisão antes de compartilhar, conforme fluxo anterior do projeto. Agendamento simples pode entrar quando houver atualização real; envio externo não integra o MVP obrigatório.

Sem fontes novas, o relatório deve indicar “edição sobre dados históricos”. Repetir execução em 2026 não cria uma nova semana de desempenho comercial. Um ciclo de demonstração usa semana histórica escolhida, nunca o relógio atual como se existissem vendas atuais.
