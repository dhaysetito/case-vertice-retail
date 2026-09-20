# 02 — Fontes, preservação e métricas

## Auditoria executada

**[DADO]** A auditoria inicial confirmou hashes iguais por nome de arquivo entre `Data`, `../Estudo do case/2.Data Room` e `../Estudo do case/2.Data Room/dados_originais`. Por solicitação do usuário, as cópias redundantes do estudo foram excluídas do backup. Permanece apenas o conjunto de cinco CSVs de `Data`, em `backups/20260919T231914609851Z/projeto_Data`. Há mais cinco cópias em `data_work/20260919T231914609851Z`, destinadas à futura limpeza. Os arquivos nas pastas de origem não foram alterados.

O [manifesto](evidencias/backup-manifest.json) registra hashes SHA-256, tamanhos e caminhos. O [perfil](evidencias/perfil-dados.json) registra colunas reais e resultados da auditoria. Os CSVs não foram regravados. Exclusões usadas nos cálculos desta auditoria ocorreram apenas em memória.

| Fonte | Linhas originais | Colunas | Granularidade e cobertura verificadas |
|---|---:|---:|---|
| vendas | 27.759 | 20 | `order_id` único; uma linha/SKU por pedido nesta base; 01/01/2023–26/01/2024 |
| clientes | 15.000 | 14 | `customer_id` único; cadastro 2020–2025; atributos históricos sem série temporal |
| estoque | 5.000 | 16 | `sku_id` único; fotografia sem data de posição confirmada; última entrada 2023–2025 |
| marketing | 3.500 | 15 | Campanha; início/fim em 2023–2025; sem fatos diários nem chave de pedido |
| atendimento | 35.841 | 12 | Ticket; abertura 2023–2025; uma linha incompleta |

Não foram encontradas duplicatas integrais nem de chave nessas leituras. Existem uma venda truncada e um ticket truncado. A última venda completa é de 26/01/2024 às 10:53:49; a linha truncada tem horário posterior. Não usar a linha incompleta para estender a cobertura válida.

### Protocolo da futura limpeza

1. Ler a cópia de trabalho, mantendo IDs como texto e validando esquema e tipos.
2. Colocar registros truncados em quarentena com arquivo, linha, motivo e conteúdo recuperável; não imputar medidas.
3. Preservar pagamentos cancelados/aguardando na camada tratada; o filtro financeiro pertence à população analítica.
4. Sinalizar relações temporais inválidas e provável sentinela, sem inventar correções.
5. Preservar outliers e margens negativas salvo evidência de erro; validar identidades monetárias.
6. Gravar saídas em `data_processed/<versao>/`, com relatório de transformação e hash da entrada; não sobrescrever `Data` ou backups.
7. Conferir hashes dos originais ao terminar. Datas de extração não são datas de posição do estoque.

## Limitações verificadas e consequências

| Achado | Consequência |
|---|---|
| Vendas com 27.758 linhas completas, 24.454 aprovadas | Universo deve constar de todo KPI financeiro |
| 23.436 de 35.840 tickets válidos sem pedido nas vendas | Não calcular tickets por pedido usando todos os tickets e apenas vendas disponíveis |
| 12.404 tickets encontram pedido; 1.688 antecedem sua venda | Match de ID não basta; investigação conjunta exige coerência temporal e cobertura publicada |
| 8.464 vendas antecedem cadastro | Não usar cadastro automaticamente como aquisição ou origem de coorte |
| 8.974 fechamentos em `2025-12-31 23:59:00` | Provável sentinela; não publicar tempo de resolução como métrica executiva validada |
| Somente 346 clientes nas vendas completas, 331 nas aprovadas e 445 nos tickets | Não generalizar frequência/reincidência para 15.000 clientes cadastrados |
| Custos de ticket assumem apenas R$ 2, R$ 15 e R$ 45 | Custo registrado não demonstra gasto marginal evitável ou horas liberadas |
| Não há campanha em vendas | Sem CAC de aquisição validado, ROAS incremental ou margem pós-marketing reconciliada |
| Estoque sem histórico de posições | Ruptura atual é calculável; giro real, tendência e vendas perdidas não |
| Comissões, impostos, tarifas e efeito financeiro de devoluções ausentes | Margem = líquida − produto − frete; não chamar de lucro líquido ou margem econômica completa |

