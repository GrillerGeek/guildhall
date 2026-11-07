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
        done_before = self.p.counted(self.r)[0]
        self.apply('loop', milestone='tests', why='contract changed')
        self.assertEqual(self.p.counted(self.r)[0], done_before)  # the count the user sees never drops
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

    def test_partial_record_refuses_update_without_traceback(self):
        self.init()
        record = self.record()
        del record['milestones'][0]['pass']
        (self.root / RECORD).write_text(json.dumps(record))
        result = self.run_cli('start', 'plan')
        self.assertEqual(result.returncode, 2, result.stderr)
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

    def test_symlinked_record_folder_refuses(self):
        outside = self.root.parent / (self.root.name + '-outside')
        outside.mkdir()
        self.addCleanup(lambda: [p.unlink() for p in outside.iterdir()] and None or outside.rmdir())
        (self.root / RECORD).parent.symlink_to(outside, target_is_directory=True)
        result = self.run_cli('init', '--title', 't', '--skeleton-json', '-', stdin=json.dumps(SKELETON))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(list(outside.iterdir()), [])

    def test_init_twice_refuses_without_force(self):
        self.init()
        result = self.run_cli('init', '--title', 'again', '--skeleton-json', '-', stdin=json.dumps(SKELETON))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.record()['title'], 'MCP agent access')



def width(line):
    return len(line)


