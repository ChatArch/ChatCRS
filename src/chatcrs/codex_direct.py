"""Direct OpenAI/Codex account and usage helpers backed by ChatEnv.

ChatEnv owns stable OpenAI profiles (``envs/OpenAI/<profile>.env``) and the
runtime token store (``tokens/OpenAI/<profile>.json``). ChatCRS only provides the
OpenAI OAuth refresh semantics and consumes the resulting access token for
Codex account/usage inspection. Safe outputs never include raw access tokens,
refresh tokens, id tokens, cookies, or API keys.
"""

from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from chatenv import EnvStore, OpenAIConfig, TokenRefreshResult, TokenStore, get_paths
from chatenv.token_refreshers import refresh_token as refresh_runtime_token
from chatenv.tokens import normalize_token_profile

from chatcrs.redaction import redact

AUTH_BASE_URL = "https://auth.openai.com"
CHATGPT_BACKEND_BASE_URL = "https://chatgpt.com/backend-api"
ACCOUNTS_URL = f"{AUTH_BASE_URL}/api/accounts"
CODEX_USAGE_URL = f"{CHATGPT_BACKEND_BASE_URL}/codex/usage"
CODEX_RESPONSES_URL = f"{CHATGPT_BACKEND_BASE_URL}/codex/responses"
WHAM_USAGE_URL = f"{CHATGPT_BACKEND_BASE_URL}/wham/usage"
DEFAULT_OPENAI_CODEX_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
DEFAULT_CODEX_QUOTA_MODEL = "gpt-5.5"
OPENAI_SERVICE_NAME = "OpenAI"
OPENAI_OAUTH_TOKEN_TYPE = "openai_oauth"
OPENAI_CLIENT_ID_KEYS = ("OPENAI_OAUTH_CLIENT_ID", "OPENAI_CODEX_CLIENT_ID", "OPENAI_CLIENT_ID")
CHATGPT_BACKEND_BASE_URL_KEYS = (
    "CHATGPT_BACKEND_BASE_URL",
    "OPENAI_CHATGPT_BACKEND_BASE_URL",
    "OPENAI_CODEX_BACKEND_BASE_URL",
)

# Backward-compatible constants for callers that imported the 0.2.8 names. The
# storage service is intentionally OpenAI, not Codex: Codex uses ChatEnv's shared
# OpenAI profile schema.
CODEX_SERVICE_NAME = OPENAI_SERVICE_NAME
CODEX_TOKEN_TYPE = OPENAI_OAUTH_TOKEN_TYPE
OAUTH_TOKEN_URL = f"{AUTH_BASE_URL}/oauth/token"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _is_expired(value: Any) -> bool:
    expires_at = _parse_iso(value)
    return expires_at is not None and expires_at <= _now()


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


def _oauth_token_url(oauth_base_url: str | None = None) -> str:
    return f"{(oauth_base_url or AUTH_BASE_URL).rstrip('/')}/oauth/token"


def _accounts_url(auth_base_url: str | None = None) -> str:
    return f"{(auth_base_url or AUTH_BASE_URL).rstrip('/')}/api/accounts"


def _chatgpt_backend_base_url(backend_base_url: str | None = None) -> str:
    return (backend_base_url or CHATGPT_BACKEND_BASE_URL).rstrip("/")


def _codex_usage_url(backend_base_url: str | None = None) -> str:
    return f"{_chatgpt_backend_base_url(backend_base_url)}/wham/usage"


def _codex_responses_url(backend_base_url: str | None = None) -> str:
    return f"{_chatgpt_backend_base_url(backend_base_url)}/codex/responses"


