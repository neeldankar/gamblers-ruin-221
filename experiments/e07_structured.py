"""Chunk 7: the right parametrization. Perturb A's off-diagonals, its row sums and b (not its diagonal).

Writes results/e07_structured.csv: one row per N, b = out_first_3 (rhs_out_first(S, 2)), eps = 1e-8.
A perturbed matrix is built from its off-diagonal entries and row sums: diagonal = row sum + sum_j |a_ij|.
The base system is built the same way from the unperturbed values (so it differs from build_A only by a rounding
in the diagonal), and every solve is SuperLU (gr.matrix.solve). Ratios are |x'_i - x_i| / x_i / eps.
  (a) structured_random_max: 20 draws; each off-diagonal entry (independently, so A' is not symmetric), each
      row sum and each b_i times 1 + eps * uniform(-1, 1), rng = default_rng(221) fresh for each N.
      The largest ratio over all states and draws.
  (b) structured_push: row sums times (1 - eps), b times (1 + eps), off-diagonals unchanged. Largest ratio.
  (c) cond_max = max_i cond_i from gr.accuracy.entry_condition (chunk 4's parametrization: A's entries).
  two_n_minus_1 = 2n - 1, for comparison.
Chunk 7b additions (after the computations above, so their values do not change), with x the base solution,
kappa = gr.accuracy.structured_condition on the base system and tiny = (1, 1, N-2):
  (d) structured_cond_tiny, structured_cond_max, structured_argmax_state, structured_cond_over_N = max / N.
  (e) attained_tiny, attained_max_dev: off-diagonal weights times 1 + eps sign(x_j - x_i), row sums times 1 - eps,
      b times 1 + eps. ratio_i = (x'_i - x_i) / x_i / eps (signed): the ratio at tiny, and max_i |ratio_i / kappa_i - 1|.
  (f) coherent_tiny: (A + eps (H A - A H)) x' = b, H = diag(x3), A = build_A; ratio at tiny against x0 = solve(A, b).
  (g) drift_tiny: the weights of (e) only (row sums and b unchanged); ratio at tiny.
  (h) symmetric_cond_tiny: with g = A^-1 e_tiny and each unordered pair {i, j} once,
      (sum_i g_i (b_i + s_i x_i) + sum_{i<j} |a_ij| |g_i - g_j| |x_i - x_j|) / x_tiny.
  (i) cond_tiny: chunk 4's entry_condition at tiny (next to cond_max).
    python experiments/e07_structured.py [--quick] [--outdir DIR]
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from gr import accuracy as acc
from gr.matrix import boundary_rhs, build_A, rhs_out_first, solve
from gr.runlog import save_results
from gr.states import StateSpace

FULL = [10, 20, 40, 80, 160, 320, 640]
QUICK = [10, 20]
EPS = 1e-8
DRAWS = 20


def structured_matrix(off_rows, off_cols, off_vals, sums):
    """CSR matrix with the given off-diagonal entries and row sums: diagonal_i = sums_i + sum_j |a_ij|
    (a sum of nonnegative numbers, since every a_ij <= 0)."""
    n = len(sums)
    diag = sums + np.bincount(off_rows, weights=-off_vals, minlength=n)
    rows = np.concatenate([np.arange(n), off_rows])
    cols = np.concatenate([np.arange(n), off_cols])
    return sp.csr_matrix((np.concatenate([diag, off_vals]), (rows, cols)), shape=(n, n))


def run_size(N):
    S = StateSpace(N)
    A = build_A(S).tocsr()
    b = rhs_out_first(S, 2)
    sums = boundary_rhs(S, lambda Y: np.ones(len(Y)))
    C = A.tocoo()
    off = C.row != C.col
    r, c, v = C.row[off], C.col[off], C.data[off]

    x = solve(structured_matrix(r, c, v, sums), b)

    rng = np.random.default_rng(221)
    random_max = 0.0
    for _ in range(DRAWS):
        Ap = structured_matrix(r, c, v * (1 + EPS * rng.uniform(-1, 1, len(v))),
                               sums * (1 + EPS * rng.uniform(-1, 1, S.n)))
        bp = b * (1 + EPS * rng.uniform(-1, 1, S.n))
        random_max = max(random_max, np.max(np.abs(solve(Ap, bp) - x) / x / EPS))

    xp = solve(structured_matrix(r, c, v, sums * (1 - EPS)), b * (1 + EPS))
    push = np.max(np.abs(xp - x) / x / EPS)

    x0 = solve(A, b)
    cond = acc.entry_condition(A, b, x0, lambda rhs: solve(A, rhs))
    cond_max = cond.max()

    # chunk 7b: the structured condition number and the directions that attain it
    tiny = S.index((1, 1, N - 2))
    base = spla.splu(structured_matrix(r, c, v, sums).tocsc())  # factored once, for kappa and g
    kappa = acc.structured_condition(A, b, x, sums, base.solve)
    k_arg = int(np.argmax(kappa))
    toward = 1 + EPS * np.sign(x[c] - x[r])  # weight up toward the larger x: a drift toward the event

    xp = solve(structured_matrix(r, c, v * toward, sums * (1 - EPS)), b * (1 + EPS))
    attained = (xp - x) / x / EPS

    h = S.x3.astype(float)
    H = sp.diags(h)
    xp = solve((A + EPS * (H @ A - A @ H)).tocsr(), b)
    coherent = (xp - x0) / x0 / EPS

    xp = solve(structured_matrix(r, c, v * toward, sums), b)
    drift = (xp - x) / x / EPS

    e = np.zeros(S.n)
    e[tiny] = 1.0
    g = base.solve(e)
    up = r < c  # each unordered pair {i, j} once (the matrix is symmetric)
    pair = np.sum(-v[up] * np.abs(g[r[up]] - g[c[up]]) * np.abs(x[r[up]] - x[c[up]]))
    symmetric = (np.sum(g * (b + sums * x)) + pair) / x[tiny]

    print(f"N = {N:4d}  n = {S.n:6d}  random max {random_max:.3f}  push {push:.3f}  cond_max {cond_max:.1f}  "
          f"kappa_tiny {kappa[tiny]:.4f} ({kappa[tiny] / N:.4f} N)  attained {attained[tiny]:.4f}  "
          f"coherent {coherent[tiny]:.4f}  drift {drift[tiny]:.4f}  symmetric {symmetric:.4f}", flush=True)
    return {"N": N, "n": S.n, "structured_random_max": random_max, "structured_push": push, "cond_max": cond_max,
            "two_n_minus_1": 2 * S.n - 1, "eps": EPS, "draws": DRAWS,
            "structured_cond_tiny": kappa[tiny], "structured_cond_max": kappa[k_arg],
            "structured_argmax_state": str(S.state(k_arg)), "structured_cond_over_N": kappa[k_arg] / N,
            "attained_tiny": attained[tiny], "attained_max_dev": np.max(np.abs(attained / kappa - 1)),
            "coherent_tiny": coherent[tiny], "drift_tiny": drift[tiny], "symmetric_cond_tiny": symmetric,
            "cond_tiny": cond[tiny]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    rows = [run_size(N) for N in (QUICK if args.quick else FULL)]
    path = save_results(rows, "e07_structured", outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
