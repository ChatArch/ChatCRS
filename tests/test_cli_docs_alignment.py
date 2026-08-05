from pathlib import Path

from chatcrs.cli import main


EXPECTED_CLI_LEAVES = {
    "chatcrs health",
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
    "chatcrs inspect",
}

REMOVED_OPERATIONAL_CLI_LEAVES = {
    "chatcrs local verify",
    "chatcrs verify sidecar",
    "chatcrs verify images",
    "chatcrs nginx plan-cutover",
    "chatcrs cutover precheck",
    "chatcrs debug status",
    "chatcrs debug logs",
    "chatcrs debug restart",
    "chatcrs debug settings show",
    "chatcrs debug settings set",
    "chatcrs debug upgrade plan",
    "chatcrs debug upgrade apply",
}


def _leaf_commands(command, prefix="chatcrs"):
    children = getattr(command, "commands", {})
    if not children:
        return {prefix}
    leaves = set()
    for name, child in children.items():
        leaves.update(_leaf_commands(child, f"{prefix} {name}"))
    return leaves


def _reference_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_final_cli_surface_matches_user_approved_tree():
    assert _leaf_commands(main) == EXPECTED_CLI_LEAVES


def test_removed_operational_workflows_are_not_registered():
    registered = _leaf_commands(main)
    assert registered.isdisjoint(REMOVED_OPERATIONAL_CLI_LEAVES)


def test_cli_reference_covers_only_registered_leaf_commands():
    docs = _reference_text("docs/cli.md")
    missing = sorted(command for command in EXPECTED_CLI_LEAVES if command not in docs)
    stale = sorted(command for command in REMOVED_OPERATIONAL_CLI_LEAVES if command in docs)
    assert not missing
    assert not stale


def test_english_cli_reference_covers_only_registered_leaf_commands():
    docs = _reference_text("docs/cli.en.md")
    missing = sorted(command for command in EXPECTED_CLI_LEAVES if command not in docs)
    stale = sorted(command for command in REMOVED_OPERATIONAL_CLI_LEAVES if command in docs)
    assert not missing
    assert not stale
