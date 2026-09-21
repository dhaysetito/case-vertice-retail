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

### Credencial da IA (opcional)

A investigação com IA precisa de uma credencial, lida do ambiente pelo servidor. Sem ela,
o dashboard continua funcionando e a aba de perguntas informa a indisponibilidade.

```powershell
$env:AI_API_KEY = "<sua-chave>"
```

```bash
export AI_API_KEY='<sua-chave>'
```

Defina a variável **no mesmo terminal em que a API será iniciada**. Variáveis opcionais:
`AI_MODEL` (padrão `gpt-55`), `AI_BASE_URL`, `AI_TIMEOUT` (padrão 60s).

### Modo offline — trabalhar sem consumir tokens

Durante o desenvolvimento, `AI_MODE=offline` responde pela camada analítica, **sem chamar
o provedor e sem consumir token nenhum**:

```bash
AI_MODE=offline python3 -m app.server
```

```powershell
$env:AI_MODE = "offline"; python -m app.server
```

`AI_MODE=offline` desliga **apenas a chamada ao provedor de IA**. A API analítica continua
servindo normalmente: KPIs, tendências, alertas e as seis frentes de negócio funcionam
igual. A aba "Perguntar" também continua inteira — sugestões, caixa de texto, carregamento
e renderização —, e a resposta traz os números reais do recorte. O que ela
não faz é interpretar a pergunta, e diz isso: a etiqueta mostra **"Modo offline · sem
consumo de tokens"** e a resposta vem marcada como **"Resposta local · sem IA"**.

Remova a variável para voltar a usar o provedor.

A chave nunca é gravada em arquivo nem enviada ao navegador: só o servidor fala com o
provedor.

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
| **Saúde do negócio** | Exibe os cinco KPIs executivos, filtros temporais e comparações por canal e categoria. Traz a navegação **Explorar por frente** com Geral, Vendas, Marketing, Estoque e Atendimento, sem sair da página. |
| **Evolução e tendências** | Permite alternar entre os cinco KPIs no tempo, comparar o período anterior e respeitar intervalos anuais, trimestrais, mensais e semanais. Aceita a navegação por frente, mostrando a série mensal dos KPIs da frente escolhida. |
| **Alertas prioritários** | Motor determinístico com seis famílias de regra (A01–A05 e Q01), materialidade, persistência e catálogo. Cada alerta abre evidência, limitações e leva ao recorte. O catálogo mostra também as famílias que não publicaram e por quê. |
| **Relatório executivo** | Monta o documento a partir da mesma camada analítica, respeitando os filtros: KPIs com período anterior, alertas publicados, leitura por canal e limites da edição. Botão **Gerar resumo em PDF** via impressão do navegador, sem biblioteca externa. |
| **Hipóteses e métricas** | Abriga a investigação com IA: hipóteses sugeridas para o recorte, caixa de pergunta livre e as leituras determinísticas por canal e categoria. O botão "Investigar com IA" leva a esta seção. |

## Seções e funcionalidades a implementar

| Seção ou funcionalidade | O que falta |
|---|---|
| **Alertas prioritários** | Os parâmetros vigentes foram calibrados sobre 2023 em 2026-09-20, não validados com usuários. Falta reconhecimento e silenciamento temporário com prazo e justificativa. |
| **Giro de estoque e venda perdida** | Dependem de histórico de posições de estoque, que a base não tem. Só a ruptura atual é calculável, e o card de giro foi removido da tela. |
| **Frente Cliente** | Removida em 2026-09-20: os pedidos se concentram em 325 clientes de 15.000 cadastrados, e LTV, churn e recompra descreveriam 2,2% da carteira. |
| **IA para investigação** | Ferramentas de leitura próprias: o gateway atual descarta as declaradas pelo cliente, então a IA recebe o recorte pré-calculado e não consulta a base por conta própria. Persistir o histórico de perguntas também fica pendente. |
| **Histórico de edições do relatório** | O relatório é montado sob demanda e não é persistido: reemitir produz outro documento, não uma edição rastreável com snapshot e filtros congelados. Falta também a síntese redigida pela IA, que `docs/07` admite sobre o template determinístico. |
| **Oportunidades, plano de ação e resultados** | As três seções foram **removidas da navegação em 2026-09-20**, a pedido. Eram demonstrativas e não persistiam nada. Retomá-las exige antes uma camada de gravação: ranking com critérios avaliados, ações com responsável e prazo, e intervenções reais para medir. |
| **Catálogo de hipóteses e KPIs na tela** | Os vereditos H01/H02/H07 e o dicionário de indicadores saíram da interface em 2026-09-20, quando a seção passou a ser a investigação com IA. Seguem em `docs/01` e `docs/02`. |
| **Governança e acesso** | Implementar autenticação, perfis de acesso, histórico de alterações e trilha de auditoria. |
| **Integrações** | Adicionar notificações e conexões com sistemas corporativos somente após validação do MVP. |

