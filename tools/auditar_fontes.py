"""Auditoria documental: copia fontes sem sobrescrever e perfila CSVs em memoria.

Nao limpa dados nem implementa a aplicacao. Executar da raiz do repositorio.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['vendas', 'clientes', 'estoque', 'marketing', 'atendimento']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = ROOT / 'backups' / stamp
    working = ROOT / 'data_work' / stamp
    docs = ROOT / 'docs' / 'evidencias'
    docs.mkdir(parents=True, exist_ok=True)
    sources = {'projeto_Data': ROOT / 'Data'}
    manifest = {'created_utc': stamp, 'files': [], 'working_copy': str(working.relative_to(ROOT)),
                'cleaning_applied': False}
    for label, folder in sources.items():
        for name in NAMES:
            source = folder / f'{name}.csv'
            before = sha(source)
            target = backup / label / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open('rb') as src, target.open('xb') as dst:
                shutil.copyfileobj(src, dst)
            assert sha(target) == before == sha(source), source
            record = {'source': str(source.relative_to(ROOT.parent)),
                      'backup': str(target.relative_to(ROOT)), 'bytes': source.stat().st_size,
                      'sha256': before, 'verified': True}
            if label == 'projeto_Data':
                working.mkdir(parents=True, exist_ok=True)
                copy = working / source.name
                with source.open('rb') as src, copy.open('xb') as dst:
                    shutil.copyfileobj(src, dst)
                assert sha(copy) == before
                record['working_copy'] = str(copy.relative_to(ROOT))
            manifest['files'].append(record)
    serialized = json.dumps(manifest, indent=2, ensure_ascii=False)
    (docs / 'backup-manifest.json').write_text(serialized, encoding='utf-8')
    (backup / 'manifest.json').write_text(serialized, encoding='utf-8')
    frames = {name: pd.read_csv(working / f'{name}.csv', dtype=str) for name in NAMES}
    profile = {'source_manifest': 'backup-manifest.json', 'datasets': {}}
    keys = dict(vendas='order_id', clientes='customer_id', estoque='sku_id', marketing='campanha_id', atendimento='ticket_id')
    for name, df in frames.items():
        dates = {}
        for col in df.columns:
            if col.startswith('data_'):
                parsed = pd.to_datetime(df[col], errors='coerce')
                dates[col] = {'min': str(parsed.min()), 'max': str(parsed.max()),
                              'invalid_nonempty': int((df[col].notna() & parsed.isna()).sum())}
        profile['datasets'][name] = {'rows': len(df), 'columns': list(df.columns),
            'nulls': {k:int(v) for k,v in df.isna().sum().items() if v},
            'duplicate_keys': int(df[keys[name]].duplicated().sum()),
            'duplicate_rows': int(df.duplicated().sum()), 'dates': dates}
    v = frames['vendas'].dropna(subset=['quantidade']).copy()
    a = frames['atendimento'].dropna(subset=['customer_id']).copy()
    c, e, m = (frames[n] for n in ['clientes', 'estoque', 'marketing'])
    n = lambda s: pd.to_numeric(s, errors='coerce')
    d = lambda s: pd.to_datetime(s, errors='coerce')
    av = a.merge(v[['order_id','customer_id','data_pedido']], on='order_id', suffixes=('_ticket','_venda'), validate='many_to_one')
    vc = v.merge(c[['customer_id','data_cadastro']], on='customer_id', validate='many_to_one')
    profile['relationships'] = {
        'sales_valid_rows': len(v), 'tickets_valid_rows': len(a),
        'sales_customers': int(v.customer_id.nunique()), 'ticket_customers': int(a.customer_id.nunique()),
        'ticket_order_unmatched': int((~a.order_id.isin(v.order_id)).sum()),
        'tickets_matched': len(av), 'ticket_before_order': int((d(av.data_abertura)<d(av.data_pedido)).sum()),
        'sale_before_customer_registration': int((d(vc.data_pedido)<d(vc.data_cadastro)).sum()),
        'ticket_customer_mismatch': int((av.customer_id_ticket != av.customer_id_venda).sum()),
        'sentinel_closure': int((a.data_fechamento=='2025-12-31 23:59:00').sum()),
        'sales_unknown_sku': int((~v.sku_id.isin(e.sku_id)).sum()),
        'sales_unknown_customer': int((~v.customer_id.isin(c.customer_id)).sum())}
    profile['sales_populations'] = {}
    for label, frame in [('all_complete',v), ('approved',v[v.status_pagamento=='Aprovado'])]:
        revenue = n(frame.receita_liquida).sum()
        margin = n(frame.receita_liquida).sum()-n(frame.custo_produto).sum()-n(frame.custo_frete).sum()
        market = frame[frame.canal=='Marketplace']
        mr, mm = n(market.receita_liquida).sum(), n(market.margem_contribuicao).sum()
        profile['sales_populations'][label] = {'rows':len(frame),'customers':int(frame.customer_id.nunique()),
            'revenue':float(revenue),'margin':float(margin),'margin_pct':float(margin/revenue),
            'marketplace_revenue':float(mr),'marketplace_margin':float(mm),'marketplace_margin_pct':float(mm/mr),
            'negative_margin_orders':int((n(frame.margem_contribuicao)<0).sum())}
    profile['checks'] = {
        'margin_identity_errors_gt_0011': int(((n(v.margem_contribuicao)-(n(v.receita_liquida)-n(v.custo_produto)-n(v.custo_frete))).abs()>.011).sum()),
        'stock_identity_errors':int((n(e.estoque_disponivel)!=n(e.estoque_fisico)-n(e.estoque_reservado)).sum()),
        'stock_zero_or_negative':int((n(e.estoque_disponivel)<=0).sum()),
        'stock_below_or_at_reorder':int((n(e.estoque_disponivel)<=n(e.ponto_pedido)).sum()),
        'ticket_cost_values':sorted(n(a.custo_operacional_ticket).unique().tolist()),
        'marketing_campaigns_contained_in_sales_window':int(((d(m.data_inicio)>=d(v.data_pedido).min().normalize()) & (d(m.data_fim)<=d(v.data_pedido).max().normalize())).sum())}
    (docs / 'perfil-dados.json').write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding='utf-8')
    for row in manifest['files']:
        assert sha(ROOT.parent / row['source']) == row['sha256']
    print(json.dumps({'backup': str(backup.relative_to(ROOT)), 'working':str(working.relative_to(ROOT)),
                      'backup_files': len(manifest['files']),
                      'relationships':profile['relationships'],'populations':profile['sales_populations'],
                      'checks':profile['checks']}, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
