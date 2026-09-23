#!/usr/bin/env python3
"""Validate generated Guildhall resources and native distribution metadata."""
from __future__ import annotations
import json
from pathlib import Path
import re
from build_portable import build, ROOT, DEST


def validate(root: Path = ROOT) -> None:
    build(root, check=True)
    # Execute the standalone module without importing it into the generated tree:
    # packaging validation must not create an unknown __pycache__ output.
    helper = root / DEST / 'scripts/route_model.py'
    namespace = {'__name__': '_routing_validation', '__file__': str(helper)}
    exec(compile(helper.read_bytes(), str(helper), 'exec'), namespace)
    for name, constant in [('policy', 'POLICY_SCHEMA'), ('request', 'REQUEST_SCHEMA'), ('policy-v2', 'POLICY_SCHEMA_V2'), ('request-v2', 'REQUEST_SCHEMA_V2'), ('policy-v3', 'POLICY_SCHEMA_V3'), ('request-v3', 'REQUEST_SCHEMA_V3')]:
        schema = json.loads((root / DEST / f'resources/schemas/{name}.schema.json').read_text())
        schema.pop('$schema')
        schema.pop('$comment')
        if schema != namespace[constant]:
            raise ValueError(f'routing schema drift: {name}')
    example = json.loads((root / DEST / 'resources/examples/off-request.json').read_text())
    policy_example = json.loads((root / DEST / 'resources/examples/off-policy.json').read_text())
    namespace['validate_request'](example)
    if example['policy'] != policy_example or policy_example['mode'] != 'off':
        raise ValueError('routing examples must agree and remain off')
    if any(c['qualification'] is not None for c in policy_example['candidates']):
        raise ValueError('examples cannot ship qualified profiles')
    paths = ['plugin/plugin.json','plugin/.codex-plugin/plugin.json','plugin/.claude-plugin/plugin.json']
    manifests = [json.loads((root/p).read_text()) for p in paths]
    portable, codex, claude = manifests
    for key in ['name','version','author','homepage','repository','license']:
        if not all(m.get(key) == portable.get(key) for m in manifests):
            raise ValueError(f'manifest disagreement: {key}')
    if portable['name'] != 'guildhall' or not re.fullmatch(r'\d+\.\d+\.\d+',portable['version']):
        raise ValueError('invalid plugin identity/version')
    if portable.get('$schema') != 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json':
        raise ValueError('invalid portable schema')
    common = {'name','version','description','author','homepage','repository','license','keywords'}
    if set(portable) != common | {'$schema'} or set(codex) != common | {'skills','interface'}:
        raise ValueError('unexpected manifest fields')
    if codex.get('skills') != './skills/':
        raise ValueError('skills must use fixed plugin-local discovery')
    if sorted(p.name for p in (root/'plugin/skills').iterdir()) != ['guildhall-quest']:
        raise ValueError('unexpected skill inventory')
    for file in (root/DEST).rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',file.read_text()):
            if '://' in target or target.startswith('#'):
                continue
            target = target.split('#')[0]
            resolved = (file.parent/target).resolve()
            if not resolved.is_relative_to((root/DEST).resolve()) or not resolved.is_file():
                raise ValueError(f'missing/escaped reference: {file}: {target}')
    for rel in ['.agents/plugins/marketplace.json','.claude-plugin/marketplace.json']:
        m = json.loads((root/rel).read_text())
        if m['name'] != 'guildhall-local' or len(m['plugins']) != 1 or m['plugins'][0]['name'] != 'guildhall':
            raise ValueError('unexpected marketplace inventory')
        source = m['plugins'][0]['source']
        expected = {'source':'local','path':'./plugin'} if rel.startswith('.agents/') else './plugin'
        if source != expected:
            raise ValueError('marketplace must resolve the repository-owned plugin')


if __name__ == '__main__':
    try:
        validate()
        print('Portable bundle, manifests, versions, catalogs and resource links passed')
    except (ValueError, OSError, KeyError, TypeError) as exc:
        raise SystemExit(str(exc))
