from pathlib import Path


PUBLIC_DOCS = (
    "README.md",
    "README.en.md",
    "docs/index.md",
    "docs/index.en.md",
    "docs/cli.md",
    "docs/cli.en.md",
    "docs/interfaces.md",
    "docs/interfaces.en.md",
    "docs/configuration.md",
    "docs/configuration.en.md",
    "docs/production-maintenance.md",
    "docs/production-maintenance.en.md",
    "docs/development.md",
)


def test_mkdocs_material_renderer_and_public_url_contract():
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "site_url: https://arch.gh.wzhecnu.cn/ChatCRS/" in mkdocs
    assert "name: material" in mkdocs
    assert "mkdocs-material>=9.5,<10.0" in pyproject
    assert "pymdownx.emoji" in mkdocs
    assert "material.extensions.emoji.twemoji" in mkdocs
    assert "material.extensions.emoji.to_svg" in mkdocs
    assert "index.md" in mkdocs
    assert "index.en.md" in "\n".join(p.name for p in Path("docs").glob("*.en.md"))


def test_public_markdown_sources_do_not_leak_material_icon_shorthand():
    offenders = []
    for path in PUBLIC_DOCS:
        p = Path(path)
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        if ":material-" in text:
            offenders.append(path)
    assert offenders == []


def test_readmes_include_current_admin_token_tree():
    for path in ("README.md", "README.en.md"):
        text = Path(path).read_text(encoding="utf-8")
        assert "chatcrs admin token status" in text
        assert "chatcrs admin token refresh" in text
        assert "chatcrs admin token clear" in text
        assert "[--save-token]" in text
