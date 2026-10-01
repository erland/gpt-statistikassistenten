import unittest
from scripts.source_planner import plan_sources

class BraBroadRoutingTests(unittest.TestCase):
    def test_reported_crimes_routes_to_bra(self):
        self.assertEqual(plan_sources("Hur många anmälda misshandelsbrott var det 2025?")["sources"],["bra"])

    def test_handled_crimes_routes_to_bra(self):
        self.assertEqual(plan_sources("Hur har personuppklaringsprocenten för rån utvecklats?")["sources"],["bra"])

    def test_suspected_persons_routes_to_bra(self):
        self.assertEqual(plan_sources("Hur många personer var misstänkta för bedrägeribrott 2025?")["sources"],["bra"])

    def test_handled_suspicions_routes_to_bra(self):
        self.assertEqual(plan_sources("Hur många handlagda brottsmisstankar gällde trafikbrott?")["sources"],["bra"])

    def test_sanctioned_persons_routes_to_bra(self):
        self.assertEqual(plan_sources("Hur många personer lagfördes för misshandel 2025?")["sources"],["bra"])

    def test_drug_sanctions_still_route_to_bra(self):
        self.assertEqual(plan_sources("Hur många lagföringsbeslut för narkotikabrott gällde kokain?")["sources"],["bra"])

if __name__=="__main__":
    unittest.main()
