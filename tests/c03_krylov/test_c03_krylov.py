"""Chunk 3 acceptance tests: conjugate gradients and preconditioners.

Spec: plan/c03_krylov.md. Skipped until gr/krylov.py exists.
Stopping rule everywhere: the CG-updated residual satisfies ||r_k||_2 <= rtol ||b||_2 (unpreconditioned
residual, also for preconditioned CG, so every method stops on the same test).
"""
import numpy as np
import pytest
import scipy.linalg as sla
import scipy.sparse as sp
import scipy.sparse.linalg as spla

krylov = pytest.importorskip("gr.krylov")

from gr.matrix import build_A, rhs_rounds, solve
from gr.spectrum import kappa2
from gr.states import StateSpace

try:
    import pyamg  # noqa: F401
    HAVE_PYAMG = True
except ImportError:
    HAVE_PYAMG = False
needs_pyamg = pytest.mark.skipif(not HAVE_PYAMG, reason="pyamg not installed")

KINDS = [pytest.param(k, marks=needs_pyamg) if k == "amg" else k for k in ("none", "jacobi", "ic0", "mic0", "amg")]


def problem(N):
    S = StateSpace(N)
    return S, build_A(S).tocsr()


def random_rhs(S):
    return np.random.default_rng(221).standard_normal(S.n)


def iterations(A, b, kind, rtol=1e-10):
    M, _ = krylov.make_preconditioner(A, kind)
    _, info = krylov.cg(A, b, rtol=rtol, M=M)
    assert info["converged"]
    return info["iterations"]


# ---------------------------------------------------------------- plain CG

def test_preconditioner_names():
    assert list(krylov.PRECONDITIONERS) == ["none", "jacobi", "ic0", "mic0", "amg"]


def test_cg_solves_a_small_system():
    S, A = problem(20)
    b = random_rhs(S)
    x, info = krylov.cg(A, b, rtol=1e-12)
    ref = solve(A, b)
    assert info["converged"]
    assert np.max(np.abs(x - ref)) < 1e-9 * np.max(np.abs(ref))


def test_residual_history():
    S, A = problem(20)
    b = random_rhs(S)
    _, info = krylov.cg(A, b, rtol=1e-10)
    res = np.asarray(info["residuals"])
    assert len(res) == info["iterations"] + 1
    assert abs(res[0] - 1) < 1e-15, "x0 = 0, so the first relative residual is exactly 1"
    assert res[-1] <= 1e-10 and np.all(res[:-1] > 1e-10), "stop at the first k with ||r_k|| <= rtol ||b||"


def test_x0_and_maxiter():
    S, A = problem(20)
    b = random_rhs(S)
    _, info = krylov.cg(A, b, rtol=1e-10, x0=solve(A, b))
    assert info["iterations"] == 0 and info["converged"]
    _, info = krylov.cg(A, b, rtol=1e-10, maxiter=5)
    assert info["iterations"] == 5 and not info["converged"]


@pytest.mark.parametrize("N", [40, 80])
def test_same_iterates_as_scipy_cg(N):
    """Same algorithm and stopping rule as scipy.sparse.linalg.cg (measured: identical counts and x)."""
    S, A = problem(N)
    b = random_rhs(S)
    count = [0]
    xs, flag = spla.cg(A, b, rtol=1e-8, atol=0.0, callback=lambda xk: count.__setitem__(0, count[0] + 1))
    assert flag == 0
    x, info = krylov.cg(A, b, rtol=1e-8)
    assert abs(info["iterations"] - count[0]) <= 2
    assert np.max(np.abs(x - xs)) < 1e-6 * np.max(np.abs(xs))


def test_energy_norm_error_never_increases():
    """CG minimizes ||x - x*||_A over a growing Krylov space, so the A-norm error is monotone."""
    S, A = problem(30)
    b = random_rhs(S)
    xs = solve(A, b)
    errs = []
    krylov.cg(A, b, rtol=1e-12, callback=lambda xk: errs.append(np.sqrt((xk - xs) @ (A @ (xk - xs)))))
    assert len(errs) > 10
    assert np.all(np.diff(errs) <= 1e-12 * errs[0])


