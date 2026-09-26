#!/usr/bin/env python3
"""Metadata-first planner for ECB Data Portal SDMX 2.1 web services."""
from __future__ import annotations
from urllib.parse import quote, urlencode

BASE_URL="https://data-api.ecb.europa.eu/service"

class EcbAdapterError(ValueError): pass

def dataflow_url() -> str:
    return f"{BASE_URL}/dataflow"

def data_url(flow_ref: str, key: str, *, start_period: str | None = None, end_period: str | None = None, detail: str = "dataonly") -> str:
    if not flow_ref or "/" in flow_ref or " " in flow_ref:
        raise EcbAdapterError("flow_ref must come from verified ECB metadata")
    if not key or "/" in key or " " in key:
        raise EcbAdapterError("key must come from verified ECB metadata")
    params={"detail":detail}
    if start_period: params["startPeriod"]=start_period
    if end_period: params["endPeriod"]=end_period
    return f"{BASE_URL}/data/{quote(flow_ref,safe=',')}/{quote(key,safe='.+')}"+"?"+urlencode(params)
