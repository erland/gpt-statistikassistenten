#!/usr/bin/env python3
"""URL planner for Socialstyrelsen Statistikdatabasen API v1."""
from __future__ import annotations
import re
from urllib.parse import quote, urlencode

BASE_URL = "https://sdb.socialstyrelsen.se/api/v1"
SAFE = re.compile(r"^[a-z0-9_-]+$", re.I)

class SocialstyrelsenAdapterError(ValueError): pass

def subjects_url(*, lang: str = "sv") -> str:
    if lang not in {"sv", "en"}: raise SocialstyrelsenAdapterError("lang must be sv or en")
    return f"{BASE_URL}/{lang}"

def dimension_url(subject: str, dimension: str, *, lang: str = "sv") -> str:
    if lang not in {"sv", "en"}: raise SocialstyrelsenAdapterError("lang must be sv or en")
    if not SAFE.fullmatch(subject) or not SAFE.fullmatch(dimension):
        raise SocialstyrelsenAdapterError("subject/dimension contains unsupported characters")
    return f"{BASE_URL}/{lang}/{quote(subject)}/{quote(dimension)}"

def result_url(subject: str, filters: list[tuple[str, list[str]]], *, lang: str = "sv", per_page: int = 5000, page: int = 1) -> str:
    if lang not in {"sv", "en"}: raise SocialstyrelsenAdapterError("lang must be sv or en")
    if not SAFE.fullmatch(subject): raise SocialstyrelsenAdapterError("invalid subject")
    if not 1 <= per_page <= 5000: raise SocialstyrelsenAdapterError("per_page must be 1..5000")
    if page < 1: raise SocialstyrelsenAdapterError("page must be >= 1")
    parts = [BASE_URL, lang, quote(subject), "resultat"]
    seen=set()
    for dim, values in filters:
        if not SAFE.fullmatch(dim) or dim in seen or not values:
            raise SocialstyrelsenAdapterError("invalid or duplicate filter dimension")
        if any("/" in str(v) for v in values): raise SocialstyrelsenAdapterError("invalid filter value")
        seen.add(dim); parts += [quote(dim), quote(",".join(map(str, values)), safe=",")]
    return "/".join(parts) + "?" + urlencode({"per_sida": per_page, "sida": page})
