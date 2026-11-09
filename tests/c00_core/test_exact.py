from fractions import Fraction

import numpy as np
import pytest

from gr.exact import exact_order, exact_out_first, exact_solve
from gr.matrix import build_A, rhs_order, rhs_out_first, rhs_rounds, solve
from gr.states import StateSpace


def test_N4_hand_example():
    """By hand: from (2,1,1) player 1 busts first w.p. 1/7; from (1,2,1) w.p. 3/7."""
    h = exact_out_first(4, 0)
    assert h[(2, 1, 1)] == Fraction(1, 7)
    assert h[(1, 2, 1)] == Fraction(3, 7)
    assert h[(1, 1, 2)] == Fraction(3, 7)
    S = StateSpace(4)
    hf = solve(build_A(S), rhs_out_first(S, 0))
    assert abs(hf[S.index((2, 1, 1))] - 1 / 7) < 1e-15
    assert abs(hf[S.index((1, 2, 1))] - 3 / 7) < 1e-15


@pytest.mark.parametrize("N", [4, 6, 9, 12, 15])
def test_float_matches_exact(N):
    S = StateSpace(N)
    A = build_A(S)
    pairs = [
        (solve(A, rhs_out_first(S, 0)), exact_out_first(N, 0)),
        (solve(A, rhs_order(S, 0, 1, 2)), exact_order(N, 0, 1, 2)),
        (solve(A, rhs_rounds(S)), exact_solve(N, rhs_ones=True)),
    ]
    for u, ex in pairs:
        for i in range(S.n):
            assert abs(u[i] - float(ex[S.state(i)])) < 1e-12
