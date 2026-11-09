"""Chunk 7 acceptance tests: three ways to get the tiny probabilities right.

Spec: plan/c07_fixes.md. Skipped until gr/refine.py exists.
1. A componentwise stopping rule for CG (stop on the Oettli-Prager backward error of the true residual).
2. Iterative refinement with an accurate residual: 6N A and 6N b are integers, so b - A x can be computed
   with error-free transformations (TwoProduct, TwoSum) to about one rounding per entry.
3. GTH-style elimination: pivots from row sums, so no subtraction ever happens.
"""
from fractions import Fraction
from functools import lru_cache

import numpy as np
import pytest
import scipy.sparse as sp

refine = pytest.importorskip("gr.refine")

from gr.accuracy import componentwise_backward_error, flint_solve
from gr.krylov import cg, make_preconditioner
from gr.matrix import boundary_rhs, build_A, rhs_out_first, solve
from gr.states import StateSpace

try:
    import flint  # noqa: F401
    HAVE_FLINT = True
except ImportError:
    HAVE_FLINT = False
needs_flint = pytest.mark.skipif(not HAVE_FLINT, reason="python-flint not installed")

U = 2.0 ** -53


def setup(N):
    S = StateSpace(N)
    A = build_A(S).tocsr()
    return S, A, rhs_out_first(S, 2), S.index((1, 1, N - 2))


@lru_cache(maxsize=None)
def exact(N):
    """Exact answer for b = rhs_out_first(S, 2), computed once per N (N = 60 takes about 5 s)."""
    S, A, b, _ = setup(N)
    return flint_solve(A, b, 6 * N)


def row_sums(S):
    """A 1 = probability of a bust in one round, built from the boundary (independent of A's entries)."""
    return boundary_rhs(S, lambda Y: np.ones(len(Y)))


def exact_residual(Ai, B, x, scale):
    out = []
    for i in range(len(x)):
        acc = Fraction(int(B[i]))
        for p in range(Ai.indptr[i], Ai.indptr[i + 1]):
            acc -= Fraction(int(Ai.data[p])) * Fraction(float(x[Ai.indices[p]]))
        out.append(acc / scale)
    return out


# ---------------------------------------------------------------- accurate residual

def test_integer_system():
    S, A, b, _ = setup(10)
    Ai, B = refine.integer_system(A, b, 60)
    assert np.all(Ai.data == np.round(Ai.data)) and np.all(B == np.round(B))
    assert set(np.unique(Ai.data)) <= {60.0, -10.0}
    with pytest.raises(ValueError):
        refine.integer_system(A, b, 7)


def test_row_sums_match_A_times_ones():
    S, A, _, _ = setup(20)
    assert np.max(np.abs(row_sums(S) - A @ np.ones(S.n))) < 1e-15


@pytest.mark.parametrize("which", ["near_solution", "random"])
def test_accurate_residual_is_correct_to_a_few_rounding_errors(which):
    """Measured: exact at the computed solution (where the naive residual is off by 700%), 1.85 u for random x."""
    S, A, b, _ = setup(10)
    x = solve(A, b) if which == "near_solution" else np.random.default_rng(221).uniform(0, 1, S.n)
    Ai, B = refine.integer_system(A, b, 60)
    ex = np.array([float(v) for v in exact_residual(Ai, B, x, 60)])
    r = refine.accurate_residual(A, b, x, 60)
    nz = ex != 0
    assert np.all(r[~nz] == 0)
    assert np.max(np.abs(r[nz] - ex[nz]) / np.abs(ex[nz])) <= 3 * U


def test_naive_residual_is_garbage_at_the_solution():
    S, A, b, _ = setup(10)
    x = solve(A, b)
    Ai, B = refine.integer_system(A, b, 60)
    ex = np.array([float(v) for v in exact_residual(Ai, B, x, 60)])
    nz = ex != 0
    naive = b - A @ x
    assert np.max(np.abs(naive[nz] - ex[nz]) / np.abs(ex[nz])) > 0.5


# ---------------------------------------------------------------- iterative refinement

@needs_flint
@pytest.mark.parametrize("N", [20, 40])
def test_refinement_with_a_direct_inner_solve_is_correctly_rounded(N):
    """Measured: 2 steps, then every entry equals the exact answer rounded to double."""
    S, A, b, _ = setup(N)
    xe = exact(N)
    x, info = refine.iterative_refinement(A, b, lambda r: solve(A, r), 6 * N)
    assert info["converged"] and info["steps"] <= 3
    assert np.max(np.abs(x - xe) / xe) <= 2 * U


