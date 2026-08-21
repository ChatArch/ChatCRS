from chatstyle import render_click_tree
from click.testing import CliRunner

from chatcrs import __version__
from chatcrs.cli import main


def test_version_option_reports_package_version():
    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert f"chatcrs, version {__version__}" in result.output


def test_help_mentions_tree_options():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0, result.output
    assert "--tree" in result.output
    assert "--tree-brief" in result.output


def test_tree_option_prints_registered_tree():
    result = CliRunner().invoke(main, ["--tree"])

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[0] == "chatcrs"
    assert "├── --help  # Show this message and exit." in result.output
    assert "├── --version  # Show the version and exit." in result.output
    assert "├── --tree  # Print the registered CLI tree and exit." in result.output
    assert "├── --tree-brief  # Print the registered CLI tree without parameter signatures and exit." in result.output
    assert "admin  # Remote CRS administrator operations via HTTPS Admin API." in result.output
    assert "refresh-status [--profile PROFILE]" in result.output
    assert "<ACCOUNT-ID>" in result.output
    assert "quota [--profile PROFILE]" in result.output
    assert "service" in result.output
    assert "update-pricing" in result.output
    assert "hello" not in result.output.lower()


def test_tree_brief_omits_signatures_but_keeps_nodes_and_descriptions():
    result = CliRunner().invoke(main, ["--tree-brief"])

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[0] == "chatcrs"
    assert "refresh-status  # Reset a CRS OpenAI account status after transient failures." in result.output
    assert "quota  # Run a profile-only Codex responses smoke and show quota headers." in result.output
    assert "switch-branch  # Plan or execute local `crs switch-branch <branch>` on this server." in result.output
    assert "[--profile PROFILE]" not in result.output
    assert "<ACCOUNT-ID>" not in result.output


def test_shared_tree_renderer_matches_cli_output():
    result = CliRunner().invoke(main, ["--tree"])
    brief_result = CliRunner().invoke(main, ["--tree-brief"])

    assert result.exit_code == 0, result.output
    assert brief_result.exit_code == 0, brief_result.output
    assert result.output.strip() == render_click_tree(main, root_name="chatcrs")
    assert brief_result.output.strip() == render_click_tree(
        main, root_name="chatcrs", brief=True
    )
