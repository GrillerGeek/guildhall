#!/usr/bin/env python3
"""Offline policy discovery and explicit user-owned approval persistence.

JSON operations on stdin; no provider requests, worker dispatch or host changes.
The caller owns truthful host evidence and explicit user consent. Approval hashes
are references to reviewed evidence, not evidence verification or authentication.
"""
from __future__ import annotations

from contextlib import contextmanager
import copy
import json
import math
import os
from pathlib import Path
import runpy
import stat
import sys
import tempfile
import time

_R = runpy.run_path(str(Path(__file__).with_name('route_model.py')), run_name='_routing_config_engine')
canonical = _R['canonical']
digest = _R['policy_hash']
validate = _R['validate']
ROUTES = _R['ROUTES']
LIMIT = 1024 * 1024
OPT_OUT = dict(config_version=1, kind='guildhall-routing-override', mode='off')
OPT_OUT_SCHEMA = _R['obj'](config_version=_R['enum']([1]),
    kind=_R['enum'](['guildhall-routing-override']), mode=_R['enum'](['off']))
GLOBAL_SCHEMA = _R['obj'](config_version=_R['enum']([1]), hosts={
    'type': 'object', 'properties': {route: {'anyOf': [{'$ref': name + '.schema.json'} for name in
        ('policy', 'policy-v2', 'policy-v3', 'policy-v4')]}
        for route in ROUTES}, 'additionalProperties': False})
PATH_STRING = dict(type='string', minLength=1, maxLength=4096)
APPROVAL = _R['obj'](source_key=_R['HASH'], policy_hash=_R['HASH'],
    host_fingerprint=_R['HASH'], scope=PATH_STRING, approved_at=_R['NUMBER'],
    expires_at=_R['nullable'](_R['NUMBER']), evidence_hashes=_R['array'](_R['HASH'], 64))
APPROVAL_SCHEMA = _R['obj'](config_version=_R['enum']([1]),
    approvals=_R['array'](APPROVAL, 256))


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def clock(now):
    value = time.time() if now is None else now
    need(type(value) in (float, int) and math.isfinite(value) and value >= 0, 'invalid_clock')
    return value


def strict_json(raw):
    need(len(raw) <= LIMIT, 'configuration_too_large')
    def pairs(items):
        value = {}
        for key, item in items:
            need(key not in value, 'duplicate_json_key')
            value[key] = item
        return value
    def constant(_):
        raise ValueError('nonfinite_json')
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('invalid_json') from exc


def validate_global(value):
    need(type(value) is dict and set(value) == {'config_version', 'hosts'}, 'invalid_global_config')
    validate(value['config_version'], _R['enum']([1]))
    hosts = value['hosts']
    need(type(hosts) is dict and set(hosts) <= set(ROUTES), 'invalid_host_mapping')
    for policy in hosts.values():
        _R['validate_policy'](policy)


def validate_approvals(value):
    validate(value, APPROVAL_SCHEMA)
    need(len({a['source_key'] for a in value['approvals']}) == len(value['approvals']),
         'duplicate_approval_source')


def exists(path):
    # lstat distinguishes dangling links/unreadable paths from an absent file.
    try:
        path.lstat()
        return True
    except FileNotFoundError:
        return False


def safe_state_directory(directory):
    need(not directory.is_symlink(), 'unsafe_state_directory')
    if exists(directory):
        info = directory.stat()
        need(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
             and not info.st_mode & 0o022, 'unsafe_state_directory')


def read_json(path, *, private=False):
    if private:
        safe_state_directory(path.parent)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ValueError('unreadable_or_unsafe_file') from exc
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        need(stat.S_ISREG(info.st_mode), 'not_regular_file')
        if private:
            need(info.st_uid == os.getuid() and not info.st_mode & 0o077, 'unsafe_approval_permissions')
        value = strict_json(stream.read(LIMIT + 1))
        need(type(value) is dict, 'configuration_must_be_object')
        return value


@contextmanager
def locked_write(path):
    safe_state_directory(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    safe_state_directory(path.parent)
    lock = path.with_name(path.name + '.lock')
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError as exc:
        raise ValueError('configuration_busy: retry after the other writer finishes; inspect stale locks manually') from exc
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink()


def write_json(path, value, expected_revision, *, private=False):
    """Compare-and-swap under a bounded exclusive lock, then atomic replacement."""
    validate(expected_revision, _R['nullable'](_R['HASH']))
    raw = canonical(value)
    need(len(raw) <= LIMIT, 'configuration_too_large')
    with locked_write(path):
        current = read_json(path, private=private)
        need((digest(current) if current is not None else None) == expected_revision,
             'configuration_conflict: reread and review before retrying')
        fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False).encode() + b'\n')
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return digest(value)


