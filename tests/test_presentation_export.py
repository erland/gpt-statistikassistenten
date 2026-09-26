import json
from pathlib import Path

from scripts.presentation_export import from_calculation_result, from_statistical_result, to_csv, to_markdown

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / "examples" / name).read_text())


def test_normalized_result_to_presentation():
    p = from_statistical_result(load("normalized-scb.json"), "Sundsvall hade 100 000 invånare 2025.")
    assert p["rows"][0]["origin"] == "source"
    assert p["sources"][0]["organization"] == "SCB"
    assert p["answer"].startswith("Sundsvall")


def test_calculation_is_marked_calculated():
    calc = load("calculation-per-capita.json")
    p = from_calculation_result(calc, "Brott per 100 000", "500 per 100 000.", [{"organization":"Brå + SCB", "dataset":"Kombinerat mått"}])
    assert p["rows"][0]["origin"] == "calculated"
    assert p["rows"][0]["unit"] == "per 100000"


def test_markdown_contains_required_sections():
    p = from_statistical_result(load("normalized-scb.json"))
    md = to_markdown(p)
    assert "## Data" in md
    assert "## Källor" in md
    assert "SCB" in md


def test_csv_has_machine_readable_columns():
    p = from_statistical_result(load("normalized-scb.json"))
    csv_text = to_csv(p)
    assert "value,unit,status,origin" in csv_text.splitlines()[0]
    assert ",observed,source" in csv_text


def test_missing_value_not_rendered_as_zero():
    result = load("normalized-scb.json")
    result["observations"][0]["value"] = None
    result["observations"][0]["status"] = "missing"
    p = from_statistical_result(result)
    assert "—" in to_markdown(p)
    assert ",,persons,missing,source" in to_csv(p)


def test_trend_analysis_only_describes_observed_direction():
    result = load("normalized-scb.json")
    result["dimensions"][1]["values"] = [{"key":"2024","label":"2024"},{"key":"2025","label":"2025"}]
    result["observations"] = [
        {"dimensions":{"geography":"sundsvall","time":"2024"},"measure":"population","value":99000,"status":"observed"},
        {"dimensions":{"geography":"sundsvall","time":"2025"},"measure":"population","value":100000,"status":"observed"}
    ]
    p = from_statistical_result(result)
    assert any("ökade" in x for x in p["analysis"])
    assert not any("orsak" in x.lower() for x in p["analysis"])
