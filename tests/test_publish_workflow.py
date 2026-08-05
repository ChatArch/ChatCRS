from pathlib import Path


def test_publish_workflow_requires_tag_ref_before_pypi_publish():
    workflow = Path(".github/workflows/publish.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch" in workflow
    assert "GITHUB_REF_TYPE" in workflow
    assert '!= "tag"' in workflow
    assert "GITHUB_REF_NAME" in workflow
    assert "RELEASE_TAG" in workflow
    assert workflow.index("Check release ref matches package version") < workflow.index(
        "Check PyPI version"
    )
    assert workflow.index("Check release ref matches package version") < workflow.index(
        "Publish to PyPI"
    )