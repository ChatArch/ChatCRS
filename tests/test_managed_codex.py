"""Managed CRS contract: synthetic profiles/HTTP only, never upstream OAuth."""
from __future__ import annotations

import importlib
from http.client import IncompleteRead
from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest
from chatenv import EnvStore, get_paths

from chatcrs import remote
from chatcrs.config import ChatcrsConfig


ACCOUNT = "crs-account-1"
BASE = "https://crs.example.test"
PREFIX = f"/admin/openai-accounts/{ACCOUNT}/codex"
CANARY = "unstructured-private-canary"


def api():
    # Import inside tests so the initial RED is a failure, not a collection error.
    return importlib.import_module("chatcrs.managed_codex")


def checked_at(seconds=0):
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


def usage_data():
    return {
        "account_id": ACCOUNT, "checked_at": checked_at(), "source": "upstream",
        "rate_limit": {
            "primary_window": {"used_percent": 85, "limit_window_seconds": 18000, "reset_at": 2000000000},
            "secondary_window": {"used_percent": 50, "limit_window_seconds": 604800, "reset_at": 2000000000},
        },
    }


def credits_data():
    return {
        "account_id": ACCOUNT, "checked_at": checked_at(), "source": "upstream",
        "available_count": 1,
        "credits": [{"id": "credit-1", "status": "available", "expires_at": "2030-01-01T00:00:00Z"}],
    }


def save_profile(home, name="work", *, base=BASE, credentials=True):
    values = {"CRS_API_BASE": base}
    if credentials:
        values.update(CRS_USERNAME="fixture-admin", CRS_PASSWORD="fixture-password")
    EnvStore(get_paths(home).envs_dir).save_profile(ChatcrsConfig, name, values)


