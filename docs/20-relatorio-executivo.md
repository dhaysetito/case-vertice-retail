# 20 — Relatório executivo

Estado: **reconstruído em 2026-09-20**, com exportação em PDF.

## O que a auditoria encontrou

A seção era inteiramente estática. Quatro cartões descreviam o que *estaria* no relatório,
seguidos de um botão desabilitado. Nenhum número, e os filtros globais acima não tinham
efeito nenhum sobre ela.

| Achado | Gravidade |
|---|---|
| Zero dados reais: só texto descritivo de estrutura | a seção não cumpria o que `docs/07` pede — "montar automaticamente o documento com a mesma camada da interface" |
| Dois dos quatro blocos citavam **Oportunidades**, **Plano de ação** e **Resultado das ações** | as três foram removidas em 2026-09-20; o relatório prometia conteúdo inexistente |
| Texto falava em "semana" e mandava "selecionar uma semana completa" | o seletor de granularidade oferece ano, trimestre, mês e semana, e a seção ignorava a escolha |
| Botão "Geração semanal" desabilitado | sem caminho para produzir o documento |

## O que passou a existir

Quatro blocos montados da mesma camada analítica da interface, respeitando período,
canal e categoria:

| Bloco | Conteúdo | Origem |
|---|---|---|
| 01 Saúde do negócio | os cinco KPIs, período anterior e variação | agregado local |
| 02 O que merece atenção | alertas publicados com regra, severidade e impacto | `GET /api/alerts` |
| 03 Leitura por canal | receita, margem e gap contra o consolidado | agregado local |
| 04 Limites desta edição | limitações da margem, da observação e da cobertura do snapshot | fixas + Q01 do motor de alertas |

Capa com recorte, data de emissão, base tratada e população; rodapé repetindo a
identificação e a fórmula da margem.

### Divergência consciente com docs/07

`docs/07` exige que, sem fontes novas, o relatório indique **"edição sobre dados
históricos"**. O aviso existiu e foi **removido a pedido do usuário em 2026-09-20**.

A cobertura não ficou invisível: a capa mostra o recorte ("Ano completo · 2023"), o
cabeçalho e o rodapé identificam a base tratada, e o bloco 04 mantém as limitações. O que
saiu foi a frase explícita de que reemitir hoje não cria uma nova semana de desempenho.

Registrado aqui para que a ausência seja lida como decisão, não como esquecimento.

O relatório **sempre** mostra o período anterior, mesmo com o seletor "Comparação" em
"Sem comparação". Um documento que vai ser lido fora da tela precisa se contextualizar
sozinho.

## O PDF

Botão **"Gerar resumo em PDF"**. Usa `window.print()` com folha de impressão dedicada; o
navegador oferece "Salvar como PDF".

**Sem biblioteca externa**, de propósito: `docs/11` promete que o protótipo não exige
rede, fonte remota nem dependência, e `app/` é restrito à biblioteca padrão. Um gerador
de PDF em JavaScript viria de CDN, e um em Python exigiria reportlab — quando o projeto
já carrega pandas como dependência não declarada (risco 3).

A folha de impressão esconde menu lateral, topo, filtros, cabeçalho da página e as caixas
de instrução, deixando só o documento. Blocos não quebram no meio da página
(`break-inside: avoid`).

Verificado por `Page.printToPDF` no Chrome headless: arquivo válido de ~69 KB.

**Uma armadilha que custou uma correção:** a regra `footer{display:none}` da folha de
impressão escondia também o `<footer>` do próprio relatório. Agora é
`footer:not(.report-foot)`.

## Defeito corrigido junto

Os alertas do relatório não recarregavam ao mudar o filtro: `loadAlerts()` só era
disparado na seção Alertas. O relatório de novembro exibiria os alertas do ano inteiro,
lado a lado com KPIs de novembro. `render()` agora recarrega nas duas seções quando o
recorte muda.

## Verificação

`check-relatorio` — 21 asserções em Chrome headless: documento renderiza, texto de prévia
removido, sem menção às seções excluídas, valores exatos do recorte, marcação de edição
histórica, base identificada, quatro blocos, botão habilitado, troca de filtro alterando
números e alertas, cabeçalho refletindo o canal, folha de impressão escondendo a interface
e preservando o rodapé, e PDF válido gerado.

## Pendências

- **Histórico de edições.** `docs/07` pede que cada edição conserve semana de referência,
  snapshot, filtros e estado das ações no momento. Nada é persistido: reemitir produz
  outro documento, não uma nova edição rastreável.
- **Síntese redigida pela IA.** `docs/07` admite que a IA redija o texto, com o template
  funcionando também de forma determinística. Hoje só existe a versão determinística.
