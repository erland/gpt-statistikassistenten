#!/usr/bin/env python3
"""Deterministic helpers for planning Brå reported-crime statistics retrieval.

Brå does not expose a general public statistics API for this product. This
module therefore validates a normalized metadata snapshot obtained by runtime
from Brå's official statistics service or published files, and builds a
source/provenance plan without fabricating an API contract.
"""
from __future__ import annotations

from typing import Any, Iterable

SERVICE_URL = "https://statistik.bra.se/solwebb/action/start"
HELP_URL = "https://statistik.bra.se/solwebb/action/hjalp?kod=h_hjalp_anv"
MAX_CELLS = 10_000


class BraAdapterError(ValueError):
    pass


def discovery_plan(query: str) -> dict[str, Any]:
    q = query.strip()
    if not q:
        raise BraAdapterError("query must not be empty")
    return {
        "source": "bra",
        "product": "reported_crimes",
        "mode": "official_web_service_or_published_file",
        "service_url": SERVICE_URL,
        "help_url": HELP_URL,
        "query": q,
        "requires_runtime_retrieval": True,
    }


def _catalog(snapshot: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    raw = snapshot.get(key)
    if not isinstance(raw, list) or not raw:
        raise BraAdapterError(f"metadata snapshot must contain non-empty {key}")
    result: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise BraAdapterError(f"invalid item in {key}")
        code = item.get("code") or item.get("id")
        label = item.get("label") or item.get("name")
        if not isinstance(code, str) or not code or not isinstance(label, str) or not label:
            raise BraAdapterError(f"{key} item must contain code/id and label/name")
        result[code] = item
    return result


def validate_metadata_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    if snapshot.get("source") != "bra" or snapshot.get("product") != "reported_crimes":
        raise BraAdapterError("snapshot must describe Brå reported-crime statistics")
    periods = _catalog(snapshot, "periods")
    areas = _catalog(snapshot, "areas")
    crimes = _catalog(snapshot, "crimes")
    units = _catalog(snapshot, "units")
    status_values = snapshot.get("status_values") or ["preliminary", "final"]
    if not isinstance(status_values, list) or not all(isinstance(v, str) for v in status_values):
        raise BraAdapterError("invalid status_values")
    return {
        "periods": periods,
        "areas": areas,
        "crimes": crimes,
        "units": units,
        "status_values": set(status_values),
    }


def _normalize_values(raw: Iterable[str] | str, *, label: str) -> list[str]:
    values = [raw] if isinstance(raw, str) else list(raw)
    if not values or any(not isinstance(v, str) or not v for v in values):
        raise BraAdapterError(f"at least one non-empty value is required for {label}")
    return values


def reported_crimes_plan(
    snapshot: dict[str, Any],
    *,
    crimes: Iterable[str] | str,
    areas: Iterable[str] | str,
    periods: Iterable[str] | str,
    unit: str,
    status: str | None = None,
) -> dict[str, Any]:
    """Build a verified retrieval plan from an official Brå metadata snapshot."""
    catalogs = validate_metadata_snapshot(snapshot)
    selected = {
        "crimes": _normalize_values(crimes, label="crimes"),
        "areas": _normalize_values(areas, label="areas"),
        "periods": _normalize_values(periods, label="periods"),
    }
    for group, values in selected.items():
        catalog = catalogs[group]
        unknown = [v for v in values if v not in catalog]
        if unknown:
            raise BraAdapterError(f"unknown {group} values: {', '.join(unknown)}")

    if unit not in catalogs["units"]:
        raise BraAdapterError(f"unknown unit: {unit}")
    if status is not None and status not in catalogs["status_values"]:
        raise BraAdapterError(f"unknown publication status: {status}")

    cells = len(selected["crimes"]) * len(selected["areas"]) * len(selected["periods"])
    if cells > MAX_CELLS:
        raise BraAdapterError(f"selection exceeds Brå service limit of {MAX_CELLS} data cells")

    # Known publication rule from Brå: monthly statistics at municipality/city-
    # district level are restricted for detailed crime types/codes for secrecy.
    selected_area_levels = {catalogs["areas"][a].get("level") for a in selected["areas"]}
    selected_period_granularities = {catalogs["periods"][p].get("granularity") for p in selected["periods"]}
    crime_detail_levels = {catalogs["crimes"][c].get("detail_level") for c in selected["crimes"]}
    restricted = bool(
        selected_area_levels & {"municipality", "city_district"}
        and selected_period_granularities & {"month", "quarter"}
        and crime_detail_levels & {"crime_code", "detailed"}
    )
    if restricted:
        raise BraAdapterError(
            "selected small-area short-period crime detail may be unavailable for confidentiality; choose broader crime type, area, or period"
        )

    source_url = snapshot.get("source_url") or SERVICE_URL
    if not isinstance(source_url, str) or not source_url.startswith("https://"):
        raise BraAdapterError("snapshot source_url must be an https URL")

    return {
        "source": "bra",
        "product": "reported_crimes",
        "retrieval_mode": snapshot.get("retrieval_mode", "official_web_service_or_published_file"),
        "source_url": source_url,
        "selection": {**selected, "unit": unit, "status": status},
        "estimated_cells": cells,
        "max_cells": MAX_CELLS,
        "requires_runtime_retrieval": True,
        "provenance_requirements": [
            "source_url",
            "retrieval_date",
            "crime_definition",
            "area_definition",
            "period_definition",
            "unit",
            "publication_status",
        ],
        "method_notes": [
            "Reported crimes are registered reports, not a direct measure of total crime prevalence.",
            "Previously published values can differ because Brå's statistics database is updated continuously.",
        ],
    }
