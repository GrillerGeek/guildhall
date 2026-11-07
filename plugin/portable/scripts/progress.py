#!/usr/bin/env python3
"""Quest progress record: milestones, tasks, declared loops and user waypoints.

Python 3.12+, standard library only. Mordain updates the record with short
commands; terminal and browser views read it. The record lives beside the plan
at docs/guildhall/plans/<slug>/progress.json and holds no source or evidence.
Exit codes: 0 ok, 2 refusal (one line on stderr), 4 I/O failure.
"""
from __future__ import annotations
import argparse
import contextlib
import copy
import fcntl
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import time

SCHEMA_VERSION = 1
PLAN_DIR = ('docs', 'guildhall', 'plans')
ID = re.compile(r'^[a-z0-9][a-z0-9_-]{0,47}$')
TEXT_LIMIT = 300
STATUSES = ('active', 'completed', 'abandoned')


class Refusal(Exception):
    """A request the helper will not apply; the record is left unchanged."""


def require(condition, message):
    if not condition:
        raise Refusal(message)


def text(value, field, limit=TEXT_LIMIT, empty=False):
    require(isinstance(value, str), f'{field} must be text')
    value = ' '.join(value.split())
    require(empty or value, f'{field} must not be empty')
    return value[:limit]


def ident(value, field):
    require(isinstance(value, str) and ID.match(value), f'{field} must be a short lowercase id (a-z, 0-9, - or _): {value!r}')
    return value


# ---------------------------------------------------------------- paths

def record_path(root: Path, plan: str) -> Path:
    """The record beside the plan; refuses anything but a relative plans/*.md path."""
    require(isinstance(plan, str) and plan, 'plan path required')
    pure = PurePosixPath(plan.replace('\\', '/'))
    require(not pure.is_absolute(), f'plan path must be relative to the project: {plan}')
    require('..' not in pure.parts and '.' not in pure.parts, f'plan path must not leave the plans folder: {plan}')
    require(pure.parts[:3] == PLAN_DIR and len(pure.parts) == 4, f'plan must be docs/guildhall/plans/<name>.md: {plan}')
    require(pure.suffix == '.md' and pure.name.lower() != 'readme.md', f'plan must be a plan .md file: {plan}')
    return Path(root) / Path(*pure.parts[:-1]) / pure.stem / 'progress.json'


# ---------------------------------------------------------------- record

def _milestone(spec, index):
    require(isinstance(spec, dict), f'milestone {index} must be an object')
    loop = spec.get('loop')
    if loop is not None:
        require(isinstance(loop, dict), 'loop must be an object with reason and limit')
        limit = loop.get('limit')
        require(isinstance(limit, int) and not isinstance(limit, bool) and 1 <= limit <= 9, 'loop limit must be 1-9 passes')
        loop = {'reason': text(loop.get('reason'), 'loop reason'), 'limit': limit}
    return {
        'id': ident(spec.get('id'), 'milestone id'),
        'name': text(spec.get('name'), 'milestone name', 40),
        'goal': text(spec.get('goal', ''), 'milestone goal', empty=True),
        'state': 'upcoming', 'loop': loop, 'pass': 0,
        'started_at': None, 'finished_at': None, 'added_because': None, 'skipped_why': None,
    }


def _waypoint(spec, milestone_ids, planned=True):
    require(isinstance(spec, dict), 'waypoint must be an object')
    after = ident(spec.get('after'), 'waypoint after')
    require(after in milestone_ids, f'waypoint follows an unknown milestone: {after}')
    return {'id': ident(spec.get('id'), 'waypoint id'), 'need': text(spec.get('need'), 'waypoint need'),
            'after': after, 'state': 'upcoming', 'planned': planned, 'waiting_since': None, 'done_at': None}


def init_record(title, plan, milestones, waypoints, repo='', branch='', host='', now=None) -> dict:
    now = time.time() if now is None else now
    require(isinstance(milestones, list) and milestones, 'at least one milestone required')
    require(isinstance(waypoints, list), 'waypoints must be a list')
    ms = [_milestone(m, i) for i, m in enumerate(milestones)]
    ids = [m['id'] for m in ms]
    require(len(set(ids)) == len(ids), 'milestone ids must be unique')
    wps = [_waypoint(w, ids) for w in waypoints]
    require(len({w['id'] for w in wps}) == len(wps), 'waypoint ids must be unique')
    return {
        'schema_version': SCHEMA_VERSION, 'title': text(title, 'title', 120),
        'repo': text(repo, 'repo', 80, True), 'branch': text(branch, 'branch', 120, True),
        'host': text(host, 'host', 40, True), 'plan_path': plan, 'status': 'active', 'note': '',
        'started_at': now, 'updated_at': now,
        'milestones': ms, 'tasks': [], 'waypoints': wps, 'loops': [],
    }


