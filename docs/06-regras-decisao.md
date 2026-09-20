# 06 — Alertas, priorização e mensuração

## Princípios

**[PRODUTO]** Usar regras determinísticas, parâmetros versionados e revisão humana. Os CSVs sustentam valores e distribuições, mas não fornecem metas oficiais, tolerâncias, esforço de execução ou apetite a risco. Logo, nenhum limiar numérico ou peso é declarado aprovado aqui.

Regras podem ser executadas em modo retrospectivo de calibração. Resultados desse modo devem ser identificados como candidatos, não alertas operacionais publicados. Um parâmetro obrigatório ausente desabilita a regra, com explicação; não recebe valor silencioso.

## Pré-condições comuns

- População e fonte válidas; custos necessários à fórmula disponíveis.
- Janelas comparáveis; sem misturar meses parciais/completos ou universos financeiros.
- Denominador e amostra suficientes, com limite explicitamente calibrado.
- Benchmark da mesma métrica, população e contexto; valor consolidado é referência diagnóstica, não meta recuperável garantida.
- Materialidade suficiente; filtros de usuário não mudam retrospectivamente a regra que originou uma evidência.

Os custos disponíveis são suficientes para a margem operacional definida (produto + frete). Sua incompletude econômica deve permanecer visível; não é coerente bloquear toda análise por falta de comissão e simultaneamente chamar a métrica de margem completa.

## Famílias iniciais de alertas

| ID e finalidade | Condição proposta | Evidência e encaminhamento |
|---|---|---|
| A01 — gap material de margem | `benchmark_pct − margem_pct > limite_pp`, impacto diagnóstico ≥ limite monetário, volume ≥ mínimo; persistência quando houver série | Mostrar benchmark, receita, margem absoluta, custos e série; investigar canal/categoria/SKU |
| A02 — deterioração temporal | Queda de margem em p.p. ou de receita/margem em R$ acima de tolerância; janela anterior comparável; persistência mínima | Diferenciar queda pontual e repetida; decompor sem declarar causa |
| A03 — perdas em pedidos | Soma das perdas observadas em pedidos com margem negativa supera materialidade no recorte | Mostrar pedidos afetados, perda absoluta e concentração; investigar custos/preço/frete |
| A04 — demanda repetitiva relevante | Volume e custo de motivo são materiais e há aumento/persistência acima da referência calibrada | Mostrar tickets, participação e custo registrado; abrir investigação H07, sem inferir atraso |
| A05 — guardrail após ação | Receita, margem absoluta, CSAT ou outro KPI de proteção piora além da tolerância definida no plano | Revisar intervenção; não declarar automaticamente que a ação causou a piora |
| Q01 — qualidade/cobertura | Esquema inválido, truncamento, ausência de cobertura ou join incoerente | Aviso de confiabilidade separado de oportunidade financeira; bloquear só as métricas afetadas |

A01–A03 são o primeiro conjunto comercial; A04 pode começar como candidato em atendimento; A05 acompanha ações reais ou cenários claramente separados. Ruptura de estoque pode aparecer como condição de fotografia, mas não como “nova piora” sem snapshots históricos.

Magnitude em p.p. deve usar taxas em fração multiplicadas por 100. Impacto diagnóstico: `max(0, benchmark_pct − margem_pct) × receita_liquida`, com ambas as taxas na mesma escala fracionária. O valor é dimensão do gap, não saving.

## Materialidade, persistência e fadiga

1. Calibrar candidatos nas semanas/meses completos de 2023 para vendas e na cobertura própria de atendimento.
2. Examinar volume de alertas, concentração por entidade e exemplos úteis/inúteis com gestores.
3. Definir materialidade absoluta e relativa; evitar pequenas células extremas e múltiplos testes de SKU sem controle de ruído.
4. Definir persistência como `k` de `n` períodos elegíveis; definir recuperação com tolerância própria para evitar abre/fecha contínuo.
5. Agrupar por regra/versão, entidade e população. Atualização periódica acrescenta ocorrência, não outra notificação idêntica.
6. Agrupar canal e seus SKUs quando representam o mesmo problema; preservar acesso aos detalhes.
7. Mostrar poucas prioridades na entrada, com acesso à lista completa. Reconhecimento/silenciamento temporário tem prazo e justificativa.

Severidade do alerta depende de materialidade, persistência e relevância; não confundir com confiança dos dados ou prioridade de uma iniciativa. Recorrência da condição também não deve aumentar score indefinidamente.

## Ranking sem pesos arbitrários

**Problema:** o ranking anterior propunha pesos fixos (40%, 15% etc.). Eles são hipótese de design, não evidência. A definição atual pede impacto, esforço, risco, velocidade e confiança; portanto, não adotá-los automaticamente.

