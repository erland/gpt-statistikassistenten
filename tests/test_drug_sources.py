import unittest
from scripts import euda_adapter as euda
from scripts import tullverket_adapter as tull
from scripts.source_planner import plan_sources

class DrugSourceTests(unittest.TestCase):
    def test_euda_wastewater_plan(self):
        plan=euda.wastewater_plan(country="Sweden",substance="cocaine",year=2025)
        self.assertIn("ww2026-all-data_en.csv",plan["data_url"])
        self.assertIn("site-info",plan["site_info_url"])
        self.assertEqual(plan["unit"],"mg/1000 population/day")
        with self.assertRaises(euda.EudaAdapterError):
            euda.wastewater_plan(year=2026)

    def test_euda_url_validation(self):
        self.assertTrue(euda.validate_official_data_url(euda.wastewater_source_url("all_data")).endswith(".csv"))
        with self.assertRaises(euda.EudaAdapterError):
            euda.validate_official_data_url("https://example.com/data.csv")

    def test_tullverket_plan(self):
        plan=tull.seizure_plan(periods=["2025-H1","2025-H2"],commodity_type="Narkotika",commodity="Kokain",county="Stockholms län")
        self.assertEqual(plan["method"],"official-page-csv-export")
        self.assertEqual(plan["filters"]["commodity_type"],"Narkotika")
        with self.assertRaises(tull.TullverketAdapterError):
            tull.seizure_plan(periods=["2025"])

    def test_tullverket_general_seizure_types(self):
        plan=tull.seizure_plan(periods=["2026-H1"],commodity_type="Skjutvapen")
        self.assertEqual(plan["filters"]["commodity_type"],"Skjutvapen")
        self.assertIsNone(tull.seizure_plan()["filters"]["commodity_type"])

    def test_router_general_tullverket_seizures(self):
        self.assertEqual(plan_sources("Hur många skjutvapen har Tullverket beslagtagit?")["sources"],["tullverket"])
        self.assertEqual(plan_sources("Hur har tobaksbeslagen utvecklats?")["sources"],["tullverket"])
        self.assertEqual(plan_sources("Hur mycket alkohol har Tullverket beslagtagit?")["sources"],["tullverket"])
        self.assertEqual(plan_sources("Hur många beslag av sprängämnen gjorde Tullverket?")["sources"],["tullverket"])

    def test_router_drug_sources(self):
        self.assertEqual(plan_sources("Hur har kokain i avloppsvatten utvecklats i svenska städer?")["sources"],["euda"])
        self.assertEqual(plan_sources("Hur mycket kokain har Tullverket beslagtagit 2025?")["sources"],["tullverket"])
        combined=plan_sources("Jämför kokain i avloppsvatten med Tullverkets kokainbeslag")
        self.assertEqual(combined["sources"],["euda","tullverket"])

if __name__ == "__main__":
    unittest.main()