def _find(items, key, kind):
    for item in items:
        if item['id'] == key:
            return item
    raise Refusal(f'unknown {kind}: {key}')


def _current(record):
    return next((m for m in record['milestones'] if m['state'] == 'current'), None)


def _make_current(record, m, now):
    for other in record['milestones']:
        if other is not m and other['state'] == 'current':
            other['state'] = 'done' if other['pass'] >= 1 else 'upcoming'
            other['finished_at'] = now if other['state'] == 'done' else other['finished_at']
    m['state'] = 'current'
    m['pass'] = max(1, m['pass'])
    m['started_at'] = m['started_at'] or now
    m['finished_at'] = None


def apply(record: dict, op: str, args: dict, now: float) -> dict:
    """Return a new record with `op` applied; raise Refusal and leave `record` untouched otherwise."""
    r = copy.deepcopy(record)
    ms, tasks, wps = r['milestones'], r['tasks'], r['waypoints']
    get = args.get
    if op == 'start':
        m = _find(ms, get('milestone'), 'milestone')
        require(m['state'] in ('upcoming', 'current'), f"{m['id']} is {m['state']}; use loop to repeat a milestone")
        _make_current(r, m, now)
    elif op == 'done':
        m = _find(ms, get('milestone'), 'milestone')
        require(m['state'] != 'skipped', f"{m['id']} was skipped")
        m['state'], m['pass'] = 'done', max(1, m['pass'])
        m['started_at'] = m['started_at'] or now
        m['finished_at'] = now
    elif op == 'skip':
        m = _find(ms, get('milestone'), 'milestone')
        require(m['state'] == 'upcoming', f"{m['id']} is {m['state']}; only upcoming milestones can be skipped")
        m['state'], m['skipped_why'] = 'skipped', text(get('why'), 'why')
    elif op == 'add-milestone':
        new_id = ident(get('milestone'), 'milestone id')
        require(all(m['id'] != new_id for m in ms), f'milestone already exists: {new_id}')
        after = _find(ms, get('after'), 'milestone')
        m = _milestone({'id': new_id, 'name': get('name'), 'goal': get('goal') or ''}, len(ms))
        m['added_because'] = text(get('because'), 'because')
        ms.insert(ms.index(after) + 1, m)
    elif op == 'loop':
        m = _find(ms, get('milestone'), 'milestone')
        require(m['pass'] >= 1, f"{m['id']} has not started; start it instead of looping")
        _make_current(r, m, now)
        m['pass'] += 1
        limit = (m['loop'] or {}).get('limit')
        r['loops'].append({'milestone': m['id'], 'pass': m['pass'], 'why': text(get('why'), 'why'),
                           'at': now, 'within_limit': limit is not None and m['pass'] <= limit})
    elif op == 'task':
        m = _find(ms, get('milestone'), 'milestone')
        task_id = ident(get('task'), 'task id')
        require(all(t['id'] != task_id for t in tasks), f'task already exists: {task_id}')
        tasks.append({'id': task_id, 'milestone': m['id'], 'pass': max(1, m['pass']),
                      'name': text(get('name'), 'task name', 80), 'state': 'upcoming',
                      'who': text(get('who') or '', 'who', 40, True) or None,
                      'added_because': text(get('because') or '', 'because', empty=True) or None,
                      'started_at': None, 'finished_at': None})
    elif op == 'work':
        t = _find(tasks, get('task'), 'task')
        t['state'], t['started_at'] = 'working', t['started_at'] or now
        if get('who'):
            t['who'] = text(get('who'), 'who', 40)
    elif op == 'finish-task':
        t = _find(tasks, get('task'), 'task')
        t['state'], t['finished_at'] = 'done', now
        t['started_at'] = t['started_at'] or now
    elif op == 'wait':
        if get('need'):
            current = _current(r) or next((m for m in reversed(ms) if m['state'] == 'done'), ms[0])
            w = _waypoint({'id': f'ask-{sum(not w["planned"] for w in wps) + 1}', 'need': get('need'),
                           'after': current['id']}, [m['id'] for m in ms], planned=False)
            wps.append(w)
        else:
            w = _find(wps, get('waypoint'), 'waypoint')
        w['state'], w['waiting_since'] = 'waiting', now
    elif op == 'resume':
        w = _find(wps, get('waypoint'), 'waypoint')
        w['state'], w['done_at'] = 'done', now
    elif op == 'note':
        r['note'] = text(get('text') or '', 'note', 160, True)
    elif op == 'close':
        status = get('status') or 'completed'
        require(status in STATUSES[1:], f'status must be completed or abandoned: {status}')
        r['status'] = status
        current = _current(r)
        if current and status == 'completed':
            current['state'], current['finished_at'] = 'done', now
    else:
        raise Refusal(f'unknown operation: {op}')
    r['updated_at'] = now
    return r


