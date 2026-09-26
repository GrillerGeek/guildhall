"""Setup skill packaging and offline workflows, without personal configuration."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_routing import ROOT, request
sys.path.insert(0, str(ROOT / 'scripts'))

SETUP = Path('plugin/skills/guildhall-routing-setup')


class RoutingSetupTests(unittest.TestCase):
    def test_standalone_setup_needs_no_quest_or_source_tree(self):
        with tempfile.TemporaryDirectory(prefix='guildhall wizard ') as tmp:
            root = Path(tmp).resolve()
            installed = root / 'installed'
            shutil.copytree(ROOT / SETUP, installed)
            for file in installed.rglob('*.md'):
                for target in re.findall(r'\]\(([^)]+)\)', file.read_text()):
                    if '://' in target or target.startswith('#'):
                        continue
                    path = (file.parent / target.split('#')[0]).resolve()
                    self.assertTrue(path.is_relative_to(installed) and path.is_file(), target)
            project = root / 'project'
            project.mkdir()
            env = {'PATH': '/usr/bin:/bin', 'XDG_CONFIG_HOME': str(root / 'settings')}
            helper = installed / 'scripts/routing_config.py'
            host = request()['host']
            def invoke(operation, **fields):
                packet = dict(operation=operation, project_root=str(project),
                              host_route='codex-skill', **fields)
                result = subprocess.run([sys.executable, '-I', '-B', str(helper)],
                    cwd=project, env=env, input=json.dumps(packet), text=True,
                    capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return json.loads(result.stdout)
            self.assertEqual(invoke('resolve')['reason'], 'no_policy')
            off = request('off')['policy']
            proposal = invoke('preview', policy=off, target='global')
            self.assertFalse((root / 'settings').exists(), 'Review/cancellation must not write')
            invoke('prepare', policy=off, target='global', expected_revision=proposal['expected_revision'])
            self.assertEqual(invoke('status', host=host)['reason'], 'router_disabled')
            self.assertFalse((root / 'settings/guildhall/routing-approvals.json').exists())
            shadow = request('shadow')['policy']
            proposal = invoke('preview', policy=shadow, target='global')
            invoke('prepare', policy=shadow, target='global', expected_revision=proposal['expected_revision'])
            status = invoke('status', host=host)
            self.assertEqual(status['reason'], 'activation_required')
            activated = invoke('activate', host=host, expected_policy_hash=status['policy_hash'],
                expected_host_fingerprint=status['host_fingerprint'], expected_source_key=status['source_key'],
                expected_revision=status['approval_revision'], confirm_scope=status['scope'],
                evidence_hashes=[host['evidence_hash']])
            self.assertEqual(activated['reason'], 'ready')
            invoke('revoke', source_key=activated['source_key'], expected_revision=activated['approval_revision'])
            self.assertEqual(invoke('status', host=host)['reason'], 'activation_required')
            opt_out = json.loads((installed / 'resources/examples/routing-opt-out.json').read_text())
            proposal = invoke('preview', policy=opt_out, target='project')
            invoke('prepare', policy=opt_out, target='project', expected_revision=proposal['expected_revision'])
            self.assertEqual(invoke('resolve')['reason'], 'router_disabled')
            self.assertFalse(list(installed.rglob('__pycache__')))

    def test_setup_bundle_shares_canonical_routing_resources(self):
        bundle = ROOT / SETUP
        self.assertTrue((bundle / 'SKILL.md').is_file())
        for directory in ('scripts', 'resources'):
            expected = {p.relative_to(ROOT / 'plugin/portable'): p.read_bytes()
                        for p in (ROOT / 'plugin/portable' / directory).rglob('*') if p.is_file()}
            self.assertTrue(expected)
            for relative, data in expected.items():
                self.assertEqual((bundle / relative).read_bytes(), data)
        self.assertFalse((bundle / 'references/roles').exists())

    def test_setup_output_is_checked_before_any_bundle_write(self):
        from build_portable import build, DEST
        with tempfile.TemporaryDirectory(prefix='guildhall setup build ') as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / 'plugin', root / 'plugin')
            shutil.copy2(ROOT / 'LICENSE', root / 'LICENSE')
            personal = root / SETUP / 'personal-notes.md'
            personal.write_text('retain this')
            source = root / 'plugin/portable/SKILL.md'
            source.write_text(source.read_text() + '\nChanged.\n')
            original = (root / DEST / 'SKILL.md').read_bytes()
            with self.assertRaisesRegex(ValueError, 'unknown output'):
                build(root)
            self.assertEqual((root / DEST / 'SKILL.md').read_bytes(), original)
            self.assertEqual(personal.read_text(), 'retain this')


if __name__ == '__main__':
    unittest.main()
