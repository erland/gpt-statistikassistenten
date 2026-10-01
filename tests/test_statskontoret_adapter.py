import unittest
from scripts import statskontoret_adapter as sk
from scripts.source_planner import plan_sources

class StatskontoretAdapterTests(unittest.TestCase):
    def test_products(self):
        self.assertEqual(
            sk.available_products(),
            ["agency_directory", "annual_budget_outturn", "monthly_budget_outturn"],
        )

    def test_monthly_plan(self):
        plan = sk.data_plan(
            "monthly_budget_outturn",
            year=2026,
            month=8,
            agency="Tullverket",
            appropriation="1:3",
        )
        self.assertEqual(plan["method"], "official-open-data-distribution")
        self.assertIn("manadsutfall", plan["discovery_url"])
        self.assertEqual(plan["filters"]["agency"], "Tullverket")

    def test_annual_plan(self):
        plan = sk.data_plan("annual_budget_outturn", year=2025, agency="Trafikverket")
        self.assertIn("csv", plan["preferred_formats"])
        self.assertIn("arsutfall", plan["discovery_url"])

    def test_agency_directory_plan(self):
        plan = sk.data_plan("agency_directory", year=2026, agency="Skatteverket")
        self.assertEqual(plan["preferred_formats"], ["xlsx"])
        self.assertIn("myndighetsforteckning", plan["discovery_url"])

    def test_distribution_url_must_be_official(self):
        url = "https://www.statskontoret.se/contentassets/example/utfall.csv"
        self.assertEqual(sk.validate_distribution_url("annual_budget_outturn", url), url)
        with self.assertRaises(sk.StatskontoretAdapterError):
            sk.validate_distribution_url("annual_budget_outturn", "https://example.com/utfall.csv")

    def test_directory_rejects_csv(self):
        with self.assertRaises(sk.StatskontoretAdapterError):
            sk.validate_distribution_url(
                "agency_directory",
                "https://www.statskontoret.se/contentassets/example/myndigheter.csv",
            )

    def test_invalid_month(self):
        with self.assertRaises(sk.StatskontoretAdapterError):
            sk.data_plan("monthly_budget_outturn", year=2026, month=13)

    def test_budget_routing(self):
        self.assertEqual(
            plan_sources("Hur stort var Trafikverkets anslag och budgetutfall 2025?")["sources"],
            ["statskontoret"],
        )

    def test_annual_work_units_routing(self):
        self.assertEqual(
            plan_sources("Hur många årsarbetskrafter hade Skatteverket 2025?")["sources"],
            ["statskontoret"],
        )

    def test_employees_route_to_scb(self):
        self.assertEqual(
            plan_sources("Hur många anställda per myndighet finns i staten?")["sources"],
            ["scb"],
        )

    def test_budget_and_employees_use_both(self):
        self.assertEqual(
            plan_sources("Jämför budgetutfall och antal anställda per myndighet")["sources"],
            ["statskontoret", "scb"],
        )

if __name__ == "__main__":
    unittest.main()