class RenderTests(unittest.TestCase):
    """The journey + focus card, as a terminal and a browser draw it."""

    def setUp(self):
        self.p = load_module()
        r = self.p.init_record('MCP agent access', PLAN, SKELETON['milestones'], SKELETON['waypoints'],
                               repo='camp-planner', branch='feature/mcp', now=0.0)
        for op, args in (('start', {'milestone': 'plan'}), ('wait', {'waypoint': 'scope'}),
                         ('resume', {'waypoint': 'scope'}), ('start', {'milestone': 'tests'}),
                         ('start', {'milestone': 'build'})):
            r = self.p.apply(r, op, args, 10.0)
        names = ['Read consistency', 'Grocery tools', 'Provider cancellation', 'Photo replacement race',
                 'Storage provenance', 'Shutdown errors surface', 'Full suite green']
        for i, name in enumerate(names):
            r = self.p.apply(r, 'task', {'milestone': 'build', 'task': f't{i}', 'name': name}, 20.0)
        for i in range(3):
            r = self.p.apply(r, 'finish-task', {'task': f't{i}'}, 30.0)
        r = self.p.apply(r, 'work', {'task': 't3', 'who': 'Bruga'}, 40.0)
        self.r = r

    def render(self, record=None, cols=60):
        return self.p.render_text(record or self.r, width=cols, color=False, now=760.0)

    def test_render_working_state_snapshot(self):
        out = self.render()
        self.assertIn('MCP agent access', out)
        self.assertIn('2 of 6', out)
        self.assertIn('camp-planner · feature/mcp', out)
        self.assertIn('NOW', out)
        self.assertIn('Build', out)
        self.assertIn('3 of 7', out)
        self.assertIn('✓ Read consistency', out)
        self.assertIn('Photo replacement race', out)
        self.assertIn('Bruga 12m', out)
        self.assertIn('○ 3 more', out)
        self.assertIn('⚑', out)
        self.assertIn("You're needed after PR", out)
        self.assertIn('↻', out)
        self.assertNotIn('PASS', out)
        self.assertNotIn('\x1b[', out)

    def test_render_loop_state_shows_pass_and_why(self):
        r = self.p.apply(self.r, 'loop', {'milestone': 'build', 'why': 'security review found a stale read'}, 50.0)
        out = self.render(r)
        self.assertIn('NOW · PASS 2 OF BUILD', out)
        self.assertIn('Why: security review found a stale read', out)
        self.assertIn('Expected', out)
        self.assertIn('↻2', out)
        over = self.p.apply(r, 'loop', {'milestone': 'build', 'why': 'again'}, 60.0)
        over = self.p.apply(over, 'loop', {'milestone': 'build', 'why': 'and again'}, 70.0)
        self.assertIn('beyond the planned 2 passes', self.render(over))

    def test_render_your_turn_takes_over_card(self):
        r = self.p.apply(self.r, 'wait', {'need': 'Open the PR with hosted checks pending?'}, 400.0)
        out = self.render(r)
        self.assertIn('YOUR TURN', out)
        self.assertIn('Open the PR with hosted checks pending?', out)
        self.assertIn('Answer in the chat', out)
        self.assertIn('waiting 6m · unplanned', out)
        self.assertNotIn('Photo replacement race', out)

    def test_render_color_uses_one_color_per_state(self):
        out = self.p.render_text(self.r, width=60, color=True, now=760.0)
        self.assertIn(self.p.COLORS['done'], out)
        self.assertIn(self.p.COLORS['now'], out)
        r = self.p.apply(self.r, 'wait', {'waypoint': 'accept'}, 400.0)
        self.assertIn(self.p.COLORS['you'], self.p.render_text(r, width=60, color=True, now=760.0))

    def test_render_narrow_width_box_aligned(self):
        for cols in (30, 40, 60, 100):
            lines = self.render(cols=cols).splitlines()
            self.assertTrue(all(width(l) <= cols for l in lines), (cols, [l for l in lines if width(l) > cols]))
            card = [l for l in lines if l and l[0] in '╭│╰']
            self.assertGreaterEqual(len(card), 3)
            self.assertEqual(len({width(l) for l in card}), 1, (cols, card))
            self.assertTrue(all(l.endswith(('╮', '│', '╯')) for l in card), card)

    def test_journey_spans_the_width_and_footer_wraps(self):
        for cols in (46, 60, 90):
            lines = self.render(cols=cols).splitlines()
            path = next(l for l in lines if '◉' in l)
            self.assertGreaterEqual(len(path), cols - 6, (cols, path))  # last label owns the tail
            self.assertTrue(all(len(l) <= cols for l in lines))
        out = self.render(cols=46)
        self.assertIn('Muse/Dots acceptance', out)
        self.assertNotIn('…', '\n'.join(l for l in out.splitlines() if l.startswith(('⚑', '↻', '  '))))

    def test_render_completed_quest(self):
        r = self.p.apply(self.r, 'close', {'status': 'completed'}, 900.0)
        out = self.render(r)
        self.assertIn('DONE', out)

    def test_render_corrupt_record_is_calm(self):
        for bad in ({}, {'schema_version': 1}, {'schema_version': 1, 'milestones': 'x'}, [], 'x'):
            out = self.p.render_safe(bad, width=40, color=False, now=0.0)
            self.assertIn('No progress', out)
        self.assertIn('No progress', self.p.render_missing(40))

    def test_html_has_timeline_tasks_and_waypoints(self):
        page = self.p.render_html(self.r, now=760.0)
        self.assertTrue(page.startswith('<!doctype html>'))
        for text in ('MCP agent access', 'Milestones', 'Where you come in', 'Approve mode and scope',
                     'Muse/Dots acceptance', 'Full suite green', 'Photo replacement race', '3 of 7'):
            self.assertIn(text, page)
        self.assertIn('prefers-color-scheme', page)

    def test_html_loop_pass_is_violet_and_empty_task_list_reads_plainly(self):
        r = self.p.apply(self.r, 'loop', {'milestone': 'build', 'why': 'review found a race'}, 50.0)
        page = self.p.render_html(r, now=760.0)
        self.assertIn('class="st current loop"', page)
        self.assertIn('class="d current loop"', page)
        self.assertIn('No tasks recorded yet', page)
        self.assertNotIn('0 of 0 tasks', page)

    def test_hostile_record_states_never_reach_html_attributes(self):
        r = json.loads(json.dumps(self.r))
        r['milestones'][0]['state'] = 'done" onmouseover="alert(1)'
        r['waypoints'][0]['state'] = 'x"><script>alert(2)</script>'
        page = self.p.render_html(r, now=760.0)
        self.assertNotIn('onmouseover', page)
        self.assertNotIn('<script>alert', page)

    def test_control_characters_never_reach_the_terminal(self):
        r = json.loads(json.dumps(self.r))
        r['title'] = 'Evil\x1b]0;pwned\x07\x1b[2J title'
        r['tasks'][3]['name'] = 'Task\x9b31m red'
        r['note'] = 'bell\x07'
        out = self.p.render_safe(r, width=60, color=True, now=760.0)
        stripped = out
        for code in self.p.COLORS.values():
            stripped = stripped.replace(code, '')
        self.assertFalse(any(ord(ch) < 32 and ch != '\n' or 0x7f <= ord(ch) < 0xa0 for ch in stripped), repr(stripped))
        with self.assertRaises(self.p.Refusal):
            self.p.apply(self.r, 'note', {'text': 'hi\x1b[2J'}, 1.0)

    def partials(self):
        def drop(path, key):
            r = json.loads(json.dumps(self.r))
            target = r
            for part in path:
                target = target[part]
            del target[key]
            return r
        def setv(path, key, value):
            r = json.loads(json.dumps(self.r))
            target = r
            for part in path:
                target = target[part]
            target[key] = value
            return r
        return [drop(['waypoints', 1], 'after'), drop(['milestones', 0], 'name'), drop(['waypoints', 0], 'need'),
                setv(['milestones', 2], 'pass', 'two'), setv(['milestones', 2], 'started_at', 'noon'),
                drop(['milestones', 0], 'pass'), drop([], 'status'), setv([], 'loops', [None]),
                setv(['milestones', 2], 'goal', {'x': 1}), setv([], 'note', ['x'])]

    def test_partial_records_are_calm_in_every_view(self):
        for bad in self.partials():
            self.assertIn('No progress', self.p.render_safe(bad, width=40, color=False, now=0.0))
            self.assertIn('No progress', self.p.render_html(bad, now=0.0))
            with self.assertRaises(self.p.Refusal):
                self.p.validate(bad)

    def test_close_resolves_waiting_and_status_wins(self):
        r = self.p.apply(self.r, 'wait', {'waypoint': 'accept'}, 100.0)
        closed = self.p.apply(r, 'close', {'status': 'completed'}, 200.0)
        self.assertEqual(closed['waypoints'][1]['state'], 'done')
        self.assertEqual(self.p.focus(closed, 300.0)['kind'], 'done')
        hand_edited = json.loads(json.dumps(r))
        hand_edited['status'] = 'abandoned'
        self.assertEqual(self.p.focus(hand_edited, 300.0)['label'], 'ABANDONED')

    def test_loop_back_leaves_the_interrupted_milestone_unfinished(self):
        r = self.p.apply(self.r, 'start', {'milestone': 'review'}, 100.0)
        r = self.p.apply(r, 'loop', {'milestone': 'build', 'why': 'blocking review finding'}, 200.0)
        states = {m['id']: m['state'] for m in r['milestones']}
        self.assertEqual((states['build'], states['review']), ('current', 'upcoming'))
        r = self.p.apply(r, 'start', {'milestone': 'review'}, 300.0)
        self.assertEqual({m['id']: m['state'] for m in r['milestones']}['build'], 'done')

    def test_html_escapes_record_text(self):
        r = self.p.apply(self.r, 'note', {'text': '<script>alert(1)</script>'}, 50.0)
        r = self.p.apply(r, 'task', {'milestone': 'build', 'task': 'x', 'name': '<img src=x>'}, 50.0)
        page = self.p.render_html(r, now=760.0)
        self.assertNotIn('<script>alert', page)
        self.assertNotIn('<img src=x>', page)


