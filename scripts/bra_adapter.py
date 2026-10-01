#!/usr/bin/env python3
"""Deterministic helpers for planning Brå statistics retrieval.

Brå publishes several official crime-justice statistics products through web
tables and downloadable files, but Statistikassistenten does not assume one
stable general-purpose public API. Runtime retrieves an official metadata
snapshot for the selected product; this module validates that snapshot and
builds bounded retrieval/provenance plans.
"""
from __future__ import annotations

from math import prod
from typing import Any, Iterable

SERVICE_URL = "https://statistik.bra.se/solwebb/action/start"
HELP_URL = "https://statistik.bra.se/solwebb/action/hjalp?kod=h_hjalp_anv"
MAX_CELLS = 10_000

PRODUCTS = {
    "reported_crimes": {
        "label": "Anmälda brott",
        "url": "https://bra.se/statistik/statistik-om-rattsvasendet/anmalda-brott",
        "required_dimensions": ("periods", "areas", "crimes", "units"),
        "method_notes": (
            "Anmälda brott är registrerade brottsanmälningar och inte ett direkt mått på all faktisk brottslighet.",
            "Tidigare publicerade värden kan ändras när Brås statistikdatabas uppdateras.",
        ),
    },
    "handled_crimes": {
        "label": "Handlagda brott",
        "url": "https://bra.se/statistik/statistik-om-rattsvasendet/handlagda-brott",
        "required_dimensions": ("periods", "areas", "crimes", "measures"),
        "method_notes": (
            "Handlagda brott avser anmälda brott där ett avslutande beslut fattats under redovisningsåret.",
            "Personuppklaringsprocent och lagföringsprocent har andra nämnare och får inte behandlas som samma mått.",
        ),
    },
    "suspected_persons": {
        "label": "Misstänkta personer",
        "url": "https://bra.se/statistik/statistik-om-rattsvasendet/misstankta-personer",
        "required_dimensions": ("periods", "areas", "crimes", "measures"),
        "method_notes": (
            "Misstänkta personer avser straffmyndiga personer registrerade som minst skäligen misstänkta för brott.",
            "Personer kan förekomma i flera brottskategorier; summering över kategorier kan därför dubbelräkna personer.",
        ),
    },
    "handled_suspicions": {
        "label": "Handlagda brottsmisstankar",
        "url": "https://bra.se/statistik/statistik-om-rattsvasendet/handlagda-brottsmisstankar",
        "required_dimensions": ("periods", "areas", "crimes", "measures"),
        "method_notes": (
            "Handlagda brottsmisstankar avser avslutade brottsmisstankar mot straffmyndiga personer som varit minst skäligen misstänkta.",
            "Brottsmisstankar är inte personer; samma person kan ligga bakom flera brottsmisstankar.",
        ),
    },
    "sanctioned_persons": {
        "label": "Personer lagförda för brott",
        "url": "https://bra.se/statistik/statistik-om-rattsvasendet/personer-lagforda-for-brott",
        "required_dimensions": ("periods", "crimes", "measures"),
        "method_notes": (
            "Lagföringsstatistiken avser lagföringsbeslut mot personer som konstaterats skyldiga genom domslut, strafföreläggande eller åtalsunderlåtelse.",
            "Huvudbrott, samtliga brott i lagföringen och påföljd är olika redovisningsgrunder och ska hållas isär.",
        ),
    },
}


class BraAdapterError(ValueError):
    pass


def available_products() -> list[dict[str, str]]:
    return [
        {"id": product_id, "label": spec["label"], "url": spec["url"]}
        for product_id, spec in PRODUCTS.items()
    ]


def product_discovery_plan(product: str, query: str) -> dict[str, Any]:
    if product not in PRODUCTS:
        raise BraAdapterError(f"unsupported Brå product: {product}")
    q = query.strip()
    if not q:
        raise BraAdapterError("query must not be empty")
    spec = PRODUCTS[product]
    return {
        "source": "bra",
        "product": product,
        "product_label": spec["label"],
        "mode": "official_web_service_or_published_file",
        "product_url": spec["url"],
        "service_url": SERVICE_URL if product == "reported_crimes" else None,
        "help_url": HELP_URL if product == "reported_crimes" else None,
        "query": q,
        "requires_runtime_retrieval": True,
    }


def discovery_plan(query: str) -> dict[str, Any]:
    """Backward-compatible discovery plan for reported-crime statistics."""
    return product_discovery_plan("reported_crimes", query)


def _catalog(raw: Any, key: str) -> dict[str, dict[str, Any]]:
    if not isinstance(raw, list) or not raw:
        raise BraAdapterError(f"metadata snapshot must contain non-empty dimension {key}")
    result: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise BraAdapterError(f"invalid item in dimension {key}")
        code = item.get("code") or item.get("id")
        label = item.get("label") or item.get("name")
        if not isinstance(code, str) or not code or not isinstance(label, str) or not label:
            raise BraAdapterError(f"{key} item must contain code/id and label/name")
        result[code] = item
    return result


