#!/usr/bin/env python3
"""Bounded handoff chunks and supplied host-visible delivery checks; no model calls."""
from __future__ import annotations
import hashlib
import json
import math
import re
import sys

def obj(**fields):
    return dict(type='object', properties=fields, required=list(fields))


def enum(values):
    return {'enum': values, 'type': 'integer' if type(values[0]) is int else 'string'}


def array(items, maximum=16, minimum=0):
    return dict(type='array', items=items, maxItems=maximum, minItems=minimum)


def nullable(schema):
    return {'anyOf': [schema, {'type': 'null'}]}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def evidence_hash(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def validate(value, schema):
    """Validate the bounded delivery records without external dependencies."""
    if 'anyOf' in schema:
        for option in schema['anyOf']:
            try:
                validate(value, option)
                return
            except ValueError:
                pass
        raise ValueError('invalid_delivery_input')
    if 'enum' in schema:
        need(any(type(value) is type(item) and value == item for item in schema['enum']))
        return
    kind = schema['type']
    types = {'object': dict, 'array': list, 'string': str, 'integer': int,
             'boolean': bool, 'null': type(None)}
    if kind == 'number':
        need(type(value) in (int, float) and math.isfinite(value))
    else:
        need(type(value) is types[kind])
    if kind == 'object':
        need(set(value) == set(schema['properties']))
        for key, item in value.items():
            validate(item, schema['properties'][key])
    elif kind == 'array':
        need(schema.get('minItems', 0) <= len(value) <= schema['maxItems'])
        for item in value:
            validate(item, schema['items'])
        need(len({canonical(item) for item in value}) == len(value))
    elif kind == 'string':
        need(schema.get('minLength', 0) <= len(value) <= schema.get('maxLength', 256))
        need('pattern' not in schema or re.fullmatch(schema['pattern'], value) is not None)
    elif kind in ('number', 'integer'):
        need('minimum' not in schema or value >= schema['minimum'])
        need('maximum' not in schema or value <= schema['maximum'])


LIMIT=2*1024*1024
STRING=dict(type='string',minLength=1,maxLength=256)
CID=dict(STRING,maxLength=32,pattern=r'^[a-z][a-z0-9_-]{0,31}$')
HASH=dict(type='string',pattern=r'^[0-9a-f]{64}$',minLength=64,maxLength=64)
MATERIAL=obj(id=CID,text=dict(type='string',maxLength=262144))
CHUNK=obj(id=dict(type='string',pattern=r'^[a-z][a-z0-9_-]{0,31}:[0-9]+$',maxLength=40),
          bytes=dict(type='integer',minimum=0,maximum=4096),sha256=HASH)
MANIFEST=obj(schema_version=enum([1]),chunks=array(CHUNK,1024,1),
             max_read_attempts=dict(type='integer',minimum=1,maximum=4096),
             max_read_ms=dict(type='integer',minimum=1,maximum=3600000))
OBSERVATION=obj(chunk_id=CHUNK['properties']['id'],attempt=dict(type='integer',minimum=0),
    text=dict(type='string',maxLength=8192),truncated=nullable(dict(type='boolean')),
    source=enum(['host_tool_output','worker_assertion','unavailable']),evidence=nullable(STRING),
    elapsed_ms=nullable(dict(type='number',minimum=0)))
PACKET=obj(schema_version=enum([1]),host=enum(['claude-native','claude-skill','codex-skill']),
           worker_id=STRING,manifest=MANIFEST,observations=array(OBSERVATION,4096))
TRUNCATED=re.compile(r'(?:output (?:was |is )?truncated|truncated output|\[\.\.\.\s*truncated\s*\.\.\.\]|omitted \d+ lines)',re.I)


def need(value):
    if not value:raise ValueError('invalid_delivery_input')


def chunks(materials):
    validate(materials,array(MATERIAL,64,1))
    need(len({m['id'] for m in materials})==len(materials))
    need(sum(len(m['text'].encode()) for m in materials)<=LIMIT//2)
    result=[]
    for material in materials:
        # At most 512 Unicode characters / 2048 UTF-8 bytes per visible read.
        pieces=[material['text'][n:n+512] for n in range(0,len(material['text']),512)] or ['']
        result.extend(dict(id=f"{material['id']}:{i}",text=text) for i,text in enumerate(pieces))
    need(len(result)<=1024)
    return result


def plan(materials,max_read_attempts,max_read_ms):
    result=dict(schema_version=1,chunks=[dict(id=c['id'],bytes=len(c['text'].encode()),
        sha256=hashlib.sha256(c['text'].encode()).hexdigest()) for c in chunks(materials)],
        max_read_attempts=max_read_attempts,max_read_ms=max_read_ms)
    validate(result,MANIFEST)
    need(max_read_attempts>=len(result['chunks']))
    return result


def emit(materials,chunk_id):
    result=next((c for c in chunks(materials) if c['id']==chunk_id),None)
    need(result is not None)
    return result


def assess(packet):
    validate(packet,PACKET)
    manifest=packet['manifest'];expected={c['id']:c for c in manifest['chunks']}
    need(len(expected)==len(manifest['chunks']))
    observations=packet['observations'];seen=set();complete=set();failed=set();unknown=set()
    elapsed=0;timing_known=True
    for o in observations:
        cid=o['chunk_id'];identity=(cid,o['attempt'])
        need(cid in expected and identity not in seen);seen.add(identity)
        if o['elapsed_ms'] is None:timing_known=False
        else:elapsed+=o['elapsed_ms']
        if o['source']!='host_tool_output' or o['truncated'] is None or o['evidence'] is None:
            unknown.add(cid);continue
        raw=o['text'].encode()
        if (o['truncated'] or TRUNCATED.search(o['text']) or len(raw)!=expected[cid]['bytes'] or
            hashlib.sha256(raw).hexdigest()!=expected[cid]['sha256']):
            failed.add(cid)
        else:complete.add(cid)
    missing=sorted(set(expected)-complete)
    exhausted=len(observations)>manifest['max_read_attempts'] or elapsed>manifest['max_read_ms']
    status=('budget_exceeded' if exhausted else 'complete' if not missing else
            'incomplete' if failed-set(complete) or set(missing)-unknown else 'unknown')
    remaining=max(0,manifest['max_read_attempts']-len(observations))
    return dict(schema_version=1,host=packet['host'],worker_id=packet['worker_id'],
        status=status,missing_chunks=missing,
        manifest_hash=evidence_hash(manifest),evidence_hash=evidence_hash(packet),
        attempts_used=len(observations),attempts_remaining=remaining,read_ms=elapsed if timing_known else None,
        recoverable_chunks=missing[:remaining] if not exhausted and timing_known and elapsed<manifest['max_read_ms'] else [],
        replay_worker=False,proves_worker_comprehension=False)


def main():
    try:
        raw=sys.stdin.buffer.read(LIMIT+1);need(len(raw)<=LIMIT)
        def pairs(items):
            result={}
            for key,value in items:
                need(key not in result);result[key]=value
            return result
        packet=json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:need(False))
        operation=packet.pop('operation')
        need(operation in ('plan','emit','assess'))
        result=globals()[operation](**packet)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True,allow_nan=False));return 0
    except (ValueError,TypeError,KeyError,RecursionError,OverflowError,UnicodeError):
        print('{"error":"invalid_delivery_input"}');return 2


if __name__=='__main__':raise SystemExit(main())
