import os
import random

import numpy as np
import pytest

from RandomMachine import RandomMachine
from plane import RecordingError, plane


def test_machine_input_detects_horizontal_win_and_rejects_occupied_cell():
    board = plane()

    for column in range(4):
        assert board.MachineInput(8, column, -1) == 0

    assert board.MachineInput(8, 4, -1) == -1
    assert board.MachineInput(8, 4, -1) == -2


def test_random_machine_uses_the_only_available_position():
    available = np.full((19, 19), False)
    available[4, 7] = True
    machine = RandomMachine()

    machine.InputData__Available(available)

    assert (machine.resulty, machine.resultx) == (4, 7)


def test_random_machine_returns_no_move_for_full_board():
    machine = RandomMachine(random.Random(3))

    assert machine.InputData__Available(np.zeros((19, 19), dtype=bool)) is None
    assert (machine.resulty, machine.resultx) == (None, None)


def test_recording_lifecycle_writes_moves(tmp_path):
    board = plane()
    board.startrecord(str(tmp_path) + os.sep)

    assert board.isrecording()
    assert board.MachineInput(2, 3, -1) == 0
    record_path = board.filepath
    board.closerecord()

    assert not board.isrecording()
    assert open(record_path, encoding="utf-8").read() == "2,3,"


def test_drive_backed_recording_uses_requested_mounted_directory(tmp_path):
    board = plane(ondrive=True)

    record_path = board.startrecord(tmp_path)
    moves = [
        (0, 0, 1),
        (1, 0, -1),
        (0, 1, 1),
        (1, 1, -1),
        (0, 2, 1),
        (1, 2, -1),
        (0, 3, 1),
        (1, 3, -1),
        (0, 4, 1),
    ]
    game_state = 0
    for y, x, player in moves:
        if player == 1:
            board.checkemptydig(board.p1919, player)
        game_state = board.MachineInput(y, x, player)
    board.closerecord()

    assert game_state == 1
    assert os.path.dirname(record_path) == str(tmp_path)
    assert open(record_path, encoding="utf-8").read() == (
        "0,0,1,0,0,1,1,1,0,2,1,2,0,3,1,3,0,4,"
    )


def test_unavailable_recording_directory_fails_without_open_handle(tmp_path):
    unavailable = tmp_path / "not-a-directory"
    unavailable.write_text("occupied", encoding="utf-8")
    board = plane(ondrive=True)

    with pytest.raises(RecordingError, match="unavailable"):
        board.startrecord(unavailable)

    assert not board.isrecording()
    assert board.f is None


def test_human_input_retries_invalid_and_forbidden_first_hand_moves(
    monkeypatch, capsys
):
    board = plane()
    board.checkemptydig(board.p1919, 1)
    board.p1919a[0, 0] = False
    answers = iter(["bad", "0", "19", "0", "0", "0", "1", "1"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    assert board.Humaninput(1) == 0
    assert board.p1919[1, 1] == 1
    output = capsys.readouterr().out
    assert output.count("First hand re-enter") == 2


def test_human_input_retries_invalid_and_occupied_second_hand_moves(
    monkeypatch, capsys
):
    board = plane()
    board.p1919[0, 0] = 1
    answers = iter(["bad", "0", "0", "0", "1", "1"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    assert board.Humaninput(-1) == 0
    assert board.p1919[1, 1] == -1
    output = capsys.readouterr().out
    assert "second hand re-enter" in output


def test_board_renderer_covers_human_and_availability_views(capsys):
    board = plane()
    board.p1919[0, 0] = 1
    board.p1919[0, 1] = -1

    board.print(board.p1919)
    board.print(np.eye(19, dtype=bool), bot=True)

    output = capsys.readouterr().out
    assert "[]" in output
    assert " O" in output
    assert " X" in output
    assert "O" in output
    assert "X" in output
