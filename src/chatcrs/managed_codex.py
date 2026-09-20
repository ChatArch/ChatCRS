"""HTTP-only access to CRS-owned Codex accounts; no local upstream OAuth.

Only explicitly selected CRS profiles are read. Responses are validated and
allowlisted, not passed through a best-effort secret-pattern redactor.
"""
from __future__ import annotations

import ipaddress
import math
import re
from datetime import datetime, timezone
from http.client import HTTPException
from pathlib import Path
from urllib.parse import urlsplit

from chatenv.tokens import normalize_token_profile

from chatcrs import remote


class ManagedCodexError(RuntimeError):
    """Fixed machine-readable failure; never retain a remote body or exception."""

    def __init__(self, code: str, *, status: int | None = None):
        self.code = code
        self.status = status
        super().__init__(f"CRS managed Codex request failed ({code}).")


def _identifier(value, code: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value):
        raise ManagedCodexError(code)
    return value


def _origin(base: str) -> str:
    try:
        if not base or any(ord(c) <= 32 or ord(c) >= 127 for c in base) or any(c in base for c in "\\?#%"):
            raise ValueError
        parts = urlsplit(base)
        host, port = parts.hostname, parts.port
        if not host or parts.username is not None or parts.password is not None or parts.path not in ("", "/"):
            raise ValueError
        try:
            ip = ipaddress.ip_address(host)
            loopback = ip.is_loopback
        except ValueError:
            if not re.fullmatch(r"[A-Za-z0-9.-]+", host):
                raise ValueError
            loopback = host == "localhost"
        if parts.scheme != "https" and not (parts.scheme == "http" and loopback):
            raise ValueError
        if port == 0:
            raise ValueError
        authority = f"[{host}]" if ":" in host else host
        if port is not None and port != {"https": 443, "http": 80}[parts.scheme]:
            authority += f":{port}"
        return f"{parts.scheme}://{authority}"
    except (TypeError, ValueError):
        raise ManagedCodexError("invalid_base_url") from None


def _iso(value) -> datetime:
    try:
        if not isinstance(value, str) or len(value) > 40 or "T" not in value:
            raise ValueError
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError
        return parsed
    except ValueError:
        pass
    # Raising inside the handler would retain the untrusted date in __context__.
    raise ManagedCodexError("invalid_response")


def _number(value, *, minimum=0, maximum=2**53 - 1, integer=False):
    if (type(value) not in (int, float) or not minimum <= value <= maximum
            or not math.isfinite(value) or (integer and type(value) is not int)):
        raise ManagedCodexError("invalid_response")
    return value


def _timeout(value):
    try:
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError
    except (ValueError, OverflowError):
        raise ManagedCodexError("invalid_timeout") from None
    return value


def _rate_limit(value) -> dict:
    if not isinstance(value, dict):
        raise ManagedCodexError("invalid_response")
    result = {}
    valid_windows = 0
    for name in ("primary_window", "secondary_window"):
        if name not in value:
            continue
        window = value.get(name)
        if window is None:
            result[name] = None
            continue
        if not isinstance(window, dict):
            raise ManagedCodexError("invalid_response")
        result[name] = {
            "used_percent": _number(window.get("used_percent"), maximum=100),
            "limit_window_seconds": _number(window.get("limit_window_seconds"), minimum=1, integer=True),
            "reset_at": _number(window.get("reset_at")),
        }
        if "reset_after_seconds" in window:
            result[name]["reset_after_seconds"] = _number(window["reset_after_seconds"])
        valid_windows += 1
    if not valid_windows:
        raise ManagedCodexError("invalid_response")
    return result


def _credit_rows(rows) -> list[dict]:
    if not isinstance(rows, list):
        raise ManagedCodexError("invalid_response")
    result = []
    for row in rows:
        if (not isinstance(row, dict) or row.get("status") not in ("available", "redeemed", "expired", "consumed")
                or "expires_at" not in row):
            raise ManagedCodexError("invalid_response")
        if row["expires_at"] is not None:
            _iso(row["expires_at"])
        result.append({
            "id": _identifier(row.get("id"), "invalid_response"),
            "status": row["status"], "expires_at": row["expires_at"],
        })
    return result


