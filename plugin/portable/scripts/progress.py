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


def no_symlinks(root: Path, path: Path) -> None:
    """Refuse a record reached through a symbolic link anywhere below the project root."""
    probe = Path(path)
    while probe != root and root in probe.parents:
        require(not probe.is_symlink(), f'progress record path passes through a symbolic link: {probe}')
        probe = probe.parent


@contextlib.contextmanager
def locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path.with_name(path.name + '.lock'), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


# ---------------------------------------------------------------- views

COLORS = {'done': '\x1b[38;5;78m', 'now': '\x1b[38;5;75m', 'loop': '\x1b[38;5;141m',
          'you': '\x1b[38;5;214m', 'dim': '\x1b[38;5;244m', 'bold': '\x1b[1m', 'reset': '\x1b[0m'}
SPINNER = '◐◓◑◒'
MISSING = 'No progress record yet. It appears once a quest writes its plan.'


def elapsed(seconds) -> str:
    s = max(0, int(seconds or 0))
    if s < 60:
        return f'{s}s'
    if s < 3600:
        return f'{s // 60}m'
    if s < 86400:
        return f'{s // 3600}h {s % 3600 // 60}m'
    return f'{s // 86400}d {s % 86400 // 3600}h'


def counted(record):
    live = [m for m in record['milestones'] if m['state'] != 'skipped']
    return sum(m['state'] == 'done' for m in live), len(live)


def journey(record) -> list[dict]:
    """Nodes left to right: live milestones, each followed by an open user waypoint if one waits there."""
    nodes = []
    for m in record['milestones']:
        if m['state'] == 'skipped':
            continue
        badge = ''
        if m.get('pass', 0) >= 2:
            badge = f"↻{m['pass']}"
        elif m.get('loop'):
            badge = '↻'
        nodes.append({'kind': 'milestone', 'label': m['name'], 'state': m['state'], 'badge': badge,
                      'repeat': m['state'] == 'current' and m.get('pass', 0) >= 2})
        open_here = [w for w in record['waypoints'] if w['after'] == m['id'] and w['state'] != 'done']
        if open_here:
            waiting = any(w['state'] == 'waiting' for w in open_here)
            nodes.append({'kind': 'waypoint', 'label': 'You', 'state': 'waiting' if waiting else 'upcoming', 'badge': ''})
    return nodes


def focus(record, now) -> dict:
    """What the card says: your turn wins, then the current milestone (a loop pass says why), then next or done."""
    waiting = [w for w in record['waypoints'] if w['state'] == 'waiting']
    if waiting:
        w = max(waiting, key=lambda x: x.get('waiting_since') or 0)
        return {'kind': 'you', 'label': 'YOUR TURN', 'title': w['need'],
                'lines': ['Mordain is waiting for your answer.'], 'cta': 'Answer in the chat',
                'meta': f"waiting {elapsed(now - (w.get('waiting_since') or now))} · {'planned' if w['planned'] else 'unplanned'}"}
    current = next((m for m in record['milestones'] if m['state'] == 'current'), None)
    if record.get('status') != 'active' or (current is None and all(m['state'] in ('done', 'skipped') for m in record['milestones'])):
        status = record.get('status')
        return {'kind': 'done', 'label': 'ABANDONED' if status == 'abandoned' else 'DONE',
                'title': 'Quest abandoned' if status == 'abandoned' else 'Quest complete', 'lines': [], 'tasks': []}
    if current is None:
        nxt = next((m for m in record['milestones'] if m['state'] == 'upcoming'), record['milestones'][0])
        return {'kind': 'next', 'label': 'UP NEXT', 'title': nxt['name'], 'goal': nxt.get('goal', ''), 'lines': [], 'tasks': []}
    tasks = [t for t in record['tasks'] if t['milestone'] == current['id'] and t.get('pass') == current['pass']]
    card = {'kind': 'now', 'label': 'NOW', 'title': current['name'], 'goal': current.get('goal', ''),
            'tasks': tasks, 'done': sum(t['state'] == 'done' for t in tasks), 'total': len(tasks), 'lines': [],
            'milestone_elapsed': elapsed(now - (current.get('started_at') or now))}
    if current['pass'] >= 2:
        loop = next((l for l in reversed(record['loops']) if l['milestone'] == current['id']), None)
        limit = (current.get('loop') or {}).get('limit')
        card['kind'], card['label'] = 'loop', f"NOW · PASS {current['pass']} OF {current['name'].upper()}"
        if loop:
            card['lines'].append(f"Why: {loop['why']}")
        if limit is None:
            card['lines'].append('Not a planned repeat.')
        elif current['pass'] <= limit:
            card['lines'].append(f"Expected — {current['name']} allows {limit} passes.")
        else:
            card['lines'].append(f'This is beyond the planned {limit} passes.')
    return card


