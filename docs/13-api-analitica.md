# 13 — API analítica inicial

A primeira fatia funcional do backend está em `app/`. Ela consulta somente o snapshot apontado por `data_processed/current.json`, valida o hash do CSV e não altera arquivos.

## Iniciar localmente

Na raiz de `Case solution`:

```powershell
python -m app.server
```

O servidor fica em `http://127.0.0.1:8765`. Ele usa apenas a biblioteca padrão do Python; nenhuma dependência externa foi instalada.

## Rotas

| Rota | Uso |
|---|---|
| `/api/metadata` | snapshot, população, ano e dimensões suportadas |
| `/api/health` | KPIs executivos do contexto |
| `/api/trend` | pontos mensais de receita, margem, pedidos e ticket |
| `/api/channels` | canais, participação, receita e margem |
| `/api/evidence` | gap descritivo contra o consolidado e limitações |

Parâmetros opcionais: `year=2023`, `month=1..12`, `channel=Marketplace`, `category=Beleza`. Dimensões incompatíveis não são ignoradas: ano, canal e categoria fora do catálogo retornam HTTP 400 com uma mensagem explícita.

Exemplos:

```text
/api/health?year=2023&channel=Marketplace
/api/trend?year=2023&channel=Marketplace
/api/channels?year=2023&category=Beleza
/api/evidence?year=2023&channel=Marketplace
```

## Contrato da resposta

As respostas carregam `snapshot`, `population`, contexto temporal e filtros. KPIs usam razão de somas; `margin_pct` está em percentual (por exemplo, `54.3368`), enquanto variações para o usuário devem ser apresentadas em pontos percentuais. Valores ausentes aparecem como `null`, não zero artificial.

`/api/evidence` é descritiva: sua lista de limitações explicita que a margem disponível não é margem econômica completa, o gap não é saving e a observação não demonstra causalidade. A API não cria alertas, scores ou recomendações automáticas nesta fatia.

## Relação com a interface

O protótipo visual aprovado tenta chamar estas rotas para cards, série e canais quando a API estiver ativa. A cópia local continua como fallback para apresentação offline; o indicador no filtro mostra “API conectada · dados tratados” ou “Dados tratados · offline”. Detalhes ainda podem usar o agregado local enquanto a persistência completa não existe.

## Verificação

`tests/test_analytics.py` valida reconciliação com os totais aprovados, 12 pontos mensais, sete canais, filtros combináveis e limitações da evidência. Os testes de limpeza continuam cobrindo preservação dos originais e idempotência do snapshot.
