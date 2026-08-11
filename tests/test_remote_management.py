from __future__ import annotations

import json
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from chatcrs.cli import main
from chatcrs.remote import CrsApiError, CrsHttpClient, CrsProfile, build_stats_time_range_payload, load_crs_profile
from chatcrs.tokens import CrsTokenStore

CRS_ENV_KEYS = (
    "CRS_API_BASE",
    "CRS_API_KEY",
    "CRS_USERNAME",
    "CRS_PASSWORD",
    "CRS_ACCESS_TOKEN",
)


@pytest.fixture(autouse=True)
def isolate_crs_profile_env(tmp_path, monkeypatch):
    """Keep remote-management tests independent from the user's real CRS profiles."""

    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "chatarch-home"))
    for key in CRS_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


class FakeCrsHandler(BaseHTTPRequestHandler):
    admin_token = "admin-session-token"
    last_batch_stats_body: dict[str, Any] | None = None

    def log_message(self, format: str, *args: object) -> None:  # pragma: no cover - silence tests
        return None

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0") or "0")
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _require_admin(self) -> bool:
        auth = self.headers.get("authorization", "")
        if auth != f"Bearer {self.admin_token}":
            self._send_json(401, {"success": False, "message": "missing admin"})
            return False
        return True

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/web/auth/login":
            body = self._read_json()
            if body == {"username": "admin", "password": "secret"}:
                self._send_json(200, {"success": True, "token": self.admin_token, "expiresIn": 86400, "username": "admin"})
            else:
                self._send_json(401, {"success": False})
            return
        if self.path == "/admin/api-keys/batch-stats":
            if not self._require_admin():
                return
            body = self._read_json()
            FakeCrsHandler.last_batch_stats_body = body
            self._send_json(
                200,
                {
                    "success": True,
                    "data": {
                        key_id: {"total": {"requests": 3, "tokens": 42, "cost": 0.0123}}
                        for key_id in body.get("keyIds", [])
                    },
                },
            )
            return
        if self.path == "/admin/api-keys/batch-last-usage":
            if not self._require_admin():
                return
            body = self._read_json()
            self._send_json(
                200,
                {
                    "success": True,
                    "data": {
                        key_id: {
                            "platform": "openai",
                            "accountName": "codex-pro",
                            "recordedAt": "2026-08-05T00:00:00.000Z",
                        }
                        for key_id in body.get("keyIds", [])
                    },
                },
            )
            return
        if self.path == "/admin/openai-accounts/acct_1/reset-status":
            if not self._require_admin():
                return
            self._send_json(200, {"success": True, "message": "reset"})
            return
        self._send_json(404, {"success": False, "path": self.path})

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/admin/openai-accounts":
            if not self._require_admin():
                return
            self._send_json(
                200,
                {
                    "success": True,
                    "data": [
                        {
                            "id": "acct_1",
                            "name": "codex-pro",
                            "accountType": "shared",
                            "isActive": "true",
                            "schedulable": "true",
                            "status": "active",
                            "planType": "pro",
                            "usage": {
                                "daily": {"requests": 1, "tokens": 10},
                                "total": {"requests": 7, "tokens": 99},
                            },
                        }
                    ],
                },
            )
            return
        if self.path == "/admin/api-keys":
            if not self._require_admin():
                return
            self._send_json(
                200,
                {
                    "success": True,
                    "data": {
                        "items": [
                            {
                                "id": "key_1",
                                "name": "primary",
                                "token": "should-not-leak",
                                "apiKey": "should-not-leak",
                                "isActive": True,
                                "permissions": "all",
                                "rateLimitWindow": 60,
                                "usage": {"total": {"requests": 0, "tokens": 0}},
                            }
                        ],
                        "pagination": {"page": 1, "pageSize": 20, "total": 1, "totalPages": 1},
                    },
                },
            )
            return
        if self.path == "/openai/key-info":
            if self.headers.get("authorization") != "Bearer cr_live_key":
                self._send_json(401, {"success": False, "message": "missing api key"})
                return
            self._send_json(
                200,
                {
                    "name": "primary",
                    "permissions": "all",
                    "accountBinding": {"platform": "openai", "accountId": "acct_1"},
                    "usage": {"total": {"requests": 7, "tokens": 99}},
                },
            )
            return
        self._send_json(404, {"success": False, "path": self.path})


def run_fake_crs():
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeCrsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_port}"


