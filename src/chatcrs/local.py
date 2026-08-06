from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_BASE_URL = "http://127.0.0.1:12390"


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def normalize_base_url(base_url: str | None = None) -> str:
    value = base_url or os.environ.get("CRS_API_BASE") or DEFAULT_BASE_URL
    return value.rstrip("/")


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
