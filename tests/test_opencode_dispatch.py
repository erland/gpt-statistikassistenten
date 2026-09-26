import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DISPATCH=ROOT/'scripts'/'opencode_dispatch.py'

def run(module, function, payload):
    p=subprocess.run([sys.executable,str(DISPATCH),'--module',module,'--function',function,'--payload',json.dumps(payload)],capture_output=True,text=True,check=True)
    try: return json.loads(p.stdout)
    except json.JSONDecodeError: return p.stdout.strip()

def test_source_planner_dispatch():
    out=run('source_planner','plan_sources',{'question':'Anmälda brott per 100 000 invånare i Sundsvall'})
    assert out['status']=='ready'
    assert out['sources']==['bra','scb']

def test_scb_search_url_dispatch():
    out=run('scb_adapter','search_url',{'query':'befolkning','lang':'sv','page_size':5})
    assert '/tables?' in out and 'query=befolkning' in out

def test_disallowed_function_fails():
    p=subprocess.run([sys.executable,str(DISPATCH),'--module','source_planner','--function','__dict__','--payload','{}'],capture_output=True,text=True)
    assert p.returncode != 0
