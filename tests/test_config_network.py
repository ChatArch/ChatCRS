"""Transport-isolated coverage for the real ChatEnv CRS test entry point."""
from email.message import Message
import io
import json
import urllib.error
import urllib.request

import click
import pytest
from chatenv import EnvStore, get_paths
from chatenv.cli import cli as chatenv_cli
from click.testing import CliRunner

from chatcrs.config import ChatcrsConfig, CodexConfig
from chatcrs.tokens import CrsTokenStore

KEY = "fixture-private-caller-key"
PRIVATE = "fixture-private-upstream-detail"


class Response(io.BytesIO):
    status = 200

    def __init__(self, body, content_type="application/json"):
        super().__init__(body)
        self.headers = {"content-type": content_type}


def sse(*events):
    return b"".join(b"data: " + json.dumps(e).encode() + b"\n\n" for e in events)


def completed():
    return sse(
        {"type": "response.output_text.delta", "delta": "OK"},
        {"type": "response.completed", "response": {"status": "completed"}},
    )


@pytest.fixture
def setup_config(tmp_path, monkeypatch):
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "chatarch"))
    for name in ChatcrsConfig.get_fields():
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("CRS_API_MODEL", raising=False)
    values = {"CRS_API_BASE": "https://fixture.invalid/", "CRS_API_KEY": KEY}
    requests = []

    def forbid_tokens(*args, **kwargs):
        pytest.fail("CRS key test must not load admin tokens")

    monkeypatch.setattr(CrsTokenStore, "load_token", forbid_tokens)

    def configure(*, model=None, key_status=200, key_body=None, stream=None, stream_status=200):
        if model is not None:
            values["CRS_API_MODEL"] = model
        EnvStore(get_paths().envs_dir).save_active(ChatcrsConfig, values)

        def urlopen(request, timeout):
            requests.append(request)
            assert 0 < timeout <= 20
            if request.full_url.endswith("/openai/key-info"):
                body = json.dumps(key_body if key_body is not None else {"name": "fixture"}).encode()
                if key_status != 200:
                    raise urllib.error.HTTPError(request.full_url, key_status, PRIVATE, Message(), io.BytesIO(body))
                return Response(body)
            assert request.full_url == "https://fixture.invalid/openai/responses"
            if stream_status != 200:
                raise urllib.error.HTTPError(request.full_url, stream_status, PRIVATE, Message(), io.BytesIO(KEY.encode()))
            return Response(completed() if stream is None else stream, "text/event-stream")

        monkeypatch.setattr(urllib.request, "urlopen", urlopen)
        return requests

    return configure, values


def test_key_only_authenticates_and_explicitly_skips_upstream(setup_config, capsys):
    configure, _ = setup_config
    requests = configure()
    ChatcrsConfig.test()
    assert len(requests) == 1
    assert requests[0].get_header("Authorization") == f"Bearer {KEY}"
    output = capsys.readouterr().out
    assert "Key authentication succeeded" in output
    assert "upstream not tested" in output
    assert KEY not in output


@pytest.mark.parametrize("missing", ["CRS_API_BASE", "CRS_API_KEY"])
def test_missing_required_field_fails_before_network(setup_config, missing):
    configure, values = setup_config
    values[missing] = ""
    requests = configure()
    with pytest.raises(click.ClickException, match=missing):
        ChatcrsConfig.test()
    assert requests == []


@pytest.mark.parametrize("status,body", [(401, {"error": PRIVATE}), (403, {"error": KEY}), (200, {"success": False}), (200, {"error": PRIVATE})])
def test_auth_failure_is_safe_and_never_probes_model(setup_config, status, body, capsys):
    configure, _ = setup_config
    requests = configure(model="fixture-model", key_status=status, key_body=body)
    with pytest.raises(click.ClickException) as exc:
        ChatcrsConfig.test()
    assert len(requests) == 1
    assert KEY not in str(exc.value) + capsys.readouterr().out
    assert PRIVATE not in str(exc.value)


def test_explicit_model_uses_same_key_and_codex_stream_contract(setup_config, capsys):
    configure, _ = setup_config
    requests = configure(model="fixture-model")
    ChatcrsConfig.test()
    assert len(requests) == 2
    assert {r.get_header("Authorization") for r in requests} == {f"Bearer {KEY}"}
    request = requests[1]
    assert request.method == "POST"
    assert request.get_header("Accept") == "text/event-stream"
    payload = json.loads(request.data)
    assert payload == {
        "model": "fixture-model",
        "input": [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": "Reply OK."}]}],
        "stream": True,
        "store": False,
    }
    assert "Codex Responses text test succeeded" in capsys.readouterr().out


@pytest.mark.parametrize("stream", [
    b"", b"data: [DONE]\n\n", b"data: not-json\n\n", b"x" * 65537,
    sse({"type": "response.output_text.delta", "delta": "OK"}),
    sse({"type": "response.failed", "response": {"error": {"message": PRIVATE}}}),
    sse({"type": "error", "error": {"message": KEY}}),
    sse({"type": "response.completed", "response": {"status": "completed"}}),
    sse({"type": "response.incomplete", "response": {"status": "incomplete"}}),
], ids=["empty", "done-only", "malformed", "over-limit", "truncated", "failed", "error", "no-text", "incomplete"])
def test_stream_failure_or_no_completed_text_is_nonzero_and_safe(setup_config, stream, capsys):
    configure, _ = setup_config
    configure(model="fixture-model", stream=stream)
    with pytest.raises(click.ClickException) as exc:
        ChatcrsConfig.test()
    output = str(exc.value) + capsys.readouterr().out
    assert KEY not in output
    assert PRIVATE not in output
    assert "text test succeeded" not in output


def test_upstream_http_error_is_nonzero_and_safe(setup_config):
    configure, _ = setup_config
    configure(model="fixture-model", stream_status=429)
    with pytest.raises(click.ClickException) as exc:
        ChatcrsConfig.test()
    assert KEY not in str(exc.value)
    assert PRIVATE not in str(exc.value)


def test_network_exception_is_safe(setup_config, monkeypatch):
    configure, _ = setup_config
    configure()

    def fail(*args, **kwargs):
        raise urllib.error.URLError(PRIVATE + KEY)

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    result = CliRunner().invoke(chatenv_cli, ["test", "-t", "crs", "-I"])
    assert result.exit_code != 0
    assert KEY not in result.output
    assert PRIVATE not in result.output
    assert "Traceback" not in result.output


def test_chatenv_registration_and_home_override_use_selected_profile(setup_config, tmp_path):
    configure, values = setup_config
    requests = configure()
    other_home = tmp_path / "other-home"
    selected = {**values, "CRS_API_KEY": "fixture-selected-key"}
    EnvStore(get_paths(other_home).envs_dir).save_active(ChatcrsConfig, selected)
    result = CliRunner().invoke(chatenv_cli, ["--home", str(other_home), "test", "-t", "crs", "-I"])
    assert result.exit_code == 0, result.output
    assert len(requests) == 1
    assert requests[0].get_header("Authorization") == "Bearer fixture-selected-key"


def test_codex_schema_test_stays_offline(setup_config, capsys):
    configure, _ = setup_config
    requests = configure()
    CodexConfig.test()
    assert requests == []
    assert "Schema loaded" in capsys.readouterr().out
