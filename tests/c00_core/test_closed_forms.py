from fractions import Fraction

import numpy as np
import pytest

from gr.exact import exact_solve
from gr.matrix import build_A, rhs_rounds, rhs_win, solve
from gr.states import StateSpace


@pytest.mark.parametrize("N", [10, 50, 200])
def test_expected_rounds_to_first_bust(N):
    """t = 3 x1 x2 x3 / N solves A t = 1."""
    S = StateSpace(N)
    t = solve(build_A(S), rhs_rounds(S))
    exact = 3.0 * S.x1 * S.x2 * S.x3 / N
    assert np.max(np.abs(t - exact)) / np.max(exact) < 1e-10


@pytest.mark.parametrize("N", [10, 50, 200])
def test_win_probability(N):
    """P(player i wins) = x_i / N."""
    S = StateSpace(N)
    A = build_A(S)
    X = S.coords()
    for i in range(3):
        w = solve(A, rhs_win(S, i))
        assert np.max(np.abs(w - X[:, i] / N)) < 1e-10


@pytest.mark.parametrize("N", [5, 8])
def test_closed_forms_exactly_in_rationals(N):
    t = exact_solve(N, rhs_ones=True)
    w = exact_solve(N, lambda y: Fraction(y[0], N))
    for x in t:
        assert t[x] == Fraction(3 * x[0] * x[1] * x[2], N)
        assert w[x] == Fraction(x[0], N)
