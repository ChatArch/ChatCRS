from __future__ import annotations

import json
from pathlib import Path

from chatcrs.remote import CrsProfile
from chatcrs.tokens import CrsTokenStore


def test_token_store_uses_parallel_chatarch_tokens_directory(tmp_path: Path):
    home = tmp_path / "chatarch"
    profile = CrsProfile(base_url="https://crs.tencent-am.wzhecnu.cn", username="admin")

    store = CrsTokenStore(profile_name="admin", profile=profile, home=home)

    assert store.path == home / "tokens" / "CRS" / "admin.json"
    assert store.status()["token_file_exists"] is False
    assert store.status()["token_present"] is False
    assert store.status()["base_url_match"] is False


def test_token_store_saves_session_token_with_metadata_and_private_permissions(tmp_path: Path):
    home = tmp_path / "chatarch"
    profile = CrsProfile(base_url="https://crs.tencent-am.wzhecnu.cn", username="admin")
    store = CrsTokenStore(profile_name="admin", profile=profile, home=home)

    summary = store.save_login_token("session-secret", expires_in=3600, username="admin")

    assert summary["ok"] is True
    assert summary["token_present"] is True
    assert summary["profile"] == "admin"
    assert summary["service"] == "CRS"
    assert summary["token_file"] == str(store.path)
    assert "session-secret" not in json.dumps(summary)
    saved = json.loads(store.path.read_text())
    assert saved["service"] == "CRS"
    assert saved["profile"] == "admin"
    assert saved["base_url"] == "https://crs.tencent-am.wzhecnu.cn"
    assert saved["base_url_hash"]
    assert saved["token_type"] == "admin_session"
    assert saved["access_token"] == "session-secret"
    assert saved["expires_at"]
    assert store.path.stat().st_mode & 0o777 == 0o600
    assert store.path.parent.stat().st_mode & 0o777 == 0o700


def test_token_store_rejects_token_when_profile_base_url_changes(tmp_path: Path):
    home = tmp_path / "chatarch"
    original = CrsProfile(base_url="https://crs.tencent-am.wzhecnu.cn", username="admin")
    CrsTokenStore(profile_name="admin", profile=original, home=home).save_login_token(
        "session-secret", expires_in=3600, username="admin"
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
    store.save_login_token("session-secret", expires_in=3600, username="admin")

    plan = store.clear(execute=False)

    assert plan["ok"] is True
    assert plan["mutated"] is False
    assert plan["would_delete"] == str(store.path)
    assert store.path.exists()

    result = store.clear(execute=True)

    assert result["ok"] is True
    assert result["mutated"] is True
    assert not store.path.exists()
