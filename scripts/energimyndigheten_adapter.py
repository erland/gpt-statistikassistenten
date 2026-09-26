#!/usr/bin/env python3
"""Conservative planner for Energimyndigheten PxWeb API v1."""
from __future__ import annotations
from urllib.parse import quote

BASE_URL = "https://pxexternal.energimyndigheten.se/api/v1/sv/Energimyndighetens_statistikdatabas"

class EnergimyndighetenAdapterError(ValueError):
    pass

def root_url() -> str:
    return BASE_URL

def node_url(path: list[str]) -> str:
    if not path:
        return BASE_URL
    if any(not isinstance(x, str) or not x.strip() or "/" in x for x in path):
        raise EnergimyndighetenAdapterError("path segments must be non-empty and slash-free")
    return BASE_URL + "/" + "/".join(quote(x.strip(), safe="") for x in path)

def query_plan(table_url: str, selection: list[dict], *, response_format: str = "json") -> dict:
    if not table_url.startswith(BASE_URL + "/") or not table_url.lower().endswith(".px"):
        raise EnergimyndighetenAdapterError("table_url must point to an official PxWeb .px table")
    if not selection:
        raise EnergimyndighetenAdapterError("selection is required")
    query=[]
    for item in selection:
        code=item.get("code"); values=item.get("values")
        if not isinstance(code,str) or not code.strip() or not isinstance(values,list) or not values:
            raise EnergimyndighetenAdapterError("each selection needs code and values")
        query.append({"code":code.strip(),"selection":{"filter":"item","values":[str(v) for v in values]}})
    return {"method":"POST","url":table_url,"json":{"query":query,"response":{"format":response_format}}}
