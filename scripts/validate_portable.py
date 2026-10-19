#!/usr/bin/env python3
"""Validate generated Guildhall resources and native distribution metadata."""
from __future__ import annotations
import json
from pathlib import Path
import re
from build_portable import build, ROOT, DEST, DESTINATIONS


def validate(root: Path = ROOT) -> None:
    build(root, check=True)
    # Review stays self-contained in quest and absent from routing setup.
    from tempfile import TemporaryDirectory
    review_helper = root / DEST / 'scripts/review.py'
    review = {'__name__': '_review_validation', '__file__': str(review_helper)}
    exec(compile(review_helper.read_bytes(), str(review_helper), 'exec'), review)
    resources = root / DEST / 'resources/review'
    schema = json.loads((resources / 'record.schema.json').read_text())
    example = json.loads((resources / 'example.json').read_text())
    if (schema.get('additionalProperties') is not False or
        set(schema['required']) != set(example) or
        schema['properties']['schema_version'] != {'const': 1}):
        raise ValueError('review schema/example fields disagree')
    # Exercise semantic record validation, not merely JSON parseability.
    with TemporaryDirectory(prefix='guildhall-review-validation-') as temporary:
        project = Path(temporary)
        plan = project / example['plan_path']
        plan.parent.mkdir(parents=True)
        plan.write_text('# Synthetic validation plan\n')
        workspace = review['Workspace'](str(project), example['plan_path'], 'document')
        workspace.validate_record(example)
    if '<!--REVIEW_CONTENT-->' not in (resources / 'template.html').read_text():
        raise ValueError('review template insertion point missing')
    for removed in ('plugin/skills/guildhall-routing-setup', 'plugin/routing-setup',
                    'plugin/portable/scripts/route_model.py'):
        if (root / removed).exists():
            raise ValueError('removed routing support must not be restored')
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
    if sorted(p.name for p in (root/'plugin/skills').iterdir()) != sorted(p.name for p in DESTINATIONS):
        raise ValueError('unexpected skill inventory')
    for destination in DESTINATIONS:
        for file in (root/destination).rglob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)',file.read_text()):
                if '://' in target or target.startswith('#'):
                    continue
                target = target.split('#')[0]
                resolved = (file.parent/target).resolve()
                if not resolved.is_relative_to((root/destination).resolve()) or not resolved.is_file():
                    raise ValueError(f'missing/escaped reference: {file}: {target}')
    for rel in ['.agents/plugins/marketplace.json','.claude-plugin/marketplace.json']:
        m = json.loads((root/rel).read_text())
        # Claude's catalog also lists the tavern mod (function hooks are Claude-only).
        extras = [{'name':'guildhall-tavern','source':'./mods/guildhall-tavern'}] if rel.startswith('.claude-plugin/') else []
        if m['name'] != 'guildhall-local' or m['plugins'][0]['name'] != 'guildhall' or m['plugins'][1:] != extras:
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
