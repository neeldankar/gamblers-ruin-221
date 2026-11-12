"""Chunk 1: exact spectrum and condition numbers, with shift-invert Lanczos as an independent check.

Writes results/e01_conditioning.csv, one row per N.
    python experiments/e01_conditioning.py [--quick] [--outdir DIR]
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import time

import numpy as np
import scipy.sparse.linalg as spla

from gr import spectrum
from gr.matrix import build_A
from gr.runlog import repeats, save_results
from gr.states import StateSpace

FULL = [10, 20, 30, 40, 80, 90, 160, 300, 320, 640]
QUICK = [10, 20, 30, 40]
EIGSH_MAX_N = 320
REPEATS = repeats()  # 3 by default, 5 in the chunk 11 final run


def eigsh_lambda_min(A):
    """Smallest eigenvalue by shift-invert Lanczos around 0; median time over REPEATS runs."""
    times, lam = [], None
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        lam = spla.eigsh(A, k=1, sigma=0, which="LM", return_eigenvectors=False)[0]
        times.append(time.perf_counter() - t0)
    return lam, float(np.median(times))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()

    rows = []
    for N in QUICK if args.quick else FULL:
        S = StateSpace(N)
        if N <= EIGSH_MAX_N:
            A = build_A(S).tocsc()  # built outside the timer
            lam_eigsh, sec = eigsh_lambda_min(A)
        else:
            lam_eigsh, sec = np.nan, np.nan
        k2, kinf = spectrum.kappa2(N), spectrum.kappa_inf(N)
        rows.append({
            "N": N,
            "n": S.n,
            "lambda_min_formula": spectrum.lambda_min(N),
            "lambda_min_eigsh": lam_eigsh,
            "lambda_max_formula": spectrum.lambda_max(N),
            "kappa2": k2,
            "kappa2_over_N2": k2 / N**2,
            "kappa_inf": kinf,
            "kappa_inf_over_N2": kinf / N**2,
            "jacobi_rate": spectrum.jacobi_rate(N),
            "seconds_eigsh": sec,
        })
        print(f"N = {N:4d}  n = {S.n:6d}  kappa2 = {k2:.6g}  kappa_inf = {kinf:.6g}  eigsh {sec:.3g} s")
    path = save_results(rows, "e01_conditioning", outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
