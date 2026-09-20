import unittest

from app.analytics import Analytics, Query


class AnalyticsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analytics = Analytics()

    def test_health_reconciles_dashboard(self):
        data = self.analytics.health()
        self.assertEqual(data["metrics"]["orders"], 23388)
        self.assertAlmostEqual(data["metrics"]["revenue"], 15966340.87, places=2)
        self.assertAlmostEqual(data["metrics"]["margin"], 8675612.00, places=2)

    def test_trend_has_full_year_and_month_context(self):
        data = self.analytics.trend()
        self.assertEqual(len(data["points"]), 12)
        december = data["points"][-1]
        self.assertEqual(december["month"], 12)
        self.assertGreater(december["orders"], 0)

    def test_channels_have_same_population_and_share(self):
        data = self.analytics.channels()
        self.assertEqual(len(data["items"]), 7)
        self.assertAlmostEqual(sum(item["revenue_share_pct"] for item in data["items"]), 100, places=6)
        marketplace = next(item for item in data["items"] if item["channel"] == "Marketplace")
        self.assertAlmostEqual(marketplace["margin_pct"], 51.518849201, places=6)

    def test_filters_are_composable(self):
        marketplace = self.analytics.health(Query(channel="Marketplace"))
        beauty = self.analytics.health(Query(category="Beleza"))
        self.assertEqual(marketplace["metrics"]["orders"], 5075)
        self.assertGreater(beauty["metrics"]["orders"], 0)

    def test_evidence_is_descriptive_and_has_limitations(self):
        evidence = self.analytics.evidence(Query(channel="Marketplace"))
        self.assertAlmostEqual(evidence["gap_margin_pp"], -2.818034, places=2)
        self.assertIn("gap diagnóstico não é saving", evidence["limitations"])

    def test_unknown_filter_is_not_silently_ignored(self):
        with self.assertRaisesRegex(ValueError, "canal não disponível"):
            self.analytics.health(Query(channel="Canal inexistente"))


if __name__ == "__main__":
    unittest.main()
