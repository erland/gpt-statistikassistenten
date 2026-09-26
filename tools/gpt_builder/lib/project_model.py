from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def load_project_config(root: Path) -> dict[str, Any]:
    return load_yaml(root / "gpt-project.yaml")


def load_project_status(root: Path) -> dict[str, Any]:
    return load_yaml(root / "project-status.yaml")


def select_reference_profile(features: dict[str, Any]) -> str:
    """Return the canonical reference profile for a feature set."""
    if (
        features.get("research_heavy")
        or features.get("evidence_required")
        or features.get("multi_stage_workflow")
    ):
        return "workflow_research_heavy"

    if (
        features.get("project_zip_manipulation")
        or features.get("scripts_required")
        or features.get("rich_structured_runtime")
    ):
        return "zip_first_advanced"

    if (
        features.get("structured_knowledge")
        or features.get("repeatable_outputs")
        or features.get("moderate_workflow")
    ):
        return "standard"

    return "simple"


def get_registered_next_step(status: dict[str, Any]) -> dict[str, Any] | None:
    value = status.get("next_step")
    return value if isinstance(value, dict) and value else None


def get_blockers(status: dict[str, Any]) -> list[Any]:
    return list(status.get("blocking_issues") or status.get("blockers") or [])


CAPABILITY_LEVELS = {"required", "recommended", "optional", "not_required", "to_be_recommended"}

LEGACY_CAPABILITY_MAP = {
    "web": "web",
    "data_analysis": "code_execution",
    "image_generation": "image_generation",
    "structured_knowledge": "structured_data",
}


def _legacy_level(value: Any) -> str:
    if isinstance(value, str):
        aliases = {
            "likely_required": "recommended",
            "not_recommended": "not_required",
        }
        return aliases.get(value, value if value in CAPABILITY_LEVELS else "to_be_recommended")
    if isinstance(value, dict):
        return _legacy_level(value.get("state", value.get("level")))
    return "to_be_recommended"


def normalize_capability_contract(cfg: dict[str, Any]) -> dict[str, Any]:
    """Return the platform-neutral capability contract.

    Current projects use capabilities.requirements. Legacy projects using
    web/data_analysis/file_handling/etc. are mapped without mutating source data.
    """
    caps = cfg.get("capabilities") or {}
    requirements = caps.get("requirements")
    if isinstance(requirements, dict):
        return {
            "contract_version": caps.get("contract_version", 1),
            "recommendation_mode": caps.get("recommendation_mode", "inferred_from_use_case"),
            "ask_user_only_when_business_choice_is_ambiguous": caps.get(
                "ask_user_only_when_business_choice_is_ambiguous", True
            ),
            "requirements": requirements,
        }

    normalized: dict[str, Any] = {}
    for legacy, canonical in LEGACY_CAPABILITY_MAP.items():
        if legacy in caps:
            normalized[canonical] = {"level": _legacy_level(caps[legacy])}

    file_handling = caps.get("file_handling")
    if file_handling is not None:
        level = _legacy_level(file_handling)
        normalized["filesystem"] = {"read": level, "write": level}

    return {
        "contract_version": 1,
        "recommendation_mode": caps.get("recommendation_mode", "inferred_from_use_case"),
        "ask_user_only_when_business_choice_is_ambiguous": caps.get(
            "ask_user_only_when_business_choice_is_ambiguous", True
        ),
        "requirements": normalized,
    }


def capability_level(contract: dict[str, Any], capability: str, default: str = "optional") -> str:
    value = (contract.get("requirements") or {}).get(capability)
    if isinstance(value, dict):
        return str(value.get("level", default))
    return default


LEGACY_ARTIFACT_MAP = {
    "project_zip": "project_package",
    "chat_zip": "runtime_package",
    "custom_gpt_zip": "runtime_package",
    "claude_zip": "runtime_package",
    "opencode_zip": "runtime_package",
    "plugin_zip": "runtime_package",
    "validation_report": "validation_report",
    "parity_report": "parity_report",
    "checksums": "checksums",
}


def normalize_artifact_contract(cfg: dict[str, Any]) -> dict[str, Any]:
    """Return the platform-neutral artifact/output contract.

    New projects use artifacts.outputs. Legacy projects with project_zip/chat_zip/
    custom_gpt_zip style entries are mapped without mutating source data.
    """
    artifacts = cfg.get("artifacts") or {}
    outputs = artifacts.get("outputs")
    if isinstance(outputs, dict):
        return {
            "contract_version": artifacts.get("contract_version", 1),
            "outputs": outputs,
            "legacy_mapping": artifacts.get("legacy_mapping", {}),
        }

    normalized: dict[str, Any] = {}
    for legacy_id, value in artifacts.items():
        canonical_id = LEGACY_ARTIFACT_MAP.get(legacy_id)
        if not canonical_id or canonical_id in normalized:
            continue
        value = value if isinstance(value, dict) else {}
        requirement = "required"
        condition = None
        if value.get("required_when_enabled") or value.get("required_when_multiple_runtimes"):
            requirement = "conditional"
            condition = "runtime_condition"
        elif value.get("required") is False:
            requirement = "optional"
        normalized[canonical_id] = {
            "kind": "distribution" if canonical_id == "runtime_package" else (
                "package" if canonical_id == "project_package" else (
                    "report" if canonical_id.endswith("_report") else "metadata"
                )
            ),
            "format": "zip" if canonical_id in {"runtime_package", "project_package"} else (
                "sha256" if canonical_id == "checksums" else "structured"
            ),
            "requirement": requirement,
            "persistence": "persistent",
            "multiplicity": "many" if canonical_id == "runtime_package" else "one",
        }
        if condition:
            normalized[canonical_id]["condition"] = condition

    return {
        "contract_version": 1,
        "outputs": normalized,
        "legacy_mapping": dict(LEGACY_ARTIFACT_MAP),
    }


