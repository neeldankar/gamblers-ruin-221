"""Chunk 2 acceptance tests: direct solvers, fill-in and orderings.

Spec: plan/c02_direct.md. Skipped until gr/direct.py exists.

Fill counts:
  * Cholesky-type methods (dense_cholesky, banded_cholesky, cholmod): nnz = stored entries of L,
    diagonal included.
  * splu: nnz = L.nnz + U.nnz. A is diagonally dominant, so SuperLU never pivots off the diagonal,
    L and U^T have the same pattern, and splu's count is exactly twice the Cholesky count for the
    same column ordering.
"""
import numpy as np
import pytest

direct = pytest.importorskip("gr.direct")

from gr.matrix import build_A, rhs_order, rhs_rounds, solve
from gr.states import StateSpace

try:
    import sksparse.cholmod  # noqa: F401
    HAVE_CHOLMOD = True
except ImportError:
    HAVE_CHOLMOD = False
needs_cholmod = pytest.mark.skipif(not HAVE_CHOLMOD, reason="scikit-sparse (CHOLMOD) not installed")

PAIRS = [
    pytest.param(m, o, marks=needs_cholmod) if m == "cholmod" else pytest.param(m, o)
    for m, orders in direct.ORDERINGS.items()
    for o in orders
]

ORDERS = ["123", "132", "213", "231", "312", "321"]


def natural_fill(N):
    """nnz(L) for the lexicographic order: the factor fills its whole envelope.

    Row (a, b) with a >= 2 reaches back exactly N - a places (to its neighbour (a-1, b));
    rows (1, b) reach back 1 place for b >= 2. Summing gives the formula below.
    """
    n = (N - 1) * (N - 2) // 2
    return n + (N - 3) + (N - 1) * (N - 2) * (N - 3) // 3


def problem(N):
    S = StateSpace(N)
    return S, build_A(S)


def order_rhs(S):
    return np.column_stack([rhs_order(S, int(o[0]) - 1, int(o[1]) - 1, int(o[2]) - 1) for o in ORDERS])


# ---------------------------------------------------------------- interface

def test_orderings_table():
    assert set(direct.ORDERINGS) == {"dense_cholesky", "banded_cholesky", "splu", "cholmod"}
    assert list(direct.ORDERINGS["dense_cholesky"]) == ["natural"]
    assert list(direct.ORDERINGS["banded_cholesky"]) == ["natural"]
    assert set(direct.ORDERINGS["splu"]) == {"NATURAL", "COLAMD", "MMD_AT_PLUS_A", "MMD_ATA"}
    assert {"natural", "amd", "metis", "nesdis"} <= set(direct.ORDERINGS["cholmod"])


def test_unknown_method_or_ordering_raises():
    _, A = problem(10)
    with pytest.raises(ValueError):
        direct.factorize(A, "gaussian_magic", "natural")
    with pytest.raises(ValueError):
        direct.factorize(A, "splu", "NOT_AN_ORDERING")


def test_dense_refuses_large_problems():
    """n = 7021 at N = 120 is over MAX_DENSE_N = 6000: refuse before allocating."""
    assert direct.MAX_DENSE_N == 6000
    _, A = problem(120)
    with pytest.raises(ValueError):
        direct.factorize(A, "dense_cholesky", "natural")


def test_factor_attributes_and_info():
    _, A = problem(20)
    F = direct.factorize(A, "splu", "COLAMD")
    assert F.method == "splu" and F.ordering == "COLAMD"
    assert isinstance(F.nnz, (int, np.integer)) and F.nnz > 0
    assert isinstance(F.setup_time, float) and F.setup_time >= 0
    x, info = direct.direct_solve(A, np.ones(A.shape[0]), "splu", "COLAMD")
    assert {"setup_time", "solve_time", "nnz_factor"} <= set(info)
    assert info["setup_time"] >= 0 and info["solve_time"] >= 0
    assert info["nnz_factor"] == F.nnz


# ---------------------------------------------------------------- structure

@pytest.mark.parametrize("N", [4, 6, 30, 100])
def test_bandwidth_is_N_minus_2(N):
    _, A = problem(N)
    assert direct.bandwidth(A) == N - 2


@pytest.mark.parametrize("N", [5, 10, 30, 60])
def test_banded_fill_is_the_full_band(N):
    S, A = problem(N)
    n, p = S.n, N - 2
    assert direct.factorize(A, "banded_cholesky", "natural").nnz == n * (p + 1) - p * (p + 1) // 2


@pytest.mark.parametrize("N", [5, 10, 30])
def test_dense_fill_is_the_full_triangle(N):
    S, A = problem(N)
    assert direct.factorize(A, "dense_cholesky", "natural").nnz == S.n * (S.n + 1) // 2


@pytest.mark.parametrize("N", [4, 5, 10, 17, 30, 60, 100])
def test_natural_ordering_fills_exactly_the_envelope(N):
    _, A = problem(N)
    assert direct.factorize(A, "splu", "NATURAL").nnz == 2 * natural_fill(N)


@needs_cholmod
@pytest.mark.parametrize("N", [4, 10, 30, 100, 200])
def test_cholmod_natural_fill_formula(N):
    _, A = problem(N)
    assert direct.factorize(A, "cholmod", "natural").nnz == natural_fill(N)


