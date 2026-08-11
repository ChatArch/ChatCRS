"""Runtime token store for ChatCRS.

Dynamic CRS Admin session tokens are runtime state, not stable ChatEnv
configuration.  They are stored under ``~/.chatarch/tokens/CRS/<profile>.json``
parallel to ``~/.chatarch/envs/CRS/<profile>.env``.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from chatenv import get_paths

if TYPE_CHECKING:
    from chatcrs.remote import CrsProfile

SERVICE_NAME = "CRS"
TOKEN_SCHEMA_VERSION = 1


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _safe_profile_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    cleaned = cleaned.strip(".-")
    return cleaned or "default"


def base_url_hash(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


class CrsTokenStore:
    """JSON file store for one CRS profile's Admin session token."""

    def __init__(self, *, profile_name: str, profile: CrsProfile, home: str | Path | None = None):
        self.profile_name = profile_name
        self.profile = profile
        self.home = Path(get_paths(home).home_dir)
        safe_name = _safe_profile_name(profile_name)
        self.path = self.home / "tokens" / SERVICE_NAME / f"{safe_name}.json"

    @property
    def _normalized_base_url(self) -> str:
        return self.profile.base_url.rstrip("/")

    @property
    def _base_url_hash(self) -> str:
        return base_url_hash(self._normalized_base_url)

    def _read(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.path.read_text())
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _base_url_matches(self, payload: dict[str, Any]) -> bool:
        return payload.get("base_url") == self._normalized_base_url and payload.get("base_url_hash") == self._base_url_hash

    def _is_expired(self, payload: dict[str, Any]) -> bool:
        expires_at = _parse_iso(payload.get("expires_at"))
        if expires_at is None:
            return False
        return expires_at <= _now()

    def load_token(self) -> str:
        """Return a usable cached token or an empty string."""

        payload = self._read()
        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
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
        now = _now()
        expires_at = None
        if expires_in is not None:
            try:
                seconds = int(float(expires_in))
            except (TypeError, ValueError):
                seconds = 0
            if seconds > 0:
                expires_at = now + timedelta(seconds=seconds)
        payload = {
            "schema_version": TOKEN_SCHEMA_VERSION,
            "service": SERVICE_NAME,
            "profile": self.profile_name,
            "base_url": self._normalized_base_url,
            "base_url_hash": self._base_url_hash,
            "token_type": "admin_session",
            "access_token": token,
            "username": username or self.profile.username or "",
            "created_at": _iso(now),
            "updated_at": _iso(now),
            "expires_at": _iso(expires_at) if expires_at else "",
            "source": "login",
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(self.path.parent, 0o700)
        fd, tmp_name = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp", dir=str(self.path.parent), text=True)
        try:
            with os.fdopen(fd, "w") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.chmod(tmp_name, 0o600)
            os.replace(tmp_name, self.path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
        os.chmod(self.path, 0o600)
        return {
            "ok": True,
            "service": SERVICE_NAME,
            "profile": self.profile_name,
            "base_url": self._normalized_base_url,
            "base_url_hash": self._base_url_hash,
            "token_type": "admin_session",
            "token_present": True,
            "token_saved": True,
            "token_file": str(self.path),
            "expires_at": payload["expires_at"],
            "updated_at": payload["updated_at"],
        }

    def status(self) -> dict[str, Any]:
        payload = self._read()
        token_present = isinstance(payload.get("access_token"), str) and bool(payload.get("access_token"))
        base_url_match = bool(payload) and self._base_url_matches(payload)
        expired = bool(payload) and self._is_expired(payload)
        return {
            "ok": True,
            "service": SERVICE_NAME,
            "profile": self.profile_name,
            "base_url": self._normalized_base_url,
            "base_url_hash": self._base_url_hash,
            "token_file": str(self.path),
            "token_file_exists": self.path.exists(),
            "token_present": token_present,
            "base_url_match": base_url_match,
            "expired": expired,
            "expires_at": payload.get("expires_at", "") if isinstance(payload, dict) else "",
            "updated_at": payload.get("updated_at", "") if isinstance(payload, dict) else "",
        }

    def clear(self, *, execute: bool = False) -> dict[str, Any]:
        exists = self.path.exists()
        if not execute:
            return {
                "ok": True,
                "mutated": False,
                "profile": self.profile_name,
                "token_file": str(self.path),
                "token_file_exists": exists,
                "would_delete": str(self.path),
            }
        if exists:
            self.path.unlink()
        return {
            "ok": True,
            "mutated": exists,
            "profile": self.profile_name,
            "token_file": str(self.path),
            "token_file_exists": False,
            "deleted": exists,
        }


__all__ = ["CrsTokenStore", "base_url_hash"]
