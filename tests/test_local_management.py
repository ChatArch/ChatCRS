import base64
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


def test_verify_images_preflight_checks_key_and_regular_model(monkeypatch, tmp_path):
    import chatcrs.local as local

    env_file = tmp_path / "openai.env"
    env_file.write_text("OPENAI_API_KEY='secret-crs-key'\n", encoding="utf-8")
    calls = []

    def fake_request(base_url, path, **kwargs):
        calls.append((base_url, path, kwargs))
        assert kwargs["headers"]["authorization"] == "Bearer secret-crs-key"
        if path == "/openai/key-info":
            return 200, json.dumps({"name": "image-test", "permissions": ["openai"]}).encode()
        if path == "/openai/v1/responses":
            return 200, b'data: {"text":"CHATCRS_KEY_OK"}\n\n'
        raise AssertionError(path)

    monkeypatch.setattr(local, "_request_status", fake_request)

    payload = local.verify_images_api(
        base_url="http://127.0.0.1:12392",
        openai_env_file=env_file,
    )

    assert payload["ok"] is True
    assert payload["mutated"] is False
    assert payload["api_key"] == "[REDACTED]"
    assert payload["key_info"]["name"] == "image-test"
    assert payload["regular_model"]["expected_marker"] is True
    assert payload["image"]["executed"] is False
    assert [path for _, path, _ in calls] == ["/openai/key-info", "/openai/v1/responses"]


def test_verify_images_execute_writes_valid_png(monkeypatch, tmp_path):
    import chatcrs.local as local

    env_file = tmp_path / "openai.env"
    env_file.write_text("OPENAI_API_KEY=secret-crs-key\n", encoding="utf-8")
    output = tmp_path / "result.png"
    png = b"\x89PNG\r\n\x1a\n" + b"image-bytes"

    def fake_request(base_url, path, **kwargs):
        if path == "/openai/key-info":
            return 200, b'{"name":"image-test","permissions":["openai"]}'
        if path == "/openai/v1/responses":
            return 200, b"data: CHATCRS_KEY_OK\n\n"
        if path == "/openai/v1/images/generations":
            body = {"data": [{"b64_json": base64.b64encode(png).decode()}]}
            return 200, json.dumps(body).encode()
        raise AssertionError(path)

    monkeypatch.setattr(local, "_request_status", fake_request)

    payload = local.verify_images_api(
        openai_env_file=env_file,
        output_path=output,
        execute_image=True,
    )

    assert payload["ok"] is True
    assert payload["mutated"] is True
    assert payload["image"]["executed"] is True
    assert payload["image"]["png"] is True
    assert output.read_bytes() == png


def test_verify_images_cli_is_gated_and_redacted(monkeypatch, tmp_path):
    import chatcrs.local as local

    env_file = tmp_path / "openai.env"
    env_file.write_text("OPENAI_API_KEY=secret-crs-key\n", encoding="utf-8")

    def fake_verify(**kwargs):
        assert kwargs["execute_image"] is False
        assert kwargs["openai_env_file"] == env_file
        return {
            "ok": True,
            "mutated": False,
            "api_key": "[REDACTED]",
            "key_info": {"ok": True},
            "regular_model": {"ok": True},
            "image": {"ok": None, "executed": False},
        }

    monkeypatch.setattr(local, "verify_images_api", fake_verify)
    result = CliRunner().invoke(
        main,
        ["verify", "images", "--openai-env-file", str(env_file), "--json-output"],
    )

    assert result.exit_code == 0, result.output
    assert "secret-crs-key" not in result.output
    assert json.loads(result.output)["api_key"] == "[REDACTED]"
