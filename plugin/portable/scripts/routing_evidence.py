#!/usr/bin/env python3
"""Inspect explicitly supplied task-owned captures; never scan sessions or dispatch."""
from __future__ import annotations
import hashlib
import argparse
import json
from pathlib import Path
import runpy
import sys

_USAGE = runpy.run_path(str(Path(__file__).with_name('routing_usage.py')), run_name='_usage')
LIMIT = 16 * 1024 * 1024
LEVELS = ('unknown','configuration_verified','execution_observed')


def need(ok):
    if not ok:raise ValueError('invalid_evidence_input')


def fields(value, names):
    need(type(value) is dict and set(value)==set(names.split()))


def string(value):
    need(type(value) is str and 0<len(value)<=4096)


def token_event(worker,turn,response,seq,usage,source,kind='response',includes=False):
    return dict(worker_id=worker['id'],turn_id=turn['id'],attempt_id=turn['attempt_id'],
        meter='host',response_id=response,sequence=seq,kind=kind,complete=True,
        input_tokens=usage.get('input_tokens'),output_tokens=usage.get('output_tokens'),
        cache_read_tokens=usage.get('cache_read_input_tokens'),
        cache_write_tokens=usage.get('cache_creation_input_tokens'),
        reasoning_tokens=usage.get('reasoning_tokens'),input_includes_cache=includes,evidence=source)


