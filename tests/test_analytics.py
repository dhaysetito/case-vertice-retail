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

    def test_quarter_trend_contains_only_selected_months(self):
        data = self.analytics.trend(Query(grain="quarter", start="2023-04-01", end="2023-07-01"))
        self.assertEqual([point["month"] for point in data["points"]], [4, 5, 6])
        self.assertTrue(all(point["orders"] > 0 for point in data["points"]))

    def test_channels_have_same_population_and_share(self):
        data = self.analytics.channels()
        self.assertEqual(len(data["items"]), 7)
        self.assertAlmostEqual(sum(item["revenue_share_pct"] for item in data["items"]), 100, places=6)
        marketplace = next(item for item in data["items"] if item["channel"] == "Marketplace")
        self.assertAlmostEqual(marketplace["margin_pct"], 51.518849201, places=6)

    def test_channels_keep_comparison_when_one_channel_is_selected(self):
        data = self.analytics.channels(Query(channel="Marketplace"))
        self.assertEqual(len(data["items"]), 7)
        self.assertAlmostEqual(sum(item["revenue_share_pct"] for item in data["items"]), 100, places=6)
        self.assertEqual(data["context"]["channel"], "Marketplace")

    def test_categories_compare_all_values_and_respect_channel(self):
        data = self.analytics.categories(Query(channel="Marketplace", category="Beleza"))
        self.assertEqual(len(data["items"]), 4)
        self.assertAlmostEqual(sum(item["revenue_share_pct"] for item in data["items"]), 100, places=6)
        self.assertEqual(data["context"]["category"], "Beleza")

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
