import itertools

import numpy as np

from gr.matrix import label, order_probabilities
from gr.montecarlo import simulate
from gr.states import StateSpace


def test_montecarlo_agrees_with_solve():
    """10^5 simulated games from (5,3,2): every probability within 4 standard errors."""
    start, games = (5, 3, 2), 100_000
    first, second = simulate(start, games, seed=221)
    S = StateSpace(sum(start))
    P = order_probabilities(S)
    x = S.index(start)
    for i, j, k in itertools.permutations(range(3)):
        p = P[label((i, j, k))][x]
        phat = np.mean((first == i) & (second == j))
        se = np.sqrt(p * (1 - p) / games)
        assert abs(phat - p) < 4 * se, (label((i, j, k)), phat, p)
