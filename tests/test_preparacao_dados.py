"""Protecoes relevantes da limpeza: exclusoes, integridade e preservacao."""
import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('preparar', ROOT / 'tools/preparar_dados.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class CleaningSafetyTests(unittest.TestCase):
    def test_only_confirmed_truncations_are_recognized(self):
        self.assertTrue(p.known_truncation('vendas', ['ORD-072219'] + ['x'] * 6, 20))
        self.assertTrue(p.known_truncation('atendimento', ['TKT'] + [''] * 11, 12))
        self.assertFalse(p.known_truncation('vendas', ['ORD-999999'] + ['x'] * 6, 20))
        self.assertFalse(p.known_truncation('atendimento', ['TKT', 'CLI-00001'] + [''] * 10, 12))

    def test_unexpected_missing_values_fail_without_silent_drop(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'vendas.csv'
            path.write_text('order_id,quantidade\nORD-000001,\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'ausente nao previsto'):
                p.read_dataset(path, 'vendas', ['order_id', 'quantidade'])

    def test_duplicate_key_fails(self):
        current = json.loads((ROOT / 'data_processed/current.json').read_text(encoding='utf-8'))
        with (ROOT / current['path'] / 'vendas.csv').open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.reader(handle)
            header, valid = next(reader), next(reader)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'vendas.csv'
            with path.open('w', encoding='utf-8', newline='') as handle:
                writer = csv.writer(handle); writer.writerows([header, valid, valid])
            with self.assertRaisesRegex(ValueError, 'duplicada'):
                p.read_dataset(path, 'vendas', header)

    def test_financial_inconsistency_fails(self):
        sale = dict(quantidade='1', preco_unitario='100.00', receita_bruta='100.00',
                    desconto_reais='10.00', receita_liquida='90.00', custo_produto='40.00',
                    custo_frete='10.00', margem_contribuicao='999.00', _source_line=2)
        with self.assertRaisesRegex(ValueError, 'margem_contribuicao'):
            p.verify_identities({'vendas': [sale], 'estoque': [], 'marketing': []})

    def test_nonfinite_numbers_fail(self):
        for value in ['NaN', 'Infinity', '-Infinity']:
            with self.assertRaises(ValueError):
                p.decimal(value)

    def test_snapshot_reuse_and_tampering_protection(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target, created = p.publish(root, 'teste', {'vendas.csv': b'original'})
            self.assertTrue(created)
            self.assertFalse(p.publish(root, 'teste', {'vendas.csv': b'original'})[1])
            (target / 'vendas.csv').write_bytes(b'alterado')
            with self.assertRaisesRegex(ValueError, 'alterado'):
                p.publish(root, 'teste', {'vendas.csv': b'original'})
            self.assertEqual((target / 'vendas.csv').read_bytes(), b'alterado')

    def test_all_valid_fields_preserved_in_actual_snapshot(self):
        backup = json.loads((ROOT / 'docs/evidencias/backup-manifest.json').read_text(encoding='utf-8-sig'))
        current = json.loads((ROOT / 'data_processed/current.json').read_text(encoding='utf-8'))
        for entry in backup['files']:
            name = Path(entry['working_copy']).stem
            with (ROOT / entry['working_copy']).open(encoding='utf-8-sig', newline='') as handle:
                reader = csv.reader(handle); header = next(reader)
                original = [r for r in reader if not p.known_truncation(name, r, len(header))]
            with (ROOT / current['path'] / (name + '.csv')).open(encoding='utf-8-sig', newline='') as handle:
                reader = csv.reader(handle)
                self.assertEqual(next(reader), header)
                self.assertEqual(list(reader), original, name)
        p.verify_sources(ROOT, backup)

    def test_financial_filter_is_not_a_cleaning_exclusion(self):
        current = json.loads((ROOT / 'data_processed/current.json').read_text(encoding='utf-8'))
        summary = json.loads((ROOT / current['path'] / 'resumo.json').read_text(encoding='utf-8'))
        self.assertEqual(summary['sales_status'], {'Aprovado': 24454, 'Cancelado': 2207, 'Aguardando': 1097})
        self.assertEqual(summary['metrics']['approved_2023']['orders'], 23388)
        self.assertEqual(summary['metrics']['approved_2023']['margin'], '8675612.00')
        self.assertEqual(summary['metrics']['approved_2023']['negative_margin_orders'], 414)


if __name__ == '__main__':
    unittest.main()
