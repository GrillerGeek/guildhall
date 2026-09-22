"""Synthetic arithmetic witnesses; no fixture qualifies a live routing profile."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / 'scripts/evaluate_routing.py'
sys.dont_write_bytecode = True


def load_evaluator():
    if not SCRIPT.is_file():
        raise ModuleNotFoundError(f'Promised routing evaluation module absent: {SCRIPT}')
    spec = importlib.util.spec_from_file_location('synthetic_evaluate_routing', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def triplet(fixture='synthetic-docs', repeat=0, split='holdout', role='docs-writer', category='docs',
            elapsed=(100, 100, 90)):
    return [dict(fixture_id=fixture, repeat=repeat, split=split, role=role, category=category,
        strategy=strategy, accepted=True, critical_misses=0, violations=0, elapsed_ms=time,
        retries=0, usage_tokens=int(time), cost_usd=time/100, evidence=['SYNTHETIC arithmetic fixture; no live evidence'])
        for strategy, time in zip(('static', 'deterministic', 'jev'), elapsed)]


def payload(records=None, objective='latency'):
    return dict(schema_version=1, synthetic=True, objective=objective,
                records=triplet() if records is None else records)


class RoutingEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.evaluate = load_evaluator().evaluate

    def test_exact_ten_percent_passes_both_baselines_without_qualification(self):
        for objective in ('latency', 'usage', 'cost'):
            with self.subTest(objective=objective):
                result = self.evaluate(payload(objective=objective))
                self.assertEqual(result['status'], 'eligible_for_review')
                self.assertFalse(result['qualification'])
                self.assertTrue(result['synthetic'])
                self.assertEqual(result['metrics']['heldout_records'], 3)
                group = result['metrics']['groups'][0]
                self.assertEqual((group['role'], group['category']), ('docs-writer', 'docs'))
                for baseline in ('static', 'deterministic'):
                    self.assertAlmostEqual(group['improvement'][baseline], 0.1)

    def test_beating_static_alone_cannot_pass(self):
        result = self.evaluate(payload(triplet(elapsed=(200, 90, 90))))
        self.assertEqual(result['status'], 'failed')
        group = result['metrics']['groups'][0]
        self.assertAlmostEqual(group['improvement']['static'], 0.55)
        self.assertAlmostEqual(group['improvement']['deterministic'], 0)

    def test_just_below_ten_percent_fails(self):
        result = self.evaluate(payload(triplet(elapsed=(100, 100, 90.01))))
        self.assertEqual(result['status'], 'failed')

    def test_aggregate_arithmetic_includes_repeats_and_reports_measured_totals(self):
        records = triplet(elapsed=(100, 100, 50)) + triplet(repeat=1, elapsed=(300, 300, 310))
        records[-1]['retries'] = 2
        result = self.evaluate(payload(records))
        self.assertEqual(result['status'], 'eligible_for_review')
        group = result['metrics']['groups'][0]
        self.assertAlmostEqual(group['improvement']['static'], 0.1)
        self.assertEqual(group['strategies']['jev'], dict(runs=2, accepted=2, acceptance_rate=1,
            critical_misses=0, violations=0, elapsed_ms=360, retries=2, usage_tokens=360, cost_usd=3.6))

    def test_development_results_cannot_rescue_holdout(self):
        records = triplet('synthetic-development', split='development', elapsed=(1000, 1000, 1))
        records += triplet(elapsed=(100, 100, 100))
        result = self.evaluate(payload(records))
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['metrics']['development_records'], 3)
        self.assertEqual(result['metrics']['heldout_records'], 3)
        self.assertEqual(result['metrics']['groups'][0]['strategies']['jev']['elapsed_ms'], 100)

    def test_quality_regressions_fail_even_when_efficiency_passes(self):
        for field, value in [('accepted', False), ('critical_misses', 1), ('violations', 1)]:
            with self.subTest(field=field):
                records = triplet(elapsed=(100, 100, 1)); records[-1][field] = value
                self.assertEqual(self.evaluate(payload(records))['status'], 'failed')

    def test_role_category_groups_cannot_hide_each_others_regression(self):
        records = triplet(elapsed=(1000, 1000, 1))
        records += triplet('synthetic-pr', role='pr-author', category='pr', elapsed=(100, 100, 90))
        records[-1]['accepted'] = False
        result = self.evaluate(payload(records))
        self.assertEqual(result['status'], 'failed')
        groups = {(g['role'], g['category']): g for g in result['metrics']['groups']}
        self.assertEqual(groups[('docs-writer', 'docs')]['status'], 'eligible_for_review')
        self.assertEqual(groups[('pr-author', 'pr')]['status'], 'failed')

    def test_incomplete_pairs_visible_and_inconclusive(self):
        records = triplet()[:-1]
        result = self.evaluate(payload(records))
        self.assertEqual(result['status'], 'inconclusive')
        self.assertTrue(result['issues'])
        self.assertEqual(result['metrics']['heldout_records'], 2)
        group = result['metrics']['groups'][0]
        self.assertEqual(group['strategies']['jev']['runs'], 0)
        self.assertIsNone(group['strategies']['jev']['acceptance_rate'])
        self.assertIsNone(group['improvement']['static'])

    def test_known_quality_failure_takes_precedence_over_missing_pair(self):
        records = triplet(); records[-1]['violations'] = 1
        records += triplet('synthetic-incomplete')[:-1]
        self.assertEqual(self.evaluate(payload(records))['status'], 'failed')

    def test_no_holdout_is_inconclusive(self):
        for records in ([], triplet(split='development')):
            with self.subTest(records=len(records)):
                result = self.evaluate(payload(records))
                self.assertEqual(result['status'], 'inconclusive')
                self.assertTrue(result['issues'])

    def test_missing_objective_measurement_and_zero_baseline_inconclusive(self):
        for objective, field in [('usage', 'usage_tokens'), ('cost', 'cost_usd')]:
            for value in (None, 0):
                with self.subTest(objective=objective, value=value):
                    records = triplet(); records[0][field] = value
                    result = self.evaluate(payload(records, objective))
                    self.assertEqual(result['status'], 'inconclusive')
                    self.assertIsNone(result['metrics']['groups'][0]['improvement']['static'])

    def test_missing_measurements_stay_null_when_other_objective_passes(self):
        records = triplet()
        records[-1]['usage_tokens'] = None; records[-1]['cost_usd'] = None
        result = self.evaluate(payload(records))
        self.assertEqual(result['status'], 'eligible_for_review')
        stats = result['metrics']['groups'][0]['strategies']['jev']
        self.assertIsNone(stats['usage_tokens']); self.assertIsNone(stats['cost_usd'])

    def test_duplicate_records_rejected_not_dropped(self):
        records = triplet(); records.append(copy.deepcopy(records[0]))
        with self.assertRaises(ValueError): self.evaluate(payload(records))

    def test_fixture_scope_and_split_cannot_change_across_repeats(self):
        for field, value in [('split', 'development'), ('role', 'pr-author'), ('category', 'pr')]:
            with self.subTest(field=field):
                records = triplet() + triplet(repeat=1)
                for record in records[3:]: record[field] = value
                with self.assertRaises(ValueError): self.evaluate(payload(records))

    def test_invalid_records_rejected(self):
        changes = [('repeat', True), ('repeat', -1), ('accepted', 1), ('elapsed_ms', 0),
            ('elapsed_ms', float('inf')), ('elapsed_ms', float('nan')), ('critical_misses', -1),
            ('violations', True), ('retries', -1), ('usage_tokens', True), ('cost_usd', -0.1),
            ('strategy', 'unknown'), ('split', 'unknown'), ('evidence', []),
            ('evidence', ['']), ('unknown_field', 'private')]
        for field, value in changes:
            with self.subTest(field=field, value=value):
                records = triplet(); records[0][field] = value
                with self.assertRaises(ValueError): self.evaluate(payload(records))
        malformed = payload(); del malformed['records'][0]['evidence']
        with self.assertRaises(ValueError): self.evaluate(malformed)

    def test_non_synthetic_data_still_does_not_auto_qualify(self):
        req = payload(); req['synthetic'] = False
        result = self.evaluate(req)
        self.assertFalse(result['qualification'])

    def test_cli_json_demo_and_sanitized_invalid_input(self):
        env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
        completed = subprocess.run([sys.executable, str(SCRIPT)], input=json.dumps(payload()),
            text=True, capture_output=True, timeout=10, env=env)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)['status'], 'eligible_for_review')
        demo = subprocess.run([sys.executable, str(SCRIPT), '--demo'], text=True,
            capture_output=True, timeout=10, env=env)
        self.assertEqual(demo.returncode, 0, demo.stderr)
        result = json.loads(demo.stdout)
        self.assertTrue(result['synthetic']); self.assertFalse(result['qualification'])
        self.assertGreater(result['metrics']['development_records'], 0)
        self.assertGreater(result['metrics']['heldout_records'], 0)
        self.assertGreaterEqual(len(result['metrics']['groups']), 2)
        for raw in ('PRIVATE_INVALID_INPUT', '{"schema_version":1,"schema_version":1}'):
            failed = subprocess.run([sys.executable, str(SCRIPT)], input=raw, text=True,
                capture_output=True, timeout=10, env=env)
            self.assertEqual(failed.returncode, 2)
            self.assertIsInstance(json.loads(failed.stdout), dict)
            self.assertNotIn('PRIVATE_INVALID_INPUT', failed.stdout + failed.stderr)


if __name__ == '__main__': unittest.main()
