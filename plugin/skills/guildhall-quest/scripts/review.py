#!/usr/bin/env python3
"""Optional, bounded planning review workspace. Python 3.12+, standard library only."""
from __future__ import annotations
import argparse
import contextlib
import difflib
import fcntl
import hashlib
import html
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import queue
import re
import secrets
import selectors
import socket
import stat
import shutil
import signal
import subprocess
import sys
import threading
import time
from urllib.parse import quote, urlsplit
import uuid

DOC_LIMIT = 256 * 1024
EDIT_LIMIT = 264 * 1024
FEEDBACK_LIMIT = 32 * 1024
HOSTS = {'document', 'claude-artifact', 'codex-space', 'opencode', 'pi'}
HOSTED = {'claude-artifact', 'codex-space'}
STATES = {'clean', 'local-changed', 'hosted-changed', 'both-changed', 'conflict',
          'pending-local-save', 'pending-hosted-save', 'unavailable'}
DELIVERIES = ('prepared', 'sent-unknown', 'response-received', 'failed-before-send')
DISPOSITIONS = {'proposed', 'accepted', 'rejected', 'deferred', 'unresolved'}

class Refusal(Exception):
    def __init__(self, message, code=2, http=None, details=None):
        super().__init__(message)
        self.code = code
        self.details = details or {}
        self.http = http or {2:400, 3:409, 4:502}[code]


def require(condition, message, code=2, http=None, details=None):
    if not condition:
        raise Refusal(message, code, http, details)


def diagnostic(stage, error_class):
    # Only bounded labels chosen by this helper, never exception messages/paths.
    return {'stage':stage[:64], 'error_class':error_class[:64]}


def failure(stage, error, message='Review operation unavailable; saved evidence retained'):
    return Refusal(message,4,details=diagnostic(stage,type(error).__name__))


def report(operation, error):
    if error.details:
        print(json.dumps({'operation':operation if operation in ('init','inspect','checkpoint','export','serve',
              'state','document','feedback','cancel','rebind') else 'unknown', **error.details}),file=sys.stderr,flush=True)


def remaining(deadline, stage):
    budget = deadline-time.monotonic()
    require(budget > 0, 'Host operation deadline exceeded; inspect delivery before retrying',4,
            details=diagnostic(stage,'DeadlineExceeded'))
    return budget


@contextlib.contextmanager
def synchronized(lock,deadline,stage):
    # An expired operation may still record its observed outcome without waiting
    # when the lock is immediately available; it never acquires a fresh budget.
    locked = lock.acquire(timeout=max(0,deadline-time.monotonic()))
    require(locked, 'Host operation synchronization deadline exceeded',4,
            details=diagnostic(stage,'DeadlineExceeded'))
    try: yield
    finally: lock.release()


def safety(condition,message,identity=False):
    require(condition,message,3 if identity else 4,
            details=diagnostic('session-identity' if identity else 'tool-restrictions',
                               'IdentityMismatch' if identity else 'RestrictionFailure'))


def fields(value, required, optional=()):
    require(isinstance(value, dict), 'Expected a JSON object')
    require(set(required) <= set(value) <= set(required) | set(optional), 'Missing or unknown fields')
    return value


def text(value, limit=4000, nullable=False, empty=False):
    if value is None and nullable:
        return value
    require(isinstance(value, str) and (empty or bool(value.strip())) and len(value) <= limit,
            'Expected bounded text')
    require('\x00' not in value, 'NUL text is not supported')
    return value


def document(value):
    require(isinstance(value,str), 'Expected review text')
    try: encoded = value.encode('utf-8')
    except UnicodeError: raise Refusal('Review must be valid UTF-8') from None
    require(len(encoded) <= DOC_LIMIT, 'Review exceeds 256 KiB; split it explicitly', http=413)
    require('\x00' not in value, 'NUL text is not supported')
    return value


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normalized(value):
    return value.removeprefix('\ufeff').replace('\r\n', '\n').replace('\r', '\n')


def hashtext(value):
    return digest(value.encode('utf-8'))


def valid_hash(value):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'Invalid SHA-256')


def dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def envelope(operation, result=None, error=None):
    return {'schema_version':1, 'operation':operation, 'ok':error is None,
            'result':result if error is None else None,
            'error':None if error is None else {'code':{2:'invalid-input',3:'refused',4:'unavailable'}[error.code],
                                               'message':str(error), 'details':error.details}}


def parse(raw):
    try:
        def pairs(items):
            value = {}
            for key, item in items:
                require(key not in value, 'Duplicate JSON field')
                value[key] = item
            return value
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError, RecursionError):
        raise Refusal('Invalid JSON') from None


def no_symlink(path):
    for item in [path, *path.parents]:
        require(not item.is_symlink() or item in (Path('/var'), Path('/tmp'), Path('/etc')), 'Symlink paths are refused', 3)


def atomic(path, data):
    no_symlink(path)
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex)
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def validate_authority(value):
    fields(value, ('display_label', 'source'))
    text(value['display_label']); text(value['source'])


def validate_surface(value, host):
    fields(value, ('kind','id','url'))
    require(value['kind'] == host, 'Surface and selected host disagree', 3)
    if host in HOSTED:
        text(value['id'], 512)
        url = urlsplit(text(value['url'], 2048))
        require(url.scheme == 'https' and bool(url.hostname) and not url.username and not url.password,
                'Hosted surface requires an explicit HTTPS URL')
    else:
        require(value['id'] is None and value['url'] is None, 'Local surface identity must be null')


def validate_feedback(entries):
    require(isinstance(entries, list) and len(entries) <= 200, 'Feedback exceeds 200 entries; archive explicitly')
    ids = set()
    for entry in entries:
        fields(entry, ('id','source_ref','source_revision','author','selection','text','disposition','rationale'))
        for key in ('id','source_ref','text','rationale'):
            text(entry[key], empty=key == 'rationale')
        text(entry['source_revision'], nullable=True); text(entry['author'], nullable=True)
        require(entry['id'] not in ids, 'Duplicate feedback identity'); ids.add(entry['id'])
        require(entry['disposition'] in DISPOSITIONS, 'Invalid disposition')
        if entry['selection'] is not None:
            fields(entry['selection'], ('status','text'))
            require(entry['selection']['status'] in ('attached','detached'), 'Invalid anchor')
            text(entry['selection']['text'], nullable=entry['selection']['status'] == 'detached')


def validate_decisions(entries, authority):
    require(isinstance(entries, list) and len(entries) <= 200, 'Decisions exceed 200 entries')
    ids = set()
    for entry in entries:
        fields(entry, ('id','text','disposition','source_ref','authority_label','rationale'))
        for key in ('id','text','source_ref','authority_label','rationale'):
            text(entry[key], empty=key == 'rationale')
        require(entry['id'] not in ids, 'Duplicate decision identity'); ids.add(entry['id'])
        require(entry['disposition'] in DISPOSITIONS, 'Invalid disposition')
        if entry['disposition'] == 'accepted':
            require(entry['authority_label'] == authority['display_label'], 'Only designated authority can accept', 3)


def merge_entries(existing, incoming):
    result = list(existing)
    by_id = {item['id']:item for item in result}
    conflicts = []
    for item in incoming:
        prior = by_id.get(item['id'])
        if prior is not None and prior != item:
            conflicts.append({'kind':'decision','baseline':json.dumps(prior, ensure_ascii=False),
                              'local':json.dumps(prior, ensure_ascii=False),'hosted':json.dumps(item, ensure_ascii=False)})
        elif prior is None:
            result.append(item); by_id[item['id']] = item
    require(len(result) <= 200, 'Combined entries exceed 200; archive explicitly')
    return result, conflicts


