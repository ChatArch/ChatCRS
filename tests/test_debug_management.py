from __future__ import annotations

import json
from pathlib import Path

import pytest
import chatcrs.debug as debug


def _result(stdout: str = "", returncode: int = 0, stderr: str = "") -> dict:
    return {"cmd": [], "returncode": returncode, "stdout": stdout, "stderr": stderr}



def test_restart_defaults_to_dry_run_without_commands():
    calls = []

    def runner(args, **kwargs):
        calls.append((args, kwargs))
        return _result()

    payload = debug.restart_debug(runner=runner)

    assert payload["mode"] == "dry-run"
    assert payload["mutated"] is False
    assert payload["target"] == "debug"
    assert calls == []


def test_status_passes_redis_password_only_in_child_environment(monkeypatch, tmp_path):
    app = tmp_path / "app"
    app.mkdir()
    env = app / ".env"
    env.write_text(
        "HOST=127.0.0.1\nPORT=12392\nREDIS_HOST=127.0.0.1\n"
        "REDIS_PORT=6382\nREDIS_DB=0\nREDIS_PASSWORD=redis-secret\nLOG_LEVEL=debug\n",
        encoding="utf-8",
    )
    (app / "VERSION").write_text("test-version\n", encoding="utf-8")
    monkeypatch.setattr(debug, "DEBUG_APP", app)
    monkeypatch.setattr(debug, "DEBUG_ENV", env)
    calls = []

    def runner(args, **kwargs):
        calls.append((args, kwargs))
        text = " ".join(args)
        if args[:2] == ["tmux", "has-session"]:
            return _result()
        if args[:2] == ["tmux", "list-panes"]:
            return _result("123|/debug|node|node src/app.js")
        if args and args[0] == "redis-cli":
            assert "redis-secret" not in text
            assert kwargs["env"]["REDISCLI_AUTH"] == "redis-secret"
            return _result("PONG")
        if "branch --show-current" in text:
            return _result("debug-branch")
        if "rev-parse HEAD" in text:
            return _result("debug-sha")
        if "status --short --branch" in text:
            return _result("## debug-branch")
        return _result()

    payload = debug.debug_status(
        runner=runner,
        probe=lambda url: {"url": url, "status": 200, "ok": True},
    )

    assert payload["ok"] is True
    assert payload["redis"]["ping"] == "PONG"
    assert "redis-secret" not in json.dumps(payload)


def test_restart_execute_targets_only_debug_tmux(monkeypatch, tmp_path):
    calls = []

    def runner(args, **kwargs):
        calls.append(args)
        return _result()

    monkeypatch.setenv("CHATCRS_AUDIT_DIR", str(tmp_path / "audit"))
    payload = debug.restart_debug(
        execute=True,
        runner=runner,
        probe=lambda url: {"url": url, "status": 200, "ok": True},
        enforce_guard=False,
    )

    assert payload["ok"] is True
    assert payload["mutated"] is True
    assert calls[0] == ["tmux", "kill-session", "-t", "crs-debug-12392"]
    assert calls[1][:6] == ["tmux", "new-session", "-d", "-s", "crs-debug-12392", "-c"]
    assert calls[2][:5] == ["tmux", "send-keys", "-t", "crs-debug-12392:0.0", "-l"]
    assert calls[3] == ["tmux", "send-keys", "-t", "crs-debug-12392:0.0", "Enter"]
    flattened = " ".join(" ".join(call) for call in calls)
    assert "12390" not in flattened
    assert "12391" not in flattened


