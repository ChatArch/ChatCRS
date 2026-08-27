import json
import base64
from datetime import datetime, timezone
from pathlib import Path

import pytest
from chatenv import EnvStore, TokenRefreshResult, TokenStore
from chatcrs.config import CodexConfig
from chatenv.token_refreshers import refresh_token
from click.testing import CliRunner
import chatenv.token_refreshers as chatenv_refreshers

from chatcrs.cli import main


def jwt_with_account(account_id: str, *, exp: int | None = None) -> str:
    def encode(payload: dict) -> str:
        encoded = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
        return encoded.rstrip("=")

    claims = {"https://api.openai.com/auth": {"chatgpt_account_id": account_id, "chatgpt_plan_type": "pro"}}
    if exp is not None:
        claims["exp"] = exp
    return ".".join(
        [
            encode({"alg": "RS256", "typ": "JWT"}),
            encode(claims),
            "signature",
        ]
    )


class FakeCodexTransport:
    def __init__(self):
        self.calls = []

    def __call__(self, method, url, *, data=None, json_data=None, headers=None, timeout=20.0):
        self.calls.append({"method": method, "url": url, "data": data, "json_data": json_data, "headers": headers or {}, "timeout": timeout})
        if url == "https://auth.openai.com/oauth/token":
            assert method == "POST"
            assert data["grant_type"] == "refresh_token"
            assert data["refresh_token"] == "refresh-secret"
            return 200, {
                "access_token": "access-secret",
                "refresh_token": "rotated-refresh-secret",
                "expires_in": 3600,
                "token_type": "Bearer",
            }, {}
        if url == "https://auth.openai.com/api/accounts":
            assert headers["authorization"] == "Bearer access-secret"
            return 200, {
                "accounts": [
                    {
                        "id": "acct_123",
                        "email": "user@example.com",
                        "plan_type": "pro",
                        "refresh_token": "must-not-leak",
                    }
                ]
            }, {}
        if url == "https://chatgpt.com/backend-api/codex/responses":
            assert method == "POST"
            assert headers["authorization"] == "Bearer access-secret"
            assert headers["ChatGPT-Account-ID"] == "acct_123"
            assert headers["originator"] == "codex_cli_rs"
            assert headers["user-agent"].startswith("codex_cli_rs/")
            assert isinstance(json_data, dict)
            assert json_data["model"] == "gpt-5.5"
            assert json_data["store"] is False
            assert json_data["stream"] is True
            assert "max_output_tokens" not in json_data
            return 200, None, {
                "x-codex-primary-used-percent": "12.5",
                "x-codex-primary-reset-after-seconds": "1800",
                "x-codex-primary-window-minutes": "300",
                "x-codex-secondary-used-percent": "3",
            }
        if url == "https://chatgpt.com/backend-api/wham/usage":
            assert headers["authorization"] == "Bearer access-secret"
            assert headers["ChatGPT-Account-ID"] == "acct_123"
            assert headers["originator"] == "codex_cli_rs"
            assert headers["user-agent"].startswith("codex_cli_rs/")
            assert headers["accept"] == "application/json"
            return 200, {
                "summary": {"tokens": 42},
                "daily_usage_buckets": [{"start_date": "2026-08-12", "tokens": 42}],
            }, {
                "x-codex-primary-used-percent": "12.5",
                "x-codex-primary-reset-after-seconds": "1800",
                "x-codex-primary-window-minutes": "300",
                "x-codex-secondary-used-percent": "3",
            }
        raise AssertionError(f"unexpected request {method} {url}")


