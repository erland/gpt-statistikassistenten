#!/usr/bin/env python3
"""Metadata-first planner for World Bank Indicators API v2."""
from __future__ import annotations
import re
from urllib.parse import quote, urlencode

BASE_URL="https://api.worldbank.org/v2"
INDICATOR_RE=re.compile(r"^[A-Z0-9_.-]+$", re.I)
COUNTRY_RE=re.compile(r"^[A-Z0-9]{2,3}$", re.I)
YEAR_RE=re.compile(r"^\d{4}$")

class WorldBankAdapterError(ValueError): pass

def indicators_url(*, page: int = 1, per_page: int = 100) -> str:
    if page < 1 or not 1 <= per_page <= 1000:
        raise WorldBankAdapterError("invalid pagination")
    return f"{BASE_URL}/indicator?"+urlencode({"format":"json","page":page,"per_page":per_page})

def indicator_metadata_url(indicator_id: str) -> str:
    code=indicator_id.strip().upper()
    if not INDICATOR_RE.fullmatch(code):
        raise WorldBankAdapterError("invalid indicator_id")
    return f"{BASE_URL}/indicator/{quote(code)}?format=json"

def data_url(indicator_id: str, countries: list[str], *, from_year: str | None = None, to_year: str | None = None, per_page: int = 1000) -> str:
    code=indicator_id.strip().upper()
    if not INDICATOR_RE.fullmatch(code) or not countries:
        raise WorldBankAdapterError("verified indicator_id and countries are required")
    normalized=[]
    for country in countries:
        c=country.strip().upper()
        if not COUNTRY_RE.fullmatch(c):
            raise WorldBankAdapterError("country codes must be verified 2-3 character codes")
        normalized.append(c)
    params={"format":"json","per_page":per_page}
    if from_year or to_year:
        if not from_year or not YEAR_RE.fullmatch(from_year) or (to_year is not None and not YEAR_RE.fullmatch(to_year)):
            raise WorldBankAdapterError("years must be YYYY")
        params["date"]=from_year if to_year is None else f"{from_year}:{to_year}"
    return f"{BASE_URL}/country/{';'.join(normalized)}/indicator/{quote(code)}?"+urlencode(params)
