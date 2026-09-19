"""Exercise real ChatEnv lifecycle with fake OAuth/resource boundaries only."""
import base64
import json
from pathlib import Path

import chatenv.token_refreshers as refreshers
import pytest
from chatenv import EnvStore, TokenStore
from click.testing import CliRunner

from chatcrs import codex_direct as direct, reset_credits as reset
from chatcrs.config import CodexConfig
from chatcrs.cli import main


def token(account='fixture-account', *, exp=4102444800, subject='fixture-user', generation=0):
    claims = {'exp': exp, 'sub': subject, 'generation': generation,
              'https://api.openai.com/auth': {'chatgpt_account_id': account}}
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip('=')
    return 'fixture.' + payload + '.signature'


@pytest.fixture
def lifecycle(tmp_path, monkeypatch):
    home = tmp_path / 'chatarch'
    monkeypatch.setenv('CHATARCH_HOME', str(home))
    for key in ['OPENAI_ACCESS_TOKEN', 'OPENAI_REFRESH_TOKEN', 'CHATGPT_BACKEND_BASE_URL']:
        monkeypatch.setenv(key, 'ambient-must-not-be-used')
    envs = EnvStore(home / 'envs')
    envs.save_profile(CodexConfig, 'work', {
        'OPENAI_REFRESH_TOKEN': 'fixture-bootstrap',
        'OPENAI_OAUTH_BASE_URL': 'https://auth.example.invalid/selected',
        'CHATGPT_BACKEND_BASE_URL': 'https://gpt.example.invalid/selected/backend-api',
    })
    stores = TokenStore(home=home)
    for name in ['work', 'other']:
        stores.write('Codex', name, values={'access_token': token(), 'refresh_token': 'fixture-rotated', 'account_id': 'fixture-account'}, token_type=direct.CODEX_TOKEN_TYPE, summary={})
    stores.write('OpenAI', 'work', values={'access_token': 'unrelated'}, summary={})
    state = {'home': home, 'stores': stores, 'env': envs.profile_path(CodexConfig, 'work'),
             'oauth': [], 'resource': [], 'account': 'fixture-account', 'subject': 'fixture-user',
             'status': 200, 'failure': None}

    def oauth(method, url, *, data=None, **kwargs):
        assert (method, url) == ('POST', 'https://auth.example.invalid/selected/oauth/token')
        state['oauth'].append(data['refresh_token'])
        if state['failure']:
            raise state['failure']
        return state['status'], {'access_token': token(state['account'], subject=state['subject'], generation=1),
                                 'refresh_token': 'fixture-new-refresh', 'expires_in': 3600}, {}

    monkeypatch.setattr(direct, '_request_json', oauth)
    # Keep dispatch/write under ChatEnv rather than emulating TokenStore writes.
    monkeypatch.setattr(refreshers, 'get_token_refresher', lambda service: direct.refresh_chatenv_token if service == 'Codex' else None)

    def resource(method, url, headers, body, timeout):
        state['resource'].append((method, url, headers, body))
        return 200, {'available_count': 2, 'credits': [], 'account_id': 'fixture-account'}

    state['transport'] = resource
    monkeypatch.setattr(reset, '_http', resource)
    return state


def expire(state, *, jwt=False):
    state['stores'].write('Codex', 'work', values={
        'access_token': token(exp=1 if jwt else 4102444800),
        'refresh_token': 'fixture-rotated', 'account_id': 'fixture-account',
    }, summary={}, expires_at='' if jwt else '2000-01-01T00:00:00Z')


@pytest.mark.parametrize('jwt', [False, True])
def test_profile_pre_refresh_persists_rotations_without_changing_env_or_other_stores(lifecycle, jwt):
    s = lifecycle
    expire(s, jwt=jwt)
    before = {p: p.read_bytes() for p in [s['env'], s['home'] / 'tokens/Codex/other.json', s['home'] / 'tokens/OpenAI/work.json']}
    client = reset.CodexResetClient.from_profile('work', home=s['home'])
    client.reset_credits()
    assert s['oauth'] == ['fixture-rotated']
    payload = s['stores'].read('Codex', 'work')
    assert payload['values']['access_token'] == token(generation=1)
    assert payload['values']['refresh_token'] == 'fixture-new-refresh'
    assert payload['expires_at'] and not direct._is_expired(payload['expires_at'])
    assert payload['source'] == 'refresh'
    assert all(p.read_bytes() == content for p, content in before.items())
    assert s['resource'][0][1] == 'https://gpt.example.invalid/selected/backend-api/wham/rate-limit-reset-credits'
    assert s['resource'][0][2]['Authorization'] == 'Bearer ' + token(generation=1)


def test_long_lived_profile_client_rechecks_expiry_before_next_request(lifecycle):
    s = lifecycle
    client = reset.CodexResetClient.from_profile('work', home=s['home'])
    expire(s)
    client.usage()
    assert len(s['oauth']) == 1
    assert s['resource'][0][2]['Authorization'] == 'Bearer ' + token(generation=1)


