"""Chunk 7: settle whether the FFT solver or SuperLU is off at the smallest entry of order 123 (chunk 6).

Writes results/e07_fft_check.csv. b = rhs_order(S, 0, 1, 2) (order 123: player 1 out first, 2 second, 3 wins);
its smallest entry is at the state (N-2, 1, 1). For N in {50, 100, 200, 400, 800}: fft_solve (chunk 6), splu
(COLAMD) and CHOLMOD (nesdis), each compared with ir_direct (iterative refinement after CHOLMOD, reference
"refined") and, for N <= 60, with flint_solve (reference "exact"; ir_direct itself gets a row there too).
Needs chunk 6's gr.fft_solver: without it the script prints a message and writes nothing.
    python experiments/e07_fft_check.py [--quick] [--outdir DIR]

Columns: N, method, reference, rel_err_smallest (|x - x_ref| / x_ref at (N-2, 1, 1)), max_rel_err (all states),
normwise_rel_err (max |x - x_ref| / max x_ref), data_term_smallest (data_error_term(x_ref) at (N-2, 1, 1)), plus
n and signed_err_smallest (added).
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import gc

import numpy as np

from gr import accuracy as acc
from gr import direct, refine
from gr.matrix import build_A, rhs_order
from gr.runlog import save_results
from gr.states import StateSpace

FULL = [50, 100, 200, 400, 800]
QUICK = [50]
EXACT_MAX_N = 60


def run_size(N, fft_solve):
    S = StateSpace(N)
    A = build_A(S).tocsr()
    b = rhs_order(S, 0, 1, 2)
    smallest = S.index((N - 2, 1, 1))
    scale = 6 * N

    F = direct.factorize(A, "cholmod", "nesdis")
    x_ir, info = refine.iterative_refinement(A, b, F.solve, scale)
    if not info["converged"]:
        print(f"N = {N}: WARNING: ir_direct did not converge: {info['corrections']}", flush=True)
    data_term = acc.data_error_term(x_ir, F.solve)
    solutions = {"fft": fft_solve(N, b), "cholmod": F.solve(b)}
    del F
    gc.collect()
    G = direct.factorize(A, "splu", "COLAMD")
    solutions["splu"] = G.solve(b)
    del G
    gc.collect()

    references = [("refined", x_ir)]
    if N <= EXACT_MAX_N:
        references.append(("exact", acc.flint_solve(A, b, scale)))
        solutions["ir_direct"] = x_ir

    rows = []
    for reference, x_ref in references:
        for method, x in solutions.items():
            if method == "ir_direct" and reference == "refined":
                continue  # its own reference
            rel = acc.relative_errors(x, x_ref)
            r = {"N": N, "n": S.n, "method": method, "reference": reference, "rel_err_smallest": rel[smallest],
                 "max_rel_err": rel.max(), "normwise_rel_err": np.max(np.abs(x - x_ref)) / np.max(np.abs(x_ref)),
                 "data_term_smallest": data_term[smallest],
                 "signed_err_smallest": (x[smallest] - x_ref[smallest]) / x_ref[smallest]}
            print(f"N = {N:4d}  {method:9s} vs {reference:7s}  smallest {r['rel_err_smallest']:.2e} "
                  f"(signed {r['signed_err_smallest']:+.2e}, data term {r['data_term_smallest']:+.2e})  "
                  f"max {r['max_rel_err']:.2e}  normwise {r['normwise_rel_err']:.2e}", flush=True)
            rows.append(r)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    try:
        from gr.fft_solver import fft_solve
    except ImportError:
        print("gr.fft_solver not found (chunk 6 is not built yet): skipping e07_fft_check, no CSV written")
        return
    fft_solve(10, np.ones(StateSpace(10).n))  # warm-up
    rows = []
    for N in QUICK if args.quick else FULL:
        rows += run_size(N, fft_solve)
    path = save_results(rows, "e07_fft_check", outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
