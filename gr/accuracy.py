"""Accuracy tools: forward and backward errors, the condition number of each entry, and an exact solve.

Why the tiny probabilities are well conditioned. A = I - Q with Q >= 0 and a zero diagonal, so |A| = 2I - A.
If A x = b with b >= 0, then |A||x| + |b| = (2I - A) x + b = 2x, and the condition number of entry i is
    cond_i = (A^{-1} (|A||x| + |b|))_i / x_i = 2 (A^{-1} x)_i / x_i.
A^{-1} x = sum_k Q^k x, and (Q^k x)_i = P_i(no bust in the first k rounds, and the event happens), so
(A^{-1} x)_i = E_i[T 1{event}] with T the rounds until the first bust. Hence cond_i = 2 E_i[T | event].
"""
from fractions import Fraction

import numpy as np
import scipy.sparse as sp

U = 2.0 ** -53  # unit roundoff of float64
DELTA_SIXTH = -2.0 ** -54  # fl(1/6) = (1 + DELTA_SIXTH) / 6 exactly: 1/6 rounds down when stored in float64


def relative_errors(x, x_true):
    """|x - x_true| / |x_true|, entry by entry."""
    return np.abs(x - x_true) / np.abs(x_true)


def normwise_backward_error(A, x, b):
    """Rigal-Gaches: ||b - A x||_inf / (||A||_inf ||x||_inf + ||b||_inf)."""
    r = b - A @ x
    norm_A = abs(A).sum(axis=1).max()  # infinity norm = largest absolute row sum
    return float(np.max(np.abs(r)) / (norm_A * np.max(np.abs(x)) + np.max(np.abs(b))))


def componentwise_backward_error(A, x, b):
    """Oettli-Prager: max_i |b - A x|_i / (|A||x| + |b|)_i. A row with denominator 0 counts as 0 (0/0 = 0)."""
    r = np.abs(b - A @ x)
    den = abs(A) @ np.abs(x) + np.abs(b)
    ratio = np.divide(r, den, out=np.zeros_like(r), where=den > 0)
    return float(ratio.max())


def entry_condition(A, b, x, solve):
    """cond_i = (A^{-1} (|A||x| + |b|))_i / |x_i|. solve(r) applies A^{-1}; since A^{-1} >= 0 (M-matrix),
    |A^{-1}| = A^{-1} and one extra solve gives every cond_i."""
    return solve(abs(A) @ np.abs(x) + np.abs(b)) / np.abs(x)


def structured_condition(A, b, x, row_sums, solve):
    """kappa_i = (A^{-1} v)_i / x_i with v_i = b_i + row_sums_i x_i + sum_{j != i} |a_ij| |x_i - x_j|.

    The structured condition number: every off-diagonal entry, every row sum and every b_i perturbed relatively
    by at most eps (diagonal rebuilt from them) moves entry i by at most eps kappa_i to first order, and the
    perturbation w_ij -> w_ij (1 + eps sign(x_j - x_i)), s -> s (1 - eps), b -> b (1 + eps) attains it in every
    entry at once. solve(r) applies A^{-1}. Hypotheses: off-diagonals <= 0, row sums >= 0, b >= 0, A^{-1} >= 0,
    x > 0. Derivation: notes/proofs.md, section 7."""
    C = sp.coo_matrix(A)
    off = C.row != C.col
    r, c, w = C.row[off], C.col[off], -C.data[off]  # w_ij = -a_ij >= 0
    v = b + row_sums * x + np.bincount(r, weights=w * np.abs(x[r] - x[c]), minlength=C.shape[0])
    return solve(v) / x


def conditional_mean_time(A, x, solve):
    """(A^{-1} x)_i / x_i = E_i[T | event], the expected rounds to the first bust given the event x."""
    return solve(x) / x


def data_error_term(x, solve):
    """DELTA_SIXTH * (A^{-1} x)_i / x_i = DELTA_SIXTH * E_i[T | event] = -(u/4) cond_i.

    The relative change of each entry caused by storing 1/6 in float64 (exactly: x' - x = d A_d^-1 x, and `solve`
    applies the stored inverse A_d^-1, so x (1 + data_error_term(x)) is the stored solution up to rounding):
    (x_stored - x_ideal)_i / x_i. Every float solver inherits it; an exact rational solve of the ideal system
    does not. Exact (to 1e-15 relative) for right-hand sides built from 1/6 alone (rhs_out_first); for rhs_order
    the individually rounded entries of b add about u. Derivation: notes/proofs.md, section 3."""
    return DELTA_SIXTH * solve(x) / x


def aposteriori_bound(A, b, x, solve):
    """(omega + 8u) cond_i, entry by entry: a bound on |x_stored - x|_i / |x_i| for a computed x.

    x_stored - x = A^{-1} r with A^{-1} >= 0, and |r| <= omega (|A||x| + |b|), so the error is at most omega cond_i.
    The 8u covers the rounding in evaluating the residual of a row with at most 7 nonzeros. Add
    abs(data_error_term) for the distance to the true probability. It is computed in floating point, so it is a
    bound to trust, not a machine-checked certificate (notes/proofs.md, section 5)."""
    return (componentwise_backward_error(A, x, b) + 8 * U) * entry_condition(A, b, x, solve)


def worst_case_perturbation(A, b, eps):
    """(A - eps|A|, b + eps|b|): the diagonal shrinks, every off-diagonal -1/6 grows in size, and b grows.
    All three push the solution up, so every entry rises by about eps * cond_i at once. A_pert is CSR."""
    return sp.csr_matrix(A - eps * abs(A)), b + eps * np.abs(b)


def flint_solve(A, b, scale):
    """Exact rational solve of (scale A) u = (scale b) with python-flint, each entry rounded correctly to
    float64. scale = 6N makes both sides integer here. Raises ValueError if they are not (to 1e-9).
    Dense, so only practical up to N = 80 (about 30 s)."""
    import flint  # only this function needs python-flint

    M = scale * sp.csr_matrix(A).toarray()
    c = scale * np.asarray(b, dtype=float)
    for name, arr in (("scale * A", M), ("scale * b", c)):
        if np.max(np.abs(arr - np.rint(arr))) > 1e-9:
            raise ValueError(f"{name} is not integer for scale = {scale}")
    Mf = flint.fmpz_mat(np.rint(M).astype(np.int64).tolist())
    cf = flint.fmpz_mat([[v] for v in np.rint(c).astype(np.int64).tolist()])
    u = Mf.solve(cf)  # an fmpq_mat: exact rationals
    return np.array([float(Fraction(int(u[i, 0].p), int(u[i, 0].q))) for i in range(u.nrows())])
