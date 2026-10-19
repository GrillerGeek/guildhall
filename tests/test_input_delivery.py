"""Offline bounded input delivery and recovery, without model calls."""
import copy
import runpy
import json
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent.parent
D=runpy.run_path(str(ROOT/'plugin/portable/scripts/input_delivery.py'))


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
                out=D['assess'](q);self.assertNotEqual(out['status'],'complete',change)
            p['observations'].append(copy.deepcopy(p['observations'][0]))
            with self.assertRaises(ValueError):D['assess'](p)

    def test_recover_only_missing_chunk_without_restarting_budget(self):
        p=packet();original=copy.deepcopy(p['observations'][0])
        p['observations'][0]['text']='short';p['observations'][0]['truncated']=True
        out=D['assess'](p);self.assertEqual(out['recoverable_chunks'],[original['chunk_id']])
        original['attempt']=1;p['observations'].append(original)
        out=D['assess'](p);self.assertEqual(out['status'],'complete');self.assertFalse(out['replay_worker'])
        p['observations'][-1]['elapsed_ms']=2000
        self.assertEqual(D['assess'](p)['status'],'budget_exceeded')

    def test_emit_is_bounded_and_hashing_source_alone_is_not_delivery(self):
        materials=[dict(id='ref',text='漢字'*3000)]
        manifest=D['plan'](materials,20,500)
        for c in manifest['chunks']:
            emitted=D['emit'](materials,c['id'])
            self.assertLessEqual(len(emitted['text'].encode()),2048)
        p=packet();p['observations']=[]
        self.assertNotEqual(D['assess'](p)['status'],'complete')


    def test_delivery_cli_works_from_independently_copied_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            installed=Path(tmp)/'skill';shutil.copytree(ROOT/'plugin/skills/guildhall-quest',installed)
            result=subprocess.run([sys.executable,'-I','-B',str(installed/'scripts/input_delivery.py')],
                input=json.dumps(dict(operation='assess',packet=packet())),text=True,capture_output=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'],'complete')



if __name__=='__main__':unittest.main()
