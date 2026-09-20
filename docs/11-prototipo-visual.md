# 11 — Protótipo visual do dashboard

Abrir [prototipo/index.html](prototipo/index.html) no navegador. Não exige servidor, rede, fontes remotas ou bibliotecas externas.

## Alteração de experiência

O wireframe longo anterior permanece como referência, mas a proposta visual atual usa uma seção por vez, menu lateral fixo, cards compactos, gráficos e detalhamento em painel lateral. A página inicial reúne cinco KPIs, evolução de receita/margem, participação de canais, achados e eficiência dos canais. A altura adapta-se à tela; em dispositivos menores, os gráficos se reorganizam sem acumular todas as seções em uma página.

## Interações disponíveis

- Navegar entre saúde, tendências, alertas, oportunidades, ações, resultados, hipóteses e relatório.
- Filtrar período, canal e categoria; cards, gráficos e detalhes comerciais usam o mesmo recorte.
- Clicar nos KPIs para consultar fórmula, valor preciso e limitações.
- Clicar em canais para consultar receita, margem, componentes e gap; aplicar o canal à investigação.
- Clicar em mês ou ponto do gráfico para abrir valores. A área de tendências também oferece tabela de valores mensais.
- Abrir achado, oportunidade e plano sem sair da tela; Escape ou botão de fechar encerra o painel.
- Consultar roteiro contextual da IA, identificado como demonstrativo, com números calculados localmente.
- Abrir explicitamente uma simulação de resultados; o estado inicial informa ausência de resultados reais.

## Dados e limites

Após a aprovação inicial do visual, o script `tools/preparar_dados_prototipo.py` passou a ler a versão tratada apontada por `data_processed/current.json`, validando hashes do manifesto e do CSV. Filtra aprovados em 2023 e produz 336 agregados por mês, canal e categoria em `docs/prototipo/dados.js`. Não modifica os CSVs nem cria outro backup. Receita anual: R$ 15.966.340,87; margem: R$ 8.675.612,00; pedidos: 23.388. Consulte a [preparação executada](12-preparacao-dados.md).

Gráfico temporal: barras de receita no eixo esquerdo; linha de margem % no eixo direito, de 0 a 100%. Participação usa receita do recorte. Benchmark de margem mantém todos os canais, preservando período e categoria. A comparação do ano completo não inventa dados de 2022; trimestre/mês usam o período anterior disponível.

Oportunidade e plano H02 são rascunhos globais com sua evidência de referência, não entidades reescritas pelos filtros. Resultados fictícios são isolados e explicitamente identificados. O relatório exibe apenas sua estrutura; não transforma números anuais em semanais. Nenhum texto demonstrativo deve ser tratado como resposta real de LLM.

O protótipo não implementa backend, persistência de ações, IA, envio de relatórios ou regras operacionais calibradas. O tratamento conservador dos dados foi implementado em etapa própria após a aprovação visual. SKU e outros domínios não têm filtros neste recorte visual. O cadastro de hipóteses preserva os vereditos anteriores.

Arquivos: `index.html` (estrutura), `visual.css` (design), `dashboard.js` (interações locais), `dados.js` (agregados históricos).
