from chatcrs import __version__


def test_version_present():
    assert __version__ == "0.2.9"


def test_chatenv_dependency_and_refresh_provider_entry_point_declared():
    from pathlib import Path

    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert '"chatenv>=0.2.7,<0.3.0"' in pyproject
    assert '[project.entry-points."chatenv.token_refreshers"]' in pyproject
    assert 'CRS = "chatcrs.tokens:refresh_chatenv_token"' in pyproject
    assert 'OpenAI = "chatcrs.codex_direct:refresh_chatenv_token"' in pyproject
