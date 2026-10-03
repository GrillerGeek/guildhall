"""Offline truncation/recovery and normal-work feedback, without paid workers."""
import copy
import runpy
import json
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
import unittest
from test_routing import ROOT, load_script, provider, NOW
from test_routing_dynamic import dynamic_request
import test_routing_study as study_tests

D=runpy.run_path(str(ROOT/'plugin/portable/scripts/routing_delivery.py'))
F=runpy.run_path(str(ROOT/'plugin/portable/scripts/routing_feedback.py'))


def packet(host='codex-skill'):
    materials=[dict(id='role',text='Allowed role contract. '+('é漢字 '*180)),dict(id='reference',text='Required credential details and GUI inheritance.')]
    chunk_list=D['chunks'](materials)
    manifest=D['plan'](materials,len(chunk_list)+2,1000)
    return dict(schema_version=1,host=host,worker_id='synthetic-worker',manifest=manifest,
        observations=[dict(chunk_id=c['id'],attempt=0,text=c['text'],truncated=False,source='host_tool_output',evidence='synthetic-visible-tool-result',elapsed_ms=1) for c in chunk_list])


class DeliveryTests(unittest.TestCase):
    def test_complete_truncated_missing_duplicated_and_unknown_on_every_host(self):
        for host in ['codex-skill','claude-native','claude-skill']:
            p=packet(host);self.assertEqual(D['assess'](p)['status'],'complete')
            for change in ['truncated','marker','omitted','modified','assertion','unknown']:
                q=copy.deepcopy(p)
                if change=='truncated':q['observations'][0]['truncated']=True
                if change=='marker':q['observations'][0]['text']='Warning: truncated output'
                if change=='omitted':q['observations'].pop()
                if change=='modified':q['observations'][0]['text']+='X'
                if change=='assertion':
                    for o in q['observations']:o['source']='worker_assertion'
                if change=='unknown':
                    for o in q['observations']:o['truncated']=None
                out=D['assess'](q);self.assertFalse(out['comparison_eligible'],change)
            p['observations'].append(copy.deepcopy(p['observations'][0]))
            with self.assertRaises(ValueError):D['assess'](p)

    def test_recover_only_missing_chunk_without_restarting_budget(self):
        p=packet();original=copy.deepcopy(p['observations'][0])
        p['observations'][0]['text']='short';p['observations'][0]['truncated']=True
        out=D['assess'](p);self.assertEqual(out['recoverable_chunks'],[original['chunk_id']])
        original['attempt']=1;p['observations'].append(original)
        out=D['assess'](p);self.assertTrue(out['comparison_eligible']);self.assertFalse(out['replay_worker'])
        p['observations'][-1]['elapsed_ms']=2000
        self.assertEqual(D['assess'](p)['status'],'budget_exceeded')

    def test_emit_is_bounded_and_hashing_source_alone_is_not_delivery(self):
        materials=[dict(id='ref',text='漢字'*3000)]
        manifest=D['plan'](materials,20,500)
        for c in manifest['chunks']:
            emitted=D['emit'](materials,c['id'])
            self.assertLessEqual(len(emitted['text'].encode()),2048)
        p=packet();p['observations']=[]
        self.assertFalse(D['assess'](p)['comparison_eligible'])


    def test_delivery_cli_works_from_each_independently_copied_skill(self):
        for name in ['guildhall-quest','guildhall-routing-setup']:
            with tempfile.TemporaryDirectory() as tmp:
                installed=Path(tmp)/'skill';shutil.copytree(ROOT/'plugin/skills'/name,installed)
                result=subprocess.run([sys.executable,'-I','-B',str(installed/'scripts/routing_delivery.py')],
                    input=json.dumps(dict(operation='assess',packet=packet())),text=True,capture_output=True,timeout=10)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertTrue(json.loads(result.stdout)['comparison_eligible'])


