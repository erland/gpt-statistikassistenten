#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import yaml

REQUIRED_STATES = [
    "idea_analysis",
    "architecture",
    "planning",
    "implementation",
    "validation",
    "packaging",
    "release",
    "maintenance",
    "blocked",
    "paused",
]

REQUIRED_CORE = [
    "read_project_contract",
    "read_project_status",
    "select_one_state_or_bounded_goal",
    "load_only_relevant_policy",
    "execute_change",
    "validate_deterministically",
    "correct_before_completion_on_failure",
    "update_structured_status_after_pass",
    "rebuild_project_zip_when_required",
    "recommend_next_step_from_actual_state",
]

RUNTIME_BUILD_FLAGS = {
    "chat_zip": "build_chat_zip",
    "custom_gpt": "build_custom_gpt_zip",
    "claude": "build_claude_zip",
    "opencode": "build_opencode_zip",
    "plugin": "build_plugin_zip",
}

EXPECTED_TRANSITIONS = {
    "idea_analysis": {"architecture"},
    "architecture": {"planning"},
    "planning": {"implementation"},
    "implementation": {"validation"},
    "validation": {"implementation", "packaging"},
    "packaging": {"release"},
    "release": {"maintenance"},
    "maintenance": {"implementation", "validation"},
}


def fail(message: str) -> None:
    raise ValueError(message)


def validate(project_root: Path) -> None:
    config_path = project_root / "gpt-project.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    workflow = config.get("workflow") or {}
    if workflow.get("mode") != "explicit_state_machine":
        fail("MODEL-ROBUSTNESS-001: workflow.mode must be explicit_state_machine")

    policy = workflow.get("policy")
    if not policy or not (project_root / policy).is_file():
        fail("MODEL-ROBUSTNESS-002: workflow policy is missing or does not exist")

    states = workflow.get("states") or {}
    missing_states = [state for state in REQUIRED_STATES if state not in states]
    if missing_states:
        fail("MODEL-ROBUSTNESS-003: missing workflow states: " + ", ".join(missing_states))

    for state, expected in EXPECTED_TRANSITIONS.items():
        actual = set((states.get(state) or {}).get("next") or [])
        if actual != expected:
            fail(
                f"MODEL-ROBUSTNESS-004: {state}.next must be "
                f"{sorted(expected)}, got {sorted(actual)}"
            )

    core = workflow.get("operational_core") or []
    missing_core = [item for item in REQUIRED_CORE if item not in core]
    if missing_core:
        fail("MODEL-ROBUSTNESS-005: operational core is incomplete: " + ", ".join(missing_core))

    robustness = config.get("model_robustness") or {}
    if robustness.get("separate_model_instructions") is not False:
        fail("MODEL-ROBUSTNESS-006: separate_model_instructions must remain false")
    if robustness.get("prefer_deterministic_validation") is not True:
        fail("MODEL-ROBUSTNESS-007: deterministic validation must be preferred")
    if robustness.get("max_core_policy_hops") != 1:
        fail("MODEL-ROBUSTNESS-008: max_core_policy_hops must be 1")

    runtimes = config.get("runtime") or {}
    build = config.get("build") or {}
    for runtime_name, build_flag in RUNTIME_BUILD_FLAGS.items():
        runtime = runtimes.get(runtime_name) or {}
        if runtime.get("enabled") is True and build.get(build_flag) is not True:
            fail(
                f"MODEL-ROBUSTNESS-009: enabled runtime {runtime_name} "
                f"requires build.{build_flag}=true"
            )

    scenario_dir = project_root / "evals" / "model-compatibility"
    scenarios = sorted(scenario_dir.glob("*.yaml")) if scenario_dir.is_dir() else []
    if len(scenarios) < 4:
        fail("MODEL-ROBUSTNESS-010: at least four model-compatibility scenarios are required")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    try:
        validate(Path(args.project_root).resolve())
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("Model robustness contract OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
