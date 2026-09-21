"""Contrato das frentes de negócio da página Saúde do negócio.

O que se protege aqui é o que quebra em silêncio: KPI que reconcilia com a
camada canônica, direção correta de cada indicador (subir não é bom para custo
por conversão nem para ruptura), filtro que a frente não pode aplicar, e frente
ou KPI removido que precisa continuar removido.
"""
import unittest

from app.analytics import Analytics, Query
from app.fronts import SLA_TARGETS_MIN, Fronts


class FrontContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analytics = Analytics()
        cls.fronts = Fronts(cls.analytics)

    def cards(self, front, query=Query()):
        return {card["id"]: card for card in self.fronts.payload(front, query)["kpis"]}

    def test_every_front_answers_with_kpis_and_panels(self):
        for front in Fronts.FRONTS:
            payload = self.fronts.payload(front, Query(month=11))
            self.assertTrue(payload["kpis"], front)
            self.assertTrue(payload["panels"], front)
            self.assertTrue(payload["question"].endswith("?"), front)
            self.assertEqual(payload["scope"]["snapshot"], self.analytics.version)

    def test_unknown_front_is_refused(self):
        with self.assertRaisesRegex(ValueError, "frente não disponível"):
            self.fronts.payload("financeiro")

    def test_removed_fronts_and_kpis_stay_removed(self):
        # Cliente e giro de estoque saíram a pedido do usuário em 2026-09-20.
        self.assertEqual(list(Fronts.FRONTS), ["sales", "marketing", "inventory", "support"])
        with self.assertRaises(ValueError):
            self.fronts.payload("customer")
        self.assertNotIn("inventory_turn", self.cards("inventory"))

    def test_unknown_filter_is_not_silently_ignored(self):
        with self.assertRaisesRegex(ValueError, "canal não disponível"):
            self.fronts.payload("sales", Query(channel="Canal inexistente"))

    def test_sales_reconciles_with_the_canonical_layer(self):
        query = Query(month=11)
        cards = self.cards("sales", query)
        metrics = self.analytics.health(query)["metrics"]
        self.assertAlmostEqual(cards["revenue"]["value"], metrics["revenue"], places=6)
        self.assertAlmostEqual(cards["ticket"]["value"], metrics["ticket"], places=6)
        self.assertAlmostEqual(cards["margin"]["value"], metrics["margin"], places=6)

    def test_direction_marks_what_is_good(self):
        # Subir é bom para receita; é ruim para custo por conversão, ruptura
        # e custo por ticket. Sem isso a seta verde mente.
        self.assertEqual(self.cards("sales")["revenue"]["direction"], "up_good")
        self.assertEqual(self.cards("marketing")["cost_per_conversion"]["direction"], "down_good")
        self.assertEqual(self.cards("inventory")["stockout_rate"]["direction"], "down_good")
        self.assertEqual(self.cards("support")["cost_per_ticket"]["direction"], "down_good")
        self.assertEqual(self.cards("sales")["discount_pct"]["direction"], "neutral")

    def test_fronts_declare_the_filters_they_cannot_honour(self):
        inventory = self.fronts.payload("inventory")["scope"]
        self.assertIn("período", inventory["filters_ignored"])
        self.assertIn("canal", inventory["filters_ignored"])
        support = self.fronts.payload("support")["scope"]
        self.assertIn("canal", support["filters_ignored"])
        sales = self.fronts.payload("sales")["scope"]
        self.assertEqual(sales["filters_ignored"], [])

    def test_inventory_has_no_previous_period_because_it_is_a_snapshot(self):
        payload = self.fronts.payload("inventory", Query(month=11))
        self.assertIsNone(payload["scope"]["previous"])
        self.assertTrue(all(card["delta"] is None for card in payload["kpis"]))
        self.assertTrue(payload["warnings"])


