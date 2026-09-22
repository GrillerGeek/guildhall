"""Rejected packets must not reset trusted quest routing state; synthetic only."""
import copy
import json
import os
import subprocess
import sys
import unittest

from test_routing import NOW, SCRIPT, load_script, provider, qualify, request


TRUSTED_STATES = (
    ('budget', dict(calls_used=8, provider_failed=False, adaptive_suspended=False), 'budget_exhausted'),
    ('circuit', dict(calls_used=3, provider_failed=True, adaptive_suspended=False), 'provider_failed'),
    ('suspension', dict(calls_used=2, provider_failed=False, adaptive_suspended=True), 'adaptive_unqualified'),
)


class RoutingRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.router = load_script()
        self.calls = []

    def invoke(self, packet):
        def fake(payload, timeout_ms):
            self.calls.append((payload, timeout_ms))
            return provider()
        return self.router.route(packet, transport=fake, now=NOW)

    def malformed(self, field, state):
        packet = qualify(request('adaptive'))
        packet['state'] = copy.deepcopy(state)
        if field == 'task':
            packet['task']['risk'] = 'invalid-risk'
        else:
            packet['policy']['timeout_ms'] = 0
        return packet

    def test_rejection_preserves_each_independently_valid_state_exactly(self):
        for label, state, _ in TRUSTED_STATES:
            for field in ('task', 'policy'):
                with self.subTest(state=label, field=field):
                    result = self.invoke(self.malformed(field, state))
                    self.assertEqual((result['status'], result['reason']), ('hold', 'invalid_request'))
                    self.assertIsNone(result['dispatch'])
                    self.assertEqual(result['state'], state)
        self.assertEqual(self.calls, [])

    def test_correction_carrying_rejected_packet_state_cannot_restart_routing(self):
        for label, state, reason in TRUSTED_STATES:
            for field in ('task', 'policy'):
                with self.subTest(state=label, field=field):
                    self.calls.clear()
                    rejected = self.invoke(self.malformed(field, state))
                    corrected = qualify(request('adaptive'))
                    corrected['state'] = copy.deepcopy(rejected['state'])
                    result = self.invoke(corrected)
                    self.assertEqual(self.calls, [])
                    self.assertEqual(result['state'], state)
                    self.assertEqual(result['reason'], reason)
                    self.assertEqual(result['dispatch'], corrected['baseline'])

    def test_invalid_or_missing_state_returns_closed_hold(self):
        invalid_states = [None, {}, [],
            dict(calls_used=-1, provider_failed=False, adaptive_suspended=False),
            dict(calls_used=True, provider_failed=False, adaptive_suspended=False),
            dict(calls_used=3, provider_failed='false', adaptive_suspended=False),
            dict(calls_used=3, provider_failed=False, adaptive_suspended=0)]
        for index, state in enumerate(invalid_states + ['missing']):
            with self.subTest(case=index):
                packet = request()
                if state == 'missing':
                    del packet['state']
                else:
                    packet['state'] = state
                result = self.invoke(packet)
                self.assertEqual((result['status'], result['reason']), ('hold', 'invalid_request'))
                self.assertIsNone(result['dispatch'])
                self.assertIs(result['state']['provider_failed'], True)
                self.assertIs(result['state']['adaptive_suspended'], True)
        self.assertEqual(self.calls, [])

    def test_invalid_json_cli_returns_closed_state_without_raw_input(self):
        for raw in ('PRIVATE_MALFORMED_PACKET', '{', '[1,2,3]'):
            with self.subTest(raw=raw):
                completed = subprocess.run([sys.executable, str(SCRIPT)], input=raw, text=True,
                    capture_output=True, timeout=10,
                    env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
                self.assertEqual(completed.returncode, 2)
                result = json.loads(completed.stdout)
                self.assertEqual((result['status'], result['reason']), ('hold', 'invalid_request'))
                self.assertIsNone(result['dispatch'])
                self.assertIs(result['state']['provider_failed'], True)
                self.assertIs(result['state']['adaptive_suspended'], True)
                self.assertNotIn('PRIVATE_MALFORMED_PACKET', completed.stdout + completed.stderr)


if __name__ == '__main__': unittest.main()
