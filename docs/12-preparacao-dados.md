# 12 — Dados tratados e conexão com o protótipo aprovado

Estado: **visual aprovado inicialmente pelo grupo; preparação de dados executada**. Backend, persistência de decisões, regras calibradas e IA real continuam como próximas entregas. O layout aprovado foi preservado nesta etapa.

## Entrega

- Cinco CSVs tratados em `data_processed/limpeza-v1-2d6da7f3e091/`.
- Dois registros truncados em quarentena, preservados com campos originais, linha física, motivo e hash da fonte.
- Sinalizações de qualidade por registro em arquivo separado, sem alterar datas ou valores de negócio.
- Elegibilidade comercial separada da limpeza: dados de pagamentos não aprovados continuam nos CSVs tratados.
- Manifesto de fontes/saídas com hashes; ponteiro `data_processed/current.json` para a versão atual.
- Gerador de dados do dashboard atualizado para ler o snapshot tratado e verificar sua integridade.
- Processo reexecutado: reutilizou a mesma versão, sem criar cópias adicionais.

## Contagens

| Base | Entrada | Tratada | Quarentena |
|---|---:|---:|---:|
| Vendas | 27.759 | 27.758 | 1 |
| Clientes | 15.000 | 15.000 | 0 |
| Estoque | 5.000 | 5.000 | 0 |
| Marketing | 3.500 | 3.500 | 0 |
| Atendimento | 35.841 | 35.840 | 1 |

Quarentena: `ORD-072219`, vendas, linha física 27.760 (7 de 20 campos); `TKT`, atendimento, linha física 35.842 (identificador truncado e demais campos vazios). A limpeza não reconstruiu conteúdo.

As colunas, ordem dos registros e valores textuais de todos os registros válidos foram preservados. A saída usa UTF-8 com BOM e quebra de linha padronizada, portanto seu hash é diferente do original. IDs continuam textuais; números e datas foram validados em memória sem reescrever sua representação.

## Sinalizações preservadas

| Regra | Registros | Consequência analítica |
|---|---:|---|
| Venda anterior ao cadastro | 8.464 | Não assumir aquisição/coorte a partir de cadastro |
| Ticket sem pedido correspondente | 23.436 | Não compor taxa integrada por pedido sem população válida |
| Ticket anterior ao pedido | 1.688 | Não inferir sequência causal a partir do vínculo de ID |
| Fechamento com provável sentinela | 8.974 | Não usar esse fechamento para duração até confirmar semântica |
| Margem negativa | 491 | Preservar perdas observadas; não remover como outlier |

As contagens podem se sobrepor; não são quantidade de registros excluídos. As 491 margens negativas cobrem todos os status completos; há 427 em aprovados de todo o período e 414 em aprovados de 2023. Os vereditos H01/H02/H07 permanecem inalterados.

Atendimento sem pedido continua válido para contagem/custo de tickets no próprio domínio. Inconsistência no cadastro não invalida automaticamente uma venda para cálculo financeiro.

## População e períodos

- Tratada: 24.454 aprovados, 2.207 cancelados e 1.097 aguardando.
- Dashboard: 23.388 pedidos aprovados em 2023 completo.
- Receita do dashboard: **R$ 15.966.340,87**.
- Margem disponível: **R$ 8.675.612,00**, ou aproximadamente **54,34%**.
- Janeiro/2024 permanece no CSV tratado, identificado como mês incompleto para comparação. Não foi descartado nem incluído silenciosamente no ano de 2023.
- Custos econômicos adicionais continuam ausentes; não foram preenchidos com zero.

A elegibilidade mensal está definida para este snapshot auditado: meses de 2023 completos, janeiro/2024 parcial. Uma nova carga exige nova avaliação de cobertura; a regra não deve ser generalizada automaticamente para qualquer fonte futura.

## Arquivos da camada tratada

| Arquivo | Uso |
|---|---|
| `vendas.csv`, `clientes.csv`, `estoque.csv`, `marketing.csv`, `atendimento.csv` | Dados válidos, preservando colunas e valores |
| `quarentena.jsonl` | Registros excluídos da camada analítica e motivo |
| `qualidade_flags.csv` | Chave, linha, sinalização e consequência por registro |
| `vendas_elegibilidade.csv` | Elegibilidade financeira e de período, sem exclusão física |
| `resumo.json` | Contagens, cobertura, métricas reconciliadas e política |
| `manifest.json` | Hashes de entrada e de cada saída |

O snapshot é local e ignorado pelo Git. As cópias resumidas para documentação estão em [limpeza-resumo.json](evidencias/limpeza-resumo.json) e [limpeza-manifest.json](evidencias/limpeza-manifest.json). Quarentena e flags por registro não foram incluídas na documentação pública do repositório.

## Reproduzir

Executar na raiz de `Case solution`:

```powershell
python tools/preparar_dados.py
python -m unittest discover -s tests -v
python tools/preparar_dados_prototipo.py
```

O primeiro comando usa apenas a biblioteca padrão. O gerador do protótipo usa pandas já disponível no ambiente. Nenhuma dependência foi instalada nesta etapa.

Não executar `auditar_fontes.py` para atualizar o dashboard: ele cria backups; os comandos acima reutilizam o backup e a cópia existentes. Uma reexecução com as mesmas fontes/versão confere e reutiliza o snapshot. Alterações em uma saída existente causam erro em vez de sobrescrita silenciosa. Mudanças de regra exigem nova versão do pipeline.

Esquema inesperado, ausentes fora dos casos conhecidos, chaves duplicadas, números inválidos e identidades financeiras divergentes impedem publicação. Reconciliações estão fixadas para o conjunto auditado deste case; não são metas ou parâmetros comerciais.

## Validações realizadas

- Oito testes: reconhecimento restrito de truncamentos, bloqueio de ausentes inesperados, duplicatas, identidade financeira inválida, números não finitos, reutilização/proteção de snapshot, preservação de todos os campos válidos e manutenção de status não aprovados.
- Conferência de 15 hashes: cinco originais, cinco backups e cinco cópias de trabalho.
- Reexecução idempotente, sem nova pasta tratada ou backup.
- Geração dos 336 agregados do dashboard a partir da camada tratada, com os mesmos totais do visual aprovado.

## Próxima fatia funcional

Usar esta camada como entrada de uma API analítica única, mantendo o visual aprovado: KPIs, séries, filtros e evidências servidos pelos mesmos contratos. Depois conectar persistência de hipóteses/oportunidades/ações e resultados. Alertas continuam candidatos até calibrar materialidade e persistência; IA real depende de integração e credenciais, não de substituir seu roteiro por texto aparentemente autônomo.
