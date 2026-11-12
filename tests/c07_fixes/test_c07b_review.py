"""Chunk 7b acceptance tests: fixes from the second external review (chunks 4b and 7).

Spec: plan/c07b_review_fixes.md. Skipped until gr.accuracy.structured_condition and gr.refine.exact_residual exist.
The reference numbers below were computed in the Project chat with independent code (its own matrix builder,
SuperLU solves, exact Python-integer residuals validated against exact rational solves at N = 12, 20, 30).

What they pin down:
1. The structured condition number (independent relative perturbations of each off-diagonal entry, each row sum
   and each b_i, diagonal rebuilt) is kappa_i = (A^-1 v)_i / x_i with v_i = b_i + s_i x_i + sum_j |a_ij| |x_i - x_j|.
   It is attained, and it grows like 1.22 N at the tiny entry: it is NOT bounded in N (the review's finding).
2. exact_residual is exact, the Dot2 residual stays inside its real error bound, and refinement lands on the
   correctly rounded true probability at N = 160, where there are no exact rationals to compare with.
3. The stored solution is x + d A_d^-1 x exactly (no first-order step).
"""
from fractions import Fraction

import numpy as np
import pytest
import scipy.sparse as sp
import scipy.sparse.linalg as spla

acc = pytest.importorskip("gr.accuracy")
refine = pytest.importorskip("gr.refine")
if not (hasattr(acc, "structured_condition") and hasattr(refine, "exact_residual")):
    pytest.skip("chunk 7b functions are not built yet", allow_module_level=True)

from gr.matrix import boundary_rhs, build_A, rhs_out_first
from gr.states import StateSpace

U = 2.0 ** -53
D = Fraction(-1, 2 ** 54)  # fl(1/6) = (1 + D) / 6


def system(N):
    S = StateSpace(N)
    A = build_A(S).tocsr()
    b = rhs_out_first(S, 2)
    sums = boundary_rhs(S, lambda Y: np.ones(len(Y)))
    lu = spla.splu(A.tocsc())
    return S, A, b, sums, lu, lu.solve(b)


def off_diagonals(A):
    C = A.tocoo()
    off = C.row != C.col
    return C.row[off], C.col[off], -C.data[off]  # rows, columns, weights w_ij = -a_ij > 0


def structured_matrix(r, c, w, sums):
    """The matrix with off-diagonal weights w and row sums `sums`: diagonal_i = sums_i + sum_j w_ij."""
    n = len(sums)
    diag = sums + np.bincount(r, weights=w, minlength=n)
    return sp.csr_matrix((np.concatenate([diag, -w]), (np.concatenate([np.arange(n), r]), np.concatenate([np.arange(n), c]))),
                         shape=(n, n)).tocsc()


def kappa(A, b, sums, lu, x):
    return acc.structured_condition(A, b, x, sums, lu.solve)


# ---------------------------------------------------------------- structured condition number

@pytest.mark.parametrize("N, expected", [(10, 11.352952530), (20, 23.799328693), (40, 48.303085939), (80, 97.096884240)])
def test_structured_condition_reference_values(N, expected):
    S, A, b, sums, lu, x = system(N)
    k = kappa(A, b, sums, lu, x)
    tiny = S.index((1, 1, N - 2))
    assert k[tiny] == pytest.approx(expected, rel=1e-7)
    assert int(np.argmax(k)) == tiny  # the tiny entry is also the most sensitive one
    assert np.all(k >= 1 - 1e-12)  # scaling b alone already moves every entry by eps


@pytest.mark.parametrize("N", [12, 20])
def test_structured_condition_is_attained_in_every_entry(N):
    S, A, b, sums, lu, x = system(N)
    k = kappa(A, b, sums, lu, x)
    r, c, w = off_diagonals(A)
    x0 = spla.splu(structured_matrix(r, c, w, sums)).solve(b)
    eps = 1e-7  # weights up toward the larger x, row sums down, b up: every entry rises by eps * kappa_i
    xp = spla.splu(structured_matrix(r, c, w * (1 + eps * np.sign(x[c] - x[r])), sums * (1 - eps))).solve(b * (1 + eps))
    ratio = (xp - x0) / x0 / eps
    assert np.max(np.abs(ratio / k - 1)) < 1e-4


