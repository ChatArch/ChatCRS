from pathlib import Path


def test_publish_workflow_requires_tag_ref_before_pypi_publish():
    workflow = Path(".github/workflows/publish.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch" in workflow
    assert "GITHUB_REF_TYPE" in workflow
    assert '!= "tag"' in workflow
    assert "GITHUB_REF_NAME" in workflow
    assert "RELEASE_TAG" in workflow
    assert workflow.index("Check release ref matches package version") < workflow.index(
        "Check release commit is on default branch"
    )
    assert workflow.index("Check release commit is on default branch") < workflow.index(
        "Check PyPI version"
    )
    assert workflow.index("Check release commit is on default branch") < workflow.index(
        "Publish to PyPI (OIDC)"
    )


def test_publish_workflow_uses_oidc_with_main_ancestry_and_no_legacy_secret():
    workflow = Path(".github/workflows/publish.yml").read_text(encoding="utf-8")

    assert "id-token: write" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "Publish to PyPI (OIDC)" in workflow
    assert "git fetch --no-tags origin main:refs/remotes/origin/main" in workflow
    assert 'git merge-base --is-ancestor "${GITHUB_SHA}" "origin/main"' in workflow
    assert "git fetch origin main --tags" not in workflow
    assert "git fetch origin master --tags" not in workflow
    assert "environment: pypi" not in workflow
    assert "TWINE_PASSWORD" not in workflow
    assert "PYPI_API_TOKEN" not in workflow
    assert "secrets.PYPI" not in workflow


def test_ci_workflow_installs_package_and_smokes_cli_tree():
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "python-version: ${{ matrix.python-version }}" in workflow
    assert '"3.10"' in workflow
    assert '"3.11"' in workflow
    assert '"3.12"' in workflow
    assert "python -m pip install -e .[dev,docs]" in workflow
    assert "chatcrs --version" in workflow
    assert "chatcrs --tree" in workflow
    assert "chatcrs --tree-brief" in workflow
    assert "python -m mkdocs build --strict" in workflow