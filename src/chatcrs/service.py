"""Guarded remote CRS service lifecycle helpers."""

from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Callable, Protocol

from chatcrs.redaction import redact


class CompletedProcessLike(Protocol):
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[list[str]], CompletedProcessLike]


OFFICIAL_CRS_ACTIONS = {
    "install",
    "update",
    "start",
    "stop",
    "restart",
    "status",
    "switch-branch",
    "update-pricing",
}
MUTATING_ACTIONS = {
    "install",
    "update",
    "start",
    "stop",
    "restart",
    "switch-branch",
    "update-pricing",
}


@dataclass(frozen=True)
class ServiceTarget:
    """Remote CRS host/service target for lifecycle commands."""

    ssh_alias: str | None = None
    app_dir: str = "/home/zhihong/claude-relay-service/app"
    crs_command: str = "crs"
    timeout: float = 120.0

    @classmethod
    def from_options(
        cls,
        *,
        ssh_alias: str | None = None,
        app_dir: str | None = None,
        crs_command: str | None = None,
        timeout: float = 120.0,
    ) -> "ServiceTarget":
        return cls(
            ssh_alias=ssh_alias or os.environ.get("CHATCRS_SSH_ALIAS"),
            app_dir=app_dir or os.environ.get("CHATCRS_APP_DIR") or cls.app_dir,
            crs_command=crs_command or os.environ.get("CHATCRS_CRS_COMMAND") or cls.crs_command,
            timeout=timeout,
        )

    def safe_summary(self) -> dict[str, object]:
        return {
            "ssh_alias": self.ssh_alias,
            "app_dir": self.app_dir,
            "crs_command": self.crs_command,
            "timeout": self.timeout,
        }


def _default_runner(argv: list[str], *, timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, text=True, capture_output=True, timeout=timeout, check=False)


def _official_crs_command(action: str, *, crs_command: str = "crs", branch: str | None = None) -> list[str]:
    if action not in OFFICIAL_CRS_ACTIONS:
        raise ValueError(f"Unsupported CRS service action: {action}")
    command = [crs_command, action]
    if action == "switch-branch":
        if not branch:
            raise ValueError("switch-branch requires a branch argument")
        command.append(branch)
    elif branch:
        raise ValueError(f"{action} does not accept a branch argument")
    return command


def _remote_shell(target: ServiceTarget, official_command: list[str]) -> str:
    return f"cd {shlex.quote(target.app_dir)} && " + " ".join(shlex.quote(part) for part in official_command)


def _ssh_argv(target: ServiceTarget, shell_command: str) -> list[str]:
    if not target.ssh_alias:
        raise ValueError("--ssh-alias or CHATCRS_SSH_ALIAS is required for service execution")
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=8",
        target.ssh_alias,
        shell_command,
    ]


def _safe_text(text: str, *, limit: int = 12000) -> str:
    redacted = str(redact(text or ""))
    if len(redacted) <= limit:
        return redacted
    return redacted[-limit:]


def run_service_action(
    action: str,
    *,
    target: ServiceTarget,
    execute: bool = False,
    branch: str | None = None,
    runner: Callable[[list[str]], CompletedProcessLike] | None = None,
) -> dict[str, object]:
    """Plan or execute one official-CRS lifecycle action through SSH."""

    official_command = _official_crs_command(action, crs_command=target.crs_command, branch=branch)
    shell_command = _remote_shell(target, official_command)
    is_mutating = action in MUTATING_ACTIONS
    payload: dict[str, object] = {
        "ok": True,
        "action": action,
        "mode": "execute" if execute else "plan",
        "mutated": bool(execute and is_mutating),
        "target": target.safe_summary(),
        "official_crs_command": official_command,
        "remote_shell": shell_command,
        "safety": {
            "requires_execute": is_mutating,
            "dry_run_default": is_mutating,
            "transport": "ssh",
            "redacted_output": True,
        },
    }

    if not execute:
        return payload

    argv = _ssh_argv(target, shell_command)
    run = runner or _default_runner
    try:
        completed = run(argv, timeout=target.timeout)  # type: ignore[misc]
    except TypeError:
        completed = run(argv)  # type: ignore[misc]

    payload.update(
        {
            "ok": completed.returncode == 0,
            "exit_code": completed.returncode,
            "stdout": _safe_text(getattr(completed, "stdout", "")),
            "stderr": _safe_text(getattr(completed, "stderr", "")),
        }
    )
    return payload


__all__ = ["ServiceTarget", "run_service_action"]
