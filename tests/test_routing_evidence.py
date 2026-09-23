"""Sanitized synthetic captures exercise attribution guarantees, never live claims."""
import copy
import importlib.util
from pathlib import Path
import unittest
from test_routing import activate, digest, load_script, NOW
from test_routing_scoped_metrics import scoped_request

ROOT=Path(__file__).resolve().parent.parent


def capture(host='claude'):
    p=dict(schema_version=1,synthetic=True,format='claude-transcript-v1' if host=='claude' else 'codex-app-server-v2',
        host=dict(application='synthetic desktop',executable='/synthetic/codex',version='fixture-v1',
            identity_source='host_handshake',worker_tool='synthetic-worker',configuration_revision='revision-1',
            model_selection=True,effort_selection=True,independent_workers=True,fresh_context=True),
        worker=dict(id='w',session_id='s',role='docs-writer',category='docs',requested=dict(model='alias',effort=None)),
        turns=[dict(id='t',attempt_id='a',response_ids=['r'],status='completed')],inventory_complete=True,records=[])
    if host=='claude':
        p['records']=[dict(type='assistant',agentId='w',sessionId='s',message=dict(id='r',model='concrete-1',
            usage=dict(input_tokens=100,output_tokens=20,cache_read_input_tokens=10,cache_creation_input_tokens=0)))]
    else:
        p['records']=[dict(id=1,method='thread/start',params={}),dict(id=1,result=dict(model='alias',reasoningEffort=None,
            thread=dict(id='w',sessionId='s',turns=[]))),dict(id=2,method='turn/start',params=dict(threadId='w')),
            dict(id=2,result=dict(turn=dict(id='t'))),dict(method='thread/tokenUsage/updated',params=dict(threadId='w',turnId='t',
                tokenUsage=dict(total=dict(inputTokens=100,outputTokens=20,totalTokens=120,cachedInputTokens=10,reasoningOutputTokens=5)))),
            dict(method='turn/completed',params=dict(threadId='w',turn=dict(id='t',status='completed',items=[dict(type='agentMessage',id='r')])))]
    return p