def test_dense_cholesky_factor_has_no_cancellation():
    """A is an M-matrix, so Schur complements never cancel: numerical fill = structural fill."""
    _, A = problem(30)
    L = np.linalg.cholesky(A.toarray())
    assert np.count_nonzero(L) == natural_fill(30)


@pytest.mark.parametrize("N", [100, 200])
def test_splu_orderings_rank(N):
    """Symmetric minimum degree on A^T + A < COLAMD < natural (measured: 0.36 and 0.54 of natural at N=100)."""
    _, A = problem(N)
    fill = {o: direct.factorize(A, "splu", o).nnz for o in ("NATURAL", "COLAMD", "MMD_AT_PLUS_A")}
    assert fill["MMD_AT_PLUS_A"] < fill["COLAMD"] < fill["NATURAL"]


@needs_cholmod
@pytest.mark.parametrize("N,limit", [(100, 0.45), (200, 0.35)])
def test_cholmod_fill_reducing_orderings_beat_natural(N, limit):
    """Measured ratios to natural: about 0.37 at N = 100 and 0.24-0.26 at N = 200."""
    _, A = problem(N)
    for o in ("amd", "metis", "nesdis"):
        assert direct.factorize(A, "cholmod", o).nnz < limit * natural_fill(N), o


@needs_cholmod
def test_fill_growth_exponents():
    """Fill grows like n^1.5 for the natural order, like n^1.1-1.25 for fill-reducing orders."""
    (S1, A1), (S2, A2) = problem(100), problem(200)
    dlogn = np.log(S2.n / S1.n)
    nat = np.log(natural_fill(200) / natural_fill(100)) / dlogn
    assert 1.45 < nat < 1.55
    for o in ("amd", "metis", "nesdis"):
        slope = np.log(direct.factorize(A2, "cholmod", o).nnz / direct.factorize(A1, "cholmod", o).nnz) / dlogn
        assert 1.0 < slope < 1.35, (o, slope)


@pytest.mark.parametrize("method,ordering", PAIRS)
def test_column_counts_add_up_to_fill(method, ordering):
    S, A = problem(20)
    F = direct.factorize(A, method, ordering)
    c = np.asarray(F.column_counts())
    assert c.shape == (S.n,) and c.min() >= 1
    assert c.sum() == (F.nnz // 2 if method == "splu" else F.nnz)


def test_column_counts_dense_and_banded():
    S, A = problem(25)
    n, p = S.n, 23
    j = np.arange(n)
    assert np.array_equal(direct.factorize(A, "dense_cholesky", "natural").column_counts(), n - j)
    assert np.array_equal(direct.factorize(A, "banded_cholesky", "natural").column_counts(),
                          np.minimum(p + 1, n - j))


def test_natural_column_counts_match_dense_factor():
    """Same elimination structure, so the same multiset of column counts (a solver may postorder)."""
    _, A = problem(25)
    want = np.sort(np.count_nonzero(np.linalg.cholesky(A.toarray()), axis=0))
    assert np.array_equal(np.sort(direct.factorize(A, "splu", "NATURAL").column_counts()), want)
    if HAVE_CHOLMOD:
        assert np.array_equal(np.sort(direct.factorize(A, "cholmod", "natural").column_counts()), want)


# ---------------------------------------------------------------- accuracy

@pytest.mark.parametrize("method,ordering", PAIRS)
def test_forward_error_on_expected_rounds(method, ordering):
    """A t = 1 with t = 3 x1 x2 x3 / N exactly. Measured errors are 3e-15 to 5e-15 at N = 30."""
    S, A = problem(30)
    t = 3.0 * S.x1 * S.x2 * S.x3 / 30
    x, _ = direct.direct_solve(A, rhs_rounds(S), method, ordering)
    assert np.max(np.abs(x - t)) / np.max(t) < 1e-13


@pytest.mark.parametrize("method,ordering", PAIRS)
def test_agrees_with_reference_on_order_probabilities(method, ordering):
    S, A = problem(40)
    b = rhs_order(S, 0, 1, 2)
    x, _ = direct.direct_solve(A, b, method, ordering)
    ref = solve(A, b)
    assert np.max(np.abs(x - ref)) <= 1e-13 * np.max(np.abs(ref))


@pytest.mark.parametrize("method,ordering", PAIRS)
def test_one_factorization_many_right_hand_sides(method, ordering):
    """Factor once, solve all six orders as an n x 6 block; the six probabilities sum to 1."""
    S, A = problem(20)
    B = order_rhs(S)
    F = direct.factorize(A, method, ordering)
    X = F.solve(B)
    assert X.shape == B.shape
    for j in range(6):
        xj = F.solve(B[:, j])
        assert xj.shape == (S.n,)
        assert np.max(np.abs(X[:, j] - xj)) <= 1e-14 * np.max(np.abs(xj))
        assert np.max(np.abs(xj - solve(A, B[:, j]))) <= 1e-13 * np.max(np.abs(xj))
    assert np.max(np.abs(X.sum(axis=1) - 1)) < 1e-13
