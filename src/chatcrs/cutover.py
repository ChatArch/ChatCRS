"""Formal cutover precheck helpers."""

from __future__ import annotations

from typing import Any, Callable

from .paths import CrsPaths
from .redaction import redact
from .runtime import default_probe

Probe = Callable[[str], Any]


def formal_single_active_precheck(paths: CrsPaths | None = None, *, probe: Probe | None = None) -> dict[str, Any]:
    """Return read-only readiness for a single-active DB0 cutover."""

    paths = paths or CrsPaths()
    probe = probe or (lambda name: default_probe(paths, name))

    old_health = probe("old_health")
    new_health = probe("new_health")
    images = probe("new_images_no_auth")
    systemd = probe("systemd")
    nginx_line = probe("nginx_proxy_line")
    redis = probe("redis")
    new_redis_db = probe("new_redis_db")

    ready = all(
        [
            old_health.get("status") == 200,
            new_health.get("status") == 200,
            images.get("status") == 401,
            systemd.get("active") == "active",
            systemd.get("enabled") == "enabled",
            "12390" in nginx_line,
        ]
    )

    return redact({
        "mode": "formal-single-active-precheck-read-only",
        "mutated": False,
        "current": {
            "old": {"app": paths.old_app, "port": paths.old_port, "health": old_health},
            "new": {
                "app": paths.new_app,
                "port": paths.new_port,
                "redis_db": str(new_redis_db),
                "health": new_health,
                "images_no_auth": images,
                "systemd": systemd,
            },
            "nginx_proxy_line": nginx_line,
            "redis": redis,
        },
        "formal_cutover_recommendation": {
            "target_new_redis_db": "0",
            "reason": "Formal operation is single-active; DB0 is canonical live data.",
        },
        "ready_for_formal_cutover_after_packages": ready,
    })
