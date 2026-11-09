"""Chunk 10 (optional) acceptance tests, part 2: unequal skill (Bradley-Terry).

Each round an unordered pair {a, b} is chosen with probability 1/3 and a beats b with probability
s_a / (s_a + s_b). The chain is reversible with pi(x) = prod s_i^{x_i}, so S = D^{1/2} A D^{-1/2}
(D = diag(pi)) is symmetric although A is not. Skills used: s = (1, 1.5, 2).
Spec: plan/c10_extras.md. Skipped until gr/extras.py exists.
Every expected number below was computed by an independent reference implementation.
"""
import itertools
import math
from fractions import Fraction

import numpy as np
import pytest
import scipy.sparse as sp
import scipy.sparse.linalg as spla

extras = pytest.importorskip("gr.extras")

from gr.matrix import build_A, rhs_win
from gr.states import MOVES, StateSpace

SK = (1.0, 1.5, 2.0)


def _solve(A, b):
    return spla.splu(sp.csc_matrix(A)).solve(b)


def _bt(N, skills=SK):
    S = StateSpace(N)
    A = sp.csr_matrix(extras.build_A_bt(S, skills))
    lp = np.asarray(extras.log_pi(S, skills))
    return S, A, lp, sp.csr_matrix(extras.symmetrize_bt(A, lp))


def test_equal_skill_is_the_fair_game():
    S = StateSpace(30)
    assert abs(sp.csr_matrix(extras.build_A_bt(S, (1, 1, 1))) - build_A(S)).max() < 1e-16
    for i in range(3):
        assert np.max(np.abs(extras.rhs_win_bt(S, (1, 1, 1), i) - rhs_win(S, i))) < 1e-15