def validate(record) -> dict:
    """Light shape check for records read from disk; views treat failure as 'no record'."""
    require(isinstance(record, dict) and record.get('schema_version') == SCHEMA_VERSION, 'not a progress record')
    for key in ('milestones', 'tasks', 'waypoints', 'loops'):
        require(isinstance(record.get(key), list), f'progress record lacks {key}')
    require(record['milestones'] and all(isinstance(m, dict) and 'id' in m and 'state' in m for m in record['milestones']),
            'progress record has malformed milestones')
    return record


# ---------------------------------------------------------------- storage

def load(path: Path) -> dict:
    try:
        raw = Path(path).read_text(encoding='utf-8')
    except FileNotFoundError:
        raise Refusal(f'no progress record yet at {path}; run init first') from None
    try:
        return validate(json.loads(raw))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise Refusal(f'progress record is not valid JSON: {path}') from None


def save(path: Path, record: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(record, indent=2, ensure_ascii=False) + '\n'
    fd, temp = tempfile.mkstemp(prefix='.progress-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temp)
        raise


@contextlib.contextmanager
def locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path.with_name(path.name + '.lock'), 'a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


# ---------------------------------------------------------------- CLI

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='progress.py', description='Quest progress record for Guildhall quests.')
    p.add_argument('--root', default='.', help='project root (default: current directory)')
    p.add_argument('--plan', required=True, help='plan path, docs/guildhall/plans/<name>.md')
    sub = p.add_subparsers(dest='op', required=True)
    s = sub.add_parser('init', help='create the record from a skeleton')
    s.add_argument('--title', required=True)
    s.add_argument('--repo', default='')
    s.add_argument('--branch', default='')
    s.add_argument('--host', default='')
    s.add_argument('--skeleton-json', required=True, help='file path, or - for stdin')
    s.add_argument('--force', action='store_true', help='replace an existing record')
    for name in ('start', 'done'):
        sub.add_parser(name).add_argument('milestone')
    s = sub.add_parser('skip')
    s.add_argument('milestone')
    s.add_argument('--why', required=True)
    s = sub.add_parser('add-milestone')
    s.add_argument('milestone')
    s.add_argument('name')
    s.add_argument('--goal', default='')
    s.add_argument('--after', required=True)
    s.add_argument('--because', required=True)
    s = sub.add_parser('loop')
    s.add_argument('milestone')
    s.add_argument('--why', required=True)
    s = sub.add_parser('task')
    s.add_argument('milestone')
    s.add_argument('task')
    s.add_argument('name')
    s.add_argument('--who', default='')
    s.add_argument('--because', default='')
    s = sub.add_parser('work')
    s.add_argument('task')
    s.add_argument('--who', default='')
    sub.add_parser('finish-task').add_argument('task')
    s = sub.add_parser('wait')
    group = s.add_mutually_exclusive_group(required=True)
    group.add_argument('waypoint', nargs='?')
    group.add_argument('--unplanned', dest='need')
    sub.add_parser('resume').add_argument('waypoint')
    sub.add_parser('note').add_argument('text')
    sub.add_parser('close').add_argument('--status', default='completed', choices=STATUSES[1:])
    return p


def run(argv) -> int:
    args = parser().parse_args(argv)
    root = Path(args.root).resolve()
    path = record_path(root, args.plan)
    op = args.op
    if op == 'init':
        source = sys.stdin.read() if args.skeleton_json == '-' else Path(args.skeleton_json).read_text()
        try:
            skeleton = json.loads(source)
        except json.JSONDecodeError:
            raise Refusal('skeleton is not valid JSON') from None
        require(isinstance(skeleton, dict), 'skeleton must be an object with milestones and waypoints')
        record = init_record(args.title, args.plan, skeleton.get('milestones'), skeleton.get('waypoints', []),
                             args.repo, args.branch, args.host)
        with locked(path):
            require(args.force or not path.exists(), f'progress record already exists: {path} (use --force to replace)')
            save(path, record)
        return 0
    values = {k: v for k, v in vars(args).items() if k not in ('root', 'plan', 'op')}
    with locked(path):
        save(path, apply(load(path), op, values, time.time()))
    return 0


def main(argv=None) -> int:
    try:
        return run(sys.argv[1:] if argv is None else argv)
    except Refusal as error:
        print(f'progress: {error}', file=sys.stderr)
        return 2
    except OSError as error:
        print(f'progress: could not read or write the record ({type(error).__name__})', file=sys.stderr)
        return 4


if __name__ == '__main__':
    sys.exit(main())
