import unittest
from scripts import energimyndigheten_adapter as energy
from scripts import forsakringskassan_adapter as fk
from scripts import jordbruksverket_adapter as sjv
from scripts import skolverket_adapter as skv
from scripts import smhi_adapter as smhi
from scripts.source_planner import plan_sources

class MoreOpenSourceTests(unittest.TestCase):
    def test_energimyndigheten_pxweb_plan(self):
        table=energy.node_url(["Officiell_energistatistik","Arlig_energibalans","EN0202_28A.px"])
        plan=energy.query_plan(table,[{"code":"Typ","values":["0","1"]}])
        self.assertEqual(plan["method"],"POST")
        self.assertEqual(plan["json"]["query"][0]["code"],"Typ")

    def test_forsakringskassan_metadata_first(self):
        self.assertEqual(
            fk.meta_url("sjp-beslut-forsta"),
            "https://www.forsakringskassan.se/api/sprstatistikrapportera/public/v1/sjp-beslut-forsta/meta/json"
        )
        self.assertEqual(
            fk.validate_distribution_url("https://www.forsakringskassan.se/api/sprstatistikrapportera/public/v1/sjp-beslut-forsta/meta/json"),
            "https://www.forsakringskassan.se/api/sprstatistikrapportera/public/v1/sjp-beslut-forsta/meta/json"
        )
        with self.assertRaises(fk.ForsakringskassanAdapterError):
            fk.validate_distribution_url("https://example.com/data.json")

    def test_jordbruksverket_pxweb_plan(self):
        table=sjv.node_url(["Skordar","JO0601J01.px"])
        plan=sjv.query_plan(table,[{"code":"Ar","values":["2025"]}])
        self.assertEqual(plan["method"],"POST")
        self.assertIn("statistik.jordbruksverket.se",plan["url"])

    def test_skolverket_planned_education_headers(self):
        plan=skv.request_plan("https://api.skolverket.se/planned-educations/schools")
        self.assertEqual(plan["method"],"GET")
        self.assertIn("plannededucations.api.v3",plan["headers"]["Accept"])

    def test_smhi_metobs_urls(self):
        self.assertEqual(
            smhi.parameter_url(5),
            "https://opendata-download-metobs.smhi.se/api/version/latest/parameter/5.json"
        )
        self.assertTrue(smhi.data_url(5,97390,"corrected-archive").endswith("/period/corrected-archive/data.json"))
        with self.assertRaises(smhi.SmhiAdapterError):
            smhi.data_url(5,97390,"all-time")

    def test_router_more_sources(self):
        self.assertEqual(plan_sources("Hur har elproduktionen per kraftslag utvecklats?")["sources"],["energimyndigheten"])
        self.assertEqual(plan_sources("Hur många personer har fått sjukpenning?")["sources"],["forsakringskassan"])
        self.assertEqual(plan_sources("Hur har skörden av spannmål per län utvecklats?")["sources"],["jordbruksverket"])
        self.assertEqual(plan_sources("Vilka skolenheter erbjuder gymnasieprogram?")["sources"],["skolverket"])
        self.assertEqual(plan_sources("Hur har nederbörden vid SMHI:s väderstationer utvecklats?")["sources"],["smhi"])

if __name__ == "__main__":
    unittest.main()
