"""Chunk 4 acceptance tests: diagnosing the accuracy of tiny probabilities.

Spec: plan/c04_accuracy.md. Skipped until gr/accuracy.py exists.
Running example: b = rhs_out_first(S, 2) (player 3, the big stack, is out first). Its smallest entry is at
the state (1, 1, N-2), where it is about 9.1196 / N^3.
"""
import numpy as np
import pytest
import scipy.sparse as sp

acc = pytest.importorskip("gr.accuracy")

from gr.exact import exact_out_first
from gr.matrix import build_A, rhs_out_first, rhs_rounds, solve
from gr.states import StateSpace

try:
    import flint  # noqa: F401
    HAVE_FLINT = True
except ImportError:
    HAVE_FLINT = False
needs_flint = pytest.mark.skipif(not HAVE_FLINT, reason="python-flint not installed")

U = 2.0 ** -53


def setup(N):
    S = StateSpace(N)
    A = build_A(S).tocsr()
    b = rhs_out_first(S, 2)
    return S, A, b, S.index((1, 1, N - 2))


def dsolve(A):
    return lambda r: solve(A, r)


# ---------------------------------------------------------------- backward errors and conditioning

def test_backward_errors_on_a_hand_example():
    A = sp.csr_matrix(np.array([[2.0, -1.0], [-1.0, 2.0]]))
    b = np.array([1.0, 1.0])
    assert acc.normwise_backward_error(A, np.array([1.0, 1.0]), b) == 0
    assert acc.componentwise_backward_error(A, np.array([1.0, 1.0]), b) == 0
    x = np.array([1.1, 1.0])  # r = (-0.2, 0.1)
    assert abs(acc.normwise_backward_error(A, x, b) - 0.2 / (3 * 1.1 + 1)) < 1e-15
    assert abs(acc.componentwise_backward_error(A, x, b) - max(0.2 / 4.2, 0.1 / 4.1)) < 1e-15
    assert acc.U == U


def test_componentwise_backward_error_convention_for_zero_rows():
    """A row with |A||x| + |b| = 0 must also have residual 0 there; count it as 0 (0/0 = 0), never NaN.
    At x = 0 the residual is b, so omega = 1 (rows with b_i > 0 give 1, rows with b_i = 0 give 0/0)."""
    S, A, b, _ = setup(10)
    assert np.any(b == 0)
    assert acc.componentwise_backward_error(A, np.zeros(S.n), b) == 1.0


def test_relative_errors():
    got = acc.relative_errors(np.array([1.0, 2.2, -3.0]), np.array([1.0, 2.0, -2.0]))
    assert np.allclose(got, [0.0, 0.1, 0.5], rtol=1e-14, atol=0)


def test_entry_condition_matches_the_dense_formula():
    """cond_i = (|A^-1| (|A||x| + |b|))_i / |x_i|, computed here with a dense inverse."""
    S, A, b, _ = setup(10)
    x = solve(A, b)
    Ainv = np.linalg.inv(A.toarray())
    want = (np.abs(Ainv) @ (np.abs(A.toarray()) @ np.abs(x) + np.abs(b))) / np.abs(x)
    got = acc.entry_condition(A, b, x, dsolve(A))
    assert np.max(np.abs(got / want - 1)) < 1e-12


def test_entry_condition_is_twice_the_conditional_mean_time():
    """|A| = 2I - A and A x = b >= 0 give cond_i = 2 (A^-1 x)_i / x_i = 2 E_x[T | event]."""
    S, A, b, _ = setup(20)
    x = solve(A, b)
    cond = acc.entry_condition(A, b, x, dsolve(A))
    ET = acc.conditional_mean_time(A, x, dsolve(A))
    assert np.max(np.abs(cond - 2 * ET) / cond) < 1e-12
    assert cond.min() >= 1


def test_conditional_mean_time_of_the_sure_event():
    """x = 1 (b = A 1): E[T] = rounds until the first bust = 3 x1 x2 x3 / N."""
    S = StateSpace(20)
    A = build_A(S).tocsr()
    t = acc.conditional_mean_time(A, np.ones(S.n), dsolve(A))
    assert np.max(np.abs(t - 3.0 * S.x1 * S.x2 * S.x3 / 20)) < 1e-12 * t.max()


@pytest.mark.parametrize("N", [10, 20])
def test_worst_case_perturbation_attains_the_condition_number(N):
    """A -> A - eps|A|, b -> b + eps|b| raises every entry by eps * cond_i to first order."""
    S, A, b, _ = setup(N)
    x = solve(A, b)
    cond = acc.entry_condition(A, b, x, dsolve(A))
    eps = 1e-9
    Ap, bp = acc.worst_case_perturbation(A, b, eps)
    ratio = (solve(Ap, bp) - x) / x / (eps * cond)
    assert np.all(np.abs(ratio - 1) < 1e-3)


