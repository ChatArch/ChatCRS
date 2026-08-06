from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from chatcrs.cli import main


LEGACY_REMOTE_ENV_KEYS = ("CHATCRS_SSH_ALIAS", "CHATCRS_APP_DIR", "CHATCRS_CRS_COMMAND")


def test_service_namespace_is_registered_without_legacy_or_remote_options():
    result = CliRunner().invoke(main, ["service", "--help"])

    assert result.exit_code == 0, result.output
    for command in ["install", "update", "start", "stop", "restart", "status", "switch-branch", "update-pricing"]:
        assert command in result.output
    assert "--ssh-alias" not in result.output
    assert "CHATCRS_SSH_ALIAS" not in result.output
    assert "envs/Chatcrs" not in result.output


def test_service_status_executes_local_crs_command_by_default(tmp_path):
    from chatcrs.service import ServiceTarget, run_service_action

    calls: list[tuple[list[str], Path, float]] = []

    class FakeCompleted:
        returncode = 0
        stdout = "local service healthy"
        stderr = ""

    def fake_runner(argv: list[str], *, cwd: Path, timeout: float):
        calls.append((argv, cwd, timeout))
        return FakeCompleted()

    target = ServiceTarget(app_dir=tmp_path, timeout=7.5)
    payload = run_service_action("status", target=target, runner=fake_runner)

    assert calls == [(["crs", "status"], tmp_path, 7.5)]
    assert payload["ok"] is True
    assert payload["action"] == "status"
    assert payload["mode"] == "execute"
    assert payload["mutated"] is False
    assert payload["target"]["scope"] == "local"
    assert payload["safety"]["transport"] == "local"
    assert payload["safety"]["server_local_only"] is True
    assert "remote_shell" not in payload
    assert "ssh_alias" not in payload["target"]


def test_mutating_service_commands_are_local_dry_run_by_default(tmp_path):
    from chatcrs.service import ServiceTarget, run_service_action

    calls: list[list[str]] = []

    def fake_runner(argv: list[str], *, cwd: Path, timeout: float):
        calls.append(argv)
        raise AssertionError("dry-run must not execute")

    target = ServiceTarget(app_dir=tmp_path, crs_command="/usr/local/bin/crs")
    payload = run_service_action("restart", target=target, execute=False, runner=fake_runner)

    assert calls == []
    assert payload["ok"] is True
    assert payload["mode"] == "plan"
    assert payload["mutated"] is False
    assert payload["local_command"] == ["/usr/local/bin/crs", "restart"]
    assert payload["target"] == {
        "scope": "local",
        "app_dir": str(tmp_path),
        "crs_command": "/usr/local/bin/crs",
        "timeout": 120.0,
    }
    assert payload["safety"]["requires_execute"] is True
    assert payload["safety"]["dry_run_default"] is True
    assert payload["safety"]["transport"] == "local"


def test_service_execute_runs_locally_and_redacts_sensitive_output(tmp_path):
    from chatcrs.service import ServiceTarget, run_service_action

    calls: list[tuple[list[str], Path, float]] = []

    class FakeCompleted:
        returncode = 0
        stdout = "ok Authorization: Bearer secret-token cr_live_SECRET_VALUE"
        stderr = ""

    def fake_runner(argv: list[str], *, cwd: Path, timeout: float):
        calls.append((argv, cwd, timeout))
        return FakeCompleted()

    target = ServiceTarget(app_dir=tmp_path, timeout=30.0)
    payload = run_service_action("update", target=target, execute=True, runner=fake_runner)

    assert calls == [(["crs", "update"], tmp_path, 30.0)]
    assert payload["ok"] is True
    assert payload["mode"] == "execute"
    assert payload["mutated"] is True
    assert "secret-token" not in payload["stdout"]
    assert "cr_live_SECRET_VALUE" not in payload["stdout"]
    assert "[REDACTED]" in payload["stdout"]


def test_cli_service_plan_ignores_legacy_remote_env_and_chatenv_profile(tmp_path, monkeypatch):
    chatarch_home = tmp_path / "chatarch"
    legacy_profile = chatarch_home / "envs" / "Chatcrs"
    legacy_profile.mkdir(parents=True)
    (legacy_profile / ".env").write_text(
        "CHATCRS_SSH_ALIAS=remote-host\n"
        "CHATCRS_APP_DIR=/remote/crs\n"
        "CHATCRS_CRS_COMMAND=/remote/bin/crs\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CHATARCH_HOME", str(chatarch_home))
    monkeypatch.setenv("CHATCRS_SSH_ALIAS", "env-remote-host")
    monkeypatch.setenv("CHATCRS_APP_DIR", "/env/remote/crs")
    monkeypatch.setenv("CHATCRS_CRS_COMMAND", "/env/remote/bin/crs")

    result = CliRunner().invoke(main, ["service", "update", "--app-dir", str(tmp_path), "--json-output"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "plan"
    assert payload["target"] == {
        "scope": "local",
        "app_dir": str(tmp_path),
        "crs_command": "crs",
        "timeout": 120.0,
    }
    assert "remote-host" not in result.output
    assert "/remote/crs" not in result.output
    assert "ssh_alias" not in result.output


def test_cli_service_rejects_ssh_alias_option():
    result = CliRunner().invoke(main, ["service", "status", "--ssh-alias", "remote-host"])

    assert result.exit_code != 0
    assert "No such option" in result.output


def test_cli_service_status_returns_nonzero_when_local_status_fails(tmp_path):
    fake_crs = tmp_path / "crs-fails"
    fake_crs.write_text("#!/bin/sh\necho local status failed >&2\nexit 7\n", encoding="utf-8")
    fake_crs.chmod(0o700)

    result = CliRunner().invoke(main, ["service", "status", "--app-dir", str(tmp_path), "--crs-command", str(fake_crs), "--json-output"])

    assert result.exit_code != 0
    assert '"ok": false' in result.output
    assert "local status failed" in result.output


def test_verify_image_debug_and_cutover_surfaces_stay_removed():
    runner = CliRunner()
    for argv in (["verify", "images"], ["verify", "sidecar"], ["debug", "status"], ["nginx", "plan-cutover"], ["cutover", "precheck"]):
        result = runner.invoke(main, list(argv))
        assert result.exit_code != 0, argv
        assert "No such command" in result.output
