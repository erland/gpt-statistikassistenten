import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from eurostat_adapter import (  # noqa: E402
    EurostatAdapterError,
    data_request_plan,
    dataflow_catalog_url,
    structure_url,
)

STRUCTURE = {
    "dimensions": [
        {"id": "FREQ", "values": ["A", "M"]},
        {"id": "INDIC_DE", "values": ["POP", "NATGROW"]},
        {"id": "GEO", "values": ["SE", "DE", "EU27_2020"]},
        {"id": "TIME_PERIOD", "values": []},
    ]
}


class EurostatAdapterTests(unittest.TestCase):
    def test_catalog_endpoint(self):
        self.assertEqual(
            dataflow_catalog_url(),
            "https://ec.europa.eu/eurostat/api/dissemination/sdmx/3.0/structure/dataflow/*/*/~",
        )

    def test_structure_endpoint(self):
        url = structure_url("demo_gind")
        self.assertIn("/ESTAT/DEMO_GIND/~?", url)

    def test_build_verified_plan(self):
        plan = data_request_plan(
            "demo_gind",
            STRUCTURE,
            {"FREQ": "A", "INDIC_DE": "POP", "GEO": "SE", "TIME_PERIOD": ["ge:2020", "le:2025"]},
        )
        self.assertEqual(plan["dataset_id"], "DEMO_GIND")
        self.assertIn("c[GEO]=SE", plan["url"])
        self.assertIn("c[TIME_PERIOD]=ge:2020+le:2025", plan["url"])

    def test_unknown_dimension_is_rejected(self):
        with self.assertRaises(EurostatAdapterError):
            data_request_plan("demo_gind", STRUCTURE, {"COUNTRY": "SE"})

    def test_unknown_code_is_rejected(self):
        with self.assertRaises(EurostatAdapterError):
            data_request_plan("demo_gind", STRUCTURE, {"GEO": "XX"})

    def test_comext_dataset_is_rejected(self):
        with self.assertRaises(EurostatAdapterError):
            data_request_plan("DS-045409", STRUCTURE, {"GEO": "SE"})

    def test_example_matches_schema_shape(self):
        example = json.loads((ROOT / "examples/eurostat-query-plan.json").read_text())
        self.assertEqual(example["method"], "GET")
        self.assertTrue(example["url"].startswith("https://ec.europa.eu/eurostat/api/dissemination/sdmx/3.0/data/"))


if __name__ == "__main__":
    unittest.main()