def merge_prose(base, local, remote):
    if local == remote: return local, False
    if local == base: return remote, False
    if remote == base: return local, False
    lines = base.splitlines(keepends=True)
    # minimal: SequenceMatcher on bounded documents; refuse pathological line products
    # instead of monopolizing the companion. A linear-space diff can lift this ceiling.
    def edits(value):
        other = value.splitlines(keepends=True)
        require(len(lines) * len(other) <= 4_000_000, 'Merge complexity bound; split the document explicitly')
        return [(i,j,other[a:b]) for tag,i,j,a,b in difflib.SequenceMatcher(None,lines,other,autojunk=False).get_opcodes() if tag != 'equal']
    left, right = edits(local), edits(remote)
    all_edits = list(left)
    for b in right:
        same = False
        for a in left:
            if a == b: same = True; continue
            ai,aj,_ = a; bi,bj,_ = b
            overlap = (max(ai,bi) < min(aj,bj))
            if ai == aj: overlap |= bi <= ai <= bj
            if bi == bj: overlap |= ai <= bi <= aj
            if overlap: return None, True
        if not same: all_edits.append(b)
    for i,j,replacement in sorted(all_edits, key=lambda e:(e[0],e[1]), reverse=True):
        lines[i:j] = replacement
    return ''.join(lines), False


