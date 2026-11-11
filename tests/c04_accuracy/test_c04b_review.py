"""Chunk 4b acceptance tests: fixes from the external review of chunks 1-4 (Nov 10).

Spec: plan/c04b_review_fixes.md. Skipped until gr.accuracy has data_error_term and gr.matrix has rhs_landing.

Three facts the review established, each tested here:
1. The stored matrix is not the ideal one. fl(1/6) = (1 - 2^-54)/6, so every float solver solves
   (I - (1+d)Q) x = (1+d) b with d = -2^-54, whose exact solution differs from the true probabilities by
   d E_i[T | event] = -(u/4) cond_i in entry i. Exact rationals (flint_solve) solve the ideal system.
2. "tiny-entry error ~ cond_tiny * rtol" is a coincidence of one right-hand side at one state, not a law.
   What a residual test controls is the ABSOLUTE error: e_i = (A^-1 e_i) . r.
3. (omega + 8u) cond_i is an a posteriori bound on the distance to the stored system's solution.
"""
from fractions import Fraction

import numpy as np
import pytest

acc = pytest.importorskip("gr.accuracy")
matrix = pytest.importorskip("gr.matrix")
if not (hasattr(acc, "data_error_term") and hasattr(acc, "aposteriori_bound") and hasattr(matrix, "rhs_landing")):
    pytest.skip("chunk 4b not built yet", allow_module_level=True)

from gr.matrix import build_A, rhs_landing, rhs_order, rhs_out_first, rhs_rounds, solve
from gr.spectrum import kappa_inf
from gr.states import StateSpace

try:
    import flint
    HAVE_FLINT = True
except ImportError:
    HAVE_FLINT = False
needs_flint = pytest.mark.skipif(not HAVE_FLINT, reason="python-flint not installed")

U = 2.0 ** -53
D = Fraction(-1, 2 ** 54)


def setup(N):
    S = StateSpace(N)
    A = build_A(S).tocsr()
    return S, A, S.index((1, 1, N - 2))


def dsolve(A):
    return lambda r: solve(A, r)


def exact_stored(A, b):
    """Exact rational solution of the system exactly as stored in float64 (every double is a dyadic rational)."""
    fa = [[Fraction(float(v)) for v in row] for row in A.toarray()]
    fb = [Fraction(float(v)) for v in b]
    den = max(max(v.denominator for row in fa for v in row), max(v.denominator for v in fb))
    M = flint.fmpz_mat([[int(v * den) for v in row] for row in fa])
    u = M.solve(flint.fmpz_mat([[int(v * den)] for v in fb]))
    return [Fraction(int(u[i, 0].p), int(u[i, 0].q)) for i in range(len(fb))]


def exact_ideal(A, b, N):
    """Exact rational solution of the ideal system (6N A and 6N b rounded to the integers they stand for)."""
    M = flint.fmpz_mat(np.rint(6 * N * A.toarray()).astype(np.int64).tolist())
    u = M.solve(flint.fmpz_mat([[int(v)] for v in np.rint(6 * N * np.asarray(b)).astype(np.int64)]))
    return [Fraction(int(u[i, 0].p), int(u[i, 0].q)) for i in range(u.nrows())]


def rel_diff(xs, xi):
    return np.array([float((s - i) / i) for s, i in zip(xs, xi)])


# ---------------------------------------------------------------- the stored system

def test_one_sixth_is_stored_slightly_low():
    assert Fraction(1.0 / 6.0) * 6 - 1 == D
    assert acc.DELTA_SIXTH == -2.0 ** -54
    S, A, _ = setup(10)
    off = A - A.multiply(np.eye(S.n))
    assert set(np.unique(off.toarray())) == {0.0, -1.0 / 6.0}
    assert np.all(A.diagonal() == 1.0)
    assert set(np.unique(rhs_out_first(S, 2))) == {0.0, 1.0 / 6.0 + 1.0 / 6.0}
    assert Fraction(1.0 / 6.0 + 1.0 / 6.0) == 2 * Fraction(1.0 / 6.0)


