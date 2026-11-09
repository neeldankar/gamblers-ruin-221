"""Chunk 8 acceptance tests: the Independent Chip Model (Malmuth-Harville) against exact probabilities.

Spec: plan/c08_icm.md. Skipped until gr/icm.py exists.
Every expected number below was computed by an independent reference implementation.
"""
import itertools

import numpy as np
import pytest

icm = pytest.importorskip("gr.icm")

from gr.matrix import order_probabilities
from gr.states import StateSpace

ORDERS = ["123", "132", "213", "231", "312", "321"]
PAYOUTS = [(50, 30, 20), (65, 35, 0), (100, 0, 0), (50, 50, 0)]


def _setup(N):
    S = StateSpace(N)
    X = S.coords()
    return S, X, order_probabilities(S), icm.icm_orders(X)


def test_icm_hand_example_N4():
    """From (2,1,1), P_ICM(ijk) = (x_k/N) * x_j/(N - x_k): 1/12, 1/12, 1/6, 1/4, 1/6, 1/4."""
    P = icm.icm_orders(np.array([[2, 1, 1]]))
    want = dict(zip(ORDERS, [1 / 12, 1 / 12, 1 / 6, 1 / 4, 1 / 6, 1 / 4]))
    assert set(P) == set(ORDERS)
    for o in ORDERS:
        assert np.shape(P[o]) == (1,)
        assert abs(P[o][0] - want[o]) < 1e-15


@pytest.mark.parametrize("N", [7, 50])
def test_icm_orders_sum_to_one(N):
    _, _, _, C = _setup(N)
    assert np.max(np.abs(sum(C.values()) - 1)) < 1e-14


@pytest.mark.parametrize("N", [7, 50])
def test_icm_first_place_is_exact(N):
    """Orders ending in k sum to x_k / N, the exact win probability."""
    _, X, _, C = _setup(N)
    for k in range(3):
        wins = sum(C[o] for o in ORDERS if o[2] == str(k + 1))
        assert np.max(np.abs(wins - X[:, k] / N)) < 1e-15


def test_icm_relabeling():
    """Same symmetry as the exact chain: P_ICM(ijk) at x = P_ICM(123) at (x_i, x_j, x_k)."""
    rng = np.random.default_rng(221)
    X = rng.integers(1, 40, size=(25, 3))
    C = icm.icm_orders(X)
    for i, j, k in itertools.permutations(range(3)):
        moved = icm.icm_orders(X[:, [i, j, k]])["123"]
        assert np.max(np.abs(C[f"{i+1}{j+1}{k+1}"] - moved)) < 1e-15


def test_place_probabilities_N4_by_hand():
    """Player 1 at (2,1,1). Exact: 1/2, 5/14, 1/7 (from the six exact orders). ICM: 1/2, 1/3, 1/6."""
    S = StateSpace(4)
    x = S.index((2, 1, 1))
    exact = icm.place_probabilities(order_probabilities(S), 0)
    assert exact.shape == (3, S.n)
    assert np.max(np.abs(exact[:, x] - [1 / 2, 5 / 14, 1 / 7])) < 1e-14
    model = icm.place_probabilities(icm.icm_orders(np.array([[2, 1, 1]])), 0)
    assert model.shape == (3, 1)
    assert np.max(np.abs(model[:, 0] - [1 / 2, 1 / 3, 1 / 6])) < 1e-15


@pytest.mark.parametrize("player", [0, 1, 2])
def test_place_probabilities_rows(player):
    """Rows are 1st, 2nd, 3rd place; they sum to 1 and row 0 is x / N for exact and ICM alike."""
    S, X, P, C = _setup(30)
    for orders in (P, C):
        pl = icm.place_probabilities(orders, player)
        assert pl.shape == (3, S.n)
        assert np.max(np.abs(pl.sum(axis=0) - 1)) < 1e-12
        assert np.max(np.abs(pl[0] - X[:, player] / 30)) < 1e-12


