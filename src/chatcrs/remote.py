"""Remote CRS HTTP API helpers for ChatCRS."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from chatcrs.redaction import redact

DEFAULT_CRS_PROFILE = "admin"
DEFAULT_CHATARCH_HOME = Path("~/.chatarch")


@dataclass(frozen=True)
class CrsProfile:
    """Connection and credential material for a remote CRS target."""

    base_url: str
    api_key: str = ""
    username: str = ""
    password: str = ""
    admin_token: str = ""

    def safe_summary(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "api_key_present": bool(self.api_key),
            "username_present": bool(self.username),
            "password_present": bool(self.password),
            "admin_token_present": bool(self.admin_token),
        }


def _strip_env_value(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1]
    return stripped


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = _strip_env_value(value)
    return values


def load_crs_profile(profile: str = DEFAULT_CRS_PROFILE, *, home: str | Path | None = None) -> CrsProfile:
    """Load a CRS profile from ChatEnv-style ``envs/CRS/<profile>.env``.

    The user's current CRS admin profile uses the generic ``CRS_*`` keys. ChatCRS
    also accepts ``CHATCRS_*`` aliases for forward compatibility.
    """

    chatarch_home = Path(home or os.environ.get("CHATARCH_HOME") or DEFAULT_CHATARCH_HOME).expanduser()
    values = _read_env_file(chatarch_home / "envs" / "CRS" / f"{profile}.env")
    base_url = (
        values.get("CRS_API_BASE")
        or values.get("CRS_BASE_URL")
        or values.get("CHATCRS_BASE_URL")
        or os.environ.get("CRS_API_BASE")
        or os.environ.get("CRS_BASE_URL")
        or os.environ.get("CHATCRS_BASE_URL")
        or ""
    ).rstrip("/")
    return CrsProfile(
        base_url=base_url,
        api_key=values.get("CRS_API_KEY") or values.get("CHATCRS_API_KEY") or os.environ.get("CRS_API_KEY", ""),
        username=values.get("CRS_USERNAME") or values.get("CHATCRS_ADMIN_USERNAME") or os.environ.get("CRS_USERNAME", ""),
        password=values.get("CRS_PASSWORD") or values.get("CHATCRS_ADMIN_PASSWORD") or os.environ.get("CRS_PASSWORD", ""),
        admin_token=(
            values.get("CRS_ACCESS_TOKEN")
            or values.get("CRS_ADMIN_TOKEN")
            or values.get("CHATCRS_ADMIN_TOKEN")
            or os.environ.get("CRS_ACCESS_TOKEN", "")
        ),
    )


def resolve_profile(
    *,
    profile: str = DEFAULT_CRS_PROFILE,
    base_url: str | None = None,
    api_key: str | None = None,
    username: str | None = None,
    password: str | None = None,
    admin_token: str | None = None,
) -> CrsProfile:
    loaded = load_crs_profile(profile)
    return replace(
        loaded,
        base_url=(base_url or loaded.base_url).rstrip("/"),
        api_key=api_key if api_key is not None else loaded.api_key,
        username=username if username is not None else loaded.username,
        password=password if password is not None else loaded.password,
        admin_token=admin_token if admin_token is not None else loaded.admin_token,
    )


class CrsApiError(RuntimeError):
    """Raised when a CRS HTTP API request fails."""

    def __init__(self, message: str, *, status: int | None = None, body: Any = None):
        super().__init__(message)
        self.status = status
        self.body = body


class CrsHttpClient:
    """Small stdlib-only CRS HTTP client for admin and API-key endpoints."""

    def __init__(self, profile: CrsProfile, *, timeout: float = 20.0):
        if not profile.base_url:
            raise ValueError("CRS base URL is required; set CRS_API_BASE or pass --base-url")
        self.profile = profile
        self.timeout = timeout
        self._admin_token = profile.admin_token

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, Any]:
        body = None
        request_headers = {"accept": "application/json"}
        if headers:
            request_headers.update(headers)
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            request_headers["content-type"] = "application/json"
        request = urllib.request.Request(
            f"{self.profile.base_url}{path}",
            data=body,
            headers=request_headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_body = response.read()
                status = response.status
        except urllib.error.HTTPError as exc:
            response_body = exc.read()
            status = exc.code
        try:
            parsed: Any = json.loads(response_body.decode("utf-8")) if response_body else {}
        except json.JSONDecodeError:
            parsed = {"raw": response_body.decode("utf-8", errors="replace")}
        return status, parsed

    def login(self) -> dict[str, Any]:
        if not self.profile.username or not self.profile.password:
            raise ValueError("CRS admin username/password are required for login")
        status, parsed = self._request_json(
            "POST",
            "/web/auth/login",
            payload={"username": self.profile.username, "password": self.profile.password},
        )
        if status != 200 or not isinstance(parsed, dict) or not parsed.get("token"):
            raise CrsApiError("CRS admin login failed", status=status, body=redact(parsed))
        self._admin_token = str(parsed["token"])
        return {
            "ok": True,
            "status": status,
            "username": parsed.get("username"),
            "expiresIn": parsed.get("expiresIn"),
            "token_present": True,
        }

    def _admin_headers(self) -> dict[str, str]:
        if not self._admin_token:
            self.login()
        return {"authorization": f"Bearer {self._admin_token}"}

    def admin_request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        return self._request_json(method, path, payload=payload, headers=self._admin_headers())

    def accounts_usage(self) -> dict[str, Any]:
        status, parsed = self.admin_request("GET", "/admin/openai-accounts")
        ok = status == 200 and isinstance(parsed, dict) and parsed.get("success") is not False
        accounts = parsed.get("data", []) if isinstance(parsed, dict) else []
        return {
            "ok": ok,
            "mutated": False,
            "status": status,
            "accounts": redact(accounts),
            "count": len(accounts) if isinstance(accounts, list) else 0,
        }

    def reset_openai_account_status(self, account_id: str) -> dict[str, Any]:
        status, parsed = self.admin_request("POST", f"/admin/openai-accounts/{account_id}/reset-status")
        return {
            "ok": status == 200 and isinstance(parsed, dict) and parsed.get("success") is not False,
            "mutated": True,
            "status": status,
            "account_id": account_id,
            "body": redact(parsed),
        }

    def api_keys(self, *, include_stats: bool = False, time_range: str = "all") -> dict[str, Any]:
        status, parsed = self.admin_request("GET", "/admin/api-keys")
        ok = status == 200 and isinstance(parsed, dict) and parsed.get("success") is not False
        data = parsed.get("data", []) if isinstance(parsed, dict) else []
        pagination: dict[str, Any] | None = None
        if isinstance(data, dict):
            keys = data.get("items", [])
            pagination = data.get("pagination") if isinstance(data.get("pagination"), dict) else None
        else:
            keys = data
        if not isinstance(keys, list):
            keys = []

        stats: dict[str, Any] = {}
        last_usage: dict[str, Any] = {}
        key_ids = [str(item.get("id") or item.get("keyId")) for item in keys if isinstance(item, dict) and (item.get("id") or item.get("keyId"))]
        if include_stats and key_ids:
            stats_status, stats_payload = self.admin_request(
                "POST",
                "/admin/api-keys/batch-stats",
                payload={"keyIds": key_ids, "timeRange": time_range},
            )
            if stats_status == 200 and isinstance(stats_payload, dict):
                stats = stats_payload.get("data", {}) or {}
            usage_status, usage_payload = self.admin_request(
                "POST",
                "/admin/api-keys/batch-last-usage",
                payload={"keyIds": key_ids},
            )
            if usage_status == 200 and isinstance(usage_payload, dict):
                last_usage = usage_payload.get("data", {}) or {}

        enriched = []
        for item in keys:
            if not isinstance(item, dict):
                continue
            key_id = str(item.get("id") or item.get("keyId") or "")
            safe_item = redact(item)
            if include_stats:
                safe_item["stats"] = redact(stats.get(key_id, {}))
                safe_item["last_usage"] = redact(last_usage.get(key_id))
            enriched.append(safe_item)

        return {
            "ok": ok,
            "mutated": False,
            "status": status,
            "count": len(enriched),
            "pagination": pagination,
            "keys": enriched,
        }

    def api_key_detail(self, key_id: str, *, include_stats: bool = True, time_range: str = "all") -> dict[str, Any]:
        payload = self.api_keys(include_stats=include_stats, time_range=time_range)
        matches = [item for item in payload["keys"] if str(item.get("id") or item.get("keyId")) == key_id or item.get("name") == key_id]
        return {
            "ok": bool(matches),
            "mutated": False,
            "key": matches[0] if matches else None,
            "query": key_id,
            "source_count": payload["count"],
        }

    def key_info(self, *, api_key: str | None = None, path: str = "/openai/key-info") -> dict[str, Any]:
        key = api_key or self.profile.api_key
        if not key:
            raise ValueError("CRS API key is required; set CRS_API_KEY or pass --api-key")
        status, parsed = self._request_json("GET", path, headers={"authorization": f"Bearer {key}"})
        return {
            "ok": status == 200,
            "mutated": False,
            "status": status,
            "key_info": redact(parsed),
        }


def client_from_options(
    *,
    profile: str = DEFAULT_CRS_PROFILE,
    base_url: str | None = None,
    api_key: str | None = None,
    username: str | None = None,
    password: str | None = None,
    admin_token: str | None = None,
    timeout: float = 20.0,
) -> CrsHttpClient:
    return CrsHttpClient(
        resolve_profile(
            profile=profile,
            base_url=base_url,
            api_key=api_key,
            username=username,
            password=password,
            admin_token=admin_token,
        ),
        timeout=timeout,
    )
