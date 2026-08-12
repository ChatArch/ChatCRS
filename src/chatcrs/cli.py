"""CLI entrypoint for chatcrs."""

from __future__ import annotations

import json
from typing import Any, cast

import click

import chatcrs.codex_direct as codex_direct
import chatcrs.local as local_management
import chatcrs.remote as remote_management
import chatcrs.service as service_management
from chatcrs import __version__


def _format_metavar(name: str) -> str:
    return name.replace("_", "-").upper()


def _format_argument(param: click.Argument) -> str:
    metavar = _format_metavar(param.name or "arg")
    if param.nargs == -1:
        value = f"<{metavar}>..."
    else:
        value = f"<{metavar}>"
    if not param.required:
        return f"[{value}]"
    return value


def _format_option(param: click.Option) -> str:
    primary = next((opt for opt in param.opts if opt.startswith("--")), param.opts[0] if param.opts else param.name)
    if param.secondary_opts:
        secondary = next((opt for opt in param.secondary_opts if opt.startswith("--")), param.secondary_opts[0])
        return f"[{primary}/{secondary}]"
    if param.is_flag or param.flag_value is not None:
        return f"[{primary}]"
    metavar = param.metavar or _format_metavar(param.name or "value")
    return f"[{primary} <{metavar}>]"


def _format_command_signature(command: click.Command) -> str:
    arguments: list[str] = []
    options: list[str] = []
    for param in command.params:
        if getattr(param, "hidden", False):
            continue
        if isinstance(param, click.Argument):
            arguments.append(_format_argument(param))
        elif isinstance(param, click.Option):
            options.append(_format_option(param))
    return " ".join(arguments + options)


def _command_purpose(command: click.Command) -> str:
    text = command.short_help or command.help or ""
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "No description.")
    return first_line.rstrip(".") + "."


def _visible_children(command: click.Command) -> list[tuple[str, click.Command]]:
    children = getattr(command, "commands", {})
    return [(name, child) for name, child in children.items() if not getattr(child, "hidden", False)]


def render_cli_tree(command: click.Command, root_name: str = "chatcrs") -> str:
    """Render the registered Click command tree."""

    lines = [f"{root_name}  # {_command_purpose(command)}"]
    synthetic = [
        ("--help", "Show this help message."),
        ("--version", "Show the installed package version."),
        ("--tree", "Print the registered command tree."),
    ]
    nodes: list[tuple[str, str | click.Command]] = [(name, purpose) for name, purpose in synthetic]
    nodes.extend((name, child) for name, child in _visible_children(command))

    def walk(items: list[tuple[str, str | click.Command]] | list[tuple[str, click.Command]], prefix: str = "") -> None:
        for index, (name, value) in enumerate(items):
            is_last = index == len(items) - 1
            branch = "└── " if is_last else "├── "
            child_prefix = prefix + ("    " if is_last else "│   ")
            if isinstance(value, str):
                lines.append(f"{prefix}{branch}{name}  # {value}")
                continue
            signature = _format_command_signature(value)
            label = f"{name} {signature}".strip()
            lines.append(f"{prefix}{branch}{label}  # {_command_purpose(value)}")
            children = _visible_children(value)
            if children:
                walk(children, child_prefix)

    walk(nodes)
    return "\n".join(lines)


