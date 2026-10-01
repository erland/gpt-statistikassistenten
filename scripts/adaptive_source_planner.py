#!/usr/bin/env python3
"""Deterministic guardrail/finalizer for Source Query Plan v2.

The language model performs semantic decomposition of the user question.
This module validates that proposed information needs and source roles are
consistent with the source registry and derives the adaptive planning mode.

It deliberately does NOT try to understand arbitrary questions with keyword
rules; that would recreate the scaling problem v2 is intended to solve.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "knowledge" / "source-registry.yaml"


class SourcePlannerV2Error(ValueError):
    pass


def _registry() -> dict[str, Any]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("sources"), dict):
        raise SourcePlannerV2Error("source registry is invalid")
    return data


def registry_summary() -> dict[str, Any]:
    """Return compact capability metadata for semantic planning."""
    registry = _registry()
    return {
        "registry_version": registry["registry_version"],
        "planning_principles": registry["planning_principles"],
        "sources": {
            source_id: {
                "name": source["name"],
                "producer_role": source["producer_role"],
                "tier": source["tier"],
                "primary_for": source["primary_for"],
                "secondary_for": source["secondary_for"],
                "geographies": source["geographies"],
                "frequencies": source["frequencies"],
                "integrated_scope": source["integrated_scope"],
                "limitations": source["limitations"],
            }
            for source_id, source in registry["sources"].items()
        },
        "external_fallback": registry["external_fallback"],
    }


def source_capability(source_id: str) -> dict[str, Any]:
    """Return full registry metadata for one integrated source."""
    source = _registry()["sources"].get(source_id)
    if source is None:
        raise SourcePlannerV2Error(f"unknown registry source: {source_id}")
    return deepcopy(source)


def _require_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SourcePlannerV2Error(f"{field} must be a non-empty string")


def _validate_information_needs(plan: dict[str, Any]) -> set[str]:
    needs = plan.get("information_needs")
    if not isinstance(needs, list) or not needs:
        raise SourcePlannerV2Error("information_needs must be a non-empty list")

    ids: set[str] = set()
    for index, need in enumerate(needs):
        if not isinstance(need, dict):
            raise SourcePlannerV2Error(f"information_needs[{index}] must be an object")
        for field in ("id", "measure", "concept", "population", "geography", "period", "frequency"):
            _require_string(need.get(field), f"information_needs[{index}].{field}")
        need_id = need["id"]
        if need_id in ids:
            raise SourcePlannerV2Error(f"duplicate information need id: {need_id}")
        ids.add(need_id)

        breakdowns = need.get("breakdowns")
        if not isinstance(breakdowns, list) or any(not isinstance(item, str) or not item.strip() for item in breakdowns):
            raise SourcePlannerV2Error(f"{need_id}.breakdowns must be a list of strings")
        if need.get("comparison_mode") not in {
            "single_value", "trend", "cross_section", "national",
            "municipal_comparison", "eu_harmonised", "oecd_harmonised",
            "global_harmonised", "custom"
        }:
            raise SourcePlannerV2Error(f"{need_id}.comparison_mode is invalid")
        if not isinstance(need.get("derived"), bool):
            raise SourcePlannerV2Error(f"{need_id}.derived must be boolean")
        if need["derived"]:
            _require_string(need.get("formula"), f"{need_id}.formula")
            depends_on = need.get("depends_on")
            if not isinstance(depends_on, list) or not depends_on:
                raise SourcePlannerV2Error(f"{need_id}.depends_on must be a non-empty list")

    for need in needs:
        if need["derived"]:
            missing = [dep for dep in need["depends_on"] if dep not in ids]
            if missing:
                raise SourcePlannerV2Error(
                    f"{need['id']} depends on unknown information needs: {', '.join(missing)}"
                )
    return ids


def _validate_source_roles(plan: dict[str, Any], need_ids: set[str]) -> None:
    roles = plan.get("source_roles")
    if not isinstance(roles, list) or not roles:
        raise SourcePlannerV2Error("source_roles must be a non-empty list")

    registry = _registry()["sources"]
    primary_by_need: dict[str, int] = {need_id: 0 for need_id in need_ids}

    for index, role in enumerate(roles):
        if not isinstance(role, dict):
            raise SourcePlannerV2Error(f"source_roles[{index}] must be an object")
        need_id = role.get("need_id")
        source_id = role.get("source_id")
        if need_id not in need_ids:
            raise SourcePlannerV2Error(f"source role refers to unknown need: {need_id}")
        _require_string(source_id, f"source_roles[{index}].source_id")

        role_name = role.get("role")
        if role_name not in {"primary", "supporting", "alternative", "excluded"}:
            raise SourcePlannerV2Error(f"invalid source role: {role_name}")

        tier = role.get("tier")
        integration_status = role.get("integration_status")
        if tier not in {"A", "B", "C", "D"}:
            raise SourcePlannerV2Error(f"invalid source tier: {tier}")
        if integration_status not in {"integrated", "catalog_only", "external"}:
            raise SourcePlannerV2Error(f"invalid integration_status: {integration_status}")

        if source_id in registry:
            registered = registry[source_id]
            if tier != registered["tier"]:
                raise SourcePlannerV2Error(
                    f"{source_id} tier must match source registry ({registered['tier']})"
                )
            if integration_status == "external":
                raise SourcePlannerV2Error(
                    f"{source_id} is registered; use integrated or catalog_only, not external"
                )
        else:
            if integration_status != "external":
                raise SourcePlannerV2Error(
                    f"unregistered source {source_id} must have integration_status external"
                )
            if tier == "A":
                raise SourcePlannerV2Error(
                    f"unregistered source {source_id} cannot be tier A"
                )

        _require_string(role.get("reason"), f"source_roles[{index}].reason")
        limitations = role.get("limitations")
        if not isinstance(limitations, list) or any(not isinstance(item, str) or not item.strip() for item in limitations):
            raise SourcePlannerV2Error(f"source_roles[{index}].limitations must be a list of strings")

        if role_name == "primary":
            primary_by_need[need_id] += 1

    derived = {need["id"] for need in plan["information_needs"] if need["derived"]}
    for need_id in need_ids - derived:
        if primary_by_need[need_id] == 0:
            raise SourcePlannerV2Error(f"non-derived need {need_id} has no primary source")


def _review_reasons(plan: dict[str, Any]) -> list[str]:
    reasons = list(plan.get("decision", {}).get("review_reasons", []))
    roles = plan["source_roles"]
    combination = plan["combination"]
    fallback = plan.get("external_fallback")

    if any(
        role["role"] in {"primary", "supporting"}
        and role["integration_status"] != "integrated"
        for role in roles
    ):
        reasons.append("Minst en vald källa saknar fullt integrerad åtkomst.")

    if any(
        role["role"] in {"primary", "supporting"} and role["tier"] != "A"
        for role in roles
    ):
        reasons.append("Minst en vald källa ligger utanför kvalitetssäkrad tier A.")

    if fallback and fallback.get("required"):
        reasons.append("Extern källfallback krävs.")

    if combination.get("required") and combination.get("risks"):
        reasons.append("Källkombinationen har metodrisker som bör granskas.")

    # Multiple sources or simple deterministic transformations are not by
    # themselves review-worthy. METHOD-GATE still applies, and the semantic
    # planner should record a risk when the combination affects interpretation.
    if plan.get("decision", {}).get("confidence") in {"medium", "low"}:
        reasons.append("Planens confidence är inte high.")

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(reasons))


def _default_review_prompt(plan: dict[str, Any], reasons: list[str]) -> str:
    primary = [
        f"{role['source_id']} för {role['need_id']}"
        for role in plan["source_roles"]
        if role["role"] == "primary"
    ]
    source_text = ", ".join(primary) if primary else "de föreslagna källorna"
    risk_text = " ".join(reasons[:3])
    return (
        f"Jag föreslår {source_text}. "
        f"{risk_text} "
        "Vill du att jag går vidare med detta upplägg?"
    ).strip()


def finalize_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Validate a semantic v2 plan and derive adaptive execution mode/status.

    The caller proposes information_needs/source_roles. This function enforces
    registry alignment and decides whether direct execution is safe enough or
    user review is required before data retrieval.
    """
    if not isinstance(plan, dict):
        raise SourcePlannerV2Error("plan must be an object")
    result = deepcopy(plan)
    _require_string(result.get("question"), "question")

    need_ids = _validate_information_needs(result)
    _validate_source_roles(result, need_ids)

    combination = result.get("combination")
    if not isinstance(combination, dict):
        raise SourcePlannerV2Error("combination must be an object")
    if not isinstance(combination.get("required"), bool):
        raise SourcePlannerV2Error("combination.required must be boolean")
    for field in ("join_dimensions", "transformations", "risks"):
        if not isinstance(combination.get(field), list):
            raise SourcePlannerV2Error(f"combination.{field} must be a list")

    decision = result.get("decision")
    if not isinstance(decision, dict):
        raise SourcePlannerV2Error("decision must be an object")
    if decision.get("confidence") not in {"high", "medium", "low"}:
        raise SourcePlannerV2Error("decision.confidence must be high, medium or low")
    decision.setdefault("review_reasons", [])
    decision.setdefault("clarifications", [])
    if not isinstance(decision["review_reasons"], list) or not isinstance(decision["clarifications"], list):
        raise SourcePlannerV2Error("decision review_reasons/clarifications must be lists")

    fallback = result.get("external_fallback")
    external_selected = any(
        role["role"] in {"primary", "supporting"} and role["integration_status"] == "external"
        for role in result["source_roles"]
    )
    if external_selected and not (isinstance(fallback, dict) and fallback.get("required") is True):
        raise SourcePlannerV2Error("external selected source requires external_fallback.required=true")
    if fallback is not None:
        if not isinstance(fallback, dict):
            raise SourcePlannerV2Error("external_fallback must be an object")
        if not isinstance(fallback.get("required"), bool):
            raise SourcePlannerV2Error("external_fallback.required must be boolean")
        _require_string(fallback.get("reason"), "external_fallback.reason")
        _require_string(fallback.get("search_target"), "external_fallback.search_target")
        if not isinstance(fallback.get("disclosure_required"), bool):
            raise SourcePlannerV2Error("external_fallback.disclosure_required must be boolean")
        if fallback.get("required") and not fallback.get("disclosure_required"):
            raise SourcePlannerV2Error("external fallback requires disclosure_required=true")

    if any(
        role["role"] == "primary" and role["tier"] == "D"
        for role in result["source_roles"]
    ):
        result["status"] = "blocked"
        result["planning_mode"] = "review_before_execution"
        decision["review_reasons"] = list(dict.fromkeys(
            decision["review_reasons"] + ["En tier-D-källa kan inte bära ett statistiskt resultat."]
        ))
        result["user_review_prompt"] = (
            "Den föreslagna källan är inte tillräckligt verifierbar för att bära resultatet. "
            "Jag behöver en annan källa eller ett ändrat informationsbehov."
        )
        return result

    if decision["clarifications"]:
        result["status"] = "needs_clarification"
        result["planning_mode"] = "review_before_execution"
        result["user_review_prompt"] = " ".join(decision["clarifications"])
        return result

    reasons = _review_reasons(result)
    decision["review_reasons"] = reasons

    if reasons:
        result["status"] = "needs_user_review"
        result["planning_mode"] = "review_before_execution"
        result["user_review_prompt"] = result.get("user_review_prompt") or _default_review_prompt(result, reasons)
    else:
        result["status"] = "ready"
        result["planning_mode"] = "direct"
        result.pop("user_review_prompt", None)

    return result
