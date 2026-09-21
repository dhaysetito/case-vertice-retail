# 19 — Motor de alertas

Estado: **implementado em 2026-09-20**. Substitui a versão anterior, que tinha uma regra
única escrita em JavaScript, sem materialidade, persistência nem catálogo.

## Onde vive

A avaliação é do servidor, em `app/alerts.py`, exposta por `GET /api/alerts`. Regra,
materialidade, persistência e severidade ficam num lugar só; a tela renderiza e explica.
Isso evita repetir em JavaScript a lógica que `docs/06` define — o risco 4 do bootstrap.

## As seis famílias

| ID | Família | Estado nesta base |
|---|---|---|
| **A01** | Gap material de margem | **ativa** — publica Marketplace no ano: 2,82 p.p. abaixo do consolidado, R$ 95.333,87 de impacto diagnóstico |
| **A02** | Deterioração temporal | **ativa** — dispara em fevereiro, julho, novembro e nos meses seguintes aos picos |
| **A03** | Perdas em pedidos | sem caso material: 414 pedidos com margem negativa somam R$ 5.571,63 |
| **A04** | Demanda repetitiva | **ativa** — "Onde está meu pedido?" concentra 30,5% dos tickets e R$ 54.371 de custo |
| **A05** | Guardrail após ação | **desabilitada** — não há ações registradas com KPI-alvo, baseline e tolerância |
| **Q01** | Qualidade e cobertura | **ativa** — informativa, separada da leitura financeira |

**O catálogo aparece inteiro na tela, sempre.** Uma família que não publicou pode não ter
sido avaliada, e a diferença importa para quem decide. `docs/06` é explícito: parâmetro
obrigatório ausente desabilita a regra **com explicação**, não em silêncio.

Quando A01 e A03 reprovam só por materialidade, a tela diz qual foi o maior candidato e
quanto ele somou. Sem isso, "nenhum alerta" se confunde com "nenhum gap".

## Parâmetros

Decisão do usuário em 2026-09-20, calibrada sobre 2023. **Não é política aprovada da
empresa** — a tela repete essa frase.

| Parâmetro | Valor | Por quê |
|---|---|---|
| Materialidade | R$ 50.000 | separa o achado real do ruído: publica Marketplace (R$ 95.334) e exclui Lifestyle (R$ 7.483) e Beleza (R$ 1.321), cujos gaps são de 0,23 e 0,03 p.p. |
| Queda de margem | −0,5 p.p. | o limiar anterior de 1 p.p. **nunca disparava**: a maior queda mensal de 2023 é 0,89 p.p. e a mediana é 0,18 p.p. |
| Queda de receita | −5% | mantido do desenho anterior |
| Participação de motivo | 25% | publica só o motivo dominante; o segundo tem 18,2% |
| Amostra mínima | 100 pedidos | piso técnico contra célula pequena. **Não é decisão de negócio**, é proteção de denominador |
| Persistência | 2 de 3 | não bloqueia a publicação: distingue queda **pontual** de **repetida** e eleva a severidade |

Severidade vem de materialidade e persistência, como `docs/06` pede — nunca da magnitude
sozinha. Crítica exige impacto ≥ 2× a materialidade **e** condição repetida.

## Base atípica

Março, maio e novembro de 2023 concentram cerca de duas vezes a receita dos demais meses.
Sem guarda, junho publicava **Crítica** por cair 56% contra maio — o que é reversão do
pico, não deterioração.

Quando o período anterior fica acima de 1,5× a mediana mensal do recorte, o alerta
**continua sendo publicado** — a queda é um fato — mas a severidade é limitada a Moderada
e o card diz quantas vezes a base excedeu a mediana. Esconder seria pior que explicar.

## O que a correção do período anterior destravou

A interface manda sempre `start`/`end`, nunca `month`. `Analytics._previous_query()` caía
no ramo de janela livre e calculava "30 dias antes": novembro comparava com **02/10 a
01/11** em vez de outubro. O rótulo na tela mostrava a data crua, o valor divergia do
mês-calendário e a persistência nem era avaliada.

`Analytics.calendar_month()` reconhece uma janela que é exatamente um mês do calendário.
A correção vale também para as **frentes de negócio** e para a **investigação com IA**,
que usam o mesmo método.

## Desempenho

Persistência e mediana pedem o mesmo mês várias vezes. Um cache por avaliação
(`Alerts._agg`, com `Query` congelado como chave) levou a rota de 1,9 s para cerca de 1 s.

## Seções removidas

`Oportunidades`, `Plano de ação` e `Resultado das ações` saíram da navegação em
2026-09-20, a pedido do usuário. Eram ilustrativas e não persistiam nada, o que deixava a
cadeia `Alerta → Oportunidade → Ação → Resultado` com três elos decorativos.

Consequência para os alertas: o botão "Investigar no recorte" leva a **Evolução e
tendências** ou à frente correspondente, nunca a uma oportunidade. A família **A05**
(guardrail após ação) continua desabilitada — agora por dois motivos, não um.

## Verificação

`tests/test_alerts.py` — 22 testes: normalização do mês de calendário, catálogo completo,
A05 desabilitada com motivo, A03 e A01 declarando o candidato reprovado, benchmark que
exclui a própria entidade, limiar recalibrado de margem, persistência pontual, motivo
dominante de atendimento, Q01 informativa, base atípica com severidade limitada, e a
tabela de severidade.

`check` de interface: 26 asserções em Chrome headless sobre publicação, catálogo, painel
de evidência, navegação para o recorte, estado vazio e base atípica.
