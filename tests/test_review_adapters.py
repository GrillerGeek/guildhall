"""Synthetic localhost HTTP/Pi transport acceptance; no real host/model claims."""
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import threading
import time
import unittest
from urllib.parse import urlsplit

from test_review_contract import ReviewFixture, ROOT, sha


class FakeOpenCode:
    def __init__(self):
        self.session_id='oc-fixture-session'
        self.route_session_id='oc-fixture-session'
        self.preflight_entered=threading.Event()
        self.preflight_release=None
        self.delay=0
        self.trickle=0
        self.history_status=200
        self.error_text='synthetic provider failure'
        self.permission=[{'permission':'*','pattern':'*','action':'deny'}]
        self.model={'providerID':'fixture-provider','id':'fixture-selected'}
        self.history=[]
        self.calls=[]
        self.prompts=[]
        self.drop=False
        self.withhold=False
        self.abort_ack=True
        peer=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):
                pass
            def do_GET(self):
                peer.calls.append(('GET',self.path,None))
                if peer.delay:
                    time.sleep(peer.delay)
                if self.path=='/session/'+peer.route_session_id:
                    if peer.preflight_release is not None:
                        peer.preflight_entered.set()
                        peer.preflight_release.wait(5)
                    self.reply(200,{'id':peer.session_id,'permission':peer.permission,'model':peer.model})
                elif self.path=='/experimental/tool/ids':
                    self.reply(200,['read','shell','write','mcp-fixture'])
                elif self.path=='/session/'+peer.route_session_id+'/message':
                    self.reply(peer.history_status,peer.history if peer.history_status==200 else {'error':peer.error_text})
                else:
                    self.reply(404,{'error':'unexpected fixture path'})
            def do_POST(self):
                value=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))) or '{}')
                peer.calls.append(('POST',self.path,value))
                if self.path=='/session/'+peer.route_session_id+'/abort':
                    self.reply(200,peer.abort_ack)
                elif self.path=='/session/'+peer.route_session_id+'/message':
                    peer.prompts.append(value)
                    uid='user-'+str(len(peer.prompts))
                    peer.history.append({'info':{'id':uid,'role':'user','model':value.get('model')},'parts':value['parts']})
                    answer={'info':{'id':'assistant-'+uid,'role':'assistant','parentID':uid,'time':{'completed':2}},
                            'parts':[{'type':'text','text':'Synthetic OpenCode proposal'}]}
                    if not peer.withhold:
                        peer.history.append(answer)
                    if peer.drop:
                        self.close_connection=True
                        return
                    if peer.withhold:
                        self.reply(200,{'info':dict(answer['info'],time={}), 'parts':[]})
                    else:
                        self.reply(200,answer)
                else:
                    self.reply(404,{'error':'unexpected mutation'})
            def reply(self,status,value):
                body=json.dumps(value).encode()
                self.send_response(status)
                self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(body)))
                self.end_headers()
                try:
                    if peer.trickle and self.command=='POST':
                        for offset in range(0,len(body),16):
                            self.wfile.write(body[offset:offset+16])
                            self.wfile.flush()
                            time.sleep(peer.trickle)
                    else:
                        self.wfile.write(body)
                except (BrokenPipeError,ConnectionResetError):
                    pass
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.origin='http://127.0.0.1:'+str(self.server.server_port)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


