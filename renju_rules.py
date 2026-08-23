from dataclasses import asdict, dataclass

import numpy as np


DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


@dataclass(frozen=True)
class MoveOutcome:
    legal: bool
    win: bool
    reason: str

    def as_dict(self):
        return asdict(self)


def _line_coordinates(size, row, column, row_step, column_step):
    start_row, start_column = row, column
    while (
        0 <= start_row - row_step < size
        and 0 <= start_column - column_step < size
    ):
        start_row -= row_step
        start_column -= column_step

    coordinates = []
    while 0 <= start_row < size and 0 <= start_column < size:
        coordinates.append((start_row, start_column))
        start_row += row_step
        start_column += column_step
    return coordinates


def _run_through(board, row, column, row_step, column_step):
    player = board[row, column]
    run = [(row, column)]
    scan_row, scan_column = row - row_step, column - column_step
    while (
        0 <= scan_row < len(board)
        and 0 <= scan_column < len(board)
        and board[scan_row, scan_column] == player
    ):
        run.insert(0, (scan_row, scan_column))
        scan_row -= row_step
        scan_column -= column_step

    scan_row, scan_column = row + row_step, column + column_step
    while (
        0 <= scan_row < len(board)
        and 0 <= scan_column < len(board)
        and board[scan_row, scan_column] == player
    ):
        run.append((scan_row, scan_column))
        scan_row += row_step
        scan_column += column_step
    return run


def _run_lengths(board, row, column):
    return [
        len(_run_through(board, row, column, row_step, column_step))
        for row_step, column_step in DIRECTIONS
    ]


def _four_signatures(board, row, column):
    signatures = set()
    size = len(board)
    anchor = (row, column)
    for direction_index, (row_step, column_step) in enumerate(DIRECTIONS):
        line = _line_coordinates(size, row, column, row_step, column_step)
        for extension_row, extension_column in line:
            if board[extension_row, extension_column] != 0:
                continue
            trial = board.copy()
            trial[extension_row, extension_column] = 1
            run = _run_through(
                trial, extension_row, extension_column, row_step, column_step
            )
            if len(run) != 5 or anchor not in run:
                continue
            four = frozenset(position for position in run if position != (extension_row, extension_column))
            signatures.add((direction_index, four))
    return signatures


def _straight_four_threes(
    board, anchor, extension, row_step, column_step, direction_index
):
    line = _line_coordinates(
        len(board), anchor[0], anchor[1], row_step, column_step
    )
    signatures = set()
    for start in range(1, len(line) - 4):
        run = line[start : start + 4]
        if anchor not in run or extension not in run:
            continue
        if not all(board[row, column] == 1 for row, column in run):
            continue
        before = line[start - 1]
        after = line[start + 4]
        if board[before] != 0 or board[after] != 0:
            continue
        three = frozenset(position for position in run if position != extension)
        if len(three) == 3:
            signatures.add((direction_index, three))
    return signatures


def _three_signatures(board, row, column, memo):
    signatures = set()
    anchor = (row, column)
    size = len(board)
    for direction_index, (row_step, column_step) in enumerate(DIRECTIONS):
        line = _line_coordinates(size, row, column, row_step, column_step)
        for extension in line:
            if board[extension] != 0:
                continue
            trial = board.copy()
            trial[extension] = 1
            threes = _straight_four_threes(
                trial,
                anchor,
                extension,
                row_step,
                column_step,
                direction_index,
            )
            if not threes:
                continue
            follow_up = _evaluate_black(board, extension[0], extension[1], memo)
            if follow_up.legal and not follow_up.win:
                signatures.update(threes)
    return signatures


def _evaluate_black(board, row, column, memo):
    key = (board.shape, board.tobytes(), row, column)
    if key in memo:
        return memo[key]

    candidate = board.copy()
    candidate[row, column] = 1
    run_lengths = _run_lengths(candidate, row, column)
    if 5 in run_lengths:
        outcome = MoveOutcome(True, True, "exact_five")
    elif any(length > 5 for length in run_lengths):
        outcome = MoveOutcome(False, False, "overline")
    elif len(_four_signatures(candidate, row, column)) >= 2:
        outcome = MoveOutcome(False, False, "double_four")
    elif len(_three_signatures(candidate, row, column, memo)) >= 2:
        outcome = MoveOutcome(False, False, "double_three")
    else:
        outcome = MoveOutcome(True, False, "legal")
    memo[key] = outcome
    return outcome


def _validated_board(board):
    candidate = np.asarray(board)
    if candidate.ndim != 2 or candidate.shape[0] != candidate.shape[1]:
        raise ValueError("board must be a square matrix")
    if not np.isin(candidate, (-1, 0, 1)).all():
        raise ValueError("board values must be -1, 0, or 1")
    return candidate


def evaluate_move(board, row, column, player):
    board = _validated_board(board)
    if player not in (-1, 1):
        return MoveOutcome(False, False, "invalid_player")
    if not isinstance(row, (int, np.integer)) or not isinstance(
        column, (int, np.integer)
    ):
        return MoveOutcome(False, False, "outside")
    if not (0 <= row < len(board) and 0 <= column < len(board)):
        return MoveOutcome(False, False, "outside")
    if board[row, column] != 0:
        return MoveOutcome(False, False, "occupied")

    if player == 1:
        return _evaluate_black(board, row, column, {})

    candidate = board.copy()
    candidate[row, column] = -1
    win = any(length >= 5 for length in _run_lengths(candidate, row, column))
    return MoveOutcome(True, win, "white_five_or_more" if win else "legal")
