import json
from pathlib import Path

import numpy as np
import pytest

from renju_rules import MoveOutcome, evaluate_move


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "renju" / "corpus.json"


def load_corpus():
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


def board_for(case, board_size):
    board = np.zeros((board_size, board_size), dtype=int)
    for row, column in case["black"]:
        board[row, column] = 1
    for row, column in case["white"]:
        board[row, column] = -1
    return board


def test_corpus_schema_covers_each_required_rule_kind():
    corpus = load_corpus()

    assert corpus["schemaVersion"] == "1.0.0"
    assert corpus["variant"] == "RIF-1998-line-rules-on-legacy-19x19"
    assert corpus["boardSize"] == 19
    assert len({case["id"] for case in corpus["cases"]}) == len(corpus["cases"])
    required_kinds = {"positive", "negative", "symmetry", "edge"}
    for rule in ("win", "overline", "double_three", "double_four", "blocked"):
        assert {
            case["kind"] for case in corpus["cases"] if case["rule"] == rule
        } >= required_kinds


@pytest.mark.parametrize("case", load_corpus()["cases"], ids=lambda case: case["id"])
def test_rif_variant_corpus(case):
    corpus = load_corpus()
    board = board_for(case, corpus["boardSize"])

    outcome = evaluate_move(board, *case["move"], case["player"])

    assert outcome.as_dict() == case["expected"]


@pytest.mark.parametrize(
    ("row", "column", "player", "reason"),
    [
        (-1, 0, 1, "outside"),
        (19, 0, 1, "outside"),
        (0, 19, -1, "outside"),
        (0, 0, 0, "invalid_player"),
    ],
)
def test_invalid_candidates_are_rejected(row, column, player, reason):
    outcome = evaluate_move(np.zeros((19, 19), dtype=int), row, column, player)

    assert outcome == MoveOutcome(legal=False, win=False, reason=reason)


def test_occupied_candidate_is_rejected_without_mutating_board():
    board = np.zeros((19, 19), dtype=int)
    board[4, 7] = -1
    original = board.copy()

    outcome = evaluate_move(board, 4, 7, 1)

    assert outcome == MoveOutcome(legal=False, win=False, reason="occupied")
    assert np.array_equal(board, original)


def test_board_shape_and_values_are_validated():
    with pytest.raises(ValueError, match="square"):
        evaluate_move(np.zeros((5, 6), dtype=int), 0, 0, 1)
    with pytest.raises(ValueError, match="values"):
        evaluate_move(np.full((5, 5), 7, dtype=int), 0, 0, 1)
