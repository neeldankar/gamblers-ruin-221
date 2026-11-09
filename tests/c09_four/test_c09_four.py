"""Chunk 9 acceptance tests: four-player gambler's ruin and the S3-lumped chain.

Model: chips (x1, x2, x3, x4), sum N. Each round one of the 12 ordered pairs (a, b) is chosen with
probability 1/12 and a takes one chip from b. Live states have every xi >= 1, so n = C(N-1, 3).
Spec: plan/c09_four_players.md. Skipped until gr/four.py exists.
Every expected number below was computed by an independent reference implementation.
"""
import itertools
import math
from fractions import Fraction

import numpy as np
import pytest
import scipy.sparse as sp
import scipy.sparse.linalg as spla

four = pytest.importorskip("gr.four")

from gr.matrix import build_A, rhs_out_first
from gr.states import StateSpace


def _solve(A, b):
    return spla.splu(sp.csc_matrix(A)).solve(b)


def _e2_e4(S):
    X = S.coords().astype(float)
    e2 = sum(X[:, i] * X[:, j] for i, j in itertools.combinations(range(4), 2))
    return X, e2, X.prod(axis=1)


def test_twelve_moves():
    assert sorted(four.MOVES4) == [(a, b) for a in range(4) for b in range(4) if a != b]


