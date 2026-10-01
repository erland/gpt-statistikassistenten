#!/usr/bin/env python3
"""Deterministic assessment for external statistical data sources."""
from __future__ import annotations

from copy import deepcopy
from urllib.parse import urlparse
from typing import Any


class ExternalSourceError(ValueError):
    pass


OFFICIAL_KINDS = {"official_primary", "official_international"}
OFFICIAL_STATUSES = {
    "official_statistics", "official_open_data", "official_operational_data", "official_publication"
}
REQUIRED_METADATA = ("definition", "population", "geography", "period", "unit", "status_or_revision")


def _require_text(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ExternalSourceError(f"{field} must be a non-empty string")


def _https_url(value: Any, field: str) -> None:
    _require_text(value, field)
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ExternalSourceError(f"{field} must be an absolute https URL")


def assessment_requirements() -> dict[str, Any]:
    return {
        "search_order": [
            "official_primary_source_or_official_open_data",
            "official_international_organisation",
            "credible_research_or_secondary_source",
        ],
        "required_metadata_checks": list(REQUIRED_METADATA),
        "preferred_access": ["api", "file", "web_service"],
        "never_use_as_result_source": ["D"],
        "disclosure_required_for": ["B", "C"],
    }


def assess_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Validate and classify one external source candidate.

    Tier B requires an official source and all core metadata checks.
    Tier C may be used only when official sources are unavailable and all core
    metadata checks still pass. Tier D is blocked.
    """
    if not isinstance(candidate, dict):
        raise ExternalSourceError("candidate must be an object")
    result = deepcopy(candidate)

    for field in ("source_id", "organization", "dataset_title", "need_id"):
        _require_text(result.get(field), field)
    _https_url(result.get("dataset_url"), "dataset_url")

    source_kind = result.get("source_kind")
    if source_kind not in {"official_primary", "official_international", "research", "secondary"}:
        raise ExternalSourceError("invalid source_kind")
    tier = result.get("source_tier")
    if tier not in {"B", "C", "D"}:
        raise ExternalSourceError("source_tier must be B, C or D")
    status = result.get("official_status")
    if status not in {
        "official_statistics", "official_open_data", "official_operational_data",
        "official_publication", "research_data", "secondary_compilation"
    }:
        raise ExternalSourceError("invalid official_status")
    if result.get("access_method") not in {"api", "file", "web_service", "manual"}:
        raise ExternalSourceError("invalid access_method")

    checks = result.get("metadata_checks")
    if not isinstance(checks, dict):
        raise ExternalSourceError("metadata_checks must be an object")
    missing = [field for field in REQUIRED_METADATA if checks.get(field) is not True]

    limitations = result.get("limitations")
    if not isinstance(limitations, list) or any(not isinstance(x, str) or not x.strip() for x in limitations):
        raise ExternalSourceError("limitations must be a list of non-empty strings")

    evidence = result.get("evidence_urls", [])
    if not isinstance(evidence, list):
        raise ExternalSourceError("evidence_urls must be a list")
    for index, url in enumerate(evidence):
        _https_url(url, f"evidence_urls[{index}]")

    issues: list[str] = []
    if missing:
        issues.append("Saknade verifieringar: " + ", ".join(missing) + ".")

    official = source_kind in OFFICIAL_KINDS and status in OFFICIAL_STATUSES
    if tier == "B" and not official:
        issues.append("Tier B kräver officiell primärkälla eller officiell internationell organisation.")
    if tier == "C" and official:
        issues.append("Officiell källa bör normalt klassas som tier B, inte C.")
    if tier == "D":
        issues.append("Tier D får inte bära ett statistiskt resultat.")

    if result.get("access_method") == "manual":
        issues.append("Manuell åtkomst är svagare än dokumenterad API-/fil-/webbtjänståtkomst.")
    if result.get("machine_readable") is False:
        issues.append("Källan saknar maskinläsbar distribution; kontrollera uttagsrisk manuellt.")

    usable = not missing and tier in {"B", "C"} and not (
        tier == "B" and not official
    ) and not (
        tier == "C" and official
    )

    result["assessment"] = {
        "result": "usable_with_disclosure" if usable else "blocked",
        "metadata_verified": not missing,
        "official_source": official,
        "requires_disclosure": tier in {"B", "C"},
        "issues": issues,
    }
    return result


def disclosure_text(assessment: dict[str, Any]) -> str:
    """Generate required user-facing disclosure for a usable external source."""
    if not isinstance(assessment, dict):
        raise ExternalSourceError("assessment must be an object")
    status = assessment.get("assessment", {})
    if status.get("result") != "usable_with_disclosure":
        raise ExternalSourceError("source is not approved for use")
    return (
        f"Ingen integrerad och kvalitetssäkrad källa täckte detta mått. "
        f"Jag använder därför {assessment['organization']} – {assessment['dataset_title']}, "
        f"en extern tier {assessment['source_tier']}-källa. Definition, population, geografi, "
        f"period, enhet och statistikens status har verifierats för detta uttag. "
        f"Källan är inte permanent kvalitetssäkrad i Statistikassistentens source registry."
    )
