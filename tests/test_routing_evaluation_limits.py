"""Finite synthetic observations must not produce nonfinite evaluation metrics."""
import json
import os
import subprocess
import sys
import unittest

from test_routing_evaluation import SCRIPT, load_evaluator, payload, triplet


PRIVATE_MARKER = 'SYNTHETIC_PRIVATE_OVERFLOW_EVIDENCE'


def overflow_payload(field='elapsed_ms'):
    records = triplet(fixture=PRIVATE_MARKER) + triplet(fixture=PRIVATE_MARKER, repeat=1)
    for record in records:
        record[field] = 1e308
        record['evidence'] = [PRIVATE_MARKER]
    return payload(records, objective='cost' if field == 'cost_usd' else 'latency')


class RoutingEvaluationLimitTests(unittest.TestCase):
    def test_finite_observations_with_overflowing_aggregates_raise_value_error(self):
        evaluate = load_evaluator().evaluate
        for field in ('elapsed_ms', 'cost_usd'):
            with self.subTest(field=field):
                request = overflow_payload(field)
                # Verify the inputs themselves are valid finite JSON numbers.
                json.dumps(request, allow_nan=False)
                with self.assertRaises(ValueError):
                    evaluate(request)

    def test_finite_totals_with_overflowing_improvement_ratio_raise_value_error(self):
        evaluate = load_evaluator().evaluate
        records = triplet()
        for record in records:
            record['elapsed_ms'] = 1e308 if record['strategy'] == 'jev' else 1e-300
        request = payload(records)
        json.dumps(request, allow_nan=False)
        with self.assertRaises(ValueError):
            evaluate(request)

    def test_overflow_cli_returns_sanitized_json_exit_two(self):
        if not SCRIPT.is_file():
            raise ModuleNotFoundError(f'Promised routing evaluation module absent: {SCRIPT}')
        completed = subprocess.run([sys.executable, str(SCRIPT)],
            input=json.dumps(overflow_payload(), allow_nan=False), text=True,
            capture_output=True, timeout=10,
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual(completed.returncode, 2)
        def reject_nonfinite(value):
            raise ValueError(f'Nonfinite response JSON: {value}')
        result = json.loads(completed.stdout, parse_constant=reject_nonfinite)
        self.assertIsInstance(result, dict)
        self.assertNotIn(PRIVATE_MARKER, completed.stdout + completed.stderr)
        self.assertNotIn('Traceback', completed.stdout + completed.stderr)


if __name__ == '__main__': unittest.main()
