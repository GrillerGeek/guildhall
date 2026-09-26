#!/usr/bin/env python3
"""Prepare owned study worktrees and record host-run outcomes; never launch models."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import random
import runpy
import secrets
import subprocess
import sys
import time

_S=runpy.run_path(str(Path(__file__).with_name('routing_study.py')),run_name='_study')
need,shape,digest=_S['need'],_S['shape'],_S['digest']
LIMIT=_S['LIMIT']


def git(root,*args):
    result=subprocess.run(['git','-C',str(root),*args],capture_output=True,timeout=30)
    need(result.returncode==0 and len(result.stdout)<=LIMIT)
    return result.stdout


def read(path):
    def pairs(items):
        result={}
        for k,v in items:need(k not in result);result[k]=v
        return result
    with Path(path).open('rb') as stream:raw=stream.read(LIMIT+1)
    need(len(raw)<=LIMIT)
    return json.loads(raw,object_pairs_hook=pairs)


def save(root,state):
    temporary=root/'study.json.tmp'
    with temporary.open('x') as stream:json.dump(state,stream,sort_keys=True,allow_nan=False)
    os.replace(temporary,root/'study.json')


@contextmanager
def locked(directory):
    root=Path(directory).resolve();lock=root/'.controller-lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    try:
        state=read(root/'study.json')
        _S['validate_manifest'](state['manifest'])
        need(digest(state['manifest'])==state['manifest_hash'] and state['status']=='prepared')
        yield root,state
    finally:lock.unlink()


def prepare(manifest,repository,directory,phase='development',observations=None):
    _S['validate_manifest'](manifest);need(phase in ('development','holdout'))
    repo=Path(repository).resolve();root=Path(directory).resolve()
    need(not root.is_relative_to(repo) and not repo.is_relative_to(root))
    need(not git(repo,'status','--porcelain'))
    baseline=git(repo,'rev-parse','HEAD').decode().strip()
    need(len(baseline) in (40,64) and all(c in '0123456789abcdef' for c in baseline))
    if phase=='holdout':
        need(type(observations) is dict and observations.get('manifest_hash')==digest(manifest))
        report=_S['headroom'](manifest,observations.get('observations'))
        allowed={(g['role'],g['category']) for g in report['groups'] if g['status']=='headroom_observed'}
        need(all((f['role'],f['category']) in allowed for f in manifest['fixtures'] if f['split']=='holdout'))
    prior_usage=0
    if phase=='holdout':
        need(all(r['usage_tokens'] is not None for r in observations['observations']))
        prior_usage=sum(r['usage_tokens'] for r in observations['observations'])
    runs=[]
    for fixture in manifest['fixtures']:
        if fixture['split']!=phase:continue
        strategies=[(c['id'],c['id']) for c in manifest['candidates']] if phase=='development' else [
            ('static',manifest['baseline_candidate']),('deterministic',fixture['deterministic_candidate']),('jev',None)]
        for repeat in range(manifest['repeats']):
            for strategy,candidate in strategies:
                runs.append(dict(id=secrets.token_hex(12),fixture_id=fixture['id'],repeat=repeat,
                                 strategy=strategy,candidate=candidate,status='pending'))
    need(0<len(runs)<=manifest['max_runs'])
    random.Random(manifest['seed']).shuffle(runs)
    root.mkdir(parents=False,exist_ok=False)
    state=dict(schema_version=1,status='preparing',manifest=manifest,manifest_hash=digest(manifest),
               repository=str(repo),baseline=baseline,phase=phase,prior_usage_tokens=prior_usage,runs=runs)
    save(root,state)
    # Partial preparation is preserved for explicit recovery; never delete/replay automatically.
    for run in runs:
        tree=root/run['id'];git(repo,'worktree','add','--detach',str(tree),baseline)
        run['git_marker']=(tree/'.git').read_text();save(root,state)
    state['status']='prepared';save(root,state)
    return dict(directory=str(root),manifest_hash=state['manifest_hash'],runs=len(runs),phase=phase,dispatch='host-owned')


def selected(state,run_id):
    run=next((r for r in state['runs'] if r['id']==run_id),None);need(run is not None)
    fixture=next(f for f in state['manifest']['fixtures'] if f['id']==run['fixture_id'])
    return run,fixture


def verify_tree(root,state,run):
    tree=root/run['id']
    need(not tree.is_symlink() and not (tree/'.git').is_symlink() and (tree/'.git').read_text()==run['git_marker'])
    need(git(tree,'rev-parse','HEAD').decode().strip()==state['baseline'])
    return tree


def select(directory,run_id,decision):
    with locked(directory) as (root,state):
        run,_=selected(state,run_id);need(run['status']=='pending' and run['strategy']=='jev' and run['candidate'] is None)
        need(type(decision) is dict and decision.get('status')=='dispatch')
        settings=decision.get('dispatch')
        matches=[c for c in state['manifest']['candidates'] if settings=={k:c[k] for k in ('model','effort')}]
        need(len(matches)==1)
        if not state['manifest']['synthetic']:
            # First-time qualification uses shadow recommendations followed by an
            # explicitly authorized study override, never forged qualifications.
            if decision.get('source')=='user_override':
                recommendation=decision.get('study_recommendation',{})
                need(recommendation.get('reason')=='shadow' and recommendation.get('status')=='dispatch')
                need(recommendation.get('recommended_candidate')==matches[0]['id'])
                receipt=decision.get('receipt',{});prior= recommendation.get('receipt',{})
                need(prior.get('router_identity') is not None)
                for key in ('policy_hash','input_fingerprint','host_snapshot'):
                    need(receipt.get(key) is not None and receipt[key]==prior.get(key))
            else:need(decision.get('source')=='jev')
            need(decision.get('recommended_candidate')==matches[0]['id'])
        run['candidate']=matches[0]['id'];run['routing_receipt_hash']=digest(decision);save(root,state)
        return dict(run_id=run_id,candidate=run['candidate'])


def claim(directory,run_id):
    with locked(directory) as (root,state):
        run,fixture=selected(state,run_id)
        need(run['status']=='pending' and run['candidate'] is not None)
        need(not any(r['status']=='running' for r in state['runs']))
        recorded=[r['outcome'] for r in state['runs'] if r['status']=='recorded']
        need(all(r['usage_tokens'] is not None for r in recorded))
        need(state['prior_usage_tokens']+sum(r['usage_tokens'] for r in recorded)<state['manifest']['usage_budget_tokens'])
        tree=verify_tree(root,state,run);need(not git(tree,'status','--porcelain'))
        candidate=next(c for c in state['manifest']['candidates'] if c['id']==run['candidate'])
        run['status']='running';run['started_at']=time.time();save(root,state)
        return dict(run_id=run_id,cwd=str(tree),role=fixture['role'],task=fixture['prompt'],
            allowed_files=fixture['allowed_files'],settings={k:candidate[k] for k in ('model','effort')},
            timeout_seconds=state['manifest']['timeout_seconds'],host_requirements=state['manifest']['host'],
            remaining_usage_tokens=state['manifest']['usage_budget_tokens']-state['prior_usage_tokens']-sum(r['usage_tokens'] for r in recorded),
            instruction='Use the original role contract and actual host worker. Enforce these budgets. A running claim is never automatically replayed.')


def tree_evidence(tree,include_artifacts=False):
    files=set(x.decode() for x in git(tree,'diff','--name-only','-z','HEAD').split(b'\0') if x)
    files.update(x.decode() for x in git(tree,'ls-files','--others','--exclude-standard','-z').split(b'\0') if x)
    files.update(x.decode() for x in git(tree,'ls-files','--others','--ignored','--exclude-standard','-z').split(b'\0') if x)
    entries=[];artifacts=[];total_bytes=0
    for name in sorted(files):
        path=tree/name
        if not path.is_symlink():need(path.resolve().is_relative_to(tree.resolve()))
        if path.is_symlink():content=('symlink:'+os.readlink(path)).encode()
        elif path.is_file():
            with path.open('rb') as stream:content=stream.read(LIMIT+1)
            need(len(content)<=LIMIT)
        else:content=b'<deleted>'
        total_bytes+=len(content);need(total_bytes<=LIMIT)
        if include_artifacts:artifacts.append(dict(path=name,content=content.decode('utf-8')))
        entries.append((name,digest(dict(bytes=content.hex(),mode=path.lstat().st_mode if path.exists() or path.is_symlink() else None))))
    return (files,digest(entries),artifacts) if include_artifacts else (files,digest(entries))


def record(directory,run_id,outcome):
    shape(outcome,'worker_id evidence elapsed_ms usage_tokens cost_usd output status retries host_report')
    _S['number'](outcome['retries'],True)
    _S['string'](outcome['worker_id']);_S['string'](outcome['output'],100000)
    need(outcome['status'] in ('completed','interrupted','failed'))
    need(type(outcome['evidence']) is list and 1<=len(outcome['evidence'])<=64)
    for ref in outcome['evidence']:_S['string'](ref)
    for metric in _S['METRICS']:
        if outcome[metric] is not None:_S['number'](outcome[metric],metric=='usage_tokens')
    need(outcome['elapsed_ms'] is None or outcome['elapsed_ms']>0)
    with locked(directory) as (root,state):
        run,fixture=selected(state,run_id);need(run['status']=='running')
        tree=verify_tree(root,state,run);files,tree_hash=tree_evidence(tree)
        violations=sorted(files-set(fixture['allowed_files']))
        report=outcome['host_report']
        if not state['manifest']['synthetic']:
            host=state['manifest']['host']
            candidate=next(c for c in state['manifest']['candidates'] if c['id']==run['candidate'])
            levels=['unknown','configuration_verified','execution_observed']
            matches=(type(report) is dict and report.get('synthetic') is False and report.get('complete') is True
                and report.get('worker_id')==outcome['worker_id']
                and report.get('scope')==dict(host=host['route'],role=fixture['role'],category=fixture['category'])
                and report.get('requested')=={k:candidate[k] for k in ('model','effort')}
                and report.get('host',{}).get('version')==host['client_version']
                and report.get('host',{}).get('configuration_revision')==host['configuration_revision']
                and report.get('evidence_level') in levels
                and levels.index(report['evidence_level'])>=levels.index(host['evidence_requirement']))
            if matches:
                usage=report.get('usage');need(type(usage) is dict)
                meters=usage.get('meters');need(type(meters) is dict)
                host_usage=meters.get('host');need(type(host_usage) is dict and 'usage_tokens' in host_usage)
                # A mismatched total must be corrected before recording; otherwise
                # the next claim could undercount the study's consumed budget.
                need(outcome['usage_tokens']==host_usage['usage_tokens'])
                if host['evidence_requirement']=='execution_observed':
                    observed=report.get('observed',{})
                    matches=(type(observed) is dict and observed.get('model') is not None
                        and (candidate['effort'] is None or observed.get('effort')==candidate['effort']))
            if not matches:violations.append('<host-evidence>')
        if time.time()-run['started_at']>state['manifest']['timeout_seconds'] or (outcome['elapsed_ms'] or 0)>state['manifest']['timeout_seconds']*1000:
            violations.append('<time-budget>')
        known=state['prior_usage_tokens']+sum(r['outcome']['usage_tokens'] or 0 for r in state['runs'] if r['status']=='recorded')
        if known+(outcome['usage_tokens'] or 0)>state['manifest']['usage_budget_tokens']:violations.append('<usage-budget>')
        run.update(status='recorded',outcome=outcome,tree_hash=tree_hash,violations=violations)
        save(root,state);return dict(run_id=run_id,violations=violations,recorded=True)


def blind(directory):
    with locked(directory) as (root,state):
        packets=[]
        for run in state['runs']:
            if run['status']!='recorded':continue
            _,fixture=selected(state,run['id'])
            _,snapshot_hash,artifacts=tree_evidence(verify_tree(root,state,run),include_artifacts=True)
            need(snapshot_hash==run['tree_hash'])
            packet=dict(blind_id=run['id'],task=fixture['prompt'],rubric=fixture['rubric'],output=run['outcome']['output'],artifacts=artifacts)
            need(len(json.dumps(packet).encode())<=LIMIT)
            # Refuse explicit selector leakage rather than silently editing material being graded.
            text=json.dumps(packet).lower()
            need(all(c['model'].lower() not in text for c in state['manifest']['candidates']))
            packets.append(packet)
        return dict(schema_version=1,packets=packets,instruction='Grade accepted/critical_misses independently; do not inspect study.json, worktree names or strategy metadata.')


def grade(directory,grades):
    need(type(grades) is list and len(grades)<=1000)
    with locked(directory) as (root,state):
        seen=set()
        for item in grades:
            shape(item,'blind_id accepted critical_misses reason')
            need(type(item['accepted']) is bool);_S['number'](item['critical_misses'],True);_S['string'](item['reason'])
            need(item['blind_id'] not in seen);seen.add(item['blind_id'])
            run,_=selected(state,item['blind_id']);need(run['status']=='recorded' and 'grade' not in run)
            need(tree_evidence(verify_tree(root,state,run))[1]==run['tree_hash'])
            run['grade']=item
        save(root,state);return dict(frozen_grades=len(grades),qualification=False)


def export(directory):
    with locked(directory) as (root,state):
        need(all(r['status']=='recorded' and 'grade' in r for r in state['runs']))
        records=[]
        for run in state['runs']:
            need(tree_evidence(verify_tree(root,state,run))[1]==run['tree_hash'])
            _,f=selected(state,run['id']);o,g=run['outcome'],run['grade']
            row=dict(fixture_id=f['id'],repeat=run['repeat'],accepted=g['accepted'] and o['status']=='completed',
                     critical_misses=g['critical_misses'],violations=len(run['violations']),**{k:o[k] for k in _S['METRICS']})
            if state['phase']=='development':row['candidate']=run['candidate']
            else:row.update(split='holdout',role=f['role'],category=f['category'],strategy=run['strategy'],retries=o['retries'],evidence=o['evidence'])
            records.append(row)
        if state['phase']=='development':
            return dict(manifest_hash=state['manifest_hash'],observations=records,qualification=False)
        if any(r['elapsed_ms'] is None for r in records):
            return dict(status='incomplete',qualification=False,reason='missing_elapsed_measurement',records=records)
        payload=dict(schema_version=1,synthetic=state['manifest']['synthetic'],objective=state['manifest']['objective'],records=records)
        _S['_EVAL']['validate'](payload)
        return payload


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['prepare','select','claim','record','blind','grade','export'])
    parser.add_argument('--directory',required=True,type=Path)
    parser.add_argument('--manifest',type=Path);parser.add_argument('--repo',type=Path)
    parser.add_argument('--phase',default='development',choices=['development','holdout'])
    parser.add_argument('--input',type=Path);parser.add_argument('--run')
    args=parser.parse_args()
    try:
        need(sys.version_info>=(3,12))
        if args.operation=='prepare':
            need(args.manifest is not None and args.repo is not None)
            result=prepare(read(args.manifest),args.repo,args.directory,args.phase,read(args.input) if args.input else None)
        elif args.operation in ('claim','blind','export'):
            result=globals()[args.operation](args.directory,*([args.run] if args.operation=='claim' else []))
        elif args.operation=='grade':result=grade(args.directory,read(args.input))
        else:result=globals()[args.operation](args.directory,args.run,read(args.input))
        print(json.dumps(result,sort_keys=True,allow_nan=False));return 0
    except (ValueError,KeyError,TypeError,OSError,OverflowError,UnicodeError,RecursionError,subprocess.SubprocessError):
        print('{"error":"study_operation_refused","recovery":"Preserve study/worktrees; inspect missing evidence, budget or existing claim. Never automatically replay.","schema_version":1}');return 2


if __name__=='__main__':raise SystemExit(main())