@pytest.mark.parametrize('second_status', [200, 401])
@pytest.mark.parametrize('method', ['usage', 'reset_credits'])
def test_readonly_401_forces_exactly_one_refresh_retry(lifecycle, second_status, method):
    s = lifecycle
    calls = []

    def transport(verb, url, headers, body, timeout):
        calls.append((verb, url, headers['Authorization']))
        return (401 if len(calls) == 1 else second_status), {'available_count': 1}

    client = reset.CodexResetClient.from_profile('work', home=s['home'], transport=transport)
    if second_status == 401:
        with pytest.raises(reset.SafeResetError):
            getattr(client, method)()
    else:
        getattr(client, method)()
    assert s['oauth'] == ['fixture-rotated']
    assert len(calls) == 2
    assert calls[0][:2] == calls[1][:2]
    assert calls[1][2] == 'Bearer ' + token(generation=1)


def test_no_refresh_diagnostic_is_readonly_and_never_rotates(lifecycle):
    s = lifecycle
    client = reset.CodexResetClient.from_profile('work', home=s['home'], refresh=False,
        transport=lambda *a: (401, {}))
    with pytest.raises(reset.SafeResetError):
        client.reset_credits()
    with pytest.raises(reset.SafeResetError):
        client.consume('fixture-id', execute=True)
    expire(s)
    with pytest.raises(reset.SafeResetError):
        reset.CodexResetClient.from_profile('work', home=s['home'], refresh=False)
    assert s['oauth'] == []


@pytest.mark.parametrize('changed', ['account', 'subject'])
def test_refresh_identity_change_fails_before_store_write_or_resource_request(lifecycle, changed):
    s = lifecycle
    expire(s)
    original = (s['home'] / 'tokens/Codex/work.json').read_bytes()
    s[changed] = 'different-identity'
    with pytest.raises(reset.SafeResetError):
        reset.CodexResetClient.from_profile('work', home=s['home']).reset_credits()
    assert s['resource'] == []
    assert (s['home'] / 'tokens/Codex/work.json').read_bytes() == original


def test_401_refresh_identity_change_never_retries_resource(lifecycle):
    s = lifecycle
    s['account'] = 'different-identity'
    calls = []
    def transport(*args):
        calls.append(args)
        return 401, {}
    client = reset.CodexResetClient.from_profile('work', home=s['home'], transport=transport)
    with pytest.raises(reset.SafeResetError):
        client.reset_credits()
    assert len(s['oauth']) == 1
    assert len(calls) == 1


def test_external_store_identity_change_cannot_retarget_existing_client(lifecycle):
    s = lifecycle
    client = reset.CodexResetClient.from_profile('work', home=s['home'])
    s['stores'].write('Codex', 'work', values={'access_token': token('different'), 'account_id': 'different'}, summary={})
    with pytest.raises(reset.SafeResetError):
        client.usage()
    assert s['resource'] == []


@pytest.mark.parametrize('status', [302, 429, 500, 503])
def test_ambiguous_oauth_failure_does_not_try_bootstrap_or_resource(lifecycle, status):
    s = lifecycle
    expire(s)
    s['status'] = status
    with pytest.raises(reset.SafeResetError):
        reset.CodexResetClient.from_profile('work', home=s['home']).reset_credits()
    assert s['oauth'] == ['fixture-rotated']
    assert s['resource'] == []


def test_oauth_network_failure_is_safe_and_does_not_fall_back(lifecycle):
    s = lifecycle
    expire(s)
    s['failure'] = OSError('fixture-credential-canary')
    with pytest.raises(reset.SafeResetError) as error:
        reset.CodexResetClient.from_profile('work', home=s['home']).reset_credits()
    assert 'fixture-credential-canary' not in str(error.value)
    assert s['oauth'] == ['fixture-rotated']
    assert s['resource'] == []


def test_cli_normal_reset_query_renews_without_manual_refresh(lifecycle):
    s = lifecycle
    expire(s)
    result = CliRunner().invoke(main, ['codex', 'reset', 'list', '--profile', 'work', '--json-output'])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)['available_count'] == 2
    assert s['oauth'] == ['fixture-rotated']
    assert 'fixture-new-refresh' not in result.output


