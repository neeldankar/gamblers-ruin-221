"""Three ways to get the tiny probabilities right (chunk 7).

1. cg_componentwise: CG that stops on the Oettli-Prager backward error of the true residual, not on ||r||.
2. iterative_refinement with accurate_residual: 6N A and 6N b are integers that stand for the IDEAL system
   (1/6 exactly), so b - A x computed from them with a compensated (Dot2) sum is the residual of the true problem.
   Refinement then removes the error of storing 1/6 in float64 as well as the solver's own error.
3. gth_solve: Gaussian elimination where every pivot comes from a row sum, so no step ever subtracts.

Error-free transformations (Dekker 1971, Knuth; used in Ogita, Rump and Oishi's Dot2):
  TwoSum(a, b) = (s, e) with s = fl(a + b) and s + e = a + b exactly.
  TwoProduct(a, b) = (p, e) with p = fl(a b) and p + e = a b exactly. Dekker splits each factor into a high and
  a low half of at most 26 significant bits, so every partial product fits in 53 bits and is exact.
"""
import numpy as np
import scipy.sparse as sp
from numba import njit

from .accuracy import U, componentwise_backward_error

SPLITTER = 2.0 ** 27 + 1.0  # Dekker's constant for float64: splits a double into two 26-bit halves


# ---------------------------------------------------------------- accurate residual

def integer_system(A, b, scale):
    """(scale A, scale b) with exactly integer values: CSR with sorted indices, and a float array.
    Raises ValueError if either is not integer to 1e-9 (for example scale = 7 here; scale = 6N works)."""
    Ai = sp.csr_matrix(A, dtype=float, copy=True) * scale
    Ai.sort_indices()
    B = scale * np.asarray(b, dtype=float)
    for name, vals in (("scale * A", Ai.data), ("scale * b", B)):
        if len(vals) and np.max(np.abs(vals - np.rint(vals))) > 1e-9:
            raise ValueError(f"{name} is not integer for scale = {scale}")
    Ai.data = np.rint(Ai.data)  # 6N fl(1/6) = N (1 - 2^-54) rounds to N: these are the ideal entries
    return Ai, np.rint(B)


@njit(cache=True)
def _two_sum(a, b):
    """s = fl(a + b) and the exact error e, so that s + e = a + b (Knuth, no branch)."""
    s = a + b
    bb = s - a
    e = (a - (s - bb)) + (b - bb)
    return s, e


@njit(cache=True)
def _split(a):
    """a = hi + lo exactly, each half with at most 26 significant bits (Dekker)."""
    c = SPLITTER * a
    hi = c - (c - a)
    return hi, a - hi


@njit(cache=True)
def _two_product(a, b):
    """p = fl(a b) and the exact error e, so that p + e = a b (Dekker; no fma needed)."""
    p = a * b
    ah, al = _split(a)
    bh, bl = _split(b)
    e = al * bl - (((p - ah * bh) - al * bh) - ah * bl)
    return p, e


@njit(cache=True)
def _integer_residual(indptr, indices, data, B, x):
    """B - Ai x row by row, as in Dot2: every product and every sum is split into its rounded value and its
    exact error, and the errors are added up in a compensation term c. The result is as accurate as if the
    sum had been computed in twice the working precision and then rounded once."""
    n = B.shape[0]
    r = np.empty(n)
    for i in range(n):
        s = B[i]
        c = 0.0
        for idx in range(indptr[i], indptr[i + 1]):
            p, pe = _two_product(data[idx], x[indices[idx]])  # Ai_ij x_j = p + pe exactly
            s, se = _two_sum(s, -p)  # old s - p = new s + se exactly
            c += se - pe  # what s is missing: the sum error, minus the product's low part
        r[i] = s + c
    return r


def _residual(Ai, B, x, scale):
    x = np.ascontiguousarray(x, dtype=float)
    return _integer_residual(Ai.indptr.astype(np.int64), Ai.indices.astype(np.int64), Ai.data, B, x) / scale


def accurate_residual(A, b, x, scale):
    """r = b - A x for the ideal system: (B - Ai x) / scale with error-free products and sums.
    Error of entry i: at most 2u |r_i| + about 64 u^2 (|A||x| + |b|)_i (Ogita, Rump and Oishi's Dot2 bound).
    That is about 2u only while the first term dominates; `exact_residual` is the exact (slow) version."""
    Ai, B = integer_system(A, b, scale)
    return _residual(Ai, B, x, scale)


