from __future__ import annotations

import json
from pathlib import Path

import pytest
from chatenv import TokenRefreshResult
from chatenv.store import EnvStore
import chatenv.token_refreshers as chatenv_refreshers
from chatenv.token_refreshers import refresh_token

from chatcrs.config import ChatcrsConfig
from chatcrs.remote import CrsProfile
from chatcrs import tokens as crs_tokens
from chatcrs.tokens import CrsTokenStore


def test_token_store_uses_parallel_chatarch_tokens_directory(tmp_path: Path):
    home = tmp_path / "chatarch"
    profile = CrsProfile(base_url="https://crs.tencent-am.wzhecnu.cn", username="admin")

    store = CrsTokenStore(profile_name="admin", profile=profile, home=home)

    assert store.path == home / "tokens" / "CRS" / "admin.json"
    assert store.status()["token_file_exists"] is False
    assert store.status()["token_present"] is False
    assert store.status()["base_url_match"] is False


def test_token_store_saves_session_token_through_chatenv_store(tmp_path: Path):
    home = tmp_path / "chatarch"
    profile = CrsProfile(base_url="https://crs.tencent-am.wzhecnu.cn", username="admin")
    store = CrsTokenStore(profile_name="admin", profile=profile, home=home)

    summary = store.save_login_token("opaque-session-value", expires_in=3600, username="admin")

    assert summary["ok"] is True
    assert summary["token_present"] is True
    assert summary["profile"] == "admin"
    assert summary["service"] == "CRS"
    assert summary["token_file"] == str(store.path)
    assert "opaque-session-value" not in json.dumps(summary)
    saved = json.loads(store.path.read_text())
    assert saved["service"] == "CRS"
    assert saved["profile"] == "admin"
    assert saved["token_type"] == "admin_session"
    assert saved["summary"]["base_url"] == "https://crs.tencent-am.wzhecnu.cn"
    assert saved["summary"]["base_url_hash"]
    assert saved["summary"]["username"] == "admin"
    assert saved["values"]["access_token"] == "opaque-session-value"
    assert "access_token" not in {key for key in saved if key != "values"}
    assert saved["expires_at"]


def test_token_store_rejects_token_when_profile_base_url_changes(tmp_path: Path):
    home = tmp_path / "chatarch"
    original = CrsProfile(base_url="https://crs.tencent-am.wzhecnu.cn", username="admin")
    CrsTokenStore(profile_name="admin", profile=original, home=home).save_login_token(
        "opaque-session-value", expires_in=3600, username="admin"
    )

    moved = CrsProfile(base_url="https://staging.example.test", username="admin")
    moved_store = CrsTokenStore(profile_name="admin", profile=moved, home=home)

    assert moved_store.load_token() == ""
    status = moved_store.status()
    assert status["token_file_exists"] is True
    assert status["token_present"] is True
    assert status["base_url_match"] is False


def test_token_store_clear_is_dry_run_until_execute(tmp_path: Path):
    home = tmp_path / "chatarch"
    profile = CrsProfile(base_url="https://crs.tencent-am.wzhecnu.cn", username="admin")
    store = CrsTokenStore(profile_name="admin", profile=profile, home=home)
    store.save_login_token("opaque-session-value", expires_in=3600, username="admin")

    plan = store.clear(execute=False)

    assert plan["ok"] is True
    assert plan["mutated"] is False
    assert plan["would_delete"] == str(store.path)
    assert store.path.exists()

    result = store.clear(execute=True)

    assert result["ok"] is True
    assert result["mutated"] is True
    assert not store.path.exists()


