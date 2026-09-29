#!/usr/bin/env python3
"""Summarize already-authorized worker outcomes locally; never train or rerun."""
import json
from pathlib import Path
import runpy
import sys

_R=runpy.run_path(str(Path(__file__).with_name('route_model.py')),run_name='_feedback_router')
_U=runpy.run_path(str(Path(__file__).with_name('routing_usage.py')),run_name='_feedback_usage')
obj,enum=_R['obj'],_R['enum']
OUTCOME=obj(worker_id=_R['STRING'],status=enum(['completed','failed','interrupted']),
    tests=enum(['passed','failed','unknown','not_applicable']),
    review=enum(['accepted','rejected','unknown','not_applicable']),
    retries=_R['INTEGER'],evidence=_R['array'](_R['STRING'],64),
    delivery=enum(['complete','incomplete','unknown','budget_exceeded']))
OBSERVATION=obj(source=enum(['host_metadata','worker_assertion','unknown']),
    evidence=_R['nullable'](_R['STRING']),requested_resolved=_R['BASELINE'],
    observed=_R['BASELINE'],configuration_supported=_R['nullable'](_R['BOOL']))


def feedback(request,decision,outcome,observation,usage=None):
    _R['validate_request'](request)
    if request['schema_version']!=5:raise ValueError('v5_required')
    _R['validate'](outcome,OUTCOME);_R['validate'](observation,OBSERVATION)
    _R['validate'](decision['state'],_R['REQUEST_SCHEMA_V5']['properties']['state'])
    if (decision['status']!='dispatch' or decision['receipt']['policy_hash']!=_R['policy_hash'](request['policy']) or
        decision['receipt']['requested']!=decision['dispatch']):raise ValueError('uncorrelated_decision')
    snapshot={k:request['host'][k] for k in ('route','client_version','provider','worker_tool','configuration_revision','attribution','evidence_level')}
    fingerprint=_R['policy_hash'](dict(task={k:v for k,v in request['task'].items() if k!='summary'},
        policy_hash=_R['policy_hash'](request['policy']),host=snapshot))
    if decision['receipt']['input_fingerprint']!=fingerprint:raise ValueError('uncorrelated_task_or_host')
    _R['validate'](decision['dispatch'],_R['BASELINE'])
    scope=dict(host=request['host']['route'],role=request['task']['role'],category=request['task']['category'])
    trusted=observation['source']=='host_metadata' and observation['evidence'] is not None
    observed=observation['observed'] if trusted else dict(model=None,effort=None)
    resolved=observation['requested_resolved']
    substitution=trusted and (observation['configuration_supported'] is False or any(
        resolved[k] is not None and observed[k] is not None and resolved[k]!=observed[k] for k in ('model','effort')))
    state=dict(decision['state'])
    if substitution:state['adaptive_suspended']=True
    normalized=None
    if usage is not None:
        if usage['scope']!=scope or any(e['meter']=='host' and e['worker_id']!=outcome['worker_id'] for e in usage['expected']+usage['events']):
            raise ValueError('usage_scope_mismatch')
        normalized=_U['normalize'](usage)
    return dict(schema_version=1,scope=scope,worker_id=outcome['worker_id'],
        policy_hash=decision['receipt']['policy_hash'],catalog_revision=request['policy']['catalog_revision'],
        requested=decision['dispatch'],observed=observed,observation_source=observation['source'],
        observation_evidence=observation['evidence'] if trusted else None,
        outcome=outcome,usage=normalized,subscription_allowance_percent=None,
        state=state,known_substitution=bool(substitution),qualification=False,
        catalog_update='review_required',additional_runs=0,replay_worker=False)


def main():
    try:
        packet=_U['read_packet']()
        result=feedback(**packet)
        print(json.dumps(result,sort_keys=True,allow_nan=False));return 0
    except (ValueError,TypeError,KeyError,OverflowError,RecursionError,UnicodeError):
        print('{"error":"invalid_feedback_input"}');return 2


if __name__=='__main__':raise SystemExit(main())
