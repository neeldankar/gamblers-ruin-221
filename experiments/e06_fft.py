"""Chunk 6: the FFT (method of images) solver: speed against splu, normwise accuracy, and relative accuracy at
the smallest P(123).

Writes results/e06_fft.csv, one row per N (plan/c06_fft.md):
    python experiments/e06_fft.py [--quick] [--outdir DIR]

Columns: N, n, P, seconds_fft, seconds_splu, speedup, fwd_err_t, kappa2, fwd_err_over_eps_kappa, resid_random,
err_vs_splu, sum_out_first_err, min_p123, p123_reldiff, plus min_state (added: where min P(123) sits, "a-b-c"
with player 1 first). splu columns are NaN at N = 1600.
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import gc
import time

import numpy as np
from scipy.sparse.linalg import splu

from gr.fft_solver import fft_solve
from gr.matrix import build_A, rhs_order, rhs_out_first, solve
from gr.runlog import save_results
from gr.spectrum import kappa2
from gr.states import StateSpace

FULL = [50, 100, 200, 400, 800, 1600]
QUICK = [50, 100, 200]
SPLU_MAX_N = 800
EPS = 2.0 ** -52


def median_seconds(f, runs=3):
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        f()
        times.append(time.perf_counter() - t0)
    return float(np.median(times))


def run_size(N):
    S = StateSpace(N)
    A = build_A(S)
    ones = np.ones(S.n)
    use_splu = N <= SPLU_MAX_N

    fft_solve(N, ones)  # warm-up (group and symbol caches, first-call costs)
    seconds_fft = median_seconds(lambda: fft_solve(N, ones))
    seconds_splu = median_seconds(lambda: splu(A.tocsc()).solve(ones)) if use_splu else np.nan

    # forward error against the closed form A t = 1
    t = 3.0 * S.x1 * S.x2 * S.x3 / N
    fwd_err_t = np.max(np.abs(fft_solve(N, ones) - t)) / np.max(t)
    k2 = kappa2(N)

    # random right-hand side
    b = np.random.default_rng(221).standard_normal(S.n)
    x = fft_solve(N, b)
    resid_random = np.linalg.norm(b - A @ x) / np.linalg.norm(b)
    err_vs_splu = np.nan
    if use_splu:
        xd = solve(A, b)
        err_vs_splu = np.linalg.norm(x - xd) / np.linalg.norm(xd)

    # out-first probabilities sum to 1
    total = sum(fft_solve(N, rhs_out_first(S, i)) for i in range(3))
    sum_out_first_err = np.max(np.abs(total - 1))

    # smallest P(123), from splu, and the FFT's relative difference there
    min_p123 = p123_reldiff = np.nan
    min_state = ""
    if use_splu:
        b123 = rhs_order(S, 0, 1, 2)
        xs = solve(A, b123)
        i = int(np.argmin(xs))
        min_p123 = xs[i]
        min_state = "-".join(map(str, S.state(i)))
        p123_reldiff = abs(fft_solve(N, b123)[i] / xs[i] - 1)

    row = {"N": N, "n": S.n, "P": 3 * N, "seconds_fft": seconds_fft, "seconds_splu": seconds_splu,
           "speedup": seconds_splu / seconds_fft, "fwd_err_t": fwd_err_t, "kappa2": k2,
           "fwd_err_over_eps_kappa": fwd_err_t / (EPS * k2), "resid_random": resid_random,
           "err_vs_splu": err_vs_splu, "sum_out_first_err": sum_out_first_err, "min_p123": min_p123,
           "p123_reldiff": p123_reldiff, "min_state": min_state}
    print(f"N = {N:5d}  n = {S.n:8d}  fft {seconds_fft:.3f} s  splu {seconds_splu:.3f} s  "
          f"fwd/(eps k2) {row['fwd_err_over_eps_kappa']:.3f}  resid {resid_random:.1e}  "
          f"vs splu {err_vs_splu:.1e}  sum {sum_out_first_err:.1e}  min p123 N^3 {min_p123 * N ** 3:.6f} "
          f"at {min_state}  reldiff {p123_reldiff:.1e}", flush=True)
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    np.random.default_rng(221)  # project convention; each random b is drawn from a fresh rng(221)
    fft_solve(10, np.ones(StateSpace(10).n))  # warm-up
    rows = []
    for N in QUICK if args.quick else FULL:
        rows.append(run_size(N))
        _clear()
    path = save_results(rows, "e06_fft", outdir=args.outdir)
    print(f"wrote {path}")


def _clear():
    """Free the cached group and symbol and the big temporaries before the next N (N = 1600 peaks near 2.5 GB)."""
    from gr import fft_solver

    fft_solver._symbol.cache_clear()
    gc.collect()


if __name__ == "__main__":
    main()
