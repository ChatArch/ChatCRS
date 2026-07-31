"""Guarded management operations for the isolated CRS debug runtime."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .redaction import redact
from .runtime import http_status

DEBUG_APP = Path("/home/zhihong/claude-relay-service-independent/app")
DEBUG_ENV = DEBUG_APP / ".env"
DEBUG_BASE_URL = "http://127.0.0.1:12392"
DEBUG_PORT = "12392"
DEBUG_REDIS_HOST = "127.0.0.1"
DEBUG_REDIS_PORT = "6382"
DEBUG_REDIS_DB = "0"
DEBUG_SESSION = "crs-debug-12392"
DEBUG_LOG = Path(
    "/home/zhihong/Playground/projects/07-18-tencent-independent-crs/"
    "playground/crs-debug-12392.log"
)
NODE = Path("/home/zhihong/.nvm/versions/node/v24.14.1/bin/node")
NPM = Path("/home/zhihong/.nvm/versions/node/v24.14.1/bin/npm")

SAFE_SETTING_RULES: dict[str, dict[str, Any]] = {
    "LOG_LEVEL": {"choices": {"debug", "info", "warn", "error"}},
    "ENABLE_CORS": {"choices": {"true", "false"}},
    "TRUST_PROXY": {"choices": {"true", "false"}},
    "OPENAI_IMAGES_HOST_MODEL": {"pattern": r"[A-Za-z0-9._-]{1,64}"},
    "REQUEST_MAX_SIZE_MB": {"integer": (1, 200)},
    "WEB_TITLE": {"text": 120},
    "WEB_DESCRIPTION": {"text": 240},
}
PROTECTED_SETTINGS = {
    "HOST",
    "PORT",
    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_DB",
    "REDIS_PASSWORD",
    "JWT_SECRET",
    "ENCRYPTION_KEY",
}

Runner = Callable[..., dict[str, Any]]
Probe = Callable[..., dict[str, Any]]


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run(
    args: list[str],
    *,
    timeout: int = 30,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=env,
        )
    except FileNotFoundError as exc:
        return {"cmd": args, "returncode": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired:
        return {"cmd": args, "returncode": 124, "stdout": "", "stderr": "timeout"}
    return redact(
        {
            "cmd": args,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    )


def _env_values(path: Path | None = None) -> dict[str, str]:
    path = path or DEBUG_ENV
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(errors="replace").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _assert_debug_target() -> dict[str, str]:
    expected = Path("/home/zhihong/claude-relay-service-independent/app")
    if DEBUG_APP.resolve() != expected.resolve():
        raise ValueError("debug app guard rejected a non-debug path")
    values = _env_values()
    required = {
        "HOST": "127.0.0.1",
        "PORT": DEBUG_PORT,
        "REDIS_HOST": DEBUG_REDIS_HOST,
        "REDIS_PORT": DEBUG_REDIS_PORT,
        "REDIS_DB": DEBUG_REDIS_DB,
    }
    mismatches = {
        key: {"expected": expected_value, "actual": values.get(key)}
        for key, expected_value in required.items()
        if values.get(key) != expected_value
    }
    if mismatches:
        raise ValueError(f"debug isolation guard failed: {json.dumps(mismatches, sort_keys=True)}")
    if DEBUG_SESSION != "crs-debug-12392":
        raise ValueError("debug tmux session guard failed")
    return required


def _audit_dir() -> Path:
    configured = os.environ.get("CHATCRS_AUDIT_DIR")
    return Path(configured).expanduser() if configured else Path.home() / ".chatarch/chatcrs/audit"


def _write_audit(name: str, payload: dict[str, Any]) -> Path:
    destination = _audit_dir() / f"{_stamp()}-{name}.safe.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(redact(payload), ensure_ascii=False, indent=2) + "\n")
    destination.chmod(0o600)
    return destination


def _git(args: list[str], *, runner: Runner = _run, timeout: int = 30) -> dict[str, Any]:
    return runner(["git", "-C", str(DEBUG_APP), *args], timeout=timeout)


def _health(probe: Probe = http_status) -> dict[str, Any]:
    return probe(f"{DEBUG_BASE_URL}/health")


def debug_status(*, runner: Runner = _run, probe: Probe = http_status) -> dict[str, Any]:
    values = _env_values()
    tmux = runner(["tmux", "has-session", "-t", DEBUG_SESSION])
    pane = runner(
        [
            "tmux",
            "list-panes",
            "-t",
            DEBUG_SESSION,
            "-F",
            "#{pane_pid}|#{pane_current_path}|#{pane_current_command}|#{pane_start_command}",
        ]
    )
    redis_env = os.environ.copy()
    if values.get("REDIS_PASSWORD"):
        redis_env["REDISCLI_AUTH"] = values["REDIS_PASSWORD"]
    redis = runner(
        ["redis-cli", "-h", DEBUG_REDIS_HOST, "-p", DEBUG_REDIS_PORT, "ping"],
        env=redis_env,
    )
    branch = _git(["branch", "--show-current"], runner=runner)
    head = _git(["rev-parse", "HEAD"], runner=runner)
    status = _git(["status", "--short", "--branch"], runner=runner)
    health = _health(probe)
    version = (DEBUG_APP / "VERSION").read_text().strip() if (DEBUG_APP / "VERSION").exists() else None
    safe_settings = {key: values.get(key) for key in SAFE_SETTING_RULES}
    isolation = {
        "host": values.get("HOST"),
        "port": values.get("PORT"),
        "redis_host": values.get("REDIS_HOST"),
        "redis_port": values.get("REDIS_PORT"),
        "redis_db": values.get("REDIS_DB"),
    }
    return redact(
        {
            "ok": health.get("status") == 200
            and tmux.get("returncode") == 0
            and "PONG" in redis.get("stdout", ""),
            "mutated": False,
            "target": "debug",
            "app": str(DEBUG_APP),
            "base_url": DEBUG_BASE_URL,
            "health": health,
            "tmux": {
                "session": DEBUG_SESSION,
                "active": tmux.get("returncode") == 0,
                "pane": pane.get("stdout", ""),
            },
            "redis": {
                "host": DEBUG_REDIS_HOST,
                "port": DEBUG_REDIS_PORT,
                "db": DEBUG_REDIS_DB,
                "ping": redis.get("stdout", ""),
            },
            "git": {
                "branch": branch.get("stdout", ""),
                "head": head.get("stdout", ""),
                "status": status.get("stdout", ""),
            },
            "version": version,
            "isolation": isolation,
            "settings": safe_settings,
            "log": str(DEBUG_LOG),
        }
    )


def debug_logs(lines: int = 100, *, log_path: Path | None = None) -> dict[str, Any]:
    log_path = log_path or DEBUG_LOG
    if lines < 1 or lines > 2000:
        raise ValueError("lines must be between 1 and 2000")
    if not log_path.exists():
        return {
            "ok": False,
            "mutated": False,
            "target": "debug",
            "path": str(log_path),
            "lines": [],
            "reason": "log_not_found",
        }
    with log_path.open(errors="replace") as handle:
        selected = list(deque(handle, maxlen=lines))
    return redact(
        {
            "ok": True,
            "mutated": False,
            "target": "debug",
            "path": str(log_path),
            "requested_lines": lines,
            "lines": [line.rstrip("\n") for line in selected],
        }
    )


def _wait_health(probe: Probe = http_status, *, attempts: int = 45) -> dict[str, Any]:
    result: dict[str, Any] = {"status": "error", "ok": False}
    for _ in range(attempts):
        result = _health(probe)
        if result.get("status") == 200:
            return result
        time.sleep(1)
    return result


def restart_debug(
    *,
    execute: bool = False,
    runner: Runner = _run,
    probe: Probe = http_status,
    enforce_guard: bool = True,
) -> dict[str, Any]:
    plan: dict[str, Any] = {
        "ok": True,
        "target": "debug",
        "mode": "execute" if execute else "dry-run",
        "mutated": False,
        "session": DEBUG_SESSION,
        "app": str(DEBUG_APP),
        "base_url": DEBUG_BASE_URL,
        "steps": [
            f"validate fixed debug isolation on port {DEBUG_PORT} and Redis {DEBUG_REDIS_PORT}/0",
            f"kill only tmux session {DEBUG_SESSION} if present",
            f"start only tmux session {DEBUG_SESSION} from {DEBUG_APP}",
            "wait for debug /health HTTP 200",
        ],
    }
    if not execute:
        return plan
    if enforce_guard:
        _assert_debug_target()

    runner(["tmux", "kill-session", "-t", DEBUG_SESSION])
    start_command = (
        f"exec {shlex.quote(str(NODE))} src/app.js 2>&1 | "
        f"tee -a {shlex.quote(str(DEBUG_LOG))}"
    )
    target = f"{DEBUG_SESSION}:0.0"
    created = runner(
        ["tmux", "new-session", "-d", "-s", DEBUG_SESSION, "-c", str(DEBUG_APP)],
        timeout=30,
    )
    sent = {"returncode": 1, "stdout": "", "stderr": "session creation failed"}
    entered = {"returncode": 1, "stdout": "", "stderr": "command was not sent"}
    if created.get("returncode") == 0:
        sent = runner(["tmux", "send-keys", "-t", target, "-l", start_command])
        if sent.get("returncode") == 0:
            entered = runner(["tmux", "send-keys", "-t", target, "Enter"])
    command_started = all(
        item.get("returncode") == 0 for item in [created, sent, entered]
    )
    health = _wait_health(probe) if command_started else _health(probe)
    result = {
        **plan,
        "ok": command_started and health.get("status") == 200,
        "mutated": True,
        "start": {
            "session": created,
            "command": sent,
            "enter": entered,
        },
        "health": health,
    }
    result["audit"] = str(_write_audit("debug-restart", result))
    return redact(result)


def show_debug_settings() -> dict[str, Any]:
    values = _env_values()
    return {
        "ok": DEBUG_ENV.exists(),
        "mutated": False,
        "target": "debug",
        "env_file": str(DEBUG_ENV),
        "settings": {key: values.get(key) for key in SAFE_SETTING_RULES},
        "allowed": sorted(SAFE_SETTING_RULES),
        "protected": sorted(PROTECTED_SETTINGS),
    }


def validate_debug_setting(key: str, value: str) -> str:
    if key in PROTECTED_SETTINGS:
        raise ValueError(f"{key} is protected by the debug isolation guard")
    rule = SAFE_SETTING_RULES.get(key)
    if rule is None:
        raise ValueError(f"unsupported setting {key}; allowed: {', '.join(sorted(SAFE_SETTING_RULES))}")
    normalized = value.strip()
    if "choices" in rule and normalized not in rule["choices"]:
        raise ValueError(f"{key} must be one of: {', '.join(sorted(rule['choices']))}")
    if "pattern" in rule and not re.fullmatch(rule["pattern"], normalized):
        raise ValueError(f"invalid value for {key}")
    if "integer" in rule:
        try:
            number = int(normalized)
        except ValueError as exc:
            raise ValueError(f"{key} must be an integer") from exc
        minimum, maximum = rule["integer"]
        if not minimum <= number <= maximum:
            raise ValueError(f"{key} must be between {minimum} and {maximum}")
        normalized = str(number)
    if "text" in rule:
        if not normalized or len(normalized) > rule["text"] or "\n" in normalized:
            raise ValueError(f"{key} must be 1-{rule['text']} characters on one line")
    return normalized


def _serialize_env_value(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9._:/-]+", value):
        return value
    return json.dumps(value, ensure_ascii=False)


def _updated_env_text(original: str, key: str, value: str) -> str:
    replacement = f"{key}={_serialize_env_value(value)}"
    output: list[str] = []
    replaced = False
    for line in original.splitlines():
        if line.startswith(f"{key}="):
            output.append(replacement)
            replaced = True
        else:
            output.append(line)
    if not replaced:
        if output and output[-1] != "":
            output.append("")
        output.append(replacement)
    return "\n".join(output).rstrip() + "\n"


def set_debug_setting(
    key: str,
    value: str,
    *,
    execute: bool = False,
    runner: Runner = _run,
    probe: Probe = http_status,
    enforce_guard: bool = True,
) -> dict[str, Any]:
    normalized = validate_debug_setting(key, value)
    values = _env_values()
    current = values.get(key)
    plan: dict[str, Any] = {
        "ok": True,
        "target": "debug",
        "mode": "execute" if execute else "dry-run",
        "mutated": False,
        "env_file": str(DEBUG_ENV),
        "setting": key,
        "current": current,
        "proposed": normalized,
        "changed": current != normalized,
        "restart_required": current != normalized,
    }
    if not execute or current == normalized:
        return plan
    if enforce_guard:
        _assert_debug_target()

    audit_dir = _audit_dir() / _stamp()
    audit_dir.mkdir(parents=True, exist_ok=False)
    audit_dir.chmod(0o700)
    backup = audit_dir / ".env.before"
    shutil.copy2(DEBUG_ENV, backup)
    backup.chmod(0o600)
    updated = _updated_env_text(DEBUG_ENV.read_text(errors="strict"), key, normalized)
    with tempfile.NamedTemporaryFile("w", dir=DEBUG_ENV.parent, delete=False) as handle:
        handle.write(updated)
        temporary = Path(handle.name)
    temporary.chmod(0o600)
    os.replace(temporary, DEBUG_ENV)

    restart = restart_debug(execute=True, runner=runner, probe=probe, enforce_guard=enforce_guard)
    if not restart.get("ok"):
        shutil.copy2(backup, DEBUG_ENV)
        DEBUG_ENV.chmod(0o600)
        restored = restart_debug(execute=True, runner=runner, probe=probe, enforce_guard=enforce_guard)
        raise RuntimeError(f"debug restart failed; env restored; recovery_ok={restored.get('ok')}")

    result = {
        **plan,
        "mutated": True,
        "backup": str(backup),
        "restart": restart,
    }
    result["audit"] = str(_write_audit("debug-setting", result))
    return redact(result)


def upgrade_plan(*, runner: Runner = _run) -> dict[str, Any]:
    current_head = _git(["rev-parse", "HEAD"], runner=runner)
    current_tree = _git(["rev-parse", "HEAD^{tree}"], runner=runner)
    status = _git(["status", "--porcelain"], runner=runner)
    origin_url = _git(["remote", "get-url", "origin"], runner=runner)
    local_target = _git(["rev-parse", "origin/dev"], runner=runner)
    target_tree = _git(["rev-parse", "origin/dev^{tree}"], runner=runner)
    remote = runner(["git", "ls-remote", origin_url.get("stdout", ""), "refs/heads/dev"])
    remote_sha = remote.get("stdout", "").split()[0] if remote.get("stdout") else None
    local_sha = local_target.get("stdout", "") or None
    return {
        "ok": all(
            result.get("returncode") == 0
            for result in [current_head, current_tree, status, origin_url, local_target, target_tree, remote]
        ),
        "mutated": False,
        "target": "debug",
        "app": str(DEBUG_APP),
        "current": {
            "sha": current_head.get("stdout", ""),
            "tree": current_tree.get("stdout", ""),
            "clean": status.get("stdout", "") == "",
        },
        "dev": {
            "local_ref_sha": local_sha,
            "remote_sha": remote_sha,
            "local_ref_current": local_sha == remote_sha,
            "tree": target_tree.get("stdout", ""),
        },
        "already_target_tree": current_tree.get("stdout") == target_tree.get("stdout"),
        "execute_requires": ["--execute", "--expected-sha <remote-dev-sha>"],
        "steps": [
            "validate debug isolation and clean worktree",
            "back up current SHA and debug .env",
            "fetch exact origin/dev",
            "stop only tmux crs-debug-12392",
            "checkout exact expected SHA",
            "run npm ci and build web assets",
            "restart only debug tmux and verify health",
            "restore previous SHA/env and restart on failure",
        ],
    }


def apply_debug_upgrade(
    expected_sha: str | None,
    *,
    execute: bool = False,
    runner: Runner = _run,
    probe: Probe = http_status,
    enforce_guard: bool = True,
) -> dict[str, Any]:
    plan = upgrade_plan(runner=runner)
    plan["mode"] = "execute" if execute else "dry-run"
    if not execute:
        return plan
    if enforce_guard:
        _assert_debug_target()
    if not expected_sha or not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise ValueError("--expected-sha must be a full 40-character Git SHA")
    if plan["dev"]["remote_sha"] != expected_sha:
        raise ValueError("remote dev SHA differs from --expected-sha; rerun upgrade plan")
    if not plan["current"]["clean"]:
        raise ValueError("debug worktree is dirty; upgrade refused")
    if plan["already_target_tree"] and plan["dev"]["local_ref_current"]:
        return {**plan, "ok": True, "mutated": False, "reason": "already_target_tree"}

    stamp = _stamp()
    audit_dir = _audit_dir() / f"upgrade-{stamp}"
    audit_dir.mkdir(parents=True, exist_ok=False)
    audit_dir.chmod(0o700)
    previous_sha = plan["current"]["sha"]
    env_backup = audit_dir / ".env.before"
    shutil.copy2(DEBUG_ENV, env_backup)
    env_backup.chmod(0o600)
    (audit_dir / "previous-sha.txt").write_text(f"{previous_sha}\n")

    runner(["tmux", "kill-session", "-t", DEBUG_SESSION])
    try:
        fetch = _git(["fetch", "origin", "dev"], runner=runner, timeout=180)
        if fetch.get("returncode") != 0:
            raise RuntimeError("git fetch origin dev failed")
        checkout = _git(["checkout", "--detach", expected_sha], runner=runner)
        if checkout.get("returncode") != 0:
            raise RuntimeError("git checkout target failed")
        install = runner([str(NPM), "ci"], timeout=1200, cwd=DEBUG_APP)
        if install.get("returncode") != 0:
            raise RuntimeError("npm ci failed")
        web_install = runner([str(NPM), "run", "install:web"], timeout=1200, cwd=DEBUG_APP)
        if web_install.get("returncode") != 0:
            raise RuntimeError("web dependency install failed")
        web_build = runner([str(NPM), "run", "build:web"], timeout=1200, cwd=DEBUG_APP)
        if web_build.get("returncode") != 0:
            raise RuntimeError("web build failed")
        restart = restart_debug(execute=True, runner=runner, probe=probe, enforce_guard=enforce_guard)
        if not restart.get("ok"):
            raise RuntimeError("debug health failed after upgrade")
    except BaseException as original_error:
        recovery_failures = []
        checkout_previous = _git(["checkout", "--detach", previous_sha], runner=runner)
        if checkout_previous.get("returncode") != 0:
            recovery_failures.append("checkout_previous")
        shutil.copy2(env_backup, DEBUG_ENV)
        DEBUG_ENV.chmod(0o600)
        for name, command, timeout in [
            ("npm_ci", [str(NPM), "ci"], 1200),
            ("web_install", [str(NPM), "run", "install:web"], 1200),
            ("web_build", [str(NPM), "run", "build:web"], 1200),
        ]:
            recovery = runner(command, timeout=timeout, cwd=DEBUG_APP)
            if recovery.get("returncode") != 0:
                recovery_failures.append(name)
        restarted = restart_debug(
            execute=True,
            runner=runner,
            probe=probe,
            enforce_guard=enforce_guard,
        )
        if not restarted.get("ok"):
            recovery_failures.append("restart_previous")
        if recovery_failures:
            raise RuntimeError(
                f"debug upgrade failed and recovery was incomplete: {', '.join(recovery_failures)}"
            ) from original_error
        raise

    result = {
        **plan,
        "ok": True,
        "mutated": True,
        "target_sha": expected_sha,
        "previous_sha": previous_sha,
        "backup": str(env_backup),
        "restart": restart,
    }
    result["audit"] = str(_write_audit("debug-upgrade", result))
    return redact(result)


__all__ = [
    "SAFE_SETTING_RULES",
    "PROTECTED_SETTINGS",
    "apply_debug_upgrade",
    "debug_logs",
    "debug_status",
    "restart_debug",
    "set_debug_setting",
    "show_debug_settings",
    "upgrade_plan",
    "validate_debug_setting",
]
