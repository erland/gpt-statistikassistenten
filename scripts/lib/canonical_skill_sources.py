"""Opt-in canonical core + Skill sources with legacy monolithic fallback."""
from pathlib import Path


def _read(root: Path, relative: str) -> str:
    p = Path(relative)
    if p.is_absolute() or ".." in p.parts or not (root / p).resolve().is_relative_to(root.resolve()) or not (root / p).is_file():
        raise ValueError(f"Unsafe or missing canonical source: {relative}")
    result = (root / p).read_text(encoding="utf-8").strip()
    if not result:
        raise ValueError(f"Empty canonical source: {relative}")
    return result


def is_modular(cfg: dict) -> bool:
    return (cfg.get("instructions") or {}).get("mode") == "modular_skills"


def modules(root: Path, cfg: dict, definitions: list[dict]) -> tuple[str, list[tuple[dict, str]]]:
    if not is_modular(cfg):
        return _read(root, cfg["instructions"]["canonical"]), []
    core = (cfg.get("instructions") or {}).get("core")
    if not isinstance(core, str):
        raise ValueError("modular_skills requires instructions.core")
    if not definitions:
        raise ValueError("modular_skills requires at least one canonical Skill")
    parts = []
    seen = set()
    source_paths = set()
    for skill in definitions:
        name = skill.get("id")
        source = skill.get("source")
        if not isinstance(name, str) or not name or name in seen:
            raise ValueError("Canonical Skill IDs must be unique and nonempty")
        if not isinstance(source, str):
            raise ValueError(f"Canonical Skill {name} requires source")
        resolved_source = (root / source).resolve()
        if resolved_source == (root / core).resolve() or resolved_source in source_paths:
            raise ValueError(f"Canonical Skill {name} duplicates a core/Skill source")
        seen.add(name)
        source_paths.add(resolved_source)
        parts.append((skill, _read(root, source)))
    return _read(root, core), parts




def assembled_instruction(root: Path, cfg: dict, definitions: list[dict]) -> str:
    """Reassemble interleaved canonical sections without changing legacy behavior."""
    import json
    import re

    relative = (cfg.get("instructions") or {}).get("assembly")
    if not isinstance(relative, str):
        raise ValueError("instructions.assembly is required for section assembly")
    p = Path(relative)
    manifest_path = (root / p).resolve()
    if p.is_absolute() or ".." in p.parts or not manifest_path.is_relative_to(root.resolve()):
        raise ValueError("Unsafe assembly manifest path")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources = {"core": cfg["instructions"]["core"]}
    sources.update({item["id"]: item["source"] for item in definitions})
    if sources != manifest.get("sources"):
        raise ValueError("Assembly sources disagree with canonical Skill definitions")
    section_re = re.compile(r"^## (.+)$", re.MULTILINE)
    sections = {}
    header = ""
    for owner, source in sources.items():
        p = Path(source)
        file_path = (root / p).resolve()
        if p.is_absolute() or ".." in p.parts or not file_path.is_relative_to(root.resolve()):
            raise ValueError("Unsafe canonical assembly source")
        raw = file_path.read_text(encoding="utf-8")
        hits = list(section_re.finditer(raw))
        if owner == "core":
            header = raw[:hits[0].start()] if hits else raw
        found = {}
        for i, m in enumerate(hits):
            title = m.group(1)
            if title in found:
                raise ValueError(f"Duplicate section heading: {owner}/{title}")
            found[title] = raw[m.start():hits[i + 1].start() if i + 1 < len(hits) else None]
        sections[owner] = found
    sequence = []
    seen = set()
    for entry in manifest.get("sections", []):
        key = (entry["owner"], entry["title"])
        if key in seen or key[0] not in sections or key[1] not in sections[key[0]]:
            raise ValueError(f"Duplicate or missing assembly section: {key}")
        sequence.append(sections[key[0]][key[1]])
        seen.add(key)
    available = {(o, title) for o, section in sections.items() for title in section}
    if available != seen:
        raise ValueError(f"Unmapped canonical sections: {available ^ seen}")
    return header + "".join(sequence)

def projected_instruction(root: Path, cfg: dict, definitions: list[dict]) -> str:
    core, parts = modules(root, cfg, definitions)
    if not is_modular(cfg):
        return (root / cfg["instructions"]["canonical"]).read_text(encoding="utf-8")
    if (cfg.get("instructions") or {}).get("assembly"):
        return assembled_instruction(root, cfg, definitions)
    return core + "\n\n" + "\n\n".join(
        f"## Skill: {item['id']}\n\n{body}" for item, body in parts
    ) + "\n"


def skill_instruction(root: Path, cfg: dict, definitions: list[dict], skill: dict, *, runtime: str = "standalone") -> str:
    core, parts = modules(root, cfg, definitions)
    if not is_modular(cfg):
        return core
    for item, body in parts:
        if item["id"] == skill["id"]:
            if runtime == "opencode":
                # AGENTS.md contains the canonical core in the same workspace.
                # Avoid repeating it in every discoverable OpenCode Skill.
                return body
            compact = (cfg.get("instructions") or {}).get("portable_skill_core")
            if compact is not None:
                if not isinstance(compact, str):
                    raise ValueError("instructions.portable_skill_core must name a source file")
                return _read(root, compact) + "\n\n" + body
            return core + "\n\n" + body
    raise ValueError(f"Unknown Skill: {skill['id']}")
