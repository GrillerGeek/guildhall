"""Synthetic feature inputs for the opt-in model evaluation, never live approval."""
from pathlib import Path
import hashlib
import json


def prepare(project: Path, parser_python: str) -> str:
    files = {
        'src/__init__.py': '',
        'src/greetings.py': 'def greet(name):\n    raise NotImplementedError\n',
        'tests/__init__.py': '',
        'tests/test_baseline.py': 'import unittest\n\nclass Baseline(unittest.TestCase):\n    def test_sum(self):\n        self.assertEqual(sum([2, 3]), 5)\n    def test_join(self):\n        self.assertEqual("".join(["a", "b"]), "ab")\n',
        'README.md': '# Fixture\n\nA local greeting utility.\n',
    }
    for name, content in files.items():
        path = project/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    boundaries = [
        'Do not modify KEEP.txt, AGENTS.md, installed skill resources, or existing baseline tests.',
        'Do not install dependencies, use the network, commit, push, or modify client settings.',
        'Do not write outside this disposable project.',
        'Implementation writes are limited to src/greetings.py; test-author writes are limited to tests/test_greetings.py; documentation writes are limited to README.md.',
        'Only orchestration may change the selected Spec status and create its new execution report; do not modify other Spec content, gap-check evidence, or fixture readiness evidence.',
    ]
    spec = {
        'id': 'SPEC-f101', 'product': 'PROD-f101', 'intentions': ['INT-f101'],
        'expectations': ['EXP-f101'], 'status': 'ready',
        'context': {'stack': 'Python 3, standard library unittest; preinstalled PyYAML for safe lifecycle parsing.',
                    'patterns': 'One pure function in src/greetings.py; unittest discovery in tests/.',
                    'conventions': ['Use python3 -B -m unittest discover -s tests -v. No additional build/lint tooling exists.',
                                    'Public API: from src.greetings import greet; greet(name: str) returns str. Only string inputs are in scope.'],
                    'existing_code_refs': [{'path': 'tests/test_baseline.py', 'note': 'Test conventions; preserve both baseline tests.'}],
                    'auth': 'None: pure local function, no secrets or external services.'},
        'expectations_detail': [{'id': 'EXP-f101', 'description': 'greet trims surrounding whitespace and returns Hello, <trimmed name>!; an empty trimmed name returns Hello, adventurer!.',
                                 'validation': 'Three independent tests cover padded ordinary input, whitespace-only input, and a Unicode name; both existing baseline tests still pass.',
                                 'edge_cases': ['Whitespace-only input returns Hello, adventurer!.', 'Unicode name Zoë remains intact and returns Hello, Zoë!.']}],
        'boundaries': boundaries,
        'deliverables': ['src/greetings.py implements greet.', 'tests/test_greetings.py supplies three independent behavior tests.',
                         'README.md documents the public function with ordinary and blank examples.',
                         'A quest plan under docs/guildhall/plans/ and a new docs/reviews/SPEC-f101-<UTC timestamp>-execution.md report with all required evidence.'],
        'validation': {'automated': ['python3 -B -m unittest discover -s tests -v: all five tests pass.',
                                     'Protected input files remain byte-for-byte unchanged, aside from the explicitly allowed source, README and status-only Spec edits.'],
                       'human_review': ['A human reviews wording and implementation after status review. This remains pending during the evaluation.']},
        'gap_check': {'status': 'passed', 'blockers': 0, 'warnings': 0,
                      'report': 'docs/reviews/SPEC-f101-gap-check.md', 'date': '2026-09-19'},
    }
    path = project/'docs/specs/SPEC-f101.yaml'
    path.parent.mkdir(parents=True)
    # JSON is a safe YAML subset; whitespace remains stable for status-only edits.
    path.write_text(json.dumps({'spec': spec}, indent=2, ensure_ascii=False)+'\n')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    report = project/'docs/reviews/SPEC-f101-gap-check.md'
    report.parent.mkdir(parents=True)
    report.write_text('PASS — 0 blockers, 0 warnings\n\nSynthetic evaluation input, not a live review or approval.\n\n## Coverage\n\nAll fixture impact paths are owned by the listed Deliverables. No omissions.\n\nReady Spec SHA-256: '+digest+'\n')
    (project/'FIXTURE-READINESS.md').write_text('# Synthetic readiness input\n\nThis is a mocked human-readiness dependency for a disposable integration test. No person reviewed or approved this synthetic Spec. The evaluator explicitly substitutes this record only for the readiness human-fact input; never describe it as actual human approval or apply it to a live Spec. All other execution, review and lifecycle requirements remain real.\n\nReady Spec SHA-256: '+digest+'\n')
    return ('Run a feature quest for docs/specs/SPEC-f101.yaml in this disposable integration test. '
            'This invocation explicitly mocks only the readiness human-fact prerequisite using FIXTURE-READINESS.md; it is not actual human approval, and the final report must say so. '
            'The gap-check report is also labeled synthetic fixture input. Do not fabricate live review history. '
            'Exercise the remaining contracts for real: fresh workers, status-only recorder transitions, independent test author, observed RED/GREEN, mandatory reviews, Execution Report and final status review. '
            'For YAML parsing, use the preinstalled PyYAML at '+parser_python+' and reject duplicate keys. '
            'Do not send the implementation or main transcript to the test author. Internal pure utility has no deployed service or UI; document reviewer trigger decisions. '
            'No refactor is needed unless a concrete issue appears. All final human review/QA checks stay pending. '
            'Use available worker slots efficiently; await every selected reviewer. Protected fixture evidence must remain unchanged. '
            'If blocked, preserve partial state and report the exact reason. Do not force a pass.')