class RoutingConfig:
    def __init__(self, project_root, host_route, *, home=None, environ=None,
                 policy_path=None, session_off=False):
        need(sys.version_info >= (3, 12), 'unsupported_runtime: Python 3.12+ required')
        need(host_route in ROUTES, 'unsupported_host_route')
        need(type(session_off) is bool, 'invalid_session_off')
        root = Path(project_root)
        need(root.is_absolute() and root.is_dir(), 'project_root_must_be_existing_absolute_directory')
        self.project = root.resolve()
        self.host_route = host_route
        env = os.environ if environ is None else environ
        user_home = Path.home() if home is None else Path(home)
        need(user_home.is_absolute(), 'home_must_be_absolute')
        xdg = env.get('XDG_CONFIG_HOME', '')
        base = Path(xdg) if xdg and Path(xdg).is_absolute() else user_home / '.config'
        self.global_path = base / 'guildhall/routing.json'
        self.approvals_path = base / 'guildhall/routing-approvals.json'
        self.project_path = self.project / '.guildhall/routing.json'
        self.explicit_path = Path(policy_path) if policy_path is not None else None
        if self.explicit_path is not None:
            need(self.explicit_path.is_absolute(), 'policy_path_must_be_absolute')
        self.session_off = session_off

    def resolve(self, *, target=None):
        # Targeted reads are explicit setup operations. Worker dispatch omits
        # target and always resolves the ordinary session/project/global chain.
        need(target in (None, 'global', 'project'), 'invalid_setup_target')
        need(target is None or not (self.session_off or self.explicit_path is not None),
             'setup_target_conflicts_with_session_selection')
        result = dict(source='none', source_path=None, scope=None, source_key=None,
                      policy=None, policy_hash=None, config_revision=None, reason='no_policy')
        if self.session_off:
            return dict(result, source='session', reason='router_disabled')
        if target == 'global':
            source, path = 'global', self.global_path
        elif target == 'project':
            source, path = 'project', self.project_path
        elif self.explicit_path is not None:
            source, path = 'explicit', self.explicit_path
        elif exists(self.project_path):
            source, path = 'project', self.project_path
        else:
            source, path = 'global', self.global_path
        value = read_json(path)
        if value is None:
            need(source == 'global' or target == 'project', 'selected_policy_missing')
            return result
        scope = 'all-projects' if source == 'global' else str(self.project)
        identity = dict(source=source, path=str(path.resolve()), scope=scope, host_route=self.host_route)
        result.update(source=source, source_path=identity['path'], scope=scope,
                      source_key=digest(identity), config_revision=digest(value))
        if source != 'global' and type(value) is dict and 'config_version' in value:
            validate(value, OPT_OUT_SCHEMA)
            return dict(result, reason='router_disabled')
        if source == 'global':
            validate_global(value)
            policy = value['hosts'].get(self.host_route)
            if policy is None:
                return dict(result, reason='no_host_policy')
        else:
            policy = value
            _R['validate_policy'](policy)
        return dict(result, policy=policy, policy_hash=digest(policy),
                    reason='router_disabled' if policy['mode'] == 'off' else 'policy_selected')

    def _host_fingerprint(self, host, version):
        schema = _R['REQUEST_SCHEMA_V3' if version >= 3 else 'REQUEST_SCHEMA']['properties']['host']
        validate(host, schema)
        need(host['route'] == self.host_route, 'host_route_mismatch')
        stable = {k: v for k, v in host.items() if k != 'evidence_hash'}
        stable['allowed_settings'] = sorted(stable['allowed_settings'], key=canonical)
        return digest(stable)

    def _approvals(self):
        value = read_json(self.approvals_path, private=True)
        if value is None:
            return dict(config_version=1, approvals=[]), None
        validate_approvals(value)
        return value, digest(value)

    def status(self, host=None, *, target=None, now=None):
        current = clock(now)
        result = self.resolve(target=target)
        result.update(host_fingerprint=None, approval_revision=None,
            activation=dict(policy_hash=None, external_requests=False,
                            summary_preview_hash=None, evidence_hashes=[]))
        if result['reason'] != 'policy_selected':
            return result
        if host is None:
            return dict(result, reason='host_evidence_required')
        fingerprint = self._host_fingerprint(host, result['policy']['schema_version'])
        approvals, revision = self._approvals()
        result.update(host_fingerprint=fingerprint, approval_revision=revision)
        record = next((a for a in approvals['approvals'] if a['source_key'] == result['source_key']), None)
        if record is None:
            return dict(result, reason='activation_required')
        if record['policy_hash'] != result['policy_hash']:
            return dict(result, reason='policy_changed')
        if record['host_fingerprint'] != fingerprint or record['scope'] != result['scope']:
            return dict(result, reason='host_changed')
        if record['expires_at'] is not None and record['expires_at'] <= current:
            return dict(result, reason='approval_expired')
        if host['evidence_hash'] is None or host['evidence_hash'] not in record['evidence_hashes']:
            return dict(result, reason='evidence_review_required')
        result['activation'].update(policy_hash=result['policy_hash'], external_requests=True,
                                    evidence_hashes=record['evidence_hashes'])
        return dict(result, reason='summary_approval_required' if result['policy']['data_mode'] == 'summary' else 'ready')

    def preview(self, policy, *, target):
        """Return the exact write proposal and revision without changing files."""
        need(target in ('global', 'project'), 'invalid_prepare_target')
        if policy == OPT_OUT:
            need(target == 'project', 'opt_out_is_project_only')
            validate(policy, OPT_OUT_SCHEMA)
        else:
            _R['validate_policy'](policy)
        if target == 'project':
            path, value = self.project_path, policy
            previous = read_json(path)
        else:
            path = self.global_path
            value = read_json(path)
            previous = copy.deepcopy(value)
            if value is None:
                value = dict(config_version=1, hosts={})
            validate_global(value)
            # Retain other host entries; CAS below prevents lost updates.
            value['hosts'][self.host_route] = copy.deepcopy(policy)
        return dict(reason='preview', path=str(path), document=value,
                    expected_revision=digest(previous) if previous is not None else None,
                    scope='all-projects' if target == 'global' else str(self.project),
                    project_override_retained=target == 'global' and exists(self.project_path),
                    activated=False)

    def prepare(self, policy, *, target, expected_revision):
        """Stage reviewed configuration, without activation or project deletion."""
        proposal = self.preview(policy, target=target)
        need(proposal['expected_revision'] == expected_revision, 'configuration_conflict: preview changed')
        path = Path(proposal['path'])
        revision = write_json(path, proposal['document'], expected_revision)
        return dict(reason='prepared', path=str(path), config_revision=revision,
                    policy_hash=None if policy == OPT_OUT else digest(policy), activated=False)

    def activate(self, host, *, expected_policy_hash, expected_host_fingerprint,
                 expected_source_key, expected_revision, confirm_scope,
                 evidence_hashes, expires_at=None, target=None, now=None):
        """Called only after explicit approval of the displayed policy and scope."""
        current = clock(now)
        result = self.status(host, target=target, now=current)
        need(result['policy'] is not None and result['policy']['mode'] != 'off', 'no_enabled_policy')
        need((result['policy_hash'], result['host_fingerprint'], result['source_key'], result['scope']) ==
             (expected_policy_hash, expected_host_fingerprint, expected_source_key, confirm_scope),
             'activation_preview_changed')
        validate(evidence_hashes, _R['array'](_R['HASH'], 64))
        validate(expires_at, _R['nullable'](_R['NUMBER']))
        need(expires_at is None or expires_at > current, 'approval_already_expired')
        need(host['evidence_hash'] is not None and host['evidence_hash'] in evidence_hashes,
             'host_evidence_not_reviewed')
        approvals, revision = self._approvals()
        need(revision == expected_revision, 'configuration_conflict: approval store changed')
        approvals['approvals'] = [a for a in approvals['approvals'] if a['source_key'] != result['source_key']]
        approvals['approvals'].append(dict(source_key=result['source_key'], scope=confirm_scope,
            policy_hash=expected_policy_hash, host_fingerprint=expected_host_fingerprint,
            approved_at=current, expires_at=expires_at, evidence_hashes=evidence_hashes))
        validate_approvals(approvals)
        write_json(self.approvals_path, approvals, revision, private=True)
        return self.status(host, target=target, now=current)

    def revoke(self, source_key, *, expected_revision):
        validate(source_key, _R['HASH'])
        approvals, revision = self._approvals()
        need(revision == expected_revision, 'configuration_conflict: approval store changed')
        approvals['approvals'] = [a for a in approvals['approvals'] if a['source_key'] != source_key]
        new_revision = write_json(self.approvals_path, approvals, revision, private=True)
        return dict(reason='revoked', source_key=source_key, approval_revision=new_revision)


