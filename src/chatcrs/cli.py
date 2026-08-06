"""CLI entrypoint for chatcrs."""

from __future__ import annotations

import json

import click

import chatcrs.local as local_management
import chatcrs.remote as remote_management
from chatcrs import __version__


def _echo_json(payload: dict) -> None:
    click.echo(json.dumps(payload, ensure_ascii=False, indent=2))


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="chatcrs")
def main() -> None:
    """HTTP-first CRS management helpers for ChatArch."""


@main.command(name="health")
@click.option("--base-url", default=None, help="CRS base URL. Defaults to CRS_API_BASE or local CRS default.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def health_command(base_url: str | None, json_output: bool) -> None:
    """Verify the CRS /health endpoint."""

    try:
        payload = local_management.health_check(base_url)
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        click.echo(f"ok={payload['ok']} base_url={payload['base_url']} status={payload['health']['status']}")


def _remote_client(
    *,
    profile: str,
    base_url: str | None,
    api_key: str | None,
    username: str | None,
    password: str | None,
    admin_token: str | None,
    timeout: float,
) -> remote_management.CrsHttpClient:
    return remote_management.client_from_options(
        profile=profile,
        base_url=base_url,
        api_key=api_key,
        username=username,
        password=password,
        admin_token=admin_token,
        timeout=timeout,
    )


def _common_remote_options(function):
    function = click.option("--timeout", type=float, default=20.0, show_default=True)(function)
    function = click.option("--admin-token", default=None, help="Admin bearer token. Prefer the CRS ChatEnv profile for real use.")(function)
    function = click.option("--password", default=None, help="Admin password. Prefer the CRS ChatEnv profile for real use.")(function)
    function = click.option("--username", default=None, help="Admin username. Prefer the CRS ChatEnv profile for real use.")(function)
    function = click.option("--api-key", default=None, help="CRS API key for non-admin endpoints. Prefer the CRS ChatEnv profile.")(function)
    function = click.option("--base-url", default=None, help="Remote CRS base URL. Defaults to CRS_API_BASE in the CRS ChatEnv profile.")(function)
    function = click.option("--profile", default="admin", show_default=True, help="CRS ChatEnv profile under envs/CRS/<profile>.env.")(function)
    return function


def _api_key_remote_options(function):
    function = click.option("--timeout", type=float, default=20.0, show_default=True)(function)
    function = click.option("--api-key", default=None, help="CRS API key. Defaults to CRS_API_KEY in the CRS ChatEnv profile.")(function)
    function = click.option("--base-url", default=None, help="Remote CRS base URL. Defaults to CRS_API_BASE in the CRS ChatEnv profile.")(function)
    function = click.option("--profile", default="admin", show_default=True, help="CRS ChatEnv profile under envs/CRS/<profile>.env.")(function)
    return function


@main.group(name="admin")
def admin_group() -> None:
    """Remote CRS administrator operations via HTTPS Admin API."""


@admin_group.command(name="login")
@_common_remote_options
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def admin_login_command(
    profile: str,
    base_url: str | None,
    api_key: str | None,
    username: str | None,
    password: str | None,
    admin_token: str | None,
    timeout: float,
    json_output: bool,
) -> None:
    """Verify CRS admin login without printing the session token."""

    try:
        client = _remote_client(
            profile=profile,
            base_url=base_url,
            api_key=api_key,
            username=username,
            password=password,
            admin_token=admin_token,
            timeout=timeout,
        )
        payload = client.login()
    except (OSError, ValueError, remote_management.CrsApiError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        click.echo(f"ok={payload['ok']} status={payload['status']} token_present={payload['token_present']}")


@admin_group.group(name="accounts")
def admin_accounts_group() -> None:
    """Inspect or refresh remote CRS account state via HTTP Admin API."""


@admin_accounts_group.command(name="usage")
@_common_remote_options
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def admin_accounts_usage_command(
    profile: str,
    base_url: str | None,
    api_key: str | None,
    username: str | None,
    password: str | None,
    admin_token: str | None,
    timeout: float,
    json_output: bool,
) -> None:
    """List OpenAI/Codex account usage and scheduling metadata."""

    try:
        payload = _remote_client(
            profile=profile,
            base_url=base_url,
            api_key=api_key,
            username=username,
            password=password,
            admin_token=admin_token,
            timeout=timeout,
        ).accounts_usage()
    except (OSError, ValueError, remote_management.CrsApiError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        click.echo(f"ok={payload['ok']} accounts={payload['count']} mutated={payload['mutated']}")


@admin_accounts_group.command(name="refresh-status")
@_common_remote_options
@click.argument("account_id")
@click.option("--execute", is_flag=True, default=False, help="Actually call CRS reset-status. Without it, print a dry-run plan.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def admin_accounts_refresh_status_command(
    profile: str,
    base_url: str | None,
    api_key: str | None,
    username: str | None,
    password: str | None,
    admin_token: str | None,
    timeout: float,
    account_id: str,
    execute: bool,
    json_output: bool,
) -> None:
    """Reset a CRS OpenAI account status after transient failures."""

    if not execute:
        payload = {
            "ok": True,
            "mutated": False,
            "would_call": f"POST /admin/openai-accounts/{account_id}/reset-status",
            "account_id": account_id,
        }
    else:
        try:
            payload = _remote_client(
                profile=profile,
                base_url=base_url,
                api_key=api_key,
                username=username,
                password=password,
                admin_token=admin_token,
                timeout=timeout,
            ).reset_openai_account_status(account_id)
        except (OSError, ValueError, remote_management.CrsApiError) as exc:
            raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        click.echo(f"ok={payload['ok']} account_id={account_id} mutated={payload['mutated']}")


@admin_group.group(name="keys")
def admin_keys_group() -> None:
    """Inspect remote CRS API keys with admin privileges."""


@admin_keys_group.command(name="list")
@_common_remote_options
@click.option("--include-stats", is_flag=True, default=False, help="Fetch batch usage and last-account attribution for each key.")
@click.option("--time-range", default="all", show_default=True, type=click.Choice(["today", "7days", "30days", "all"]))
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def admin_keys_list_command(
    profile: str,
    base_url: str | None,
    api_key: str | None,
    username: str | None,
    password: str | None,
    admin_token: str | None,
    timeout: float,
    include_stats: bool,
    time_range: str,
    json_output: bool,
) -> None:
    """List CRS API key metadata, optionally including usage stats."""

    try:
        payload = _remote_client(
            profile=profile,
            base_url=base_url,
            api_key=api_key,
            username=username,
            password=password,
            admin_token=admin_token,
            timeout=timeout,
        ).api_keys(include_stats=include_stats, time_range=time_range)
    except (OSError, ValueError, remote_management.CrsApiError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        click.echo(f"ok={payload['ok']} keys={payload['count']} mutated={payload['mutated']}")


@admin_keys_group.command(name="show")
@_common_remote_options
@click.argument("key_id")
@click.option("--include-stats/--no-include-stats", default=True, show_default=True)
@click.option("--time-range", default="all", show_default=True, type=click.Choice(["today", "7days", "30days", "all"]))
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def admin_keys_show_command(
    profile: str,
    base_url: str | None,
    api_key: str | None,
    username: str | None,
    password: str | None,
    admin_token: str | None,
    timeout: float,
    key_id: str,
    include_stats: bool,
    time_range: str,
    json_output: bool,
) -> None:
    """Show one CRS API key by id or name."""

    try:
        payload = _remote_client(
            profile=profile,
            base_url=base_url,
            api_key=api_key,
            username=username,
            password=password,
            admin_token=admin_token,
            timeout=timeout,
        ).api_key_detail(key_id, include_stats=include_stats, time_range=time_range)
    except (OSError, ValueError, remote_management.CrsApiError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        click.echo(f"ok={payload['ok']} query={key_id} mutated={payload['mutated']}")


@main.group(name="key")
def key_group() -> None:
    """CRS API-key-only operations that do not require admin login."""


@key_group.command(name="info")
@_api_key_remote_options
@click.option("--path", "info_path", default="/openai/key-info", show_default=True, help="CRS key-info endpoint path.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def key_info_command(
    profile: str,
    base_url: str | None,
    api_key: str | None,
    timeout: float,
    info_path: str,
    json_output: bool,
) -> None:
    """Query CRS key-info using only a CRS API key."""

    try:
        payload = _remote_client(
            profile=profile,
            base_url=base_url,
            api_key=api_key,
            username=None,
            password=None,
            admin_token=None,
            timeout=timeout,
        ).key_info(path=info_path)
    except (OSError, ValueError, remote_management.CrsApiError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        click.echo(f"ok={payload['ok']} status={payload['status']} mutated={payload['mutated']}")


if __name__ == "__main__":
    main()