@pytest.mark.parametrize("N", [10, 20, 40])
def test_coherent_perturbation_moves_the_tiny_entry_by_N_minus_3(N):
    """The reviewer's counterexample: A + eps (H A - A H), H = diag(player 3's chips), b unchanged.
    It changes every off-diagonal by at most eps relatively, every row sum by at most eps relatively, leaves
    the diagonal alone, and moves entry i by eps (h_i - 1) x_i: N - 3 at (1, 1, N-2)."""
    S, A, b, sums, lu, x = system(N)
    h = S.x3.astype(float)
    H = sp.diags(h)
    Dm = (H @ A - A @ H).tocsr()
    assert np.max(np.abs(Dm.diagonal())) == 0.0
    C = Dm.tocoo()
    assert np.max(np.abs(C.data)) <= (1.0 / 6.0) * (1 + 1e-12)  # |change| <= eps |a_ij|
    assert np.all(np.abs(np.asarray(Dm.sum(axis=1)).ravel()) <= sums + 1e-12)  # |change| <= eps s_i, and 0 stays 0
    eps = 1e-7
    xp = spla.splu((A + eps * Dm).tocsc()).solve(b)
    ratio = (xp - x) / x / eps
    assert np.max(np.abs(ratio - (h - 1))) < 1e-4 * N
    assert ratio[S.index((1, 1, N - 2))] == pytest.approx(N - 3, rel=1e-4)
    assert np.all(ratio <= kappa(A, b, sums, lu, x) * (1 + 1e-4) + 1e-6)  # consistent with the condition number


def test_random_structured_perturbations_stay_far_below_the_condition_number():
    N = 40
    S, A, b, sums, lu, x = system(N)
    k = kappa(A, b, sums, lu, x)
    r, c, w = off_diagonals(A)
    x0 = spla.splu(structured_matrix(r, c, w, sums)).solve(b)
    rng = np.random.default_rng(221)
    eps, worst = 1e-7, 0.0
    for _ in range(10):
        Ap = structured_matrix(r, c, w * (1 + eps * rng.uniform(-1, 1, len(w))), sums * (1 + eps * rng.uniform(-1, 1, S.n)))
        ratio = np.abs(spla.splu(Ap).solve(b * (1 + eps * rng.uniform(-1, 1, S.n))) - x0) / x0 / eps
        assert np.all(ratio <= k * (1 + 1e-3))
        worst = max(worst, ratio.max())
    assert worst < 5  # random signs cancel: O(1), while the worst case is 48.3 here
    assert k.max() > 9 * worst


@pytest.mark.parametrize("N", [20, 40, 80])
def test_three_condition_numbers_are_ordered(N):
    S, A, b, sums, lu, x = system(N)
    tiny = S.index((1, 1, N - 2))
    k = kappa(A, b, sums, lu, x)[tiny]
    cond = acc.entry_condition(A, b, x, lu.solve)[tiny]
    assert N - 3 < k < 1.25 * N  # at least the coherent direction, and about 1.22 N
    assert k / N == pytest.approx(1.2, abs=0.02)
    assert cond / k == pytest.approx(0.32 * N, rel=0.02)  # 0.388 N^2 against 1.2 N


# ---------------------------------------------------------------- exact residual, Dot2, refinement

def fraction_residual(A, b, x, denom=1):
    A = sp.csr_matrix(A)
    out = []
    for i in range(A.shape[0]):
        acc_ = Fraction(float(b[i]))
        for kk in range(A.indptr[i], A.indptr[i + 1]):
            acc_ -= Fraction(float(A.data[kk])) * Fraction(float(x[A.indices[kk]]))
        out.append(float(acc_ / denom))
    return np.array(out)


def test_exact_residual_is_exact():
    N = 9
    S, A, b, sums, lu, x = system(N)
    xs = x * (1 + 1e-3 * np.random.default_rng(221).uniform(-1, 1, S.n))
    for v in (x, xs):
        assert np.array_equal(refine.exact_residual(A, b, v), fraction_residual(A, b, v))
        Ai, B = refine.integer_system(A, b, 6 * N)
        assert np.array_equal(refine.exact_residual(Ai, B, v, denom=6 * N), fraction_residual(Ai, B, v, denom=6 * N))


