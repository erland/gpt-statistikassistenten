import unittest

from scripts.source_planner import SourcePlannerError, plan_sources


class SourcePlannerTests(unittest.TestCase):
    def test_empty_question_rejected(self):
        with self.assertRaises(SourcePlannerError):
            plan_sources("   ")

    def test_scb_population(self):
        p = plan_sources("Hur har befolkningen i Sundsvalls kommun utvecklats sedan 2010?")
        self.assertEqual(p["status"], "ready")
        self.assertEqual(p["sources"], ["scb"])

    def test_bra_reported_crime(self):
        p = plan_sources("Hur har antalet anmälda bostadsinbrott utvecklats sedan 2015?")
        self.assertEqual(p["sources"], ["bra"])

    def test_comext_trade(self):
        p = plan_sources("Hur mycket exporterade Sverige av läkemedel till USA 2025?")
        self.assertEqual(p["sources"], ["comext"])
        self.assertTrue(any("Comext" in c for c in p["decision"]["conflicts"]) or p["decision"]["confidence"] == "high")

    def test_eurostat_country_comparison(self):
        p = plan_sources("Jämför arbetslösheten i EU-länderna under 2025")
        self.assertIn("eurostat", p["sources"])
        self.assertNotIn("comext", p["sources"])

    def test_combined_bra_and_scb_for_per_capita(self):
        p = plan_sources("Hur har anmälda bilstölder per 100 000 invånare utvecklats i Sundsvall?")
        self.assertEqual(p["sources"], ["bra", "scb"])
        self.assertEqual(p["steps"][-1]["id"], "combine-results")
        self.assertEqual(len(p["steps"][-1]["depends_on"]), 2)

    def test_combined_trade_and_gdp(self):
        p = plan_sources("Har Sveriges export till USA ökat snabbare än BNP sedan 2015?")
        self.assertEqual(set(p["sources"]), {"comext", "scb"})
        self.assertEqual(p["steps"][-1]["id"], "combine-results")

    def test_unknown_domain_requests_clarification(self):
        p = plan_sources("Hur har det förändrats de senaste åren?")
        self.assertEqual(p["status"], "needs_clarification")
        self.assertIn("clarification_question", p)

    def test_trade_routes_away_from_generic_eurostat(self):
        p = plan_sources("Jämför Sveriges export till EU-länderna efter varukod")
        self.assertIn("comext", p["sources"])
        self.assertNotIn("eurostat", p["sources"])
        self.assertTrue(p["decision"]["conflicts"])


if __name__ == "__main__":
    unittest.main()
