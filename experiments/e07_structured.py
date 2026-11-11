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
    python experiments/e07_structured.py [--quick] [--outdir DIR]
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse

import numpy as np
import scipy.sparse as sp

from gr import accuracy as acc
from gr.matrix import boundary_rhs, build_A, rhs_out_first, solve
from gr.runlog import save_results
from gr.states import StateSpace

FULL = [10, 20, 40, 80, 160]
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
    cond_max = acc.entry_condition(A, b, x0, lambda rhs: solve(A, rhs)).max()
    print(f"N = {N:4d}  n = {S.n:6d}  random max {random_max:.3f}  push {push:.3f}  cond_max {cond_max:.1f}  "
          f"cond_max / push {cond_max / push:.1f}", flush=True)
    return {"N": N, "n": S.n, "structured_random_max": random_max, "structured_push": push, "cond_max": cond_max,
            "two_n_minus_1": 2 * S.n - 1, "eps": EPS, "draws": DRAWS}


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