class Workspace:
    def __init__(self, root, plan, host):
        self.root = Path(root)
        require(self.root.is_absolute() and self.root.is_dir(), 'Root must be an existing absolute directory', 3)
        no_symlink(self.root)
        self.root = self.root.resolve()
        relative = Path(plan)
        require(not relative.is_absolute() and '..' not in relative.parts and
                relative.parts[:3] == ('docs','guildhall','plans') and len(relative.parts) == 4 and
                relative.suffix == '.md', 'Plan must be a Markdown file under docs/guildhall/plans', 3)
        self.plan = self.root / relative
        no_symlink(self.plan)
        require(self.plan.is_file(), 'Plan must already exist', 3)
        self.bundle = self.plan.with_suffix('')
        self.review = self.bundle / 'review.md'
        self.html = self.bundle / 'review.html'
        self.state = self.bundle / 'review-state.json'
        self.snapshots = self.bundle / 'snapshots'
        self.host = host
        self.check_paths()

    def rel(self, path): return path.relative_to(self.root).as_posix()

    def check_paths(self, strict=False):
        no_symlink(self.bundle)
        if not self.bundle.exists(): return
        require(self.bundle.is_dir(), 'Bundle is not a directory', 3)
        allowed = {self.review,self.html,self.state,self.snapshots,
                   self.snapshots/'common.md',self.snapshots/'pending.md'}
        for path in self.bundle.rglob('*'):
            require(not path.is_symlink() and (not strict or path in allowed), 'Unexpected file or symlink in review bundle', 3)
            if path not in allowed: continue
            require(path.is_dir() if path == self.snapshots else path.is_file(), 'Unexpected bundle entry type', 3)

    @contextlib.contextmanager
    def locked(self, strict=False, deadline=None):
        # Lock the directory inode without adding helper files to durable content.
        # minimal: serialize review operations within this plans directory; per-quest
        # locks can improve throughput if needed. External editors use hash guards.
        fd = os.open(self.plan.parent, os.O_RDONLY)
        try:
            if deadline is None:
                fcntl.flock(fd,fcntl.LOCK_EX)
            else:
                while True:
                    try:
                        fcntl.flock(fd,fcntl.LOCK_EX | fcntl.LOCK_NB); break
                    except BlockingIOError:
                        time.sleep(min(.01,remaining(deadline,'workspace-lock')))
            self.check_paths(strict=strict)
            yield
        finally:
            os.close(fd)

    def read(self):
        self.check_paths()
        require(self.state.is_file() and self.review.is_file(), 'Initialize the review workspace first', 3)
        require(self.state.stat().st_size <= 128 * 1024 * 1024, 'Checkpoint record is too large', 3)
        data = self.state.read_bytes()
        record = parse(data)
        self.validate_record(record)
        require(self.review.stat().st_size <= DOC_LIMIT, 'Review exceeds 256 KiB', 2)
        content = document(self.review.read_bytes().decode('utf-8'))
        return record, content, digest(data)

    def validate_record(self, record):
        fields(record, ('schema_version','quest_id','plan_path','review_path','html_path','surface','authority','checkpoint','feedback','decisions'))
        require(type(record['schema_version']) is int and record['schema_version'] == 1, 'Unsupported record schema')
        text(record['quest_id'], 512)
        for key, path in [('plan_path',self.plan),('review_path',self.review),('html_path',self.html)]:
            require(record[key] == self.rel(path), 'Record path mismatch', 3)
        validate_surface(record['surface'], self.host); validate_authority(record['authority'])
        validate_feedback(record['feedback']); validate_decisions(record['decisions'],record['authority'])
        cp = fields(record['checkpoint'], ('state','common','pending'))
        require(cp['state'] in STATES, 'Invalid checkpoint state')
        if cp['common'] is not None:
            common = fields(cp['common'], ('local_sha256','normalized_sha256','hosted_revision','source_ref','snapshot_path'))
            valid_hash(common['local_sha256']); valid_hash(common['normalized_sha256'])
            text(common['hosted_revision'], nullable=True); text(common['source_ref'])
            require(common['snapshot_path'] in {self.rel(self.snapshots/name) for name in ('common.md','pending.md')}, 'Invalid common snapshot path', 3)
            path = self.root/common['snapshot_path']
            require(path.is_file() and path.stat().st_size <= DOC_LIMIT and digest(path.read_bytes()) == common['normalized_sha256'],
                    'Common snapshot does not match its record', 3)
        if cp['pending'] is not None:
            pending = fields(cp['pending'], ('id','merged_sha256','snapshot_path','required_saves','hosted_saved','source_ref','hosted_revision','feedback','decisions'))
            text(pending['id'],512); valid_hash(pending['merged_sha256'])
            require(pending['snapshot_path'] in {self.rel(self.snapshots/name) for name in ('common.md','pending.md')} and
                    (cp['common'] is None or pending['snapshot_path'] != cp['common']['snapshot_path']), 'Invalid pending snapshot', 3)
            path = self.root/pending['snapshot_path']
            require(path.is_file() and path.stat().st_size <= DOC_LIMIT and digest(path.read_bytes()) == pending['merged_sha256'], 'Pending snapshot mismatch', 3)
            require(isinstance(pending['required_saves'],list) and set(pending['required_saves']) <= {'local','hosted'}, 'Invalid save actions')
            require(isinstance(pending['hosted_saved'],bool), 'Invalid receipt flag')
            text(pending['source_ref']); text(pending['hosted_revision'],nullable=True)
            validate_feedback(pending['feedback']); validate_decisions(pending['decisions'],record['authority'])

    def render(self, content, online=False):
        template = Path(__file__).resolve().parent.parent / 'resources/review/template.html'
        return template.read_text().replace('/*REVIEW_ONLINE*/false','true' if online else 'false').replace('<!--REVIEW_CONTENT-->',html.escape(content)).encode('utf-8')

    def init(self, payload):
        fields(payload, ('quest_id','content','authority','surface'))
        text(payload['quest_id'],512); document(payload['content'])
        validate_authority(payload['authority']); validate_surface(payload['surface'],self.host)
        record = {'schema_version':1,'quest_id':payload['quest_id'],'plan_path':self.rel(self.plan),
                  'review_path':self.rel(self.review),'html_path':self.rel(self.html),
                  'surface':payload['surface'],'authority':payload['authority'],
                  'checkpoint':{'state':'local-changed','common':None,'pending':None},'feedback':[],'decisions':[]}
        expected = {self.review:payload['content'].encode(), self.html:self.render(payload['content']), self.state:dump(record)}
        with self.locked(strict=True):
            for path, data in expected.items():
                require(not path.exists() or path.read_bytes() == data, 'Conflicting initialization; existing content preserved', 3)
            self.bundle.mkdir(exist_ok=True)
            created = []
            for path, data in expected.items():
                if not path.exists(): atomic(path,data); created.append(self.rel(path))
        return {'bundle_path':self.rel(self.bundle),'created_paths':created,
                'hashes':{'review_sha256':digest(expected[self.review]),'html_sha256':digest(expected[self.html]),'state_sha256':digest(expected[self.state])}}

    def observation(self, value, record):
        if value is None: return None
        fields(value, ('surface_id','text','revision','source_ref'), ('feedback_complete','feedback'))
        require(value['surface_id'] == record['surface']['id'], 'Observed surface identity mismatch', 3)
        document(value['text']); text(value['revision'],nullable=True); text(value['source_ref'])
        require(isinstance(value.get('feedback_complete',False),bool), 'Invalid completeness flag')
        validate_feedback(value.get('feedback',[]))
        return value

    def status(self, record, content, state_hash, observation=None):
        obs = self.observation(observation, record)
        local = normalized(content)
        hosted = normalized(obs['text']) if obs else None
        cp = record['checkpoint']; common = cp['common']; conflicts = []
        state = 'local-changed'; merged = local
        if self.host in HOSTED and obs is None:
            state = 'unavailable'; merged = None
        elif common:
            base = (self.root/common['snapshot_path']).read_bytes().decode('utf-8')
            lc = hashtext(local) != common['normalized_sha256']
            hc = hosted is not None and hashtext(hosted) != common['normalized_sha256']
            state = 'both-changed' if lc and hc else 'local-changed' if lc else 'hosted-changed' if hc else 'clean'
            if hosted is not None:
                merged, conflict = merge_prose(base,local,hosted)
                if conflict:
                    state = 'conflict'; conflicts.append({'kind':'prose','baseline':base,'local':local,'hosted':hosted})
        elif hosted is not None and local != hosted:
            state = 'conflict'; merged = None
            conflicts.append({'kind':'prose','baseline':None,'local':local,'hosted':hosted})
        if cp['pending'] is not None and state not in ('conflict','unavailable'):
            pending = cp['pending']
            state = 'pending-local-save' if hashtext(local) != pending['merged_sha256'] else 'pending-hosted-save' if 'hosted' in pending['required_saves'] and not pending['hosted_saved'] else cp['state']
        status = {'state':state,'checkpoint_needed':common is None or state != 'clean',
                  'state_sha256':state_hash,'review_sha256':hashtext(content),'normalized_sha256':hashtext(local),
                  'hosted_sha256':hashtext(hosted) if hosted is not None else None,
                  'hosted_revision':obs['revision'] if obs else None,
                  'completeness':{'feedback':bool(obs and obs.get('feedback_complete',False))},
                  'conflicts':conflicts,'pending_delivery_counts':None,'delivery_coverage':'unavailable'}
        return status, merged

    def inspect(self, payload):
        fields(payload, (), ('observation','runtime_dir'))
        with self.locked():
            record, content, state_hash = self.read()
            result = self.status(record,content,state_hash,payload.get('observation'))[0]
            if 'runtime_dir' in payload:
                runtime = validate_runtime(payload['runtime_dir'],self,privacy=False)
                require(runtime.is_dir(), 'Runtime inspection unavailable',4)
                owner = runtime/'owner.json'; journal = runtime/'requests.json'
                no_symlink(owner); no_symlink(journal)
                require(owner.is_file() and journal.is_file(), 'Runtime ownership or journal unavailable',4)
                validate_runtime(str(runtime),self)
                require(owner.stat().st_size <= 16384, 'Invalid runtime owner record',3)
                require(parse(owner.read_bytes()) == runtime_owner(self,record), 'Runtime belongs to a different review',3)
                requests = read_journal(journal)
                counts = {name:0 for name in DELIVERIES}
                for request in requests.values(): counts[request['delivery_state']] += 1
                result['pending_delivery_counts'] = counts
                result['delivery_coverage'] = 'complete'
            return result

    def guards(self, payload, state_hash, content):
        valid_hash(payload['expected_state_hash']); valid_hash(payload['expected_review_hash'])
        require(payload['expected_state_hash'] == state_hash and payload['expected_review_hash'] == hashtext(content), 'Stale review or state guard', 3)

    def checkpoint(self, payload, deadline=None):
        fields(payload, ('phase','expected_state_hash','expected_review_hash'), ('observation','checkpoint_id','decisions','resolution','receipt'))
        require(payload['phase'] in ('prepare','complete'), 'Invalid checkpoint phase')
        with self.locked(strict=True,deadline=deadline):
            record, content, state_hash = self.read(); self.guards(payload,state_hash,content)
            obs = self.observation(payload.get('observation'),record)
            cp = record['checkpoint']
            if payload['phase'] == 'prepare':
                require('receipt' not in payload and 'checkpoint_id' not in payload, 'Prepare cannot supply a receipt or checkpoint ID')
                require(cp['pending'] is None, 'Resolve existing pending checkpoint first', 3)
                status, merged = self.status(record,content,state_hash,obs)
                require(status['state'] != 'unavailable', 'Hosted review unavailable; preserve local material', 4)
                decisions = payload.get('decisions',[]); validate_decisions(decisions,record['authority'])
                combined, conflicts = merge_entries(record['decisions'],decisions)
                feedback, feedback_conflicts = merge_entries(record['feedback'],obs.get('feedback',[]) if obs else [])
                conflicts = status['conflicts'] + conflicts + feedback_conflicts
                if 'resolution' in payload:
                    resolution = fields(payload['resolution'], ('content','source_ref','authority_label'))
                    document(resolution['content']); text(resolution['source_ref']); text(resolution['authority_label'])
                    require(resolution['authority_label'] == record['authority']['display_label'], 'Resolution requires designated owner',3)
                    require(status['conflicts'] and not conflicts[len(status['conflicts']):], 'Resolution must address a prose conflict',3)
                    merged = normalized(resolution['content']); conflicts = []
                    resolution_decision = {'id':'resolution-' + uuid.uuid4().hex,
                        'text':'Owner supplied review prose conflict resolution: ' + hashtext(merged),
                        'disposition':'accepted','source_ref':resolution['source_ref'],
                        'authority_label':resolution['authority_label'],'rationale':'Explicit supplied owner resolution'}
                    combined.append(resolution_decision)
                    validate_decisions(combined,record['authority'])
                if conflicts:
                    return {'checkpoint_id':None,'state':'conflict','merged_content':None,'merged_sha256':None,
                            'required_saves':[],'changed_paths':[],'conflicts':conflicts}
                require(merged is not None, 'No review content available',4); document(merged)
                required = []
                if content != merged: required.append('local')
                if self.host in HOSTED and (obs is None or normalized(obs['text']) != merged): required.append('hosted')
                # Even an unchanged hosted baseline needs an actual observation/receipt at completion.
                slot = self.snapshots/('common.md' if cp['common'] and cp['common']['snapshot_path'] == self.rel(self.snapshots/'pending.md') else 'pending.md')
                pending = {'id':uuid.uuid4().hex,'merged_sha256':hashtext(merged),
                           'snapshot_path':self.rel(slot),'required_saves':required,
                           'hosted_saved':False,'source_ref':obs['source_ref'] if obs else 'local review checkpoint',
                           'hosted_revision':obs['revision'] if obs else None,'feedback':feedback,'decisions':combined}
                cp['pending'] = pending
                cp['state'] = 'pending-local-save' if 'local' in required else 'pending-hosted-save'
                self.snapshots.mkdir(exist_ok=True)
                changed = [self.rel(slot),self.rel(self.state)]
                atomic(slot,merged.encode())
                if self.host not in HOSTED and 'local' in required:
                    atomic(self.review,merged.encode()); changed.append(self.rel(self.review))
                atomic(self.state,dump(record))
                return {'checkpoint_id':pending['id'],'state':cp['state'],'merged_content':merged,'merged_sha256':hashtext(merged),
                        'required_saves':required,'changed_paths':changed,'conflicts':[]}
            require('decisions' not in payload and 'resolution' not in payload, 'Complete cannot introduce decisions or resolutions')
            pending = cp['pending']
            require(pending is not None and payload.get('checkpoint_id') == pending['id'], 'Unknown or completed checkpoint',3)
            hosted = self.host in HOSTED
            if hosted:
                require('receipt' in payload, 'Hosted completion requires actual save receipt')
                receipt = fields(payload['receipt'], ('surface_id','revision','content_sha256','source_ref'))
                text(receipt['revision'],nullable=True); text(receipt['source_ref']); valid_hash(receipt['content_sha256'])
                require(receipt['surface_id'] == record['surface']['id'], 'Receipt surface mismatch',3)
                require(receipt['content_sha256'] == pending['merged_sha256'], 'Receipt content mismatch',3)
                require(obs is not None and hashtext(normalized(obs['text'])) == pending['merged_sha256'] and obs['revision'] == receipt['revision'], 'Fresh hosted observation required',3)
                pending['hosted_saved'] = True; pending['source_ref'] = receipt['source_ref']; pending['hosted_revision'] = receipt['revision']
            else:
                require('receipt' not in payload, 'Local checkpoint has no hosted receipt')
            if hashtext(normalized(content)) != pending['merged_sha256']:
                if hosted:
                    cp['state'] = 'pending-local-save'; atomic(self.state,dump(record))
                raise Refusal('Hosted save observed; local save still pending' if hosted else 'Local save still pending',3)
            feedback, feedback_conflicts = merge_entries(record['feedback'],pending['feedback'])
            decisions, decision_conflicts = merge_entries(record['decisions'],pending['decisions'])
            require(not feedback_conflicts and not decision_conflicts,
                    'Feedback or decisions changed during checkpoint; preserve pending review',3)
            cp['common'] = {'local_sha256':hashtext(content),'normalized_sha256':pending['merged_sha256'],
                            'hosted_revision':pending['hosted_revision'],'source_ref':pending['source_ref'],
                            'snapshot_path':pending['snapshot_path']}
            record['feedback'] = feedback; record['decisions'] = decisions
            cp['state'] = 'clean'; cp['pending'] = None
            try: atomic(self.state,dump(record))
            except OSError as error:
                raise failure('checkpoint-publication',error,'Checkpoint publication failed; prior baseline and pending save retained') from None
            return {'state':'clean','checkpoint_id':pending['id'],'changed_paths':[self.rel(self.state)]}

    def export(self, payload):
        fields(payload, ('expected_review_hash',)); valid_hash(payload['expected_review_hash'])
        with self.locked(strict=True):
            _, content, _ = self.read()
            require(hashtext(content) == payload['expected_review_hash'], 'Stale review guard',3)
            require(not self.html.exists() or b'<!-- Guildhall maintained review template v1 -->' in self.html.read_bytes()[:200],
                    'Unexpected HTML output; preserve it before exporting',3)
            rendered = self.render(content); atomic(self.html,rendered)
        return {'source_sha256':hashtext(content),'output_sha256':digest(rendered),'output_path':self.rel(self.html),
                'disabled_capabilities':['agent chat','hosted comments','checkpoint synchronization']}


