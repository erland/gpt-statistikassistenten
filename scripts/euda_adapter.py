#!/usr/bin/env python3
"""Metadata-first planner for EUDA open drug datasets.

The first supported dataset family is EUDA/SCORE wastewater analysis. EUDA
publishes the source data as reusable CSV files and a factsheet that acts as
the canonical metadata/discovery page. The adapter deliberately keeps the
verified 2026 URLs explicit so later EUDA revisions cannot silently change the
meaning of an extraction.
"""
from __future__ import annotations
from urllib.parse import urlparse

FACTSHEET_URL = "https://www.euda.europa.eu/publications/pods/waste-water-analysis_en"
DATA_HOSTS = {"www.euda.europa.eu", "d9www.euda.europa.eu"}

WASTEWATER_2026 = {
    "all_data": "https://d9www.euda.europa.eu/sites/default/files/data/data-nodes/33337/versions/5/ww2026-all-data_en.csv",
    "site_info": "https://d9www.euda.europa.eu/sites/default/files/data/data-nodes/33337/versions/5/ww2026-site-info-table_en.csv",
}

class EudaAdapterError(ValueError):
    pass

def wastewater_metadata_url() -> str:
    return FACTSHEET_URL

def wastewater_source_url(kind: str) -> str:
    if kind not in WASTEWATER_2026:
        raise EudaAdapterError("kind must be all_data or site_info")
    return WASTEWATER_2026[kind]

def validate_official_data_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in DATA_HOSTS:
        raise EudaAdapterError("EUDA data URL must use an official EUDA host")
    if not (parsed.path.endswith(".csv") or parsed.path.endswith(".zip")):
        raise EudaAdapterError("EUDA data URL must point to a CSV or ZIP distribution")
    return url

def wastewater_plan(*, country: str | None = None, city: str | None = None,
                    substance: str | None = None, year: int | None = None) -> dict:
    if year is not None and (year < 2011 or year > 2025):
        raise EudaAdapterError("SCORE study year must be between 2011 and 2025 for the verified 2026 dataset")
    return {
        "metadata_url": FACTSHEET_URL,
        "data_url": WASTEWATER_2026["all_data"],
        "site_info_url": WASTEWATER_2026["site_info"],
        "filters": {
            "country": country,
            "city": city,
            "substance": substance,
            "year": year,
        },
        "unit": "mg/1000 population/day",
        "method_notes": [
            "Wastewater values are population-normalised residue loads, not counts of users or prevalence.",
            "Cocaine is measured through benzoylecgonine and cannabis through THC-COOH.",
            "Join site metadata by SiteID and preserve EUDA/SCORE attribution.",
        ],
    }
