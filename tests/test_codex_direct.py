import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from chatenv import EnvStore, OpenAIConfig, TokenRefreshResult, TokenStore
from chatenv.token_refreshers import refresh_token
from click.testing import CliRunner
import chatenv.token_refreshers as chatenv_refreshers

from chatcrs.cli import main


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
        if url == "https://chatgpt.com/backend-api/codex/usage":
            assert headers["authorization"] == "Bearer access-secret"
            assert headers["chatgpt-account-id"] == "acct_123"
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


def test_openai_chatenv_refresh_provider_uses_registered_openai_profile_without_writing_store(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    env_store.save_profile(
        OpenAIConfig,
        "wzh",
        {
            "OPENAI_REFRESH_TOKEN": "refresh-secret",
            "OPENAI_OAUTH_BASE_URL": "https://auth.openai.com",
        },
    )
    transport = FakeCodexTransport()
    monkeypatch.setattr(codex_direct, "_request_json", transport)

    result = codex_direct.refresh_chatenv_token(
        service="OpenAI",
        profile="wzh",
        home=home,
        env_store=env_store,
    )

    assert result.token_type == "openai_oauth"
    assert result.values["access_token"] == "access-secret"
    assert result.values["refresh_token"] == "rotated-refresh-secret"
    assert result.summary["provider"] == "OpenAI"
    assert result.summary["profile"] == "wzh"
    assert result.summary["access_token_present"] is True
    assert result.summary["refresh_token_present"] is True
    assert result.summary["refresh_token_rotated"] is True
    dumped_summary = json.dumps(result.summary, ensure_ascii=False)
    assert "access-secret" not in dumped_summary
    assert "refresh-secret" not in dumped_summary
    assert not (home / "tokens" / "OpenAI" / "wzh.json").exists()
    assert not (home / "tokens" / "Codex" / "wzh.json").exists()


def test_openai_chatenv_refresh_provider_prefers_rotated_token_store_refresh(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    env_store.save_profile(OpenAIConfig, "wzh", {"OPENAI_REFRESH_TOKEN": "old-profile-refresh"})
    TokenStore(home=home).write(
        "OpenAI",
        "wzh",
        values={"refresh_token": "refresh-secret", "account_id": "acct_123", "account_label": "wzh"},
        token_type="openai_oauth",
        summary={"refresh_token_present": True, "account_id_present": True},
    )
    transport = FakeCodexTransport()
    monkeypatch.setattr(codex_direct, "_request_json", transport)

    result = codex_direct.refresh_chatenv_token(service="OpenAI", profile="wzh", home=home, env_store=env_store)

    assert result.values["access_token"] == "access-secret"
    assert result.values["refresh_token"] == "rotated-refresh-secret"
    assert result.values["account_id"] == "acct_123"
    assert result.values["account_label"] == "wzh"
    assert result.summary["account_id_present"] is True
    assert transport.calls[0]["data"]["refresh_token"] == "refresh-secret"


def test_chatenv_refresh_writes_openai_provider_result_without_codex_namespace(monkeypatch, tmp_path: Path):
    home = tmp_path / "chatarch"

    def fake_provider(**kwargs):
        return TokenRefreshResult(
            values={"access_token": "access-secret", "refresh_token": "refresh-secret"},
            token_type="openai_oauth",
            summary={"provider": "OpenAI", "access_token_present": True, "refresh_token_present": True},
            expires_at="2026-08-12T12:00:00Z",
        )

    chatenv_refreshers.clear_token_refreshers()
    monkeypatch.setitem(chatenv_refreshers._token_refreshers, "openai", fake_provider)
    monkeypatch.setattr(chatenv_refreshers, "_loaded", True)

    status = refresh_token("OpenAI", "wzh", home=home)
    saved = json.loads((home / "tokens" / "OpenAI" / "wzh.json").read_text(encoding="utf-8"))

    assert status["service"] == "OpenAI"
    assert status["profile"] == "wzh"
    assert status["token_type"] == "openai_oauth"
    assert status["token_present"] is True
    assert status["source"] == "refresh"
    assert saved["values"]["access_token"] == "access-secret"
    assert not (home / "tokens" / "Codex" / "wzh.json").exists()
    assert "access-secret" not in json.dumps(status, ensure_ascii=False)
    assert "refresh-secret" not in json.dumps(status, ensure_ascii=False)


def test_codex_account_can_use_openai_token_store(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    TokenStore(home=home).write(
        "OpenAI",
        "wzh",
        values={"access_token": "access-secret"},
        token_type="openai_oauth",
        summary={"access_token_present": True},
    )
    transport = FakeCodexTransport()
    monkeypatch.setattr(codex_direct, "_request_json", transport)

    payload = codex_direct.inspect_account(profile="wzh", home=home, refresh=False)

    assert payload["ok"] is True
    assert payload["profile"] == "wzh"
    assert payload["token_service"] == "OpenAI"
    assert payload["account_count"] == 1
    assert not (home / "tokens" / "Codex" / "wzh.json").exists()


def test_codex_usage_can_use_token_store_account_id_without_accounts_api(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    TokenStore(home=home).write(
        "OpenAI",
        "wzh",
        values={"access_token": "access-secret", "account_id": "acct_123"},
        token_type="openai_oauth",
        summary={"access_token_present": True, "account_id_present": True},
    )
    transport = FakeCodexTransport()
    monkeypatch.setattr(codex_direct, "_request_json", transport)

    payload = codex_direct.inspect_usage(profile="wzh", home=home, refresh=False)

    assert payload["ok"] is True
    assert payload["profile"] == "wzh"
    assert payload["account_id"] == "acct_123"
    assert payload["token_service"] == "OpenAI"
    assert payload["account_resolution"] == {
        "source": "token_store_account_id",
        "account_id_hash": "182d1cfdc619",
    }
    called_urls = [call["url"] for call in transport.calls]
    assert called_urls == ["https://chatgpt.com/backend-api/codex/usage"]


def test_codex_quota_uses_responses_smoke_and_redacts_account_id(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    TokenStore(home=home).write(
        "OpenAI",
        "wzh",
        values={"access_token": "access-secret", "account_id": "acct_123"},
        token_type="openai_oauth",
        summary={"access_token_present": True, "account_id_present": True},
    )
    transport = FakeCodexTransport()
    monkeypatch.setattr(codex_direct, "_request_json", transport)

    payload = codex_direct.inspect_quota(profile="wzh", home=home, refresh=False)

    assert payload["ok"] is True
    assert payload["status"] == 200
    assert payload["profile"] == "wzh"
    assert payload["token_service"] == "OpenAI"
    assert payload["account_id_hash"] == "182d1cfdc619"
    assert payload["account_resolution"]["source"] == "token_store_account_id"
    assert payload["request"] == {"store": False, "stream": True}
    assert payload["model"] == codex_direct.DEFAULT_CODEX_QUOTA_MODEL
    assert payload["has_quota_headers"] is True
    assert payload["rate_limits"]["primary_used_percent"] == 12.5
    assert "account_id" not in payload
    assert "acct_123" not in json.dumps(payload, ensure_ascii=False)
    assert transport.calls[-1]["url"] == "https://chatgpt.com/backend-api/codex/responses"


def test_codex_usage_can_resolve_unique_account_from_profile(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    TokenStore(home=home).write(
        "OpenAI",
        "wzh",
        values={"access_token": "access-secret"},
        token_type="openai_oauth",
        summary={"access_token_present": True},
    )
    transport = FakeCodexTransport()
    monkeypatch.setattr(codex_direct, "_request_json", transport)

    payload = codex_direct.inspect_usage(profile="wzh", home=home, refresh=False)

    assert payload["ok"] is True
    assert payload["profile"] == "wzh"
    assert payload["account_id"] == "acct_123"
    assert payload["token_service"] == "OpenAI"
    assert payload["account_resolution"] == {
        "source": "profile_account_metadata",
        "account_count": 1,
        "status": 200,
    }
    called_urls = [call["url"] for call in transport.calls]
    assert called_urls == ["https://auth.openai.com/api/accounts", "https://chatgpt.com/backend-api/codex/usage"]


def test_codex_usage_refuses_ambiguous_profile_accounts(monkeypatch, tmp_path: Path):
    from chatcrs import codex_direct

    home = tmp_path / "chatarch"
    TokenStore(home=home).write(
        "OpenAI",
        "wzh",
        values={"access_token": "access-secret"},
        token_type="openai_oauth",
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
    assert account["accounts"][0]["id"] == "acct_123"
    assert account["accounts"][0]["refresh_token"] == "[REDACTED]"
    assert usage["ok"] is True
    assert usage["account_id"] == "acct_123"
    assert usage["rate_limits"]["primary_used_percent"] == 12.5
    assert usage["rate_limits"]["primary_reset_after_seconds"] == 1800.0
    combined = json.dumps({"account": account, "usage": usage}, ensure_ascii=False)
    assert "access-secret" not in combined
    assert "must-not-leak" not in combined


def test_codex_cli_surface_is_registered():
    result = CliRunner().invoke(main, ["--tree"])

    assert result.exit_code == 0, result.output
    assert "codex  # Direct OpenAI Codex account token and usage helpers." in result.output
    assert "refresh [--profile <PROFILE>]" in result.output
    assert "account [--profile <PROFILE>]" in result.output
    assert "quota [--profile <PROFILE>]" in result.output
    assert "usage [--profile <PROFILE>]" in result.output
    assert "tokens/Codex" not in result.output


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
            "token_service": "OpenAI",
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
            "account_id": "acct_123",
            "token_service": "OpenAI",
            "account_resolution": {"source": "profile_account_metadata", "account_count": 1, "status": 200},
            "rate_limits": {"primary_used_percent": 10.0},
        }

    monkeypatch.setattr(cli.codex_direct, "inspect_usage", fake_usage)

    result = CliRunner().invoke(
        main,
        ["codex", "usage", "--profile", "wzh", "--json-output"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["account_id"] == "acct_123"
    assert payload["account_resolution"]["source"] == "profile_account_metadata"
    assert called == {
        "profile": "wzh",
        "account_id": None,
        "access_token": None,
        "refresh": True,
        "client_id": None,
        "timeout": 20.0,
    }


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
            "account_id": "acct_123",
            "token_service": "OpenAI",
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
    assert payload["token_service"] == "OpenAI"
    assert called == {
        "profile": "codex-admin",
        "account_id": "acct_123",
        "access_token": "access-secret",
        "refresh": False,
        "client_id": None,
        "timeout": 20.0,
    }
    assert "access-secret" not in result.output
