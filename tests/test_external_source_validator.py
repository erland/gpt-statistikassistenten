import pytest

from scripts.external_source_validator import (
    ExternalSourceError,
    assess_candidate,
    assessment_requirements,
    disclosure_text,
)


def candidate():
    return {
        "source_id": "transportstyrelsen-example",
        "organization": "Exempelmyndigheten",
        "dataset_title": "Fordonsstatistik",
        "dataset_url": "https://example.se/data",
        "source_kind": "official_primary",
        "source_tier": "B",
        "official_status": "official_open_data",
        "access_method": "file",
        "need_id": "cars",
        "machine_readable": True,
        "publisher_is_producer": True,
        "metadata_checks": {
            "definition": True,
            "population": True,
            "geography": True,
            "period": True,
            "unit": True,
            "status_or_revision": True,
            "license_or_terms": True,
        },
        "limitations": [],
        "evidence_urls": ["https://example.se/metadata"],
    }


def test_official_tier_b_is_usable_with_disclosure():
    result = assess_candidate(candidate())
    assert result["assessment"]["result"] == "usable_with_disclosure"
    assert result["assessment"]["official_source"] is True
    assert result["assessment"]["requires_disclosure"] is True
    assert "inte permanent kvalitetssäkrad" in disclosure_text(result)


def test_missing_metadata_blocks_candidate():
    c = candidate()
    c["metadata_checks"]["unit"] = False
    result = assess_candidate(c)
    assert result["assessment"]["result"] == "blocked"
    assert any("unit" in issue for issue in result["assessment"]["issues"])


def test_non_official_cannot_claim_tier_b():
    c = candidate()
    c["source_kind"] = "research"
    c["official_status"] = "research_data"
    result = assess_candidate(c)
    assert result["assessment"]["result"] == "blocked"


def test_official_source_should_not_be_tier_c():
    c = candidate()
    c["source_tier"] = "C"
    result = assess_candidate(c)
    assert result["assessment"]["result"] == "blocked"


def test_research_tier_c_can_be_used_when_fully_verified():
    c = candidate()
    c["source_kind"] = "research"
    c["source_tier"] = "C"
    c["official_status"] = "research_data"
    result = assess_candidate(c)
    assert result["assessment"]["result"] == "usable_with_disclosure"


def test_tier_d_is_blocked():
    c = candidate()
    c["source_tier"] = "D"
    result = assess_candidate(c)
    assert result["assessment"]["result"] == "blocked"


def test_https_is_required():
    c = candidate()
    c["dataset_url"] = "http://example.se/data"
    with pytest.raises(ExternalSourceError):
        assess_candidate(c)


def test_requirements_expose_search_order():
    req = assessment_requirements()
    assert req["search_order"][0] == "official_primary_source_or_official_open_data"
    assert "D" in req["never_use_as_result_source"]
