import unittest
from scripts import worldbank_adapter as wb
from scripts import oecd_adapter as oecd
from scripts import who_adapter as who
from scripts import bis_adapter as bis
from scripts import ecb_adapter as ecb
from scripts.source_planner import plan_sources

class InternationalSourceTests(unittest.TestCase):
    def test_worldbank_urls(self):
        self.assertIn("/indicator/SP.POP.TOTL?format=json", wb.indicator_metadata_url("SP.POP.TOTL"))
        u=wb.data_url("NY.GDP.PCAP.CD",["SE","CN","IN"],from_year="2000",to_year="2025")
        self.assertIn("/country/SE;CN;IN/indicator/NY.GDP.PCAP.CD",u)
        self.assertIn("date=2000%3A2025",u)

    def test_oecd_urls(self):
        self.assertEqual(
            oecd.dataflow_url("OECD.SDD.NAD","DSD_NASEC10@DF_TABLE12","1.1"),
            "https://sdmx.oecd.org/public/rest/dataflow/OECD.SDD.NAD/DSD_NASEC10%40DF_TABLE12/1.1?references=all"
        )
        self.assertIn("/data/OECD.SDD.NAD,DSD_NASEC10%40DF_TABLE12,1.1/all", 
                      oecd.data_url("OECD.SDD.NAD,DSD_NASEC10@DF_TABLE12,1.1"))

    def test_who_fallback(self):
        self.assertEqual(who.hub_url(),"https://data.who.int")
        self.assertEqual(who.validate_official_url("https://data.who.int/indicators"),"https://data.who.int/indicators")
        with self.assertRaises(who.WhoAdapterError):
            who.validate_official_url("https://example.com/health")

    def test_bis_urls(self):
        self.assertEqual(
            bis.structure_url("dataflow","BIS","all","latest"),
            "https://stats.bis.org/api/v2/structure/dataflow/BIS/all/latest"
        )
        self.assertIn("/data/dataflow/BIS/WS_LONG_CPI/1.0/",bis.data_url("dataflow","BIS","WS_LONG_CPI","1.0","A.SE.628"))

    def test_ecb_urls(self):
        self.assertEqual(ecb.dataflow_url(),"https://data-api.ecb.europa.eu/service/dataflow")
        self.assertIn("/data/ECB,EXR,1.0/",ecb.data_url("ECB,EXR,1.0","D.USD.EUR.SP00.A"))

    def test_router_international(self):
        self.assertEqual(plan_sources("Jämför BNP per capita i Sverige, Kina och Indien")["sources"],["worldbank"])
        self.assertEqual(plan_sources("Jämför produktiviteten i OECD-länderna")["sources"],["oecd"])
        self.assertEqual(plan_sources("Hur har global barnadödlighet utvecklats enligt WHO?")["sources"],["who"])
        self.assertEqual(plan_sources("Jämför hushållens skuldsättning internationellt enligt BIS")["sources"],["bis"])
        self.assertEqual(plan_sources("Hur har ECB:s ränta i euroområdet utvecklats?")["sources"],["ecb"])

if __name__ == "__main__":
    unittest.main()