def footer(record) -> list[tuple[str, str]]:
    rows = []
    names = {m['id']: m['name'] for m in record['milestones']}
    ahead = [w for w in record['waypoints'] if w['state'] == 'upcoming']
    if ahead:
        first = ahead[0]
        later = f' · {len(ahead)} checks' if len(ahead) > 1 else ''
        rows.append(('you', f"⚑ You're needed after {names.get(first['after'], first['after'])}{later}"))
        rows.append(('dim', f"  {first['need']}"))
    repeat = [m for m in record['milestones'] if m.get('loop') and m['state'] in ('upcoming', 'current')]
    if repeat:
        who = ', '.join(m['name'] for m in repeat[:-1]) + (' and ' if len(repeat) > 1 else '') + repeat[-1]['name']
        limits = {m['loop']['limit'] for m in repeat}
        cap = f" · up to {limits.pop()} passes" if len(limits) == 1 else ''
        rows.append(('dim', f'↻ {who} may repeat{cap}'))
    if record.get('note'):
        rows.append(('dim', record['note']))
    return rows


def clip(value: str, width: int) -> str:
    return value if len(value) <= width else value[:max(0, width - 1)] + '…'


def _journey_rows(nodes, width):
    glyph = {'done': '●', 'current': '◉', 'upcoming': '○', 'waiting': '⚑'}
    for label_len in (12, 6, 4, 3, 0):
        cells = [max(2, min(len(n['label']), label_len) + 1, len(n['badge']) + 1) for n in nodes]
        if sum(cells) + 1 <= width or label_len == 0:
            break
    if sum(cells) + 1 > width:  # still too wide: show a window that keeps the current node in view
        keep = max(1, (width - 1) // 2)
        cur = next((i for i, n in enumerate(nodes) if n['state'] in ('current', 'waiting')), 0)
        start = max(0, min(cur - keep // 2, len(nodes) - keep))
        nodes, cells = nodes[start:start + keep], [2] * min(keep, len(nodes))
    spare = width - 1 - sum(cells)
    if spare > 0 and len(cells) > 1:  # spread the path across the pane, leftover to the earliest gaps
        gaps = len(cells) - 1
        cells = [w + spare // gaps + (1 if i < spare % gaps else 0) if i < gaps else w for i, w in enumerate(cells)]
    path, labels, badges = [' '], [' '], [' ']
    for i, (n, w) in enumerate(zip(nodes, cells)):
        g = '⚑' if n['kind'] == 'waypoint' else glyph.get(n['state'], '○')
        state = 'you' if n['kind'] == 'waypoint' else {'done': 'done', 'current': 'now'}.get(n['state'], 'dim')
        last = i == len(nodes) - 1
        link = '' if last else ('━' if n['state'] == 'done' and n['kind'] == 'milestone' else '┈') * (w - 1)
        path.append((state, g))
        path.append(('done' if link.startswith('━') else 'dim', link))
        labels.append((state, clip(n['label'], w - 1).ljust(w) if label_len else ' ' * w))
        badges.append(('loop', n['badge'].ljust(w)))
    return path, labels, badges


def render_text(record, width=60, color=False, now=None, frame=0) -> str:
    now = time.time() if now is None else now
    width = max(24, int(width))
    paint = (lambda tone, s: f"{COLORS[tone]}{s}{COLORS['reset']}" if s and tone in COLORS else s) if color else (lambda tone, s: s)
    out = []

    def line(*parts):  # parts: (tone, text) or str; clipped to width
        room, pieces = width, []
        for part in parts:
            tone, s = part if isinstance(part, tuple) else ('', part)
            s = clip(s, room) if len(s) > room else s
            room -= len(s)
            pieces.append(paint(tone, s))
            if room <= 0:
                break
        out.append(''.join(pieces).rstrip() if not color else ''.join(pieces))

    done, total = counted(record)
    count = f'{done} of {total}'
    title = clip(record['title'], width - len(count) - 2)
    line(('bold', title), ' ' * (width - len(title) - len(count)), ('dim', count))
    where = ' · '.join(x for x in (record.get('repo'), record.get('branch')) if x)
    line(('dim', ' · '.join(x for x in (where, elapsed(now - record.get('started_at', now))) if x)))
    out.append('')
    for row in _journey_rows(journey(record), width):
        line(*[p for p in row if isinstance(p, tuple)], *[])
    out.append('')

    card = focus(record, now)
    tone = {'now': 'now', 'loop': 'loop', 'you': 'you', 'done': 'done', 'next': 'dim'}[card['kind']]
    inner = width - 4
    body = []
    if card['kind'] == 'you':
        body += [('bold', card['title']), '', *card['lines'], '', ('you', '→ ' + card['cta']), ('dim', card['meta'])]
    else:
        heading = card['title'] + (f"  {card.get('goal')}" if card.get('goal') else '')
        body.append(('bold', heading))
        for extra in card['lines']:
            body.append(('loop' if extra.startswith('Why') else 'dim', extra))
        if card['kind'] in ('now', 'loop'):
            body.append('')
            if card['total']:
                bar_w = max(4, min(20, inner - 14))
                filled = round(bar_w * card['done'] / card['total'])
                body.append([(tone, '▰' * filled), ('dim', '▱' * (bar_w - filled)), f"  {card['done']} of {card['total']} tasks"])
                shown = card['tasks'][:5] if len(card['tasks']) <= 5 else card['tasks'][:4]
                for t in shown:
                    if t['state'] == 'done':
                        body.append([('done', '✓'), ' ' + t['name']])
                    elif t['state'] == 'working':
                        who = ' '.join(x for x in (t.get('who') or '', elapsed(now - (t.get('started_at') or now))) if x)
                        name = clip(t['name'], max(4, inner - len(who) - 4))
                        body.append([(tone, SPINNER[frame % 4]), ' ' + name, ' ' * max(1, inner - len(name) - len(who) - 2), ('dim', who)])
                    else:
                        body.append([('dim', '○ ' + t['name'])])
                if len(card['tasks']) > len(shown):
                    body.append(('dim', f"○ {len(card['tasks']) - len(shown)} more"))
            else:
                body.append(('dim', f"No tasks recorded yet · {card['milestone_elapsed']} so far"))
    label = f'─ {card["label"]} '
    out.append(paint(tone, '╭' + clip(label, width - 2).ljust(width - 2, '─') + '╮'))
    for row in body:
        parts = row if isinstance(row, list) else [row]
        parts = [p if isinstance(p, tuple) else ('', p) for p in parts]
        room, pieces = inner, []
        for t_, s in parts:
            s = clip(s, room)
            room -= len(s)
            pieces.append(paint(t_, s))
        out.append(paint(tone, '│') + ' ' + ''.join(pieces) + ' ' * room + ' ' + paint(tone, '│'))
    out.append(paint(tone, '╰' + '─' * (width - 2) + '╯'))
    import textwrap
    for t_, s in footer(record):
        for i, chunk in enumerate(textwrap.wrap(s, width, subsequent_indent='  ', break_on_hyphens=False) or ['']):
            line((t_, chunk))
    return '\n'.join(out)


def render_missing(width=60, reason=MISSING) -> str:
    return clip(reason, max(24, int(width)))


def render_safe(record, width=60, color=False, now=None, frame=0) -> str:
    try:
        return render_text(validate(record), width, color, now, frame)
    except (Refusal, KeyError, TypeError, ValueError, AttributeError, IndexError):
        return render_missing(width, 'No progress to show: the record could not be read.')


PAGE_CSS = """
:root{--bg:#f7f8fa;--panel:#fff;--line:#e3e7ee;--txt:#1d2430;--mut:#667085;--dim:#a0a8b5;--done:#1f9d63;--now:#2f7fe0;--loop:#8b5cf6;--you:#c27c0e;--track:#e6e9ef}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0e1117;--panel:#151a22;--line:#262e3a;--txt:#d6dce4;--mut:#8792a2;--dim:#4b5563;--done:#3fcf8e;--now:#5aa9ff;--loop:#b48cff;--you:#f5b041;--track:#2a3240}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Inter","Segoe UI",sans-serif}
main{max-width:1040px;margin:0 auto;padding:24px 16px}
.win{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden}
.head{display:flex;justify-content:space-between;align-items:center;gap:12px;border-bottom:1px solid var(--line);padding:16px 22px;flex-wrap:wrap}
.title{font-weight:650;font-size:17px}.sub{color:var(--mut);font-size:12.5px}
.chip{font-size:12px;padding:3px 10px;border-radius:20px;border:1px solid currentColor;white-space:nowrap}
.k-now{color:var(--now)}.k-loop{color:var(--loop)}.k-you{color:var(--you)}.k-done{color:var(--done)}.k-next{color:var(--mut)}
.pad{padding:18px 22px}
.jr{position:relative;display:flex;justify-content:space-between;margin:26px 14px 10px}
.jr::before{content:"";position:absolute;left:10px;right:10px;top:10px;height:3px;border-radius:3px;background:linear-gradient(90deg,var(--done) 0 var(--p),var(--track) var(--p) 100%)}
.st{position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;width:0}
.dot{width:22px;height:22px;border-radius:50%;display:grid;place-items:center;font-size:11px;font-weight:700;background:var(--panel);border:2px solid var(--line)}
.st.done .dot{background:var(--done);border-color:var(--done);color:#fff}
.st.current .dot{border:3px solid var(--now);box-shadow:0 0 0 6px color-mix(in srgb,var(--now) 18%,transparent)}
.st.current.loop .dot{border-color:var(--loop);box-shadow:0 0 0 6px color-mix(in srgb,var(--loop) 18%,transparent)}.st.current.loop .nm{color:var(--loop)}
.st.you .dot{border-color:var(--you);color:var(--you)}.st.you.waiting .dot{background:var(--you);color:#fff}
.nm{margin-top:7px;font-size:11.5px;color:var(--mut);white-space:nowrap}
.st.current .nm{color:var(--now);font-weight:600}.st.you .nm{color:var(--you)}
.lp{position:absolute;top:-18px;font-size:10.5px;color:var(--loop);white-space:nowrap}
.grid{display:grid;grid-template-columns:1.35fr 1fr;gap:20px;margin-top:10px;align-items:start}
@media (max-width:720px){.grid{grid-template-columns:1fr}.jr .nm{display:none}}
.card{border:1px solid currentColor;border-radius:12px;padding:16px;background:color-mix(in srgb,currentColor 6%,transparent)}
.card *{color:var(--txt)}.card .tag{color:inherit;font-size:10.5px;letter-spacing:.1em;font-weight:700}
.ct{font-size:17px;font-weight:650;margin:2px 0}.why{color:var(--loop)!important}
.bar{height:8px;border-radius:8px;background:var(--track);margin:14px 0 6px;overflow:hidden}.bar i{display:block;height:100%;border-radius:8px;background:currentColor}
.card .bar i{background:var(--now)}.k-loop .bar i{background:var(--loop)}
.bm{display:flex;justify-content:space-between;font-size:12px}.bm span{color:var(--mut)}
ul{list-style:none;margin:12px 0 0;padding:0}
.tasks li{display:flex;align-items:center;gap:10px;padding:6px 0;border-top:1px solid var(--line);font-size:13.5px}
.ck{width:16px;height:16px;border-radius:50%;flex:none;display:grid;place-items:center;font-size:10px;border:1.5px solid var(--line)}
.ck.ok{border:0;background:color-mix(in srgb,var(--done) 18%,transparent);color:var(--done)}
.ck.run{border:2px solid var(--line);border-top-color:var(--now);animation:sp 1s linear infinite}
@keyframes sp{to{transform:rotate(360deg)}}@media (prefers-reduced-motion:reduce){.ck.run{animation:none}}
.muted{color:var(--mut)!important}.who{margin-left:auto;font-size:11.5px;color:var(--mut);padding:2px 8px;border-radius:20px;background:color-mix(in srgb,var(--mut) 12%,transparent)}
h4{margin:0 0 10px;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--mut)}
.tl li{display:grid;grid-template-columns:14px 1fr auto;gap:10px;align-items:center;padding:6px 0;font-size:13.5px}
.d{width:10px;height:10px;border-radius:50%;border:2px solid var(--line)}.d.done{background:var(--done);border-color:var(--done)}.d.current{background:var(--now);border-color:var(--now)}
.d.current.loop{background:var(--loop);border-color:var(--loop)}.d.you{border-color:var(--you)}.d.waiting{background:var(--you);border-color:var(--you)}
.t{color:var(--mut);font-size:12px;font-variant-numeric:tabular-nums}
.pill{font-size:10.5px;padding:1px 7px;border-radius:20px;margin-left:6px;color:var(--loop);background:color-mix(in srgb,var(--loop) 14%,transparent)}
.youcard{border:1px solid color-mix(in srgb,var(--you) 40%,transparent);border-radius:12px;padding:14px;margin-top:16px;background:color-mix(in srgb,var(--you) 6%,transparent)}
.youcard h4{color:var(--you)}.skipped{text-decoration:line-through;color:var(--dim)}
.note{margin-top:14px;color:var(--mut);font-size:12.5px}
"""


def _e(value) -> str:
    import html
    return html.escape(str(value), quote=True)


def render_fragment(record, now=None) -> str:
    now = time.time() if now is None else now
    try:
        record = validate(record)
    except Refusal:
        return f'<main><div class="win pad">{_e(MISSING)}</div></main>'
    done, total = counted(record)
    card = focus(record, now)
    kind = card['kind']
    names = {m['id']: m['name'] for m in record['milestones']}
    nodes = journey(record)
    pct = 0 if len(nodes) < 2 else round(100 * max([i for i, n in enumerate(nodes) if n['state'] == 'done'] or [0]) / (len(nodes) - 1))
    chip = {'now': 'Working', 'loop': 'Repeating', 'you': 'Waiting on you', 'done': card['label'].title(), 'next': 'Up next'}[kind]
    where = ' · '.join(x for x in (record.get('repo'), record.get('branch')) if x)
    h = [f'<main><div class="win"><div class="head"><div><div class="title">{_e(record["title"])}</div>'
         f'<div class="sub">{_e(where)}{" · " if where else ""}running {_e(elapsed(now - record.get("started_at", now)))}</div></div>'
         f'<span class="chip k-{kind}">● {chip} · {done} of {total}</span></div><div class="pad">']
    h.append(f'<div class="jr" style="--p:{pct}%">')
    for n in nodes:
        cls = 'you ' + n['state'] if n['kind'] == 'waypoint' else n['state'] + (' loop' if n.get('repeat') else '')
        mark = '⚑' if n['kind'] == 'waypoint' else ('✓' if n['state'] == 'done' else '')
        badge = f'<div class="lp">{_e(n["badge"])}</div>' if n['badge'] else ''
        h.append(f'<div class="st {cls}">{badge}<div class="dot">{mark}</div><div class="nm">{_e(n["label"])}</div></div>')
    h.append('</div><div class="grid">')
    h.append(f'<section class="card k-{kind}" aria-live="polite"><div class="tag">{_e(card["label"])}</div>')
    if kind == 'you':
        h.append(f'<div class="ct">{_e(card["title"])}</div><div class="sub">{_e(card["lines"][0])}</div>'
                 f'<p><b>→ {_e(card["cta"])}</b></p><div class="sub">{_e(card["meta"])}</div>')
    else:
        h.append(f'<div class="ct">{_e(card["title"])}</div>')
        if card.get('goal'):
            h.append(f'<div class="sub">{_e(card["goal"])}</div>')
        for extra in card['lines']:
            h.append(f'<div class="sub{" why" if extra.startswith("Why") else ""}">{_e(extra)}</div>')
        if kind in ('now', 'loop'):
            if not card['total']:
                h.append(f'<p class="sub">No tasks recorded yet · {_e(card["milestone_elapsed"])} on this milestone</p>')
        if kind in ('now', 'loop') and card['total']:
            width_pct = round(100 * card['done'] / card['total'])
            h.append(f'<div class="bar"><i style="width:{width_pct}%"></i></div><div class="bm"><span>{card["done"]} of {card["total"]} tasks</span>'
                     f'<span>{_e(card["milestone_elapsed"])} on this milestone</span></div><ul class="tasks">')
            for t in card['tasks']:
                if t['state'] == 'done':
                    h.append(f'<li><span class="ck ok">✓</span>{_e(t["name"])}</li>')
                elif t['state'] == 'working':
                    who = ' · '.join(x for x in (t.get('who') or '', elapsed(now - (t.get('started_at') or now))) if x)
                    h.append(f'<li><span class="ck run"></span>{_e(t["name"])}<span class="who">{_e(who)}</span></li>')
                else:
                    because = f' <span class="muted">· {_e(t["added_because"])}</span>' if t.get('added_because') else ''
                    h.append(f'<li class="muted"><span class="ck"></span>{_e(t["name"])}{because}</li>')
            h.append('</ul>')
    h.append('</section><aside><h4>Milestones</h4><ul class="tl">')
    for m in record['milestones']:
        if m['state'] == 'skipped':
            h.append(f'<li><span class="d"></span><span class="skipped">{_e(m["name"])}</span><span class="t">skipped</span></li>')
            continue
        pill = f'<span class="pill">↻ {m["pass"]}</span>' if m.get('pass', 0) >= 2 else ''
        if m['state'] == 'done':
            t = elapsed((m.get('finished_at') or now) - (m.get('started_at') or now))
        elif m['state'] == 'current':
            t = elapsed(now - (m.get('started_at') or now))
        else:
            t = 'may loop' if m.get('loop') else ''
        cls = '' if m['state'] in ('done', 'current') else ' class="muted"'
        h.append(f'<li><span class="d {m["state"]}{" loop" if m["state"] == "current" and m.get("pass", 0) >= 2 else ""}"></span><span{cls}>{_e(m["name"])}{pill}</span><span class="t">{_e(t)}</span></li>')
    h.append('</ul><div class="youcard"><h4>⚑ Where you come in</h4><ul class="tl">')
    if not record['waypoints']:
        h.append('<li><span></span><span class="muted">No checkpoints planned</span><span></span></li>')
    for w in record['waypoints']:
        when = {'done': 'done', 'waiting': 'now'}.get(w['state'], f"after {names.get(w['after'], w['after'])}")
        tag = '' if w['planned'] else ' <span class="muted">(unplanned)</span>'
        dot = 'done' if w['state'] == 'done' else ('you waiting' if w['state'] == 'waiting' else 'you')
        h.append(f'<li><span class="d {dot}"></span><span>{_e(w["need"])}{tag}</span><span class="t">{_e(when)}</span></li>')
    h.append('</ul></div></aside></div>')
    if record.get('note'):
        h.append(f'<div class="note">{_e(record["note"])}</div>')
    h.append('</div></div></main>')
    return ''.join(h)


def render_html(record, now=None) -> str:
    title = record.get('title', 'Quest progress') if isinstance(record, dict) else 'Quest progress'
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{_e(title)} · Guildhall</title><style>{PAGE_CSS}</style></head><body>'
            f'<div id="app">{render_fragment(record, now)}</div>'
            '<script>setInterval(async()=>{try{const r=await fetch("/fragment",{cache:"no-store"});'
            'if(r.ok)document.getElementById("app").innerHTML=await r.text()}catch(e){}},2000)</script>'
            '</body></html>')


def find_record(root: Path, plan=None):
    """The plan's record, or the newest active record under the plans folder."""
    if plan:
        return record_path(root, plan)
    folder = root.joinpath(*PLAN_DIR)
    found = [p for p in folder.glob('*/progress.json') if p.is_file() and not p.is_symlink()]
    if not found:
        return None

    def active(p):
        try:
            return json.loads(p.read_text()).get('status') == 'active'
        except (OSError, ValueError, AttributeError):
            return False
    return max(found, key=lambda p: (active(p), p.stat().st_mtime))


def read_any(path):
    if path is None:
        return None
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def make_server(root: Path, plan=None, port=0):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    root = Path(root).resolve()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            record = read_any(find_record(root, plan))
            if self.path in ('/', '/index.html'):
                body = render_html(record) if record is not None else render_html({}, None)
            elif self.path == '/fragment':
                body = render_fragment(record if record is not None else {})
            else:
                self.send_error(404)
                return
            data = body.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'")
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def watch(root: Path, plan, once=False, width=None, web=False, port=0, interval=1.0) -> int:
    import shutil
    root = Path(root).resolve()
    if web:
        server = make_server(root, plan, port)
        print(f'Quest progress: http://127.0.0.1:{server.server_address[1]}/  (Ctrl-C to stop)', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return 0
    tty = sys.stdout.isatty()
    frame = 0
    try:
        if tty and not once:
            sys.stdout.write('\x1b[?1049h\x1b[?25l')
        while True:
            cols = width or shutil.get_terminal_size((60, 24)).columns
            path = find_record(root, plan)
            record = read_any(path)
            view = render_missing(cols) if record is None else render_safe(record, cols, tty, time.time(), frame)
            if once:
                print(view)
                return 0
            sys.stdout.write('\x1b[H\x1b[2J' + view + '\n')
            sys.stdout.flush()
            frame += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        return 0
    finally:
        if tty and not once:
            sys.stdout.write('\x1b[?25h\x1b[?1049l')
            sys.stdout.flush()


# ---------------------------------------------------------------- CLI

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='progress.py', description='Quest progress record for Guildhall quests.')
    p.add_argument('--root', default='.', help='project root (default: current directory)')
    p.add_argument('--plan', help='plan path, docs/guildhall/plans/<name>.md (watch: optional, newest active quest)')
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
    s = sub.add_parser('show', help='print the progress view once')
    s.add_argument('--width', type=int, default=0)
    s.add_argument('--color', action='store_true')
    s = sub.add_parser('watch', help='live view in this terminal, or --web for a browser page')
    s.add_argument('--once', action='store_true', help='print one frame and exit')
    s.add_argument('--width', type=int, default=0)
    s.add_argument('--web', action='store_true', help='serve the full page on 127.0.0.1')
    s.add_argument('--port', type=int, default=0)
    return p


def run(argv) -> int:
    args = parser().parse_args(argv)
    root = Path(args.root).resolve()
    if args.op == 'watch':
        return watch(root, args.plan, args.once, args.width or None, args.web, args.port)
    require(args.plan, '--plan is required')
    if args.op == 'show':
        import shutil
        cols = args.width or shutil.get_terminal_size((60, 24)).columns
        print(render_safe(load(record_path(root, args.plan)), cols, args.color))
        return 0
    path = record_path(root, args.plan)
    no_symlinks(root, path.with_name(path.name + '.lock'))
    no_symlinks(root, path)
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