def test_random_perturbations_stay_below_the_bound():
    S, A, b, _ = setup(20)
    x = solve(A, b)
    cond = acc.entry_condition(A, b, x, dsolve(A))
    eps, rng = 1e-8, np.random.default_rng(221)
    Acoo = A.tocoo()
    worst = 0.0
    for _ in range(10):
        dA = sp.csr_matrix((eps * Acoo.data * rng.uniform(-1, 1, Acoo.nnz), (Acoo.row, Acoo.col)), shape=A.shape)
        db = eps * b * rng.uniform(-1, 1, S.n)
        worst = max(worst, np.max(np.abs(solve(A + dA, b + db) - x) / x / (eps * cond)))
    assert worst <= 1 + 1e-3


# ---------------------------------------------------------------- the tiny entry

def test_tiny_entry_is_the_smallest_and_worst_conditioned():
    S, A, b, tiny = setup(40)
    x = solve(A, b)
    cond = acc.entry_condition(A, b, x, dsolve(A))
    assert np.argmin(x) == tiny and np.argmax(cond) == tiny


@pytest.mark.parametrize("N,lo,hi", [(20, 9.11975, 9.11985), (40, 9.11955, 9.11965), (160, 9.119585, 9.119593)])
def test_tiny_entry_times_N_cubed(N, lo, hi):
    """N^3 P_(1,1,N-2)(3 out first) -> 9.119589 (9.119797 at N = 20, 9.119602 at N = 40)."""
    S, A, b, tiny = setup(N)
    assert lo < N ** 3 * solve(A, b)[tiny] < hi


def test_condition_of_tiny_entry_grows_like_N_squared():
    """cond / N^2 at (1, 1, N-2): 0.3846, 0.3874, 0.3881 for N = 20, 40, 80 (limit about 0.3884)."""
    vals = []
    for N in (20, 40, 80):
        S, A, b, tiny = setup(N)
        x = solve(A, b)
        vals.append(acc.entry_condition(A, b, x, dsolve(A))[tiny] / N ** 2)
    assert np.all(np.diff(vals) > 0)
    assert abs(vals[0] - 0.3846) < 1e-3 and abs(vals[2] - 0.3881) < 1e-3


# ---------------------------------------------------------------- exact reference

@needs_flint
def test_flint_solve_matches_the_fraction_solver():
    N = 8
    S = StateSpace(N)
    A = build_A(S).tocsr()
    got = acc.flint_solve(A, rhs_out_first(S, 2), 6 * N)
    exact = exact_out_first(N, 2)  # {state: Fraction}
    want = np.array([float(exact[S.state(i)]) for i in range(S.n)])
    assert np.max(np.abs(got - want) / want) < 1e-15


@needs_flint
def test_flint_solve_refuses_non_integer_scaling():
    S = StateSpace(8)
    A = build_A(S).tocsr()
    with pytest.raises(ValueError):
        acc.flint_solve(A, rhs_out_first(S, 2), 7)


@needs_flint
@pytest.mark.parametrize("N", [20, 40])
def test_direct_solve_is_accurate_in_every_entry(N):
    """Measured: relative error <= 2.1e-14 in every entry and omega = 2-4 u."""
    S, A, b, tiny = setup(N)
    xe = acc.flint_solve(A, b, 6 * N)
    x = solve(A, b)
    rel = acc.relative_errors(x, xe)
    omega = acc.componentwise_backward_error(A, x, b)
    cond = acc.entry_condition(A, b, xe, dsolve(A))
    assert rel.max() < 1e-13
    assert omega < 20 * U
    assert np.all(rel <= 2 * cond * max(omega, U))


@needs_flint
def test_residual_stopping_misses_the_tiny_entry():
    """CG at rtol 1e-10, N = 40 (measured): normwise error 4.7e-11, tiny-entry error 3.7e-8,
    normwise backward error 6e-12 but componentwise backward error 4.5e-9."""
    krylov = pytest.importorskip("gr.krylov")
    S, A, b, tiny = setup(40)
    xe = acc.flint_solve(A, b, 6 * 40)
    x, info = krylov.cg(A, b, rtol=1e-10)
    rel = acc.relative_errors(x, xe)
    normwise = np.max(np.abs(x - xe)) / np.max(xe)
    assert normwise < 1e-9
    assert rel[tiny] > 100 * normwise
    assert acc.componentwise_backward_error(A, x, b) > 100 * acc.normwise_backward_error(A, x, b)
