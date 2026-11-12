"""Stationary (splitting) methods for A u = b: Jacobi, Gauss-Seidel and SOR.

Write A = D + L + U (diagonal, strictly lower, strictly upper, in StateSpace order). Then
  Jacobi        x <- D^-1 (b - (L + U) x)                       (every unknown from the old iterate)
  SOR(omega)    x_i <- (1 - omega) x_i + omega (b_i - sum_{j != i} a_ij x_j) / a_ii,   i = 0, 1, ..., n - 1,
                using the newest values; Gauss-Seidel is omega = 1.
Here diag(A) = 1, so the Jacobi iteration matrix is Q = I - A: from x0 = 0 the k-th Jacobi iterate is
sum_{m<k} Q^m b, the game played forward k rounds.

Stopping rule (all three): the relative residual ||b - A x_k||_2 / ||b||_2 is computed for k = 0, 1, 2, ...
and the run stops at the first k where it is <= rtol, or at k = maxiter. The check comes before every sweep.

The sweeps and the residual are numba loops over the CSR arrays. Call warmup() before timing anything.
"""
import numpy as np
from numba import njit

MAXITER = 10 ** 7


# ---------------------------------------------------------------- numba kernels

@njit(cache=True)
def _jacobi_sweep(indptr, indices, data, diag, b, x, out):
    """out_i = (b_i - sum_{j != i} a_ij x_j) / a_ii, reading only the old iterate x."""
    for i in range(x.shape[0]):
        s = b[i]
        for idx in range(indptr[i], indptr[i + 1]):
            j = indices[idx]
            if j != i:
                s -= data[idx] * x[j]
        out[i] = s / diag[i]


@njit(cache=True)
def _sor_sweep(indptr, indices, data, diag, b, x, omega):
    """One forward SOR sweep in place: x_j for j < i are already new when row i is updated."""
    for i in range(x.shape[0]):
        s = b[i]
        for idx in range(indptr[i], indptr[i + 1]):
            j = indices[idx]
            if j != i:
                s -= data[idx] * x[j]
        x[i] = (1.0 - omega) * x[i] + omega * s / diag[i]


@njit(cache=True)
def _residual_norm(indptr, indices, data, b, x):
    """||b - A x||_2."""
    total = 0.0
    for i in range(x.shape[0]):
        r = b[i]
        for idx in range(indptr[i], indptr[i + 1]):
            r -= data[idx] * x[indices[idx]]
        total += r * r
    return np.sqrt(total)


# ---------------------------------------------------------------- the solvers

def _iterate(A, b, rtol, maxiter, x0, omega):
    """Shared driver. omega = None means Jacobi, otherwise forward SOR with that omega."""
    indptr, indices, data = A.indptr.astype(np.int64), A.indices.astype(np.int64), A.data.astype(float)
    diag = A.diagonal().astype(float)
    b = np.ascontiguousarray(b, dtype=float)
    x = np.zeros(len(b)) if x0 is None else np.array(x0, dtype=float)  # a copy: x0 is never modified
    work = np.empty_like(x)
    maxiter = MAXITER if maxiter is None else maxiter
    bnorm = np.linalg.norm(b)

    res = []
    k = 0
    while True:
        res.append(_residual_norm(indptr, indices, data, b, x) / bnorm)
        if res[-1] <= rtol or k == maxiter:
            break
        if omega is None:
            _jacobi_sweep(indptr, indices, data, diag, b, x, work)
            x, work = work, x
        else:
            _sor_sweep(indptr, indices, data, diag, b, x, omega)
        k += 1
    info = {"iterations": k, "converged": bool(res[-1] <= rtol), "residual_norms": np.array(res)}
    return x, info


def jacobi(A, b, rtol=1e-10, maxiter=None, x0=None):
    return _iterate(A, b, rtol, maxiter, x0, omega=None)


def sor(A, b, omega, rtol=1e-10, maxiter=None, x0=None):
    if not 0 < omega < 2:
        raise ValueError(f"SOR needs 0 < omega < 2, got {omega}")
    return _iterate(A, b, rtol, maxiter, x0, omega=float(omega))


def gauss_seidel(A, b, rtol=1e-10, maxiter=None, x0=None):
    return sor(A, b, 1.0, rtol=rtol, maxiter=maxiter, x0=x0)


# ---------------------------------------------------------------- theory: omega* and iteration matrices

def young_omega(rho_j):
    """Young's optimal omega for a consistently ordered matrix with Jacobi spectral radius rho_j."""
    return 2 / (1 + np.sqrt(1 - rho_j ** 2))


def iteration_matrix(A, method, omega=None):
    """Dense iteration matrix M (one sweep maps x to M x + c). Small n only.

    jacobi:              I - D^-1 A
    gauss_seidel / sor:  (D + omega L)^-1 ((1 - omega) D - omega U), omega = 1 for gauss_seidel.
    """
    Ad = A.toarray()
    D = np.diag(np.diag(Ad))
    if method == "jacobi":
        return np.eye(len(Ad)) - Ad / np.diag(Ad)[:, None]
    if method == "gauss_seidel":
        omega = 1.0
    elif method != "sor":
        raise ValueError(f"unknown method {method!r}")
    L, U = np.tril(Ad, -1), np.triu(Ad, 1)
    return np.linalg.solve(D + omega * L, (1 - omega) * D - omega * U)


def spectral_radius(M):
    """Largest |eigenvalue| of a dense matrix."""
    return float(np.max(np.abs(np.linalg.eigvals(M))))


def warmup():
    """Compile the numba kernels on a tiny problem (N = 10) so later timings exclude compile time."""
    from .matrix import build_A
    from .states import StateSpace

    A = build_A(StateSpace(10))
    b = np.ones(A.shape[0])
    jacobi(A, b, maxiter=2)
    sor(A, b, 1.5, maxiter=2)
