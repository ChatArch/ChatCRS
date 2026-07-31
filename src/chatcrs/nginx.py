"""Read-only Nginx planning helpers."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from .redaction import redact


def plan_nginx_cutover(config: str | Path, *, from_port: int = 12390, to_port: int = 12391) -> dict[str, Any]:
    """Return a proposed Nginx proxy_pass diff without writing the config."""

    path = Path(config)
    if not path.exists():
        return {
            "ok": False,
            "read_only": True,
            "mutated": False,
            "config": str(path),
            "reason": "config_missing",
        }
    original = path.read_text(errors="replace")
    proposed = original.replace(f"127.0.0.1:{from_port}", f"127.0.0.1:{to_port}")
    diff = "".join(
        difflib.unified_diff(
            original.splitlines(True),
            proposed.splitlines(True),
            fromfile=str(path),
            tofile=f"{path}.proposed",
        )
    )
    return redact({
        "ok": True,
        "read_only": True,
        "mutated": False,
        "config": str(path),
        "from_port": from_port,
        "to_port": to_port,
        "changed": original != proposed,
        "diff": diff,
    })
