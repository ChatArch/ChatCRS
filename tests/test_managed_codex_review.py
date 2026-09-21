"""Independent-review regressions; only synthetic sessions and HTTP payloads."""
from copy import deepcopy

import pytest

from chatcrs import remote
from chatcrs.managed_codex import CrsManagedCodexClient, ManagedCodexError
from test_managed_codex import ACCOUNT, BASE, usage_data, credits_data, receipt_data

CANARY = "RAW_UPSTREAM_CANARYT"


def operator(tmp_path, *, session=True):
    profile = remote.CrsProfile(
        BASE, username="synthetic-admin", password="synthetic-password",
        admin_token="synthetic-session" if session else "",
    )
    return CrsManagedCodexClient(profile, account_id=ACCOUNT, profile_name="review", home=tmp_path)


def invoke(client, operation):
    if operation == "consume":
        return client.consume("request-1", execute=True)
    if operation == "operation":
        return client.operation("request-1")
    return getattr(client, operation)()


@pytest.mark.parametrize("operation,field", [
    ("usage", "checked_at"),
    ("reset_credits", "checked_at"),
    ("reset_credits", "expires_at"),
    ("operation", "before_usage"),
    ("operation", "after_usage"),
    ("operation", "before_expiry"),
    ("operation", "after_expiry"),
])
def test_invalid_upstream_dates_leave_no_exception_context(tmp_path, monkeypatch, operation, field):
    if operation == "usage":
        data = usage_data()
        data[field] = CANARY
    elif operation == "reset_credits":
        data = credits_data()
        if field == "expires_at":
            data["credits"][0][field] = CANARY
        else:
            data[field] = CANARY
    else:
        data = receipt_data(old=True)
        side, kind = field.split("_")
        if kind == "usage":
            data[side]["usage"]["checked_at"] = CANARY
        else:
            data[side]["credits"]["credits"][0]["expires_at"] = CANARY
    monkeypatch.setattr(remote.CrsHttpClient, "_request_json", lambda *a, **k: (200, {"success": True, "data": deepcopy(data)}))
    with pytest.raises(ManagedCodexError) as caught:
        invoke(operator(tmp_path), operation)
    assert caught.value.code == "invalid_response"
    assert CANARY not in str(caught.value)
    assert caught.value.__context__ is None
    assert caught.value.__cause__ is None


@pytest.mark.parametrize("operation", ["usage", "reset_credits", "operation", "consume"])
def test_operator_without_session_does_not_login_or_send(tmp_path, monkeypatch, operation):
    calls = []
    def login(*args, **kwargs):
        calls.append("login")
        raise ValueError("synthetic login was unexpectedly requested")
    def request(*args, **kwargs):
        calls.append("request")
        return 401, {}
    monkeypatch.setattr(remote.CrsHttpClient, "login", login)
    monkeypatch.setattr(remote.CrsHttpClient, "_request_json", request)
    with pytest.raises(ManagedCodexError) as caught:
        invoke(operator(tmp_path, session=False), operation)
    assert calls == []
    assert caught.value.code == "admin_session_required"


@pytest.mark.parametrize("operation", ["usage", "reset_credits", "operation", "consume"])
def test_operator_rejected_session_never_logs_in_or_replays(tmp_path, monkeypatch, operation):
    calls = []
    def login(self, **kwargs):
        calls.append("login")
        self._admin_token = "synthetic-renewed"
        return {}
    def request(self, method, path, **kwargs):
        calls.append((method, path))
        return 401, {"message": CANARY}
    monkeypatch.setattr(remote.CrsHttpClient, "login", login)
    monkeypatch.setattr(remote.CrsHttpClient, "_request_json", request)
    with pytest.raises(ManagedCodexError) as caught:
        invoke(operator(tmp_path), operation)
    assert len(calls) == 1
    assert calls[0] != "login"
    assert caught.value.code == "unauthorized"
    assert caught.value.__context__ is None
