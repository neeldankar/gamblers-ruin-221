import itertools
from fractions import Fraction

import numpy as np
import pytest

from gr.exact import exact_order
from gr.matrix import build_A, label, order_probabilities, rhs_order, rhs_out_first, solve
from gr.states import StateSpace


@pytest.mark.parametrize("N", [5, 30, 80])
def test_six_orders_sum_to_one(N):
    P = order_probabilities(StateSpace(N))
    assert np.max(np.abs(sum(P.values()) - 1)) < 1e-12


@pytest.mark.parametrize("N", [6, 30, 80])
def test_relabeling_matches_direct_solves(N):
    S = StateSpace(N)
    A = build_A(S)
    P = order_probabilities(S, A)
    for i, j, k in itertools.permutations(range(3)):
        direct = solve(A, rhs_order(S, i, j, k))
        assert np.max(np.abs(P[label((i, j, k))] - direct)) < 1e-12


@pytest.mark.parametrize("N", [6, 30])
def test_out_first_is_sum_of_two_orders(N):
    S = StateSpace(N)
    A = build_A(S)
    P = order_probabilities(S, A)
    h1 = solve(A, rhs_out_first(S, 0))
    assert np.max(np.abs(h1 - P["123"] - P["132"])) < 1e-12


@pytest.mark.parametrize("N", [6, 40])
def test_orders_ending_in_k_give_win_probability(N):
    S = StateSpace(N)
    P = order_probabilities(S)
    X = S.coords()
    for k in range(3):
        wins = sum(P[label(o)] for o in itertools.permutations(range(3)) if o[2] == k)
        assert np.max(np.abs(wins - X[:, k] / N)) < 1e-12


def test_N4_six_orders_exact():
    """From (2,1,1): 1/14, 1/14, 5/28, 1/4, 5/28, 1/4 for orders 123, 132, 213, 231, 312, 321."""
    want = {"123": Fraction(1, 14), "132": Fraction(1, 14), "213": Fraction(5, 28),
            "231": Fraction(1, 4), "312": Fraction(5, 28), "321": Fraction(1, 4)}
    for (i, j, k) in itertools.permutations(range(3)):
        assert exact_order(4, i, j, k)[(2, 1, 1)] == want[label((i, j, k))]