def _scaled_ints(v):
    """Python integers V and a shift s with v[i] = V[i] / 2**s exactly."""
    v = np.asarray(v, dtype=float)
    m, e = np.frexp(v)
    M = np.ldexp(m, 53).astype(np.int64)  # exact: m has 53 significant bits
    s = int((53 - e).max())
    return [int(a) << (s - 53 + int(k)) for a, k in zip(M.tolist(), e.tolist())], s


def exact_residual(A, b, x, denom=1):
    """(b - A x) / denom with every entry correctly rounded. For checks only: a slow Python loop.

    The float values of A, b and x are converted to exact Python integers (each a multiple of a common power of
    2), each row is summed exactly, and one integer division rounds once. denom must be a positive integer.
    exact_residual(A, b, xhat) is the residual of the stored system; with Ai, B = integer_system(A, b, 6N),
    exact_residual(Ai, B, xhat, denom=6N) is the residual of the ideal system."""
    A = sp.csr_matrix(A)
    ip, ix = A.indptr, A.indices
    Ad, sa = _scaled_ints(A.data)
    X, sx = _scaled_ints(x)
    Bv, sb = _scaled_ints(b)
    if int(denom) != denom or denom < 1 or sa + sx < sb:
        raise ValueError("denom must be a positive integer (and b must not need more bits than A x)")
    up, D = sa + sx - sb, int(denom) << (sa + sx)
    r = np.empty(A.shape[0])
    for i in range(A.shape[0]):
        R = Bv[i] << up
        for k in range(ip[i], ip[i + 1]):
            R -= Ad[k] * X[ix[k]]
        r[i] = R / D  # Python's int / int is correctly rounded
    return r


# ---------------------------------------------------------------- iterative refinement

def iterative_refinement(A, b, solve, scale, x0=None, max_steps=10):
    """Refine x with the accurate residual: r = b - A x (ideal system), d = solve(r), x = x + d.

    solve(r) applies an approximate A^{-1} (a direct factor, or a sloppy inner CG). x starts as solve(b), or x0.
    Stops when the correction max_i |d_i| / |x_i| is at most 4u, or after max_steps steps.
    The 4u test is a stopping rule, not a proof of correct rounding.
    Returns x and {"steps": steps taken, "corrections": one per step, "converged": bool}.
    """
    Ai, B = integer_system(A, b, scale)  # built once, used in every step
    x = solve(np.asarray(b, dtype=float)) if x0 is None else np.array(x0, dtype=float)
    corrections = []
    converged = False
    for _ in range(max_steps):
        r = _residual(Ai, B, x, scale)
        d = solve(r)
        x = x + d
        corrections.append(float(np.max(np.abs(d) / np.abs(x))))
        if corrections[-1] <= 4 * U:
            converged = True
            break
    return x, {"steps": len(corrections), "corrections": np.array(corrections), "converged": converged}


# ---------------------------------------------------------------- GTH elimination

@njit(cache=True)
def _gth_factor(ub, s, pivots):
    """Symmetric Gaussian elimination on the upper band ub (ub[k, d] = a_{k, k+d}), driven by the row sums s.

    Signs: off-diagonals a_kj <= 0, row sums s_k >= 0, so every multiplier l = a_ik / pivot is <= 0 and -l >= 0.
      pivot_k = s_k + sum_j (-a_kj)        nonnegative terms
      s_i     = s_i + (-l) s_k             nonnegative + nonnegative
      a_ij    = a_ij + (-l) a_kj           nonpositive + nonpositive
    The diagonal ub[k, 0] is never used: it is recomputed from the row sum when row k becomes the pivot row.
    (The Schur complement's row sums are s_i - l s_k, because a_k. 1 = s_k - pivot_k.)
    Returns -1, or the first row with pivot <= 0."""
    n, w = ub.shape
    p = w - 1
    for k in range(n):
        piv = s[k]
        for d in range(1, p + 1):
            piv += -ub[k, d]
        if piv <= 0:
            return k
        pivots[k] = piv
        for d in range(1, p + 1):  # i = k + d; entries past the end of the matrix are 0 and skipped
            a = ub[k, d]
            if a == 0.0:
                continue
            i = k + d
            ml = -(a / piv)  # -l_ik >= 0
            s[i] += ml * s[k]
            for e in range(1, p - d + 1):  # j = i + e, so a_kj = ub[k, d + e] and a_ij = ub[i, e]
                ub[i, e] += ml * ub[k, d + e]
    return -1


