#!/usr/bin/env python3
"""Planner for Statskontoret open state-budget and agency-directory data.

Statskontoret publishes the relevant datasets as official open-data pages with
CSV/Excel distributions. The adapter deliberately plans discovery from those
pages and validates the selected official distribution URL instead of assuming
an undocumented API or hard-coding transient file names.
"""
from __future__ import annotations
from urllib.parse import urlparse

MONTHLY_URL = "https://www.statskontoret.se/analys-och-statistik/oppna-data/manadsutfall/"
ANNUAL_URL = "https://www.statskontoret.se/analys-och-statistik/oppna-data/arsutfall/"
AGENCY_DIRECTORY_URL = "https://www.statskontoret.se/analys-och-statistik/oppna-data/myndighetsforteckning/"
OFFICIAL_HOSTS = {"statskontoret.se", "www.statskontoret.se"}
PRODUCTS = {
    "monthly_budget_outturn": {
        "url": MONTHLY_URL,
        "formats": ("csv", "xlsx"),
        "notes": "Monthly state-budget outturn; expenditure is available by appropriation item/sub-item and agency.",
    },
    "annual_budget_outturn": {
        "url": ANNUAL_URL,
        "formats": ("csv", "xlsx"),
        "notes": "Annual state-budget outturn; expenditure files contain both budget values and outturn by appropriation.",
    },
    "agency_directory": {
        "url": AGENCY_DIRECTORY_URL,
        "formats": ("xlsx",),
        "notes": "Agency directory with annual work units and organisational metadata; population differs from SCB's agency register.",
    },
}

class StatskontoretAdapterError(ValueError):
    pass

def available_products() -> list[str]:
    return sorted(PRODUCTS)

def discovery_url(product: str) -> str:
    if product not in PRODUCTS:
        raise StatskontoretAdapterError("unsupported product")
    return PRODUCTS[product]["url"]

def validate_distribution_url(product: str, url: str) -> str:
    if product not in PRODUCTS:
        raise StatskontoretAdapterError("unsupported product")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() not in OFFICIAL_HOSTS:
        raise StatskontoretAdapterError("distribution URL must use an official Statskontoret host")
    path = parsed.path.lower()
    allowed = PRODUCTS[product]["formats"]
    if not any(path.endswith("." + ext) for ext in allowed):
        raise StatskontoretAdapterError(
            "distribution format must be one of: " + ", ".join(allowed)
        )
    return url

def data_plan(product: str, *, year: int | None = None, month: int | None = None,
              agency: str | None = None, appropriation: str | None = None) -> dict:
    if product not in PRODUCTS:
        raise StatskontoretAdapterError("unsupported product")
    if year is not None and (year < 2006 or year > 2100):
        raise StatskontoretAdapterError("year must be 2006 or later")
    if month is not None:
        if product != "monthly_budget_outturn":
            raise StatskontoretAdapterError("month is only valid for monthly_budget_outturn")
        if month < 1 or month > 12:
            raise StatskontoretAdapterError("month must be between 1 and 12")
    if agency is not None and (not isinstance(agency, str) or not agency.strip()):
        raise StatskontoretAdapterError("agency must be a non-empty string when provided")
    if appropriation is not None and product == "agency_directory":
        raise StatskontoretAdapterError("appropriation is not valid for agency_directory")
    return {
        "product": product,
        "discovery_url": PRODUCTS[product]["url"],
        "method": "official-open-data-distribution",
        "preferred_formats": list(PRODUCTS[product]["formats"]),
        "filters": {
            "year": year,
            "month": month,
            "agency": agency,
            "appropriation": appropriation,
        },
        "instructions": [
            "Open the official Statskontoret product page and select the current published CSV/Excel distribution there.",
            "Validate the selected distribution URL with validate_distribution_url before retrieval.",
            "Preserve agency, appropriation/item/sub-item, period, budget/outturn and preliminary/final status exactly as published.",
            "Do not interpret appropriation outturn as the agency's total accrual-based cost.",
            "For agency_directory, preserve the directory population definition; it is not identical to SCB's agency register.",
        ],
    }
