"""Conjugate gradients and preconditioners for the SPD system A u = b.

cg is our own preconditioned CG (not a wrapper of scipy's). It always stops on the unpreconditioned residual
from the CG recurrence, ||r_k||_2 <= rtol ||b||_2, so every preconditioner is judged by the same test.

Preconditioners (make_preconditioner):
  none    plain CG
  jacobi  r -> r / diag(A). Here diag(A) = 1, so this is the identity and changes nothing.
  ic0     incomplete Cholesky with zero fill: L has the pattern of tril(A) and (L L^T)_ij = A_ij on that pattern.
  mic0    modified IC(0): fill that IC(0) drops is subtracted from the diagonal instead, so (L L^T) 1 = A 1.
  amg     one V-cycle of pyamg's smoothed aggregation multigrid (a symmetric operator, so valid for CG).

The factorization loop and the two triangular solves are numba loops over CSR arrays. Call warmup() before
timing anything, so numba's compile time is not counted.
"""
import math
import time

import numpy as np
import scipy.sparse as sp
from numba import njit

PRECONDITIONERS = ["none", "jacobi", "ic0", "mic0", "amg"]


# ---------------------------------------------------------------- conjugate gradients

def cg(A, b, rtol=1e-10, maxiter=None, M=None, x0=None, callback=None):
    """Preconditioned CG for SPD A. M is a callable r -> z ~ A^{-1} r, or None for plain CG.

    Stops at the first k with ||r_k||_2 <= rtol ||b||_2 (r_k from the recurrence, never preconditioned),
    or after maxiter steps (default 10 n). callback(x_k) is called after every step.
    Returns x and {"iterations": k, "residuals": ||r_j|| / ||b|| for j = 0..k, "converged": bool}.
    """
    b = np.asarray(b, dtype=float)
    n = b.shape[0]
    if maxiter is None:
        maxiter = 10 * n
    bnorm = np.linalg.norm(b)
    if bnorm == 0:
        return np.zeros(n), {"iterations": 0, "residuals": np.array([0.0]), "converged": True}

    if x0 is None:
        x = np.zeros(n)
        r = b.copy()  # r_0 = b exactly, so the first relative residual is exactly 1
    else:
        x = np.array(x0, dtype=float)
        r = b - A @ x
    res = [np.linalg.norm(r) / bnorm]

    k = 0
    p = None
    rz_old = 0.0
    while res[-1] > rtol and k < maxiter:
        z = r if M is None else M(r)
        rz = r @ z
        p = z.copy() if p is None else z + (rz / rz_old) * p  # new search direction, A-conjugate to the old ones
        q = A @ p
        alpha = rz / (p @ q)  # step that minimizes the A-norm error along p
        x += alpha * p
        r -= alpha * q
        rz_old = rz
        k += 1
        res.append(np.linalg.norm(r) / bnorm)
        if callback is not None:
            callback(x)
    return x, {"iterations": k, "residuals": np.array(res), "converged": bool(res[-1] <= rtol)}


def cg_iteration_bound(kappa, rtol):
    """Steps that guarantee ||r_k||_2 <= rtol ||b||_2 for plain CG from x0 = 0: ceil((s/2) ln(2 s / rtol)), s = sqrt(kappa).

    Derivation. Chebyshev: ||e_k||_A <= 2 rho^k ||e_0||_A with rho = (s - 1)/(s + 1). With x0 = 0 we have
    r = A e, so ||r_k||_2 <= sqrt(lambda_max) ||e_k||_A and ||b||_2 = ||r_0||_2 >= sqrt(lambda_min) ||e_0||_A.
    Hence ||r_k|| / ||b|| <= 2 s rho^k, which is <= rtol once k >= ln(2 s / rtol) / ln(1/rho).
    Since ln(1/rho) = ln((s + 1)/(s - 1)) >= 2/s, k >= (s/2) ln(2 s / rtol) is enough.
    """
    s = math.sqrt(kappa)
    return int(math.ceil(s / 2 * math.log(2 * s / rtol)))


# ---------------------------------------------------------------- incomplete Cholesky

@njit(cache=True)
def _ilu0_ikj(indptr, indices, data, diag_pos, modified):
    """In-place ILU(0) of a CSR matrix with sorted column indices, row by row (IKJ form).

    Afterwards the strictly lower part of row i holds the multipliers l_ik of the unit lower factor, and
    the diagonal and upper part hold row i of U. For modified=True, every update that would land outside
    the pattern (dropped fill) is subtracted from the diagonal of row i instead.
    Returns -1, or the first row whose pivot u_ii is not positive.
    """
    n = indptr.shape[0] - 1
    pos = np.full(n, -1)  # pos[j] = index in data of entry (i, j) of the current row i, or -1
    for i in range(n):
        for idx in range(indptr[i], indptr[i + 1]):
            pos[indices[idx]] = idx
        for idx in range(indptr[i], diag_pos[i]):  # entries (i, k) with k < i, in increasing k
            k = indices[idx]
            data[idx] /= data[diag_pos[k]]  # l_ik = a_ik / u_kk
            lik = data[idx]
            for kj in range(diag_pos[k] + 1, indptr[k + 1]):  # entries (k, j) with j > k
                j = indices[kj]
                if pos[j] >= 0:
                    data[pos[j]] -= lik * data[kj]  # in the pattern: ordinary elimination
                elif modified:
                    data[diag_pos[i]] -= lik * data[kj]  # dropped fill goes to the diagonal (MIC)
        if data[diag_pos[i]] <= 0:
            return i
        for idx in range(indptr[i], indptr[i + 1]):
            pos[indices[idx]] = -1
    return -1


