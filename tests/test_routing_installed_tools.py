"""Regression witnesses for issue #37: installed tools, runtime and payload privacy."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from test_routing import ROOT, activate, load_script, request


class InstalledToolTests(unittest.TestCase):
    def test_identifying_ids_are_not_sent_and_choice_maps_back(self):
        router = load_script()
        req = request()
        names = ['private_project_sonnet', 'private_project_haiku']
        for c, name in zip(req['policy']['candidates'], names):
            c['id'] = name
        req['policy']['allowed_candidates'] = names
        req['host']['baseline_candidate'] = names[0]
        activate(req)
        def transport(payload, timeout):
            raw = json.dumps(payload)
            self.assertNotIn('private_project', raw)
            self.assertNotIn('synthetic-fast', raw)
            ids = [x for x in payload['questions']['route']['criteria'] if x != 'defer']
            self.assertEqual(ids, ['p0', 'p1'])
            self.assertEqual([c['id'] for c in json.loads(payload['state'])['candidates']], ids)
            return dict(model='test', answers={'route': dict(type='choice', choice=ids[1],
                confidence=1, probabilities={ids[0]: 0, ids[1]: 1, 'defer': 0})})
        result = router.route(req, transport=transport)
        self.assertEqual(result['recommended_candidate'], names[1])
        self.assertEqual(result['dispatch'], req['baseline'])

    def test_unsupported_runtime_holds_and_preserves_trusted_state(self):
        router = load_script()
        req = request()
        req['state'] = dict(calls_used=5, provider_failed=True, adaptive_suspended=True)
        with patch.object(router.sys, 'version_info', (3, 9, 6)):
            result = router.route(req, transport=lambda *_: self.fail('must not call transport'))
        self.assertEqual((result['status'], result['reason']), ('hold', 'unsupported_runtime'))
        self.assertEqual(result['state'], req['state'])

    def test_unsupported_http_child_does_not_read_or_request(self):
        router = load_script()
        with patch.object(router.sys, 'version_info', (3, 9, 6)), patch.object(router.sys, 'stdin', None):
            self.assertEqual(router._http_child(), 2)

    def test_installed_evaluator_and_guide_after_source_removal(self):
        with tempfile.TemporaryDirectory() as tmp:
            installed = Path(tmp)/'installed'
            shutil.copytree(ROOT/'plugin/skills/guildhall-quest', installed)
            guide = installed/'references/model-routing.md'
            self.assertTrue(guide.is_file(), 'Full setup guide must ship in bundle')
            self.assertIn('Credentials and activation', guide.read_text())
            cli = subprocess.run([sys.executable, '-I', '-B', str(installed/'scripts/evaluate_routing.py'), '--demo'],
                cwd=tmp, capture_output=True, text=True, timeout=10)
            self.assertEqual(cli.returncode, 0, cli.stderr)
            self.assertFalse(json.loads(cli.stdout)['qualification'])


if __name__ == '__main__':
    unittest.main()
