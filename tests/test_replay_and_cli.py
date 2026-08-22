import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pytest

from replay import ReplayError, load_moves, replay_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _cli_command(script, *arguments):
    command = [sys.executable]
    if os.environ.get("COVER_REAL_SUBPROCESSES") == "1":
        command.extend(["-m", "coverage", "run", "--parallel-mode"])
    command.extend([script, *arguments])
    return command


def _winning_record():
    return "0,0,1,0,0,1,1,1,0,2,1,2,0,3,1,3,0,4,"


def test_valid_legacy_record_replays_to_the_same_terminal_board(tmp_path):
    record = tmp_path / "legacy.txt"
    record.write_text(_winning_record(), encoding="utf-8")

    board, state, move_count = replay_file(record, root=tmp_path)

    assert state == 1
    assert move_count == 9
    assert np.array_equal(board.p1919[0, :5], np.ones(5, dtype=int))


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("0,0,1", "coordinate pairs"),
        ("0,0,19,1,", "outside"),
        ("0,0,1,1,0,0,", "reuses occupied"),
        ("0,0,one,1,", "non-integer"),
    ],
)
def test_malformed_record_is_rejected_before_replay(tmp_path, payload, message):
    record = tmp_path / "bad.txt"
    record.write_text(payload, encoding="utf-8")

    with pytest.raises(ReplayError, match=message):
        replay_file(record, root=tmp_path)


def test_replay_cannot_escape_selected_root(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text(_winning_record(), encoding="utf-8")
    link = allowed / "record.txt"
    link.symlink_to(outside)

    with pytest.raises(ReplayError, match="escapes"):
        load_moves(link, root=allowed)


def test_seeded_real_machines_finish_record_and_replay_in_subprocess(tmp_path):
    game = subprocess.run(
        _cli_command("game.py", "--record-dir", str(tmp_path), "--seed", "7"),
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    assert game.returncode == 0, game.stderr
    assert "Game complete:" in game.stdout

    records = list(tmp_path.glob("*.txt"))
    assert len(records) == 1
    replay = subprocess.run(
        _cli_command("replay.py", str(records[0]), "--root", str(tmp_path)),
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    assert replay.returncode == 0, replay.stderr
    assert "Replay complete:" in replay.stdout


def test_interrupted_game_closes_a_real_partial_record(tmp_path):
    process = subprocess.Popen(
        _cli_command("game.py", "--record-dir", str(tmp_path), "--seed", "17"),
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 5
    while not list(tmp_path.glob("*.txt")) and time.monotonic() < deadline:
        time.sleep(0.02)
    process.send_signal(signal.SIGINT)
    _, stderr = process.communicate(timeout=10)

    assert process.returncode != 0
    assert "KeyboardInterrupt" in stderr
    record = next(tmp_path.glob("*.txt"))
    with record.open("a", encoding="utf-8") as handle:
        handle.write("")
    fields = record.read_text(encoding="utf-8").split(",")
    assert (len(fields) - 1) % 2 == 0


def test_human_input_parsing_runs_through_real_stdin(tmp_path):
    command = (
        "from plane import plane; "
        "b=plane(); b.checkemptydig(b.p1919,1); "
        "print('state=' + str(b.Humaninput(1)))"
    )
    run = subprocess.run(
        [sys.executable, "-c", command],
        cwd=PROJECT_ROOT,
        input="bad\n0\n0\n0\n",
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert run.returncode == 0, run.stderr
    assert "First hand re-enter" in run.stdout
    assert "state=0" in run.stdout
