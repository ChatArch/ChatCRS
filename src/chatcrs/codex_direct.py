"""Direct OpenAI Codex account and usage helpers.

This module intentionally models only the direct ChatGPT/Codex account surface
needed for account/usage inspection. It never logs or returns raw token values in
safe output fields; callers that need persistence should use the explicit token
store helpers and still render only redacted summaries.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from chatenv import TokenStore

from chatcrs.redaction import redact

AUTH_BASE_URL = "https://auth.openai.com"
CHATGPT_BACKEND_BASE_URL = "https://chatgpt.com/backend-api"
OAUTH_TOKEN_URL = f"{AUTH_BASE_URL}/oauth/token"
ACCOUNTS_URL = f"{AUTH_BASE_URL}/api/accounts"
CODEX_USAGE_URL = f"{CHATGPT_BACKEND_BASE_URL}/codex/usage"
WHAM_USAGE_URL = f"{CHATGPT_BACKEND_BASE_URL}/wham/usage"
DEFAULT_OPENAI_CODEX_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
CODEX_SERVICE_NAME = "Codex"
CODEX_TOKEN_TYPE = "openai_codex_oauth"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _expires_at_from_expires_in(expires_in: Any) -> str:
    if expires_in is None:
        return ""
    try:
        seconds = int(float(expires_in))
    except (TypeError, ValueError):
        return ""
    if seconds <= 0:
        return ""
    return _iso(_now() + timedelta(seconds=seconds))


def _to_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _normalize_headers(headers: dict[str, Any] | None) -> dict[str, str]:
    normalized: dict[str, str] = {}
    if not headers:
        return normalized
    for key, value in headers.items():
        if not key:
            continue
        if isinstance(value, list):
            value = value[0] if value else ""
        normalized[str(key).lower()] = str(value)
    return normalized


def extract_codex_rate_limit_headers(headers: dict[str, Any] | None) -> dict[str, float | None]:
    """Extract Codex quota/rate-limit headers from a backend response."""

    normalized = _normalize_headers(headers)
    return {
        "primary_used_percent": _to_number(normalized.get("x-codex-primary-used-percent")),
        "primary_reset_after_seconds": _to_number(normalized.get("x-codex-primary-reset-after-seconds")),
        "primary_window_minutes": _to_number(normalized.get("x-codex-primary-window-minutes")),
        "secondary_used_percent": _to_number(normalized.get("x-codex-secondary-used-percent")),
        "secondary_reset_after_seconds": _to_number(normalized.get("x-codex-secondary-reset-after-seconds")),
        "secondary_window_minutes": _to_number(normalized.get("x-codex-secondary-window-minutes")),
        "primary_over_secondary_percent": _to_number(normalized.get("x-codex-primary-over-secondary-limit-percent")),
    }


def _request_json(
    method: str,
    url: str,
    *,
    data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 20.0,
) -> tuple[int, Any, dict[str, str]]:
    """Perform an HTTP JSON/form request using stdlib only."""

    request_headers = {"accept": "application/json"}
    if headers:
        request_headers.update(headers)
    body = None
    if data is not None:
        body = urllib.parse.urlencode({key: str(value) for key, value in data.items()}).encode("utf-8")
        request_headers["content-type"] = "application/x-www-form-urlencoded"
    request = urllib.request.Request(url, data=body, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = response.read()
            status = response.status
            response_headers = dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        response_body = exc.read()
        status = exc.code
        response_headers = dict(exc.headers.items())
    try:
        parsed: Any = json.loads(response_body.decode("utf-8")) if response_body else {}
    except json.JSONDecodeError:
        parsed = {"raw": response_body.decode("utf-8", errors="replace")}
    return status, parsed, response_headers


def refresh_access_token(
    *,
    refresh_token: str,
    client_id: str | None = None,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Exchange an OpenAI refresh token for a fresh access token."""

    if not refresh_token:
        raise ValueError("OpenAI refresh token is required")
    status, parsed, _headers = _request_json(
        "POST",
        OAUTH_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": client_id or DEFAULT_OPENAI_CODEX_CLIENT_ID,
            "refresh_token": refresh_token,
            "scope": "openid profile email",
        },
        timeout=timeout,
    )
    if status != 200 or not isinstance(parsed, dict) or not parsed.get("access_token"):
        return {
            "ok": False,
            "mutated": False,
            "status": status,
            "safe": redact(parsed),
            "values": {},
            "token_present": False,
            "refresh_token_rotated": False,
        }

    values: dict[str, Any] = {
        "access_token": parsed.get("access_token"),
        "token_type": parsed.get("token_type") or "Bearer",
    }
    if parsed.get("refresh_token"):
        values["refresh_token"] = parsed.get("refresh_token")
    if parsed.get("id_token"):
        values["id_token"] = parsed.get("id_token")
    expires_at = _expires_at_from_expires_in(parsed.get("expires_in"))
    safe = {
        "ok": True,
        "status": status,
        "token_present": True,
        "refresh_token_rotated": bool(parsed.get("refresh_token")),
        "expires_in": parsed.get("expires_in"),
        "expires_at": expires_at,
        "token_type": parsed.get("token_type") or "Bearer",
    }
    return {
        "ok": True,
        "mutated": False,
        "status": status,
        "safe": safe,
        "values": values,
        "token_present": True,
        "refresh_token_rotated": bool(parsed.get("refresh_token")),
        "expires_at": expires_at,
    }


