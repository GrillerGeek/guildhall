"""Complete offline v5 setup and dispatch using independent installed bundles."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from test_routing import ROOT, NOW, activate, provider, load_script
from test_routing_dynamic import dynamic_request, refresh_controls
from test_routing_config import load_config


class DynamicSetupTests(unittest.TestCase):
    def test_each_bundle_and_host_enables_without_study(self):
        for bundle in ['guildhall-quest','guildhall-routing-setup']:
            for route in ['codex-skill','claude-native','claude-skill']:
                with self.subTest(bundle=bundle,route=route), tempfile.TemporaryDirectory() as tmp:
                    root=Path(tmp);installed=root/'installed'
                    shutil.copytree(ROOT/'plugin/skills'/bundle,installed)
                    project=root/'project';project.mkdir();home=root/'user';home.mkdir()
                    module=load_config(installed/'scripts/routing_config.py')
                    config=module.RoutingConfig(project,route,home=home,environ={})
                    req=dynamic_request(host=route)
                    # Preview/cancel does not create configuration or approval.
                    proposal=config.preview(req['policy'],target='global')
                    self.assertFalse(config.global_path.exists())
                    config.prepare(req['policy'],target='global',expected_revision=proposal['expected_revision'])
                    s=config.status(req['host'],now=NOW)
                    ready=config.activate(req['host'],expected_policy_hash=s['policy_hash'],expected_host_fingerprint=s['host_fingerprint'],expected_source_key=s['source_key'],expected_revision=s['approval_revision'],confirm_scope=s['scope'],evidence_hashes=[],now=NOW)
                    self.assertEqual(ready['reason'],'ready')
                    req['activation']=ready['activation']
                    engine=load_script(installed/'scripts/route_model.py')
                    self.assertEqual(engine.route(req,transport=lambda *a:provider(),now=NOW)['source'],'jev')
                    # Another project inherits without a policy file; opt-out masks it.
                    other=root/'other';other.mkdir()
                    inherited=module.RoutingConfig(other,route,home=home,environ={})
                    self.assertEqual(inherited.status(req['host'],now=NOW)['reason'],'ready')
                    inherited.prepare(module.OPT_OUT,target='project',expected_revision=None)
                    self.assertEqual(inherited.status(req['host'],now=NOW)['reason'],'router_disabled')
                    self.assertEqual(inherited.status(req['host'],target='global',now=NOW)['reason'],'ready')
                    config.revoke(s['source_key'],expected_revision=ready['approval_revision'])
                    self.assertEqual(config.status(req['host'],now=NOW)['reason'],'activation_required')

    def test_claude_defaults_allow_routing_but_explicit_locks_win(self):
        router=load_script();r=dynamic_request(host='claude-native')
        r['policy']['role_baselines']=[dict(role='docs-writer',candidate='base')]
        out=router.route(activate(r),transport=lambda *a:provider(),now=NOW)
        self.assertEqual(out['source'],'jev')
        r['policy']['role_locks']=[dict(role='docs-writer',candidate='base')]
        self.assertEqual(router.route(activate(r))['source'],'role_override')
        r['selection']['user_candidate']='fast'
        self.assertEqual(router.route(r)['dispatch']['model'],'synthetic-fast')

    def test_role_fallback_changes_do_not_change_control_identity(self):
        router=load_script();r=dynamic_request(host='claude-native')
        fingerprint=router.control_fingerprint(r['host'])
        r['host']['baseline_candidate']='fast'
        self.assertEqual(router.control_fingerprint(r['host']),fingerprint)
        r['policy']['role_baselines']=[dict(role='docs-writer',candidate='fast')]
        r['baseline']=dict(model='synthetic-fast',effort='high')
        self.assertEqual(router.route(activate(r),transport=lambda *a:provider(choice='defer'),now=NOW)['dispatch'],r['baseline'])

    def test_activation_rejects_unavailable_fallback_and_duplicate_locks(self):
        router=load_script();r=dynamic_request()
        r['host']['allowed_settings']=r['host']['allowed_settings'][1:];refresh_controls(r)
        self.assertEqual(router.activation_issues(r['policy'],r['host']),['unsupported_fallback_or_lock:docs-writer'])
        r=dynamic_request();r['policy']['role_locks']=[dict(role='docs-writer',candidate='base'),dict(role='docs-writer',candidate='fast')]
        with self.assertRaises(ValueError):router.validate_policy(r['policy'])

if __name__=='__main__':unittest.main()
