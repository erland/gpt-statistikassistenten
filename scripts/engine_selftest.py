"""Offline smoke tests for the standalone Statistikassistenten Engine."""
from __future__ import annotations
import importlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main() -> int:
    modules = ["calculation_engine", "quality_gate", "presentation_export", "source_planner"]
    for module in modules:
        importlib.import_module("scripts." + module)
    from scripts.calculation_engine import percent_change, CalculationError
    example = {
        "dataset": {"title": "Selftest", "publisher": "Selftest", "subject": "test", "frequency": "annual"},
        "dimensions": [{"id": "year", "kind": "time", "label": "År", "values": [{"key": "2024", "label": "2024"}, {"key": "2025", "label": "2025"}]},
                       {"id": "geo", "kind": "geography", "label": "Plats", "values": [{"key": "SE", "label": "SE"}]}],
        "measures": [{"id": "m", "label": "M", "statistic_type": "count", "unit": "count"}],
        "observations": [{"dimensions": {"year": "2024", "geo": "SE"}, "measure": "m", "value": 100, "status": "observed"},
                         {"dimensions": {"year": "2025", "geo": "SE"}, "measure": "m", "value": 110, "status": "observed"}],
        "provenance": {"source": {"organization": "Selftest", "dataset": "Selftest"}, "retrieval": {"verified": True}},
    }
    result = percent_change(example, "m", "2024", "2025")
    assert abs(result["observations"][0]["value"] - 10.0) < 1e-10, result
    print("PASS: imports and percent_change(100,110) = 10%")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
