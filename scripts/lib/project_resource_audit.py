"""Fail fast on declared but absent GPT project validation resources.

An explicit path in the project profile is an obligation, not proof of testing.
This check applies to all runtime distribution builds (Chat and Plugin alike).
"""
from __future__ import annotations
from pathlib import Path, PurePosixPath

# Deliberately scoped to authoritative verification/model declarations, not
# optional runtime-provided capabilities or free-form descriptive strings.
DECLARED_PATHS = (
    ("testing", "manifest"),
    ("testing", "manifest_schema"),
    ("testing", "model"),
    ("linting", "script"),
    ("linting", "model"),
    ("model_robustness", "model_compatibility", "documentation"),
)


def validate_project_resources(root: Path, cfg: dict) -> list[str]:
    missing: list[str] = []
    for keys in DECLARED_PATHS:
        value = cfg
        for key in keys:
            value = value.get(key) if isinstance(value, dict) else None
        if not isinstance(value, str) or not value.strip():
            continue
        rel = PurePosixPath(value)
        if rel.is_absolute() or ".." in rel.parts or "\\" in value:
            missing.append(f"{'.'.join(keys)}: unsafe path {value}")
        elif not (root / value).is_file():
            missing.append(f"{'.'.join(keys)}: missing declared file {value}")
    return missing
