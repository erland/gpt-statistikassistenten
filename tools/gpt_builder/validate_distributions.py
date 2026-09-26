#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

try:
    import yaml
except Exception as exc:
    raise SystemExit("PyYAML is required") from exc


FORBIDDEN_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "research",
    "evals",
    "tests",
}


def load_cfg(root: Path) -> dict:
    return yaml.safe_load((root / "gpt-project.yaml").read_text(encoding="utf-8"))


def validate_custom(root: Path, cfg: dict) -> list[str]:
    errors = []
    build = root / "build" / "custom-gpt"
    if not build.exists():
        return ["Custom GPT build directory missing"]

    instr = build / "builder" / "instructions.md"
    if not instr.exists():
        errors.append("Missing builder/instructions.md")
    else:
        actual = len(instr.read_text(encoding="utf-8"))
        limit = int(cfg["runtime"]["custom_gpt"]["instruction"]["max_characters"])
        if actual > limit:
            errors.append(f"Instruction too long: {actual} > {limit}")

    kp = build / "builder" / "knowledge-package"
    files = [p for p in kp.rglob("*") if p.is_file()] if kp.exists() else []
    limit = int(cfg["runtime"]["custom_gpt"]["knowledge"]["max_files"])
    if len(files) > limit:
        errors.append(f"Too many Knowledge files: {len(files)} > {limit}")

    required = [
        build / "builder" / "instructions.md",
        build / "builder" / "conversation-starters.md",
        build / "builder" / "capabilities.md",
        build / cfg["runtime"]["custom_gpt"]["builder"].get("runtime_contract", "builder/runtime-contract.json"),
        build / "README.md",
        build / "COMPATIBILITY.md",
        build / "VERSION",
        build / "MANIFEST.json",
    ]
    for p in required:
        if not p.exists():
            errors.append(f"Missing required file: {p.relative_to(build)}")
    return errors


def validate_claude(root: Path, cfg: dict) -> list[str]:
    errors = []
    build = root / "build" / "claude"
    if not build.exists():
        return ["Claude build directory missing"]

    runtime_cfg = cfg["runtime"]["claude"]
    required = [
        build / "README.md",
        build / "VERSION",
        build / "MANIFEST.json",
        build / runtime_cfg["project"]["instructions"],
        build / runtime_cfg["project"]["runtime_contract"],
    ]
    for p in required:
        if not p.exists():
            errors.append(f"Missing required file: {p.relative_to(build)}")
    return errors


def validate_opencode(root: Path, cfg: dict) -> list[str]:
    errors = []
    build = root / "build" / "opencode"
    if not build.exists():
        return ["OpenCode build directory missing"]

    runtime_cfg = cfg["runtime"]["opencode"]
    required = [
        build / "README.md",
        build / "VERSION",
        build / "MANIFEST.json",
        build / runtime_cfg["layout"]["instructions"],
        build / runtime_cfg["layout"]["config"],
        build / runtime_cfg["layout"]["runtime_contract"],
    ]
    for p in required:
        if not p.exists():
            errors.append(f"Missing required file: {p.relative_to(build)}")

    if (build / "CLAUDE.md").exists():
        errors.append("OpenCode base runtime must use AGENTS.md, not CLAUDE.md")

    tool_contract = cfg.get("tools", {}).get("tools", [])
    tools_dir = build / runtime_cfg["layout"]["tools"]
    scripts_dir = build / runtime_cfg["layout"]["runtime_scripts"]
    expected_tools = []
    for item in tool_contract:
        if item.get("type") != "script":
            continue
        tool_name = "gpt_" + item["id"].replace("-", "_")
        expected_tools.append(tool_name)
        wrapper = tools_dir / f"{tool_name}.ts"
        script = scripts_dir / Path(item["script"]).name
        if not wrapper.exists():
            errors.append(f"Missing OpenCode custom tool: {wrapper.relative_to(build)}")
        if not script.exists():
            errors.append(f"Missing OpenCode runtime script: {script.relative_to(build)}")

    config_path = build / runtime_cfg["layout"]["config"]
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            permissions = config.get("permission", {})
            for item in tool_contract:
                if item.get("type") != "script":
                    continue
                tool_name = "gpt_" + item["id"].replace("-", "_")
                expected = "ask" if item.get("mutates_workspace") else "allow"
                if permissions.get(tool_name) != expected:
                    errors.append(f"OpenCode permission mismatch for {tool_name}")
        except Exception as exc:
            errors.append(f"Invalid OpenCode config: {exc}")

    skills_cfg = runtime_cfg.get("skills", {})
    if skills_cfg.get("enabled"):
        root_path = build / skills_cfg.get("directory", ".opencode/skills")
        canonical_skills = cfg.get("skills", {}).get("definitions") or skills_cfg.get("definitions", [])
        for skill in canonical_skills:
            skill_file = root_path / skill["id"] / "SKILL.md"
            if not skill_file.exists():
                errors.append(f"Missing OpenCode skill: {skill_file.relative_to(build)}")
            else:
                text = skill_file.read_text(encoding="utf-8")
                if f"name: {skill['name']}" not in text:
                    errors.append(f"OpenCode skill name mismatch: {skill['id']}")
                if f"description: {skill['description']}" not in text:
                    errors.append(f"OpenCode skill description mismatch: {skill['id']}")
    return errors


