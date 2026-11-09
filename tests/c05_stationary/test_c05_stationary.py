"""Chunk 5 acceptance tests: Jacobi, Gauss-Seidel and SOR as solvers.

Spec: plan/c05_stationary.md. Skipped until gr/stationary.py exists.

Conventions these tests rely on (all stated in the spec): sweeps visit the unknowns in StateSpace
index order, x0 defaults to 0, and info["residual_norms"][k] = ||b - A x_k||_2 / ||b||_2 for
k = 0, 1, ..., info["iterations"], with the stopping rule checked before every sweep (including
the first). Expected counts were measured with an independent reference implementation.
"""
import numpy as np
import pytest

stationary = pytest.importorskip("gr.stationary")

from gr.matrix import build_A, rhs_out_first, rhs_rounds, solve
from gr.states import StateSpace

RTOL = 1e-10
METHODS = ["jacobi", "gauss_seidel", "sor"]
KINDS = ["ones", "out_first", "random"]


def rho_jacobi(N):
    """Spectral radius of Q = I - A (chunk 1): 1 - lambda_min = (1 + 2 cos(2 pi / N)) / 3."""
    return (1 + 2 * np.cos(2 * np.pi / N)) / 3


def omega_star(N):
    return stationary.young_omega(rho_jacobi(N))


def system(N):
    S = StateSpace(N)
    return S, build_A(S)


def rhs(S, kind):
    if kind == "ones":
        return rhs_rounds(S)  # solution: expected rounds t = 3 x1 x2 x3 / N
    if kind == "out_first":
        return rhs_out_first(S, 0)  # solution: P(player 1 is out first)
    return np.random.default_rng(221).standard_normal(S.n)


def run(method, S, A, b, **kw):
    if method == "jacobi":
        return stationary.jacobi(A, b, **kw)
    if method == "gauss_seidel":
        return stationary.gauss_seidel(A, b, **kw)
    return stationary.sor(A, b, omega_star(S.N), **kw)


# ---------------------------------------------------------------- interface and correctness


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("method", METHODS)
def test_solution_matches_direct_solve(method, kind):
    """Relative residual 1e-10 bounds the relative error by kappa2 * 1e-10 = 4.5e-9 at N = 20."""
    S, A = system(20)
    b = rhs(S, kind)
    x, info = run(method, S, A, b)
    assert info["converged"]
    xd = solve(A, b)
    assert np.linalg.norm(x - xd) <= 1e-7 * np.linalg.norm(xd)


@pytest.mark.parametrize("method", METHODS)
def test_info_and_stopping_rule(method):
    S, A = system(12)
    b = rhs_rounds(S)
    x, info = run(method, S, A, b)
    assert {"iterations", "converged", "residual_norms"} <= set(info)
    k = info["iterations"]
    assert int(k) == k and k > 0
    assert bool(info["converged"])
    res = np.asarray(info["residual_norms"], dtype=float)
    assert res.shape == (k + 1,), "one entry per iterate x_0, ..., x_k"
    assert abs(res[0] - 1) < 1e-14, "x0 = 0, so the starting residual is b itself"
    assert res[-1] <= RTOL < res[-2], "stop at the first iterate that meets rtol"
    true = np.linalg.norm(b - A @ x) / np.linalg.norm(b)
    assert abs(true - res[-1]) <= 1e-12, "residual_norms must be the true residual of x"


@pytest.mark.parametrize("method", METHODS)
def test_maxiter_caps_the_sweeps(method):
    S, A = system(12)
    b = rhs_rounds(S)
    x, info = run(method, S, A, b, maxiter=5)
    assert info["iterations"] == 5 and not info["converged"]
    res = np.asarray(info["residual_norms"], dtype=float)
    assert res.shape == (6,)
    assert abs(np.linalg.norm(b - A @ x) / np.linalg.norm(b) - res[-1]) <= 1e-12


@pytest.mark.parametrize("method", METHODS)
def test_exact_start_needs_no_sweeps(method):
    """The stopping rule is checked before the first sweep too."""
    S, A = system(12)
    b = rhs_out_first(S, 0)
    xd = solve(A, b)
    x, info = run(method, S, A, b, x0=xd)
    assert info["iterations"] == 0 and info["converged"]
    assert np.max(np.abs(x - xd)) <= 1e-15 * np.max(np.abs(xd))


@pytest.mark.parametrize("method", METHODS)
def test_inputs_not_modified(method):
    S, A = system(12)
    b = rhs_rounds(S)
    x0 = np.random.default_rng(221).random(S.n)
    b_keep, x0_keep = b.copy(), x0.copy()
    run(method, S, A, b, x0=x0, maxiter=3)
    assert np.array_equal(b, b_keep) and np.array_equal(x0, x0_keep)


def test_sor_with_omega_one_is_gauss_seidel():
    S, A = system(20)
    b = rhs(S, "random")
    xg, info_g = stationary.gauss_seidel(A, b)
    xs, info_s = stationary.sor(A, b, 1.0)
    assert info_g["iterations"] == info_s["iterations"]
    assert np.max(np.abs(xs - xg)) <= 1e-12 * np.max(np.abs(xg))


@pytest.mark.parametrize("omega", [0.0, -0.5, 2.0, 2.5])
def test_sor_rejects_omega_outside_0_2(omega):
    """rho(SOR(omega)) >= |omega - 1| (Kahan), so SOR cannot converge unless 0 < omega < 2."""
    S, A = system(10)
    with pytest.raises(ValueError):
        stationary.sor(A, rhs_rounds(S), omega)


