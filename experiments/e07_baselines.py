"""Chunk 7b: the own error of several direct solvers, and the error of each method against the true probability.

Writes results/e07_baselines.csv: one row per (N, method), b = out_first_3 (rhs_out_first(S, 2)).
Errors come from exact integer residuals (gr.refine.exact_residual), not from a reference solution:
  xhat - x_stored = -A^-1 (b - A xhat)      residual of the stored system (A, b as float64)
  xhat - x_true   = -A^-1 (B - Ai xhat)/6N  residual of the ideal system, Ai, B = integer_system(A, b, 6N)
Both residuals are exact (one rounding); A^-1 is applied by one CHOLMOD nesdis factor F per N, which is accurate
to about 10 digits on a correction this small. Signed relative errors, divided by xhat, every entry.
Methods (each returns xhat):
  cholmod_default     F.solve(b) (e07_fixes' "direct": supernodal from N = 160, simplicial below)
  cholmod_simplicial  CHOLMOD nesdis, supernodal_mode="simplicial"
  cholmod_supernodal  CHOLMOD nesdis, supernodal_mode="supernodal"
  splu_colamd         SuperLU COLAMD
  splu_natural        SuperLU natural order, N <= 320
  banded              LAPACK band Cholesky (gr.direct banded_cholesky): about 1 GB at N = 640
  banded_int          band Cholesky of A6 = integer_system(A, b, 6) (entries 6, -1; rhs 0, 1, 2: no data term)
  cholmod_int         CHOLMOD nesdis on A6, B6
  gth                 gr.refine.gth_solve
  ir_direct           gr.refine.iterative_refinement with F
At N = 1280 only cholmod_default and ir_direct.
Columns:
  * own_err_* (against the stored solution) only for methods that solve the stored system (cholmod_* except
    cholmod_int, splu_*, banded); NaN for the others. *_over_N2u = the tiny-entry error / (N^2 u).
  * max_true_err_in_ulp = max_i |xhat_i - x_true_i| / spacing(xhat_i).
  * data_term_tiny = data_error_term(F.solve(b), F.solve) at tiny.
  * seconds: one run from A to xhat, factorization included (cholmod_default and ir_direct add F's setup
    time). Not a benchmark.
    python experiments/e07_baselines.py [--quick] [--outdir DIR]
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import gc
import time

import numpy as np

from gr import accuracy as acc
from gr import direct, refine
from gr.matrix import boundary_rhs, build_A, rhs_out_first
from gr.runlog import save_results
from gr.states import StateSpace

FULL = [20, 40, 80, 160, 320, 640, 1280]
QUICK = [20, 40]
BIG_N = 1280  # only cholmod_default and ir_direct here
SPLU_NATURAL_MAX_N = 320
STORED = {"cholmod_default", "cholmod_simplicial", "cholmod_supernodal", "splu_colamd", "splu_natural", "banded"}


def cholmod_mode(A, b, mode):
    import sksparse.cholmod

    return sksparse.cholmod.cho_factor(A.tocsc(), order="nesdis", supernodal_mode=mode).solve(b)


def methods(N, A, b, sums, F):
    """(name, function returning xhat) for this N, in output order."""
    scale = 6 * N
    A6, B6 = refine.integer_system(A, b, 6)
    out = [("cholmod_default", lambda: F.solve(b))]
    if N < BIG_N:
        out += [
            ("cholmod_simplicial", lambda: cholmod_mode(A, b, "simplicial")),
            ("cholmod_supernodal", lambda: cholmod_mode(A, b, "supernodal")),
            ("splu_colamd", lambda: direct.factorize(A, "splu", "COLAMD").solve(b)),
        ]
        if N <= SPLU_NATURAL_MAX_N:
            out.append(("splu_natural", lambda: direct.factorize(A, "splu", "NATURAL").solve(b)))
        out += [
            ("banded", lambda: direct.factorize(A, "banded_cholesky", "natural").solve(b)),
            ("banded_int", lambda: direct.factorize(A6, "banded_cholesky", "natural").solve(B6)),
            ("cholmod_int", lambda: direct.factorize(A6, "cholmod", "nesdis").solve(B6)),
            ("gth", lambda: refine.gth_solve(A, b, sums)),
        ]
    out.append(("ir_direct", lambda: refine.iterative_refinement(A, b, F.solve, scale)[0]))
    return out


def warmup():
    """Compile the numba functions (GTH, Dot2 residual) on N = 10."""
    S = StateSpace(10)
    A = build_A(S).tocsr()
    b = rhs_out_first(S, 2)
    refine.gth_solve(A, b, boundary_rhs(S, lambda Y: np.ones(len(Y))))
    refine.accurate_residual(A, b, np.ones(S.n), 60)


def run_size(N):
    S = StateSpace(N)
    A = build_A(S).tocsr()
    b = rhs_out_first(S, 2)
    sums = boundary_rhs(S, lambda Y: np.ones(len(Y)))
    tiny = S.index((1, 1, N - 2))
    scale = 6 * N
    Ai, B = refine.integer_system(A, b, scale)
    F = direct.factorize(A, "cholmod", "nesdis")
    data_term_tiny = acc.data_error_term(F.solve(b), F.solve)[tiny]
    u, N2u = acc.U, N ** 2 * acc.U

    rows = []
    for name, fn in methods(N, A, b, sums, F):
        t0 = time.perf_counter()
        xhat = fn()
        seconds = time.perf_counter() - t0
        if name in ("cholmod_default", "ir_direct"):
            seconds += F.setup_time
        true_err = -F.solve(refine.exact_residual(Ai, B, xhat, denom=scale)) / xhat
        if name in STORED:
            own_err = -F.solve(refine.exact_residual(A, b, xhat)) / xhat
            own_tiny, own_max = own_err[tiny], np.max(np.abs(own_err)) / u
        else:
            own_tiny = own_max = np.nan
        ulp = np.max(np.abs(true_err * xhat) / np.spacing(xhat))
        row = {"N": N, "n": S.n, "method": name, "own_err_tiny": own_tiny, "own_err_over_N2u": own_tiny / N2u,
               "max_own_err_in_u": own_max, "true_err_tiny": true_err[tiny],
               "true_err_over_N2u": true_err[tiny] / N2u, "max_true_err_in_u": np.max(np.abs(true_err)) / u,
               "max_true_err_in_ulp": ulp, "data_term_tiny": data_term_tiny, "seconds": seconds}
        print(f"N = {N:4d}  {name:18s} own {own_tiny:+.3e} ({row['own_err_over_N2u']:+.4f} N^2 u, max {own_max:8.1f} u)"
              f"  true {true_err[tiny]:+.3e} (max {row['max_true_err_in_u']:9.1f} u, {ulp:.3f} ulp)  {seconds:7.2f} s",
              flush=True)
        rows.append(row)
        del xhat, true_err
        gc.collect()  # the band methods and GTH hold about 1 GB each at N = 640
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    warmup()
    rows = []
    for N in QUICK if args.quick else FULL:
        rows += run_size(N)
    path = save_results(rows, "e07_baselines", outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
