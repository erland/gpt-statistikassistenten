"""Regression tests for the offline Engine-to-Plugin package contract."""
import tempfile
from pathlib import Path
import unittest
import zipfile
from scripts.verify_plugin_engine_handoff import verify


class HandoffContractTests(unittest.TestCase):
    def test_reject_modified_engine_resource(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            engine = root / 'engine.zip'
            plugin = root / 'plugin.zip'
            content = b'print(1)'
            import hashlib, json
            manifest = {'engine_id': 'statistikassistenten', 'entrypoint': 'scripts/engine_selftest.py',
                        'python_dependencies': ['PyYAML>=6.0'],
                        'files': {'scripts/calculation_engine.py': hashlib.sha256(content).hexdigest()}}
            with zipfile.ZipFile(engine, 'w') as archive:
                archive.writestr('engine-package.json', json.dumps(manifest))
                archive.writestr('scripts/calculation_engine.py', b'print(2)')
            with zipfile.ZipFile(plugin, 'w') as archive:
                archive.writestr('skills/statistikassistenten/scripts/calculation_engine.py', content)
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                verify(plugin, engine, run_selftest=False)


if __name__ == '__main__':
    unittest.main()
