#!/usr/bin/env python3
"""Deterministic helpers for Kolada API v3.

No network calls are performed. Runtime tooling discovers KPI/municipality metadata
from the official API and passes verified identifiers to these helpers.
"""
from __future__ import annotations
import re
from urllib.parse import quote, urlencode

BASE_URL = "https://api.kolada.se/v3"
KPI_RE = re.compile(r"^[NU]\d{5}$")
AREA_RE = re.compile(r"^\d{4}$")

class KoladaAdapterError(ValueError): pass

def docs_url() -> str:
    return f"{BASE_URL}/docs"

def kpi_metadata_url(kpi_id: str) -> str:
    kpi_id = kpi_id.strip().upper()
    if not KPI_RE.fullmatch(kpi_id):
        raise KoladaAdapterError("kpi_id must match N/U + five digits")
    return f"{BASE_URL}/kpi/{quote(kpi_id)}"

def municipality_metadata_url(municipality_id: str) -> str:
    municipality_id = municipality_id.strip()
    if not AREA_RE.fullmatch(municipality_id):
        raise KoladaAdapterError("municipality_id must be a four-digit code")
    return f"{BASE_URL}/municipality/{quote(municipality_id)}"

def data_url(*, municipality_id: str, kpi_id: str, from_date: str | None = None) -> str:
    municipality_id = municipality_id.strip()
    kpi_id = kpi_id.strip().upper()
    if not AREA_RE.fullmatch(municipality_id):
        raise KoladaAdapterError("municipality_id must be a four-digit code")
    if not KPI_RE.fullmatch(kpi_id):
        raise KoladaAdapterError("kpi_id must match N/U + five digits")
    url = f"{BASE_URL}/data/municipality/{municipality_id}/kpi/{kpi_id}"
    return url + ("?" + urlencode({"from_date": from_date}) if from_date else "")

def validate_kpi_metadata(metadata: dict, *, expected_id: str) -> dict:
    actual = str(metadata.get("id") or "").upper()
    expected = expected_id.strip().upper()
    if actual != expected or not KPI_RE.fullmatch(actual):
        raise KoladaAdapterError("KPI metadata does not match expected id")
    title = metadata.get("title")
    description = metadata.get("description")
    if not isinstance(title, str) or not title.strip():
        raise KoladaAdapterError("KPI metadata lacks title")
    if not isinstance(description, str) or not description.strip():
        raise KoladaAdapterError("KPI metadata lacks description/source context")
    return {"id": actual, "title": title.strip(), "description": description.strip(),
            "publication_period": metadata.get("publication_period"),
            "publication_date": metadata.get("publication_date"),
            "prel_publication_date": metadata.get("prel_publication_date")}