class CompanionFixture(ReviewFixture):
    def start(self,binding=None,env=None,runtime=None,request_timeout=2,harness=False):
        runtime=runtime or Path(self.temp.name)/'runtime'
        self.runtime=runtime
        payload={'runtime_dir':str(runtime),'startup_timeout_seconds':3,'request_timeout_seconds':request_timeout}
        if binding is not None:
            payload['binding']=binding
        command=self.command('serve')
        if harness:
            command=[command[0],str(ROOT/'tests/fixtures/review/run_opaque.py'),*command[1:]]
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE,text=True,env=env or self.env)
        self.addCleanup(self.stop,process)
        process.stdin.write(json.dumps(payload))
        process.stdin.close()
        selector=selectors.DefaultSelector()
        try:
            selector.register(process.stdout,selectors.EVENT_READ)
            self.assertTrue(selector.select(6),'serve startup must be bounded and emit startup record')
            line=process.stdout.readline()
        finally:
            selector.close()
        self.assertTrue(line,'serve exited before startup success')
        startup=json.loads(line)
        self.assertTrue(startup['ok'],startup)
        self.assertEqual(startup['operation'],'serve')
        result=startup['result']
        origin=urlsplit(result['origin'])
        self.assertIn(origin.hostname,('127.0.0.1','::1'))
        self.assertEqual(origin.scheme,'http')
        return process,result

    def stop(self,process):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        for stream in (process.stdout,process.stderr):
            if stream:
                stream.close()

    def http(self,start,method,path,payload=None,status=200,headers=None,raw=None):
        origin=urlsplit(start['origin'])
        request_headers={'Origin':start['origin'],'X-Review-Token':start['write_token'],
                         'Content-Type':'application/json'}
        if headers:
            for key,value in headers.items():
                if value is None:
                    request_headers.pop(key,None)
                else:
                    request_headers[key]=value
        data=raw if raw is not None else (json.dumps(payload).encode() if payload is not None else None)
        connection=http.client.HTTPConnection(origin.hostname,origin.port,timeout=6)
        try:
            connection.request(method,path,body=data,headers=request_headers)
            response=connection.getresponse()
            content=response.read()
            self.assertEqual(response.status,status,content[:600])
            self.assertNotEqual(response.getheader('Access-Control-Allow-Origin'),'*')
            reply=json.loads(content)
        finally:
            connection.close()
        self.assertEqual(reply['schema_version'],1)
        self.assertEqual(reply['ok'],status<400)
        if status>=400:
            self.assertIsNone(reply['result'])
            self.assertEqual(set(reply['error']),{'code','message','details'})
            return reply['error']
        return reply['result']

    def exchange(self,start,method,path,payload):
        origin=urlsplit(start['origin'])
        connection=http.client.HTTPConnection(origin.hostname,origin.port,timeout=5)
        try:
            connection.request(method,path,body=json.dumps(payload),headers={
                'Origin':start['origin'],'X-Review-Token':start['write_token'],
                'Content-Type':'application/json'})
            response=connection.getresponse()
            return response.status,json.loads(response.read())
        except TimeoutError:
            self.fail('public HTTP response exceeded the bounded five-second harness deadline')
        finally:
            connection.close()

    def comment(self,start,state,identifier='request-1',session_id=None,**extra):
        return dict(id=identifier,session_id=session_id,base_revision=state['revision'],
                    selection='First line',comment='Discuss this choice',**extra)


