"""Dynamic routing uses reviewed controls, never synthetic qualification."""
import copy
import unittest
from test_routing import activate, digest, load_script, NOW, provider
from test_routing_all_roles import request_for, ROLES
import test_routing_config as config_tests


def dynamic_request(role='docs-writer', host='codex-skill'):
    r=request_for(role,host)
    r['schema_version']=r['policy']['schema_version']=5
    p=r['policy'];p.update(mode='dynamic',routing_roles=p.pop('adaptive_roles'),
        catalog_revision='a'*64,outbound_contract='categories-v2',fallback_candidate='base',role_baselines=[],role_locks=[])
    for c in p['candidates']:
        c['qualification']=None;c['measurements']=[]
        c['facts_source']=dict(kind='host_metadata',reference='synthetic-controls')
        c['routing_profile']=dict(work_types=c['categories'],reasoning_depth='extended' if c['id']=='base' else 'routine',
            complexity=['high'] if c['id']=='base' else ['low'],risk=['high'] if c['id']=='base' else ['low'],
            efficiency='thorough' if c['id']=='base' else 'low_overhead',basis='user_preference',source='synthetic-review',revision='1')
    p['catalog_revision']=load_script().catalog_revision(p['candidates'])
    r['task'].update(reasoning_depth='routine',change_breadth='single',expected_output='documentation',verification='inspection')
    r['host'].update(attribution='unknown',evidence_level='unknown',evidence_hash=None)
    refresh_controls(r)
    r['activation']['evidence_hashes']=[]
    r['state']['router_identity']=None
    return activate(r)


def refresh_controls(r):
    r['host']['control_basis']=dict(source='callable_tool',fingerprint=load_script().control_fingerprint(r['host']))
    r['activation']['control_basis_hash']=digest(r['host']['control_basis'])
    return r


class DynamicTests(unittest.TestCase):
    def setUp(self):self.router=load_script()

    def test_all_roles_hosts_without_study_or_execution_evidence(self):
        for host in self.router.ROUTES:
            for role in ROLES:
                r=dynamic_request(role,host)
                out=self.router.route(r,transport=lambda *a:provider(),now=NOW)
                self.assertEqual(out['source'],'jev',(host,role,out))
                self.assertEqual(out['receipt']['assurance'],'unbenchmarked')
                self.assertEqual(out['dispatch']['model'],'synthetic-fast')

    def test_permission_controls_roles_and_fallback(self):
        for change,reason in [('approval','activation_required'),('control','control_review_required'),
                              ('role','role_not_enabled'),('fallback','baseline_ineligible'),
                              ('qualified','adaptive_unqualified')]:
            r=dynamic_request()
            if change=='approval':r['activation']['external_requests']=False
            if change=='control':r['host']['model_selection']=False
            if change=='role':r['policy']['routing_roles']=[]
            if change=='fallback':r['baseline']['model']='unsupported'
            if change=='qualified':r['policy']['mode']='adaptive'
            out=self.router.route(activate(r),transport=lambda *a:self.fail('unexpected request'),now=NOW)
            self.assertEqual(out['reason'],reason)
            self.assertEqual(out['state']['calls_used'],0)

    def test_overrides_remain_explicit_and_unsupported_effort_filtered(self):
        r=dynamic_request();r['selection']['role_candidate']='fast'
        self.assertEqual(self.router.route(r)['source'],'role_override')
        r['selection']['user_candidate']='base'
        self.assertEqual(self.router.route(r)['source'],'user_override')
        r['host']['effort_selection']=False;refresh_controls(r)
        self.assertEqual(self.router.route(r)['reason'],'invalid_override')

    def test_provider_failure_defer_budget_and_identity_drift(self):
        r=dynamic_request()
        for answer,reason in [(provider(choice='defer'),'defer'),(provider(confidence=.1),'low_confidence')]:
            out=self.router.route(r,transport=lambda *a:copy.deepcopy(answer),now=NOW)
            self.assertEqual(out['dispatch'],r['baseline']);self.assertEqual(out['reason'],reason)
        first=self.router.route(r,transport=lambda *a:provider(),now=NOW)
        r['state']=first['state'];answer=provider();answer['model']='changed-router'
        out=self.router.route(r,transport=lambda *a:answer,now=NOW)
        self.assertEqual(out['reason'],'router_changed');self.assertTrue(out['state']['adaptive_suspended'])
        r['state']=out['state']
        self.assertEqual(self.router.route(r)['reason'],'routing_suspended')
        r=dynamic_request();r['state']['calls_used']=r['policy']['max_calls']
        self.assertEqual(self.router.route(r)['reason'],'budget_exhausted')
        r['task']['risk']='invalid'
        self.assertEqual(self.router.route(r)['state']['calls_used'],r['policy']['max_calls'])


class DynamicApprovalTests(unittest.TestCase):
    setUp = config_tests.GlobalRoutingTests.setUp
    client = config_tests.GlobalRoutingTests.client
    prepare = config_tests.GlobalRoutingTests.prepare
    def test_dynamic_global_approval_without_capture_and_observation_changes(self):
        self.req=dynamic_request();self.prepare()
        status=self.config.status(self.req['host'],now=NOW)
        ready=self.config.activate(self.req['host'],expected_policy_hash=status['policy_hash'],
            expected_host_fingerprint=status['host_fingerprint'],expected_source_key=status['source_key'],
            expected_revision=status['approval_revision'],confirm_scope=status['scope'],evidence_hashes=[],now=NOW)
        self.assertEqual(ready['reason'],'ready')
        self.req['host']['evidence_level']='configuration_verified'
        self.req['host']['evidence_hash']='b'*64
        self.assertEqual(self.client(self.other).status(self.req['host'],now=NOW)['reason'],'ready')
        self.req['host']['configuration_revision']='changed'
        self.assertEqual(self.config.status(self.req['host'],now=NOW)['reason'],'host_changed')
        self.req['host']['configuration_revision']='synthetic-host-v1'
        changed=copy.deepcopy(self.req['policy']);changed['candidates'][0]['routing_profile']['revision']='changed'
        changed['catalog_revision']=load_script().catalog_revision(changed['candidates'])
        proposal=self.config.preview(changed,target='global')
        self.config.prepare(changed,target='global',expected_revision=proposal['expected_revision'])
        self.assertEqual(self.config.status(self.req['host'],now=NOW)['reason'],'policy_changed')

if __name__=='__main__':unittest.main()