Não houve erro da identidade de margem acima da tolerância de R$ 0,011 nas vendas completas, nem da identidade de estoque disponível = físico − reservado. Isso demonstra consistência interna, não completude econômica.

## Reconciliação preservada

| População | Receita total | Margem total | Receita Marketplace | Margem % Marketplace |
|---|---:|---:|---:|---:|
| Todos os status completos — H02 | R$ 18.889.334,01 | R$ 10.270.436,65 | R$ 3.986.568,87 | 51,42% |
| Aprovados — proposta do dashboard | R$ 16.668.956,49 | R$ 9.058.427,55 | R$ 3.527.694,64 | 51,50% |

Margem consolidada de aprovados: 54,34%; gap Marketplace: aproximadamente −2,84 p.p. A H02 continua validada em seu universo original. Há 427 pedidos aprovados com margem negativa. A nova auditoria reproduz a reconciliação já existente, não altera os vereditos.

## Contrato comum de KPI

Cada KPI declara ID, versão, pergunta de negócio, fórmula, unidade, fonte, população, campo temporal, granularidades, dimensões compatíveis, regra de comparação, sentido desejável, tratamento de nulos/denominador zero, limitações e responsável pela definição.

Taxas são calculadas como razão de somas, salvo médias de medidas individuais explicitamente definidas. Denominador zero retorna “não calculável”, nunca zero artificial. Diferença entre taxas é em pontos percentuais; variação relativa só quando a base permite interpretação. Para receita/margem em reais, mostrar também diferença absoluta; base negativa exige cautela e pode desabilitar percentual relativo.

**[PRODUTO]** Saúde comercial inicia com cinco cards: receita líquida, margem absoluta, margem %, pedidos e ticket médio. Atendimento aparece em bloco operacional enxuto (tickets e custo registrado), com aprofundamento em CSAT e tempo de resposta. Evitar misturar janelas: se o bloco operacional tiver outro período, rotulá-lo claramente ou usar a interseção escolhida pelo usuário.

## Catálogo inicial

| ID / pergunta | Fórmula e campos reais | Uso e restrição |
|---|---|---|
| receita_liquida / quanto vendemos? | Σ `vendas.receita_liquida` de aprovados completos | Saúde, tendência; `data_pedido` |
| margem_absoluta / quanto sobra após custos disponíveis? | Σ líquida − Σ `custo_produto` − Σ `custo_frete` | Saúde; reconciliar `margem_contribuicao`; custos incompletos |
| margem_pct / qual eficiência? | margem absoluta / receita líquida | Saúde, alertas, oportunidade, resultado; não média simples de margens |
| pedidos / qual volume? | distintos `order_id` na população | Saúde, materialidade e proteção |
| ticket_medio / receita por pedido? | receita líquida / pedidos | Saúde e diagnóstico de mix |
| desconto_pct / qual concessão? | Σ `desconto_reais` / Σ `receita_bruta` | Detalhe; aumento não é automaticamente ruim ou causa comprovada |
| produto_receita e frete_receita / composição dos custos? | Σ componente / Σ receita líquida | Investigação e evidências |
| devolucao_pct / frequência registrada? | pedidos com `devolvido=True` / pedidos | Detalhe; sem inferir estorno ou custo |
| perdas_observadas / onde há margem negativa? | −Σ mínimo(`margem_contribuicao`, 0) | Diagnóstico; não confundir com ganho recuperável |
| tickets / qual demanda? | distintos `ticket_id` completos | Operacional/tendência por `data_abertura` |
| custo_atendimento / esforço financeiro registrado? | Σ `custo_operacional_ticket` | Operacional; não equivale a economia evitável |
| custo_ticket / custo médio? | custo registrado / tickets | Detalhe; sensível a composição de canais |
| participacao_motivo / onde concentra demanda? | tickets do motivo / tickets do recorte | H07, alertas candidatos e investigação |
| csat_medio / satisfação registrada? | média `nota_csat` válida, com n e escala observada 1–5 | Detalhe; mostrar quantidade de respostas, não inventar meta |
| primeira_resposta / espera inicial? | mediana e p90 `tempo_primeira_resposta_minutos` | Eficiência; não medir descumprimento de SLA sem meta |
| ruptura_snapshot / indisponibilidade na fotografia? | SKUs `estoque_disponivel <= 0` / SKUs selecionados | Detalhe estático; 99/5.000; data de posição desconhecida |
| ponto_pedido_snapshot / necessidade sinalizada? | SKUs disponível ≤ `ponto_pedido` / SKUs selecionados | Detalhe; 800/5.000, incluindo rupturas; não somar com elas |
| roas_atribuido / retorno registrado em campanhas? | Σ `receita_gerada` / Σ `investimento_reais` | Contexto de marketing; sem incrementalidade |
| custo_conversao_proxy / custo por conversão reportada? | Σ investimento / Σ `conversoes` | Campo original `cac` é proxy, não aquisição comprovada |
| ctr e conversao_clique / desempenho do funil? | Σ cliques / Σ impressões; Σ conversões / Σ cliques | Campanhas selecionadas; não taxa de conversão do site |

