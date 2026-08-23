import numpy as np

from datetime import datetime
from pathlib import Path

from renju_rules import evaluate_move


class RecordingError(OSError):
    pass


class plane:
    def WillWinInstant(self, x, y, d):
        return evaluate_move(self.p1919, x, y, d).win

    def checkemptydig(self, data, firsthand):
        result = np.full([19, 19], True)
        for i in range(len(result)):
            for j in range(len(result[i])):
                result[i, j] = evaluate_move(data, i, j, firsthand).legal
        self.p1919a = np.copy(result)
        return result

    def extractarray(self, i, j, data, d):
        tem = np.copy(data)
        tem[i, j] = d
        HorzontalArray = []
        VerticalArray = []
        PosSlopeArray = []
        NegSlopeArray = []
        x = 0 if j < i else j - i
        y = 0 if j > i else i - j
        pcounter = 0
        counter = 0
        while x in range(19) and y in range(19):
            NegSlopeArray.append(tem[y, x])
            if y == i and x == j:
                ncounter = counter
            y += 1
            counter += 1
            x += 1
        # print(NegSlopeArray)
        e = 18 - j
        x = 0 if e >= i else j - (18 - i)
        y = 18 if e <= i else i + j
        counter = 0
        while x in range(19) and y in range(19):
            PosSlopeArray.append(tem[y, x])
            if y == i and x == j:
                pcounter = counter
            counter += 1
            x += 1
            y -= 1
        # print(PosSlopeArray)
        for k in range(19):
            HorzontalArray.append(tem[i, k])
            VerticalArray.append(tem[k, j])
        return [HorzontalArray, j, VerticalArray, i, PosSlopeArray, pcounter, NegSlopeArray, ncounter]

    def stopmorefive(self, a, d):
        result = self.stopmorefivescb(a[0], a[1], d) or self.stopmorefivescb(a[2], a[3], d) or self.stopmorefivescb(
            a[4], a[5],
            d) or self.stopmorefivescb(a[6],
                                       a[7], d)
        return result

    def stopmorefivescb(self, data, j, d):
        p = 0
        result = 0
        tem = data
        counter1 = 0  # near same chess
        counterL = 0  # left same chess one empty space
        counterR = 0  # right same chess after space
        temlen = len(tem)
        LfirstSpace = 0
        RfirstSpace = 0
        while j + p in range(temlen):
            if tem[j + p] == d:
                counter1 += 1
                p += 1
            else:
                break
        if j + p in range(temlen):
            if tem[j + p] == 0:
                RfirstSpace = p
        p = -1
        while j + p in range(temlen):
            if tem[j + p] == d:
                counter1 += 1
                p -= 1
            else:
                break
        if j + p in range(temlen):
            if tem[j + p] == 0:
                LfirstSpace = p
        return True if counter1 > 5 else False

    def doublelivethree(self, a, d):

        result1 = self.livethree(a[0], a[1], d) + self.livethree(a[2], a[3], d) + self.livethree(a[4], a[5],
                                                                                                 d) + self.livethree(
            a[6], a[7], d)

        return True if result1 == 2 else False

    def livethree(self, data, j, d):
        result = 0
        tem = data
        counter1 = 0  # near same chess
        counterL = 0  # left same chess one empty space
        counterR = 0  # right same chess after space
        temlen = len(tem)
        LfirstSpace = 0
        RfirstSpace = 0
        LSecondSpace = 0
        RSecondSpace = 0

        # main count LR empty count
        p = 0
        while j + p in range(temlen):
            if tem[j + p] == d:
                counter1 += 1
                p += 1
            else:
                break
        if j + p in range(temlen):
            if tem[j + p] == 0:
                RfirstSpace = p
        p = -1
        while j + p in range(temlen):
            if tem[j + p] == d:
                counter1 += 1
                p -= 1
            else:
                break
        if j + p in range(temlen):
            if tem[j + p] == 0:
                LfirstSpace = p
        # Second Count
        if LfirstSpace != 0:
            p = LfirstSpace - 1
            while j + p in range(temlen):
                if tem[j + p] == d:
                    counterL += 1
                    p -= 1
                else:
                    break
            if j + p in range(temlen):
                if tem[j + p] == 0:
                    LSecondSpace = p
        if RfirstSpace != 0:
            p = RfirstSpace + 1
            while j + p in range(temlen):
                if tem[j + p] == d:
                    counterR += 1
                    p += 1
                else:
                    break
            if j + p in range(temlen):
                if tem[j + p] == 0:
                    RSecondSpace = p
        # determine is it live three
        if counter1 + counterR == 3 or counter1 + counterL == 3:
            if counter1 == 3:  # check X[]OOO[]X or [][]OOO[][]
                if RfirstSpace != 0 and LfirstSpace != 0:
                    if LSecondSpace != 0 or RSecondSpace != 0:
                        result = 1
            elif counter1 + counterL == 3:
                if LfirstSpace != 0 and RfirstSpace != 0 and LSecondSpace != 0:
                    result = 1
            elif counter1 + counterR == 3:
                if RfirstSpace != 0 and LfirstSpace != 0 and RSecondSpace != 0:
                    result = 1
        # print(LSecondSpace,counterL,LfirstSpace,counter1,RfirstSpace,counterR,RSecondSpace)
        # print(result)
        return result

    def doubledeadfour(self, a, d):
        result = self.deadfour(a[0], a[1], d) + self.deadfour(a[2], a[3], d) + self.deadfour(a[4], a[5],
                                                                                             d) + self.deadfour(a[6],
                                                                                                                a[7], d)
        return True if result == 2 else False

    def deadfour(self, data, j, d):
        result = 0
        result = 0
        tem = data
        counter1 = 0  # near same chess
        counterL = 0  # left same chess one empty space
        counterR = 0  # right same chess after space
        temlen = len(tem)
        LfirstSpace = 0
        RfirstSpace = 0
        LSecondSpace = 0
        RSecondSpace = 0

        # main count LR empty count
        p = 0
        while j + p in range(temlen):
            if tem[j + p] == d:
                counter1 += 1
                p += 1
            else:
                break
        if j + p in range(temlen):
            if tem[j + p] == 0:
                RfirstSpace = p
        p = -1
        while j + p in range(temlen):
            if tem[j + p] == d:
                counter1 += 1
                p -= 1
            else:
                break
        if j + p in range(temlen):
            if tem[j + p] == 0:
                LfirstSpace = p
        # Second Count
        if LfirstSpace != 0:
            p = LfirstSpace - 1
            while j + p in range(temlen):
                if tem[j + p] == d:
                    counterL += 1
                    p -= 1
                else:
                    break
            if j + p in range(temlen):
                if tem[j + p] == 0:
                    LSecondSpace = p
        if RfirstSpace != 0:
            p = RfirstSpace + 1
            while j + p in range(temlen):
                if tem[j + p] == d:
                    counterR += 1
                    p += 1
                else:
                    break
            if j + p in range(temlen):
                if tem[j + p] == 0:
                    RSecondSpace = p
        if counter1 + counterL == 4 or counter1 + counterR == 4:
            if counter1 == 4:
                if LfirstSpace == 0 or RfirstSpace == 0:
                    if LfirstSpace != 0 or RfirstSpace != 0:
                        result = 1
            elif counter1 + counterR == 4:
                if RfirstSpace != 0 and (LfirstSpace == 0 or RSecondSpace == 0):
                    result = 1
            elif counter1 + counterL == 4:
                if LfirstSpace != 0 and (RfirstSpace == 0 or LSecondSpace == 0):
                    result = 1
        return result

    def __init__(self,ondrive =False):  # initslize a game board
        self.p1919 = np.full([19, 19], fill_value=0, dtype=int)
        self.ondrive = ondrive
        self.record = False
        self.f = None
        self.filepath = None
        self.p1919a = np.full([19, 19], fill_value=0, dtype=int)

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
            raise RecordingError(f"Cannot create recording in {destination}: {error}") from error

        self.f = handle
        self.filepath = str(record_path)
        self.record = True
        return self.filepath

    def addrecord(self, x, y):
        if not self.isrecording():
            raise RecordingError("Recording is not active")
        self.f.write(str(y) + "," + str(x) + ",")
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
        # try:
        if self.isrecording():
            self.addrecord(x_cord, y_cord)
        # except:
        pass
        if outcome.win:
            return data
        else:
            if self.checkenmty():
                return 0
            else:
                return 2
        # add a chest
        # check if it win

    def checkenmty(self):
        if 0 in self.p1919[:, :]:
            return True

    def Humaninput(self, d):

        checked = False
        if d == 1:
            while not (checked):
                print(str(d) + 'inputing')
                y = input("y")
                x = input("x")
                try:
                    y = int(y)
                    x = int(x)
                except:
                    print('First hand re-enter')
                    continue
                if x in range(19) and y in range(19):

                    if self.p1919a[y, x] == True:
                        checked = True
                    else:
                        print('First hand re-enter')
        else:
            while not (checked):
                print(str(d) + 'inputing')
                y = input("y")
                x = input("x")
                try:
                    y = int(y)
                    x = int(x)
                except:
                    print('second hand re-enter')
                    continue
                if x in range(19) and y in range(19):

                    if self.p1919[y, x] == 0:
                        checked = True
                    else:
                        print('second hand re-enter')
        return self.change(y, x, d)

    def MachineInput(self, y, x,d):

        return self.change(y, x, d)

    def checkwin(self, data, board):
        win = False
        for i in range(len(board)):  # stright line
            counter1 = 0
            counter2 = 0
            idex = 0
            while idex < len(board) and counter2 < 5 and counter1 < 5:
                if board[i, idex] == data:
                    counter1 += 1
                else:
                    counter1 = 0
                if board[idex, i] == data:
                    counter2 += 1
                else:
                    counter2 = 0
                idex += 1
            if counter1 >= 5 or counter2 >= 5:
                win = True

        for i in range(len(board) - 4):
            # slope
            counter1 = 0
            counter2 = 0
            idex = 0
            while idex < len(board) - i and counter2 < 5 and counter1 < 5:
                if board[idex, i + idex] == data:
                    counter1 += 1
                else:
                    counter1 = 0
                if board[i + idex, idex] == data:
                    counter2 += 1
                else:
                    counter2 = 0
                idex += 1
            if counter1 >= 5 or counter2 >= 5:
                win = True

        return win

    def print(self, data, bot=False):
        z = []
        for i in range(19):
            z.append(i)
        print('\n')
        print('   ', end=" ")
        for i in z:
            print('{:2}'.format(str(i)), end=" ")
        print()
        for i in data:
            print('{:3}'.format(str(z[0]) + ':'), end=" ")
            z.remove(z[0])
            for j in i:
                if bot == False:
                    if j == 0:
                        print(('{:2}'.format('[]')), end=" ")
                    elif j == 1:
                        print(' O', end=" ")
                    else:
                        print(' X', end=" ")
                else:
                    if j == True:
                        print('O', end=" ")
                    else:
                        print('X', end=" ")

            print()
    def __del__(self):
        handle = getattr(self, "f", None)
        if handle is not None and not handle.closed:
            handle.close()
