import copy
import json
from pathlib import Path

from scripts.presentation_export import from_statistical_result
from scripts.quality_gate import run_quality_gate, validate_statistical_result

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / "examples" / name).read_text())


def test_valid_scb_result_and_presentation_pass():
    result = load("normalized-scb.json")
    p = from_statistical_result(result)
    report = run_quality_gate(statistical_results=[result], presentation=p)
    assert report["result"] == "passed"
    assert report["blockers"] == []


def test_unverified_metadata_blocks():
    result = load("normalized-scb.json")
    result["provenance"]["retrieval"]["metadata_verified"] = False
    issues = validate_statistical_result(result)
    assert any(i["code"] == "metadata_not_verified" for i in issues)


def test_confidential_numeric_value_blocks():
    result = load("normalized-scb.json")
    result["observations"][0]["status"] = "confidential"
    result["observations"][0]["value"] = 42
    issues = validate_statistical_result(result)
    assert any(i["code"] == "masked_value_has_number" for i in issues)


def test_bra_requires_interpretation_note():
    result = load("normalized-bra.json")
    result["method"]["definitions"] = []
    issues = validate_statistical_result(result)
    assert any(i["code"] == "bra_reported_crime_definition_missing" for i in issues)


def test_per_capita_requires_method_checks():
    calc = load("calculation-per-capita.json")
    calc["method"]["checks"].remove("same_period")
    report = run_quality_gate(calculations=[calc])
    assert report["result"] == "blocked"
    assert any(i["code"] == "per_capita_checks_missing" for i in report["blockers"])


def test_unsupported_causal_claim_blocks():
    result = load("normalized-scb.json")
    p = from_statistical_result(result, "Befolkningsökningen beror på arbetsmarknaden.")
    report = run_quality_gate(statistical_results=[result], presentation=p)
    assert report["result"] == "blocked"
    assert any(i["code"] == "unsupported_causal_claim" for i in report["blockers"])


def test_causal_claim_can_pass_with_separate_verified_evidence_flag():
    result = load("normalized-scb.json")
    p = from_statistical_result(result, "Befolkningsökningen beror på arbetsmarknaden.")
    report = run_quality_gate(statistical_results=[result], presentation=p, causal_evidence_verified=True)
    assert report["result"] == "passed"


def test_provisional_requires_presentation_note():
    result = load("normalized-scb.json")
    result["observations"][0]["status"] = "provisional"
    p = from_statistical_result(result)
    p["method_notes"] = []
    report = run_quality_gate(statistical_results=[result], presentation=p)
    assert report["result"] == "blocked"
    assert any(i["code"] == "provisional_note_missing" for i in report["blockers"])