def _short_hash(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _base_url_hash(base_url: str) -> str:
    return _short_hash(base_url.rstrip("/"))[:16]


def _jwt_claims(token: str) -> dict[str, Any]:
    if not isinstance(token, str) or token.count(".") != 2:
        return {}
    payload = token.split(".", 2)[1]
    payload += "=" * ((4 - len(payload) % 4) % 4)
    try:
        parsed = json.loads(base64.urlsafe_b64decode(payload.encode("utf-8")).decode("utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _timestamp_to_iso(value: Any) -> str:
    try:
        seconds = int(float(value))
    except (TypeError, ValueError):
        return ""
    return _iso(datetime.fromtimestamp(seconds, tz=timezone.utc))


def _safe_hash_field(summary: dict[str, Any], name: str, value: Any) -> None:
    if isinstance(value, str) and value:
        summary[f"{name}_hash"] = _short_hash(value)
        summary[f"{name}_present"] = True


def _account_summary_from_token_claims(access_token: str, *, stored_account_id: str = "") -> dict[str, Any]:
    claims = _jwt_claims(access_token)
    auth_claim = claims.get("https://api.openai.com/auth") if isinstance(claims, dict) else None
    if not isinstance(auth_claim, dict):
        auth_claim = {}

    summary: dict[str, Any] = {
        "source": "access_token_claims",
        "claims_present": bool(claims),
        "auth_claim_present": bool(auth_claim),
    }
    account_id = auth_claim.get("chatgpt_account_id")
    if isinstance(account_id, str) and account_id:
        summary["account_id_hash"] = _short_hash(account_id)
        summary["account_id_present"] = True
    elif stored_account_id:
        summary["account_id_hash"] = _short_hash(stored_account_id)
        summary["account_id_present"] = True
        summary["account_id_source"] = "token_store"
    if stored_account_id:
        summary["token_store_account_id_hash"] = _short_hash(stored_account_id)
        if isinstance(account_id, str) and account_id:
            summary["token_store_account_id_matches_claim"] = stored_account_id == account_id

    plan_type = auth_claim.get("chatgpt_plan_type")
    if isinstance(plan_type, str) and plan_type:
        summary["plan_type"] = plan_type
    _safe_hash_field(summary, "chatgpt_user_id", auth_claim.get("chatgpt_user_id") or auth_claim.get("user_id"))
    _safe_hash_field(summary, "chatgpt_account_user_id", auth_claim.get("chatgpt_account_user_id"))
    _safe_hash_field(summary, "poid", auth_claim.get("poid"))
    expires_at = _timestamp_to_iso(claims.get("exp")) if isinstance(claims, dict) else ""
    if expires_at:
        summary["token_expires_at"] = expires_at
        summary["token_expired"] = _is_expired(expires_at)
    return summary


def _safe_accounts(accounts: Any) -> list[dict[str, Any]]:
    if not isinstance(accounts, list):
        return []
    safe: list[dict[str, Any]] = []
    for account in accounts:
        if not isinstance(account, dict):
            continue
        item: dict[str, Any] = {}
        account_id = account.get("id") or account.get("account_id") or account.get("accountId")
        if isinstance(account_id, str) and account_id:
            item["account_id_hash"] = _short_hash(account_id)
        for key in ("plan_type", "plan", "role", "name"):
            value = account.get(key)
            if isinstance(value, (str, int, float, bool)) and value != "":
                item[key] = value
        email = account.get("email")
        if isinstance(email, str) and email:
            item["email_hash"] = _short_hash(email.lower())
        safe.append(item)
    return safe


def _extract_accounts(parsed: Any) -> list[dict[str, Any]]:
    if not isinstance(parsed, dict):
        return []
    raw_accounts = parsed.get("accounts", parsed.get("data", parsed.get("items", [])))
    if not isinstance(raw_accounts, list):
        return []
    return [account for account in raw_accounts if isinstance(account, dict)]


def _fetch_accounts(
    *,
    access_token: str,
    timeout: float = 20.0,
    auth_base_url: str | None = None,
) -> tuple[str, int, Any, list[dict[str, Any]]]:
    accounts_url = _accounts_url(auth_base_url)
    status, parsed, _headers = _request_json(
        "GET",
        accounts_url,
        headers={"authorization": f"Bearer {access_token}"},
        timeout=timeout,
    )
    return accounts_url, status, parsed, _extract_accounts(parsed)


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
    json_data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 20.0,
) -> tuple[int, Any, dict[str, str]]:
    """Perform an HTTP JSON/form request using stdlib only."""

    request_headers = {"accept": "application/json"}
    if headers:
        request_headers.update(headers)
    body = None
    if data is not None and json_data is not None:
        raise ValueError("Pass either form data or JSON data, not both")
    if json_data is not None:
        body = json.dumps(json_data).encode("utf-8")
        request_headers["content-type"] = "application/json"
    elif data is not None:
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


def _token_store(home: str | Path | None = None) -> TokenStore:
    return TokenStore(home=home)


def _token_values(payload: dict[str, Any]) -> dict[str, Any]:
    values = payload.get("values") if isinstance(payload, dict) else None
    return values if isinstance(values, dict) else {}


_IDENTITY_KEY_NAMES = {
    "accountid",
    "accountuuid",
    "chatgptaccountid",
    "userid",
    "useruuid",
    "chatgptuserid",
    "chatgptaccountuserid",
    "email",
    "emailaddress",
}


def _redact_identity_text(value: str) -> str:
    value = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED]", value)
    value = re.sub(r"\bacct_[A-Za-z0-9_-]+\b", "[REDACTED]", value)
    value = re.sub(r"\buser_[A-Za-z0-9_-]+\b", "[REDACTED]", value)
    value = re.sub(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        "[REDACTED]",
        value,
    )
    return value


def _identity_key_name(key: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def _redact_identity(value: Any) -> Any:
    """Redact tokens plus account/user/email identity fields from public payloads."""

    value = redact(value)
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if _identity_key_name(key) in _IDENTITY_KEY_NAMES else _redact_identity(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_identity(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_identity(item) for item in value)
    if isinstance(value, str):
        return _redact_identity_text(value)
    return value


def _load_openai_profile_values(
    profile: str | None,
    *,
    home: str | Path | None = None,
    env_store: EnvStore | None = None,
) -> tuple[str, dict[str, str]]:
    profile_name = normalize_token_profile(profile)
    store = env_store or EnvStore(get_paths(home).envs_dir)
    try:
        profile_path = (
            store.active_path(OpenAIConfig)
            if profile_name == "default"
            else store.profile_path(OpenAIConfig, profile_name)
        )
    except ValueError as exc:
        raise ValueError(f"OpenAI ChatEnv profile not found or invalid: {profile_name}") from exc
    if not profile_path.exists():
        raise ValueError(f"OpenAI ChatEnv profile not found or invalid: {profile_name}")
    try:
        values = (
            store.load_active(OpenAIConfig)
            if profile_name == "default"
            else store.load_profile(OpenAIConfig, profile_name)
        )
    except ValueError as exc:
        raise ValueError(f"OpenAI ChatEnv profile not found or invalid: {profile_name}") from exc
    return profile_name, {str(key): str(value) for key, value in values.items() if value is not None}


def _configured_client_id(values: dict[str, str], client_id: str | None = None) -> tuple[str, str]:
    if client_id:
        return client_id, "option"
    for key in OPENAI_CLIENT_ID_KEYS:
        value = values.get(key)
        if value:
            return value, key
    return DEFAULT_OPENAI_CODEX_CLIENT_ID, "default_codex_client_id"


def _configured_backend_base_url(values: dict[str, str] | None = None) -> str:
    values = values or {}
    for key in CHATGPT_BACKEND_BASE_URL_KEYS:
        value = values.get(key)
        if value:
            return value.rstrip("/")
    return CHATGPT_BACKEND_BASE_URL


def _openai_profile_values_or_empty(*, profile: str, home: str | Path | None = None) -> dict[str, str]:
    try:
        _profile_name, values = _load_openai_profile_values(profile, home=home)
    except ValueError:
        return {}
    return values


def refresh_access_token(
    *,
    refresh_token: str,
    client_id: str | None = None,
    oauth_base_url: str | None = None,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Exchange an OpenAI refresh token for a fresh access token."""

    if not refresh_token:
        raise ValueError("OpenAI refresh token is required")
    status, parsed, _headers = _request_json(
        "POST",
        _oauth_token_url(oauth_base_url),
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


def refresh_chatenv_token(
    *,
    service: str,
    profile: str,
    home: str | Path | None = None,
    env_store: EnvStore | None = None,
    token_store: TokenStore | None = None,
) -> TokenRefreshResult:
    """Refresh OpenAI OAuth runtime state for ChatEnv's token lifecycle.

    Stable OAuth bootstrap values come from the registered ChatEnv ``OpenAI``
    profile. Rotated refresh tokens are read from the existing ChatEnv token
    store when present. ChatEnv owns the final token-store write.
    """

    if service != OPENAI_SERVICE_NAME:
        raise ValueError(f"ChatCRS can refresh only {OPENAI_SERVICE_NAME} tokens")
    profile_name, values = _load_openai_profile_values(profile, home=home, env_store=env_store)
    store = token_store or TokenStore(home=home)
    existing_values = _token_values(store.read(OPENAI_SERVICE_NAME, profile_name))
    refresh_token = existing_values.get("refresh_token") or values.get("OPENAI_REFRESH_TOKEN")
    if not isinstance(refresh_token, str) or not refresh_token:
        raise ValueError(f"OpenAI ChatEnv profile {profile_name} is missing OPENAI_REFRESH_TOKEN")

    oauth_base_url = values.get("OPENAI_OAUTH_BASE_URL") or AUTH_BASE_URL
    client_id, client_id_source = _configured_client_id(values)
    refreshed = refresh_access_token(
        refresh_token=refresh_token,
        client_id=client_id,
        oauth_base_url=oauth_base_url,
        timeout=20.0,
    )
    if not refreshed.get("ok"):
        raise ValueError(f"OpenAI OAuth refresh failed: status={refreshed.get('status')}")
    refreshed_values = dict(refreshed.get("values") or {})
    if "refresh_token" not in refreshed_values:
        refreshed_values["refresh_token"] = refresh_token
    for metadata_key in ("account_id", "account_label", "account_name"):
        metadata_value = existing_values.get(metadata_key)
        if metadata_value and metadata_key not in refreshed_values:
            refreshed_values[metadata_key] = metadata_value
    account_id = refreshed_values.get("account_id")
    return TokenRefreshResult(
        values={key: value for key, value in refreshed_values.items() if value},
        token_type=OPENAI_OAUTH_TOKEN_TYPE,
        summary={
            "provider": OPENAI_SERVICE_NAME,
            "profile": profile_name,
            "oauth_base_url_hash": _base_url_hash(oauth_base_url),
            "client_id_source": client_id_source,
            "access_token_present": bool(refreshed_values.get("access_token")),
            "refresh_token_present": bool(refreshed_values.get("refresh_token")),
            "refresh_token_rotated": bool(refreshed.get("refresh_token_rotated")),
            "id_token_present": bool(refreshed_values.get("id_token")),
            "account_id_present": isinstance(account_id, str) and bool(account_id),
            "account_id_hash": _short_hash(account_id) if isinstance(account_id, str) and account_id else "",
        },
        expires_at=refreshed.get("expires_at") or "",
    )


def refresh_openai_profile_token(*, profile: str = "default", home: str | Path | None = None) -> dict[str, Any]:
    """Refresh ``OpenAI`` runtime token state through ChatEnv."""

    return refresh_runtime_token(OPENAI_SERVICE_NAME, profile, home=home)


def read_stored_token(*, profile: str = "default", home: str | Path | None = None) -> dict[str, Any]:
    profile_name = normalize_token_profile(profile)
    return _token_store(home).read(OPENAI_SERVICE_NAME, profile_name)


def token_status(*, profile: str = "default", home: str | Path | None = None) -> dict[str, Any]:
    profile_name = normalize_token_profile(profile)
    status = _token_store(home).status(OPENAI_SERVICE_NAME, profile_name)
    status["token_type"] = read_stored_token(profile=profile_name, home=home).get("token_type", OPENAI_OAUTH_TOKEN_TYPE)
    return status


def save_token_values(
    *,
    profile: str = "default",
    values: dict[str, Any],
    expires_at: str | None = None,
    source: str = "import",
    home: str | Path | None = None,
) -> dict[str, Any]:
    """Compatibility helper that writes OpenAI tokens through TokenStore API.

    New command-line workflows should prefer ``chatenv token import OpenAI`` or
    ``chatenv token refresh OpenAI``. This function remains for Python callers
    and tests; it never writes a Codex-specific service namespace.
    """

    profile_name = normalize_token_profile(profile)
    account_id = values.get("account_id") if isinstance(values.get("account_id"), str) else ""
    summary = {
        "provider": OPENAI_SERVICE_NAME,
        "profile": profile_name,
        "access_token_present": bool(values.get("access_token")),
        "refresh_token_present": bool(values.get("refresh_token")),
        "id_token_present": bool(values.get("id_token")),
        "account_id_present": bool(account_id),
        "account_id_hash": _short_hash(account_id) if account_id else "",
    }
    return _token_store(home).write(
        OPENAI_SERVICE_NAME,
        profile_name,
        values={key: value for key, value in values.items() if value},
        token_type=OPENAI_OAUTH_TOKEN_TYPE,
        summary=summary,
        expires_at=expires_at or "",
        source=source,
    )


def _stored_values(*, profile: str = "default", home: str | Path | None = None) -> dict[str, Any]:
    payload = read_stored_token(profile=profile, home=home)
    return _token_values(payload)


def _usable_access_from_payload(payload: dict[str, Any]) -> str:
    if _is_expired(payload.get("expires_at")):
        return ""
    token = _token_values(payload).get("access_token")
    return token if isinstance(token, str) and token else ""


def _usable_access_from_openai_profile(*, profile: str, home: str | Path | None = None) -> str:
    try:
        _profile_name, values = _load_openai_profile_values(profile, home=home)
    except ValueError:
        return ""
    if _is_expired(values.get("OPENAI_ACCESS_TOKEN_EXPIRES_AT")):
        return ""
    token = values.get("OPENAI_ACCESS_TOKEN")
    return token if isinstance(token, str) and token else ""


def _resolve_access_token(
    *,
    access_token: str | None,
    profile: str,
    refresh: bool,
    client_id: str | None,
    timeout: float,
    home: str | Path | None = None,
) -> tuple[str, dict[str, Any] | None]:
    del client_id, timeout  # Refresh parameters are owned by the ChatEnv provider.
    profile_name = normalize_token_profile(profile)
    if access_token:
        return access_token, None

    payload = read_stored_token(profile=profile_name, home=home)
    stored_access = _usable_access_from_payload(payload)
    if stored_access:
        return stored_access, None

    configured_access = _usable_access_from_openai_profile(profile=profile_name, home=home)
    if configured_access:
        return configured_access, None

    if refresh:
        refresh_status = refresh_openai_profile_token(profile=profile_name, home=home)
        refreshed_payload = read_stored_token(profile=profile_name, home=home)
        refreshed_access = _usable_access_from_payload(refreshed_payload)
        if refreshed_access:
            return refreshed_access, refresh_status
    raise ValueError(
        "OpenAI access token is required; use a registered ChatEnv OpenAI profile and run "
        "`chatenv token refresh OpenAI <profile>` or pass --access-token for a one-off read."
    )


def get_account(
    *,
    access_token: str,
    timeout: float = 20.0,
    auth_base_url: str | None = None,
    stored_account_id: str = "",
) -> dict[str, Any]:
    """Read safe ChatGPT/Codex account metadata using an access token.

    The token itself carries useful account claims. The accounts API is kept as
    a best-effort probe because it is frequently protected by Cloudflare and may
    return HTML challenge bodies even for otherwise usable Codex tokens.
    """

    if not access_token:
        raise ValueError("OpenAI access token is required")
    accounts_url, status, parsed, accounts = _fetch_accounts(access_token=access_token, timeout=timeout, auth_base_url=auth_base_url)
    account_summary = _account_summary_from_token_claims(access_token, stored_account_id=stored_account_id)
    safe_accounts = _safe_accounts(accounts)
    api_ok = status == 200 and bool(safe_accounts)
    return {
        "ok": bool(account_summary.get("account_id_present") or api_ok),
        "mutated": False,
        "status": status,
        "accounts_url": accounts_url,
        "account_count": len(safe_accounts),
        "account_summary": account_summary,
        "accounts": safe_accounts,
        "accounts_api": {
            "ok": api_ok,
            "status": status,
            "account_count": len(safe_accounts),
            "body_redacted": _redact_identity(parsed) if status == 200 and not safe_accounts else None,
            "body_kind": "html" if isinstance(parsed, dict) and str(parsed.get("raw", "")).lstrip().startswith("<") else type(parsed).__name__,
        },
    }


def get_usage(
    *,
    access_token: str,
    account_id: str,
    timeout: float = 20.0,
    usage_url: str | None = None,
    backend_base_url: str | None = None,
) -> dict[str, Any]:
    """Read Codex token usage and quota headers for one ChatGPT account."""

    if not access_token:
        raise ValueError("OpenAI access token is required")
    if not account_id:
        raise ValueError("ChatGPT account id is required")
    resolved_usage_url = usage_url or _codex_usage_url(backend_base_url)
    status, parsed, headers = _request_json(
        "GET",
        resolved_usage_url,
        headers={
            "authorization": f"Bearer {access_token}",
            "ChatGPT-Account-ID": account_id,
            "accept": "application/json",
            "user-agent": "codex_cli_rs/0.0.0 (ChatCRS)",
            "originator": "codex_cli_rs",
        },
        timeout=timeout,
    )
    return {
        "ok": status == 200,
        "mutated": False,
        "status": status,
        "account_id_hash": _short_hash(account_id),
        "usage_url": resolved_usage_url,
        "rate_limits": extract_codex_rate_limit_headers(headers),
        "usage": _redact_identity(parsed),
    }


def _codex_quota_smoke_payload(*, model: str = DEFAULT_CODEX_QUOTA_MODEL, prompt: str = "Reply OK.") -> dict[str, Any]:
    return {
        "model": model,
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    }
                ],
            }
        ],
        "store": False,
        "stream": True,
    }


def get_quota(
    *,
    access_token: str,
    account_id: str,
    model: str = DEFAULT_CODEX_QUOTA_MODEL,
    prompt: str = "Reply OK.",
    timeout: float = 20.0,
    responses_url: str | None = None,
    backend_base_url: str | None = None,
) -> dict[str, Any]:
    """Run a minimal Codex responses smoke and return only safe quota headers."""

    if not access_token:
        raise ValueError("OpenAI access token is required")
    if not account_id:
        raise ValueError("ChatGPT account id is required")
    payload = _codex_quota_smoke_payload(model=model, prompt=prompt)
    resolved_responses_url = responses_url or _codex_responses_url(backend_base_url)
    status, parsed, headers = _request_json(
        "POST",
        resolved_responses_url,
        json_data=payload,
        headers={
            "authorization": f"Bearer {access_token}",
            "ChatGPT-Account-ID": account_id,
            "content-type": "application/json",
            "accept": "text/event-stream",
            "user-agent": "codex_cli_rs/0.0.0 (ChatCRS)",
            "originator": "codex_cli_rs",
        },
        timeout=timeout,
    )
    rate_limits = extract_codex_rate_limit_headers(headers)
    return {
        "ok": status == 200,
        "mutated": False,
        "status": status,
        "account_id_hash": _short_hash(account_id),
        "responses_url": resolved_responses_url,
        "model": model,
        "request": {"store": payload["store"], "stream": payload["stream"]},
        "rate_limits": rate_limits,
        "has_quota_headers": any(value is not None for value in rate_limits.values()),
        "body": _redact_identity(parsed) if status != 200 else None,
    }


def _normalize_profile(profile: str | None) -> str:
    return normalize_token_profile(profile)


def inspect_account(
    *,
    profile: str = "default",
    access_token: str | None = None,
    refresh: bool = True,
    client_id: str | None = None,
    timeout: float = 20.0,
    home: str | Path | None = None,
) -> dict[str, Any]:
    profile_name = _normalize_profile(profile)
    profile_values = _openai_profile_values_or_empty(profile=profile_name, home=home)
    token, refresh_summary = _resolve_access_token(
        access_token=access_token,
        profile=profile_name,
        refresh=refresh,
        client_id=client_id,
        timeout=timeout,
        home=home,
    )
    stored_account_id = _stored_account_id(profile=profile_name, home=home)
    payload = get_account(
        access_token=token,
        timeout=timeout,
        auth_base_url=profile_values.get("OPENAI_OAUTH_BASE_URL"),
        stored_account_id=stored_account_id,
    )
    payload["profile"] = profile_name
    payload["token_service"] = OPENAI_SERVICE_NAME
    payload["refresh"] = refresh_summary
    return payload


def _account_ids_from_payload(payload: dict[str, Any]) -> list[str]:
    accounts = payload.get("accounts") if isinstance(payload, dict) else None
    if not isinstance(accounts, list):
        return []
    ids: list[str] = []
    for account in accounts:
        if not isinstance(account, dict):
            continue
        for key in ("id", "account_id", "accountId"):
            value = account.get(key)
            if isinstance(value, str) and value and value not in ids:
                ids.append(value)
                break
    return ids


def _stored_account_id(*, profile: str, home: str | Path | None = None) -> str:
    values = _stored_values(profile=profile, home=home)
    account_id = values.get("account_id")
    return account_id if isinstance(account_id, str) and account_id else ""


def _resolve_account_id_from_profile(
    *,
    profile: str,
    access_token: str,
    timeout: float,
    home: str | Path | None = None,
    auth_base_url: str | None = None,
) -> tuple[str, dict[str, Any]]:
    stored_account_id = _stored_account_id(profile=profile, home=home)
    if stored_account_id:
        return stored_account_id, {
            "source": "token_store_account_id",
            "account_id_hash": _short_hash(stored_account_id),
        }
    _accounts_url_value, status, _parsed, accounts = _fetch_accounts(
        access_token=access_token,
        timeout=timeout,
        auth_base_url=auth_base_url,
    )
    ids = _account_ids_from_payload({"accounts": accounts})
    if len(ids) == 1:
        return ids[0], {
            "source": "profile_account_metadata",
            "account_count": len(ids),
            "status": status,
            "account_id_hash": _short_hash(ids[0]),
        }
    if not ids:
        raise ValueError(
            "No OpenAI account id was found for this profile; run `chatcrs codex account --profile <profile> --json-output` "
            "or pass --account-id explicitly."
        )
    raise ValueError(
        f"OpenAI profile exposes {len(ids)} account ids; pass --account-id explicitly to choose one."
    )


def inspect_usage(
    *,
    profile: str = "default",
    account_id: str | None = None,
    access_token: str | None = None,
    refresh: bool = True,
    client_id: str | None = None,
    timeout: float = 20.0,
    home: str | Path | None = None,
) -> dict[str, Any]:
    profile_name = _normalize_profile(profile)
    profile_values = _openai_profile_values_or_empty(profile=profile_name, home=home)
    token, refresh_summary = _resolve_access_token(
        access_token=access_token,
        profile=profile_name,
        refresh=refresh,
        client_id=client_id,
        timeout=timeout,
        home=home,
    )
    account_resolution: dict[str, Any] | None = None
    if not account_id:
        account_id, account_resolution = _resolve_account_id_from_profile(
            profile=profile_name,
            access_token=token,
            timeout=timeout,
            home=home,
            auth_base_url=profile_values.get("OPENAI_OAUTH_BASE_URL"),
        )
    payload = get_usage(
        access_token=token,
        account_id=account_id,
        timeout=timeout,
        backend_base_url=_configured_backend_base_url(profile_values),
    )
    payload["profile"] = profile_name
    payload["token_service"] = OPENAI_SERVICE_NAME
    payload["refresh"] = refresh_summary
    payload["account_resolution"] = account_resolution or {"source": "explicit", "account_id_hash": _short_hash(account_id)}
    return payload


def inspect_quota(
    *,
    profile: str = "default",
    account_id: str | None = None,
    access_token: str | None = None,
    refresh: bool = True,
    client_id: str | None = None,
    model: str = DEFAULT_CODEX_QUOTA_MODEL,
    timeout: float = 20.0,
    home: str | Path | None = None,
) -> dict[str, Any]:
    """Run a profile-only Codex quota smoke through the responses endpoint."""

    profile_name = _normalize_profile(profile)
    profile_values = _openai_profile_values_or_empty(profile=profile_name, home=home)
    token, refresh_summary = _resolve_access_token(
        access_token=access_token,
        profile=profile_name,
        refresh=refresh,
        client_id=client_id,
        timeout=timeout,
        home=home,
    )
    account_resolution: dict[str, Any] | None = None
    if not account_id:
        account_id, account_resolution = _resolve_account_id_from_profile(
            profile=profile_name,
            access_token=token,
            timeout=timeout,
            home=home,
            auth_base_url=profile_values.get("OPENAI_OAUTH_BASE_URL"),
        )
    payload = get_quota(
        access_token=token,
        account_id=account_id,
        model=model,
        timeout=timeout,
        backend_base_url=_configured_backend_base_url(profile_values),
    )
    payload["profile"] = profile_name
    payload["token_service"] = OPENAI_SERVICE_NAME
    payload["refresh"] = refresh_summary
    payload["account_resolution"] = account_resolution or {"source": "explicit", "account_id_hash": _short_hash(account_id)}
    return payload


__all__ = [
    "ACCOUNTS_URL",
    "AUTH_BASE_URL",
    "CHATGPT_BACKEND_BASE_URL",
    "CODEX_SERVICE_NAME",
    "CODEX_TOKEN_TYPE",
    "CODEX_RESPONSES_URL",
    "CODEX_USAGE_URL",
    "DEFAULT_CODEX_QUOTA_MODEL",
    "DEFAULT_OPENAI_CODEX_CLIENT_ID",
    "OAUTH_TOKEN_URL",
    "OPENAI_OAUTH_TOKEN_TYPE",
    "OPENAI_SERVICE_NAME",
    "WHAM_USAGE_URL",
    "extract_codex_rate_limit_headers",
    "get_account",
    "get_quota",
    "get_usage",
    "inspect_account",
    "inspect_quota",
    "inspect_usage",
    "read_stored_token",
    "refresh_access_token",
    "refresh_chatenv_token",
    "refresh_openai_profile_token",
    "save_token_values",
    "token_status",
]