@njit(cache=True)
def _gth_substitute(ub, pivots, b):
    """Forward (L y = b) then backward (U x = y) substitution. With b >= 0 and -l >= 0, -a_kj >= 0 and x >= 0,
    every addition is of two nonnegative numbers."""
    n, w = ub.shape
    p = w - 1
    y = b.copy()
    for k in range(n):
        for d in range(1, p + 1):
            a = ub[k, d]
            if a != 0.0:
                y[k + d] += -(a / pivots[k]) * y[k]  # the same -l_ik as in the factorization
    x = np.zeros(n)
    for k in range(n - 1, -1, -1):
        t = y[k]
        for d in range(1, p + 1):
            if k + d < n:
                t += -ub[k, d] * x[k + d]
        x[k] = t / pivots[k]
    return x


def gth_solve(A, b, row_sums):
    """Solve A x = b for a symmetric M-matrix A whose row sums are row_sums (>= 0), with b >= 0, by
    subtraction-free (GTH-style) elimination in natural order with band storage.

    Pass row_sums exactly, from boundary_rhs(S, lambda Y: np.ones(len(Y))), not as A @ 1 (that is a
    subtraction). Only the upper triangle's off-diagonals and the row sums are used; the diagonal of A is not.
    Raises ValueError for a positive off-diagonal entry, a negative row sum or a negative b."""
    from .direct import bandwidth

    A = sp.csr_matrix(A, dtype=float)
    C = sp.coo_matrix(A)
    s = np.array(row_sums, dtype=float)
    b = np.array(b, dtype=float)
    if np.any(C.data[C.row != C.col] > 0):
        raise ValueError("gth_solve needs every off-diagonal entry <= 0")
    if np.any(s < 0):
        raise ValueError("gth_solve needs every row sum >= 0")
    if np.any(b < 0):
        raise ValueError("gth_solve needs b >= 0")
    n, p = A.shape[0], bandwidth(A)
    ub = np.zeros((n, p + 1))
    upper = C.col > C.row
    ub[C.row[upper], C.col[upper] - C.row[upper]] = C.data[upper]
    pivots = np.empty(n)
    bad = _gth_factor(ub, s, pivots)
    if bad >= 0:
        raise ValueError(f"gth_solve: pivot <= 0 in row {bad} (A is singular)")
    return _gth_substitute(ub, pivots, b)


# ---------------------------------------------------------------- componentwise stopping

def cg_componentwise(A, b, tol, M=None, check_every=10, maxiter=None):
    """The CG recurrence of gr.krylov.cg (x0 = 0), stopped when the componentwise backward error of the TRUE
    residual, omega(x_k) = componentwise_backward_error(A, x_k, b), is at most tol.

    omega is evaluated at k = 0 and every check_every iterations (one extra product with A and one with |A|).
    maxiter defaults to 10 n. Returns x and {"iterations", "omegas" (k = 0, check_every, ...), "converged"}.
    """
    b = np.asarray(b, dtype=float)
    n = b.shape[0]
    if maxiter is None:
        maxiter = 10 * n
    x = np.zeros(n)
    r = b.copy()
    omegas = [componentwise_backward_error(A, x, b)]  # exactly 1 at x = 0 (0 if b = 0)

    k = 0
    p = None
    rz_old = 0.0
    while omegas[-1] > tol and k < maxiter:
        z = r if M is None else M(r)
        rz = r @ z
        if rz == 0:  # the recurrence residual is exactly 0: nothing left to do
            break
        p = z.copy() if p is None else z + (rz / rz_old) * p
        q = A @ p
        alpha = rz / (p @ q)
        x += alpha * p
        r -= alpha * q
        rz_old = rz
        k += 1
        if k % check_every == 0:
            omegas.append(componentwise_backward_error(A, x, b))
    return x, {"iterations": k, "omegas": np.array(omegas), "converged": bool(omegas[-1] <= tol)}
