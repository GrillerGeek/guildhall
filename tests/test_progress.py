"""Quest progress record: the helper Mordain drives and the views read."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / 'plugin/portable/scripts/progress.py'
PLAN = 'docs/guildhall/plans/2026-11-07-mcp-agent-access.md'
RECORD = 'docs/guildhall/plans/2026-11-07-mcp-agent-access/progress.json'


def load_module():
    spec = importlib.util.spec_from_file_location('guildhall_progress', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SKELETON = {
    'milestones': [
        {'id': 'plan', 'name': 'Plan', 'goal': 'Agree mode and scope'},
        {'id': 'tests', 'name': 'Tests', 'goal': 'Write the failing tests',
         'loop': {'reason': 'the contract may change', 'limit': 2}},
        {'id': 'build', 'name': 'Build', 'goal': 'Make the new tests pass',
         'loop': {'reason': 'reviews may find blocking issues', 'limit': 2}},
        {'id': 'review', 'name': 'Review', 'goal': 'Independent reviews',
         'loop': {'reason': 'fixes are re-reviewed', 'limit': 2}},
        {'id': 'ui', 'name': 'UI', 'goal': 'Walk the app in a real browser'},
        {'id': 'pr', 'name': 'PR', 'goal': 'Draft the pull request'},
    ],
    'waypoints': [
        {'id': 'scope', 'need': 'Approve mode and scope', 'after': 'plan'},
        {'id': 'accept', 'need': 'Muse/Dots acceptance', 'after': 'pr'},
    ],
}


class Project:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='guildhall progress ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / PLAN).parent.mkdir(parents=True)
        (self.root / PLAN).write_text('# Plan\n')

    def run_cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root), '--plan', PLAN, *args],
                              input=stdin, capture_output=True, text=True, timeout=30)

    def init(self):
        result = self.run_cli('init', '--title', 'MCP agent access', '--repo', 'camp-planner',
                              '--branch', 'feature/mcp', '--host', 'codex', '--skeleton-json', '-',
                              stdin=json.dumps(SKELETON))
        self.assertEqual(result.returncode, 0, result.stderr)

    def record(self):
        return json.loads((self.root / RECORD).read_text())


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.p = load_module()
        self.r = self.p.init_record('MCP agent access', PLAN, SKELETON['milestones'], SKELETON['waypoints'], now=100.0)

    def apply(self, op, now=200.0, **args):
        self.r = self.p.apply(self.r, op, args, now)
        return self.r

    def states(self):
        return {m['id']: m['state'] for m in self.r['milestones']}

    def test_record_path_refuses_outside_plans(self):
        root = Path('/project')
        self.assertEqual(self.p.record_path(root, PLAN), root / RECORD)
        for bad in ('docs/guildhall/plans/x.txt', 'docs/other/x.md', '../docs/guildhall/plans/x.md',
                    'docs/guildhall/plans/../../x.md', '/abs/docs/guildhall/plans/x.md',
                    'docs/guildhall/plans/README.md'):
            with self.assertRaises(self.p.Refusal, msg=bad):
                self.p.record_path(root, bad)

    def test_init_seeds_milestones_and_waypoints(self):
        self.assertEqual(self.r['schema_version'], 1)
        self.assertEqual(self.r['status'], 'active')
        self.assertEqual(self.r['plan_path'], PLAN)
        self.assertEqual([m['id'] for m in self.r['milestones']], ['plan', 'tests', 'build', 'review', 'ui', 'pr'])
        self.assertTrue(all(m['state'] == 'upcoming' and m['pass'] == 0 for m in self.r['milestones']))
        self.assertEqual(self.r['milestones'][2]['loop'], {'reason': 'reviews may find blocking issues', 'limit': 2})
        self.assertIsNone(self.r['milestones'][0]['loop'])
        self.assertEqual([(w['id'], w['state'], w['planned']) for w in self.r['waypoints']],
                         [('scope', 'upcoming', True), ('accept', 'upcoming', True)])

    def test_init_refuses_bad_skeleton(self):
        for milestones, waypoints in (([], []),
                                      ([{'id': 'a', 'name': 'A', 'goal': 'g'}] * 2, []),
                                      ([{'id': 'a', 'name': 'A', 'goal': 'g'}], [{'id': 'w', 'need': 'n', 'after': 'zzz'}]),
                                      ([{'id': 'Bad Id', 'name': 'A', 'goal': 'g'}], [])):
            with self.assertRaises(self.p.Refusal):
                self.p.init_record('t', PLAN, milestones, waypoints)

    def test_start_makes_single_current_and_done_never_decreases(self):
        self.apply('start', milestone='plan')
        self.apply('start', milestone='tests')
        self.assertEqual(self.states()['plan'], 'done')
        self.assertEqual(self.states()['tests'], 'current')
        self.assertEqual(self.r['milestones'][1]['pass'], 1)
        self.apply('done', milestone='tests')
        self.apply('start', milestone='build')
        done_before = sum(s == 'done' for s in self.states().values())
        self.apply('loop', milestone='tests', why='contract changed')
        self.assertEqual(sum(s == 'done' for s in self.states().values()), done_before)
        self.assertEqual(list(self.states().values()).count('current'), 1)
        with self.assertRaises(self.p.Refusal):
            self.apply('start', milestone='plan')  # done milestones repeat only through loop

    def test_loop_increments_pass_and_flags_over_limit(self):
        self.apply('start', milestone='build')
        self.apply('loop', milestone='build', why='security review found a stale read')
        build = self.r['milestones'][2]
        self.assertEqual((build['state'], build['pass']), ('current', 2))
        self.assertEqual(self.r['loops'][-1]['why'], 'security review found a stale read')
        self.assertTrue(self.r['loops'][-1]['within_limit'])
        self.apply('loop', milestone='build', why='again')
        self.assertEqual(self.r['milestones'][2]['pass'], 3)
        self.assertFalse(self.r['loops'][-1]['within_limit'])
        with self.assertRaises(self.p.Refusal):
            self.apply('loop', milestone='ui', why='never started')

    def test_loop_on_undeclared_milestone_is_recorded_outside_plan(self):
        self.apply('start', milestone='ui')
        self.apply('loop', milestone='ui', why='walkthrough failed')
        self.assertFalse(self.r['loops'][-1]['within_limit'])

    def test_tasks_scoped_to_current_pass(self):
        self.apply('start', milestone='build')
        self.apply('task', milestone='build', task='read', name='Read consistency', who='feature-implementer')
        self.apply('work', task='read')
        self.apply('finish-task', task='read')
        self.apply('loop', milestone='build', why='review found a race')
        self.apply('task', milestone='build', task='photo', name='Photo race', because='security review B5')
        tasks = {t['id']: t for t in self.r['tasks']}
        self.assertEqual((tasks['read']['pass'], tasks['read']['state']), (1, 'done'))
        self.assertEqual((tasks['photo']['pass'], tasks['photo']['state']), (2, 'upcoming'))
        self.assertEqual(tasks['photo']['added_because'], 'security review B5')
        with self.assertRaises(self.p.Refusal):
            self.apply('task', milestone='build', task='photo', name='dup')

    def test_wait_and_resume_planned_and_unplanned(self):
        self.apply('start', milestone='plan')
        self.apply('wait', waypoint='scope', now=300.0)
        scope = self.r['waypoints'][0]
        self.assertEqual((scope['state'], scope['waiting_since']), ('waiting', 300.0))
        self.apply('resume', waypoint='scope')
        self.assertEqual(self.r['waypoints'][0]['state'], 'done')
        self.apply('wait', need='Choose between two storage designs')
        ask = self.r['waypoints'][-1]
        self.assertEqual((ask['planned'], ask['state'], ask['after']), (False, 'waiting', 'plan'))
        self.apply('resume', waypoint=ask['id'])
        self.assertEqual(self.r['waypoints'][-1]['state'], 'done')

    def test_skip_add_note_close(self):
        self.apply('skip', milestone='ui', why='no UI change')
        self.assertEqual(self.r['milestones'][4]['skipped_why'], 'no UI change')
        self.apply('add-milestone', milestone='refactor', name='Refactor', goal='Extract helper', after='build',
                   because='review asked for it')
        self.assertEqual([m['id'] for m in self.r['milestones']][3], 'refactor')
        self.apply('note', text='Bruga is fixing the photo race')
        self.assertEqual(self.r['note'], 'Bruga is fixing the photo race')
        self.apply('close', status='completed')
        self.assertEqual(self.r['status'], 'completed')
        self.apply('start', milestone='plan')
        with self.assertRaises(self.p.Refusal):
            self.apply('skip', milestone='plan', why='started milestones cannot be skipped')

    def test_unknown_ids_refuse(self):
        for op, args in (('start', {'milestone': 'nope'}), ('work', {'task': 'nope'}),
                         ('resume', {'waypoint': 'nope'}), ('task', {'milestone': 'nope', 'task': 't', 'name': 'n'}),
                         ('bogus-op', {})):
            with self.assertRaises(self.p.Refusal, msg=op):
                self.apply(op, **args)


class CliTests(Project, unittest.TestCase):
    def test_init_and_update_through_cli(self):
        self.init()
        result = self.run_cli('start', 'build')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.record()['milestones'][2]['state'], 'current')
        self.assertEqual(self.record()['host'], 'codex')

    def test_unknown_id_refuses_and_file_unchanged(self):
        self.init()
        before = (self.root / RECORD).read_bytes()
        result = self.run_cli('start', 'nope')
        self.assertEqual(result.returncode, 2)
        self.assertIn('nope', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual((self.root / RECORD).read_bytes(), before)

    def test_update_without_record_refuses(self):
        result = self.run_cli('start', 'build')
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)

    def test_corrupt_record_refuses_update_without_traceback(self):
        self.init()
        (self.root / RECORD).write_text('{not json')
        result = self.run_cli('start', 'build')
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)

    def test_concurrent_cli_updates_all_land(self):
        self.init()
        self.run_cli('start', 'review')
        procs = [subprocess.Popen([sys.executable, str(SCRIPT), '--root', str(self.root), '--plan', PLAN,
                                   'task', 'review', f'r{i}', f'Reviewer {i}'],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE) for i in range(10)]
        for proc in procs:
            _, err = proc.communicate(timeout=30)
            self.assertEqual(proc.returncode, 0, err)
        self.assertEqual(sorted(t['id'] for t in self.record()['tasks']), sorted(f'r{i}' for i in range(10)))

    def test_cli_bad_plan_path_writes_nothing(self):
        for bad in ('docs/other/plan.md', '../outside/docs/guildhall/plans/x.md', 'docs/guildhall/plans/x.txt'):
            result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root), '--plan', bad,
                                     'init', '--title', 't', '--skeleton-json', '-'],
                                    input=json.dumps(SKELETON), capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 2, bad)
        written = sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*') if p.is_file())
        self.assertEqual(written, [PLAN])
        self.assertFalse((self.root.parent / 'outside').exists())

    def test_init_twice_refuses_without_force(self):
        self.init()
        result = self.run_cli('init', '--title', 'again', '--skeleton-json', '-', stdin=json.dumps(SKELETON))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.record()['title'], 'MCP agent access')


if __name__ == '__main__':
    unittest.main()