def test_equity_is_payout_weighted_places():
    places = np.array([[0.5, 0.2], [0.3, 0.3], [0.2, 0.5]])
    assert np.allclose(icm.equity(places, (50, 30, 20)), [50 * 0.5 + 30 * 0.3 + 20 * 0.2, 50 * 0.2 + 30 * 0.3 + 20 * 0.5])
    assert np.allclose(icm.equity(places, (1, 0, 0)), places[0])


@pytest.mark.parametrize("N", [30, 60])
@pytest.mark.parametrize("payouts", PAYOUTS)
def test_equity_error_identity(N, payouts):
    """First place is exact in the ICM, so equity error = (w2 - w3) * (P_ICM(2nd) - P(2nd))."""
    _, _, P, C = _setup(N)
    w2, w3 = payouts[1], payouts[2]
    for player in range(3):
        ex = icm.place_probabilities(P, player)
        mo = icm.place_probabilities(C, player)
        err = icm.equity(mo, payouts) - icm.equity(ex, payouts)
        assert np.max(np.abs(err - (w2 - w3) * (mo[1] - ex[1]))) < 1e-11


# Wikipedia "Independent Chip Model" table: 200 chips, payouts 50/30/20, player 1's stack listed first.
# Columns: P(1st), P(2nd), P(3rd), equity. "FEM" there is the exact answer, printed to 4 or 6 digits.
PUBLISHED = {
    (25, 87, 88): dict(icm=(0.125, 0.1944, 0.6806, 25.69), fem=(0.125, 0.1584, 0.7166, 25.33), digits=1e-4),
    (21, 89, 90): dict(icm=(0.105, 0.1701, 0.7249, 24.85), fem=(0.105, 0.1346, 0.7604, 24.50), digits=1e-4),
    (198, 1, 1): dict(icm=(0.99, 0.009950, 0.000050, 49.80), fem=(0.99, 0.009999, 0.000001, 49.80), digits=1e-6),
}
# Our exact values (reference implementation, sparse direct solve): P(2nd), P(3rd), equity.
EXACT_N200 = {
    (25, 87, 88): (0.158408007121, 0.716591992879, 25.3340800712),
    (21, 89, 90): (0.134640012776, 0.760359987224, 24.4964001278),
    (198, 1, 1): (9.998860051372e-03, 1.139948627676e-06, 49.7999886005),
}


@pytest.fixture(scope="module")
def n200():
    return _setup(200)


@pytest.mark.parametrize("stacks", list(PUBLISHED))
def test_wikipedia_table_N200(n200, stacks):
    S, X, P, C = n200
    x = S.index(stacks)
    ex = icm.place_probabilities(P, 0)[:, x]
    mo = icm.place_probabilities(C, 0)[:, x]
    pub = PUBLISHED[stacks]
    half = pub["digits"] / 2
    # Exact matches the printed exact ("FEM") row to print precision.
    assert np.max(np.abs(ex - pub["fem"][:3])) <= half + 1e-12
    assert abs(icm.equity(ex, (50, 30, 20)) - pub["fem"][3]) <= 0.005
    # The printed ICM row was truncated, not rounded, so allow one unit in the last digit.
    assert np.max(np.abs(mo - pub["icm"][:3])) <= pub["digits"] + 1e-12
    assert abs(icm.equity(mo, (50, 30, 20)) - pub["icm"][3]) <= 0.005


@pytest.mark.parametrize("stacks", list(EXACT_N200))
def test_wikipedia_rows_to_ten_digits(n200, stacks):
    S, X, P, C = n200
    x = S.index(stacks)
    ex = icm.place_probabilities(P, 0)[:, x]
    p2, p3, eq = EXACT_N200[stacks]
    assert abs(ex[1] - p2) < 1e-10
    assert abs(ex[2] - p3) < 1e-10 * max(1.0, p3) and abs(ex[2] / p3 - 1) < 1e-7
    assert abs(icm.equity(ex, (50, 30, 20)) - eq) < 1e-8


