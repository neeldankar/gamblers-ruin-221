"""Chunk 4: does the condition number cond_i predict the effect of real perturbations?

Writes results/e04_perturbation.csv: one row per (N, eps), b = out_first_3 (rhs_out_first(S, 2)).
  * worst case: A -> A - eps|A|, b -> b + eps|b|. ratio_i = (x_pert - x)_i / x_i / (eps cond_i); its min and
    max over i should both be 1 to first order.
  * random: 20 draws of dA_ij = eps A_ij s, db_i = eps b_i s with s ~ uniform(-1, 1) per entry (so
    |dA| <= eps|A|, |db| <= eps|b|), rng = default_rng(221) fresh for each (N, eps). random_max_ratio is the
    largest |x_pert - x|_i / x_i / (eps cond_i) over all entries and draws; it should stay at most 1.
    python experiments/e04_perturbation.py [--quick] [--outdir DIR]
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse

import numpy as np
import scipy.sparse as sp

from gr import accuracy as acc
from gr.matrix import build_A, rhs_out_first, solve
from gr.runlog import save_results
from gr.states import StateSpace

FULL = [10, 20, 40, 80]
QUICK = [10, 20]
EPS = [1e-10, 1e-8, 1e-6]
DRAWS = 20


def run_size(N):
    S = StateSpace(N)
    A = build_A(S).tocsr()
    b = rhs_out_first(S, 2)
    x = solve(A, b)
    cond = acc.entry_condition(A, b, x, lambda r: solve(A, r))
    Acoo = A.tocoo()
    rows = []
    for eps in EPS:
        Ap, bp = acc.worst_case_perturbation(A, b, eps)
        worst = (solve(Ap, bp) - x) / x / (eps * cond)

        rng = np.random.default_rng(221)
        rand_max = 0.0
        for _ in range(DRAWS):
            dA = sp.csr_matrix((eps * Acoo.data * rng.uniform(-1, 1, Acoo.nnz), (Acoo.row, Acoo.col)), shape=A.shape)
            db = eps * b * rng.uniform(-1, 1, S.n)
            rand_max = max(rand_max, np.max(np.abs(solve(A + dA, b + db) - x) / x / (eps * cond)))

        rows.append({"N": N, "n": S.n, "eps": eps, "eps_cond_max": eps * cond.max(),
                     "worst_ratio_min": worst.min(), "worst_ratio_max": worst.max(),
                     "random_max_ratio": rand_max, "draws": DRAWS})
        print(f"N = {N:3d}  eps {eps:.0e}  worst ratio {worst.min():.6f} to {worst.max():.6f}  "
              f"random max {rand_max:.4f}", flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    rows = []
    for N in QUICK if args.quick else FULL:
        rows += run_size(N)
    path = save_results(rows, "e04_perturbation", outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
