"""Schema v2 prevents reuse of measurements outside their role/category scope."""
import copy
import unittest
from test_routing import activate, load_script, request


def scoped_request():
    r=request();r['schema_version']=2;r['policy']['schema_version']=2
    for c in r['policy']['candidates']:
        metrics={k:c[k] for k in ('quality','latency_ms','cost_usd','usage_tokens')}
        c['measurements']=[dict(role='docs-writer',category='docs',basis='synthetic-v1',**metrics)]
        for k in metrics:c[k]=None
    return activate(r)


class ScopedMetricsTests(unittest.TestCase):
    def test_v2_scope_used_and_not_leaked_to_other_role(self):
        router=load_script();r=scoped_request()
        router.validate_request(r)
        c=r['policy']['candidates'][0]
        self.assertEqual(router.metrics(c,r)['latency_ms'],100)
        r['task']['role']='pr-author'
        self.assertIsNone(router.metrics(c,r)['latency_ms'])

    def test_unknown_scoped_cost_cannot_satisfy_ceiling(self):
        router=load_script();r=scoped_request();r['policy']['max_cost_usd']=1
        r['policy']['candidates'][0]['measurements']=[]
        result=router.route(activate(r))
        self.assertNotIn('base',result['eligible_candidates'])

    def test_global_metrics_and_duplicate_scopes_rejected(self):
        router=load_script()
        for change in ['global','duplicate']:
            r=scoped_request();c=r['policy']['candidates'][0]
            if change=='global':c['usage_tokens']=20
            else:c['measurements'].append(copy.deepcopy(c['measurements'][0]))
            self.assertEqual(router.route(activate(r))['reason'],'invalid_request')

    def test_v1_unchanged_and_mixed_versions_rejected(self):
        router=load_script();router.validate_request(request())
        r=scoped_request();r['policy']['schema_version']=1
        self.assertEqual(router.route(r)['reason'],'invalid_request')

if __name__=='__main__':unittest.main()
