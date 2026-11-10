"""Direct solvers for A u = b: dense, banded and sparse Cholesky, and SuperLU, under several orderings.

Every method returns a Factor that can be reused for many right-hand sides, reports how many entries
of the triangular factor it stores (nnz), and how many of those sit in each column (column_counts).

Fill counts:
  * Cholesky-type methods (dense_cholesky, banded_cholesky, cholmod): entries of L, diagonal included.
  * splu: L.nnz + U.nnz. A is diagonally dominant by columns (diagonal 1, at most six off-diagonals of
    -1/6), and Gaussian elimination keeps that property in every Schur complement. So in each column the
    diagonal is the largest entry, partial pivoting never swaps rows, U = D L^T, L and U^T have the same
    pattern, and the count is exactly twice the Cholesky count for the same column order. (SuperLU stores
    the unit diagonal of L, so both halves include the diagonal.)
"""
import time

import numpy as np
import scipy.linalg as sla
import scipy.sparse as sp
import scipy.sparse.linalg as spla

ORDERINGS = {
    "dense_cholesky": ["natural"],
    "banded_cholesky": ["natural"],
    "splu": ["NATURAL", "COLAMD", "MMD_AT_PLUS_A", "MMD_ATA"],
    "cholmod": ["natural", "amd", "metis", "nesdis"],
}

MAX_DENSE_N = 6000  # n x n doubles at n = 6000 is 288 MB


def bandwidth(A):
    """Largest |i - j| over the nonzeros of A. For our matrix it is N - 2: the neighbour (x1 - 1, x2 + 1)
    of state (x1, x2) sits N - 2 places away in the lexicographic order."""
    C = sp.coo_matrix(A)
    return int(np.max(np.abs(C.row - C.col)))


class Factor:
    """A factorization of A, ready to solve.

    method, ordering: which solver and which fill-reducing order produced it.
    nnz: stored entries of the factor (see the module docstring for what counts).
    setup_time: wall seconds for everything in factorize (conversion, ordering, factorization).
    """

    def __init__(self, method, ordering, nnz, setup_time, solve_fn, counts_fn):
        self.method = method
        self.ordering = ordering
        self.nnz = int(nnz)
        self.setup_time = float(setup_time)
        self._solve = solve_fn
        self._counts = counts_fn

    def solve(self, b):
        """Solve A x = b. b has shape (n,) or (n, k); x has the same shape."""
        b = np.asarray(b, dtype=float)
        return np.asarray(self._solve(b)).reshape(b.shape)

    def column_counts(self):
        """Length-n array: entry j = stored entries in column j of L, diagonal included."""
        return np.asarray(self._counts(), dtype=np.int64)


def _dense(A):
    n = A.shape[0]
    if n > MAX_DENSE_N:  # check before A.toarray() allocates n^2 doubles
        raise ValueError(f"dense_cholesky refuses n = {n} > MAX_DENSE_N = {MAX_DENSE_N}")
    c = sla.cho_factor(A.toarray(), lower=True)
    nnz = n * (n + 1) // 2  # the whole lower triangle is stored
    return nnz, (lambda b: sla.cho_solve(c, b)), (lambda: n - np.arange(n))


def _banded(A):
    """Lower band storage with p = bandwidth: ab[i, j] = A[j + i, j] for i = 0..p (row 0 is the diagonal,
    row i the i-th subdiagonal). The last i slots of row i lie below the matrix and are never used: those
    p(p+1)/2 corner slots are not counted in nnz. The Cholesky factor fills the whole band."""
    n, p = A.shape[0], bandwidth(A)
    A = sp.csr_matrix(A)
    ab = np.zeros((p + 1, n))
    for i in range(p + 1):
        ab[i, : n - i] = A.diagonal(-i)
    cb = sla.cholesky_banded(ab, lower=True)
    nnz = n * (p + 1) - p * (p + 1) // 2
    return nnz, (lambda b: sla.cho_solve_banded((cb, True), b)), (lambda: np.minimum(p + 1, n - np.arange(n)))


def _splu(A, ordering):
    lu = spla.splu(sp.csc_matrix(A), permc_spec=ordering)
    nnz = lu.L.nnz + lu.U.nnz  # exactly 2 x the Cholesky count, see the module docstring

    def counts():
        L = lu.L.tocsc()  # lu.L builds a copy of SuperLU's L
        return np.diff(L.indptr)

    return nnz, lu.solve, counts


def _cholmod(A, ordering):
    import sksparse.cholmod  # only this method needs scikit-sparse

    F = sksparse.cholmod.cho_factor(sp.csc_matrix(A), order=ordering)
    return F.nnz, F.solve, (lambda: F.colcount)


def factorize(A, method, ordering):
    """Factor the SPD matrix A with the given method and ordering (one of ORDERINGS[method])."""
    if method not in ORDERINGS:
        raise ValueError(f"unknown method {method!r}; choose from {list(ORDERINGS)}")
    if ordering not in ORDERINGS[method]:
        raise ValueError(f"ordering {ordering!r} is not one of {ORDERINGS[method]} for {method}")
    t0 = time.perf_counter()
    if method == "dense_cholesky":
        nnz, solve_fn, counts_fn = _dense(A)
    elif method == "banded_cholesky":
        nnz, solve_fn, counts_fn = _banded(A)
    elif method == "splu":
        nnz, solve_fn, counts_fn = _splu(A, ordering)
    else:
        nnz, solve_fn, counts_fn = _cholmod(A, ordering)
    setup_time = time.perf_counter() - t0
    return Factor(method, ordering, nnz, setup_time, solve_fn, counts_fn)


def direct_solve(A, b, method, ordering):
    """Factor A and solve A x = b. Returns x and {"setup_time", "solve_time", "nnz_factor"}."""
    F = factorize(A, method, ordering)
    t0 = time.perf_counter()
    x = F.solve(b)
    solve_time = time.perf_counter() - t0
    return x, {"setup_time": F.setup_time, "solve_time": solve_time, "nnz_factor": F.nnz}
