"""Study headroom and real disposable-worktree orchestration, without model calls."""
import copy
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent.parent
STUDY=ROOT/'plugin/portable/scripts/routing_study.py'
RUNNER=ROOT/'plugin/portable/scripts/study_runner.py'


def manifest():
    fixtures=[dict(id=f'f{i}',split='development' if i<3 else 'holdout',role='docs-writer',category='docs',
        prompt='Update task.txt with ready.',rubric='The requested file contains ready.',allowed_files=['task.txt'],deterministic_candidate='a') for i in range(4)]
    return dict(schema_version=1,study_id='synthetic-study',synthetic=True,objective='latency',seed=5,repeats=2,
        baseline_candidate='a',candidates=[dict(id='a',model='synthetic-alpha',effort=None),dict(id='b',model='synthetic-beta',effort=None)],
        fixtures=fixtures,router_overhead=dict(elapsed_ms=5,usage_tokens=0,cost_usd=None),
        max_relative_spread=0.25,max_runs=100,timeout_seconds=60,usage_budget_tokens=100000,
        host=dict(route='codex-skill',evidence_requirement='configuration_verified',client_version='synthetic',configuration_revision='synthetic'))


def observations(m=None,fast=True):
    m=m or manifest()
    return [dict(fixture_id=f['id'],repeat=i,candidate=c['id'],accepted=True,critical_misses=0,violations=0,
        elapsed_ms=50 if fast and c['id']=='b' else 100,usage_tokens=100,cost_usd=None)
        for f in m['fixtures'] if f['split']=='development' for i in range(m['repeats']) for c in m['candidates']]


