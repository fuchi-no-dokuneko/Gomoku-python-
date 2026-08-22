import argparse
import random
import sys

from RandomMachine import RandomMachine
from plane import RecordingError, plane


def play_random_game(record_dir, seed=1):
    board = plane()
    players = {
        1: RandomMachine(random.Random(seed)),
        -1: RandomMachine(random.Random(seed + 1)),
    }
    game_state = 0
    move_count = 0
    board.startrecord(record_dir)
    try:
        while game_state == 0:
            player = 1 if move_count % 2 == 0 else -1
            available = board.checkemptydig(board.p1919, player)
            move = players[player].InputData__Available(available)
            if move is None:
                game_state = 2
                break
            game_state = board.MachineInput(*move, player)
            if game_state == -2:
                raise RuntimeError(f"Machine selected an illegal move: {move}")
            move_count += 1
    finally:
        board.closerecord()
    return board, game_state, move_count


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Play and record a seeded random Gomoku game"
    )
    parser.add_argument("--record-dir", required=True)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args(argv)

    try:
        board, game_state, move_count = play_random_game(args.record_dir, args.seed)
    except (RecordingError, RuntimeError) as error:
        print(f"Game failed: {error}", file=sys.stderr)
        return 2
    print(
        f"Game complete: state={game_state} moves={move_count} record={board.filepath}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
