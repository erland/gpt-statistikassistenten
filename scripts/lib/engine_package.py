"""Generic, deterministic Engine ZIP packaging for GPT projects."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

EXCLUDED = {"__pycache__", ".pytest_cache", ".git", "build", "dist"}
DATE = (2020, 1, 1, 0, 0, 0)


def engine_config(cfg: dict) -> dict | None:
    value = cfg.get("engine")
    if not isinstance(value, dict) or not value.get("enabled", False):
        return None
    return value


def engine_filename(cfg: dict, version: str) -> str:
    return f"{cfg['project']['id']}-engine-{version}.zip"


def engine_paths(root: Path, cfg: dict) -> list[Path]:
    engine = engine_config(cfg)
    if engine is None:
        return []
    resources = engine.get("resources")
    entrypoint = engine.get("selftest")
    if not isinstance(resources, list) or not resources:
        raise ValueError("engine.resources must contain explicit file/directory paths")
    if not isinstance(entrypoint, str) or not entrypoint:
        raise ValueError("engine.selftest is required")
    paths: set[Path] = set()
    for item in [*resources, entrypoint]:
        if not isinstance(item, str) or not item:
            raise ValueError("Invalid engine resource path")
        rel = PurePosixPath(item)
        if rel.is_absolute() or ".." in rel.parts or "\\" in item:
            raise ValueError(f"Unsafe engine path: {item}")
        target = (root / item).resolve()
        if not target.is_relative_to(root.resolve()) or not target.exists():
            raise ValueError(f"Missing/escaping Engine path: {item}")
        candidates = target.rglob("*") if target.is_dir() else [target]
        for file in candidates:
            if file.is_file() and not (set(file.relative_to(root).parts) & EXCLUDED) and file.suffix not in {".pyc", ".pyo"}:
                paths.add(file)
    if not (root / entrypoint).is_file():
        raise ValueError("engine.selftest must point to a file")
    return sorted(paths, key=lambda p: p.relative_to(root).as_posix())


def package_engine(root: Path, cfg: dict, version: str, dist: Path) -> Path | None:
    engine = engine_config(cfg)
    if engine is None:
        return None
    files = engine_paths(root, cfg)
    output = dist / engine_filename(cfg, version)
    manifest = {
        "schema_version": 1,
        "engine_id": cfg["project"]["id"],
        "version": version,
        "entrypoint": engine["selftest"],
        "required_files": sorted({engine["selftest"], *engine.get("required_files", [])}),
        "python_dependencies": engine.get("python_dependencies", []),
        "files": {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
    }
    if not set(manifest["required_files"]) <= set(manifest["files"]):
        raise ValueError("engine.required_files must be included in engine.resources")
    dist.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in [*((p.relative_to(root).as_posix(), p.read_bytes()) for p in files),
                           ("engine-package.json", (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())]:
            info = zipfile.ZipInfo(name, DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)
    return output