def capture_native():
    p=capture('codex');p['format']='codex-native-session-v1'
    p['records']=[
        dict(type='session_meta',thread_id='w',parent_thread_id='parent-1',session_id='s',runtime_version='0.155.0-alpha.16.3'),
        dict(type='turn_context',thread_id='w',turn_id='t',model='alias',reasoning_effort=None),
        dict(type='token_usage_record',thread_id='w',turn_id='t',response_id='r',
             usage=dict(input_tokens=100,output_tokens=20,cache_read_input_tokens=10,cache_creation_input_tokens=0,reasoning_tokens=5)),
        dict(type='event_msg',event='token_count',thread_id='w',turn_id='t',
             totals=dict(input_tokens=100,output_tokens=20,cache_read_input_tokens=10,cache_creation_input_tokens=0,reasoning_tokens=5)),
        dict(type='event_msg',event='task_complete',thread_id='w',turn_id='t',status='completed',response_ids=['r'])]
    return p


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('evidence',ROOT/'plugin/portable/scripts/routing_evidence.py')
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)

    def test_preflight_without_records_never_claims_qualification(self):
        packet=dict(schema_version=1,format='preflight-v1',host=capture()['host'],record_access='none')
        result=self.module.preflight(packet)
        self.assertIsNone(result['candidate_evidence_lane'])
        self.assertFalse(result['qualification'])
        packet['record_access']='codex-owned-jsonrpc'
        self.assertEqual(self.module.preflight(packet)['candidate_evidence_lane'],'configuration_verified')
        packet['record_access']='codex-native-session-records'
        self.assertEqual(self.module.preflight(packet)['candidate_evidence_lane'],'configuration_verified')

    def test_claude_observes_concrete_model_not_effort(self):
        result=self.module.analyze(capture())
        self.assertEqual(result['evidence_level'],'execution_observed')
        self.assertEqual(result['observed'],dict(model='concrete-1',effort=None))
        self.assertEqual(result['usage']['meters']['host']['usage_tokens'],130)
        self.assertFalse(result['qualification'])
        self.assertNotIn('adaptive_after_qualification:execution_observed',result['supported_modes'])

    def test_codex_config_is_never_observation(self):
        result=self.module.analyze(capture('codex'))
        self.assertEqual(result['evidence_level'],'configuration_verified')
        self.assertEqual(result['observed'],dict(model=None,effort=None))
        self.assertEqual(result['usage']['meters']['host']['usage_tokens'],120)

    def test_all_responses_must_have_same_model(self):
        p=capture();p['turns'][0]['response_ids'].append('r2')
        self.assertEqual(self.module.analyze(p)['evidence_level'],'unknown')
        r=copy.deepcopy(p['records'][0]);r['message'].update(id='r2',model='concrete-2');p['records'].append(r)
        self.assertEqual(self.module.analyze(p)['evidence_level'],'unknown')

    def test_wrong_worker_or_session_rejected(self):
        for field in ['agentId','sessionId']:
            p=capture();p['records'][0][field]='other'
            with self.assertRaises(ValueError):self.module.analyze(p)

    def test_duplicate_claude_messages_not_double_counted(self):
        p=capture();p['records']*=2
        self.assertEqual(self.module.analyze(p)['usage']['meters']['host']['usage_tokens'],130)

    def test_interruption_and_unconfirmed_host_do_not_qualify(self):
        p=capture();p['turns'][0]['status']='interrupted'
        self.assertEqual(self.module.analyze(p)['evidence_level'],'unknown')
        p=capture();p['host']['identity_source']='unconfirmed'
        self.assertEqual(self.module.analyze(p)['evidence_level'],'unknown')

    def test_codex_reroute_or_unacknowledged_override_invalidates(self):
        p=capture('codex');p['records'].append(dict(method='model/rerouted',params=dict(threadId='w',turnId='t',fromModel='alias',toModel='other')))
        self.assertEqual(self.module.analyze(p)['evidence_level'],'unknown')
        p=capture('codex');p['records'][2]['params']['model']='other'
        self.assertEqual(self.module.analyze(p)['evidence_level'],'unknown')

    def test_replayed_codex_response_and_usage_are_deduplicated(self):
        p=capture('codex');p['records'].insert(2,copy.deepcopy(p['records'][1]));p['records'].append(copy.deepcopy(p['records'][-2]))
        result=self.module.analyze(p)
        self.assertEqual(result['evidence_level'],'configuration_verified')
        self.assertEqual(result['usage']['meters']['host']['usage_tokens'],120)

    def test_native_codex_session_records_support_configuration_verified(self):
        result=self.module.analyze(capture_native())
        self.assertEqual(result['evidence_level'],'configuration_verified')
        self.assertEqual(result['configured'],dict(model='alias',effort=None))
        self.assertEqual(result['observed'],dict(model=None,effort=None))
        self.assertEqual(result['usage']['meters']['host']['usage_tokens'],130)

    def test_native_codex_missing_parent_or_conflicting_context_fails_closed(self):
        p=capture_native();p['records'][0]['parent_thread_id']=''
        self.assertEqual(self.module.analyze(p)['evidence_level'],'unknown')
        p=capture_native();p['records'].insert(2,dict(type='turn_context',thread_id='w',turn_id='t',model='other',reasoning_effort=None))
        self.assertEqual(self.module.analyze(p)['evidence_level'],'unknown')

    def test_native_codex_token_count_snapshots_normalize_without_double_counting(self):
        p=capture_native()
        p['records']=[r for r in p['records'] if r['type']!='token_usage_record']
        p['records'].insert(2,dict(type='event_msg',event='token_count',thread_id='w',turn_id='t',
             totals=dict(input_tokens=60,output_tokens=10,cache_read_input_tokens=5,cache_creation_input_tokens=0,reasoning_tokens=2)))
        result=self.module.analyze(p)
        self.assertEqual(result['evidence_level'],'configuration_verified')
        self.assertEqual(result['usage']['meters']['host']['usage_tokens'],120)

    def test_native_codex_multi_turn_snapshots_are_scoped_per_turn(self):
        p=capture_native()
        p['turns'].append(dict(id='t2',attempt_id='a2',response_ids=['r2'],status='completed'))
        p['records'].extend([
            dict(type='turn_context',thread_id='w',turn_id='t2',model='alias',reasoning_effort=None),
            dict(type='token_usage_record',thread_id='w',turn_id='t2',response_id='r2',
                 usage=dict(input_tokens=20,output_tokens=5,cache_read_input_tokens=1,cache_creation_input_tokens=0,reasoning_tokens=1)),
            dict(type='event_msg',event='token_count',thread_id='w',turn_id='t2',
                 totals=dict(input_tokens=20,output_tokens=5,cache_read_input_tokens=1,cache_creation_input_tokens=0,reasoning_tokens=1)),
            dict(type='event_msg',event='task_complete',thread_id='w',turn_id='t2',status='completed',response_ids=['r2'])])
        result=self.module.analyze(p)
        self.assertEqual(result['evidence_level'],'configuration_verified')
        self.assertEqual(result['usage']['meters']['host']['usage_tokens'],156)

    def test_alias_drift_suspends_without_replay(self):
        previous=self.module.analyze(capture());p=capture();p['records'][0]['message']['model']='concrete-2'
        result=self.module.drift(previous,self.module.analyze(p))
        self.assertTrue(result['adaptive_suspended']);self.assertFalse(result['replay'])

    def test_v3_configuration_lane_is_explicit_and_strong_default_holds(self):
        r=scoped_request();r['schema_version']=r['policy']['schema_version']=3
        r['policy']['required_evidence']='configuration_verified';r['host']['evidence_level']='configuration_verified'
        r['host']['attribution']='unknown'
        for c in r['policy']['candidates']:
            c['qualification']=dict(report_hash='2'*64,profile_hash=digest({k:v for k,v in c.items() if k!='qualification'}),
                expires_at=NOW+3600,host_revision=r['host']['configuration_revision'],router_request=r['policy']['router_model'],
                router_identity='synthetic-jev-version-1',roles=['docs-writer'],categories=['docs'],
                evidence_level='configuration_verified',observed_model=None,observed_effort=None,objective='latency')
        router=load_script();r['policy']['mode']='adaptive';r['policy']['allowed_candidates']=['base'];activate(r)
        self.assertEqual(router.route(r,now=NOW)['reason'],'single_candidate')
        r['policy']['required_evidence']='execution_observed';activate(r)
        self.assertEqual(router.route(r,now=NOW)['reason'],'adaptive_unqualified')
        r['policy']['required_evidence']='configuration_verified';r['policy']['objective']='usage';activate(r)
        self.assertEqual(router.route(r,now=NOW)['reason'],'adaptive_unqualified')

if __name__=='__main__':unittest.main()
