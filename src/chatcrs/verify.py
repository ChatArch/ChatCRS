"""Read-only CRS verification helpers."""

from __future__ import annotations

from typing import Any

from .cutover import Probe
from .paths import CrsPaths
from .redaction import redact
from .runtime import default_probe


def verify_sidecar(paths: CrsPaths | None = None, *, probe: Probe | None = None) -> dict[str, Any]:
    """Verify old/new CRS services and the new Images auth guard."""

    paths = paths or CrsPaths()
    probe = probe or (lambda name: default_probe(paths, name))
    old_health = probe("old_health")
    new_health = probe("new_health")
    images = probe("new_images_no_auth")
    systemd = probe("systemd")
    checks = {
        "old_health_200": old_health.get("status") == 200,
        "new_health_200": new_health.get("status") == 200,
        "new_images_route_auth_guard_401": images.get("status") == 401,
        "new_systemd_active": systemd.get("active") == "active",
        "new_systemd_enabled": systemd.get("enabled") == "enabled",
    }
    return redact({
        "mutated": False,
        "old": {"port": paths.old_port, "health": old_health},
        "new": {"port": paths.new_port, "health": new_health, "images_no_auth": images, "systemd": systemd},
        "checks": checks,
        "ok": all(checks.values()),
    })
