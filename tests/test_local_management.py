import json

from click.testing import CliRunner

from chatcrs.cli import main


def test_local_verify_command_returns_json(monkeypatch, tmp_path):
    import chatcrs.local as local

    secrets = tmp_path / ".local-secrets.env"
    secrets.write_text("ADMIN_USERNAME=admin\nADMIN_PASSWORD=secret\n", encoding="utf-8")

    def fake_verify(*, base_url, secrets_file=None):
        assert base_url == "http://127.0.0.1:12404"
        assert secrets_file == secrets
        return {"ok": True, "base_url": base_url, "mutated": False, "admin_login": {"status": 200}}

    monkeypatch.setattr(local, "verify_local_crs", fake_verify)

    result = CliRunner().invoke(
        main,
        [
            "local",
            "verify",
            "--base-url",
            "http://127.0.0.1:12404",
            "--secrets-file",
            str(secrets),
            "--json-output",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["mutated"] is False
    assert payload["admin_login"]["status"] == 200


def test_health_command_uses_base_url_argument(monkeypatch):
    import chatcrs.local as local

    calls = []

    def fake_health(base_url):
        calls.append(base_url)
        return {"ok": True, "base_url": base_url, "health": {"status": 200}}

    monkeypatch.setattr(local, "health_check", fake_health)

    result = CliRunner().invoke(
        main,
        ["health", "--base-url", "http://127.0.0.1:12404", "--json-output"],
    )

    assert result.exit_code == 0, result.output
    assert calls == ["http://127.0.0.1:12404"]
    assert json.loads(result.output)["health"]["status"] == 200


def test_load_local_secrets_redacts_password(tmp_path):
    from chatcrs.local import load_local_secrets

    secrets = tmp_path / ".local-secrets.env"
    secrets.write_text("ADMIN_USERNAME=admin\nADMIN_PASSWORD=secret\n", encoding="utf-8")

    loaded = load_local_secrets(secrets)

    assert loaded["ADMIN_USERNAME"] == "admin"
    assert loaded["ADMIN_PASSWORD"] == "secret"
    assert "secret" not in loaded["_redacted"]
    assert loaded["_redacted"]["ADMIN_PASSWORD"] == "[REDACTED]"
