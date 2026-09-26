#!/usr/bin/env python3
"""Metadata-first planner for Försäkringskassan open statistics API."""
from __future__ import annotations
import re
from urllib.parse import quote, urlparse

BASE_URL = "https://www.forsakringskassan.se/api/sprstatistikrapportera/public/v1"
DATASET_RE = re.compile(r"^[a-z0-9-]+$")

class ForsakringskassanAdapterError(ValueError):
    pass

def meta_url(dataset_id: str) -> str:
    dataset_id=dataset_id.strip().lower()
    if not DATASET_RE.fullmatch(dataset_id):
        raise ForsakringskassanAdapterError("invalid dataset_id")
    return f"{BASE_URL}/{quote(dataset_id)}/meta/json"

def validate_distribution_url(url: str) -> str:
    parsed=urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "www.forsakringskassan.se":
        raise ForsakringskassanAdapterError("distribution URL must use official Försäkringskassan host")
    if not parsed.path.startswith("/api/sprstatistikrapportera/public/v1/"):
        raise ForsakringskassanAdapterError("distribution URL must be below the public statistics API")
    return url
