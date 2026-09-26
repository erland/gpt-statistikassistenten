#!/usr/bin/env python3
"""Conservative planner for Folkhälsomyndigheten Folkhälsodata PxWeb API v1."""
from __future__ import annotations
from urllib.parse import quote

BASE_URL = "https://fohm-app.folkhalsomyndigheten.se/Folkhalsodata/api/v1/sv/A_Folkhalsodata"
class FolkhalsodataAdapterError(ValueError): pass

def root_url() -> str: return BASE_URL

def node_url(path: list[str]) -> str:
    if not path: return BASE_URL
    if any(not isinstance(x,str) or not x.strip() or "/" in x for x in path):
        raise FolkhalsodataAdapterError("path segments must be non-empty and slash-free")
    return BASE_URL + "/" + "/".join(quote(x.strip(), safe="") for x in path)

def query_plan(table_url: str, selection: list[dict], *, response_format: str = "json-stat2") -> dict:
    if not table_url.startswith(BASE_URL + "/"):
        raise FolkhalsodataAdapterError("table_url must be below official Folkhälsodata API root")
    if not selection: raise FolkhalsodataAdapterError("selection is required")
    normalized=[]
    for item in selection:
        code=item.get("code"); values=item.get("values")
        if not isinstance(code,str) or not code or not isinstance(values,list) or not values:
            raise FolkhalsodataAdapterError("each selection needs code and values")
        normalized.append({"code": code, "selection": {"filter": "item", "values": [str(v) for v in values]}})
    return {"method":"POST","url":table_url,"json":{"query":normalized,"response":{"format":response_format}}}
