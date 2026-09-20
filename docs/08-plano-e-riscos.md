# 08 — Plano de implementação, riscos e critérios de aceite

## Horizonte de até 90 dias

**[PRODUTO]** O MVP inclui todas as capacidades; os marcos abaixo aumentam profundidade. Em 0–30 dias deve existir uma jornada demonstrável completa, mesmo que resultados sejam simulados e registros de ação sejam simples. Não adiar uma seção inteira obrigatória para uma evolução indefinida.

| Período | Entregas | Dependências e saída verificável |
|---|---|---|
| 0–10 dias | Contratos de dados/métricas, protocolo de limpeza, população, desenho das telas e plano de medição | Backup já feito; confirmar parâmetros pendentes; reconciliar métricas com estudos |
| 11–20 dias | Camada analítica, cinco KPIs principais, filtros válidos, tendências, regras candidatas e evidências | Hashes preservados, contagens rastreadas, períodos comparáveis e sem multiplicação em joins |
| 21–30 dias | Fluxo básico completo: alerta → oportunidade → decisão → ação → resultado; IA limitada; relatório de semana histórica | Registrar e recuperar uma decisão; cenário explícito quando faltar dado; validar utilidade com gestor |
| 31–60 dias | Calibração de alertas/ranking, refinamento de ações, IA, integração entre análises e testes de usabilidade | Pesos apenas se justificados; dados de atendimento cruzados com cobertura; ajustes baseados em uso |
| 61–90 dias | Medição de intervenções se houver dados, relatório recorrente, documentação operacional e governança | Resultados reais somente com observações posteriores; separar melhorias do produto de efeito financeiro |

Esse cronograma é uma proposta, não estimativa fechada de esforço. Capacidade da equipe, disponibilidade do gestor, credenciais e acesso a fontes determinam o que poderá ser operacionalizado. Sem fontes recorrentes, entregar protótipo histórico confiável e plano de instrumentação.

## Backlog por prioridade

| Ordem | Item | Aceite essencial |
|---|---|---|
| 1 | Ingestão da cópia e quarentena | Originais com hashes inalterados; apenas exclusões documentadas; cancelados preservados na camada tratada |
| 2 | Catálogos de KPI/dimensão/hipótese | H01 refutada, H02/H07 validadas com fontes e limitações; fórmula e população versionadas |
| 3 | Métricas e comparação | Totais reconciliados; margem ponderada; sem dados ≠ zero; janeiro parcial sinalizado |
| 4 | Visão executiva e investigação | Poucos cards, detalhe navegável, contexto mantido; filtros incompatíveis explícitos |
| 5 | Alertas simples | Evidência reprodutível, materialidade, deduplicação; regras sem calibração em modo candidato |
| 6 | Oportunidade e ranking | Evidência obrigatória; critérios completos/pendentes visíveis; empate permitido; decisão humana registrada |
| 7 | Plano de ação | KPI e motivo rastreáveis, baseline/plano antes de intervenção; responsável opcional; persistência após recarga |
| 8 | Resultado | Esperado/observado e limitações; simulação isolada; concluir execução não fabrica ganho |
| 9 | IA contextual | Consulta real à camada analítica com fontes ou demonstração declarada; nenhuma causalidade fabricada |
| 10 | Relatório semanal | Mesmo snapshot e valores do dashboard; fontes e cenários preservados; versão reproduzível |

Os itens são dependências lógicas e podem ter desenvolvimento sobreposto futuramente; não autorizam implementação nesta etapa.

## MVP desejável e simplificações

- Desejável: exportação PDF aprimorada, comentários, edição simples de parâmetros, avaliação de sensibilidade, anotações no gráfico e histórico visual mais rico.
- Usar tabela/lista de ações antes de um gerenciador corporativo de projetos.
- Usar catálogo curado e funções registradas antes de um construtor visual de KPIs.
- Usar regras de comparação/materialidade antes de modelos de anomalia ou predição.
- Usar ferramentas tabulares da IA antes de banco vetorial ou múltiplos agentes.
- Usar geração de relatório sob demanda antes de integrações e notificações.
- Não estimar perda de receita por ruptura, elasticidade de preço ou retorno marginal de mídia sem novos dados/métodos.
- Não adicionar dezenas de cards só porque os campos existem; marketing/LTV não precisam disputar a entrada executiva com métricas mais confiáveis.