def validate_runtime(value, workspace, privacy=True):
    runtime = Path(text(value,4096))
    require(runtime.is_absolute() and '..' not in runtime.parts, 'Runtime must be an absolute directory',3)
    no_symlink(runtime)
    runtime = runtime.resolve()
    if privacy and runtime.exists():
        attributes = runtime.stat()
        require(stat.S_ISDIR(attributes.st_mode) and attributes.st_uid == os.geteuid() and
                not attributes.st_mode & 0o077, 'Runtime must be owned by the current user with private permissions',3)
    require(not runtime.is_relative_to(workspace.bundle) and not workspace.bundle.is_relative_to(runtime),
            'Runtime must be separate from durable bundle',3)
    require(not runtime.is_relative_to(workspace.root), 'Runtime must be outside the repository',3)
    return runtime


def runtime_owner(workspace,record):
    return {'schema_version':1,'root':str(workspace.root),'plan_path':workspace.rel(workspace.plan),
            'quest_id':record['quest_id']}


def read_journal(path):
    require(path.stat().st_size <= 64 * 1024 * 1024, 'Runtime journal exceeds bound',3)
    requests = parse(path.read_bytes())
    require(isinstance(requests,dict) and len(requests) <= 200, 'Runtime request journal exceeds bounds',3)
    for identity,request in requests.items():
        fields(request, ('request_id','session_id','delivery_state','response','payload','marker'), ('cancel_acknowledged','cancel_requested','recovery_error','local_only'))
        text(identity,512)
        require(request['request_id'] == identity and request['delivery_state'] in DELIVERIES, 'Invalid runtime request identity/state',3)
        text(request['session_id'],512,nullable=True); text(request['response'],DOC_LIMIT,nullable=True,empty=True)
        fields(request['payload'], ('id','session_id','base_revision','selection','comment'))
        fields(request['marker'], ('review_request_id','base_revision','selection','comment'))
        require(request['payload']['id'] == identity and request['payload']['session_id'] == request['session_id'] and
                request['marker'] == {'review_request_id':identity, **{key:request['payload'][key] for key in ('base_revision','selection','comment')}},
                'Invalid runtime request marker',3)
        if request.get('recovery_error') is not None:
            error = fields(request['recovery_error'], ('code','message','details'))
            text(error['code'],64); text(error['message'],256)
            fields(error['details'], ('stage','error_class'))
            text(error['details']['stage'],64); text(error['details']['error_class'],64)
        valid_hash(request['payload']['base_revision'])
        text(request['payload']['selection'],nullable=True); text(request['payload']['comment'])
    return requests


def validate_binding(binding, runtime):
    if binding is None: return
    require(isinstance(binding,dict), 'Invalid binding')
    if binding.get('kind') == 'opencode':
        fields(binding, ('kind','base_url','session_id'))
        text(binding['session_id'],512)
        require(re.fullmatch(r'[A-Za-z0-9_.-]+',binding['session_id']), 'Invalid session ID')
        url = urlsplit(text(binding['base_url'],2048))
        try: port = url.port
        except ValueError: raise Refusal('Invalid loopback port') from None
        require(url.scheme == 'http' and url.hostname in ('127.0.0.1','::1') and port is not None and
                0 < port < 65536 and not url.username and not url.password and not url.path and not url.query and not url.fragment,
                'OpenCode requires an explicit loopback HTTP origin')
    elif binding.get('kind') == 'pi':
        fields(binding, ('kind','session_file'))
        session = Path(text(binding['session_file'],4096))
        require(session.is_absolute() and session.suffix == '.jsonl' and session.resolve().is_relative_to(runtime.resolve()) and '..' not in session.parts,
                'Pi session must be a dedicated runtime JSONL path',3)
        no_symlink(session)
    else:
        raise Refusal('Unsupported binding kind')


