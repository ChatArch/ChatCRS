"""CLI entrypoint for chatcrs."""

from __future__ import annotations

import json
from pathlib import Path

import click

import chatcrs.local as local_management
import chatcrs.remote as remote_management
import chatcrs.service as service_management
from chatcrs import __version__
from chatcrs.inspect import inspect_crs_layout


def _echo_json(payload: dict) -> None:
    click.echo(json.dumps(payload, ensure_ascii=False, indent=2))



@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="chatcrs")
def main() -> None:
    """CRS management helpers for ChatArch."""


@main.command(name="health")
@click.option("--base-url", default=None, help="CRS base URL. Defaults to CHATCRS_BASE_URL or local CRS default.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def health_command(base_url: str | None, json_output: bool) -> None:
    """Verify the CRS /health endpoint."""

    payload = local_management.health_check(base_url)
    if json_output:
        _echo_json(payload)
    else:
        click.echo(f"ok={payload['ok']} base_url={payload['base_url']} status={payload['health']['status']}")


@main.command(name="inspect")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def inspect_command(json_output: bool) -> None:
    """Inspect known CRS services without mutating them."""

    payload = inspect_crs_layout()
    if json_output:
        _echo_json(payload)
    else:
        click.echo(f"old={payload['old']['health'].get('status')} new={payload['new']['health'].get('status')} mutated={payload['mutated']}")



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
    function = click.option("--admin-token", default=None, help="Admin bearer token. Prefer ChatEnv profile for real use.")(function)
    function = click.option("--password", default=None, help="Admin password. Prefer ChatEnv profile for real use.")(function)
    function = click.option("--username", default=None, help="Admin username. Prefer ChatEnv profile for real use.")(function)
    function = click.option("--api-key", default=None, help="CRS API key for non-admin endpoints. Prefer ChatEnv profile.")(function)
    function = click.option("--base-url", default=None, help="Remote CRS base URL. Defaults to CRS_API_BASE in ChatEnv profile.")(function)
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
    """Inspect or refresh remote CRS account state."""


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
@_common_remote_options
@click.option("--path", "info_path", default="/openai/key-info", show_default=True, help="CRS key-info endpoint path.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def key_info_command(
    profile: str,
    base_url: str | None,
    api_key: str | None,
    username: str | None,
    password: str | None,
    admin_token: str | None,
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
            username=username,
            password=password,
            admin_token=admin_token,
            timeout=timeout,
        ).key_info(path=info_path)
    except (OSError, ValueError, remote_management.CrsApiError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        click.echo(f"ok={payload['ok']} status={payload['status']} mutated={payload['mutated']}")


def _service_target(
    *,
    ssh_alias: str | None,
    app_dir: str | None,
    crs_command: str | None,
    timeout: float,
) -> service_management.ServiceTarget:
    return service_management.ServiceTarget.from_options(
        ssh_alias=ssh_alias,
        app_dir=app_dir,
        crs_command=crs_command,
        timeout=timeout,
    )


def _common_service_options(function):
    function = click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")(function)
    function = click.option(
        "--execute",
        is_flag=True,
        default=False,
        help="Actually run the official crs lifecycle command over SSH. Without it, print a guarded plan.",
    )(function)
    function = click.option("--timeout", type=float, default=120.0, show_default=True)(function)
    function = click.option(
        "--crs-command",
        default=None,
        help="Remote crs command path. Defaults to process CHATCRS_CRS_COMMAND, ChatEnv Chatcrs profile, then crs.",
    )(function)
    function = click.option(
        "--app-dir",
        default=None,
        help="Remote CRS app directory. Defaults to process CHATCRS_APP_DIR, ChatEnv Chatcrs profile, then canonical app path.",
    )(function)
    function = click.option(
        "--ssh-alias",
        default=None,
        help="SSH target alias. Defaults to process CHATCRS_SSH_ALIAS or ChatEnv Chatcrs profile.",
    )(function)
    return function


def _emit_service_payload(payload: dict, *, json_output: bool) -> None:
    if json_output:
        _echo_json(payload)
    else:
        click.echo(
            f"ok={payload['ok']} action={payload['action']} mode={payload['mode']} "
            f"mutated={payload['mutated']} command={' '.join(payload['official_crs_command'])}"
        )


@main.group(name="service")
def service_group() -> None:
    """Guarded CRS lifecycle commands; target defaults can come from ChatEnv Chatcrs profile."""


def _service_action_command(action: str, *, branch: str | None, ssh_alias: str | None, app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    target = _service_target(ssh_alias=ssh_alias, app_dir=app_dir, crs_command=crs_command, timeout=timeout)
    try:
        payload = service_management.run_service_action(action, target=target, branch=branch, execute=execute)
    except (OSError, RuntimeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    _emit_service_payload(payload, json_output=json_output)
    if execute and not payload.get("ok", False):
        raise click.ClickException(f"crs {action} failed")


@service_group.command(name="install")
@_common_service_options
def service_install_command(ssh_alias: str | None, app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    """Plan or execute official `crs install` on a remote target."""

    _service_action_command("install", branch=None, ssh_alias=ssh_alias, app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=execute, json_output=json_output)


@service_group.command(name="update")
@_common_service_options
def service_update_command(ssh_alias: str | None, app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    """Plan or execute official `crs update` on a remote target."""

    _service_action_command("update", branch=None, ssh_alias=ssh_alias, app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=execute, json_output=json_output)


@service_group.command(name="start")
@_common_service_options
def service_start_command(ssh_alias: str | None, app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    """Plan or execute official `crs start` on a remote target."""

    _service_action_command("start", branch=None, ssh_alias=ssh_alias, app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=execute, json_output=json_output)


@service_group.command(name="stop")
@_common_service_options
def service_stop_command(ssh_alias: str | None, app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    """Plan or execute official `crs stop` on a remote target."""

    _service_action_command("stop", branch=None, ssh_alias=ssh_alias, app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=execute, json_output=json_output)


@service_group.command(name="restart")
@_common_service_options
def service_restart_command(ssh_alias: str | None, app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    """Plan or execute official `crs restart` on a remote target."""

    _service_action_command("restart", branch=None, ssh_alias=ssh_alias, app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=execute, json_output=json_output)


@service_group.command(name="status")
@_common_service_options
def service_status_command(ssh_alias: str | None, app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    """Plan or execute official `crs status` on a remote target."""

    _service_action_command("status", branch=None, ssh_alias=ssh_alias, app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=execute, json_output=json_output)


@service_group.command(name="switch-branch")
@_common_service_options
@click.argument("branch")
def service_switch_branch_command(branch: str, ssh_alias: str | None, app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    """Plan or execute official `crs switch-branch <branch>` on a remote target."""

    _service_action_command("switch-branch", branch=branch, ssh_alias=ssh_alias, app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=execute, json_output=json_output)


@service_group.command(name="update-pricing")
@_common_service_options
def service_update_pricing_command(ssh_alias: str | None, app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    """Plan or execute official `crs update-pricing` on a remote target."""

    _service_action_command("update-pricing", branch=None, ssh_alias=ssh_alias, app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=execute, json_output=json_output)



if __name__ == "__main__":
    main()
