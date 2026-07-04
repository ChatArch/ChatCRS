from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REDACTED = "[REDACTED]"
DEFAULT_BASE_URL = "http://127.0.0.1:12392"


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def normalize_base_url(base_url: str | None = None) -> str:
    value = base_url or os.environ.get("CHATCRS_BASE_URL") or DEFAULT_BASE_URL
    return value.rstrip("/")


def load_local_secrets(path: str | Path) -> dict[str, Any]:
    secrets_path = Path(path).expanduser().resolve()
    values: dict[str, Any] = {}
    for line in secrets_path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    values["_path"] = str(secrets_path)
    values["_redacted"] = {
        key: (REDACTED if key.endswith("PASSWORD") or key.endswith("SECRET") or key.endswith("KEY") else value)
        for key, value in values.items()
        if not key.startswith("_")
    }
    return values


def _request_status(base_url: str, path: str, *, method: str = "GET", body: bytes | None = None, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    opener = urllib.request.build_opener(NoRedirectHandler)
    request = urllib.request.Request(f"{base_url}{path}", data=body, method=method, headers=headers or {})
    try:
        with opener.open(request, timeout=10) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def health_check(base_url: str | None = None) -> dict[str, Any]:
    base = normalize_base_url(base_url)
    status, body = _request_status(base, "/health")
    parsed: Any
    try:
        parsed = json.loads(body.decode("utf-8")) if body else {}
    except json.JSONDecodeError:
        parsed = {"raw": body.decode("utf-8", errors="replace")}
    return {
        "ok": status == 200 and parsed.get("status") == "healthy",
        "base_url": base,
        "mutated": False,
        "health": {"status": status, "body": parsed},
    }


def admin_login(base_url: str, secrets_file: str | Path) -> dict[str, Any]:
    secrets = load_local_secrets(secrets_file)
    payload = json.dumps(
        {
            "username": secrets.get("ADMIN_USERNAME", ""),
            "password": secrets.get("ADMIN_PASSWORD", ""),
        }
    ).encode("utf-8")
    status, body = _request_status(
        base_url,
        "/web/auth/login",
        method="POST",
        body=payload,
        headers={"content-type": "application/json"},
    )
    parsed: Any
    try:
        parsed = json.loads(body.decode("utf-8")) if body else {}
    except json.JSONDecodeError:
        parsed = {"raw": body.decode("utf-8", errors="replace")}
    if isinstance(parsed, dict):
        parsed = {key: (REDACTED if key == "token" else value) for key, value in parsed.items()}
    return {"status": status, "ok": status == 200, "body": parsed, "secrets": secrets["_redacted"]}


def verify_local_crs(base_url: str | None = None, secrets_file: str | Path | None = None) -> dict[str, Any]:
    base = normalize_base_url(base_url)
    health = health_check(base)
    admin_status, _ = _request_status(base, "/admin-next/")
    root_status, _ = _request_status(base, "/")
    api_status, _ = _request_status(
        base,
        "/api/v1/messages",
        method="POST",
        body=b"{}",
        headers={"content-type": "application/json"},
    )
    admin_payload = None
    if secrets_file:
        admin_payload = admin_login(base, secrets_file)
    checks = {
        "health": health["ok"],
        "admin_next": admin_status == 200,
        "root_redirect": root_status in {301, 302},
        "api_route_auth_protected": api_status in {400, 401, 403},
    }
    if admin_payload is not None:
        checks["admin_login"] = bool(admin_payload.get("ok"))
    return {
        "ok": all(checks.values()),
        "base_url": base,
        "mutated": False,
        "checks": checks,
        "health": health["health"],
        "admin_next": {"status": admin_status},
        "root": {"status": root_status},
        "api_messages_no_auth": {"status": api_status},
        "admin_login": admin_payload,
    }
