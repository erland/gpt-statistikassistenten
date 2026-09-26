#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("scb_adapter", ROOT / "scripts" / "scb_adapter.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

metadata = json.loads((ROOT / "tests/fixtures/scb/tab638-metadata-minimal.json").read_text())


def expect_error(fn, contains):
    try:
        fn()
    except mod.ScbAdapterError as exc:
        assert contains in str(exc), (contains, str(exc))
    else:
        raise AssertionError("expected ScbAdapterError")


# Discovery must be dynamic and URL encoded.
u = mod.search_url("befolk*", page_size=5)
assert "/tables?" in u and "query=befolk%2A" in u and "pageSize=5" in u

# Metadata endpoint uses the discovered ID, not a hardcoded semantic alias.
assert mod.metadata_url("TAB638").endswith("/tables/TAB638/metadata?lang=sv")

selection = [
    {"variableCode": "Region", "valueCodes": ["2281"]},
    {"variableCode": "Civilstand", "valueCodes": ["OG"]},
    {"variableCode": "Alder", "valueCodes": ["0"]},
    {"variableCode": "Kon", "valueCodes": ["1", "2"]},
    {"variableCode": "ContentsCode", "valueCodes": ["BE0101N1"]},
    {"variableCode": "Tid", "valueCodes": ["2023", "2024"]}
]
plan = mod.post_request_plan("TAB638", metadata, selection)
assert plan["method"] == "POST"
assert plan["estimated_cells"] == 4
assert plan["body"]["selection"] == selection

# Unknown codes must stop the request rather than be guessed.
expect_error(lambda: mod.validate_selection(metadata, [{"variableCode": "Region", "valueCodes": ["9999"]}]), "unknown valueCode")
expect_error(lambda: mod.validate_selection(metadata, [{"variableCode": "Tid", "valueCodes": ["2024"]}]), "missing mandatory variables")
expect_error(lambda: mod.validate_selection(metadata, [{"variableCode": "NoSuchVariable", "valueCodes": ["x"]}]), "unknown variableCode")

print("SCB adapter tests passed")