class SalesCategoryPanelTests(unittest.TestCase):
    """Painel por categoria com seletor de KPI, como o da aba Geral."""

    @classmethod
    def setUpClass(cls):
        cls.analytics = Analytics()
        cls.fronts = Fronts(cls.analytics)
        cls.panels = {p["id"]: p for p in cls.fronts.payload("sales", Query(month=11))["panels"]}

    def test_sku_rankings_were_removed(self):
        self.assertNotIn("sales_best", self.panels)
        self.assertNotIn("sales_worst", self.panels)

    def test_category_panel_offers_every_front_kpi(self):
        panel = self.panels["sales_category"]
        self.assertEqual(panel["type"], "metric_bars")
        cards = [c["id"] for c in self.fronts.payload("sales", Query(month=11))["kpis"]]
        self.assertEqual([m["id"] for m in panel["metrics"]], cards)
        self.assertEqual(panel["default"], "revenue")

    def test_every_category_carries_every_metric(self):
        panel = self.panels["sales_category"]
        esperado = {m["id"] for m in panel["metrics"]}
        self.assertEqual(len(panel["items"]), 4)
        for item in panel["items"]:
            self.assertEqual(set(item["values"]), esperado, item["name"])

    def test_category_values_reconcile_with_the_canonical_layer(self):
        query = Query(month=11)
        panel = {p["id"]: p for p in self.fronts.payload("sales", query)["panels"]}["sales_category"]
        canonical = {item["category"]: item for item in self.analytics.categories(query)["items"]}
        for item in panel["items"]:
            reference = canonical[item["name"]]
            self.assertAlmostEqual(item["values"]["revenue"], reference["revenue"], places=6, msg=item["name"])
            self.assertAlmostEqual(item["values"]["margin_pct"], reference["margin_pct"], places=9, msg=item["name"])
            self.assertAlmostEqual(item["values"]["ticket"], reference["ticket"], places=6, msg=item["name"])


class DecisionTests(unittest.TestCase):
    """Parâmetros definidos pelo usuário em 2026-09-20; mudá-los é decisão dele."""

    @classmethod
    def setUpClass(cls):
        cls.fronts = Fronts()

    def test_sla_uses_a_target_per_channel(self):
        self.assertEqual(set(SLA_TARGETS_MIN), {"ChatBot", "WhatsApp", "Telefone", "E-mail", "Reclame Aqui"})
        card = {c["id"]: c for c in self.fronts.payload("support")["kpis"]}["sla"]
        self.assertIsNotNone(card["value"])
        self.assertIn("Meta por canal", card["note"])
        self.assertIn("não compromisso contratual", card["note"])
        # Uma meta que todo canal cumpre não informa nada; esta discrimina.
        self.assertLess(card["value"], 95)
        self.assertGreater(card["value"], 40)

    def test_sla_adherence_matches_a_manual_count(self):
        rows = self.fronts._tickets(Query())
        expected = sum(1 for row in rows
                       if float(row["tempo_primeira_resposta_minutos"]) <= SLA_TARGETS_MIN[row["canal_entrada"]])
        card = {c["id"]: c for c in self.fronts.payload("support")["kpis"]}["sla"]
        self.assertAlmostEqual(card["value"], expected / len(rows) * 100, places=9)


class ProxyNamingTests(unittest.TestCase):
    """docs/02 proíbe chamar de CAC e ROAS incremental o que é proxy declarado."""

    @classmethod
    def setUpClass(cls):
        cls.cards = {c["id"]: c for c in Fronts().payload("marketing")["kpis"]}

    def test_cost_per_conversion_is_not_called_cac(self):
        card = self.cards["cost_per_conversion"]
        self.assertEqual(card["label"], "Custo por conversão")
        self.assertIn("proxy", card["note"])

    def test_roas_states_it_is_attributed_and_not_incremental(self):
        card = self.cards["roas"]
        self.assertIn("atribuído", card["label"])
        self.assertIn("Sem incrementalidade", card["note"])


if __name__ == "__main__":
    unittest.main()