class StudyDeliveryTests(unittest.TestCase):
    setUp=study_tests.RunnerTests.setUp
    prepare=study_tests.RunnerTests.prepare
    outcome=study_tests.RunnerTests.outcome

    def test_invalid_trial_is_not_graded_or_exported_and_consumption_remains(self):
        state=self.prepare();p=packet()
        for run in state['runs']:
            self.r['delivery_plan'](self.directory,run['id'],p['manifest'])
            self.r['claim'](self.directory,run['id'])
            bad=copy.deepcopy(p);bad['observations'][0]['truncated']=True
            self.r['delivery'](self.directory,run['id'],bad)
            result=self.r['record'](self.directory,run['id'],self.outcome())
            self.assertFalse(result['comparison_eligible'])
        self.assertEqual(self.r['blind'](self.directory)['packets'],[])
        with self.assertRaises(ValueError):self.r['grade'](self.directory,[dict(blind_id=state['runs'][0]['id'],accepted=True,critical_misses=0,reason='would hide bad delivery')])
        result=self.r['export'](self.directory)
        self.assertEqual(result['status'],'invalid_input_delivery')
        saved=self.r['read'](self.directory/'study.json')
        self.assertEqual(sum(r['outcome']['usage_tokens'] for r in saved['runs']),400)

    def test_delivery_manifest_freezes_before_claim_and_recovery_appends(self):
        state=self.prepare();run=state['runs'][0];p=packet()
        self.r['delivery_plan'](self.directory,run['id'],p['manifest']);self.r['claim'](self.directory,run['id'])
        with self.assertRaises(ValueError):self.r['delivery_plan'](self.directory,run['id'],p['manifest'])
        missing=copy.deepcopy(p);missing['observations'].pop()
        self.r['delivery'](self.directory,run['id'],missing)
        self.assertEqual(self.r['delivery'](self.directory,run['id'],p)['status'],'complete')
        with self.assertRaises(ValueError):self.r['delivery'](self.directory,run['id'],missing)
        self.assertTrue(self.r['record'](self.directory,run['id'],self.outcome())['comparison_eligible'])

    def test_legacy_live_trial_without_delivery_is_unknown_not_model_failure(self):
        self.m['synthetic']=False;state=self.prepare();run=state['runs'][0]
        state['schema_version']=1;self.r['save'](self.directory,state)
        self.r['claim'](self.directory,run['id'])
        result=self.r['record'](self.directory,run['id'],self.outcome())
        self.assertEqual(result['input_delivery'],'unknown')
        self.assertEqual(self.r['blind'](self.directory)['packets'],[])


    def test_new_live_study_requires_manifest_and_stops_after_bad_delivery(self):
        self.m['synthetic']=False;state=self.prepare();run=state['runs'][0];p=packet()
        with self.assertRaises(ValueError):self.r['claim'](self.directory,run['id'])
        for item in state['runs']:self.r['delivery_plan'](self.directory,item['id'],p['manifest'])
        self.r['claim'](self.directory,run['id'])
        p['observations'][0]['truncated']=True
        self.r['delivery'](self.directory,run['id'],p)
        self.r['record'](self.directory,run['id'],self.outcome())
        with self.assertRaises(ValueError):self.r['claim'](self.directory,state['runs'][1]['id'])


class FeedbackTests(unittest.TestCase):
    def test_unknown_identity_and_usage_need_no_runs_but_known_substitution_suspends(self):
        r=dynamic_request();decision=load_script().route(r,transport=lambda *a:provider(),now=NOW)
        outcome=dict(worker_id='worker',status='completed',tests='passed',review='unknown',retries=0,evidence=['test-result'],delivery='complete')
        observation=dict(source='unknown',evidence=None,requested_resolved=dict(model=None,effort=None),observed=dict(model=None,effort=None),configuration_supported=None)
        result=F['feedback'](r,decision,outcome,observation)
        self.assertFalse(result['state']['adaptive_suspended']);self.assertIsNone(result['usage'])
        self.assertIsNone(result['subscription_allowance_percent']);self.assertEqual(result['additional_runs'],0)
        observation.update(source='host_metadata',evidence='host-tool-result',requested_resolved=dict(model='resolved-fast',effort='high'),observed=dict(model='forced-model',effort=None))
        result=F['feedback'](r,decision,outcome,observation)
        self.assertTrue(result['state']['adaptive_suspended']);self.assertFalse(result['replay_worker'])
        self.assertEqual(result['state']['calls_used'],decision['state']['calls_used'])
        observation['source']='worker_assertion'
        self.assertIsNone(F['feedback'](r,decision,outcome,observation)['observed']['model'])


    def test_feedback_correlates_task_and_usage_and_preserves_unknown_totals(self):
        from test_routing_usage import packet as usage_packet
        r=dynamic_request();decision=load_script().route(r,transport=lambda *a:provider(),now=NOW)
        outcome=dict(worker_id='w',status='completed',tests='passed',review='unknown',retries=0,evidence=['tests'],delivery='unknown')
        observation=dict(source='unknown',evidence=None,requested_resolved=dict(model=None,effort=None),observed=dict(model=None,effort=None),configuration_supported=None)
        usage=usage_packet();usage['inventory_complete']=False
        result=F['feedback'](r,decision,outcome,observation,usage)
        self.assertIsNone(result['usage']['meters']['host']['usage_tokens'])
        usage['scope']['role']='pr-author'
        with self.assertRaises(ValueError):F['feedback'](r,decision,outcome,observation,usage)
        r['task']['risk']='high'
        with self.assertRaises(ValueError):F['feedback'](r,decision,outcome,observation)

if __name__=='__main__':unittest.main()
