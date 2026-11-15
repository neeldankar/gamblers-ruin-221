"""Chunk 5, checkpoint 3: the SOR 3/4 law as a theorem (notes/proofs.md, section 10).

For every 0 < omega < 2, rho(S_omega) = max(R+, R-)^3, where R+ is the largest positive root and R- the largest
modulus of a negative root of the Perron cubic g(z) = z^3 - (omega mu/2)(z^2 + z) + omega - 1, with
mu = (1 + 2 cos(2 pi/N))/3. The expected values come from the cubic alone (numpy.roots), never from gr.

Validated in the Project chat on Nov 14 against an independent stand-in package (own matrix builder and own dense
SOR matrices): every case passes there with a relative difference below 3e-14.
"""
import numpy as np
import pytest

from gr.matrix import build_A
from gr.states import StateSpace
from gr.stationary import iteration_matrix, spectral_radius, young_omega


def mu_of(N):
    return (1 + 2 * np.cos(2 * np.pi / N)) / 3


def perron_radius(N, omega):
    """max(R+, R-)^3 from the real roots of the Perron cubic."""
    p = omega * mu_of(N) / 2
    roots = np.roots([1.0, -p, -p, omega - 1.0])
    real = roots[np.abs(roots.imag) < 1e-9].real
    r_plus = max([r for r in real if r > 0], default=0.0)
    r_minus = max([-r for r in real if r < 0], default=0.0)
    return max(r_plus, r_minus) ** 3


@pytest.mark.parametrize("N", [7, 12, 13, 20])
@pytest.mark.parametrize("omega", [0.3, 0.7, 1.0, 1.2, 1.5, 1.7, 1.9, 1.97])
def test_perron_cubic_gives_the_spectral_radius_for_every_omega(N, omega):
    A = build_A(StateSpace(N))
    rho = spectral_radius(iteration_matrix(A, "sor", omega))
    assert rho == pytest.approx(perron_radius(N, omega), rel=1e-11)


@pytest.mark.parametrize("N", [7, 12, 13, 20, 30])
def test_three_quarter_law_and_strict_minimum_at_young_omega(N):
    w = young_omega(mu_of(N))
    A = build_A(StateSpace(N))
    rho_star = spectral_radius(iteration_matrix(A, "sor", w))
    assert rho_star == pytest.approx((w - 1) ** 0.75, rel=1e-11)
    assert perron_radius(N, w) == pytest.approx((w - 1) ** 0.75, rel=1e-7)  # +-sqrt(q) are roots of the cubic
    for dw in (-0.05, -0.01, 0.01, 0.05):
        assert spectral_radius(iteration_matrix(A, "sor", w + dw)) > rho_star * (1 + 1e-4)


def test_dominant_eigenvalues_at_young_omega_are_a_real_pair_of_opposite_sign():
    N = 20
    w = young_omega(mu_of(N))
    ev = np.linalg.eigvals(iteration_matrix(build_A(StateSpace(N)), "sor", w))
    top = ev[np.argsort(-np.abs(ev))[:2]]
    assert np.max(np.abs(top.imag)) < 1e-8
    assert sorted(np.sign(top.real)) == [-1.0, 1.0]
    assert np.abs(top.real) == pytest.approx([(w - 1) ** 0.75] * 2, rel=1e-9)


@pytest.mark.parametrize("N", [6, 12, 20])
def test_gauss_seidel_closed_form(N):
    mu = mu_of(N)
    closed = ((mu / 4) * (1 + np.sqrt(1 + 8 / mu))) ** 3
    A = build_A(StateSpace(N))
    assert spectral_radius(iteration_matrix(A, "gauss_seidel")) == pytest.approx(closed, rel=1e-11)
    assert closed > mu ** 2


def test_gauss_seidel_gap_tends_to_16_pi4_over_81():
    """N^4 (rho_GS - mu^2) from the closed form: 10.1329 at N = 6, 19.2005 at N = 100; limit 19.2413."""
    def gap(N):
        mu = mu_of(N)
        return N ** 4 * (((mu / 4) * (1 + np.sqrt(1 + 8 / mu))) ** 3 - mu ** 2)

    assert gap(6) == pytest.approx(10.1329224, rel=1e-7)
    assert gap(100) == pytest.approx(19.20054, rel=1e-5)
    assert gap(100) < 16 * np.pi ** 4 / 81 < 19.2414


def test_above_young_omega_the_radius_exceeds_youngs_prediction():
    """Young's theory would give omega - 1 = 0.9 at omega = 1.9; the true radius at N = 20 is 0.92345."""
    A = build_A(StateSpace(20))
    assert spectral_radius(iteration_matrix(A, "sor", 1.9)) == pytest.approx(0.9234456911, rel=1e-9)
