"""Chunk 7: three fixes for the tiny probabilities, measured against the true probability and the stored solution.

Writes results/e07_fixes.csv: one row per (N, method, kind, param), b = out_first_3 (rhs_out_first(S, 2)).
Reference (the true probability): flint_solve for N <= 80 ("exact"); for N >= 160, iterative refinement with the
accurate residual after the CHOLMOD nesdis solve ("refined"; correctly rounded at N <= 80, see the exact rows).
Methods:
  direct            CHOLMOD nesdis (SuperLU MMD_AT_PLUS_A if scikit-sparse is missing)
  gth               gr.refine.gth_solve, N <= 640 (band storage needs about 8 GB at N = 1280)
  cg                gr.krylov.cg at rtol 1e-10 (the usual normwise rule)
  cg_componentwise  stop at omega <= tol, tol 1e-12 and 1e-14; check_every 10 (none), 5 (mic0), 1 (amg)
  ir_direct         iterative refinement with the CHOLMOD factor (at N >= 160 this is the reference itself)
  ir_cg_mic0/amg    iterative refinement with an inner CG at rtol 1e-6, max_steps 15
    python experiments/e07_fixes.py [--quick] [--outdir DIR]

Column notes:
  * kind = preconditioner (CG rows) or ordering (direct rows); param = rtol (cg), tol (cg_componentwise), the inner
    rtol (ir_cg_*), NaN otherwise. iterations_or_steps = CG iterations or refinement steps.
  * setup_seconds = factorization or preconditioner setup; seconds = setup + solve (the whole method). Median of
    REPEATS runs each. ir_direct reuses the direct factor, so its seconds = factor time + refinement time.
  * rel_err_tiny = |x - x_ref| / x_ref at the tiny state (1, 1, N-2); max_rel_err over all states; both against
    the true probability. signed_err_tiny = (x - x_ref) / x_ref at the tiny state (added).
  * omega = componentwise backward error of the stored system (gr.accuracy, naive residual).
  * cond_tiny = entry_condition at x_ref; data_term_tiny = data_error_term(x_ref) at the tiny state.
  * The stored solution is x_stored = x_ref (1 + data_error_term(x_ref)). err_vs_stored_tiny is SIGNED,
    (x - x_stored) / x_stored at the tiny state; max_err_vs_stored = max_i |x - x_stored|_i / x_stored_i.
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import gc
import time

import numpy as np

from gr import accuracy as acc
from gr import direct, krylov, refine
from gr.matrix import boundary_rhs, build_A, rhs_out_first
from gr.runlog import save_results
from gr.states import StateSpace

FULL = [20, 40, 60, 80, 160, 320, 640, 1280]
QUICK = [20, 40]
EXACT_MAX_N = 80  # flint_solve is dense: about 30 s at N = 80
GTH_MAX_N = 640  # band storage n (N - 1) doubles: 1.04 GB at N = 640, 8.4 GB at N = 1280
KINDS = ["none", "mic0", "amg"]
CHECK_EVERY = {"none": 10, "mic0": 5, "amg": 1}
CG_RTOL = 1e-10
CW_TOLS = [1e-12, 1e-14]
INNER_RTOL = 1e-6
IR_CG_STEPS = 15
MAXITER = 30000
REPEATS = 3


def timed(fn, repeats=REPEATS):
    """Run fn() `repeats` times; return the last result and the median wall time."""
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        out = fn()
        times.append(time.perf_counter() - t0)
    return out, float(np.median(times))


def reference_factor(A):
    """CHOLMOD nesdis, or SuperLU MMD_AT_PLUS_A if scikit-sparse is missing (as in e04_errors)."""
    try:
        import sksparse.cholmod  # noqa: F401
        return direct.factorize(A, "cholmod", "nesdis")
    except ImportError:
        return direct.factorize(A, "splu", "MMD_AT_PLUS_A")


def warmup():
    """Compile every numba function on N = 10 before anything is timed."""
    krylov.warmup()
    S = StateSpace(10)
    A = build_A(S).tocsr()
    b = rhs_out_first(S, 2)
    refine.gth_solve(A, b, boundary_rhs(S, lambda Y: np.ones(len(Y))))
    refine.accurate_residual(A, b, np.ones(S.n), 60)


def run_size(N, kinds):
    S = StateSpace(N)
    A = build_A(S).tocsr()
    b = rhs_out_first(S, 2)
    tiny = S.index((1, 1, N - 2))
    scale = 6 * N

    F, factor_time = timed(lambda: reference_factor(A))
    x_direct, solve_time = timed(lambda: F.solve(b))
    if N <= EXACT_MAX_N:
        t0 = time.perf_counter()
        x_ref, reference = acc.flint_solve(A, b, scale), "exact"
        print(f"N = {N:4d}  flint_solve {time.perf_counter() - t0:.1f} s", flush=True)
    else:
        x_ref, info = refine.iterative_refinement(A, b, F.solve, scale, x0=x_direct)
        reference = "refined"
        if not info["converged"]:
            print(f"N = {N:4d}  WARNING: reference refinement did not converge: {info['corrections']}", flush=True)
    cond = acc.entry_condition(A, b, x_ref, F.solve)
    data_term = acc.data_error_term(x_ref, F.solve)
    x_stored = x_ref * (1 + data_term)

    def row(method, kind, x, seconds, setup=np.nan, param=np.nan, its=np.nan, converged=True):
        rel = acc.relative_errors(x, x_ref)
        vs_stored = (x - x_stored) / x_stored
        r = {"N": N, "n": S.n, "method": method, "kind": kind, "param": param, "iterations_or_steps": its,
             "converged": converged, "setup_seconds": setup, "seconds": seconds, "reference": reference,
             "rel_err_tiny": rel[tiny], "max_rel_err": rel.max(), "max_rel_err_in_u": rel.max() / acc.U,
             "omega": acc.componentwise_backward_error(A, x, b), "cond_tiny": cond[tiny],
             "data_term_tiny": data_term[tiny], "err_vs_stored_tiny": vs_stored[tiny],
             "max_err_vs_stored": np.max(np.abs(vs_stored)), "signed_err_tiny": (x[tiny] - x_ref[tiny]) / x_ref[tiny]}
        flag = "" if converged else "  NOT CONVERGED"
        print(f"N = {N:4d}  {method:16s} {kind:7s} {param:7.0e}  its {its:>6}  {seconds:8.3f} s  "
              f"tiny {r['rel_err_tiny']:.2e}  max {r['max_rel_err_in_u']:9.1f} u  vs stored {vs_stored[tiny]:+.2e}  "
              f"omega {r['omega'] / acc.U:.1f} u{flag}", flush=True)
        return r

    rows = [row("direct", F.ordering, x_direct, factor_time + solve_time, setup=factor_time)]
    (x, info), t = timed(lambda: refine.iterative_refinement(A, b, F.solve, scale))
    rows.append(row("ir_direct", F.ordering, x, factor_time + t, setup=factor_time, its=info["steps"],
                    converged=info["converged"]))
    del F
    gc.collect()

    if N <= GTH_MAX_N:
        sums = boundary_rhs(S, lambda Y: np.ones(len(Y)))
        x, t = timed(lambda: refine.gth_solve(A, b, sums))
        rows.append(row("gth", "natural", x, t))
        del x
        gc.collect()

    for kind in kinds:
        (M, _), setup = timed(lambda: krylov.make_preconditioner(A, kind))
        (x, info), t = timed(lambda: krylov.cg(A, b, rtol=CG_RTOL, maxiter=MAXITER, M=M))
        rows.append(row("cg", kind, x, setup + t, setup, CG_RTOL, info["iterations"], info["converged"]))
        for tol in CW_TOLS:
            (x, info), t = timed(lambda: refine.cg_componentwise(A, b, tol, M=M, check_every=CHECK_EVERY[kind],
                                                                 maxiter=MAXITER))
            rows.append(row("cg_componentwise", kind, x, setup + t, setup, tol, info["iterations"], info["converged"]))
            if not info["converged"]:
                print(f"            smallest omega reached: {info['omegas'].min():.2e}", flush=True)
        if kind != "none":
            inner = lambda r: krylov.cg(A, r, rtol=INNER_RTOL, maxiter=MAXITER, M=M)[0]  # noqa: E731
            (x, info), t = timed(lambda: refine.iterative_refinement(A, b, inner, scale, max_steps=IR_CG_STEPS))
            rows.append(row(f"ir_cg_{kind}", kind, x, setup + t, setup, INNER_RTOL, info["steps"], info["converged"]))
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
    warmup()
    rows = []
    for N in QUICK if args.quick else FULL:
        rows += run_size(N, kinds)
    path = save_results(rows, "e07_fixes", outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
