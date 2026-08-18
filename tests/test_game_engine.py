import os

import numpy as np

from RandomMachine import test as RandomMachine
from plane import plane


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


def test_recording_lifecycle_writes_moves(tmp_path):
    board = plane()
    board.startrecord(str(tmp_path) + os.sep)

    assert board.isrecording()
    assert board.MachineInput(2, 3, -1) == 0
    record_path = board.filepath
    board.closerecord()

    assert not board.isrecording()
    assert open(record_path, encoding="utf-8").read() == "2,3,"
