"""Local eligibility explanations without paid diagnostic or router calls."""
import copy
import unittest

from test_routing import activate, load_script, NOW, provider
from test_routing_dynamic import dynamic_request, refresh_controls


class EligibilityDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.router = load_script()

    def prepare(self, request):
        request['policy']['catalog_revision'] = self.router.catalog_revision(request['policy']['candidates'])
        return activate(refresh_controls(request))

    def test_unknown_capacity_explains_hold_without_spending_or_rewriting_task(self):
        for host in self.router.ROUTES:
            for bucket, minimum in [('small', 4096), ('medium', 32768), ('large', 131072)]:
                with self.subTest(host=host, bucket=bucket):
                    request = dynamic_request(host=host)
                    request['task']['context_bucket'] = bucket
                    for candidate in request['policy']['candidates']:
                        candidate['context_tokens'] = None
                    self.prepare(request)
                    before = copy.deepcopy(request)
                    result = self.router.route(request, transport=lambda *a: self.fail('unexpected call'), now=NOW)
                    self.assertEqual((result['status'], result['reason']), ('hold', 'no_candidates'))
                    self.assertEqual(result['state'], before['state'])
                    self.assertEqual(request, before)
                    self.assertEqual(result['receipt']['eligibility'], {
                        'context_min_tokens': minimum,
                        'excluded_candidates': [
                            {'id': c['id'], 'reasons': ['context_capacity_unknown']}
                            for c in request['policy']['candidates']]})

    def test_no_hard_minimum_routes_unknown_capacity_on_every_host(self):
        for host in self.router.ROUTES:
            request = dynamic_request(host=host)
            request['task']['context_bucket'] = 'unknown'
            for candidate in request['policy']['candidates']:
                candidate['context_tokens'] = None
            result = self.router.route(self.prepare(request), transport=lambda *a: provider(), now=NOW)
            self.assertEqual(result['source'], 'jev')
            self.assertEqual(result['receipt']['eligibility'], {
                'context_min_tokens': None, 'excluded_candidates': []})

    def test_known_capacity_boundaries_remain_enforced(self):
        for bucket, minimum in [('small', 4096), ('medium', 32768), ('large', 131072)]:
            request = dynamic_request()
            request['task']['context_bucket'] = bucket
            request['policy']['candidates'][0]['context_tokens'] = minimum
            request['policy']['candidates'][1]['context_tokens'] = minimum - 1
            result = self.router.route(self.prepare(request), transport=lambda *a: self.fail('unexpected call'), now=NOW)
            self.assertEqual(result['reason'], 'single_candidate')
            self.assertEqual(result['receipt']['eligibility']['excluded_candidates'], [
                {'id': 'fast', 'reasons': ['context_capacity_insufficient']}])

    def test_multiple_exclusions_are_reported_not_just_context(self):
        request = dynamic_request()
        candidate = request['policy']['candidates'][1]
        candidate['context_tokens'] = None
        candidate['capabilities'] = []
        request['host']['allowed_settings'] = request['host']['allowed_settings'][:1]
        result = self.router.route(self.prepare(request), now=NOW)
        self.assertEqual(result['reason'], 'single_candidate')
        self.assertEqual(result['receipt']['eligibility']['excluded_candidates'], [{
            'id': 'fast', 'reasons': ['required_capabilities_missing', 'context_capacity_unknown', 'settings_unsupported']}])

    def test_worker_controls_are_explained(self):
        request = dynamic_request()
        request['host']['effort_selection'] = False
        result = self.router.route(self.prepare(request), now=NOW)
        self.assertTrue(all('effort_selection_unavailable' in c['reasons']
                            for c in result['receipt']['eligibility']['excluded_candidates']))

    def test_diagnostics_stay_local(self):
        request = dynamic_request()
        excluded = copy.deepcopy(request['policy']['candidates'][1])
        excluded.update(id='local-only', model='synthetic-excluded', context_tokens=None)
        request['policy']['candidates'].append(excluded)
        request['policy']['allowed_candidates'].append(excluded['id'])
        request['host']['allowed_settings'].append({'model': excluded['model'], 'effort': excluded['effort']})
        def fake(payload, timeout):
            self.assertNotIn('local-only', str(payload))
            self.assertNotIn('context_capacity_unknown', str(payload))
            self.assertNotIn('excluded_candidates', str(payload))
            return provider()
        result = self.router.route(self.prepare(request), transport=fake, now=NOW)
        self.assertEqual(result['source'], 'jev')
        self.assertEqual(result['receipt']['eligibility']['excluded_candidates'], [
            {'id': 'local-only', 'reasons': ['context_capacity_unknown']}])
