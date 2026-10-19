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
    def __init__(self, message, code=2, http=None):
        super().__init__(message)
        self.code = code
        self.http = http or {2:400, 3:409, 4:502}[code]


def require(condition, message, code=2, http=None):
    if not condition:
        raise Refusal(message, code, http)


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
                                               'message':str(error), 'details':{}}}


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
    def locked(self, strict=False):
        # Lock the directory inode without adding helper files to durable content.
        # minimal: serialize review operations within this plans directory; per-quest
        # locks can improve throughput if needed. External editors use hash guards.
        fd = os.open(self.plan.parent, os.O_RDONLY)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
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
            require(common['snapshot_path'] == self.rel(self.snapshots/'common.md'), 'Invalid common snapshot path', 3)
            path = self.snapshots/'common.md'
            require(path.is_file() and path.stat().st_size <= DOC_LIMIT and digest(path.read_bytes()) == common['normalized_sha256'],
                    'Common snapshot does not match its record', 3)
        if cp['pending'] is not None:
            pending = fields(cp['pending'], ('id','merged_sha256','snapshot_path','required_saves','hosted_saved','source_ref','hosted_revision','feedback','decisions'))
            text(pending['id'],512); valid_hash(pending['merged_sha256'])
            require(pending['snapshot_path'] == self.rel(self.snapshots/'pending.md'), 'Invalid pending snapshot', 3)
            path = self.snapshots/'pending.md'
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
            base = (self.snapshots/'common.md').read_bytes().decode('utf-8')
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
                runtime = validate_runtime(payload['runtime_dir'],self)
                require(runtime.is_dir(), 'Runtime inspection unavailable',4)
                owner = runtime/'owner.json'; journal = runtime/'requests.json'
                no_symlink(owner); no_symlink(journal)
                require(owner.is_file() and journal.is_file(), 'Runtime ownership or journal unavailable',4)
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

    def checkpoint(self, payload):
        fields(payload, ('phase','expected_state_hash','expected_review_hash'), ('observation','checkpoint_id','decisions','resolution','receipt'))
        require(payload['phase'] in ('prepare','complete'), 'Invalid checkpoint phase')
        with self.locked(strict=True):
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
                pending = {'id':uuid.uuid4().hex,'merged_sha256':hashtext(merged),
                           'snapshot_path':self.rel(self.snapshots/'pending.md'),'required_saves':required,
                           'hosted_saved':False,'source_ref':obs['source_ref'] if obs else 'local review checkpoint',
                           'hosted_revision':obs['revision'] if obs else None,'feedback':feedback,'decisions':combined}
                cp['pending'] = pending
                cp['state'] = 'pending-local-save' if 'local' in required else 'pending-hosted-save'
                self.snapshots.mkdir(exist_ok=True)
                changed = [self.rel(self.snapshots/'pending.md'),self.rel(self.state)]
                atomic(self.snapshots/'pending.md',merged.encode())
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
            merged = (self.snapshots/'pending.md').read_bytes()
            atomic(self.snapshots/'common.md',merged)
            cp['common'] = {'local_sha256':hashtext(content),'normalized_sha256':pending['merged_sha256'],
                            'hosted_revision':pending['hosted_revision'],'source_ref':pending['source_ref'],
                            'snapshot_path':self.rel(self.snapshots/'common.md')}
            record['feedback'] = pending['feedback']; record['decisions'] = pending['decisions']
            cp['state'] = 'clean'; cp['pending'] = None
            atomic(self.state,dump(record))
            return {'state':'clean','checkpoint_id':pending['id'],'changed_paths':[self.rel(self.state),self.rel(self.snapshots/'common.md')]}

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


