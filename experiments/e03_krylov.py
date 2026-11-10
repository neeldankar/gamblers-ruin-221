"""Chunk 3: CG iterations and time for each preconditioner, against the exact spectrum.

Writes results/e03_krylov.csv: one row per (N, kind, rhs) for kind in PRECONDITIONERS (jacobi only up to
N = 320) plus one "direct" row per (N, rhs) (CHOLMOD nesdis; SuperLU MMD_AT_PLUS_A if CHOLMOD is missing).
    python experiments/e03_krylov.py [--quick] [--outdir DIR]

forward_error = max|x - x_direct| / max|x_direct| (NaN on the direct rows, which are the reference).
final_relres = last CG recurrence residual ||r_k|| / ||b||; on direct rows the true residual ||b - A x|| / ||b||.
bound = cg_iteration_bound(kappa2(N), 1e-10), filled only for kind none.
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import gc
import time

import numpy as np

from gr import direct, krylov, spectrum
from gr.matrix import build_A, rhs_order, rhs_out_first, rhs_rounds
from gr.runlog import save_results
from gr.states import StateSpace

FULL = [20, 40, 80, 160, 320, 640, 1280]
QUICK = [20, 40, 80]
JACOBI_MAX_N = 320  # jacobi is identical to none (diag(A) = 1); no need to pay for it at large N
RTOL = 1e-10


def repeats_for(N):
    return 3 if N <= 640 else 1


def right_hand_sides(S):
    rng = np.random.default_rng(221)
    return {
        "ones": rhs_rounds(S),
        "random": rng.standard_normal(S.n),
        "out_first": rhs_out_first(S, 2),  # player 3 out first
        "order321": rhs_order(S, 2, 1, 0),  # 3 out first, then 2, 1 wins
    }


def reference_factor(A, repeats):
    """Factor A `repeats` times (median setup time); return the last factor and that median."""
    try:
        import sksparse.cholmod  # noqa: F401
        method, ordering = "cholmod", "nesdis"
    except ImportError:
        method, ordering = "splu", "MMD_AT_PLUS_A"
    times, F = [], None
    for _ in range(repeats):
        F = None
        gc.collect()
        F = direct.factorize(A, method, ordering)
        times.append(F.setup_time)
    return F, float(np.median(times))


def timed(fn, repeats):
    """Run fn() `repeats` times; return the last result and the median wall time."""
    times, out = [], None
    for _ in range(repeats):
        t0 = time.perf_counter()
        out = fn()
        times.append(time.perf_counter() - t0)
    return out, float(np.median(times))


def run_size(N, kinds):
    S = StateSpace(N)
    A = build_A(S).tocsr()
    rep = repeats_for(N)
    k2 = spectrum.kappa2(N)
    bound = krylov.cg_iteration_bound(k2, RTOL)
    rhs = right_hand_sides(S)
    base = {"N": N, "n": S.n}

    rows, ref = [], {}
    F, setup = reference_factor(A, rep)
    for name, b in rhs.items():
        x, solve_time = timed(lambda: F.solve(b), rep)
        ref[name] = x
        rows.append({**base, "kind": "direct", "rhs": name, "iterations": np.nan, "bound": np.nan,
                     "iterations_over_N": np.nan, "setup_time": setup, "solve_time": solve_time,
                     "time_per_iteration": np.nan,
                     "final_relres": np.linalg.norm(b - A @ x) / np.linalg.norm(b),
                     "forward_error": np.nan, "kappa2": k2})
        print(f"N = {N:4d}  direct  {name:9s} setup {setup:7.3f} s  solve {solve_time:8.4f} s", flush=True)
    del F
    gc.collect()

    for kind in kinds:
        if kind == "jacobi" and N > JACOBI_MAX_N:
            continue
        setups, M = [], None
        for _ in range(rep):
            M = None
            M, t = krylov.make_preconditioner(A, kind)
            setups.append(t)
        setup = float(np.median(setups))
        for name, b in rhs.items():
            (x, info), solve_time = timed(lambda: krylov.cg(A, b, rtol=RTOL, M=M), rep)
            its = info["iterations"]
            xd = ref[name]
            fwd = np.max(np.abs(x - xd)) / np.max(np.abs(xd))
            rows.append({**base, "kind": kind, "rhs": name, "iterations": its,
                         "bound": bound if kind == "none" else np.nan, "iterations_over_N": its / N,
                         "setup_time": setup, "solve_time": solve_time,
                         "time_per_iteration": solve_time / its if its else np.nan,
                         "final_relres": info["residuals"][-1], "forward_error": fwd, "kappa2": k2})
            flag = "" if info["converged"] else "  NOT CONVERGED"
            print(f"N = {N:4d}  {kind:6s}  {name:9s} its {its:5d}  setup {setup:7.3f} s  solve {solve_time:8.3f} s"
                  f"  fwd {fwd:.2e}{flag}", flush=True)
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
        kinds = list(krylov.PRECONDITIONERS)
    except ImportError:
        kinds = [k for k in krylov.PRECONDITIONERS if k != "amg"]
        print("pyamg not installed: skipping amg")
    krylov.warmup()  # compile numba before any timer starts

    rows = []
    for N in QUICK if args.quick else FULL:
        rows += run_size(N, kinds)
    path = save_results(rows, "e03_krylov", outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
