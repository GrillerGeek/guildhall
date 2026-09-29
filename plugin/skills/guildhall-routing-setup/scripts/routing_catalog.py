#!/usr/bin/env python3
"""Compile a reviewed host catalog against supplied live controls, offline."""
import json
from pathlib import Path
import runpy
import sys

_R=runpy.run_path(str(Path(__file__).with_name('route_model.py')),run_name='_catalog_router')


def compile_catalog(catalog, host):
    _R['validate'](catalog,_R['CATALOG_SCHEMA'])
    _R['validate'](host,_R['REQUEST_SCHEMA_V5']['properties']['host'])
    if catalog['host'] != host['route'] or not _R['valid_controls'](host):
        raise ValueError('catalog_host_or_controls_mismatch')
    profiles=[];excluded=[]
    for c in catalog['profiles']:
        if c['host'] != catalog['host'] or c['qualification'] is not None:
            raise ValueError('catalog_is_not_host_scoped_unqualified_profiles')
        if (_R['settings'](c) not in host['allowed_settings'] or not _R['controls'](c,host)
            or host['route'].startswith('claude') and _R['re'].search(r'(^|[^a-z])fable([^a-z]|$)',c['model'].lower())):
            excluded.append(c['id'])
        else:profiles.append(c)
    if len({c['id'] for c in profiles})!=len(profiles) or len({(c['model'],c['effort']) for c in profiles})!=len(profiles):
        raise ValueError('duplicate_catalog_profile')
    return dict(candidates=profiles,catalog_revision=_R['catalog_revision'](profiles),
                excluded=excluded,qualification=False,activation=False)


def main():
    try:
        packet=_R['strict_json'](sys.stdin.buffer.read(_R['LIMIT']+1))
        if set(packet)!= {'catalog','host'}:raise ValueError('invalid_packet')
        result=compile_catalog(**packet)
        print(json.dumps(result,sort_keys=True,allow_nan=False));return 0
    except (ValueError,TypeError,KeyError,RecursionError,OverflowError):
        print('{"error":"invalid_catalog_or_controls"}');return 2


if __name__=='__main__':raise SystemExit(main())