def test_codex_chatenv_refresh_provider_uses_registered_codex_profile_without_writing_store(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    env_store.save_profile(
        CodexConfig,
        "wzh",
        {
            "OPENAI_REFRESH_TOKEN": "refresh-secret",
            "OPENAI_OAUTH_BASE_URL": "https://auth.openai.com",
        },
    )
    transport = FakeCodexTransport()
    monkeypatch.setattr(codex_direct, "_request_json", transport)

    result = codex_direct.refresh_chatenv_token(
        service="Codex",
        profile="wzh",
        home=home,
        env_store=env_store,
    )

    assert result.token_type == "openai_codex_oauth"
    assert result.values["access_token"] == "access-secret"
    assert result.values["refresh_token"] == "rotated-refresh-secret"
    assert result.summary["provider"] == "Codex"
    assert result.summary["profile"] == "wzh"
    assert result.summary["access_token_present"] is True
    assert result.summary["refresh_token_present"] is True
    assert result.summary["refresh_token_rotated"] is True
    dumped_summary = json.dumps(result.summary, ensure_ascii=False)
    assert "access-secret" not in dumped_summary
    assert "refresh-secret" not in dumped_summary
    assert not (home / "tokens" / "Codex" / "wzh.json").exists()
    assert not (home / "tokens" / "OpenAI" / "wzh.json").exists()


def test_codex_chatenv_refresh_provider_prefers_rotated_token_store_refresh(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    env_store.save_profile(CodexConfig, "wzh", {"OPENAI_REFRESH_TOKEN": "old-profile-refresh"})
    TokenStore(home=home).write(
        "Codex",
        "wzh",
        values={"refresh_token": "refresh-secret", "account_id": "acct_123", "account_label": "wzh"},
        token_type="openai_codex_oauth",
        summary={"refresh_token_present": True, "account_id_present": True},
    )
    transport = FakeCodexTransport()
    monkeypatch.setattr(codex_direct, "_request_json", transport)

    result = codex_direct.refresh_chatenv_token(service="Codex", profile="wzh", home=home, env_store=env_store)

    assert result.values["access_token"] == "access-secret"
    assert result.values["refresh_token"] == "rotated-refresh-secret"
    assert result.values["account_id"] == "acct_123"
    assert result.values["account_label"] == "wzh"
    assert result.summary["account_id_present"] is True
    assert transport.calls[0]["data"]["refresh_token"] == "refresh-secret"


def test_codex_chatenv_refresh_derives_account_id_from_access_token_claims(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    env_store.save_profile(CodexConfig, "wzh", {"OPENAI_REFRESH_TOKEN": "refresh-secret"})

    def refresh_transport(method, url, *, data=None, json_data=None, headers=None, timeout=20.0):
        assert url == "https://auth.openai.com/oauth/token"
        assert data["refresh_token"] == "refresh-secret"
        return 200, {"access_token": jwt_with_account("acct_123"), "expires_in": 3600}, {}

    monkeypatch.setattr(codex_direct, "_request_json", refresh_transport)

    result = codex_direct.refresh_chatenv_token(service="Codex", profile="wzh", home=home, env_store=env_store)

    assert result.values["account_id"] == "acct_123"
    assert result.values["refresh_token"] == "refresh-secret"
    assert result.summary["account_id_present"] is True
    assert result.summary["account_id_hash"] == "182d1cfdc619"
    assert result.summary["refresh_token_source"] == "env_profile"
    assert result.summary["refresh_fallback_attempts"] == 0
    assert "acct_123" not in json.dumps(result.summary, ensure_ascii=False)
    assert "refresh-secret" not in json.dumps(result.summary, ensure_ascii=False)


def test_codex_chatenv_refresh_falls_back_to_env_refresh_token(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    env_store.save_profile(CodexConfig, "wzh", {"OPENAI_REFRESH_TOKEN": "profile-refresh"})
    TokenStore(home=home).write(
        "Codex",
        "wzh",
        values={"refresh_token": "stale-token-store-refresh"},
        token_type="openai_codex_oauth",
        summary={"refresh_token_present": True},
    )
    seen_refresh_tokens = []

    def refresh_transport(method, url, *, data=None, json_data=None, headers=None, timeout=20.0):
        assert url == "https://auth.openai.com/oauth/token"
        seen_refresh_tokens.append(data["refresh_token"])
        if data["refresh_token"] == "stale-token-store-refresh":
            return 401, {"error": "invalid_grant"}, {}
        assert data["refresh_token"] == "profile-refresh"
        return 200, {"access_token": jwt_with_account("acct_123"), "expires_in": 3600}, {}

    monkeypatch.setattr(codex_direct, "_request_json", refresh_transport)

    result = codex_direct.refresh_chatenv_token(service="Codex", profile="wzh", home=home, env_store=env_store)

    assert seen_refresh_tokens == ["stale-token-store-refresh", "profile-refresh"]
    assert result.values["refresh_token"] == "profile-refresh"
    assert result.values["account_id"] == "acct_123"
    assert result.summary["refresh_token_source"] == "env_profile"
    assert result.summary["refresh_fallback_attempts"] == 1
    dumped_summary = json.dumps(result.summary, ensure_ascii=False)
    assert "stale-token-store-refresh" not in dumped_summary
    assert "profile-refresh" not in dumped_summary


def test_codex_usage_auto_refreshes_expired_access_and_uses_claim_account_id(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    env_store.save_profile(CodexConfig, "wzh", {"OPENAI_REFRESH_TOKEN": "refresh-secret"})
    TokenStore(home=home).write(
        "Codex",
        "wzh",
        values={"access_token": jwt_with_account("acct_123", exp=946684800), "refresh_token": "refresh-secret"},
        token_type="openai_codex_oauth",
        summary={"access_token_present": True, "refresh_token_present": True},
    )
    called_urls = []

    def refresh_and_save(*, profile="default", home=None):
        result = codex_direct.refresh_chatenv_token(service="Codex", profile=profile, home=home, env_store=env_store)
        TokenStore(home=home).write(
            "Codex",
            profile,
            values=result.values,
            token_type=result.token_type,
            summary=result.summary,
            expires_at=result.expires_at,
            source="refresh",
        )
        return {"source": "refresh", "token_present": True, "summary": result.summary}

    def transport(method, url, *, data=None, json_data=None, headers=None, timeout=20.0):
        called_urls.append(url)
        if url == "https://auth.openai.com/oauth/token":
            assert data["refresh_token"] == "refresh-secret"
            return 200, {"access_token": jwt_with_account("acct_123"), "expires_in": 3600}, {}
        if url == "https://chatgpt.com/backend-api/wham/usage":
            assert headers["authorization"].startswith("Bearer ")
            assert headers["ChatGPT-Account-ID"] == "acct_123"
            return 200, {"summary": {"tokens": 42}}, {}
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(codex_direct, "refresh_codex_profile_token", refresh_and_save)
    monkeypatch.setattr(codex_direct, "_request_json", transport)

    payload = codex_direct.inspect_usage(profile="wzh", home=home, refresh=True)

    assert payload["ok"] is True
    assert payload["account_resolution"]["source"] == "token_store_account_id"
    assert payload["account_id_hash"] == "182d1cfdc619"
    assert called_urls == ["https://auth.openai.com/oauth/token", "https://chatgpt.com/backend-api/wham/usage"]
    stored = json.loads((home / "tokens" / "Codex" / "wzh.json").read_text(encoding="utf-8"))
    assert stored["values"]["account_id"] == "acct_123"
    assert "acct_123" not in json.dumps(payload, ensure_ascii=False)


def test_chatenv_refresh_writes_codex_provider_result_without_openai_namespace(monkeypatch, tmp_path: Path):
    home = tmp_path / "chatarch"

    def fake_provider(**kwargs):
        return TokenRefreshResult(
            values={"access_token": "access-secret", "refresh_token": "refresh-secret"},
            token_type="openai_codex_oauth",
            summary={"provider": "Codex", "access_token_present": True, "refresh_token_present": True},
            expires_at="2026-08-12T12:00:00Z",
        )

    chatenv_refreshers.clear_token_refreshers()
    monkeypatch.setitem(chatenv_refreshers._token_refreshers, "codex", fake_provider)
    monkeypatch.setattr(chatenv_refreshers, "_loaded", True)

    status = refresh_token("Codex", "wzh", home=home)
    saved = json.loads((home / "tokens" / "Codex" / "wzh.json").read_text(encoding="utf-8"))

    assert status["service"] == "Codex"
    assert status["profile"] == "wzh"
    assert status["token_type"] == "openai_codex_oauth"
    assert status["token_present"] is True
    assert status["source"] == "refresh"
    assert saved["values"]["access_token"] == "access-secret"
    assert not (home / "tokens" / "OpenAI" / "wzh.json").exists()
    assert "access-secret" not in json.dumps(status, ensure_ascii=False)
    assert "refresh-secret" not in json.dumps(status, ensure_ascii=False)


def test_codex_account_can_use_codex_token_store(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    TokenStore(home=home).write(
        "Codex",
        "wzh",
        values={"access_token": "access-secret"},
        token_type="openai_codex_oauth",
        summary={"access_token_present": True},
    )
    transport = FakeCodexTransport()
    monkeypatch.setattr(codex_direct, "_request_json", transport)

    payload = codex_direct.inspect_account(profile="wzh", home=home, refresh=False)

    assert payload["ok"] is True
    assert payload["profile"] == "wzh"
    assert payload["token_service"] == "Codex"
    assert payload["account_count"] == 1
    assert not (home / "tokens" / "OpenAI" / "wzh.json").exists()


def test_codex_usage_can_use_token_store_account_id_without_accounts_api(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    TokenStore(home=home).write(
        "Codex",
        "wzh",
        values={"access_token": "access-secret", "account_id": "acct_123"},
        token_type="openai_codex_oauth",
        summary={"access_token_present": True, "account_id_present": True},
    )
    transport = FakeCodexTransport()
    monkeypatch.setattr(codex_direct, "_request_json", transport)

    payload = codex_direct.inspect_usage(profile="wzh", home=home, refresh=False)

    assert payload["ok"] is True
    assert payload["profile"] == "wzh"
    assert payload["account_id_hash"] == "182d1cfdc619"
    assert "account_id" not in payload
    assert payload["token_service"] == "Codex"
    assert payload["account_resolution"] == {
        "source": "token_store_account_id",
        "account_id_hash": "182d1cfdc619",
    }
    called_urls = [call["url"] for call in transport.calls]
    assert called_urls == ["https://chatgpt.com/backend-api/wham/usage"]
    assert "acct_123" not in json.dumps(payload, ensure_ascii=False)


def test_codex_quota_uses_responses_smoke_and_redacts_account_id(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    TokenStore(home=home).write(
        "Codex",
        "wzh",
        values={"access_token": "access-secret", "account_id": "acct_123"},
        token_type="openai_codex_oauth",
        summary={"access_token_present": True, "account_id_present": True},
    )
    transport = FakeCodexTransport()
    monkeypatch.setattr(codex_direct, "_request_json", transport)

    payload = codex_direct.inspect_quota(profile="wzh", home=home, refresh=False)

    assert payload["ok"] is True
    assert payload["status"] == 200
    assert payload["profile"] == "wzh"
    assert payload["token_service"] == "Codex"
    assert payload["account_id_hash"] == "182d1cfdc619"
    assert payload["account_resolution"]["source"] == "token_store_account_id"
    assert payload["request"] == {"store": False, "stream": True}
    assert payload["model"] == codex_direct.DEFAULT_CODEX_QUOTA_MODEL
    assert payload["has_quota_headers"] is True
    assert payload["rate_limits"]["primary_used_percent"] == 12.5
    assert "account_id" not in payload
    assert "acct_123" not in json.dumps(payload, ensure_ascii=False)
    assert transport.calls[-1]["url"] == "https://chatgpt.com/backend-api/codex/responses"


def test_codex_profile_can_route_auth_accounts_usage_and_quota_through_relay(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    env_store.save_profile(
        CodexConfig,
        "wzh",
        {
            "OPENAI_REFRESH_TOKEN": "refresh-secret",
            "OPENAI_OAUTH_BASE_URL": "https://auth.tencent-am.wzhecnu.cn",
            "CHATGPT_BACKEND_BASE_URL": "https://gpt.tencent-am.wzhecnu.cn/backend-api",
        },
    )
    TokenStore(home=home).write(
        "Codex",
        "wzh",
        values={"refresh_token": "refresh-secret", "account_id": "acct_123"},
        token_type="openai_codex_oauth",
        summary={"refresh_token_present": True, "account_id_present": True},
    )

    def relay_transport(method, url, *, data=None, json_data=None, headers=None, timeout=20.0):
        if url == "https://auth.tencent-am.wzhecnu.cn/oauth/token":
            return 200, {"access_token": "access-secret", "refresh_token": "rotated-refresh-secret", "expires_in": 3600}, {}
        if url == "https://gpt.tencent-am.wzhecnu.cn/backend-api/wham/usage":
            assert headers["authorization"] == "Bearer access-secret"
            assert headers["ChatGPT-Account-ID"] == "acct_123"
            return 200, {"summary": {"tokens": 42}, "email": "user@example.com", "user_id": "user_123", "account_id": "acct_123"}, {}
        if url == "https://gpt.tencent-am.wzhecnu.cn/backend-api/codex/responses":
            assert headers["authorization"] == "Bearer access-secret"
            assert headers["ChatGPT-Account-ID"] == "acct_123"
            return 200, {}, {"x-codex-primary-used-percent": "7", "x-codex-primary-window-minutes": "10080"}
        raise AssertionError(f"unexpected relay request {method} {url}")

    monkeypatch.setattr(codex_direct, "_request_json", relay_transport)

    refresh_payload = codex_direct.refresh_chatenv_token(service="Codex", profile="wzh", home=home, env_store=env_store)
    TokenStore(home=home).write("Codex", "wzh", values=refresh_payload.values | {"account_id": "acct_123"}, token_type="openai_codex_oauth")
    usage = codex_direct.inspect_usage(profile="wzh", home=home)
    quota = codex_direct.inspect_quota(profile="wzh", home=home)

    assert refresh_payload.summary["oauth_base_url_hash"] == codex_direct._base_url_hash("https://auth.tencent-am.wzhecnu.cn")
    assert usage["ok"] is True
    assert usage["usage_url"] == "https://gpt.tencent-am.wzhecnu.cn/backend-api/wham/usage"
    assert usage["account_id_hash"] == "182d1cfdc619"
    assert "acct_123" not in json.dumps(usage, ensure_ascii=False)
    assert "user@example.com" not in json.dumps(usage, ensure_ascii=False)
    assert quota["ok"] is True
    assert quota["responses_url"] == "https://gpt.tencent-am.wzhecnu.cn/backend-api/codex/responses"


def test_codex_usage_can_resolve_unique_account_from_profile(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    TokenStore(home=home).write(
        "Codex",
        "wzh",
        values={"access_token": "access-secret"},
        token_type="openai_codex_oauth",
        summary={"access_token_present": True},
    )
    transport = FakeCodexTransport()
    monkeypatch.setattr(codex_direct, "_request_json", transport)

    payload = codex_direct.inspect_usage(profile="wzh", home=home, refresh=False)

    assert payload["ok"] is True
    assert payload["profile"] == "wzh"
    assert payload["account_id_hash"] == "182d1cfdc619"
    assert "account_id" not in payload
    assert payload["token_service"] == "Codex"
    assert payload["account_resolution"] == {
        "source": "profile_account_metadata",
        "account_count": 1,
        "status": 200,
        "account_id_hash": "182d1cfdc619",
    }
    called_urls = [call["url"] for call in transport.calls]
    assert called_urls == ["https://auth.openai.com/api/accounts", "https://chatgpt.com/backend-api/wham/usage"]
    assert "acct_123" not in json.dumps(payload, ensure_ascii=False)


def test_codex_usage_resolves_account_id_from_access_token_claims(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    TokenStore(home=home).write(
        "Codex",
        "wzh",
        values={"access_token": jwt_with_account("acct_123")},
        token_type="openai_codex_oauth",
        summary={"access_token_present": True},
    )
    called_urls = []

    def usage_only_transport(method, url, *, data=None, json_data=None, headers=None, timeout=20.0):
        called_urls.append(url)
        assert url == "https://chatgpt.com/backend-api/wham/usage"
        assert headers["ChatGPT-Account-ID"] == "acct_123"
        return 200, {"summary": {"tokens": 42}}, {}

    monkeypatch.setattr(codex_direct, "_request_json", usage_only_transport)

    payload = codex_direct.inspect_usage(profile="wzh", home=home, refresh=False)

    assert payload["ok"] is True
    assert payload["account_resolution"] == {"source": "access_token_claims", "account_id_hash": "182d1cfdc619"}
    assert called_urls == ["https://chatgpt.com/backend-api/wham/usage"]
    assert "acct_123" not in json.dumps(payload, ensure_ascii=False)


def test_codex_usage_refreshes_and_retries_after_unauthorized_response(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    TokenStore(home=home).write(
        "Codex",
        "wzh",
        values={"access_token": "revoked-access", "refresh_token": "refresh-secret", "account_id": "acct_123"},
        token_type="openai_codex_oauth",
        summary={"access_token_present": True, "refresh_token_present": True, "account_id_present": True},
    )
    usage_calls = 0

    def refresh_and_save(*, profile="default", home=None):
        TokenStore(home=home).write(
            "Codex",
            profile,
            values={"access_token": jwt_with_account("acct_123"), "refresh_token": "refresh-secret", "account_id": "acct_123"},
            token_type="openai_codex_oauth",
            summary={"access_token_present": True, "refresh_token_present": True, "account_id_present": True},
            expires_at="2099-01-01T00:00:00Z",
            source="refresh",
        )
        return {"source": "refresh", "token_present": True}

    def usage_transport(method, url, *, data=None, json_data=None, headers=None, timeout=20.0):
        nonlocal usage_calls
        assert url == "https://chatgpt.com/backend-api/wham/usage"
        usage_calls += 1
        if usage_calls == 1:
            assert headers["authorization"] == "Bearer revoked-access"
            return 401, {"error": "unauthorized"}, {}
        assert headers["authorization"] != "Bearer revoked-access"
        assert headers["ChatGPT-Account-ID"] == "acct_123"
        return 200, {"summary": {"tokens": 42}}, {}

    monkeypatch.setattr(codex_direct, "refresh_codex_profile_token", refresh_and_save)
    monkeypatch.setattr(codex_direct, "_request_json", usage_transport)

    payload = codex_direct.inspect_usage(profile="wzh", home=home, refresh=True)

    assert usage_calls == 2
    assert payload["ok"] is True
    assert payload["refresh"] == {"source": "refresh", "token_present": True}
    assert payload["account_resolution"]["source"] == "token_store_account_id"
    assert "revoked-access" not in json.dumps(payload, ensure_ascii=False)


def test_codex_usage_refuses_ambiguous_profile_accounts(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    TokenStore(home=home).write(
        "Codex",
        "wzh",
        values={"access_token": "access-secret"},
        token_type="openai_codex_oauth",
        summary={"access_token_present": True},
    )

    def multi_account_transport(method, url, *, data=None, headers=None, timeout=20.0):
        assert url == "https://auth.openai.com/api/accounts"
        return 200, {"accounts": [{"id": "acct_1"}, {"id": "acct_2"}]}, {}

    monkeypatch.setattr(codex_direct, "_request_json", multi_account_transport)

    with pytest.raises(ValueError, match="pass --account-id explicitly"):
        codex_direct.inspect_usage(profile="wzh", home=home, refresh=False)


def test_codex_refresh_access_token_redacts_and_returns_rotated_refresh(monkeypatch):
    from chatcrs import codex_direct

    transport = FakeCodexTransport()
    monkeypatch.setattr(codex_direct, "_request_json", transport)

    payload = codex_direct.refresh_access_token(refresh_token="refresh-secret", client_id="client-123", timeout=9.0)

    assert payload["ok"] is True
    assert payload["mutated"] is False
    assert payload["token_present"] is True
    assert payload["refresh_token_rotated"] is True
    assert payload["values"]["access_token"] == "access-secret"
    assert payload["values"]["refresh_token"] == "rotated-refresh-secret"
    assert "access-secret" not in json.dumps(payload["safe"], ensure_ascii=False)
    assert "refresh-secret" not in json.dumps(payload["safe"], ensure_ascii=False)


def test_codex_account_and_usage_use_access_token_without_leaking(monkeypatch):
    from chatcrs import codex_direct

    transport = FakeCodexTransport()
    monkeypatch.setattr(codex_direct, "_request_json", transport)

    account = codex_direct.get_account(access_token="access-secret", timeout=5.0)
    usage = codex_direct.get_usage(access_token="access-secret", account_id="acct_123", timeout=5.0)

    assert account["ok"] is True
    assert account["account_count"] == 1
    assert account["accounts"][0]["account_id_hash"] == "182d1cfdc619"
    assert account["accounts"][0]["email_hash"] == "b4c9a289323b"
    assert account["accounts"][0]["plan_type"] == "pro"
    assert account["accounts_api"] == {"ok": True, "status": 200, "account_count": 1, "body_redacted": None, "body_kind": "dict"}
    dumped_account = json.dumps(account, ensure_ascii=False)
    assert "acct_123" not in dumped_account
    assert "user@example.com" not in dumped_account
    assert "must-not-leak" not in dumped_account
    assert usage["ok"] is True
    assert usage["account_id_hash"] == "182d1cfdc619"
    assert "account_id" not in usage
    assert usage["rate_limits"]["primary_used_percent"] == 12.5
    assert usage["rate_limits"]["primary_reset_after_seconds"] == 1800.0
    combined = json.dumps({"account": account, "usage": usage}, ensure_ascii=False)
    assert "access-secret" not in combined
    assert "must-not-leak" not in combined
    assert "acct_123" not in json.dumps(usage, ensure_ascii=False)


def test_codex_account_redacts_identity_from_unexpected_accounts_api_body(monkeypatch):
    from chatcrs import codex_direct

    def identity_body_transport(method, url, *, data=None, json_data=None, headers=None, timeout=20.0):
        assert url == "https://auth.openai.com/api/accounts"
        return 200, {
            "message": "account acct_123 for user@example.com user_123 123e4567-e89b-12d3-a456-426614174000",
            "account_id": "acct_123",
            "accountId": "acct_456",
            "user_id": "user_123",
            "email": "user@example.com",
            "refresh_token": "must-not-leak",
        }, {}

    monkeypatch.setattr(codex_direct, "_request_json", identity_body_transport)

    payload = codex_direct.get_account(access_token="access-secret")
    dumped = json.dumps(payload, ensure_ascii=False)

    assert payload["accounts_api"]["body_redacted"] is not None
    assert "acct_123" not in dumped
    assert "acct_456" not in dumped
    assert "user_123" not in dumped
    assert "user@example.com" not in dumped
    assert "123e4567-e89b-12d3-a456-426614174000" not in dumped
    assert "must-not-leak" not in dumped


def test_codex_quota_redacts_identity_from_non_200_body(monkeypatch):
    from chatcrs import codex_direct

    def quota_error_transport(method, url, *, data=None, json_data=None, headers=None, timeout=20.0):
        assert url == "https://chatgpt.com/backend-api/codex/responses"
        return 403, {
            "error": "account acct_123 user@example.com user_123 123e4567-e89b-12d3-a456-426614174000",
            "account_id": "acct_123",
            "userId": "user_123",
            "emailAddress": "user@example.com",
            "access_token": "must-not-leak",
        }, {}

    monkeypatch.setattr(codex_direct, "_request_json", quota_error_transport)

    payload = codex_direct.get_quota(access_token="access-secret", account_id="acct_123")
    dumped = json.dumps(payload, ensure_ascii=False)

    assert payload["ok"] is False
    assert payload["body"] is not None
    assert payload["account_id_hash"] == "182d1cfdc619"
    assert "acct_123" not in dumped
    assert "user_123" not in dumped
    assert "user@example.com" not in dumped
    assert "123e4567-e89b-12d3-a456-426614174000" not in dumped
    assert "must-not-leak" not in dumped


def test_codex_cli_surface_is_registered():
    result = CliRunner().invoke(main, ["--tree"])

    assert result.exit_code == 0, result.output
    assert "codex  # Direct OpenAI Codex account token and usage helpers." in result.output
    assert "refresh [--profile PROFILE]" in result.output
    assert "account [--profile PROFILE]" in result.output
    assert "quota [--profile PROFILE]" in result.output
    assert "usage [--profile PROFILE]" in result.output
    help_result = CliRunner().invoke(main, ["codex", "usage", "--help"])
    assert help_result.exit_code == 0, help_result.output
    assert "envs/Codex" in help_result.output
    assert "tokens/Codex" in help_result.output


def test_codex_cli_token_refresh_uses_profile_oauth_base_url(monkeypatch, tmp_path: Path):
    from chatcrs import cli

    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    env_store.save_profile(
        CodexConfig,
        "wzh",
        {
            "OPENAI_REFRESH_TOKEN": "profile-refresh",
            "OPENAI_OAUTH_BASE_URL": "https://auth.tencent-am.wzhecnu.cn",
        },
    )
    TokenStore(home=home).write(
        "Codex",
        "wzh",
        values={"refresh_token": "refresh-secret"},
        token_type="openai_codex_oauth",
        summary={"refresh_token_present": True},
    )
    called = {}

    monkeypatch.setattr(cli.codex_direct, "read_stored_token", lambda *, profile="default": TokenStore(home=home).read("Codex", profile))
    monkeypatch.setattr(cli.codex_direct, "_codex_profile_values_or_empty", lambda *, profile, home=None: {"OPENAI_OAUTH_BASE_URL": "https://auth.tencent-am.wzhecnu.cn"})

    def fake_refresh_access_token(*, refresh_token, client_id=None, oauth_base_url=None, timeout=20.0):
        called.update({"refresh_token": refresh_token, "client_id": client_id, "oauth_base_url": oauth_base_url, "timeout": timeout})
        return {
            "ok": True,
            "status": 200,
            "values": {"access_token": "access-secret"},
            "safe": {"ok": True, "status": 200, "oauth_base_url_hash": "safe-hash", "token_present": True},
        }

    monkeypatch.setattr(cli.codex_direct, "refresh_access_token", fake_refresh_access_token)

    result = CliRunner().invoke(main, ["codex", "token", "refresh", "--profile", "wzh", "--json-output"])

    assert result.exit_code == 0, result.output
    assert called == {"refresh_token": "refresh-secret", "client_id": None, "oauth_base_url": "https://auth.tencent-am.wzhecnu.cn", "timeout": 20.0}
    assert "refresh-secret" not in result.output
    assert "access-secret" not in result.output


def test_codex_cli_quota_calls_python_api_without_leaking_account_id(monkeypatch):
    from chatcrs import cli

    called = {}

    def fake_quota(*, profile, account_id, access_token, refresh, client_id, model, timeout):
        called.update(
            {
                "profile": profile,
                "account_id": account_id,
                "access_token": access_token,
                "refresh": refresh,
                "client_id": client_id,
                "model": model,
                "timeout": timeout,
            }
        )
        return {
            "ok": True,
            "mutated": False,
            "status": 200,
            "profile": profile,
            "account_id_hash": "182d1cfdc619",
            "token_service": "Codex",
            "account_resolution": {"source": "token_store_account_id", "account_id_hash": "182d1cfdc619"},
            "rate_limits": {"primary_used_percent": 12.5, "primary_reset_after_seconds": 1800.0},
            "has_quota_headers": True,
        }

    monkeypatch.setattr(cli.codex_direct, "inspect_quota", fake_quota)

    result = CliRunner().invoke(
        main,
        ["codex", "quota", "--profile", "wzh", "--json-output"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["account_id_hash"] == "182d1cfdc619"
    assert payload["account_resolution"]["source"] == "token_store_account_id"
    assert "acct_123" not in result.output
    assert called == {
        "profile": "wzh",
        "account_id": None,
        "access_token": None,
        "refresh": True,
        "client_id": None,
        "model": "gpt-5.5",
        "timeout": 20.0,
    }


def test_codex_cli_usage_allows_profile_only_when_account_can_be_resolved(monkeypatch):
    from chatcrs import cli

    called = {}

    def fake_usage(*, profile, account_id, access_token, refresh, client_id, timeout):
        called.update(
            {
                "profile": profile,
                "account_id": account_id,
                "access_token": access_token,
                "refresh": refresh,
                "client_id": client_id,
                "timeout": timeout,
            }
        )
        return {
            "ok": True,
            "mutated": False,
            "status": 200,
            "account_id_hash": "182d1cfdc619",
            "token_service": "Codex",
            "account_resolution": {"source": "profile_account_metadata", "account_count": 1, "status": 200, "account_id_hash": "182d1cfdc619"},
            "rate_limits": {"primary_used_percent": 10.0},
        }

    monkeypatch.setattr(cli.codex_direct, "inspect_usage", fake_usage)

    result = CliRunner().invoke(
        main,
        ["codex", "usage", "--profile", "wzh", "--json-output"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["account_id_hash"] == "182d1cfdc619"
    assert "account_id" not in payload
    assert "acct_123" not in result.output
    assert payload["account_resolution"]["source"] == "profile_account_metadata"
    assert called == {
        "profile": "wzh",
        "account_id": None,
        "access_token": None,
        "refresh": True,
        "client_id": None,
        "timeout": 20.0,
    }


def test_codex_cli_usage_text_output_uses_account_hash(monkeypatch):
    from chatcrs import cli

    def fake_usage(*, profile, account_id, access_token, refresh, client_id, timeout):
        return {
            "ok": True,
            "mutated": False,
            "status": 200,
            "account_id_hash": "182d1cfdc619",
            "token_service": "Codex",
            "rate_limits": {"primary_used_percent": 10.0},
        }

    monkeypatch.setattr(cli.codex_direct, "inspect_usage", fake_usage)

    result = CliRunner().invoke(main, ["codex", "usage", "--profile", "wzh"])

    assert result.exit_code == 0, result.output
    assert "account_id_hash=182d1cfdc619" in result.output
    assert "account_id=acct_123" not in result.output
    assert "acct_123" not in result.output


def test_codex_cli_usage_calls_python_api(monkeypatch):
    from chatcrs import cli

    called = {}

    def fake_usage(*, profile, account_id, access_token, refresh, client_id, timeout):
        called.update(
            {
                "profile": profile,
                "account_id": account_id,
                "access_token": access_token,
                "refresh": refresh,
                "client_id": client_id,
                "timeout": timeout,
            }
        )
        return {
            "ok": True,
            "mutated": False,
            "status": 200,
            "account_id_hash": "182d1cfdc619",
            "token_service": "Codex",
            "rate_limits": {"primary_used_percent": 10.0},
            "usage": {"summary": {"tokens": 5}},
        }

    monkeypatch.setattr(cli.codex_direct, "inspect_usage", fake_usage)

    result = CliRunner().invoke(
        main,
        [
            "codex",
            "usage",
            "--profile",
            "codex-admin",
            "--account-id",
            "acct_123",
            "--access-token",
            "access-secret",
            "--no-refresh",
            "--json-output",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["token_service"] == "Codex"
    assert "acct_123" not in result.output
    assert "access-secret" not in result.output
    assert called == {
        "profile": "codex-admin",
        "account_id": "acct_123",
        "access_token": "access-secret",
        "refresh": False,
        "client_id": None,
        "timeout": 20.0,
    }
    assert "access-secret" not in result.output
