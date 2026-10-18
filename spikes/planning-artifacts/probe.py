#!/usr/bin/env python3
"""Disposable local review bridge: real harness, synthetic model, no credentials."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import secrets
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def save(path, data):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2) + '\n')
    tmp.replace(path)


def request(url, data=None, method=None, headers=None):
    payload = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(url, data=payload, method=method,
                                 headers={'Content-Type': 'application/json', **(headers or {})})
    with urllib.request.urlopen(req, timeout=40) as response:
        return json.load(response)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def respond(self, data, status=200):
        content = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def body(self):
        size = int(self.headers.get('Content-Length', '0'))
        if not 0 < size <= 32768:
            raise ValueError('body must be between 1 and 32768 bytes')
        return json.loads(self.rfile.read(size))


class SyntheticProvider(Handler):
    """Fixed transport witness; deliberately does not reason about the proposal."""
    calls = 0

    def do_POST(self):
        body = self.body()
        type(self).calls += 1
        text = 'SYNTHETIC transport response: feedback received; decision remains proposed.'
        model = body.get('model', 'fixture')
        if body.get('stream'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.end_headers()
            for delta, reason in [({'role': 'assistant', 'content': text}, None), ({}, 'stop')]:
                chunk = {'id': 'chatcmpl-fixture', 'object': 'chat.completion.chunk',
                         'created': int(time.time()), 'model': model,
                         'choices': [{'index': 0, 'delta': delta, 'finish_reason': reason}]}
                self.wfile.write(('data: ' + json.dumps(chunk) + '\n\n').encode())
            self.wfile.write(b'data: [DONE]\n\n')
            self.wfile.flush()
        else:
            self.respond({'id': 'chatcmpl-fixture', 'object': 'chat.completion',
                          'created': int(time.time()), 'model': model,
                          'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': text},
                                       'finish_reason': 'stop'}],
                          'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2}})


def server(handler):
    srv = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def isolated_env(root):
    # Do not inherit provider keys, auth tokens, personal configs, or plugin flags.
    env = {'PATH': os.environ['PATH'], 'TMPDIR': str(root), 'LANG': 'en_US.UTF-8',
           'PI_CODING_AGENT_DIR': str(root / 'pi-config'), 'PI_OFFLINE': '1',
           'PI_TELEMETRY': '0', 'OPENCODE_DISABLE_AUTOUPDATE': '1',
           'OPENCODE_DISABLE_MODELS_FETCH': '1', 'OPENCODE_CONFIG_DIR': str(root / 'opencode-config')}
    for kind in ('CONFIG', 'DATA', 'CACHE', 'STATE'):
        path = root / ('xdg-' + kind.lower())
        path.mkdir(exist_ok=True)
        env['XDG_' + kind + '_HOME'] = str(path)
    Path(env['PI_CODING_AGENT_DIR']).mkdir(exist_ok=True)
    Path(env['OPENCODE_CONFIG_DIR']).mkdir(exist_ok=True)
    return env


class OpenCode:
    def __init__(self, root, env, provider):
        self.root = root
        config = {'model': 'fixture/review', 'small_model': 'fixture/review',
                  'enabled_providers': ['fixture'], 'autoupdate': False,
                  'permission': {'*': 'deny'},
                  'provider': {'fixture': {'npm': '@ai-sdk/openai-compatible',
                    'name': 'Synthetic fixture', 'options': {'baseURL': provider + '/v1', 'apiKey': 'fixture'},
                    'models': {'review': {'name': 'Synthetic review', 'limit': {'context': 32000, 'output': 1000}}}}}}
        save(root / 'opencode.json', config)
        self.log = (root / 'opencode.log').open('w+')
        self.proc = subprocess.Popen(['opencode', 'serve', '--pure', '--hostname', '127.0.0.1', '--port', '0'],
                                     cwd=root, env=env, stdout=self.log, stderr=self.log)
        deadline = time.monotonic() + 30
        self.url = None
        while time.monotonic() < deadline:
            self.log.flush()
            text = (root / 'opencode.log').read_text()
            import re
            found = re.search(r'http://127\.0\.0\.1:\d+', text)
            if found:
                self.url = found.group()
                break
            if self.proc.poll() is not None:
                raise RuntimeError('OpenCode startup failed: ' + text[-2500:])
            time.sleep(.1)
        if not self.url:
            self.close()
            raise RuntimeError('OpenCode startup timeout: ' + text[-2500:])
        self.session_path = root / 'opencode-session.json'
        if self.session_path.exists():
            self.session = json.loads(self.session_path.read_text())['id']
            request(self.url + '/session/' + self.session)
        else:
            self.session = request(self.url + '/session', {'title': 'Guildhall artifact spike'})['id']
            save(self.session_path, {'id': self.session})

    def prompt(self, text):
        reply = request(self.url + '/session/' + self.session + '/message',
                        {'model': {'providerID': 'fixture', 'modelID': 'review'},
                         'parts': [{'type': 'text', 'text': text}]})
        if reply.get('info', {}).get('error'):
            raise RuntimeError(str(reply['info']['error']))
        answer = ''.join(p.get('text', '') for p in reply.get('parts', []) if p['type'] == 'text')
        if not answer:
            raise RuntimeError('OpenCode returned no assistant text: ' + str(reply)[:1500])
        return answer

    def history(self):
        return request(self.url + '/session/' + self.session + '/message')

    def close(self):
        self.proc.terminate()
        self.proc.wait(timeout=10)
        self.log.close()


class Pi:
    def __init__(self, root, env, provider):
        models = {'providers': {'fixture': {'baseUrl': provider + '/v1', 'api': 'openai-completions',
                   'apiKey': 'fixture', 'models': [{'id': 'review', 'name': 'Synthetic review',
                      'contextWindow': 32000, 'maxTokens': 1000, 'reasoning': False, 'input': ['text']}]}}}
        save(Path(env['PI_CODING_AGENT_DIR']) / 'models.json', models)
        self.log = (root / 'pi.log').open('w')
        self.proc = subprocess.Popen(['pi', '--mode', 'rpc', '--offline', '--provider', 'fixture',
              '--model', 'review', '--thinking', 'off', '--no-tools', '--no-extensions', '--no-mcp',
              '--no-skills', '--no-prompt-templates', '--no-themes', '--no-context-files', '--no-approve',
              '--session', str(root / 'pi-session.jsonl'), '--system-prompt', 'Review planning feedback only.'],
              cwd=root, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log)
        self.records = queue.Queue()
        def reader():
            for line in self.proc.stdout:
                try:
                    self.records.put(json.loads(line))
                except ValueError:
                    self.records.put({'type': 'invalid', 'line': line.decode(errors='replace')})
        threading.Thread(target=reader, daemon=True).start()
        self.session = self.command('get_state')['sessionId']

    def send(self, kind, **data):
        rid = secrets.token_hex(8)
        self.proc.stdin.write((json.dumps({'type': kind, 'id': rid, **data}) + '\n').encode())
        self.proc.stdin.flush()
        return rid

    def command(self, kind):
        rid = self.send(kind)
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            record = self.records.get(timeout=max(.1, deadline - time.monotonic()))
            if record.get('id') == rid and record['type'] == 'response':
                if not record.get('success'):
                    raise RuntimeError(str(record))
                return record.get('data', {})
        raise TimeoutError(kind)

    def prompt(self, text):
        rid = self.send('prompt', message=text)
        answer = None
        accepted = False
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            event = self.records.get(timeout=max(.1, deadline - time.monotonic()))
            if event.get('id') == rid:
                if not event.get('success'):
                    raise RuntimeError(str(event))
                accepted = True
            if event['type'] == 'message_end':
                msg = event.get('message', {})
                if msg.get('role') == 'assistant':
                    if msg.get('stopReason') in ('error', 'aborted'):
                        raise RuntimeError(str(msg))
                    answer = ''.join(x.get('text', '') for x in msg.get('content', []) if x['type'] == 'text')
            if event['type'] == 'agent_settled' and accepted and answer:
                return answer
        raise TimeoutError('Pi response completion')

    def history(self):
        return self.command('get_messages')

    def close(self):
        self.proc.stdin.close()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            self.proc.wait(timeout=5)
        self.log.close()


class Review:
    def __init__(self, root, harness):
        self.root, self.harness = root, harness
        self.path = root / 'proposal.md'
        if not self.path.exists():
            self.path.write_text('Use one review Page per quest. Keep accepted decisions in source control.\n')
        self.state_path = root / 'review-state.json'
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {'feedback': {}}
        self.lock = threading.Lock()

    def view(self):
        text = self.path.read_text()
        return {'proposal': text, 'revision': digest(text), 'session': self.harness.session,
                'feedback': self.state['feedback']}

    def submit(self, data):
        with self.lock:
            fingerprint = digest(json.dumps(data, sort_keys=True))
            existing = self.state['feedback'].get(data['id'])
            if existing:
                if existing['fingerprint'] != fingerprint:
                    raise ValueError('submission ID reused with different content')
                return existing
            view = self.view()
            if data['session'] != view['session'] or data['revision'] != view['revision']:
                raise ValueError('session or proposal revision changed; reload before submitting')
            selection = data.get('selection', '')
            if selection and view['proposal'].count(selection) != 1:
                raise ValueError('selection must occur exactly once in current proposal')
            comment = data['comment']
            if not isinstance(comment, str) or not comment.strip() or len(comment) > 4000:
                raise ValueError('comment required; maximum 4000 characters')
            entry = {'fingerprint': fingerprint, 'input': data, 'status': 'pending', 'disposition': 'proposed'}
            self.state['feedback'][data['id']] = entry
            save(self.state_path, self.state)
            # A crash after sending leaves pending, never automatically replayed.
            try:
                entry['response'] = self.harness.prompt('Planning review input (not execution approval):\n' +
                    json.dumps({'proposal': view['proposal'], 'feedback': data}))
                entry['status'] = 'received'
            except Exception as exc:
                entry['status'] = 'uncertain'
                entry['error'] = str(exc)
                raise
            finally:
                save(self.state_path, self.state)
            return entry

    def checkpoint(self, data):
        with self.lock:
            view = self.view()
            if data['revision'] != view['revision'] or data['session'] != view['session']:
                raise ValueError('checkpoint conflict; local proposal or session changed')
            save(self.root / 'checkpoint.json', view)
            return {'saved': True, 'revision': view['revision'], 'disposition': 'proposed'}


def bridge(review):
    token = secrets.token_hex(24)
    class Bridge(Handler):
        def do_GET(self):
            if self.path == '/':
                content = Path(__file__).with_name('review.html').read_text().replace('__TOKEN__', token).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            elif self.path == '/state':
                self.respond(review.view())
            else:
                self.respond({'error': 'not found'}, 404)

        def do_POST(self):
            # Loopback-only fixture; browser writes require the per-process token.
            if self.headers.get('X-Review-Token') != token:
                return self.respond({'error': 'missing review token'}, 403)
            origin = self.headers.get('Origin')
            if origin and origin != 'http://' + self.headers.get('Host', ''):
                return self.respond({'error': 'cross-origin write refused'}, 403)
            try:
                data = self.body()
                if self.path == '/feedback':
                    result = review.submit(data)
                elif self.path == '/checkpoint':
                    result = review.checkpoint(data)
                else:
                    return self.respond({'error': 'not found'}, 404)
                self.respond(result)
            except (ValueError, KeyError) as exc:
                self.respond({'error': str(exc)}, 409)
            except Exception as exc:
                self.respond({'error': str(exc)}, 502)
    return server(Bridge), token


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', choices=['opencode', 'pi'])
    parser.add_argument('--fixture', type=Path)
    parser.add_argument('--serve', action='store_true')
    args = parser.parse_args()
    root = args.fixture or Path(tempfile.mkdtemp(prefix='guildhall-artifact-' + args.host + '-'))
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    env = isolated_env(root)
    provider = server(SyntheticProvider)
    url = 'http://127.0.0.1:' + str(provider.server_port)
    harness = None
    web = None
    try:
        version = subprocess.check_output([args.host, '--version'], env=env, text=True).strip()
        harness = (OpenCode if args.host == 'opencode' else Pi)(root, env, url)
        review = Review(root, harness)
        web, token = bridge(review)
        web_url = 'http://127.0.0.1:' + str(web.server_port)
        print(json.dumps({'host': args.host, 'version': version, 'url': web_url, 'fixture': str(root),
                          'synthetic_provider': True}), flush=True)
        if args.serve:
            while True:
                time.sleep(1)
        else:
            view = review.view()
            data = {'id': secrets.token_hex(8), 'session': view['session'], 'revision': view['revision'],
                    'selection': 'one review Page per quest', 'comment': 'Keep one Page and record the decision.'}
            headers = {'X-Review-Token': token, 'Origin': web_url}
            for denied in ({}, {**headers, 'Origin': 'https://unrelated.example'}):
                try:
                    request(web_url + '/feedback', data, headers=denied)
                    raise AssertionError('unauthorized browser write accepted')
                except urllib.error.HTTPError as exc:
                    assert exc.code == 403
            result = request(web_url + '/feedback', data, headers=headers)
            assert 'SYNTHETIC' in result['response']
            calls = SyntheticProvider.calls
            assert review.submit(data) == result and SyntheticProvider.calls == calls
            try:
                review.submit({**data, 'comment': 'Changed same ID'})
                raise AssertionError('duplicate conflict accepted')
            except ValueError:
                pass
            request(web_url + '/checkpoint', view, headers=headers)
            recovered = Review(root, harness)
            assert recovered.state == review.state
            # Reconnect to the same persisted session through a fresh host process.
            original_session = harness.session
            history = json.dumps(harness.history())
            assert data['id'] in history and 'SYNTHETIC' in history
            harness.close()
            harness = (OpenCode if args.host == 'opencode' else Pi)(root, env, url)
            assert harness.session == original_session
            assert data['id'] in json.dumps(harness.history())
            recovered.harness = harness
            assert recovered.submit(data) == result and SyntheticProvider.calls == calls
            followup = {**data, 'id': secrets.token_hex(8), 'comment': 'Follow-up after reconnect.'}
            assert 'SYNTHETIC' in recovered.submit(followup)['response']
            assert followup['id'] in json.dumps(harness.history())
            calls = SyntheticProvider.calls
            pending = {**data, 'id': secrets.token_hex(8), 'comment': 'Interrupted delivery.'}
            recovered.state['feedback'][pending['id']] = {
                'fingerprint': digest(json.dumps(pending, sort_keys=True)),
                'input': pending, 'status': 'pending', 'disposition': 'proposed'}
            save(recovered.state_path, recovered.state)
            pending_review = Review(root, harness)
            assert pending_review.submit(pending)['status'] == 'pending'
            assert SyntheticProvider.calls == calls
            try:
                recovered.submit({**data, 'id': secrets.token_hex(8), 'session': 'wrong-session'})
                raise AssertionError('wrong session accepted')
            except ValueError:
                pass
            review.path.write_text(view['proposal'] + '\nConcurrent local edit.\n')
            try:
                recovered.checkpoint(view)
                raise AssertionError('stale checkpoint accepted')
            except ValueError:
                pass
            assert 'Concurrent local edit.' in review.path.read_text()
            receipt = {'host': args.host, 'version': version, 'synthetic_provider': True,
                       'round_trip': True, 'duplicate_suppressed': True, 'duplicate_conflict_refused': True,
                       'state_reloaded': True, 'session_reconnected': True, 'history_verified': True,
                       'post_reconnect_round_trip': True, 'pending_not_replayed': True,
                       'wrong_session_refused': True,
                       'http_feedback_checkpoint': True, 'unauthorized_browser_writes_refused': True,
                       'stale_checkpoint_refused': True, 'concurrent_edit_preserved': True,
                       'browser_exercised': False, 'provider_requests': SyntheticProvider.calls}
            save(root / 'receipt.json', receipt)
            print(json.dumps(receipt), flush=True)
    finally:
        if harness:
            harness.close()
        if web:
            web.shutdown()
        provider.shutdown()


if __name__ == '__main__':
    main()
