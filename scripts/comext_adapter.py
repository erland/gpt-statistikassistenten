#!/usr/bin/env python3
"""Deterministic helpers for planning Eurostat Comext requests.

The module performs no network access. Runtime tooling must first retrieve the
Comext dataflow/structure metadata and normalize it to the shape accepted here.
Only filtered DS-prefixed requests are allowed.
"""
from __future__ import annotations

from typing import Any, Iterable
from urllib.parse import urlencode

BASE_URL = "https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/3.0"
AGENCY = "ESTAT"
REQUIRED_ROLES = ("reporter", "partner", "flow", "product", "time", "indicator")


class ComextAdapterError(ValueError):
    pass


def _dataset_id(dataset_id: str) -> str:
    value = dataset_id.strip().upper()
    if not value.startswith("DS-"):
        raise ComextAdapterError("Comext dataset_id must use the DS- prefix")
    if len(value) <= 3:
        raise ComextAdapterError("invalid Comext dataset_id")
    return value


def dataflow_catalog_url() -> str:
    return f"{BASE_URL}/structure/dataflow/{AGENCY}/*/~"


def structure_url(dataset_id: str) -> str:
    dataset = _dataset_id(dataset_id)
    params = urlencode({"detail": "allstubs", "references": "all"})
    return f"{BASE_URL}/structure/dataflow/{AGENCY}/{dataset}/~?{params}"


def _dimensions(structure: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = structure.get("dimensions") or structure.get("components")
    if not isinstance(raw, list) or not raw:
        raise ComextAdapterError("structure must contain dimensions/components")
    result: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise ComextAdapterError("invalid component in structure")
        dim_id = item.get("id") or item.get("code")
        if not isinstance(dim_id, str) or not dim_id:
            raise ComextAdapterError("component lacks id")
        result[dim_id.upper()] = item
    return result


def _allowed_values(dimension: dict[str, Any]) -> set[str]:
    raw = dimension.get("values") or dimension.get("codes") or []
    result: set[str] = set()
    for item in raw:
        if isinstance(item, str):
            result.add(item)
        elif isinstance(item, dict):
            value = item.get("id") or item.get("code") or item.get("value")
            if isinstance(value, str):
                result.add(value)
    return result


def validate_role_map(structure: dict[str, Any]) -> dict[str, str]:
    """Validate semantic Comext roles against actual dataset dimensions."""
    dimensions = _dimensions(structure)
    raw_roles = structure.get("roles")
    if not isinstance(raw_roles, dict):
        raise ComextAdapterError("structure.roles is required for Comext semantic mapping")

    role_map: dict[str, str] = {}
    for role in REQUIRED_ROLES:
        dim = raw_roles.get(role)
        if not isinstance(dim, str) or not dim:
            raise ComextAdapterError(f"missing Comext semantic role: {role}")
        dim_upper = dim.upper()
        if dim_upper not in dimensions:
            raise ComextAdapterError(f"role {role} points to unknown dimension {dim}")
        role_map[role] = dim_upper
    return role_map


def _normalize_values(raw: Iterable[str] | str, *, label: str) -> list[str]:
    values = [raw] if isinstance(raw, str) else list(raw)
    if not values or any(not isinstance(v, str) or not v for v in values):
        raise ComextAdapterError(f"at least one non-empty value is required for {label}")
    return values


def _validate_dimension_values(
    dimensions: dict[str, dict[str, Any]], dimension_id: str, values: list[str], *, allow_time_operators: bool = False
) -> None:
    allowed = _allowed_values(dimensions[dimension_id])
    for value in values:
        is_time_operator = allow_time_operators and any(value.startswith(p) for p in ("ge:", "gt:", "le:", "lt:", "eq:", "ne:"))
        if allowed and value not in allowed and not is_time_operator:
            raise ComextAdapterError(f"unknown value {value!r} for {dimension_id}")


def trade_request_plan(
    dataset_id: str,
    structure: dict[str, Any],
    *,
    reporter: Iterable[str] | str,
    partner: Iterable[str] | str,
    flow: Iterable[str] | str,
    product: Iterable[str] | str,
    period: Iterable[str] | str,
    indicator: Iterable[str] | str,
    frequency: Iterable[str] | str | None = None,
    response_format: str = "csv",
) -> dict[str, Any]:
    """Build a verified, filtered Comext request from semantic trade roles."""
    dataset = _dataset_id(dataset_id)
    dimensions = _dimensions(structure)
    roles = validate_role_map(structure)

    semantic = {
        "reporter": _normalize_values(reporter, label="reporter"),
        "partner": _normalize_values(partner, label="partner"),
        "flow": _normalize_values(flow, label="flow"),
        "product": _normalize_values(product, label="product"),
        "time": _normalize_values(period, label="period"),
        "indicator": _normalize_values(indicator, label="indicator"),
    }
    filters: dict[str, list[str]] = {}
    for role, values in semantic.items():
        dimension_id = roles[role]
        _validate_dimension_values(dimensions, dimension_id, values, allow_time_operators=(role == "time"))
        filters[dimension_id] = values

    if frequency is not None:
        raw_freq_dim = (structure.get("roles") or {}).get("frequency")
        if not isinstance(raw_freq_dim, str) or raw_freq_dim.upper() not in dimensions:
            raise ComextAdapterError("frequency supplied but structure has no valid frequency role")
        freq_dim = raw_freq_dim.upper()
        freq_values = _normalize_values(frequency, label="frequency")
        _validate_dimension_values(dimensions, freq_dim, freq_values)
        filters[freq_dim] = freq_values

    # Comext explicitly disallows unfiltered full-dataset downloads. Requiring
    # all core trade dimensions also prevents accidental huge Cartesian queries.
    if len(filters) < 6:
        raise ComextAdapterError("Comext requests must remain explicitly filtered")

    if response_format not in {"csv", "xml"}:
        raise ComextAdapterError("response_format must be csv or xml")

    query: list[tuple[str, str]] = []
    for dimension_id, values in filters.items():
        separator = "+" if dimension_id == roles["time"] and all(":" in v for v in values) else ","
        query.append((f"c[{dimension_id}]", separator.join(values)))
    query.extend([("attributes", "dsd"), ("measures", "all")])

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
        "semantic_selection": semantic,
        "filters": filters,
        "role_map": roles,
    }
