"""The linear system (I - Q) u = b for three-player gambler's ruin.

Q[x, y] = 1/6 when y is a live state one move from x. A move from x that lands
on a state with a zero coordinate is a bust; those moves feed the right-hand
side b through the boundary value f at the landing state:

    b[x] = sum over busting moves x -> y of (1/6) * f(y)

Only one coordinate can drop per round, so the landing state has exactly one
zero coordinate.

Order labels: "ijk" (players 1, 2, 3) means i is out first, j second, k wins.
"""
import itertools

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from .states import MOVES, StateSpace


def _neighbors(S, a, b):
    """Coordinates after player a takes a chip from player b, for every state."""
    X = S.coords().copy()
    X[:, a] += 1
    X[:, b] -= 1
    return X


def build_A(S):
    """A = I - Q as a CSR matrix (symmetric positive definite)."""
    rows, cols = [np.arange(S.n)], [np.arange(S.n)]
    vals = [np.ones(S.n)]
    for a, b in MOVES:
        Y = _neighbors(S, a, b)
        live = Y.min(axis=1) >= 1
        rows.append(np.arange(S.n)[live])
        cols.append(S.lookup[Y[live, 0], Y[live, 1]])
        vals.append(np.full(live.sum(), -1.0 / 6.0))
    return sp.csr_matrix(
        (np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
        shape=(S.n, S.n),
    )


def boundary_rhs(S, f):
    """b[x] = sum over busting moves of f(landing state) / 6.

    f takes an integer array Y of shape (m, 3) of landing states and returns m values.
    """
    b = np.zeros(S.n)
    for a, c in MOVES:
        Y = _neighbors(S, a, c)
        bust = Y.min(axis=1) == 0
        b[bust] += f(Y[bust]) / 6.0
    return b


def rhs_out_first(S, i):
    """P(player i is out first). i is 0, 1 or 2."""
    return boundary_rhs(S, lambda Y: (Y[:, i] == 0).astype(float))


def rhs_order(S, i, j, k):
    """P(i out first, j out second, k wins): boundary value y_k / N where y_i = 0."""
    return boundary_rhs(S, lambda Y: (Y[:, i] == 0) * Y[:, k] / S.N)


def rhs_win(S, i):
    """P(player i wins the tournament): boundary value y_i / N."""
    return boundary_rhs(S, lambda Y: Y[:, i] / S.N)


def rhs_rounds(S):
    """Expected rounds until the first elimination: A t = 1."""
    return np.ones(S.n)


def solve(A, b):
    """Reference direct solve (SuperLU). Not a benchmark."""
    return spla.splu(A.tocsc()).solve(b)


def label(order):
    return "".join(str(p + 1) for p in order)


def order_probabilities(S, A=None):
    """All six elimination-order probabilities at every state from ONE solve.

    Solves for u_123 once, then uses relabeling: P_x(ijk) = u_123(x_i, x_j, x_k).
    Returns a dict like {"123": array of length n, ...}.
    """
    A = build_A(S) if A is None else A
    u123 = solve(A, rhs_order(S, 0, 1, 2))
    X = S.coords()
    out = {}
    for order in itertools.permutations(range(3)):
        i, j, k = order
        out[label(order)] = u123[S.lookup[X[:, i], X[:, j]]]
    return out