def analyze(capture):
    fields(capture,'schema_version synthetic format host worker turns records inventory_complete')
    need(type(capture['schema_version']) is int and capture['schema_version']==1)
    need(type(capture['synthetic']) is bool and type(capture['inventory_complete']) is bool)
    need(capture['format'] in ('claude-transcript-v1','codex-app-server-v2','codex-native-session-v1'))
    h,w=capture['host'],capture['worker']
    fields(h,'application executable version identity_source worker_tool configuration_revision model_selection effort_selection independent_workers fresh_context')
    for name in ('application','executable','version','identity_source','worker_tool','configuration_revision'):string(h[name])
    need(h['identity_source'] in ('host_handshake','active_process','unconfirmed'))
    for name in ('model_selection','effort_selection','independent_workers','fresh_context'):need(type(h[name]) is bool)
    fields(w,'id session_id role category requested')
    for name in ('id','session_id','role','category'):string(w[name])
    fields(w['requested'],'model effort');string(w['requested']['model'])
    if w['requested']['effort'] is not None:string(w['requested']['effort'])
    need(type(capture['turns']) is list and 0<len(capture['turns'])<=1000)
    turns={}
    for t in capture['turns']:
        fields(t,'id attempt_id response_ids status')
        for name in ('id','attempt_id','status'):string(t[name])
        need(t['id'] not in turns and t['status'] in ('completed','interrupted','failed','inProgress'))
        need(type(t['response_ids']) is list and len(t['response_ids'])<=10000)
        for rid in t['response_ids']:string(rid)
        need(len(set(t['response_ids']))==len(t['response_ids']))
        turns[t['id']]=t
    need(type(capture['records']) is list and len(capture['records'])<=100000)
    encoded=json.dumps(capture,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    need(len(encoded)<=LIMIT)
    digest=hashlib.sha256(encoded).hexdigest()
    complete=capture['inventory_complete'] and all(t['status']=='completed' for t in turns.values())
    events=[];expected=[];models=set();configured={};observed_effort=None;reasons=[]
    seen={tid:set() for tid in turns}
    if capture['format']=='claude-transcript-v1':
        for seq,r in enumerate(capture['records']):
            need(type(r) is dict)
            if r.get('type')!='assistant':continue
            need(r.get('agentId')==w['id'] and r.get('sessionId')==w['session_id'])
            tid=r.get('turn_id',next(iter(turns)) if len(turns)==1 else None)
            need(tid in turns)
            m=r.get('message');need(type(m) is dict)
            rid=m.get('id');need(rid in turns[tid]['response_ids'])
            seen[tid].add(rid)
            model=m.get('model')
            if type(model) is str and model:models.add(model)
            else:complete=False
            usage=m.get('usage')
            if type(usage) is not dict:usage={}
            events.append(token_event(w,turns[tid],rid,seq,usage,'capture:'+digest))
        for tid,t in turns.items():
            complete=complete and bool(t['response_ids']) and seen[tid]==set(t['response_ids'])
            expected.append(dict(worker_id=w['id'],turn_id=tid,attempt_id=t['attempt_id'],
                                 meter='host',response_ids=t['response_ids'] or None))
        if len(models)!=1:complete=False;reasons.append('missing_or_mixed_executed_models')
        level='execution_observed' if complete else 'unknown'
        configured={'model':None,'effort':None}
        observed={'model':next(iter(models)) if complete else None,'effort':None}
        route='claude-native'
    elif capture['format']=='codex-app-server-v2':
        # Pair actual app-server request/response IDs; thread configuration is not execution identity.
        requests={};initial=None;turn_config={};completed=set();last_usage={};usage_order=[];incoming=set()
        for seq,r in enumerate(capture['records']):
            need(type(r) is dict)
            if not ('method' in r and 'id' in r):
                key=json.dumps(r,sort_keys=True,separators=(',',':'))
                if key in incoming:continue
                incoming.add(key)
            if 'method' in r and 'id' in r:
                need(type(r['id']) in (int,str) and r['id'] not in requests)
                requests[r['id']]=r
            elif 'result' in r and 'id' in r:
                req=requests.get(r['id']);need(req is not None)
                result=r['result'];need(type(result) is dict)
                if req['method']=='thread/start':
                    thread=result.get('thread',{})
                    need(thread.get('id')==w['id'] and thread.get('sessionId')==w['session_id'])
                    need(not thread.get('turns') and initial is None)
                    initial={'model':result.get('model'),'effort':result.get('reasoningEffort')}
                elif req['method']=='turn/start':
                    params=req.get('params',{});tid=result.get('turn',{}).get('id')
                    need(params.get('threadId')==w['id'] and tid in turns and tid not in turn_config)
                    # Overrides are requests, not a new acknowledged effective configuration.
                    matches=initial is not None and all(params.get(k,initial[v])==initial[v]
                        for k,v in [('model','model'),('effort','effort')])
                    turn_config[tid]=dict(initial) if matches else None
            elif 'method' in r:
                method=r['method'];params=r.get('params',{})
                if method in ('turn/completed','thread/tokenUsage/updated','model/rerouted'):
                    need(params.get('threadId')==w['id'])
                if method=='turn/completed':
                    t=params.get('turn',{});tid=t.get('id');need(tid in turns)
                    need(t.get('status')==turns[tid]['status'])
                    ids={i['id'] for i in t.get('items',[]) if i.get('type')=='agentMessage'}
                    seen[tid]=ids;completed.add(tid)
                elif method=='model/rerouted':
                    need(params.get('turnId') in turns);complete=False;reasons.append('substitution_reported')
                elif method=='thread/tokenUsage/updated':
                    tid=params.get('turnId');need(tid in turns)
                    totals=params.get('tokenUsage',{}).get('total')
                    need(type(totals) is dict)
                    if tid not in last_usage:usage_order.append(tid)
                    # Thread totals are snapshots. Retain all for monotonic validation below.
                    last_usage.setdefault(tid,[]).append((seq,totals))
        counter_map={'inputTokens':'input_tokens','outputTokens':'output_tokens',
                     'cachedInputTokens':'cache_read_input_tokens','cacheWriteInputTokens':'cache_creation_input_tokens',
                     'reasoningOutputTokens':'reasoning_tokens'}
        previous={key:0 for key in counter_map}
        previous_total=0
        all_sequences=[seq for tid in usage_order for seq,_ in last_usage[tid]]
        need(all_sequences==sorted(all_sequences))
        for tid in usage_order:
            baseline=dict(previous)
            for seq,totals in last_usage[tid]:
                for key in counter_map:
                    value=totals.get(key,0 if key=='cacheWriteInputTokens' else None)
                    need(type(value) is int and value>=previous[key]);previous[key]=value
                need(type(totals.get('totalTokens')) is int and totals['totalTokens']>=previous_total)
                need(totals['totalTokens']==previous['inputTokens']+previous['outputTokens'])
                previous_total=totals['totalTokens']
                delta={counter_map[key]:previous[key]-baseline[key] for key in counter_map}
                events.append(token_event(w,turns[tid],'turn-total',seq,delta,'capture:'+digest,'cumulative',True))
        for tid,t in turns.items():
            complete=complete and tid in completed and bool(t['response_ids']) and seen[tid]==set(t['response_ids'])
            expected.append(dict(worker_id=w['id'],turn_id=tid,attempt_id=t['attempt_id'],meter='host',response_ids=None))
        configs=[turn_config.get(tid) for tid in turns]
        config_known=complete and bool(initial and initial['model']) and all(c==initial for c in configs)
        configured=initial if config_known else {'model':None,'effort':None}
        if config_known and configured != w['requested']:
            config_known=False;reasons.append('configured_settings_differ')
        level='configuration_verified' if config_known else 'unknown'
        observed={'model':None,'effort':None};route='codex-skill'
        reasons.append('served_model_and_effort_not_exposed')
    else:
        # Native Codex session records can verify acknowledged configuration, not execution identity.
        meta=[];contexts={};completed={};response_usage={};response_order=[];snapshots={};snapshot_order=[];incoming=set()
        for seq,r in enumerate(capture['records']):
            need(type(r) is dict and type(r.get('type')) is str)
            key=json.dumps(r,sort_keys=True,separators=(',',':'))
            if key in incoming:continue
            incoming.add(key)
            kind=r['type']
            if kind=='session_meta':
                for name in ('thread_id','session_id','runtime_version'):string(r.get(name))
                need(r['thread_id']==w['id'] and r['session_id']==w['session_id'])
                parent=r.get('parent_thread_id')
                need(parent is None or type(parent) is str)
                if type(parent) is str and parent:meta.append((seq,r))
            elif kind=='turn_context':
                for name in ('thread_id','turn_id','model'):string(r.get(name))
                need(r['thread_id']==w['id'] and r['turn_id'] in turns)
                effort=r.get('reasoning_effort')
                need(effort is None or type(effort) is str)
                current=dict(model=r['model'],effort=effort)
                if r['turn_id'] in contexts and contexts[r['turn_id']]!=current:
                    complete=False;reasons.append('conflicting_turn_context')
                contexts[r['turn_id']]=current
            elif kind=='token_usage_record':
                for name in ('thread_id','turn_id','response_id'):string(r.get(name))
                need(r['thread_id']==w['id'] and r['turn_id'] in turns)
                usage=r.get('usage',{})
                need(type(usage) is dict)
                normalized={}
                for source,target in [('input_tokens','input_tokens'),('output_tokens','output_tokens'),
                                      ('cache_read_input_tokens','cache_read_input_tokens'),
                                      ('cache_creation_input_tokens','cache_creation_input_tokens'),
                                      ('reasoning_tokens','reasoning_tokens')]:
                    value=usage.get(source)
                    if value is None:continue
                    need(type(value) is int and value>=0);normalized[target]=value
                key=(r['turn_id'],r['response_id'])
                if key in response_usage and response_usage[key]!=normalized:
                    complete=False;reasons.append('conflicting_response_usage')
                else:
                    if key not in response_usage:response_order.append((seq,key))
                    response_usage[key]=normalized
            elif kind=='event_msg':
                event=r.get('event')
                need(type(event) is str)
                if event=='task_complete':
                    for name in ('thread_id','turn_id','status'):string(r.get(name))
                    need(r['thread_id']==w['id'] and r['turn_id'] in turns)
                    ids=r.get('response_ids',[])
                    need(type(ids) is list and len(ids)<=10000)
                    for rid in ids:string(rid)
                    current=dict(status=r['status'],response_ids=ids)
                    if r['turn_id'] in completed and completed[r['turn_id']]!=current:
                        complete=False;reasons.append('conflicting_completion')
                    completed[r['turn_id']]=current
                    seen[r['turn_id']]=set(ids)
                elif event=='token_count':
                    for name in ('thread_id','turn_id'):string(r.get(name))
                    need(r['thread_id']==w['id'] and r['turn_id'] in turns)
                    totals=r.get('totals',{})
                    need(type(totals) is dict)
                    if r['turn_id'] not in snapshots:snapshot_order.append(r['turn_id'])
                    snapshots.setdefault(r['turn_id'],[]).append((seq,totals))
                elif event in ('model_rerouted','substitution_reported'):
                    complete=False;reasons.append('substitution_reported')
                else:
                    need(False)
            else:
                need(False)
        counter_map={'input_tokens':'input_tokens','output_tokens':'output_tokens',
                     'cache_read_input_tokens':'cache_read_input_tokens','cache_creation_input_tokens':'cache_creation_input_tokens',
                     'reasoning_tokens':'reasoning_tokens'}
        sum_usage={key:0 for key in counter_map}
        response_totals={}
        for _,(tid,rid) in sorted(response_order):
            usage=response_usage[(tid,rid)]
            sum_usage={k:sum_usage[k]+usage.get(k,0) for k in counter_map}
            response_totals.setdefault(tid,{key:0 for key in counter_map})
            response_totals[tid]={k:response_totals[tid][k]+usage.get(k,0) for k in counter_map}
            events.append(token_event(w,turns[tid],rid,_,usage,'capture:'+digest))
        cumulative_only=not events
        if cumulative_only:
            all_sequences=[seq for tid in snapshot_order for seq,_ in snapshots[tid]]
            need(all_sequences==sorted(all_sequences))
            sum_usage={key:0 for key in counter_map}
            for tid in snapshot_order:
                previous={key:0 for key in counter_map}
                for seq,totals in snapshots[tid]:
                    for key in counter_map:
                        value=totals.get(key)
                        need(type(value) is int and value>=previous[key]);previous[key]=value
                    events.append(token_event(w,turns[tid],'turn-total',seq,{key:previous[key] for key in counter_map},
                        'capture:'+digest,'cumulative',True))
                sum_usage={k:sum_usage[k]+previous[k] for k in counter_map}
        else:
            all_sequences=[seq for tid in snapshot_order for seq,_ in snapshots[tid]]
            need(all_sequences==sorted(all_sequences))
            counted={}
            for tid in snapshot_order:
                previous={key:0 for key in counter_map}
                for _,totals in snapshots[tid]:
                    for key in counter_map:
                        value=totals.get(key)
                        need(type(value) is int and value>=previous[key]);previous[key]=value
                counted[tid]=dict(previous)
            for key in counter_map:
                for tid,usage in response_totals.items():
                    if key in counted.get(tid,{}) and counted[tid][key] < usage[key]:
                        complete=False;reasons.append('token_count_below_response_usage')
        parent_link=bool(meta)
        if not parent_link:reasons.append('missing_parent_association')
        runtime_known=bool(meta and len({m['runtime_version'] for _,m in meta})==1)
        if not runtime_known:reasons.append('missing_or_mixed_runtime_version')
        for tid,t in turns.items():
            done=completed.get(tid)
            responses_ok=seen[tid]==set(t['response_ids']) and (cumulative_only or bool(t['response_ids']))
            complete=complete and done is not None and done['status']==t['status'] and responses_ok
            expected.append(dict(worker_id=w['id'],turn_id=tid,attempt_id=t['attempt_id'],meter='host',
                                 response_ids=None if cumulative_only else (t['response_ids'] or None)))
        configs=[contexts.get(tid) for tid in turns]
        consistent=complete and all(c is not None for c in configs) and len({json.dumps(c,sort_keys=True,separators=(',',':')) for c in configs})==1
        initial=configs[0] if configs and configs[0] is not None else None
        config_known=consistent and runtime_known and initial['model']==w['requested']['model'] and initial['effort']==w['requested']['effort']
        configured=initial if config_known else {'model':None,'effort':None}
        if consistent and initial and not config_known:
            reasons.append('configured_settings_differ')
        level='configuration_verified' if config_known else 'unknown'
        observed={'model':None,'effort':None};route='codex-skill'
        reasons.append('served_model_and_effort_not_exposed')
    if h['identity_source']=='unconfirmed':level='unknown';reasons.append('executing_host_unconfirmed')
    scope=dict(host=route,role=w['role'],category=w['category'])
    usage=_USAGE['normalize'](dict(schema_version=1,scope=scope,
        inventory_complete=capture['inventory_complete'],expected=expected,events=events))
    modes=['off','shadow']
    eligible_host=all(h[k] for k in ('model_selection','independent_workers','fresh_context'))
    if eligible_host and level!='unknown' and not capture['synthetic']:
        modes.append('adaptive_after_qualification:'+level)
    return dict(schema_version=1,synthetic=capture['synthetic'],host=h,worker_id=w['id'],scope=scope,
        requested=w['requested'],configured=configured,observed=observed,evidence_level=level,
        complete=bool(complete),supported_modes=modes,missing_evidence=sorted(set(reasons)),
        usage=usage,capture_hash=digest,qualification=False)


def drift(previous,current):
    """Compare reviewed observations; never reassign or replay existing workers."""
    reasons=[]
    if previous['host']!=current['host']:reasons.append('host_changed')
    if LEVELS.index(current['evidence_level'])<LEVELS.index(previous['evidence_level']):reasons.append('evidence_lost')
    for key in ('model','effort'):
        if previous['observed'][key] is not None and current['observed'][key]!=previous['observed'][key]:
            reasons.append('observed_'+key+'_changed')
    if previous['configured']!=current['configured']:reasons.append('configuration_changed')
    return dict(adaptive_suspended=bool(reasons),reasons=reasons,replay=False)



def preflight(packet):
    fields(packet,'schema_version format host record_access')
    need(type(packet['schema_version']) is int and packet['schema_version']==1)
    need(packet['format']=='preflight-v1')
    h=packet['host']
    fields(h,'application executable version identity_source worker_tool configuration_revision model_selection effort_selection independent_workers fresh_context')
    for key in ('application','executable','version','identity_source','worker_tool','configuration_revision'):string(h[key])
    need(h['identity_source'] in ('host_handshake','active_process','unconfirmed'))
    for key in ('model_selection','effort_selection','independent_workers','fresh_context'):need(type(h[key]) is bool)
    need(packet['record_access'] in ('none','claude-owned-transcript','codex-owned-jsonrpc','codex-native-session-records'))
    missing=[]
    if h['identity_source']=='unconfirmed':missing.append('confirm_executing_host_not_another_installed_binary')
    if sys.version_info<(3,12):missing.append('python_3_12_required')
    for key in ('model_selection','independent_workers','fresh_context'):
        if not h[key]:missing.append(key+'_required_for_adaptive')
    lane={'none':None,'claude-owned-transcript':'execution_observed',
          'codex-owned-jsonrpc':'configuration_verified',
          'codex-native-session-records':'configuration_verified'}[packet['record_access']]
    if lane is None:missing.append('task_owned_supported_capture_unavailable')
    return dict(schema_version=1,host=h,python_version=list(sys.version_info[:3]),
        available_modes=['off','shadow'],candidate_evidence_lane=lane if not missing else None,
        missing_evidence=missing+['review_complete_capture','independent_role_quality_study','explicit_policy_activation'],
        qualification=False,observed=dict(model=None,effort=None))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--context',type=Path)
    parser.add_argument('--records',type=Path)
    args=parser.parse_args()
    try:
        if args.context is not None or args.records is not None:
            need(args.context is not None and args.records is not None)
            def read(path):
                with path.open('rb') as stream:raw=stream.read(LIMIT+1)
                need(len(raw)<=LIMIT)
                return raw
            def pairs(items):
                result={}
                for key,value in items:
                    need(key not in result);result[key]=value
                return result
            packet=json.loads(read(args.context),object_pairs_hook=pairs)
            need(type(packet) is dict and 'records' not in packet)
            packet['records']=[json.loads(line,object_pairs_hook=pairs) for line in read(args.records).splitlines() if line.strip()]
        else:
            packet=_USAGE['read_packet']()
        if type(packet) is dict and packet.get('format')=='preflight-v1':
            result=preflight(packet)
        else:
            need(sys.version_info>=(3,12))
            result=analyze(packet)
        print(json.dumps(result,sort_keys=True,allow_nan=False));return 0
    except (ValueError,KeyError,TypeError,OverflowError,UnicodeError,RecursionError,OSError):
        print('{"schema_version":1,"error":"invalid_evidence_input"}');return 2


if __name__=='__main__':raise SystemExit(main())
