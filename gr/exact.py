"""Exact rational solves for small N, written independently of matrix.py.

Builds the same system with Fractions in plain loops and solves it by Gaussian
elimination, so it can catch bugs in the vectorized float code.
"""
from fractions import Fraction

from .states import MOVES, StateSpace


def exact_solve(N, f=None, rhs_ones=False):
    """Solve (I - Q) u = b exactly. Returns {state: Fraction}.

    f(y) gives the boundary value at a landing state y (a tuple with one zero),
    or set rhs_ones=True for the expected-rounds system A t = 1.
    """
    S = StateSpace(N)
    states = [S.state(i) for i in range(S.n)]
    pos = {s: i for i, s in enumerate(states)}
    n = len(states)
    M = [[Fraction(0)] * (n + 1) for _ in range(n)]
    sixth = Fraction(1, 6)
    for s in states:
        r = pos[s]
        M[r][r] += 1
        if rhs_ones:
            M[r][n] = Fraction(1)
        for a, c in MOVES:
            y = list(s)
            y[a] += 1
            y[c] -= 1
            y = tuple(y)
            if y in pos:
                M[r][pos[y]] -= sixth
            elif not rhs_ones:
                M[r][n] += sixth * f(y)
    for col in range(n):
        piv = next(r for r in range(col, n) if M[r][col] != 0)
        M[col], M[piv] = M[piv], M[col]
        p = M[col][col]
        M[col] = [v / p for v in M[col]]
        for r in range(n):
            if r != col and M[r][col] != 0:
                fac = M[r][col]
                M[r] = [vr - fac * vc for vr, vc in zip(M[r], M[col])]
    return {s: M[pos[s]][n] for s in states}


def exact_order(N, i, j, k):
    """Exact P(i out first, j out second, k wins) at every state."""
    return exact_solve(N, lambda y: Fraction(y[k], N) if y[i] == 0 else Fraction(0))


def exact_out_first(N, i):
    return exact_solve(N, lambda y: Fraction(1) if y[i] == 0 else Fraction(0))
