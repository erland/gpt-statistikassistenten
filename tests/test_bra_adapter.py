import unittest
from scripts.bra_adapter import (
    BraAdapterError,
    available_products,
    discovery_plan,
    product_discovery_plan,
    product_selection_plan,
    reported_crimes_plan,
)

REPORTED_SNAPSHOT = {
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

SANCTIONED_SNAPSHOT = {
    "source": "bra",
    "product": "sanctioned_persons",
    "source_url": "https://bra.se/statistik/statistik-om-rattsvasendet/personer-lagforda-for-brott",
    "dimensions": {
        "periods": [{"code": "2025", "label": "2025"}],
        "crimes": [
            {"code": "ALL", "label": "Samtliga brott"},
            {"code": "NARK", "label": "Narkotikabrott"},
            {"code": "MISS", "label": "Misshandel"},
        ],
        "measures": [
            {"code": "decisions", "label": "Lagföringsbeslut"},
            {"code": "persons", "label": "Lagförda personer"},
        ],
        "sex": [
            {"code": "ALL", "label": "Samtliga"},
            {"code": "F", "label": "Kvinnor"},
            {"code": "M", "label": "Män"},
        ],
        "preparations": [
            {"code": "COCAINE", "label": "Kokain"},
            {"code": "AMPHETAMINE", "label": "Amfetamin"},
        ],
    },
    "status_values": ["final"],
}


class BraAdapterTests(unittest.TestCase):
    def test_products_cover_justice_chain(self):
        ids={item["id"] for item in available_products()}
        self.assertEqual(
            ids,
            {
                "reported_crimes",
                "handled_crimes",
                "suspected_persons",
                "handled_suspicions",
                "sanctioned_persons",
            },
        )

    def test_discovery_backward_compatible(self):
        plan=discovery_plan("anmälda bostadsinbrott")
        self.assertEqual(plan["product"],"reported_crimes")
        self.assertTrue(plan["requires_runtime_retrieval"])

    def test_product_discovery(self):
        plan=product_discovery_plan("suspected_persons","misstänkta för rån")
        self.assertEqual(plan["product"],"suspected_persons")
        self.assertIn("misstankta-personer",plan["product_url"])
        with self.assertRaises(BraAdapterError):
            product_discovery_plan("made_up","test")

    def test_verified_reported_crime_plan(self):
        plan=reported_crimes_plan(
            REPORTED_SNAPSHOT,
            crimes="ALL",
            areas="SUN",
            periods="2024",
            unit="per_100k",
            status="final",
        )
        self.assertEqual(plan["estimated_cells"],1)
        self.assertEqual(plan["selection"]["areas"],["SUN"])

    def test_generic_sanctioned_plan(self):
        plan=product_selection_plan(
            SANCTIONED_SNAPSHOT,
            selections={
                "periods":"2025",
                "crimes":["NARK","MISS"],
                "measures":"decisions",
                "sex":"ALL",
            },
            status="final",
        )
        self.assertEqual(plan["product"],"sanctioned_persons")
        self.assertEqual(plan["estimated_cells"],2)

    def test_drug_preparation_is_optional_dimension_not_separate_product(self):
        plan=product_selection_plan(
            SANCTIONED_SNAPSHOT,
            selections={
                "periods":"2025",
                "crimes":"NARK",
                "measures":"decisions",
                "preparations":["COCAINE","AMPHETAMINE"],
            },
            status="final",
        )
        self.assertEqual(plan["product"],"sanctioned_persons")
        self.assertEqual(plan["selection"]["preparations"],["COCAINE","AMPHETAMINE"])

    def test_unknown_dimension_value_rejected(self):
        with self.assertRaises(BraAdapterError):
            product_selection_plan(
                SANCTIONED_SNAPSHOT,
                selections={"periods":"2025","crimes":"MADE_UP","measures":"decisions"},
                status="final",
            )

    def test_small_area_monthly_crime_code_rejected(self):
        with self.assertRaises(BraAdapterError):
            reported_crimes_plan(
                REPORTED_SNAPSHOT,
                crimes="0101",
                areas="SUN",
                periods="2025M01",
                unit="count",
            )

    def test_large_selection_rejected(self):
        snap=dict(REPORTED_SNAPSHOT)
        snap["periods"]=[{"code":f"P{i}","label":f"P{i}","granularity":"year"} for i in range(101)]
        snap["areas"]=[{"code":f"A{i}","label":f"A{i}","level":"municipality"} for i in range(100)]
        with self.assertRaises(BraAdapterError):
            reported_crimes_plan(
                snap,
                crimes="ALL",
                areas=[f"A{i}" for i in range(100)],
                periods=[f"P{i}" for i in range(101)],
                unit="count",
            )


if __name__=="__main__":
    unittest.main()