def ic0(A, modified=False):
    """IC(0) (modified=False) or MIC(0) (modified=True) of the SPD matrix A: lower triangular CSR L with the
    pattern of tril(A) and a positive diagonal. Raises ValueError if a pivot is not positive.

    ILU(0) of a symmetric matrix gives A ~ L_unit U with U = D L_unit^T (MIC's dropped fill is symmetric too,
    so this survives), hence L = L_unit diag(sqrt(d)).
    """
    A = sp.csr_matrix(A, dtype=float, copy=True)
    A.sort_indices()
    n = A.shape[0]
    indptr = A.indptr.astype(np.int64)
    indices = A.indices.astype(np.int64)
    rows = np.repeat(np.arange(n), np.diff(indptr))
    on_diag = np.flatnonzero(indices == rows)
    if len(on_diag) != n:
        raise ValueError("ic0 needs every diagonal entry in the sparsity pattern")
    diag_pos = on_diag  # sorted indices, one diagonal entry per row, so these are in row order

    data = A.data.copy()
    bad = _ilu0_ikj(indptr, indices, data, diag_pos, modified)
    if bad >= 0:
        raise ValueError(f"incomplete Cholesky breakdown: pivot {data[diag_pos[bad]]:.3g} <= 0 in row {bad}")

    sqrt_d = np.sqrt(data[diag_pos])
    lower = indices <= rows
    r, c = rows[lower], indices[lower]
    vals = np.where(c < r, data[lower] * sqrt_d[c], sqrt_d[r])  # l_ij sqrt(d_j) below, sqrt(d_i) on the diagonal
    L = sp.csr_matrix((vals, (r, c)), shape=(n, n))
    L.sort_indices()
    return L


@njit(cache=True)
def _forward(indptr, indices, data, r):
    """Solve L y = r, L lower triangular CSR with sorted indices (diagonal last in each row)."""
    n = r.shape[0]
    y = np.empty(n)
    for i in range(n):
        s = r[i]
        last = indptr[i + 1] - 1
        for idx in range(indptr[i], last):
            s -= data[idx] * y[indices[idx]]
        y[i] = s / data[last]
    return y


@njit(cache=True)
def _backward(indptr, indices, data, y):
    """Solve L^T z = y using the CSR rows of L as the columns of L^T, from the last row up."""
    n = y.shape[0]
    z = y.copy()
    for i in range(n - 1, -1, -1):
        last = indptr[i + 1] - 1
        z[i] /= data[last]
        for idx in range(indptr[i], last):
            z[indices[idx]] -= data[idx] * z[i]
    return z


def ic_preconditioner(L):
    """r -> (L L^T)^{-1} r by one forward and one backward substitution."""
    L = sp.csr_matrix(L)
    L.sort_indices()
    indptr, indices, data = L.indptr.astype(np.int64), L.indices.astype(np.int64), L.data.astype(float)

    def apply(r):
        y = _forward(indptr, indices, data, np.ascontiguousarray(r, dtype=float))
        return _backward(indptr, indices, data, y)

    return apply


# ---------------------------------------------------------------- the preconditioner factory

def make_preconditioner(A, kind):
    """Build preconditioner `kind` (one of PRECONDITIONERS) for A. Returns (M, setup_time in seconds)."""
    if kind not in PRECONDITIONERS:
        raise ValueError(f"unknown preconditioner {kind!r}; choose from {PRECONDITIONERS}")
    t0 = time.perf_counter()
    if kind == "none":
        M = None
    elif kind == "jacobi":
        d = A.diagonal()
        M = lambda r: r / d  # noqa: E731
    elif kind in ("ic0", "mic0"):
        M = ic_preconditioner(ic0(A, modified=(kind == "mic0")))
    else:
        import pyamg  # only this kind needs pyamg

        M = pyamg.smoothed_aggregation_solver(sp.csr_matrix(A)).aspreconditioner(cycle="V").matvec
    return M, float(time.perf_counter() - t0)


def warmup():
    """Compile the numba functions on a tiny problem (N = 10) so later timings exclude compile time."""
    from .matrix import build_A
    from .states import StateSpace

    S = StateSpace(10)
    A = build_A(S).tocsr()
    b = np.ones(S.n)
    for kind in ("ic0", "mic0"):
        M, _ = make_preconditioner(A, kind)
        cg(A, b, M=M)