def validate_runtime(value, workspace):
    runtime = Path(text(value,4096))
    require(runtime.is_absolute() and '..' not in runtime.parts, 'Runtime must be an absolute directory',3)
    no_symlink(runtime)
    runtime = runtime.resolve()
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
        fields(request, ('request_id','session_id','delivery_state','response','payload','marker'), ('cancel_acknowledged',))
        text(identity,512)
        require(request['request_id'] == identity and request['delivery_state'] in DELIVERIES, 'Invalid runtime request identity/state',3)
        text(request['session_id'],512,nullable=True); text(request['response'],DOC_LIMIT,nullable=True,empty=True)
        fields(request['payload'], ('id','session_id','base_revision','selection','comment'))
        fields(request['marker'], ('review_request_id','base_revision','selection','comment'))
        require(request['payload']['id'] == identity and request['payload']['session_id'] == request['session_id'] and
                request['marker'] == {'review_request_id':identity, **{key:request['payload'][key] for key in ('base_revision','selection','comment')}},
                'Invalid runtime request marker',3)
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
    def __init__(self, binding, runtime, timeout, startup):
        self.binding = binding; self.session_id = binding['session_id']; self.timeout = timeout
        self.path = '/session/' + quote(self.session_id, safe='')
        self.startup_deadline = time.monotonic() + startup
        self.check(startup)
        self.startup_deadline = None

    def request(self, method, path, value=None, timeout=None):
        origin = urlsplit(self.binding['base_url'])
        budget = timeout or self.timeout
        if self.startup_deadline is not None:
            budget = min(budget,max(.001,self.startup_deadline-time.monotonic()))
        connection = http.client.HTTPConnection(origin.hostname,origin.port,timeout=budget)
        try:
            body = json.dumps(value).encode() if value is not None else None
            connection.request(method,path,body,{'Content-Type':'application/json'})
            reply = connection.getresponse()
            require(200 <= reply.status < 300, 'Host operation unavailable',4)
            raw = reply.read(2 * 1024 * 1024 + 1)
            require(len(raw) <= 2 * 1024 * 1024, 'Host response exceeds bound',4)
            return parse(raw)
        except (OSError,http.client.HTTPException,TimeoutError):
            raise Refusal('Host transport unavailable',4) from None
        finally:
            connection.close()

    def check(self, timeout=None):
        session = self.request('GET',self.path,timeout=timeout)
        require(isinstance(session,dict) and session.get('id') == self.session_id, 'Host session identity changed',3)
        require(session.get('permission') == [{'permission':'*','pattern':'*','action':'deny'}], 'Tool-free session permissions unavailable',4)
        tools = self.request('GET','/experimental/tool/ids',timeout=timeout)
        require(isinstance(tools,list) and len(tools) <= 1000 and all(isinstance(tool,str) and len(tool) <= 512 for tool in tools), 'Tool inventory unavailable',4)
        self.tools = {tool:False for tool in tools}
        model = session.get('model')
        if not isinstance(model,dict) or not model.get('providerID') or not model.get('id'):
            history = self.history()
            model = next(({'providerID':m['info']['model'].get('providerID'), 'id':m['info']['model'].get('modelID')}
                          for m in reversed(history) if m.get('info',{}).get('role') == 'user' and isinstance(m['info'].get('model'),dict)),None)
        require(isinstance(model,dict) and model.get('providerID') and model.get('id'), 'Existing selected model unavailable',4)
        self.model = {'providerID':model['providerID'],'modelID':model['id']}

    def history(self):
        value = self.request('GET',self.path+'/message')
        require(isinstance(value,list), 'Host history unavailable',4)
        return value

    def recover(self, request):
        history = self.history()
        users = []
        for message in history:
            info = message.get('info',{})
            if info.get('role') != 'user': continue
            for part in message.get('parts',[]):
                if part.get('type') == 'text':
                    try: marker = parse(part.get('text',''))
                    except Refusal: continue
                    if marker == request['marker']: users.append(info.get('id'))
        require(len(users) <= 1, 'Ambiguous host request history',4)
        if not users: return None
        for message in history:
            info = message.get('info',{})
            if info.get('role') == 'assistant' and info.get('parentID') == users[0] and info.get('time',{}).get('completed'):
                require(not any(p.get('type') in ('tool','toolCall') for p in message.get('parts',[])), 'Host tool restriction failure',4)
                answer = '\n'.join(p.get('text','') for p in message.get('parts',[]) if p.get('type') == 'text')
                text(answer,DOC_LIMIT,empty=True)
                return answer
        return None

    def send(self, request):
        try:
            self.request('POST',self.path+'/message',{'parts':[{'type':'text','text':json.dumps(request['marker'],ensure_ascii=False)}],
                                                     'tools':self.tools,'model':self.model})
        except Refusal:
            # A transport failure is never permission to retry a possibly accepted prompt.
            pass
        return self.recover(request)

    def cancel(self): return self.request('POST',self.path+'/abort',{}) is True
    def close(self): pass


