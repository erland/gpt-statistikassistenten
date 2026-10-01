from scripts.quality_gate import validate_statistical_result


def result_with_external_assurance():
    return {
        "dataset": {"title": "Test", "publisher": "Extern myndighet", "subject": "test"},
        "dimensions": [{"id": "time", "kind": "time", "label": "År", "values": [{"key": "2025", "label": "2025"}]}],
        "measures": [{"id": "value", "label": "Värde", "statistic_type": "count", "unit": "antal"}],
        "observations": [{"dimensions": {"time": "2025"}, "measure": "value", "value": 1, "status": "observed"}],
        "provenance": {
            "source": {
                "organization": "Extern myndighet",
                "dataset_title": "Testdataset",
                "url": "https://example.se/data",
                "quality_assurance": {
                    "source_tier": "B",
                    "integration_status": "external",
                    "registry_quality_assured": False,
                    "verified_for_this_answer": True,
                    "disclosure": "Extern källa, verifierad för detta svar men inte permanent kvalitetssäkrad."
                }
            },
            "retrieval": {
                "retrieved_at": "2026-10-01T12:00:00+02:00",
                "access_method": "file",
                "metadata_verified": True
            },
            "transformations": [{"operation": "none"}]
        }
    }


def test_verified_external_source_passes_assurance_checks():
    issues = validate_statistical_result(result_with_external_assurance())
    codes = {issue["code"] for issue in issues}
    assert "external_source_disclosure_missing" not in codes
    assert "external_source_not_verified" not in codes


def test_external_source_without_disclosure_is_blocked():
    result = result_with_external_assurance()
    result["provenance"]["source"]["quality_assurance"]["disclosure"] = ""
    issues = validate_statistical_result(result)
    assert any(issue["code"] == "external_source_disclosure_missing" for issue in issues)


def test_external_source_cannot_claim_registry_quality_assured():
    result = result_with_external_assurance()
    result["provenance"]["source"]["quality_assurance"]["registry_quality_assured"] = True
    issues = validate_statistical_result(result)
    assert any(issue["code"] == "external_source_registry_status_invalid" for issue in issues)
