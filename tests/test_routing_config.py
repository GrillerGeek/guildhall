"""Global routing contract; temporary user state and synthetic host evidence only."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_routing import ROOT, NOW, request, provider, load_script

SCRIPT = ROOT / 'plugin/portable/scripts/routing_config.py'


def load_config(path=SCRIPT):
    spec = importlib.util.spec_from_file_location('config_under_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GlobalRoutingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='guildhall global ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.home = self.root / 'user'
        self.home.mkdir()
        self.project = self.root / 'project one'
        self.project.mkdir()
        self.other = self.root / 'project two'
        self.other.mkdir()
        self.module = load_config()
        self.req = request()
        self.config = self.client()

    def client(self, project=None, **kwargs):
        return self.module.RoutingConfig(project or self.project, 'codex-skill',
                                         home=self.home, environ={}, **kwargs)

    def write_policy(self, path, policy):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(policy))

    def prepare(self):
        return self.config.prepare(self.req['policy'], target='global', expected_revision=None)

    def approve(self, client=None, **kwargs):
        client = client or self.config
        status = client.status(self.req['host'], now=NOW)
        return client.activate(self.req['host'],
            expected_policy_hash=status['policy_hash'],
            expected_host_fingerprint=status['host_fingerprint'],
            expected_source_key=status['source_key'],
            expected_revision=status['approval_revision'],
            confirm_scope=status['scope'], evidence_hashes=['1'*64, '2'*64],
            expires_at=NOW+3600, now=NOW, **kwargs)

    def test_absent_global_inheritance_and_project_replacement(self):
        self.assertEqual(self.config.resolve()['reason'], 'no_policy')
        self.prepare()
        self.assertEqual(self.client(self.other).resolve()['policy'], self.req['policy'])
        local = request('off')['policy']
        self.write_policy(self.project / '.guildhall/routing.json', local)
        self.assertEqual(self.config.resolve()['policy'], local)
        self.assertEqual(self.config.resolve()['source'], 'project')
        self.assertFalse((self.other / '.guildhall').exists())

    def test_off_opt_out_and_session_off_override_invalid_lower_files(self):
        self.prepare()
        self.write_policy(self.project / '.guildhall/routing.json', self.module.OPT_OUT)
        self.config.global_path.write_text('broken')
        self.assertEqual(self.config.resolve()['reason'], 'router_disabled')
        self.write_policy(self.project / '.guildhall/routing.json', {'broken': True})
        with self.assertRaises(ValueError):
            self.config.resolve()
        self.assertEqual(self.client(session_off=True).resolve()['reason'], 'router_disabled')

    def test_invalid_selected_policy_never_falls_through(self):
        self.prepare()
        path = self.project / '.guildhall/routing.json'
        for raw in ('{', 'null', '[]', '{"mode":"off"}', '{"mode":"off","mode":"shadow"}'):
            path.parent.mkdir(exist_ok=True)
            path.write_text(raw)
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.config.resolve()
        path.unlink()
        path.symlink_to(self.root / 'missing')
        with self.assertRaises(ValueError):
            self.config.resolve()

    def test_approval_reused_across_projects_fresh_client_and_revoked(self):
        self.prepare()
        self.assertEqual(self.config.status(self.req['host'], now=NOW)['reason'], 'activation_required')
        self.approve()
        other = self.client(self.other)
        ready = other.status(self.req['host'], now=NOW)
        self.assertEqual(ready['reason'], 'ready')
        self.assertTrue(ready['activation']['external_requests'])
        self.config.revoke(ready['source_key'], expected_revision=ready['approval_revision'])
        self.assertFalse(other.status(self.req['host'], now=NOW)['activation']['external_requests'])

    def test_equal_project_bytes_do_not_inherit_global_consent(self):
        self.prepare()
        self.approve()
        self.write_policy(self.project / '.guildhall/routing.json', self.req['policy'])
        self.assertEqual(self.config.status(self.req['host'], now=NOW)['reason'], 'activation_required')
        self.approve()
        self.write_policy(self.other / '.guildhall/routing.json', self.req['policy'])
        self.assertEqual(self.client(self.other).status(self.req['host'], now=NOW)['reason'], 'activation_required')

    def test_hash_formatting_host_changes_expiry_and_evidence(self):
        self.prepare()
        self.approve()
        value = json.loads(self.config.global_path.read_text())
        self.config.global_path.write_text(json.dumps(value, indent=4, sort_keys=True))
        self.assertEqual(self.config.status(self.req['host'], now=NOW)['reason'], 'ready')
        host = copy.deepcopy(self.req['host'])
        host['configuration_revision'] = 'changed'
        self.assertEqual(self.config.status(host, now=NOW)['reason'], 'host_changed')
        host = copy.deepcopy(self.req['host'])
        host['evidence_hash'] = '3'*64
        self.assertEqual(self.config.status(host, now=NOW)['reason'], 'evidence_review_required')
        self.assertEqual(self.config.status(self.req['host'], now=NOW+3600)['reason'], 'approval_expired')
        value['hosts']['codex-skill']['max_calls'] = 1
        self.config.global_path.write_text(json.dumps(value))
        self.assertEqual(self.config.status(self.req['host'], now=NOW)['reason'], 'policy_changed')

    def test_summary_is_never_blanket_approved(self):
        self.req['policy']['data_mode'] = 'summary'
        self.prepare()
        self.approve()
        status = self.config.status(self.req['host'], now=NOW)
        self.assertEqual(status['reason'], 'summary_approval_required')
        self.assertIsNone(status['activation']['summary_preview_hash'])

    def test_other_host_entries_do_not_invalidate_approval(self):
        self.prepare()
        self.approve()
        claude = self.module.RoutingConfig(self.project, 'claude-native', home=self.home, environ={})
        self.assertEqual(claude.resolve()['reason'], 'no_host_policy')
        claude.prepare(request('off', 'claude-native')['policy'], target='global',
                       expected_revision=self.config.resolve()['config_revision'])
        self.assertEqual(self.config.status(self.req['host'], now=NOW)['reason'], 'ready')

    def test_xdg_absolute_only_and_explicit_path(self):
        for xdg, expected in [('relative', self.home / '.config'),
                              (str(self.root / 'xdg'), self.root / 'xdg')]:
            client = self.module.RoutingConfig(self.project, 'codex-skill', home=self.home,
                                                environ={'XDG_CONFIG_HOME': xdg})
            self.assertEqual(client.global_path, expected / 'guildhall/routing.json')
        self.prepare()
        path = self.root / 'selected.json'
        self.write_policy(path, request('off')['policy'])
        self.assertEqual(self.client(policy_path=path).resolve()['source'], 'explicit')

    def test_concurrent_updates_are_rejected_and_permissions_restricted(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'conflict'):
            self.config.prepare(self.req['policy'], target='global', expected_revision=None)
        self.approve()
        self.assertEqual(self.config.approvals_path.stat().st_mode & 0o777, 0o600)
        with self.assertRaisesRegex(ValueError, 'conflict'):
            self.config.revoke(self.config.resolve()['source_key'], expected_revision=None)
        self.assertEqual(self.config.status(self.req['host'], now=NOW)['reason'], 'ready')

    def test_unsafe_or_corrupt_approval_store_cannot_enable(self):
        self.prepare()
        self.approve()
        path = self.config.approvals_path
        path.write_text('{')
        with self.assertRaises(ValueError):
            self.config.status(self.req['host'], now=NOW)
        path.unlink()
        path.symlink_to(self.root / 'other-user-file')
        with self.assertRaises(ValueError):
            self.approve()
        self.assertFalse((self.root / 'other-user-file').exists())

    def test_activation_rejects_stale_preview_and_unreviewed_host(self):
        self.prepare()
        status = self.config.status(self.req['host'], now=NOW)
        for changes in ({'expected_policy_hash': '0'*64}, {'expected_source_key': '0'*64},
                        {'expected_host_fingerprint': '0'*64}, {'confirm_scope': 'project'},
                        {'evidence_hashes': []}, {'expires_at': NOW}):
            params = dict(expected_policy_hash=status['policy_hash'],
                expected_source_key=status['source_key'], expected_host_fingerprint=status['host_fingerprint'],
                expected_revision=None, confirm_scope='all-projects',
                evidence_hashes=['1'*64], expires_at=None, now=NOW)
            params.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.config.activate(self.req['host'], **params)

    def test_resolution_drives_router_without_resetting_quest_state(self):
        self.prepare()
        self.approve()
        router = load_script()
        calls = []
        def transport(*args):
            calls.append(args)
            self.assertNotIn(str(self.home), json.dumps(args))
            return provider()
        for project in (self.project, self.other):
            req = copy.deepcopy(self.req)
            status = self.client(project).status(req['host'], now=NOW)
            req['policy'], req['activation'] = status['policy'], status['activation']
            req['state']['calls_used'] = 3
            result = router.route(req, transport=transport, now=NOW)
            self.assertEqual(result['reason'], 'shadow')
            self.assertEqual(result['state']['calls_used'], 4)
        status = self.config.status(self.req['host'], now=NOW)
        self.config.revoke(status['source_key'], expected_revision=status['approval_revision'])
        req['activation'] = self.config.status(req['host'], now=NOW)['activation']
        self.assertEqual(router.route(req, transport=transport, now=NOW)['reason'], 'activation_required')
        self.assertEqual(len(calls), 2)

    def test_installed_cli_after_source_removal(self):
        source = self.root / 'source'
        installed = self.root / 'installed'
        shutil.copytree(ROOT / 'plugin/skills/guildhall-quest', source)
        shutil.copytree(source, installed)
        shutil.rmtree(source)
        self.prepare()
        self.approve()
        packet = dict(operation='status', project_root=str(self.other), host_route='codex-skill',
                      host=self.req['host'])
        # Expiry uses real time here, independently of the test clock.
        output = subprocess.run([sys.executable, '-I', '-B', str(installed / 'scripts/routing_config.py')],
            input=json.dumps(packet), text=True, capture_output=True, cwd=self.other,
            env={'HOME': str(self.home), 'PATH': '/usr/bin:/bin'}, timeout=10)
        self.assertEqual(output.returncode, 0, output.stderr + output.stdout)
        self.assertEqual(json.loads(output.stdout)['reason'], 'ready')
        self.assertFalse(list(installed.rglob('__pycache__')))

    def test_preview_migration_retains_project_and_creates_no_approval(self):
        self.write_policy(self.project / '.guildhall/routing.json', self.req['policy'])
        preview = self.config.preview(self.req['policy'], target='global')
        self.assertTrue(preview['project_override_retained'])
        self.assertEqual(preview['document']['hosts']['codex-skill'], self.req['policy'])
        self.assertFalse(self.config.global_path.exists())
        self.config.prepare(self.req['policy'], target='global', expected_revision=preview['expected_revision'])
        self.assertFalse(self.config.approvals_path.exists())
        self.assertEqual(self.config.resolve()['source'], 'project')
        (self.project / '.guildhall/routing.json').unlink()
        self.assertEqual(self.config.resolve()['source'], 'global')
        self.assertEqual(self.config.status(self.req['host'], now=NOW)['reason'], 'activation_required')

    def test_all_host_routes_and_policy_versions(self):
        for host_route in ('claude-native', 'claude-skill', 'codex-skill'):
            client = self.module.RoutingConfig(self.project, host_route, home=self.home, environ={})
            for version in (1, 2, 3, 4):
                req = request('shadow', host_route)
                req['policy']['schema_version'] = version
                if version >= 2:
                    for candidate in req['policy']['candidates']:
                        for metric in ('quality', 'latency_ms', 'cost_usd', 'usage_tokens'):
                            candidate[metric] = None
                        candidate['measurements'] = []
                if version >= 3:
                    req['policy']['required_evidence'] = 'execution_observed'
                    req['host']['evidence_level'] = 'execution_observed'
                proposal = client.preview(req['policy'], target='global')
                client.prepare(req['policy'], target='global', expected_revision=proposal['expected_revision'])
                status = client.status(req['host'], now=NOW)
                with self.subTest(route=host_route, version=version):
                    self.assertEqual(status['policy'], req['policy'])
                    self.assertEqual(status['reason'], 'activation_required')

    def test_all_specialist_roles_use_same_approved_policy(self):
        self.req['policy']['schema_version'] = 4
        self.req['schema_version'] = 4
        self.req['host']['evidence_level'] = 'execution_observed'
        self.req['policy']['required_evidence'] = 'execution_observed'
        router = load_script()
        for candidate in self.req['policy']['candidates']:
            candidate['roles'] = router.ROLES
            candidate['categories'] = ['review']
            candidate['measurements'] = []
            for metric in router.METRIC_NAMES:
                candidate[metric] = None
        self.prepare()
        self.approve()
        for role in router.ROLES:
            with self.subTest(role=role):
                req = copy.deepcopy(self.req)
                req['task'].update(role=role, category='review')
                req['activation'] = self.config.status(req['host'], now=NOW)['activation']
                result = router.route(req, transport=lambda *_: provider(), now=NOW)
                self.assertEqual(result['reason'], 'shadow')

    def test_invalid_semantics_and_other_host_mapping_rejected(self):
        self.prepare()
        value = json.loads(self.config.global_path.read_text())
        value['hosts']['made-up-host'] = self.req['policy']
        self.config.global_path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            self.config.resolve()
        bad = copy.deepcopy(self.req['policy'])
        bad['candidates'].append(copy.deepcopy(bad['candidates'][0]))
        with self.assertRaises(ValueError):
            self.config.preview(bad, target='project')

    def test_private_modes_symlinks_locks_and_unsupported_runtime(self):
        self.prepare()
        self.approve()
        self.config.approvals_path.chmod(0o644)
        with self.assertRaisesRegex(ValueError, 'unsafe_approval'):
            self.config.status(self.req['host'], now=NOW)
        self.config.approvals_path.chmod(0o600)
        lock = self.config.global_path.with_name('routing.json.lock')
        lock.write_text('synthetic interrupted writer')
        revision = self.config.resolve()['config_revision']
        with self.assertRaisesRegex(ValueError, 'configuration_busy'):
            self.config.prepare(self.req['policy'], target='global', expected_revision=revision)
        self.assertTrue(lock.exists())
        self.assertEqual(self.config.resolve()['config_revision'], revision)
        with patch.object(self.module.sys, 'version_info', (3, 11)):
            with self.assertRaisesRegex(ValueError, 'unsupported_runtime'):
                self.client()
        directory = self.config.approvals_path.parent
        moved = directory.with_name('moved-state')
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'unsafe_state_directory'):
            self.config.status(self.req['host'], now=NOW)

    def test_selected_unreadable_policy_and_unknown_host_do_not_inherit(self):
        self.prepare()
        with patch.object(self.module.os, 'open', side_effect=PermissionError('synthetic')):
            with self.assertRaisesRegex(ValueError, 'unreadable'):
                self.config.resolve()
        with self.assertRaisesRegex(ValueError, 'unsupported_host_route'):
            self.module.RoutingConfig(self.project, 'other', home=self.home, environ={})

    def test_unqualified_adaptive_retains_engine_fallback(self):
        self.req['policy']['mode'] = 'adaptive'
        self.prepare()
        self.approve()
        req = copy.deepcopy(self.req)
        req['activation'] = self.config.status(req['host'], now=NOW)['activation']
        result = load_script().route(req, transport=lambda *_: self.fail('unqualified call'), now=NOW)
        self.assertEqual(result['reason'], 'adaptive_unqualified')
        self.assertEqual(result['dispatch'], req['baseline'])

    def test_installed_setup_two_projects_opt_out_and_revocation(self):
        for native in (False, True):
            with self.subTest(native=native):
                case = self.root / ('native' if native else 'standalone')
                case.mkdir()
                if native:
                    shutil.copytree(ROOT / 'plugin', case / 'installed')
                    bundle = case / 'installed/skills/guildhall-quest'
                else:
                    shutil.copytree(ROOT / 'plugin/skills/guildhall-quest', case / 'installed')
                    bundle = case / 'installed'
                env = {'HOME': str(case / 'user'), 'PATH': '/usr/bin:/bin'}
                project_a, project_b = case / 'a', case / 'b'
                project_a.mkdir()
                project_b.mkdir()
                host_route = 'claude-native' if native else 'codex-skill'
                req = request('shadow', host_route)
                def invoke(operation, project=project_a, **fields):
                    packet = dict(operation=operation, project_root=str(project), host_route=host_route, **fields)
                    run = subprocess.run([sys.executable, '-I', '-B', str(bundle / 'scripts/routing_config.py')],
                        input=json.dumps(packet), text=True, capture_output=True, cwd=project, env=env, timeout=10)
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                    return json.loads(run.stdout)
                preview = invoke('preview', policy=req['policy'], target='global')
                invoke('prepare', policy=req['policy'], target='global', expected_revision=preview['expected_revision'])
                status = invoke('status', host=req['host'])
                invoke('activate', host=req['host'], expected_policy_hash=status['policy_hash'],
                    expected_host_fingerprint=status['host_fingerprint'], expected_source_key=status['source_key'],
                    expected_revision=status['approval_revision'], confirm_scope='all-projects',
                    evidence_hashes=['1'*64, '2'*64])
                for project in (project_a, project_b):
                    ready = invoke('status', project=project, host=req['host'])
                    self.assertEqual(ready['reason'], 'ready')
                    self.assertFalse((project / '.guildhall').exists())
                invoke('prepare', project=project_b, policy=self.module.OPT_OUT, target='project', expected_revision=None)
                disabled = invoke('status', project=project_b, host=req['host'])
                self.assertFalse(disabled['activation']['external_requests'])
                self.assertEqual(disabled['reason'], 'router_disabled')
                invoke('revoke', source_key=ready['source_key'], expected_revision=ready['approval_revision'])
                status = invoke('status', host=req['host'])
                self.assertEqual(status['reason'], 'activation_required')
                router = load_script(bundle / 'scripts/route_model.py')
                req['activation'] = status['activation']
                req['state']['calls_used'] = 6
                result = router.route(req, transport=lambda *_: self.fail('revoked external call'))
                self.assertEqual(result['reason'], 'activation_required')
                self.assertEqual(result['state']['calls_used'], 6)


if __name__ == '__main__':
    unittest.main()
