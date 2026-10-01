import unittest
from scripts import svk_adapter as svk
from scripts.source_planner import plan_sources

class ElectricityDataTests(unittest.TestCase):
    def test_svk_metadata_urls(self):
        self.assertTrue(svk.consumption_types_url().endswith("/GetProductSortConsumtion"))
        self.assertTrue(svk.production_types_url().endswith("/GetProductSortProduction"))

    def test_svk_statistics_url(self):
        url=svk.statistics_url(period_from="2026-01-01",period_to="2026-01-31",bidding_area_id=3,product_sort_id="VI")
        self.assertIn("biddingAreaId=3",url)
        self.assertIn("productSortId=VI",url)

    def test_svk_invalid_area(self):
        with self.assertRaises(svk.SvkAdapterError):
            svk.statistics_url(bidding_area_id=5)

    def test_svk_query_plan(self):
        p=svk.query_plan(kind="consumption",bidding_area_id=4)
        self.assertIn("GetProductSortConsumtion",p["metadata_url"])
        self.assertIn("GetProductionConsumtionStatistics",p["data_url"])

    def test_customer_elpris_routes_scb(self):
        self.assertEqual(plan_sources("Hur har elpriset för hushåll i SE3 utvecklats?")["sources"],["scb"])

    def test_elavtal_routes_scb(self):
        self.assertEqual(plan_sources("Hur skiljer sig elavtal mellan SE1 och SE4?")["sources"],["scb"])

    def test_electricity_consumption_routes_svk(self):
        self.assertEqual(plan_sources("Hur har elkonsumtionen i SE3 utvecklats?")["sources"],["svk"])

    def test_electricity_production_routes_svk(self):
        self.assertEqual(plan_sources("Hur mycket elproduktion hade SE1 förra månaden?")["sources"],["svk"])

    def test_price_and_consumption_combines(self):
        self.assertEqual(plan_sources("Jämför elpris och elkonsumtion i SE4")["sources"],["svk","scb"])

if __name__=="__main__":
    unittest.main()