def test_data_error_term_definition():
    """data_error_term = DELTA_SIXTH * E_i[T | event] = -(u/4) cond_i."""
    S, A, _ = setup(20)
    b = rhs_out_first(S, 2)
    x = solve(A, b)
    term = acc.data_error_term(x, dsolve(A))
    assert term.shape == (S.n,) and np.all(term < 0)
    assert np.max(np.abs(term / (acc.DELTA_SIXTH * acc.conditional_mean_time(A, x, dsolve(A))) - 1)) < 1e-12
    assert np.max(np.abs(term / (-(U / 4) * acc.entry_condition(A, b, x, dsolve(A))) - 1)) < 1e-12


@needs_flint
@pytest.mark.parametrize("N", [12, 20])
def test_stored_system_differs_from_ideal_by_the_data_term(N):
    """Measured: the exact difference matches the prediction to 8e-16 relative in every entry;
    at the tiny entry it is -1.5106e-15 (N = 12) and -4.2702e-15 (N = 20)."""
    S, A, tiny = setup(N)
    b = rhs_out_first(S, 2)
    xi = exact_ideal(A, b, N)
    rel = rel_diff(exact_stored(A, b), xi)
    pred = acc.data_error_term(np.array([float(v) for v in xi]), dsolve(A))
    assert np.max(np.abs(rel / pred - 1)) < 1e-9
    want = {12: -1.51056e-15, 20: -4.27019e-15}[N]
    assert abs(rel[tiny] / want - 1) < 1e-4


@needs_flint
@pytest.mark.parametrize("N", [12, 20])
def test_data_term_for_order_right_hand_sides(N):
    """rhs_order rounds (y_k/N)/6 entry by entry, which adds a term of size about u (measured: 0.75 u at most)."""
    S, A, tiny = setup(N)
    b = rhs_order(S, 2, 1, 0)
    xi = exact_ideal(A, b, N)
    rel = rel_diff(exact_stored(A, b), xi)
    pred = acc.data_error_term(np.array([float(v) for v in xi]), dsolve(A))
    assert np.max(np.abs(rel - pred)) < 2 * U
    assert abs(rel[tiny] / pred[tiny] - 1) < 0.05


@needs_flint
def test_direct_solver_error_at_the_tiny_entry_is_mostly_the_data_term():
    """N = 40, SuperLU (measured): total error against exact rationals -1.52e-14, data term -1.72e-14,
    so the solver's own error is +2.0e-15."""
    N = 40
    S, A, tiny = setup(N)
    b = rhs_out_first(S, 2)
    xe = acc.flint_solve(A, b, 6 * N)
    total = (solve(A, b) - xe) / xe
    data = acc.data_error_term(xe, dsolve(A))
    assert total[tiny] < 0
    assert abs(total[tiny] - data[tiny]) < 0.5 * abs(data[tiny])
    assert abs(data[tiny] / -1.7206e-14 - 1) < 1e-3


@pytest.mark.parametrize("N", [9, 30])
def test_expected_rounds_identity(N):
    """A^-1 t = t (1 + e2) / 4 with t = 3 x1 x2 x3 / N and e2 = x1 x2 + x1 x3 + x2 x3. So for b = 1 the stored
    solution is off by d t (e2 - 3) / 4, which in chunk 2's metric is (3/16 - 27/(16 N^2)) kappa_inf u (3 | N)."""
    S, A, _ = setup(N)
    x1, x2, x3 = (S.coords()[:, k].astype(float) for k in range(3))
    t = 3 * x1 * x2 * x3 / N
    e2 = x1 * x2 + x1 * x3 + x2 * x3
    assert np.max(np.abs(solve(A, t) - t * (1 + e2) / 4)) < 1e-11 * np.max(t * (1 + e2) / 4)
    in_units = (2.0 ** -54) * np.max(t * (e2 - 3) / 4) / np.max(t) / (kappa_inf(N) * U)
    assert abs(in_units - (3 / 16 - 27 / (16 * N * N))) < 1e-9


@needs_flint
def test_stored_expected_rounds_are_low_by_the_predicted_amount():
    """b = 1 is stored exactly, so only Q is perturbed: (x_stored - t)_i / t_i = d (e2 - 3) / 4."""
    N = 12
    S, A, _ = setup(N)
    xs = exact_stored(A, rhs_rounds(S))
    t = [Fraction(3 * int(a) * int(c) * int(e), N) for a, c, e in S.coords()]
    e2 = np.array([a * c + a * e + c * e for a, c, e in S.coords()], dtype=float)
    assert np.max(np.abs(rel_diff(xs, t) / (acc.DELTA_SIXTH * (e2 - 3) / 4) - 1)) < 1e-9


