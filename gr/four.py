"""Four-player gambler's ruin and its exact S3-lumped chain (chunk 9).

Chips (x1, x2, x3, x4), sum N. Each round one of the 12 ordered pairs (a, b) is chosen with probability 1/12
and player a takes one chip from player b. A state is live when every xi >= 1, so n = C(N-1, 3). As for three
players, A = I - Q with Q[x, y] = 1/12 for each live neighbour y; moves that bust a player feed the
right-hand side through the boundary value at the landing state.

The product identity (why A (6 x1 x2 x3 x4) = e2):
  In a move a <- b only x_a and x_b change, and x_a x_b -> (x_a + 1)(x_b - 1) = x_a x_b + x_b - x_a - 1.
  Times the other two stacks x_k x_l: the moves a <- b and b <- a together change e4 by -2 x_k x_l, so
  E[change in e4] = -(1/12) * 2 * sum over the 6 pairs of x_k x_l = -e2 / 6. A move that
  busts someone lands on e4 = 0, which is exactly what e4 gives there, so (I - Q) e4 = e2 / 6 on live states.

The lumped chain (LumpedSpace, build_lumped):
  Permuting players 1-3 maps the chain to itself, and the event "player 4 busts first" does not care about
  their labels. So the answer depends only on the multiset {x1, x2, x3}: store one sorted representative
  y1 <= y2 <= y3 per orbit. From y, each of the 12 moves lands on some state; sorting its first three
  entries gives the lumped landing state. This is an exact Markov chain (lumpable), about 6 times smaller.
  It is not symmetric, but w_y Q_L[y, z] = w_z Q_L[z, y] with w = orbit size (6, 3 or 1), because both sides
  count the 1/12-moves between the two whole orbits. Hence W^(1/2) A_L W^(-1/2) is symmetric positive definite.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

# The twelve moves: (a, b) means player a takes one chip from player b.
MOVES4 = [(a, b) for a in range(4) for b in range(4) if a != b]


def _pairs(R):
    """All (x2, x3) with x2, x3 >= 1 and x2 + x3 <= R - 1 (so the fourth stack is >= 1), in lexicographic order."""
    v = np.arange(1, R - 1)
    I, J = np.meshgrid(v, v, indexing="ij")
    keep = I + J <= R - 1
    return I[keep], J[keep]


class _Keyed:
    """Shared lookup: a state is found by its integer key (x1 (N+1) + x2) (N+1) + x3. The states are stored
    in lexicographic order of (x1, x2, x3), so the keys are sorted and np.searchsorted finds the index."""

    def _key(self, Y):
        Y = np.asarray(Y, dtype=np.int64)
        return (Y[:, 0] * (self.N + 1) + Y[:, 1]) * (self.N + 1) + Y[:, 2]

    def _index_array(self, Y):
        """Indices of the rows of Y (an (m, 4) array of states that are known to be in the space)."""
        return np.searchsorted(self.keys, self._key(Y))

    def coords(self):
        """Array of shape (n, 4): row i is the state with index i."""
        return self.X

    def state(self, i):
        return tuple(int(v) for v in self.X[i])

    def _check(self, x):
        if len(x) != 4 or sum(x) != self.N or min(x) < 1:
            raise ValueError(f"{x} is not a live state for N = {self.N}")


class FourStateSpace(_Keyed):
    """Live states (x1, x2, x3, x4), every xi >= 1, sum N, ordered lexicographically by (x1, x2, x3)."""

    def __init__(self, N):
        if N < 4:
            raise ValueError("need N >= 4 for a live state to exist")
        self.N = N
        blocks = []
        for x1 in range(1, N - 2):  # one block per x1; (x2, x3) vectorized
            x2, x3 = _pairs(N - x1)
            blocks.append(np.stack([np.full(len(x2), x1), x2, x3, N - x1 - x2 - x3], axis=1))
        self.X = np.concatenate(blocks).astype(np.int64)
        self.n = len(self.X)
        self.keys = self._key(self.X)

    def index(self, x):
        """Index of a live state x = (x1, x2, x3, x4)."""
        self._check(x)
        return int(self._index_array(np.array([x]))[0])


def _neighbors(X, a, b):
    """Coordinates after player a takes a chip from player b, for every row of X."""
    Y = X.copy()
    Y[:, a] += 1
    Y[:, b] -= 1
    return Y


def build_A4(S):
    """A = I - Q as a CSR matrix (symmetric positive definite, at most 13 nonzeros per row)."""
    X = S.coords()
    rows, cols, vals = [np.arange(S.n)], [np.arange(S.n)], [np.ones(S.n)]
    for a, b in MOVES4:
        Y = _neighbors(X, a, b)
        live = Y.min(axis=1) >= 1
        rows.append(np.arange(S.n)[live])
        cols.append(S._index_array(Y[live]))
        vals.append(np.full(live.sum(), -1.0 / 12.0))
    return sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(S.n, S.n))


def boundary_rhs4(S, f):
    """b[x] = sum over busting moves of f(landing state) / 12.

    f takes an integer array Y of shape (m, 4) of landing states (one zero coordinate) and returns m values.
    """
    X = S.coords()
    b = np.zeros(S.n)
    for a, c in MOVES4:
        Y = _neighbors(X, a, c)
        bust = Y.min(axis=1) == 0
        b[bust] += f(Y[bust]) / 12.0
    return b


def rhs_out_first4(S, i):
    """P(player i is out first). i is 0, 1, 2 or 3."""
    return boundary_rhs4(S, lambda Y: (Y[:, i] == 0).astype(float))


def rhs_win4(S, i):
    """P(player i wins the tournament): boundary value y_i / N (the remaining game is fair)."""
    return boundary_rhs4(S, lambda Y: Y[:, i] / S.N)


class LumpedSpace(_Keyed):
    """Sorted states y1 <= y2 <= y3, y4 = N - y1 - y2 - y3 >= 1, in lexicographic order.

    weights[r] = orbit size of (y1, y2, y3) under permutations: 6 (all different), 3 (two equal), 1 (all equal).
    """

    def __init__(self, N):
        if N < 4:
            raise ValueError("need N >= 4 for a live state to exist")
        self.N = N
        blocks = []
        for y1 in range(1, N - 2):
            y2, y3 = _pairs(N - y1)
            keep = (y1 <= y2) & (y2 <= y3)
            y2, y3 = y2[keep], y3[keep]
            blocks.append(np.stack([np.full(len(y2), y1), y2, y3, N - y1 - y2 - y3], axis=1))
        self.X = np.concatenate(blocks).astype(np.int64)
        self.n = len(self.X)
        self.keys = self._key(self.X)
        y1, y2, y3 = self.X[:, 0], self.X[:, 1], self.X[:, 2]
        distinct = 1 + (y1 != y2) + (y2 != y3)  # sorted, so this counts distinct values
        self.weights = np.array([0, 1, 3, 6])[distinct]

    def index(self, y):
        """Index of the orbit of the live state y; the first three entries may come in any order."""
        self._check(y)
        z = tuple(sorted(y[:3])) + (y[3],)
        return int(self._index_array(np.array([z]))[0])


def build_lumped(L):
    """(A_L, b): A_L = I - Q_L as CSR (rows follow L.coords()), b the right-hand side for P(player 4 busts first).

    Each of the 12 moves from y lands on the sorted version of the result. Moves are counted as integers and
    divided by 12 at the end, so diag(weights) A_L is symmetric to the last bit. A move can land back on y
    (for example (a, a+1) -> (a+1, a)), which only lowers the diagonal.
    """
    Y = L.coords()
    rows, cols, b = [], [], np.zeros(L.n)
    for a, c in MOVES4:
        Z = _neighbors(Y, a, c)
        live = Z.min(axis=1) >= 1
        Zl = Z[live]
        Zl[:, :3] = np.sort(Zl[:, :3], axis=1)
        rows.append(np.arange(L.n)[live])
        cols.append(L._index_array(Zl))
        b[Z[:, 3] == 0] += 1.0 / 12.0
    rows, cols = np.concatenate(rows), np.concatenate(cols)
    counts = sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(L.n, L.n))  # duplicates are summed
    A_L = (sp.identity(L.n, format="csr") - counts / 12.0).tocsr()
    return A_L, b


def solve_lumped(L, A_L, b):
    """Solve A_L u = b through the SPD matrix S = W^(1/2) A_L W^(-1/2): S v = W^(1/2) b, u = W^(-1/2) v.

    Returns (u, solver). CHOLMOD (METIS ordering) when scikit-sparse is installed, else SuperLU.
    """
    d = np.sqrt(np.asarray(L.weights, dtype=float))
    S = (sp.diags(d) @ A_L @ sp.diags(1.0 / d)).tocsc()
    S = ((S + S.T) / 2).tocsc()  # equal up to rounding; make it exactly symmetric for Cholesky
    try:
        from .direct import factorize

        v = factorize(S, "cholmod", "metis").solve(d * b)
        solver = "cholmod"
    except ImportError:
        v = spla.splu(S).solve(d * b)
        solver = "splu"
    return v / d, solver


def big_stack_out_first(N):
    """P(player 4 busts first) from (1, 1, 1, N - 3), from the lumped chain."""
    L = LumpedSpace(N)
    A_L, b = build_lumped(L)
    u, _ = solve_lumped(L, A_L, b)
    return float(u[L.index((1, 1, 1, N - 3))])