class LocalCompanionTests(CompanionFixture,unittest.TestCase):
    def test_unbound_startup_state_no_secret_and_no_implicit_model(self):
        self.init()
        process,start=self.start()
        self.assertIsNone(start['session_id'])
        self.assertFalse(start['capabilities']['chat'])
        state=self.http(start,'GET','/state')
        self.assertEqual(state['document'],self.review.read_text())
        self.assertEqual(state['revision'],sha(self.review.read_bytes()))
        self.assertIsNone(state['binding'])
        self.assertNotIn(start['write_token'],json.dumps(state))
        self.assertNotIn(start['write_token'],self.manifest.read_text())
        self.assertIsNone(process.poll())

    def test_origin_host_and_token_refusals_preserve_document(self):
        self.init()
        _,start=self.start()
        state=self.http(start,'GET','/state')
        payload={'base_revision':state['revision'],'content':'Hostile edit'}
        for headers in ({'Origin':None},{'Origin':'https://attacker.invalid'},
                        {'X-Review-Token':None},{'X-Review-Token':'wrong'},
                        {'Host':'attacker.invalid'}):
            with self.subTest(headers=headers):
                self.http(start,'PUT','/document',payload,status=403,headers=headers)
                self.assertEqual(self.review.read_text(),state['document'])

    def test_two_tabs_revision_conflict_preserves_first_save_and_second_draft(self):
        self.init()
        _,start=self.start()
        state=self.http(start,'GET','/state')
        self.http(start,'PUT','/document',{'base_revision':state['revision'],'content':'First tab draft\n'})
        second={'base_revision':state['revision'],'content':'Second tab unsaved draft\n'}
        self.http(start,'PUT','/document',second,status=409)
        self.assertEqual(second['content'],'Second tab unsaved draft\n')
        self.assertEqual(self.review.read_text(),'First tab draft\n')
        self.assertEqual(self.plan.read_bytes(),self.plan_bytes)

    def test_document_byte_and_serialized_limits_are_independent(self):
        self.init()
        _,start=self.start()
        for content in ('a'*(33*1024),'a'*(256*1024)):
            state=self.http(start,'GET','/state')
            self.http(start,'PUT','/document',{'base_revision':state['revision'],'content':content})
            self.assertEqual(self.review.read_text(),content)
        state=self.http(start,'GET','/state')
        self.http(start,'PUT','/document',{'base_revision':state['revision'],'content':'\u00e9'*(128*1024+1)},status=413)
        # The decoded text fits, but escaping exceeds the independent serialized ceiling.
        raw=json.dumps({'base_revision':state['revision'],'content':'\n'*(140*1024)}).encode()
        self.assertGreater(len(raw),264*1024)
        self.http(start,'PUT','/document',status=413,raw=raw)
        self.assertEqual(self.review.read_text(),state['document'])

    def test_comment_persistence_retry_conflict_and_restart(self):
        self.init()
        process,start=self.start()
        state=self.http(start,'GET','/state')
        payload=self.comment(start,state)
        result=self.http(start,'POST','/feedback',payload)
        self.assertEqual(result['request_id'],'request-1')
        self.assertEqual(result['delivery_state'],'prepared')
        self.assertIsNone(result['response'])
        self.assertEqual(self.http(start,'POST','/feedback',payload),result)
        changed=dict(payload,comment='Changed same ID')
        self.http(start,'POST','/feedback',changed,status=409)
        self.stop(process)
        _,resumed=self.start(runtime=self.runtime)
        restored=self.http(resumed,'GET','/state')
        self.assertTrue(any(f['text']=='Discuss this choice' and f['disposition']=='proposed' for f in restored['feedback']))
        self.assertEqual(self.http(resumed,'POST','/feedback',payload)['request_id'],'request-1')
        self.assertEqual(self.plan.read_bytes(),self.plan_bytes)

    def test_empty_ambiguous_missing_and_oversize_feedback_preserves_state(self):
        self.init('First line\nFirst line\n')
        _,start=self.start()
        state=self.http(start,'GET','/state')
        payload=self.comment(start,state)
        self.http(start,'POST','/feedback',payload,status=400)
        for changes in ({'comment':''},{'selection':'absent passage'},{'selection':'x'*4001},{'comment':'x'*4001}):
            self.http(start,'POST','/feedback',dict(payload,**changes),status=400)
        raw=json.dumps(dict(payload,comment=' '*33000)).encode()
        self.http(start,'POST','/feedback',raw=raw,status=413)
        self.assertEqual(self.http(start,'GET','/state')['feedback'],[])

    def test_no_generic_execution_configuration_or_unknown_routes(self):
        self.init()
        _,start=self.start()
        for path in ('/shell','/tools','/command','/provider','/model','/spec/status','/unknown'):
            with self.subTest(path=path):
                self.http(start,'POST',path,{'command':'touch forbidden','status':'accepted'},status=404)
        self.http(start,'DELETE','/document',{},status=404)
        state=self.http(start,'GET','/state')
        self.http(start,'PUT','/document',{'base_revision':state['revision'],'content':'changed','model':'override'},status=400)
        self.assertEqual(self.plan.read_bytes(),self.plan_bytes)

    def test_hostile_parsing_and_selection_at_three_sizes_remain_bounded(self):
        self.init()
        _,start=self.start()
        for size in (1024,10*1024,100*1024):
            with self.subTest(size=size):
                # Near-match at final character forces full prefix matching against review text.
                content='a'*size+'b'
                state=self.http(start,'GET','/state')
                self.http(start,'PUT','/document',{'base_revision':state['revision'],'content':content})
                state=self.http(start,'GET','/state')
                payload=self.comment(start,state,identifier=str(size))
                payload['selection']='a'*min(size,3999)+'c'
                started=time.monotonic()
                self.http(start,'POST','/feedback',payload,status=400)
                self.assertLess(time.monotonic()-started,4)
                # Valid leading JSON string, malformed at the very end: reaches JSON parsing.
                raw=b'{"base_revision":"'+state['revision'].encode()+b'","content":"'+b'a'*size+b'\\'
                started=time.monotonic()
                self.http(start,'PUT','/document',raw=raw,status=400)
                self.assertLess(time.monotonic()-started,4)

    def test_invalid_runtime_binding_and_deadlines_refused_before_start(self):
        self.init()
        for payload,code in (({'runtime_dir':str(self.bundle)},3),
                        ({'runtime_dir':str(Path(self.temp.name)/'runtime'),'startup_timeout_seconds':301},2),
                        ({'runtime_dir':str(Path(self.temp.name)/'runtime'),'request_timeout_seconds':301},2),
                        ({'runtime_dir':str(Path(self.temp.name)/'runtime'),'binding':{'kind':'pi','session_file':str(Path(self.temp.name)/'outside.jsonl'),'executable':'sh'}},2),
                        ({'runtime_dir':str(Path(self.temp.name)/'runtime'),'binding':{'kind':'opencode','base_url':'http://example.invalid','session_id':'s'}},2)):
            with self.subTest(payload=payload):
                self.invoke('serve',payload,code=code)


