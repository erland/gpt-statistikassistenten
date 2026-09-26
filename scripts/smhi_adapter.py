#!/usr/bin/env python3
"""Planner for SMHI Open Data MetObs API."""
from __future__ import annotations
import re
from urllib.parse import quote

BASE_URL = "https://opendata-download-metobs.smhi.se/api/version/latest"
ID_RE = re.compile(r"^\d+$")
PERIODS = {"latest-hour","latest-day","latest-months","corrected-archive"}

class SmhiAdapterError(ValueError):
    pass

def parameter_url(parameter_id: str | int) -> str:
    value=str(parameter_id)
    if not ID_RE.fullmatch(value):
        raise SmhiAdapterError("parameter_id must be numeric")
    return f"{BASE_URL}/parameter/{quote(value)}.json"

def station_url(parameter_id: str | int, station_id: str | int) -> str:
    p=str(parameter_id); s=str(station_id)
    if not ID_RE.fullmatch(p) or not ID_RE.fullmatch(s):
        raise SmhiAdapterError("parameter_id and station_id must be numeric")
    return f"{BASE_URL}/parameter/{p}/station/{s}.json"

def data_url(parameter_id: str | int, station_id: str | int, period: str) -> str:
    if period not in PERIODS:
        raise SmhiAdapterError("unsupported period")
    base=station_url(parameter_id,station_id).removesuffix(".json")
    return f"{base}/period/{quote(period)}/data.json"
