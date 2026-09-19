"""Explicit Codex endpoint contracts; all network boundaries are synthetic."""
import base64
import json

import pytest
from chatenv import EnvStore

from chatcrs import codex_direct as direct
from chatcrs.config import CodexConfig


AUTH = "https://auth.example.invalid/selected"
BACKEND = "https://backend.example.invalid/selected/backend-api"
INVALID = [None, "", " ", "http://example.invalid", "https:///missing", "https://user:canary@example.invalid", "https://example.invalid?secret=canary", "https://example.invalid#canary", "https://example.invalid:bad", "https://example.invalid/\ncanary"]


@pytest.fixture
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Network/OAuth reached before endpoint validation")
    monkeypatch.setattr(direct, "_request_json", forbidden)
    return forbidden


@pytest.mark.parametrize("base", INVALID)
@pytest.mark.parametrize("operation", ["refresh", "accounts", "usage", "quota"])
def test_direct_calls_require_valid_explicit_base_before_http(no_network, base, operation):
    with pytest.raises(ValueError, match="(?i)(base|url)") as error:
        if operation == "refresh":
            direct.refresh_access_token(refresh_token="fixture", oauth_base_url=base)
        elif operation == "accounts":
            direct.get_account(access_token="fixture", auth_base_url=base)
        else:
            getattr(direct, "get_" + operation)(access_token="fixture", account_id="fixture", backend_base_url=base)
    assert "canary" not in str(error.value)
    assert "example.invalid" not in str(error.value)


@pytest.mark.parametrize("base", INVALID)
def test_provider_validates_oauth_base_before_refresh_helper(no_network, monkeypatch, tmp_path, base):
    store = EnvStore(tmp_path / "envs")
    values = {"OPENAI_REFRESH_TOKEN": "fixture"}
    if base is not None:
        values["OPENAI_OAUTH_BASE_URL"] = base
    store.save_profile(CodexConfig, "work", values)
    monkeypatch.setattr(direct, "refresh_access_token", no_network)
    monkeypatch.setenv("OPENAI_OAUTH_BASE_URL", AUTH)
    with pytest.raises(ValueError, match="(?i)(base|url)"):
        direct.refresh_chatenv_token(service="Codex", profile="work", home=tmp_path, env_store=store)


@pytest.mark.parametrize("base", [None, "http://example.invalid", "https://user:canary@example.invalid"])
@pytest.mark.parametrize("operation", ["account", "usage", "quota"])
def test_inspection_preflights_destination_before_oauth(no_network, monkeypatch, tmp_path, base, operation):
    values = {"OPENAI_REFRESH_TOKEN": "fixture", "OPENAI_OAUTH_BASE_URL": AUTH}
    key = "OPENAI_OAUTH_BASE_URL" if operation == "account" else "CHATGPT_BACKEND_BASE_URL"
    values.pop(key, None)
    if base is not None:
        values[key] = base
    EnvStore(tmp_path / "envs").save_profile(CodexConfig, "work", values)
    monkeypatch.setattr(direct, "refresh_codex_profile_token", no_network)
    with pytest.raises(ValueError, match="(?i)(base|url)"):
        getattr(direct, "inspect_" + operation)(profile="work", home=tmp_path)


@pytest.mark.parametrize("key", direct.CHATGPT_BACKEND_BASE_URL_KEYS)
def test_configured_backend_alias_requires_valid_url(key):
    assert direct._configured_backend_base_url({key: BACKEND + "/"}) == BACKEND
    with pytest.raises(ValueError):
        direct._configured_backend_base_url({key: "http://example.invalid"})
    with pytest.raises(ValueError):
        direct._configured_backend_base_url({})


@pytest.mark.parametrize("status", [200, 401, 503])
def test_explicit_bases_are_the_only_destinations_even_on_failure(monkeypatch, status):
    calls = []
    def transport(method, url, **kwargs):
        calls.append(url)
        return status, {"access_token": "fixture", "accounts": []}, {}
    monkeypatch.setattr(direct, "_request_json", transport)
    direct.refresh_access_token(refresh_token="fixture", oauth_base_url=AUTH)
    direct.get_account(access_token="fixture", auth_base_url=AUTH)
    direct.get_usage(access_token="fixture", account_id="fixture", backend_base_url=BACKEND)
    direct.get_quota(access_token="fixture", account_id="fixture", backend_base_url=BACKEND)
    assert calls == [AUTH + "/oauth/token", AUTH + "/api/accounts", BACKEND + "/wham/usage", BACKEND + "/codex/responses"]


def test_cached_status_and_claim_resolution_do_not_require_urls(no_network, tmp_path):
    claims = {"https://api.openai.com/auth": {"chatgpt_account_id": "fixture-account"}}
    token = "fixture." + base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=") + ".signature"
    direct.save_token_values(profile="work", home=tmp_path, values={"access_token": token})
    assert direct.token_status(profile="work", home=tmp_path)["token_present"]
    assert direct._account_summary_from_token_claims(token)["account_id_present"]
    account, summary = direct._resolve_account_id_from_profile(profile="work", home=tmp_path, access_token=token, timeout=1)
    assert account == "fixture-account"
    assert summary["source"] == "access_token_claims"
    with pytest.raises(ValueError, match="(?i)(base|url)"):
        direct._resolve_account_id_from_profile(profile="work", home=tmp_path, access_token="opaque", timeout=1)
