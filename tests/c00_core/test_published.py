"""Values published by Diaconis & Ethier, "Gambler's Ruin and the ICM" (Statist. Sci. 2022)."""
from fractions import Fraction

from gr.exact import exact_order
from gr.matrix import order_probabilities
from gr.states import StateSpace


def test_123_order_321_exact():
    """(A, B, C) = (1, 2, 3): P(321) = 569/9456 (their Fig. 3)."""
    assert exact_order(6, 2, 1, 0)[(1, 2, 3)] == Fraction(569, 9456)


def test_123_full_row_exact():
    """Full row at (1,2,3) in 9456ths: 3287 2521 1441 1007 631 569."""
    S = StateSpace(6)
    P = order_probabilities(S)
    x = S.index((1, 2, 3))
    want = {"123": 3287, "132": 2521, "213": 1441, "231": 1007, "312": 631, "321": 569}
    for o, num in want.items():
        assert abs(P[o][x] - num / 9456) < 1e-14


def test_235_table9():
    S = StateSpace(10)
    P = order_probabilities(S)
    x = S.index((2, 3, 5))
    assert abs(P["213"][x] - 0.190419015064) < 1e-12
    assert abs(P["312"][x] - 0.0704242611225) < 1e-12
    assert abs(P["321"][x] - 0.0662121426098) < 1e-12


def test_table4_N300():
    """P_{1,1,298}(321) = 1.68881277854908e-7 (their Table 4)."""
    S = StateSpace(300)
    P = order_probabilities(S)
    x = S.index((1, 1, 298))
    assert abs(P["321"][x] / 1.68881277854908e-7 - 1) < 1e-9
