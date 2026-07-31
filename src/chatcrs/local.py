from __future__ import annotations

import base64
import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REDACTED = "[REDACTED]"
DEFAULT_BASE_URL = "http://127.0.0.1:12392"
DEFAULT_OPENAI_ENV_FILE = Path("~/.chatarch/envs/OpenAI/.env")


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


def _request_status(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 10,
) -> tuple[int, bytes]:
    opener = urllib.request.build_opener(NoRedirectHandler)
    request = urllib.request.Request(f"{base_url}{path}", data=body, method=method, headers=headers or {})
    try:
        with opener.open(request, timeout=timeout) as response:
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


def load_openai_api_key(path: str | Path | None = None) -> tuple[str, Path]:
    configured = path or os.environ.get("CHATCRS_OPENAI_ENV_FILE") or DEFAULT_OPENAI_ENV_FILE
    env_path = Path(configured).expanduser().resolve()
    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.strip()] = value
    api_key = values.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(f"OPENAI_API_KEY is missing from {env_path}")
    return api_key, env_path


def verify_images_api(
    *,
    base_url: str | None = None,
    openai_env_file: str | Path | None = None,
    regular_model: str = "gpt-5.5",
    image_model: str = "gpt-image-2",
    prompt: str = "A single orange triangle on a pale blue grid, minimalist icon, no text.",
    output_path: str | Path = "chatcrs-image-acceptance.png",
    execute_image: bool = False,
    timeout_seconds: float = 600,
) -> dict[str, Any]:
    base = normalize_base_url(base_url)
    api_key, env_path = load_openai_api_key(openai_env_file)
    auth_headers = {"authorization": f"Bearer {api_key}"}

    key_status, key_body = _request_status(base, "/openai/key-info", headers=auth_headers)
    try:
        key_payload = json.loads(key_body.decode("utf-8")) if key_body else {}
    except json.JSONDecodeError:
        key_payload = {}
    key_check = {
        "ok": key_status == 200,
        "status": key_status,
        "name": key_payload.get("name") if isinstance(key_payload, dict) else None,
        "permissions": key_payload.get("permissions") if isinstance(key_payload, dict) else None,
    }

    marker = "CHATCRS_KEY_OK"
    regular_payload = json.dumps(
        {
            "model": regular_model,
            "store": False,
            "stream": True,
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": f"Reply with exactly {marker}"}],
                }
            ],
        }
    ).encode("utf-8")
    regular_status, regular_body = _request_status(
        base,
        "/openai/v1/responses",
        method="POST",
        body=regular_payload,
        headers={**auth_headers, "content-type": "application/json", "accept": "text/event-stream"},
        timeout=min(timeout_seconds, 180),
    )
    regular_text = regular_body.decode("utf-8", errors="replace")
    regular_check = {
        "ok": regular_status == 200 and marker in regular_text,
        "status": regular_status,
        "model": regular_model,
        "expected_marker": marker in regular_text,
        "sse": "data:" in regular_text,
        "bytes": len(regular_body),
    }

    image_check: dict[str, Any] = {"executed": False, "ok": None, "model": image_model}
    if execute_image:
        image_payload = json.dumps(
            {
                "model": image_model,
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "quality": "low",
                "output_format": "png",
            }
        ).encode("utf-8")
        image_status, image_body = _request_status(
            base,
            "/openai/v1/images/generations",
            method="POST",
            body=image_payload,
            headers={**auth_headers, "content-type": "application/json"},
            timeout=timeout_seconds,
        )
        try:
            image_payload_result = json.loads(image_body.decode("utf-8")) if image_body else {}
        except json.JSONDecodeError:
            image_payload_result = {}
        encoded = ""
        if isinstance(image_payload_result, dict):
            data = image_payload_result.get("data")
            if isinstance(data, list) and data and isinstance(data[0], dict):
                encoded = str(data[0].get("b64_json") or "")
        image_bytes = b""
        if encoded:
            try:
                image_bytes = base64.b64decode(encoded, validate=True)
            except ValueError:
                image_bytes = b""
        is_png = image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        resolved_output = Path(output_path).expanduser().resolve()
        if is_png:
            resolved_output.parent.mkdir(parents=True, exist_ok=True)
            resolved_output.write_bytes(image_bytes)
        image_check = {
            "executed": True,
            "ok": image_status == 200 and is_png,
            "status": image_status,
            "model": image_model,
            "quality": "low",
            "png": is_png,
            "bytes": len(image_bytes),
            "sha256": hashlib.sha256(image_bytes).hexdigest() if image_bytes else None,
            "output_path": str(resolved_output) if is_png else None,
        }

    return {
        "ok": bool(key_check["ok"] and regular_check["ok"] and (not execute_image or image_check["ok"])),
        "base_url": base,
        "openai_env_file": str(env_path),
        "api_key": REDACTED,
        "mutated": execute_image,
        "key_info": key_check,
        "regular_model": regular_check,
        "image": image_check,
    }