def validate_product_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    if snapshot.get("source") != "bra":
        raise BraAdapterError("snapshot source must be bra")
    product = snapshot.get("product")
    if product not in PRODUCTS:
        raise BraAdapterError("snapshot must describe a supported Brå product")

    raw_dimensions = snapshot.get("dimensions")
    # Backward compatibility for the original reported-crime snapshot shape.
    if raw_dimensions is None and product == "reported_crimes":
        raw_dimensions = {
            key: snapshot.get(key)
            for key in ("periods", "areas", "crimes", "units")
        }
    if not isinstance(raw_dimensions, dict):
        raise BraAdapterError("snapshot must contain dimensions")

    catalogs: dict[str, dict[str, dict[str, Any]]] = {}
    for key, raw in raw_dimensions.items():
        catalogs[key] = _catalog(raw, key)

    missing = [key for key in PRODUCTS[product]["required_dimensions"] if key not in catalogs]
    if missing:
        raise BraAdapterError(f"missing required dimensions for {product}: {', '.join(missing)}")

    status_values = snapshot.get("status_values") or ["preliminary", "final"]
    if not isinstance(status_values, list) or not status_values or not all(isinstance(v, str) for v in status_values):
        raise BraAdapterError("invalid status_values")

    source_url = snapshot.get("source_url") or PRODUCTS[product]["url"]
    if not isinstance(source_url, str) or not source_url.startswith("https://"):
        raise BraAdapterError("snapshot source_url must be an https URL")

    return {
        "product": product,
        "dimensions": catalogs,
        "status_values": set(status_values),
        "source_url": source_url,
    }


def validate_metadata_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Backward-compatible validator for reported-crime snapshots."""
    validated = validate_product_snapshot(snapshot)
    if validated["product"] != "reported_crimes":
        raise BraAdapterError("snapshot must describe Brå reported-crime statistics")
    dims = validated["dimensions"]
    return {
        "periods": dims["periods"],
        "areas": dims["areas"],
        "crimes": dims["crimes"],
        "units": dims["units"],
        "status_values": validated["status_values"],
    }


def _normalize_values(raw: Iterable[str] | str, *, label: str) -> list[str]:
    values = [raw] if isinstance(raw, str) else list(raw)
    if not values or any(not isinstance(v, str) or not v for v in values):
        raise BraAdapterError(f"at least one non-empty value is required for {label}")
    return values


def product_selection_plan(
    snapshot: dict[str, Any],
    *,
    selections: dict[str, Iterable[str] | str],
    status: str | None = None,
) -> dict[str, Any]:
    validated = validate_product_snapshot(snapshot)
    product = validated["product"]
    catalogs = validated["dimensions"]
    if not isinstance(selections, dict) or not selections:
        raise BraAdapterError("selections must be a non-empty mapping")

    normalized: dict[str, list[str]] = {}
    for dimension, raw_values in selections.items():
        if dimension not in catalogs:
            raise BraAdapterError(f"unknown dimension for {product}: {dimension}")
        values = _normalize_values(raw_values, label=dimension)
        unknown = [v for v in values if v not in catalogs[dimension]]
        if unknown:
            raise BraAdapterError(f"unknown {dimension} values: {', '.join(unknown)}")
        normalized[dimension] = values

    if status is not None and status not in validated["status_values"]:
        raise BraAdapterError(f"unknown publication status: {status}")

    cells = prod(len(values) for values in normalized.values())
    if cells > MAX_CELLS:
        raise BraAdapterError(f"selection exceeds Brå planning limit of {MAX_CELLS} data cells")

    return {
        "source": "bra",
        "product": product,
        "product_label": PRODUCTS[product]["label"],
        "retrieval_mode": snapshot.get("retrieval_mode", "official_web_service_or_published_file"),
        "source_url": validated["source_url"],
        "selection": {**normalized, "status": status},
        "estimated_cells": cells,
        "max_cells": MAX_CELLS,
        "requires_runtime_retrieval": True,
        "provenance_requirements": [
            "source_url",
            "retrieval_date",
            "product_definition",
            "dimension_definitions",
            "measure_or_unit",
            "publication_status",
        ],
        "method_notes": list(PRODUCTS[product]["method_notes"]),
    }


def reported_crimes_plan(
    snapshot: dict[str, Any],
    *,
    crimes: Iterable[str] | str,
    areas: Iterable[str] | str,
    periods: Iterable[str] | str,
    unit: str,
    status: str | None = None,
) -> dict[str, Any]:
    """Build a verified retrieval plan for reported-crime statistics."""
    catalogs = validate_metadata_snapshot(snapshot)
    selected = {
        "crimes": _normalize_values(crimes, label="crimes"),
        "areas": _normalize_values(areas, label="areas"),
        "periods": _normalize_values(periods, label="periods"),
    }
    for group, values in selected.items():
        unknown = [v for v in values if v not in catalogs[group]]
        if unknown:
            raise BraAdapterError(f"unknown {group} values: {', '.join(unknown)}")
    if unit not in catalogs["units"]:
        raise BraAdapterError(f"unknown unit: {unit}")
    if status is not None and status not in catalogs["status_values"]:
        raise BraAdapterError(f"unknown publication status: {status}")

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

    # Use the generic planner after the reported-crime-specific confidentiality gate.
    modern_snapshot = dict(snapshot)
    modern_snapshot["dimensions"] = {
        "periods": snapshot["periods"],
        "areas": snapshot["areas"],
        "crimes": snapshot["crimes"],
        "units": snapshot["units"],
    }
    plan = product_selection_plan(
        modern_snapshot,
        selections={
            "crimes": selected["crimes"],
            "areas": selected["areas"],
            "periods": selected["periods"],
            "units": [unit],
        },
        status=status,
    )
    plan["selection"] = {**selected, "unit": unit, "status": status}
    plan["provenance_requirements"] = [
        "source_url",
        "retrieval_date",
        "crime_definition",
        "area_definition",
        "period_definition",
        "unit",
        "publication_status",
    ]
    return plan
