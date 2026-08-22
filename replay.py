import argparse
import csv
import sys
from pathlib import Path

from plane import plane


class ReplayError(ValueError):
    pass


def _resolve_record_path(filepath, root=None):
    path = Path(filepath).expanduser().resolve(strict=True)
    if not path.is_file():
        raise ReplayError(f"Replay path is not a file: {path}")

    if root is not None:
        allowed_root = Path(root).expanduser().resolve(strict=True)
        if not allowed_root.is_dir():
            raise ReplayError(f"Replay root is not a directory: {allowed_root}")
        if not path.is_relative_to(allowed_root):
            raise ReplayError(f"Replay path escapes the selected root: {path}")
    return path


def load_moves(filepath, root=None):
    try:
        path = _resolve_record_path(filepath, root)
        with path.open(newline="", encoding="utf-8") as csvfile:
            rows = list(csv.reader(csvfile, delimiter=",", strict=True))
    except (OSError, csv.Error) as error:
        raise ReplayError(f"Cannot read replay: {error}") from error

    if len(rows) != 1:
        raise ReplayError("Replay must contain exactly one CSV row")

    fields = rows[0]
    if fields and fields[-1] == "":
        fields.pop()
    if not fields or len(fields) % 2:
        raise ReplayError("Replay must contain complete y,x coordinate pairs")

    moves = []
    occupied = set()
    for index in range(0, len(fields), 2):
        try:
            move = int(fields[index]), int(fields[index + 1])
        except ValueError as error:
            raise ReplayError(
                f"Move {index // 2 + 1} has a non-integer coordinate"
            ) from error
        if any(value not in range(19) for value in move):
            raise ReplayError(
                f"Move {index // 2 + 1} is outside the 19x19 board: {move}"
            )
        if move in occupied:
            raise ReplayError(f"Move {index // 2 + 1} reuses occupied position: {move}")
        occupied.add(move)
        moves.append(move)
    return moves


def replay_moves(moves):
    board = plane()
    game_state = 0
    for index, (y, x) in enumerate(moves):
        if game_state != 0:
            raise ReplayError(f"Move {index + 1} appears after the game ended")
        player = 1 if index % 2 == 0 else -1
        if player == 1:
            board.checkemptydig(board.p1919, player)
        game_state = board.MachineInput(y, x, player)
        if game_state == -2:
            raise ReplayError(
                f"Move {index + 1} is illegal for player {player}: {(y, x)}"
            )
    return board, game_state


def replay_file(filepath, root=None):
    moves = load_moves(filepath, root)
    board, game_state = replay_moves(moves)
    return board, game_state, len(moves)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate and replay a Gomoku record")
    parser.add_argument("record")
    parser.add_argument("--root", help="Restrict the record to this directory")
    parser.add_argument("--print-board", action="store_true")
    args = parser.parse_args(argv)

    try:
        board, game_state, move_count = replay_file(args.record, args.root)
    except ReplayError as error:
        print(f"Replay failed: {error}", file=sys.stderr)
        return 2

    if args.print_board:
        board.print(board.p1919)
    print(f"Replay complete: moves={move_count} state={game_state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
