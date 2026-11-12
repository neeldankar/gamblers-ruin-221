"""Chunk 2: direct solvers, fill-in and orderings.

Writes results/e02_direct.csv, one row per (N, method, ordering); with --big, writes
results/e02_direct_big.csv instead (cholmod nesdis at N = 2400 and 3200, one repeat, about 6 GB).
    python experiments/e02_direct.py [--quick] [--big] [--outdir DIR]
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import gc
import time

import numpy as np
import scipy.sparse as sp

from gr import direct, spectrum
from gr.matrix import build_A, rhs_rounds
from gr.runlog import repeats, save_results
from gr.states import StateSpace

FULL = [25, 50, 100, 200, 400, 800, 1200, 1600]
QUICK = [25, 50, 100]
BIG = [2400, 3200]
REPEATS = repeats()  # 3 by default, 5 in the chunk 11 final run
FLOPS_MAX_N = 800  # column counts of splu need a copy of L; skip above this
U = 2.0**-53

# Largest N for each (method, ordering), from the spec's size-cap table.
CAPS = {
    ("dense_cholesky", "natural"): 100,
    ("banded_cholesky", "natural"): 400,
    ("splu", "NATURAL"): 400,
    ("cholmod", "natural"): 400,
    ("splu", "COLAMD"): 1200,
    ("splu", "MMD_ATA"): 1200,
    ("splu", "MMD_AT_PLUS_A"): 1600,
    ("cholmod", "amd"): 1600,
    ("cholmod", "metis"): 1600,
    ("cholmod", "nesdis"): 1600,
}


def measure(A, b, method, ordering, repeats, with_flops):
    """Factor `repeats` times and solve `repeats` times; return the measured quantities."""
    setup_times, F = [], None
    for _ in range(repeats):
        F = None  # free the previous factor first, so only one big factor is alive
        gc.collect()
        F = direct.factorize(A, method, ordering)
        setup_times.append(F.setup_time)
    solve_times, x = [], None
    for _ in range(repeats):
        t0 = time.perf_counter()
        x = F.solve(b)
        solve_times.append(time.perf_counter() - t0)
    flops = float(np.sum(F.column_counts().astype(float) ** 2)) if with_flops else np.nan
    out = {
        "nnz_factor": F.nnz,
        "setup_time": float(np.median(setup_times)),
        "solve_time": float(np.median(solve_times)),
        "flops": flops,
        "x": x,
    }
    del F
    gc.collect()
    return out


def run_size(N, pairs, repeats, flops_max_n):
    S = StateSpace(N)
    A = build_A(S).tocsc()  # built outside every timer
    b = rhs_rounds(S)
    t = 3.0 * S.x1 * S.x2 * S.x3 / N  # exact solution of A t = 1
    kinf = spectrum.kappa_inf(N)
    norm_A = abs(A).sum(axis=1).max()
    nnz_A, nnz_tril = A.nnz, sp.tril(A).nnz
    rows = []
    for method, ordering in pairs:
        m = measure(A, b, method, ordering, repeats, N <= flops_max_n)
        x = m.pop("x")
        nnz_chol = m["nnz_factor"] / 2 if method == "splu" else m["nnz_factor"]
        fwd = np.max(np.abs(x - t)) / np.max(t)
        bwd = np.max(np.abs(b - A @ x)) / (norm_A * np.max(np.abs(x)) + np.max(np.abs(b)))
        rows.append({
            "N": N,
            "n": S.n,
            "method": method,
            "ordering": ordering,
            "nnz_A": nnz_A,
            "nnz_factor": m["nnz_factor"],
            "nnz_chol_equiv": nnz_chol,
            "fill_ratio": nnz_chol / nnz_tril,
            "flops": m["flops"],
            "setup_time": m["setup_time"],
            "solve_time": m["solve_time"],
            "forward_error": fwd,
            "kappa_inf": kinf,
            "err_over_kappa_u": fwd / (kinf * U),
            "backward_error": bwd,
            "memory_MB_est": 8 * m["nnz_factor"] / 1e6,
        })
        r = rows[-1]
        print(f"N = {N:4d}  {method:15s} {ordering:13s} nnz {r['nnz_factor']:>11,d}  setup {r['setup_time']:8.3f} s"
              f"  solve {r['solve_time']:7.4f} s  fwd/(k u) {r['err_over_kappa_u']:.3f}  bwd {bwd:.1e}", flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--big", action="store_true", help="cholmod nesdis at N = 2400, 3200 (about 6 GB)")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    np.random.default_rng(221)  # project convention; this chunk uses only the deterministic b = 1

    rows = []
    if args.big:
        for N in BIG:
            rows += run_size(N, [("cholmod", "nesdis")], repeats=1, flops_max_n=FLOPS_MAX_N)
        name = "e02_direct_big"
    else:
        for N in QUICK if args.quick else FULL:
            pairs = [(m, o) for m, orders in direct.ORDERINGS.items() for o in orders if N <= CAPS[(m, o)]]
            rows += run_size(N, pairs, repeats=REPEATS, flops_max_n=FLOPS_MAX_N)
        name = "e02_direct"
    path = save_results(rows, name, outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