def _print_tree(ctx: click.Context, _param: click.Option, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return
    click.echo(render_cli_tree(ctx.command))
    ctx.exit()


def _echo_json(payload: dict) -> None:
    click.echo(json.dumps(payload, ensure_ascii=False, indent=2))


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="chatcrs")
@click.option("--tree", is_flag=True, is_eager=True, expose_value=False, callback=_print_tree, help="Print the registered command tree.")
def main() -> None:
    """CRS HTTP/API helpers plus server-local service commands for ChatArch."""


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
@click.option("--save-token", is_flag=True, default=False, help="Persist the login session under ~/.chatarch/tokens/CRS/<profile>.json.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def admin_login_command(
    profile: str,
    base_url: str | None,
    api_key: str | None,
    username: str | None,
    password: str | None,
    admin_token: str | None,
    timeout: float,
    save_token: bool,
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
        payload = client.login(save_token=save_token)
    except (OSError, ValueError, remote_management.CrsApiError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        click.echo(
            f"ok={payload['ok']} status={payload['status']} token_present={payload['token_present']} "
            f"token_saved={payload.get('token_saved', False)}"
        )


@admin_group.group(name="token")
def admin_token_group() -> None:
    """Manage cached CRS admin session tokens in the ChatArch token store."""


@admin_token_group.command(name="status")
@_common_remote_options
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def admin_token_status_command(
    profile: str,
    base_url: str | None,
    api_key: str | None,
    username: str | None,
    password: str | None,
    admin_token: str | None,
    timeout: float,
    json_output: bool,
) -> None:
    """Show cached CRS admin token metadata without printing the token."""

    try:
        payload = _remote_client(
            profile=profile,
            base_url=base_url,
            api_key=api_key,
            username=username,
            password=password,
            admin_token=admin_token,
            timeout=timeout,
        ).token_store.status()
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        click.echo(
            f"ok={payload['ok']} profile={payload['profile']} token_file_exists={payload['token_file_exists']} "
            f"token_present={payload['token_present']} base_url_match={payload['base_url_match']} expired={payload['expired']}"
        )


@admin_token_group.command(name="refresh")
@_common_remote_options
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def admin_token_refresh_command(
    profile: str,
    base_url: str | None,
    api_key: str | None,
    username: str | None,
    password: str | None,
    admin_token: str | None,
    timeout: float,
    json_output: bool,
) -> None:
    """Login and save a fresh CRS admin session token."""

    try:
        payload = _remote_client(
            profile=profile,
            base_url=base_url,
            api_key=api_key,
            username=username,
            password=password,
            admin_token=admin_token,
            timeout=timeout,
        ).login(save_token=True)
    except (OSError, ValueError, remote_management.CrsApiError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        click.echo(
            f"ok={payload['ok']} status={payload['status']} token_present={payload['token_present']} "
            f"token_saved={payload.get('token_saved', False)}"
        )


@admin_token_group.command(name="clear")
@_common_remote_options
@click.option("--execute", is_flag=True, default=False, help="Actually delete the cached token file. Without it, print a dry-run plan.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def admin_token_clear_command(
    profile: str,
    base_url: str | None,
    api_key: str | None,
    username: str | None,
    password: str | None,
    admin_token: str | None,
    timeout: float,
    execute: bool,
    json_output: bool,
) -> None:
    """Clear the cached CRS admin session token."""

    try:
        payload = _remote_client(
            profile=profile,
            base_url=base_url,
            api_key=api_key,
            username=username,
            password=password,
            admin_token=admin_token,
            timeout=timeout,
        ).token_store.clear(execute=execute)
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        click.echo(f"ok={payload['ok']} profile={payload['profile']} mutated={payload['mutated']} token_file={payload['token_file']}")


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
@click.option("--time-range", default="all", show_default=True, type=click.Choice(["today", "7days", "monthly", "30days", "all"]))
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
@click.option("--time-range", default="all", show_default=True, type=click.Choice(["today", "7days", "monthly", "30days", "all"]))
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


@main.group(name="codex")
def codex_group() -> None:
    """Direct OpenAI Codex account token and usage helpers."""


@codex_group.group(name="token")
def codex_token_group() -> None:
    """Manage OpenAI OAuth tokens through the ChatEnv OpenAI token store."""


@codex_token_group.command(name="status")
@click.option("--profile", default="default", show_default=True, help="OpenAI ChatEnv profile under envs/OpenAI and tokens/OpenAI.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def codex_token_status_command(profile: str, json_output: bool) -> None:
    """Show cached OpenAI OAuth token metadata without printing tokens."""

    try:
        payload = codex_direct.token_status(profile=profile)
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        click.echo(
            f"ok={payload['ok']} service={payload['service']} profile={payload['profile']} "
            f"token_present={payload['token_present']} expires_at={payload.get('expires_at', '')}"
        )


@codex_token_group.command(name="refresh")
@click.option("--profile", default="default", show_default=True, help="OpenAI ChatEnv profile under envs/OpenAI and tokens/OpenAI.")
@click.option("--refresh-token", default=None, help="OpenAI refresh token. Prefer token-store profile for real use.")
@click.option("--client-id", default=None, help="OpenAI OAuth client id. Defaults to the Codex app client id.")
@click.option("--timeout", type=float, default=20.0, show_default=True)
@click.option("--save-token", is_flag=True, default=False, hidden=True, help="Deprecated compatibility flag; use `chatenv token refresh OpenAI <profile>`.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def codex_token_refresh_command(
    profile: str,
    refresh_token: str | None,
    client_id: str | None,
    timeout: float,
    save_token: bool,
    json_output: bool,
) -> None:
    """Refresh an OpenAI OAuth access token without printing token values.

    Prefer `chatenv token refresh OpenAI <profile>` for durable token-store writes.
    This command is kept as a one-off redacted OAuth smoke helper; `--save-token`
    remains accepted as a hidden compatibility flag and writes the OpenAI token
    service, never a Codex-specific namespace.
    """

    try:
        if not refresh_token:
            values = codex_direct.read_stored_token(profile=profile).get("values", {})
            refresh_token = values.get("refresh_token") if isinstance(values, dict) else None
        payload = codex_direct.refresh_access_token(refresh_token=refresh_token or "", client_id=client_id, timeout=timeout)
        output = dict(payload.get("safe") or {"ok": payload.get("ok"), "status": payload.get("status")})
        output.update({"mutated": False, "profile": profile, "token_service": codex_direct.OPENAI_SERVICE_NAME})
        if payload.get("ok") and save_token:
            status = codex_direct.save_token_values(
                profile=profile,
                values=payload.get("values", {}),
                expires_at=payload.get("expires_at") or "",
                source="compat-refresh",
            )
            output.update({"mutated": True, "token_saved": status.get("token_present", False), "token_file": status.get("token_file")})
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(output)
    else:
        click.echo(
            f"ok={output['ok']} profile={profile} token_present={output.get('token_present', False)} "
            f"refresh_token_rotated={output.get('refresh_token_rotated', False)} mutated={output.get('mutated', False)}"
        )


@codex_group.command(name="account")
@click.option("--profile", default="default", show_default=True, help="OpenAI ChatEnv profile under envs/OpenAI and tokens/OpenAI.")
@click.option("--access-token", default=None, help="OpenAI access token. Prefer token-store profile for real use.")
@click.option("--refresh/--no-refresh", default=True, show_default=True, help="Use stored refresh token if no usable access token is available.")
@click.option("--client-id", default=None, help="OpenAI OAuth client id. Defaults to the Codex app client id.")
@click.option("--timeout", type=float, default=20.0, show_default=True)
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def codex_account_command(profile: str, access_token: str | None, refresh: bool, client_id: str | None, timeout: float, json_output: bool) -> None:
    """Read OpenAI Codex account metadata directly from OpenAI."""

    try:
        payload = codex_direct.inspect_account(profile=profile, access_token=access_token, refresh=refresh, client_id=client_id, timeout=timeout)
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        click.echo(f"ok={payload['ok']} status={payload['status']} accounts={payload['account_count']} profile={profile}")


@codex_group.command(name="quota")
@click.option("--profile", default="default", show_default=True, help="OpenAI ChatEnv profile under envs/OpenAI and tokens/OpenAI.")
@click.option("--account-id", default=None, help="ChatGPT/Codex account id to smoke. If omitted, use the OpenAI token-store account mapping.")
@click.option("--access-token", default=None, help="OpenAI access token. Prefer token-store profile for real use.")
@click.option("--refresh/--no-refresh", default=True, show_default=True, help="Use stored refresh token if no usable access token is available.")
@click.option("--client-id", default=None, help="OpenAI OAuth client id. Defaults to the Codex app client id.")
@click.option("--model", default=codex_direct.DEFAULT_CODEX_QUOTA_MODEL, show_default=True, help="Codex-compatible model for the quota smoke request.")
@click.option("--timeout", type=float, default=20.0, show_default=True)
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def codex_quota_command(
    profile: str,
    account_id: str | None,
    access_token: str | None,
    refresh: bool,
    client_id: str | None,
    model: str,
    timeout: float,
    json_output: bool,
) -> None:
    """Run a profile-only Codex responses smoke and show quota headers."""

    try:
        payload = codex_direct.inspect_quota(
            profile=profile,
            account_id=account_id,
            access_token=access_token,
            refresh=refresh,
            client_id=client_id,
            model=model,
            timeout=timeout,
        )
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        rate_limits = cast(dict[str, Any], payload.get("rate_limits")) if isinstance(payload.get("rate_limits"), dict) else {}
        account_resolution = cast(dict[str, Any], payload.get("account_resolution")) if isinstance(payload.get("account_resolution"), dict) else {}
        click.echo(
            f"ok={payload['ok']} status={payload['status']} profile={payload.get('profile', profile)} "
            f"account_id_hash={payload.get('account_id_hash')} account_source={account_resolution.get('source')} "
            f"primary_used_percent={rate_limits.get('primary_used_percent')} "
            f"primary_reset_after_seconds={rate_limits.get('primary_reset_after_seconds')}"
        )


@codex_group.command(name="usage")
@click.option("--profile", default="default", show_default=True, help="OpenAI ChatEnv profile under envs/OpenAI and tokens/OpenAI.")
@click.option("--account-id", default=None, help="ChatGPT/Codex account id to inspect. If omitted, resolve the unique account for the OpenAI profile.")
@click.option("--access-token", default=None, help="OpenAI access token. Prefer token-store profile for real use.")
@click.option("--refresh/--no-refresh", default=True, show_default=True, help="Use stored refresh token if no usable access token is available.")
@click.option("--client-id", default=None, help="OpenAI OAuth client id. Defaults to the Codex app client id.")
@click.option("--timeout", type=float, default=20.0, show_default=True)
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def codex_usage_command(
    profile: str,
    account_id: str | None,
    access_token: str | None,
    refresh: bool,
    client_id: str | None,
    timeout: float,
    json_output: bool,
) -> None:
    """Read Codex usage and quota metadata directly from OpenAI."""

    try:
        payload = codex_direct.inspect_usage(
            profile=profile,
            account_id=account_id,
            access_token=access_token,
            refresh=refresh,
            client_id=client_id,
            timeout=timeout,
        )
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        rate_limits = payload.get("rate_limits") if isinstance(payload.get("rate_limits"), dict) else {}
        click.echo(
            f"ok={payload['ok']} status={payload['status']} account_id={payload.get('account_id')} "
            f"primary_used_percent={rate_limits.get('primary_used_percent')}"
        )


def _service_target(
    *,
    app_dir: str | None,
    crs_command: str | None,
    timeout: float,
) -> service_management.ServiceTarget:
    return service_management.ServiceTarget.from_options(
        app_dir=app_dir,
        crs_command=crs_command,
        timeout=timeout,
    )


def _service_action_command(
    action: str,
    *,
    app_dir: str | None,
    crs_command: str | None,
    timeout: float,
    execute: bool | None,
    json_output: bool,
    branch: str | None = None,
) -> None:
    target = _service_target(app_dir=app_dir, crs_command=crs_command, timeout=timeout)
    try:
        payload = service_management.run_service_action(action, target=target, execute=execute, branch=branch)
    except (OSError, RuntimeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        _echo_json(payload)
    else:
        local_command = payload["local_command"]
        if not isinstance(local_command, list):
            local_command = [local_command]
        click.echo(
            f"ok={payload['ok']} action={payload['action']} mode={payload['mode']} "
            f"mutated={payload['mutated']} command={' '.join(str(part) for part in local_command)}"
        )
    if payload.get("mode") == "execute" and not payload.get("ok", False):
        raise click.ClickException(f"crs {action} failed")


@main.group(name="service")
def service_group() -> None:
    """Local CRS service lifecycle commands for the current server."""


@service_group.command(name="install")
@click.option("--app-dir", default=None, type=click.Path(file_okay=False, path_type=str), help="Local CRS app directory. Defaults to the current working directory.")
@click.option("--crs-command", default=None, help="Local crs executable or command name. Defaults to crs.")
@click.option("--timeout", type=float, default=120.0, show_default=True)
@click.option("--execute", is_flag=True, default=False, help="Actually run local `crs install`. Without it, print a dry-run plan.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def service_install_command(app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    """Plan or execute local `crs install` on this server."""

    _service_action_command("install", app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=execute, json_output=json_output)


@service_group.command(name="update")
@click.option("--app-dir", default=None, type=click.Path(file_okay=False, path_type=str), help="Local CRS app directory. Defaults to the current working directory.")
@click.option("--crs-command", default=None, help="Local crs executable or command name. Defaults to crs.")
@click.option("--timeout", type=float, default=120.0, show_default=True)
@click.option("--execute", is_flag=True, default=False, help="Actually run local `crs update`. Without it, print a dry-run plan.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def service_update_command(app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    """Plan or execute local `crs update` on this server."""

    _service_action_command("update", app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=execute, json_output=json_output)


@service_group.command(name="start")
@click.option("--app-dir", default=None, type=click.Path(file_okay=False, path_type=str), help="Local CRS app directory. Defaults to the current working directory.")
@click.option("--crs-command", default=None, help="Local crs executable or command name. Defaults to crs.")
@click.option("--timeout", type=float, default=120.0, show_default=True)
@click.option("--execute", is_flag=True, default=False, help="Actually run local `crs start`. Without it, print a dry-run plan.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def service_start_command(app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    """Plan or execute local `crs start` on this server."""

    _service_action_command("start", app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=execute, json_output=json_output)


@service_group.command(name="stop")
@click.option("--app-dir", default=None, type=click.Path(file_okay=False, path_type=str), help="Local CRS app directory. Defaults to the current working directory.")
@click.option("--crs-command", default=None, help="Local crs executable or command name. Defaults to crs.")
@click.option("--timeout", type=float, default=120.0, show_default=True)
@click.option("--execute", is_flag=True, default=False, help="Actually run local `crs stop`. Without it, print a dry-run plan.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def service_stop_command(app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    """Plan or execute local `crs stop` on this server."""

    _service_action_command("stop", app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=execute, json_output=json_output)


@service_group.command(name="restart")
@click.option("--app-dir", default=None, type=click.Path(file_okay=False, path_type=str), help="Local CRS app directory. Defaults to the current working directory.")
@click.option("--crs-command", default=None, help="Local crs executable or command name. Defaults to crs.")
@click.option("--timeout", type=float, default=120.0, show_default=True)
@click.option("--execute", is_flag=True, default=False, help="Actually run local `crs restart`. Without it, print a dry-run plan.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def service_restart_command(app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    """Plan or execute local `crs restart` on this server."""

    _service_action_command("restart", app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=execute, json_output=json_output)


@service_group.command(name="status")
@click.option("--app-dir", default=None, type=click.Path(file_okay=False, path_type=str), help="Local CRS app directory. Defaults to the current working directory.")
@click.option("--crs-command", default=None, help="Local crs executable or command name. Defaults to crs.")
@click.option("--timeout", type=float, default=120.0, show_default=True)
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def service_status_command(app_dir: str | None, crs_command: str | None, timeout: float, json_output: bool) -> None:
    """Execute local `crs status` on this server."""

    _service_action_command("status", app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=None, json_output=json_output)


@service_group.command(name="switch-branch")
@click.argument("branch")
@click.option("--app-dir", default=None, type=click.Path(file_okay=False, path_type=str), help="Local CRS app directory. Defaults to the current working directory.")
@click.option("--crs-command", default=None, help="Local crs executable or command name. Defaults to crs.")
@click.option("--timeout", type=float, default=120.0, show_default=True)
@click.option("--execute", is_flag=True, default=False, help="Actually run local `crs switch-branch <branch>`. Without it, print a dry-run plan.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def service_switch_branch_command(branch: str, app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    """Plan or execute local `crs switch-branch <branch>` on this server."""

    _service_action_command("switch-branch", app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=execute, json_output=json_output, branch=branch)


@service_group.command(name="update-pricing")
@click.option("--app-dir", default=None, type=click.Path(file_okay=False, path_type=str), help="Local CRS app directory. Defaults to the current working directory.")
@click.option("--crs-command", default=None, help="Local crs executable or command name. Defaults to crs.")
@click.option("--timeout", type=float, default=120.0, show_default=True)
@click.option("--execute", is_flag=True, default=False, help="Actually run local `crs update-pricing`. Without it, print a dry-run plan.")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def service_update_pricing_command(app_dir: str | None, crs_command: str | None, timeout: float, execute: bool, json_output: bool) -> None:
    """Plan or execute local `crs update-pricing` on this server."""

    _service_action_command("update-pricing", app_dir=app_dir, crs_command=crs_command, timeout=timeout, execute=execute, json_output=json_output)


if __name__ == "__main__":
    main()
