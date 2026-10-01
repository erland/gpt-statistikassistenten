#!/usr/bin/env python3
"""Planner for Svenska kraftnät Mimer electricity statistics API."""
from __future__ import annotations
from urllib.parse import urlencode

BASE_URL="https://mimer.svk.se/api/MimerAPI"

class SvkAdapterError(ValueError):
    pass

def consumption_types_url() -> str:
    return f"{BASE_URL}/GetProductSortConsumtion"

def production_types_url() -> str:
    return f"{BASE_URL}/GetProductSortProduction"

def network_areas_url() -> str:
    return f"{BASE_URL}/GetNetworkAreas"

def statistics_url(*, period_from:str|None=None, period_to:str|None=None,
                   bidding_area_id:int=0, product_sort_id:str|None=None,
                   network_area_id:str|None=None) -> str:
    if bidding_area_id not in {0,1,2,3,4}:
        raise SvkAdapterError("bidding_area_id must be 0-4")
    params={}
    if period_from: params["periodFrom"]=period_from
    if period_to: params["periodTo"]=period_to
    params["biddingAreaId"]=bidding_area_id
    if product_sort_id: params["productSortId"]=product_sort_id
    if network_area_id: params["networkAreaId"]=network_area_id
    return f"{BASE_URL}/GetProductionConsumtionStatistics?"+urlencode(params)

def query_plan(*, kind:str, period_from:str|None=None, period_to:str|None=None,
               bidding_area_id:int=0, product_sort_id:str|None=None,
               network_area_id:str|None=None) -> dict:
    if kind not in {"consumption","production"}:
        raise SvkAdapterError("kind must be consumption or production")
    return {
        "metadata_url": consumption_types_url() if kind=="consumption" else production_types_url(),
        "data_url": statistics_url(period_from=period_from,period_to=period_to,
                                   bidding_area_id=bidding_area_id,
                                   product_sort_id=product_sort_id,
                                   network_area_id=network_area_id),
        "method":"GET",
        "notes":[
            "Verify productSortId from the corresponding metadata endpoint before data retrieval.",
            "biddingAreaId 0 means Sweden; 1-4 correspond to SE1-SE4.",
            "Preserve Actual and Planned separately when both are returned.",
            "These are physical electricity statistics, not customer prices or Nord Pool spot prices.",
        ],
    }
