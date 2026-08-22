import random

import numpy as np


class RandomMachine:
    def __init__(self, rng=None):
        self._rng = rng or random
        self.EmptySpaceList = []
        self.resulty = None
        self.resultx = None

    def InputData__Available(self, data):
        available = np.asarray(data, dtype=bool)
        self.EmptySpaceList = [tuple(position) for position in np.argwhere(available)]
        return self.makedecision()

    def makedecision(self):
        if not self.EmptySpaceList:
            self.resulty = None
            self.resultx = None
            return None

        self.resulty, self.resultx = self._rng.choice(self.EmptySpaceList)
        return self.resulty, self.resultx


# Preserve the original public class name used by the existing scripts.
test = RandomMachine
