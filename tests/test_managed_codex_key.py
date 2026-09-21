"""Dedicated CRS management-key auth never falls back to an Admin login."""
import json

import pytest
from chatenv import EnvStore, get_paths
from chatcrs import remote
from chatcrs.config import ChatcrsConfig
from chatcrs.managed_codex import CrsManagedCodexClient, ManagedCodexError
from test_managed_codex import ACCOUNT, BASE, PREFIX, usage_data, credits_data, receipt_data

KEY = "crsm_" + "A" * 43


@pytest.fixture
def managed(tmp_path, monkeypatch):
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))
    EnvStore(get_paths(tmp_path).envs_dir).save_profile(ChatcrsConfig, "manager", {
        "CRS_API_BASE": BASE, "CRS_API_KEY": KEY,
        "CRS_USERNAME": "must-not-login", "CRS_PASSWORD": "must-not-login",
    })
    monkeypatch.setattr(remote.CrsTokenStore, "load_token", lambda *a: pytest.fail("Admin session read"))
    monkeypatch.setattr(remote.CrsHttpClient, "login", lambda *a, **k: pytest.fail("Admin login fallback"))
    return CrsManagedCodexClient.from_profile("manager", account_id=ACCOUNT, home=tmp_path)


@pytest.mark.parametrize("method,path,data", [
    ("usage", "/usage", usage_data), ("reset_credits", "/reset-credits", credits_data),
])
def test_key_only_reads_have_no_admin_session_or_local_oauth(managed, monkeypatch, method, path, data):
    calls = []
    payload = data()
    def request(self, verb, url, *, payload=None, headers=None):
        calls.append((verb, url, headers))
        return 200, {"success": True, "data": expected}
    expected = payload
    monkeypatch.setattr(remote.CrsHttpClient, "_request_json", request)
    assert getattr(managed, method)() == expected
    assert calls == [("GET", PREFIX + path, {"x-api-key": KEY})]
    assert KEY not in repr(managed)


def test_key_consumption_posts_once_without_login(managed, monkeypatch):
    calls = []
    result = receipt_data()
    def request(self, verb, url, *, payload=None, headers=None):
        calls.append((verb, url, payload, headers))
        return 200, {"success": True, "data": result}
    monkeypatch.setattr(remote.CrsHttpClient, "_request_json", request)
    assert managed.consume("request-1", execute=True) == result
    assert calls == [("POST", PREFIX + "/reset-credits/consume", {"execute": True, "request_id": "request-1"}, {"x-api-key": KEY})]


@pytest.mark.parametrize("verb", ["usage", "consume"])
@pytest.mark.parametrize("status", [401, 403])
def test_rejected_key_never_borrows_admin_credentials(managed, monkeypatch, verb, status):
    calls = []
    def request(self, method, path, **kwargs):
        calls.append(path)
        return status, {"success": False, "error": {"code": KEY}}
    monkeypatch.setattr(remote.CrsHttpClient, "_request_json", request)
    with pytest.raises(ManagedCodexError) as exc:
        managed.consume("request-1", execute=True) if verb == "consume" else managed.usage()
    assert len(calls) == 1
    assert KEY not in str(exc.value)


def test_model_key_is_not_a_management_key(tmp_path, monkeypatch):
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))
    EnvStore(get_paths(tmp_path).envs_dir).save_profile(ChatcrsConfig, "model", {
        "CRS_API_BASE": BASE, "CRS_API_KEY": "cr_model_fixture",
        "CRS_USERNAME": "must-not-fallback", "CRS_PASSWORD": "must-not-fallback",
    })
    with pytest.raises(ManagedCodexError) as exc:
        CrsManagedCodexClient.from_profile("model", account_id=ACCOUNT, home=tmp_path)
    assert exc.value.code == "invalid_management_key"


def test_required_key_never_uses_a_password_only_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))
    EnvStore(get_paths(tmp_path).envs_dir).save_profile(ChatcrsConfig, "password-only", {
        "CRS_API_BASE": BASE, "CRS_USERNAME": "do-not-use", "CRS_PASSWORD": "do-not-use",
    })
    monkeypatch.setattr(remote.CrsTokenStore, "load_token", lambda *a: pytest.fail("Admin token fallback"))
    with pytest.raises(ManagedCodexError) as exc:
        CrsManagedCodexClient.from_profile("password-only", account_id=ACCOUNT, home=tmp_path, require_management_key=True)
    assert exc.value.code == "management_key_required"


def test_operation_lookup_accepts_uncertain_http_200(managed, monkeypatch):
    value = receipt_data("uncertain", "unknown", old=True)
    calls = []
    def request(self, method, path, **kwargs):
        calls.append((method, path))
        return 200, {"success": True, "data": value}
    monkeypatch.setattr(remote.CrsHttpClient, "_request_json", request)
    assert managed.operation("request-1") == value
    assert calls == [("GET", PREFIX + "/reset-credits/operations/request-1")]


def test_precheck_failure_receipt_remains_uncertain_and_readable(managed, monkeypatch):
    value = receipt_data("uncertain", "precheck_failed", old=True)
    value["before"] = value["after"] = None
    monkeypatch.setattr(remote.CrsHttpClient, "_request_json", lambda *a, **k: (200, {"success": True, "data": value}))
    assert managed.operation("request-1") == value