Evoluções posteriores: notificações externas, sistemas corporativos, perfis avançados, tempo real, motor genérico de regras, modelos preditivos, atribuição de mídia e margem econômica ampliada. Novas fontes podem viabilizar partes em 90 dias, mas não há promessa sem confirmação.

## Riscos e respostas

| Risco | Efeito | Mitigação e responsável funcional sugerido |
|---|---|---|
| Mistura de populações H02/aprovados | Valores divergentes e perda de confiança | Contrato e reconciliação; Analytics/Finanças |
| Custos econômicos ausentes | Impacto superestimado | Nome correto da margem, premissas e custos adicionais; Finanças |
| Join tickets/vendas | Multiplicação financeira e falsa causalidade | Agregação, validação temporal e cobertura; Dados |
| Recortes pequenos e muitas regras | Fadiga e falsos sinais | Materialidade/amostra/persistência calibradas; Analytics/gestor |
| Score aparentar objetividade inexistente | Prioridade frágil | Critérios visíveis, empates, calibração e sensibilidade; sponsor |
| Somar impactos sobrepostos | Benefício fictício | Grupos de sobreposição e janela comum; Finanças |
| IA inventar números ou causas | Decisão indevida | Ferramentas permitidas, citações e avaliação; Produto/Analytics |
| Ausência de ações históricas e dados novos | Impossibilidade de medir impacto real | Estados aguardando dados e simulação explícita; sponsor |
| LTV/estoque sem série e datas inconsistentes | Tendências enganosas | Restringir indicadores e rotular fotografia/cobertura; Dados |
| Banco ativo sincronizado em OneDrive | Conflito entre gravações/processos | Banco do piloto no servidor local, snapshots de backup; Engenharia |
| Falta de gestor/owner de execução | Painel sem decisão ou ação | Ritual de revisão e responsabilização simples; sponsor |
| Dependência de provedor IA | Custo, indisponibilidade e atraso | Adaptador, limites, fallback de evidências; Engenharia |
| Escopo visual e técnico excessivo | Não concluir em 90 dias | Jornada completa simples e backlog graduado; Produto |
| Exposição de cadastro/texto livre | Compartilhamento desnecessário de dados | Agregados, minimização e controle de acesso antes de publicação; Engenharia |

## Validação de valor

**Desejabilidade:** em sessões curtas, observar se gestores conseguem identificar um desvio, verificar evidências, comparar prioridades e definir uma ação mensurável. Registrar dificuldades e tempo, sem inventar metas ou usuários entrevistados.

**Factibilidade:** reproduzir métricas dos CSVs, rastrear cada alerta, persistir decisões, impedir joins inflacionários e demonstrar a IA com consultas verificadas. Compatibilidade de dependências e ambiente será verificada na implementação.

**Viabilidade:** medir esforço de preparar o relatório, manter dados/regras, operar IA e executar decisões. Comparar custo operacional do produto com benefício observado/esperado qualificado. Gap diagnóstico não é ROI da solução.

## Testes necessários na implementação

- Testes financeiros e temporais: identidade, razão de somas, denominador zero, população, limites de data e comparação parcial.
- Testes de integridade: uma venda com vários tickets não muda receita; snapshots e vínculos versionados não são sobrescritos.
- Testes das regras: limiares, persistência, deduplicação, recuperação e parâmetros ausentes.
- Testes de workflow: decisões persistem; baseline congelada; simulações não entram nos totais reais.
- Testes de paridade: dashboard, ferramentas IA e relatório retornam os mesmos números para o mesmo contexto.
- Avaliação IA: fatos/números corretos, fontes válidas, recusa de causalidade e comportamento em falta de dados.
- Teste de extensibilidade: cadastrar uma hipótese adicional e reutilizar o fluxo sem nova navegação; nova fórmula pode exigir função testada.

## Critério de conclusão do MVP

Uma pessoa percorre saúde → tendência → alerta/evidência → oportunidade → decisão → ação → resultado, consegue explicar a origem de cada número e identificar o que é simulado. A IA investiga dentro da cobertura disponível; o relatório reproduz o mesmo estado. Regras e pesos não calibrados não são apresentados como verdade de negócio.

## Próxima entrega, após esta definição

Detalhar wireframes e fechar o contrato de implementação: parâmetros analíticos, política inicial de ranking, plano de mensuração, provedor de IA e ambiente do piloto. Em seguida, implementar a primeira fatia vertical do fluxo. A documentação atual não dispara instalação, deploy, commit ou push.
