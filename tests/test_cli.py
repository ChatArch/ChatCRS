from click.testing import CliRunner

from chatcrs import __version__
from chatcrs.cli import main, render_cli_tree


def test_version_option_reports_package_version():
    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert f"chatcrs, version {__version__}" in result.output


def test_help_mentions_tree_option():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0, result.output
    assert "--tree" in result.output


def test_tree_option_prints_registered_tree():
    result = CliRunner().invoke(main, ["--tree"])

    assert result.exit_code == 0, result.output
    assert "chatcrs  # CRS HTTP/API helpers" in result.output
    assert "├── --help  # Show this help message." in result.output
    assert "├── --version  # Show the installed package version." in result.output
    assert "├── --tree  # Print the registered command tree." in result.output
    assert "admin  # Remote CRS administrator operations via HTTPS Admin API." in result.output
    assert "refresh-status <ACCOUNT-ID>" in result.output
    assert "service" in result.output
    assert "update-pricing" in result.output
    assert "hello" not in result.output.lower()


def test_render_cli_tree_matches_cli_output():
    result = CliRunner().invoke(main, ["--tree"])

    assert result.exit_code == 0, result.output
    assert result.output.strip() == render_cli_tree(main)
