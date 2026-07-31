"""Path and runtime defaults for ChatCRS management helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CrsPaths:
    """Filesystem/service locations for CRS management operations."""

    old_app: str = "/home/zhihong/claude-relay-service/app"
    new_app: str = "/home/zhihong/claude-relay-service-chatarch/app"
    nginx_config: str = "/etc/nginx/sites-available/single/crs.conf"
    new_service: str = "crs-chatarch.service"
    old_port: int = 12390
    new_port: int = 12391

    @property
    def old_app_path(self) -> Path:
        return Path(self.old_app)

    @property
    def new_app_path(self) -> Path:
        return Path(self.new_app)

    @property
    def nginx_config_path(self) -> Path:
        return Path(self.nginx_config)
