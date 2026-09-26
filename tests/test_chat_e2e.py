import json
from pathlib import Path

from scripts.source_planner import plan_sources
from scripts.calculation_engine import per_capita
from scripts.presentation_export import from_statistical_result, from_calculation_result, to_markdown, to_csv
from scripts.quality_gate import run_quality_gate

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / 'examples' / name).read_text(encoding='utf-8'))


def test_chat_e2e_scb_population():
    plan = plan_sources('Hur många invånare har Sundsvalls kommun?')
    assert plan['status'] == 'ready'
    assert plan['sources'] == ['scb']
    result = load('normalized-scb.json')
    presentation = from_statistical_result(result, answer='Sundsvalls kommun har 100 000 invånare i exempelfixturen.')
    gate = run_quality_gate(statistical_results=[result], presentation=presentation)
    assert gate['result'] == 'passed'
    md = to_markdown(presentation)
    csv = to_csv(presentation)
    assert 'SCB' in md and '100000' in csv


def test_chat_e2e_trade_routes_to_comext():
    plan = plan_sources('Hur har Sveriges export av varor till USA utvecklats?')
    assert plan['status'] == 'ready'
    assert 'comext' in plan['sources']
    assert 'eurostat' not in plan['sources']


def test_chat_e2e_bra_per_capita_with_scb_denominator():
    plan = plan_sources('Hur många anmälda brott per 100 000 invånare hade Sundsvall 2025?')
    assert plan['status'] == 'ready'
    assert plan['sources'] == ['bra', 'scb']
    bra = load('normalized-bra.json')
    scb = load('normalized-scb.json')
    calc = per_capita(bra, 'reported_offences', scb, 'population', scale=100000)
    assert calc['observations'][0]['value'] == 100.0
    sources = [
        {'organization':'Brå','dataset':'Anmälda brott','period':'2025','geography':'Sundsvall','measure':'Anmälda brott'},
        {'organization':'SCB','dataset':'Befolkning efter region och år','period':'2025','geography':'Sundsvall','measure':'Folkmängd'},
    ]
    presentation = from_calculation_result(calc, 'Anmälda brott per 100 000 invånare', 'Exempelfixturen ger 100 per 100 000 invånare.', sources)
    gate = run_quality_gate(statistical_results=[bra, scb], calculations=[calc], presentation=presentation)
    assert gate['result'] == 'passed'
    assert presentation['rows'][0]['origin'] == 'calculated'
