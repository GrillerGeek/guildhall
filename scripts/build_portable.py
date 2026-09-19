#!/usr/bin/env python3
"""Build the complete portable quest bundle using Python's standard library."""
from __future__ import annotations
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
DEST = Path('plugin/skills/guildhall-quest')


def outputs(root: Path) -> dict[Path, bytes]:
    result = {}
    source = root / 'plugin/portable'
    for directory in [root/'plugin', source, root/'plugin/agents']:
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f'invalid source directory: {directory}')
    for file in sorted(source.rglob('*')):
        if file.is_symlink():
            raise ValueError(f'symlink source: {file}')
        if file.is_file():
            result[DEST / file.relative_to(source)] = file.read_bytes()
    roles = []
    for file in sorted((root / 'plugin/agents').glob('*.md')):
        if file.is_symlink():
            raise ValueError(f'symlink role: {file}')
        match = re.fullmatch(r'---\n(.*?)\n---\n(.*)', file.read_text(), re.S)
        if not match:
            raise ValueError(f'malformed role: {file}')
        fm, body = match.groups()
        name = re.search(r'^name: (.+)$', fm, re.M)
        tier = re.search(r'^model: (.+)$', fm, re.M)
        if not name or name[1] != file.stem or not tier or tier[1] not in {'opus','sonnet','haiku'}:
            raise ValueError(f'invalid role identity/tier: {file}')
        # Canonical Claude files stay exact. Only these explicit portable terms
        # change; tool/model frontmatter is never installed as host configuration.
        body = body.replace('`CLAUDE.md`', '`AGENTS.md` and applicable host guidance')
        body = body.replace('/idd-framework:resolve', 'idd-resolve')
        body = body.replace('mcp__plugin_playwright_playwright__', '')
        header = '# ' + file.stem + '\n\n'
        header += ('Generated from the canonical Claude role. Read the host adapter first.\n'
                   'Tool names in examples describe operations; use tools actually available.\n'
                   'Role restrictions are instructions, not an enforced permission sandbox.\n'
                   'Do not infer a model override from the original role tier.\n\n')
        if file.stem in {'model-echo','plugin-validator'}:
            header += ('This reference describes a Claude-specific diagnostic/checklist.\n'
                       'Do not use it to certify another host or infer model identity.\n\n')
        if file.stem == 'refactorer':
            body = body.replace('Back out completely and report to Mordain.',
                                'Preserve the diff and report to Mordain for a recovery decision; do not roll back pre-existing work.')
        body = body.replace('Mordain provides base + HEAD SHAs, or names the git range',
                            'Mordain supplies baseline-to-current-worktree evidence including untracked outputs and distinguishes pre-existing edits; a Git range is sufficient only if it covers every quest change')
        if file.stem == 'refactorer':
            body = body.replace('back out completely — every time, no exceptions.', 'stop, preserve the diff and report for a recovery decision; never undo pre-existing edits.')
            body = body.replace('you went too far — back out.', 'you went too far — stop, preserve the diff and report for a recovery decision.')
        if file.stem == 'ui-test-author':
            body = body.replace('You are the only adventurer permitted to read implementation code', 'Unlike Seraphine, you may read UI implementation code')
            body = body.replace('IDD `tech-lead-reviewer`', 'the closing IDD review capability resolved during preflight')
        if file.stem == 'ops-readiness-reviewer':
            for heading in ['Deploy plan','What to watch (first hour)','Rollback plan','On-call notes','Open ops questions']:
                body = body.replace('`## '+heading+'`', '`### '+heading+'`')
        if file.stem == 'docs-writer':
            body = body.replace('the diff Mordain names (base + HEAD SHAs or a git range), the IDD Spec (for the "why" behind the change)',
                                'the complete baseline-to-current-worktree evidence, including untracked outputs and attribution of pre-existing changes, and the Spec (for the "why" behind the change); for a scoped docs-only correction, the named user ask and verified source of truth replace the code diff and Spec')
            body = body.replace('**Read the diff and the spec.**', '**Read the supplied change evidence and Spec, or the scoped docs-only ask and source of truth.**')
            body = body.replace('before you write a single word.', 'before you write a single word; a docs-only correction uses its named source of truth.')
            body = body.replace('plus docstrings on functions actually touched by the diff', 'docstring edits only when the source file is explicitly named in your writable scope')
            body = body.replace('plus docstrings on functions the diff touched.', 'including source files for docstrings only when explicitly named.')
            body = body.replace('If the diff adds or modifies a public function / class / method,', 'Only if its source file is explicitly in the writable scope and the diff adds or modifies a public function / class / method,')
            body = body.replace('5. **Update docstrings on touched functions only.**', '5. **Skip docstrings in docs-only mode; otherwise update only explicitly scoped touched functions.**')
        if file.stem == 'pr-author':
            body = body.replace('the `git diff <base>..HEAD` summary (Mordain has already computed `<base>`)',
                                'the complete baseline-to-current-worktree evidence, including untracked outputs and attribution of pre-existing changes (a Git range only when it covers every quest change)')
            body = body.replace('preserving his subsection headings (`### Deploy plan`, `### What to watch (first hour)`, `### Rollback plan`, `### On-call notes`)',
                                'preserving all his subsection headings and text, including `### Open ops questions`')
            body = body.replace('Group them mentally: features, fixes, docs, refactors.',
                                'Use commit subjects as historical context only; describe the supplied working-tree evidence even when the quest has no commits.')
        result[DEST / 'references/roles' / file.name] = (header + body).encode()
        roles.append((file.stem,tier[1]))
    if len(roles) != 19:
        raise ValueError('Expected reviewed inventory of 19 roles; update the portability contract intentionally')
    roster = '# Bundled roles\n\nRead a role only when dispatching it. Claude tiers below are source metadata,\nnot portable model assignments. The diagnostic is not a required portable probe.\n\n| Role | Claude tier |\n|---|---|\n'
    roster += ''.join(f'| [{name}](roles/{name}.md) | {tier} |\n' for name,tier in roles)
    result[DEST / 'references/roster.md'] = roster.encode()
    result[DEST / 'LICENSE'] = (root/'LICENSE').read_bytes()
    return result


def build(root: Path = ROOT, check: bool = False) -> int:
    expected = outputs(root)
    dest = root / DEST
    # Refuse symlinks and unknown output files before the first write. This tool
    # never deletes files and is not an installer into a user's existing skills.
    for parent in [dest, *dest.parents]:
        if parent == root.parent:
            break
        if parent.is_symlink():
            raise ValueError(f'symlink output parent: {parent}')
    if dest.exists():
        for file in dest.rglob('*'):
            if file.is_symlink():
                raise ValueError(f'symlink output: {file}')
            if file.is_file() and file.relative_to(root) not in expected:
                raise ValueError(f'unknown output: {file}')
    changes = [p for p, data in expected.items() if not (root/p).is_file() or (root/p).read_bytes() != data]
    if check and changes:
        raise ValueError('Generated drift: ' + ', '.join(map(str,changes)))
    if not check:
        for p in changes:
            (root/p).parent.mkdir(parents=True, exist_ok=True)
            (root/p).write_bytes(expected[p])
    return len(changes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        count = build(check=args.check)
        print(f'Portable bundle: {len(outputs(ROOT))} files, {count} changed')
    except (ValueError, OSError) as exc:
        parser.exit(1, f'{exc}\n')
