from datetime import datetime
from pathlib import Path

import numpy as np

from renju_rules import evaluate_move


class RecordingError(OSError):
    pass


class plane:
    def __init__(self, ondrive=False):
        self.p1919 = np.zeros((19, 19), dtype=int)
        self.ondrive = ondrive
        self.record = False
        self.f = None
        self.filepath = None
        self.p1919a = np.zeros((19, 19), dtype=bool)

    def WillWinInstant(self, x, y, d):
        return evaluate_move(self.p1919, x, y, d).win

    def checkemptydig(self, data, firsthand):
        result = np.zeros((19, 19), dtype=bool)
        for row in range(19):
            for column in range(19):
                result[row, column] = evaluate_move(
                    data, row, column, firsthand
                ).legal
        self.p1919a = result.copy()
        return result

    def startrecord(self, filepath):
        destination = Path(filepath).expanduser()
        self.record = False
        self.f = None
        self.filepath = None
        if not destination.is_dir():
            raise RecordingError(f"Recording directory is unavailable: {destination}")

        self.now = datetime.now()
        timestr = self.now.strftime("%Y%m%d-%H%M%S-%f")
        record_path = destination / f"{timestr}.txt"
        try:
            handle = record_path.open(mode="x", encoding="utf-8", newline="")
        except OSError as error:
            raise RecordingError(
                f"Cannot create recording in {destination}: {error}"
            ) from error

        self.f = handle
        self.filepath = str(record_path)
        self.record = True
        return self.filepath

    def addrecord(self, x, y):
        if not self.isrecording():
            raise RecordingError("Recording is not active")
        self.f.write(f"{y},{x},")
        self.f.flush()

    def closerecord(self):
        if self.isrecording():
            self.f.close()
            self.record = False
            self.now = datetime.now()

    def isrecording(self):
        return bool(self.record and self.f is not None and not self.f.closed)

    def change(self, y_cord, x_cord, data):
        outcome = evaluate_move(self.p1919, y_cord, x_cord, data)
        if not outcome.legal:
            return -2
        self.p1919[y_cord, x_cord] = data
        if self.isrecording():
            self.addrecord(x_cord, y_cord)
        if outcome.win:
            return data
        return 0 if self.checkenmty() else 2

    def checkenmty(self):
        return bool(np.any(self.p1919 == 0))

    def Humaninput(self, d):
        checked = False
        while not checked:
            print(f"{d}inputing")
            y = input("y")
            x = input("x")
            try:
                y = int(y)
                x = int(x)
            except ValueError:
                print("First hand re-enter" if d == 1 else "second hand re-enter")
                continue

            if x not in range(19) or y not in range(19):
                continue
            if d == 1:
                checked = bool(self.p1919a[y, x])
                if not checked:
                    print("First hand re-enter")
            else:
                checked = self.p1919[y, x] == 0
                if not checked:
                    print("second hand re-enter")
        return self.change(y, x, d)

    def MachineInput(self, y, x, d):
        return self.change(y, x, d)

    def checkwin(self, data, board):
        size = len(board)
        for row in range(size):
            for column in range(size):
                if board[row, column] != data:
                    continue
                for row_step, column_step in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    end_row = row + 4 * row_step
                    end_column = column + 4 * column_step
                    if not (0 <= end_row < size and 0 <= end_column < size):
                        continue
                    if all(
                        board[row + offset * row_step, column + offset * column_step]
                        == data
                        for offset in range(5)
                    ):
                        return True
        return False

    def print(self, data, bot=False):
        print("\n")
        print("   ", end=" ")
        for column in range(19):
            print(f"{column!s:2}", end=" ")
        print()
        for row_number, row in enumerate(data):
            print(f"{row_number}:".rjust(3), end=" ")
            for value in row:
                if bot:
                    print("O" if value else "X", end=" ")
                elif value == 0:
                    print("[]", end=" ")
                elif value == 1:
                    print(" O", end=" ")
                else:
                    print(" X", end=" ")
            print()

    def __del__(self):
        handle = getattr(self, "f", None)
        if handle is not None and not handle.closed:
            handle.close()
