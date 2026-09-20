"""Managed CRS CLI contracts; all adapters and payloads are synthetic."""
import json

import pytest
from click.testing import CliRunner

from chatcrs.cli import main


PREFIX = ["admin", "accounts", "codex"]


@pytest.mark.parametrize("command", ["usage", "credits", "consume", "operation"])
def test_managed_commands_are_registered(command):
    result = CliRunner().invoke(main, PREFIX + [command, "--help"])
    assert result.exit_code == 0, result.output
    assert "--profile" in result.output
    assert "--account-id" in result.output
    assert "--json-output" in result.output
    assert "--admin-token" not in result.output
    assert "--access-token" not in result.output
    if command in ("consume", "operation"):
        assert "--request-id" in result.output
    if command == "consume":
        assert "--credit-id" in result.output
        assert "--execute" in result.output


@pytest.fixture
def adapter(monkeypatch):
    from chatcrs.managed_codex import CrsManagedCodexClient

    class FakeAdapter:
        identity = "https://crs.example.com#account=account-placeholder"
        token_service = "CRS"

        def __init__(self):
            self.calls = []
            self.factories = []
            self.status = "reset_verified"
            self.error = None

        def result(self, method, **kwargs):
            self.calls.append((method, kwargs))
            if self.error is not None:
                raise self.error
            return {"account_id": "account-placeholder", "status": self.status, **kwargs}

        def usage(self):
            return self.result("usage")

        def reset_credits(self):
            return self.result("reset_credits")

        def consume(self, request_id, credit_id=None, execute=False):
            result = self.result("consume", request_id=request_id, credit_id=credit_id, execute=execute)
            if not execute:
                result["status"] = "dry_run"
            return result

        def operation(self, request_id):
            return self.result("operation", request_id=request_id)

    fake = FakeAdapter()

    def from_profile(crs_profile="default", *, account_id, home=None, timeout=20):
        fake.factories.append((crs_profile, account_id, home, timeout))
        return fake

    monkeypatch.setattr(CrsManagedCodexClient, "from_profile", staticmethod(from_profile))
    return fake


def invoke(command, *args):
    return CliRunner().invoke(main, PREFIX + [command, "--account-id", "account-placeholder", *args])


@pytest.mark.parametrize("command,method", [("usage", "usage"), ("credits", "reset_credits")])
def test_reads_delegate_once_with_selected_crs_profile(adapter, command, method):
    result = invoke(command, "--profile", "selected-crs", "--timeout", "7", "--json-output")
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["account_id"] == "account-placeholder"
    assert adapter.factories == [("selected-crs", "account-placeholder", None, 7.0)]
    assert adapter.calls == [(method, {})]


def test_consume_is_local_plan_by_default(adapter):
    result = invoke("consume", "--request-id", "request-placeholder", "--json-output")
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["status"] == "dry_run"
    assert adapter.factories == [("default", "account-placeholder", None, 20.0)]
    assert adapter.calls == [("consume", {"request_id": "request-placeholder", "credit_id": None, "execute": False})]


@pytest.mark.parametrize("status", ["reset_verified", "nothing_to_reset", "no_credit", "uncertain", "pending", "unknown", "accepted", 202, "dry_run", None])
@pytest.mark.parametrize("command", ["consume", "operation"])
def test_receipts_exit_nonzero_unless_result_is_known(adapter, command, status):
    adapter.status = status
    args = ["--request-id", "request-placeholder", "--json-output"]
    if command == "consume":
        args += ["--execute", "--credit-id", "credit-placeholder"]
    result = invoke(command, *args)
    assert json.loads(result.output)["status"] == status
    assert (result.exit_code == 0) == (status in ("reset_verified", "nothing_to_reset", "no_credit"))
    expected = {"request_id": "request-placeholder"}
    if command == "consume":
        expected.update(credit_id="credit-placeholder", execute=True)
    assert adapter.calls == [(command, expected)]


@pytest.mark.parametrize("command", ["usage", "credits", "consume", "operation"])
def test_account_is_required_before_factory(adapter, command):
    result = CliRunner().invoke(main, PREFIX + [command])
    assert result.exit_code == 2
    assert "--account-id" in result.output
    assert adapter.factories == []


@pytest.mark.parametrize("command", ["consume", "operation"])
def test_request_id_is_required_before_factory(adapter, command):
    result = invoke(command)
    assert result.exit_code == 2
    assert "--request-id" in result.output
    assert adapter.factories == []


@pytest.mark.parametrize("json_output", [False, True])
@pytest.mark.parametrize("error_kind", ["managed", "unexpected", "factory"])
def test_errors_are_fixed_safe_messages(adapter, monkeypatch, json_output, error_kind):
    from chatcrs.managed_codex import CrsManagedCodexClient, ManagedCodexError

    if error_kind == "managed":
        adapter.error = ManagedCodexError("request_failed")
    elif error_kind == "unexpected":
        adapter.error = RuntimeError("RuntimeError.canary secret-body")
    else:
        def fail(*args, **kwargs):
            raise RuntimeError("RuntimeError.canary secret-profile")
        monkeypatch.setattr(CrsManagedCodexClient, "from_profile", staticmethod(fail))
    result = invoke("consume", "--request-id", "request-placeholder", "--execute", *(["--json-output"] if json_output else []))
    assert result.exit_code != 0
    assert "canary" not in result.output
    assert "secret-" not in result.output
    assert "failed" in result.output.lower()
    assert len(adapter.calls) == (0 if error_kind == "factory" else 1)
    if json_output:
        assert json.loads(result.output)["status"] == "error"


def test_human_output_shows_safe_receipt(adapter):
    result = invoke("operation", "--request-id", "request-placeholder")
    assert result.exit_code == 0, result.output
    assert "reset_verified" in result.output


def test_legacy_cached_usage_is_not_redirected(adapter, monkeypatch):
    import chatcrs.cli as cli

    class CachedClient:
        def accounts_usage(self):
            return {"ok": True, "count": 1, "mutated": False, "source": "cached"}

    monkeypatch.setattr(cli, "_remote_client", lambda **kwargs: CachedClient())
    result = CliRunner().invoke(main, ["admin", "accounts", "usage", "--json-output"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["source"] == "cached"
    assert adapter.factories == []


@pytest.mark.parametrize("path", ["README.md", "README.en.md", "docs/cli.md", "docs/cli.en.md", "docs/interfaces.md", "docs/interfaces.en.md"])
def test_managed_docs_match_tree_and_unreleased_contract(path):
    from pathlib import Path
    from chatstyle import render_click_tree

    text = (Path(__file__).resolve().parents[1] / path).read_text()
    block = text.split("```text", 1)[1].split("```", 1)[0].strip()
    assert block == render_click_tree(main, root_name="chatcrs")
    assert "Unreleased" in text and "0.3.4" in text
    for command in ("usage", "credits", "consume", "operation"):
        assert f"chatcrs admin accounts codex {command}" in text
    assert "reset_verified" in text and "nothing_to_reset" in text and "no_credit" in text
    assert "uncertain" in text and "pending" in text
