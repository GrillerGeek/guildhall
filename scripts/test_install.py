#!/usr/bin/env python3
"""Opt-in, no-model install probes in temporary client profiles. Retains evidence."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import sys
import re
from evaluate_portable import snapshot

ROOT = Path(__file__).resolve().parent.parent


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native-codex', action='store_true')
    p.add_argument('--native-claude', action='store_true')
    p.add_argument('--skills-cli', help='Path to an already acquired skills CLI')
    p.add_argument('--skills-version', default='1.5.25', help='Exact expected installer version (default: 1.5.25)')
    args=p.parse_args()
    if not args.native_codex and not args.native_claude and not args.skills_cli:
        p.error('select --native-codex, --native-claude and/or --skills-cli; no personal installs are performed')
    if args.skills_cli:
        cli=Path(args.skills_cli).resolve()
        package=cli.parent/'package.json'
        if not package.is_file():
            package=cli.parent.parent/'package.json'
        if not package.is_file():
            p.error('--skills-cli must resolve to a skills package')
        metadata=json.loads(package.read_text())
        if metadata.get('name')!='skills' or metadata.get('version')!=args.skills_version:
            p.error('--skills-cli must match the exact --skills-version')
    temp=Path(tempfile.mkdtemp(prefix='guildhall-install-')).resolve()
    receipts=[]
    report={'directory':str(temp),'status':'running','receipts':receipts}
    if args.skills_cli:
        report['skills_version']=args.skills_version
    print(temp,flush=True)
    def run(argv,env,cwd,input_text=None):
        r=subprocess.run(list(map(str,argv)),cwd=cwd,env=env,text=True,capture_output=True,timeout=120,input=input_text)
        receipts.append({'argv':list(map(str,argv)),'cwd':str(cwd),'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        if r.returncode:
            raise RuntimeError(f'{argv[0]} failed: {r.stderr[-1000:]}')
        return r.stdout
    def environment(root):
        home=root/'home';home.mkdir(parents=True)
        for folder in ['.codex','.claude','.config','.cache','.state']:
            (home/folder).mkdir()
        # Explicit allowlist: no API credentials or personal client settings.
        return {'PATH':os.environ['PATH'],'HOME':str(home),'TMPDIR':str(root),
                'CODEX_HOME':str(home/'.codex'),'CLAUDE_CONFIG_DIR':str(home/'.claude'),
                'XDG_CONFIG_HOME':str(home/'.config'),'XDG_CACHE_HOME':str(home/'.cache'),
                'XDG_STATE_HOME':str(home/'.state'),'GIT_CONFIG_NOSYSTEM':'1',
                'GIT_CONFIG_GLOBAL':os.devnull,'DISABLE_TELEMETRY':'1','DO_NOT_TRACK':'1',
                'CI':'1','NO_COLOR':'1'}
    def installed_tools(bundle, env, cwd):
        guide=bundle/'references/model-routing.md'
        assert 'Credentials and activation' in guide.read_text(), 'Missing installed guide'
        for target in re.findall(r'\]\(([^)]+)\)',guide.read_text()):
            if '://' in target or target.startswith('#'):
                continue
            path=(guide.parent/target.split('#')[0]).resolve()
            assert path.is_relative_to(bundle.resolve()) and path.is_file(), 'Broken installed guide link'
        result=json.loads(run([sys.executable,'-I','-B',bundle/'scripts/route_model.py'],env,cwd,
                              (bundle/'resources/examples/off-request.json').read_text()))
        assert result['reason']=='router_disabled' and result['state']['calls_used']==0
        current=json.loads(run([sys.executable,'-I','-B',bundle/'scripts/route_model.py'],env,cwd,
                               (bundle/'resources/examples/off-request-v4.json').read_text()))
        assert current['schema_version']==4 and current['reason']=='router_disabled' and current['state']['calls_used']==0
        evaluation=json.loads(run([sys.executable,'-I','-B',bundle/'scripts/evaluate_routing.py','--demo'],env,cwd))
        assert evaluation['synthetic'] and evaluation['qualification'] is False
        headroom=json.loads(run([sys.executable,'-I','-B',bundle/'scripts/routing_study.py'],env,cwd,
                                (bundle/'resources/examples/headroom-packet.json').read_text()))
        assert headroom['status']=='headroom_observed' and headroom['qualification'] is False
        run([sys.executable,'-I','-B',bundle/'scripts/study_runner.py','--help'],env,cwd)
        configuration=json.loads(run([sys.executable,'-I','-B',bundle/'scripts/routing_config.py'],env,cwd,
            json.dumps(dict(operation='resolve',project_root=str(cwd.resolve()),host_route='codex-skill'))))
        assert configuration['reason']=='no_policy' and configuration['policy'] is None
        usage=json.loads(run([sys.executable,'-I','-B',bundle/'scripts/routing_usage.py'],env,cwd,
                             (bundle/'resources/examples/usage-records.json').read_text()))
        assert usage['meters']['host']['usage_tokens']==120 and usage['meters']['host']['cost_usd'] is None
        for source,level in [('claude','execution_observed'),('codex','configuration_verified')]:
            evidence=json.loads(run([sys.executable,'-I','-B',bundle/'scripts/routing_evidence.py'],env,cwd,
                (bundle/f'resources/examples/{source}-capture.json').read_text()))
            assert evidence['evidence_level']==level and evidence['qualification'] is False
    try:
        if args.native_codex:
            case=temp/'native-codex';env=environment(case);source=case/'source';source.mkdir()
            for rel in ['plugin','.agents']:
                shutil.copytree(ROOT/rel,source/rel)
            expected=snapshot(source/'plugin')
            run(['codex','plugin','marketplace','add',source,'--json'],env,case)
            result=json.loads(run(['codex','plugin','add','guildhall@guildhall-local','--json'],env,case))
            installed=Path(result['installedPath']);assert installed.is_relative_to(case)
            assert snapshot(installed)==expected,'Native installed contents/modes differ'
            listing=json.loads(run(['codex','plugin','list','--marketplace','guildhall-local','--json'],env,case))
            assert any(x['name']=='guildhall' and x['enabled'] and x['version']==json.loads((ROOT/'plugin/.codex-plugin/plugin.json').read_text())['version'] for x in listing['installed'])
            shutil.rmtree(source)
            assert snapshot(installed)==expected,'Native cache depends on removed source'
            installed_tools(installed/'skills/guildhall-quest',env,case)
            report['native_codex']='passed: installed/enabled, exact bytes/modes, source removal'
        if args.native_claude:
            case=temp/'native-claude';env=environment(case);source=case/'source';source.mkdir()
            project=case/'project';project.mkdir()
            for rel in ['plugin','.claude-plugin']:
                shutil.copytree(ROOT/rel,source/rel)
            expected=snapshot(source/'plugin')
            run(['claude','plugin','marketplace','add',source,'--scope','project'],env,project)
            result=json.loads(run(['claude','plugin','install','guildhall@guildhall-local','--scope','project','--json'],env,project))
            assert result['outcome']=='ok' and result['pluginId']=='guildhall@guildhall-local'
            listing=json.loads(run(['claude','plugin','list','--json'],env,project))
            entries=[x for x in listing if x['id']=='guildhall@guildhall-local']
            assert len(entries)==1
            entry=entries[0]
            assert entry['enabled'] and entry['scope']=='project'
            assert entry['version']==json.loads((ROOT/'plugin/.claude-plugin/plugin.json').read_text())['version']
            installed=Path(entry['installPath']).resolve();assert installed.is_relative_to(case)
            assert snapshot(installed)==expected,'Native Claude cached contents/modes differ'
            shutil.rmtree(source)
            assert snapshot(installed)==expected,'Native Claude cache depends on removed source'
            installed_tools(installed/'skills/guildhall-quest',env,project)
            report['native_claude']='passed: project installation/enabled, exact bytes/modes, source removal'
        if args.skills_cli:
            for host in ['codex','claude-code']:
                case=temp/host;env=environment(case);source=case/'source';project=case/'project';project.mkdir()
                shutil.copytree(ROOT/'plugin/skills/guildhall-quest',source)
                expected=snapshot(source)
                run([args.skills_cli,'add',source,'--agent',host,'--skill','guildhall-quest','--copy','--yes'],env,project)
                installed=project/('.agents' if host=='codex' else '.claude')/'skills/guildhall-quest'
                assert not installed.is_symlink(),'Expected copy installation'
                assert snapshot(installed)==expected,'Standalone installed bytes/modes differ'
                shutil.rmtree(source)
                assert snapshot(installed)==expected,'Standalone copy depends on removed source'
                installed_tools(installed,env,project)
                report[host]='passed: exact copied bytes/modes and source removal'
            # Repository-root discovery must select the complete generated
            # bundle, not the similarly named canonical authoring source.
            for host in ['codex','claude-code']:
                case=temp/f'repository-{host}';env=environment(case)
                source=case/'source';source.mkdir();project=case/'project';project.mkdir()
                for rel in ['plugin','.agents','.claude-plugin']:
                    shutil.copytree(ROOT/rel,source/rel)
                expected=snapshot(source/'plugin/skills/guildhall-quest')
                run([args.skills_cli,'add',source,'--agent',host,'--skill','guildhall-quest','--copy','--yes'],env,project)
                installed=project/('.agents' if host=='codex' else '.claude')/'skills/guildhall-quest'
                assert not installed.is_symlink(),'Expected repository-root copy installation'
                assert snapshot(installed)==expected,'Repository discovery selected an incomplete/different bundle'
                shutil.rmtree(source)
                assert snapshot(installed)==expected,'Repository-root copy depends on removed source'
                installed_tools(installed,env,project)
                report[f'repository_{host}']='passed: repository discovery selects exact complete bundle; source removal'
        report['status']='passed'
    except Exception as exc:
        report['status']='failed';report['error']=str(exc)
        raise
    finally:
        (temp/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k!='receipts'},indent=2))


if __name__=='__main__':
    main()
