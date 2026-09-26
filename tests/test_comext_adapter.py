import unittest

from scripts.comext_adapter import (
    ComextAdapterError,
    dataflow_catalog_url,
    structure_url,
    trade_request_plan,
)

STRUCTURE = {
    "dimensions": [
        {"id": "FREQ", "values": ["A", "M"]},
        {"id": "REPORTER", "values": ["SE", "DK"]},
        {"id": "PARTNER", "values": ["US", "CN", "WORLD"]},
        {"id": "PRODUCT", "values": ["TOTAL", "0901", "8703"]},
        {"id": "FLOW", "values": ["1", "2"]},
        {"id": "TIME_PERIOD"},
        {"id": "INDICATORS", "values": ["VALUE_IN_EUROS", "QUANTITY_IN_100KG"]},
    ],
    "roles": {
        "frequency": "FREQ",
        "reporter": "REPORTER",
        "partner": "PARTNER",
        "product": "PRODUCT",
        "flow": "FLOW",
        "time": "TIME_PERIOD",
        "indicator": "INDICATORS",
    },
}


class ComextAdapterTest(unittest.TestCase):
    def test_catalog_uses_dedicated_comext_endpoint(self):
        self.assertIn("/comext/dissemination/", dataflow_catalog_url())

    def test_structure_rejects_non_ds_dataset(self):
        with self.assertRaises(ComextAdapterError):
            structure_url("nama_10_gdp")

    def test_builds_filtered_trade_request(self):
        plan = trade_request_plan(
            "DS-045409",
            STRUCTURE,
            reporter="SE",
            partner="US",
            flow="1",
            product="0901",
            period=["ge:2024", "le:2025"],
            indicator="VALUE_IN_EUROS",
            frequency="A",
        )
        self.assertEqual("SE", plan["semantic_selection"]["reporter"][0])
        self.assertIn("c[REPORTER]=SE", plan["url"])
        self.assertIn("c[PARTNER]=US", plan["url"])
        self.assertIn("c[PRODUCT]=0901", plan["url"])
        self.assertIn("c[TIME_PERIOD]=ge:2024+le:2025", plan["url"])

    def test_rejects_unknown_product(self):
        with self.assertRaises(ComextAdapterError):
            trade_request_plan(
                "DS-045409", STRUCTURE, reporter="SE", partner="US", flow="1",
                product="99999999", period="2025", indicator="VALUE_IN_EUROS"
            )

    def test_requires_indicator(self):
        with self.assertRaises(ComextAdapterError):
            trade_request_plan(
                "DS-045409", STRUCTURE, reporter="SE", partner="US", flow="1",
                product="0901", period="2025", indicator=[]
            )

    def test_rejects_missing_semantic_role(self):
        broken = {**STRUCTURE, "roles": {k: v for k, v in STRUCTURE["roles"].items() if k != "partner"}}
        with self.assertRaises(ComextAdapterError):
            trade_request_plan(
                "DS-045409", broken, reporter="SE", partner="US", flow="1",
                product="0901", period="2025", indicator="VALUE_IN_EUROS"
            )


if __name__ == "__main__":
    unittest.main()