# ---------------------------------------------------------------- Jacobi is the game played forward


@pytest.mark.parametrize("kind", ["ones", "out_first"])
def test_jacobi_iterates_are_the_game_played_forward(kind):
    """From x0 = 0 the k-th Jacobi iterate is sum_{m<k} Q^m b. For b = 1 that is E[min(T, k)],
    T = rounds until the first bust; for b = rhs_out_first(S, 0) it is
    P(player 1 is out first within k rounds)."""
    S, A = system(10)
    b = rhs(S, kind)
    Q = np.eye(S.n) - A.toarray()
    want, term, prev = np.zeros(S.n), b.copy(), np.zeros(S.n)
    for k in range(1, 7):
        want = want + term
        term = Q @ term
        x, info = stationary.jacobi(A, b, rtol=0, maxiter=k)
        assert info["iterations"] == k
        assert np.max(np.abs(x - want)) <= 1e-14 * max(1.0, np.max(np.abs(want)))
        assert np.all(x >= prev - 1e-15), "more rounds can only add probability or time"
        prev = x
    if kind == "ones":
        assert 1 - 1e-12 <= x.min() and x.max() <= 6 + 1e-12, "1 <= E[min(T, 6)] <= 6"
    else:
        assert -1e-15 <= x.min() and x.max() <= 1 + 1e-15


def test_jacobi_residual_contracts_by_rho_J_every_sweep():
    """r_{k+1} = Q r_k and Q is symmetric, so ||r_{k+1}|| <= rho_J ||r_k|| for every b."""
    N = 20
    S, A = system(N)
    _, info = stationary.jacobi(A, rhs(S, "random"), rtol=1e-8)
    res = np.asarray(info["residual_norms"], dtype=float)
    rho = rho_jacobi(N)
    assert np.all(res[1:] <= rho * res[:-1] * (1 + 1e-6))
    assert abs(res[-1] / res[-2] - rho) < 1e-4, "by the end the slowest mode dominates"


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("N", [12, 30])
def test_jacobi_never_needs_more_than_predicted(N, kind):
    """||r_k|| <= rho_J^k ||b||, so iterations <= ln(1/rtol) / (-ln rho_J) for every b."""
    S, A = system(N)
    _, info = stationary.jacobi(A, rhs(S, kind))
    assert info["iterations"] <= np.ceil(np.log(1 / RTOL) / -np.log(rho_jacobi(N))) + 1


@pytest.mark.parametrize("N, want", [(12, 245), (20, 689), (30, 1556)])
def test_jacobi_iterations_for_b_ones(N, want):
    """b = 1 lines up with the slowest mode, so the count sits just under the prediction
    ln(1/rtol) / (-ln rho_J) = 246.1, 694.1, 1569.0."""
    S, A = system(N)
    _, info = stationary.jacobi(A, rhs_rounds(S))
    pred = np.log(1 / RTOL) / -np.log(rho_jacobi(N))
    assert 0.97 * pred <= info["iterations"] <= pred + 1
    assert abs(info["iterations"] - want) <= 3


# ---------------------------------------------------------------- Gauss-Seidel and SOR counts


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("N", [20, 30])
def test_gauss_seidel_needs_about_half_the_jacobi_sweeps(N, kind):
    """rho_GS is just above rho_J^2 (test_c05_sor_law.py), so about half the sweeps.
    Measured ratios: 0.498 to 0.503."""
    S, A = system(N)
    b = rhs(S, kind)
    k_j = stationary.jacobi(A, b)[1]["iterations"]
    k_gs = stationary.gauss_seidel(A, b)[1]["iterations"]
    assert 0.45 <= k_gs / k_j <= 0.55


@pytest.mark.parametrize("N", [12, 20, 30, 40])
def test_sor_iterations_follow_the_three_quarter_law(N):
    """At omega* the count follows rho = (omega* - 1)^(3/4), not Young's rho = omega* - 1.
    b = 1, measured: 38, 64, 97, 129 sweeps. 3/4-law predictions ln(1/rtol) / (-0.75 ln(omega* - 1)):
    34.9, 59.3, 89.4, 119.4. Young predictions ln(1/rtol) / (-ln(omega* - 1)): 26.2, 44.5, 67.0, 89.6."""
    S, A = system(N)
    w = omega_star(N)
    _, info = stationary.sor(A, rhs_rounds(S), w)
    k = info["iterations"]
    young = np.log(1 / RTOL) / -np.log(w - 1)
    law = young / 0.75
    assert info["converged"]
    assert law <= k <= 1.2 * law
    assert k >= 1.3 * young


@pytest.mark.parametrize("N", [20, 40])
def test_sor_residual_rate_is_the_three_quarter_law(N):
    """Geometric-mean contraction over the second half of the run, b = 1:
    ln(rate) / ln(omega* - 1) = 3/4 (Young's theory says 1). Measured 0.7501 and 0.7500."""
    S, A = system(N)
    w = omega_star(N)
    _, info = stationary.sor(A, rhs_rounds(S), w)
    res = np.asarray(info["residual_norms"], dtype=float)
    k = len(res) - 1
    h = k // 2
    rate = (res[k] / res[h]) ** (1 / (k - h))
    assert abs(np.log(rate) / np.log(w - 1) - 0.75) < 0.01