## Explorar por frente

A página Saúde do negócio alterna entre cinco lentes sobre o mesmo recorte, sem recarregar
e sem duplicar filtros:

| Frente | Pergunta | KPIs principais |
|---|---|---|
| **Geral** | Como está o negócio? | receita, margem absoluta, margem %, pedidos, ticket médio |
| **Vendas** | Estamos vendendo mais e com qualidade econômica? | receita, ticket, margem de contribuição, margem %, desconto |
| **Marketing** | Quais canais geram crescimento rentável? | custo por conversão, ROAS atribuído, conversão por clique, CTR, investimento |
| **Estoque** | Perdemos venda por indisponibilidade? | taxa de ruptura, SKUs em ruptura, SKUs no ponto de pedido |
| **Atendimento** | O atendimento opera dentro do nível de serviço? | SLA de primeira resposta, custo por ticket, volume, CSAT |

Os filtros globais continuam valendo. Quando um filtro não se aplica a uma frente —
período e canal em Estoque, canal e categoria em Atendimento — a tela avisa em vez de
ignorar em silêncio. Definição do SLA em
[`docs/16`](docs/16-frentes-de-negocio.md).

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
| `/api/alerts` | Alertas publicados, parâmetros vigentes e o catálogo das seis famílias com seu estado. |
| `/api/fronts` | Catálogo das frentes de negócio, com filtros aplicáveis e ignorados. |
| `/api/front/<id>` | KPIs e painéis de uma frente: `sales`, `marketing`, `inventory`, `support`. |
| `/api/ai/status` | Disponibilidade da IA e modelo em uso. Nunca devolve a credencial. |
| `/api/ai/suggestions` | Hipóteses sugeridas, derivadas do recorte. |
| `/api/ai/investigate` | `POST`. Recebe `{question, filters}` e devolve a resposta aterrada no recorte. |

## Testes

Para executar a suíte automatizada:

```powershell
python -m unittest discover -s tests -v
```

A suíte atual possui 80 testes para contratos analíticos, filtros, intervalos, integridade e
segurança da preparação dos dados, mais o contrato da investigação com IA — contexto,
sugestões, prompt e tratamento de falha do provedor. Nenhum teste chama o provedor.

## Frentes sem servidor

As cinco frentes novas exigem `app.server` no ar: elas calculam sob demanda, e o
`dados.js` estático só contém vendas agregadas. Abrir `index.html` sem processo nenhum
deixa apenas a aba Geral funcionando. **Decidido em 2026-09-20 não cobrir esse cenário** —
as alternativas custariam 5,83 MB a mais no payload e lógica de KPI duplicada em
JavaScript. Detalhes em [`docs/16`](docs/16-frentes-de-negocio.md).

Isso é independente de `AI_MODE=offline`, que desliga apenas a IA.

### Verificação da interface

A seção Evolução e tendências tem verificação automatizada em Chrome headless, que roda em
Linux. Com os dois servidores no ar:

```bash
node tools/verificar_tendencias.mjs
```

São 25 asserções sobre a tabela de valores, a cobertura da semana 53, a troca de
granularidade e as frentes de negócio nesta seção. Detalhes em [`docs/18`](docs/18-correcoes-tendencias.md).

## Solução de problemas

- **Dashboard mostra “Dados tratados — offline”**: confirme que a API está aberta em `http://127.0.0.1:8765/api/health`.
- **`/api/categories` retorna 404**: encerre uma possível API antiga com `Ctrl + C` e inicie novamente `python -m app.server`.
- **Porta 8765 ocupada**: execute `netstat -ano | Select-String ':8765'` e encerre o terminal antigo da API.
- **Alterações não aparecem**: reinicie a API e atualize o navegador com `Ctrl + F5`.
- **Erro ao preparar os dados**: confirme os nomes dos cinco arquivos dentro do diretório `Data`. Manifestos gerados no Windows são lidos normalmente em Linux desde 2026-09-20; ver [`docs/17`](docs/17-portabilidade-de-caminhos.md).
- **Aba "Perguntar" desabilitada**: `AI_API_KEY` não estava definida quando a API subiu. Defina a variável e reinicie `python -m app.server`. Para trabalhar sem credencial, use `AI_MODE=offline`.
- **"o provedor devolveu resposta vazia"**: o gateway injeta ferramentas próprias e o modelo às vezes as chama em vez de responder. Reformule a pergunta.

## Documentação

A documentação de escopo, arquitetura, métricas, rastreabilidade e plano de implementação está disponível em [`docs/`](docs/).
