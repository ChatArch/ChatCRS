import pytest


def api():
    from chatcrs import reset_credits
    return reset_credits


def test_client_uses_separate_configured_base_and_explicit_write():
    m = api(); calls=[]
    def transport(method, url, headers, body, timeout):
        calls.append((method,url,body))
        return 200, {'available_count':2,'credits':[]} if method=='GET' else {'code':'reset','windows_reset':2}
    c=m.CodexResetClient('token-secret','account-secret','https://relay.example/backend-api',reset_base_url='https://chatgpt.com/backend-api',transport=transport)
    c.usage(); c.reset_credits()
    assert calls[0][1]=='https://relay.example/backend-api/wham/usage'
    assert calls[1][1]=='https://chatgpt.com/backend-api/wham/rate-limit-reset-credits'
    c.consume('request-one')
    assert len(calls)==2
    c.consume('request-one',execute=True,credit_id='selected')
    assert calls[-1]==('POST','https://chatgpt.com/backend-api/wham/rate-limit-reset-credits/consume',{'redeem_request_id':'request-one','credit_id':'selected'})
    assert 'token-secret' not in repr(c) and 'account-secret' not in repr(c)


@pytest.mark.parametrize('base',['http://evil.example','https://u:p@example.com','https://example.com/?token=x','https://example.com/#part'])
def test_unsafe_base_rejected(base):
    with pytest.raises(ValueError): api().CodexResetClient('t','a',base)


def test_error_output_has_no_body_secret():
    m=api()
    c=m.CodexResetClient('secret','acct','https://example.com',transport=lambda *args:(403,{'detail':{'code':'rate_limit_reset_ineligible','message':'secret@example.com'}}))
    with pytest.raises(m.SafeResetError) as error: c.reset_credits()
    assert 'secret@example.com' not in str(error.value)
    assert error.value.status==403


def test_missing_request_id_never_sends():
    c=api().CodexResetClient('t','a','https://example.com',transport=lambda *a:pytest.fail('must not send'))
    with pytest.raises(ValueError): c.consume('',execute=True)


def test_safe_summary_whitelists_and_redacts():
    m=api()
    data=m.summarize_credits({'available_count':1,'credits':[{'id':'private-credit','profile_user_id':'secret-user','email':'private@example.com','status':'available','expires_at':'2030-01-01T00:00:00Z'}]})
    assert data['available_count']==1
    assert 'private-credit' not in str(data) and 'secret-user' not in str(data) and 'private@example.com' not in str(data)


def test_cli_registered_reset_tree():
    from click.testing import CliRunner
    from chatcrs.cli import main
    result=CliRunner().invoke(main,['--tree-brief'])
    assert result.exit_code==0
    assert 'reset' in result.output and 'consume' in result.output


def test_operator_receipt_blocks_duplicate_post_and_verifies_usage(tmp_path, monkeypatch):
    m = api()
    class Client:
        identity = 'stable-account-hash'
        calls = 0
        def reset_credits(self): return {'available_count': 2 - self.calls, 'credits': []}
        def usage(self): return {'rate_limit': {'primary_window': {'used_percent': 0 if self.calls else 99}}}
        def consume(self, request_id, execute=False):
            assert execute is True
            self.calls += 1
            return {'code': 'reset', 'windows_reset': 1}
    client = Client()
    monkeypatch.setattr(m.CodexResetClient, 'from_profile', lambda *a, **k: client)
    first = m.consume_reset_credit(profile='work', request_id='op', execute=True, home=tmp_path)
    second = m.consume_reset_credit(profile='work', request_id='op', execute=True, home=tmp_path)
    assert first['state'] == 'verified'
    assert second['code'] == 'already_attempted'
    assert client.calls == 1


def test_operator_does_not_call_unchanged_usage_verified(tmp_path, monkeypatch):
    m = api()
    class Client:
        identity = 'stable-account-hash'
        calls = 0
        def reset_credits(self): return {'available_count': 2 - self.calls, 'credits': []}
        def usage(self): return {'rate_limit': {'primary_window': {'used_percent': 99}}}
        def consume(self, request_id, execute=False):
            self.calls += 1
            return {'code': 'reset', 'windows_reset': 1}
    monkeypatch.setattr(m.CodexResetClient, 'from_profile', lambda *a, **k: Client())
    result = m.consume_reset_credit(profile='work', request_id='op', execute=True, home=tmp_path)
    assert result['ok'] is False
    assert result['state'] != 'verified'


def test_operator_dry_run_never_loads_real_profile(monkeypatch):
    m = api()
    monkeypatch.setattr(m.CodexResetClient, 'from_profile', lambda *a, **k: pytest.fail('No credential reads for dry-run'))
    result = m.consume_reset_credit(profile='unconfigured', request_id='plan-only')
    assert result['code'] == 'dry_run'
