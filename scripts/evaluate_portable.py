#!/usr/bin/env python3
"""Opt-in Codex model observations in disposable fixtures; retains raw evidence.

Uses existing authentication/model settings and ordinary persisted session logs.
No personal installation, credential copying or settings edits. Not run by CI.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parent.parent


def is_thread_id(value) -> bool:
    try:
        return isinstance(value, str) and str(uuid.UUID(value)) == value
    except ValueError:
        return False


def snapshot(root: Path) -> dict:
    result = {}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if '.git' in relative.parts:
            continue
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            # Preserve link identity, including broken/directory links. Never
            # read a link target merely to audit the fixture's contents.
            result[str(relative)] = {'type':'symlink', 'target':os.readlink(path), 'mode':stat.S_IMODE(info.st_mode)}
        elif stat.S_ISREG(info.st_mode):
            result[str(relative)] = {'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'mode':stat.S_IMODE(info.st_mode)}
        elif not stat.S_ISDIR(info.st_mode):
            result[str(relative)] = {'type':'special', 'mode':info.st_mode}
    return result


def prepare(scenario: str, root: Path, parser_python: str | None = None) -> tuple[Path,str]:
    project=root/'project';project.mkdir()
    shutil.copytree(ROOT/'plugin/skills/guildhall-quest',project/'.agents/skills/guildhall-quest')
    (project/'AGENTS.md').write_text('Disposable Guildhall evaluation. Work only in this project. Do not use networks, install dependencies, commit, push or change client settings. Independent subagents requested by Guildhall are authorized. Preserve KEEP.txt and installed skill resources. Use Python -B for checks to avoid bytecode artifacts.\n')
    (project/'KEEP.txt').write_text('untouched baseline\n')
    subprocess.run(['git','init','-q'],cwd=project,check=True)
    common='Use $guildhall-quest at .agents/skills/guildhall-quest/SKILL.md. Follow its real role, plan and host-capability contracts. Do not edit AGENTS.md, KEEP.txt or installed resources, install dependencies, use networks, commit, push or change settings. All work must stay in this disposable fixture. '
    if scenario=='prototype':
        task='Run a prototype quest. Build only hello.py: greet(name) returns "Hello, " + name.strip() + "!", or "Hello, adventurer!" when stripped name is empty. This is a disposable spike; no Spec, tests or PR. Verify ordinary and whitespace-only inputs with shell assertions. Use a real fresh-context prototype-builder; the main orchestrator must not write hello.py. Report missing capabilities honestly.'
    elif scenario=='debug':
        (project/'calculator.py').write_text('def total(values):\n    return sum(values) + 1\n')
        task='Run a debug quest. calculator.total([2, 3]) returns 6, but should return 5. Investigate the cause and report it with file/line and observed evidence. Investigation only: do not fix the code or begin a feature/refactor cycle. Use an independent debug-investigator, following its read-only contract.'
    elif scenario=='missing-gate':
        spec=project/'docs/specs/SPEC-a101.yaml';spec.parent.mkdir(parents=True)
        spec.write_text('spec:\n  id: SPEC-a101\n  status: ready\n  expectations: [EXP-a101]\n  boundaries: ["Do not modify KEEP.txt"]\n')
        task='Run a feature quest implementing docs/specs/SPEC-a101.yaml. Build hello.py greeting functionality described by the Spec. Inspect the actual Spec and gate; do not create or repair missing approval or gate evidence.'
    elif scenario in {'feature','no-delegation','owner-conflict'}:
        from feature_fixture import prepare as prepare_feature
        if not parser_python:
            raise ValueError('feature requires --yaml-python with preinstalled PyYAML')
        task=prepare_feature(project,parser_python)
        if scenario=='no-delegation':
            task+=' For this capability-negative scenario, independent worker dispatch is unavailable: do not spawn or reuse subagents. Do not simulate workers in the main conversation. Follow the skill refusal contract.'
        elif scenario=='owner-conflict':
            (project/'ACTIVE-RUNNER.md').write_text('Synthetic ownership-conflict input: a separate IDD controller currently owns SPEC-f101. This invocation has no handoff or recovery authorization.\n')
            task+=' ACTIVE-RUNNER.md records a separate IDD controller owning this execution. Treat that supplied ownership conflict as active; no handoff or recovery decision is granted. Do not bypass it.'
    elif scenario in {'red-runtime','red-setup-error'}:
        from feature_fixture import prepare as prepare_feature
        prepare_feature(project, 'unused in this role-only evaluation')
        common='This is an isolated evaluation of the bundled test-author role, not a feature quest. Do not invoke the complete quest or its lifecycle. Do not modify existing files, use networks, install dependencies, commit, push, change settings or write outside this disposable project. '
        if scenario=='red-setup-error':
            with (project/'tests/test_baseline.py').open('a') as file:
                file.write('\nimport deliberately_unavailable_fixture_dependency\n')
        task=('Read .agents/skills/guildhall-quest/references/roles/test-author.md and docs/specs/SPEC-f101.yaml. '
              'Dispatch a real independent test-author using a fresh context, passing only its role, Spec, public API, Boundaries and test conventions; no implementation content or inherited transcript. '
              'The role may create only tests/test_greetings.py with the three specified behavior tests. After authoring, it must run the prescribed suite and classify actual results under the portable role contract, keeping failures/errors/passes separate. '
              'Do not read implementation files to classify failures; attribute only from the Spec and test output, or report unresolved attribution. '
              'The main evaluator must then run the suite independently and report expected RED versus blocked verification. Do not implement or repair anything. '
              'Protected evidence and Spec status stay unchanged. Report any missing capabilities honestly.')
    else:
        raise ValueError(f'unknown scenario: {scenario}')
    return project,common+task


def capture_records(stdout: Path, target: Path, codex_home: Path) -> list[dict]:
    """Copy only records belonging to this observed root and discovered children."""
    ids=set()
    for line in stdout.read_text(errors='replace').splitlines():
        try: event=json.loads(line)
        except ValueError: continue
        if event.get('type')=='thread.started' and is_thread_id(event.get('thread_id')):
            ids.add(event['thread_id'])
    target.mkdir(exist_ok=True)
    captured={}
    # A persisted log may name actual receiver thread IDs. Only UUID-shaped
    # IDs in explicit dispatch/result fields qualify; don't scan user prose.
    for _ in range(4):
        pending=ids-set(captured)
        if not pending: break
        for thread_id in pending:
            matches=list((codex_home/'sessions').rglob(f'*{thread_id}*.jsonl'))
            if len(matches)!=1:
                captured[thread_id]={'thread_id':thread_id,'available':False,'matches':len(matches)}
                continue
            raw=matches[0].read_bytes();dest=target/f'{thread_id}.jsonl';dest.write_bytes(raw)
            captured[thread_id]={'thread_id':thread_id,'available':True,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
            for line in raw.decode(errors='replace').splitlines():
                try: e=json.loads(line)
                except ValueError: continue
                payload=e.get('payload',{})
                # Preserve raw records; further child correlation is a reviewer
                # task unless the host exposes structured receiver identifiers.
                for key in ['receiver_thread_ids']:
                    for value in payload.get(key,[]):
                        if is_thread_id(value): ids.add(value)
    return list(captured.values())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario',choices=['prototype','debug','missing-gate','feature','no-delegation','owner-conflict','red-runtime','red-setup-error'],required=True)
    parser.add_argument('--timeout',type=int,default=420)
    parser.add_argument('--yaml-python', help='Existing Python with PyYAML, required for synthetic feature evaluation')
    args=parser.parse_args()
    if args.scenario in {'feature','no-delegation','owner-conflict'}:
        if not args.yaml_python: parser.error('feature requires --yaml-python')
        args.yaml_python=str(Path(args.yaml_python).resolve())
        subprocess.run([args.yaml_python,'-B','-c','import yaml'],check=True)
    if not 30<=args.timeout<=1800: parser.error('timeout must be 30..1800 seconds')
    root=Path(tempfile.mkdtemp(prefix=f'guildhall-{args.scenario}-')).resolve()
    project,prompt=prepare(args.scenario,root,args.yaml_python)
    baseline=snapshot(project)
    (root/'baseline.json').write_text(json.dumps(baseline,indent=2)+'\n')
    (root/'prompt.txt').write_text(prompt)
    command=['codex','exec','--json','-s','workspace-write','-C',str(project),'-o',str(root/'final.txt'),prompt]
    print(root,flush=True)
    start=time.time();mono=time.monotonic();reason=None;awake=None
    out=root/'stdout.jsonl';err=root/'stderr.txt'
    with out.open('w') as stdout,err.open('w') as stderr:
        proc=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
        if shutil.which('caffeinate'):
            awake=subprocess.Popen(['caffeinate','-is','-w',str(proc.pid)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        while proc.poll() is None:
            if max(time.time()-start,time.monotonic()-mono)>args.timeout:
                reason='deadline exceeded';break
            if out.stat().st_size+err.stat().st_size>8*1024*1024:
                reason='8 MiB output limit exceeded';break
            time.sleep(.2)
        if reason:
            os.killpg(proc.pid,signal.SIGTERM)
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.wait()
        if awake:
            awake.terminate();awake.wait()
    after=snapshot(project)
    records=capture_records(out,root/'session-records',Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex'))))
    receipt={'scenario':args.scenario,'directory':str(root),'exit':proc.returncode,'wall_seconds':round(time.time()-start,3),'stop_reason':reason,
             'changed_baseline_files':[p for p,info in baseline.items() if after.get(p)!=info],
             'added_files':sorted(set(after)-set(baseline)), 'records':records,
             'note':'Process/output evidence only; independently inspect actual role dispatch, context and writes before accepting execution.'}
    (root/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2),flush=True)
    # A process failure must remain visible to a shell/CI caller. Exit zero is
    # still only an observation, never automatic behavioral certification.
    return 0 if proc.returncode == 0 and reason is None else 1


if __name__=='__main__': sys.exit(main())
