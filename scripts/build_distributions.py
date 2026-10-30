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
# Support CLI execution and direct importlib loading used by regression tests.
import importlib.util as _skill_importlib
_skill_module_path = Path(__file__).resolve().parent / "lib" / "canonical_skill_sources.py"
_skill_spec = _skill_importlib.spec_from_file_location("canonical_skill_sources", _skill_module_path)
_skill_module = _skill_importlib.module_from_spec(_skill_spec)
_skill_spec.loader.exec_module(_skill_module)
projected_instruction = _skill_module.projected_instruction
skill_instruction = _skill_module.skill_instruction
is_modular = _skill_module.is_modular

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
        rel = Path(script_ref).name
        copy_file(src, target / rel)
        copied.append(script_ref)

    shared_lib = root / "scripts" / "lib"
    if copied and shared_lib.exists():
        copy_tree_filtered(shared_lib, target / "lib")
    return copied


def copy_portable_skill_modules(root: Path, cfg: dict, target: Path) -> list[str]:
    """Compile canonical skills and copy their explicit resources for text-first runtimes.

    These files are included as usable references without assuming that Claude
    Projects or Chat ZIP will automatically install/activate host Skills.
    """
    result = []
    validate_skill_dependencies(canonical_skill_definitions(cfg))
    for skill in canonical_skill_definitions(cfg):
        ident = skill["id"]
        destination = target / ident
        for category in ("references", "assets", "scripts"):
            seen = set()
            for source_ref in skill.get(category, []) or []:
                source = root / source_ref
                if not (source.is_file() or (category == "assets" and source.is_dir())) or source.is_symlink() or not source.resolve().is_relative_to(root.resolve()):
                    raise SystemExit(f"Missing/unsafe canonical skill resource: {source_ref}")
                if source.name in seen:
                    raise SystemExit(f"Colliding skill resource filename: {source.name}")
                seen.add(source.name)
                if category == "assets" and source.is_dir():
                    copy_tree_filtered(source, destination / category / source.name)
                else:
                    copy_file(source, destination / category / source.name)
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SKILL.md").write_text(
            compile_skill_markdown(
                skill,
                compatibility="portable-reference",
                canonical_instruction=(
                    skill_instruction(root, cfg, canonical_skill_definitions(cfg), skill)
                    if is_modular(cfg) else None
                ),
                include_canonical_behavior=is_modular(cfg),
            ),
            encoding="utf-8",
        )
        result.append(ident)
    return result


def bundle_distribution_engine(root: Path, destination: Path) -> None:
    """Include the offline project generator in a runtime distribution."""
    engine = destination / "distribution-engine"
    engine.mkdir(parents=True, exist_ok=True)
    required = ("scripts/build_distributions.py", "scripts/lib/project_model.py", "gpt-project.yaml")
    if any(not (root / relative).is_file() for relative in required):
        raise FileNotFoundError("Canonical distribution engine is incomplete")
    copy_file(root / "gpt-project.yaml", engine / "gpt-project.yaml")
    for folder in ("scripts", "templates"):
        for source_file in sorted((root / folder).rglob("*")):
            if not source_file.is_file() or "__pycache__" in source_file.parts or source_file.suffix == ".pyc":
                continue
            relative = source_file.relative_to(root)
            copy_file(source_file, engine / relative)


def build_chat(root: Path, cfg: dict, build_root: Path, version: str) -> Path:
    out = build_root / "chat"
    ensure_clean_dir(out)

    # Only assistants that explicitly need the offline project generator include it.
    if cfg.get("runtime", {}).get("chat_zip", {}).get("bundle_distribution_engine", False):
        bundle_distribution_engine(root, out)
    assistant = out / "assistant"
    policies = assistant / "policies"
    policies.mkdir(parents=True)

    instr_src = root / cfg["instructions"]["canonical"]
    (assistant / "instructions.md").write_text(projected_instruction(root, cfg, canonical_skill_definitions(cfg)), encoding="utf-8")
    copy_portable_skill_modules(root, cfg, assistant / "skills")

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
    instructions_path.parent.mkdir(parents=True, exist_ok=True)
    instructions_path.write_text(projected_instruction(root, cfg, canonical_skill_definitions(cfg)), encoding="utf-8")
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