class Pi:
    def __init__(self,binding,runtime,timeout,startup):
        self.binding = binding; self.runtime = runtime; self.timeout = timeout
        session = Path(binding['session_file']); marker = runtime/'pi-owner.json'
        no_symlink(marker)
        if marker.exists():
            require(parse(marker.read_bytes()) == binding, 'Pi runtime ownership mismatch; explicit rebind required',3)
        else:
            require(not session.exists(), 'Refusing an existing unowned Pi/TUI session',3)
            atomic(marker,dump(binding))
        executable = shutil.which('pi')
        require(executable is not None, 'Existing Pi executable unavailable',4)
        session.parent.mkdir(parents=True,exist_ok=True)
        self.process = subprocess.Popen([executable,'--mode','rpc','--session',str(session),'--no-tools','--no-extensions',
            '--no-mcp','--no-skills','--no-prompt-templates','--no-themes','--no-context-files','--no-approve','--offline'],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,bufsize=0)
        self.messages = queue.Queue(maxsize=2048)
        self.responses = {}
        self.response_lock = threading.Lock()
        self.write_lock = threading.Lock()
        self.reader_error = None
        self.reader = threading.Thread(target=self.read_loop,daemon=True); self.reader.start()
        try:
            state = self.command('get_state',timeout=startup)
            require(state.get('sessionFile') == str(session) and isinstance(state.get('sessionId'),str), 'Pi session identity mismatch',3)
            self.session_id = state['sessionId']
            require(state.get('model'), 'Existing Pi model unavailable',4)
            self.check(state=state)
        except Exception:
            self.close(); raise

    def read_loop(self):
        try:
            while True:
                raw = self.process.stdout.readline(2 * 1024 * 1024 + 1)
                if not raw: break
                if len(raw) > 2 * 1024 * 1024: raise ValueError()
                item = parse(raw)
                if item.get('type') == 'response':
                    with self.response_lock:
                        target = self.responses.get(item.get('id'))
                    if target is not None: target.put(item,timeout=1)
                else:
                    self.messages.put(item,timeout=1)
        except Exception:
            self.reader_error = True
        finally:
            with contextlib.suppress(queue.Full): self.messages.put_nowait(None)

    def next(self, deadline):
        try: item = self.messages.get(timeout=max(.001,deadline-time.monotonic()))
        except queue.Empty: raise Refusal('Pi response timeout; delivery remains unknown',4) from None
        require(isinstance(item,dict), 'Pi disconnected; delivery remains unknown',4)
        return item

    def command(self, command, timeout=None, **extra):
        identity = uuid.uuid4().hex
        target = queue.Queue(maxsize=1)
        require(self.process.poll() is None, 'Pi process disconnected',4)
        with self.response_lock: self.responses[identity] = target
        try:
            try:
                with self.write_lock:
                    self.process.stdin.write((json.dumps({'id':identity,'type':command,**extra})+'\n').encode())
                    self.process.stdin.flush()
            except (OSError,BrokenPipeError): raise Refusal('Pi disconnected',4) from None
            try: value = target.get(timeout=timeout or self.timeout)
            except queue.Empty: raise Refusal('Pi command timeout; delivery remains unknown',4) from None
            require(value.get('type') == 'response' and value.get('command') == command and value.get('success') is True,
                    'Pi command refused',4)
            data = value.get('data',{})
            require(isinstance(data,dict), 'Malformed Pi response',4)
            return data
        finally:
            with self.response_lock: self.responses.pop(identity,None)

    def check(self, state=None, active=False):
        state = state if state is not None else self.command('get_state')
        require(state.get('sessionFile') == self.binding['session_file'] and state.get('sessionId') == self.session_id, 'Pi identity changed',3)
        require(state.get('model'), 'Existing Pi model unavailable',4)
        require(not state.get('isCompacting') and not state.get('pendingMessageCount') and
                (active or not state.get('isStreaming')), 'Pi has unrelated streaming, compaction or queued messages',4)

    @staticmethod
    def answer(message):
        content = message.get('content',[])
        require(isinstance(content,list) and not any(p.get('type') == 'toolCall' for p in content), 'Pi tool restriction failure',4)
        result = '\n'.join(p.get('text','') for p in content if p.get('type') == 'text')
        text(result,DOC_LIMIT,empty=True)
        return result

    def recover(self, request):
        messages = self.command('get_messages').get('messages')
        require(isinstance(messages,list), 'Pi history unavailable',4)
        match = None
        for index,message in enumerate(messages):
            if message.get('role') != 'user': continue
            for part in message.get('content',[]):
                if part.get('type') != 'text': continue
                try: marker = parse(part.get('text',''))
                except Refusal: continue
                if marker == request['marker']:
                    require(match is None, 'Ambiguous Pi request history',4); match = index
        if match is not None:
            for message in messages[match+1:]:
                if message.get('role') == 'user': break
                if message.get('role') == 'assistant' and message.get('stopReason') in ('stop','length'):
                    # History recovery also requires the observed session to be settled.
                    self.check()
                    return self.answer(message)
        return None

    def send(self, request):
        self.command('prompt',message=json.dumps(request['marker'],ensure_ascii=False))
        deadline = time.monotonic() + self.timeout; answer = None
        while time.monotonic() < deadline:
            event = self.next(deadline)
            if event.get('type') == 'message_end' and event.get('message',{}).get('role') == 'assistant':
                answer = self.answer(event['message'])
            if event.get('type') == 'agent_settled' and answer is not None: return answer
        return None

    def cancel(self):
        unsent = self.command('clear_queue')
        # Runtime-only queue evidence; never put raw session material in the bundle.
        atomic(self.runtime/'pi-unsent.json',dump(unsent))
        self.command('abort'); return True

    def close(self):
        if not hasattr(self,'process'): return
        if self.process.poll() is None:
            with contextlib.suppress(OSError): self.process.stdin.close()
            try: self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                try: self.process.wait(timeout=1)
                except subprocess.TimeoutExpired: self.process.kill(); self.process.wait()
        for stream in (self.process.stdin,self.process.stdout):
            if stream:
                with contextlib.suppress(OSError): stream.close()


