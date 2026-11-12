"""Chunk 9 worker: one solver run in its own process.

Started by experiments/e09_four.py, one process per (method, N), so that peak_rss_mb (the process's maximum
resident memory) belongs to this run alone and the parent can kill a run that grows too large. Each worker does
one setup and one solve; the parent starts a new worker for each repeat. (Repeats inside one process are not
used: scikit-sparse 0.5 does not give a CHOLMOD factor's memory back, so the peak would grow by a factor each time.)
Methods splu, splu_mmd, cholmod, amg_cg solve the four-player system A u = e2 (exact answer 6 x1 x2 x3 x4).
Method lumped computes P(player 4 busts first) from (1, 1, 1, N - 3) on the lumped chain.
Prints one JSON line with the measurements.
    python experiments/e09_worker.py --method cholmod --N 60
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import itertools
import json
import resource
import sys
import time

import numpy as np

from gr import direct
from gr.four import FourStateSpace, LumpedSpace, build_A4, build_lumped, solve_lumped

METHODS = ["splu", "splu_mmd", "cholmod", "amg_cg", "lumped"]
DIRECT = {"splu": ("splu", "COLAMD"), "splu_mmd": ("splu", "MMD_AT_PLUS_A"), "cholmod": ("cholmod", "metis")}


def peak_rss_mb():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / 2**20 if sys.platform == "darwin" else r / 2**10  # bytes on macOS, kilobytes on Linux


def run_once(A, b, method):
    """One setup and one solve. Returns (setup_s, solve_s, x, nnz_factor, iters)."""
    if method in DIRECT:
        F = direct.factorize(A, *DIRECT[method])
        t0 = time.perf_counter()
        x = F.solve(b)
        return F.setup_time, time.perf_counter() - t0, x, F.nnz, np.nan
    import pyamg

    t0 = time.perf_counter()
    ml = pyamg.smoothed_aggregation_solver(A)
    setup = time.perf_counter() - t0
    res = []
    t0 = time.perf_counter()
    x = ml.solve(b, tol=1e-12, accel="cg", maxiter=500, residuals=res)
    return setup, time.perf_counter() - t0, x, np.nan, len(res) - 1


def lumped(N):
    """Build and solve the lumped chain once; seconds = build + solve wall time."""
    t0 = time.perf_counter()
    L = LumpedSpace(N)
    A_L, b = build_lumped(L)
    u, solver = solve_lumped(L, A_L, b)
    P = float(u[L.index((1, 1, 1, N - 3))])
    return {"N": N, "n_lumped": L.n, "P": P, "seconds": time.perf_counter() - t0, "solver": solver,
            "peak_rss_mb": peak_rss_mb()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=METHODS, required=True)
    parser.add_argument("--N", type=int, required=True)
    args = parser.parse_args()
    if args.method == "lumped":
        lumped(8)  # warm-up: imports, library setup
        print(json.dumps(lumped(args.N)), flush=True)
        return

    run_once(build_A4(FourStateSpace(8)).tocsc(), np.ones(35), args.method)  # warm-up: imports, library setup

    S = FourStateSpace(args.N)
    A = build_A4(S)  # built outside every timer
    if args.method in DIRECT:
        A = A.tocsc()
    X = S.coords().astype(float)
    b = sum(X[:, i] * X[:, j] for i, j in itertools.combinations(range(4), 2))  # e2
    exact = 6 * X.prod(axis=1)  # A^{-1} e2 = 6 x1 x2 x3 x4

    setup, solve, x, nnz, iters = run_once(A, b, args.method)
    out = {
        "N": args.N,
        "n": S.n,
        "method": args.method,
        "setup_s": setup,
        "solve_s": solve,
        "peak_rss_mb": peak_rss_mb(),
        "nnz_factor": float(nnz),
        "iters": float(iters),
        "rel_err": float(np.max(np.abs(x - exact)) / np.max(exact)),
    }
    print(json.dumps(out), flush=True)


if __name__ == "__main__":
    main()
