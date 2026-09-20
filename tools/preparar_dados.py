"""Limpeza conservadora e auditavel. Somente biblioteca padrao do Python.

Leitura da copia de trabalho; publica um snapshot imutavel apos validacao.
Nao altera Data, backup, copia de entrada ou conclusoes das hipoteses.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'limpeza-v1'
KEYS = dict(vendas='order_id', clientes='customer_id', estoque='sku_id', marketing='campanha_id', atendimento='ticket_id')
NUMERIC = {
    'vendas': 'quantidade preco_unitario receita_bruta desconto_reais receita_liquida custo_produto custo_frete margem_contribuicao tempo_entrega_real'.split(),
    'clientes': 'renda_estimada total_pedidos_historico ltv_acumulado'.split(),
    'estoque': 'lead_time_reposicao custo_unitario preco_venda_sugerido estoque_fisico estoque_reservado estoque_disponivel ponto_pedido shelf_life_dias volume_m3'.split(),
    'marketing': 'investimento_reais impressoes cliques conversoes roas receita_gerada cac'.split(),
    'atendimento': 'nota_csat tempo_primeira_resposta_minutos custo_operacional_ticket'.split(),
}
INTEGER = set('quantidade tempo_entrega_real total_pedidos_historico lead_time_reposicao estoque_fisico estoque_reservado estoque_disponivel ponto_pedido shelf_life_dias impressoes cliques conversoes nota_csat tempo_primeira_resposta_minutos'.split())
TOLERANCE = Decimal('0.011')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decimal(value):
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('Numero invalido') from exc
    require(result.is_finite(), 'Numero nao finito')
    return result


def known_truncation(name, row, width):
    # Apenas registros fisicamente incompletos identificados na auditoria.
    return (name == 'vendas' and len(row) == 7 and row[0] == 'ORD-072219') or (
        name == 'atendimento' and len(row) == width and row[0] == 'TKT' and not any(row[1:]))


def read_dataset(path, name, expected_columns):
    records, quarantine, seen = [], [], set()
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.reader(handle, strict=True)
        columns = next(reader)
        require(columns == expected_columns, f'{name}: esquema diferente do perfil auditado')
        while True:
            first_line = reader.line_num + 1
            try:
                values = next(reader)
            except StopIteration:
                break
            if known_truncation(name, values, len(columns)):
                quarantine.append({'dataset': name, 'record_id': values[0], 'source_line_start': first_line,
                                   'source_line_end': reader.line_num, 'reason': 'truncamento_fisico_confirmado',
                                   'original_fields': values})
                continue
            require(len(values) == len(columns), f'{name}: quantidade de campos invalida na linha {first_line}')
            require(all(v != '' for v in values), f'{name}: ausente nao previsto na linha {first_line}')
            row = dict(zip(columns, values))
            key = row[KEYS[name]]
            require(key not in seen, f'{name}: chave duplicada na linha {first_line}')
            seen.add(key)
            for col in NUMERIC[name]:
                number = decimal(row[col])
                require(col == 'margem_contribuicao' or number >= 0, f'{name}.{col}: negativo inesperado na linha {first_line}')
                if col in INTEGER:
                    require(number == number.to_integral_value(), f'{name}.{col}: inteiro invalido')
            for col in columns:
                if col.startswith('data_'):
                    datetime.fromisoformat(row[col])
            if name == 'vendas':
                require(row['status_pagamento'] in {'Aprovado', 'Cancelado', 'Aguardando'}, 'Status financeiro nao previsto')
                require(row['devolvido'] in {'True', 'False'}, 'Booleano devolvido invalido')
            if name == 'clientes':
                require(row['opt_in_newsletter'] in {'True', 'False'}, 'Booleano opt-in invalido')
            if name == 'atendimento':
                require(1 <= decimal(row['nota_csat']) <= 5, 'CSAT fora da escala observada')
            row['_source_line'] = first_line
            records.append(row)
    return columns, records, quarantine


def verify_identities(tables):
    for row in tables['vendas']:
        n = lambda k: decimal(row[k])
        expected = {
            'receita_bruta': n('quantidade') * n('preco_unitario'),
            'receita_liquida': n('receita_bruta') - n('desconto_reais'),
            'margem_contribuicao': n('receita_liquida') - n('custo_produto') - n('custo_frete'),
        }
        for key, val in expected.items():
            require(abs(n(key) - val) <= TOLERANCE, f'vendas: identidade {key} divergente na linha {row["_source_line"]}')
    for row in tables['estoque']:
        require(decimal(row['estoque_disponivel']) == decimal(row['estoque_fisico']) - decimal(row['estoque_reservado']), 'Identidade de estoque divergente')
    for row in tables['marketing']:
        investment, conversions = decimal(row['investimento_reais']), decimal(row['conversoes'])
        require(investment > 0 and conversions > 0, 'Marketing: denominador nao positivo exige revisao')
        require(abs(decimal(row['roas']) - decimal(row['receita_gerada']) / investment) <= TOLERANCE, 'ROAS registrado inconsistente')
        require(abs(decimal(row['cac']) - investment / conversions) <= TOLERANCE, 'Proxy de custo por conversao inconsistente')


def quality_flags(tables):
    flags = []
    customers = {r['customer_id']: r for r in tables['clientes']}
    products = {r['sku_id']: r for r in tables['estoque']}
    sales = {r['order_id']: r for r in tables['vendas']}
    def add(name, row, rule, effect):
        flags.append({'dataset': name, 'record_id': row[KEYS[name]], 'source_line': row['_source_line'],
                      'rule': rule, 'effect': effect, 'record_preserved': True})
    for row in tables['vendas']:
        customer = customers.get(row['customer_id'])
        if not customer:
            add('vendas', row, 'cliente_sem_correspondencia', 'bloquear_integracao_cliente')
        elif datetime.fromisoformat(row['data_pedido']) < datetime.fromisoformat(customer['data_cadastro']):
            add('vendas', row, 'venda_antes_cadastro', 'nao_usar_cadastro_como_data_de_aquisicao')
        product = products.get(row['sku_id'])
        if not product:
            add('vendas', row, 'sku_sem_correspondencia', 'bloquear_integracao_estoque')
        elif row['categoria'] != product['categoria'] or row['produto'] != product['nome_produto']:
            add('vendas', row, 'sku_atributos_divergentes', 'revisar_integracao_estoque')
        if decimal(row['margem_contribuicao']) < 0:
            add('vendas', row, 'margem_negativa', 'preservar_perda_observada')
    for row in tables['atendimento']:
        if row['customer_id'] not in customers:
            add('atendimento', row, 'cliente_sem_correspondencia', 'bloquear_integracao_cliente')
        order = sales.get(row['order_id'])
        if not order:
            add('atendimento', row, 'pedido_sem_correspondencia', 'nao_usar_em_taxa_integrada_por_pedido')
        else:
            if row['customer_id'] != order['customer_id']:
                add('atendimento', row, 'cliente_pedido_divergente', 'bloquear_investigacao_integrada')
            if datetime.fromisoformat(row['data_abertura']) < datetime.fromisoformat(order['data_pedido']):
                add('atendimento', row, 'ticket_antes_pedido', 'bloquear_inferencia_temporal_ticket_pedido')
        if row['data_fechamento'] == '2025-12-31 23:59:00':
            add('atendimento', row, 'fechamento_provavel_sentinela', 'nao_usar_em_duracao_ate_confirmacao')
        if datetime.fromisoformat(row['data_fechamento']) < datetime.fromisoformat(row['data_abertura']):
            add('atendimento', row, 'fechamento_antes_abertura', 'bloquear_duracao')
    for row in tables['marketing']:
        if row['data_fim'] < row['data_inicio']:
            add('marketing', row, 'campanha_fim_antes_inicio', 'bloquear_comparacao_temporal')
    for row in tables['clientes']:
        if row['data_nascimento'] > row['data_cadastro']:
            add('clientes', row, 'nascimento_apos_cadastro', 'revisar_atributo_temporal')
    return flags


def sales_metrics(rows):
    revenue = sum((decimal(r['receita_liquida']) for r in rows), Decimal(0))
    margin = sum((decimal(r['receita_liquida']) - decimal(r['custo_produto']) - decimal(r['custo_frete']) for r in rows), Decimal(0))
    return {'orders': len(rows), 'revenue': str(revenue), 'margin': str(margin),
            'margin_pct': str(margin / revenue * 100) if revenue else None,
            'negative_margin_orders': sum(decimal(r['margem_contribuicao']) < 0 for r in rows)}


def csv_text(columns, rows):
    handle = io.StringIO(newline='')
    writer = csv.DictWriter(handle, fieldnames=columns, extrasaction='ignore', lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def verify_sources(root, manifest):
    for record in manifest['files']:
        for path in [root.parent / record['source'], root / record['backup'], root / record['working_copy']]:
            require(sha(path) == record['sha256'], f'Hash alterado: {path}')


def publish(root, snapshot, artifacts):
    base = root / 'data_processed'
    base.mkdir(exist_ok=True)
    target = base / snapshot
    if target.exists():
        expected = set(artifacts)
        require({p.name for p in target.iterdir()} == expected, 'Snapshot existente tem arquivos inesperados/ausentes')
        for filename, data in artifacts.items():
            require((target / filename).read_bytes() == data, f'Snapshot existente foi alterado: {filename}')
        return target, False
    staging = base / ('.pending-' + snapshot)
    staging.mkdir(exist_ok=False)
    for filename, data in artifacts.items():
        (staging / filename).write_bytes(data)
    staging.rename(target)
    return target, True


def main():
    manifest = json.loads((ROOT / 'docs/evidencias/backup-manifest.json').read_text(encoding='utf-8-sig'))
    profile = json.loads((ROOT / 'docs/evidencias/perfil-dados.json').read_text(encoding='utf-8'))
    verify_sources(ROOT, manifest)
    sources = {Path(r['working_copy']).stem: r for r in manifest['files']}
    signature = json_text({'version': VERSION, 'sources': {k: v['sha256'] for k, v in sorted(sources.items())}})
    snapshot = VERSION + '-' + hashlib.sha256(signature.encode()).hexdigest()[:12]
    schemas, tables, quarantine = {}, {}, []
    for name in KEYS:
        schema, records, rejected = read_dataset(ROOT / sources[name]['working_copy'], name, profile['datasets'][name]['columns'])
        schemas[name], tables[name] = schema, records
        for row in rejected:
            row['source_sha256'] = sources[name]['sha256']
        quarantine.extend(rejected)
    require(Counter(r['dataset'] for r in quarantine) == Counter(vendas=1, atendimento=1), 'A quarentena diverge dos dois casos auditados; revisar antes de publicar')
    for name in KEYS:
        require(len(tables[name]) + sum(r['dataset'] == name for r in quarantine) == profile['datasets'][name]['rows'], f'{name}: contagem difere da auditoria')
    verify_identities(tables)
    flags = quality_flags(tables)
    approved = [r for r in tables['vendas'] if r['status_pagamento'] == 'Aprovado']
    annual = [r for r in approved if r['data_pedido'][:4] == '2023']
    metrics = {'all_complete': sales_metrics(tables['vendas']), 'approved_all_dates': sales_metrics(approved), 'approved_2023': sales_metrics(annual)}
    require(metrics['approved_all_dates']['revenue'] == '16668956.49', 'Receita de aprovados nao reconcilia com a auditoria')
    require(metrics['approved_all_dates']['margin'] == '9058427.55', 'Margem de aprovados nao reconcilia com a auditoria')
    require(metrics['approved_2023']['revenue'] == '15966340.87', 'Receita anual nao reconcilia com o visual aprovado')
    counts = dict(sorted(Counter(f['rule'] for f in flags).items()))
    eligibility = [{'order_id': r['order_id'], 'source_line': r['_source_line'],
                    'financial_eligible': r['status_pagamento'] == 'Aprovado',
                    'dashboard_2023_eligible': r['status_pagamento'] == 'Aprovado' and r['data_pedido'][:4] == '2023',
                    'month_complete_for_comparison': r['data_pedido'][:4] == '2023'} for r in tables['vendas']]
    coverage = {}
    for name in KEYS:
        coverage[name] = {}
        for col in schemas[name]:
            if col.startswith('data_'):
                values = [r[col] for r in tables[name]]
                coverage[name][col] = {'min': min(values), 'max': max(values)}
    summary = {'snapshot': snapshot, 'pipeline_version': VERSION, 'sources_verified': 15,
               'datasets': {n: {'input_rows': profile['datasets'][n]['rows'], 'output_rows': len(tables[n]), 'quarantined_rows': sum(r['dataset'] == n for r in quarantine), 'columns': len(schemas[n])} for n in KEYS},
               'flags': counts, 'sales_status': dict(Counter(r['status_pagamento'] for r in tables['vendas'])),
               'coverage': coverage, 'metrics': metrics,
               'policy': 'Valores e colunas validos preservados; apenas truncamentos confirmados em quarentena. Flags nao corrigem datas nem removem registros.'}
    artifacts = {name + '.csv': csv_text(schemas[name], tables[name]).encode('utf-8-sig') for name in KEYS}
    artifacts['quarentena.jsonl'] = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in quarantine).encode('utf-8')
    artifacts['qualidade_flags.csv'] = csv_text(['dataset', 'record_id', 'source_line', 'rule', 'effect', 'record_preserved'], flags).encode('utf-8-sig')
    artifacts['vendas_elegibilidade.csv'] = csv_text(list(eligibility[0]), eligibility).encode('utf-8-sig')
    artifacts['resumo.json'] = json_text(summary).encode('utf-8')
    output_manifest = {'snapshot': snapshot, 'pipeline_version': VERSION,
                       'inputs': {n: {'working_copy': r['working_copy'], 'sha256': r['sha256']} for n, r in sources.items()},
                       'outputs': {n: {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)} for n, data in artifacts.items()}}
    artifacts['manifest.json'] = json_text(output_manifest).encode('utf-8')
    verify_sources(ROOT, manifest)
    target, created = publish(ROOT, snapshot, artifacts)
    # Ponteiro pequeno; reexecucao reutiliza o mesmo snapshot, sem novas copias.
    pointer = {'snapshot': snapshot, 'path': target.relative_to(ROOT).as_posix(),
               'manifest_sha256': sha(target / 'manifest.json')}
    pointer_path = ROOT / 'data_processed/current.json'
    pending_pointer = pointer_path.with_suffix('.tmp')
    pending_pointer.write_text(json_text(pointer), encoding='utf-8')
    pending_pointer.replace(pointer_path)
    evidence = ROOT / 'docs/evidencias'
    (evidence / 'limpeza-resumo.json').write_text(json_text(summary), encoding='utf-8')
    (evidence / 'limpeza-manifest.json').write_text(json_text(output_manifest), encoding='utf-8')
    verify_sources(ROOT, manifest)
    print(json_text({'snapshot': snapshot, 'created': created, 'datasets': summary['datasets'], 'flags': counts, 'metrics': metrics}))


if __name__ == '__main__':
    main()
