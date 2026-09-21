# 18 — Correções em Evolução e tendências

Estado: **corrigido em 2026-09-20**. Três defeitos de comportamento, nenhum deles
acompanhado de erro no console — por isso passaram despercebidos.

## 1. A tabela de valores dizia "mensais" exibindo dias

**Sintoma.** O detalhe "Consultar os valores mensais do gráfico" e a coluna `MÊS`
apareciam em qualquer granularidade. Em mês, listava 30 linhas rotuladas `1, 2, 3…`
debaixo de "MÊS"; em semana, 7 linhas com o dia do mês.

**Causa.** O texto e o cabeçalho eram literais fixos em `trends()`, enquanto a série
vinha de `dailySeries()` para mês e semana.

**Correção.** O rótulo segue a granularidade: mensais/`MÊS` em ano e trimestre,
diários/`DIA` em mês e semana. A tabela passou a usar `displaySeries()`, a mesma fonte do
gráfico — antes usava `series()`, e em ano/trimestre o gráfico podia vir da API enquanto a
tabela vinha do agregado local.

## 2. A semana 53 desenhava dias fora da cobertura

**Sintoma.** A semana 53 ia de 31/12/2023 a 06/01/2024. Como a base termina em 31/12, o
gráfico mostrava **um dia com dado e seis zerados**, indistinguíveis de dias sem venda. A
comparação contra a semana 52, essa completa, produzia uma queda de −51,3% que era só o
efeito da janela truncada. Os alertas prioritários usavam a mesma comparação.

**Causa.** As semanas do frontend são `1º de janeiro + 7 × (n−1)`; 53 × 7 = 371 dias,
então a última estoura o ano. `rangeFor()` devolvia o intervalo sem confrontar a cobertura.

**Correção.** `rangeFor()` corta o fim da semana em `COVERAGE_END` (2024-01-01). O
predicado `weekPartial()` identifica a janela truncada e, nela:

- `previous()`, `comparisonSeries()` e `alertPrevious()` devolvem vazio — comparar um dia
  com sete não é comparação;
- o painel de evolução exibe um aviso explicando a cobertura;
- a opção no seletor passa a se chamar "Semana 53 · 31 a 31 Dez · parcial".

O KPI mostra "Sem base no período anterior", e os alertas passam a reportar "Base de
comparação: indisponível" em vez de uma queda inventada.

## 3. Trocar de granularidade jogava o usuário para o fim do ano

**Sintoma.** Estando em julho e mudando para trimestre, a tela ia para o **trimestre 4**.
De qualquer granularidade para mês, ia para dezembro.

**Causa.** `syncPeriods()` fazia `state.period = options[options.length - 1][0]` quando o
valor anterior não existia na nova lista — sempre o último.

**Correção.** `periodGrain()` infere a granularidade pelo formato do valor
(`2023` | `2023-Q3` | `2023-07` | `2023-W30`), e `syncPeriods()` escolhe a opção cujo
intervalo **contém o início do recorte anterior**. Julho passa a virar trimestre 3, e
trimestre 3 volta para julho.

## 4. As frentes de negócio não eram selecionáveis aqui

**Sintoma.** Os chips "Explorar por frente" só apareciam na Saúde do negócio.

**Causa.** Escolha da implementação original, que seguiu o pedido ao pé da letra — a
navegação foi especificada "logo abaixo do título Saúde do negócio".

**Correção.** `FRONT_SECTIONS` passou a listar `saude` e `tendencias`. Em Tendências a
frente tem leitura própria (`frontTrendView()`): os mesmos cards de KPI, mais um gráfico
da série mensal de 2023 com seletor de KPI e a tabela dos doze meses. A frente escolhida
sobrevive à troca de seção.

Estoque não tem série temporal, então ali a frente explica o motivo em vez de desenhar um
gráfico vazio.

## Descartado na investigação

Duas suspeitas não se confirmaram e ficam registradas para ninguém refazer o caminho:

- **Clique nas marcas do gráfico.** Parecia não abrir o detalhe, mas `.click()` não
  dispara em elemento SVG. Com `MouseEvent` real, abre corretamente: em mês abre o dia, em
  ano abre o mês.
- **Divergência entre gráfico e tabela.** A comparação acusava diferença, mas era ruído de
  ponto flutuante entre o `Decimal` do Python e o `float` do JavaScript, além da precisão
  exibida.

## Pendência conhecida

A grade semanal do Python e a do JavaScript **não coincidem**: `Analytics.trend()` ancora
na segunda-feira e produz 52 semanas ISO; o frontend usa 1º de janeiro + 7n e produz 53.
Hoje isso não aparece, porque `normalizeApi()` descarta a série da API em granularidade
semanal e o frontend calcula localmente. Ligar a semana da API à tela sem unificar a grade
mostraria valores diferentes para o mesmo rótulo. Registrado em `.claude/project/risks.md`.

## Verificação

`tools/verificar_tendencias.mjs` cobre as três correções em Chrome headless, e roda em
Linux — diferente de `verificar_prototipo.mjs`, que fixa o caminho do Edge no Windows.

```bash
python3 -m app.server                                   # terminal 1
python3 -m http.server 8000 --directory docs/prototipo  # terminal 2
node tools/verificar_tendencias.mjs                     # terminal 3
```

25 verificações, todas passando. A suíte Python (58 testes) e as verificações das frentes
e da investigação com IA seguem verdes.
