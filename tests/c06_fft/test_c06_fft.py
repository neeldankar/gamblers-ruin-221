"""Chunk 6 acceptance tests: the FFT (method of images) fast solver.

Spec: plan/c06_fft.md. Skipped until gr/fft_solver.py exists.

fft_solve(N, b) must solve the same system as build_A(StateSpace(N)), with b and x indexed by
StateSpace(N). Error levels quoted below were measured with an independent reference
implementation.
"""
import time

import numpy as np
import pytest

fft_solver = pytest.importorskip("gr.fft_solver")

from gr.exact import exact_order
from gr.matrix import build_A, rhs_order, rhs_out_first, solve
from gr.states import StateSpace


def random_b(n):
    return np.random.default_rng(221).standard_normal(n)


@pytest.mark.parametrize("N", [3, 4, 5, 6, 7, 12, 31, 50])
def test_matches_direct_solve(N):
    """Includes N = 3 (one live state), N not divisible by 3 and a prime N.
    Reference: relative difference from splu at most 1e-14."""
    S = StateSpace(N)
    b = random_b(S.n)
    x = fft_solver.fft_solve(N, b)
    assert isinstance(x, np.ndarray) and x.shape == (S.n,) and x.dtype == np.float64
    xd = solve(build_A(S), b)
    assert np.linalg.norm(x - xd) <= 1e-12 * np.linalg.norm(xd)


@pytest.mark.parametrize("N", [30, 61, 200])
def test_expected_rounds_closed_form(N):
    """A t = 1 with t = 3 x1 x2 x3 / N (chunk 0). Reference error at N = 200: 2e-13 of max t."""
    S = StateSpace(N)
    t = 3.0 * S.x1 * S.x2 * S.x3 / N
    x = fft_solver.fft_solve(N, np.ones(S.n))
    assert np.max(np.abs(x - t)) <= 1e-11 * np.max(t)


@pytest.mark.parametrize("N", [100, 101])
def test_small_residual(N):
    S = StateSpace(N)
    b = random_b(S.n)
    x = fft_solver.fft_solve(N, b)
    assert np.linalg.norm(b - build_A(S) @ x) <= 1e-12 * np.linalg.norm(b)


def test_linear_in_b():
    N = 40
    S = StateSpace(N)
    rng = np.random.default_rng(221)
    a, c = rng.standard_normal(S.n), rng.standard_normal(S.n)
    lhs = fft_solver.fft_solve(N, 2 * a - 3 * c)
    rhs = 2 * fft_solver.fft_solve(N, a) - 3 * fft_solver.fft_solve(N, c)
    assert np.linalg.norm(lhs - rhs) <= 1e-12 * np.linalg.norm(rhs)


@pytest.mark.parametrize("N", [20, 64])
def test_out_first_probabilities_sum_to_one(N):
    """Exactly one player is out first, so the three solutions add up to 1 at every state."""
    S = StateSpace(N)
    total = sum(fft_solver.fft_solve(N, rhs_out_first(S, i)) for i in range(3))
    assert np.max(np.abs(total - 1)) <= 1e-12


def test_order_probabilities_match_direct_solve():
    N = 45
    S = StateSpace(N)
    b = rhs_order(S, 0, 1, 2)
    x = fft_solver.fft_solve(N, b)
    xd = solve(build_A(S), b)
    assert np.linalg.norm(x - xd) <= 1e-12 * np.linalg.norm(xd)


def test_every_entry_accurate_at_N12_against_exact_rationals():
    """Componentwise check against Fractions (gr.exact). At N = 12 the smallest P(123) is 2.6e-3
    and the reference FFT gets every entry to 6e-14 relative (splu: 1e-15). At large N the FFT
    loses relative accuracy in the smallest entries; the spec's e06 experiment measures that."""
    N = 12
    S = StateSpace(N)
    exact = exact_order(N, 0, 1, 2)
    want = np.array([float(exact[S.state(i)]) for i in range(S.n)])
    x = fft_solver.fft_solve(N, rhs_order(S, 0, 1, 2))
    assert np.max(np.abs(x / want - 1)) <= 1e-11


def test_does_not_modify_b():
    N = 25
    b = random_b(StateSpace(N).n)
    keep = b.copy()
    fft_solver.fft_solve(N, b)
    assert np.array_equal(b, keep)


def test_fast_at_N400():
    """Soft check of O(n log n) work. Reference: 0.2 s at N = 400 (n = 79,401) on a slow 2-core
    machine, where splu takes 1 s. The 5 s limit only catches something far off, such as a dense
    matrix or a transform computed without the FFT."""
    N = 400
    b = np.ones(StateSpace(N).n)
    fft_solver.fft_solve(N, b)  # warm-up: caches and first-call costs
    t0 = time.perf_counter()
    fft_solver.fft_solve(N, b)
    assert time.perf_counter() - t0 < 5.0
