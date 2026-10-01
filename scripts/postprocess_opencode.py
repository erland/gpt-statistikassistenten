#!/usr/bin/env python3
"""Rewrite generic GPT Byggaren OpenCode wrappers into domain-aware wrappers."""
from __future__ import annotations
import argparse, json, shutil
from pathlib import Path

OPS = {
 'source-planner': ('source_planner',['plan_sources']),
 'adaptive-source-planner': ('adaptive_source_planner',['registry_summary','source_capability','finalize_plan']),
 'external-source-validator': ('external_source_validator',['assessment_requirements','assess_candidate','disclosure_text']),
 'scb-adapter': ('scb_adapter',['search_url','metadata_url','validate_selection','estimate_cells','post_request_plan']),
 'eurostat-adapter': ('eurostat_adapter',['dataflow_catalog_url','structure_url','validate_filters','data_request_plan']),
 'comext-adapter': ('comext_adapter',['dataflow_catalog_url','structure_url','validate_role_map','trade_request_plan']),
 'bra-adapter': ('bra_adapter',['available_products','discovery_plan','product_discovery_plan','validate_product_snapshot','validate_metadata_snapshot','product_selection_plan','reported_crimes_plan']),
 'kolada-adapter': ('kolada_adapter',['docs_url','kpi_metadata_url','municipality_metadata_url','data_url','validate_kpi_metadata']),
 'socialstyrelsen-adapter': ('socialstyrelsen_adapter',['subjects_url','dimension_url','result_url']),
 'folkhalsodata-adapter': ('folkhalsodata_adapter',['root_url','node_url','query_plan']),
 'arbetsformedlingen-adapter': ('arbetsformedlingen_adapter',['search_url','normalize_summary']),
 'riksbank-adapter': ('riksbank_adapter',['series_catalog_url','groups_url','latest_url','observations_url']),
 'energimyndigheten-adapter': ('energimyndigheten_adapter',['root_url','node_url','query_plan']),
 'forsakringskassan-adapter': ('forsakringskassan_adapter',['meta_url','validate_distribution_url']),
 'jordbruksverket-adapter': ('jordbruksverket_adapter',['root_url','node_url','query_plan']),
 'skolverket-adapter': ('skolverket_adapter',['planned_educations_docs_url','request_plan']),
 'smhi-adapter': ('smhi_adapter',['parameter_url','station_url','data_url']),
 'worldbank-adapter': ('worldbank_adapter',['indicators_url','indicator_metadata_url','data_url']),
 'oecd-adapter': ('oecd_adapter',['dataflow_url','data_url']),
 'who-adapter': ('who_adapter',['hub_url','indicators_url','validate_official_url']),
 'bis-adapter': ('bis_adapter',['structure_url','data_url']),
 'ecb-adapter': ('ecb_adapter',['dataflow_url','data_url']),
 'euda-adapter': ('euda_adapter',['wastewater_metadata_url','wastewater_source_url','validate_official_data_url','wastewater_plan']),
 'tullverket-adapter': ('tullverket_adapter',['statistics_url','seizure_plan']),
 'statskontoret-adapter': ('statskontoret_adapter',['available_products','discovery_url','validate_distribution_url','data_plan']),
 'svk-adapter': ('svk_adapter',['consumption_types_url','production_types_url','network_areas_url','statistics_url','query_plan']),
 'calculation-engine': ('calculation_engine',['absolute_change','percent_change','index_series','per_capita','share']),
 'presentation-export': ('presentation_export',['from_statistical_result','from_calculation_result','to_markdown','to_csv']),
 'quality-gate': ('quality_gate',['validate_statistical_result','validate_calculation_result','validate_presentation','run_quality_gate']),
}

def wrapper(tool_id,module,ops):
    tool_name='gpt_'+tool_id.replace('-','_')
    enums=', '.join(json.dumps(x) for x in ops)
    return f'''import {{ tool }} from "@opencode-ai/plugin"\nimport path from "path"\n\nexport default tool({{\n  description: "Statistikassistenten: {tool_id}. Payload är ett JSON-objekt med argument för vald operation.",\n  args: {{\n    operation: tool.schema.enum([{enums}]),\n    payload: tool.schema.string().optional().describe("JSON object with named function arguments")\n  }},\n  async execute(args, context) {{\n    const dispatcher = path.join(context.worktree, ".opencode/runtime-scripts/opencode_dispatch.py")\n    const cmd = ["python3", dispatcher, "--module", "{module}", "--function", args.operation, "--payload", args.payload ?? "{{}}"]\n    const proc = Bun.spawn(cmd, {{ cwd: context.worktree, stdout: "pipe", stderr: "pipe" }})\n    const stdout = await new Response(proc.stdout).text()\n    const stderr = await new Response(proc.stderr).text()\n    const code = await proc.exited\n    if (code !== 0) throw new Error((stderr || stdout || ("Tool failed with exit code " + code)).trim())\n    return (stdout || stderr).trim()\n  }}\n}})\n'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root',default='.')
    ns=ap.parse_args(); root=Path(ns.project_root).resolve(); out=root/'build'/'opencode'
    tools=out/'.opencode'/'tools'; runtime=out/'.opencode'/'runtime-scripts'
    if not tools.exists(): raise SystemExit('OpenCode build missing')
    shutil.copy2(root/'scripts'/'opencode_dispatch.py', runtime/'opencode_dispatch.py')
    for tool_id,(module,ops) in OPS.items():
        (tools/f"gpt_{tool_id.replace('-','_')}.ts").write_text(wrapper(tool_id,module,ops),encoding='utf-8')
    print('OpenCode domain wrappers updated')
if __name__=='__main__': main()
