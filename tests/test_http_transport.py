"""Bounded loopback fixtures: never use real credentials or upstreams."""
import json
import threading
import urllib.error
import urllib.request
from contextlib import ExitStack, contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from chatcrs import codex_direct, local, remote, reset_credits


@contextmanager
def server(*, status=200, redirect=None):
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            seen.append((self.command, self.path))
            self.rfile.read(int(self.headers.get('Content-Length', 0)))
            self.send_response(status)
            if redirect:
                self.send_header('Location', redirect)
            stream = self.path.endswith('/openai/responses')
            self.send_header('Content-Type', 'text/event-stream' if stream else 'application/json')
            self.end_headers()
            if stream:
                events = [
                    {'type': 'response.output_text.delta', 'delta': 'fixture'},
                    {'type': 'response.completed', 'response': {'status': 'completed'}},
                ]
                self.wfile.write(''.join('data: ' + json.dumps(e) + '\n\n' for e in events).encode())
            else:
                self.wfile.write(b'{"available_count": 1, "access_token": "fixture-only"}')

        do_POST = do_GET

    httpd = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{httpd.server_port}', seen
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)
        assert not thread.is_alive()


def invoke(kind, base, home):
    base += '/selected'
    if kind == 'oauth':
        # Transport fixtures intentionally use HTTP loopback; business URLs require HTTPS.
        return codex_direct._request_json('POST', base + '/oauth/token', data={'refresh_token': 'fixture-refresh'}, timeout=2)[0]
    if kind == 'codex':
        return codex_direct._request_json('GET', base + '/wham/usage', headers={'Authorization': 'Bearer fixture-access'}, timeout=2)[0]
    if kind == 'reset':
        return reset_credits._http('POST', base + '/wham/rate-limit-reset-credits/consume', {'Authorization': 'Bearer fixture-access'}, {'redeem_request_id': 'fixture-id'}, 2)[0]
    if kind == 'local':
        return local._request_status(base, '/health', headers={'Authorization': 'Bearer fixture-access'}, timeout=2)[0]
    client = remote.CrsHttpClient(remote.CrsProfile(base, api_key='fixture-access'), timeout=2, home=home)
    if kind == 'remote-json':
        return client.key_info()['status']
    try:
        return client.responses_smoke(model='fixture-model')['status']
    except urllib.error.HTTPError as exc:
        return exc.code


KINDS = ['oauth', 'codex', 'reset', 'local', 'remote-json', 'remote-sse']


@pytest.mark.parametrize('kind', KINDS)
def test_all_http_ignores_environment_and_system_proxies(kind, tmp_path, monkeypatch):
    with ExitStack() as stack:
        target, target_calls = stack.enter_context(server())
        proxy, proxy_calls = stack.enter_context(server(status=502))
        for name in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
            monkeypatch.setenv(name, proxy)
        for name in ['NO_PROXY', 'no_proxy']:
            monkeypatch.setenv(name, '')
        # Covers OS proxy discovery too, independently of the host's OS/config.
        monkeypatch.setattr(urllib.request, 'getproxies', lambda: {'http': proxy, 'https': proxy, 'all': proxy})
        monkeypatch.setattr(urllib.request, '_opener', None)
        assert invoke(kind, target, tmp_path) == 200
        assert proxy_calls == []
        assert len(target_calls) == 1
        assert target_calls[0][1].startswith('/selected/')


@pytest.mark.parametrize('kind', KINDS)
@pytest.mark.parametrize('status', [302, 307, 503])
def test_http_never_redirects_credentials_or_replays_on_failure(kind, status, tmp_path, monkeypatch):
    with ExitStack() as stack:
        other, other_calls = stack.enter_context(server())
        target, calls = stack.enter_context(server(status=status, redirect=other + '/leak'))
        monkeypatch.setattr(urllib.request, 'getproxies', lambda: {})
        monkeypatch.setattr(urllib.request, '_opener', None)
        assert invoke(kind, target, tmp_path) == status
        assert len(calls) == 1
        assert other_calls == []
