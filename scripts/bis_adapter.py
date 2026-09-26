#!/usr/bin/env python3
"""Conservative SDMX v2 planner for BIS statistics."""
from __future__ import annotations
import re
from urllib.parse import quote

BASE_URL="https://stats.bis.org/api/v2"
SAFE=re.compile(r"^[A-Za-z0-9_.@-]+$")

class BisAdapterError(ValueError): pass

def structure_url(structure_type: str, agency: str = "BIS", resource_id: str = "all", version: str = "latest") -> str:
    for value in (structure_type,agency,resource_id,version):
        if not SAFE.fullmatch(value): raise BisAdapterError("invalid SDMX identifier")
    return f"{BASE_URL}/structure/{quote(structure_type)}/{quote(agency)}/{quote(resource_id)}/{quote(version)}"

def data_url(context: str, agency: str, resource_id: str, version: str, key: str) -> str:
    for value in (context,agency,resource_id,version):
        if not SAFE.fullmatch(value): raise BisAdapterError("invalid SDMX identifier")
    if not key or "/" in key or " " in key:
        raise BisAdapterError("key must come from verified metadata")
    return f"{BASE_URL}/data/{quote(context)}/{quote(agency)}/{quote(resource_id)}/{quote(version)}/{quote(key,safe='.+')}"