class CrsManagedCodexClient:
    """Pinned CRS adapter using a scoped management Key or Admin session."""

    token_service = "CRS"

    def __init__(self, profile: remote.CrsProfile, *, account_id: str, profile_name: str, home=None, timeout=20):
        self._timeout = _timeout(timeout)
        self._account_id = _identifier(account_id, "invalid_account_id")
        self._identity = f"{_origin(profile.base_url)}#account={account_id}"
        if profile.api_key and (
            not isinstance(profile.api_key, str)
            or not re.fullmatch(r"crsm_[A-Za-z0-9_-]{43}", profile.api_key)
        ):
            raise ManagedCodexError("invalid_management_key")
        self._key_auth = bool(profile.api_key)
        self._profile = profile
        self._profile_name = profile_name
        self._home = home
        self._http = None
        self._prefix = f"/admin/openai-accounts/{account_id}/codex"

    @classmethod
    def from_profile(cls, crs_profile: str = "default", *, account_id: str,
                     home: str | Path | None = None, timeout: float = 20,
                     require_management_key: bool = False) -> CrsManagedCodexClient:
        _identifier(account_id, "invalid_account_id")
        _timeout(timeout)
        try:
            if (not isinstance(crs_profile, str) or not crs_profile or len(crs_profile) > 128
                    or crs_profile.endswith(".env") or normalize_token_profile(crs_profile) != crs_profile):
                raise ValueError
        except ValueError:
            raise ManagedCodexError("invalid_profile") from None
        try:
            profile = remote.load_crs_profile(crs_profile, home=home, allow_env=False)
        except (OSError, ValueError):
            raise ManagedCodexError("invalid_profile") from None
        if require_management_key and not profile.api_key:
            raise ManagedCodexError("management_key_required")
        return cls(profile, account_id=account_id, profile_name=crs_profile, home=home, timeout=timeout)

    @property
    def identity(self) -> str:
        return self._identity

    def _request(self, path: str, *, method="GET", payload=None, request_id=None) -> dict:
        failed = False
        failure_code = None
        try:
            # Lazy token resolution keeps validation and local plans ahead of auth.
            if self._http is None:
                self._http = remote.CrsHttpClient(
                    self._profile, profile_name=self._profile_name, home=self._home, timeout=self._timeout,
                    explicit_admin_token=self._key_auth,
                )
            if self._key_auth:
                status, envelope = self._http._request_json(
                    method, self._prefix + path, payload=payload,
                    headers={"x-api-key": self._profile.api_key},
                )
            else:
                status, envelope = self._http.admin_request(
                    method, self._prefix + path, payload=payload, retry_auth=False, allow_login=False,
                )
        except remote.CrsApiError as error:
            failed = True
            if not self._key_auth and error.status == 401:
                failure_code = "admin_session_required"
        except (OSError, ValueError, HTTPException):
            failed = True
        # Raise outside the handler: `from None` alone still retains the private
        # transport exception (and possibly its response body) in __context__.
        if failed:
            raise ManagedCodexError(failure_code or ("outcome_unknown" if method == "POST" else "request_failed"))
        if status not in ((200, 202) if request_id is not None else (200,)):
            code = {
                401: "unauthorized", 403: "forbidden", 404: "not_found", 409: "conflict",
                502: "upstream_error", 504: "upstream_error",
            }.get(status, "http_error")
            raise ManagedCodexError(code, status=status)
        # The shared transport preserves malformed JSON as {"raw": ...}.
        # Do not change that legacy behavior or treat a consumed POST as retryable.
        if method == "POST" and isinstance(envelope, dict) and "raw" in envelope:
            raise ManagedCodexError("outcome_unknown", status=status)
        if not isinstance(envelope, dict) or envelope.get("success") is not True or not isinstance(envelope.get("data"), dict):
            raise ManagedCodexError("invalid_response", status=status)
        data = envelope["data"]
        if data.get("account_id") != self._account_id:
            raise ManagedCodexError("account_mismatch", status=status)
        if request_id is not None:
            return self._receipt(data, request_id=request_id, http_status=status, lookup=method == "GET")
        return data

    def _metadata(self, data: dict, *, fresh=True) -> dict:
        if not isinstance(data, dict):
            raise ManagedCodexError("invalid_response")
        if data.get("account_id") != self._account_id:
            raise ManagedCodexError("account_mismatch")
        if data.get("source") != "upstream":
            raise ManagedCodexError("invalid_response")
        stamp = _iso(data.get("checked_at"))
        age = (datetime.now(timezone.utc) - stamp).total_seconds()
        if fresh and not -30 <= age <= 300:
            raise ManagedCodexError("stale_response")
        return {"account_id": self._account_id, "checked_at": data["checked_at"], "source": "upstream"}

    def usage(self) -> dict:
        """Return fresh, account-pinned upstream windows; never cached CRS usage."""
        data = self._request("/usage")
        return {**self._metadata(data), "rate_limit": _rate_limit(data.get("rate_limit"))}

    def reset_credits(self) -> dict:
        """Read fresh credit metadata without consuming a credit."""
        data = self._request("/reset-credits")
        return {
            **self._metadata(data),
            "available_count": _number(data.get("available_count"), integer=True),
            "credits": _credit_rows(data.get("credits")),
        }

    def _snapshot(self, snapshot, *, nullable: bool) -> dict | None:
        if snapshot is None and nullable:
            return None
        if not isinstance(snapshot, dict):
            raise ManagedCodexError("invalid_response")
        usage, credits = snapshot.get("usage"), snapshot.get("credits")
        # Receipt snapshots are historical evidence, not a fresh usage request.
        return {
            "usage": {
                **self._metadata(usage, fresh=False),
                "rate_limit": _rate_limit(usage.get("rate_limit")),
            },
            "credits": {
                **self._metadata(credits, fresh=False),
                "available_count": _number(credits.get("available_count"), integer=True),
                "credits": _credit_rows(credits.get("credits")),
            },
        }

    def _receipt(self, data: dict, *, request_id: str, http_status: int, lookup: bool = False) -> dict:
        if data.get("request_id") != request_id:
            raise ManagedCodexError("request_mismatch")
        state, code = data.get("status"), data.get("code")
        codes = {
            "reset_verified": ("reset",),
            "nothing_to_reset": ("nothing_to_reset",),
            "no_credit": ("no_credit",),
            "uncertain": ("unknown", "pending", "readback_failed", "storage_unavailable", "precheck_failed"),
        }
        if not isinstance(state, str) or state not in codes or code not in codes[state]:
            raise ManagedCodexError("invalid_response")
        if (http_status == 202 and state != "uncertain") or (
            not lookup and state == "uncertain" and http_status != 202
        ):
            raise ManagedCodexError("invalid_response")
        windows = _number(data.get("windows_reset"), integer=True)
        if state == "reset_verified" and windows <= 0:
            raise ManagedCodexError("invalid_response")
        if state in ("nothing_to_reset", "no_credit") and windows != 0:
            raise ManagedCodexError("invalid_response")
        if "before" not in data or "after" not in data:
            raise ManagedCodexError("invalid_response")
        result = {
            "account_id": self._account_id, "request_id": request_id,
            "status": state, "code": code, "windows_reset": windows,
            "before": self._snapshot(data["before"], nullable=state in ("no_credit", "uncertain")),
            "after": self._snapshot(data["after"], nullable=state in ("no_credit", "uncertain")),
        }
        for flag in ("cache_updated", "scheduling_updated"):
            if flag in data:
                if type(data[flag]) is not bool:
                    raise ManagedCodexError("invalid_response")
                result[flag] = data[flag]
        return result

    def consume(self, request_id: str, *, credit_id: str | None = None, execute: bool = False) -> dict:
        """Plan locally by default; execute one POST, never replay an uncertain write.

        Persist request_id before execution. Reconcile ambiguity with operation(),
        not another consume() call or a new request ID.
        """
        _identifier(request_id, "invalid_request_id")
        if credit_id is not None:
            _identifier(credit_id, "invalid_credit_id")
        if type(execute) is not bool:
            raise ManagedCodexError("invalid_execute")
        if not execute:
            return {
                "account_id": self._account_id, "request_id": request_id, "credit_id": credit_id,
                "status": "dry_run", "code": "dry_run", "mutated": False,
            }
        payload = {"execute": True, "request_id": request_id}
        if credit_id is not None:
            payload["credit_id"] = credit_id
        return self._request(
            "/reset-credits/consume", method="POST", payload=payload, request_id=request_id,
        )

    def operation(self, request_id: str) -> dict:
        """Read one stored receipt; do not replace historical snapshots with GETs."""
        _identifier(request_id, "invalid_request_id")
        return self._request(f"/reset-credits/operations/{request_id}", request_id=request_id)
