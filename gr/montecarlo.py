"""Vectorized Monte Carlo simulation of the full game, used only as a cross-check."""
import numpy as np

PAIRS = np.array([(a, b) for a in range(3) for b in range(3) if a != b])


def simulate(start, games, seed=0):
    """Play `games` games from `start`. Returns (first_out, second_out) as arrays of 0, 1, 2."""
    rng = np.random.default_rng(seed)
    X = np.tile(np.array(start, dtype=np.int64), (games, 1))
    first = -np.ones(games, dtype=np.int64)
    second = -np.ones(games, dtype=np.int64)
    rows = np.arange(games)
    while True:
        alive = (X > 0).sum(axis=1)
        three = alive == 3
        two = alive == 2
        if not (three.any() or two.any()):
            break
        # Three alive: pick one of the 6 ordered pairs uniformly.
        idx = np.flatnonzero(three)
        if idx.size:
            p = PAIRS[rng.integers(0, 6, idx.size)]
            X[idx, p[:, 0]] += 1
            X[idx, p[:, 1]] -= 1
        # Two alive: the two survivors flip a fair coin.
        idx = np.flatnonzero(two)
        if idx.size:
            order = np.argsort(X[idx] == 0, axis=1, kind="stable")  # survivors first
            s0, s1 = order[:, 0], order[:, 1]
            coin = rng.integers(0, 2, idx.size).astype(bool)
            win = np.where(coin, s0, s1)
            lose = np.where(coin, s1, s0)
            X[idx, win] += 1
            X[idx, lose] -= 1
        # Record eliminations that just happened.
        zero = X == 0
        n_out = zero.sum(axis=1)
        new_first = (first < 0) & (n_out >= 1)
        first[new_first] = np.argmax(zero[new_first], axis=1)
        new_second = (second < 0) & (n_out >= 2)
        z2 = zero[new_second].copy()
        z2[np.arange(z2.shape[0]), first[new_second]] = False
        second[new_second] = np.argmax(z2, axis=1)
    return first, second