class RuntimeInspectionTests(CompanionFixture,unittest.TestCase):
    def snapshot(self,path):
        # Observe bytes, file modes and modification times without depending on journal filenames.
        return {str(item.relative_to(path)):(item.is_dir(),item.stat().st_mode,
                item.stat().st_mtime_ns,None if item.is_dir() else item.read_bytes())
                for item in path.rglob('*')}

    def populated_runtime(self):
        self.init()
        process,start=self.start()
        state=self.http(start,'GET','/state')
        for identifier in ('runtime-comment-1','runtime-comment-2'):
            result=self.http(start,'POST','/feedback',self.comment(start,state,identifier=identifier))
            self.assertEqual(result['delivery_state'],'prepared')
        observed=self.http(start,'GET','/state')
        self.assertEqual({request['request_id'] for request in observed['requests']},
                         {'runtime-comment-1','runtime-comment-2'})
        self.stop(process)
        return self.runtime

    def test_fresh_inspection_counts_owned_runtime_and_preserves_all_bytes(self):
        runtime=self.populated_runtime()
        before_project=self.tree()
        before_runtime=self.snapshot(runtime)
        expected={'prepared':2,'sent-unknown':0,'response-received':0,'failed-before-send':0}
        for _ in range(2):
            # Each invoke is a fresh CLI process, after the companion is stopped.
            result=self.invoke('inspect',{'runtime_dir':str(runtime)})
            self.assertEqual(result['pending_delivery_counts'],expected)
            self.assertEqual(result['delivery_coverage'],'complete')
            self.assertEqual(self.tree(),before_project)
            self.assertEqual(self.snapshot(runtime),before_runtime)
        self.assertNotIn(str(runtime),self.manifest.read_text())

    def test_foreign_plan_and_symlink_runtime_are_refused_without_changes(self):
        runtime=self.populated_runtime()
        other_plan='docs/guildhall/plans/2026-10-18-other-review.md'
        (self.root/other_plan).write_bytes(self.plan_bytes)
        self.invoke('init',{'quest_id':'other-quest','content':'Other review',
                    'authority':{'display_label':'Fixture owner','source':'fixture initiating-user designation'},
                    'surface':{'kind':'document','id':None,'url':None}},plan=other_plan)
        direct_alias=Path(self.temp.name)/'runtime-alias'
        direct_alias.symlink_to(runtime,target_is_directory=True)
        parent_alias=Path(self.temp.name)/'parent-alias'
        parent_alias.symlink_to(runtime.parent,target_is_directory=True)
        before_project=self.tree()
        before_runtime=self.snapshot(runtime)
        self.invoke('inspect',{'runtime_dir':str(runtime)},plan=other_plan,code=3)
        for alias in (direct_alias,parent_alias/runtime.name):
            with self.subTest(runtime=str(alias)):
                self.invoke('inspect',{'runtime_dir':str(alias)},code=3)
        self.assertTrue(direct_alias.is_symlink())
        self.assertTrue(parent_alias.is_symlink())
        self.assertEqual(self.tree(),before_project)
        self.assertEqual(self.snapshot(runtime),before_runtime)