def _parse_skill_frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    block = text[4:end]
    data = {}
    for line in block.splitlines():
        if not line.strip() or line.startswith(" ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def validate_plugin(root: Path, cfg: dict) -> list[str]:
    errors = []
    build = root / "build" / "plugin"
    if not build.exists():
        return ["Plugin build directory missing"]

    runtime_cfg = cfg["runtime"]["plugin"]
    required = [
        build / "README.md",
        build / "VERSION",
        build / "MANIFEST.json",
        build / "runtime-contract.json",
        build / runtime_cfg["layout"]["manifest_file"],
    ]
    for p in required:
        if not p.exists():
            errors.append(f"Missing required file: {p.relative_to(build)}")

    plugin_json = build / runtime_cfg["layout"]["manifest_file"]
    if plugin_json.exists():
        try:
            manifest = json.loads(plugin_json.read_text(encoding="utf-8"))
            for key in ("name", "version", "description"):
                if not manifest.get(key):
                    errors.append(f"Plugin manifest missing required field: {key}")
        except Exception as exc:
            errors.append(f"Invalid plugin.json: {exc}")

    manifest_path = build / "MANIFEST.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("adapter_id") != "openai_plugin":
                errors.append("Plugin MANIFEST adapter_id mismatch")
            if manifest.get("plugin_manifest") != runtime_cfg["layout"]["manifest_file"]:
                errors.append("Plugin MANIFEST plugin_manifest mismatch")
            if manifest.get("contract_snapshot") != "runtime-contract.json":
                errors.append("Plugin MANIFEST contract_snapshot mismatch")
        except Exception as exc:
            errors.append(f"Invalid plugin MANIFEST.json: {exc}")

    skill_defs = cfg.get("skills", {}).get("definitions") or []
    skills_root = build / runtime_cfg["layout"]["skills"]
    if runtime_cfg.get("validation", {}).get("require_skill", True) and not skill_defs:
        errors.append("Plugin runtime requires at least one canonical skill")

    for skill in skill_defs:
        skill_dir = skills_root / skill["id"]
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            errors.append(f"Missing plugin skill: {skill_file.relative_to(build)}")
            continue

        text = skill_file.read_text(encoding="utf-8")
        frontmatter = _parse_skill_frontmatter(text)
        if runtime_cfg.get("validation", {}).get("require_skill_frontmatter", True):
            if frontmatter.get("name") != skill["name"]:
                errors.append(f"Plugin skill name mismatch: {skill['id']}")
            if frontmatter.get("description") != skill["description"]:
                errors.append(f"Plugin skill description mismatch: {skill['id']}")

        for key in ("references", "assets", "scripts"):
            for ref in skill.get(key, []) or []:
                expected = skill_dir / key / Path(ref).name
                if not expected.exists():
                    errors.append(
                        f"Missing plugin skill {key[:-1]}: {expected.relative_to(build)}"
                    )

    forbidden_parts = {
        ".git",
        ".github",
        "tests",
        "evals",
        "research",
        "build",
        "dist",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
    }
    for p in build.rglob("*"):
        rel = p.relative_to(build)
        if any(part in forbidden_parts for part in rel.parts):
            errors.append(f"Forbidden plugin runtime path: {rel}")

    return errors


def validate_chat(root: Path, cfg: dict) -> list[str]:
    errors = []
    build = root / "build" / "chat"
    if not build.exists():
        return ["Chat build directory missing"]

    required = [
        build / "START-HERE.md",
        build / "VERSION",
        build / "MANIFEST.json",
        build / "assistant" / "instructions.md",
    ]
    for p in required:
        if not p.exists():
            errors.append(f"Missing required file: {p.relative_to(build)}")

    for p in build.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(build)
        if any(part in FORBIDDEN_PARTS for part in rel.parts):
            errors.append(f"Forbidden runtime path: {rel}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    cfg = load_cfg(root)

    errors = []
    errors.extend(validate_chat(root, cfg))
    if cfg["runtime"]["custom_gpt"]["enabled"]:
        errors.extend(validate_custom(root, cfg))
    if cfg.get("runtime", {}).get("claude", {}).get("enabled"):
        errors.extend(validate_claude(root, cfg))
    if cfg.get("runtime", {}).get("opencode", {}).get("enabled"):
        errors.extend(validate_opencode(root, cfg))
    if cfg.get("runtime", {}).get("plugin", {}).get("enabled"):
        errors.extend(validate_plugin(root, cfg))

    if errors:
        print("VALIDATION: FAIL")
        for e in errors:
            print(f"- {e}")
        return 1

    print("VALIDATION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
