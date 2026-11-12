"""Chunk 5: dense spectral radii of the Jacobi, Gauss-Seidel and SOR(omega*) iteration matrices (the 3/4 law).

Writes results/e05_sor_spectra.csv, one row per N (plan/c05_stationary.md):
    python experiments/e05_sor_spectra.py [--quick] [--outdir DIR]

law_value = (omega* - 1)^(3/4), young_value = omega* - 1, gs_gap = rho_gs_dense - rho_jacobi_dense^2.
seconds_dense is the wall time of the three dense iteration matrices and eigenvalue problems for that N.
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import gc
import time

import numpy as np

from gr import stationary
from gr.matrix import build_A
from gr.runlog import save_results
from gr.states import StateSpace

FULL = [6, 8, 10, 12, 16, 20, 24, 30, 40, 50, 60, 80, 100]
QUICK = [N for N in FULL if N <= 30]


def rho_jacobi(N):
    return (1 + 2 * np.cos(2 * np.pi / N)) / 3


def dense_rho(A, method, omega=None):
    return stationary.spectral_radius(stationary.iteration_matrix(A, method, omega))


def run_size(N):
    S = StateSpace(N)
    A = build_A(S)
    rho_j = rho_jacobi(N)
    w = stationary.young_omega(rho_j)
    t0 = time.perf_counter()
    rho_j_dense = dense_rho(A, "jacobi")
    rho_gs = dense_rho(A, "gauss_seidel")
    rho_sor = dense_rho(A, "sor", w)
    seconds = time.perf_counter() - t0
    gap = rho_gs - rho_j_dense ** 2
    law, young = (w - 1) ** 0.75, w - 1
    row = {"N": N, "n": S.n, "omega_star": w, "rho_jacobi_formula": rho_j, "rho_jacobi_dense": rho_j_dense,
           "rho_gs_dense": rho_gs, "gs_gap": gap, "gs_gap_times_N4": gap * N ** 4, "rho_sor_dense": rho_sor,
           "law_value": law, "young_value": young, "law_relerr": abs(rho_sor / law - 1),
           "sor_over_young": rho_sor / young, "seconds_dense": seconds}
    print(f"N = {N:3d}  n = {S.n:5d}  rho_sor {rho_sor:.12f}  law relerr {row['law_relerr']:.1e}  "
          f"gap N^4 {row['gs_gap_times_N4']:.3f}  sor/young {row['sor_over_young']:.4f}  {seconds:.1f} s", flush=True)
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    rows = []
    for N in QUICK if args.quick else FULL:
        rows.append(run_size(N))
        gc.collect()  # the dense matrices at N = 100 are 190 MB each
    path = save_results(rows, "e05_sor_spectra", outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
