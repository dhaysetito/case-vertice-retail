# 17 — Portabilidade de caminhos entre Windows e Linux

Estado: **corrigido em 2026-09-20**.

## O sintoma

`python3 -m unittest discover -s tests` reprovava em Linux com um erro só:

```
FileNotFoundError: .../data_work\20260919T231914609851Z\vendas.csv
```

Mais grave que o teste: `tools/preparar_dados.py` lê os mesmos campos, então **o pipeline
de dados não era reexecutável fora do Windows**. A API e o dashboard seguiam funcionando
porque leem o snapshot já publicado via `data_processed/current.json`, que foi gravado
com `as_posix()`.

## A causa

`tools/auditar_fontes.py` gravava os caminhos do manifesto com `str(path.relative_to(...))`,
que usa o separador do sistema. Gerado no Windows, o manifesto ficou com
`data_work\<stamp>\vendas.csv`. Em Linux a barra invertida é caractere válido de nome de
arquivo, não separador — o caminho não resolve, e nenhum erro aparece até a leitura.

Inconsistência dentro do próprio código: o ponteiro do snapshot já usava `.as_posix()`.

## A correção, e por que não foi reescrever os manifestos

Duas frentes:

**1. Escrita nova em POSIX.** `auditar_fontes.py` passou a usar `.as_posix()` nos quatro
campos de caminho. Manifestos gerados daqui em diante resolvem nas duas plataformas.

**2. Leitura tolerante.** `preparar_dados.py` ganhou `local(root, recorded)`, que aceita
os dois separadores ao resolver um caminho gravado.

A tentação era normalizar os manifestos existentes. **Não dá**, e o motivo é a própria
invariante do projeto: `data_processed/<snapshot>/manifest.json` guarda esses caminhos, e
seu hash está registrado em `current.json`. Reescrevê-lo alteraria um snapshot declarado
imutável, e `publish()` acusaria adulteração na execução seguinte — corretamente.

Normalizar na leitura preserva o dado publicado e conserta o comportamento. O manifesto do
snapshot continua com barras invertidas, e isso é intencional.

## Onde a normalização foi aplicada

| Arquivo | Ponto |
|---|---|
| `tools/preparar_dados.py` | `verify_sources()`, a chave de `sources` e `read_dataset()` |
| `tests/test_preparacao_dados.py` | resolução da cópia de trabalho e do CSV tratado, e a derivação do nome do dataset |

`preparar_dados.py` preserva o valor original ao gravar o manifesto de saída — é o que
mantém a igualdade byte a byte com o snapshot já publicado.

## Verificação

`python3 tools/preparar_dados.py` executado em Linux devolveu `"created": false`: o
pipeline reencontrou o snapshot `limpeza-v1-2d6da7f3e091`, comparou **byte a byte** cada
artefato e não republicou. O `manifest_sha256` de `current.json` continua conferindo.

Os três arquivos regravados — `current.json`, `limpeza-manifest.json` e
`limpeza-resumo.json` — mudaram **apenas o fim de linha** (CRLF → LF); o conteúdo é
idêntico.

Suíte completa: 58 testes, todos passando. O portão `verify-done.sh` fechou **APROVADO**
pela primeira vez.
