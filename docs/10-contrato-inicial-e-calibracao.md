# 10 — Contrato inicial e calibração pendente

Complementa os documentos 02 e 06. **Definido para o desenho** não significa validado como política operacional da empresa.

## Decisões utilizáveis na próxima implementação

| Item | Definição de produto | Justificativa |
|---|---|---|
| Universo comercial | Pagamentos aprovados com medidas completas; status restantes preservados no dado tratado | Coerência com proposta anterior e reconciliação já verificada |
| Janela inicial da jornada | 2023 completo | Evita janeiro/2024 parcial e permite comparação mensal dentro da cobertura |
| Comparação ilustrada | Dezembro versus novembro/2023 | Meses completos; não implica ajuste sazonal ou duração diária igual |
| Métricas principais | Receita, margem absoluta, margem %, pedidos, ticket médio | Perguntas executivas e campos disponíveis |
| Unidade da variação de margem | Pontos percentuais | Evita confusão com variação relativa |
| Referência do wireframe | Margem consolidada no mesmo período/população e filtros compartilhados | Diagnóstico transparente; não meta nem garantia de captura |
| Filtro comparado | Remover apenas a dimensão que define o grupo de comparação | Comparar Marketplace com empresa sem deixar benchmark igual à própria célula |
| Rótulo de alerta sem calibração | Candidato; prioridade não calculada | Sem publicar um gatilho sem parâmetros |
| Oportunidade incompleta | Aguardando avaliação, sem posição ordinal | Ausente não recebe pontuação favorável |
| Ação inicial H02 | Investigação de composição de custos e dados faltantes | Evidência não autoriza automaticamente alterar preço/desconto |
| IA no desenho | Roteiro identificado; implementação exigirá ferramentas reais | Evita aparência enganosa de integração pronta |
| Resultado inicial | Aguardando dados; exemplo sintético em área separada | Não existem ações empresariais pós-achado identificadas nos CSVs |
| Relatório | Seleção explícita de semana histórica completa | Não converter agregados anuais em semanais |

O benchmark consolidado inclui o próprio canal na comparação, portanto é apenas uma referência contextual. Comparação com outros canais excluindo o analisado é uma alternativa futura distinta, com identificação própria. Não trocar a referência silenciosamente.

## Parâmetros não fornecidos pelos dados

| Parâmetro | Como definir | Comportamento antes da definição |
|---|---|---|
| Gap mínimo em p.p. | Inspecionar distribuição histórica e avaliar relevância com gestor | A01 permanece candidato |
| Materialidade monetária | Relacionar tamanho da exposição e custo de investigação | Não marcar todo gap como prioritário |
| Amostra mínima | Avaliar estabilidade por granularidade; SKU difere de canal | Não publicar regra de SKU extremo |
| Persistência k de n | Avaliar séries completas e repetição de sinais | Não inventar recorrência histórica |
| Tolerância de recuperação | Definir separadamente do disparo para evitar oscilação | Encerramento operacional ainda não automático |
| Risco e confiança | Descritores observáveis e avaliação humana | Marcar como não avaliado |
| Esforço e tempo até benefício | Estimativa do responsável pela execução | Não calcular ranking final |
| Meta/guardrails de uma ação | Definição no plano com período, unidade e método | Rascunho; sem conclusão de sucesso |
| Provedor/credencial de IA | Escolha técnica e acesso do projeto | Roteiro demonstrativo, sem chamada simulada como real |

## Calibração proposta, sem pesos inventados

1. Após limpeza conservadora, calcular séries por períodos completos e registrar distribuição dos gaps/volumes por canal, categoria e SKU.
2. Criar cenários de limiares identificados como experimentais; contar candidatos únicos, persistência, cobertura e concentração.
3. Revisar amostra de casos materiais, pequenos, recorrentes e benignos com gestor. O histórico não oferece rótulo universal de “alerta correto”; avaliar utilidade, não alegar precisão estatística sem ground truth.
4. Escolher limites justificáveis, registrar política/versão e avaliar em janela cronológica reservada, sem ajustar continuamente a mesma amostra.
5. Classificar oportunidades completas por camadas de dominância; manter empates e explicação. Não aplicar pesos iguais por conveniência.
6. Caso seja necessário score ponderado, elicitar trade-offs e testar sensibilidade antes de publicar pesos. Fila de investigação e fila de intervenção continuam separadas.

## Preparação para limpeza — etapa seguinte

Usar `data_work/20260919T231914609851Z`, sem criar outro backup redundante. Validar hashes contra manifesto existente. Produzir saída tratada versionada e quarentena, preservando cópia de entrada e originais.

O plano mantém exclusão apenas dos dois registros fisicamente incompletos já identificados, com rastreio; status financeiro como filtro analítico; sentinelas/inconsistências temporais como flags, sem datas inventadas; sem remoção automática de outliers. Novos achados exigem documentação da decisão.

Esta entrega limita-se a wireframes e contrato de experiência. Não executa limpeza, regras operacionais, aplicativo ou integração IA.