class OpenCode:
    def __init__(self,binding,runtime,timeout,startup):
        self.binding = binding; self.session_id = binding['session_id']; self.timeout = timeout
        self.path = '/session/' + quote(self.session_id,safe='')
        self.check(deadline=time.monotonic()+startup)

    def request(self,method,path,value=None,deadline=None,stage='opencode-transport'):
        deadline = deadline if deadline is not None else time.monotonic()+self.timeout
        origin = urlsplit(self.binding['base_url'])
        connection = http.client.HTTPConnection(origin.hostname,origin.port,timeout=remaining(deadline,stage))
        timer = None
        try:
            connection.connect()
            transport = connection.sock
            def expire():
                # Shutdown interrupts header/body reads even if the peer keeps trickling
                # bytes or HTTPConnection has transferred its socket to the response.
                with contextlib.suppress(OSError): transport.shutdown(socket.SHUT_RDWR)
            timer = threading.Timer(remaining(deadline,stage),expire); timer.daemon = True; timer.start()
            connection.request(method,path,json.dumps(value).encode() if value is not None else None,
                               {'Content-Type':'application/json'})
            reply = connection.getresponse()
            require(200 <= reply.status < 300, 'Host operation unavailable',4,
                    details=diagnostic(stage,'HTTPStatus'))
            raw = reply.read(2*1024*1024+1)
            remaining(deadline,stage)
            require(len(raw) <= 2*1024*1024, 'Host response exceeds bound',4,
                    details=diagnostic(stage,'ResponseLimit'))
            try: return parse(raw)
            except Refusal:
                raise Refusal('Host response is invalid',4,details=diagnostic(stage,'InvalidResponse')) from None
        except (OSError,http.client.HTTPException,TimeoutError) as error:
            label = 'DeadlineExceeded' if time.monotonic() >= deadline else type(error).__name__
            raise Refusal('Host transport unavailable; inspect possible delivery',4,
                          details=diagnostic(stage,label)) from None
        finally:
            if timer is not None: timer.cancel()
            connection.close()

    def check(self,deadline=None):
        deadline = deadline if deadline is not None else time.monotonic()+self.timeout
        session = self.request('GET',self.path,deadline=deadline,stage='opencode-session')
        safety(isinstance(session,dict) and session.get('id') == self.session_id, 'Host session identity changed',True)
        safety(session.get('permission') == [{'permission':'*','pattern':'*','action':'deny'}],
               'Tool-free session permissions unavailable')
        tools = self.request('GET','/experimental/tool/ids',deadline=deadline,stage='opencode-tools')
        safety(isinstance(tools,list) and len(tools) <= 1000 and
               all(isinstance(tool,str) and len(tool) <= 512 for tool in tools), 'Tool inventory unavailable')
        self.tools = {tool:False for tool in tools}
        model = session.get('model')
        if not isinstance(model,dict) or not model.get('providerID') or not model.get('id'):
            model = next(({'providerID':m['info']['model'].get('providerID'),'id':m['info']['model'].get('modelID')}
                          for m in reversed(self.history(deadline)) if m.get('info',{}).get('role') == 'user'
                          and isinstance(m['info'].get('model'),dict)),None)
        require(isinstance(model,dict) and model.get('providerID') and model.get('id'),
                'Existing selected model unavailable',4,details=diagnostic('opencode-model','ModelUnavailable'))
        self.model = {'providerID':model['providerID'],'modelID':model['id']}

    def history(self,deadline):
        value = self.request('GET',self.path+'/message',deadline=deadline,stage='opencode-history')
        require(isinstance(value,list), 'Host history unavailable',4,details=diagnostic('opencode-history','InvalidResponse'))
        return value

    def recover(self,request,deadline=None,checked=False):
        deadline = deadline if deadline is not None else time.monotonic()+self.timeout
        if not checked: self.check(deadline)
        users = []
        history = self.history(deadline)
        for message in history:
            info = message.get('info',{})
            if info.get('role') != 'user': continue
            for part in message.get('parts',[]):
                if part.get('type') != 'text': continue
                try: marker = parse(part.get('text',''))
                except Refusal: continue
                if marker == request['marker']: users.append(info.get('id'))
        require(len(users) <= 1, 'Ambiguous host request history',4,
                details=diagnostic('opencode-history','AmbiguousHistory'))
        if not users: return None
        for message in history:
            info = message.get('info',{})
            if info.get('role') != 'assistant' or info.get('parentID') != users[0]: continue
            safety(not any(p.get('type') in ('tool','toolCall') for p in message.get('parts',[])),
                   'Host tool restriction failure')
            if info.get('time',{}).get('completed'):
                answer = '\n'.join(p.get('text','') for p in message.get('parts',[]) if p.get('type') == 'text')
                document(answer)
                return answer
        return None

    def send(self,request,deadline):
        try:
            self.request('POST',self.path+'/message',{'parts':[{'type':'text','text':json.dumps(request['marker'],ensure_ascii=False)}],
                         'tools':self.tools,'model':self.model},deadline=deadline,stage='opencode-send')
        except Refusal:
            # Recovery may use only what remains of this same operation budget.
            remaining(deadline,'opencode-send')
        return self.recover(request,deadline,checked=True)

    def cancel(self,deadline):
        return self.request('POST',self.path+'/abort',{},deadline=deadline,stage='opencode-abort') is True
    def close(self): pass


