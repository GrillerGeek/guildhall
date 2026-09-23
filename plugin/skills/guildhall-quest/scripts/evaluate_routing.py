#!/usr/bin/env python3
"""Analyze supplied routing records; no network, model calls or policy changes."""
from __future__ import annotations

import argparse
import json
import math
import sys

STRATEGIES = ('static', 'deterministic', 'jev')
FIELDS = set('fixture_id repeat split role category strategy accepted critical_misses violations elapsed_ms retries usage_tokens cost_usd evidence'.split())
ROLES = set(('accessibility-reviewer architecture-reviewer debug-investigator docs-writer '
             'feature-implementer fog-cartographer migration-safety-reviewer observability-reviewer '
             'ops-readiness-reviewer performance-reviewer plugin-validator pr-author prototype-builder '
             'refactorer reliability-reviewer security-reviewer test-author ui-test-author').split())
CATEGORIES = set('docs pr implementation tests debug review prototype refactor'.split())
MAX_INPUT = 16 * 1024 * 1024


def require(condition):
    if not condition:
        raise ValueError('invalid evaluation input')


def number(value, *, integer=False, positive=False):
    require(type(value) is int if integer else type(value) in (int, float))
    try:
        require(math.isfinite(value) and (value > 0 if positive else value >= 0))
    except OverflowError:
        raise ValueError('invalid evaluation input') from None


def string(value, maximum=256):
    require(type(value) is str and 0 < len(value) <= maximum)


def validate(payload):
    require(type(payload) is dict and set(payload) == {'schema_version', 'synthetic', 'objective', 'records'})
    require(type(payload['schema_version']) is int and payload['schema_version'] == 1)
    require(type(payload['synthetic']) is bool)
    require(type(payload['objective']) is str and payload['objective'] in ('latency', 'usage', 'cost'))
    require(type(payload['records']) is list and len(payload['records']) <= 100000)
    identities, scopes = set(), {}
    for record in payload['records']:
        require(type(record) is dict and set(record) == FIELDS)
        for field in ('fixture_id', 'role', 'category', 'strategy', 'split'):
            string(record[field])
        require(record['role'] in ROLES and record['category'] in CATEGORIES)
        require(record['strategy'] in STRATEGIES and record['split'] in ('development', 'holdout'))
        require(type(record['accepted']) is bool)
        for field in ('repeat', 'critical_misses', 'violations', 'retries'):
            number(record[field], integer=True)
        number(record['elapsed_ms'], positive=True)
        for field in ('usage_tokens', 'cost_usd'):
            if record[field] is not None:
                number(record[field], integer=field == 'usage_tokens')
        require(type(record['evidence']) is list and 1 <= len(record['evidence']) <= 64)
        for evidence in record['evidence']:
            string(evidence, 4096)
        require(len(set(record['evidence'])) == len(record['evidence']))
        identity = (record['fixture_id'], record['repeat'], record['strategy'])
        require(identity not in identities)
        identities.add(identity)
        scope = (record['split'], record['role'], record['category'])
        previous = scopes.setdefault(record['fixture_id'], scope)
        require(previous == scope)
    try:
        require(len(json.dumps(payload, allow_nan=False).encode()) <= MAX_INPUT)
    except (ValueError, OverflowError, UnicodeError):
        raise ValueError('invalid evaluation input') from None


def stats(records):
    result = dict(runs=len(records), accepted=sum(r['accepted'] for r in records))
    result['acceptance_rate'] = result['accepted'] / len(records) if records else None
    for field in ('critical_misses', 'violations', 'elapsed_ms', 'retries', 'usage_tokens', 'cost_usd'):
        values = [r[field] for r in records]
        try:
            total = None if field in ('usage_tokens', 'cost_usd') and (not values or None in values) else sum(values)
            if total is not None:
                require(math.isfinite(total))
        except OverflowError:
            raise ValueError('invalid evaluation input') from None
        result[field] = total
    return result


