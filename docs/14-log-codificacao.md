# Log de codificação

## Regra permanente

Os arquivos do dashboard devem ser gravados em **UTF-8**, sem conversão manual para Latin-1. A leitura e a escrita dos arquivos visuais devem preservar acentos, símbolos e caracteres portugueses.

## Correção aplicada

Em 2026-09-19, foram corrigidos trechos de mojibake nos arquivos `dashboard.js`, `index.html` e `dados.js`. Também foi criado o verificador `tools/verificar_codificacao.py`.

## Verificação

Executar antes de qualquer commit visual:

```powershell
python tools/verificar_codificacao.py
node --check docs/prototipo/dashboard.js
```

O verificador falha quando encontra sequências como `Ã`, `Â`, `â` ou `Î`, que indicam provável conversão incorreta de UTF-8.