def test_exact_residual_on_the_reviewers_row():
    """A real row at N = 20 (state (2, 2, 16)) with an x for which the Dot2 loop loses the whole residual:
    the exact value is 20 t / 120 = t / 6."""
    q, t = 2.0 ** -54, 2.0 ** -174
    row = sp.csr_matrix(np.array([[-20.0, -20.0, -20.0, 120.0, -20.0, -20.0, -20.0]]))
    x = np.array([q, t, 1.0, 3002399751580331 * q, q, 0.0, 0.0])
    r = refine.exact_residual(row, np.array([0.0]), x, denom=120)
    assert r.shape == (1,) and r[0] == t / 6


@pytest.mark.parametrize("N", [20, 40])
def test_accurate_residual_obeys_the_dot2_bound(N):
    """|r_hat - r| <= 2u |r| + 64 u^2 (|A||x| + |b|): 'about 2u per entry' holds only when the first term wins."""
    S, A, b, sums, lu, x = system(N)
    Ai, B = refine.integer_system(A, b, 6 * N)
    for v in (x, x * (1 + 1e-9 * np.random.default_rng(221).uniform(-1, 1, S.n))):
        exact = refine.exact_residual(Ai, B, v, denom=6 * N)
        got = refine.accurate_residual(A, b, v, 6 * N)
        assert np.all(np.abs(got - exact) <= 2 * U * np.abs(exact) + 64 * U ** 2 * (abs(A) @ np.abs(v) + b))


def test_refinement_is_correctly_rounded_at_N160():
    """No exact rationals at N = 160. Instead: xhat - x = -A^-1 (b - A xhat) with the residual of the ideal
    system computed exactly, so the error of every entry is known to about 10 digits."""
    N = 160
    S, A, b, sums, lu, x = system(N)
    xr, info = refine.iterative_refinement(A, b, lu.solve, 6 * N)
    assert info["converged"] and info["steps"] <= 3
    Ai, B = refine.integer_system(A, b, 6 * N)
    err = -lu.solve(refine.exact_residual(Ai, B, xr, denom=6 * N))  # xr - x_true
    assert np.max(np.abs(err) / np.spacing(xr)) <= 0.5 + 1e-6  # within half an ulp everywhere
    # and the plain direct solve is NOT: it carries the data term -(u/4) cond_i plus its own error
    e0 = -lu.solve(refine.exact_residual(Ai, B, x, denom=6 * N)) / x
    assert 1e-13 < np.max(np.abs(e0)) < 2e-12


# ---------------------------------------------------------------- the stored solution, exactly

def fraction_solve(M, rhs):
    n = len(rhs)
    M = [row[:] + [rhs[i]] for i, row in enumerate(M)]
    for k in range(n):
        piv = M[k][k]
        for i in range(k + 1, n):
            if M[i][k] != 0:
                f = M[i][k] / piv
                for j in range(k, n + 1):
                    M[i][j] -= f * M[k][j]
    out = [Fraction(0)] * n
    for k in reversed(range(n)):
        out[k] = (M[k][n] - sum(M[k][j] * out[j] for j in range(k + 1, n))) / M[k][k]
    return out


@pytest.mark.parametrize("N", [6, 8])
def test_stored_solution_identity_is_exact(N):
    """x' - x = d A_d^-1 x as an identity between exact rationals (d = -2^-54): no O(d^2) term is dropped.
    Hence x'_i = E_i[(1 + d)^T; event] and d E[T | event] <= (x' - x)_i / x_i <= 0."""
    S, A, b, sums, lu, x = system(N)
    Ad = A.toarray()
    n = S.n
    stored = [[Fraction(float(Ad[i, j])) for j in range(n)] for i in range(n)]
    ideal = [[Fraction(1) if i == j else (Fraction(-1, 6) if Ad[i, j] != 0 else Fraction(0)) for j in range(n)] for i in range(n)]
    xs = fraction_solve(stored, [Fraction(float(v)) for v in b])
    xi = fraction_solve(ideal, [Fraction(int(round(6 * v)), 6) for v in b])
    y = fraction_solve(stored, xi)
    assert all(xs[i] - xi[i] == D * y[i] for i in range(n))
    yi = fraction_solve(ideal, xi)  # (A^-1 x)_i = E_i[T; event]
    assert all(D * yi[i] <= xs[i] - xi[i] <= 0 for i in range(n))