class HeadroomTests(unittest.TestCase):
    def setUp(self):self.s=runpy.run_path(str(STUDY))

    def test_observed_headroom_and_baseline_already_best(self):
        for fast,status in [(True,'headroom_observed'),(False,'no_measured_headroom')]:
            result=self.s['headroom'](manifest(),observations(fast=fast))
            self.assertEqual(result['status'],status);self.assertFalse(result['qualification'])

    def test_missing_unknown_and_noisy_are_inconclusive(self):
        for change in ['missing','unknown','noisy','quality']:
            rows=observations()
            if change=='missing':rows.pop()
            if change=='unknown':rows[0]['elapsed_ms']=None
            if change=='noisy':rows[0]['elapsed_ms']=1000
            if change=='quality':rows[0]['critical_misses']=1
            self.assertEqual(self.s['headroom'](manifest(),rows)['status'],'insufficient_evidence')

    def test_conditional_headroom_without_one_universal_winner(self):
        rows=observations()
        for r in rows:
            r['elapsed_ms']=40 if (r['fixture_id']=='f0' and r['candidate']=='a') or (r['fixture_id']!='f0' and r['candidate']=='b') else 100
        self.assertEqual(self.s['headroom'](manifest(),rows)['status'],'headroom_observed')

    def test_wrong_split_duplicate_and_nonfinite_rejected(self):
        for change in ['holdout','duplicate','nonfinite']:
            rows=observations()
            if change=='holdout':rows[0]['fixture_id']='f3'
            if change=='duplicate':rows.append(copy.deepcopy(rows[0]))
            if change=='nonfinite':rows[0]['elapsed_ms']=float('inf')
            with self.assertRaises(ValueError):self.s['headroom'](manifest(),rows)

    def test_zero_and_unknown_objective_do_not_manufacture_gain(self):
        rows=observations();rows[0]['elapsed_ms']=0
        self.assertEqual(self.s['headroom'](manifest(),rows)['status'],'insufficient_evidence')
        m=manifest();m['objective']='cost'
        self.assertEqual(self.s['headroom'](m,observations())['status'],'insufficient_evidence')


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='guildhall study ');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.repo=self.root/'repo';self.repo.mkdir()
        def git(*args):subprocess.run(['git','-C',str(self.repo),*args],check=True,capture_output=True)
        git('init','-q');(self.repo/'task.txt').write_text('before');(self.repo/'.gitignore').write_text('ignored.txt\n')
        git('add','.');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','baseline')
        self.r=runpy.run_path(str(RUNNER));self.m=manifest();self.directory=self.root/'study'

    def prepare(self,full=False):
        if not full:self.m['fixtures']=self.m['fixtures'][:1]
        self.r['prepare'](self.m,self.repo,self.directory)
        return self.r['read'](self.directory/'study.json')

    def outcome(self):return dict(worker_id='synthetic-worker',evidence=['synthetic:test'],elapsed_ms=100,
        usage_tokens=100,cost_usd=None,output='Completed requested edit.',status='completed',retries=0,host_report=None)

    def test_claim_is_not_replayed_and_boundary_includes_ignored_files(self):
        state=self.prepare();run=state['runs'][0];packet=self.r['claim'](self.directory,run['id'])
        with self.assertRaises(ValueError):self.r['claim'](self.directory,run['id'])
        (Path(packet['cwd'])/'ignored.txt').write_text('outside scope')
        result=self.r['record'](self.directory,run['id'],self.outcome())
        self.assertEqual(result['violations'],['ignored.txt'])
        with self.assertRaises(ValueError):self.r['record'](self.directory,run['id'],self.outcome())

    def test_changed_git_marker_refuses_without_reading_other_checkout(self):
        state=self.prepare();run=state['runs'][0];packet=self.r['claim'](self.directory,run['id'])
        marker=Path(packet['cwd'])/'.git';marker.write_text('gitdir: /not-this-study')
        with self.assertRaises(ValueError):self.r['record'](self.directory,run['id'],self.outcome())

    def test_unknown_consumption_blocks_next_claim(self):
        state=self.prepare();run=state['runs'][0];self.r['claim'](self.directory,run['id'])
        out=self.outcome();out['usage_tokens']=None;self.r['record'](self.directory,run['id'],out)
        with self.assertRaises(ValueError):self.r['claim'](self.directory,state['runs'][1]['id'])

    def test_blinding_freezes_actual_artifact_and_grades(self):
        state=self.prepare();run=state['runs'][0];packet=self.r['claim'](self.directory,run['id'])
        path=Path(packet['cwd'])/'task.txt';path.write_text('ready')
        self.r['record'](self.directory,run['id'],self.outcome())
        blind=self.r['blind'](self.directory)['packets'][0]
        self.assertEqual(blind['artifacts'][0]['content'],'ready')
        self.assertNotIn('candidate',blind);self.assertNotIn('strategy',blind)
        grade=dict(blind_id=run['id'],accepted=True,critical_misses=0,reason='matches rubric')
        self.r['grade'](self.directory,[grade])
        with self.assertRaises(ValueError):self.r['grade'](self.directory,[grade])
        path.write_text('tampered')
        with self.assertRaises(ValueError):self.r['blind'](self.directory)

    def test_holdout_requires_headroom_and_same_manifest(self):
        data=dict(manifest_hash=self.r['digest'](self.m),observations=observations(fast=False))
        with self.assertRaises(ValueError):self.r['prepare'](self.m,self.repo,self.directory,'holdout',data)
        data['observations']=observations();changed=copy.deepcopy(self.m);changed['objective']='usage'
        with self.assertRaises(ValueError):self.r['prepare'](changed,self.repo,self.directory,'holdout',data)

    def test_live_study_requires_correlated_shadow_override(self):
        self.m['synthetic']=False
        data=dict(manifest_hash=self.r['digest'](self.m),observations=observations())
        self.r['prepare'](self.m,self.repo,self.directory,'holdout',data)
        state=self.r['read'](self.directory/'study.json')
        run=next(r for r in state['runs'] if r['strategy']=='jev')
        receipt=dict(policy_hash='frozen-policy',input_fingerprint='task',host_snapshot={'version':'fixture'})
        decision=dict(status='dispatch',source='user_override',dispatch=dict(model='synthetic-beta',effort=None),
                      recommended_candidate='b',receipt=receipt)
        with self.assertRaises(ValueError):self.r['select'](self.directory,run['id'],decision)
        decision['study_recommendation']=dict(status='dispatch',reason='shadow',recommended_candidate='b',
            receipt=dict(receipt,router_identity='synthetic-router'))
        decision['study_recommendation']['receipt']['input_fingerprint']='another-task'
        with self.assertRaises(ValueError):self.r['select'](self.directory,run['id'],decision)
        decision['study_recommendation']['receipt']['input_fingerprint']='task'
        self.assertEqual(self.r['select'](self.directory,run['id'],decision)['candidate'],'b')

    def test_live_outcome_usage_and_effort_must_match_capture(self):
        self.m['synthetic']=False;self.m['host']['evidence_requirement']='execution_observed'
        for c in self.m['candidates']:c['effort']='high'
        state=self.prepare()
        for run,change in zip(state['runs'],['usage','effort','valid']):
            packet=self.r['claim'](self.directory,run['id'])
            out=self.outcome()
            out['host_report']=dict(synthetic=False,complete=True,worker_id=out['worker_id'],
                scope=dict(host='codex-skill',role='docs-writer',category='docs'),requested=packet['settings'],
                host=dict(version='synthetic',configuration_revision='synthetic'),evidence_level='execution_observed',
                observed=dict(model='concrete-fixture',effort='high'),
                usage=dict(meters=dict(host=dict(usage_tokens=100))))
            if change=='usage':out['host_report']['usage']['meters']['host']['usage_tokens']=500
            if change=='effort':out['host_report']['observed']['effort']=None
            if change=='usage':
                with self.assertRaises(ValueError):self.r['record'](self.directory,run['id'],out)
                out['usage_tokens']=500
            result=self.r['record'](self.directory,run['id'],out)
            self.assertEqual('<host-evidence>' in result['violations'],change=='effort')

    def test_complete_offline_study_exports_evaluator_input(self):
        state=self.prepare(full=True)
        def finish(directory,state,development):
            grades=[]
            for run in state['runs']:
                if run['candidate'] is None:
                    self.r['select'](directory,run['id'],dict(status='dispatch',dispatch=dict(model='synthetic-beta',effort=None)))
                    run['candidate']='b'
                packet=self.r['claim'](directory,run['id']);(Path(packet['cwd'])/'task.txt').write_text('ready')
                out=self.outcome();out['elapsed_ms']=100 if run['candidate']=='a' else 50
                self.r['record'](directory,run['id'],out)
                grades.append(dict(blind_id=run['id'],accepted=True,critical_misses=0,reason='synthetic grader sees ready'))
            self.r['blind'](directory);self.r['grade'](directory,grades)
            return self.r['export'](directory)
        development=finish(self.directory,state,True)
        holdout=self.root/'holdout';self.r['prepare'](self.m,self.repo,holdout,'holdout',development)
        state=self.r['read'](holdout/'study.json')
        self.assertEqual(state['prior_usage_tokens'],1200)
        result=finish(holdout,state,False)
        evaluation=self.r['_S']['_EVAL']['evaluate'](result)
        self.assertEqual(evaluation['status'],'eligible_for_review');self.assertFalse(evaluation['qualification'])

if __name__=='__main__':unittest.main()
