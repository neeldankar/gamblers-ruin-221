"""Exact spectrum and condition numbers of A = I - Q.

The live states form a triangle in the plane x1 + x2 + x3 = N. Q averages over the six
neighbours of the triangular lattice, and the boundary condition is zero on the edges, so the
eigenvectors are the sine modes of the equilateral triangle (method of images). For integers
k, l >= 1 with k + l <= N - 1 (exactly n = (N-1)(N-2)/2 pairs) the eigenvalues of A are

    lambda_kl = 1 - (1/3) [cos(2 pi (2k + l) / (3N)) + cos(2 pi (k + 2l) / (3N)) + cos(2 pi (k - l) / (3N))].
"""
import numpy as np

from .matrix import build_A
from .states import StateSpace


def eigenvalues(N):
    """All n eigenvalues of A, sorted ascending."""
    k, l = np.meshgrid(np.arange(1, N), np.arange(1, N), indexing="ij")
    keep = k + l <= N - 1
    k, l = k[keep], l[keep]
    c = 2 * np.pi / (3 * N)
    lam = 1 - (np.cos(c * (2 * k + l)) + np.cos(c * (k + 2 * l)) + np.cos(c * (k - l))) / 3
    return np.sort(lam)


def lambda_min(N):
    """Smallest eigenvalue, k = l = 1: 1 - (2 cos(2 pi/N) + 1)/3 = (4/3) sin^2(pi/N)."""
    return 4 / 3 * np.sin(np.pi / N) ** 2


def lambda_max(N):
    """Largest eigenvalue, at (k, l) = (1, N - 2).

    With theta = 2 pi/N the three cosines are cos(2pi/3) = -1/2, cos(4pi/3 - theta) and cos(2pi/3 - theta);
    the last two sum to -cos(theta), so lambda = 1 + (1/2 + cos theta)/3 = 3/2 - (1 - cos theta)/3.
    """
    return 1.5 - (1 - np.cos(2 * np.pi / N)) / 3


def kappa2(N):
    """2-norm condition number. A is SPD, so it is lambda_max / lambda_min."""
    return lambda_max(N) / lambda_min(N)


def kappa_inf(N):
    """inf-norm condition number ||A||_inf ||A^{-1}||_inf.

    A^{-1} = I + Q + Q^2 + ... has nonnegative entries, so ||A^{-1}||_inf is the largest entry of
    A^{-1} 1 = t, the expected number of rounds until the first bust: t = 3 x1 x2 x3 / N.
    ||A||_inf = 1 + (live neighbours)/6 is 2 once some state has all x_a >= 2 (N >= 6).
    """
    S = StateSpace(N)
    norm_A = abs(build_A(S)).sum(axis=1).max()
    max_t = 3 * S.coords().prod(axis=1).max() / N
    return norm_A * max_t


def perron_vector(S):
    """v(x) = sum_a sin(2 pi x_a / N): positive, with A v = lambda_min v (the k = l = 1 mode)."""
    return np.sin(2 * np.pi * S.coords() / S.N).sum(axis=1)


def jacobi_rate(N):
    """Spectral radius of Q = I - A, which is 1 - lambda_min (since lambda_max < 2 - lambda_min)."""
    return 1 - lambda_min(N)
