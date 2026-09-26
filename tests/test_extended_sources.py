import unittest
from scripts import kolada_adapter as kolada
from scripts import socialstyrelsen_adapter as sos
from scripts import folkhalsodata_adapter as fhm
from scripts import arbetsformedlingen_adapter as af
from scripts import riksbank_adapter as rb
from scripts.source_planner import plan_sources

class ExtendedSourceTests(unittest.TestCase):
    def test_kolada_url(self):
        self.assertEqual(kolada.data_url(municipality_id="2281", kpi_id="N00095"),
                         "https://api.kolada.se/v3/data/municipality/2281/kpi/N00095")
        with self.assertRaises(kolada.KoladaAdapterError): kolada.data_url(municipality_id="22", kpi_id="N00095")

    def test_socialstyrelsen_result(self):
        u=sos.result_url("amning", [("matt", ["1"]),("ar",["2024","2025"])], per_page=100)
        self.assertIn("/sv/amning/resultat/matt/1/ar/2024,2025", u)
        self.assertIn("per_sida=100", u)

    def test_folkhalsodata_plan(self):
        table=fhm.node_url(["B_HLV","table.px"])
        plan=fhm.query_plan(table,[{"code":"Kon","values":["Totalt"]}])
        self.assertEqual(plan["method"],"POST")
        self.assertEqual(plan["json"]["query"][0]["code"],"Kon")

    def test_arbetsformedlingen_search(self):
        u=af.search_url("java", municipality="AvNB_uwa_6n6", limit=25)
        self.assertIn("/search?",u); self.assertIn("q=java",u); self.assertIn("limit=25",u)

    def test_riksbank(self):
        self.assertEqual(rb.latest_url("SEKEURPMI"), "https://api.riksbank.se/swea/v1/Observations/Latest/SEKEURPMI")
        self.assertTrue(rb.observations_url("SECBREPOEFF","2025-01-01","2025-12-31").endswith("/2025-01-01/2025-12-31"))

    def test_router_extended_sources(self):
        self.assertEqual(plan_sources("Jämför kommunens kostnad för äldreomsorg i Sundsvall och Umeå")["sources"],["kolada"])
        self.assertEqual(plan_sources("Hur har dödsorsaker i Sverige utvecklats?")["sources"],["socialstyrelsen"])
        self.assertEqual(plan_sources("Hur har vaccinationer bland barn utvecklats?")["sources"],["folkhalsodata"])
        self.assertEqual(plan_sources("Vilka kompetenser efterfrågas i platsannonser för systemutvecklare?")["sources"],["arbetsformedlingen"])
        self.assertEqual(plan_sources("Hur har Riksbankens styrränta utvecklats?")["sources"],["riksbank"])

if __name__ == "__main__": unittest.main()
