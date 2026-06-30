"""CLI entrypoint for chatcrs."""

from __future__ import annotations

import json

import click

from chatcrs import __version__
from chatcrs.cutover import formal_single_active_precheck
from chatcrs.inspect import inspect_crs_layout
from chatcrs.nginx import plan_nginx_cutover
from chatcrs.paths import CrsPaths
from chatcrs.verify import verify_sidecar


def _echo_json(payload: dict) -> None:
    click.echo(json.dumps(payload, ensure_ascii=False, indent=2))


def _paths(**overrides: object) -> CrsPaths:
    values = {key: value for key, value in overrides.items() if value is not None}
    return CrsPaths(**values)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="chatcrs")
def main() -> None:
    """CRS management helpers for ChatArch."""


@main.command(name="inspect")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def inspect_command(json_output: bool) -> None:
    """Inspect known CRS services without mutating them."""

    payload = inspect_crs_layout()
    if json_output:
        _echo_json(payload)
    else:
        click.echo(f"old={payload['old']['health'].get('status')} new={payload['new']['health'].get('status')} mutated={payload['mutated']}")


@main.group(name="verify")
def verify_group() -> None:
    """Run read-only verification checks."""


@verify_group.command(name="sidecar")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def verify_sidecar_command(json_output: bool) -> None:
    """Verify old/new sidecar CRS services."""

    payload = verify_sidecar()
    if json_output:
        _echo_json(payload)
    else:
        click.echo(f"ok={payload['ok']} mutated={payload['mutated']}")


@main.group(name="nginx")
def nginx_group() -> None:
    """Plan Nginx CRS routing changes."""


@nginx_group.command(name="plan-cutover")
@click.option("--config", "config_path", default="/etc/nginx/sites-available/single/crs.conf", show_default=True)
@click.option("--from-port", default=12390, show_default=True, type=int)
@click.option("--to-port", default=12391, show_default=True, type=int)
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def nginx_plan_cutover_command(config_path: str, from_port: int, to_port: int, json_output: bool) -> None:
    """Generate a read-only Nginx cutover diff."""

    payload = plan_nginx_cutover(config_path, from_port=from_port, to_port=to_port)
    if json_output:
        _echo_json(payload)
    else:
        click.echo(payload.get("diff", ""))


@main.group(name="cutover")
def cutover_group() -> None:
    """Formal single-active cutover checks."""


@cutover_group.command(name="precheck")
@click.option("--json-output", is_flag=True, default=False, help="Render structured JSON output.")
def cutover_precheck_command(json_output: bool) -> None:
    """Check readiness for a formal single-active DB0 cutover."""

    payload = formal_single_active_precheck()
    if json_output:
        _echo_json(payload)
    else:
        click.echo(f"ready={payload['ready_for_formal_cutover_after_packages']} mutated={payload['mutated']}")


if __name__ == "__main__":
    main()
