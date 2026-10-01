#!/usr/bin/env python3
"""Conservative planner for Tullverket seizure statistics.

Tullverket exposes an interactive public statistics page with CSV export but
does not document a stable general-purpose API contract. The adapter therefore
plans verified use of the official page/export instead of inventing an
endpoint.
"""
from __future__ import annotations

BASE_URL = "https://www.tullverket.se/sv/omoss/beslagsstatistik.4.226de36015804b8cf353949.html"
VALID_PERIOD_PREFIX = "20"

class TullverketAdapterError(ValueError):
    pass

def statistics_url() -> str:
    return BASE_URL

def seizure_plan(*, periods: list[str] | None = None, commodity_type: str | None = None,
                 commodity: str | None = None, county: str | None = None,
                 place: str | None = None) -> dict:
    periods = periods or []
    if commodity_type is not None and (not isinstance(commodity_type, str) or not commodity_type.strip()):
        raise TullverketAdapterError("commodity_type must be a non-empty string when provided")
    for period in periods:
        if not isinstance(period, str) or len(period) != 7 or period[4:6] != "-H" or period[-1] not in {"1", "2"} or not period.startswith(VALID_PERIOD_PREFIX):
            raise TullverketAdapterError("periods must use YYYY-H1 or YYYY-H2")
    return {
        "url": BASE_URL,
        "method": "official-page-csv-export",
        "filters": {
            "periods": periods,
            "commodity_type": commodity_type,
            "commodity": commodity,
            "county": county,
            "place": place,
        },
        "instructions": [
            "Verify available filter values and the page's last-updated date before extraction.",
            "Use Tullverket's 'Exportera allt till CSV' or 'Exportera vald filtrering till CSV'.",
            "Preserve quantity unit per row; kilograms, litres and pieces must not be summed as one measure.",
            "Treat seizures as enforcement observations, not a direct measure of consumption, prevalence, availability or market size.",
        ],
    }