def evaluate(payload):
    """Return held-out per-scope arithmetic, never an automatic qualification."""
    validate(payload)
    records = payload['records']
    holdout = [r for r in records if r['split'] == 'holdout']
    issues, groups = [], []
    metric = {'latency': 'elapsed_ms', 'usage': 'usage_tokens', 'cost': 'cost_usd'}[payload['objective']]
    # Development pairing is required for study integrity, but never influences acceptance math.
    all_pairs = {}
    for r in records:
        all_pairs.setdefault((r['fixture_id'], r['repeat']), set()).add(r['strategy'])
    incomplete_study = any(strategies != set(STRATEGIES) for strategies in all_pairs.values())
    if incomplete_study:
        issues.append('Incomplete strategy pairs in supplied study.')
    if not holdout:
        issues.append('No held-out records.')
    for role, category in sorted({(r['role'], r['category']) for r in holdout}):
        scoped = [r for r in holdout if (r['role'], r['category']) == (role, category)]
        by_strategy = {s: [r for r in scoped if r['strategy'] == s] for s in STRATEGIES}
        strategies = {s: stats(by_strategy[s]) for s in STRATEGIES}
        pairs = {}
        for r in scoped:
            pairs.setdefault((r['fixture_id'], r['repeat']), {})[r['strategy']] = r
        complete = all(set(pair) == set(STRATEGIES) for pair in pairs.values())
        bad_quality = any(r['critical_misses'] or r['violations'] for r in by_strategy['jev'])
        improvement = {s: None for s in STRATEGIES[:2]}
        missing, efficiency_failed = not complete, False
        for baseline in STRATEGIES[:2]:
            comparable = [pair for pair in pairs.values() if baseline in pair and 'jev' in pair]
            if comparable and sum(p['jev']['accepted'] for p in comparable) < sum(p[baseline]['accepted'] for p in comparable):
                bad_quality = True
            base_total, jev_total = strategies[baseline][metric], strategies['jev'][metric]
            if not complete or base_total is None or jev_total is None or base_total <= 0:
                missing = True
            else:
                try:
                    improvement[baseline] = (base_total - jev_total) / base_total
                    require(math.isfinite(improvement[baseline]))
                except OverflowError:
                    raise ValueError('invalid evaluation input') from None
                if improvement[baseline] < 0.1 - 1e-12:
                    efficiency_failed = True
        status = ('failed' if bad_quality else 'inconclusive' if missing else
                  'failed' if efficiency_failed else 'eligible_for_review')
        if status != 'eligible_for_review':
            issues.append(f'{role}/{category}: {status}; inspect paired quality and objective measurements.')
        reason_codes = [name for name, active in [('quality_regression', bad_quality),
            ('missing_pairs_or_measurements', missing), ('insufficient_objective_improvement', efficiency_failed)] if active]
        groups.append(dict(role=role, category=category, status=status, reason_codes=reason_codes,
                           strategies=strategies, improvement=improvement))
    statuses = {g['status'] for g in groups}
    overall = ('failed' if 'failed' in statuses else 'inconclusive'
               if incomplete_study or not holdout or 'inconclusive' in statuses else 'eligible_for_review')
    return dict(schema_version=1, synthetic=payload['synthetic'], qualification=False, status=overall,
                issues=issues, metrics=dict(development_records=len(records)-len(holdout),
                                           heldout_records=len(holdout), groups=groups))


def demo():
    """32 synthetic fixtures, two repeats, two scopes; not observed model behavior."""
    records = []
    for fixture in range(32):
        for repeat in range(2):
            for strategy in STRATEGIES:
                elapsed = {'static': 120, 'deterministic': 100, 'jev': 85}[strategy]
                records.append(dict(fixture_id=f'synthetic-{fixture:02}', repeat=repeat,
                    split='development' if fixture < 8 else 'holdout',
                    role='docs-writer' if fixture % 2 else 'pr-author',
                    category='docs' if fixture % 2 else 'pr', strategy=strategy, accepted=True,
                    critical_misses=0, violations=0, elapsed_ms=elapsed, retries=0,
                    usage_tokens=elapsed, cost_usd=None,
                    evidence=['SYNTHETIC arithmetic fixture; no API, model execution or live qualification']))
    return dict(schema_version=1, synthetic=True, objective='latency', records=records)


def read_input():
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result)
            result[key] = value
        return result
    def constant(_):
        raise ValueError('invalid evaluation input')
    raw = sys.stdin.buffer.read(MAX_INPUT + 1)
    require(len(raw) <= MAX_INPUT)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true')
    args = parser.parse_args()
    try:
        result = evaluate(demo() if args.demo else read_input())
    except (ValueError, TypeError, OverflowError, UnicodeError, RecursionError):
        print('{"schema_version":1,"error":"invalid_evaluation_input"}')
        return 2
    print(json.dumps(result, allow_nan=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
