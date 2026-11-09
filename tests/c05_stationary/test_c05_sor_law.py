"""Chunk 5 acceptance tests: iteration matrices, spectral radii and the SOR 3/4 law.

Spec: plan/c05_stationary.md. Skipped until gr/stationary.py exists.

Young's SOR theory assumes a consistently ordered matrix. The 7-point triangular stencil in
lexicographic (x1, x2) order is not consistently ordered (its graph has triangles). Measured to
rounding with dense eigenvalues at 13 sizes from N = 6 to N = 100:
  * rho_GS sits slightly above rho_J^2 (N^4 times the gap rises from 10 to about 19);
  * Young's omega* = 2 / (1 + sqrt(1 - rho_J^2)) still minimizes rho(SOR(omega));
  * rho(SOR(omega*)) = (omega* - 1)^(3/4), not Young's omega* - 1.
"""
import numpy as np
import pytest

stationary = pytest.importorskip("gr.stationary")

from gr.matrix import build_A
from gr.states import StateSpace


def rho_jacobi(N):
    return (1 + 2 * np.cos(2 * np.pi / N)) / 3


def omega_star(N):
    return stationary.young_omega(rho_jacobi(N))


def dense_rho(A, method, omega=None):
    return stationary.spectral_radius(stationary.iteration_matrix(A, method, omega))


def test_spectral_radius_is_the_largest_modulus():
    assert abs(stationary.spectral_radius(np.array([[0.0, 2.0], [-2.0, 0.0]])) - 2) < 1e-14
    assert abs(stationary.spectral_radius(np.diag([-3.0, 1.0])) - 3) < 1e-14


def test_jacobi_iteration_matrix_is_Q():
    A = build_A(StateSpace(10))
    M = stationary.iteration_matrix(A, "jacobi")
    assert isinstance(M, np.ndarray) and M.shape == A.shape
    assert np.max(np.abs(M - (np.eye(A.shape[0]) - A.toarray()))) < 1e-15


@pytest.mark.parametrize("method, omega", [("jacobi", None), ("gauss_seidel", None), ("sor", 1.5)])
def test_one_sweep_is_the_iteration_matrix(method, omega):
    """One sweep maps x0 to M x0 + c, so sweep(x0) - sweep(0) = M x0. This ties
    iteration_matrix to the order the real sweeps use."""
    S = StateSpace(10)
    A = build_A(S)
    rng = np.random.default_rng(221)
    b, x0 = rng.standard_normal(S.n), rng.standard_normal(S.n)

    def sweep(x):
        if method == "sor":
            return stationary.sor(A, b, omega, rtol=0, maxiter=1, x0=x)[0]
        return getattr(stationary, method)(A, b, rtol=0, maxiter=1, x0=x)[0]

    M = stationary.iteration_matrix(A, method, omega)
    assert np.max(np.abs(sweep(x0) - sweep(np.zeros(S.n)) - M @ x0)) < 1e-13


@pytest.mark.parametrize("N", [12, 20])
def test_rho_jacobi_formula(N):
    assert abs(dense_rho(build_A(StateSpace(N)), "jacobi") - rho_jacobi(N)) < 1e-10


@pytest.mark.parametrize("N, want", [(12, 16.560), (20, 18.241), (30, 18.792)])
def test_gauss_seidel_rho_just_above_rho_J_squared(N, want):
    """Consistently ordered matrices have rho_GS = rho_J^2 exactly. Here the gap is positive
    and tiny: N^4 (rho_GS - rho_J^2) = 16.56, 18.24, 18.79."""
    gap = dense_rho(build_A(StateSpace(N)), "gauss_seidel") - rho_jacobi(N) ** 2
    assert gap > 0
    assert abs(N ** 4 * gap - want) < 0.01


def test_young_omega_formula():
    for rho in (0.0, 0.3, 0.9, 0.99):
        assert abs(stationary.young_omega(rho) - 2 / (1 + np.sqrt(1 - rho ** 2))) < 1e-15
    w = [stationary.young_omega(r) for r in (0.5, 0.9, 0.99, 0.999)]
    assert np.all(np.diff(w) > 0) and 1 < w[0] and w[-1] < 2


def test_three_quarter_law_at_N6_is_the_golden_ratio():
    """N = 6 (n = 10): rho_J = 2/3, omega* - 1 = phi^-4 and rho(SOR(omega*)) = phi^-3 = sqrt(5) - 2,
    phi = (1 + sqrt 5) / 2. Young's theory would say phi^-4 = 0.1459 instead of 0.2361."""
    phi = (1 + np.sqrt(5)) / 2
    w = omega_star(6)
    assert abs(w - 1 - phi ** -4) < 1e-14
    assert abs(dense_rho(build_A(StateSpace(6)), "sor", w) - (np.sqrt(5) - 2)) < 1e-12


@pytest.mark.parametrize("N, want", [(12, 0.517356404064), (20, 0.678068808994), (30, 0.772896324321)])
def test_three_quarter_law(N, want):
    w = omega_star(N)
    rho = dense_rho(build_A(StateSpace(N)), "sor", w)
    assert abs(rho / (w - 1) ** 0.75 - 1) < 1e-9
    assert abs(rho - want) < 1e-9
    assert rho > 1.05 * (w - 1), "Young's prediction rho = omega* - 1 fails for this matrix"


@pytest.mark.parametrize("N", [12, 20])
def test_young_omega_still_minimizes_rho(N):
    A = build_A(StateSpace(N))
    w = omega_star(N)
    best = dense_rho(A, "sor", w)
    for d in (-0.05, -0.01, -0.0025, 0.0025, 0.01, 0.05):
        assert dense_rho(A, "sor", w + d) > best + 1e-6, f"omega* {d:+} beats omega*"
