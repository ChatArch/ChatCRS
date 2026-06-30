"""Read-only runtime probes used by ChatCRS management APIs."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
from urllib import error, request

from .paths import CrsPaths
from .redaction import redact


def run_command(args: list[str], *, timeout: int = 20) -> dict[str, Any]:
    """Run a command and return a redacted structured result."""

    try:
        proc = subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        return {"cmd": args, "returncode": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired:
        return {"cmd": args, "returncode": 124, "stdout": "", "stderr": "timeout"}
    return redact({
        "cmd": args,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    })


def http_status(url: str, *, method: str = "GET", body: bytes | None = None, headers: dict[str, str] | None = None, timeout: int = 5) -> dict[str, Any]:
    """Return an HTTP status probe result without raising for HTTP errors."""

    req = request.Request(url, method=method, data=body, headers=headers or {})
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return {"url": url, "status": resp.status, "ok": 200 <= resp.status < 500}
    except error.HTTPError as exc:
        return {"url": url, "status": exc.code, "ok": 200 <= exc.code < 500}
    except Exception as exc:  # pragma: no cover - depends on host networking
        return {"url": url, "status": "error", "ok": False, "error_type": type(exc).__name__}


def env_value(env_file: Path, key: str, default: str | None = None) -> str | None:
    """Read a single key from a dotenv-style file without interpolation."""

    if not env_file.exists():
        return default
    for line in env_file.read_text(errors="replace").splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return default


def nginx_proxy_line(config: Path) -> str:
    """Return the first CRS proxy_pass line from an Nginx config."""

    if not config.exists():
        return ""
    for line in config.read_text(errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("proxy_pass http://127.0.0.1:"):
            return stripped
    return ""


def systemd_user_status(service: str) -> dict[str, str]:
    """Return systemd user service active/enabled/main-pid state."""

    active = run_command(["systemctl", "--user", "is-active", service])["stdout"]
    enabled = run_command(["systemctl", "--user", "is-enabled", service])["stdout"]
    main_pid = run_command(["systemctl", "--user", "show", service, "-p", "MainPID", "--value"])["stdout"]
    return {"service": service, "active": active, "enabled": enabled, "main_pid": main_pid}


def default_probe(paths: CrsPaths, name: str) -> Any:
    """Probe one named read-only fact for cutover/verify helpers."""

    if name == "old_health":
        return http_status(f"http://127.0.0.1:{paths.old_port}/health")
    if name == "new_health":
        return http_status(f"http://127.0.0.1:{paths.new_port}/health")
    if name == "new_images_no_auth":
        return http_status(
            f"http://127.0.0.1:{paths.new_port}/openai/v1/images/generations",
            method="POST",
            body=b'{"model":"gpt-image-2","prompt":"smoke","n":1}',
            headers={"Content-Type": "application/json"},
        )
    if name == "systemd":
        return systemd_user_status(paths.new_service)
    if name == "nginx_proxy_line":
        return nginx_proxy_line(paths.nginx_config_path)
    if name == "redis":
        return {
            "db0_size": run_command(["redis-cli", "-n", "0", "dbsize"])["stdout"],
            "db1_size": run_command(["redis-cli", "-n", "1", "dbsize"])["stdout"],
        }
    if name == "new_redis_db":
        return env_value(paths.new_app_path / ".env", "REDIS_DB", "0") or "0"
    raise KeyError(name)