def test_largest_second_place_error_N60():
    """max over states and players of |P_ICM(2nd) - P(2nd)| = 0.0359655670 at a permutation of (7, 26, 27).
    The runner-up (7, 25, 28) is 7.5e-5 lower, so the location is unambiguous."""
    S, X, P, C = _setup(60)
    best, where = 0.0, None
    for player in range(3):
        d = np.abs(icm.place_probabilities(C, player)[1] - icm.place_probabilities(P, player)[1])
        i = int(np.argmax(d))
        if d[i] > best:
            best, where = d[i], tuple(sorted(S.state(i)))
    assert abs(best - 0.0359655670) < 1e-9
    assert where == (7, 26, 27)


@pytest.mark.parametrize("N", [30, 61])
def test_icm_overrates_short_stacks_and_underrates_big_stacks(N):
    """At every state except the all-equal one: a shortest stack (ties allowed) has P_ICM(2nd) > P(2nd),
    and a largest stack has P_ICM(2nd) < P(2nd)."""
    S, X, P, C = _setup(N)
    D = np.array([icm.place_probabilities(C, p)[1] - icm.place_probabilities(P, p)[1] for p in range(3)])
    for idx in range(S.n):
        x = X[idx]
        if x.min() == x.max():
            continue
        for p in np.flatnonzero(x == x.min()):
            assert D[p, idx] > 0, f"short stack not overrated at {S.state(idx)}"
        for p in np.flatnonzero(x == x.max()):
            assert D[p, idx] < 0, f"big stack not underrated at {S.state(idx)}"


@pytest.mark.parametrize("N", [30, 90])
def test_center_state_is_exact_for_icm(N):
    S, X, P, C = _setup(N)
    c = S.index((N // 3, N // 3, N // 3))
    for o in ORDERS:
        assert abs(P[o][c] - 1 / 6) < 1e-12
        assert abs(C[o][c] - 1 / 6) < 1e-15


@pytest.mark.parametrize("N", [60, 120])
def test_big_stack_busting_first(N):
    """From (N-2, 1, 1): exact P(player 1 out first) * N^3 = 9.11959 (to 1e-4 relative at these N),
    while the ICM gives 2 / (N (N - 1)), so the ICM's relative error grows like N / 4.56."""
    S, X, P, C = _setup(N)
    x = S.index((N - 2, 1, 1))
    ex3 = icm.place_probabilities(P, 0)[2, x]
    mo3 = icm.place_probabilities(C, 0)[2, x]
    assert abs(ex3 * N ** 3 / 9.11959 - 1) < 1e-4
    assert abs(mo3 - 2 / (N * (N - 1))) < 1e-15
    want_rel = {60: 12.3815091, 120: 25.5381260}[N]
    assert abs((mo3 - ex3) / ex3 - want_rel) < 1e-5


def _proportional(N):
    S = StateSpace(N)
    P = order_probabilities(S)
    x = S.index((N // 5, 3 * N // 10, N // 2))
    return np.array([P[o][x] for o in ORDERS])


def test_proportional_stacks_converge_at_fourth_order():
    """At (0.2N, 0.3N, 0.5N) the six probabilities converge like N^-4: the observed order
    log2(|P(N/2) - P(N/4)| / |P(N) - P(N/2)|) is in [3.9, 4.1] for N = 80, 160, 320."""
    vals = {N: _proportional(N) for N in (20, 40, 80, 160, 320)}
    for N in (80, 160, 320):
        d_prev = np.abs(vals[N // 2] - vals[N // 4])
        d_last = np.abs(vals[N] - vals[N // 2])
        order = np.log2(d_prev / d_last)
        assert np.all(order > 3.9) and np.all(order < 4.1), (N, order)


def test_icm_error_survives_the_limit():
    """At (0.2N, 0.3N, 0.5N), exact P(player 1 2nd) -> 0.2607768223 but the ICM gives 2/7 at every N."""
    v = _proportional(320)
    p1_second = v[ORDERS.index("213")] + v[ORDERS.index("312")]
    assert abs(p1_second - 0.2607768224) < 1e-9
    C = icm.icm_orders(np.array([[64, 96, 160]]))
    assert abs(C["213"][0] + C["312"][0] - 2 / 7) < 1e-15
