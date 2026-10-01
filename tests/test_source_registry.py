import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from scripts.source_planner import SOURCE_ADAPTER

ROOT = Path(__file__).resolve().parents[1]


def test_source_registry_matches_schema_and_integrated_sources():
    registry = yaml.safe_load((ROOT / "knowledge/source-registry.yaml").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas/source-registry.schema.json").read_text(encoding="utf-8"))

    errors = sorted(Draft202012Validator(schema).iter_errors(registry), key=lambda e: list(e.path))
    assert not errors, "\n".join(error.message for error in errors)

    assert set(registry["sources"]) == set(SOURCE_ADAPTER)
    assert all(source["tier"] == "A" for source in registry["sources"].values())


def test_registry_separates_catalog_from_current_integration():
    registry = yaml.safe_load((ROOT / "knowledge/source-registry.yaml").read_text(encoding="utf-8"))

    broader_sources = {
        source_id
        for source_id, source in registry["sources"].items()
        if set(source["catalog_scope"]) != set(source["integrated_scope"])
    }
    assert {"bra", "euda", "skolverket", "smhi", "statskontoret"} <= broader_sources


def test_external_fallback_requires_disclosure_and_gates():
    registry = yaml.safe_load((ROOT / "knowledge/source-registry.yaml").read_text(encoding="utf-8"))
    fallback = registry["external_fallback"]

    requirements = " ".join(fallback["requirements"])
    assert "METADATA_GATE" in requirements
    assert "METHOD_GATE" in requirements
    assert "PROVENANCE_GATE" in requirements
    assert "not_quality_assured" in requirements
    assert "not quality-assured" in fallback["response_disclosure"]
