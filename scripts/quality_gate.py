from __future__ import annotations

from typing import Any, Dict, List

CAUSAL_MARKERS = (
    "orsakade",
    "beror på",
    "berodde på",
    "ledde till",
    "på grund av",
    "orsaken är",
)


def _issue(code: str, severity: str, message: str) -> Dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _contains_causal_claim(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in CAUSAL_MARKERS)


def validate_statistical_result(result: Dict[str, Any]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    provenance = result.get("provenance", {})
    source = provenance.get("source", {})
    retrieval = provenance.get("retrieval", {})

    if not source.get("organization"):
        issues.append(_issue("missing_source_organization", "blocker", "Källorganisation saknas."))
    if not source.get("dataset_title"):
        issues.append(_issue("missing_dataset_title", "blocker", "Dataset/statistikprodukt saknas i provenance."))
    if retrieval.get("metadata_verified") is not True:
        issues.append(_issue("metadata_not_verified", "blocker", "Metadata måste vara verifierad före färdigt statistiksvar."))
    if not retrieval.get("retrieved_at"):
        issues.append(_issue("missing_retrieval_time", "blocker", "Tidpunkt för hämtning saknas."))

    observations = result.get("observations", [])
    if not observations:
        issues.append(_issue("no_observations", "blocker", "Inga observationer finns att presentera."))

    for idx, obs in enumerate(observations):
        status = obs.get("status", "observed")
        value = obs.get("value")
        if status in {"missing", "confidential"} and value is not None:
            issues.append(_issue("masked_value_has_number", "blocker", f"Observation {idx} har status {status} men ett numeriskt värde."))
        if not obs.get("dimensions"):
            issues.append(_issue("missing_observation_dimensions", "blocker", f"Observation {idx} saknar dimensioner."))
        if not obs.get("measure"):
            issues.append(_issue("missing_observation_measure", "blocker", f"Observation {idx} saknar måttreferens."))

    organization = str(source.get("organization", "")).lower()
    dataset = str(source.get("dataset_title", "")).lower()
    definitions = " ".join(result.get("method", {}).get("definitions", [])).lower()
    if "brå" in organization and "anmälda brott" in dataset:
        if not ("inte" in definitions and "faktisk" in definitions and "brott" in definitions):
            issues.append(_issue("bra_reported_crime_definition_missing", "blocker", "Brå:s anmälda brott måste ha metodnotering om att statistiken inte är ett direkt mått på all faktisk brottslighet."))

    if any(obs.get("status") == "break_in_series" for obs in observations):
        if not result.get("method", {}).get("breaks_in_series"):
            issues.append(_issue("series_break_note_missing", "blocker", "Tidsseriebrott finns i observationerna men saknar metodnotering."))

    if any(obs.get("status") == "provisional" for obs in observations):
        issues.append(_issue("provisional_data", "warning", "Resultatet innehåller preliminär statistik och ska märkas som sådan."))

    return issues


def validate_calculation_result(calc: Dict[str, Any]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    calculation = calc.get("calculation", {})
    if not calculation.get("formula"):
        issues.append(_issue("calculation_formula_missing", "blocker", "Beräknat mått saknar formel."))
    checks = set(calc.get("method", {}).get("checks", []))
    calc_type = calculation.get("type")
    if calc_type == "per_capita":
        required = {"same_period", "same_geography", "positive_denominator", "unit_verified"}
        missing = sorted(required - checks)
        if missing:
            issues.append(_issue("per_capita_checks_missing", "blocker", "Per-capita-beräkningen saknar kontroller: " + ", ".join(missing)))
    for idx, obs in enumerate(calc.get("observations", [])):
        if not obs.get("inputs"):
            issues.append(_issue("calculation_inputs_missing", "blocker", f"Beräknad observation {idx} saknar ingångsvärden."))
    return issues


def validate_presentation(presentation: Dict[str, Any], causal_evidence_verified: bool = False) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    sources = presentation.get("sources", [])
    if not sources:
        issues.append(_issue("presentation_sources_missing", "blocker", "Presentationen saknar källor."))
    for idx, source in enumerate(sources):
        for field in ("organization", "dataset", "period", "geography", "measure"):
            if not str(source.get(field, "")).strip():
                issues.append(_issue("incomplete_presentation_source", "blocker", f"Källa {idx} saknar {field}."))

    rows = presentation.get("rows", [])
    for idx, row in enumerate(rows):
        if row.get("status") in {"missing", "confidential"} and row.get("value") is not None:
            issues.append(_issue("presentation_masked_value_has_number", "blocker", f"Rad {idx} visar numeriskt värde trots status {row.get('status')}."))
        if row.get("origin") not in {"source", "calculated"}:
            issues.append(_issue("invalid_origin", "blocker", f"Rad {idx} saknar tydlig markering som source eller calculated."))

    texts = [presentation.get("answer", "")] + list(presentation.get("analysis", []))
    if not causal_evidence_verified and any(_contains_causal_claim(str(text)) for text in texts):
        issues.append(_issue("unsupported_causal_claim", "blocker", "Presentationen innehåller en kausal formulering utan separat verifierad evidens."))

    if any(row.get("status") == "provisional" for row in rows):
        notes = " ".join(presentation.get("method_notes", [])).lower()
        if "prelimin" not in notes:
            issues.append(_issue("provisional_note_missing", "blocker", "Preliminära observationer måste markeras i metodnoteringen."))

    return issues


def run_quality_gate(*, statistical_results: List[Dict[str, Any]] | None = None,
                     calculations: List[Dict[str, Any]] | None = None,
                     presentation: Dict[str, Any] | None = None,
                     causal_evidence_verified: bool = False) -> Dict[str, Any]:
    issues: List[Dict[str, str]] = []
    for result in statistical_results or []:
        issues.extend(validate_statistical_result(result))
    for calc in calculations or []:
        issues.extend(validate_calculation_result(calc))
    if presentation is not None:
        issues.extend(validate_presentation(presentation, causal_evidence_verified=causal_evidence_verified))

    blockers = [i for i in issues if i["severity"] == "blocker"]
    warnings = [i for i in issues if i["severity"] == "warning"]
    return {
        "result": "blocked" if blockers else "passed",
        "blockers": blockers,
        "warnings": warnings,
        "checks": {
            "metadata_and_provenance": True,
            "observation_integrity": True,
            "method_compatibility": True,
            "presentation_integrity": presentation is not None,
        },
    }
