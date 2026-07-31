"""Read-only CRS layout inspection helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .nginx import plan_nginx_cutover
from .paths import CrsPaths
from .redaction import redact
from .runtime import default_probe, env_value, nginx_proxy_line, run_command


def inspect_crs_layout(paths: CrsPaths | None = None) -> dict[str, Any]:
    """Inspect known CRS runtime paths without mutating anything."""

    paths = paths or CrsPaths()
    crs_links = []
    for candidate in [Path("/usr/bin/crs"), Path("/bin/crs")]:
        if candidate.exists() or candidate.is_symlink():
            crs_links.append({"path": str(candidate), "target": str(candidate.resolve()), "is_symlink": candidate.is_symlink()})
    return redact({
        "mutated": False,
        "workspace_hint": "/home/zhihong/Playground",
        "crs_executables": crs_links,
        "old": {
            "app": paths.old_app,
            "port": paths.old_port,
            "exists": paths.old_app_path.exists(),
            "redis_db": env_value(paths.old_app_path / ".env", "REDIS_DB", "0"),
            "health": default_probe(paths, "old_health"),
        },
        "new": {
            "app": paths.new_app,
            "port": paths.new_port,
            "exists": paths.new_app_path.exists(),
            "redis_db": env_value(paths.new_app_path / ".env", "REDIS_DB", "0"),
            "health": default_probe(paths, "new_health"),
            "systemd": default_probe(paths, "systemd"),
        },
        "nginx": {
            "config": paths.nginx_config,
            "proxy_line": nginx_proxy_line(paths.nginx_config_path),
            "cutover_plan": plan_nginx_cutover(paths.nginx_config_path, from_port=paths.old_port, to_port=paths.new_port),
        },
        "redis": default_probe(paths, "redis"),
        "ports": run_command(["ss", "-ltnp"]),
    })
