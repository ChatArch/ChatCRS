from __future__ import annotations

from click.testing import CliRunner

from chatcrs.cli import main
from chatcrs.cutover import formal_single_active_precheck
from chatcrs.nginx import plan_nginx_cutover
from chatcrs.paths import CrsPaths
from chatcrs.redaction import redact


def test_cli_registers_inspect_only_as_read_only_management_command():
    result = CliRunner().invoke(main, ["inspect", "--help"])
    assert result.exit_code == 0, result.output


def test_redact_masks_sensitive_keys_and_token_patterns():
    payload = {
        "token": "«redacted:ghp_…»",
        "nested": {"REDIS_PASSWORD": "super-secret", "PORT": "12391"},
        "line": "Authorization: Bearer ***",
    }

    redacted = redact(payload)

    assert redacted["token"] == "[REDACTED]"
    assert redacted["nested"]["REDIS_PASSWORD"] == "[REDACTED]"
    assert redacted["nested"]["PORT"] == "12391"
    assert "abcdefghijklmnopqrstuvwxyz" not in redacted["line"]
    assert "[REDACTED]" in redacted["line"]


def test_nginx_plan_cutover_generates_diff_without_mutating_file(tmp_path):
    config = tmp_path / "crs.conf"
    original = """server {
    location / {
        proxy_pass http://127.0.0.1:12390;
    }
}
"""
    config.write_text(original)

    plan = plan_nginx_cutover(config, from_port=12390, to_port=12391)

    assert plan["ok"] is True
    assert plan["read_only"] is True
    assert plan["mutated"] is False
    assert plan["changed"] is True
    assert "-        proxy_pass http://127.0.0.1:12390;" in plan["diff"]
    assert "+        proxy_pass http://127.0.0.1:12391;" in plan["diff"]
    assert config.read_text() == original


def test_formal_single_active_precheck_is_read_only_and_recommends_db0():
    paths = CrsPaths(
        old_app="/old/app",
        new_app="/new/app",
        nginx_config="/etc/nginx/sites-available/single/crs.conf",
        new_service="crs-chatarch.service",
        old_port=12390,
        new_port=12391,
    )

    def probe(name: str):
        return {
            "old_health": {"status": 200},
            "new_health": {"status": 200},
            "new_images_no_auth": {"status": 401},
            "systemd": {"active": "active", "enabled": "enabled"},
            "nginx_proxy_line": "proxy_pass http://127.0.0.1:12390;",
            "redis": {"db0_size": "2024", "db1_size": "2012"},
            "new_redis_db": "1",
        }[name]

    result = formal_single_active_precheck(paths, probe=probe)

    assert result["mutated"] is False
    assert result["ready_for_formal_cutover_after_packages"] is True
    assert result["current"]["new"]["redis_db"] == "1"
    assert result["formal_cutover_recommendation"]["target_new_redis_db"] == "0"