### Primeira abordagem: vetor de critérios e camadas de dominância

1. Separar oportunidades de **investigação** e de **intervenção**. Não comparar impacto financeiro desconhecido com ganho estimado como se ambos estivessem mensurados.
2. Exigir evidência, recorte, tipo de impacto, premissas e completude dos critérios. Faltantes mantêm oportunidade “aguardando avaliação”, nunca esforço zero ou confiança alta.
3. Registrar vetor: impacto (maior melhor), esforço (menor melhor), risco (menor melhor), tempo até benefício (menor melhor), confiança (maior melhor).
4. A domina B se não for pior em nenhum critério e for melhor em ao menos um, dentro de critérios comparáveis. A primeira camada reúne oportunidades não dominadas; removê-las produz a camada seguinte.
5. Exibir **Prioridade P1, P2…**, vetor e justificativa. Na mesma camada, tratar como empate decisório; gestor escolhe e registra motivo. Não inventar precisão decimal para forçar ordem total.

Essa classificação é um score ordinal de prioridade, sem pesos. Ela não elimina escolhas: as escalas e sua comparabilidade precisam ser justificadas. Valores incertos devem usar cenários/faixas; intervalos sobrepostos ou critérios não comparáveis podem manter empate.

### Definição dos critérios

| Critério | Entrada sugerida | Origem e cuidados |
|---|---|---|
| Impacto | R$ esperados numa janela comum, com faixa e premissas; ou impacto diagnóstico em fila separada | Não somar nem comparar diretamente gap, capacidade liberada e economia financeira |
| Esforço | Pessoa-dias e dependências conhecidas | Estimativa do time; CSV não contém esforço |
| Risco | Categorias ordenadas com descritores de dano e reversibilidade | Critérios acordados com gestor; não inferir risco de negócio do desvio estatístico |
| Velocidade | Dias até primeiro benefício mensurável | Inclui implantação e maturação; diferente de esforço |
| Confiança | Evidência/cobertura/comparabilidade e incerteza da intervenção | Distinguir confiança no achado da confiança no benefício; não fabricar probabilidade de sucesso |

Investigações podem usar materialidade do problema, relevância da decisão e critérios de execução em fila própria; não ganham ROI fictício. O relatório executivo pode mostrar as prioridades de cada fila com a decisão do gestor.

### Evolução para score numérico, se necessário

Forma candidata: `S = 100 × Σ(w_j × u_j(x_j))`, com `w_j >= 0` e `Σw_j = 1`. `u_j` traduz uma escala explicitamente aprovada para 0–1; esforço, risco e tempo têm direção invertida. Ausente não vira zero. Nenhum peso ou ponto de corte foi escolhido nesta etapa.

Calibrar por comparações de iniciativas concretas com gestores, documentar trade-offs e testar sensibilidade da ordenação. Validar com casos reservados do histórico e revisar dupla contagem (por exemplo, receita já incorporada ao impacto). Se pequenas mudanças de peso inverterem a ordem, mostrar empate/instabilidade. Usar faixas de referência estáveis, não normalização min–max que muda com qualquer filtro.

## Da oportunidade à ação

Sugestões se dividem em investigação, coleta de dado e piloto de intervenção. Cada uma carrega evidência e limitação. Sem causa demonstrada, “investigar custos/comissões” é defensável; “cortar descontos” não decorre automaticamente de H02.

Ação precisa de oportunidade, justificativa, KPI primário, prazo/status e plano de medição. Impacto esperado pode ser “a estimar”; não exigir um número inventado para permitir investigação. Responsável é opcional no cadastro; sua ausência fica visível.

## Mensuração

Congelar baseline antes da ação: KPI/versão, população, segmento, datas, valor e snapshot. Meta é decisão de negócio. Medição pós-ação mantém definição, janela comparável e guardrails; registra mudanças de contexto.

- Variação observada = KPI pós − baseline; taxas em p.p. quando pertinente.
- Meta versus realizado é mensurável sem demonstrar causalidade.
- Impacto atribuível exige método adequado, como controle comparável ou experimento; não é produzido automaticamente por antes/depois.
- Mais margem % acompanhada de queda relevante de margem absoluta/receita não é sucesso automático.
- Redução de custo de tickets pode representar capacidade liberada; economia de caixa exige validação adicional.
- Ações que afetam o mesmo segmento/janela compartilham grupo de sobreposição. Não somar seus benefícios sem regra de atribuição.
- Com os CSVs atuais, não há registro de intervenção e acompanhamento posterior identificado. O MVP pode exibir “aguardando dados” e um cenário demonstrativo isolado.