@pytest.mark.parametrize("N", [10, 40])
def test_matrix_entries(N):
    """Off-diagonal (x -> x + e_a - e_b) = -(1/3) s_a / (s_a + s_b); max |A - A^T| = (1/3)(2-1)/(2+1) = 1/9."""
    S, A, lp, _ = _bt(N)
    X = S.coords()
    assert np.all(A.diagonal() == 1)
    for x in [S.index((1, 1, N - 2)), S.index((N // 3, N // 3, N - 2 * (N // 3)))]:
        for a, b in MOVES:
            y = X[x].copy()
            y[a] += 1
            y[b] -= 1
            if y.min() >= 1:
                want = -(1 / 3) * SK[a] / (SK[a] + SK[b])
                assert abs(A[x, S.index(tuple(int(v) for v in y))] - want) < 1e-16
    assert abs(abs(A - A.T).max() - 1 / 9) < 1e-15


def test_log_pi():
    S, A, lp, _ = _bt(80)
    assert np.allclose(lp, S.coords() @ np.log(SK), rtol=0, atol=1e-12)
    assert abs((lp.max() - lp.min()) - 77 * math.log(2)) < 1e-10, "pi_max / pi_min = 2^(N - 3)"


@pytest.mark.parametrize("N", [20, 80])
def test_reversibility_and_symmetrized_matrix(N):
    """pi_x Q(x, y) = pi_y Q(y, x), so S is symmetric; its off-diagonals are -(1/3) sqrt(s_a s_b)/(s_a + s_b),
    three values 0.1571348403, 0.1632993162, 0.1649572198."""
    S, A, lp, Ssym = _bt(N)
    assert abs(Ssym - Ssym.T).max() < 1e-14 * abs(Ssym).max()
    off = (Ssym - sp.diags(Ssym.diagonal())).tocsr()
    off.eliminate_zeros()
    got = np.unique(np.round(-off.data, 10))
    assert np.allclose(got, [0.1571348403, 0.1632993162, 0.1649572198], atol=1e-10)
    C = A.tocoo()
    m = C.row != C.col
    left = lp[C.row[m]] + np.log(-C.data[m])
    At = A.T.tocsr()
    right = lp[C.col[m]] + np.log(-np.asarray(At[C.row[m], C.col[m]]).ravel())
    assert np.max(np.abs(left - right)) < 1e-12


def test_log_domain_symmetrization_survives_overflow():
    """With skills (1, 1.5, 1e20) at N = 40, pi itself overflows float64 (1e20^38), but S does not.
    (log pi reaches about 1750 here, so differences of log pi carry absolute error near 1e-13;
    hence the looser symmetry tolerance.)"""
    skills = (1.0, 1.5, 1e20)
    S, A, lp, Ssym = _bt(40, skills)
    with np.errstate(over="ignore"):
        assert not np.all(np.isfinite(np.exp(lp)))
    assert np.all(np.isfinite(Ssym.data))
    assert abs(Ssym - Ssym.T).max() < 1e-12


def test_same_spectrum_and_real_eigenvalues_N20():
    S, A, lp, Ssym = _bt(20)
    evA = np.linalg.eigvals(A.toarray())
    assert np.max(np.abs(evA.imag)) < 1e-10
    assert np.max(np.abs(np.sort(evA.real) - np.linalg.eigvalsh(Ssym.toarray()))) < 1e-10


@pytest.mark.parametrize("N, lam_min, cond2", [(20, 0.0608913, 24.1394), (40, 0.0371848, 39.8478), (80, 0.0312122, 47.5685)])
def test_spectrum_of_S(N, lam_min, cond2):
    """lambda_min(S) decreases toward the Gershgorin bound 1 - 2(0.15713 + 0.16330 + 0.16496) = 0.0292172
    and cond2(S) stays bounded (about 51 at N = 320): drift makes this chain easy for CG on S."""
    S, A, lp, Ssym = _bt(N)
    lo = spla.eigsh(Ssym.tocsc(), k=1, sigma=0, which="LM", return_eigenvectors=False)[0]
    hi = spla.eigsh(Ssym, k=1, which="LA", return_eigenvectors=False)[0]
    assert abs(lo / lam_min - 1) < 1e-5
    assert abs(hi / lo / cond2 - 1) < 1e-5
    gersh = 1 - 2 * (0.1571348403 + 0.1632993162 + 0.1649572198)
    assert abs(gersh - 0.0292172) < 1e-7 and lo > gersh


def test_p2_win():
    N = 50
    y = np.arange(N + 1)
    for sk, sj in [(1.0, 2.0), (2.0, 1.0), (1.5, 1.5), (1.0, 1.5)]:
        p = np.asarray(extras.p2_win(y, sk, sj, N), dtype=float)
        q = sk / (sk + sj)
        assert p[0] == 0 and abs(p[-1] - 1) < 1e-15
        assert np.max(np.abs(p[1:-1] - (q * p[2:] + (1 - q) * p[:-2]))) < 1e-15
        assert np.all(np.diff(p) > 0)
    assert np.allclose(extras.p2_win(y, 1.5, 1.5, N), y / N, rtol=0, atol=1e-15)
    # N = 2000: P(y) = (2^y - 1) / (2^N - 1) for the weaker player, (1 - 2^-y) / (1 - 2^-N) for the stronger.
    # A naive formula overflows (2^2000); a stable one gives these without inf or nan.
    big = np.asarray(extras.p2_win(np.array([1, 1000, 1999]), 1.0, 2.0, 2000), dtype=float)
    assert np.all(np.isfinite(big))
    assert 0 <= big[0] < 1e-300
    assert abs(big[1] / 2.0 ** -1000 - 1) < 1e-12
    assert abs(big[2] - 0.5) < 1e-15
    big = np.asarray(extras.p2_win(np.array([1, 1000, 1999]), 2.0, 1.0, 2000), dtype=float)
    assert np.all(np.isfinite(big))
    assert abs(big[0] - 0.5) < 1e-15 and abs(big[1] - 1) < 1e-15 and abs(big[2] - 1) < 1e-15


def _exact_bt_wins(N, skills):
    """Independent Fraction solve of P(player i wins) at every live state."""
    S = StateSpace(N)
    states = [S.state(r) for r in range(S.n)]
    pos = {s: r for r, s in enumerate(states)}
    n = len(states)

    def two_player(y, sk, sj):
        if sk == sj:
            return Fraction(y, N)
        r = sj / sk
        return (1 - r ** y) / (1 - r ** N)

    M = [[Fraction(0)] * (n + 3) for _ in range(n)]
    for s in states:
        row = pos[s]
        M[row][row] += 1
        for a, b in MOVES:
            p = Fraction(1, 3) * skills[a] / (skills[a] + skills[b])
            y = list(s)
            y[a] += 1
            y[b] -= 1
            y = tuple(y)
            if y in pos:
                M[row][pos[y]] -= p
            else:
                for i in range(3):
                    if i != b:
                        other = 3 - i - b
                        M[row][n + i] += p * two_player(y[i], skills[i], skills[other])
    for col in range(n):
        piv = next(r for r in range(col, n) if M[r][col] != 0)
        M[col], M[piv] = M[piv], M[col]
        pv = M[col][col]
        M[col] = [v / pv for v in M[col]]
        for r in range(n):
            if r != col and M[r][col] != 0:
                f = M[r][col]
                M[r] = [v - f * w for v, w in zip(M[r], M[col])]
    return S, states, {i: [M[pos[s]][n + i] for s in states] for i in range(3)}


def test_win_probabilities_exact_rationals_N7():
    skills = (Fraction(1), Fraction(3, 2), Fraction(2))
    S, states, exact = _exact_bt_wins(7, skills)
    A = extras.build_A_bt(S, SK)
    total = [sum(exact[i][r] for i in range(3)) for r in range(S.n)]
    assert all(t == 1 for t in total)
    for i in range(3):
        u = _solve(A, extras.rhs_win_bt(S, SK, i))
        assert np.max(np.abs(u - np.array([float(v) for v in exact[i]]))) < 1e-14


@pytest.mark.parametrize("N", [20, 60])
def test_win_probabilities_sum_to_one_and_favor_skill(N):
    S, A, lp, _ = _bt(N)
    W = np.column_stack([_solve(A, extras.rhs_win_bt(S, SK, i)) for i in range(3)])
    assert np.max(np.abs(W.sum(axis=1) - 1)) < 1e-12
    c = S.index((N // 3, N // 3, N - 2 * (N // 3)))
    assert W[c, 0] < W[c, 1] < W[c, 2]


def test_gmres_on_A_vs_cg_on_S_N80():
    """P(strongest wins) at N = 80. GMRES(30) on A to rtol 1e-10 is accurate (error 7e-10). CG on S to
    rtol 1e-10 converges in about 74 steps but its answer, mapped back by D^{-1/2}, is off by 0.33:
    the S-residual does not see errors at low-pi states. A direct solve of S, mapped back, is accurate,
    so the symmetrization itself is fine; the stopping test is the problem."""
    S, A, lp, Ssym = _bt(80)
    b = extras.rhs_win_bt(S, SK, 2)
    u = _solve(A, b)
    scale = np.abs(u).max()
    ug, info = spla.gmres(A, b, rtol=1e-10, atol=0.0, restart=30, maxiter=500)
    assert info == 0 and np.abs(ug - u).max() / scale < 1e-8
    dh = np.exp(0.5 * (lp - lp.max()))
    y, info = spla.cg(Ssym, dh * b, rtol=1e-10, atol=0.0, maxiter=5000)
    assert info == 0
    assert np.abs(y / dh - u).max() / scale > 1e-3
    ys = _solve(Ssym, dh * b)
    assert np.abs(ys / dh - u).max() / scale < 1e-12
