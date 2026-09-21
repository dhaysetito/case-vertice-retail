"""Contrato da investigação com IA.

Nenhum teste chama o provedor: rede em suíte é lenta, cara e falha por motivo
alheio ao código. O que se protege aqui é o que quebra em silêncio — o contexto
que aterra o modelo, o bloco de texto enviado e o tratamento de falha.
"""
import json
import os
import unittest
import urllib.error
from unittest import mock

from app import ai
from app.analytics import Analytics, Query


class InvestigationContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analytics = Analytics()

    def test_context_carries_every_channel_and_category_and_twelve_months(self):
        context = self.analytics.investigation_context(Query(channel="Marketplace"))
        self.assertEqual(len(context["channels"]), 7)
        self.assertEqual(len(context["categories"]), 4)
        self.assertEqual([point["month"] for point in context["trend"]], list(range(1, 13)))

    def test_context_numbers_match_the_canonical_layer(self):
        query = Query(month=11)
        context = self.analytics.investigation_context(query)
        health = self.analytics.health(query)["metrics"]
        self.assertEqual(context["totals"]["orders"], health["orders"])
        self.assertAlmostEqual(context["totals"]["margin_pct"], health["margin_pct"], places=9)

    def test_previous_period_includes_channel_breakdown(self):
        context = self.analytics.investigation_context(Query(month=11))
        previous = context["previous"]
        self.assertEqual(previous["label"], "outubro de 2023")
        self.assertEqual(len(previous["channels"]), 7)
        october = self.analytics.channels(Query(month=10))["items"]
        self.assertEqual({item["channel"] for item in previous["channels"]},
                         {item["channel"] for item in october})

    def test_january_and_full_year_have_no_previous_period(self):
        self.assertIsNone(self.analytics.investigation_context(Query(month=1))["previous"])
        self.assertIsNone(self.analytics.investigation_context(Query())["previous"])

    def test_scope_label_is_readable_by_a_person(self):
        # O rótulo aparece na tela e dentro da resposta da IA; data ISO crua vaza ali.
        label = self.analytics.scope_label
        self.assertEqual(label(Query()), "2023 completo · todos os canais · todas as categorias")
        self.assertEqual(label(Query(start="2023-01-01", end="2024-01-01")),
                         "2023 completo · todos os canais · todas as categorias")
        self.assertEqual(label(Query(start="2023-12-01", end="2024-01-01")),
                         "dezembro de 2023 · todos os canais · todas as categorias")
        self.assertEqual(label(Query(month=11, channel="Marketplace")),
                         "novembro de 2023 · Marketplace · todas as categorias")
        self.assertIn("03/04/2023 a 09/04/2023", label(Query(start="2023-04-03", end="2023-04-10")))

    def test_context_rejects_unknown_filter_like_the_rest_of_the_api(self):
        with self.assertRaisesRegex(ValueError, "canal não disponível"):
            self.analytics.investigation_context(Query(channel="Canal inexistente"))


class SuggestionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analytics = Analytics()

    def test_suggestions_are_questions_derived_from_the_slice(self):
        items = self.analytics.suggestions(Query(month=11))
        self.assertGreaterEqual(len(items), 3)
        self.assertTrue(all(item["question"].endswith("?") for item in items))
        self.assertTrue(any("Marketplace" in item["question"] for item in items))

    def test_suggestions_use_brazilian_decimals(self):
        question = self.analytics.suggestions(Query(month=11))[0]["question"]
        self.assertRegex(question, r"\d+,\d{2}%")
        self.assertNotRegex(question, r"\d+\.\d{2}%")

    def test_comparison_suggestion_only_when_there_is_a_previous_period(self):
        with_previous = [item["id"] for item in self.analytics.suggestions(Query(month=11))]
        without_previous = [item["id"] for item in self.analytics.suggestions(Query(month=1))]
        self.assertIn("variacao_periodo", with_previous)
        self.assertNotIn("variacao_periodo", without_previous)


class DataBlockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = Analytics().investigation_context(Query(month=11))

    def test_block_states_snapshot_population_and_limitations(self):
        block = ai.render_data_block(self.context)
        self.assertIn(self.context["scope"]["snapshot"], block)
        self.assertIn("Aprovado; medidas completas", block)
        self.assertIn("não demonstra causalidade", block)

    def test_block_carries_preserved_study_verdicts(self):
        block = ai.render_data_block(self.context)
        self.assertIn("H01 — Refutada", block)
        self.assertIn("H02 — Validada", block)

    def test_instruction_forbids_web_and_causal_claims(self):
        message = ai.build_messages("a margem caiu?", self.context)[0]
        # Tudo vai na mensagem do usuário: o gateway sobrepõe a mensagem system.
        self.assertEqual(message["role"], "user")
        self.assertIn("Não busque na web", message["content"])
        self.assertIn("Nunca afirme causa", message["content"])
        self.assertIn("PERGUNTA DO GESTOR: a margem caiu?", message["content"])


