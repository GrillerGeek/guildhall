"""Copied routing helper works without source checkout or personal installations."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_routing import request

ROOT = Path(__file__).resolve().parent.parent
RELATIVE_HELPER = Path('scripts/route_model.py')
BUNDLE = ROOT / 'plugin/skills/guildhall-quest'
sys.dont_write_bytecode = True


class RoutingPackagingTests(unittest.TestCase):
    def exercise_copy(self, native):
        promised = BUNDLE / RELATIVE_HELPER
        if not promised.is_file():
            raise ModuleNotFoundError(f'Promised generated routing module absent: {promised}')
        with tempfile.TemporaryDirectory(prefix='guildhall routing copy ') as tmp:
            root = Path(tmp)
            source = root / 'source'
            source.mkdir()
            if native:
                shutil.copytree(ROOT / 'plugin', source / 'plugin')
                shutil.copytree(source / 'plugin', root / 'installed-native')
                helper = root / 'installed-native/skills/guildhall-quest' / RELATIVE_HELPER
            else:
                shutil.copytree(BUNDLE, source / 'bundle')
                shutil.copytree(source / 'bundle', root / 'installed-skill')
                helper = root / 'installed-skill' / RELATIVE_HELPER
            shutil.rmtree(source)
            self.assertFalse(source.exists())
            env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': ''}
            raw = json.dumps(request('off', 'claude-native' if native else 'codex-skill'))
            cli = subprocess.run([sys.executable, '-I', str(helper)], input=raw, text=True,
                capture_output=True, cwd=root, timeout=10, env=env)
            self.assertEqual(cli.returncode, 0, cli.stderr)
            self.assertEqual(json.loads(cli.stdout)['reason'], 'router_disabled')
            # Load just this script by filename, without adding its directory to sys.path.
            probe = ('import importlib.util,json,sys; sys.dont_write_bytecode=True; '
                     's=importlib.util.spec_from_file_location("copied_router",sys.argv[1]); '
                     'm=importlib.util.module_from_spec(s); s.loader.exec_module(m); '
                     'print(json.dumps(m.route(json.load(sys.stdin))))')
            api = subprocess.run([sys.executable, '-I', '-c', probe, str(helper)], input=raw,
                text=True, capture_output=True, cwd=root, timeout=10, env=env)
            self.assertEqual(api.returncode, 0, api.stderr)
            self.assertEqual(json.loads(api.stdout)['dispatch'], json.loads(raw)['baseline'])
            self.assertFalse(list(root.rglob('__pycache__')))

    def test_standalone_copied_bundle_after_source_removal(self):
        self.exercise_copy(native=False)

    def test_native_plugin_copy_after_source_removal(self):
        self.exercise_copy(native=True)


if __name__ == '__main__': unittest.main()