@pytest.mark.parametrize('failure', ['401', 'network', 'readback'])
def test_consume_attempt_is_reserved_and_never_replayed(lifecycle, failure):
    s = lifecycle
    posts = []
    def transport(method, url, headers, body, timeout):
        if method == 'POST':
            audits = list((s['home'] / 'chatcrs/reset-audits').rglob('*.safe.json'))
            assert len(audits) == 1
            assert json.loads(audits[0].read_text())['state'] == 'pending'
            posts.append(body)
            if failure == 'network':
                raise TimeoutError('fixture-credential-canary')
            return (401, {'detail': {'code': 'fixture-credential-canary'}}) if failure == '401' else (200, {'code': 'reset', 'windows_reset': 1})
        if posts:
            raise OSError('fixture-readback-failed')
        return 200, {'available_count': 2, 'account_id': 'fixture-account', 'rate_limit': {'primary_window': {'used_percent': 99}}}
    monkey = pytest.MonkeyPatch()
    with monkey.context() as m:
        m.setattr(reset, '_http', transport)
        first = reset.consume_reset_credit(profile='work', home=s['home'], request_id='persistent-fixture', execute=True)
        assert first['state'] == 'uncertain'
        assert 'fixture-credential-canary' not in Path(first['audit_path']).read_text()
        # Restore reads; a previous pending/uncertain attempt is still reserved.
        m.setattr(reset, '_http', s['transport'])
        second = reset.consume_reset_credit(profile='work', home=s['home'], request_id='persistent-fixture', execute=True)
        assert second['code'] == 'already_attempted'
    assert len(posts) == 1
    assert s['oauth'] == []


def test_upstream_error_code_cannot_smuggle_raw_credential():
    client = reset.CodexResetClient('fixture-canary', 'acct', 'https://example.invalid',
        transport=lambda *a: (403, {'detail': {'code': 'fixture-canary'}}))
    with pytest.raises(reset.SafeResetError) as error:
        client.reset_credits()
    assert 'fixture-canary' not in str(error.value)


def test_oauth_failure_safe_payload_drops_arbitrary_upstream_text(monkeypatch):
    monkeypatch.setattr(direct, '_request_json', lambda *a, **k: (400, {'message': 'fixture-raw-canary'}, {}))
    result = direct.refresh_access_token(refresh_token='fixture')
    assert 'fixture-raw-canary' not in json.dumps(result)


@pytest.mark.parametrize('path', ['usage', 'reset_credits'])
def test_response_account_mismatch_fails_closed(path):
    client = reset.CodexResetClient('fixture', 'acct', 'https://example.invalid',
        transport=lambda *a: (200, {'account_id': 'different', 'available_count': 1}))
    with pytest.raises(reset.SafeResetError):
        getattr(client, path)()


@pytest.mark.parametrize('missing', ['OPENAI_OAUTH_BASE_URL', 'CHATGPT_BACKEND_BASE_URL'])
def test_profile_missing_base_never_falls_back_to_public_endpoint(lifecycle, monkeypatch, missing):
    s = lifecycle
    expire(s)
    store = EnvStore(s['home'] / 'envs')
    config = store.load_profile(CodexConfig, 'work')
    config.pop(missing)
    store.save_profile(CodexConfig, 'work', config)
    original = (s['home'] / 'tokens/Codex/work.json').read_bytes()
    calls = []
    monkeypatch.setattr(direct, '_request_json', lambda *a, **kw: calls.append(a) or (401, {}, {}))
    with pytest.raises(reset.SafeResetError):
        reset.CodexResetClient.from_profile('work', home=s['home'])
    assert calls == []
    assert s['resource'] == []
    assert (s['home'] / 'tokens/Codex/work.json').read_bytes() == original


@pytest.mark.parametrize('options', [{'timeout': 0}, {'reset_base_url': 'http://unsafe.invalid'}])
def test_invalid_client_options_fail_before_oauth_mutation(lifecycle, options):
    s = lifecycle
    expire(s)
    original = (s['home'] / 'tokens/Codex/work.json').read_bytes()
    with pytest.raises((ValueError, reset.SafeResetError)):
        reset.CodexResetClient.from_profile('work', home=s['home'], **options)
    assert s['oauth'] == []
    assert (s['home'] / 'tokens/Codex/work.json').read_bytes() == original


def test_long_lived_profile_cannot_fall_back_after_auth_config_removed(lifecycle, monkeypatch):
    s = lifecycle
    client = reset.CodexResetClient.from_profile('work', home=s['home'])
    expire(s)
    store = EnvStore(s['home'] / 'envs')
    config = store.load_profile(CodexConfig, 'work')
    config.pop('OPENAI_OAUTH_BASE_URL')
    store.save_profile(CodexConfig, 'work', config)
    calls = []
    monkeypatch.setattr(direct, '_request_json', lambda *a, **kw: calls.append(a) or (401, {}, {}))
    with pytest.raises(reset.SafeResetError):
        client.usage()
    assert calls == []
    assert s['resource'] == []


def test_no_refresh_successful_reads_still_forbid_consume(lifecycle):
    s = lifecycle
    original = (s['home'] / 'tokens/Codex/work.json').read_bytes()
    client = reset.CodexResetClient.from_profile('work', home=s['home'], refresh=False)
    assert client.reset_credits()['available_count'] == 2
    with pytest.raises(reset.SafeResetError):
        client.consume('fixture-id', execute=True)
    assert [request[0] for request in s['resource']] == ['GET']
    assert s['oauth'] == []
    assert (s['home'] / 'tokens/Codex/work.json').read_bytes() == original