class OfflineModeTests(unittest.TestCase):
    """AI_MODE=offline responde sem provedor: serve para trabalhar sem gastar token."""

    @classmethod
    def setUpClass(cls):
        cls.analytics = Analytics()
        cls.context = cls.analytics.investigation_context(Query(month=11))

    def test_offline_mode_reports_itself_and_needs_no_credential(self):
        with mock.patch.dict(os.environ, {"AI_MODE": "offline", "AI_API_KEY": ""}):
            self.assertEqual(ai.mode(), "offline")
            status = ai.status()
            self.assertTrue(status["available"])
            self.assertEqual(status["mode"], "offline")
            self.assertIsNone(status["host"])

    def test_offline_never_touches_the_network(self):
        with mock.patch.dict(os.environ, {"AI_MODE": "offline", "AI_API_KEY": "sk-teste"}), \
                mock.patch("urllib.request.urlopen", side_effect=AssertionError("provedor foi chamado")):
            result = ai.ask("a margem caiu?", self.context)
        self.assertEqual(result["mode"], "offline")
        self.assertEqual(result["usage"], {"prompt_tokens": 0, "completion_tokens": 0})

    def test_offline_answer_says_it_is_not_ai(self):
        answer = ai.offline_answer("a margem caiu?", self.context)
        self.assertIn("Modo offline", answer)
        self.assertIn("nenhum modelo interpretou a sua pergunta", answer)
        self.assertIn("a margem caiu?", answer)

    def test_offline_answer_keeps_the_five_block_format(self):
        answer = ai.offline_answer("qualquer", self.context)
        for heading in ["## Pergunta", "## Fatos", "## Inferências", "## Limitações",
                        "## Próxima investigação"]:
            self.assertIn(heading, answer)

    def test_offline_numbers_come_from_the_canonical_layer(self):
        answer = ai.offline_answer("qualquer", self.context)
        metrics = self.analytics.health(Query(month=11))["metrics"]
        self.assertIn(f"{metrics['margin_pct']:.2f}".replace(".", ",") + "%", answer)
        self.assertIn("3.641", answer)  # pedidos de novembro, formato brasileiro

    def test_offline_omits_the_gap_when_the_slice_is_the_consolidated(self):
        # Sem filtro de canal ou categoria o gap é zero por definição.
        whole = self.analytics.investigation_context(Query(month=11))
        self.assertNotIn("Gap contra o consolidado", ai.offline_answer("x", whole))
        sliced = self.analytics.investigation_context(Query(month=11, channel="Marketplace"))
        self.assertIn("Gap contra o consolidado", ai.offline_answer("x", sliced))

    def test_auto_mode_still_uses_the_provider_when_there_is_a_key(self):
        with mock.patch.dict(os.environ, {"AI_MODE": "auto", "AI_API_KEY": "sk-teste"}):
            self.assertEqual(ai.mode(), "provider")
        with mock.patch.dict(os.environ, {"AI_MODE": "auto", "AI_API_KEY": ""}):
            self.assertEqual(ai.mode(), "unavailable")


class ProviderFailureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = Analytics().investigation_context(Query())

    def test_missing_credential_is_reported_not_guessed(self):
        with mock.patch.dict(os.environ, {"AI_API_KEY": ""}):
            self.assertFalse(ai.available())
            self.assertFalse(ai.status()["available"])
            with self.assertRaisesRegex(ai.AIError, "AI_API_KEY"):
                ai.ask("qualquer pergunta", self.context)

    def test_status_never_leaks_the_credential(self):
        with mock.patch.dict(os.environ, {"AI_API_KEY": "sk-segredo-nao-pode-vazar"}):
            self.assertNotIn("sk-segredo-nao-pode-vazar", json.dumps(ai.status()))

    def test_empty_and_blank_questions_are_refused_before_any_request(self):
        with mock.patch.dict(os.environ, {"AI_API_KEY": "sk-teste"}):
            for question in ["", "   "]:
                with self.assertRaises(ValueError):
                    ai.ask(question, self.context)
            with self.assertRaisesRegex(ValueError, "acima de"):
                ai.ask("x" * (ai.MAX_QUESTION + 1), self.context)

    def test_provider_http_error_does_not_echo_its_body(self):
        error = urllib.error.HTTPError("https://provedor/x", 500, "erro", {}, None)
        with mock.patch.dict(os.environ, {"AI_API_KEY": "sk-teste"}), \
                mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaisesRegex(ai.AIError, "HTTP 500"):
                ai.ask("a margem caiu?", self.context)

    def test_empty_answer_is_an_error_not_a_blank_screen(self):
        payload = json.dumps({"choices": [{"message": {"content": "",
                                                       "tool_calls": [{"function": {"name": "web_search"}}]}}]})
        response = mock.MagicMock()
        response.read.return_value = payload.encode("utf-8")
        response.__enter__.return_value = response
        with mock.patch.dict(os.environ, {"AI_API_KEY": "sk-teste"}), \
                mock.patch("urllib.request.urlopen", return_value=response):
            with self.assertRaisesRegex(ai.AIError, "resposta vazia"):
                ai.ask("a margem caiu?", self.context)

    def test_successful_answer_carries_scope_and_grounding(self):
        payload = json.dumps({"choices": [{"message": {"content": "## Pergunta\nok"}}],
                              "model": "gpt-5.5", "usage": {"prompt_tokens": 10, "completion_tokens": 2}})
        response = mock.MagicMock()
        response.read.return_value = payload.encode("utf-8")
        response.__enter__.return_value = response
        with mock.patch.dict(os.environ, {"AI_API_KEY": "sk-teste"}), \
                mock.patch("urllib.request.urlopen", return_value=response):
            result = ai.ask("a margem caiu?", self.context)
        self.assertEqual(result["model"], "gpt-5.5")
        self.assertEqual(result["scope"]["snapshot"], self.context["scope"]["snapshot"])
        self.assertIn("não consulta dados por conta própria", result["grounding"])


if __name__ == "__main__":
    unittest.main()
