from pathlib import Path

from chatcrs.cli import main
from chatcrs.config import ChatcrsConfig


EXPECTED_CLI_LEAVES = {
    "chatcrs health",
    "chatcrs admin login",
    "chatcrs admin accounts usage",
    "chatcrs admin accounts refresh-status",
    "chatcrs admin keys list",
    "chatcrs admin keys show",
    "chatcrs key info",
}

REMOVED_OPERATIONAL_CLI_LEAVES = {
    "chatcrs inspect",
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
    "chatcrs service install",
    "chatcrs service update",
    "chatcrs service start",
    "chatcrs service stop",
    "chatcrs service restart",
    "chatcrs service status",
    "chatcrs service switch-branch",
    "chatcrs service update-pricing",
}

PUBLIC_DOCS = (
    "README.md",
    "README.en.md",
    "docs/index.md",
    "docs/index.en.md",
    "docs/cli.md",
    "docs/cli.en.md",
    "docs/configuration.md",
    "docs/configuration.en.md",
    "docs/production-maintenance.md",
    "docs/production-maintenance.en.md",
)

FORBIDDEN_PUBLIC_DOC_FRAGMENTS = (
    "--ssh-alias",
    "CHATCRS_SSH_ALIAS",
    "CHATCRS_APP_DIR",
    "CHATCRS_CRS_COMMAND",
    "~/.chatarch/envs/Chatcrs",
    "tencent.am",
    "/home/zhihong",
    "through SSH",
    "over SSH",
    "通过 SSH",
)


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


def test_final_cli_surface_matches_http_first_tree():
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


def test_public_docs_do_not_advertise_ssh_or_real_host_paths():
    offenders = []
    for path in PUBLIC_DOCS:
        if not Path(path).exists():
            continue
        text = _reference_text(path)
        for fragment in FORBIDDEN_PUBLIC_DOC_FRAGMENTS:
            if fragment in text:
                offenders.append(f"{path}: {fragment}")
    assert offenders == []


def test_chatenv_provider_is_single_crs_http_namespace_without_ssh_fields():
    fields = ChatcrsConfig.get_fields()
    env_keys = {field.env_key for field in fields.values()}

    assert ChatcrsConfig._storage_dir == "CRS"
    assert {
        "CRS_API_BASE",
        "CRS_API_KEY",
        "CRS_USERNAME",
        "CRS_PASSWORD",
        "CRS_ACCESS_TOKEN",
    }.issubset(env_keys)
    assert not {
        "CHATCRS_SSH_ALIAS",
        "CHATCRS_APP_DIR",
        "CHATCRS_CRS_COMMAND",
    } & env_keys
