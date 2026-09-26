#!/usr/bin/env python3
"""Deterministic helpers for planning Eurostat SDMX 3.0 requests.

This module performs no network access. Runtime-specific tooling retrieves the
Eurostat dataflow catalogue and structure metadata, then passes a normalized
structure description to these helpers before any data request is issued.
"""
from __future__ import annotations

from typing import Any, Iterable
from urllib.parse import urlencode

BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/3.0"
AGENCY = "ESTAT"


class EurostatAdapterError(ValueError):
    pass


def _dataset_id(dataset_id: str) -> str:
    value = dataset_id.strip()
    if not value:
        raise EurostatAdapterError("dataset_id is required")
    if value.upper().startswith("DS-"):
        raise EurostatAdapterError("DS- datasets belong to the Comext adapter")
    return value.upper()


def dataflow_catalog_url() -> str:
    """Return the official SDMX 3.0 catalogue endpoint for public dataflows."""
    return f"{BASE_URL}/structure/dataflow/*/*/~"


def structure_url(dataset_id: str, *, references: str = "all") -> str:
    """Return a structure query that can resolve the dataflow and its DSD/codelists."""
    dataset = _dataset_id(dataset_id)
    if references not in {"all", "descendants", "children", "none"}:
        raise EurostatAdapterError("unsupported references mode")
    params = {"detail": "allstubs"}
    if references != "none":
        params["references"] = references
    return f"{BASE_URL}/structure/dataflow/{AGENCY}/{dataset}/~?" + urlencode(params)


def _components(structure: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = structure.get("dimensions") or structure.get("components")
    if not isinstance(raw, list) or not raw:
        raise EurostatAdapterError("structure must contain dimensions/components")
    out: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise EurostatAdapterError("invalid component in structure")
        code = item.get("id") or item.get("code")
        if not isinstance(code, str) or not code:
            raise EurostatAdapterError("component lacks id")
        out[code.upper()] = item
    return out


def _allowed_values(component: dict[str, Any]) -> set[str]:
    raw = component.get("values") or component.get("codes") or []
    values: set[str] = set()
    for item in raw:
        if isinstance(item, str):
            values.add(item)
        elif isinstance(item, dict):
            value = item.get("id") or item.get("code") or item.get("value")
            if isinstance(value, str):
                values.add(value)
    return values


def validate_filters(structure: dict[str, Any], filters: dict[str, Iterable[str] | str]) -> dict[str, list[str]]:
    """Verify filter dimensions and codes against retrieved structure metadata."""
    components = _components(structure)
    normalized: dict[str, list[str]] = {}
    for raw_code, raw_values in filters.items():
        code = raw_code.upper()
        if code not in components:
            raise EurostatAdapterError(f"unknown dimension: {raw_code}")
        values = [raw_values] if isinstance(raw_values, str) else list(raw_values)
        if not values:
            raise EurostatAdapterError(f"at least one value is required for {code}")
        allowed = _allowed_values(components[code])
        for value in values:
            if not isinstance(value, str) or not value:
                raise EurostatAdapterError(f"invalid value for {code}")
            # TIME_PERIOD ranges use SDMX operators and cannot be enumerated in a codelist.
            is_operator = code == "TIME_PERIOD" and any(value.startswith(prefix) for prefix in ("ge:", "gt:", "le:", "lt:", "eq:", "ne:"))
            if allowed and value not in allowed and not is_operator:
                raise EurostatAdapterError(f"unknown value {value!r} for {code}")
        normalized[code] = values
    return normalized


def data_request_plan(
    dataset_id: str,
    structure: dict[str, Any],
    filters: dict[str, Iterable[str] | str],
    *,
    attributes: str = "none",
    measures: str = "all",
    response_format: str = "csv",
) -> dict[str, Any]:
    """Build a verified SDMX 3.0 data request using component-value filters."""
    dataset = _dataset_id(dataset_id)
    checked = validate_filters(structure, filters)
    if attributes not in {"all", "dsd", "dataset", "series", "obs", "none"}:
        raise EurostatAdapterError("unsupported attributes setting")
    if measures not in {"all", "none"}:
        raise EurostatAdapterError("unsupported measures setting")
    if response_format not in {"csv", "xml"}:
        raise EurostatAdapterError("response_format must be csv or xml")

    query: list[tuple[str, str]] = []
    for dimension, values in checked.items():
        # Commas are OR; '+' combines range predicates for TIME_PERIOD.
        separator = "+" if dimension == "TIME_PERIOD" and all(":" in v for v in values) else ","
        query.append((f"c[{dimension}]", separator.join(values)))
    query.extend([("attributes", attributes), ("measures", measures)])
    url = f"{BASE_URL}/data/dataflow/{AGENCY}/{dataset}/1.0/*?" + urlencode(query, safe="[],:+")
    accept = (
        "application/vnd.sdmx.data+csv;version=2.0.0;labels=both"
        if response_format == "csv"
        else "application/vnd.sdmx.data+xml;version=3.0.0"
    )
    return {
        "method": "GET",
        "url": url,
        "headers": {"Accept": accept},
        "dataset_id": dataset,
        "filters": checked,
    }
