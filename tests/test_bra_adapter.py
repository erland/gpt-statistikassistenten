import unittest
from scripts.bra_adapter import BraAdapterError, discovery_plan, reported_crimes_plan

SNAPSHOT = {
    "source": "bra",
    "product": "reported_crimes",
    "source_url": "https://statistik.bra.se/solwebb/action/start",
    "periods": [
        {"code": "2024", "label": "2024", "granularity": "year"},
        {"code": "2025M01", "label": "Januari 2025", "granularity": "month"},
    ],
    "areas": [
        {"code": "SE", "label": "Hela landet", "level": "country"},
        {"code": "SUN", "label": "Sundsvalls kommun", "level": "municipality"},
    ],
    "crimes": [
        {"code": "ALL", "label": "Samtliga brott", "detail_level": "broad"},
        {"code": "0101", "label": "Exempelbrottskod", "detail_level": "crime_code"},
    ],
    "units": [
        {"code": "count", "label": "Antal"},
        {"code": "per_100k", "label": "Per 100 000 invånare"},
    ],
    "status_values": ["preliminary", "final"],
}

class BraAdapterTests(unittest.TestCase):
    def test_discovery(self):
        plan = discovery_plan("anmälda bostadsinbrott")
        self.assertEqual(plan["product"], "reported_crimes")
        self.assertTrue(plan["requires_runtime_retrieval"])

    def test_verified_plan(self):
        plan = reported_crimes_plan(SNAPSHOT, crimes="ALL", areas="SUN", periods="2024", unit="per_100k", status="final")
        self.assertEqual(plan["estimated_cells"], 1)
        self.assertEqual(plan["selection"]["areas"], ["SUN"])

    def test_unknown_crime_rejected(self):
        with self.assertRaises(BraAdapterError):
            reported_crimes_plan(SNAPSHOT, crimes="MADE_UP", areas="SE", periods="2024", unit="count")

    def test_small_area_monthly_crime_code_rejected(self):
        with self.assertRaises(BraAdapterError):
            reported_crimes_plan(SNAPSHOT, crimes="0101", areas="SUN", periods="2025M01", unit="count")

    def test_large_selection_rejected(self):
        snap = dict(SNAPSHOT)
        snap["periods"] = [{"code": f"P{i}", "label": f"P{i}", "granularity": "year"} for i in range(101)]
        snap["areas"] = [{"code": f"A{i}", "label": f"A{i}", "level": "municipality"} for i in range(100)]
        with self.assertRaises(BraAdapterError):
            reported_crimes_plan(snap, crimes="ALL", areas=[f"A{i}" for i in range(100)], periods=[f"P{i}" for i in range(101)], unit="count")

if __name__ == "__main__":
    unittest.main()
