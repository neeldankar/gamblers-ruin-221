"""Chunk 5: Jacobi, Gauss-Seidel and SOR(omega*) iteration counts and rates against the exact predictions.

Writes results/e05_iterations.csv, one row per (N, method, b_kind) (plan/c05_stationary.md):
    python experiments/e05_iterations.py [--quick] [--outdir DIR]

rtol = 1e-10, rho_J = (1 + 2 cos(2 pi/N))/3, omega* = young_omega(rho_J). Predicted rates: rho_J (jacobi),
rho_J^2 (gauss_seidel), (omega* - 1)^(3/4) (sor, the 3/4 law). `seconds` is one run, not a benchmark.
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import time

import numpy as np

from gr import stationary
from gr.matrix import build_A, rhs_out_first, rhs_rounds, solve
from gr.runlog import save_results
from gr.spectrum import kappa2
from gr.states import StateSpace

RTOL = 1e-10
FULL = {"jacobi": [10, 20, 40, 80, 160], "gauss_seidel": [10, 20, 40, 80, 160],
        "sor": [10, 20, 40, 80, 160, 320, 640]}
QUICK = {m: [10, 20, 40] for m in FULL}
KINDS = ["ones", "out_first", "random"]


def rho_jacobi(N):
    return (1 + 2 * np.cos(2 * np.pi / N)) / 3


def rhs(S, kind):
    if kind == "ones":
        return rhs_rounds(S)
    if kind == "out_first":
        return rhs_out_first(S, 0)
    return np.random.default_rng(221).standard_normal(S.n)


def run_size(N, methods):
    S = StateSpace(N)
    A = build_A(S)
    rho_j = rho_jacobi(N)
    w = stationary.young_omega(rho_j)
    predicted_rho = {"jacobi": rho_j, "gauss_seidel": rho_j ** 2, "sor": (w - 1) ** 0.75}
    rows = []
    for kind in KINDS:
        b = rhs(S, kind)
        x_direct = solve(A, b)
        for method in methods:
            t0 = time.perf_counter()
            if method == "sor":
                x, info = stationary.sor(A, b, w, rtol=RTOL)
            else:
                x, info = getattr(stationary, method)(A, b, rtol=RTOL)
            seconds = time.perf_counter() - t0

            r = info["residual_norms"]
            k = info["iterations"]
            h = k // 2
            rate = (r[k] / r[h]) ** (1 / (k - h))
            row = {
                "N": N, "n": S.n, "method": method, "omega": w if method == "sor" else np.nan, "b_kind": kind,
                "iterations": k, "converged": info["converged"], "final_residual": r[-1],
                "predicted_iterations": np.log(1 / RTOL) / -np.log(predicted_rho[method]),
                "young_predicted_iterations": np.log(1 / RTOL) / -np.log(w - 1) if method == "sor" else np.nan,
                "rate_measured": rate,
                "exponent_ratio": np.log(rate) / np.log(w - 1) if method == "sor" else np.nan,
                "rho_jacobi": rho_j, "kappa2": kappa2(N),
                "forward_error": np.linalg.norm(x - x_direct) / np.linalg.norm(x_direct),
                "seconds": seconds,
            }
            rows.append(row)
            print(f"N = {N:4d}  {method:12s}  {kind:9s}  k = {k:6d}  pred {row['predicted_iterations']:9.1f}  "
                  f"rate {rate:.9f}  exp {row['exponent_ratio']:.4f}  fwd {row['forward_error']:.2e}  "
                  f"{seconds:.2f} s", flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    np.random.default_rng(221)  # project convention; each random b is drawn from a fresh rng(221)
    stationary.warmup()
    sizes = QUICK if args.quick else FULL
    rows = []
    for N in sorted(set().union(*sizes.values())):
        rows += run_size(N, [m for m in sizes if N in sizes[m]])
    path = save_results(rows, "e05_iterations", outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
