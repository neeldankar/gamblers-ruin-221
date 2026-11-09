"""Chunk 10 (optional) acceptance tests, part 1: least-squares regression of P / P_ICM.

Fit R_sigma = P_sigma / P_ICM_sigma over all states 1 <= A <= B <= C at N = 300 (7500 states) by a
sextic in x = A/N, y = B/N (28 monomials), with normal equations, Householder QR and the SVD.
Spec: plan/c10_extras.md. Skipped until gr/extras.py exists.
Every expected number below was computed by an independent reference implementation.
"""
import numpy as np
import pytest

extras = pytest.importorskip("gr.extras")

ORDERS = ("321", "312", "213")


@pytest.fixture(scope="module")
def fit_data():
    states, R = extras.ratio_targets(300)
    X = extras.design_matrix(states, 300)
    return states, R, X


@pytest.mark.parametrize("N", [30, 31, 32, 299, 300])
def test_regression_states(N):
    """Partitions of N into three positive parts: round(N^2 / 12) of them."""
    st = extras.regression_states(N)
    assert st.shape == (round(N * N / 12), 3)
    assert np.all(st[:, 0] >= 1)
    assert np.all(st[:, 0] <= st[:, 1]) and np.all(st[:, 1] <= st[:, 2])
    assert np.all(st.sum(axis=1) == N)
    assert len({tuple(r) for r in st}) == len(st)


def test_monomial_order():
    m = extras.monomials(6)
    assert len(m) == 28
    assert m[:10] == [(0, 0), (1, 0), (0, 1), (2, 0), (1, 1), (0, 2), (3, 0), (2, 1), (1, 2), (0, 3)]
    assert m[-7:] == [(6 - j, j) for j in range(7)]


def test_design_matrix_columns(fit_data):
    states, R, X = fit_data
    assert X.shape == (7500, 28)
    x, y = states[:, 0] / 300, states[:, 1] / 300
    assert np.all(X[:, 0] == 1)
    assert np.allclose(X[:, 1], x, rtol=1e-15) and np.allclose(X[:, 2], y, rtol=1e-15)
    assert np.allclose(X[:, 4], x * y, rtol=1e-14) and np.allclose(X[:, 27], y ** 6, rtol=1e-13)


def test_condition_numbers(fit_data):
    """cond(X) = 1.68436e7, and forming X^T X squares it (2.837e14)."""
    _, _, X = fit_data
    s = np.linalg.svd(X, compute_uv=False)
    assert abs(s[0] / s[-1] / 1.684364e7 - 1) < 1e-4
    ratio = np.linalg.cond(X.T @ X) / (s[0] / s[-1]) ** 2
    assert 0.5 < ratio < 2


def test_targets(fit_data):
    """R_321 at (1,1,298) = 1.68881e-7 / (1/(300*299)) = 0.0151486506; R = 1 at the center;
    R_213 = 1 whenever A = B (players 1 and 2 are then interchangeable)."""
    states, R, _ = fit_data
    assert set(R) == set(ORDERS)
    rows = {tuple(int(v) for v in s): k for k, s in enumerate(states)}
    assert abs(R["321"][rows[(1, 1, 298)]] - 0.0151486506236) < 1e-11
    for o in ORDERS:
        assert abs(R[o][rows[(100, 100, 100)]] - 1) < 1e-11
    on_diag = states[:, 0] == states[:, 1]
    assert np.max(np.abs(R["213"][on_diag] - 1)) < 1e-11


@pytest.mark.parametrize("order", ORDERS)
def test_qr_and_svd_agree(fit_data, order):
    _, R, X = fit_data
    y = R[order]
    b_svd = extras.fit_svd(X, y)
    b_qr = extras.fit_qr(X, y)
    assert b_qr.shape == (28,)
    assert np.linalg.norm(b_qr - b_svd) < 1e-7 * np.linalg.norm(b_svd)


def test_normal_equations_lose_digits(fit_data):
    """Same fit, worse coefficients: NE coefficients differ from the SVD's by 1e-7 to 4e-6 (relative),
    QR's by 1e-13 to 2e-11. Required here: NE at least 10x worse than QR for every order, and worse
    than 1e-7 for at least one."""
    _, R, X = fit_data
    worst = 0.0
    for o in ORDERS:
        y = R[o]
        b_svd = extras.fit_svd(X, y)
        e_qr = np.linalg.norm(extras.fit_qr(X, y) - b_svd) / np.linalg.norm(b_svd)
        e_ne = np.linalg.norm(extras.fit_normal_equations(X, y) - b_svd) / np.linalg.norm(b_svd)
        assert e_ne > 10 * e_qr, (o, e_ne, e_qr)
        worst = max(worst, e_ne)
    assert worst > 1e-7


@pytest.mark.parametrize("order", ORDERS)
def test_all_three_methods_give_the_same_fit(fit_data, order):
    """The residual is insensitive to coefficient errors along the small singular directions."""
    _, R, X = fit_data
    y = R[order]
    fits = [X @ f(X, y) for f in (extras.fit_svd, extras.fit_qr, extras.fit_normal_equations)]
    r_svd = np.linalg.norm(y - fits[0])
    for f in fits[1:]:
        assert np.max(np.abs(f - fits[0])) < 1e-8
        assert abs(np.linalg.norm(y - f) / r_svd - 1) < 1e-8


@pytest.mark.parametrize("order, max_residual", [("321", 5.638098e-06), ("312", 6.657670e-06), ("213", 3.796276e-02)])
def test_fit_quality(fit_data, order, max_residual):
    """The sextic fits 321 and 312 to about 1e-6 relative, but not 213: R_213 has a boundary layer at
    A = 1, 2 (its largest residual is at (1, 1, 298))."""
    states, R, X = fit_data
    y = R[order]
    r = y - X @ extras.fit_svd(X, y)
    assert abs(np.abs(r).max() / max_residual - 1) < 1e-3