def test_load_crs_admin_profile_reads_crs_admin_env_without_exposing_values(tmp_path: Path):
    home = tmp_path / "chatarch"
    env_dir = home / "envs" / "CRS"
    env_dir.mkdir(parents=True)
    (env_dir / "admin.env").write_text(
        "CRS_API_BASE=https://crs.example.test\n"
        "CRS_API_KEY=cr_secret\n"
        "CRS_USERNAME=admin\n"
        "CRS_PASSWORD=secret\n"
        "CRS_ACCESS_TOKEN=\n"
    )

    profile = load_crs_profile("admin", home=home)

    assert profile.base_url == "https://crs.example.test"
    assert profile.api_key == "cr_secret"
    assert profile.username == "admin"
    assert profile.password == "secret"
    assert profile.safe_summary() == {
        "base_url": "https://crs.example.test",
        "api_key_present": True,
        "username_present": True,
        "password_present": True,
        "admin_token_present": False,
    }


def test_admin_login_failure_reports_status_and_safe_reason_without_secrets():
    server, base_url = run_fake_crs()
    try:
        client = CrsHttpClient(CrsProfile(base_url=base_url, username="admin", password="wrong-secret"))

        try:
            client.login()
        except CrsApiError as exc:
            message = str(exc)
        else:  # pragma: no cover - defensive failure clarity
            raise AssertionError("login unexpectedly succeeded")

        assert "CRS admin login failed" in message
        assert "status=401" in message
        assert "wrong-secret" not in message
        assert FakeCrsHandler.admin_token not in message
    finally:
        server.shutdown()


def test_remote_admin_cli_reports_accounts_usage_and_key_stats_without_secrets():
    server, base_url = run_fake_crs()
    runner = CliRunner()
    try:
        account_result = runner.invoke(
            main,
            [
                "admin",
                "accounts",
                "usage",
                "--base-url",
                base_url,
                "--username",
                "admin",
                "--password",
                "secret",
                "--json-output",
            ],
        )
        assert account_result.exit_code == 0, account_result.output
        account_payload = json.loads(account_result.output)
        assert account_payload["ok"] is True
        assert account_payload["accounts"][0]["id"] == "acct_1"
        assert account_payload["accounts"][0]["usage"]["total"]["requests"] == 7
        assert "admin-session-token" not in account_result.output

        key_result = runner.invoke(
            main,
            [
                "admin",
                "keys",
                "list",
                "--base-url",
                base_url,
                "--username",
                "admin",
                "--password",
                "secret",
                "--include-stats",
                "--time-range",
                "30days",
                "--json-output",
            ],
        )
        assert key_result.exit_code == 0, key_result.output
        key_payload = json.loads(key_result.output)
        assert key_payload["ok"] is True
        assert key_payload["keys"][0]["id"] == "key_1"
        assert key_payload["keys"][0]["stats"]["total"]["requests"] == 3
        assert key_payload["keys"][0]["last_usage"]["accountName"] == "codex-pro"
        assert key_payload["time_range"] == "30days"
        assert key_payload["stats_time_range"] == "custom"
        stats_body = FakeCrsHandler.last_batch_stats_body
        assert stats_body is not None
        assert stats_body["keyIds"] == ["key_1"]
        assert stats_body["timeRange"] == "custom"
        assert stats_body["startDate"] == key_payload["stats_start_date"]
        assert stats_body["endDate"] == key_payload["stats_end_date"]
        assert "should-not-leak" not in key_result.output
    finally:
        server.shutdown()
        server.server_close()


def test_legacy_30days_key_stats_range_uses_crs_custom_date_window():
    payload = build_stats_time_range_payload("30days", today=date(2026, 8, 11))

    assert payload == {"timeRange": "custom", "startDate": "2026-07-13", "endDate": "2026-08-11"}


