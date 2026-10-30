#!/usr/bin/env python3
"""Validate portable skill modules and script execution requirements.

Canonical modules are runtime-neutral. Runtime packaging is a separate, explicit
step; declaring a script does not imply it is executable in the target host.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

RUNTIMES = ("chat_zip", "plugin", "claude", "opencode")
CAPABILITIES = ("filesystem_read", "filesystem_write", "network", "code_execution", "persistent_state")
LEVELS = ("none", "optional", "required")
ENGINE = ("python", "node", "shell")

def inspect(contract: dict, root: Path) -> dict:
    errors = []
    if contract.get("schema_version") != 1:
        errors.append("Invalid schema_version")
    core = contract.get("core")
    if not isinstance(core, str) or not core.strip():
        errors.append("Missing canonical core path")
    elif not _file(root, core):
        errors.append("Canonical core is missing or unsafe")
    modules = contract.get("modules")
    if not isinstance(modules, list) or not modules:
        errors.append("At least one skill module required")
        modules = []
    ids = set()
    for idx, module in enumerate(modules):
        if not isinstance(module, dict):
            errors.append(f"Module {idx}: not an object")
            continue
        ident = module.get("id")
        if not isinstance(ident, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", ident):
            errors.append(f"Module {idx}: invalid id")
        elif ident in ids:
            errors.append(f"Module {idx}: duplicate id")
        ids.add(ident)
        for field in ("skill",):
            if not _file(root, module.get(field)):
                errors.append(f"Module {idx}: missing/unsafe {field}")
        for field in ("references", "assets"):
            paths = module.get(field, [])
            if not isinstance(paths, list) or any(not _file(root, p) for p in paths):
                errors.append(f"Module {idx}: invalid {field}")
        scripts = module.get("scripts", [])
        if not isinstance(scripts, list):
            errors.append(f"Module {idx}: invalid scripts")
            continue
        for j, script in enumerate(scripts):
            if not isinstance(script, dict) or not _file(root, script.get("path")):
                errors.append(f"Module {idx} script {j}: missing/unsafe path")
                continue
            if script.get("engine") not in ENGINE:
                errors.append(f"Module {idx} script {j}: unknown engine")
            reqs = script.get("requirements")
            if not isinstance(reqs, dict) or any(reqs.get(k) not in LEVELS for k in CAPABILITIES):
                errors.append(f"Module {idx} script {j}: incomplete capability requirements")
            if not isinstance(script.get("dependencies"), list) or any(not isinstance(x, str) or not x for x in script["dependencies"]):
                errors.append(f"Module {idx} script {j}: invalid dependencies")
            if script.get("fallback") not in ("block", "manual", "skip_optional"):
                errors.append(f"Module {idx} script {j}: missing fallback")
    fallback = contract.get("fallback")
    if not isinstance(fallback, dict) or any(not isinstance(fallback.get(r), str) or not fallback[r].strip() for r in RUNTIMES):
        errors.append("Explicit fallback required for all four runtimes")
    return {"result": "rejected" if errors else "review_ready", "errors": errors,
            "runtime_execution_verified": False, "release_ready": False}


def _file(root: Path, path: object) -> bool:
    if not isinstance(path, str) or not path.strip():
        return False
    p = Path(path)
    if p.is_absolute() or ".." in p.parts:
        return False
    target = root / p
    return target.is_file() and not target.is_symlink() and target.resolve().is_relative_to(root.resolve())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--project-root", required=True)
    a = parser.parse_args()
    try:
        report = inspect(json.loads(Path(a.contract).read_text(encoding="utf-8")), Path(a.project_root))
    except (ValueError, OSError) as exc:
        print(f"Contract invalid: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
