#!/usr/bin/env python3
"""Planner for Sveriges Riksbank SWEA v1 (rates and exchange rates)."""
from __future__ import annotations
import re
from urllib.parse import quote
BASE_URL="https://api.riksbank.se/swea/v1"
SERIES_RE=re.compile(r"^[A-Za-z0-9_]+$")
DATE_RE=re.compile(r"^\d{4}-\d{2}-\d{2}$")
class RiksbankAdapterError(ValueError): pass

def series_catalog_url() -> str: return f"{BASE_URL}/Series"
def groups_url() -> str: return f"{BASE_URL}/Groups"
def latest_url(series_id: str) -> str:
    if not SERIES_RE.fullmatch(series_id): raise RiksbankAdapterError("invalid series_id")
    return f"{BASE_URL}/Observations/Latest/{quote(series_id)}"
def observations_url(series_id: str, from_date: str, to_date: str | None = None) -> str:
    if not SERIES_RE.fullmatch(series_id): raise RiksbankAdapterError("invalid series_id")
    if not DATE_RE.fullmatch(from_date) or (to_date is not None and not DATE_RE.fullmatch(to_date)):
        raise RiksbankAdapterError("dates must be YYYY-MM-DD")
    url=f"{BASE_URL}/Observations/{quote(series_id)}/{from_date}"
    return url + (f"/{to_date}" if to_date else "")
