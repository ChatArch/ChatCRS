"""Explicit endpoint overrides must honor the same secret-routing policy."""
import pytest

from chatcrs import codex_direct as direct


@pytest.mark.parametrize("operation,keyword", [
    (direct.get_usage, "usage_url"),
    (direct.get_quota, "responses_url"),
])
@pytest.mark.parametrize("url", [
    "http://example.invalid/endpoint",
    "https://user:credential-canary@example.invalid/endpoint",
    "https://example.invalid/endpoint?credential-canary=1",
    "https://example.invalid/endpoint#credential-canary",
    "",
])
def test_endpoint_override_is_validated_before_http(monkeypatch, operation, keyword, url):
    calls = []
    monkeypatch.setattr(direct, "_request_json", lambda *a, **k: calls.append(a) or (200, {}, {}))
    with pytest.raises(ValueError) as error:
        operation(access_token="fixture-token", account_id="fixture-account",
                  backend_base_url="https://relay.example.invalid/backend-api", **{keyword: url})
    assert calls == []
    assert "credential-canary" not in str(error.value)


@pytest.mark.parametrize("operation,keyword", [
    (direct.get_usage, "usage_url"),
    (direct.get_quota, "responses_url"),
])
def test_valid_full_endpoint_is_preserved_exactly(monkeypatch, operation, keyword):
    calls = []
    monkeypatch.setattr(direct, "_request_json", lambda *a, **k: calls.append(a[1]) or (200, {}, {}))
    endpoint = "https://relay.example.invalid/nested/endpoint/"
    operation(access_token="fixture-token", account_id="fixture-account", **{keyword: endpoint})
    assert calls == [endpoint]
