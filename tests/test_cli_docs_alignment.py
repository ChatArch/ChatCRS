from pathlib import Path

from chatcrs.cli import main


DISCUSSED_CLI_LEAVES = {
    "chatcrs health",
    "chatcrs local verify",
    "chatcrs verify sidecar",
    "chatcrs verify images",
    "chatcrs admin login",
    "chatcrs admin accounts usage",
    "chatcrs admin accounts refresh-status",
    "chatcrs admin keys list",
    "chatcrs admin keys show",
    "chatcrs key info",
    "chatcrs service install",
    "chatcrs service update",
    "chatcrs service start",
    "chatcrs service stop",
    "chatcrs service restart",
    "chatcrs service status",
    "chatcrs service switch-branch",
    "chatcrs service update-pricing",
    "chatcrs nginx plan-cutover",
    "chatcrs cutover precheck",
    "chatcrs debug status",
    "chatcrs debug logs",
    "chatcrs debug restart",
    "chatcrs debug settings show",
    "chatcrs debug settings set",
    "chatcrs debug upgrade plan",
    "chatcrs debug upgrade apply",
    "chatcrs inspect",
}


def _leaf_commands(command, prefix="chatcrs"):
    children = getattr(command, "commands", {})
    if not children:
        return {prefix}
    leaves = set()
    for name, child in children.items():
        leaves.update(_leaf_commands(child, f"{prefix} {name}"))
    return leaves


def test_discussed_cli_surface_is_registered():
    registered = _leaf_commands(main)
    assert DISCUSSED_CLI_LEAVES <= registered


def test_cli_reference_covers_every_registered_leaf_command():
    docs = Path("docs/cli.md").read_text(encoding="utf-8")
    missing = sorted(command for command in _leaf_commands(main) if command not in docs)
    assert not missing


def test_english_cli_reference_covers_every_registered_leaf_command():
    docs = Path("docs/cli.en.md").read_text(encoding="utf-8")
    missing = sorted(command for command in _leaf_commands(main) if command not in docs)
    assert not missing
