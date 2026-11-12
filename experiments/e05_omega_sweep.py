"""Chunk 5: SOR iteration counts and dense spectral radius as functions of omega.

Writes results/e05_omega_sweep.csv, one row per (N, grid, omega) (plan/c05_stationary.md):
    python experiments/e05_omega_sweep.py [--quick] [--outdir DIR]

Grids: coarse omega = 1.00 + 0.02 j (j = 0..49) and fine omega = omega* + 0.0025 j (j = -20..20, offset 0 exact).
rho_dense = spectral_radius(iteration_matrix(A, "sor", omega)) for N <= 40, NaN at N = 80.
`seconds` is the wall time of the two SOR runs of that row (not a benchmark).
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import time

import numpy as np

from gr import stationary
from gr.matrix import build_A, rhs_rounds
from gr.runlog import save_results
from gr.states import StateSpace

RTOL = 1e-10
FULL = [20, 40, 80]
QUICK = [20]
DENSE_MAX_N = 40


def rho_jacobi(N):
    return (1 + 2 * np.cos(2 * np.pi / N)) / 3


def run_size(N):
    S = StateSpace(N)
    A = build_A(S)
    w_star = stationary.young_omega(rho_jacobi(N))
    b_ones = rhs_rounds(S)
    b_random = np.random.default_rng(221).standard_normal(S.n)
    grids = [("coarse", 1.00 + 0.02 * j) for j in range(50)]
    grids += [("fine", w_star + 0.0025 * j) for j in range(-20, 21)]
    rows = []
    for grid, omega in grids:
        t0 = time.perf_counter()
        k_ones = stationary.sor(A, b_ones, omega, rtol=RTOL)[1]["iterations"]
        k_random = stationary.sor(A, b_random, omega, rtol=RTOL)[1]["iterations"]
        seconds = time.perf_counter() - t0
        rho = (stationary.spectral_radius(stationary.iteration_matrix(A, "sor", omega))
               if N <= DENSE_MAX_N else np.nan)
        rows.append({"N": N, "n": S.n, "grid": grid, "omega": omega, "offset": omega - w_star,
                     "omega_star": w_star, "iterations_ones": k_ones, "iterations_random": k_random,
                     "rho_dense": rho, "seconds": seconds})
    best = min((r for r in rows if r["grid"] == "fine"), key=lambda r: r["iterations_ones"])
    print(f"N = {N:3d}  omega* = {w_star:.6f}  best fine iterations_ones {best['iterations_ones']} at offset "
          f"{best['offset']:+.4f}", flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    np.random.default_rng(221)  # project convention; each random b is drawn from a fresh rng(221)
    stationary.warmup()
    rows = []
    for N in QUICK if args.quick else FULL:
        rows += run_size(N)
    path = save_results(rows, "e05_omega_sweep", outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