def test_refresh_chatenv_token_uses_matching_stable_profile_without_writing_store(monkeypatch, tmp_path: Path):
    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    env_store.save_profile(
        ChatcrsConfig,
        "admin",
        {
            "CRS_API_BASE": "https://crs.example.invalid",
            "CRS_USERNAME": "profile-admin",
            "CRS_PASSWORD": "profile-password",
            "CRS_API_KEY": "caller-key-fixture",
        },
    )
    captured: dict[str, object] = {}

    class FakeClient:
        def __init__(self, profile, *, timeout, profile_name, home, explicit_admin_token=False):
            captured["profile"] = profile
            captured["timeout"] = timeout
            captured["profile_name"] = profile_name
            captured["home"] = home
            captured["explicit_admin_token"] = explicit_admin_token

        def login(self, *, save_token=False):
            captured["save_token"] = save_token
            self._admin_token = "opaque-admin-session-fixture"
            return {
                "ok": True,
                "status": 200,
                "profile": "admin",
                "base_url": "https://crs.example.invalid",
                "username": "profile-admin",
                "expiresIn": 3600,
                "token_present": True,
                "token_saved": False,
            }

    monkeypatch.setattr(crs_tokens, "_refresh_client_class", lambda: FakeClient)

    result = crs_tokens.refresh_chatenv_token(service="CRS", profile="admin", home=home, env_store=env_store)

    assert captured["profile"].base_url == "https://crs.example.invalid"
    assert captured["profile"].username == "profile-admin"
    assert captured["profile"].password == "profile-password"
    assert captured["timeout"] == 20.0
    assert captured["profile_name"] == "admin"
    assert captured["home"] == home
    assert captured["explicit_admin_token"] is True
    assert captured["save_token"] is False
    assert result.token_type == "admin_session"
    assert result.values == {"access_token": "opaque-admin-session-fixture"}
    assert result.summary == {
        "base_url": "https://crs.example.invalid",
        "base_url_hash": crs_tokens.base_url_hash("https://crs.example.invalid"),
        "username": "profile-admin",
    }
    assert result.expires_at
    assert not (home / "tokens" / "CRS" / "admin.json").exists()


def test_refresh_chatenv_token_fails_cleanly_for_missing_profile(tmp_path: Path):
    with pytest.raises(ValueError, match="CRS ChatEnv profile not found or invalid: Missing"):
        crs_tokens.refresh_chatenv_token(service="CRS", profile="Missing", home=tmp_path / "chatarch")


def test_refresh_chatenv_token_requires_stable_profile_credentials(tmp_path: Path):
    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    env_store.save_profile(ChatcrsConfig, "NoPassword", {"CRS_API_BASE": "https://crs.example.invalid", "CRS_USERNAME": "admin"})

    with pytest.raises(ValueError, match="CRS ChatEnv profile NoPassword is missing CRS_PASSWORD"):
        crs_tokens.refresh_chatenv_token(service="CRS", profile="NoPassword", home=home, env_store=env_store)


def test_refresh_chatenv_token_does_not_fallback_to_process_env_for_named_profile(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("CRS_API_BASE", "https://ambient.example.invalid")
    monkeypatch.setenv("CRS_USERNAME", "ambient-admin")
    monkeypatch.setenv("CRS_PASSWORD", "ambient-password")

    with pytest.raises(ValueError, match="CRS ChatEnv profile not found or invalid: Named"):
        crs_tokens.refresh_chatenv_token(service="CRS", profile="Named", home=tmp_path / "chatarch")


def test_chatenv_refresh_provider_writes_source_refresh_and_hides_raw_token(monkeypatch, tmp_path: Path):
    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    env_store.save_profile(
        ChatcrsConfig,
        "admin",
        {"CRS_API_BASE": "https://crs.example.invalid", "CRS_USERNAME": "admin", "CRS_PASSWORD": "secret"},
    )

    def fake_provider(**kwargs):
        return TokenRefreshResult(
            values={"access_token": "opaque-admin-session-fixture"},
            token_type="admin_session",
            summary={
                "base_url": "https://crs.example.invalid",
                "base_url_hash": crs_tokens.base_url_hash("https://crs.example.invalid"),
                "username": "admin",
            },
            expires_at="2026-08-11T12:00:00Z",
        )

    chatenv_refreshers.clear_token_refreshers()
    monkeypatch.setitem(chatenv_refreshers._token_refreshers, "crs", fake_provider)
    monkeypatch.setattr(chatenv_refreshers, "_loaded", True)

    status = refresh_token("CRS", "admin", home=home, env_store=env_store)
    token_file = home / "tokens" / "CRS" / "admin.json"
    saved = json.loads(token_file.read_text())
    rendered_status = CrsTokenStore(
        profile_name="admin",
        profile=CrsProfile(base_url="https://crs.example.invalid", username="admin", password="secret"),
        home=home,
    ).status()

    assert status["source"] == "refresh"
    assert saved["source"] == "refresh"
    assert saved["values"]["access_token"] == "opaque-admin-session-fixture"
    assert rendered_status["token_present"] is True
    assert rendered_status["summary"]["username"] == "admin"
    assert "opaque-admin-session-fixture" not in json.dumps(status)
    assert "opaque-admin-session-fixture" not in json.dumps(rendered_status)
