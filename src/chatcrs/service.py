"""Local-only CRS service lifecycle helpers.

The service namespace is intended to run on the CRS host itself. It never
constructs SSH commands, never reads legacy remote target profiles, and never
uses remote host aliases as an implementation shortcut.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from chatcrs.redaction import redact


class CompletedProcessLike(Protocol):
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[..., CompletedProcessLike]


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
    """Current-machine CRS service target."""

    app_dir: Path | str | None = None
    crs_command: str = "crs"
    timeout: float = 120.0

    @classmethod
    def from_options(
        cls,
        *,
        app_dir: str | Path | None = None,
        crs_command: str | None = None,
        timeout: float = 120.0,
    ) -> "ServiceTarget":
        return cls(
            app_dir=Path(app_dir).expanduser().resolve() if app_dir else Path.cwd(),
            crs_command=crs_command or "crs",
            timeout=timeout,
        )

    @property
    def resolved_app_dir(self) -> Path:
        if self.app_dir is None:
            return Path.cwd()
        return Path(self.app_dir).expanduser().resolve()

    def safe_summary(self) -> dict[str, object]:
        return {
            "scope": "local",
            "app_dir": str(self.resolved_app_dir),
            "crs_command": self.crs_command,
            "timeout": self.timeout,
        }


def _default_runner(argv: list[str], *, cwd: Path, timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False)


def _local_crs_command(action: str, *, crs_command: str = "crs", branch: str | None = None) -> list[str]:
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


def _safe_text(text: str, *, limit: int = 12000) -> str:
    redacted = str(redact(text or ""))
    if len(redacted) <= limit:
        return redacted
    return redacted[-limit:]


def run_service_action(
    action: str,
    *,
    target: ServiceTarget,
    execute: bool | None = None,
    branch: str | None = None,
    runner: Runner | None = None,
) -> dict[str, object]:
    """Plan or execute one official CRS lifecycle action on this machine."""

    is_mutating = action in MUTATING_ACTIONS
    should_execute = (not is_mutating) if execute is None else execute
    local_command = _local_crs_command(action, crs_command=target.crs_command, branch=branch)
    payload: dict[str, object] = {
        "ok": True,
        "action": action,
        "mode": "execute" if should_execute else "plan",
        "mutated": bool(should_execute and is_mutating),
        "target": target.safe_summary(),
        "local_command": local_command,
        "safety": {
            "transport": "local",
            "server_local_only": True,
            "requires_execute": is_mutating,
            "dry_run_default": is_mutating,
            "redacted_output": True,
        },
    }

    if not should_execute:
        return payload

    run = runner or _default_runner
    completed = run(local_command, cwd=target.resolved_app_dir, timeout=target.timeout)
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