@pytest.mark.parametrize("N", [4, 5, 8, 13, 20])
def test_state_count_and_order(N):
    S = four.FourStateSpace(N)
    assert S.n == math.comb(N - 1, 3)
    X = S.coords()
    assert X.shape == (S.n, 4)
    assert np.all(X >= 1) and np.all(X.sum(axis=1) == N)
    keys = [tuple(int(v) for v in r[:3]) for r in X]
    assert keys == sorted(keys), "live states must be ordered lexicographically by (x1, x2, x3)"
    for i in [0, S.n // 2, S.n - 1]:
        assert S.index(S.state(i)) == i


@pytest.mark.parametrize("N", [6, 10, 20])
def test_matrix_structure(N):
    """A = I - Q is symmetric with unit diagonal, off-diagonals -1/12, at most 13 nonzeros per row,
    and Q row sums (12 - 3 * #{players holding one chip}) / 12."""
    S = four.FourStateSpace(N)
    A = sp.csr_matrix(four.build_A4(S))
    assert A.shape == (S.n, S.n)
    assert abs(A - A.T).max() == 0
    assert np.all(A.diagonal() == 1)
    assert np.diff(A.indptr).max() <= 13
    off = (A - sp.diags(A.diagonal())).tocsr()
    off.eliminate_zeros()
    assert np.allclose(off.data, -1 / 12, rtol=0, atol=1e-16)
    ones = (S.coords() == 1).sum(axis=1)
    qsum = -np.asarray(off.sum(axis=1)).ravel()
    assert np.max(np.abs(qsum - (12 - 3 * ones) / 12)) < 1e-15


def test_positive_definite_N10():
    S = four.FourStateSpace(10)
    ev = np.linalg.eigvalsh(four.build_A4(S).toarray())
    assert ev[0] > 0.2 and ev[-1] < 2


@pytest.mark.parametrize("N", [10, 20, 30])
def test_e2_identity(N):
    """E[change in x1 x2 x3 x4 per round] = -e2 / 6, so A (6 x1 x2 x3 x4) = e2 = sum_{i<j} xi xj."""
    S = four.FourStateSpace(N)
    A = four.build_A4(S)
    X, e2, e4 = _e2_e4(S)
    assert np.max(np.abs(A @ (6 * e4) - e2)) < 1e-10 * e2.max()
    assert np.max(np.abs(_solve(A, e2) - 6 * e4)) < 1e-11 * (6 * e4).max()


@pytest.mark.parametrize("N", [12, 20])
def test_win_probability_is_stack_over_N(N):
    S = four.FourStateSpace(N)
    A = four.build_A4(S)
    X = S.coords()
    for i in range(4):
        assert np.max(np.abs(_solve(A, four.rhs_win4(S, i)) - X[:, i] / N)) < 1e-12


@pytest.mark.parametrize("N", [9, 20])
def test_out_first_sums_to_one_and_permutes(N):
    S = four.FourStateSpace(N)
    A = four.build_A4(S)
    H = [_solve(A, four.rhs_out_first4(S, i)) for i in range(4)]
    assert np.max(np.abs(sum(H) - 1)) < 1e-12
    X = S.coords()
    for perm in [(1, 0, 2, 3), (3, 2, 1, 0), (2, 3, 0, 1)]:
        Xp = X[:, perm]
        idx = np.array([S.index(tuple(int(v) for v in r)) for r in Xp])
        for i in range(4):
            assert np.max(np.abs(H[i][idx] - H[perm[i]])) < 1e-12


def _exact_big_stack_out_first(N):
    """Independent loop-and-Fraction solve of P(player 4 out first) at every live state."""
    states = [s + (N - sum(s),) for s in itertools.product(range(1, N), repeat=3) if sum(s) <= N - 1]
    pos = {s: r for r, s in enumerate(states)}
    n = len(states)
    M = [[Fraction(0)] * (n + 1) for _ in range(n)]
    for s in states:
        r = pos[s]
        M[r][r] += 1
        for a in range(4):
            for c in range(4):
                if a != c:
                    y = list(s)
                    y[a] += 1
                    y[c] -= 1
                    y = tuple(y)
                    if y in pos:
                        M[r][pos[y]] -= Fraction(1, 12)
                    elif y[3] == 0:
                        M[r][n] += Fraction(1, 12)
    for col in range(n):
        piv = next(r for r in range(col, n) if M[r][col] != 0)
        M[col], M[piv] = M[piv], M[col]
        p = M[col][col]
        M[col] = [v / p for v in M[col]]
        for r in range(n):
            if r != col and M[r][col] != 0:
                f = M[r][col]
                M[r] = [v - f * w for v, w in zip(M[r], M[col])]
    return {s: M[pos[s]][n] for s in states}


@pytest.mark.parametrize("N, want", [(5, Fraction(1, 13)), (6, Fraction(2, 71)), (7, Fraction(38, 3203)),
                                     (8, Fraction(11017, 1975144))])
def test_big_stack_out_first_exact_rationals(N, want):
    """By hand for N = 5: from (1,1,1,2), 9 of 12 moves bust a 1-chip player, 3 move to a state like
    (2,1,1,1) where the answer g solves g = 3/12 + (2/12) g + (1/12) f and f = (3/12) g: f = 1/13."""
    exact = _exact_big_stack_out_first(N)
    assert exact[(1, 1, 1, N - 3)] == want
    S = four.FourStateSpace(N)
    h = _solve(four.build_A4(S), four.rhs_out_first4(S, 3))
    for s, v in exact.items():
        assert abs(h[S.index(s)] - float(v)) < 1e-15 + 1e-13 * float(v)
    assert abs(four.big_stack_out_first(N) / float(want) - 1) < 1e-13


@pytest.mark.parametrize("N", [8, 12, 20])
def test_lumped_space(N):
    L = four.LumpedSpace(N)
    assert L.n == {8: 11, 12: 41, 20: 204}[N]
    Y = L.coords()
    assert Y.shape == (L.n, 4)
    assert np.all(Y >= 1) and np.all(Y.sum(axis=1) == N)
    assert np.all(Y[:, 0] <= Y[:, 1]) and np.all(Y[:, 1] <= Y[:, 2])
    w = np.asarray(L.weights)
    assert set(np.unique(w)) <= {1, 3, 6}
    assert w.sum() == math.comb(N - 1, 3), "orbit sizes add up to the full state count"
    for r in [0, L.n - 1]:
        y = tuple(int(v) for v in Y[r])
        assert L.index(y) == r
        assert L.index((y[2], y[0], y[1], y[3])) == r, "index() sorts the first three coordinates"


@pytest.mark.parametrize("N", [8, 12, 20, 30])
def test_lumped_chain_matches_full_chain(N):
    """Lumping over players 1-3 is exact for P(player 4 out first), and diag(weights) A_L is symmetric."""
    L = four.LumpedSpace(N)
    AL, b = four.build_lumped(L)
    AL = sp.csr_matrix(AL)
    W = sp.diags(np.asarray(L.weights, dtype=float)) @ AL
    assert abs(W - W.T).max() < 1e-15
    u = _solve(AL, b)
    S = four.FourStateSpace(N)
    h4 = _solve(four.build_A4(S), four.rhs_out_first4(S, 3))
    full = np.array([h4[S.index(tuple(int(v) for v in y))] for y in L.coords()])
    assert np.max(np.abs(u - full)) < 1e-13


def test_lumped_symmetrized_is_spd_N12():
    L = four.LumpedSpace(12)
    AL, _ = four.build_lumped(L)
    d = np.sqrt(np.asarray(L.weights, dtype=float))
    Ssym = (np.diag(d) @ sp.csr_matrix(AL).toarray() @ np.diag(1 / d))
    assert np.max(np.abs(Ssym - Ssym.T)) < 1e-15
    assert np.linalg.eigvalsh((Ssym + Ssym.T) / 2)[0] > 0


@pytest.mark.parametrize("N, want", [(12, 5.568973643914e-04), (20, 3.022376155052e-05),
                                     (40, 5.753800975152e-07), (60, 5.661341422530e-08)])
def test_big_stack_out_first_values(N, want):
    """P(player 4 out first) from (1, 1, 1, N - 3)."""
    assert abs(four.big_stack_out_first(N) / want - 1) < 1e-9


def test_big_stack_decay_exponent():
    """Local slope log(P(40)/P(80)) / log 2 = 5.7192 for four players, against exactly 3 for three
    players from (1, 1, N - 2). Tiny probabilities: P(80) = 1.09e-8."""
    p40, p80 = four.big_stack_out_first(40), four.big_stack_out_first(80)
    assert abs(p80 / 1.092193169790e-08 - 1) < 1e-8
    slope4 = math.log(p40 / p80) / math.log(2)
    assert 5.71 < slope4 < 5.73
    p3 = {}
    for N in (40, 80):
        S = StateSpace(N)
        p3[N] = _solve(build_A(S), rhs_out_first(S, 2))[S.index((1, 1, N - 2))]
    slope3 = math.log(p3[40] / p3[80]) / math.log(2)
    assert abs(slope3 - 3) < 1e-3


@pytest.mark.parametrize("N", [20, 30])
def test_expected_rounds_bounds_and_no_product_formula(N):
    """A^{-1} >= 0 and e2 lies between 3N - 6 and 3N^2/8 on live states, so A^{-1} e2 = 6 e4 gives
    16 e4 / N^2 <= T <= 2 e4 / (N - 2) for T = A^{-1} 1. T is not a multiple of e4 (unlike three
    players, where T = 3 x1 x2 x3 / N): T / e4 varies by more than a factor of 2."""
    S = four.FourStateSpace(N)
    X, e2, e4 = _e2_e4(S)
    T = _solve(four.build_A4(S), np.ones(S.n))
    assert np.all(T >= 16 * e4 / N ** 2 - 1e-9)
    assert np.all(T <= 2 * e4 / (N - 2) + 1e-9)
    r = T / e4
    assert r.max() / r.min() > 2


def test_amg_cg_solves_four_player_system():
    """The experiment's iterative solver: pyamg smoothed aggregation as a CG preconditioner."""
    pyamg = pytest.importorskip("pyamg")
    S = four.FourStateSpace(40)
    A = sp.csr_matrix(four.build_A4(S))
    X, e2, e4 = _e2_e4(S)
    ml = pyamg.smoothed_aggregation_solver(A)
    u = ml.solve(e2, tol=1e-12, accel="cg", maxiter=200)
    assert np.max(np.abs(u - 6 * e4)) < 1e-9 * (6 * e4).max()
