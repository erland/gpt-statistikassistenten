import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def _schema():
    return json.loads((ROOT / "schemas/source-query-plan-v2.schema.json").read_text(encoding="utf-8"))


def _validate(plan):
    errors = sorted(Draft202012Validator(_schema()).iter_errors(plan), key=lambda e: list(e.path))
    assert not errors, "\n".join(error.message for error in errors)


def test_direct_plan_is_valid():
    _validate({
        "question": "Hur många invånare hade Sundsvalls kommun 2025?",
        "status": "ready",
        "planning_mode": "direct",
        "information_needs": [{
            "id": "population",
            "measure": "folkmängd",
            "concept": "befolkning",
            "population": "folkbokförda invånare",
            "geography": "Sundsvalls kommun",
            "period": "2025",
            "frequency": "annual",
            "breakdowns": [],
            "comparison_mode": "single_value",
            "derived": False,
        }],
        "source_roles": [{
            "need_id": "population",
            "source_id": "scb",
            "role": "primary",
            "tier": "A",
            "integration_status": "integrated",
            "reason": "SCB är primär källa för kommunal befolkningsstatistik.",
            "limitations": [],
        }],
        "combination": {
            "required": False,
            "join_dimensions": [],
            "transformations": [],
            "risks": [],
        },
        "decision": {
            "confidence": "high",
            "review_reasons": [],
            "clarifications": [],
        },
    })


def test_review_plan_requires_prompt():
    plan = {
        "question": "Jämför budgetutfall och antal anställda per myndighet 2025.",
        "status": "needs_user_review",
        "planning_mode": "review_before_execution",
        "information_needs": [{
            "id": "budget",
            "measure": "budgetutfall",
            "concept": "statliga anslag",
            "population": "statliga myndigheter",
            "geography": "Sverige",
            "period": "2025",
            "frequency": "annual",
            "breakdowns": ["myndighet"],
            "comparison_mode": "cross_section",
            "derived": False,
        }],
        "source_roles": [{
            "need_id": "budget",
            "source_id": "statskontoret",
            "role": "primary",
            "tier": "A",
            "integration_status": "integrated",
            "reason": "Statskontoret publicerar budgetutfall.",
            "limitations": ["Anslagsutfall är inte total periodiserad kostnad."],
        }],
        "combination": {
            "required": True,
            "join_dimensions": ["myndighet", "år"],
            "transformations": [],
            "risks": ["Populationer måste verifieras."],
        },
        "decision": {
            "confidence": "medium",
            "review_reasons": ["Join krävs."],
            "clarifications": [],
        },
    }
    errors = list(Draft202012Validator(_schema()).iter_errors(plan))
    assert any(error.validator == "required" and "user_review_prompt" in error.message for error in errors)


def test_external_fallback_can_be_modelled():
    _validate({
        "question": "Hur många laddbara personbilar finns registrerade per kommun?",
        "status": "needs_user_review",
        "planning_mode": "review_before_execution",
        "information_needs": [{
            "id": "cars",
            "measure": "antal registrerade laddbara personbilar",
            "concept": "fordonsbestånd",
            "population": "registrerade personbilar",
            "geography": "svensk kommun",
            "period": "senaste tillgängliga",
            "frequency": "annual",
            "breakdowns": ["kommun", "drivmedelstyp"],
            "comparison_mode": "cross_section",
            "derived": False,
        }],
        "source_roles": [{
            "need_id": "cars",
            "source_id": "external-official-source",
            "role": "primary",
            "tier": "B",
            "integration_status": "external",
            "reason": "Ingen integrerad källa täcker måttet.",
            "limitations": ["Källa och metadata måste verifieras."],
        }],
        "combination": {
            "required": False,
            "join_dimensions": [],
            "transformations": [],
            "risks": ["Definitionen av laddbar bil måste verifieras."],
        },
        "external_fallback": {
            "required": True,
            "reason": "Tier-A saknar det exakta måttet.",
            "search_target": "Officiell svensk fordonsstatistik med kommun och drivmedelstyp.",
            "disclosure_required": True,
        },
        "decision": {
            "confidence": "medium",
            "review_reasons": ["Extern officiell källa krävs."],
            "clarifications": [],
        },
        "user_review_prompt": "Jag föreslår en verifierad officiell extern källa. Vill du att jag går vidare?",
    })


def test_derived_measure_requires_formula_and_dependencies():
    plan = {
        "question": "Brott per 100 000 invånare",
        "status": "ready",
        "planning_mode": "direct",
        "information_needs": [{
            "id": "rate",
            "measure": "brott per 100 000 invånare",
            "concept": "brottsfrekvens",
            "population": "invånare",
            "geography": "Sverige",
            "period": "2025",
            "frequency": "annual",
            "breakdowns": [],
            "comparison_mode": "single_value",
            "derived": True,
        }],
        "source_roles": [{
            "need_id": "rate",
            "source_id": "bra",
            "role": "primary",
            "tier": "A",
            "integration_status": "integrated",
            "reason": "Brå levererar brottsmåttet.",
            "limitations": [],
        }],
        "combination": {
            "required": True,
            "join_dimensions": ["år", "geografi"],
            "transformations": ["per 100 000"],
            "risks": [],
        },
        "decision": {
            "confidence": "high",
            "review_reasons": [],
            "clarifications": [],
        },
    }
    errors = list(Draft202012Validator(_schema()).iter_errors(plan))
    messages = " ".join(error.message for error in errors)
    assert "formula" in messages
    assert "depends_on" in messages
