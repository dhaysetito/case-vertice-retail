# Vértice Retail — Dashboard Executivo Inteligente

Estado: **visual aprovado inicialmente; dados tratados e conectados ao protótipo. Aplicação completa ainda em desenvolvimento por etapas**.

**[Abrir protótipo visual do dashboard](docs/prototipo/index.html)** — seções independentes, gráficos com dados de 2023, filtros de período/canal/categoria e detalhes em painel lateral. Funciona localmente, sem servidor ou dependências externas. É um protótipo de apresentação; IA, execução de ações e geração de relatórios não estão implementadas.

O produto conecta monitoramento, investigação, priorização, decisão, ação e mensuração. A IA atua transversalmente, com evidências e limitações explícitas. O relatório semanal é uma saída da mesma camada analítica do dashboard.

## Documentação inicial do escopo

1. [Escopo consolidado e decisões](docs/01-escopo.md)
2. [Fontes, backup, auditoria e contrato de métricas](docs/02-dados-e-kpis.md)
3. [Arquitetura funcional, telas e navegação](docs/03-arquitetura-funcional.md)
4. [Arquitetura técnica sugerida](docs/04-arquitetura-tecnica.md)
5. [Modelo conceitual e rastreabilidade](docs/05-modelo-dominio.md)
6. [Alertas, oportunidades, ranking e mensuração](docs/06-regras-decisao.md)
7. [IA contextual e relatório executivo](docs/07-ia-e-relatorio.md)
8. [Plano de 90 dias, riscos e critérios de aceite](docs/08-plano-e-riscos.md)
9. [Wireframes e jornada H02](docs/09-wireframes-e-jornada.md) — [abrir desenho navegável](docs/wireframes.html)
10. [Contrato inicial e calibração pendente](docs/10-contrato-inicial-e-calibracao.md)
11. [Protótipo visual e interações](docs/11-prototipo-visual.md)
12. [Preparação de dados executada](docs/12-preparacao-dados.md)
13. [API analítica inicial](docs/13-api-analitica.md)

## Dados preservados

- `Data/`: cinco CSVs originais do projeto, **não modificar**.
- `backups/20260919T231914609851Z/projeto_Data/`: um único conjunto de backup dos cinco CSVs de `Data`.
- `data_work/20260919T231914609851Z/`: cópia de entrada usada pelo tratamento, preservada e ainda idêntica aos originais.
- `data_processed/limpeza-v1-2d6da7f3e091/`: cinco bases tratadas, quarentena, sinalizações de qualidade, elegibilidade e manifesto. O protótipo agora lê os agregados produzidos dessa versão.
- [Manifesto de backup](docs/evidencias/backup-manifest.json): origem, destino, tamanho e SHA-256 dos cinco arquivos preservados no backup.
- [Perfil dos CSVs](docs/evidencias/perfil-dados.json): leitura dos arquivos, estrutura, datas, nulos, relacionamentos e reconciliação financeira.

O backup é local, no mesmo ambiente de armazenamento; protege contra alterações de trabalho, mas não equivale a uma cópia externa de recuperação de desastre. Nenhum arquivo foi enviado ao GitHub. Dados e cópias locais estão no `.gitignore`.

## O que foi executado nesta etapa

Leitura do case, backup verificado, documentação, protótipo visual e limpeza conservadora concluídos. Dois registros truncados foram segregados; os valores válidos foram preservados. Oito testes de integridade passaram. Originais, backup e cópia de entrada permanecem intactos. Não foram instaladas dependências ou implementadas APIs nesta etapa.

Para reproduzir o tratamento e atualizar os dados do protótipo, executar `python tools/preparar_dados.py` e depois `python tools/preparar_dados_prototipo.py`. A primeira execução publica uma versão tratada; reexecuções com as mesmas fontes reutilizam a versão sem criar novos backups. Testes: `python -m unittest discover -s tests -v`.

O utilitário `tools/auditar_fontes.py` reproduz a auditoria documental com Python e pandas já disponíveis no ambiente. Executá-lo novamente cria outro conjunto datado de cópias e atualiza os relatórios JSON; não é o futuro pipeline da aplicação. O manifesto de cada execução também fica guardado em seu backup.

## Convenção de evidência

- **[CASE]**: orientação do enunciado original.
- **[REQ]**: requisito explícito do grupo, consolidado nesta documentação.
- **[DADO]**: resultado verificado nos CSVs ou conclusão identificada de estudo existente.
- **[PRODUTO]**: escolha proposta de experiência, arquitetura ou regra operacional.
- **[INFERÊNCIA]**: explicação plausível ainda não demonstrada.
- **[PENDENTE]**: parâmetro ou dependência sem definição suficiente; não é um fato.

O escopo funcional está delimitado. Limiares, pesos de priorização, credenciais de IA e ambiente de hospedagem continuam explicitamente pendentes; isso não autoriza inventá-los.
