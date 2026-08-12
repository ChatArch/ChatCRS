import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from chatcrs.cli import main


class FakeCodexTransport:
    def __init__(self):
        self.calls = []

    def __call__(self, method, url, *, data=None, headers=None, timeout=20.0):
        self.calls.append({"method": method, "url": url, "data": data, "headers": headers or {}, "timeout": timeout})
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
    assert "usage [--profile <PROFILE>]" in result.output


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
    assert called == {
        "profile": "codex-admin",
        "account_id": "acct_123",
        "access_token": "access-secret",
        "refresh": False,
        "client_id": None,
        "timeout": 20.0,
    }
    assert "access-secret" not in result.output
