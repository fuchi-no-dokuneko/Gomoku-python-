import json
from pathlib import Path

from tools.check_ci_policy import validate_repository, validate_workflow_text


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "ci" / "pipeline-policy.json"


def load_policy():
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def test_repository_workflows_satisfy_pipeline_policy():
    assert validate_repository(ROOT, load_policy()) == []


def test_policy_rejects_privileged_fork_trigger_and_mutable_action():
    workflow = """
name: unsafe
on: pull_request_target
permissions:
  contents: write
jobs:
  unsafe:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: true
"""

    errors = validate_workflow_text("unsafe.yml", workflow, load_policy())

    assert any("pull_request_target" in error for error in errors)
    assert any("write permission" in error for error in errors)
    assert any("immutable SHA" in error for error in errors)
    assert any("persist-credentials" in error for error in errors)


def test_policy_rejects_unknown_third_party_action():
    workflow = """
name: unknown
on: push
permissions:
  contents: read
jobs:
  inspect:
    runs-on: ubuntu-24.04
    steps:
      - uses: example/unknown-action@0123456789012345678901234567890123456789
"""

    errors = validate_workflow_text("unknown.yml", workflow, load_policy())

    assert any("not trusted" in error for error in errors)


def test_coverage_workflow_names_every_required_report():
    workflow = (ROOT / ".github" / "workflows" / "coverage.yml").read_text(
        encoding="utf-8"
    )

    for report in load_policy()["requiredReports"]:
        assert report in workflow
