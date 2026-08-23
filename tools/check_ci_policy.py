#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "ci" / "pipeline-policy.json"
ACTION_PATTERN = re.compile(r"^\s*-\s+uses:\s*([^@\s]+)@([^\s#]+)", re.MULTILINE)
WRITE_PERMISSION_PATTERN = re.compile(
    r"^\s*(?:permissions:\s*write-all|[A-Za-z-]+:\s*write)\s*$", re.MULTILINE
)


def validate_workflow_text(name, text, policy):
    errors = []
    for event in policy["forbiddenEvents"]:
        if re.search(rf"\b{re.escape(event)}\b", text):
            errors.append(f"{name}: forbidden event {event}")

    if WRITE_PERMISSION_PATTERN.search(text):
        errors.append(f"{name}: write permission is forbidden")
    if re.search(r"^permissions:\s*read-all\s*$", text, re.MULTILINE):
        errors.append(f"{name}: permissions must be explicit contents: read")
    if not re.search(
        r"^permissions:\s*\n\s+contents:\s*read\s*$", text, re.MULTILINE
    ):
        errors.append(f"{name}: top-level contents: read permission is required")

    trusted = policy["trustedActions"]
    for match in ACTION_PATTERN.finditer(text):
        action, reference = match.groups()
        if action.startswith("./"):
            continue
        if action not in trusted:
            errors.append(f"{name}: action {action} is not trusted")
            continue
        if not re.fullmatch(r"[0-9a-f]{40}", reference):
            errors.append(f"{name}: action {action} must use an immutable SHA")
        elif reference != trusted[action]:
            errors.append(f"{name}: action {action} SHA differs from policy")

        if action == "actions/checkout":
            next_step = text.find("\n      - ", match.end())
            step = text[match.start() : next_step if next_step >= 0 else len(text)]
            if not re.search(r"persist-credentials:\s*false\b", step):
                errors.append(f"{name}: checkout must set persist-credentials false")

    fork_condition = (
        "github.event_name != 'pull_request' || "
        "github.event.pull_request.head.repo.fork == false"
    )
    if "pull_request" in text and "SONAR_TOKEN" in text and fork_condition not in text:
        errors.append(f"{name}: Sonar token use lacks the fork pull-request guard")
    return errors


def validate_repository(root, policy):
    errors = []
    workflows = root / ".github" / "workflows"
    for workflow in sorted(workflows.glob("*.y*ml")):
        errors.extend(
            validate_workflow_text(
                workflow.name, workflow.read_text(encoding="utf-8"), policy
            )
        )

    coverage_path = workflows / "coverage.yml"
    if not coverage_path.is_file():
        errors.append("coverage.yml: required workflow is missing")
        return errors
    coverage = coverage_path.read_text(encoding="utf-8")
    threshold = policy["coverageMinimum"]
    if f"--fail-under={threshold}" not in coverage:
        errors.append(f"coverage.yml: missing {threshold}% coverage gate")
    for report in policy["requiredReports"]:
        if report not in coverage:
            errors.append(f"coverage.yml: required report not named: {report}")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate GitHub workflow policy")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args(argv)
    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    errors = validate_repository(args.root, policy)
    for error in errors:
        print(error)
    if errors:
        return 1
    print("pipeline policy passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
