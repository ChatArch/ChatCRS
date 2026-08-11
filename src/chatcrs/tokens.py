"""CRS-specific adapter around ChatEnv's generic runtime token store."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from chatenv import EnvStore, TokenRefreshResult, TokenStore, get_paths
from chatenv.tokens import normalize_token_profile

from chatcrs.config import ChatcrsConfig

if TYPE_CHECKING:
    from chatcrs.remote import CrsProfile

SERVICE_NAME = "CRS"
TOKEN_TYPE = "admin_session"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def base_url_hash(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


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


def _load_refresh_profile_values(
    profile: str | None,
    *,
    home: str | Path | None = None,
    env_store: EnvStore | None = None,
) -> tuple[str, dict[str, str]]:
    profile_name = normalize_token_profile(profile)
    store = env_store or EnvStore(get_paths(home).envs_dir)
    try:
        profile_path = (
            store.active_path(ChatcrsConfig)
            if profile_name == "default"
            else store.profile_path(ChatcrsConfig, profile_name)
        )
    except ValueError as exc:
        raise ValueError(f"CRS ChatEnv profile not found or invalid: {profile_name}") from exc
    if not profile_path.exists():
        raise ValueError(f"CRS ChatEnv profile not found or invalid: {profile_name}")
    try:
        values = (
            store.load_active(ChatcrsConfig)
            if profile_name == "default"
            else store.load_profile(ChatcrsConfig, profile_name)
        )
    except ValueError as exc:
        raise ValueError(f"CRS ChatEnv profile not found or invalid: {profile_name}") from exc
    return profile_name, {str(key): str(value) for key, value in values.items() if value is not None}


def _refresh_client_class():
    from chatcrs.remote import CrsHttpClient

    return CrsHttpClient


def refresh_chatenv_token(
    *,
    service: str,
    profile: str,
    home: str | Path | None = None,
    env_store: EnvStore | None = None,
    token_store: TokenStore | None = None,
) -> TokenRefreshResult:
    """Refresh a CRS Admin session token for ChatEnv's provider lifecycle.

    ChatCRS owns the CRS `/web/auth/login` semantics. ChatEnv owns the actual
    token-store write for `chatenv token refresh CRS <profile>`, so this
    provider returns opaque values plus a safe summary and never writes the
    token file itself.
    """

    del token_store  # ChatEnv owns persistence after this provider returns.
    if service != SERVICE_NAME:
        raise ValueError(f"ChatCRS can refresh only {SERVICE_NAME} tokens")
    profile_name, values = _load_refresh_profile_values(profile, home=home, env_store=env_store)
    required = ["CRS_API_BASE", "CRS_USERNAME", "CRS_PASSWORD"]
    for key in required:
        if not values.get(key):
            raise ValueError(f"CRS ChatEnv profile {profile_name} is missing {key}")

    from chatcrs.remote import CrsProfile

    base_url = values["CRS_API_BASE"].rstrip("/")
    crs_profile = CrsProfile(
        base_url=base_url,
        api_key=values.get("CRS_API_KEY", ""),
        username=values["CRS_USERNAME"],
        password=values["CRS_PASSWORD"],
        admin_token="",
    )
    paths = get_paths(home)
    client = _refresh_client_class()(crs_profile, timeout=20.0, profile_name=profile_name, home=paths.home_dir, explicit_admin_token=True)
    login_payload = client.login(save_token=False)
    token = getattr(client, "_admin_token", "")
    if not isinstance(token, str) or not token:
        raise ValueError("CRS admin login did not return a session token")
    return TokenRefreshResult(
        values={"access_token": token},
        token_type=TOKEN_TYPE,
        summary={
            "base_url": base_url,
            "base_url_hash": base_url_hash(base_url),
            "username": str(login_payload.get("username") or crs_profile.username or ""),
        },
        expires_at=_expires_at_from_expires_in(login_payload.get("expiresIn")),
    )


class CrsTokenStore:
    """CRS Admin-session view over ChatEnv's generic service/profile store."""

    def __init__(self, *, profile_name: str, profile: CrsProfile, home: str | Path | None = None):
        self.profile_name = profile_name
        self.profile = profile
        self._store = TokenStore(home=home)
        self.path = self._store.token_path(SERVICE_NAME, profile_name)

    @property
    def _normalized_base_url(self) -> str:
        return self.profile.base_url.rstrip("/")

    @property
    def _base_url_hash(self) -> str:
        return base_url_hash(self._normalized_base_url)

    def _read(self) -> dict[str, Any]:
        return self._store.read(SERVICE_NAME, self.profile_name)

    def _summary(self, payload: dict[str, Any]) -> dict[str, Any]:
        summary = payload.get("summary")
        return summary if isinstance(summary, dict) else {}

    def _values(self, payload: dict[str, Any]) -> dict[str, Any]:
        values = payload.get("values")
        return values if isinstance(values, dict) else {}

    def _base_url_matches(self, payload: dict[str, Any]) -> bool:
        summary = self._summary(payload)
        return summary.get("base_url") == self._normalized_base_url and summary.get("base_url_hash") == self._base_url_hash

    def _is_expired(self, payload: dict[str, Any]) -> bool:
        expires_at = _parse_iso(payload.get("expires_at"))
        if expires_at is None:
            return False
        return expires_at <= _now()

    def load_token(self) -> str:
        """Return a usable cached token or an empty string."""

        payload = self._read()
        token = self._values(payload).get("access_token")
        if not isinstance(token, str) or not token:
            return ""
        if payload.get("token_type") != TOKEN_TYPE:
            return ""
        if not self._base_url_matches(payload):
            return ""
        if self._is_expired(payload):
            return ""
        return token

    def save_login_token(self, token: str, *, expires_in: int | float | None = None, username: str | None = None) -> dict[str, Any]:
        """Persist a CRS login token and return a redacted summary."""

        if not token:
            raise ValueError("token is required")
        expires_at = ""
        if expires_in is not None:
            try:
                seconds = int(float(expires_in))
            except (TypeError, ValueError):
                seconds = 0
            if seconds > 0:
                expires_at = _iso(_now() + timedelta(seconds=seconds))
        status = self._store.write(
            SERVICE_NAME,
            self.profile_name,
            values={"access_token": token},
            token_type=TOKEN_TYPE,
            summary={
                "base_url": self._normalized_base_url,
                "base_url_hash": self._base_url_hash,
                "username": username or self.profile.username or "",
            },
            expires_at=expires_at,
            source="login",
        )
        summary = status.get("summary") if isinstance(status.get("summary"), dict) else {}
        status.update(
            {
                "base_url": summary.get("base_url", self._normalized_base_url),
                "base_url_hash": summary.get("base_url_hash", self._base_url_hash),
                "token_saved": True,
            }
        )
        return status

    def status(self) -> dict[str, Any]:
        payload = self._read()
        generic = self._store.status(SERVICE_NAME, self.profile_name)
        token_present = generic["token_present"]
        base_url_match = bool(payload) and self._base_url_matches(payload)
        expired = bool(payload) and self._is_expired(payload)
        summary = self._summary(payload)
        return {
            "ok": True,
            "service": SERVICE_NAME,
            "profile": self.profile_name,
            "base_url": self._normalized_base_url,
            "base_url_hash": self._base_url_hash,
            "token_file": str(self.path),
            "token_file_exists": self.path.exists(),
            "token_present": token_present,
            "token_type": payload.get("token_type") if payload else TOKEN_TYPE,
            "base_url_match": base_url_match,
            "expired": expired,
            "expires_at": generic.get("expires_at", ""),
            "updated_at": generic.get("updated_at", ""),
            "source": generic.get("source", ""),
            "summary": summary,
        }

    def clear(self, *, execute: bool = False) -> dict[str, Any]:
        return self._store.clear(SERVICE_NAME, self.profile_name, execute=execute)


__all__ = ["CrsTokenStore", "base_url_hash", "refresh_chatenv_token"]
