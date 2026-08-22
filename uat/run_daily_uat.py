#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FEATURE = ROOT / "uat" / "features" / "daily.feature"
REPOSITORY = "fuchi-no-dokuneko/Gomoku-python-"
STEP_BINDINGS = []


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def step(pattern):
    def register(function):
        STEP_BINDINGS.append((re.compile(pattern), function))
        return function

    return register


def run_command(arguments, timeout=45):
    return subprocess.run(
        arguments,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def capture(context, name, completed):
    transcript = (
        f"command: {' '.join(str(value) for value in completed.args)}\n"
        f"exit: {completed.returncode}\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}\n"
    )
    workspace = str(context["workspace"])
    transcript = transcript.replace(workspace, "<temporary-workspace>")
    (context["capture_dir"] / f"{name}.txt").write_text(transcript, encoding="utf-8")


@step(r"a clean temporary record directory")
def clean_record_directory(context):
    context["record_dir"] = context["workspace"] / "records"
    context["record_dir"].mkdir()


@step(r"I play seeded game (\d+) through the real command line")
def play_seeded_game(context, seed):
    context["game"] = run_command(
        [
            sys.executable,
            "game.py",
            "--record-dir",
            str(context["record_dir"]),
            "--seed",
            seed,
        ]
    )
    capture(context, "game", context["game"])


@step(r"the game command succeeds")
def game_succeeds(context):
    assert context["game"].returncode == 0, context["game"].stderr


@step(r"the saved game contains legal coordinate pairs")
def saved_coordinates_are_legal(context):
    records = list(context["record_dir"].glob("*.txt"))
    assert len(records) == 1, f"expected one record, found {len(records)}"
    context["record"] = records[0]
    fields = context["record"].read_text(encoding="utf-8").split(",")
    assert fields[-1] == "", "legacy record must end after a complete pair"
    fields.pop()
    assert fields and len(fields) % 2 == 0, "record has an incomplete coordinate pair"
    values = [int(field) for field in fields]
    moves = list(zip(values[0::2], values[1::2]))
    assert all(0 <= value < 19 for move in moves for value in move)
    assert len(moves) == len(set(moves)), "record reuses an occupied coordinate"
    context["move_count"] = len(moves)


@step(r"the saved game reaches a terminal result")
def game_reaches_terminal_result(context):
    match = re.search(r"state=(-?\d+) moves=(\d+)", context["game"].stdout)
    assert match, "game output has no result summary"
    context["game_state"] = int(match.group(1))
    assert context["game_state"] in (-1, 1, 2)
    assert int(match.group(2)) == context["move_count"]


@step(r"I replay the generated record through the real command line")
def replay_generated_record(context):
    context["replay"] = run_command(
        [
            sys.executable,
            "replay.py",
            str(context["record"]),
            "--root",
            str(context["record_dir"]),
        ]
    )
    capture(context, "replay", context["replay"])


@step(r"the replay command succeeds")
def replay_succeeds(context):
    assert context["replay"].returncode == 0, context["replay"].stderr


@step(r"the replay terminal result matches the game")
def replay_result_matches(context):
    match = re.search(r"moves=(\d+) state=(-?\d+)", context["replay"].stdout)
    assert match, "replay output has no result summary"
    assert int(match.group(1)) == context["move_count"]
    assert int(match.group(2)) == context["game_state"]


def parse_feature(path):
    feature_name = None
    scenarios = []
    current = None
    keywords = ("Given ", "When ", "Then ", "And ", "But ")
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("Feature:"):
            feature_name = line.removeprefix("Feature:").strip()
        elif line.startswith("Scenario:"):
            current = {"name": line.removeprefix("Scenario:").strip(), "steps": []}
            scenarios.append(current)
        elif line.startswith(keywords):
            if current is None:
                raise ValueError(f"step before scenario at line {line_number}")
            current["steps"].append((line.split(maxsplit=1)[1], line_number))
    if not feature_name or not scenarios:
        raise ValueError("feature and at least one scenario are required")
    return feature_name, scenarios


def binding_for(text):
    matches = [
        (pattern.fullmatch(text), function) for pattern, function in STEP_BINDINGS
    ]
    matches = [(match, function) for match, function in matches if match]
    if len(matches) != 1:
        raise ValueError(f"expected one binding for '{text}', found {len(matches)}")
    return matches[0]


def verify_bindings(scenarios):
    for scenario in scenarios:
        for text, line_number in scenario["steps"]:
            try:
                binding_for(text)
            except ValueError as error:
                raise ValueError(f"{error} at line {line_number}") from error


def git_commit():
    completed = run_command(["git", "rev-parse", "HEAD"], timeout=5)
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def write_reports(output, feature_path, started_at, results):
    completed_at = utc_now()
    checklist = {
        "repository": REPOSITORY,
        "commit": git_commit(),
        "startedAt": started_at,
        "completedAt": completed_at,
        "overall": all(result["passed"] for result in results),
        "scenarios": results,
    }
    (output / "checklist.json").write_text(
        json.dumps(checklist, indent=2) + "\n", encoding="utf-8"
    )

    root = ET.Element("testExecutions", version="1")
    file_node = ET.SubElement(root, "file", path=str(feature_path.relative_to(ROOT)))
    for result in results:
        case = ET.SubElement(
            file_node,
            "testCase",
            name=result["name"],
            duration=str(result["durationMs"]),
        )
        if not result["passed"]:
            failure = ET.SubElement(case, "failure", message=result["diagnostics"])
            failure.text = result["diagnostics"]
    ET.ElementTree(root).write(
        output / "sonar-test-execution.xml", encoding="utf-8", xml_declaration=True
    )
    return checklist


def run(feature_path, output):
    _, scenarios = parse_feature(feature_path)
    verify_bindings(scenarios)
    output.mkdir(parents=True, exist_ok=True)
    capture_dir = output / "screenshots"
    capture_dir.mkdir(exist_ok=True)
    started_at = utc_now()
    results = []

    for scenario in scenarios:
        scenario_start = time.monotonic()
        scenario_started_at = utc_now()
        diagnostics = ""
        passed = True
        with tempfile.TemporaryDirectory(prefix="gomoku-uat-") as workspace:
            context = {
                "workspace": Path(workspace),
                "capture_dir": capture_dir,
            }
            try:
                for text, _ in scenario["steps"]:
                    match, function = binding_for(text)
                    function(context, *match.groups())
            except Exception as error:
                passed = False
                diagnostics = f"{type(error).__name__}: {error}"
        results.append(
            {
                "name": scenario["name"],
                "passed": passed,
                "startedAt": scenario_started_at,
                "completedAt": utc_now(),
                "durationMs": round((time.monotonic() - scenario_start) * 1000),
                "diagnostics": diagnostics,
            }
        )

    checklist = write_reports(output, feature_path, started_at, results)
    return 0 if checklist["overall"] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the daily Gomoku Gherkin UAT")
    parser.add_argument("--feature", type=Path, default=DEFAULT_FEATURE)
    parser.add_argument("--output", type=Path, default=ROOT / "uat-results")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sonar", action="store_true")
    args = parser.parse_args(argv)

    _, scenarios = parse_feature(args.feature)
    verify_bindings(scenarios)
    if args.dry_run:
        step_count = sum(len(scenario["steps"]) for scenario in scenarios)
        print(f"Bound {step_count} steps in {len(scenarios)} scenario(s)")
        return 0

    exit_code = run(args.feature, args.output)
    if args.sonar and exit_code == 0:
        scanner = shutil.which("sonar-scanner")
        if scanner is None:
            print("sonar-scanner is not installed", file=sys.stderr)
            return 2
        scan = subprocess.run(
            [
                scanner,
                f"-Dsonar.testExecutionReportPaths={args.output / 'sonar-test-execution.xml'}",
            ],
            cwd=ROOT,
            check=False,
        )
        return scan.returncode
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
