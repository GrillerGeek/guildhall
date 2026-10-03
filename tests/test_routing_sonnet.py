"""Sonnet catalog refresh and version-aware approvals; synthetic controls only."""
import copy
import json
import runpy
import unittest
from test_routing import ROOT, NOW, activate, provider, load_script
from test_routing_dynamic import dynamic_request, refresh_controls
import test_routing_config as config_tests


def mapped_request(host='claude-native', version='claude-sonnet-5-5'):
    r=dynamic_request(host=host)
    for c,model in zip(r['policy']['candidates'],['sonnet','opus']):c['model']=model;c['effort']=None
    r['baseline']=dict(model='sonnet',effort=None)
    r['host'].update(client_version='2.1.284',provider='anthropic',effort_selection=False,
        allowed_settings=[dict(model='sonnet',effort=None),dict(model='opus',effort=None)],
        model_resolutions=[dict(requested_model='sonnet',resolved_model=version,default_effort='medium',
            source='configuration',reference='current-provider-model-mapping')])
    r['policy']['catalog_revision']=load_script().catalog_revision(r['policy']['candidates'])
    return activate(refresh_controls(r))


class SonnetTests(unittest.TestCase):
    def setUp(self):
        self.router=load_script()
        self.compile=runpy.run_path(str(ROOT/'plugin/portable/scripts/routing_catalog.py'))['compile_catalog']

    def catalog(self,host):return json.loads((ROOT/f'plugin/portable/resources/catalogs/{host}.json').read_text())

    def test_legacy_v5_without_mapping_keeps_schema_and_fingerprint(self):
        r=dynamic_request();self.router.validate_request(r)
        fingerprint=self.router.control_fingerprint(r['host'])
        r['host']['model_resolutions']=[];self.router.validate_request(r)
        self.assertEqual(fingerprint,self.router.control_fingerprint(r['host']))
        self.assertEqual(self.router.route(r,transport=lambda *a:provider(),now=NOW)['source'],'jev')

    def test_provider_mapping_specializes_only_known_sonnet_55(self):
        for host in ['claude-native','claude-skill']:
            catalog=self.catalog(host);original=copy.deepcopy(catalog)
            r=mapped_request(host);result=self.compile(catalog,r['host'])
            sonnet=next(c for c in result['candidates'] if c['model']=='sonnet')
            self.assertEqual(sonnet['routing_profile']['work_types'],['implementation','debug','docs'])
            self.assertEqual(sonnet['effort'],None)
            self.assertIsNone(sonnet['quality']);self.assertEqual(sonnet['measurements'],[])
            self.assertIsNone(sonnet['context_tokens'])
            self.assertEqual(catalog,original)
            for model,provider_name in [('claude-sonnet-4-5','bedrock'),('claude-sonnet-4-6','aws-platform')]:
                r=mapped_request(host,model);r['host']['provider']=provider_name;refresh_controls(r)
                old=self.compile(catalog,r['host'])
                self.assertEqual(next(c for c in old['candidates'] if c['model']=='sonnet')['routing_profile']['work_types'],[])
            r=mapped_request(host);r['host']['model_resolutions']=[];refresh_controls(r)
            unknown=self.compile(catalog,r['host'])
            self.assertEqual(next(c for c in unknown['candidates'] if c['model']=='sonnet')['routing_profile']['work_types'],[])

    def test_pinned_profile_and_actual_effort_controls(self):
        r=mapped_request();catalog=self.catalog('claude-native')
        pinned=next(c for c in catalog['profiles'] if c['id']=='sonnet-5-5')
        catalog['profiles']=[pinned]
        self.assertEqual(self.compile(catalog,r['host'])['candidates'],[])
        r['host']['allowed_settings'].append(dict(model='claude-sonnet-5-5',effort=None));refresh_controls(r)
        self.assertEqual(self.compile(catalog,r['host'])['candidates'][0]['model'],'claude-sonnet-5-5')
        pinned['effort']='medium'
        r['host']['allowed_settings'].append(dict(model='claude-sonnet-5-5',effort='medium'));refresh_controls(r)
        self.assertEqual(self.compile(catalog,r['host'])['candidates'],[])
        r['host']['effort_selection']=True;refresh_controls(r)
        self.assertEqual(self.compile(catalog,r['host'])['candidates'][0]['effort'],'medium')

    def test_alias_and_pin_scopes_are_preserved(self):
        r=mapped_request();r['host']['allowed_settings'].append(dict(model='claude-sonnet-5-5',effort=None));refresh_controls(r)
        out=self.compile(self.catalog('claude-native'),r['host'])
        self.assertIn('sonnet-5-5',[c['id'] for c in out['candidates']]);self.assertIn('sonnet',[c['id'] for c in out['candidates']])

    def test_mapping_validation_unknowns_and_stale_controls(self):
        for mutation in ['duplicate','unsupported','false_unknown','missing_source']:
            r=mapped_request();mapping=r['host']['model_resolutions'][0]
            if mutation=='duplicate':r['host']['model_resolutions'].append(dict(mapping,resolved_model='other'))
            if mutation=='unsupported':mapping['requested_model']='not-allowed'
            if mutation=='false_unknown':mapping['source']='unknown'
            if mutation=='missing_source':mapping['reference']=None
            self.assertEqual(self.router.route(r)['reason'],'invalid_request',mutation)
        r=mapped_request();r['host']['model_resolutions'][0]['resolved_model']='claude-sonnet-5'
        self.assertEqual(self.router.route(r)['reason'],'control_review_required')
        r=mapped_request();r['host']['model_resolutions'][0].update(resolved_model=None,default_effort=None,source='unknown',reference=None)
        refresh_controls(r);self.router.validate_request(r)

    def test_mapping_receipts_remain_local_and_not_execution_proof(self):
        r=mapped_request();captured=[]
        def fake(payload,timeout):captured.append(json.dumps(payload));return provider()
        out=self.router.route(r,transport=fake,now=NOW)
        self.assertEqual(out['source'],'jev')
        self.assertEqual(out['receipt']['model_resolutions'],r['host']['model_resolutions'])
        self.assertEqual(out['receipt']['observed']['model'],'unknown')
        for text in ['claude-sonnet-5-5','sonnet','current-provider-model-mapping','model_resolutions']:
            self.assertNotIn(text,captured[0])

    def test_fable_resolution_cannot_bypass_existing_worker_exclusion(self):
        r=mapped_request(version='claude-fable-5-1')
        self.assertEqual(self.router.route(r)['reason'],'baseline_ineligible')
        self.assertIn('sonnet',self.compile(self.catalog('claude-native'),r['host'])['excluded'])

    def test_user_preferences_are_not_overwritten_and_codex_starter_stays_empty(self):
        r=mapped_request();catalog=self.catalog('claude-native')
        entry=next(c for c in catalog['profiles'] if c['id']=='sonnet')
        entry['routing_profile'].update(basis='user_preference',work_types=['review'])
        result=self.compile(catalog,r['host'])
        self.assertEqual(next(c for c in result['candidates'] if c['id']=='sonnet')['routing_profile']['work_types'],['review'])
        self.assertEqual(self.catalog('codex-skill')['profiles'],[])


    def test_feedback_rejects_a_receipt_from_another_mapping(self):
        feedback=runpy.run_path(str(ROOT/'plugin/portable/scripts/routing_feedback.py'))['feedback']
        r=mapped_request();decision=self.router.route(r,transport=lambda *a:provider(),now=NOW)
        outcome=dict(worker_id='w',status='completed',tests='passed',review='unknown',retries=0,evidence=['tests'],delivery='unknown')
        observation=dict(source='unknown',evidence=None,requested_resolved=dict(model=None,effort=None),observed=dict(model=None,effort=None),configuration_supported=None)
        self.assertFalse(feedback(r,decision,outcome,observation)['known_substitution'])
        r['host']['model_resolutions'][0]['resolved_model']='claude-sonnet-5'
        refresh_controls(r)
        with self.assertRaises(ValueError):feedback(r,decision,outcome,observation)
        decision['receipt'].pop('control_fingerprint')
        with self.assertRaises(ValueError):feedback(r,decision,outcome,observation)