# ---------------------------------------------------------------- the a posteriori bound

@needs_flint
def test_aposteriori_bound_holds():
    """(omega + 8u) cond_i bounds the distance to the STORED solution; adding |data term| bounds the distance
    to the true probability. Measured at N = 20: bound 1.8e-13 at most, actual solver error 6.7e-16 at most."""
    N = 20
    S, A, _ = setup(N)
    b = rhs_out_first(S, 2)
    xh = solve(A, b)
    bound = acc.aposteriori_bound(A, b, xh, dsolve(A))
    assert bound.shape == (S.n,)
    omega = acc.componentwise_backward_error(A, xh, b)
    assert np.max(np.abs(bound / ((omega + 8 * U) * acc.entry_condition(A, b, xh, dsolve(A))) - 1)) < 1e-12
    xs, xi = exact_stored(A, b), exact_ideal(A, b, N)
    err_stored = np.array([abs(float(Fraction(float(v)) - s)) / float(v) for v, s in zip(xh, xs)])
    err_ideal = np.array([abs(float(Fraction(float(v)) - i)) / float(v) for v, i in zip(xh, xi)])
    assert np.all(err_stored <= bound)
    assert np.all(err_ideal <= bound + np.abs(acc.data_error_term(xh, dsolve(A))))
    assert bound.max() < 1e-12


# ---------------------------------------------------------------- what a residual test controls

def test_rhs_landing():
    """P(the first bust lands exactly on boundary state y). Summed over a face it is rhs_out_first."""
    S = StateSpace(8)
    assert np.array_equal(sum(rhs_landing(S, (a, 8 - a, 0)) for a in range(1, 8)), rhs_out_first(S, 2))
    b = rhs_landing(S, (4, 4, 0))
    assert np.count_nonzero(b) == 2 and set(np.unique(b)) == {0.0, 1.0 / 6.0}
    assert b[S.index((3, 4, 1))] > 0 and b[S.index((4, 3, 1))] > 0


@pytest.mark.parametrize("N", [40, 80])
def test_entry_error_is_inverse_row_times_residual(N):
    """e_i = (A^-1 e_i) . r exactly, so |e_i| <= ||A^-1 e_i||_2 ||r||_2: a residual test bounds the absolute
    error. At the corner ||A^-1 e_i||_2 = 1.1702 for every N (measured 1.17022 and 1.17023)."""
    krylov = pytest.importorskip("gr.krylov")
    S, A, tiny = setup(N)
    b = rhs_out_first(S, 2)
    x, _ = krylov.cg(A, b, rtol=1e-8)
    r = b - A @ x
    e = np.zeros(S.n)
    e[tiny] = 1.0
    g = solve(A, e)
    err = solve(A, b)[tiny] - x[tiny]
    assert abs(err - g @ r) < 1e-6 * abs(err)
    assert abs(err) <= np.linalg.norm(g) * np.linalg.norm(r)
    assert abs(np.linalg.norm(g) - 1.1702) < 1e-3


def test_cond_times_rtol_is_not_a_law():
    """N = 320, plain CG, rtol 1e-10 (measured). Same state (1, 1, N-2), same cond (0.39 N^2):
    out_first_3 has error / (cond rtol) = 1.46, but 'first bust lands at (N/4, 3N/4, 0)' has 15.9.
    Over all states of the out_first_3 run the median of err_i / (cond_i rtol) is 3e-4."""
    krylov = pytest.importorskip("gr.krylov")
    N, rtol = 320, 1e-10
    S, A, tiny = setup(N)
    ratios = {}
    for name, b in [("out_first_3", rhs_out_first(S, 2)), ("land_quarter", rhs_landing(S, (N // 4, 3 * N // 4, 0)))]:
        xref = solve(A, b)
        cond = acc.entry_condition(A, b, xref, dsolve(A))
        assert int(np.argmin(xref)) == tiny and 0.37 < cond[tiny] / N ** 2 < 0.41
        x, info = krylov.cg(A, b, rtol=rtol)
        assert info["converged"]
        ratio = np.abs(x - xref) / xref / (cond * rtol)
        ratios[name] = ratio[tiny]
        if name == "out_first_3":
            assert np.median(ratio) < 0.01
    assert 0.5 < ratios["out_first_3"] < 3
    assert ratios["land_quarter"] > 5