def handle(packet):
    """Strict operation packets; no secret values or arbitrary write paths."""
    need(type(packet) is dict, 'invalid_operation')
    data = dict(packet)
    operation = data.pop('operation', None)
    need(operation in ('resolve', 'status', 'preview', 'prepare', 'activate', 'revoke'), 'invalid_operation')
    need('now' not in data, 'clock_override_is_test_api_only')
    options = {key: data.pop(key) for key in ('policy_path', 'session_off') if key in data}
    config = RoutingConfig(data.pop('project_root'), data.pop('host_route'), **options)
    return getattr(config, operation)(**data)


def main():
    if sys.argv[1:] == ['--help']:
        print('Offline JSON stdin operations: resolve, status, preview, prepare, activate, revoke. '
              'See references/global-routing.md for packet fields and explicit approval requirements.')
        return 0
    try:
        need(sys.version_info >= (3, 12), 'unsupported_runtime: Python 3.12+ required')
        need(not sys.argv[1:], 'unexpected_arguments')
        result = handle(strict_json(sys.stdin.buffer.read(LIMIT + 1)))
        print(canonical(result).decode())
        return 0
    except (ValueError, TypeError, KeyError, OSError, RecursionError, OverflowError) as exc:
        # Never echo the input or arbitrary exception text containing file content.
        reason = str(exc) if isinstance(exc, ValueError) else 'invalid_operation_or_unreadable_file'
        print(canonical(dict(reason='configuration_error', detail=reason, external_requests=False)).decode())
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