def test_api_key_only_cli_reports_key_info_without_admin_credentials():
    server, base_url = run_fake_crs()
    runner = CliRunner()
    try:
        result = runner.invoke(
            main,
            [
                "key",
                "info",
                "--base-url",
                base_url,
                "--api-key",
                "cr_live_key",
                "--json-output",
            ],
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["ok"] is True
        assert payload["key_info"]["name"] == "primary"
        assert payload["key_info"]["usage"]["total"]["requests"] == 7
        assert "cr_live_key" not in result.output
    finally:
        server.shutdown()
        server.server_close()


def test_api_key_only_help_does_not_advertise_admin_credentials():
    result = CliRunner().invoke(main, ["key", "info", "--help"])

    assert result.exit_code == 0
    assert "--api-key" in result.output
    assert "--base-url" in result.output
    assert "--path" in result.output
    assert "--username" not in result.output
    assert "--password" not in result.output
    assert "--admin-token" not in result.output


def _write_crs_profile(home: Path, *, base_url: str, access_token: str = "") -> None:
    env_dir = home / "envs" / "CRS"
    env_dir.mkdir(parents=True)
    (env_dir / "admin.env").write_text(
        f"CRS_API_BASE={base_url}\n"
        "CRS_API_KEY=cr_live_key\n"
        "CRS_USERNAME=admin\n"
        "CRS_PASSWORD=secret\n"
        f"CRS_ACCESS_TOKEN={access_token}\n"
    )


def test_admin_login_can_save_session_token_to_parallel_token_store(tmp_path: Path):
    server, base_url = run_fake_crs()
    home = tmp_path / "chatarch-home"
    _write_crs_profile(home, base_url=base_url)
    runner = CliRunner(env={"CHATARCH_HOME": str(home)})
    try:
        result = runner.invoke(main, ["admin", "login", "--profile", "admin", "--save-token", "--json-output"])

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["ok"] is True
        assert payload["token_saved"] is True
        assert payload["base_url"] == base_url
        assert payload["token_file"].endswith("tokens/CRS/admin.json")
        assert FakeCrsHandler.admin_token not in result.output
        token_file = home / "tokens" / "CRS" / "admin.json"
        assert token_file.exists()
        saved = json.loads(token_file.read_text())
        assert saved["access_token"] == FakeCrsHandler.admin_token
        assert saved["base_url"] == base_url
    finally:
        server.shutdown()
        server.server_close()


def test_admin_token_refresh_status_and_clear_commands_manage_runtime_token_file(tmp_path: Path):
    server, base_url = run_fake_crs()
    home = tmp_path / "chatarch-home"
    _write_crs_profile(home, base_url=base_url)
    runner = CliRunner(env={"CHATARCH_HOME": str(home)})
    try:
        refresh = runner.invoke(main, ["admin", "token", "refresh", "--profile", "admin", "--json-output"])
        assert refresh.exit_code == 0, refresh.output
        refresh_payload = json.loads(refresh.output)
        assert refresh_payload["ok"] is True
        assert refresh_payload["token_saved"] is True
        assert FakeCrsHandler.admin_token not in refresh.output

        status = runner.invoke(main, ["admin", "token", "status", "--profile", "admin", "--json-output"])
        assert status.exit_code == 0, status.output
        status_payload = json.loads(status.output)
        assert status_payload["token_file_exists"] is True
        assert status_payload["token_present"] is True
        assert status_payload["base_url_match"] is True
        assert FakeCrsHandler.admin_token not in status.output

        dry_run = runner.invoke(main, ["admin", "token", "clear", "--profile", "admin", "--json-output"])
        assert dry_run.exit_code == 0, dry_run.output
        assert json.loads(dry_run.output)["mutated"] is False
        assert (home / "tokens" / "CRS" / "admin.json").exists()

        cleared = runner.invoke(main, ["admin", "token", "clear", "--profile", "admin", "--execute", "--json-output"])
        assert cleared.exit_code == 0, cleared.output
        assert json.loads(cleared.output)["mutated"] is True
        assert not (home / "tokens" / "CRS" / "admin.json").exists()
    finally:
        server.shutdown()
        server.server_close()


def test_admin_requests_retry_once_and_refresh_token_store_after_stale_token(tmp_path: Path):
    server, base_url = run_fake_crs()
    home = tmp_path / "chatarch-home"
    _write_crs_profile(home, base_url=base_url)
    stale_profile = CrsProfile(base_url=base_url, username="admin", password="secret")
    CrsTokenStore(profile_name="admin", profile=stale_profile, home=home).save_login_token(
        "old-session-token", expires_in=3600, username="admin"
    )
    runner = CliRunner(env={"CHATARCH_HOME": str(home)})
    try:
        result = runner.invoke(main, ["admin", "accounts", "usage", "--profile", "admin", "--json-output"])

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["ok"] is True
        assert payload["count"] == 1
        assert payload["accounts"][0]["id"] == "acct_1"
        assert "old-session-token" not in result.output
        assert FakeCrsHandler.admin_token not in result.output
        saved = json.loads((home / "tokens" / "CRS" / "admin.json").read_text())
        assert saved["access_token"] == FakeCrsHandler.admin_token
    finally:
        server.shutdown()
        server.server_close()
