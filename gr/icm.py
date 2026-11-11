"""The Independent Chip Model (Malmuth-Harville) for three players.

Player k wins with probability x_k / N; among the other two, j takes 2nd with probability
x_j / (N - x_k). Order labels are the same as in gr.matrix: "ijk" means i is out first (3rd place),
j is out second (2nd place) and k wins (1st place).

Equity identity. Place probabilities sum to 1 and P(1st) = x / N in both the ICM and the exact chain,
so the 2nd- and 3rd-place errors are negatives of each other. Hence for payouts (w1, w2, w3) the equity
error is (w2 - w3) * (P_ICM(2nd) - P(2nd)).
"""
import itertools

import numpy as np

ORDERS = ["123", "132", "213", "231", "312", "321"]


def icm_orders(X):
    """X has shape (m, 3), one row of stacks per state. Returns {"ijk": array of shape (m,)}."""
    X = np.asarray(X, dtype=float)
    N = X.sum(axis=1)
    out = {}
    for i, j, k in itertools.permutations(range(3)):
        out[f"{i + 1}{j + 1}{k + 1}"] = (X[:, k] / N) * X[:, j] / (N - X[:, k])
    return out


def place_probabilities(P, player):
    """Rows P(1st), P(2nd), P(3rd) for player 0, 1 or 2, from a dict of six order arrays."""
    p = str(player + 1)
    first = sum(v for o, v in P.items() if o[2] == p)   # the player wins
    second = sum(v for o, v in P.items() if o[1] == p)  # the player is out second
    third = sum(v for o, v in P.items() if o[0] == p)   # the player is out first
    return np.stack([first, second, third])


def equity(places, payouts):
    """Prize equity w1 P(1st) + w2 P(2nd) + w3 P(3rd); places has shape (3,) or (3, m)."""
    w1, w2, w3 = payouts
    return w1 * places[0] + w2 * places[1] + w3 * places[2]
