"""Chunk 7 follow-up: how small can the componentwise backward error omega get along the CG iteration?

Writes results/e07_floor.csv: one row per (N, kind), b = out_first_3 (rhs_out_first(S, 2)).
For each kind (none, check_every 10; mic0, 5; amg, 1): k10 = the iterations of gr.krylov.cg at rtol 1e-10 with the
same preconditioner; then cg_componentwise(A, b, tol=0.0, M=M, check_every=c, maxiter=4 * k10). tol 0 never
triggers, so the run goes to maxiter and its omega history shows the floor. One run, no timing.
    python experiments/e07_floor.py [--quick] [--outdir DIR]

Columns: min_omega = smallest omega after k = 0 (omega is recorded at k = 0, c, 2c, ...), k_at_min = the iteration
where it occurred, k_at_min_over_k10 = k_at_min / k10 (above about 3.5 means maxiter cut the run before the floor),
final_omega_in_u = omega at the last recorded iteration, in units of u = 2^-53.
Then plain gr.krylov.cg(A, b, rtol=0.0, M=M, maxiter=4 * k10) from x0 = 0, with a callback that records each iterate's
|x_k[tiny]| (tiny = (1, 1, N-2)) and max |x_k|: max_x_corner_ratio = max_k |x_k[tiny]| / x_ref[tiny] and
max_x_inf_ratio = max_k max |x_k| / max |x_ref|, x_ref = the CHOLMOD nesdis solve. Greenbaum (1997): rounding in the
recursively updated residual grows with the largest iterate, so an iterate that overshoots at the corner could
explain plain CG's componentwise floor (review 2, question 4).
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import gc

import numpy as np

from gr import direct, krylov, refine
from gr.accuracy import U
from gr.matrix import build_A, rhs_out_first
from gr.runlog import save_results
from gr.states import StateSpace

FULL = [80, 160, 320, 640, 1280]
QUICK = [80, 160]
KINDS = ["none", "mic0", "amg"]
CHECK_EVERY = {"none": 10, "mic0": 5, "amg": 1}
MAXITER_RTOL = 30000  # cap for the rtol 1e-10 run, as in e04 and e07_fixes


def run_size(N, kinds):
    S = StateSpace(N)
    A = build_A(S).tocsr()
    b = rhs_out_first(S, 2)
    tiny = S.index((1, 1, N - 2))
    x_ref = direct.factorize(A, "cholmod", "nesdis").solve(b)
    rows = []
    for kind in kinds:
        c = CHECK_EVERY[kind]
        M, _ = krylov.make_preconditioner(A, kind)
        k10 = krylov.cg(A, b, rtol=1e-10, maxiter=MAXITER_RTOL, M=M)[1]["iterations"]
        _, info = refine.cg_componentwise(A, b, 0.0, M=M, check_every=c, maxiter=4 * k10)
        om = info["omegas"]

        peak = {"corner": 0.0, "inf": 0.0}  # the largest |x_k[tiny]| and max |x_k| over the iterates

        def track(x):
            peak["corner"] = max(peak["corner"], abs(x[tiny]))
            peak["inf"] = max(peak["inf"], np.abs(x).max())

        krylov.cg(A, b, rtol=0.0, M=M, maxiter=4 * k10, callback=track)
        j = int(np.argmin(om[1:])) + 1  # skip k = 0, where omega = 1
        r = {"N": N, "kind": kind, "check_every": c, "iters_rtol_1e10": k10, "maxiter": 4 * k10,
             "min_omega": om[j], "min_omega_in_u": om[j] / U, "k_at_min": j * c, "k_at_min_over_k10": j * c / k10,
             "final_omega_in_u": om[-1] / U, "max_x_corner_ratio": peak["corner"] / x_ref[tiny],
             "max_x_inf_ratio": peak["inf"] / np.abs(x_ref).max()}
        print(f"N = {N:4d}  {kind:5s}  k10 {k10:5d}  min omega {r['min_omega']:.3e} ({r['min_omega_in_u']:.1f} u) "
              f"at k = {r['k_at_min']} ({r['k_at_min_over_k10']:.2f} k10)  final {r['final_omega_in_u']:.1f} u  "
              f"peak/x_ref: corner {r['max_x_corner_ratio']:.4f}, inf {r['max_x_inf_ratio']:.4f}",
              flush=True)
        rows.append(r)
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
    krylov.warmup()
    rows = []
    for N in QUICK if args.quick else FULL:
        rows += run_size(N, kinds)
    path = save_results(rows, "e07_floor", outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
