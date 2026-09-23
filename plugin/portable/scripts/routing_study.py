#!/usr/bin/env python3
"""Bounded development headroom analysis; never qualifies or dispatches models."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import runpy
import sys

_EVAL=runpy.run_path(str(Path(__file__).with_name('evaluate_routing.py')),run_name='_study_eval')
LIMIT=16*1024*1024
METRICS=('elapsed_ms','usage_tokens','cost_usd')


def need(ok):
    if not ok:raise ValueError('invalid_study_input')


def shape(value,fields):
    need(type(value) is dict and set(value)==set(fields.split()))


def string(value,maximum=4096):
    need(type(value) is str and 0<len(value)<=maximum)


def number(value,integer=False):
    need(type(value) is int if integer else type(value) in (int,float))
    need(math.isfinite(value) and value>=0)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def validate_manifest(m):
    shape(m,'schema_version study_id synthetic objective seed repeats baseline_candidate candidates fixtures router_overhead max_relative_spread max_runs timeout_seconds usage_budget_tokens host')
    need(type(m['schema_version']) is int and m['schema_version']==1)
    need(type(m['synthetic']) is bool);string(m['study_id'],128)
    need(m['objective'] in ('latency','usage','cost'))
    shape(m['host'],'route evidence_requirement client_version configuration_revision')
    need(m['host']['route'] in ('claude-native','claude-skill','codex-skill'))
    need(m['host']['evidence_requirement'] in ('configuration_verified','execution_observed'))
    string(m['host']['client_version']);string(m['host']['configuration_revision'])
    for k in ('seed','repeats','max_runs','timeout_seconds','usage_budget_tokens'):number(m[k],True)
    need(2<=m['repeats']<=20 and 1<=m['max_runs']<=1000 and 1<=m['timeout_seconds']<=3600 and m['usage_budget_tokens']>0)
    number(m['max_relative_spread']);need(m['max_relative_spread']<=1)
    shape(m['router_overhead'],'elapsed_ms usage_tokens cost_usd')
    for value in m['router_overhead'].values():
        if value is not None:number(value)
    # Host subscription tokens and Jev tokens are different meters.
    need(m['router_overhead']['usage_tokens'] in (None,0))
    need(type(m['candidates']) is list and 1<=len(m['candidates'])<=16)
    ids=set();settings=set()
    for c in m['candidates']:
        shape(c,'id model effort');string(c['id'],64);string(c['model'],256)
        if c['effort'] is not None:string(c['effort'],32)
        need(c['id'] not in ids and (c['model'],c['effort']) not in settings)
        ids.add(c['id']);settings.add((c['model'],c['effort']))
    need(m['baseline_candidate'] in ids)
    need(type(m['fixtures']) is list and 1<=len(m['fixtures'])<=100)
    fixtures=set()
    for f in m['fixtures']:
        shape(f,'id split role category prompt rubric allowed_files deterministic_candidate')
        string(f['id'],128);string(f['prompt']);string(f['rubric'])
        need(f['id'] not in fixtures);fixtures.add(f['id'])
        need(f['split'] in ('development','holdout') and f['role'] in _EVAL['ROLES'] and f['category'] in _EVAL['CATEGORIES'])
        need(f['deterministic_candidate'] in ids and type(f['allowed_files']) is list)
        for p in f['allowed_files']:
            string(p,256);need(not p.startswith('/') and '..' not in p.split('/') and '.git' not in p.split('/') and '\\' not in p)
        need(len(set(f['allowed_files']))==len(f['allowed_files']))
    planned=sum((len(m['candidates']) if f['split']=='development' else 3)*m['repeats'] for f in m['fixtures'])
    need(planned<=m['max_runs'])
    need(len(json.dumps(m).encode())<=LIMIT)


def headroom(manifest,observations):
    validate_manifest(manifest)
    need(type(observations) is list and len(observations)<=100000)
    fixtures={f['id']:f for f in manifest['fixtures'] if f['split']=='development'}
    candidates={c['id'] for c in manifest['candidates']}
    rows={}
    for r in observations:
        shape(r,'fixture_id repeat candidate accepted critical_misses violations elapsed_ms usage_tokens cost_usd')
        need(r['fixture_id'] in fixtures and r['candidate'] in candidates)
        number(r['repeat'],True);need(r['repeat']<manifest['repeats'])
        need(type(r['accepted']) is bool)
        for k in ('critical_misses','violations'):number(r[k],True)
        for k in METRICS:
            if r[k] is not None:number(r[k],k=='usage_tokens')
        key=(r['fixture_id'],r['repeat'],r['candidate']);need(key not in rows);rows[key]=r
    metric={'latency':'elapsed_ms','usage':'usage_tokens','cost':'cost_usd'}[manifest['objective']]
    groups=[]
    for scope in sorted({(f['role'],f['category']) for f in fixtures.values()}):
        fs=[f for f in fixtures.values() if (f['role'],f['category'])==scope]
        missing=len(fs)<3;noise=False;quality=False;static_total=det_total=oracle_total=0
        fixed={c:0 for c in candidates};fixed_ok={c:True for c in candidates}
        for f in fs:
            values={};valid={}
            for c in candidates:
                samples=[rows.get((f['id'],repeat,c)) for repeat in range(manifest['repeats'])]
                if any(r is None or r[metric] is None for r in samples):missing=True;continue
                xs=[r[metric] for r in samples];mean=sum(xs)/len(xs)
                need(math.isfinite(mean))
                if mean<=0:missing=True;continue
                if (max(xs)-min(xs))/mean>manifest['max_relative_spread']:noise=True
                values[c]=mean
                valid[c]=all(r['accepted'] and not r['critical_misses'] and not r['violations'] for r in samples)
                fixed[c]+=mean;need(math.isfinite(fixed[c]));fixed_ok[c]=fixed_ok[c] and valid[c]
            base=manifest['baseline_candidate'];det=f['deterministic_candidate']
            if base not in values or det not in values:missing=True;continue
            if not valid[base] or not valid[det]:quality=True
            acceptable=[values[c] for c in values if valid[c]]
            if not acceptable:quality=True;continue
            static_total+=values[base];det_total+=values[det];oracle_total+=min(acceptable)
        overhead=manifest['router_overhead'][metric]
        if overhead is None:missing=True
        gains={'static':None,'deterministic':None}
        if not missing and not noise and not quality:
            oracle_total+=(overhead or 0)*len(fs)
            need(all(math.isfinite(v) and v>0 for v in (static_total,det_total,oracle_total)))
            gains=dict(static=(static_total-oracle_total)/static_total,deterministic=(det_total-oracle_total)/det_total)
        status=('insufficient_evidence' if missing or noise or quality else
                'headroom_observed' if min(gains.values())>=0.1-1e-12 else 'no_measured_headroom')
        groups.append(dict(role=scope[0],category=scope[1],status=status,improvement=gains,
            reasons=[name for name,yes in [('missing_measurements_or_fixtures',missing),('noisy_repeats',noise),('baseline_quality_failure',quality)] if yes],
            best_fixed_candidate=min((c for c in fixed if fixed_ok[c]),key=fixed.get,default=None) if not missing else None))
    status=('insufficient_evidence' if not groups or any(g['status']=='insufficient_evidence' for g in groups)
            else 'headroom_observed' if any(g['status']=='headroom_observed' for g in groups) else 'no_measured_headroom')
    return dict(schema_version=1,manifest_hash=digest(manifest),synthetic=manifest['synthetic'],
        status=status,groups=groups,qualification=False,
        limitation='Development measurements of this candidate set only; not global optimality or held-out qualification.')


def main():
    try:
        need(sys.version_info>=(3,12))
        raw=sys.stdin.buffer.read(LIMIT+1);need(len(raw)<=LIMIT)
        def pairs(items):
            result={}
            for k,v in items:need(k not in result);result[k]=v
            return result
        packet=json.loads(raw,object_pairs_hook=pairs);shape(packet,'manifest observations')
        print(json.dumps(headroom(packet['manifest'],packet['observations']),allow_nan=False,sort_keys=True));return 0
    except (ValueError,TypeError,KeyError,OverflowError,RecursionError,UnicodeError):
        print('{"error":"invalid_study_input","schema_version":1}');return 2


if __name__=='__main__':raise SystemExit(main())