class OpenCodeAdapterTests(CompanionFixture,unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.host='opencode'
        self.init(surface={'kind':'opencode','id':None,'url':None})
        self.peer=FakeOpenCode()
        self.addCleanup(self.peer.close)
        self.binding={'kind':'opencode','base_url':self.peer.origin,'session_id':'oc-fixture-session'}

    def test_explicit_session_tool_free_request_selected_model_and_response(self):
        _,start=self.start(self.binding)
        self.assertEqual(self.peer.prompts,[],'startup must not prompt')
        self.assertEqual(start['session_id'],'oc-fixture-session')
        state=self.http(start,'GET','/state')
        result=self.http(start,'POST','/feedback',self.comment(start,state,session_id=start['session_id']))
        self.assertEqual(result['delivery_state'],'response-received')
        self.assertEqual(result['response'],'Synthetic OpenCode proposal')
        self.assertEqual(len(self.peer.prompts),1)
        sent=self.peer.prompts[0]
        self.assertEqual(sent['model'],{'providerID':'fixture-provider','modelID':'fixture-selected'})
        self.assertEqual(sent['tools'],{'read':False,'shell':False,'write':False,'mcp-fixture':False})
        marker=json.loads(sent['parts'][0]['text'])
        self.assertEqual(marker['review_request_id'],'request-1')
        self.assertEqual(marker['base_revision'],state['revision'])
        self.assertEqual(marker['selection'],'First line')
        self.assertEqual(self.plan.read_bytes(),self.plan_bytes)
        self.assertTrue(all(method=='GET' or path=='/session/oc-fixture-session/message' for method,path,_ in self.peer.calls))

    def test_request_identity_retry_conflict_and_wrong_session_never_resends(self):
        _,start=self.start(self.binding)
        state=self.http(start,'GET','/state')
        payload=self.comment(start,state,session_id=start['session_id'])
        first=self.http(start,'POST','/feedback',payload)
        self.assertEqual(self.http(start,'POST','/feedback',payload),first)
        self.http(start,'POST','/feedback',dict(payload,comment='Different content'),status=409)
        self.http(start,'POST','/feedback',dict(payload,id='wrong-session',session_id='other'),status=409)
        self.assertEqual(len(self.peer.prompts),1)

    def test_restrictions_and_identity_rechecked_before_every_send(self):
        _,start=self.start(self.binding)
        state=self.http(start,'GET','/state')
        self.peer.session_id='unexpected-session'
        self.http(start,'POST','/feedback',self.comment(start,state,session_id=start['session_id']),status=409)
        self.assertEqual(self.peer.prompts,[])
        self.peer.session_id='oc-fixture-session'
        self.peer.permission=[]
        self.http(start,'POST','/feedback',self.comment(start,state,identifier='restricted',session_id=start['session_id']),status=502)
        self.assertEqual(self.peer.prompts,[])
        self.assertFalse(any(method in ('PATCH','PUT') for method,_,_ in self.peer.calls))

    def test_unsafe_session_falls_back_without_permission_changes(self):
        self.peer.permission=[]
        _,start=self.start(self.binding)
        self.assertFalse(start['capabilities']['chat'])
        self.assertTrue(start['capabilities']['document'])
        self.assertTrue(start['capabilities']['comments'])
        self.assertIn('unavailable_reason',start)
        self.assertEqual(self.peer.prompts,[])

    def test_send_disconnect_history_recovery_and_restart_do_not_duplicate(self):
        self.peer.drop=True
        process,start=self.start(self.binding)
        state=self.http(start,'GET','/state')
        payload=self.comment(start,state,session_id=start['session_id'])
        # May recover the already observed answer immediately or on subsequent inspection.
        result=self.http(start,'POST','/feedback',payload)
        self.assertIn(result['delivery_state'],('sent-unknown','response-received'))
        self.stop(process)
        self.peer.drop=False
        _,resumed=self.start(self.binding,runtime=self.runtime)
        retry=self.http(resumed,'POST','/feedback',payload)
        self.assertEqual(retry['delivery_state'],'response-received')
        self.assertEqual(len(self.peer.prompts),1)

    def test_unknown_delivery_blocks_rebind_and_cancel_requires_ack(self):
        self.peer.withhold=True
        process,start=self.start(self.binding,request_timeout=1)
        state=self.http(start,'GET','/state')
        payload=self.comment(start,state,session_id=start['session_id'])
        result=self.http(start,'POST','/feedback',payload)
        self.assertEqual(result['delivery_state'],'sent-unknown')
        self.http(start,'POST','/rebind',{'expected_session_id':start['session_id'],
                  'new_binding':self.binding,'source_ref':'fixture operator rebind'},status=409)
        self.peer.abort_ack=False
        result=self.http(start,'POST','/cancel',{'request_id':'request-1','session_id':start['session_id']})
        self.assertEqual(result['delivery_state'],'sent-unknown')
        self.assertEqual(len(self.peer.prompts),1)
        self.stop(process)
        # Companion shutdown leaves the externally owned host running.
        self.assertTrue(self.peer.thread.is_alive())


class PiAdapterTests(CompanionFixture,unittest.TestCase):
    def start_pi(self,mode='complete'):
        self.host='pi'
        self.init(surface={'kind':'pi','id':None,'url':None})
        runtime=Path(self.temp.name)/'pi-runtime'
        runtime.mkdir(mode=0o700,exist_ok=True)
        bindir=Path(self.temp.name)/'bin'
        bindir.mkdir()
        shutil.copy2(ROOT/'tests/fixtures/review/pi',bindir/'pi')
        env=dict(self.env,PATH=str(bindir)+os.pathsep+os.environ.get('PATH',''),
                 REVIEW_FAKE_PI_LOG=str(runtime/'calls.jsonl'),
                 REVIEW_FAKE_PI_HISTORY=str(runtime/'history.json'),REVIEW_FAKE_PI_MODE=mode)
        process,start=self.start({'kind':'pi','session_file':str(runtime/'owned.jsonl')},env=env,runtime=runtime)
        self.pi_log=runtime/'calls.jsonl'
        return process,start

    def calls(self):
        return [json.loads(line) for line in self.pi_log.read_text().splitlines()]

    def test_owned_tool_free_rpc_startup_and_terminal_response(self):
        _,start=self.start_pi()
        calls=self.calls()
        self.assertFalse(any(c.get('type')=='prompt' for c in calls))
        argv=calls[0]['argv']
        for flag in ('--mode','rpc','--session','--no-tools','--no-extensions','--no-mcp',
                     '--no-skills','--no-prompt-templates','--no-themes','--no-context-files','--no-approve','--offline'):
            self.assertIn(flag,argv)
        self.assertNotIn('--model',argv)
        self.assertNotIn('--provider',argv)
        self.assertEqual(start['session_id'],'pi-fixture-session')
        state=self.http(start,'GET','/state')
        result=self.http(start,'POST','/feedback',self.comment(start,state,session_id=start['session_id']))
        self.assertEqual(result['delivery_state'],'response-received')
        self.assertEqual(result['response'],'Synthetic Pi proposal')
        prompts=[c for c in self.calls() if c.get('type')=='prompt']
        self.assertEqual(len(prompts),1)
        self.assertEqual(json.loads(prompts[0]['message'])['review_request_id'],'request-1')

    def test_acceptance_is_not_completion_cancel_clears_queue_before_abort(self):
        _,start=self.start_pi(mode='pending')
        state=self.http(start,'GET','/state')
        result=self.http(start,'POST','/feedback',self.comment(start,state,session_id=start['session_id']))
        self.assertEqual(result['delivery_state'],'sent-unknown')
        self.http(start,'POST','/cancel',{'request_id':'request-1','session_id':start['session_id']})
        types=[c.get('type') for c in self.calls()]
        self.assertIn('clear_queue',types)
        self.assertIn('abort',types)
        self.assertLess(types.index('clear_queue'),types.index('abort'))
        self.assertEqual(types.count('prompt'),1)

    def test_tool_call_cannot_be_reported_as_successful_chat(self):
        _,start=self.start_pi(mode='toolcall')
        state=self.http(start,'GET','/state')
        result=self.http(start,'POST','/feedback',self.comment(start,state,session_id=start['session_id']),status=502)
        self.assertIsInstance(result['details'],dict)
        self.assertEqual(self.plan.read_bytes(),self.plan_bytes)


class ReviewRaceAndRuntimeTests(CompanionFixture,unittest.TestCase):
    def test_feedback_preflight_racing_rebind_never_crosses_sessions(self):
        self.host='opencode'
        self.init(surface={'kind':'opencode','id':None,'url':None})
        first=FakeOpenCode()
        second=FakeOpenCode()
        self.addCleanup(first.close)
        self.addCleanup(second.close)
        second.route_session_id=second.session_id='session-B'
        binding={'kind':'opencode','base_url':first.origin,'session_id':first.session_id}
        _,start=self.start(binding,request_timeout=3)
        state=self.http(start,'GET','/state')
        first.preflight_release=threading.Event()
        results={}
        errors=[]
        def run(key,path,payload):
            try:
                response=self.exchange(start,'POST',path,payload)
                results[key]=(*response,time.monotonic())
            except Exception as error:
                errors.append(error)
        feedback=threading.Thread(target=run,args=('feedback','/feedback',
                  self.comment(start,state,session_id=first.session_id)),daemon=True)
        feedback.start()
        self.assertTrue(first.preflight_entered.wait(2),'probe must reach paused A preflight')
        rebind=threading.Thread(target=run,args=('rebind','/rebind',{
            'expected_session_id':first.session_id,
            'new_binding':{'kind':'opencode','base_url':second.origin,'session_id':second.session_id},
            'source_ref':'fixture operator decision'}),daemon=True)
        rebind.start()
        time.sleep(.1)
        first.preflight_release.set()
        feedback.join(4)
        rebind.join(4)
        self.assertFalse(feedback.is_alive() or rebind.is_alive(),'race must finish within deadlines')
        self.assertEqual(errors,[])
        self.assertEqual(second.prompts,[],'A feedback must never be sent into B')
        rebind_status,_,rebind_completed=results['rebind']
        feedback_status,feedback_reply,feedback_completed=results['feedback']
        if rebind_status==200:
            if feedback_status==200:
                # Safe serialization: A completes in A before the successful B rebind.
                self.assertEqual(len(first.prompts),1)
                self.assertEqual(feedback_reply['result']['response'],'Synthetic OpenCode proposal')
                self.assertEqual(feedback_reply['result']['delivery_state'],'response-received')
                self.assertLessEqual(feedback_completed,rebind_completed)
            else:
                self.assertIn(feedback_status,(409,502))
                self.assertEqual(first.prompts,[])
        else:
            self.assertEqual(rebind_status,409)
            self.assertEqual(feedback_status,200)
            self.assertEqual(len(first.prompts),1)

    def test_comment_saved_after_prepare_survives_complete_or_safe_refusal(self):
        self.init()
        prepared=self.prepare()
        _,start=self.start()
        state=self.http(start,'GET','/state')
        self.http(start,'POST','/feedback',self.comment(start,state,identifier='post-prepare-comment'))
        before=json.loads(self.manifest.read_text())
        comment=next(entry for entry in before['feedback'] if entry['id']=='post-prepare-comment')
        self.assertEqual(comment['disposition'],'proposed')
        self.assertTrue(comment['source_ref'])
        packet=dict(phase='complete',checkpoint_id=prepared['checkpoint_id'],**self.guards())
        completed=subprocess.run(self.command('checkpoint'),input=json.dumps(packet),text=True,
                  capture_output=True,env=self.env,timeout=5)
        self.assertIn(completed.returncode,(0,2,3,4))
        self.assertIsInstance(json.loads(completed.stdout),dict)
        after=json.loads(self.manifest.read_text())
        self.assertIn(comment,after['feedback'],'fresh guards do not authorize erasing intervening feedback')
        if completed.returncode:
            self.assertIsNotNone(after['checkpoint']['pending'])

    def test_unsafe_runtime_is_refused_without_chmod_or_host_access(self):
        self.init()
        process,start=self.start()
        state=self.http(start,'GET','/state')
        self.http(start,'POST','/feedback',self.comment(start,state))
        self.stop(process)
        runtime=self.runtime
        before={str(p.relative_to(runtime)):p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
        for mode in (0o750,0o770,0o707):
            with self.subTest(mode=oct(mode)):
                runtime.chmod(mode)
                self.invoke('inspect',{'runtime_dir':str(runtime)},code=3)
                self.assertEqual(runtime.stat().st_mode & 0o777,mode)
                self.invoke('serve',{'runtime_dir':str(runtime)},code=3)
                self.assertEqual(runtime.stat().st_mode & 0o777,mode)
                self.assertEqual({str(p.relative_to(runtime)):p.read_bytes() for p in runtime.rglob('*') if p.is_file()},before)
        runtime.chmod(0o700)

    def test_total_timeout_includes_preflight_and_slow_trickle_read(self):
        self.host='opencode'
        self.init(surface={'kind':'opencode','id':None,'url':None})
        peer=FakeOpenCode()
        self.addCleanup(peer.close)
        _,start=self.start({'kind':'opencode','base_url':peer.origin,'session_id':peer.session_id},request_timeout=1)
        state=self.http(start,'GET','/state')
        peer.delay=.3
        peer.trickle=.2
        begun=time.monotonic()
        status,reply=self.exchange(start,'POST','/feedback',self.comment(start,state,session_id=peer.session_id))
        elapsed=time.monotonic()-begun
        self.assertLess(elapsed,1.8,'one overall budget must cover individually sub-timeout phases and trickle')
        self.assertIn(status,(200,502))
        observed=self.http(start,'GET','/state')
        record=next(item for item in observed['requests'] if item['request_id']=='request-1')
        if peer.prompts:
            self.assertEqual(record['delivery_state'],'sent-unknown')
            self.assertIsNone(record['response'])
        else:
            self.assertIn(record['delivery_state'],('prepared','failed-before-send'))

    def test_failed_history_recovery_is_correlated_safe_and_disables_unsafe_chat(self):
        self.host='opencode'
        self.init(surface={'kind':'opencode','id':None,'url':None})
        peer=FakeOpenCode()
        self.addCleanup(peer.close)
        peer.withhold=True
        _,start=self.start({'kind':'opencode','base_url':peer.origin,'session_id':peer.session_id},request_timeout=1)
        state=self.http(start,'GET','/state')
        sent=self.http(start,'POST','/feedback',self.comment(start,state,session_id=peer.session_id))
        self.assertEqual(sent['delivery_state'],'sent-unknown')
        peer.history_status=500
        peer.error_text='SYNTHETIC_SECRET_PROVIDER_DIAGNOSTIC /private/fixture/account'
        peer.permission=[]
        recovered=self.http(start,'GET','/state')
        record=next(item for item in recovered['requests'] if item['request_id']=='request-1')
        self.assertEqual(record['session_id'],peer.session_id)
        self.assertEqual(record['delivery_state'],'sent-unknown')
        error=record['recovery_error']
        self.assertEqual(set(error),{'code','message','details'})
        self.assertTrue(error['details']['stage'])
        self.assertTrue(error['details']['error_class'])
        self.assertLess(len(json.dumps(error)),2048)
        self.assertNotIn('SYNTHETIC_SECRET_PROVIDER_DIAGNOSTIC',json.dumps(recovered))
        self.assertNotIn('/private/fixture/account',json.dumps(recovered))
        self.assertNotIn(start['write_token'],json.dumps(recovered))
        self.assertFalse(recovered['capabilities']['chat'])
        self.assertTrue(recovered['unavailable_reason'])
        self.assertEqual(len(peer.prompts),1)


class PiRecoveryRegressions(CompanionFixture,unittest.TestCase):
    def start_controlled(self,harness=False):
        self.host='pi'
        self.init(surface={'kind':'pi','id':None,'url':None})
        self.runtime=Path(self.temp.name)/'controlled-runtime'
        self.runtime.mkdir(mode=0o700)
        binpath=Path(self.temp.name)/'controlled-bin'
        binpath.mkdir()
        executable=binpath/'pi'
        shutil.copy2(ROOT/'tests/fixtures/review/pi',executable)
        self.control=self.runtime/'fixture-control.json'
        self.control.write_text(json.dumps({'mode':'pending'}))
        self.pi_environment=dict(self.env,PATH=str(binpath)+os.pathsep+self.env.get('PATH',''),
            REVIEW_FAKE_PI_LOG=str(self.runtime/'fixture-calls.jsonl'),
            REVIEW_FAKE_PI_HISTORY=str(self.runtime/'fixture-history.json'),
            REVIEW_FAKE_PI_CONTROL=str(self.control),REVIEW_FAKE_PI_EXECUTABLE=str(executable),
            REVIEW_SATURATE_OWNED_PIPE='1' if harness else '0')
        self.pi_binding={'kind':'pi','session_file':str(self.runtime/'dedicated.jsonl')}
        return self.start(self.pi_binding,env=self.pi_environment,runtime=self.runtime,request_timeout=1,harness=harness)

    def wait_file(self,path,timeout=3):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline and not path.exists():
            time.sleep(.02)
        self.assertTrue(path.exists(),'fixture synchronization boundary was not reached: '+path.name)

    def test_late_A_is_recovered_but_cannot_complete_pending_B(self):
        _,start=self.start_controlled()
        state=self.http(start,'GET','/state')
        a=self.comment(start,state,identifier='A',session_id=start['session_id'])
        self.assertEqual(self.http(start,'POST','/feedback',a)['delivery_state'],'sent-unknown')
        self.control.write_text(json.dumps({'mode':'pending','complete_request':'A'}))
        deadline=time.monotonic()+3
        recovered=None
        while time.monotonic()<deadline:
            result=self.http(start,'GET','/state')
            recovered=next(request for request in result['requests'] if request['request_id']=='A')
            if recovered['delivery_state']=='response-received':
                break
            time.sleep(.05)
        self.assertEqual(recovered['delivery_state'],'response-received')
        self.assertEqual(recovered['response'],'Synthetic late answer A')
        b=self.http(start,'POST','/feedback',self.comment(start,state,identifier='B',session_id=start['session_id']))
        self.assertEqual(b['delivery_state'],'sent-unknown')
        self.assertIsNone(b['response'],'A terminal events/history must not complete B')
        observed=self.http(start,'GET','/state')
        record=next(request for request in observed['requests'] if request['request_id']=='B')
        self.assertEqual(record['delivery_state'],'sent-unknown')
        self.assertIsNone(record['response'])

    def test_restart_same_session_file_changed_session_id_requires_rebind(self):
        process,start=self.start_controlled()
        self.assertEqual(start['session_id'],'pi-fixture-session')
        self.stop(process)
        self.control.write_text(json.dumps({'mode':'pending','session_id':'unexpected-new-session'}))
        # A refusal may occur at startup or preserve visibly disabled document mode.
        command=self.command('serve')
        restarted=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                   text=True,env=self.pi_environment)
        self.addCleanup(self.stop,restarted)
        restarted.stdin.write(json.dumps({'runtime_dir':str(self.runtime),'binding':self.pi_binding,
                              'startup_timeout_seconds':2,'request_timeout_seconds':1}))
        restarted.stdin.close()
        ready=selectors.DefaultSelector()
        try:
            ready.register(restarted.stdout,selectors.EVENT_READ)
            self.assertTrue(ready.select(4))
            reply=json.loads(restarted.stdout.readline())
        finally:
            ready.close()
        if reply['ok']:
            self.assertFalse(reply['result']['capabilities']['chat'])
            self.assertTrue(reply['result']['unavailable_reason'])
        else:
            self.assertEqual(restarted.wait(timeout=3),3)
        calls=[json.loads(line) for line in (self.runtime/'fixture-calls.jsonl').read_text().splitlines()]
        self.assertFalse(any(call.get('type')=='prompt' for call in calls))

    def test_saturated_owned_pi_stdin_feedback_and_cancel_are_bounded(self):
        import signal
        process,start=self.start_controlled(harness=True)
        unrelated=subprocess.Popen([self.command('serve')[0],'-c','import time; time.sleep(30)'],
                    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=self.env)
        self.addCleanup(self.stop,unrelated)
        state=self.http(start,'GET','/state')
        self.control.write_text(json.dumps({'mode':'pending','stall':True}))
        self.wait_file(Path(str(self.control)+'.stalled'))
        self.wait_file(Path(str(self.control)+'.saturated'))
        self.assertGreater(int(Path(str(self.control)+'.saturated').read_text()),0)
        calls=[json.loads(line) for line in (self.runtime/'fixture-calls.jsonl').read_text().splitlines()]
        owned_pid=calls[0]['pid']
        try:
            with self.subTest(operation='feedback'):
                begun=time.monotonic()
                status,reply=self.exchange(start,'POST','/feedback',self.comment(start,state,session_id=start['session_id']))
                self.assertLess(time.monotonic()-begun,1.8,'full owned stdin pipe must not block request indefinitely')
                self.assertIn(status,(200,502))
            with self.subTest(operation='cancel'):
                begun=time.monotonic()
                status,_=self.exchange(start,'POST','/cancel',{'request_id':'request-1','session_id':start['session_id']})
                self.assertLess(time.monotonic()-begun,1.8,'cancel cannot block indefinitely writing to full owned pipe')
                self.assertIn(status,(200,409,502))
        finally:
            self.control.write_text(json.dumps({'mode':'pending','stall':False}))
            try:
                os.kill(owned_pid,signal.SIGCONT)
            except ProcessLookupError:
                pass
        observed=self.http(start,'GET','/state')
        pending=[request for request in observed['requests'] if request['request_id']=='request-1']
        if pending:
            self.assertIn(pending[0]['delivery_state'],('failed-before-send','sent-unknown'))
            self.assertIsNone(pending[0]['response'])
        else:
            # A blocked preflight may safely refuse before any model request exists.
            calls=[json.loads(line) for line in (self.runtime/'fixture-calls.jsonl').read_text().splitlines()]
            self.assertFalse(any(call.get('type')=='prompt' for call in calls))
        self.stop(process)
        self.assertIsNone(unrelated.poll(),'companion cleanup must leave unrelated processes alive')


if __name__=='__main__':
    unittest.main()
