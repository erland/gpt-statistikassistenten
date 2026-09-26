#!/usr/bin/env python3
"""Deterministic helpers for planning SCB PxWebApi v2 requests.

The module intentionally performs no network requests. Runtime-specific tooling
fetches /tables and /metadata, then passes verified metadata to these helpers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlencode

BASE_URL = "https://statistikdatabasen.scb.se/api/v2"
MAX_CELLS = 150_000


class ScbAdapterError(ValueError):
    pass


def search_url(query: str, *, lang: str = "sv", page_size: int = 10) -> str:
    query = query.strip()
    if not query:
        raise ScbAdapterError("search query must not be empty")
    if lang not in {"sv", "en"}:
        raise ScbAdapterError("lang must be sv or en")
    if not 1 <= page_size <= 100:
        raise ScbAdapterError("page_size must be between 1 and 100")
    return f"{BASE_URL}/tables?" + urlencode({"lang": lang, "query": query, "pageSize": page_size})


def metadata_url(table_id: str, *, lang: str = "sv") -> str:
    if not table_id:
        raise ScbAdapterError("table_id is required")
    return f"{BASE_URL}/tables/{table_id}/metadata?" + urlencode({"lang": lang})


def _metadata_variables(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    # PxWebApi implementations expose variables/dimensions under slightly
    # different wrapper names. Accept the documented/common shapes but never
    # invent a variable when none is present.
    for key in ("variables", "dimension", "dimensions"):
        value = metadata.get(key)
        if isinstance(value, list):
            return value
    if isinstance(metadata.get("dataset"), dict):
        for key in ("variables", "dimension", "dimensions"):
            value = metadata["dataset"].get(key)
            if isinstance(value, list):
                return value
    raise ScbAdapterError("metadata does not contain a supported variable list")


def _code(var: dict[str, Any]) -> str:
    for key in ("code", "id", "variableCode"):
        value = var.get(key)
        if isinstance(value, str) and value:
            return value
    raise ScbAdapterError("metadata variable lacks code")


def _values(var: dict[str, Any]) -> set[str]:
    raw = var.get("values") or var.get("valueCodes") or []
    out: set[str] = set()
    for value in raw:
        if isinstance(value, str):
            out.add(value)
        elif isinstance(value, dict):
            code = value.get("code") or value.get("id") or value.get("value")
            if isinstance(code, str):
                out.add(code)
    return out


def _mandatory(var: dict[str, Any]) -> bool:
    if var.get("mandatory") is True:
        return True
    if var.get("elimination") is False:
        return True
    return False


def validate_selection(metadata: dict[str, Any], selection: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    variables = {_code(v): v for v in _metadata_variables(metadata)}
    normalized: list[dict[str, Any]] = []
    selected_codes: set[str] = set()

    for item in selection:
        code = item.get("variableCode")
        vals = item.get("valueCodes")
        if code not in variables:
            raise ScbAdapterError(f"unknown variableCode: {code}")
        if not isinstance(vals, list) or not vals:
            raise ScbAdapterError(f"valueCodes required for {code}")
        allowed = _values(variables[code])
        # Selectors such as top(5) are allowed by PxWebApi v2 and are not
        # literal metadata values. Everything else must be verified.
        for val in vals:
            if not isinstance(val, str):
                raise ScbAdapterError(f"non-string valueCode for {code}")
            is_selector = val.startswith("top(") or val.startswith("bottom(") or val == "*"
            if allowed and val not in allowed and not is_selector:
                raise ScbAdapterError(f"unknown valueCode {val!r} for {code}")
        normalized.append({
            "variableCode": code,
            "valueCodes": vals,
            **({"codelist": item.get("codelist")} if "codelist" in item else {}),
        })
        selected_codes.add(code)

    missing = [code for code, var in variables.items() if _mandatory(var) and code not in selected_codes]
    if missing:
        raise ScbAdapterError("missing mandatory variables: " + ", ".join(sorted(missing)))
    return normalized


def estimate_cells(selection: Iterable[dict[str, Any]]) -> int:
    cells = 1
    for item in selection:
        values = item.get("valueCodes", [])
        if any(v == "*" or v.startswith("top(") or v.startswith("bottom(") for v in values):
            raise ScbAdapterError("cannot estimate cells for dynamic selectors")
        cells *= len(values)
        if cells > MAX_CELLS:
            raise ScbAdapterError(f"selection exceeds SCB max cells ({MAX_CELLS})")
    return cells


def post_request_plan(table_id: str, metadata: dict[str, Any], selection: list[dict[str, Any]], *, lang: str = "sv") -> dict[str, Any]:
    checked = validate_selection(metadata, selection)
    try:
        cells = estimate_cells(checked)
    except ScbAdapterError as exc:
        if "dynamic selectors" in str(exc):
            cells = None
        else:
            raise
    return {
        "method": "POST",
        "url": f"{BASE_URL}/tables/{table_id}/data?" + urlencode({"lang": lang, "outputFormat": "json-stat2"}),
        "body": {"selection": checked},
        "estimated_cells": cells,
    }
