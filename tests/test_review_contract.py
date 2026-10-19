"""Public review CLI contract from the approved issue-64 requirements.

No production imports or implementation inspection. All durable inputs are synthetic.
Instruction-only and live-host acceptance coverage is recorded in the handoff.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / 'plugin/portable/scripts/review.py'
PLAN = 'docs/guildhall/plans/2026-10-18-fixture.md'
AUTHORITY = {'display_label': 'Fixture owner', 'source': 'fixture initiating-user designation'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ReviewFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='guildhall review contract ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        self.root.mkdir()
        self.plan = self.root / PLAN
        self.plan.parent.mkdir(parents=True)
        self.plan.write_text('# Canonical plan\nKeep this plan unchanged.\n')
        self.plan_bytes = self.plan.read_bytes()
        self.bundle = self.plan.with_suffix('')
        self.review = self.bundle / 'review.md'
        self.manifest = self.bundle / 'review-state.json'
        self.host = 'document'
        self.env = {key: os.environ[key] for key in ('PATH','HOME','LANG','TMPDIR') if key in os.environ}
        self.env.update(XDG_CONFIG_HOME=str(Path(self.temp.name) / 'empty-config'),
                        PI_CODING_AGENT_DIR=str(Path(self.temp.name) / 'pi-config'),
                        PYTHONDONTWRITEBYTECODE='1')

    def command(self, operation, plan=PLAN, root=None):
        self.assertTrue(SCRIPT.is_file(), 'promised public review.py entry point is missing (attributable RED)')
        return [sys.executable, str(SCRIPT), operation, '--root', str(root or self.root),
                '--plan', plan, '--host', self.host, '--input-json', '-']

    def invoke(self, operation, payload, code=0, plan=PLAN, root=None, raw=False):
        process = subprocess.run(self.command(operation, plan, root),
                                 input=payload if raw else json.dumps(payload),
                                 text=True, capture_output=True, env=self.env, timeout=8)
        self.assertEqual(process.returncode, code, process.stderr + process.stdout)
        try:
            reply = json.loads(process.stdout)
        except ValueError:
            self.fail('finite operation must emit exactly one JSON object: ' + repr(process.stdout[:500]))
        self.assertEqual(set(reply), {'schema_version', 'operation', 'ok', 'result', 'error'})
        self.assertEqual(reply['schema_version'], 1)
        self.assertEqual(reply['operation'], operation)
        self.assertEqual(reply['ok'], code == 0)
        if code:
            self.assertIsNone(reply['result'])
            self.assertEqual(set(reply['error']), {'code', 'message', 'details'})
            self.assertIsInstance(reply['error']['details'], dict)
        else:
            self.assertIsNone(reply['error'])
            self.assertIsInstance(reply['result'], dict)
        self.assertEqual(self.plan.read_bytes(), self.plan_bytes, 'helper may never mutate PLAN')
        return reply['result'] if code == 0 else reply['error']

    def init(self, content='First line\nSecond line\nThird line\n', surface=None):
        return self.invoke('init', {'quest_id': 'fixture-quest', 'content': content,
                          'authority': AUTHORITY,
                          'surface': surface or {'kind': 'document', 'id': None, 'url': None}})

    def inspect(self, observation=None):
        return self.invoke('inspect', {} if observation is None else {'observation': observation})

    def guards(self):
        current = self.inspect()
        return {'expected_state_hash': current['state_sha256'],
                'expected_review_hash': current['review_sha256']}

    def prepare(self, **extra):
        return self.invoke('checkpoint', dict(phase='prepare', **self.guards(), **extra))

    def baseline(self):
        pending = self.prepare()
        self.invoke('checkpoint', dict(phase='complete', checkpoint_id=pending['checkpoint_id'], **self.guards()))
        self.assertEqual(self.inspect()['state'], 'clean')

    def tree(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}


class ReviewContractTests(ReviewFixture, unittest.TestCase):
    def test_delivery_counts_without_runtime_are_unavailable_not_zero(self):
        self.init()
        before=self.tree()
        result=self.invoke('inspect',{})
        self.assertIsNone(result['pending_delivery_counts'])
        self.assertEqual(result['delivery_coverage'],'unavailable')
        self.assertEqual(self.tree(),before)

    def test_explicit_missing_runtime_or_journal_is_unavailable_without_creation(self):
        self.init()
        missing=Path(self.temp.name)/'missing-runtime'
        before=self.tree()
        self.invoke('inspect',{'runtime_dir':str(missing)},code=4)
        self.assertFalse(missing.exists())
        self.assertEqual(self.tree(),before)
        empty=Path(self.temp.name)/'empty-runtime'
        empty.mkdir()
        self.invoke('inspect',{'runtime_dir':str(empty)},code=4)
        self.assertEqual(list(empty.iterdir()),[])
        self.assertEqual(self.tree(),before)

    def test_init_record_and_exact_hashes_without_implicit_sync(self):
        content = '\ufeffA\r\nB\rC\n \u00e9 e\u0301\n'
        result = self.init(content)
        record = json.loads(self.manifest.read_bytes())
        self.assertTrue({'schema_version', 'quest_id', 'plan_path', 'review_path',
                         'html_path', 'surface', 'authority', 'checkpoint', 'feedback', 'decisions'} <= set(record))
        self.assertEqual(record['schema_version'], 1)
        self.assertEqual(record['quest_id'], 'fixture-quest')
        self.assertEqual(record['plan_path'], PLAN)
        self.assertEqual(record['review_path'], str(self.review.relative_to(self.root)))
        self.assertEqual(record['html_path'], str((self.bundle/'review.html').relative_to(self.root)))
        self.assertEqual(record['surface'], {'kind': 'document', 'id': None, 'url': None})
        self.assertEqual(record['authority'], AUTHORITY)
        self.assertIsNone(record['checkpoint']['common'])
        self.assertIsNone(record['checkpoint']['pending'])
        self.assertEqual(self.review.read_bytes(), content.encode())
        status = self.inspect()
        self.assertEqual(status['review_sha256'], sha(content.encode()))
        self.assertEqual(status['state_sha256'], sha(self.manifest.read_bytes()))
        self.assertEqual(status['state'], 'local-changed')
        self.assertTrue(status['checkpoint_needed'])
        self.assertIn('bundle_path', result)
        self.assertIn('created_paths', result)
        self.assertIn('hashes', result)
        self.assertNotIn(str(self.root), self.manifest.read_text())

    def test_identical_init_is_idempotent_conflicting_init_is_non_destructive(self):
        self.init()
        before = self.tree()
        again = self.init()
        self.assertEqual(again['created_paths'], [])
        self.assertEqual(self.tree(), before)
        self.invoke('init', {'quest_id': 'fixture-quest', 'content': 'conflicting',
                    'authority': AUTHORITY, 'surface': {'kind':'document','id':None,'url':None}}, code=3)
        self.assertEqual(self.tree(), before)

    def test_inspection_is_read_only_and_does_not_clear_pending(self):
        self.init()
        self.prepare()
        before = self.tree()
        first = self.inspect()
        self.assertIsNotNone(json.loads(self.manifest.read_bytes())['checkpoint']['pending'])
        self.assertEqual(first, self.inspect())
        self.assertEqual(self.tree(), before)

    def test_local_two_phase_checkpoint_and_single_common_snapshot(self):
        self.init()
        self.baseline()
        old = json.loads(self.manifest.read_bytes())['checkpoint']['common']
        self.review.write_text('A new owner draft\n')
        self.assertEqual(self.inspect()['state'], 'local-changed')
        self.prepare()
        self.assertEqual(json.loads(self.manifest.read_bytes())['checkpoint']['common'], old)

    def test_normalization_only_bom_and_line_endings(self):
        self.init('\ufeffAlpha\r\nBeta\rGamma\n')
        self.baseline()
        self.review.write_bytes(b'Alpha\nBeta\nGamma\n')
        self.assertEqual(self.inspect()['state'], 'clean')
        for content in ('Alpha\nBeta\nGamma', 'Alpha\nBeta\nGamma\n ', 'alpha\nBeta\nGamma\n'):
            with self.subTest(content=content):
                self.review.write_text(content)
                self.assertEqual(self.inspect()['state'], 'local-changed')

    def test_unknown_fields_and_malformed_json_do_not_mutate(self):
        self.init()
        before = self.tree()
        for operation, payload in [('inspect', {'surprise':True}), ('export', {'expected_review_hash':sha(self.review.read_bytes()), 'surprise':True})]:
            with self.subTest(operation=operation):
                self.invoke(operation, payload, code=2)
                self.assertEqual(self.tree(), before)
        self.invoke('inspect', '{"observation":', code=2, raw=True)
        self.assertEqual(self.tree(), before)

    def test_stale_state_and_review_guards_refuse(self):
        self.init()
        guards = self.guards()
        self.review.write_text('User edit\n')
        before = self.tree()
        self.invoke('checkpoint', dict(phase='prepare', **guards), code=3)
        self.assertEqual(self.tree(), before)
        guards = self.guards()
        record = json.loads(self.manifest.read_bytes())
        record['authority']['source'] = 'new owner designation'
        self.manifest.write_text(json.dumps(record))
        before = self.tree()
        self.invoke('checkpoint', dict(phase='prepare', **guards), code=3)
        self.assertEqual(self.tree(), before)

    def test_missing_plan_and_outside_plan_are_refused_before_mutation(self):
        before = self.tree()
        self.invoke('init', {'quest_id':'q','content':'draft','authority':AUTHORITY,
                     'surface':{'kind':'document','id':None,'url':None}}, code=3,
                    plan='docs/guildhall/plans/missing.md')
        self.assertEqual(self.tree(), before)
        self.invoke('inspect', {}, code=3, plan='../outside.md')
        self.assertEqual(self.tree(), before)

    def test_unexpected_files_preserved_before_initialization(self):
        self.bundle.mkdir()
        (self.bundle/'personal.txt').write_text('user content')
        before = self.tree()
        self.invoke('init', {'quest_id':'q','content':'draft','authority':AUTHORITY,
                    'surface':{'kind':'document','id':None,'url':None}}, code=3)
        self.assertEqual(self.tree(), before)

    def test_symlink_review_and_bundle_parent_are_refused(self):
        self.init()
        outside = Path(self.temp.name)/'outside.md'
        outside.write_text('protected')
        self.review.unlink()
        self.review.symlink_to(outside)
        self.invoke('export', {'expected_review_hash':sha(b'protected')}, code=3)
        self.assertEqual(outside.read_text(), 'protected')
        self.review.unlink()
        self.bundle.rename(self.bundle.with_name('saved'))
        self.bundle.symlink_to(self.bundle.with_name('saved'), target_is_directory=True)
        self.invoke('inspect', {}, code=3)

    def test_export_guard_and_offline_output(self):
        self.init('Review <script>alert("draft")</script>\nOptions and tradeoffs\n')
        before = self.tree()
        self.invoke('export', {'expected_review_hash':'0'*64}, code=3)
        self.assertEqual(self.tree(), before)
        result = self.invoke('export', {'expected_review_hash':sha(self.review.read_bytes())})
        html = self.bundle/'review.html'
        self.assertEqual(result['source_sha256'], sha(self.review.read_bytes()))
        self.assertEqual(result['output_sha256'], sha(html.read_bytes()))
        self.assertEqual(result['output_path'], str(html.relative_to(self.root)))
        self.assertIsInstance(result['disabled_capabilities'], list)
        self.assertNotIn('<script>alert("draft")</script>', html.read_text())
        self.assertEqual(self.review.read_bytes(), before[str(self.review.relative_to(self.root))])
        self.assertEqual(self.manifest.read_bytes(), before[str(self.manifest.relative_to(self.root))])

    def test_document_limit_exact_utf8_bytes_and_rejection_preserves_files(self):
        self.init('a'*(256*1024))
        self.assertEqual(len(self.review.read_bytes()), 256*1024)
        before = self.tree()
        self.invoke('init', {'quest_id':'fixture-quest','content':'\u00e9'*(128*1024+1),
                    'authority':AUTHORITY,'surface':{'kind':'document','id':None,'url':None}}, code=2)
        self.assertEqual(self.tree(), before)

    def test_export_symlink_and_user_snapshot_are_never_overwritten_or_removed(self):
        self.init()
        outside=Path(self.temp.name)/'protected.html'
        outside.write_text('Protected user HTML')
        html=self.bundle/'review.html'
        html.unlink()
        html.symlink_to(outside)
        self.invoke('export',{'expected_review_hash':sha(self.review.read_bytes())},code=3)
        self.assertEqual(outside.read_text(),'Protected user HTML')
        html.unlink()
        # Restore only via the public operation before adding a user-owned snapshot.
        self.invoke('export',{'expected_review_hash':sha(self.review.read_bytes())})
        snapshots=self.bundle/'snapshots'
        snapshots.mkdir(exist_ok=True)
        (snapshots/'personal.md').write_text('User-created snapshot')
        before=self.tree()
        self.invoke('checkpoint',dict(phase='prepare',**self.guards()),code=3)
        self.assertEqual(self.tree(),before)

    def test_hosted_unavailable_is_not_local_mode(self):
        self.host = 'codex-space'
        self.init(surface={'kind':'codex-space','id':'fixture-page','url':'https://example.invalid/review'})
        status = self.inspect()
        self.assertEqual(status['state'], 'unavailable')
        self.assertIsNone(json.loads(self.manifest.read_bytes())['checkpoint']['common'])

    def test_observation_identity_partial_feedback_and_unknown_revision(self):
        self.host = 'codex-space'
        self.init(surface={'kind':'codex-space','id':'fixture-page','url':'https://example.invalid/review'})
        observation = {'surface_id':'fixture-page','text':self.review.read_text(),'revision':None,
                       'source_ref':'fixture export','feedback_complete':False,'feedback':[]}
        before = self.tree()
        status = self.inspect(observation)
        self.assertFalse(status['completeness']['feedback'])
        self.assertEqual(status['hosted_revision'], None)
        self.assertEqual(self.tree(), before)
        observation['surface_id'] = 'other-page'
        self.invoke('inspect', {'observation':observation}, code=3)
        self.assertEqual(self.tree(), before)

    def test_missing_feedback_completeness_is_not_assumed(self):
        self.host = 'codex-space'
        self.init(surface={'kind':'codex-space','id':'fixture-page','url':'https://example.invalid/review'})
        observation = {'surface_id':'fixture-page','text':self.review.read_text(),'revision':None,
                       'source_ref':'fixture export'}
        # An absent feedback listing may be accepted or rejected, but never certified complete.
        process = subprocess.run(self.command('inspect'), input=json.dumps({'observation':observation}),
                                 text=True,capture_output=True,env=self.env,timeout=8)
        self.assertIn(process.returncode, (0,2))
        reply=json.loads(process.stdout)
        if reply['ok']:
            self.assertFalse(reply['result']['completeness']['feedback'])

    def test_hostile_json_and_document_paths_three_sizes_are_bounded(self):
        self.init()
        for size in (1024, 10*1024, 100*1024):
            with self.subTest(size=size):
                # Valid JSON envelope reaches content/idempotency validation with a changed final line.
                content = ('a' * size) + '\n'
                started = time.monotonic()
                self.invoke('init', {'quest_id':'fixture-quest','content':content,'authority':AUTHORITY,
                          'surface':{'kind':'document','id':None,'url':None}}, code=3)
                self.assertLess(time.monotonic()-started, 5)
                # Valid leading JSON string; parser must scan it and discover the missing terminator.
                started = time.monotonic()
                self.invoke('inspect', '{"observation":"' + 'a'*size + '\\', code=2, raw=True)
                self.assertLess(time.monotonic()-started, 5)


class ReviewReconciliationTests(ReviewFixture, unittest.TestCase):
    def observation(self, text, feedback=None, revision=None):
        return {'surface_id':'fixture-page','text':text,'revision':revision,
                'source_ref':'fixture exported Page','feedback_complete':True,
                'feedback':feedback or []}

    def hosted_baseline(self, text='A\nB\nC\nD\n'):
        self.host='codex-space'
        self.init(text, {'kind':'codex-space','id':'fixture-page','url':'https://example.invalid/review'})
        observation=self.observation(text)
        prepared=self.prepare(observation=observation)
        self.assertEqual(prepared['merged_content'],text)
        self.finish(prepared, observation)
        self.assertEqual(self.inspect(observation)['state'],'clean')

    def finish(self, prepared, observation):
        if 'local' in prepared['required_saves']:
            self.review.write_bytes(prepared['merged_content'].encode())
        receipt={'surface_id':'fixture-page','revision':observation['revision'],
                 'content_sha256':sha(prepared['merged_content'].encode()),
                 'source_ref':'fixture saved Page receipt'}
        return self.invoke('checkpoint',dict(phase='complete',checkpoint_id=prepared['checkpoint_id'],
                           observation=self.observation(prepared['merged_content'], observation['feedback'], observation['revision']),
                           receipt=receipt,**self.guards()))

    def test_state_changes_follow_both_observed_representations(self):
        baseline='A\nB\nC\nD\n'
        self.hosted_baseline(baseline)
        self.assertEqual(self.inspect(self.observation('A\nB!\nC\nD\n'))['state'],'hosted-changed')
        self.review.write_text('A!\nB\nC\nD\n')
        self.assertEqual(self.inspect(self.observation(baseline))['state'],'local-changed')
        self.assertEqual(self.inspect(self.observation('A\nB!\nC\nD\n'))['state'],'both-changed')

    def test_disjoint_and_identical_line_edits_merge_once(self):
        cases=[('A!\nB\nC\nD\n','A\nB\nC!\nD\n','A!\nB\nC!\nD\n'),
               ('A!\nB\nC\nD\n','A\nB!\nC\nD\n','A!\nB!\nC\nD\n'),
               ('A\nB!\nC\nD\n','A\nB!\nC\nD\n','A\nB!\nC\nD\n')]
        for local,hosted,expected in cases:
            with self.subTest(local=local,hosted=hosted):
                if self.bundle.exists():
                    import shutil
                    shutil.rmtree(self.bundle)
                self.hosted_baseline()
                old=json.loads(self.manifest.read_bytes())['checkpoint']['common']
                self.review.write_text(local)
                prepared=self.prepare(observation=self.observation(hosted))
                self.assertEqual(prepared['merged_content'],expected)
                self.assertEqual(prepared['merged_sha256'],sha(expected.encode()))
                self.assertEqual(prepared['conflicts'],[])
                self.assertEqual(json.loads(self.manifest.read_bytes())['checkpoint']['common'],old)
                self.finish(prepared,self.observation(hosted))
                self.assertEqual(self.inspect(self.observation(expected))['state'],'clean')

    def test_overlaps_insertions_and_range_boundaries_conflict_without_winner(self):
        self.hosted_baseline()
        for local,hosted in [('A\nlocal\nC\nD\n','A\nhosted\nC\nD\n'),
                             ('A\nX\nB\nC\nD\n','A\nY\nB\nC\nD\n'),
                             ('A\nC\nD\n','A\nB!\nC\nD\n'),
                             ('A\nX\nB\nC\nD\n','A\nB!\nC\nD\n')]:
            with self.subTest(local=local,hosted=hosted):
                self.review.write_text(local)
                before=self.tree()
                result=self.prepare(observation=self.observation(hosted))
                self.assertEqual(result['state'],'conflict')
                self.assertIsNone(result['merged_content'])
                self.assertIsNone(result['merged_sha256'])
                self.assertEqual(result['required_saves'],[])
                conflict=next(c for c in result['conflicts'] if c['kind']=='prose')
                self.assertEqual(conflict['baseline'],'A\nB\nC\nD\n')
                self.assertEqual(conflict['local'],local)
                self.assertEqual(conflict['hosted'],hosted)
                self.assertEqual(self.tree(),before)

    def test_owner_conflict_resolution_is_explicit_and_guarded(self):
        self.hosted_baseline()
        self.review.write_text('Local version\n')
        observed=self.observation('Hosted version\n')
        self.assertEqual(self.prepare(observation=observed)['state'],'conflict')
        result=self.prepare(observation=observed,resolution={'content':'Owner resolution\n',
                            'source_ref':'fixture owner resolution decision','authority_label':'Fixture owner'})
        self.assertEqual(result['merged_content'],'Owner resolution\n')
        self.assertEqual(self.plan.read_bytes(),self.plan_bytes)

    def test_partial_save_missing_bad_receipt_and_replay_never_advance_common(self):
        self.hosted_baseline()
        common=json.loads(self.manifest.read_bytes())['checkpoint']['common']
        self.review.write_text('A!\nB\nC\nD\n')
        prepared=self.prepare(observation=self.observation('A\nB\nC!\nD\n'))
        if 'local' in prepared['required_saves']:
            self.review.write_text(prepared['merged_content'])
        # No hosted receipt is not evidence the hosted side saved.
        self.invoke('checkpoint',dict(phase='complete',checkpoint_id=prepared['checkpoint_id'],**self.guards()),code=2)
        self.assertEqual(json.loads(self.manifest.read_bytes())['checkpoint']['common'],common)
        self.assertIsNotNone(json.loads(self.manifest.read_bytes())['checkpoint']['pending'])
        receipt={'surface_id':'other-page','revision':None,'content_sha256':prepared['merged_sha256'],
                 'source_ref':'fixture receipt'}
        self.invoke('checkpoint',dict(phase='complete',checkpoint_id=prepared['checkpoint_id'],receipt=receipt,**self.guards()),code=3)
        self.assertEqual(json.loads(self.manifest.read_bytes())['checkpoint']['common'],common)
        self.finish(prepared,self.observation(prepared['merged_content']))
        completed=self.tree()
        # A fresh process cannot replay an already observed save.
        self.invoke('checkpoint',dict(phase='complete',checkpoint_id=prepared['checkpoint_id'],receipt=receipt,**self.guards()),code=3)
        self.assertEqual(self.tree(),completed)

    def test_unknown_revision_detached_selection_and_proposals_retain_provenance(self):
        self.hosted_baseline()
        entry={'id':'comment-1','source_ref':'fixture Page comment 1','source_revision':None,'author':None,
               'selection':{'status':'detached','text':None},'text':'Consider the alternative',
               'disposition':'proposed','rationale':'Selection no longer exists'}
        observed=self.observation(self.review.read_text(),[entry])
        prepared=self.prepare(observation=observed)
        self.finish(prepared,observed)
        record=json.loads(self.manifest.read_bytes())
        self.assertEqual(record['feedback'],[entry])
        self.assertEqual(record['decisions'],[])
        self.assertIsNone(record['checkpoint']['common']['hosted_revision'])
        self.assertTrue(record['checkpoint']['common']['source_ref'])
        self.assertEqual(self.plan.read_bytes(),self.plan_bytes)

    def test_feedback_limit_and_accepted_without_source_are_rejected(self):
        self.hosted_baseline()
        entry={'id':'comment','source_ref':'fixture comment','source_revision':None,'author':None,
               'selection':None,'text':'Suggestion','disposition':'proposed','rationale':'For review'}
        entries=[dict(entry,id=str(n)) for n in range(201)]
        before=self.tree()
        self.invoke('checkpoint',dict(phase='prepare',observation=self.observation(self.review.read_text(),entries),**self.guards()),code=2)
        self.assertEqual(self.tree(),before)
        decision={'id':'decision-1','text':'Accept alternative','disposition':'accepted',
                  'source_ref':'','authority_label':'Fixture owner','rationale':'Owner decision'}
        self.invoke('checkpoint',dict(phase='prepare',observation=self.observation(self.review.read_text()),decisions=[decision],**self.guards()),code=2)
        self.assertEqual(self.tree(),before)

    def test_hosted_save_before_local_failure_preserves_pending_and_common(self):
        self.hosted_baseline()
        common=json.loads(self.manifest.read_bytes())['checkpoint']['common']
        prepared=self.prepare(observation=self.observation('A!\nB\nC\nD\n'))
        # Hosted save succeeds while the local writer has not saved the merge.
        receipt={'surface_id':'fixture-page','revision':None,'content_sha256':prepared['merged_sha256'],
                 'source_ref':'fixture observed hosted save'}
        self.invoke('checkpoint',dict(phase='complete',checkpoint_id=prepared['checkpoint_id'],receipt=receipt,
                    observation=self.observation(prepared['merged_content']),**self.guards()),code=3)
        record=json.loads(self.manifest.read_bytes())
        self.assertEqual(record['checkpoint']['common'],common)
        self.assertIsNotNone(record['checkpoint']['pending'])
        self.assertEqual(self.plan.read_bytes(),self.plan_bytes)

    def test_maximum_feedback_entries_are_retained_without_truncation(self):
        self.hosted_baseline()
        entries=[{'id':str(n),'source_ref':'fixture comment '+str(n),'source_revision':None,
                  'author':None,'selection':None,'text':'Suggestion '+str(n),
                  'disposition':'proposed','rationale':'Await owner'} for n in range(200)]
        observed=self.observation(self.review.read_text(),entries)
        prepared=self.prepare(observation=observed)
        self.finish(prepared,observed)
        self.assertEqual(json.loads(self.manifest.read_bytes())['feedback'],entries)

    def test_decision_ids_append_independently_and_differing_same_id_conflicts(self):
        self.init()
        self.baseline()
        def decision(identifier,text):
            return {'id':identifier,'text':text,'disposition':'accepted','source_ref':'fixture owner decision '+identifier,
                    'authority_label':'Fixture owner','rationale':'Explicit authorized handoff'}
        first=decision('d1','Choose first')
        pending=self.prepare(decisions=[first])
        self.invoke('checkpoint',dict(phase='complete',checkpoint_id=pending['checkpoint_id'],**self.guards()))
        second=decision('d2','Choose second')
        pending=self.prepare(decisions=[second])
        self.invoke('checkpoint',dict(phase='complete',checkpoint_id=pending['checkpoint_id'],**self.guards()))
        self.assertEqual(json.loads(self.manifest.read_bytes())['decisions'],[first,second])
        before=self.tree()
        result=self.prepare(decisions=[decision('d1','Different first')])
        self.assertEqual(result['state'],'conflict')
        self.assertTrue(any(c['kind']=='decision' for c in result['conflicts']))
        self.assertEqual(self.tree(),before)


class ReviewPackagingTests(ReviewFixture, unittest.TestCase):
    def checkout_fixture(self):
        self.command('inspect')  # Missing promised resource is attributable RED before packaging setup.
        import shutil
        checkout=Path(self.temp.name)/'checkout'
        checkout.mkdir()
        for name in ('plugin','scripts','.agents','.claude-plugin'):
            shutil.copytree(ROOT/name,checkout/name)
        shutil.copy2(ROOT/'LICENSE',checkout/'LICENSE')
        return checkout

    def run_packaging(self, checkout, script, *args):
        process=subprocess.run([sys.executable,str(checkout/script),*args],cwd=checkout,
                               capture_output=True,text=True,env=self.env,timeout=30)
        self.assertEqual(process.returncode,0,process.stderr+process.stdout)

    def test_build_validators_and_routing_resource_separation(self):
        checkout=self.checkout_fixture()
        self.run_packaging(checkout,'scripts/build_portable.py')
        self.run_packaging(checkout,'scripts/build_portable.py','--check')
        self.run_packaging(checkout,'scripts/validate_plugin.py')
        self.run_packaging(checkout,'scripts/validate_portable.py')
        quest=checkout/'plugin/skills/guildhall-quest'
        routing=checkout/'plugin/skills/guildhall-routing-setup'
        self.assertTrue((quest/'scripts/review.py').is_file())
        self.assertTrue((quest/'references/collaborative-planning.md').is_file())
        self.assertTrue((quest/'resources/review').is_dir())
        self.assertTrue(any((quest/'resources/review').iterdir()))
        self.assertFalse((routing/'scripts/review.py').exists())
        self.assertFalse((routing/'resources/review').exists())
        self.assertFalse((routing/'references/collaborative-planning.md').exists())

    def test_native_artifact_is_known_and_unknown_tool_still_warns(self):
        import shutil
        checkout=self.checkout_fixture()
        fixtures=ROOT/'tests/fixtures/review'
        agents=checkout/'plugin/agents'
        shutil.copy2(fixtures/'artifact-agent.md',agents/'artifact-fixture.md')
        known=subprocess.run([sys.executable,str(checkout/'scripts/validate_plugin.py')],cwd=checkout,
                             text=True,capture_output=True,env=self.env,timeout=15)
        self.assertEqual(known.returncode,0,known.stdout+known.stderr)
        known_warnings=[line for line in (known.stdout+known.stderr).splitlines()
                        if 'warn' in line.lower() and 'Artifact' in line]
        self.assertEqual(known_warnings,[])
        shutil.copy2(fixtures/'unknown-tool-agent.md',agents/'unknown-tool-fixture.md')
        unknown=subprocess.run([sys.executable,str(checkout/'scripts/validate_plugin.py')],cwd=checkout,
                               text=True,capture_output=True,env=self.env,timeout=15)
        self.assertEqual(unknown.returncode,0,unknown.stdout+unknown.stderr)
        self.assertTrue(any('UnrecognizedFixtureTool' in line and 'warn' in line.lower()
                            for line in (unknown.stdout+unknown.stderr).splitlines()))

    def test_copied_bundle_init_and_export_without_authoring_source(self):
        import shutil
        checkout=self.checkout_fixture()
        self.run_packaging(checkout,'scripts/build_portable.py')
        installed=Path(self.temp.name)/'installed-quest'
        shutil.copytree(checkout/'plugin/skills/guildhall-quest',installed)
        shutil.rmtree(checkout)
        script=installed/'scripts/review.py'
        self.assertTrue(script.is_file())
        def call(operation,payload):
            process=subprocess.run([sys.executable,str(script),operation,'--root',str(self.root),
                     '--plan',PLAN,'--host','document','--input-json','-'],input=json.dumps(payload),
                     text=True,capture_output=True,env=self.env,timeout=8)
            self.assertEqual(process.returncode,0,process.stderr+process.stdout)
            reply=json.loads(process.stdout)
            self.assertTrue(reply['ok'])
            return reply['result']
        call('init',{'quest_id':'fixture-quest','content':'Portable options and tradeoffs\n',
                    'authority':AUTHORITY,'surface':{'kind':'document','id':None,'url':None}})
        status=call('inspect',{})
        exported=call('export',{'expected_review_hash':status['review_sha256']})
        self.assertEqual(exported['output_sha256'],sha((self.bundle/'review.html').read_bytes()))
        self.assertEqual(self.plan.read_bytes(),self.plan_bytes)


class ReviewFilesystemRegressions(ReviewFixture,unittest.TestCase):
    def fail_completed_manifest_publication(self):
        self.init()
        self.baseline()
        common=json.loads(self.manifest.read_text())['checkpoint']['common']
        snapshot=self.root/common['snapshot_path']
        original_snapshot=snapshot.read_bytes()
        self.review.write_text('A substantive next revision\n')
        prepared=self.prepare()
        marker=Path(self.temp.name)/'manifest-failure-reached'
        environment=dict(self.env,REVIEW_FAULT_MARKER=str(marker))
        command=self.command('checkpoint')
        process=subprocess.run([command[0],str(ROOT/'tests/fixtures/review/run_opaque.py'),*command[1:]],
            input=json.dumps(dict(phase='complete',checkpoint_id=prepared['checkpoint_id'],**self.guards())),
            capture_output=True,text=True,env=environment,timeout=5)
        self.assertTrue(marker.is_file(),'fault probe must reach review-state.json publication boundary')
        self.assertEqual(process.returncode,4,process.stdout+process.stderr)
        reply=json.loads(process.stdout)
        self.assertFalse(reply['ok'])
        return process,reply,common,snapshot,original_snapshot

    def test_failed_manifest_publish_preserves_reopenable_last_common_baseline(self):
        process,reply,common,snapshot,original=self.fail_completed_manifest_publication()
        # A fresh subprocess must still inspect the last complete checkpoint.
        self.invoke('inspect',{})
        current=json.loads(self.manifest.read_text())
        self.assertEqual(current['checkpoint']['common'],common)
        self.assertEqual(snapshot.read_bytes(),original,'old baseline cannot be overwritten before manifest commit')
        self.assertIsNotNone(current['checkpoint']['pending'])
        self.assertEqual(self.plan.read_bytes(),self.plan_bytes)

    def test_boundary_failure_diagnostics_are_safe_bounded_and_actionable(self):
        process,reply,common,snapshot,original=self.fail_completed_manifest_publication()
        error=reply['error']
        self.assertEqual(set(error),{'code','message','details'})
        details=error['details']
        self.assertIsInstance(details['stage'],str)
        self.assertTrue(details['stage'])
        self.assertIsInstance(details['error_class'],str)
        self.assertTrue(details['error_class'])
        self.assertLess(len(json.dumps(error)),2048)
        self.assertLess(len(process.stderr),2048)
        self.assertIn('checkpoint',process.stderr)
        self.assertIn(details['stage'],process.stderr)
        self.assertIn(details['error_class'],process.stderr)
        for forbidden in ('SYNTHETIC_SECRET_FILESYSTEM','/private/fixture/account',str(self.root)):
            self.assertNotIn(forbidden,process.stdout+process.stderr)


if __name__ == '__main__':
    unittest.main()