def artifact_contract_id_for_delivery_type(cfg: dict[str, Any], delivery_type: str) -> str | None:
    contract = normalize_artifact_contract(cfg)
    mapping = contract.get("legacy_mapping") or LEGACY_ARTIFACT_MAP
    return mapping.get(delivery_type)


def normalize_workspace_state_contract(cfg: dict[str, Any]) -> dict[str, Any]:
    """Return a platform-neutral workspace/state contract.

    New projects use workspace_state directly. Legacy projects are inferred
    conservatively from resume/workflow settings without mutating source data.
    """
    current = cfg.get("workspace_state")
    if isinstance(current, dict):
        return current

    resume = cfg.get("resume") or {}
    workflow = cfg.get("workflow") or {}
    supported = bool(resume.get("supported"))
    independent_of_chat = resume.get("requires_previous_chat_history") is False

    uses_project_package = bool(
        workflow.get("resume_from_project_zip")
        or workflow.get("resume_from_project_package")
        or workflow.get("create_project_zip_on_first_execution_step")
        or workflow.get("create_project_package_on_first_execution_step")
    )

    workspace_required = supported or uses_project_package
    state_required = supported and independent_of_chat

    result: dict[str, Any] = {
        "contract_version": 1,
        "workspace": {
            "requirement": "required" if workspace_required else "optional",
            "persistence": "required" if supported else "preferred",
            "portable": True,
            "separate_from_assistant": True,
        },
        "state": {
            "requirement": "required" if state_required else "optional",
            "persistence": "required" if state_required else "preferred",
            "authority": "workspace_file" if state_required else "conversation",
            "conversation_fallback": not state_required,
        },
        "runtime_preferences": {
            "chat": "conversation_or_file",
            "agent": "workspace_file" if workspace_required else "runtime_managed",
        },
    }

    if uses_project_package:
        result["workspace"]["artifact"] = "project_package"

    if state_required:
        result["state"]["format"] = "yaml"
        result["state"]["path"] = "project-status.yaml"

    return result


def normalize_tool_contract(cfg: dict[str, Any]) -> dict[str, Any]:
    """Return a platform-neutral tool contract.

    Explicit tool declarations are authoritative. Legacy projects are handled
    conservatively: scripts are not promoted to runtime tools merely because
    they exist in a scripts directory.
    """
    current = cfg.get("tools")
    if isinstance(current, dict):
        return current

    legacy = cfg.get("tooling")
    if isinstance(legacy, dict) and isinstance(legacy.get("tools"), list):
        return {
            "contract_version": 1,
            "tools": legacy.get("tools", []),
        }

    return {
        "contract_version": 1,
        "tools": [],
    }


def normalize_runtime_parity_report(report: dict[str, Any]) -> dict[str, Any]:
    """Normalize legacy two-runtime parity reports to the generic v2 model."""
    if report.get("schema_version") == 2 and isinstance(report.get("runtimes"), dict):
        return report

    capabilities = report.get("capabilities")
    if not isinstance(capabilities, list):
        return report

    summary = report.get("summary") or {}
    runtimes: dict[str, Any] = {}
    for runtime_id in ("chat_zip", "custom_gpt"):
        runtimes[runtime_id] = {
            "level": summary.get("level", "moderate"),
            "release_recommendation": summary.get("release_recommendation", "publish_with_warning"),
        }
        if isinstance(summary.get("weighted_score"), (int, float)):
            runtimes[runtime_id]["weighted_score"] = summary["weighted_score"]

    requirements = []
    for item in capabilities:
        states = {}
        for runtime_id in ("chat_zip", "custom_gpt"):
            if runtime_id in item:
                states[runtime_id] = {
                    "state": item.get(runtime_id, "not_applicable"),
                }
                if item.get("reason"):
                    states[runtime_id]["reason"] = item["reason"]
        requirements.append({
            "category": "capability",
            "id": item.get("id", "unknown"),
            "title": item.get("title", item.get("id", "unknown")),
            "criticality": item.get("criticality", "important"),
            "runtime_states": states,
        })

    return {
        "schema_version": 2,
        "reference": {"type": "canonical_contract"},
        "runtimes": runtimes,
        "requirements": requirements,
    }


def runtime_ids_from_parity(report: dict[str, Any]) -> list[str]:
    normalized = normalize_runtime_parity_report(report)
    return sorted((normalized.get("runtimes") or {}).keys())


def validate_runtime_parity_report(report: dict[str, Any]) -> list[str]:
    """Return semantic errors not expressible conveniently in JSON Schema."""
    normalized = normalize_runtime_parity_report(report)
    runtimes = set((normalized.get("runtimes") or {}).keys())
    errors: list[str] = []

    if not runtimes:
        errors.append("Runtime parity report has no runtimes.")
        return errors

    for requirement in normalized.get("requirements") or []:
        req_id = str(requirement.get("id", "unknown"))
        states = set((requirement.get("runtime_states") or {}).keys())
        missing = runtimes - states
        unknown = states - runtimes
        if missing:
            errors.append(
                f"Requirement {req_id} is missing runtime states for: {', '.join(sorted(missing))}"
            )
        if unknown:
            errors.append(
                f"Requirement {req_id} references unknown runtimes: {', '.join(sorted(unknown))}"
            )

    return errors
