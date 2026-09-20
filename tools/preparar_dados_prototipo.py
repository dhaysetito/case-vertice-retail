"""Agrega o snapshot tratado validado para o prototipo visual, sem alterar CSVs."""
from pathlib import Path
import hashlib
import json
import pandas as pd

root = Path(__file__).resolve().parents[1]
pointer_path = root / 'data_processed/current.json'
if not pointer_path.exists():
    raise RuntimeError('Execute primeiro: python tools/preparar_dados.py')
pointer = json.loads(pointer_path.read_text(encoding='utf-8'))
snapshot = (root / pointer['path']).resolve()
if not snapshot.is_relative_to((root / 'data_processed').resolve()):
    raise RuntimeError('Snapshot fora do diretorio tratado')
manifest_path = snapshot / 'manifest.json'
if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != pointer['manifest_sha256']:
    raise RuntimeError('Manifesto do snapshot alterado')
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
source = snapshot / 'vendas.csv'
expected_hash = manifest['outputs']['vendas.csv']['sha256']
if hashlib.sha256(source.read_bytes()).hexdigest() != expected_hash:
    raise RuntimeError('CSV tratado alterado; interrompida a atualizacao do dashboard')
df = pd.read_csv(source)
if df[['quantidade', 'receita_liquida', 'custo_produto', 'custo_frete']].isna().any().any():
    raise RuntimeError('Medidas ausentes na fonte tratada; nao descartar silenciosamente')
if df.order_id.duplicated().any():
    raise RuntimeError('Pedidos duplicados na fonte tratada')
df = df[df.status_pagamento.eq('Aprovado')].copy()
df['date'] = pd.to_datetime(df.data_pedido)
df = df[df.date.ge('2023-01-01') & df.date.lt('2024-01-01')].copy()
df['month'] = df.date.dt.month
df['week_start'] = df.date - pd.to_timedelta(df.date.dt.weekday, unit='D')
df['week'] = df.date.dt.isocalendar().week.astype(int)
df['margin'] = df.receita_liquida - df.custo_produto - df.custo_frete
rows = df.groupby(['month', 'canal', 'categoria']).agg(
    revenue=('receita_liquida', 'sum'), margin=('margin', 'sum'), orders=('order_id', 'nunique'),
    product=('custo_produto', 'sum'), freight=('custo_frete', 'sum'),
    discount=('desconto_reais', 'sum'), gross=('receita_bruta', 'sum')).reset_index()
weekly_rows = df.groupby(['week', 'week_start', 'canal', 'categoria']).agg(
    revenue=('receita_liquida', 'sum'), margin=('margin', 'sum'), orders=('order_id', 'nunique'),
    product=('custo_produto', 'sum'), freight=('custo_frete', 'sum'),
    discount=('desconto_reais', 'sum'), gross=('receita_bruta', 'sum')).reset_index()
daily_rows = df.groupby(['date', 'canal', 'categoria']).agg(
    revenue=('receita_liquida', 'sum'), margin=('margin', 'sum'), orders=('order_id', 'nunique'),
    product=('custo_produto', 'sum'), freight=('custo_frete', 'sum'),
    discount=('desconto_reais', 'sum'), gross=('receita_bruta', 'sum')).reset_index()
payload = {'source_sha256': manifest['inputs']['vendas']['sha256'],
           'processed_snapshot': pointer['snapshot'], 'processed_sha256': expected_hash, 'year': 2023,
           'channels': sorted(df.canal.unique().tolist()), 'categories': sorted(df.categoria.unique().tolist()),
           'rows': json.loads(rows.to_json(orient='records', force_ascii=False, double_precision=10)),
           'weekly_rows': json.loads(weekly_rows.to_json(orient='records', date_format='iso', force_ascii=False, double_precision=10)),
           'daily_rows': json.loads(daily_rows.to_json(orient='records', date_format='iso', force_ascii=False, double_precision=10))}
target = root / 'docs/prototipo'
target.mkdir(exist_ok=True)
(target / 'dados.js').write_text('window.VERTICE_DATA = ' + json.dumps(payload, ensure_ascii=False) + ';\n', encoding='utf-8')
if hashlib.sha256(source.read_bytes()).hexdigest() != expected_hash:
    raise RuntimeError('Fonte tratada foi alterada durante a leitura')
print(f'{len(rows)} agregados; receita={df.receita_liquida.sum():.2f}; margem={df.margin.sum():.2f}; pedidos={len(df)}')
