#!/usr/bin/env python3
"""Conservative SDMX planner for OECD Data Explorer."""
from __future__ import annotations
import re
from urllib.parse import quote, urlencode

BASE_URL="https://sdmx.oecd.org/public/rest"
SAFE=re.compile(r"^[A-Za-z0-9_.@-]+$")

class OecdAdapterError(ValueError): pass

def dataflow_url(agency: str, flow_id: str, version: str = "latest") -> str:
    for value in (agency,flow_id,version):
        if not SAFE.fullmatch(value): raise OecdAdapterError("invalid SDMX identifier")
    return f"{BASE_URL}/dataflow/{quote(agency, safe='._-')}/{quote(flow_id, safe='.@_-')}/{quote(version, safe='._-')}?references=all"

def data_url(flow_ref: str, key: str = "all", *, start_period: str | None = None, end_period: str | None = None) -> str:
    if not flow_ref or "/" in flow_ref or " " in flow_ref:
        raise OecdAdapterError("flow_ref must be copied from verified OECD metadata")
    if not key or "/" in key or " " in key:
        raise OecdAdapterError("key must be copied from verified OECD metadata")
    params={"dimension_at_observation":"AllDimensions"}
    if start_period: params["startPeriod"]=start_period
    if end_period: params["endPeriod"]=end_period
    return f"{BASE_URL}/data/{quote(flow_ref,safe=',.@')}/{quote(key,safe='.+')}"+"?"+urlencode(params)
