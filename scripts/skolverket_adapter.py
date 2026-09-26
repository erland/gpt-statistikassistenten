#!/usr/bin/env python3
"""Conservative helper for Skolverket open REST APIs."""
from __future__ import annotations
from urllib.parse import urlparse

PLANNED_DOCS = "https://api.skolverket.se/planned-educations/swagger-ui/index.html"
PLANNED_PREFIX = "/planned-educations/"
V3_ACCEPT = "application/vnd.skolverket.plannededucations.api.v3.hal+json"

class SkolverketAdapterError(ValueError):
    pass

def planned_educations_docs_url() -> str:
    return PLANNED_DOCS

def request_plan(url: str) -> dict:
    parsed=urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "api.skolverket.se":
        raise SkolverketAdapterError("URL must use api.skolverket.se")
    if not parsed.path.startswith(PLANNED_PREFIX):
        raise SkolverketAdapterError("URL must belong to Planned educations API")
    return {"method":"GET","url":url,"headers":{"Accept":V3_ACCEPT}}
