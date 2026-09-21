"""Contrato do motor de alertas, conforme docs/06-regras-decisao.md.

O que se protege aqui é o que transforma um painel de alertas em ruído: regra
que dispara sem materialidade, comparação contra base atípica vendida como
deterioração, família que some da tela sem dizer por que não foi avaliada, e
período anterior que não é o período anterior.
"""
import unittest

from app import alerts as motor
from app.alerts import Alerts
from app.analytics import Analytics, Query
from app.fronts import Fronts


class CalendarWindowTests(unittest.TestCase):
    """A interface manda `start`/`end`; sem normalizar, novembro compara com 02/10."""

    @classmethod
    def setUpClass(cls):
        cls.analytics = Analytics()

    def test_calendar_month_recognises_a_month_sent_as_a_window(self):
        self.assertEqual(self.analytics.calendar_month(Query(month=11)), 11)
        self.assertEqual(self.analytics.calendar_month(Query(start="2023-11-01", end="2023-12-01")), 11)
        self.assertEqual(self.analytics.calendar_month(Query(start="2023-12-01", end="2024-01-01")), 12)

    def test_calendar_month_is_none_for_windows_that_are_not_a_month(self):
        self.assertIsNone(self.analytics.calendar_month(Query()))
        self.assertIsNone(self.analytics.calendar_month(Query(start="2023-01-01", end="2024-01-01")))
        self.assertIsNone(self.analytics.calendar_month(Query(start="2023-10-05", end="2023-11-05")))

    def test_previous_period_of_a_month_is_the_previous_calendar_month(self):
        pelo_mes = self.analytics._previous_query(Query(month=11))
        pela_janela = self.analytics._previous_query(Query(start="2023-11-01", end="2023-12-01"))
        self.assertEqual(pelo_mes[1], "outubro de 2023")
        self.assertEqual(pela_janela[1], "outubro de 2023")
        # E os dois caminhos precisam medir o mesmo, não 30 dias contados para trás.
        self.assertEqual(self.analytics._aggregate(self.analytics._rows(pelo_mes[0]))["revenue"],
                         self.analytics._aggregate(self.analytics._rows(pela_janela[0]))["revenue"])

    def test_january_has_no_previous_period(self):
        self.assertIsNone(self.analytics._previous_query(Query(month=1)))


class CatalogTests(unittest.TestCase):
    """Família ausente da lista de alertas não é família aprovada."""

    @classmethod
    def setUpClass(cls):
        fronts = Fronts()
        cls.engine = Alerts(fronts.analytics, fronts)

    def estado(self, rule, query=Query()):
        return {r["id"]: r for r in self.engine.evaluate(query)["rules"]}[rule]

    def test_every_family_reports_its_state(self):
        rules = self.engine.evaluate()["rules"]
        self.assertEqual([r["id"] for r in rules], ["A01", "A02", "A03", "A04", "A05", "Q01"])
        self.assertTrue(all(r["state"] for r in rules))

    def test_a05_is_disabled_and_says_why(self):
        card = self.estado("A05")
        self.assertEqual(card["published"], 0)
        self.assertIn("desabilitada", card["state"])
        self.assertIn("não há ações registradas", card["state"])

    def test_a02_explains_the_absence_of_a_previous_period(self):
        self.assertIn("sem período anterior", self.estado("A02")["state"])

    def test_a03_reports_the_observed_loss_when_below_materiality(self):
        estado = self.estado("A03")
        self.assertEqual(estado["published"], 0)
        self.assertIn("414 pedidos", estado["state"])
        self.assertIn("R$ 5.571,63", estado["state"])
        self.assertIn("abaixo da materialidade", estado["state"])

    def test_a01_names_the_best_candidate_it_refused(self):
        # Em setembro nenhum gap atinge R$ 50 mil; dizer qual chegou mais perto
        # evita a leitura de que não existe gap nenhum.
        estado = self.estado("A01", Query(month=9))
        self.assertEqual(estado["published"], 0)
        self.assertIn("maior candidato abaixo da materialidade", estado["state"])
        self.assertIn("Marketplace", estado["state"])


class PublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fronts = Fronts()
        cls.engine = Alerts(fronts.analytics, fronts)

    def alerts_of(self, rule, query=Query()):
        return [a for a in self.engine.evaluate(query)["alerts"] if a["rule"] == rule]

    def test_a01_publishes_only_above_materiality(self):
        publicados = self.alerts_of("A01")
        self.assertEqual([a["entity"] for a in publicados], ["Marketplace"])
        self.assertGreaterEqual(publicados[0]["impact"], motor.MATERIALITY_BRL)
        # Lifestyle tem gap de 0,23 p.p. e R$ 7.483 de impacto: fica de fora.
        self.assertNotIn("Lifestyle", [a["entity"] for a in publicados])

    def test_a01_benchmark_excludes_the_entity_itself(self):
        alerta = self.alerts_of("A01")[0]
        rotulos = {e["rotulo"]: e["valor"] for e in alerta["evidence"]}
        self.assertAlmostEqual(rotulos["Gap"], rotulos["Consolidado comparável"] - rotulos["Margem de Marketplace"], places=9)

    def test_a02_fires_on_the_recalibrated_margin_threshold(self):
        # O limiar anterior de 1 p.p. nunca disparava: a maior queda é 0,89 p.p.
        novembro = self.alerts_of("A02", Query(month=11))
        self.assertTrue(any("Margem percentual" in a["title"] for a in novembro))
        self.assertTrue(any("outubro de 2023" in a["title"] for a in novembro))

    def test_a02_marks_a_one_off_drop_as_pontual(self):
        alerta = [a for a in self.alerts_of("A02", Query(month=11)) if "Margem percentual" in a["title"]][0]
        self.assertEqual(alerta["persistence"]["estado"], "pontual")
        self.assertEqual(alerta["persistence"]["janela"], motor.PERSISTENCE_WINDOW)

    def test_a04_publishes_the_dominant_support_theme(self):
        publicados = self.alerts_of("A04")
        self.assertEqual([a["entity"] for a in publicados], ["Onde está meu pedido?"])
        share = {e["rotulo"]: e["valor"] for e in publicados[0]["evidence"]}["Participação"]
        self.assertGreaterEqual(share, motor.SUPPORT_SHARE_PCT)

    def test_q01_is_informative_and_separate_from_financial_alerts(self):
        alerta = self.alerts_of("Q01")[0]
        self.assertEqual(alerta["severity"], "Informativa")
        self.assertIsNone(alerta["impact"])
        self.assertTrue(any("separado de oportunidade financeira" in l for l in alerta["limitations"]))

    def test_every_alert_carries_limitations(self):
        for alerta in self.engine.evaluate()["alerts"]:
            self.assertTrue(alerta["limitations"], alerta["rule"])
            self.assertTrue(alerta["explanation"], alerta["rule"])


class AtypicalBaseTests(unittest.TestCase):
    """Março, maio e novembro concentram ~2x a receita. Queda contra eles é reversão."""

    @classmethod
    def setUpClass(cls):
        fronts = Fronts()
        cls.engine = Alerts(fronts.analytics, fronts)
        cls.junho = [a for a in cls.engine.evaluate(Query(month=6))["alerts"] if a["rule"] == "A02"]

    def test_the_drop_is_still_published(self):
        # O fato é real: a receita caiu 56% contra maio. Esconder seria pior.
        self.assertTrue(any("Receita líquida" in a["title"] for a in self.junho))

    def test_severity_is_capped_and_the_reason_is_on_the_card(self):
        for alerta in self.junho:
            self.assertEqual(alerta["severity"], "Moderada")
            self.assertIn("base de comparação é atípica", alerta["explanation"])
            self.assertIn("maio de 2023", alerta["explanation"])
            self.assertTrue(any("atípica" in l for l in alerta["limitations"]))

    def test_a_typical_base_is_not_flagged(self):
        novembro = [a for a in self.engine.evaluate(Query(month=11))["alerts"] if a["rule"] == "A02"]
        self.assertTrue(novembro)
        for alerta in novembro:
            self.assertNotIn("atípica", alerta["explanation"])


class ParameterTests(unittest.TestCase):
    """Decisões do usuário em 2026-09-20; mudá-las é decisão dele, não do código."""

    def test_parameters_are_published_with_their_origin(self):
        parametros = motor.PARAMETERS
        self.assertEqual(parametros["materialidade_brl"], 50_000.0)
        self.assertEqual(parametros["queda_margem_pp"], -0.5)
        self.assertEqual(parametros["persistencia"], "2 de 3")
        self.assertIn("não é política aprovada da empresa", parametros["origem"])

    def test_severity_depends_on_materiality_and_persistence(self):
        # docs/06: severidade vem de materialidade e persistência, não da magnitude.
        self.assertEqual(motor._severity(2 * motor.MATERIALITY_BRL, True), "Crítica")
        self.assertEqual(motor._severity(2 * motor.MATERIALITY_BRL, False), "Alta")
        self.assertEqual(motor._severity(motor.MATERIALITY_BRL, True), "Alta")
        self.assertEqual(motor._severity(motor.MATERIALITY_BRL, False), "Moderada")

    def test_money_is_formatted_for_a_brazilian_reader(self):
        self.assertEqual(motor._brl(5571.63), "R$ 5.571,63")
        self.assertEqual(motor._brl(95333.87), "R$ 95.333,87")
        self.assertEqual(motor._num(-0.5, 1), "-0,5")


if __name__ == "__main__":
    unittest.main()