def test_iteration_bound_formula():
    """ceil( (sqrt(kappa)/2) ln(2 sqrt(kappa)/rtol) ): the Chebyshev bound turned into a residual bound."""
    assert krylov.cg_iteration_bound(100, 1e-10) == 131
    assert krylov.cg_iteration_bound(kappa2(80), 1e-10) == 365


@pytest.mark.parametrize("N", [20, 40, 80])
def test_iterations_below_the_bound(N):
    """Measured 39, 77, 154: about 0.43 of the bound."""
    S, A = problem(N)
    its = iterations(A, random_rhs(S), "none")
    assert its <= krylov.cg_iteration_bound(kappa2(N), 1e-10)
    assert 1.8 * N <= its <= 2.05 * N


@pytest.mark.parametrize("N", [10, 11, 20, 21, 30, 31])
def test_b_equal_ones_touches_floor_half_N_eigenvalues(N):
    """The fact behind finite termination: b = 1 has weight on exactly floor((N-1)/2) distinct eigenvalues."""
    S, A = problem(N)
    w, V = np.linalg.eigh(A.toarray())
    c2 = (V.T @ rhs_rounds(S)) ** 2
    weights, i = [], 0
    while i < len(w):
        j = i
        while j + 1 < len(w) and w[j + 1] - w[i] < 1e-9:
            j += 1
        weights.append(c2[i:j + 1].sum())
        i = j + 1
    weights = np.array(weights)
    assert np.sum(weights > 1e-20 * weights.sum()) == (N - 1) // 2


@pytest.mark.parametrize("N", [10, 11, 20, 21, 30, 31, 40, 41])
def test_finite_termination_for_b_equal_ones(N):
    S, A = problem(N)
    _, info = krylov.cg(A, rhs_rounds(S), rtol=1e-10)
    assert info["iterations"] == (N - 1) // 2


def test_jacobi_does_nothing_here():
    """diag(A) = I, so Jacobi preconditioning is the identity: same iterations, same answer."""
    S, A = problem(40)
    b = random_rhs(S)
    assert np.all(A.diagonal() == 1)
    M, _ = krylov.make_preconditioner(A, "jacobi")
    x1, i1 = krylov.cg(A, b, rtol=1e-10)
    x2, i2 = krylov.cg(A, b, rtol=1e-10, M=M)
    assert i1["iterations"] == i2["iterations"]
    assert np.max(np.abs(x1 - x2)) < 1e-14 * np.max(np.abs(x1))


# ---------------------------------------------------------------- incomplete Cholesky

@pytest.mark.parametrize("N", [10, 30])
def test_ic0_pattern_and_defining_property(N):
    """IC(0): L has the pattern of tril(A) and (L L^T)_ij = A_ij on the whole pattern of A."""
    _, A = problem(N)
    L = sp.csr_matrix(krylov.ic0(A))
    assert (sp.triu(L, 1)).nnz == 0
    assert ((abs(L) > 0) != (abs(sp.tril(A)) > 0)).nnz == 0
    R = (L @ L.T - A).tocoo()
    on_pattern = np.asarray(abs(A).tocsr()[R.row, R.col]).ravel() > 0
    assert np.max(np.abs(R.data[on_pattern])) < 1e-14
    assert L.diagonal().min() > 0


@pytest.mark.parametrize("N", [10, 30])
def test_mic0_keeps_row_sums(N):
    """MIC(0): dropped fill goes to the diagonal, so (L L^T) 1 = A 1; off-diagonal pattern entries stay exact."""
    S, A = problem(N)
    L = sp.csr_matrix(krylov.ic0(A, modified=True))
    one = np.ones(S.n)
    assert np.max(np.abs(L @ (L.T @ one) - A @ one)) < 1e-13
    R = (L @ L.T - A).tocoo()
    on_pattern = np.asarray(abs(A).tocsr()[R.row, R.col]).ravel() > 0
    off = on_pattern & (R.row != R.col)
    assert np.max(np.abs(R.data[off])) < 1e-14
    assert np.max(np.abs(R.diagonal() if hasattr(R, "diagonal") else 0)) > 1e-3, "MIC must change the diagonal"