class WatchTests(Project, unittest.TestCase):
    def test_watch_once_prints_frame(self):
        self.init()
        self.run_cli('start', 'build')
        result = self.run_cli('watch', '--once', '--width', '50')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('MCP agent access', result.stdout)
        self.assertIn('NOW', result.stdout)

    def test_watch_without_plan_finds_newest_active_quest(self):
        self.init()
        result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root), 'watch', '--once'],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('MCP agent access', result.stdout)

    def test_watch_once_missing_record_is_calm(self):
        result = self.run_cli('watch', '--once')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('No progress', result.stdout)

    def test_web_serves_calm_page_for_partial_record(self):
        import threading
        import urllib.request
        self.init()
        record = self.record()
        del record['waypoints'][0]['after']
        (self.root / RECORD).write_text(json.dumps(record))
        server = load_module().make_server(self.root, PLAN, port=0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f'http://127.0.0.1:{server.server_address[1]}'
        for path in ('/', '/fragment'):
            body = urllib.request.urlopen(base + path, timeout=10).read().decode()
            self.assertIn('No progress', body)

    def test_web_serves_page_and_fragment(self):
        import threading
        import urllib.request
        self.init()
        p = load_module()
        server = p.make_server(self.root, PLAN, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f'http://127.0.0.1:{server.server_address[1]}'
        page = urllib.request.urlopen(base + '/', timeout=10).read().decode()
        fragment = urllib.request.urlopen(base + '/fragment', timeout=10).read().decode()
        self.assertIn('MCP agent access', page)
        self.assertIn('/fragment', page)
        self.assertIn('MCP agent access', fragment)
        self.assertNotIn('<html', fragment)
        with self.assertRaises(urllib.error.HTTPError):
            urllib.request.urlopen(base + '/../../etc/passwd', timeout=10)
        self.assertEqual(server.server_address[0], '127.0.0.1')
        rebound = urllib.request.Request(base + '/', headers={'Host': 'attacker.example'})
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(rebound, timeout=10)
        self.assertEqual(caught.exception.code, 421)
        local = urllib.request.Request(base + '/fragment', headers={'Host': f'localhost:{server.server_address[1]}'})
        self.assertEqual(urllib.request.urlopen(local, timeout=10).status, 200)



class InstructionTests(unittest.TestCase):
    """Mordain on both hosts is told to seed and keep the record; the bundle ships the helper."""

    def test_bundle_ships_helper(self):
        bundled = ROOT / 'plugin/skills/guildhall-quest/scripts/progress.py'
        self.assertEqual(bundled.read_bytes(), SCRIPT.read_bytes())

    def test_quest_instructions_name_helper(self):
        for rel in ('plugin/commands/quest.md', 'plugin/portable/references/quest.md'):
            text = (ROOT / rel).read_text()
            for needle in ('progress.py', 'progress.json', 'init', 'wait', 'loop', 'never blocks', 'keep updating',
                           'Plan → Reproduce → Root cause → Report', 'Plan → Spike → Show'):
                self.assertIn(needle, text, f'{rel}: {needle}')

    def test_write_scope_exception_is_narrow_and_consistent(self):
        for rel in ('plugin/commands/quest.md', 'plugin/portable/SKILL.md',
                    'plugin/portable/references/collaborative-planning.md'):
            text = (ROOT / rel).read_text()
            self.assertIn('progress.py', text, rel)
            self.assertRegex(text, r'only (through|via) `?progress\.py`?', rel)

    def test_versions_bumped_together(self):
        versions = {json.loads((ROOT / rel).read_text())['version'] for rel in
                    ('plugin/plugin.json', 'plugin/.codex-plugin/plugin.json', 'plugin/.claude-plugin/plugin.json')}
        self.assertEqual(versions, {'0.20.0'})
        tavern = json.loads((ROOT / 'mods/guildhall-tavern/.claude-plugin/plugin.json').read_text())
        self.assertEqual(tavern['version'], '0.4.0')


if __name__ == '__main__':
    unittest.main()