`clientes.ltv_acumulado` existe, mas não possui janela/metodologia reconciliada. Pode constar do dicionário como atributo histórico informado; não compõe card de LTV estimado, LTV/CAC, ranking ou efeito de ações no MVP. Reincidência de atendimento permanece evidência qualificada do estudo, sem transformá-la em FCR/reabertura.

## Métricas por seção do fluxo

| Seção | Métricas iniciais |
|---|---|
| Saúde | Cinco KPIs comerciais e bloco operacional reduzido |
| Tendências | Séries dos KPIs com data de evento válida; sem série histórica de estoque/LTV |
| Alertas | Valor observado, referência, variação absoluta/relativa ou p.p., volume, persistência e materialidade |
| Oportunidades | Gap e impacto diagnóstico; impacto esperado somente com premissas; esforço, risco, tempo e confiança registrados |
| Ações | KPI-alvo, baseline, meta, prazo e indicadores de proteção; status vem do uso da aplicação |
| Resultados | KPI antes/depois, esperado/observado, janela e nível de atribuição; simulação explicitamente separada |
| Relatório | Reutiliza essas métricas; nenhuma fórmula adicional |

Tempo alerta–decisão, ações concluídas e esforço de produzir relatórios são métricas futuras de uso do produto, não derivadas dos CSVs históricos.

## Regras temporais e filtros

- **Vendas:** começar pelos meses completos de 2023. Comparação semanal usa semanas completas na cobertura disponível; janeiro/2024 parcial não é comparado automaticamente com mês completo. Calendário e cobertura são metadados, não inferidos apenas pela existência de linhas.
- **Atendimento:** `data_abertura`, motivo e canal de entrada; recortes comerciais só após join validado e com cobertura exibida. Não alterar total de vendas por multiplicação de tickets.
- **Marketing:** campanhas integralmente contidas na janela, com exclusões visíveis. Existem 853 na janela de vendas conforme o estudo. Uma série por coorte de campanha não representa investimento/receita diária; não ratear duração arbitrariamente.
- **Estoque:** filtro de categoria/SKU sobre fotografia, sem filtro temporal histórico; canal não existe. `data_ultima_entrada` não é data de snapshot.
- **Clientes:** atributos atuais/históricos informados não descrevem automaticamente o estado do cliente na data da venda.
- **Dimensões:** `canal_venda`, `canal_entrada`, `categoria_produto`, `categoria_problema` e `categoria_foco` são distintas. “Geral” em marketing não deve ser distribuído artificialmente entre categorias.
- Filtro incompatível aparece como indisponível ou exige troca explícita de contexto; nunca é ignorado silenciosamente. Fora da cobertura retorna “sem dados”, não queda para zero.