@needs_flint
def test_refinement_with_a_sloppy_cg_inner_solve():
    """Inner CG + MIC(0) at rtol 1e-6 is enough: measured 4 steps, every entry exact."""
    N = 40
    S, A, b, _ = setup(N)
    xe = exact(N)
    M, _ = make_preconditioner(A, "mic0")
    x, info = refine.iterative_refinement(A, b, lambda r: cg(A, r, rtol=1e-6, M=M)[0], 6 * N, max_steps=10)
    assert info["converged"] and info["steps"] <= 6
    assert np.max(np.abs(x - xe) / xe) <= 2 * U
    c = np.asarray(info["corrections"])
    assert len(c) == info["steps"] and c[-1] <= 4 * U


def test_refinement_reports_non_convergence():
    S, A, b, _ = setup(20)
    _, info = refine.iterative_refinement(A, b, lambda r: 0.5 * r, 120, x0=np.ones(S.n), max_steps=3)
    assert info["steps"] == 3 and not info["converged"]


# ---------------------------------------------------------------- GTH

@needs_flint
@pytest.mark.parametrize("N,limit", [(20, 30), (40, 40), (60, 60)])
def test_gth_is_accurate_in_every_entry(N, limit):
    """Measured max errors: 8 u, 12 u, 25 u (the plain direct solve: 39 u, 137 u, 267 u)."""
    S, A, b, _ = setup(N)
    x = refine.gth_solve(A, b, row_sums(S))
    assert np.max(np.abs(x - exact(N)) / exact(N)) <= limit * U


@needs_flint
def test_gth_beats_plain_elimination_at_N60():
    S, A, b, _ = setup(60)
    gth = np.max(np.abs(refine.gth_solve(A, b, row_sums(S)) - exact(60)) / exact(60))
    plain = np.max(np.abs(solve(A, b) - exact(60)) / exact(60))
    assert gth < plain / 4


def test_gth_refuses_bad_input():
    S, A, b, _ = setup(10)
    with pytest.raises(ValueError):
        refine.gth_solve(A, b, -row_sums(S))
    with pytest.raises(ValueError):
        refine.gth_solve(A, -b - 1, row_sums(S))
    bad = A.tolil()
    bad[0, 1] = 0.5
    with pytest.raises(ValueError):
        refine.gth_solve(bad.tocsr(), b, row_sums(S))


def test_gth_agrees_with_refinement_at_N200():
    """Measured: 57 u apart, against 1913 u for the plain direct solve."""
    S, A, b, tiny = setup(200)
    xr, info = refine.iterative_refinement(A, b, lambda r: solve(A, r), 1200)
    assert info["converged"]
    xg = refine.gth_solve(A, b, row_sums(S))
    assert np.max(np.abs(xg - xr) / xr) < 200 * U


# ---------------------------------------------------------------- componentwise stopping

def test_cg_componentwise_history_and_stop():
    S, A, b, tiny = setup(40)
    x, info = refine.cg_componentwise(A, b, 1e-14, check_every=10)
    om = np.asarray(info["omegas"])
    assert om[0] == 1.0, "at x = 0 the backward error is exactly 1"
    assert info["converged"] and om[-1] <= 1e-14
    assert info["iterations"] % 10 == 0 and len(om) == info["iterations"] // 10 + 1
    assert componentwise_backward_error(A, x, b) <= 1e-14


@needs_flint
@pytest.mark.parametrize("kind", ["none", "mic0"])
def test_componentwise_stopping_gets_the_tiny_entry(kind):
    """N = 60. With rtol 1e-10 the tiny entry's relative error is 5e-8 (none) or 1.3e-10 (mic0);
    stopping at omega <= 1e-14 gives 4e-14 to 6e-14, for 140 instead of 107 (none) or 40 instead of 27 iterations."""
    N = 60
    S, A, b, tiny = setup(N)
    xe = exact(N)
    M, _ = make_preconditioner(A, kind)
    x, info = refine.cg_componentwise(A, b, 1e-14, M=M, check_every=5)
    assert info["converged"]
    assert abs(x[tiny] - xe[tiny]) / xe[tiny] < 1e-11
    x10, info10 = cg(A, b, rtol=1e-10, M=M)
    assert info["iterations"] > info10["iterations"]
