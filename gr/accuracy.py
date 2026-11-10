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


def conditional_mean_time(A, x, solve):
    """(A^{-1} x)_i / x_i = E_i[T | event], the expected rounds to the first bust given the event x."""
    return solve(x) / x


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