class MappingApprovalTests(unittest.TestCase):
    setUp=config_tests.GlobalRoutingTests.setUp
    prepare=config_tests.GlobalRoutingTests.prepare
    client=config_tests.GlobalRoutingTests.client

    def approve_mapping(self):
        status=self.config.status(self.req['host'],now=NOW)
        return self.config.activate(self.req['host'],expected_policy_hash=status['policy_hash'],
            expected_host_fingerprint=status['host_fingerprint'],expected_source_key=status['source_key'],
            expected_revision=status['approval_revision'],confirm_scope=status['scope'],evidence_hashes=[],now=NOW)

    def test_version_default_effort_provider_and_mapping_loss_need_new_approval(self):
        self.req=mapped_request()
        self.config=self.module.RoutingConfig(self.project,'claude-native',home=self.home,environ={})
        self.prepare();self.approve_mapping()
        original=copy.deepcopy(self.req['host'])
        for mutation in ['version','default_effort','provider','lost']:
            host=copy.deepcopy(original)
            if mutation=='version':host['model_resolutions'][0]['resolved_model']='claude-sonnet-5'
            if mutation=='default_effort':host['model_resolutions'][0]['default_effort']='high'
            if mutation=='provider':host['provider']='another-provider'
            if mutation=='lost':host.pop('model_resolutions')
            host['control_basis']['fingerprint']=load_script().control_fingerprint(host)
            self.assertEqual(self.config.status(host,now=NOW)['reason'],'host_changed',mutation)
        other=self.module.RoutingConfig(self.other,'claude-native',home=self.home,environ={})
        self.assertEqual(other.status(original,now=NOW)['reason'],'ready')

    def test_mapping_order_does_not_change_reviewed_identity(self):
        self.req=mapped_request(host='claude-skill')
        self.config=self.module.RoutingConfig(self.project,'claude-skill',home=self.home,environ={})
        self.req['host']['model_resolutions'].append(dict(requested_model='opus',resolved_model=None,default_effort=None,source='unknown',reference=None))
        refresh_controls(self.req);self.prepare();self.approve_mapping()
        self.req['host']['model_resolutions'].reverse()
        self.req['host']['allowed_settings'].reverse()
        self.assertEqual(self.config.status(self.req['host'],now=NOW)['reason'],'ready')

if __name__=='__main__':unittest.main()
