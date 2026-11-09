"""Chunk 1 acceptance tests: the exact spectrum of A = I - Q and its condition numbers.

Spec: plan/c01_spectrum.md. Skipped until gr/spectrum.py exists.
"""
import numpy as np
import pytest
import scipy.sparse.linalg as spla

spectrum = pytest.importorskip("gr.spectrum")

from gr.matrix import build_A, rhs_rounds, solve
from gr.states import StateSpace


@pytest.mark.parametrize("N", [5, 6, 10, 17, 30])
def test_eigenvalue_formula_matches_dense(N):
    """Method-of-images formula = every eigenvalue of A, to rounding."""
    A = build_A(StateSpace(N)).toarray()
    dense = np.linalg.eigvalsh(A)
    exact = spectrum.eigenvalues(N)
    assert exact.shape == dense.shape
    assert np.all(np.diff(exact) >= 0), "eigenvalues(N) must be sorted ascending"
    assert np.max(np.abs(exact - dense)) < 1e-12


@pytest.mark.parametrize("N", [6, 10, 40, 200])
def test_lambda_min_closed_form(N):
    assert abs(spectrum.lambda_min(N) - 4 / 3 * np.sin(np.pi / N) ** 2) < 1e-15
    assert abs(spectrum.lambda_min(N) - spectrum.eigenvalues(N)[0]) < 1e-13


@pytest.mark.parametrize("N", [6, 10, 40, 200])
def test_lambda_max_closed_form(N):
    want = 1.5 - (1 - np.cos(2 * np.pi / N)) / 3
    assert abs(spectrum.lambda_max(N) - want) < 1e-13
    assert abs(spectrum.lambda_max(N) - spectrum.eigenvalues(N)[-1]) < 1e-13


@pytest.mark.parametrize("N", [10, 50, 400])
def test_all_eigenvalues_in_open_interval(N):
    ev = spectrum.eigenvalues(N)
    assert ev.min() > 0 and ev.max() < 1.5


@pytest.mark.parametrize("N", [6, 15, 60])
def test_perron_vector(N):
    """v = sum_a sin(2 pi x_a / N) is positive and A v = lambda_min v."""
    S = StateSpace(N)
    v = spectrum.perron_vector(S)
    assert v.shape == (S.n,)
    assert v.min() > 0
    A = build_A(S)
    assert np.linalg.norm(A @ v - spectrum.lambda_min(N) * v) < 1e-12 * np.linalg.norm(v)


@pytest.mark.parametrize("N", [6, 10, 30, 80])
def test_kappa2(N):
    ev = np.linalg.eigvalsh(build_A(StateSpace(N)).toarray()) if N <= 30 else spectrum.eigenvalues(N)
    assert abs(spectrum.kappa2(N) / (ev[-1] / ev[0]) - 1) < 1e-12


def test_kappa2_reference_values():
    """Measured in the prototype with shift-invert Lanczos."""
    for N, want in [(10, 11.28), (20, 45.47), (40, 182.25), (80, 729.39), (160, 2917.9), (320, 11672.1)]:
        assert abs(spectrum.kappa2(N) / want - 1) < 1e-3


def test_kappa2_over_N2_tends_to_9_over_8pi2():
    limit = 9 / (8 * np.pi ** 2)
    vals = [spectrum.kappa2(N) / N ** 2 for N in (40, 80, 160, 320, 640)]
    assert all(v < limit for v in vals), "approached from below"
    assert np.all(np.diff(vals) > 0), "increasing in N"
    assert abs(vals[-1] / limit - 1) < 1e-5


@pytest.mark.parametrize("N", [6, 7, 10, 17, 30])
def test_kappa_inf_matches_dense(N):
    A = build_A(StateSpace(N)).toarray()
    dense = np.abs(A).sum(1).max() * np.abs(np.linalg.inv(A)).sum(1).max()
    assert abs(spectrum.kappa_inf(N) / dense - 1) < 1e-12


@pytest.mark.parametrize("N", [6, 30, 99, 300])
def test_kappa_inf_when_3_divides_N(N):
    """||A||_inf = 2 and A^{-1} 1 = t = 3 x1 x2 x3 / N, so kappa_inf = 2 max t = 2 N^2 / 9."""
    assert abs(spectrum.kappa_inf(N) - 2 * N ** 2 / 9) < 1e-9 * N ** 2


@pytest.mark.parametrize("N", [12, 20, 30])
def test_jacobi_rate_is_spectral_radius_of_Q(N):
    Q = np.eye((N - 1) * (N - 2) // 2) - build_A(StateSpace(N)).toarray()
    rho = np.abs(np.linalg.eigvals(Q)).max()
    assert abs(spectrum.jacobi_rate(N) - rho) < 1e-12
    assert abs(spectrum.jacobi_rate(N) - (1 + 2 * np.cos(2 * np.pi / N)) / 3) < 1e-14


def test_shift_invert_lanczos_agrees_at_N80():
    """The way you'd measure lambda_min without the formula."""
    A = build_A(StateSpace(80)).tocsc()
    lam = spla.eigsh(A, k=1, sigma=0, which="LM", return_eigenvectors=False)[0]
    assert abs(lam / spectrum.lambda_min(80) - 1) < 1e-10