def get_account(*, access_token: str, timeout: float = 20.0) -> dict[str, Any]:
    """Read ChatGPT/Codex account metadata using an access token."""

    if not access_token:
        raise ValueError("OpenAI access token is required")
    status, parsed, _headers = _request_json(
        "GET",
        ACCOUNTS_URL,
        headers={"authorization": f"Bearer {access_token}"},
        timeout=timeout,
    )
    accounts: Any = []
    if isinstance(parsed, dict):
        raw_accounts = parsed.get("accounts", parsed.get("data", parsed.get("items", [])))
        accounts = raw_accounts if isinstance(raw_accounts, list) else []
    return {
        "ok": status == 200,
        "mutated": False,
        "status": status,
        "account_count": len(accounts),
        "accounts": redact(accounts),
        "body": redact(parsed) if not accounts else None,
    }


def get_usage(
    *,
    access_token: str,
    account_id: str,
    timeout: float = 20.0,
    usage_url: str = CODEX_USAGE_URL,
) -> dict[str, Any]:
    """Read Codex token usage and quota headers for one ChatGPT account."""

    if not access_token:
        raise ValueError("OpenAI access token is required")
    if not account_id:
        raise ValueError("ChatGPT account id is required")
    status, parsed, headers = _request_json(
        "GET",
        usage_url,
        headers={
            "authorization": f"Bearer {access_token}",
            "chatgpt-account-id": account_id,
        },
        timeout=timeout,
    )
    return {
        "ok": status == 200,
        "mutated": False,
        "status": status,
        "account_id": account_id,
        "usage_url": usage_url,
        "rate_limits": extract_codex_rate_limit_headers(headers),
        "usage": redact(parsed),
    }


def _normalize_profile(profile: str | None) -> str:
    value = (profile or "default").strip()
    return value or "default"


def _token_store(home: str | Path | None = None) -> TokenStore:
    return TokenStore(home=home)


def read_stored_token(*, profile: str = "default", home: str | Path | None = None) -> dict[str, Any]:
    profile_name = _normalize_profile(profile)
    return _token_store(home).read(CODEX_SERVICE_NAME, profile_name)


def token_status(*, profile: str = "default", home: str | Path | None = None) -> dict[str, Any]:
    profile_name = _normalize_profile(profile)
    status = _token_store(home).status(CODEX_SERVICE_NAME, profile_name)
    status["token_type"] = read_stored_token(profile=profile_name, home=home).get("token_type", CODEX_TOKEN_TYPE)
    return status


