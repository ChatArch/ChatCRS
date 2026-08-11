"""CRS-specific adapter around ChatEnv's generic runtime token store."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from chatenv import TokenStore

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


__all__ = ["CrsTokenStore", "base_url_hash"]
