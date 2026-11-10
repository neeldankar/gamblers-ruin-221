"""Chunk 4: which solvers get the tiny probability right? Forward and backward errors for b = out_first_3.

Writes results/e04_errors.csv: one row per (N, method, kind, rtol). The reference is the exact rational solve
(flint_solve) for N in {20, 40, 80} (reference = "exact") and the CHOLMOD nesdis solve for N >= 160
(reference = "direct", trusted to its certified bound from e04_condition). Methods: cholmod (nesdis), splu
(COLAMD), banded (N <= 400) and CG with kinds none, mic0, amg at five rtols (maxiter 30000).
    python experiments/e04_errors.py [--quick] [--outdir DIR]

Column notes:
  * kind is the CG preconditioner, or the ordering on direct rows; rtol and iterations are NaN on direct rows.
  * cond_i comes from entry_condition at the reference solution. tiny = the state (1, 1, N-2).
  * cond_times_rtol = cond_tiny * rtol and ratio_tiny_to_prediction = rel_err_tiny / cond_times_rtol (CG only).
  * max_err_over_bound = max_i rel_err_i / (2 cond_i max(omega, u)) (added: the first-order bound, entry by
    entry; at most 1 means it holds in every entry).
  * At N >= 160 the cholmod row is its own reference, so its errors are 0 by construction.
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import gc
import time

import numpy as np

from gr import accuracy as acc
from gr import direct, krylov
from gr.matrix import build_A, rhs_out_first
from gr.runlog import save_results
from gr.states import StateSpace

FULL = [20, 40, 80, 160, 320, 640, 1280]
QUICK = [20, 40]
EXACT_MAX_N = 80  # flint_solve is dense: about 30 s at N = 80, do not go higher
BANDED_MAX_N = 400
KINDS = ["none", "mic0", "amg"]
RTOLS = [1e-6, 1e-8, 1e-10, 1e-12, 1e-14]
MAXITER = 30000


def reference_factor(A):
    """CHOLMOD nesdis, or SuperLU MMD_AT_PLUS_A if scikit-sparse is missing."""
    try:
        import sksparse.cholmod  # noqa: F401
        return direct.factorize(A, "cholmod", "nesdis")
    except ImportError:
        return direct.factorize(A, "splu", "MMD_AT_PLUS_A")


def run_size(N, kinds):
    S = StateSpace(N)
    A = build_A(S).tocsr()
    b = rhs_out_first(S, 2)
    tiny = S.index((1, 1, N - 2))

    F = reference_factor(A)
    x_direct = F.solve(b)
    if N <= EXACT_MAX_N:
        t0 = time.perf_counter()
        x_ref, reference = acc.flint_solve(A, b, 6 * N), "exact"
        print(f"N = {N:4d}  flint_solve {time.perf_counter() - t0:.1f} s", flush=True)
    else:
        x_ref, reference = x_direct, "direct"
    cond = acc.entry_condition(A, b, x_ref, F.solve)

    def row(method, kind, x, rtol=np.nan, iterations=np.nan, converged=True):
        rel = acc.relative_errors(x, x_ref)
        omega = acc.componentwise_backward_error(A, x, b)
        pred = cond[tiny] * rtol
        r = {"N": N, "n": S.n, "method": method, "kind": kind, "rtol": rtol, "iterations": iterations,
             "converged": converged, "reference": reference, "rel_err_tiny": rel[tiny], "max_rel_err": rel.max(),
             "argmax_rel_err_state": str(S.state(int(np.argmax(rel)))),
             "normwise_rel_err": np.max(np.abs(x - x_ref)) / np.max(np.abs(x_ref)),
             "normwise_backward_error": acc.normwise_backward_error(A, x, b),
             "componentwise_backward_error": omega, "cond_tiny": cond[tiny], "cond_times_rtol": pred,
             "ratio_tiny_to_prediction": rel[tiny] / pred, "max_err_over_bound": np.max(rel / (2 * cond * max(omega, acc.U)))}
        flag = "" if converged else "  NOT CONVERGED"
        print(f"N = {N:4d}  {method:7s} {kind:7s} rtol {rtol:7.0e}  its {iterations:>6}  tiny {r['rel_err_tiny']:.2e}  "
              f"max {r['max_rel_err']:.2e}  nw {r['normwise_rel_err']:.2e}  omega_nw {r['normwise_backward_error']:.1e}  "
              f"omega_cw {omega:.1e}  ratio {r['ratio_tiny_to_prediction']:.3g}{flag}", flush=True)
        return r

    rows = [row(F.method, F.ordering, x_direct)]
    del F  # free the reference factor before the next factorization
    gc.collect()

    others = [("splu", "COLAMD")] + ([("banded_cholesky", "natural")] if N <= BANDED_MAX_N else [])
    for method, ordering in others:
        G = direct.factorize(A, method, ordering)
        rows.append(row("banded" if method == "banded_cholesky" else method, ordering, G.solve(b)))
        del G
        gc.collect()

    for kind in kinds:
        M, _ = krylov.make_preconditioner(A, kind)
        for rtol in RTOLS:
            x, info = krylov.cg(A, b, rtol=rtol, maxiter=MAXITER, M=M)
            rows.append(row("cg", kind, x, rtol, info["iterations"], info["converged"]))
        del M
        gc.collect()
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    try:
        import pyamg  # noqa: F401
        kinds = KINDS
    except ImportError:
        kinds = [k for k in KINDS if k != "amg"]
        print("pyamg not installed: skipping amg")
    rows = []
    for N in QUICK if args.quick else FULL:
        rows += run_size(N, kinds)
    path = save_results(rows, "e04_errors", outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