def save_token_values(
    *,
    profile: str = "default",
    values: dict[str, Any],
    expires_at: str | None = None,
    source: str = "refresh",
    home: str | Path | None = None,
) -> dict[str, Any]:
    profile_name = _normalize_profile(profile)
    summary = {
        "access_token_present": bool(values.get("access_token")),
        "refresh_token_present": bool(values.get("refresh_token")),
        "id_token_present": bool(values.get("id_token")),
    }
    return _token_store(home).write(
        CODEX_SERVICE_NAME,
        profile_name,
        values={key: value for key, value in values.items() if value},
        token_type=CODEX_TOKEN_TYPE,
        summary=summary,
        expires_at=expires_at or "",
        source=source,
    )


def _stored_values(*, profile: str = "default", home: str | Path | None = None) -> dict[str, Any]:
    payload = read_stored_token(profile=profile, home=home)
    values = payload.get("values")
    return values if isinstance(values, dict) else {}


def _resolve_access_token(
    *,
    access_token: str | None,
    profile: str,
    refresh: bool,
    client_id: str | None,
    timeout: float,
    home: str | Path | None = None,
) -> tuple[str, dict[str, Any] | None]:
    if access_token:
        return access_token, None
    values = _stored_values(profile=profile, home=home)
    stored_access = values.get("access_token")
    if isinstance(stored_access, str) and stored_access:
        return stored_access, None
    if refresh:
        stored_refresh = values.get("refresh_token")
        if isinstance(stored_refresh, str) and stored_refresh:
            refreshed = refresh_access_token(refresh_token=stored_refresh, client_id=client_id, timeout=timeout)
            if refreshed.get("ok"):
                save_token_values(
                    profile=profile,
                    values=refreshed.get("values", {}),
                    expires_at=refreshed.get("expires_at") or "",
                    source="refresh",
                    home=home,
                )
                token = refreshed.get("values", {}).get("access_token")
                if isinstance(token, str) and token:
                    return token, refreshed.get("safe") if isinstance(refreshed.get("safe"), dict) else refreshed
    raise ValueError("OpenAI access token is required; pass --access-token, refresh, or store a Codex token profile")


def inspect_account(
    *,
    profile: str = "default",
    access_token: str | None = None,
    refresh: bool = True,
    client_id: str | None = None,
    timeout: float = 20.0,
    home: str | Path | None = None,
) -> dict[str, Any]:
    token, refresh_summary = _resolve_access_token(
        access_token=access_token,
        profile=profile,
        refresh=refresh,
        client_id=client_id,
        timeout=timeout,
        home=home,
    )
    payload = get_account(access_token=token, timeout=timeout)
    payload["profile"] = _normalize_profile(profile)
    payload["refresh"] = refresh_summary
    return payload


def inspect_usage(
    *,
    profile: str = "default",
    account_id: str,
    access_token: str | None = None,
    refresh: bool = True,
    client_id: str | None = None,
    timeout: float = 20.0,
    home: str | Path | None = None,
) -> dict[str, Any]:
    token, refresh_summary = _resolve_access_token(
        access_token=access_token,
        profile=profile,
        refresh=refresh,
        client_id=client_id,
        timeout=timeout,
        home=home,
    )
    payload = get_usage(access_token=token, account_id=account_id, timeout=timeout)
    payload["profile"] = _normalize_profile(profile)
    payload["refresh"] = refresh_summary
    return payload


__all__ = [
    "ACCOUNTS_URL",
    "AUTH_BASE_URL",
    "CHATGPT_BACKEND_BASE_URL",
    "CODEX_SERVICE_NAME",
    "CODEX_TOKEN_TYPE",
    "CODEX_USAGE_URL",
    "DEFAULT_OPENAI_CODEX_CLIENT_ID",
    "OAUTH_TOKEN_URL",
    "WHAM_USAGE_URL",
    "extract_codex_rate_limit_headers",
    "get_account",
    "get_usage",
    "inspect_account",
    "inspect_usage",
    "read_stored_token",
    "refresh_access_token",
    "save_token_values",
    "token_status",
]
