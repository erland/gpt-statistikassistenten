#!/usr/bin/env python3
"""Planner for Arbetsförmedlingen/JobTech public JobSearch API."""
from __future__ import annotations
from urllib.parse import urlencode
BASE_URL="https://jobsearch.api.jobtechdev.se"
class ArbetsformedlingenAdapterError(ValueError): pass

def search_url(query: str, *, limit: int = 20, offset: int = 0, municipality: str | None = None, occupation_field: str | None = None) -> str:
    query=query.strip()
    if not query: raise ArbetsformedlingenAdapterError("query is required")
    if not 1 <= limit <= 100: raise ArbetsformedlingenAdapterError("limit must be 1..100")
    if offset < 0: raise ArbetsformedlingenAdapterError("offset must be >= 0")
    params={"q":query,"limit":limit,"offset":offset}
    if municipality: params["municipality"]=municipality
    if occupation_field: params["occupation-field"]=occupation_field
    return f"{BASE_URL}/search?"+urlencode(params)

def normalize_summary(payload: dict) -> dict:
    total=(payload.get("total") or {}).get("value") if isinstance(payload.get("total"),dict) else payload.get("total")
    hits=payload.get("hits")
    if not isinstance(hits,list): raise ArbetsformedlingenAdapterError("response lacks hits list")
    return {"total": total, "returned": len(hits), "hits": hits}
