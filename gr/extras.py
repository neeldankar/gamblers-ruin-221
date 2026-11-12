"""Chunk 10 extras: a least-squares lab and unequal skill (Bradley-Terry).

Part A, least squares. R_sigma = P_sigma / P_ICM_sigma over all states 1 <= A <= B <= C is fit by a
polynomial in x = A/N, y = B/N. The same problem is solved three ways: normal equations (squares cond(X)),
Householder QR and the SVD.

Part B, unequal skill. Each round an unordered pair {a, b} is chosen with probability 1/3 and a beats b with
probability s_a / (s_a + s_b). A = I - Q is not symmetric, but the chain is reversible with
pi(x) = prod s_i^{x_i}, so S = D^{1/2} A D^{-1/2} (D = diag(pi)) is symmetric. pi spans 2^(N-3), so S is
built from log pi and pi itself is never formed.
"""
import numpy as np
import scipy.linalg as la
import scipy.sparse as sp

from .icm import icm_orders
from .matrix import order_probabilities
from .states import MOVES, StateSpace


# ---------------------------------------------------------------- Part A: regression

def regression_states(N):
    """All (A, B, C) with 1 <= A <= B <= C and A + B + C = N, in lexicographic order. Shape (m, 3)."""
    rows = []
    for a in range(1, N // 3 + 1):
        for b in range(a, (N - a) // 2 + 1):  # keeps c = N - a - b >= b
            rows.append((a, b, N - a - b))
    return np.array(rows, dtype=np.int64)


def monomials(degree=6):
    """Exponents (i, j) of x^i y^j: by total degree d, then x^d, x^(d-1) y, ..., y^d."""
    return [(d - j, j) for d in range(degree + 1) for j in range(d + 1)]


def design_matrix(states, N, degree=6):
    """One column x^i y^j per monomial, x = A/N, y = B/N."""
    states = np.asarray(states)
    x = states[:, 0] / N
    y = states[:, 1] / N
    return np.column_stack([x**i * y**j for i, j in monomials(degree)])


def ratio_targets(N, orders=("321", "312", "213")):
    """States from regression_states(N), and per order the ratio P / P_ICM there (players 1, 2, 3 hold A, B, C)."""
    states = regression_states(N)
    S = StateSpace(N)
    P = order_probabilities(S)
    rows = S.lookup[states[:, 0], states[:, 1]]
    icm = icm_orders(states)
    return states, {o: P[o][rows] / icm[o] for o in orders}


def fit_normal_equations(X, y):
    """Solve X^T X beta = X^T y by Cholesky. Forming X^T X squares the condition number."""
    factor = la.cho_factor(X.T @ X)
    return la.cho_solve(factor, X.T @ y)


def fit_qr(X, y):
    """Householder QR (LAPACK, via numpy): X = Q R, then R beta = Q^T y."""
    Q, R = np.linalg.qr(X)  # reduced: Q is m x p, R is p x p
    return la.solve_triangular(R, Q.T @ y)


def fit_svd(X, y):
    """Thin SVD: X = U diag(s) V^T, beta = V (U^T y / s)."""
    U, s, Vt = np.linalg.svd(X, full_matrices=False)
    return Vt.T @ ((U.T @ y) / s)


# ---------------------------------------------------------------- Part B: Bradley-Terry

def _move_prob(skills, a, b):
    """P(the round moves a chip from b to a) = (1/3) s_a / (s_a + s_b). Equal skills give exactly 1/6."""
    return skills[a] / (3.0 * (skills[a] + skills[b]))


def build_A_bt(S, skills):
    """A = I - Q, Q(x, x + e_a - e_b) = (1/3) s_a / (s_a + s_b), as a CSR matrix (not symmetric)."""
    X = S.coords()
    rows, cols, vals = [np.arange(S.n)], [np.arange(S.n)], [np.ones(S.n)]
    for a, b in MOVES:
        Y = X.copy()
        Y[:, a] += 1
        Y[:, b] -= 1
        live = Y.min(axis=1) >= 1
        rows.append(np.arange(S.n)[live])
        cols.append(S.lookup[Y[live, 0], Y[live, 1]])
        vals.append(np.full(live.sum(), -_move_prob(skills, a, b)))
    return sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(S.n, S.n))


def p2_win(y, s_k, s_j, N):
    """P(k reaches N before 0) from y chips, when k beats j with probability s_k / (s_k + s_j).

    With r = s_j / s_k the classical answer is (1 - r^y) / (1 - r^N). Written with l = log r:
      l < 0 (k stronger): expm1(y l) / expm1(N l), both terms in (-1, 0];
      l > 0 (k weaker):   r^(y - N) (1 - r^-y) / (1 - r^-N) = exp((y - N) l) expm1(-y l) / expm1(-N l),
    so nothing larger than 1 is ever formed (no overflow at N = 2000).
    """
    y = np.asarray(y, dtype=float)
    l = np.log(s_j / s_k)
    if l == 0:
        return y / N
    if l < 0:
        return np.expm1(y * l) / np.expm1(N * l)
    return np.exp((y - N) * l) * np.expm1(-y * l) / np.expm1(-N * l)


def rhs_win_bt(S, skills, i):
    """Right-hand side for P(player i wins): each busting move x -> y adds its probability times the
    two-player value p2_win(y_i) against the other survivor (0 if i is the one who busts)."""
    X = S.coords()
    b = np.zeros(S.n)
    for a, c in MOVES:  # a takes a chip from c
        if c == i:
            continue  # i busts: P(i wins) = 0 there
        Y = X.copy()
        Y[:, a] += 1
        Y[:, c] -= 1
        bust = Y[:, c] == 0
        other = 3 - i - c
        b[bust] += _move_prob(skills, a, c) * p2_win(Y[bust, i], skills[i], skills[other], S.N)
    return b


def log_pi(S, skills):
    """log pi(x) = sum_i x_i log s_i at every state (pi is the reversing measure)."""
    return S.coords() @ np.log(np.asarray(skills, dtype=float))


def symmetrize_bt(A, lp):
    """S = D^{1/2} A D^{-1/2}, D = diag(pi): S_xy = A_xy exp((lp_x - lp_y) / 2). pi is never formed."""
    C = sp.coo_matrix(A)
    data = C.data * np.exp((lp[C.row] - lp[C.col]) / 2)
    return sp.csr_matrix((data, (C.row, C.col)), shape=C.shape)
