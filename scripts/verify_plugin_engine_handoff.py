"""Offline contract check for the separately distributed Plugin and statistics Engine ZIPs."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

PREFIX = 'skills/statistikassistenten/'

def verify(plugin_path: Path, engine_path: Path, run_selftest: bool = True) -> dict:
    with zipfile.ZipFile(engine_path) as e, zipfile.ZipFile(plugin_path) as p:
        metadata = json.loads(e.read('engine-package.json'))
        if metadata.get('engine_id') != 'statistikassistenten':
            raise ValueError('Unexpected engine identity')
        if metadata.get('entrypoint') != 'scripts/engine_selftest.py':
            raise ValueError('Unexpected Engine selftest entrypoint')
        if not metadata.get('python_dependencies'):
            raise ValueError('Missing dependency declaration')
        names = set(e.namelist())
        files = metadata['files']
        if set(names) != set(files) | {'engine-package.json'}:
            raise ValueError('Engine archive has missing or undeclared content')
        for name, expected in files.items():
            if name.startswith('/') or '..' in Path(name).parts or '\\' in name:
                raise ValueError('Unsafe Engine path: ' + name)
            digest = hashlib.sha256(e.read(name)).hexdigest()
            if digest != expected:
                raise ValueError('Engine checksum mismatch: ' + name)
            plugin_name = PREFIX + ('references/' + name[len('knowledge/'):] if name.startswith('knowledge/') else name)
            if name == 'scripts/engine_selftest.py' or name == 'scripts/__init__.py':
                continue  # Only carried by the separately packaged Engine.
            if plugin_name not in p.namelist():
                raise ValueError('Missing Plugin resource: ' + plugin_name)
            if e.read(name) != p.read(plugin_name):
                raise ValueError('Plugin and Engine resource diverged: ' + name)
        if run_selftest:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                for name in files:
                    target = root / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(e.read(name))
                proc = subprocess.run([sys.executable, str(root / metadata['entrypoint'])], cwd=root,
                                      text=True, capture_output=True, timeout=30)
                if proc.returncode:
                    raise RuntimeError(f'Engine selftest failed ({proc.returncode}): {proc.stdout} {proc.stderr}')
    return {'status': 'PASS', 'checked_files': len(files), 'selftest': run_selftest,
            'scope': 'offline package integrity and local Python execution; NOT Plugin host runtime'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plugin', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.plugin, args.engine), ensure_ascii=False, indent=2))
