# Vértice Retail — Dashboard Executivo Inteligente

Dashboard executivo orientado à decisão para acompanhar a saúde do negócio, investigar desvios, priorizar oportunidades e conectar análises a ações mensuráveis.

O projeto utiliza dados históricos de 2023 e mantém a cadeia de rastreabilidade:

```text
Hipótese → KPI → Evidência → Alerta → Oportunidade → Ação → Resultado
```

## Requisitos

- Python 3 instalado e disponível no terminal como `python`.
- Diretório `Data` na raiz do projeto com estes cinco arquivos atualizados:
  - `atendimento.csv`
  - `clientes.csv`
  - `estoque.csv`
  - `marketing.csv`
  - `vendas.csv`

A aplicação atual não exige a instalação de pacotes externos.

## Preparar os dados

Na primeira execução, abra o PowerShell na raiz do projeto:

```powershell
cd "caminho\para\case-vertice-retail"
```

Execute os comandos abaixo na ordem apresentada:

```powershell
python tools/auditar_fontes.py
python tools/preparar_dados.py
python tools/preparar_dados_prototipo.py
```

Esses comandos validam os cinco CSVs e geram localmente os dados utilizados pela API e pelo dashboard. Os arquivos fornecidos no diretório `Data` não são alterados.

## Rodar a aplicação

A aplicação utiliza dois processos locais: a API analítica e o servidor do dashboard.

### 1. Iniciar a API

No primeiro terminal, na raiz do projeto, execute:

```powershell
python -m app.server
```

Saída esperada:

```text
API analítica: http://127.0.0.1:8765
```

Para confirmar que a API está funcionando, abra:

[http://127.0.0.1:8765/api/health](http://127.0.0.1:8765/api/health)

### 2. Iniciar o dashboard

Mantenha a API aberta. No segundo terminal, também na raiz do projeto, execute:

```powershell
python -m http.server 8000 --directory docs/prototipo
```

Acesse a aplicação em:

[http://127.0.0.1:8000](http://127.0.0.1:8000)

Quando a conexão estiver correta, o dashboard mostrará **“API conectada — dados tratados”**. O aviso `GET /favicon.ico 404` no terminal é inofensivo.

Para encerrar a aplicação, pressione `Ctrl + C` nos dois terminais.

## Seções implementadas

| Seção | Estado atual |
|---|---|
| **Saúde do negócio** | Exibe os cinco KPIs executivos, filtros temporais e comparações por canal e categoria. |
| **Evolução e tendências** | Permite alternar entre os cinco KPIs no tempo, comparar o período anterior e respeitar intervalos anuais, trimestrais, mensais e semanais. |
| **Alertas prioritários** | Detecta quedas relevantes dos cinco KPIs contra o período anterior, explica o limiar e direciona para a tendência correspondente. |
| **Oportunidades** | Demonstra a transformação de uma evidência validada em oportunidade de investigação priorizável. |
| **Plano de ação** | Apresenta um plano ilustrativo conectado à hipótese, evidência e KPI que se pretende modificar. |
| **Resultado das ações** | Exibe o estado sem resultados reais e permite abrir uma simulação explicitamente identificada. |
| **Hipóteses e métricas** | Mantém o catálogo inicial de hipóteses, vereditos, definições de KPIs e limitações analíticas. |

## Seções e funcionalidades a implementar

| Seção ou funcionalidade | O que falta |
|---|---|
| **Alertas prioritários** | Calibrar persistência, recorrência, amostra mínima e materialidade financeira com usuários. |
| **Ranking de oportunidades** | Implementar avaliação e score documentado de impacto, esforço, risco, velocidade e confiança. |
| **Plano de ação** | Adicionar criação, edição, responsável, prazo, status e persistência das ações. |
| **Resultado das ações** | Conectar intervenções reais, baseline, meta, período de acompanhamento e impacto observado. |
| **IA para investigação** | Substituir o roteiro demonstrativo por uma integração contextual com dados, evidências e limitações. |
| **Relatório executivo semanal** | Gerar automaticamente o relatório a partir da mesma camada analítica utilizada pelo dashboard. |
| **Governança e acesso** | Implementar autenticação, perfis de acesso, histórico de alterações e trilha de auditoria. |
| **Integrações** | Adicionar notificações e conexões com sistemas corporativos somente após validação do MVP. |

## Filtros e métricas disponíveis

Filtros globais:

- período;
- granularidade: ano, trimestre, mês ou semana;
- comparação com período anterior;
- canal;
- categoria.

KPIs disponíveis:

- receita líquida;
- margem absoluta;
- margem percentual;
- pedidos;
- ticket médio.

## Rotas da API

| Rota | Finalidade |
|---|---|
| `/api/health` | KPIs do recorte selecionado. |
| `/api/trend` | Série temporal dos indicadores. |
| `/api/channels` | Comparação dos canais de venda. |
| `/api/categories` | Comparação das categorias. |
| `/api/evidence` | Evidências descritivas e limitações. |
| `/api/metadata` | Metadados, dimensões e contratos disponíveis. |

## Testes

Para executar a suíte automatizada:

```powershell
python -m unittest discover -s tests -v
```

A suíte atual possui 17 testes para contratos analíticos, filtros, intervalos, integridade e segurança da preparação dos dados.

## Solução de problemas

- **Dashboard mostra “Dados tratados — offline”**: confirme que a API está aberta em `http://127.0.0.1:8765/api/health`.
- **`/api/categories` retorna 404**: encerre uma possível API antiga com `Ctrl + C` e inicie novamente `python -m app.server`.
- **Porta 8765 ocupada**: execute `netstat -ano | Select-String ':8765'` e encerre o terminal antigo da API.
- **Alterações não aparecem**: reinicie a API e atualize o navegador com `Ctrl + F5`.
- **Erro ao preparar os dados**: confirme os nomes dos cinco arquivos dentro do diretório `Data`.

## Documentação

A documentação de escopo, arquitetura, métricas, rastreabilidade e plano de implementação está disponível em [`docs/`](docs/).
