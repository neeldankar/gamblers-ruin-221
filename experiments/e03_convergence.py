"""Chunk 3: CG convergence histories at N = 320 against the Chebyshev bound.

Writes results/e03_convergence.csv: one row per (kind, rhs, k) for kinds none, ic0, mic0, amg and rhs random,
order321, with
  relres   ||r_k||_2 / ||b||_2 (CG recurrence residual)
  err_A    ||x_k - x*||_A / ||x*||_A
  err_inf  max|x_k - x*| / max|x*|
  chebyshev  2 ((sqrt(kappa) - 1)/(sqrt(kappa) + 1))^k with kappa = kappa2(N), kind none only.
x* is the CHOLMOD nesdis solution (SuperLU MMD_AT_PLUS_A if CHOLMOD is missing).
    python experiments/e03_convergence.py [--quick] [--outdir DIR]      (--quick: N = 80)
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse

import numpy as np

from gr import direct, krylov, spectrum
from gr.matrix import build_A, rhs_order
from gr.runlog import save_results
from gr.states import StateSpace

KINDS = ["none", "ic0", "mic0", "amg"]
RTOL = 1e-10


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    N = 80 if args.quick else 320

    S = StateSpace(N)
    A = build_A(S).tocsr()
    rhs = {"random": np.random.default_rng(221).standard_normal(S.n), "order321": rhs_order(S, 2, 1, 0)}
    try:
        F = direct.factorize(A, "cholmod", "nesdis")
    except ImportError:
        F = direct.factorize(A, "splu", "MMD_AT_PLUS_A")
    s = np.sqrt(spectrum.kappa2(N))
    rho = (s - 1) / (s + 1)
    krylov.warmup()

    rows = []
    for kind in KINDS:
        M, _ = krylov.make_preconditioner(A, kind)
        for name, b in rhs.items():
            xs = F.solve(b)
            xs_A = np.sqrt(xs @ (A @ xs))
            xs_inf = np.max(np.abs(xs))
            err_A, err_inf = [1.0], [1.0]  # k = 0: x0 = 0

            def record(xk):
                e = xk - xs
                err_A.append(np.sqrt(e @ (A @ e)) / xs_A)
                err_inf.append(np.max(np.abs(e)) / xs_inf)

            _, info = krylov.cg(A, b, rtol=RTOL, M=M, callback=record)
            for k, relres in enumerate(info["residuals"]):
                rows.append({"N": N, "n": S.n, "kind": kind, "rhs": name, "k": k, "relres": relres,
                             "err_A": err_A[k], "err_inf": err_inf[k],
                             "chebyshev": 2 * rho**k if kind == "none" else np.nan})
            print(f"N = {N}  {kind:5s} {name:9s} its {info['iterations']:4d}  final err_A {err_A[-1]:.2e}"
                  f"  err_inf {err_inf[-1]:.2e}", flush=True)
    path = save_results(rows, "e03_convergence", outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