def test_show_settings_never_returns_secret_values(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "LOG_LEVEL=debug\nJWT_SECRET=do-not-print\nREDIS_PASSWORD=also-secret\n"
        "OPENAI_IMAGES_HOST_MODEL=gpt-5.5\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(debug, "DEBUG_ENV", env)

    payload = debug.show_debug_settings()
    serialized = json.dumps(payload)

    assert payload["settings"]["LOG_LEVEL"] == "debug"
    assert "do-not-print" not in serialized
    assert "also-secret" not in serialized
    assert "JWT_SECRET" in payload["protected"]


def test_protected_setting_is_rejected():
    with pytest.raises(ValueError, match="protected"):
        debug.validate_debug_setting("PORT", "12390")
    with pytest.raises(ValueError, match="protected"):
        debug.validate_debug_setting("REDIS_DB", "0")


def test_setting_dry_run_does_not_modify_env(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    original = "LOG_LEVEL=debug\nJWT_SECRET=keep-me\n"
    env.write_text(original, encoding="utf-8")
    monkeypatch.setattr(debug, "DEBUG_ENV", env)

    payload = debug.set_debug_setting("LOG_LEVEL", "info")

    assert payload["changed"] is True
    assert payload["mutated"] is False
    assert env.read_text() == original


def test_setting_execute_backs_up_preserves_secrets_and_restarts(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("LOG_LEVEL=debug\nJWT_SECRET=keep-me\n", encoding="utf-8")
    monkeypatch.setattr(debug, "DEBUG_ENV", env)
    monkeypatch.setenv("CHATCRS_AUDIT_DIR", str(tmp_path / "audit"))
    monkeypatch.setattr(
        debug,
        "restart_debug",
        lambda **kwargs: {"ok": True, "mutated": True, "target": "debug"},
    )

    payload = debug.set_debug_setting(
        "LOG_LEVEL",
        "info",
        execute=True,
        enforce_guard=False,
    )

    assert payload["mutated"] is True
    assert "LOG_LEVEL=info" in env.read_text()
    assert "JWT_SECRET=keep-me" in env.read_text()
    backup = Path(payload["backup"])
    assert backup.exists()
    assert "LOG_LEVEL=debug" in backup.read_text()


def test_setting_failure_restores_original_env(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    original = "LOG_LEVEL=debug\nJWT_SECRET=keep-me\n"
    env.write_text(original, encoding="utf-8")
    monkeypatch.setattr(debug, "DEBUG_ENV", env)
    monkeypatch.setenv("CHATCRS_AUDIT_DIR", str(tmp_path / "audit"))
    outcomes = iter(
        [
            {"ok": False, "mutated": True, "target": "debug"},
            {"ok": True, "mutated": True, "target": "debug"},
        ]
    )
    monkeypatch.setattr(debug, "restart_debug", lambda **kwargs: next(outcomes))

    with pytest.raises(RuntimeError, match="env restored"):
        debug.set_debug_setting(
            "LOG_LEVEL",
            "info",
            execute=True,
            enforce_guard=False,
        )

    assert env.read_text() == original


def test_logs_are_bounded_and_redacted(tmp_path):
    log = tmp_path / "debug.log"
    log.write_text(
        "first\nAuthorization: Bearer ***",
        encoding="utf-8",
    )

    payload = debug.debug_logs(2, log_path=log)
    serialized = json.dumps(payload)

    assert payload["requested_lines"] == 2
    assert len(payload["lines"]) == 2
    assert "abcdefghijklmnopqrstuvwxyz" not in serialized
    assert "[REDACTED]" in serialized


def test_debug_guard_rejects_production_path(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "HOST=127.0.0.1\nPORT=12392\nREDIS_HOST=127.0.0.1\n"
        "REDIS_PORT=6382\nREDIS_DB=0\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(debug, "DEBUG_APP", Path("/home/zhihong/claude-relay-service/app"))
    monkeypatch.setattr(debug, "DEBUG_ENV", env)

    with pytest.raises(ValueError, match="non-debug path"):
        debug._assert_debug_target()


def _upgrade_runner(expected_sha: str):
    calls = []

    def runner(args, **kwargs):
        calls.append(args)
        text = " ".join(args)
        if "remote get-url origin" in text:
            return _result("https://github.com/ChatArch/claude-relay-service.git")
        if args[:2] == ["git", "ls-remote"]:
            return _result(f"{expected_sha}\trefs/heads/dev")
        if "rev-parse HEAD^{tree}" in text:
            return _result("tree-1")
        if "rev-parse origin/dev^{tree}" in text:
            return _result("tree-1")
        if "rev-parse origin/dev" in text:
            return _result(expected_sha)
        if "rev-parse HEAD" in text:
            return _result("current-sha")
        if "status --porcelain" in text:
            return _result("")
        return _result()

    return runner, calls


def test_upgrade_plan_is_read_only_and_detects_equal_tree():
    expected = "a" * 40
    runner, calls = _upgrade_runner(expected)

    payload = debug.upgrade_plan(runner=runner)

    assert payload["ok"] is True
    assert payload["mutated"] is False
    assert payload["already_target_tree"] is True
    assert payload["dev"]["remote_sha"] == expected
    assert not any("checkout" in call for args in calls for call in args)


def test_upgrade_apply_noops_when_tree_already_matches():
    expected = "b" * 40
    runner, calls = _upgrade_runner(expected)

    payload = debug.apply_debug_upgrade(
        expected,
        execute=True,
        runner=runner,
        enforce_guard=False,
    )

    assert payload["ok"] is True
    assert payload["mutated"] is False
    assert payload["reason"] == "already_target_tree"
    assert not any(args and args[0] == "tmux" for args in calls)


def test_upgrade_failure_restores_sha_env_dependencies_and_runtime(monkeypatch, tmp_path):
    expected = "c" * 40
    previous = "d" * 40
    app = tmp_path / "app"
    app.mkdir()
    env = app / ".env"
    original_env = "LOG_LEVEL=debug\nJWT_SECRET=keep-me\n"
    env.write_text(original_env, encoding="utf-8")
    monkeypatch.setattr(debug, "DEBUG_APP", app)
    monkeypatch.setattr(debug, "DEBUG_ENV", env)
    monkeypatch.setenv("CHATCRS_AUDIT_DIR", str(tmp_path / "audit"))
    calls = []
    target_install_failed = False
    restarts = []

    def runner(args, **kwargs):
        nonlocal target_install_failed
        calls.append(args)
        text = " ".join(args)
        if "remote get-url origin" in text:
            return _result("https://github.com/ChatArch/claude-relay-service.git")
        if args[:2] == ["git", "ls-remote"]:
            return _result(f"{expected}\trefs/heads/dev")
        if "rev-parse HEAD^{tree}" in text:
            return _result("old-tree")
        if "rev-parse origin/dev^{tree}" in text:
            return _result("new-tree")
        if "rev-parse origin/dev" in text:
            return _result(expected)
        if "rev-parse HEAD" in text:
            return _result(previous)
        if "status --porcelain" in text:
            return _result("")
        if args and args[0] == str(debug.NPM) and args[1:] == ["ci"] and not target_install_failed:
            target_install_failed = True
            return _result(returncode=1, stderr="target install failed")
        return _result()

    monkeypatch.setattr(
        debug,
        "restart_debug",
        lambda **kwargs: restarts.append(kwargs) or {"ok": True, "mutated": True},
    )

    with pytest.raises(RuntimeError, match="npm ci failed"):
        debug.apply_debug_upgrade(
            expected,
            execute=True,
            runner=runner,
            enforce_guard=False,
        )

    assert env.read_text() == original_env
    assert any("checkout --detach" in " ".join(args) and previous in args for args in calls)
    assert sum(1 for args in calls if args and args[0] == str(debug.NPM) and args[1:] == ["ci"]) == 2
    assert len(restarts) == 1
