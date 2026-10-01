#!/usr/bin/env python3
"""Safe CLI bridge for Statistikassistenten's OpenCode wrappers.

Accepts only allow-listed module/function pairs and JSON payloads. Domain logic
remains in the canonical adapter/calculation/presentation modules.
"""
from __future__ import annotations
import argparse, importlib, inspect, json, sys
from pathlib import Path

ALLOW = {
  'source_planner': {'plan_sources'},
  'scb_adapter': {'search_url','metadata_url','validate_selection','estimate_cells','post_request_plan'},
  'eurostat_adapter': {'dataflow_catalog_url','structure_url','validate_filters','data_request_plan'},
  'comext_adapter': {'dataflow_catalog_url','structure_url','validate_role_map','trade_request_plan'},
  'bra_adapter': {'available_products','discovery_plan','product_discovery_plan','validate_product_snapshot','validate_metadata_snapshot','product_selection_plan','reported_crimes_plan'},
  'kolada_adapter': {'docs_url','kpi_metadata_url','municipality_metadata_url','data_url','validate_kpi_metadata'},
  'socialstyrelsen_adapter': {'subjects_url','dimension_url','result_url'},
  'folkhalsodata_adapter': {'root_url','node_url','query_plan'},
  'arbetsformedlingen_adapter': {'search_url','normalize_summary'},
  'riksbank_adapter': {'series_catalog_url','groups_url','latest_url','observations_url'},
  'energimyndigheten_adapter': {'root_url','node_url','query_plan'},
  'forsakringskassan_adapter': {'meta_url','validate_distribution_url'},
  'jordbruksverket_adapter': {'root_url','node_url','query_plan'},
  'skolverket_adapter': {'planned_educations_docs_url','request_plan'},
  'smhi_adapter': {'parameter_url','station_url','data_url'},
  'worldbank_adapter': {'indicators_url','indicator_metadata_url','data_url'},
  'oecd_adapter': {'dataflow_url','data_url'},
  'who_adapter': {'hub_url','indicators_url','validate_official_url'},
  'bis_adapter': {'structure_url','data_url'},
  'ecb_adapter': {'dataflow_url','data_url'},
  'euda_adapter': {'wastewater_metadata_url','wastewater_source_url','validate_official_data_url','wastewater_plan'},
  'tullverket_adapter': {'statistics_url','seizure_plan'},
  'statskontoret_adapter': {'available_products','discovery_url','validate_distribution_url','data_plan'},
  'svk_adapter': {'consumption_types_url','production_types_url','network_areas_url','statistics_url','query_plan'},
  'calculation_engine': {'absolute_change','percent_change','index_series','per_capita','share'},
  'presentation_export': {'from_statistical_result','from_calculation_result','to_markdown','to_csv'},
  'quality_gate': {'validate_statistical_result','validate_calculation_result','validate_presentation','run_quality_gate'},
}

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--module', required=True, choices=sorted(ALLOW))
    ap.add_argument('--function', required=True)
    ap.add_argument('--payload', default='{}')
    ns=ap.parse_args()
    if ns.function not in ALLOW[ns.module]:
        raise SystemExit('Function is not allowed for this OpenCode tool')
    payload=json.loads(ns.payload)
    if not isinstance(payload, dict):
        raise SystemExit('payload must be a JSON object')
    here=Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    mod=importlib.import_module(ns.module)
    fn=getattr(mod, ns.function)
    sig=inspect.signature(fn)
    try:
        bound=sig.bind(**payload)
    except TypeError as e:
        raise SystemExit(str(e))
    result=fn(*bound.args, **bound.kwargs)
    if isinstance(result, str):
        print(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
