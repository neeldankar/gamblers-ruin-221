"""Chunk 4b: what a residual stopping rule controls. Plain CG on four right-hand sides, every entry's error.

The exact identity behind it: with r = b - A x, the error of entry i is e_i = (A^{-1} e_i) . r = g_i . r, so
|e_i| <= ||g_i||_2 ||r||_2. A residual test bounds the ABSOLUTE error of an entry; the ratio
error / (cond_i rtol) is not controlled and varies with the right-hand side and the state.

Writes two CSVs.
  * results/e04_mechanism_rhs.csv: one row per (N, rhs, rtol), N in {320, 640} (--quick: 80), plain CG (kind none,
    maxiter 30000), rtol in {1e-6, 1e-8, 1e-10, 1e-12, 1e-14}. Reference: CHOLMOD nesdis on the stored A (SuperLU
    MMD_AT_PLUS_A if CHOLMOD is missing). Right-hand sides: out_first_3 = rhs_out_first(S, 2), order_321 =
    rhs_order(S, 2, 1, 0), land_mid = rhs_landing(S, (N/2, N/2, 0)), land_quarter = rhs_landing(S, (N/4, 3N/4, 0)).
  * results/e04_mechanism_states.csv: N = 640 (--quick: 80), out_first_3, rtol in {1e-8, 1e-10, 1e-12}: 4000 states
    drawn with np.random.default_rng(221) plus the 200 states with the smallest x (the same states for every rtol).
    python experiments/e04_mechanism.py [--quick] [--outdir DIR]

Column notes (rhs CSV):
  * smallest = the state where x_ref is smallest; cond_i comes from entry_condition at x_ref.
  * ratio_to_cond_rtol = rel_err_smallest / (cond_smallest * rtol).
  * normwise_rel_err = max_i |x - x_ref|_i / max_i |x_ref|_i (as in e04_errors).
  * abs_err_* are |x - x_ref| at the smallest state, and the median and max over all states.
  * true_relres = ||b - A x||_2 / ||b||_2 (the residual recomputed, not CG's recurrence).
  * g = A^{-1} e_smallest, g_norm = ||g||_2, residual_bound_abs = g_norm ||b - A x||_2 (a rigorous bound on
    abs_err_smallest, up to the reference's own error).
  * median_ratio_all_states and q90_ratio_all_states: median and 90th percentile over every state of
    rel_err_i / (cond_i rtol).
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import gc

import numpy as np

from gr import accuracy as acc
from gr import direct, krylov
from gr.matrix import build_A, rhs_landing, rhs_order, rhs_out_first
from gr.runlog import save_results
from gr.states import StateSpace

FULL = [320, 640]
QUICK = [80]
RTOLS = [1e-6, 1e-8, 1e-10, 1e-12, 1e-14]
MAXITER = 30000
STATE_RTOLS = [1e-8, 1e-10, 1e-12]
N_RANDOM_STATES = 4000
N_SMALLEST_STATES = 200


def right_hand_sides(S):
    N = S.N
    return {"out_first_3": rhs_out_first(S, 2),
            "order_321": rhs_order(S, 2, 1, 0),
            "land_mid": rhs_landing(S, (N // 2, N // 2, 0)),
            "land_quarter": rhs_landing(S, (N // 4, 3 * N // 4, 0))}


def reference_factor(A):
    """CHOLMOD nesdis, or SuperLU MMD_AT_PLUS_A if scikit-sparse is missing."""
    try:
        import sksparse.cholmod  # noqa: F401
        return direct.factorize(A, "cholmod", "nesdis")
    except ImportError:
        return direct.factorize(A, "splu", "MMD_AT_PLUS_A")


def sample_states(x_ref):
    """4000 random states (default_rng(221)) plus the 200 with the smallest x_ref, sorted, no duplicates."""
    rng = np.random.default_rng(221)
    random = rng.choice(len(x_ref), size=min(N_RANDOM_STATES, len(x_ref)), replace=False)
    smallest = np.argsort(x_ref)[:N_SMALLEST_STATES]
    return np.union1d(random, smallest)


def run_size(N, states_N):
    S = StateSpace(N)
    A = build_A(S).tocsr()
    F = reference_factor(A)
    X = S.coords()
    rhs_rows, state_rows = [], []
    for name, b in right_hand_sides(S).items():
        x_ref = F.solve(b)
        cond = acc.entry_condition(A, b, x_ref, F.solve)
        s = int(np.argmin(x_ref))
        e = np.zeros(S.n)
        e[s] = 1.0
        g_norm = float(np.linalg.norm(F.solve(e)))  # g = A^{-1} e_s: expected visits to each state from s
        picked = sample_states(x_ref) if (N == states_N and name == "out_first_3") else None

        for rtol in RTOLS:
            x, info = krylov.cg(A, b, rtol=rtol, maxiter=MAXITER)
            res = np.linalg.norm(b - A @ x)
            abs_err = np.abs(x - x_ref)
            rel = abs_err / np.abs(x_ref)
            ratio_all = rel / (cond * rtol)
            r = {"N": N, "rhs": name, "rtol": rtol, "iterations": info["iterations"], "converged": info["converged"],
                 "smallest_state": str(S.state(s)), "x_smallest": x_ref[s], "cond_smallest": cond[s],
                 "rel_err_smallest": rel[s], "ratio_to_cond_rtol": rel[s] / (cond[s] * rtol),
                 "normwise_rel_err": np.max(abs_err) / np.max(np.abs(x_ref)),
                 "abs_err_smallest": abs_err[s], "abs_err_median": np.median(abs_err), "abs_err_max": abs_err.max(),
                 "x_max": x_ref.max(), "true_relres": res / np.linalg.norm(b), "g_norm": g_norm,
                 "residual_bound_abs": g_norm * res, "median_ratio_all_states": np.median(ratio_all),
                 "q90_ratio_all_states": np.quantile(ratio_all, 0.9)}
            rhs_rows.append(r)
            print(f"N = {N:4d}  {name:12s} rtol {rtol:7.0e}  its {info['iterations']:5d}  smallest {r['smallest_state']}  "
                  f"rel {r['rel_err_smallest']:.2e}  ratio {r['ratio_to_cond_rtol']:8.3g}  "
                  f"abs {abs_err[s]:.1e} <= bound {r['residual_bound_abs']:.1e}  g {g_norm:.5f}  "
                  f"median ratio {r['median_ratio_all_states']:.1e}", flush=True)

            if picked is not None and any(np.isclose(rtol, t, rtol=1e-12, atol=0) for t in STATE_RTOLS):
                for i in picked:
                    state_rows.append({"N": N, "rtol": rtol, "x1": int(X[i, 0]), "x2": int(X[i, 1]),
                                       "x3": int(X[i, 2]), "x": x_ref[i], "abs_err": abs_err[i], "rel_err": rel[i],
                                       "cond": cond[i], "ratio": ratio_all[i]})
    del F
    gc.collect()
    return rhs_rows, state_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    sizes = QUICK if args.quick else FULL
    states_N = 80 if args.quick else 640
    rhs_rows, state_rows = [], []
    for N in sizes:
        a, b = run_size(N, states_N)
        rhs_rows += a
        state_rows += b
    for rows, name in ((rhs_rows, "e04_mechanism_rhs"), (state_rows, "e04_mechanism_states")):
        path = save_results(rows, name, outdir=args.outdir)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
