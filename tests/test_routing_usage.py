"""Usage accounting must never invent billing or add cumulative events twice."""
import copy
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parent.parent/'plugin/portable/scripts/routing_usage.py'


def packet(kind='response', includes=True):
    event=dict(worker_id='w', turn_id='t', attempt_id='a', response_id='r', sequence=0,
        kind=kind, meter='host', complete=True, input_tokens=100, output_tokens=20,
        cache_read_tokens=40, cache_write_tokens=10, reasoning_tokens=5,
        input_includes_cache=includes, evidence='synthetic:response')
    return dict(schema_version=1, scope=dict(host='codex-skill', role='docs-writer', category='docs'),
        inventory_complete=True, expected=[dict(worker_id='w',turn_id='t',attempt_id='a',meter='host',
        response_ids=['r'] if kind=='response' else None)], events=[event])


class UsageTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('usage',PATH)
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)

    def test_overlap_and_separate_cache(self):
        for includes, total in [(True,120),(False,170)]:
            result=self.module.normalize(packet(includes=includes))
            self.assertEqual(result['meters']['host']['usage_tokens'],total)
            self.assertIsNone(result['meters']['host']['cost_usd'])
            self.assertIsNone(result['meters']['router']['usage_tokens'])

    def test_duplicate_response_and_cumulative_updates(self):
        p=packet();p['events']*=2
        self.assertEqual(self.module.normalize(p)['meters']['host']['usage_tokens'],120)
        p=packet('cumulative');later=copy.deepcopy(p['events'][0]);later.update(sequence=1,input_tokens=150)
        p['events'].extend([later,later])
        self.assertEqual(self.module.normalize(p)['meters']['host']['usage_tokens'],170)

    def test_missing_and_partial_are_unknown(self):
        for field in ['events','inventory_complete','complete','input_tokens']:
            p=packet()
            if field=='events':p[field]=[]
            elif field=='inventory_complete':p[field]=False
            else:p['events'][0][field]=False if field=='complete' else None
            self.assertIsNone(self.module.normalize(p)['meters']['host']['usage_tokens'])

    def test_retries_count_router_is_separate(self):
        p=packet()
        for attempt,meter in [('retry','host'),('jev','router')]:
            expected=copy.deepcopy(p['expected'][0]);expected.update(attempt_id=attempt,meter=meter)
            e=copy.deepcopy(p['events'][0]);e.update(attempt_id=attempt,meter=meter)
            p['expected'].append(expected);p['events'].append(e)
        result=self.module.normalize(p)
        self.assertEqual(result['meters']['host']['usage_tokens'],240)
        self.assertEqual(result['meters']['router']['usage_tokens'],120)

    def test_conflicting_duplicate_and_counter_reset_rejected(self):
        for kind in ['response','cumulative']:
            p=packet(kind);other=copy.deepcopy(p['events'][0]);other['input_tokens']=1
            p['events'].append(other)
            with self.assertRaises(ValueError):self.module.normalize(p)
        p=packet('cumulative');other=copy.deepcopy(p['events'][0]);other.update(sequence=1,input_tokens=1)
        p['events'].append(other)
        with self.assertRaises(ValueError):self.module.normalize(p)

    def test_unexpected_response_or_attempt_rejected(self):
        for field in ['worker_id','turn_id','attempt_id','response_id']:
            p=packet();p['events'][0][field]='unexpected'
            with self.assertRaises(ValueError):self.module.normalize(p)

    def test_invalid_types_or_unknown_fields_rejected(self):
        for field,value in [('input_tokens',True),('input_tokens',-1),('input_tokens',float('inf')),('complete',1),('secret','bad')]:
            p=packet();p['events'][0][field]=value
            with self.assertRaises(ValueError):self.module.normalize(p)

    def test_scope_preserved_and_empty_inventory_incomplete(self):
        p=packet();p['expected']=[];p['events']=[]
        result=self.module.normalize(p)
        self.assertEqual(result['scope'],p['scope'])
        self.assertIsNone(result['meters']['host']['usage_tokens'])

if __name__=='__main__':unittest.main()
