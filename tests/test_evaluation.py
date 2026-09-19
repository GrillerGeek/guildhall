"""Evidence isolation and synthetic input checks; no model or network calls."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'scripts'))
from evaluate_portable import capture_records, prepare, snapshot


class EvaluationTests(unittest.TestCase):
    def test_snapshot_detects_symlink_substitution_without_reading_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'project'; root.mkdir()
            outside = Path(tmp)/'outside'; outside.write_text('identical')
            protected = root/'KEEP'; protected.write_text('identical')
            before = snapshot(root)
            protected.unlink(); protected.symlink_to(outside)
            (root/'broken').symlink_to(Path(tmp)/'missing')
            (root/'directory').symlink_to(Path(tmp), target_is_directory=True)
            after = snapshot(root)
            self.assertNotEqual(before['KEEP'], after['KEEP'])
            self.assertEqual(after['KEEP']['type'], 'symlink')
            self.assertEqual(after['broken']['target'], str(Path(tmp)/'missing'))
            self.assertEqual(set(after), {'KEEP','broken','directory'})
            self.assertNotIn('sha256', after['KEEP'])

    def test_captures_only_identified_session_and_preserves_raw_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root/'home/sessions'; sessions.mkdir(parents=True)
            thread = '01a0bbd1-5b2e-7c21-8a23-6513fffc61a8'
            raw = b'{"type":"response_item","payload":{"message":"opaque: leave unchanged"}}\n'
            (sessions/f'rollout-{thread}.jsonl').write_bytes(raw)
            (sessions/'unrelated.jsonl').write_text('unrelated private session')
            stdout = root/'stdout.jsonl'
            stdout.write_text('malformed\n'+json.dumps({'type':'thread.started', 'thread_id':'../../*'})+'\n'+json.dumps({'type':'thread.started','thread_id':thread})+'\n')
            records = capture_records(stdout, root/'captured', root/'home')
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual((root/'captured'/f'{thread}.jsonl').read_bytes(), raw)
            self.assertEqual(len(list((root/'captured').iterdir())), 1)

    def test_ambiguous_session_is_reported_without_copying_either(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); sessions = root/'home/sessions'; sessions.mkdir(parents=True)
            thread = '01a0bbd1-5b2e-7c21-8a23-6513fffc61a8'
            for prefix in ['one','two']:
                (sessions/f'{prefix}-{thread}.jsonl').write_text('{}\n')
            stdout = root/'stdout.jsonl'
            stdout.write_text(json.dumps({'type':'thread.started','thread_id':thread})+'\n')
            records = capture_records(stdout, root/'captured', root/'home')
            self.assertFalse(records[0]['available'])
            self.assertEqual(records[0]['matches'], 2)
            self.assertEqual(list((root/'captured').iterdir()), [])

    def test_feature_input_cannot_masquerade_as_real_human_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            project, prompt = prepare('feature', Path(tmp), '/existing/python')
            readiness = (project/'FIXTURE-READINESS.md').read_text()
            self.assertIn('No person reviewed or approved', readiness)
            self.assertIn('not actual human approval', prompt)
            spec = project/'docs/specs/SPEC-f101.yaml'
            self.assertIn(hashlib.sha256(spec.read_bytes()).hexdigest(), readiness)
            parsed = json.loads(spec.read_text())['spec']
            self.assertEqual(parsed['status'], 'ready')
            self.assertEqual(parsed['gap_check']['warnings'], 0)
            for block in ['context','expectations_detail','boundaries','deliverables','validation']:
                self.assertTrue(parsed[block])
            before = snapshot(project)
            self.assertIn('KEEP.txt', before)
            self.assertNotIn('tests/test_greetings.py', before)


if __name__ == '__main__': unittest.main()