def expose_canonical_engine_skill_files(engine_root: Path, skill_dir: Path) -> None:
    """Expose original canonical engine files as ordinary Skill resources."""
    for file in sorted(engine_root.rglob("*")):
        if not file.is_file():
            continue
        relative = file.relative_to(engine_root)
        category = "scripts" if relative.parts[0] == "scripts" else "assets"
        copy_file(file, skill_dir / category / "canonical-engine" / relative)


def build_claude_skills(root: Path, cfg: dict, build_root: Path, version: str) -> Path:
    """Build a Claude Skills distribution with the canonical portable resources."""
    out = build_root / "claude-skills"
    ensure_clean_dir(out)
    canonical_instruction = projected_instruction(root, cfg, canonical_skill_definitions(cfg))
    validate_skill_dependencies(canonical_skill_definitions(cfg))
    built_skills = []
    for skill in canonical_skill_definitions(cfg):
        skill_id = skill["id"]
        skill_dir = out / "skills" / skill_id
        resources = resolve_plugin_skill_resources(root, cfg, skill)
        _copy_skill_resources(root, skill_dir, resources)
        if cfg.get("project", {}).get("id") == "gpt-byggaren" and skill_id == "distribution-and-parity":
            from package_distribution_engine import package as package_engine
            staging = build_root / "claude-skills-engine"
            ensure_clean_dir(staging)
            bundle_distribution_engine(root, staging)
            expose_canonical_engine_skill_files(staging / "distribution-engine", skill_dir)
            engine_root = staging / "distribution-engine"
            package_engine(
                root=root,
                version=version,
                output=skill_dir / "assets" / "gpt-byggaren-engine.zip",
            )
        if cfg.get("project", {}).get("id") == "gpt-byggaren":
            if skill_id == "distribution-and-parity":
                copy_file(root / "scripts" / "selftest_distribution_engine.py",
                          skill_dir / "scripts" / "selftest_distribution_engine.py")
        compiled = dict(skill)
        compiled.update(resources)
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            compile_skill_markdown(
                compiled,
                canonical_instruction=skill_instruction(root, cfg, canonical_skill_definitions(cfg), skill),
                include_canonical_behavior=True,
                runtime_requirements=plugin_script_runtime_requirements(cfg, resources["scripts"]),
            ),
            encoding="utf-8",
        )
        built_skills.append(skill_id)
    (out / "README.md").write_text(
        "# Claude Skills – " + cfg["project"]["name"] + "\n\n"
        "Install the individual folders under skills/ as Claude Skills. "
        "Scripts require a compatible execution environment; packaging alone "
        "does not verify host execution.\n",
        encoding="utf-8",
    )
    (out / "VERSION").write_text(version + "\n", encoding="utf-8")
    (out / "runtime-contract.json").write_text(
        json.dumps(claude_skills_runtime_contract(cfg, built_skills), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_manifest(out, cfg["project"]["id"] + "-claude-skills", version, "README.md")
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


def validate_skill_dependencies(definitions: list[dict]) -> None:
    """Fail closed on unknown, self-referential or cyclic Skill handoffs."""
    ids = [item["id"] for item in definitions]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate canonical Skill IDs")
    graph = {}
    for skill in definitions:
        dependencies = skill.get("requires_skills", [])
        if not isinstance(dependencies, list) or len(dependencies) != len(set(dependencies)):
            raise ValueError(f"Invalid Skill dependencies: {skill['id']}")
        for dep in dependencies:
            if dep not in ids or dep == skill["id"]:
                raise ValueError(f"Unknown or self Skill dependency: {skill['id']} -> {dep}")
        graph[skill["id"]] = dependencies

    visiting, visited = set(), set()
    def visit(skill_id: str) -> None:
        if skill_id in visiting:
            raise ValueError(f"Cyclic Skill dependencies involving {skill_id}")
        if skill_id in visited:
            return
        visiting.add(skill_id)
        for dep in graph[skill_id]:
            visit(dep)
        visiting.remove(skill_id)
        visited.add(skill_id)
    for skill_id in ids:
        visit(skill_id)


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
    canonical Knowledge becomes references, but assets are only included when
    explicitly declared by the Skill. Only declared runtime tool scripts become scripts.
    """
    knowledge_root = root / cfg.get("knowledge_architecture", {}).get("canonical_root", "knowledge")

    fallback = {
        "references": _project_relative_files(root, knowledge_root, exclude_names={"KNOWLEDGE.md"}),
        "assets": [],
        "scripts": _declared_runtime_script_refs(cfg),
    }

    # New modular projects can opt into explicit resource ownership.
    # The default retains legacy project-wide inheritance for existing projects.
    explicit = (cfg.get("skills") or {}).get("resource_policy") == "explicit"
    resolved: dict[str, list[str]] = {}
    for key in ("references", "assets", "scripts"):
        declared = skill.get(key)
        if explicit and not isinstance(declared, list):
            raise ValueError(
                f"Skill {skill.get('id', '<unknown>')} must declare {key} "
                "(use [] when no resources are needed)"
            )
        values = list(declared) if isinstance(declared, list) else list(fallback[key])
        unique = sorted(dict.fromkeys(str(value) for value in values))
        for ref in unique:
            src = (root / ref).resolve()
            if not src.is_relative_to(root.resolve()) or not src.exists() or (root / ref).is_symlink() or not (src.is_file() or (key == "assets" and src.is_dir())):
                raise SystemExit(f"Plugin skill {skill.get('id', '<unknown>')} {key[:-1]} missing/unsafe: {ref}")
        resolved[key] = unique
    return resolved


def plugin_script_runtime_requirements(cfg: dict, scripts: list[str] | None = None) -> dict:
    """Derive requirements from scripts actually packaged in a Skill.

    A None selection retains the legacy project-wide behavior. An explicit
    empty selection requires no code execution. This does not alter the
    project-wide runtime contract or the Work engine's special handoff.
    """
    selected = None if scripts is None else set(scripts)
    tools = [
        tool for tool in normalize_tool_contract(cfg).get("tools", [])
        if tool.get("type") == "script" and tool.get("script")
        and (selected is None or tool["script"] in selected)
    ]
    if not tools:
        return {
            "code_execution": {"level": "not_required", "languages": [], "fallback": "not_applicable"}
        }

    required = any(tool.get("requirement") == "required" for tool in tools)
    blocking = any(
        tool.get("requirement") == "required" and tool.get("runtime_fallback") == "block"
        for tool in tools
    )
    languages = sorted({
        "python" if str(tool.get("script", "")).endswith(".py") else "other"
        for tool in tools
    })
    return {
        "code_execution": {
            "level": "required" if required else "recommended",
            "languages": languages,
            "fallback": "block" if blocking else "degrade",
        }
    }


def compile_skill_markdown(
    skill: dict,
    *,
    compatibility: str | None = None,
    canonical_instruction: str | None = None,
    include_canonical_behavior: bool = False,
    runtime_requirements: dict | None = None,
) -> str:
    """Compile one canonical skill definition into deterministic SKILL.md text."""
    # Agent Skills frontmatter name is the directory/technical identifier,
    # not the human-readable display name.
    import re
    skill_id = skill["id"]
    if not isinstance(skill_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill_id) or len(skill_id) > 64:
        raise ValueError(f"Invalid Agent Skill ID: {skill_id!r}")
    frontmatter = [
        "---",
        f"name: {skill_id}",
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

    dependencies = list(skill.get("requires_skills", []) or [])
    if dependencies:
        body.extend([
            "## Skill dependencies",
            "",
            "When this workflow needs a capability owned by another Skill, "
            "activate or consult that Skill using its own installed resources. "
            "Do not assume its files exist relative to this Skill. "
            "If the host cannot activate another Skill, use the complete "
            "canonical instruction where available, or report the blocked "
            "operation without simulating it.",
            "",
        ])
        for dependency in dependencies:
            body.append(f"- `{dependency}`")
        body.append("")

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
        requirements = runtime_requirements or {}
        code_execution = requirements.get("code_execution") or {}
        level = code_execution.get("level", "recommended")
        languages = ", ".join(code_execution.get("languages") or []) or "compatible"
        fallback = code_execution.get("fallback", "degrade")
        body.extend([
            "## Runtime requirements",
            "",
            f"- Code execution: {level}.",
            f"- Required script runtime/language: {languages}.",
            "- When compatible code execution is available, run the packaged script resources rather than simulating their deterministic result.",
            f"- If compatible code execution is unavailable, apply fallback: {fallback}.",
            "",
            "## Scripts",
            "",
        ])
        for script in scripts:
            body.append(
                f"- Use `scripts/{Path(script).name}` as a script resource when the host provides "
                "compatible code execution. An MCP wrapper is not required merely to package or use "
                "the script resource."
            )
        body.append("")

    return "\n".join(body).rstrip() + "\n"


def build_opencode_skills(root: Path, cfg: dict, out: Path) -> list[str]:
    """Project canonical modular skills into OpenCode, unless explicitly disabled.

    The modern canonical skills contract is the source of truth. Legacy
    nonmodular projects retain the opt-in OpenCode skill behavior.
    """
    runtime_cfg = cfg["runtime"]["opencode"]
    skills_cfg = runtime_cfg.get("skills") or {}
    if not skills_cfg.get("enabled", is_modular(cfg)):
        return []

    skill_root = out / skills_cfg.get("directory", ".opencode/skills")
    validate_skill_dependencies(canonical_skill_definitions(cfg))
    built: list[str] = []

    for skill in canonical_skill_definitions(cfg):
        skill_id = skill["id"]
        skill_dir = skill_root / skill_id
        resources = resolve_plugin_skill_resources(root, cfg, skill)
        _copy_skill_resources(root, skill_dir, resources)

        body = compile_skill_markdown(
            dict(skill, **resources),
            compatibility="opencode",
            canonical_instruction=skill_instruction(root, cfg, canonical_skill_definitions(cfg), skill, runtime="opencode"),
            include_canonical_behavior=is_modular(cfg),
            runtime_requirements=plugin_script_runtime_requirements(cfg, resources["scripts"]),
        )
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
        built.append(skill_id)

    return built


def claude_skills_runtime_contract(cfg: dict, built_skills: list[str] | None = None) -> dict:
    """Claude Skills contract: portable resources, host-dependent execution."""
    snapshot = plugin_runtime_contract(cfg, built_skills)
    snapshot["runtime_id"] = "claude_skills"
    adapter = snapshot["adapter"]
    adapter["mode"] = "claude_skills"
    adapter["parity_notes"] = dict(adapter["parity_notes"])
    adapter["parity_notes"]["artifact"] = "Claude Skills package is generated as a portable runtime distribution."
    adapter["parity_notes"]["workspace_state"] = "Persistent workspace/state depends on the Claude host runtime and is not created by portable Skills."
    adapter["parity_notes"]["tool"] = "Canonical scripts are packaged as Claude Skill resources and require compatible host code execution."
    adapter["parity_notes"]["capability"] = "External execution capabilities depend on the Claude host runtime."
    return snapshot


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
            "runtime_requirements": plugin_script_runtime_requirements(cfg),
            "script_resources": {
                "packaged": _declared_runtime_script_refs(cfg),
                "execution": "host_code_execution_when_available",
                "mcp_required_for_resource_use": False,
                "mcp_role": "Use MCP when a guaranteed explicit tool interface is required.",
            },
            "parity_notes": {
                "behavior": "Canonical behavior is projected through skills.",
                "artifact": "Plugin package is generated as a runtime distribution.",
                "workspace_state": "Persistent workspace/state depends on the host runtime and is not created by Plugin v1.",
                "tool": "Canonical scripts are packaged as skill resources and may run directly when the host provides compatible code execution. Plugin v1 does not generate a guaranteed MCP tool interface.",
                "capability": "External tool execution and advanced integrations depend on the host runtime in Plugin v1.",
            },
        },
    }


def _copy_skill_resources(root: Path, skill_dir: Path, resources: dict[str, list[str]]) -> None:
    """Copy resolved skill resources, including shared runtime script dependencies."""
    for key in ("references", "assets", "scripts"):
        seen_names: set[str] = set()
        for ref in resources.get(key, []):
            src = root / ref
            name = src.name
            if name in seen_names:
                raise SystemExit(f"Plugin skill resource collision in {key}: {name}")
            seen_names.add(name)
            if key == "assets" and src.is_dir():
                copy_tree_filtered(src, skill_dir / key / name)
            else:
                copy_file(src, skill_dir / key / name)

    # Only copy shared helpers explicitly imported by packaged scripts.
    # Avoid shipping the whole GPT Builder implementation with unrelated Skills.
    if resources.get("scripts"):
        import ast
        shared_lib = root / "scripts" / "lib"
        required = set()
        pending = [root / ref for ref in resources["scripts"]]
        while pending:
            source = pending.pop()
            if not source.is_file() or source.suffix != ".py":
                continue
            try:
                tree = ast.parse(source.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                module = node.module if isinstance(node, ast.ImportFrom) else None
                if module and (module == "lib" or module.startswith("lib.")):
                    names = [a.name for a in node.names] if module == "lib" else [module.split(".")[1]]
                    for name in names:
                        helper = shared_lib / (name + ".py")
                        if helper.is_file() and helper not in required:
                            required.add(helper)
                            pending.append(helper)
        if root.name == "gpt-byggaren":
            copy_tree_filtered(shared_lib, skill_dir / "scripts" / "lib")
            return
        if required:
            init = shared_lib / "__init__.py"
            if init.is_file():
                copy_file(init, skill_dir / "scripts" / "lib" / "__init__.py")
            for helper in sorted(required):
                copy_file(helper, skill_dir / "scripts" / "lib" / helper.name)


def build_plugin(root: Path, cfg: dict, build_root: Path, version: str) -> Path:
    """Build a portable skills-first OpenAI Plugin v1 distribution."""
    out = build_root / "plugin"
    ensure_clean_dir(out)
    write_plugin_manifest(out, cfg, version)

    canonical_instruction = projected_instruction(root, cfg, canonical_skill_definitions(cfg))
    validate_skill_dependencies(canonical_skill_definitions(cfg))
    built_skills: list[str] = []
    for skill in canonical_skill_definitions(cfg):
        skill_id = skill["id"]
        skill_dir = out / "skills" / skill_id
        resources = resolve_plugin_skill_resources(root, cfg, skill)
        _copy_skill_resources(root, skill_dir, resources)

        compiled_skill = dict(skill)
        compiled_skill.update(resources)
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_markdown = compile_skill_markdown(
            compiled_skill,
            canonical_instruction=skill_instruction(root, cfg, canonical_skill_definitions(cfg), skill),
            include_canonical_behavior=True,
            runtime_requirements=plugin_script_runtime_requirements(cfg, resources["scripts"]),
        )
        # Keep release identity readable through the installed Skill itself.
        # Top-level plugin.json and VERSION may not be exposed by the host.
        skill_markdown = skill_markdown.replace(
            "  source: generated-from-canonical-project\n",
            "  source: generated-from-canonical-project\n"
            + f"  plugin_id: {cfg['project']['id']}\n"
            + f"  plugin_version: {version}\n",
            1,
        )
        if cfg.get("project", {}).get("id") == "gpt-byggaren" and skill_id == "distribution-and-parity":
            skill_markdown += (
                "\\n## Mandatory engine access self-test\\n\\n"
                "Before building a generated GPT, run "
                "`scripts/selftest_distribution_engine.py --source <materialized-engine-root>` "
                "in a compatible Python workspace. The self-test checks source files, "
                "materialization, SHA-256 integrity, the original installer and a "
                "six-archive smoke build. Report the first failed stage and its "
                "error verbatim. If no writable workspace or Python execution "
                "is available, report materialize/installer as unavailable; "
                "never claim self-test success or invent an alternative packager.\\n"
            )
        if cfg.get("project", {}).get("id") == "gpt-byggaren":
            is_ci_version = version == "0.0.0-ci" or version.endswith("-ci")
            release_link = (
                "https://github.com/erland/gpt-byggaren/releases/download/"
                f"v{version}/gpt-byggaren-engine-{version}.zip"
            )
            delivery_instruction = (
                "This is a CI/test Plugin version. Do not reference GitHub Actions, "
                "CI artifacts or pretend a Release asset exists. If an actual downloadable "
                "file cannot be exported, simply ask the user to attach "
                f"`gpt-byggaren-engine-{version}.zip` and continue in source-only fallback."
                if is_ci_version else
                "For a released Plugin, present this exact-version direct download "
                "link to the Engine ZIP in the corresponding GitHub Release: "
                + release_link
                + " . Tell the user to open this link, download the Engine ZIP, attach the ZIP in this conversation, and then say Gör nästa steg. Do not use latest or a different release version."
            )
            skill_markdown += (
                "\n## Plugin engine preflight and handoff\n\n"
                "At the first actual GPT project creation or resumption, first " 
                "try the original packaged engine in `scripts/distribution-engine/`. "
                "Only if direct execution is unavailable, run a "
                "one-time, non-blocking engine access preflight. Do not check on "
                "unrelated questions or repeatedly on every turn. Test whether "
                f"a user-attached `gpt-byggaren-engine-{version}.zip` is a real readable "
                "file in the Python workspace. "
                "If missing, explain the actual download-and-attach steps in the conversation language, not merely the Engine name. "
                "If accessible, run the unchanged canonical integrity checks and "
                "self-test and reuse the engine in the current workspace. "
                "The fallback Engine ZIP is distributed separately through the matching "
                "release, not embedded in this Plugin. Never invent a sandbox "
                "download or claim an inaccessible file was exported. "
                + delivery_instruction
                + " If the user does not attach the file, continue with explicitly "
                  "unverified declarative source-only fallback. Never use a "
                  "GitHub Python downloader, alternative packager or MCP.\n"
            )
            if skill_id == "distribution-and-parity":
                # Reuse canonical packaging to expose original scripts as Work files.
                bundle_distribution_engine(root, skill_dir / "scripts")
                copy_file(root / "scripts" / "selftest_distribution_engine.py",
                          skill_dir / "scripts" / "selftest_distribution_engine.py")
                skill_markdown += (
                    "\n## Direct installed engine execution (preferred)\n\n"
                    "If the installed Skill scripts are exposed as real files, run the original "
                    "`scripts/distribution-engine/scripts/detect_plugin_engine_runtime.py` "
                    "as a file with `--engine-root` set to the observed installed "
                    "Skill's `scripts/distribution-engine/` and optionally "
                    "`--fallback-zip` pointing at an actual attached ZIP. "
                    "If the detector itself is inaccessible, do NOT copy or simulate it: "
                    "use the existing attached Engine ZIP preflight directly. "
                    "Read the JSON mode when the detector actually runs: direct, "
                    "zip_fallback, or blocked. A zip_fallback result only proves "
                    "file presence: validate archive identity, version, hashes, "
                    "safe paths and original self-test before declaring success. "
                    "Direct means files are present, NOT that self-test passed. "
                    "Do not silently fall back when a real self-test fails. "
                    "Then check whether "
                    "`scripts/distribution-engine/scripts/selftest_distribution_engine.py` "
                    "is a real file relative to the installed Skill. The engine root "
                    "is `scripts/distribution-engine/`. Execute the original "
                    "self-test with `--source` set to that engine root, and record "
                    "actual stdout, stderr and exit code. Run the original canonical "
                    "installer and builders only after a PASS, with a separate "
                    "writable project workspace outside the plugin cache. "
                    "Never simulate execution or reconstruct scripts. Only fall "
                    "back to the separately released Engine ZIP if direct file "
                    "access or execution is unavailable; report actual test errors.\n"
                )
        # Generic Engine handoff for generated GPT projects; no embedded scripts.
        if cfg.get("project", {}).get("id") != "gpt-byggaren":
            from lib.engine_package import engine_config, engine_filename
            if engine_config(cfg):
                engine_name = engine_filename(cfg, version)
                is_test = version.endswith("-ci") or version.startswith("0.0.0-")
                engine_cfg = cfg["engine"]
                release_repo = engine_cfg.get("release_repository")
                link = (
                    f"https://github.com/{release_repo}/releases/download/v{version}/{engine_name}"
                    if isinstance(release_repo, str) and "/" in release_repo and not is_test
                    else None
                )
                handoff = (
                    f"Direct Engine ZIP download for this exact release: {link}. "
                    if link else
                    "No verified release download link is configured for this build. "
                )
                skill_markdown += (
                    "\n## Executable Engine ZIP preflight\n\n"
                    "For tasks requiring execution, first determine whether the "
                    "bundled Skill script resources and their declared dependencies "
                    "are directly executable in the current host. If they are, "
                    "run those resources directly without asking for an Engine ZIP. "
                    "Only if direct execution is unavailable or the bundled "
                    "resources are insufficient, check once for a real user-attached "
                    f"`{engine_name}` in the Python workspace. "
                    "The Plugin does not embed the executable engine. "
                    + handoff +
                    "If fallback is needed and the Engine ZIP is missing, ask once "
                    "for that exact file; permit non-executable work without falsely "
                    "claiming a completed build. "
                    "Before execution, verify engine-package.json, expected engine_id "
                    f"({cfg['project']['id']}), version ({version}), file hashes, "
                    "and safe relative paths; execute only the declared selftest "
                    f"({engine_cfg['selftest']}) in a compatible workspace. "
                    "Never invent an archive, link, test result or replacement engine.\n"
                )
        (skill_dir / "SKILL.md").write_text(skill_markdown, encoding="utf-8")
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
    """Generate a workspace-aware OpenCode adapter using each script's real CLI."""
    tool_id = tool["id"]
    description = tool.get("purpose", tool_id).replace('"', '\\"')
    arg_schema = 'projectRoot: tool.schema.string().optional().describe("Target project directory")'
    if tool_id == "project-hygiene":
        arg_schema += ',\n    mode: tool.schema.enum(["checkpoint", "final"]).optional(),\n    fix: tool.schema.boolean().optional()'
        command_lines = """
    const mode = args.mode ?? "checkpoint"
    const fix = args.fix ? ["--fix"] : []
    const cmd = ["python3", script, "--project-root", projectRoot, "--mode", mode, ...fix, "--json"]"""
    elif tool_id == "build-distributions":
        arg_schema += ',\n    version: tool.schema.string().optional(),\n    targets: tool.schema.string().optional()'
        command_lines = """
    const version = args.version ?? "0.0.0-dev"
    const targets = args.targets ?? "project,chat,custom-gpt,claude_project,claude_skills,opencode,plugin"
    const cmd = ["python3", script, "--project-root", projectRoot, "--version", version, "--targets", targets]"""
    elif tool_id == "distribution-build":
        arg_schema += ',\n    version: tool.schema.string().optional()'
        command_lines = """
    const cmd = ["python3", script, "--version", args.version ?? "0.0.0-dev"]"""
    elif tool_id in ("book-export", "book-build"):
        arg_schema += ',\n    outputDir: tool.schema.string().optional(),\n    format: tool.schema.enum(["epub", "pdf", "all"]).optional()'
        if tool_id == "book-export":
            command_lines = """
    const cmd = ["python3", script, "--format", args.format ?? "all", "--output-dir", path.resolve(projectRoot, args.outputDir ?? "exports")]"""
        else:
            command_lines = """
    const cmd = ["python3", script, "--output-dir", path.resolve(projectRoot, args.outputDir ?? "exports")]"""
    elif tool_id in ("presentation_plan_validate", "pptx_validate"):
        arg_schema += ',\n    file: tool.schema.string().min(1).describe("Path to presentation-plan.md or PPTX file, relative to the target project")'
        command_lines = """
    const file = path.resolve(projectRoot, args.file)
    const relative = path.relative(projectRoot, file)
    if (relative === ".." || relative.startsWith(".." + path.sep) || path.isAbsolute(relative)) {
      throw new Error("File must be within projectRoot")
    }
    const cmd = ["python3", script, file]"""
    elif tool_id in ("project-integrity",):
        arg_schema += ',\n    operation: tool.schema.enum(["verify", "status"]).optional()'
        command_lines = """
    const cmd = ["python3", script, args.operation ?? "verify", projectRoot]"""
    elif tool_id in ("project-validation",):
        command_lines = """
    const cmd = ["python3", script, projectRoot]"""
    elif tool_id in ("distribution-validation",):
        command_lines = """
    const cmd = ["python3", script]"""
    elif tool_id == "recommend-next-step":
        command_lines = """
    const cmd = ["python3", script, "--project-root", projectRoot, "--json"]"""
    else:
        # Unrecognized tools must not receive invented CLI flags.
        command_lines = """
    const cmd = ["python3", script]"""

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
    const proc = Bun.spawn(cmd, {{ cwd: projectRoot, stdout: "pipe", stderr: "pipe" }})
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

    canonical_instruction = projected_instruction(root, cfg, canonical_skill_definitions(cfg))
    agents_path = out / runtime_cfg["layout"]["instructions"]
    agents_path.write_text(
        canonical_instruction.rstrip()
        + "\n\n## OpenCode adapter\n\n"
        + "- Treat this AGENTS.md as a generated projection of the canonical assistant instructions.\n"
        + "- Work inside this repository/workspace.\n"
        + "- Reusable workflows may be available as project-local skills under .opencode/skills/.\n"
        + "- Load a skill when its description matches the current task instead of duplicating that workflow here.\n"
        + "- Use only the explicitly generated OpenCode custom tools for canonical runtime scripts; do not infer extra scripts as tools.\n"
        + "- The OpenCode workspace runs the installed assistant, and its project files may live in a subdirectory. Pass projectRoot when operating on a separate project directory.\n",
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
    "claude_skills": build_claude_skills,
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
    if filename == f"{project_id}-project-{version}.zip":
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
    if isinstance(cfg.get("reconstruction"), dict) and (
        cfg["reconstruction"].get("release_ready") is not True
        or cfg["reconstruction"].get("status") != "runtime_parity_verified"
    ):
        raise SystemExit(
            "Reconstructed project is not release-ready: complete and verify "
            "runtime parity before distribution build or validation"
        )
    from lib.project_resource_audit import validate_project_resources
    missing_resources = validate_project_resources(root, cfg)
    if missing_resources:
        raise SystemExit("Incomplete declared GPT project resources:\n" + "\n".join(missing_resources))
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

    # A newly generated project must not ship five identical generic archives.
    # Compare paths inside the ZIPs, not filenames or ZIP metadata.
    runtime_archives = []
    for target in selected_targets:
        if target == "project":
            continue
        target_cfg = runtime_targets.get(target, {})
        runtime_cfg = cfg.get("runtime", {}).get(target_cfg.get("runtime_key"), {})
        if not runtime_cfg.get("enabled"):
            continue
        name = (target_cfg["filename_pattern"]
                .replace("<project-id>", project_id)
                .replace("<version>", version))
        archive = dist / name
        if archive.exists():
            runtime_archives.append((target, archive))
    if len(runtime_archives) >= 2:
        from zipfile import ZipFile
        layouts = {}
        for target, archive in runtime_archives:
            with ZipFile(archive) as zf:
                layouts[target] = frozenset(zf.namelist())
        if len(set(layouts.values())) == 1:
            raise SystemExit(
                "All enabled runtime distributions have identical file layouts; "
                "use platform-specific builders instead of generic ZIP packaging"
            )

    if "project" in targets:
        project_zip = dist / f"{project_id}-project-{version}.zip"
        stable_write_zip(project_zip, root, project_files(root))

    from lib.engine_package import package_engine
    if "plugin" in targets and cfg.get("runtime", {}).get("plugin", {}).get("enabled"):
        package_engine(root, cfg, version, dist)

    write_checksums(dist)
    write_delivery_manifest(dist, cfg, version)

    print(f"Build complete: {dist}")
    for p in sorted(dist.iterdir()):
        if p.is_file():
            print(p.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
