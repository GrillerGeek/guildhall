"""All-role routing contract; synthetic qualifications are test inputs only."""
import copy
import json
from pathlib import Path
import unittest
from test_routing import activate, digest, load_script, NOW, provider
from test_routing_scoped_metrics import scoped_request

ROLES='accessibility-reviewer architecture-reviewer debug-investigator docs-writer feature-implementer fog-cartographer migration-safety-reviewer observability-reviewer ops-readiness-reviewer performance-reviewer plugin-validator pr-author prototype-builder refactorer reliability-reviewer security-reviewer test-author ui-test-author'.split()


def request_for(role,host='codex-skill'):
    r=scoped_request();r['schema_version']=r['policy']['schema_version']=4
    r['policy'].update(mode='adaptive',required_evidence='execution_observed',adaptive_roles=[role])
    r['host'].update(route=host,evidence_level='execution_observed')
    r['task']['role']=role
    category={'docs-writer':'docs','pr-author':'pr','feature-implementer':'implementation','prototype-builder':'prototype',
              'debug-investigator':'debug','test-author':'tests','ui-test-author':'tests','refactorer':'refactor'}.get(role,'review')
    r['task']['category']=category
    for c in r['policy']['candidates']:
        c.update(host=host,roles=[role],categories=[category])
        c['measurements'][0].update(role=role,category=category)
        c['qualification']=dict(report_hash='2'*64,profile_hash=digest({k:v for k,v in c.items() if k!='qualification'}),
            expires_at=NOW+3600,host_revision=r['host']['configuration_revision'],router_request=r['policy']['router_model'],
            router_identity='synthetic-jev-version-1',roles=[role],categories=[category],evidence_level='execution_observed',
            observed_model='synthetic-concrete',observed_effort='high',objective='latency')
    return activate(r)


class AllRolesTests(unittest.TestCase):
    def setUp(self):self.router=load_script()

    def test_role_inventory_matches_native_specialists_and_fixture_seeds(self):
        root=Path(__file__).resolve().parent.parent
        native={p.stem for p in (root/'plugin/agents').glob('*.md')}
        self.assertEqual(set(ROLES),native-{'model-echo'})
        self.assertEqual(set(self.router.ROLES),set(ROLES))
        packet=json.loads((root/'plugin/portable/resources/examples/role-study-fixtures.json').read_text())
        self.assertTrue(packet['synthetic']);self.assertFalse(packet['qualification'])
        self.assertEqual({s['id'] for s in packet['seeds']},{'authoring','implementation','review','diagnostics','operations'})
        for seed in packet['seeds']:
            self.assertIn(seed['role'],ROLES)
            self.assertTrue(seed['rubric'])
            if seed['id'] in ('review','diagnostics','operations'):
                self.assertEqual(seed['allowed_files'],[])
                self.assertIn('stdout',seed['prompt'])
            else:self.assertTrue(seed['allowed_files'])

    def test_all_roles_and_hosts_change_only_supported_settings(self):
        for role in ROLES:
            for host in ['claude-native','claude-skill','codex-skill']:
                with self.subTest(role=role,host=host):
                    r=request_for(role,host);before=copy.deepcopy(r)
                    result=self.router.route(r,transport=lambda *args:provider(),now=NOW)
                    self.assertEqual(result['source'],'jev')
                    self.assertEqual(result['dispatch'],dict(model='synthetic-fast',effort='high'))
                    self.assertEqual(r,before)
                    self.assertEqual(result['receipt']['host_snapshot']['evidence_level'],'execution_observed')

    def test_every_role_has_explicit_overrides_and_conservative_fallback(self):
        for role in ROLES:
            with self.subTest(role=role):
                for selection in ['user_candidate','role_candidate']:
                    r=request_for(role)
                    for c in r['policy']['candidates']:c['qualification']=None
                    r['selection'][selection]='fast'
                    result=self.router.route(activate(r),now=NOW)
                    self.assertEqual(result['dispatch']['model'],'synthetic-fast')
                for missing in ['qualification','allowlist','evidence','controls','scope']:
                    r=request_for(role)
                    if missing=='qualification':
                        for c in r['policy']['candidates']:c['qualification']=None
                    if missing=='allowlist':r['policy']['adaptive_roles']=[]
                    if missing=='evidence':r['host']['evidence_level']='unknown'
                    if missing=='controls':r['host']['model_selection']=False
                    if missing=='scope':
                        for c in r['policy']['candidates']:c['qualification']['categories']=['pr' if r['task']['category']!='pr' else 'docs']
                    result=self.router.route(activate(r),now=NOW)
                    self.assertEqual(result['reason'],'adaptive_unqualified')
                    self.assertEqual(result['dispatch'],r['baseline'])
                    self.assertEqual(result['state']['calls_used'],0)

    def test_diagnostic_parent_external_and_unknown_roles_rejected(self):
        for role in ['model-echo','mordain','idd-implementer','unknown']:
            r=request_for('docs-writer');r['task']['role']=role
            self.assertEqual(self.router.route(r)['reason'],'invalid_request')
            r=request_for('docs-writer');r['policy']['adaptive_roles']=[role]
            self.assertEqual(self.router.route(activate(r))['reason'],'invalid_request')

    def test_legacy_schemas_keep_role_limit_and_v4_still_needs_activation(self):
        r=request_for('test-author')
        r['schema_version']=r['policy']['schema_version']=3
        self.assertEqual(self.router.route(activate(r))['reason'],'invalid_request')
        r=request_for('test-author');r['activation']['policy_hash']='0'*64
        self.assertEqual(self.router.route(r)['reason'],'activation_required')
        r=request_for('docs-writer');r['schema_version']=r['policy']['schema_version']=3
        self.router.validate_request(activate(r))
        r['schema_version']=r['policy']['schema_version']=4
        self.assertEqual(self.router.route(r)['reason'],'activation_required')

if __name__=='__main__':unittest.main()
