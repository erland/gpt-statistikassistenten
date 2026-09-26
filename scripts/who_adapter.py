#!/usr/bin/env python3
"""Fallback planner for WHO World Health Data Hub.

The legacy GHO OData interface was scheduled for deprecation. This adapter
therefore exposes only current official hub URLs and validates download links;
runtime must verify the current data.who.int export/API path before use.
"""
from __future__ import annotations
from urllib.parse import urlparse

BASE_URL="https://data.who.int"

class WhoAdapterError(ValueError): pass

def hub_url() -> str:
    return BASE_URL

def indicators_url() -> str:
    return f"{BASE_URL}/indicators"

def validate_official_url(url: str) -> str:
    parsed=urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in {"data.who.int","www.who.int"}:
        raise WhoAdapterError("WHO URL must use an official WHO host")
    return url