@pytest.mark.parametrize("N", [10, 20])
def test_mic0_smallest_eigenvalue_is_exactly_one(N):
    """L L^T = A + R with R a negative semidefinite Laplacian and R 1 = 0, so lambda_min((LL^T)^-1 A) = 1."""
    _, A = problem(N)
    L = krylov.ic0(A, modified=True).toarray()
    ev = sla.eigh(A.toarray(), L @ L.T, eigvals_only=True)
    assert abs(ev[0] - 1) < 1e-10


@pytest.mark.parametrize("N,ic,mic", [(20, 4.36, 2.725), (40, 15.11, 5.604)])
def test_preconditioned_condition_numbers(N, ic, mic):
    """kappa(none) ~ 0.114 N^2, kappa(IC(0)) ~ 0.009 N^2, kappa(MIC(0)) ~ 0.15 N (measured)."""
    _, A = problem(N)
    Ad = A.toarray()
    for modified, want in [(False, ic), (True, mic)]:
        L = krylov.ic0(A, modified=modified).toarray()
        ev = sla.eigh(Ad, L @ L.T, eigvals_only=True)
        assert abs(ev[-1] / ev[0] / want - 1) < 0.01


def test_ic_preconditioner_applies_the_inverse():
    S, A = problem(15)
    L = krylov.ic0(A)
    M = krylov.ic_preconditioner(L)
    r = random_rhs(S)
    Ld = L.toarray()
    assert np.max(np.abs(M(r) - np.linalg.solve(Ld @ Ld.T, r))) < 1e-12 * np.max(np.abs(r))


def test_ic0_reports_breakdown():
    """Kershaw's SPD matrix (eigenvalues 0.17 and 5.83): IC(0) hits a negative pivot."""
    K = sp.csr_matrix(np.array([[3.0, -2, 0, 2], [-2, 3, -2, 0], [0, -2, 3, -2], [2, 0, -2, 3]]))
    assert np.linalg.eigvalsh(K.toarray()).min() > 0
    with pytest.raises(ValueError):
        krylov.ic0(K)


# ---------------------------------------------------------------- preconditioned CG

def test_make_preconditioner_interface():
    _, A = problem(20)
    M, t = krylov.make_preconditioner(A, "none")
    assert M is None and t >= 0
    M, t = krylov.make_preconditioner(A, "ic0")
    assert callable(M) and isinstance(t, float) and t >= 0
    with pytest.raises(ValueError):
        krylov.make_preconditioner(A, "ilu_magic")


@pytest.mark.parametrize("kind", KINDS)
def test_preconditioned_cg_is_accurate(kind):
    S, A = problem(40)
    b = random_rhs(S)
    M, _ = krylov.make_preconditioner(A, kind)
    x, info = krylov.cg(A, b, rtol=1e-12, M=M)
    ref = solve(A, b)
    assert info["converged"]
    assert np.max(np.abs(x - ref)) < 1e-9 * np.max(np.abs(ref))


@needs_pyamg
def test_iteration_ranking_at_N80():
    """Measured: amg 9 < mic0 33 < ic0 49 < none 154."""
    S, A = problem(80)
    b = random_rhs(S)
    its = {k: iterations(A, b, k) for k in ("none", "ic0", "mic0", "amg")}
    assert its["amg"] < its["mic0"] < its["ic0"] < its["none"]


def test_iteration_growth_per_doubling():
    """Per doubling of N: none ~2.0 (kappa ~ N^2), ic0 ~1.8-1.95 (still ~ N^2), mic0 ~1.5 (kappa ~ N)."""
    its = {}
    for N in (40, 80, 160):
        S, A = problem(N)
        b = random_rhs(S)
        its[N] = {k: iterations(A, b, k) for k in ("none", "ic0", "mic0")}
    for lo, hi in [(40, 80), (80, 160)]:
        g = {k: its[hi][k] / its[lo][k] for k in its[lo]}
        assert 1.85 < g["none"] < 2.15, g
        assert 1.65 < g["ic0"] < 2.1, g
        assert 1.3 < g["mic0"] < 1.7, g