@pytest.fixture(autouse=True)
def isolated_profiles(tmp_path, monkeypatch):
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path))
    for name in ("CRS_API_BASE", "CRS_API_KEY", "CRS_USERNAME", "CRS_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    save_profile(tmp_path)
    # An explicitly established synthetic Admin session; managed calls cannot login.
    remote.CrsTokenStore(
        profile_name="work", profile=remote.load_crs_profile("work", home=tmp_path, allow_env=False), home=tmp_path,
    ).save_login_token("fixture-admin-session", expires_in=3600)


def client(home, **kwargs):
    return api().CrsManagedCodexClient.from_profile("work", account_id=ACCOUNT, home=home, **kwargs)


def respond(monkeypatch, data, *, status=200):
    calls = []

    def request(self, method, path, *, payload=None, headers=None):
        calls.append((method, path, payload, headers))
        assert path != "/web/auth/login", "Managed requests must not log in"
        return status, {"success": True, "data": deepcopy(data)}

    monkeypatch.setattr(remote.CrsHttpClient, "_request_json", request)
    return calls


@pytest.mark.parametrize("method,data,path", [
    ("usage", usage_data, "/usage"), ("reset_credits", credits_data, "/reset-credits"),
])
def test_reads_exact_crs_route_and_returns_data_using_admin_session(tmp_path, monkeypatch, method, data, path):
    expected = data()
    calls = respond(monkeypatch, expected)
    managed = client(tmp_path, timeout=7)
    assert getattr(managed, method)() == expected
    assert [(call[0], call[1]) for call in calls] == [
        ("GET", PREFIX + path),
    ]
    assert calls[-1][3] == {"authorization": "Bearer fixture-admin-session"}
    assert managed.token_service == "CRS"
    assert managed.identity == BASE + "#account=" + ACCOUNT
    assert CANARY not in repr(managed)


def test_identity_is_origin_account_not_profile_or_secret(tmp_path, monkeypatch):
    save_profile(tmp_path, "other", base="https://CRS.EXAMPLE.TEST:443/")
    one = client(tmp_path)
    two = api().CrsManagedCodexClient.from_profile("other", account_id=ACCOUNT, home=tmp_path)
    assert one.identity == two.identity
    assert "fixture" not in repr(one)
    with pytest.raises(AttributeError):
        one.identity = "changed"


@pytest.mark.parametrize("account", ["", "../other", "a/b", "a?b", "a#b", "a%2fb", "a\\b", "a\nb", " a", "a" * 129, None])
def test_account_rejected_before_profile_or_auth(tmp_path, monkeypatch, account):
    monkeypatch.setattr(remote, "load_crs_profile", lambda *a, **k: pytest.fail("profile read before validation"))
    with pytest.raises(api().ManagedCodexError) as exc:
        api().CrsManagedCodexClient.from_profile("work", account_id=account, home=tmp_path)
    assert exc.value.code == "invalid_account_id"


@pytest.mark.parametrize("base", ["", "ftp://host", "http://remote.example.test", "https://u:p@host", "https://host/path", "https://host?key=x", "https://host#x", "https://host\\evil", "https://host\nevil", "https://host:bad", "https://", "//host"])
def test_base_rejected_before_token_read_or_login(tmp_path, monkeypatch, base):
    save_profile(tmp_path, base=base)
    monkeypatch.setattr(remote.CrsTokenStore, "load_token", lambda self: pytest.fail("token read"))
    monkeypatch.setattr(remote.CrsHttpClient, "login", lambda *a, **k: pytest.fail("login"))
    with pytest.raises(api().ManagedCodexError) as exc:
        client(tmp_path)
    assert exc.value.code == "invalid_base_url"


def test_named_profile_never_borrows_ambient_credentials(tmp_path, monkeypatch):
    save_profile(tmp_path, "empty", credentials=False)
    for key in ("CRS_USERNAME", "CRS_PASSWORD", "CRS_API_KEY"):
        monkeypatch.setenv(key, CANARY)
    calls = respond(monkeypatch, usage_data())
    with pytest.raises(api().ManagedCodexError):
        api().CrsManagedCodexClient.from_profile("empty", account_id=ACCOUNT, home=tmp_path).usage()
    assert calls == []


def test_named_profile_never_borrows_ambient_base(tmp_path, monkeypatch):
    save_profile(tmp_path, base="")
    monkeypatch.setenv("CRS_API_BASE", BASE)
    with pytest.raises(api().ManagedCodexError) as exc:
        client(tmp_path)
    assert exc.value.code == "invalid_base_url"


def test_only_crs_profile_and_token_service_are_read(tmp_path, monkeypatch):
    from chatenv import TokenStore

    profile_read, token_read = EnvStore.load_profile, TokenStore.read
    seen = []

    def load(store, config, name):
        assert config is ChatcrsConfig
        seen.append(("profile", name))
        return profile_read(store, config, name)

    def read(store, service, profile):
        assert service == "CRS"
        seen.append(("token", profile))
        return token_read(store, service, profile)

    monkeypatch.setattr(EnvStore, "load_profile", load)
    monkeypatch.setattr(TokenStore, "read", read)
    respond(monkeypatch, usage_data())
    client(tmp_path).usage()
    assert ("profile", "work") in seen
    assert ("token", "work") in seen
    assert {name for _, name in seen} == {"work"}


@pytest.mark.parametrize("field,value", [
    ("account_id", "other-account"), ("source", "cache"), ("source", None),
    ("checked_at", "not-a-date"), ("checked_at", "2001-01-01T00:00:00Z"),
    ("checked_at", "2039-01-01T00:00:00Z"), ("checked_at", "2026-01-01"),
    ("rate_limit", {}), ("rate_limit", None),
])
def test_usage_rejects_wrong_account_stale_or_malformed(tmp_path, monkeypatch, field, value):
    data = usage_data()
    data[field] = value
    respond(monkeypatch, data)
    with pytest.raises(api().ManagedCodexError) as exc:
        client(tmp_path).usage()
    assert exc.value.code in {"invalid_response", "stale_response", "account_mismatch"}


@pytest.mark.parametrize("field,value", [
    ("used_percent", True), ("used_percent", -1), ("used_percent", 101), ("used_percent", float("nan")),
    ("limit_window_seconds", 0), ("limit_window_seconds", "18000"),
    ("reset_at", -1), ("reset_at", float("inf")),
])
def test_usage_rejects_bad_window_numbers(tmp_path, monkeypatch, field, value):
    data = usage_data()
    data["rate_limit"]["primary_window"][field] = value
    respond(monkeypatch, data)
    with pytest.raises(api().ManagedCodexError):
        client(tmp_path).usage()


@pytest.mark.parametrize("field,value", [
    ("available_count", True), ("available_count", -1), ("available_count", 1.5),
    ("credits", [None]), ("credits", [{"id": "credit-1", "status": "available"}]),
    ("credits", [{"id": "../credit", "status": "available", "expires_at": None}]),
])
def test_credit_shape_is_validated(tmp_path, monkeypatch, field, value):
    data = credits_data()
    data[field] = value
    respond(monkeypatch, data)
    with pytest.raises(api().ManagedCodexError):
        client(tmp_path).reset_credits()


def test_success_output_is_whitelisted_not_only_key_redacted(tmp_path, monkeypatch):
    data = usage_data()
    expected = deepcopy(data)
    data.update(message=CANARY, email=CANARY, access_token=CANARY)
    data["rate_limit"]["primary_window"]["debug"] = CANARY
    respond(monkeypatch, data)
    assert client(tmp_path).usage() == expected


@pytest.mark.parametrize("profile", ["../work", "/work", "work/other", " work", "work.env", "", "a" * 129])
def test_invalid_profile_is_safe_and_fails_before_load(tmp_path, monkeypatch, profile):
    monkeypatch.setattr(remote, "load_crs_profile", lambda *a, **k: pytest.fail("unexpected profile IO"))
    with pytest.raises(api().ManagedCodexError) as exc:
        api().CrsManagedCodexClient.from_profile(profile, account_id=ACCOUNT, home=tmp_path)
    assert exc.value.code == "invalid_profile"


def receipt_data(status="reset_verified", code="reset", *, old=False):
    usage, credits = usage_data(), credits_data()
    if old:
        usage["checked_at"] = credits["checked_at"] = "2001-01-01T00:00:00Z"
    return {
        "account_id": ACCOUNT, "request_id": "request-1", "status": status, "code": code,
        "windows_reset": 1 if status == "reset_verified" else 0,
        "before": {"usage": usage, "credits": credits},
        "after": {"usage": deepcopy(usage), "credits": deepcopy(credits)},
    }


def test_dry_run_does_not_resolve_tokens_or_contact_crs(tmp_path, monkeypatch):
    monkeypatch.setattr(remote.CrsTokenStore, "load_token", lambda self: pytest.fail("token read"))
    monkeypatch.setattr(remote.CrsHttpClient, "_request_json", lambda *a, **k: pytest.fail("network"))
    result = client(tmp_path).consume("request-1", credit_id="credit-1")
    assert result == {
        "account_id": ACCOUNT, "request_id": "request-1", "credit_id": "credit-1",
        "status": "dry_run", "code": "dry_run", "mutated": False,
    }


@pytest.mark.parametrize("request_id", ["", "../other", "a/b", "a%2fb", "a?b", "a\\b", " a", "a" * 129, None])
@pytest.mark.parametrize("method", ["consume", "operation"])
def test_request_id_rejected_before_auth_or_network(tmp_path, monkeypatch, request_id, method):
    monkeypatch.setattr(remote.CrsTokenStore, "load_token", lambda self: pytest.fail("token read"))
    with pytest.raises(api().ManagedCodexError) as exc:
        getattr(client(tmp_path), method)(request_id)
    assert exc.value.code == "invalid_request_id"


@pytest.mark.parametrize("credit", ["", "../credit", "a" * 129])
def test_credit_id_rejected_even_for_dry_run(tmp_path, monkeypatch, credit):
    monkeypatch.setattr(remote.CrsTokenStore, "load_token", lambda self: pytest.fail("token read"))
    with pytest.raises(api().ManagedCodexError) as exc:
        client(tmp_path).consume("request-1", credit_id=credit)
    assert exc.value.code == "invalid_credit_id"


@pytest.mark.parametrize("execute", [1, "true", None])
def test_execute_requires_literal_boolean(tmp_path, monkeypatch, execute):
    monkeypatch.setattr(remote.CrsTokenStore, "load_token", lambda self: pytest.fail("token read"))
    with pytest.raises(api().ManagedCodexError) as exc:
        client(tmp_path).consume("request-1", execute=execute)
    assert exc.value.code == "invalid_execute"


@pytest.mark.parametrize("state,code,http_status", [
    ("reset_verified", "reset", 200), ("nothing_to_reset", "nothing_to_reset", 200),
    ("no_credit", "no_credit", 200), ("uncertain", "unknown", 202),
])
def test_consumption_preserves_receipt_outcome_without_followup_requests(tmp_path, monkeypatch, state, code, http_status):
    data = receipt_data(state, code)
    calls = respond(monkeypatch, data, status=http_status)
    result = client(tmp_path).consume("request-1", credit_id="credit-1", execute=True)
    assert result == data
    assert [(m, p) for m, p, _, _ in calls] == [("POST", PREFIX + "/reset-credits/consume")]
    assert calls[-1][2] == {"execute": True, "request_id": "request-1", "credit_id": "credit-1"}


def test_consume_without_credit_does_not_send_null_field(tmp_path, monkeypatch):
    calls = respond(monkeypatch, receipt_data())
    client(tmp_path).consume("request-1", execute=True)
    assert calls[-1][2] == {"execute": True, "request_id": "request-1"}


def test_consume_401_never_logs_in_again_or_replays(tmp_path, monkeypatch):
    calls = respond(monkeypatch, {"message": CANARY}, status=401)
    with pytest.raises(api().ManagedCodexError) as exc:
        client(tmp_path).consume("request-1", execute=True)
    assert exc.value.code == "unauthorized"
    assert [(m, p) for m, p, _, _ in calls] == [("POST", PREFIX + "/reset-credits/consume")]
    assert CANARY not in str(exc.value)


def test_admin_request_opt_out_preserves_legacy_default_retry(tmp_path, monkeypatch):
    calls = []

    def request(self, method, path, **kwargs):
        calls.append(path)
        if path == "/web/auth/login":
            return 200, {"token": "fixture-new", "expiresIn": 60}
        return 401, {}

    monkeypatch.setattr(remote.CrsHttpClient, "_request_json", request)
    profile = remote.CrsProfile(BASE, username="fixture", password="fixture", admin_token="fixture-old")
    http = remote.CrsHttpClient(profile, home=tmp_path, explicit_admin_token=True)
    assert http.admin_request("POST", "/write", retry_auth=False)[0] == 401
    assert calls == ["/write"]
    calls.clear()
    assert http.admin_request("GET", "/read")[0] == 401
    assert calls == ["/read", "/web/auth/login", "/read"]


@pytest.mark.parametrize("state,code,http_status", [("reset_verified", "reset", 200), ("uncertain", "unknown", 202)])
def test_operation_reads_old_receipt_without_fresh_usage_or_credit_reads(tmp_path, monkeypatch, state, code, http_status):
    data = receipt_data(state, code, old=True)
    calls = respond(monkeypatch, data, status=http_status)
    assert client(tmp_path).operation("request-1") == data
    assert [(m, p) for m, p, _, _ in calls] == [("GET", PREFIX + "/reset-credits/operations/request-1")]


@pytest.mark.parametrize("field,value", [
    ("account_id", "wrong"), ("request_id", "wrong"), ("status", "completed"),
    ("code", "unknown"), ("windows_reset", 0), ("windows_reset", True), ("before", None), ("after", []),
])
def test_malformed_successful_receipt_is_not_accepted(tmp_path, monkeypatch, field, value):
    data = receipt_data()
    data[field] = value
    respond(monkeypatch, data)
    with pytest.raises(api().ManagedCodexError):
        client(tmp_path).consume("request-1", execute=True)


def test_http_202_cannot_claim_verified_consumption(tmp_path, monkeypatch):
    respond(monkeypatch, receipt_data(), status=202)
    with pytest.raises(api().ManagedCodexError):
        client(tmp_path).consume("request-1", execute=True)


def test_uncertain_receipt_allows_missing_readback_but_does_not_invent_it(tmp_path, monkeypatch):
    data = receipt_data("uncertain", "unknown")
    data["before"] = data["after"] = None
    respond(monkeypatch, data, status=202)
    assert client(tmp_path).consume("request-1", execute=True) == data


def test_receipt_audit_is_safe_and_pins_nested_account(tmp_path, monkeypatch):
    data = receipt_data()
    expected = deepcopy(data)
    data["before"]["debug"] = CANARY
    data["after"]["usage"]["authorization"] = CANARY
    data["after"]["credits"]["credits"][0]["note"] = CANARY
    respond(monkeypatch, data)
    assert client(tmp_path).operation("request-1") == expected
    data["after"]["usage"]["account_id"] = "other-account"
    respond(monkeypatch, data)
    with pytest.raises(api().ManagedCodexError):
        client(tmp_path).operation("request-1")


@pytest.mark.parametrize("status,code", [(401, "unauthorized"), (403, "forbidden"), (404, "not_found"), (409, "conflict"), (502, "upstream_error"), (504, "upstream_error"), (307, "http_error")])
def test_http_errors_have_fixed_safe_codes(tmp_path, monkeypatch, status, code):
    def request(self, method, path, **kwargs):
        if path == "/web/auth/login":
            return 200, {"token": "fixture", "expiresIn": 60}
        return status, {"success": False, "error": {"code": CANARY}, "message": CANARY}

    monkeypatch.setattr(remote.CrsHttpClient, "_request_json", request)
    with pytest.raises(api().ManagedCodexError) as exc:
        client(tmp_path).usage()
    assert exc.value.code == code
    assert CANARY not in str(exc.value)
    assert not hasattr(exc.value, "body")


@pytest.mark.parametrize("envelope", [{}, [], {"success": False, "message": CANARY}, {"success": 1, "data": {}}, {"success": True, "data": []}])
def test_non_contract_200_never_counts_as_success(tmp_path, monkeypatch, envelope):
    monkeypatch.setattr(remote.CrsHttpClient, "admin_request", lambda *a, **k: (200, envelope))
    with pytest.raises(api().ManagedCodexError) as exc:
        client(tmp_path).usage()
    assert exc.value.code == "invalid_response"
    assert CANARY not in str(exc.value)


@pytest.mark.parametrize("failure", [TimeoutError(CANARY), OSError(CANARY), ValueError(CANARY), IncompleteRead(CANARY.encode()), remote.CrsApiError(CANARY, body={"message": CANARY})])
def test_consume_network_or_decode_failure_is_not_retried(tmp_path, monkeypatch, failure):
    calls = []

    def request(self, method, path, **kwargs):
        calls.append(path)
        if path == "/web/auth/login":
            return 200, {"token": "fixture", "expiresIn": 60}
        raise failure

    monkeypatch.setattr(remote.CrsHttpClient, "_request_json", request)
    with pytest.raises(api().ManagedCodexError) as exc:
        client(tmp_path).consume("request-1", execute=True)
    assert exc.value.code == "outcome_unknown"
    assert CANARY not in str(exc.value)
    assert exc.value.__context__ is None
    assert calls == [PREFIX + "/reset-credits/consume"]


@pytest.mark.parametrize("missing", [True, False])
@pytest.mark.parametrize("name", ["primary_window", "secondary_window"])
def test_single_weekly_window_is_valid_in_either_slot(tmp_path, monkeypatch, missing, name):
    data = usage_data()
    other = "secondary_window" if name == "primary_window" else "primary_window"
    data["rate_limit"][name]["limit_window_seconds"] = 604800
    if missing:
        del data["rate_limit"][other]
    else:
        data["rate_limit"][other] = None
    respond(monkeypatch, data)
    assert client(tmp_path).usage() == data


@pytest.mark.parametrize("windows", [{}, {"primary_window": None}, {"primary_window": None, "secondary_window": None}, {"primary_window": {}}, {"unknown_window": {"used_percent": 0}}])
def test_missing_or_empty_windows_fail_closed(tmp_path, monkeypatch, windows):
    data = usage_data()
    data["rate_limit"] = windows
    respond(monkeypatch, data)
    with pytest.raises(api().ManagedCodexError) as exc:
        client(tmp_path).usage()
    assert exc.value.code == "invalid_response"


@pytest.mark.parametrize("field", ["used_percent", "limit_window_seconds", "reset_at"])
def test_unknown_alias_cannot_replace_required_window_field(tmp_path, monkeypatch, field):
    data = usage_data()
    window = data["rate_limit"]["primary_window"]
    window["unknown_" + field] = window.pop(field)
    respond(monkeypatch, data)
    with pytest.raises(api().ManagedCodexError) as exc:
        client(tmp_path).usage()
    assert exc.value.code == "invalid_response"


@pytest.mark.parametrize("timeout", [True, False, float("nan"), float("inf"), 0, -1, "20", None, 10**1000])
@pytest.mark.parametrize("direct", [False, True])
def test_bad_timeout_rejected_at_construction_before_io(tmp_path, monkeypatch, timeout, direct):
    monkeypatch.setattr(remote, "load_crs_profile", lambda *a, **k: pytest.fail("profile IO"))
    monkeypatch.setattr(remote.CrsTokenStore, "load_token", lambda *a: pytest.fail("token IO"))
    with pytest.raises(api().ManagedCodexError) as exc:
        if direct:
            api().CrsManagedCodexClient(remote.CrsProfile(BASE), account_id=ACCOUNT, profile_name="work", timeout=timeout)
        else:
            client(tmp_path, timeout=timeout)
    assert exc.value.code == "invalid_timeout"


@pytest.mark.parametrize("state,code,http_status", [
    ("no_credit", "no_credit", 200), ("uncertain", "pending", 202),
    ("uncertain", "readback_failed", 202), ("uncertain", "storage_unavailable", 202),
])
def test_node_receipts_allow_null_snapshots_and_safe_update_flags(tmp_path, monkeypatch, state, code, http_status):
    data = receipt_data(state, code)
    data.update(before=None, after=None, cache_updated=False, scheduling_updated=False)
    respond(monkeypatch, data, status=http_status)
    assert client(tmp_path).consume("request-1", execute=True) == data


@pytest.mark.parametrize("field,value", [
    ("status", CANARY), ("code", CANARY), ("status", []), ("code", {}),
    ("cache_updated", CANARY), ("scheduling_updated", 1),
])
def test_receipt_critical_fields_are_strictly_allowlisted(tmp_path, monkeypatch, field, value):
    data = receipt_data()
    data[field] = value
    respond(monkeypatch, data)
    with pytest.raises(api().ManagedCodexError) as exc:
        client(tmp_path).operation("request-1")
    assert exc.value.code == "invalid_response"
    assert CANARY not in str(exc.value)


def test_consumption_json_decoder_fallback_is_unknown_without_replay(tmp_path, monkeypatch):
    from io import BytesIO
    calls = []
    remote.CrsTokenStore(profile_name="work", profile=remote.CrsProfile(BASE), home=tmp_path).save_login_token(
        "fixture-cached", expires_in=3600,
    )

    def open_request(request, *, timeout):
        calls.append(request.full_url)
        response = BytesIO(CANARY.encode())
        response.status = 200
        return response

    monkeypatch.setattr(remote, "open_request", open_request)
    with pytest.raises(api().ManagedCodexError) as exc:
        client(tmp_path).consume("request-1", execute=True)
    assert exc.value.code == "outcome_unknown"
    assert CANARY not in str(exc.value)
    assert calls == [BASE + PREFIX + "/reset-credits/consume"]
