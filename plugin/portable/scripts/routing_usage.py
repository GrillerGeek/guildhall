#!/usr/bin/env python3
"""Normalize reviewed usage records; offline, scoped, no billing/limit inference."""
from __future__ import annotations
import hashlib
import json
import sys

LIMIT = 16 * 1024 * 1024
IDENTITY = ('worker_id', 'turn_id', 'attempt_id', 'meter')
COUNTERS = ('input_tokens', 'output_tokens', 'cache_read_tokens', 'cache_write_tokens', 'reasoning_tokens')
EVENT_FIELDS = set(IDENTITY) | set(COUNTERS) | {'response_id','sequence','kind','complete','input_includes_cache','evidence'}


def require(ok):
    if not ok:
        raise ValueError('invalid_usage_input')


def text(value):
    require(type(value) is str and 0 < len(value) <= 4096)


def identity(value):
    for field in IDENTITY:
        text(value[field])
    require(value['meter'] in ('host','router'))
    return tuple(value[k] for k in IDENTITY)


def number(value):
    require(type(value) is int and 0 <= value <= 2**53-1)


def total(event):
    if not event['complete'] or event['input_tokens'] is None or event['output_tokens'] is None:
        return None
    tokens = event['input_tokens'] + event['output_tokens']
    if not event['input_includes_cache']:
        if any(event[k] is None for k in ('cache_read_tokens','cache_write_tokens')):
            return None
        tokens += event['cache_read_tokens'] + event['cache_write_tokens']
    # Reasoning is a subset of normalized output, never another additive counter.
    return tokens


def normalize(packet):
    require(type(packet) is dict and set(packet)=={'schema_version','scope','inventory_complete','expected','events'})
    require(type(packet['schema_version']) is int and packet['schema_version']==1)
    require(type(packet['inventory_complete']) is bool)
    scope=packet['scope']
    require(type(scope) is dict and set(scope)=={'host','role','category'})
    for value in scope.values():text(value)
    require(scope['host'] in ('claude-native','claude-skill','codex-skill'))
    require(type(packet['expected']) is list and len(packet['expected'])<=10000)
    require(type(packet['events']) is list and len(packet['events'])<=100000)
    encoded=json.dumps(packet,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    require(len(encoded)<=LIMIT)
    expected={}
    for entry in packet['expected']:
        require(type(entry) is dict and set(entry)==set(IDENTITY)|{'response_ids'})
        key=identity(entry);require(key not in expected)
        ids=entry['response_ids']
        require(ids is None or type(ids) is list and 0<len(ids)<=100000)
        if ids is not None:
            for rid in ids:text(rid)
            require(len(ids)==len(set(ids)))
        expected[key]=ids
    records={key:{} for key in expected}
    for event in packet['events']:
        require(type(event) is dict and set(event)==EVENT_FIELDS)
        key=identity(event);require(key in expected)
        text(event['response_id']);text(event['evidence']);number(event['sequence'])
        require(type(event['complete']) is bool and type(event['input_includes_cache']) is bool)
        require(event['kind'] in ('response','cumulative'))
        require((event['kind']=='cumulative') == (expected[key] is None))
        if expected[key] is not None:require(event['response_id'] in expected[key])
        for field in COUNTERS:
            if event[field] is not None:number(event[field])
        if event['reasoning_tokens'] is not None and event['output_tokens'] is not None:
            require(event['reasoning_tokens']<=event['output_tokens'])
        if event['input_includes_cache'] and event['input_tokens'] is not None:
            require(sum(event[k] or 0 for k in ('cache_read_tokens','cache_write_tokens'))<=event['input_tokens'])
        stream=event['response_id'] if event['kind']=='response' else 'cumulative'
        versions=records[key].setdefault(stream,{})
        sequence=event['sequence']
        require(sequence not in versions or versions[sequence]==event)
        versions[sequence]=event
    attempts=[]
    for key, streams in records.items():
        chosen=[]
        for versions in streams.values():
            ordered=[versions[i] for i in sorted(versions)]
            for previous,current in zip(ordered,ordered[1:]):
                require(previous['input_includes_cache']==current['input_includes_cache'])
                require(not previous['complete'] or current['complete'])
                for field in COUNTERS:
                    if previous[field] is not None:
                        require(current[field] is not None and current[field]>=previous[field])
            chosen.append(ordered[-1])
        complete=bool(chosen) and packet['inventory_complete']
        if expected[key] is not None:complete=complete and set(streams)==set(expected[key])
        values=[total(e) for e in chosen]
        complete=complete and all(v is not None for v in values)
        attempts.append(dict(zip(IDENTITY,key),complete=complete,
            usage_tokens=sum(values) if complete else None,
            evidence=sorted({e['evidence'] for e in chosen})))
    meters={}
    for meter in ('host','router'):
        items=[a for a in attempts if a['meter']==meter]
        complete=bool(items) and all(a['complete'] for a in items)
        meters[meter]=dict(complete=complete,usage_tokens=sum(a['usage_tokens'] for a in items) if complete else None,
                          cost_usd=None,attempts=len(items))
    return dict(schema_version=1,scope=scope,measurement_basis='normalized-token-usage-v1',
        input_hash=hashlib.sha256(encoded).hexdigest(),meters=meters,attempts=attempts,
        qualification=False)


def read_packet():
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result);result[key]=value
        return result
    raw=sys.stdin.buffer.read(LIMIT+1);require(len(raw)<=LIMIT)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _: require(False))


def main():
    try:
        require(sys.version_info>=(3,12))
        result=normalize(read_packet())
        print(json.dumps(result,allow_nan=False,sort_keys=True))
        return 0
    except (ValueError,TypeError,KeyError,OverflowError,UnicodeError,RecursionError):
        print('{"error":"invalid_usage_input","schema_version":1}')
        return 2


if __name__=='__main__':raise SystemExit(main())
