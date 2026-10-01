from scripts.source_planner_v2 import SourcePlannerV2Error, finalize_plan, registry_summary, source_capability


def base_need(need_id="population", measure="folkmängd"):
    return {
        "id": need_id,
        "measure": measure,
        "concept": measure,
        "population": "relevant population",
        "geography": "Sverige",
        "period": "2025",
        "frequency": "annual",
        "breakdowns": [],
        "comparison_mode": "single_value",
        "derived": False,
    }


def base_plan():
    return {
        "question": "Hur många invånare hade Sverige 2025?",
        "status": "ready",
        "planning_mode": "direct",
        "information_needs": [base_need()],
        "source_roles": [{
            "need_id": "population",
            "source_id": "scb",
            "role": "primary",
            "tier": "A",
            "integration_status": "integrated",
            "reason": "SCB är primär källa.",
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
    }


def test_registry_summary_exposes_all_integrated_sources():
    summary = registry_summary()
    assert "scb" in summary["sources"]
    assert "euda" in summary["sources"]
    assert "integrated_scope" in summary["sources"]["scb"]


def test_source_capability_returns_full_registry_entry():
    scb = source_capability("scb")
    assert scb["tier"] == "A"
    assert "catalog_scope" in scb
    assert "integrated_scope" in scb


def test_simple_integrated_high_confidence_plan_runs_direct():
    result = finalize_plan(base_plan())
    assert result["status"] == "ready"
    assert result["planning_mode"] == "direct"
    assert "user_review_prompt" not in result


def test_method_risk_forces_user_review():
    plan = base_plan()
    plan["combination"] = {
        "required": True,
        "join_dimensions": ["myndighet", "år"],
        "transformations": [],
        "risks": ["Populationerna kan skilja mellan källorna."],
    }
    result = finalize_plan(plan)
    assert result["status"] == "needs_user_review"
    assert result["planning_mode"] == "review_before_execution"
    assert "user_review_prompt" in result


def test_safe_multi_source_combination_can_stay_direct():
    plan = base_plan()
    plan["question"] = "Anmälda brott per 100 000 invånare 2025"
    plan["information_needs"] = [
        base_need("crimes", "anmälda brott"),
        base_need("population", "folkmängd"),
        {
            "id": "rate",
            "measure": "anmälda brott per 100 000 invånare",
            "concept": "brottsfrekvens",
            "population": "invånare",
            "geography": "Sverige",
            "period": "2025",
            "frequency": "annual",
            "breakdowns": [],
            "comparison_mode": "single_value",
            "derived": True,
            "formula": "crimes / population * 100000",
            "depends_on": ["crimes", "population"],
        },
    ]
    plan["source_roles"] = [
        {
            "need_id": "crimes",
            "source_id": "bra",
            "role": "primary",
            "tier": "A",
            "integration_status": "integrated",
            "reason": "Brå är primär källa för anmälda brott.",
            "limitations": [],
        },
        {
            "need_id": "population",
            "source_id": "scb",
            "role": "primary",
            "tier": "A",
            "integration_status": "integrated",
            "reason": "SCB är primär källa för befolkning.",
            "limitations": [],
        },
    ]
    plan["combination"] = {
        "required": True,
        "join_dimensions": ["år", "geografi"],
        "transformations": ["per 100 000"],
        "risks": [],
    }
    result = finalize_plan(plan)
    assert result["status"] == "ready"
    assert result["planning_mode"] == "direct"


def test_catalog_only_source_forces_review():
    plan = base_plan()
    plan["source_roles"][0]["source_id"] = "skolverket"
    plan["source_roles"][0]["integration_status"] = "catalog_only"
    plan["source_roles"][0]["reason"] = "Skolverket har relevant statistik i katalogen."
    result = finalize_plan(plan)
    assert result["status"] == "needs_user_review"
    assert any("saknar fullt integrerad" in reason for reason in result["decision"]["review_reasons"])


def test_external_source_requires_fallback_and_review():
    plan = base_plan()
    plan["source_roles"][0] = {
        "need_id": "population",
        "source_id": "external-official-source",
        "role": "primary",
        "tier": "B",
        "integration_status": "external",
        "reason": "Ingen integrerad källa täcker måttet.",
        "limitations": ["Metadata måste verifieras."],
    }
    try:
        finalize_plan(plan)
        assert False, "expected external fallback error"
    except SourcePlannerV2Error as error:
        assert "external_fallback" in str(error)

    plan["external_fallback"] = {
        "required": True,
        "reason": "Ingen tier-A-källa täcker måttet.",
        "search_target": "Officiell statistik för det efterfrågade måttet.",
        "disclosure_required": True,
    }
    result = finalize_plan(plan)
    assert result["status"] == "needs_user_review"
    assert result["planning_mode"] == "review_before_execution"


def test_medium_confidence_forces_review():
    plan = base_plan()
    plan["decision"]["confidence"] = "medium"
    result = finalize_plan(plan)
    assert result["status"] == "needs_user_review"


def test_clarification_takes_precedence():
    plan = base_plan()
    plan["decision"]["clarifications"] = ["Vilken geografi avser du?"]
    result = finalize_plan(plan)
    assert result["status"] == "needs_clarification"
    assert result["planning_mode"] == "review_before_execution"


def test_unregistered_source_cannot_claim_tier_a():
    plan = base_plan()
    plan["source_roles"][0] = {
        "need_id": "population",
        "source_id": "made-up-source",
        "role": "primary",
        "tier": "A",
        "integration_status": "external",
        "reason": "Test.",
        "limitations": [],
    }
    try:
        finalize_plan(plan)
        assert False, "expected tier validation error"
    except SourcePlannerV2Error as error:
        assert "cannot be tier A" in str(error)
