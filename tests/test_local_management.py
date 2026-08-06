import json

from click.testing import CliRunner

from chatcrs.cli import main


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


def test_health_command_reads_crs_api_base(monkeypatch):
    import chatcrs.local as local

    monkeypatch.setenv("CRS_API_BASE", "https://crs.example.test/")
    monkeypatch.setattr(local, "_request_status", lambda base, path, **kwargs: (200, b'{"status":"healthy"}'))

    payload = local.health_check()

    assert payload["ok"] is True
    assert payload["base_url"] == "https://crs.example.test"
    assert payload["mutated"] is False
