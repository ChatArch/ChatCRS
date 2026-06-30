"""Secret redaction helpers for ChatCRS output."""

from __future__ import annotations

import re
from typing import Any

SENSITIVE_KEY_RE = re.compile(
    r"(token|secret|password|passwd|authorization|api[_-]?key|credential|jwt|encryption|refresh)",
    re.IGNORECASE,
)
GITHUB_TOKEN_RE = re.compile(r"gh[pousr]_[A-Za-z0-9_]{12,}")
AUTH_RE = re.compile(r"(?i)(authorization:\s*(?:bearer|basic)\s+)[^\s,;]+")
ASSIGNMENT_RE = re.compile(
    r"(?i)((?:token|secret|password|passwd|api[_-]?key|credential|jwt|encryption|refresh)[A-Z0-9_\-]*\s*[=:]\s*)[^\s,'\"]+"
)


def redact(value: Any) -> Any:
    """Return *value* with likely secret material masked."""

    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if SENSITIVE_KEY_RE.search(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    if isinstance(value, str):
        masked = AUTH_RE.sub(r"\1[REDACTED]", value)
        masked = GITHUB_TOKEN_RE.sub("[REDACTED]", masked)
        masked = ASSIGNMENT_RE.sub(r"\1[REDACTED]", masked)
        return masked
    return value