class Pi:
    def __init__(self,binding,runtime,timeout,startup):
        deadline = time.monotonic()+startup
        self.binding = binding; self.runtime = runtime; self.timeout = timeout
        session = Path(binding['session_file']); self.marker = runtime/'pi-owner.json'
        no_symlink(self.marker)
        if self.marker.exists():
            owned = fields(parse(self.marker.read_bytes()), ('binding','session_id'))
            require(owned['binding'] == binding, 'Pi runtime ownership mismatch; explicit rebind required',3)
            text(owned['session_id'],512,nullable=True)
            require(owned['session_id'] is not None or not session.exists(), 'Pi session identity was not established; explicit rebind required',3)
        else:
            require(not session.exists(), 'Refusing an existing unowned Pi/TUI session',3)
            owned = {'binding':binding,'session_id':None}; atomic(self.marker,dump(owned))
        executable = shutil.which('pi')
        require(executable is not None, 'Existing Pi executable unavailable',4,details=diagnostic('pi-startup','ExecutableUnavailable'))
        session.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.process = subprocess.Popen([executable,'--mode','rpc','--session',str(session),'--no-tools','--no-extensions',
            '--no-mcp','--no-skills','--no-prompt-templates','--no-themes','--no-context-files','--no-approve','--offline'],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
        self.messages = queue.Queue(maxsize=2048); self.responses = {}
        self.response_lock = threading.Lock(); self.write_lock = threading.Lock()
        self.reader_error = None; self.stderr_seen = False
        os.set_blocking(self.process.stdin.fileno(),False)
        self.reader = threading.Thread(target=self.read_loop,daemon=True); self.reader.start()
        self.stderr_reader = threading.Thread(target=self.drain_stderr,daemon=True); self.stderr_reader.start()
        try:
            state = self.command('get_state',deadline)
            safety(state.get('sessionFile') == str(session) and isinstance(state.get('sessionId'),str), 'Pi session identity mismatch',True)
            text(state['sessionId'],512)
            safety(owned['session_id'] is None or owned['session_id'] == state['sessionId'], 'Pi session identity changed; explicit rebind required',True)
            self.session_id = state['sessionId']
            require(state.get('model'), 'Existing Pi model unavailable',4,details=diagnostic('pi-model','ModelUnavailable'))
            self.check(deadline,state=state)
            atomic(self.marker,dump({'binding':binding,'session_id':self.session_id}))
        except Exception:
            self.close(); raise

    def drain_stderr(self):
        # Drain to avoid a blocked peer; retain no provider bytes, paths or transcripts.
        try:
            while self.process.stderr.read(4096): self.stderr_seen = True
        except (OSError,ValueError): pass

    def process_failure(self,stage,label):
        # Safe exit metadata is diagnostic text, never raw process output.
        code = self.process.poll()
        if code is not None:
            print(json.dumps({'operation':'serve','stage':stage,'error_class':label,
                              'process_exit':code,'stderr_present':self.stderr_seen}),file=sys.stderr,flush=True)
        return Refusal('Pi operation unavailable; inspect possible delivery',4,details=diagnostic(stage,label))

    def read_loop(self):
        try:
            while True:
                raw = self.process.stdout.readline(2*1024*1024+1)
                if not raw: break
                require(len(raw) <= 2*1024*1024, 'Pi response exceeds bound',4)
                item = parse(raw)
                require(isinstance(item,dict), 'Invalid Pi response',4)
                if item.get('type') == 'response':
                    with self.response_lock: target = self.responses.get(item.get('id'))
                    if target is not None:
                        with contextlib.suppress(queue.Full): target.put_nowait(item)
                else: self.messages.put(item,timeout=1)
        except Exception as error:
            self.reader_error = type(error).__name__
        finally:
            with self.response_lock:
                for target in self.responses.values():
                    with contextlib.suppress(queue.Full): target.put_nowait(None)
            with contextlib.suppress(queue.Full): self.messages.put_nowait(None)

    def next(self,deadline):
        try: item = self.messages.get(timeout=remaining(deadline,'pi-events'))
        except queue.Empty: raise self.process_failure('pi-events','DeadlineExceeded') from None
        require(isinstance(item,dict), 'Pi disconnected; delivery remains unknown',4,
                details=diagnostic('pi-events',self.reader_error or 'Disconnected'))
        return item

    def command(self,command,deadline=None,**extra):
        deadline = deadline if deadline is not None else time.monotonic()+self.timeout
        identity = uuid.uuid4().hex; target = queue.Queue(maxsize=1)
        if self.process.poll() is not None: raise self.process_failure('pi-command','ProcessExited')
        with self.response_lock: self.responses[identity] = target
        locked = False
        try:
            locked = self.write_lock.acquire(timeout=remaining(deadline,'pi-write-lock'))
            require(locked, 'Pi write deadline exceeded',4,details=diagnostic('pi-write-lock','DeadlineExceeded'))
            raw = (json.dumps({'id':identity,'type':command,**extra})+'\n').encode()
            fd = self.process.stdin.fileno(); offset = 0
            with selectors.DefaultSelector() as selector:
                selector.register(fd,selectors.EVENT_WRITE)
                while offset < len(raw):
                    require(selector.select(remaining(deadline,'pi-write')), 'Pi write deadline exceeded',4,
                            details=diagnostic('pi-write','DeadlineExceeded'))
                    # A test harness or another owner of the descriptor may restore its
                    # flags; enforce nonblocking immediately before every bounded write.
                    os.set_blocking(fd,False)
                    try: offset += os.write(fd,raw[offset:])
                    except BlockingIOError: continue
            self.write_lock.release(); locked = False
            try: value = target.get(timeout=remaining(deadline,'pi-response'))
            except queue.Empty: raise self.process_failure('pi-response','DeadlineExceeded') from None
            if value is None: raise self.process_failure('pi-response',self.reader_error or 'Disconnected')
            require(value.get('type') == 'response' and value.get('command') == command and value.get('success') is True,
                    'Pi command refused',4,details=diagnostic('pi-response','CommandRefused'))
            require(isinstance(value.get('data',{}),dict), 'Malformed Pi response',4,details=diagnostic('pi-response','InvalidResponse'))
            remaining(deadline,'pi-response')
            return value.get('data',{})
        except (OSError,ValueError) as error:
            raise self.process_failure('pi-write',type(error).__name__) from None
        finally:
            if locked: self.write_lock.release()
            with self.response_lock: self.responses.pop(identity,None)

    def check(self,deadline=None,state=None,active=False):
        deadline = deadline if deadline is not None else time.monotonic()+self.timeout
        state = state if state is not None else self.command('get_state',deadline)
        safety(state.get('sessionFile') == self.binding['session_file'] and state.get('sessionId') == self.session_id, 'Pi identity changed',True)
        require(state.get('model'), 'Existing Pi model unavailable',4,details=diagnostic('pi-model','ModelUnavailable'))
        require(not state.get('isCompacting') and not state.get('pendingMessageCount') and
                (active or not state.get('isStreaming')), 'Pi has unrelated streaming, compaction or queued messages',4,
                details=diagnostic('pi-session','SessionBusy'))
        return state

    @staticmethod
    def answer(message):
        content = message.get('content',[])
        safety(isinstance(content,list) and not any(p.get('type') == 'toolCall' for p in content), 'Pi tool restriction failure')
        result = '\n'.join(p.get('text','') for p in content if p.get('type') == 'text')
        document(result)
        return result

    def recover(self,request,deadline=None):
        deadline = deadline if deadline is not None else time.monotonic()+self.timeout
        state = self.check(deadline,active=True)
        messages = self.command('get_messages',deadline).get('messages')
        require(isinstance(messages,list), 'Pi history unavailable',4,details=diagnostic('pi-history','InvalidResponse'))
        match = None
        for index,message in enumerate(messages):
            if message.get('role') != 'user': continue
            for part in message.get('content',[]):
                if part.get('type') != 'text': continue
                try: marker = parse(part.get('text',''))
                except Refusal: continue
                if marker == request['marker']:
                    require(match is None, 'Ambiguous Pi request history',4,details=diagnostic('pi-history','AmbiguousHistory'))
                    match = index
        if match is not None:
            for message in messages[match+1:]:
                if message.get('role') == 'user': break
                if message.get('role') == 'assistant':
                    answer = self.answer(message)
                    if message.get('stopReason') in ('stop','length') and not state.get('isStreaming'):
                        return answer
        return None

    def send(self,request,deadline):
        # Queued terminal events from a recovered request cannot identify a new
        # answer. Drain old events and attribute every later settlement via history.
        while True:
            try: event = self.messages.get_nowait()
            except queue.Empty: break
            if isinstance(event,dict) and event.get('type') == 'message_end' and event.get('message',{}).get('role') == 'assistant':
                self.answer(event['message'])
        self.command('prompt',deadline,message=json.dumps(request['marker'],ensure_ascii=False))
        while remaining(deadline,'pi-events'):
            event = self.next(deadline)
            if event.get('type') == 'message_end' and event.get('message',{}).get('role') == 'assistant': self.answer(event['message'])
            if event.get('type') == 'agent_settled':
                answer = self.recover(request,deadline)
                if answer is not None: return answer

    def cancel(self,deadline):
        unsent = self.command('clear_queue',deadline)
        atomic(self.runtime/'pi-unsent.json',dump(unsent))
        self.command('abort',deadline); return True

    def close(self):
        if not hasattr(self,'process'): return
        if self.process.poll() is None:
            with contextlib.suppress(OSError): self.process.stdin.close()
            try: self.process.wait(timeout=.5)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                try: self.process.wait(timeout=.5)
                except subprocess.TimeoutExpired: self.process.kill(); self.process.wait(timeout=.5)
        for stream in (self.process.stdin,self.process.stdout,self.process.stderr):
            if stream:
                with contextlib.suppress(OSError,ValueError): stream.close()

class Companion:
    def __init__(self,workspace,payload):
        fields(payload, ('runtime_dir',), ('binding','startup_timeout_seconds','request_timeout_seconds'))
        self.workspace = workspace; self.runtime = validate_runtime(payload['runtime_dir'],workspace)
        for key in ('startup_timeout_seconds','request_timeout_seconds'):
            value = payload.get(key,30 if key.startswith('startup') else 60)
            require(type(value) in (int,float) and 0 < value <= 300, 'Deadline must be greater than zero and at most 300 seconds')
        self.timeout = payload.get('request_timeout_seconds',60); self.startup = payload.get('startup_timeout_seconds',30)
        self.binding = payload.get('binding'); validate_binding(self.binding,self.runtime)
        if self.binding: require(workspace.host == self.binding['kind'], 'Host and adapter binding disagree',3)
        record,_,_ = workspace.read()
        self.runtime.mkdir(parents=True,exist_ok=True,mode=0o700)
        validate_runtime(str(self.runtime),workspace)
        self.lock_file = self.runtime/'companion.lock'; no_symlink(self.lock_file)
        self.lock_fd = os.open(self.lock_file,os.O_CREAT | os.O_RDWR,0o600)
        self.adapter = None; self.mutex = threading.RLock(); self.generation = 0
        self.reason = None; self.chat_blocked = False; self.recovery_after = {}
        try:
            try: fcntl.flock(self.lock_fd,fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError: raise Refusal('Runtime already owned by a companion',3) from None
            owner_path = self.runtime/'owner.json'; no_symlink(owner_path)
            owner = runtime_owner(workspace,record)
            if owner_path.exists():
                require(owner_path.stat().st_size <= 16384 and parse(owner_path.read_bytes()) == owner, 'Runtime belongs to a different review',3)
            else:
                require(not any((self.runtime/name).exists() for name in ('binding.json','requests.json','pi-owner.json')),
                        'Refusing existing unowned runtime data',3)
                atomic(owner_path,dump(owner))
            self.journal = self.runtime/'requests.json'; self.binding_path = self.runtime/'binding.json'
            no_symlink(self.journal); no_symlink(self.binding_path)
            self.requests = read_journal(self.journal) if self.journal.exists() else {}
            if self.binding_path.exists(): require(parse(self.binding_path.read_bytes()) == self.binding, 'Explicit rebind required for changed session',3)
            else: atomic(self.binding_path,dump(self.binding))
            self.session_id = self.binding.get('session_id') if self.binding else None
            deadline = time.monotonic()+self.startup
            self.connect(deadline)
            for request in self.requests.values():
                if request['delivery_state'] == 'sent-unknown' and self.adapter: self.recover(request,deadline)
            self.persist()
        except Exception:
            self.close(); raise

    def connect(self,deadline):
        self.reason = None; self.chat_blocked = False
        if self.binding is None:
            self.reason = 'Agent chat is unavailable in document/comment mode.'; return
        try:
            cls = OpenCode if self.binding['kind'] == 'opencode' else Pi
            self.adapter = cls(self.binding,self.runtime,self.timeout,remaining(deadline,'adapter-startup'))
            self.session_id = self.adapter.session_id
        except Refusal as error:
            if error.code == 3: raise
            self.reason = str(error); self.adapter = None
            report('serve',error)

    def unresolved(self):
        return any(request['delivery_state'] in ('prepared','sent-unknown') and request['session_id'] is not None and not request.get('local_only',False)
                   for request in self.requests.values())

    def unavailable_reason(self):
        if self.reason: return self.reason
        if self.unresolved(): return 'A request has unresolved delivery; inspect its exact session before another send.'
        return None

    def capabilities(self):
        return {'document':True,'comments':True,
                'chat':self.adapter is not None and not self.chat_blocked and not self.unresolved(),
                'cancel':self.adapter is not None,'rebind':True}

    def persist(self): atomic(self.journal,dump(self.requests))

    def public_request(self,request):
        return {key:request.get(key) for key in ('request_id','session_id','delivery_state','response','recovery_error')}

    def remember_error(self,request,error):
        details = error.details or diagnostic('host-operation','Refusal')
        request['recovery_error'] = {'code':{2:'invalid-input',3:'refused',4:'unavailable'}[error.code],
                                     'message':str(error)[:256],'details':details}
        if details['error_class'] in ('IdentityMismatch','RestrictionFailure','AmbiguousHistory'):
            self.chat_blocked = True; self.reason = str(error)
        # minimal: at most one recovery attempt per second after a failure. This
        # avoids a refresh loop consuming repeated full transport budgets; an
        # explicit same-ID retry or fresh process may inspect immediately.
        self.recovery_after[request['request_id']] = time.monotonic()+min(1,self.timeout)
        self.persist(); report('feedback',error)

    def recover(self,request,deadline=None,force=False):
        deadline = deadline if deadline is not None else time.monotonic()+self.timeout
        with synchronized(self.mutex,deadline,'companion-lock'):
            if not force and time.monotonic() < self.recovery_after.get(request['request_id'],0): return
            adapter = self.adapter; generation = self.generation; session_id = self.session_id
        if adapter is None: return
        try:
            safety(request['session_id'] == session_id, 'Pending request belongs to a different session',True)
            answer = adapter.recover(request,deadline)
            with synchronized(self.mutex,deadline,'companion-lock'):
                safety(generation == self.generation and adapter is self.adapter, 'Bound session changed during recovery',True)
                if answer is not None:
                    request['response'] = answer; request['delivery_state'] = 'response-received'
                    request['recovery_error'] = None
                    self.recovery_after.pop(request['request_id'],None); self.persist()
        except Exception as error:
            error = error if isinstance(error,Refusal) else failure('history-recovery',error)
            with synchronized(self.mutex,deadline,'companion-lock'): self.remember_error(request,error)

    def state(self):
        deadline = time.monotonic()+self.timeout
        with synchronized(self.mutex,deadline,'companion-lock'): pending = [request for request in self.requests.values() if request['delivery_state'] == 'sent-unknown']
        for request in pending: self.recover(request,deadline)
        with synchronized(self.mutex,deadline,'companion-lock'):
            record,content,state_hash = self.workspace.read()
            checkpoint = self.workspace.status(record,content,state_hash)[0]
            checkpoint['pending_delivery_counts'] = {name:0 for name in DELIVERIES}; checkpoint['delivery_coverage'] = 'complete'
            for request in self.requests.values(): checkpoint['pending_delivery_counts'][request['delivery_state']] += 1
            return {'checkpoint':checkpoint,'document':content,'revision':hashtext(content),
                    'binding':{'kind':self.binding['kind'],'session_id':self.session_id} if self.binding else None,
                    'capabilities':self.capabilities(),'unavailable_reason':self.unavailable_reason(),
                    'feedback':record['feedback'],'requests':[self.public_request(r) for r in self.requests.values()]}

    def cancel(self,payload):
        deadline = time.monotonic()+self.timeout
        fields(payload, ('request_id','session_id'))
        with synchronized(self.mutex,deadline,'companion-lock'):
            request = self.requests.get(payload['request_id'])
            require(request is not None and payload['session_id'] == self.session_id == request['session_id'], 'Unknown request/session',3)
            request['cancel_requested'] = True; self.persist()
            adapter = self.adapter
        acknowledged = False
        if adapter:
            try: acknowledged = adapter.cancel(deadline)
            except Refusal as error:
                with synchronized(self.mutex,deadline,'companion-lock'): self.remember_error(request,error)
        with synchronized(self.mutex,deadline,'companion-lock'):
            request['cancel_acknowledged'] = acknowledged; self.persist()
            return dict(self.public_request(request),cancel_acknowledged=acknowledged)

    def dispatch(self,route,payload):
        deadline = time.monotonic()+(self.startup if route == 'rebind' else self.timeout)
        if route == 'feedback': return self.feedback(payload)
        if route == 'cancel': return self.cancel(payload)
        with synchronized(self.mutex,deadline,'companion-lock'):
            if route == 'document':
                fields(payload, ('base_revision','content')); document(payload['content']); valid_hash(payload['base_revision'])
                with self.workspace.locked(strict=True,deadline=deadline):
                    _,content,_ = self.workspace.read()
                    require(payload['base_revision'] == hashtext(content), 'Document changed; preserve your draft for comparison',3)
                    atomic(self.workspace.review,payload['content'].encode())
                return {'revision':hashtext(payload['content'])}
            if route == 'checkpoint': return self.workspace.checkpoint(payload,deadline=deadline)
            if route == 'rebind':
                fields(payload, ('expected_session_id','new_binding','source_ref'))
                text(payload['source_ref']); validate_binding(payload['new_binding'],self.runtime)
                require(payload['expected_session_id'] == self.session_id, 'Session changed',3)
                require(not self.unresolved(), 'Resolve in-flight requests before rebinding',3)
                next_binding = payload['new_binding']
                require(next_binding is None or next_binding['kind'] == self.workspace.host, 'Host adapter mismatch',3)
                if next_binding and next_binding['kind'] == 'pi' and next_binding != self.binding:
                    require(not Path(next_binding['session_file']).exists(), 'New Pi binding must use a fresh dedicated session',3)
                if self.adapter: self.adapter.close()
                if next_binding and next_binding['kind'] == 'pi' and next_binding != self.binding:
                    atomic(self.runtime/'pi-owner.json',dump({'binding':next_binding,'session_id':None}))
                self.generation += 1; self.adapter = None; self.binding = next_binding
                self.session_id = next_binding.get('session_id') if next_binding else None
                atomic(self.binding_path,dump(self.binding)); self.connect(deadline)
                return {'session_id':self.session_id,'capabilities':self.capabilities(),'unavailable_reason':self.unavailable_reason()}
            raise Refusal('Unknown route',2,404)

    def feedback(self,payload):
        deadline = time.monotonic()+self.timeout
        fields(payload, ('id','session_id','base_revision','selection','comment'))
        text(payload['id'],512); valid_hash(payload['base_revision']); text(payload['comment']); text(payload['selection'],nullable=True)
        require(payload['selection'] is None or payload['selection'] != '', 'Empty selection is ambiguous')
        # Reserve before any blocking preflight, atomically with rebind. The local
        # adapter/generation below never follow a later self.adapter replacement.
        locked = self.mutex.acquire(timeout=remaining(deadline,'feedback-reservation'))
        require(locked, 'Feedback reservation deadline exceeded',4,details=diagnostic('feedback-reservation','DeadlineExceeded'))
        try:
            require(payload['session_id'] == self.session_id, 'Bound session identity mismatch',3)
            existing = self.requests.get(payload['id'])
            if existing:
                require(existing['payload'] == payload, 'Request ID reused with changed content',3)
                request = existing; adapter = None; generation = self.generation
            else:
                require(len(self.requests) < 200, 'Runtime request limit reached; archive explicitly')
                adapter = self.adapter if not self.unresolved() else None; generation = self.generation
                if adapter: require(not self.unresolved(), 'Inspect pending delivery before another send',3)
                with self.workspace.locked(strict=True,deadline=deadline):
                    record,content,_ = self.workspace.read()
                    remaining(deadline,'feedback-reservation')
                    require(hashtext(content) == payload['base_revision'], 'Document changed; preserve feedback draft',3)
                    require(payload['selection'] is None or content.count(payload['selection']) == 1, 'Selection must identify one exact passage')
                    require(len(record['feedback']) < 200, 'Feedback limit reached; archive explicitly')
                    require(not any(f['id'] == payload['id'] for f in record['feedback']), 'Feedback identity already exists',3)
                    request = {'request_id':payload['id'],'session_id':self.session_id,'delivery_state':'prepared','response':None,
                               'recovery_error':None,'local_only':adapter is None,'payload':payload,'marker':{'review_request_id':payload['id'],
                               'base_revision':payload['base_revision'],'selection':payload['selection'],'comment':payload['comment']}}
                    self.requests[payload['id']] = request; self.persist()
                    record['feedback'].append({'id':payload['id'],'source_ref':'local review feedback '+payload['id'],
                        'source_revision':payload['base_revision'],'author':None,
                        'selection':{'status':'attached','text':payload['selection']} if payload['selection'] is not None else None,
                        'text':payload['comment'],'disposition':'proposed','rationale':'Awaiting designated owner decision'})
                    atomic(self.workspace.state,dump(record))
        finally: self.mutex.release()
        if existing:
            if request['delivery_state'] == 'sent-unknown': self.recover(request,deadline,force=True)
            with synchronized(self.mutex,deadline,'companion-lock'): return self.public_request(request)
        if adapter is None:
            with synchronized(self.mutex,deadline,'companion-lock'): return self.public_request(request)
        possible_send = False
        try:
            adapter.check(deadline)
            with synchronized(self.mutex,deadline,'companion-lock'):
                safety(generation == self.generation and adapter is self.adapter and payload['session_id'] == self.session_id,
                       'Bound session changed before sending',True)
                remaining(deadline,'feedback-send')
                self.chat_blocked = False; self.reason = None
                if request.get('cancel_requested'):
                    request['delivery_state'] = 'failed-before-send'; self.persist(); return self.public_request(request)
                request['delivery_state'] = 'sent-unknown'; self.persist(); possible_send = True
            answer = adapter.send(request,deadline)
            with synchronized(self.mutex,deadline,'companion-lock'):
                safety(generation == self.generation and adapter is self.adapter, 'Bound session changed during send',True)
                if answer is not None:
                    request['delivery_state'] = 'response-received'; request['response'] = answer
                    request['recovery_error'] = None
                self.persist()
        except Exception as error:
            error = error if isinstance(error,Refusal) else failure('feedback-transport',error)
            with synchronized(self.mutex,deadline,'companion-lock'):
                if not possible_send: request['delivery_state'] = 'failed-before-send'
                self.remember_error(request,error)
            if not possible_send or error.details.get('error_class') in ('RestrictionFailure','IdentityMismatch'):
                raise
        with synchronized(self.mutex,deadline,'companion-lock'): return self.public_request(request)

    def close(self):
        if self.adapter: self.adapter.close()
        with contextlib.suppress(OSError): os.close(self.lock_fd)

    def serve(self):
        companion = self
        token = secrets.token_urlsafe(32)
        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.0'
            def log_message(self,*args): pass
            def reply(self,status,value,content_type='application/json; charset=utf-8'):
                body = value if isinstance(value,bytes) else dump(value)
                self.send_response(status)
                self.send_header('Content-Type',content_type); self.send_header('Content-Length',str(len(body)))
                self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Cache-Control','no-store')
                self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
                self.end_headers()
                with contextlib.suppress(BrokenPipeError,ConnectionResetError): self.wfile.write(body)
            def handle_route(self):
                operation = self.path.removeprefix('/')
                try:
                    require(self.headers.get('Host') == origin.removeprefix('http://'), 'Bound Host required',2,403)
                    if self.command == 'GET' and self.path == '/':
                        _,content,_ = companion.workspace.read()
                        return self.reply(200,companion.workspace.render(content,online=True),'text/html; charset=utf-8')
                    if self.command == 'GET' and self.path == '/state':
                        return self.reply(200,envelope('state',companion.state()))
                    routes = {('PUT','/document'),('POST','/feedback'),('POST','/checkpoint'),('POST','/cancel'),('POST','/rebind')}
                    require((self.command,self.path) in routes, 'Unknown route or method',2,404)
                    require(self.headers.get('Origin') == origin and secrets.compare_digest(self.headers.get('X-Review-Token',''),token), 'Exact Origin and write token required',2,403)
                    require(not self.headers.get('Transfer-Encoding'), 'Transfer encoding unsupported')
                    length = self.headers.get('Content-Length','')
                    require(length.isdecimal(), 'Content-Length required')
                    limit = EDIT_LIMIT if self.path == '/document' else FEEDBACK_LIMIT
                    self.connection.settimeout(5)
                    if int(length) > limit:
                        # Drain a bounded small overflow so ordinary clients can read the
                        # refusal rather than losing it to a closed-socket write race.
                        remaining = min(int(length), 1024 * 1024)
                        while remaining:
                            chunk = self.rfile.read(min(remaining,65536))
                            if not chunk: break
                            remaining -= len(chunk)
                        raise Refusal('Serialized request exceeds limit; preserve draft and split explicitly',2,413)
                    payload = parse(self.rfile.read(int(length)))
                    return self.reply(200,envelope(operation,companion.dispatch(operation,payload)))
                except Refusal as exc:
                    report(operation,exc); self.reply(exc.http,envelope(operation,error=exc))
                except Exception as error:
                    exc = failure('http-operation',error)
                    report(operation,exc); self.reply(502,envelope(operation,error=exc))
            do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = handle_route
        class ReviewServer(ThreadingHTTPServer):
            # minimal: sixteen local connections; reject excess sockets instead of
            # growing an unbounded thread pool. A queued worker pool can lift this ceiling.
            slots = threading.BoundedSemaphore(16)
            def get_request(self):
                connection,address = super().get_request()
                connection.settimeout(5)
                return connection,address
            def process_request(self,request,address):
                if not self.slots.acquire(blocking=False):
                    self.shutdown_request(request); return
                try: super().process_request(request,address)
                except Exception:
                    self.slots.release(); raise
            def process_request_thread(self,request,address):
                try: super().process_request_thread(request,address)
                finally: self.slots.release()
        try: server = ReviewServer(('127.0.0.1',0),Handler)
        except Exception:
            self.close(); raise
        server.daemon_threads = True
        origin = 'http://127.0.0.1:' + str(server.server_port)
        startup = {'origin':origin,'write_token':token,'session_id':self.session_id,'capabilities':self.capabilities()}
        startup['unavailable_reason'] = self.unavailable_reason()
        print(json.dumps(envelope('serve',startup)),flush=True)
        def stop(signum,frame): raise KeyboardInterrupt()
        old = signal.signal(signal.SIGTERM,stop)
        try: server.serve_forever(poll_interval=.2)
        except KeyboardInterrupt: pass
        finally:
            signal.signal(signal.SIGTERM,old); server.server_close(); self.close()


def main():
    class Parser(argparse.ArgumentParser):
        def error(self,message): raise Refusal('Invalid command arguments')
    parser = Parser(description=__doc__)
    parser.add_argument('operation',choices=('init','inspect','checkpoint','export','serve'))
    parser.add_argument('--root',required=True); parser.add_argument('--plan',required=True)
    parser.add_argument('--host',required=True,choices=sorted(HOSTS)); parser.add_argument('--input-json',required=True)
    try:
        args = parser.parse_args()
    except Refusal as exc:
        print(json.dumps(envelope(sys.argv[1] if len(sys.argv) > 1 else 'unknown',error=exc)))
        return exc.code
    try:
        if args.input_json == '-': raw = sys.stdin.buffer.read(64 * 1024 * 1024 + 1)
        else:
            path = Path(args.input_json); require(path.stat().st_size <= 64 * 1024 * 1024,'Input exceeds bound')
            raw = path.read_bytes()
        require(len(raw) <= 64 * 1024 * 1024,'Input exceeds bound')
        payload = parse(raw)
        workspace = Workspace(args.root,args.plan,args.host)
        if args.operation == 'serve':
            Companion(workspace,payload).serve(); return 0
        result = getattr(workspace,args.operation)(payload)
        print(json.dumps(envelope(args.operation,result),ensure_ascii=False)); return 0
    except Refusal as exc:
        report(args.operation,exc)
        print(json.dumps(envelope(args.operation,error=exc))); return exc.code
    except Exception as error:
        exc = failure('cli-operation',error)
        report(args.operation,exc)
        print(json.dumps(envelope(args.operation,error=exc))); return 4


if __name__ == '__main__':
    sys.exit(main())
