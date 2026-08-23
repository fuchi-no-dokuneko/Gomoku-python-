#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import numpy as np

from plane import plane


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "renju" / "corpus.json"


def load_corpus(path):
    document = json.loads(path.read_text(encoding="utf-8"))
    required_kinds = {"positive", "negative", "symmetry", "edge"}
    for rule in ("win", "overline", "double_three", "double_four", "blocked"):
        kinds = {case["kind"] for case in document["cases"] if case["rule"] == rule}
        missing = required_kinds - kinds
        if missing:
            raise ValueError(f"{rule} is missing corpus kinds: {sorted(missing)}")
    return document


def current_outcome(case):
    board = plane()
    for row, column in case["black"]:
        board.p1919[row, column] = 1
    for row, column in case["white"]:
        board.p1919[row, column] = -1

    row, column = case["move"]
    player = case["player"]
    if board.p1919[row, column] != 0:
        return {"legal": False, "win": False, "reason": "occupied"}

    candidate = np.copy(board.p1919)
    candidate[row, column] = player
    detected_win = bool(board.checkwin(player, candidate))
    if player == -1:
        return {
            "legal": True,
            "win": detected_win,
            "reason": "white_five_or_more" if detected_win else "legal",
        }

    lines = board.extractarray(row, column, board.p1919, player)
    overline = bool(board.stopmorefive(lines, player))
    double_four = bool(board.doubledeadfour(lines, player))
    double_three = bool(board.doublelivethree(lines, player))
    if overline:
        return {"legal": False, "win": False, "reason": "overline"}
    if detected_win:
        return {"legal": True, "win": True, "reason": "exact_five"}
    if double_four:
        return {"legal": False, "win": False, "reason": "double_four"}
    if double_three:
        return {"legal": False, "win": False, "reason": "double_three"}
    return {"legal": True, "win": False, "reason": "legal"}


def audit(corpus):
    results = []
    for case in corpus["cases"]:
        actual = current_outcome(case)
        results.append(
            {
                "id": case["id"],
                "rule": case["rule"],
                "kind": case["kind"],
                "expected": case["expected"],
                "actual": actual,
                "matches": actual == case["expected"],
            }
        )
    return results


def write_report(path, corpus, results):
    mismatches = [result for result in results if not result["matches"]]
    lines = [
        "# Initial Renju Corpus Audit",
        "",
        "This report captures the pre-change legacy behavior. It is generated before",
        "the rule implementation is changed and is retained as mismatch evidence.",
        "",
        f"Variant: `{corpus['variant']}`",
        f"Cases: {len(results)}; matched: {len(results) - len(mismatches)}; mismatched: {len(mismatches)}",
        "",
        "| Case | Rule | Kind | Expected | Legacy result |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in mismatches:
        expected = result["expected"]
        actual = result["actual"]
        lines.append(
            f"| {result['id']} | {result['rule']} | {result['kind']} | "
            f"{expected['reason']} (legal={expected['legal']}, win={expected['win']}) | "
            f"{actual['reason']} (legal={actual['legal']}, win={actual['win']}) |"
        )
    if not mismatches:
        lines.append("| None | - | - | - | - |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit legacy rules against the Renju corpus")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)

    corpus = load_corpus(args.corpus)
    results = audit(corpus)
    if args.report:
        write_report(args.report, corpus, results)
    mismatch_count = sum(not result["matches"] for result in results)
    print(f"cases={len(results)} mismatches={mismatch_count}")
    return 1 if mismatch_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
