"""State space for three-player gambler's ruin.

A state is a chip split (x1, x2, x3) with x1 + x2 + x3 = N. A state is live
when every xi >= 1, which gives n = (N - 1)(N - 2)/2 live states. Live states
are ordered lexicographically by (x1, x2). This file is the only place that
maps states to matrix indices.
"""
import numpy as np

# The six moves: (a, b) means player a takes one chip from player b.
MOVES = [(a, b) for a in range(3) for b in range(3) if a != b]


class StateSpace:
    def __init__(self, N):
        if N < 3:
            raise ValueError("need N >= 3 for a live state to exist")
        self.N = N
        x1, x2 = [], []
        for a in range(1, N - 1):
            for b in range(1, N - a):  # keeps x3 = N - a - b >= 1
                x1.append(a)
                x2.append(b)
        self.x1 = np.array(x1)
        self.x2 = np.array(x2)
        self.x3 = N - self.x1 - self.x2
        self.n = len(x1)
        # lookup[x1, x2] = index of the live state (x1, x2, N - x1 - x2), else -1
        self.lookup = -np.ones((N + 1, N + 1), dtype=np.int64)
        self.lookup[self.x1, self.x2] = np.arange(self.n)

    def coords(self):
        """Array of shape (n, 3): row i is the state with index i."""
        return np.stack([self.x1, self.x2, self.x3], axis=1)

    def index(self, x):
        """Index of a live state x = (x1, x2, x3)."""
        x1, x2, x3 = x
        if x1 + x2 + x3 != self.N or min(x) < 1:
            raise ValueError(f"{x} is not a live state for N = {self.N}")
        return int(self.lookup[x1, x2])

    def state(self, i):
        return (int(self.x1[i]), int(self.x2[i]), int(self.x3[i]))
