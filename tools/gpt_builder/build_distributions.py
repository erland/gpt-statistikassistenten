#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.project_model import (
    normalize_capability_contract,
    capability_level,
    normalize_artifact_contract,
    normalize_workspace_state_contract,
    normalize_tool_contract,
    artifact_contract_id_for_delivery_type,
)

try:
    import yaml
except Exception as exc:
    raise SystemExit("PyYAML is required to run build_distributions.py") from exc


FIXED_ZIP_DATE = (2020, 1, 1, 0, 0, 0)


def load_config(root: Path) -> dict:
    path = root / "gpt-project.yaml"
    if not path.exists():
        raise SystemExit(f"Missing config: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_write_zip(zip_path: Path, root: Path, files: list[Path]) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(files, key=lambda p: p.as_posix()):
            rel = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(rel, FIXED_ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree_filtered(src: Path, dst: Path, ignore_names: set[str] | None = None) -> None:
    # Runtime distributions must never contain local Python/cache artifacts.
    ignore_names = set(ignore_names or set()) | {
        "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"
    }
    if not src.exists():
        return
    for p in src.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(src)
        if any(part in ignore_names for part in rel.parts):
            continue
        if p.suffix in {".pyc", ".pyo"}:
            continue
        copy_file(p, dst / rel)


def render_template(text: str, replacements: dict[str, str]) -> str:
    for k, v in replacements.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def build_manifest(root: Path, runtime_id: str, version: str, entrypoint: str | None = None) -> dict:
    files = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.json":
            files.append({
                "path": p.relative_to(root).as_posix(),
                "sha256": sha256(p),
                "size": p.stat().st_size,
            })
    result = {
        "runtime_id": runtime_id,
        "version": version,
        "files": files,
    }
    if entrypoint:
        result["entrypoint"] = entrypoint
    return result


def write_manifest(root: Path, runtime_id: str, version: str, entrypoint: str | None = None) -> None:
    manifest = build_manifest(root, runtime_id, version, entrypoint)
    (root / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def chat_runtime_contract(cfg: dict) -> dict:
    """Compile canonical assistant contracts into a Chat-runtime snapshot."""
    return {
        "schema_version": 1,
        "runtime_id": "chatgpt_chat",
        "capabilities": normalize_capability_contract(cfg),
        "artifacts": normalize_artifact_contract(cfg),
        "workspace_state": normalize_workspace_state_contract(cfg),
        "tools": normalize_tool_contract(cfg),
    }


def copy_declared_tool_scripts(root: Path, cfg: dict, target: Path) -> list[str]:
    """Copy only explicitly declared script tools plus their shared library."""
    copied = []
    contract = normalize_tool_contract(cfg)
    for tool in contract.get("tools", []):
        if tool.get("type") != "script":
            continue
        script_ref = tool.get("script")
        if not script_ref:
            continue
        src = root / script_ref
        if not src.exists():
            raise SystemExit(f"Declared runtime tool script missing: {script_ref}")
        rel = Path(script_ref)
        if rel.parts and rel.parts[0] == "scripts":
            rel = Path(*rel.parts[1:])
        copy_file(src, target / rel)
        copied.append(script_ref)

    shared_lib = root / "scripts" / "lib"
    if copied and shared_lib.exists():
        copy_tree_filtered(shared_lib, target / "lib")
    return copied


def build_chat(root: Path, cfg: dict, build_root: Path, version: str) -> Path:
    out = build_root / "chat"
    ensure_clean_dir(out)

    assistant = out / "assistant"
    policies = assistant / "policies"
    policies.mkdir(parents=True)

    instr_src = root / cfg["instructions"]["canonical"]
    copy_file(instr_src, assistant / "instructions.md")

    starters_root = root / cfg["structure"]["conversation_starters"]["path"]
    if starters_root.exists():
        starters = [p for p in starters_root.rglob("*") if p.is_file() and p.name != "README.md"]
        if starters:
            combined = "\n\n".join(p.read_text(encoding="utf-8") for p in sorted(starters))
            (assistant / "conversation-starters.md").write_text(combined, encoding="utf-8")

    policy_root = root / cfg["structure"]["runtime_policy"]["path"]
    if policy_root.exists():
        for p in sorted(policy_root.rglob("*.md")):
            copy_file(p, policies / p.name)

    knowledge_root = root / cfg["knowledge_architecture"]["canonical_root"]
    if knowledge_root.exists():
        for p in sorted(knowledge_root.rglob("*")):
            if p.is_file() and p.name != "KNOWLEDGE.md":
                copy_file(p, out / "knowledge" / p.relative_to(knowledge_root))

    # Schemas/templates still follow the existing declarative Chat ZIP include model.
    # Runtime scripts are now selected from the canonical tool contract.
    for key in ["schemas", "templates"]:
        path = root / cfg["structure"][key]["path"]
        if path.exists():
            copy_tree_filtered(path, out / key, ignore_names={"README.md"})

    declared_tool_scripts = copy_declared_tool_scripts(root, cfg, out / "scripts")

    contract_snapshot = chat_runtime_contract(cfg)
    contract_snapshot["declared_tool_scripts"] = declared_tool_scripts
    (assistant / "runtime-contract.json").write_text(
        json.dumps(contract_snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    template_path = root / cfg["runtime"]["chat_zip"]["start_here_template"]
    template = template_path.read_text(encoding="utf-8")
    start_here = render_template(template, {
        "GPT_NAME": cfg["project"]["name"],
        "VERSION": version,
    })
    (out / "START-HERE.md").write_text(start_here, encoding="utf-8")
    (out / "VERSION").write_text(version + "\n", encoding="utf-8")
    write_manifest(out, cfg["project"]["id"] + "-chat", version, "START-HERE.md")
    manifest_path = out / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["adapter_id"] = "chatgpt_chat"
    manifest["contract_snapshot"] = "assistant/runtime-contract.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def _knowledge_priority_patterns(cfg: dict) -> list[str]:
    return list(cfg.get("knowledge_architecture", {}).get("custom_gpt", {}).get("priority", []) or [])


def _rank_knowledge(files: list[Path], root: Path, cfg: dict) -> list[Path]:
    patterns = _knowledge_priority_patterns(cfg)
    ranked = []
    for p in files:
        rel_from_project = p.relative_to(root).as_posix()
        rank = len(patterns) + 1
        for idx, pattern in enumerate(patterns):
            if fnmatch.fnmatch(rel_from_project, pattern):
                rank = idx
                break
        ranked.append((rank, rel_from_project, p))
    return [p for _, _, p in sorted(ranked)]


def collect_custom_knowledge(root: Path, cfg: dict, target: Path) -> list[Path]:
    knowledge_root = root / cfg["knowledge_architecture"]["canonical_root"]
    files = [p for p in sorted(knowledge_root.rglob("*")) if p.is_file() and p.name != "KNOWLEDGE.md"] if knowledge_root.exists() else []
    max_files = int(cfg["runtime"]["custom_gpt"]["knowledge"]["max_files"])
    strategy = cfg["runtime"]["custom_gpt"]["knowledge"]["strategy"]

    if len(files) <= max_files:
        selected = files
    elif strategy in {"prioritize", "hybrid"}:
        selected = _rank_knowledge(files, root, cfg)[:max_files]
    else:
        raise SystemExit(
            f"Custom GPT Knowledge has {len(files)} files but max is {max_files}; "
            f"strategy {strategy!r} requires explicit consolidation support for overflow."
        )

    copied = []
    for p in selected:
        dst = target / p.relative_to(knowledge_root)
        copy_file(p, dst)
        copied.append(dst)
    return copied


def compile_custom_instruction(text: str, mode: str, max_chars: int, core_markers: list[str]) -> str:
    if mode == "identical":
        compiled = text
    elif mode in {"compressed", "compiled"}:
        # Conservative deterministic compression: preserve wording and headings,
        # remove trailing whitespace and collapse repeated blank lines.
        lines = [line.rstrip() for line in text.splitlines()]
        out = []
        blank = False
        for line in lines:
            if not line.strip():
                if blank:
                    continue
                blank = True
                out.append("")
            else:
                blank = False
                out.append(line)
        compiled = "\n".join(out).strip() + "\n"
    else:
        raise SystemExit(f"Unknown Custom GPT instruction mode: {mode!r}")

    missing = [marker for marker in core_markers if marker not in compiled]
    if missing:
        raise SystemExit(f"Custom GPT instruction compilation removed core behavior markers: {missing}")
    if len(compiled) > max_chars:
        raise SystemExit(
            f"Custom GPT instruction is {len(compiled)} characters after {mode!r} compilation; max is {max_chars}. "
            "Reduce or explicitly mark distribution-specific source material; do not move core behavior to Knowledge."
        )
    return compiled


def custom_runtime_contract(cfg: dict) -> dict:
    """Compile canonical assistant contracts into a Custom GPT adapter snapshot."""
    tool_contract = normalize_tool_contract(cfg)
    tool_states = []
    for tool in tool_contract.get("tools", []):
        fallback = tool.get("runtime_fallback", "not_applicable")
        state = "missing" if tool.get("requirement") == "required" and fallback == "block" else (
            "reduced" if tool.get("type") in {"script", "local_command"} else "not_applicable"
        )
        tool_states.append({
            "id": tool.get("id"),
            "type": tool.get("type"),
            "requirement": tool.get("requirement"),
            "state": state,
            "runtime_fallback": fallback,
        })

    return {
        "schema_version": 1,
        "runtime_id": "chatgpt_custom",
        "capabilities": normalize_capability_contract(cfg),
        "artifacts": normalize_artifact_contract(cfg),
        "workspace_state": normalize_workspace_state_contract(cfg),
        "tools": tool_contract,
        "adapter": {
            "tool_execution": "not_embedded",
            "tool_states": tool_states,
            "builder_package": True,
        },
    }


def build_custom(root: Path, cfg: dict, build_root: Path, version: str) -> Path:
    out = build_root / "custom-gpt"
    ensure_clean_dir(out)
    builder = out / "builder"
    kp = builder / "knowledge-package"
    kp.mkdir(parents=True)

    instr = (root / cfg["instructions"]["canonical"]).read_text(encoding="utf-8")
    max_chars = int(cfg["runtime"]["custom_gpt"]["instruction"]["max_characters"])
    mode = cfg["runtime"]["custom_gpt"]["instruction"]["mode"]
    core_markers = list(cfg.get("instructions", {}).get("core_contract", {}).get("required_markers", []) or [])
    compiled_instr = compile_custom_instruction(instr, mode, max_chars, core_markers)
    (builder / "instructions.md").write_text(compiled_instr, encoding="utf-8")

    starters_root = root / cfg["structure"]["conversation_starters"]["path"]
    starters = [p for p in starters_root.rglob("*") if p.is_file() and p.name != "README.md"] if starters_root.exists() else []
    combined = "\n\n".join(p.read_text(encoding="utf-8") for p in sorted(starters))
    (builder / "conversation-starters.md").write_text(combined, encoding="utf-8")

    cap_tpl = (root / cfg["runtime"]["custom_gpt"]["templates"]["capabilities"]).read_text(encoding="utf-8")
    capability_contract = normalize_capability_contract(cfg)
    filesystem = capability_contract.get("requirements", {}).get("filesystem", {})
    filesystem_level = "required" if "required" in {filesystem.get("read"), filesystem.get("write")} else (
        "recommended" if "recommended" in {filesystem.get("read"), filesystem.get("write")} else "optional"
    )
    cap_text = render_template(cap_tpl, {
        "CAPABILITY_RECOMMENDATIONS": (
            f"- Webbsökning: {capability_level(capability_contract, 'web', 'optional')}\n"
            f"- Dataanalys/kodexekvering: {capability_level(capability_contract, 'code_execution', 'optional')}\n"
            f"- Bildgenerering: {capability_level(capability_contract, 'image_generation', 'optional')}\n"
            f"- Filhantering: {filesystem_level}"
        )
    })
    (builder / "capabilities.md").write_text(cap_text, encoding="utf-8")

    contract_snapshot = custom_runtime_contract(cfg)
    contract_ref = cfg["runtime"]["custom_gpt"]["builder"].get(
        "runtime_contract", "builder/runtime-contract.json"
    )
    contract_path = out / contract_ref
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        json.dumps(contract_snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    copied_knowledge = collect_custom_knowledge(root, cfg, kp)

    # Project-specific canonical Custom GPT Actions, when declared.
    actions_cfg = cfg.get("runtime", {}).get("custom_gpt", {}).get("actions", {})
    actions_dir = actions_cfg.get("directory") if isinstance(actions_cfg, dict) else None
    if actions_dir:
        src_actions = root / actions_dir
        if not src_actions.is_dir():
            raise SystemExit(f"Custom GPT actions directory missing: {actions_dir}")
        copy_tree_filtered(src_actions, builder / "actions")

    knowledge_root = root / cfg["knowledge_architecture"]["canonical_root"]
    canonical_knowledge = [p for p in sorted(knowledge_root.rglob("*")) if p.is_file() and p.name != "KNOWLEDGE.md"] if knowledge_root.exists() else []
    selected_rel = [p.relative_to(kp).as_posix() for p in copied_knowledge]
    selected_set = set(selected_rel)
    excluded_rel = [p.relative_to(knowledge_root).as_posix() for p in canonical_knowledge if p.relative_to(knowledge_root).as_posix() not in selected_set]
    compilation_report = {
        "runtime_id": "chatgpt_custom",
        "contract_snapshot": contract_ref,
        "instruction": {
            "mode": mode,
            "canonical_characters": len(instr),
            "compiled_characters": len(compiled_instr),
            "max_characters": max_chars,
            "core_markers_verified": len(core_markers),
        },
        "knowledge": {
            "strategy": cfg["runtime"]["custom_gpt"]["knowledge"]["strategy"],
            "canonical_files": len(canonical_knowledge),
            "selected_files": len(copied_knowledge),
            "max_files": int(cfg["runtime"]["custom_gpt"]["knowledge"]["max_files"]),
            "priority_patterns": _knowledge_priority_patterns(cfg),
            "selected": selected_rel,
            "excluded": excluded_rel,
        },
    }
    (builder / "compilation-report.json").write_text(json.dumps(compilation_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme_tpl = (root / cfg["runtime"]["custom_gpt"]["templates"]["readme"]).read_text(encoding="utf-8")
    (out / "README.md").write_text(
        render_template(readme_tpl, {"GPT_NAME": cfg["project"]["name"], "VERSION": version}),
        encoding="utf-8",
    )

    compat_tpl = (root / cfg["runtime"]["custom_gpt"]["templates"]["compatibility"]).read_text(encoding="utf-8")
    compat = render_template(compat_tpl, {
        "GPT_NAME": cfg["project"]["name"],
        "RUNTIME_RECOMMENDATION": "Ingen förvald primär runtime; välj endast utifrån faktisk capability/paritet.",
        "PARITY_TABLE": "Paritetsrapport genereras mer fullständigt i senare buildsteg.",
        "REDUCED_FEATURES": "Ej automatiskt analyserat ännu.",
        "MISSING_FEATURES": "Ej automatiskt analyserat ännu.",
    })
    (out / "COMPATIBILITY.md").write_text(compat, encoding="utf-8")
    (out / "VERSION").write_text(version + "\n", encoding="utf-8")

    write_manifest(out, cfg["project"]["id"] + "-custom-gpt", version)
    manifest_path = out / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["adapter_id"] = "chatgpt_custom"
    manifest["contract_snapshot"] = contract_ref
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def claude_runtime_contract(cfg: dict) -> dict:
    """Compile canonical assistant contracts into a Claude Projects snapshot."""
    tool_contract = normalize_tool_contract(cfg)
    tool_states = []
    for tool in tool_contract.get("tools", []):
        state = "not_applicable"
        reason = None
        if tool.get("type") in {"script", "local_command"}:
            state = "reduced" if tool.get("runtime_fallback") == "manual" else "missing"
            reason = "Claude Projects package does not embed local command execution."
        elif tool.get("type") in {"mcp", "api_action"}:
            state = "reduced"
            reason = "Availability depends on the Claude account/project integration."

        item = {
            "id": tool.get("id"),
            "type": tool.get("type"),
            "requirement": tool.get("requirement"),
            "state": state,
        }
        if reason:
            item["reason"] = reason
        tool_states.append(item)

    return {
        "schema_version": 1,
        "runtime_id": "claude_project",
        "capabilities": normalize_capability_contract(cfg),
        "artifacts": normalize_artifact_contract(cfg),
        "workspace_state": normalize_workspace_state_contract(cfg),
        "tools": tool_contract,
        "adapter": {
            "mode": "claude_project",
            "project_instructions": True,
            "project_knowledge": True,
            "claude_code_conventions": False,
            "embedded_local_tools": False,
            "tool_states": tool_states,
        },
    }


def build_claude(root: Path, cfg: dict, build_root: Path, version: str) -> Path:
    out = build_root / "claude"
    ensure_clean_dir(out)

    runtime_cfg = cfg["runtime"]["claude"]
    project_dir = out / "project"
    project_dir.mkdir(parents=True)

    instr_src = root / cfg["instructions"]["canonical"]
    instructions_ref = runtime_cfg["project"]["instructions"]
    instructions_path = out / instructions_ref
    copy_file(instr_src, instructions_path)

    knowledge_root = root / cfg["knowledge_architecture"]["canonical_root"]
    knowledge_ref = runtime_cfg["project"]["knowledge"]
    knowledge_target = out / knowledge_ref
    if knowledge_root.exists():
        for p in sorted(knowledge_root.rglob("*")):
            if p.is_file() and p.name != "KNOWLEDGE.md":
                copy_file(p, knowledge_target / p.relative_to(knowledge_root))

    contract_ref = runtime_cfg["project"]["runtime_contract"]
    contract_path = out / contract_ref
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        json.dumps(claude_runtime_contract(cfg), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    readme_tpl = (root / runtime_cfg["templates"]["readme"]).read_text(encoding="utf-8")
    (out / "README.md").write_text(
        render_template(readme_tpl, {
            "GPT_NAME": cfg["project"]["name"],
            "VERSION": version,
        }),
        encoding="utf-8",
    )
    (out / "VERSION").write_text(version + "\n", encoding="utf-8")

    write_manifest(out, cfg["project"]["id"] + "-claude", version, "README.md")
    manifest_path = out / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["adapter_id"] = "claude_project"
    manifest["contract_snapshot"] = contract_ref
    manifest["project_instructions"] = instructions_ref
    manifest["project_knowledge"] = knowledge_ref
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out


def canonical_skill_definitions(cfg: dict) -> list[dict]:
    """Return platform-neutral skill definitions with conservative legacy fallback."""
    canonical = cfg.get("skills")
    if isinstance(canonical, dict):
        definitions = canonical.get("definitions")
        if isinstance(definitions, list) and definitions:
            return definitions

    legacy = cfg.get("runtime", {}).get("opencode", {}).get("skills", {})
    definitions = legacy.get("definitions") if isinstance(legacy, dict) else None
    if isinstance(definitions, list) and definitions:
        return definitions

    project = cfg.get("project", {})
    project_id = str(project.get("id") or "assistant")
    name = str(project.get("name") or project_id)
    description = str(project.get("description") or f"Use {name} according to its canonical instructions.").strip()
    return [{
        "id": project_id,
        "name": project_id,
        "description": description,
        "references": [],
        "assets": [],
        "scripts": [],
        "_inferred_default": True,
    }]


def plugin_manifest(cfg: dict, version: str) -> dict:
    """Build deterministic Plugin v1 metadata from canonical project data only."""
    project = cfg.get("project") or {}
    manifest = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": str(project.get("id") or "").strip(),
        "version": str(version).strip(),
        "description": str(project.get("description") or "").strip(),
    }

    author = project.get("author")
    if isinstance(author, str) and author.strip():
        manifest["author"] = {"name": author.strip()}
    elif isinstance(author, dict):
        name = str(author.get("name") or "").strip()
        if name:
            manifest["author"] = {"name": name}

    # Only emit optional metadata when it is explicitly canonical.
    for source_key, manifest_key in (
        ("license", "license"),
        ("homepage", "homepage"),
        ("repository", "repository"),
    ):
        value = project.get(source_key)
        if isinstance(value, str) and value.strip():
            manifest[manifest_key] = value.strip()

    missing = [key for key in ("name", "version", "description") if not manifest.get(key)]
    if missing:
        raise SystemExit("Plugin manifest requires canonical metadata: " + ", ".join(missing))

    return manifest


def write_plugin_manifest(target: Path, cfg: dict, version: str) -> Path:
    """Write plugin.json deterministically and return its path."""
    path = target / "plugin.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(plugin_manifest(cfg, version), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _project_relative_files(root: Path, directory: Path, *, exclude_names: set[str] | None = None) -> list[str]:
    """Return deterministic project-relative file paths from a canonical directory."""
    exclude_names = set(exclude_names or set())
    if not directory.exists():
        return []
    return [
        p.relative_to(root).as_posix()
        for p in sorted(directory.rglob("*"))
        if p.is_file() and p.name not in exclude_names
    ]


def _declared_runtime_script_refs(cfg: dict) -> list[str]:
    """Return only scripts explicitly declared as runtime tools."""
    refs = []
    for tool in normalize_tool_contract(cfg).get("tools", []):
        if tool.get("type") != "script":
            continue
        ref = tool.get("script")
        if ref:
            refs.append(str(ref))
    return sorted(set(refs))


def resolve_plugin_skill_resources(root: Path, cfg: dict, skill: dict) -> dict[str, list[str]]:
    """Resolve canonical resources into the Plugin v1 references/assets/scripts model.

    Explicit skill metadata wins per resource class. When a class is not declared,
    Plugin v1 uses a conservative project-level fallback:
    canonical Knowledge becomes references, templates become assets, and only
    explicitly declared runtime tool scripts become scripts.
    """
    knowledge_root = root / cfg.get("knowledge_architecture", {}).get("canonical_root", "knowledge")
    templates_root = root / cfg.get("structure", {}).get("templates", {}).get("path", "templates")

    fallback = {
        "references": _project_relative_files(root, knowledge_root, exclude_names={"KNOWLEDGE.md"}),
        "assets": _project_relative_files(root, templates_root, exclude_names={"README.md"}),
        "scripts": _declared_runtime_script_refs(cfg),
    }

    resolved: dict[str, list[str]] = {}
    for key in ("references", "assets", "scripts"):
        declared = skill.get(key)
        values = list(declared) if isinstance(declared, list) and declared else list(fallback[key])
        unique = sorted(dict.fromkeys(str(value) for value in values))
        for ref in unique:
            if not (root / ref).is_file():
                raise SystemExit(f"Plugin skill {skill.get('id', '<unknown>')} {key[:-1]} missing: {ref}")
        resolved[key] = unique
    return resolved


def compile_skill_markdown(
    skill: dict,
    *,
    compatibility: str | None = None,
    canonical_instruction: str | None = None,
    include_canonical_behavior: bool = False,
) -> str:
    """Compile one canonical skill definition into deterministic SKILL.md text."""
    frontmatter = [
        "---",
        f"name: {skill['name']}",
        f"description: {skill['description']}",
    ]
    if compatibility:
        frontmatter.append(f"compatibility: {compatibility}")
    frontmatter.extend([
        "metadata:",
        "  source: generated-from-canonical-project",
        "---",
        "",
        "## Purpose",
        "",
        str(skill["description"]).strip(),
        "",
    ])

    body = frontmatter

    if (skill.get("_inferred_default") or include_canonical_behavior) and canonical_instruction:
        body.extend([
            "## Canonical behavior",
            "",
            canonical_instruction.strip(),
            "",
        ])

    references = list(skill.get("references", []) or [])
    if references:
        body.extend(["## References", ""])
        for ref in references:
            body.append(f"- Read `references/{Path(ref).name}` when that material is relevant.")
        body.append("")

    assets = list(skill.get("assets", []) or [])
    if assets:
        body.extend(["## Assets", ""])
        for asset in assets:
            body.append(f"- Use `assets/{Path(asset).name}` when the task requires that resource.")
        body.append("")

    scripts = list(skill.get("scripts", []) or [])
    if scripts:
        body.extend(["## Scripts", ""])
        for script in scripts:
            body.append(f"- Use `scripts/{Path(script).name}` only when runtime execution is available and appropriate.")
        body.append("")

    return "\n".join(body).rstrip() + "\n"


def build_opencode_skills(root: Path, cfg: dict, out: Path) -> list[str]:
    """Generate OpenCode skills from the canonical skill contract."""
    runtime_cfg = cfg["runtime"]["opencode"]
    skills_cfg = runtime_cfg.get("skills", {})
    if not skills_cfg.get("enabled"):
        return []

    skill_root = out / skills_cfg.get("directory", ".opencode/skills")
    canonical_instruction = (root / cfg["instructions"]["canonical"]).read_text(encoding="utf-8")
    built: list[str] = []

    for skill in canonical_skill_definitions(cfg):
        skill_id = skill["id"]
        skill_dir = skill_root / skill_id

        for ref_key, target_name in (
            ("references", "references"),
            ("assets", "assets"),
            ("scripts", "scripts"),
        ):
            for ref in skill.get(ref_key, []) or []:
                src = root / ref
                if not src.exists():
                    raise SystemExit(f"Canonical skill {ref_key[:-1]} missing: {ref}")
                copy_file(src, skill_dir / target_name / src.name)

        body = compile_skill_markdown(
            skill,
            compatibility="opencode",
            canonical_instruction=canonical_instruction,
        )
        (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
        built.append(skill_id)

    return built


def plugin_runtime_contract(cfg: dict, built_skills: list[str] | None = None) -> dict:
    """Compile canonical assistant contracts into an OpenAI Plugin snapshot."""
    built_skills = list(built_skills or [])
    return {
        "schema_version": 1,
        "runtime_id": "openai_plugin",
        "capabilities": normalize_capability_contract(cfg),
        "artifacts": normalize_artifact_contract(cfg),
        "workspace_state": normalize_workspace_state_contract(cfg),
        "tools": normalize_tool_contract(cfg),
        "adapter": {
            "mode": "openai_plugin",
            "skills_first": True,
            "skills": built_skills,
            "mcp_generated": False,
            "ui_generated": False,
            "hooks_generated": False,
            "parity_notes": {
                "behavior": "Canonical behavior is projected through skills.",
                "artifact": "Plugin package is generated as a runtime distribution.",
                "workspace_state": "Persistent workspace/state depends on the host runtime and is not created by Plugin v1.",
                "tool": "Canonical local script tools are packaged only as skill resources; Plugin v1 does not generate MCP execution.",
                "capability": "External tool execution and advanced integrations depend on the host runtime in Plugin v1.",
            },
        },
    }


def _copy_skill_resources(root: Path, skill_dir: Path, resources: dict[str, list[str]]) -> None:
    """Copy resolved skill resources and reject basename collisions."""
    for key in ("references", "assets", "scripts"):
        seen_names: set[str] = set()
        for ref in resources.get(key, []):
            src = root / ref
            name = src.name
            if name in seen_names:
                raise SystemExit(f"Plugin skill resource collision in {key}: {name}")
            seen_names.add(name)
            copy_file(src, skill_dir / key / name)


def build_plugin(root: Path, cfg: dict, build_root: Path, version: str) -> Path:
    """Build a portable skills-first OpenAI Plugin v1 distribution."""
    out = build_root / "plugin"
    ensure_clean_dir(out)
    write_plugin_manifest(out, cfg, version)

    canonical_instruction = (root / cfg["instructions"]["canonical"]).read_text(encoding="utf-8")
    built_skills: list[str] = []
    for skill in canonical_skill_definitions(cfg):
        skill_id = skill["id"]
        skill_dir = out / "skills" / skill_id
        resources = resolve_plugin_skill_resources(root, cfg, skill)
        _copy_skill_resources(root, skill_dir, resources)

        compiled_skill = dict(skill)
        compiled_skill.update(resources)
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            compile_skill_markdown(
                compiled_skill,
                canonical_instruction=canonical_instruction,
                include_canonical_behavior=True,
            ),
            encoding="utf-8",
        )
        built_skills.append(skill_id)

    if not built_skills:
        raise SystemExit("Plugin build requires at least one skill")

    readme_tpl = (root / cfg["runtime"]["plugin"]["templates"]["readme"]).read_text(encoding="utf-8")
    (out / "README.md").write_text(
        render_template(readme_tpl, {
            "GPT_NAME": cfg["project"]["name"],
            "VERSION": version,
            "SKILLS": "\n".join(f"- `{skill_id}`" for skill_id in built_skills),
        }),
        encoding="utf-8",
    )
    (out / "VERSION").write_text(version + "\n", encoding="utf-8")
    (out / "runtime-contract.json").write_text(
        json.dumps(plugin_runtime_contract(cfg, built_skills), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    write_manifest(out, cfg["project"]["id"] + "-plugin", version, "plugin.json")
    manifest_path = out / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["adapter_id"] = "openai_plugin"
    manifest["plugin_manifest"] = "plugin.json"
    manifest["skills"] = built_skills
    manifest["contract_snapshot"] = "runtime-contract.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def _opencode_tool_name(tool_id: str) -> str:
    return "gpt_" + tool_id.replace("-", "_")


def _opencode_tool_wrapper(tool: dict, script_ref: str) -> str:
    tool_id = tool["id"]
    description = tool.get("purpose", tool_id).replace('"', '\\"')
    arg_schema = 'projectRoot: tool.schema.string().optional().describe("Project root relative to the worktree")'
    if tool_id == "project-hygiene":
        arg_schema += ',\n    mode: tool.schema.enum(["checkpoint", "final"]).optional(),\n    fix: tool.schema.boolean().optional()'
        command_lines = '''
    const mode = args.mode ?? "checkpoint"
    const fix = args.fix ? ["--fix"] : []
    const cmd = ["python3", script, "--project-root", projectRoot, "--mode", mode, ...fix, "--json"]'''
    elif tool_id == "build-distributions":
        arg_schema += ',\n    version: tool.schema.string().optional(),\n    targets: tool.schema.string().optional()'
        command_lines = '''
    const version = args.version ?? "0.0.0-dev"
    const targets = args.targets ?? "project,chat,custom-gpt,claude,opencode,plugin"
    const cmd = ["python3", script, "--project-root", projectRoot, "--version", version, "--targets", targets]'''
    elif tool_id == "recommend-next-step":
        command_lines = '''
    const cmd = ["python3", script, "--project-root", projectRoot, "--json"]'''
    else:
        command_lines = '''
    const cmd = ["python3", script, "--project-root", projectRoot]'''

    return f'''import {{ tool }} from "@opencode-ai/plugin"
import path from "path"

export default tool({{
  description: "{description}",
  args: {{
    {arg_schema}
  }},
  async execute(args, context) {{
    const projectRoot = path.resolve(context.worktree, args.projectRoot ?? ".")
    const script = path.join(context.worktree, "{script_ref}"){command_lines}
    const proc = Bun.spawn(cmd, {{ cwd: context.worktree, stdout: "pipe", stderr: "pipe" }})
    const stdout = await new Response(proc.stdout).text()
    const stderr = await new Response(proc.stderr).text()
    const code = await proc.exited
    if (code !== 0) throw new Error((stderr || stdout || ("Tool failed with exit code " + code)).trim())
    return (stdout || stderr).trim()
  }}
}})
'''


def build_opencode_tools(root: Path, cfg: dict, out: Path) -> list[dict]:
    runtime_cfg = cfg["runtime"]["opencode"]
    scripts_target = out / runtime_cfg["layout"]["runtime_scripts"]
    copied = copy_declared_tool_scripts(root, cfg, scripts_target)
    copied_set = set(copied)
    tools_target = out / runtime_cfg["layout"]["tools"]
    tools_target.mkdir(parents=True, exist_ok=True)

    integrations = []
    permissions = {
        "skill": {"*": "allow"},
        "bash": "ask",
        "edit": "ask",
    }
    for tool_cfg in normalize_tool_contract(cfg).get("tools", []):
        if tool_cfg.get("type") != "script":
            continue
        script_ref = tool_cfg.get("script")
        if not script_ref or script_ref not in copied_set:
            continue
        packaged_script = str(Path(runtime_cfg["layout"]["runtime_scripts"]) / Path(script_ref).name)
        tool_name = _opencode_tool_name(tool_cfg["id"])
        (tools_target / f"{tool_name}.ts").write_text(
            _opencode_tool_wrapper(tool_cfg, packaged_script),
            encoding="utf-8",
        )
        permissions[tool_name] = "ask" if tool_cfg.get("mutates_workspace") else "allow"
        integrations.append({
            "id": tool_cfg["id"],
            "opencode_tool": tool_name,
            "script": packaged_script,
            "permission": permissions[tool_name],
        })

    config_path = out / runtime_cfg["layout"]["config"]
    config_path.write_text(json.dumps({
        "$schema": "https://opencode.ai/config.json",
        "permission": permissions,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return integrations


def opencode_runtime_contract(cfg: dict, built_skills: list[str] | None = None, tool_integrations: list[dict] | None = None) -> dict:
    """Compile canonical assistant contracts into an OpenCode workspace snapshot."""
    built_skills = list(built_skills or [])
    tool_integrations = list(tool_integrations or [])
    return {
        "schema_version": 1,
        "runtime_id": "opencode",
        "capabilities": normalize_capability_contract(cfg),
        "artifacts": normalize_artifact_contract(cfg),
        "workspace_state": normalize_workspace_state_contract(cfg),
        "tools": normalize_tool_contract(cfg),
        "adapter": {
            "mode": "opencode_workspace",
            "instructions": "AGENTS.md",
            "skills_included": bool(built_skills),
            "skills": built_skills,
            "tool_integration": "custom_tools",
            "tool_integrations": tool_integrations,
            "workspace_first": True,
        },
    }


def build_opencode(root: Path, cfg: dict, build_root: Path, version: str) -> Path:
    out = build_root / "opencode"
    ensure_clean_dir(out)

    runtime_cfg = cfg["runtime"]["opencode"]

    canonical_instruction = (root / cfg["instructions"]["canonical"]).read_text(encoding="utf-8")
    agents_path = out / runtime_cfg["layout"]["instructions"]
    agents_path.write_text(
        canonical_instruction.rstrip()
        + "\n\n## OpenCode adapter\n\n"
        + "- Treat this AGENTS.md as a generated projection of the canonical assistant instructions.\n"
        + "- Work inside this repository/workspace.\n"
        + "- Reusable workflows may be available as project-local skills under .opencode/skills/.\n"
        + "- Load a skill when its description matches the current task instead of duplicating that workflow here.\n"
        + "- Use only the explicitly generated OpenCode custom tools for canonical runtime scripts; do not infer extra scripts as tools.\n"
        + "- The OpenCode workspace is the GPT Byggaren runtime; the GPT project being worked on may be a subdirectory. Pass projectRoot to generated tools when the target project is not the workspace root.\n",
        encoding="utf-8",
    )

    knowledge_root = root / cfg["knowledge_architecture"]["canonical_root"]
    knowledge_target = out / runtime_cfg["layout"]["knowledge"]
    if knowledge_root.exists():
        for p in sorted(knowledge_root.rglob("*")):
            if p.is_file() and p.name != "KNOWLEDGE.md":
                copy_file(p, knowledge_target / p.relative_to(knowledge_root))

    built_skills = build_opencode_skills(root, cfg, out)
    tool_integrations = build_opencode_tools(root, cfg, out)

    contract_ref = runtime_cfg["layout"]["runtime_contract"]
    contract_path = out / contract_ref
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        json.dumps(opencode_runtime_contract(cfg, built_skills, tool_integrations), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    readme_tpl = (root / runtime_cfg["templates"]["readme"]).read_text(encoding="utf-8")
    (out / "README.md").write_text(
        render_template(readme_tpl, {
            "GPT_NAME": cfg["project"]["name"],
            "VERSION": version,
        }),
        encoding="utf-8",
    )
    (out / "VERSION").write_text(version + "\n", encoding="utf-8")

    write_manifest(out, cfg["project"]["id"] + "-opencode", version, "AGENTS.md")
    manifest_path = out / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["adapter_id"] = "opencode"
    manifest["contract_snapshot"] = contract_ref
    manifest["instructions"] = runtime_cfg["layout"]["instructions"]
    manifest["skills_included"] = bool(built_skills)
    manifest["skills"] = built_skills
    manifest["tool_integration"] = "custom_tools"
    manifest["tools"] = [item["opencode_tool"] for item in tool_integrations]
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out


RUNTIME_BUILDERS = {
    "chat": build_chat,
    "custom_gpt": build_custom,
    "claude": build_claude,
    "opencode": build_opencode,
    "plugin": build_plugin,
}


def configured_targets(cfg: dict) -> list[str]:
    targets = cfg.get("build_system", {}).get("targets") or ["project"]
    return [str(target) for target in targets]


def build_runtime_target(
    root: Path,
    cfg: dict,
    build_root: Path,
    dist: Path,
    version: str,
    target: str,
) -> Path | None:
    target_cfg = (cfg.get("build_system", {}).get("runtime_targets") or {}).get(target)
    if not isinstance(target_cfg, dict):
        raise SystemExit(f"Unknown runtime build target: {target}")

    runtime_key = target_cfg["runtime_key"]
    runtime_cfg = cfg.get("runtime", {}).get(runtime_key, {})
    if not runtime_cfg.get("enabled"):
        return None

    builder_id = target_cfg["builder"]
    builder = RUNTIME_BUILDERS.get(builder_id)
    if builder is None:
        raise SystemExit(f"No runtime builder registered for builder id: {builder_id}")

    runtime_root = builder(root, cfg, build_root, version)
    filename = (
        target_cfg["filename_pattern"]
        .replace("<project-id>", cfg["project"]["id"])
        .replace("<version>", version)
    )
    zip_path = dist / filename
    stable_write_zip(zip_path, runtime_root, [p for p in runtime_root.rglob("*") if p.is_file()])
    return zip_path


def project_files(root: Path) -> list[Path]:
    excluded_top = {"build", "dist", ".git"}
    result = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if rel.parts and rel.parts[0] in excluded_top:
            continue
        if "__pycache__" in rel.parts or ".pytest_cache" in rel.parts:
            continue
        result.append(p)
    return result


def write_checksums(dist: Path) -> None:
    lines = []
    for p in sorted(dist.glob("*.zip")):
        lines.append(f"{sha256(p)}  {p.name}")
    (dist / "SHA256SUMS.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def artifact_type_for_distribution(cfg: dict, filename: str, version: str) -> str:
    project_id = cfg["project"]["id"]
    if filename == f"{project_id}-project.zip":
        return "project_zip"

    for target_cfg in (cfg.get("build_system", {}).get("runtime_targets") or {}).values():
        pattern = target_cfg.get("filename_pattern")
        artifact_type = target_cfg.get("artifact_type")
        if not pattern or not artifact_type:
            continue
        expected = pattern.replace("<project-id>", project_id).replace("<version>", version)
        if filename == expected:
            return artifact_type
    return "zip"


def write_delivery_manifest(dist: Path, cfg: dict, version: str) -> None:
    artifacts = []
    for p in sorted(dist.iterdir()):
        if not p.is_file() or p.name in {"DELIVERY-MANIFEST.json"}:
            continue
        if p.suffix == ".zip":
            artifact_type = artifact_type_for_distribution(cfg, p.name, version)
        elif p.name == "SHA256SUMS.txt":
            artifact_type = "checksums"
        else:
            artifact_type = "file"
        artifact = {
            "type": artifact_type,
            "file": p.name,
            "sha256": sha256(p),
            "size": p.stat().st_size,
        }
        contract_id = artifact_contract_id_for_delivery_type(cfg, artifact_type)
        if contract_id:
            artifact["artifact_id"] = contract_id
        artifacts.append(artifact)

    payload = {
        "project": cfg["project"]["id"],
        "project_name": cfg["project"]["name"],
        "version": version,
        "primary_runtime": cfg.get("runtime", {}).get("primary", "none"),
        "runtime_strategy": "peer_distributions",
        "runtime_targets": [
            target_cfg["runtime_id"]
            for target, target_cfg in (cfg.get("build_system", {}).get("runtime_targets") or {}).items()
            if target in (cfg.get("build_system", {}).get("targets") or [])
            and cfg.get("runtime", {}).get(target_cfg["runtime_key"], {}).get("enabled")
        ],
        "custom_gpt_enabled": bool(cfg["runtime"]["custom_gpt"]["enabled"]),
        "artifacts": artifacts,
    }
    (dist / "DELIVERY-MANIFEST.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--version", default="0.0.0-dev")
    parser.add_argument(
        "--targets",
        default=None,
        help="Comma-separated build targets. Defaults to build_system.targets from gpt-project.yaml.",
    )
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    cfg = load_config(root)
    build_root = root / "build"
    dist = root / "dist"
    build_root.mkdir(exist_ok=True)
    dist.mkdir(exist_ok=True)

    selected_targets = (
        [t.strip() for t in args.targets.split(",") if t.strip()]
        if args.targets
        else configured_targets(cfg)
    )
    targets = set(selected_targets)
    project_id = cfg["project"]["id"]
    version = args.version

    runtime_targets = cfg.get("build_system", {}).get("runtime_targets") or {}
    unknown = targets - (set(runtime_targets) | {"project"})
    if unknown:
        raise SystemExit("Unknown build target(s): " + ", ".join(sorted(unknown)))

    for target in selected_targets:
        if target == "project":
            continue
        build_runtime_target(root, cfg, build_root, dist, version, target)

    if "project" in targets:
        project_zip = dist / f"{project_id}-project.zip"
        stable_write_zip(project_zip, root, project_files(root))

    write_checksums(dist)
    write_delivery_manifest(dist, cfg, version)

    print(f"Build complete: {dist}")
    for p in sorted(dist.iterdir()):
        if p.is_file():
            print(p.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
