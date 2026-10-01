import unittest
from scripts.source_planner import plan_sources

class ScbTradeRoutingTests(unittest.TestCase):
    def test_retail_volume_routes_to_scb(self):
        self.assertEqual(
            plan_sources("Hur har detaljhandelns försäljningsvolym utvecklats sedan 2020?")["sources"],
            ["scb"],
        )

    def test_grocery_trade_routes_to_scb(self):
        self.assertEqual(
            plan_sources("Hur har dagligvaruhandeln utvecklats?")["sources"],
            ["scb"],
        )

    def test_company_ecommerce_routes_to_scb(self):
        self.assertEqual(
            plan_sources("Hur stor andel av företagens omsättning kommer från e-handel?")["sources"],
            ["scb"],
        )

    def test_consumer_ecommerce_routes_to_scb(self):
        self.assertEqual(
            plan_sources("Hur många svenskar handlar kläder på nätet?")["sources"],
            ["scb"],
        )

    def test_household_consumption_routes_to_scb(self):
        self.assertEqual(
            plan_sources("Hur har hushållens konsumtion utvecklats?")["sources"],
            ["scb"],
        )

    def test_goods_import_stays_comext(self):
        self.assertEqual(
            plan_sources("Hur mycket kläder importerade Sverige från Kina?")["sources"],
            ["comext"],
        )

    def test_domestic_retail_and_import_combines_scb_and_comext(self):
        self.assertEqual(
            plan_sources("Jämför svensk detaljhandelsomsättning med importen av kläder")["sources"],
            ["comext","scb"],
        )

if __name__=="__main__":
    unittest.main()
