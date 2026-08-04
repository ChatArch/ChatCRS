from __future__ import annotations

import json

from click.testing import CliRunner

from chatcrs.cli import main
from chatcrs.service import ServiceTarget, run_service_action


def test_service_lifecycle_cli_plans_official_crs_management_commands_without_mutation():
    runner = CliRunner()

    result = runner.invoke(
        main,
        [
            "service",
            "update",
            "--ssh-alias",
            "tencent.am",
            "--app-dir",
            "/home/zhihong/claude-relay-service/app",
            "--json-output",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["action"] == "update"
    assert payload["mode"] == "plan"
    assert payload["mutated"] is False
    assert payload["official_crs_command"] == ["crs", "update"]
    assert "cd /home/zhihong/claude-relay-service/app && crs update" in payload["remote_shell"]
    assert payload["safety"]["requires_execute"] is True

    branch_result = runner.invoke(
        main,
        [
            "service",
            "switch-branch",
            "dev",
            "--ssh-alias",
            "tencent.am",
            "--app-dir",
            "/home/zhihong/claude-relay-service/app",
            "--json-output",
        ],
    )

    assert branch_result.exit_code == 0, branch_result.output
    branch_payload = json.loads(branch_result.output)
    assert branch_payload["mutated"] is False
    assert branch_payload["official_crs_command"] == ["crs", "switch-branch", "dev"]


def test_service_lifecycle_execute_uses_injected_runner_and_redacts_sensitive_output():
    calls: list[list[str]] = []

    class FakeCompleted:
        returncode = 0
        stdout = "ok Authorization: Bearer secret-token-1234567890 cr_live_SECRET_VALUE"
        stderr = ""

    def fake_runner(argv: list[str], *, timeout: float):
        calls.append(argv)
        assert timeout == 30.0
        return FakeCompleted()

    target = ServiceTarget(
        ssh_alias="tencent.am",
        app_dir="/home/zhihong/claude-relay-service/app",
        timeout=30.0,
    )

    payload = run_service_action("restart", target=target, execute=True, runner=fake_runner)

    assert payload["ok"] is True
    assert payload["mode"] == "execute"
    assert payload["mutated"] is True
    assert payload["exit_code"] == 0
    assert calls == [
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=8",
            "tencent.am",
            "cd /home/zhihong/claude-relay-service/app && crs restart",
        ]
    ]
    assert "secret-token" not in payload["stdout"]
    assert "cr_live_SECRET_VALUE" not in payload["stdout"]
    assert "[REDACTED]" in payload["stdout"]


def test_service_lifecycle_help_exposes_absorbed_official_commands():
    runner = CliRunner()
    result = runner.invoke(main, ["service", "--help"])

    assert result.exit_code == 0, result.output
    for command in ["install", "update", "start", "stop", "restart", "switch-branch", "update-pricing", "status"]:
        assert command in result.output