class Companion:
    def __init__(self, workspace, payload):
        fields(payload, ('runtime_dir',), ('binding','startup_timeout_seconds','request_timeout_seconds'))
        self.workspace = workspace
        self.runtime = validate_runtime(payload['runtime_dir'],workspace)
        for key in ('startup_timeout_seconds','request_timeout_seconds'):
            value = payload.get(key,30 if key.startswith('startup') else 60)
            require(type(value) in (int,float) and 0 < value <= 300, 'Deadline must be greater than zero and at most 300 seconds')
        self.timeout = payload.get('request_timeout_seconds',60); self.startup = payload.get('startup_timeout_seconds',30)
        self.binding = payload.get('binding'); validate_binding(self.binding,self.runtime)
        if self.binding:
            require(workspace.host == self.binding['kind'], 'Host and adapter binding disagree',3)
        record,_,_ = workspace.read()
        self.runtime.mkdir(parents=True,exist_ok=True,mode=0o700)
        require(self.runtime.is_dir(), 'Runtime directory unavailable',3)
        self.lock_file = self.runtime/'companion.lock'; no_symlink(self.lock_file)
        self.lock_fd = os.open(self.lock_file, os.O_CREAT | os.O_RDWR,0o600)
        try: fcntl.flock(self.lock_fd,fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: os.close(self.lock_fd); raise Refusal('Runtime already owned by a companion',3) from None
        owner_path = self.runtime/'owner.json'; no_symlink(owner_path)
        owner = runtime_owner(workspace,record)
        if owner_path.exists():
            require(owner_path.stat().st_size <= 16384 and parse(owner_path.read_bytes()) == owner,
                    'Runtime belongs to a different review',3)
        else:
            require(not any((self.runtime/name).exists() for name in ('binding.json','requests.json','pi-owner.json')),
                    'Refusing existing unowned runtime data',3)
            atomic(owner_path,dump(owner))
        self.journal = self.runtime/'requests.json'; self.binding_path = self.runtime/'binding.json'
        no_symlink(self.journal); no_symlink(self.binding_path)
        self.requests = read_journal(self.journal) if self.journal.exists() else {}
        require(isinstance(self.requests,dict) and len(self.requests) <= 200, 'Runtime request journal exceeds bounds',3)
        if self.binding_path.exists():
            require(parse(self.binding_path.read_bytes()) == self.binding, 'Explicit rebind required for changed session',3)
        else: atomic(self.binding_path,dump(self.binding))
        self.adapter = None; self.reason = None; self.session_id = self.binding.get('session_id') if self.binding else None
        self.mutex = threading.RLock()
        self.connect()
        for request in self.requests.values():
            if request['delivery_state'] == 'sent-unknown' and self.adapter:
                self.recover(request)
        self.persist()

    def connect(self):
        self.reason = None
        if self.binding is None:
            self.reason = 'Agent chat is unavailable in document/comment mode.'; return
        try:
            cls = OpenCode if self.binding['kind'] == 'opencode' else Pi
            self.adapter = cls(self.binding,self.runtime,self.timeout,self.startup)
            self.session_id = self.adapter.session_id
        except Refusal as exc:
            if exc.code == 3: raise
            self.reason = str(exc); self.adapter = None

    def capabilities(self):
        return {'document':True,'comments':True,'chat':self.adapter is not None,
                'cancel':self.adapter is not None,'rebind':True}

    def persist(self): atomic(self.journal,dump(self.requests))

    def public_request(self, request):
        return {key:request[key] for key in ('request_id','session_id','delivery_state','response')}

    def recover(self, request):
        try:
            require(request['session_id'] == self.session_id, 'Pending request belongs to a different session',3)
            answer = self.adapter.recover(request)
            if answer is not None:
                request['response'] = answer; request['delivery_state'] = 'response-received'; self.persist()
        except Refusal:
            # Unknown delivery remains recorded; never replay on history failure.
            pass

    def state(self):
        with self.mutex:
            for request in self.requests.values():
                if request['delivery_state'] == 'sent-unknown' and self.adapter: self.recover(request)
            record,content,state_hash = self.workspace.read()
            checkpoint = self.workspace.status(record,content,state_hash)[0]
            checkpoint['pending_delivery_counts'] = {name:0 for name in DELIVERIES}
            checkpoint['delivery_coverage'] = 'complete'
            for request in self.requests.values():
                checkpoint['pending_delivery_counts'][request['delivery_state']] += 1
            return {'checkpoint':checkpoint,'document':content,'revision':hashtext(content),
                    'binding':{'kind':self.binding['kind'],'session_id':self.session_id} if self.binding else None,
                    'capabilities':self.capabilities(),'feedback':record['feedback'],
                    'requests':[self.public_request(r) for r in self.requests.values()]}

    def dispatch(self, route, payload):
        if route == 'feedback': return self.feedback(payload)
        with self.mutex:
            if route == 'document':
                fields(payload, ('base_revision','content')); document(payload['content']); valid_hash(payload['base_revision'])
                with self.workspace.locked(strict=True):
                    _,content,_ = self.workspace.read()
                    require(payload['base_revision'] == hashtext(content), 'Document changed; preserve your draft for comparison',3)
                    atomic(self.workspace.review,payload['content'].encode())
                return {'revision':hashtext(payload['content'])}
            if route == 'checkpoint':
                return self.workspace.checkpoint(payload)
            if route == 'cancel':
                fields(payload, ('request_id','session_id'))
                request = self.requests.get(payload['request_id'])
                require(request is not None and payload['session_id'] == self.session_id == request['session_id'], 'Unknown request/session',3)
                acknowledged = False
                if self.adapter:
                    try: acknowledged = self.adapter.cancel()
                    except Refusal: pass
                request['cancel_acknowledged'] = acknowledged; self.persist()
                return dict(self.public_request(request),cancel_acknowledged=acknowledged)
            if route == 'rebind':
                fields(payload, ('expected_session_id','new_binding','source_ref'))
                text(payload['source_ref']); validate_binding(payload['new_binding'],self.runtime)
                require(payload['expected_session_id'] == self.session_id, 'Session changed',3)
                require(not any(r['delivery_state'] in ('prepared','sent-unknown') and r['session_id'] is not None for r in self.requests.values()), 'Resolve in-flight requests before rebinding',3)
                require(payload['new_binding'] is None or payload['new_binding']['kind'] == self.workspace.host, 'Host adapter mismatch',3)
                next_binding = payload['new_binding']
                if next_binding and next_binding['kind'] == 'pi' and next_binding != self.binding:
                    require(not Path(next_binding['session_file']).exists(), 'New Pi binding must use a fresh dedicated session',3)
                if self.adapter: self.adapter.close()
                if next_binding and next_binding['kind'] == 'pi':
                    atomic(self.runtime/'pi-owner.json',dump(next_binding))
                self.adapter = None; self.binding = payload['new_binding']; self.session_id = None
                atomic(self.binding_path,dump(self.binding)); self.connect()
                return {'session_id':self.session_id,'capabilities':self.capabilities()}
            raise Refusal('Unknown route',2,404)

    def feedback(self,payload):
        fields(payload, ('id','session_id','base_revision','selection','comment'))
        text(payload['id'],512); valid_hash(payload['base_revision']); text(payload['comment']); text(payload['selection'],nullable=True)
        require(payload['selection'] is None or payload['selection'] != '', 'Empty selection is ambiguous')
        require(payload['session_id'] == self.session_id, 'Bound session identity mismatch',3)
        existing = self.requests.get(payload['id'])
        if existing:
            require(existing['payload'] == payload, 'Request ID reused with changed content',3)
            if existing['delivery_state'] == 'sent-unknown' and self.adapter: self.recover(existing)
            return self.public_request(existing)
        require(len(self.requests) < 200, 'Runtime request limit reached; archive explicitly')
        with self.workspace.locked(strict=True):
            record,content,_ = self.workspace.read()
            require(hashtext(content) == payload['base_revision'], 'Document changed; preserve feedback draft',3)
            require(payload['selection'] is None or content.count(payload['selection']) == 1, 'Selection must identify one exact passage')
            require(len(record['feedback']) < 200, 'Feedback limit reached; archive explicitly')
            require(not any(f['id'] == payload['id'] for f in record['feedback']), 'Feedback identity already exists',3)
            if self.adapter:
                require(not any(r['delivery_state'] in ('prepared','sent-unknown') and r['session_id'] is not None for r in self.requests.values()), 'Inspect pending delivery before another send',3)
                self.adapter.check()
            request = {'request_id':payload['id'],'session_id':self.session_id,'delivery_state':'prepared','response':None,
                       'payload':payload,'marker':{'review_request_id':payload['id'],'base_revision':payload['base_revision'],
                                                 'selection':payload['selection'],'comment':payload['comment']}}
            self.requests[payload['id']] = request; self.persist()
            record['feedback'].append({'id':payload['id'],'source_ref':'local review feedback '+payload['id'],
                'source_revision':payload['base_revision'],'author':None,
                'selection':{'status':'attached','text':payload['selection']} if payload['selection'] is not None else None,
                'text':payload['comment'],'disposition':'proposed','rationale':'Awaiting designated owner decision'})
            atomic(self.workspace.state,dump(record))
            if self.adapter:
                request['delivery_state'] = 'sent-unknown'; self.persist()
        if self.adapter:
            request['delivery_state'] = 'sent-unknown'; self.persist()
            try:
                answer = self.adapter.send(request)
                if answer is not None:
                    request['delivery_state'] = 'response-received'; request['response'] = answer
            except Refusal as exc:
                self.persist()
                if 'restriction' in str(exc):
                    self.reason = str(exc); self.adapter.close(); self.adapter = None
                    raise
                # Timeout/disconnect after possible delivery is a successful observation of unknown state.
            self.persist()
        return self.public_request(request)

    def close(self):
        if self.adapter: self.adapter.close()
        os.close(self.lock_fd)

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
                except Refusal as exc: self.reply(exc.http,envelope(operation,error=exc))
                except (OSError,UnicodeError,ValueError,TypeError,KeyError):
                    self.reply(502,envelope(operation,error=Refusal('Review operation unavailable; saved drafts retained',4)))
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
        if self.reason: startup['unavailable_reason'] = self.reason
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
        print(json.dumps(envelope(args.operation,error=exc))); return exc.code
    except (OSError,UnicodeError,ValueError,KeyError,TypeError,RecursionError):
        exc = Refusal('Review operation unavailable; no approval or completion inferred',4)
        print(json.dumps(envelope(args.operation,error=exc))); return 4


if __name__ == '__main__':
    sys.exit(main())
