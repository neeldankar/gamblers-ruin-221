"""Chunk 4: the componentwise condition number of every entry, and how big the tiny entry's is.

Writes results/e04_condition.csv: one row per (N, event), events out_first_3 (rhs_out_first(S, 2)) and
order_321 (rhs_order(S, 2, 1, 0)). One CHOLMOD nesdis factor per N (SuperLU MMD_AT_PLUS_A if CHOLMOD is missing)
gives x and is reused for the extra solves behind cond and E[T | event].
    python experiments/e04_condition.py [--quick] [--outdir DIR]

tiny = the state (1, 1, N-2). certified_bound = max_i cond_i * omega_direct, a first-order bound on the
largest relative error of any entry of the direct solution.
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import gc

import numpy as np

from gr import accuracy as acc
from gr import direct
from gr.matrix import build_A, rhs_order, rhs_out_first
from gr.runlog import save_results
from gr.states import StateSpace

FULL = [10, 20, 40, 80, 160, 320, 640, 1280]
QUICK = [10, 20, 40]
EVENTS = {"out_first_3": lambda S: rhs_out_first(S, 2), "order_321": lambda S: rhs_order(S, 2, 1, 0)}


def reference_factor(A):
    """CHOLMOD nesdis, or SuperLU MMD_AT_PLUS_A if scikit-sparse is missing."""
    try:
        import sksparse.cholmod  # noqa: F401
        return direct.factorize(A, "cholmod", "nesdis")
    except ImportError:
        return direct.factorize(A, "splu", "MMD_AT_PLUS_A")


def state_str(S, i):
    return str(S.state(int(i)))  # "(x1, x2, x3)"


def run_size(N):
    S = StateSpace(N)
    A = build_A(S).tocsr()
    F = reference_factor(A)
    tiny = S.index((1, 1, N - 2))
    rows = []
    for event, make_b in EVENTS.items():
        b = make_b(S)
        x = F.solve(b)
        cond = acc.entry_condition(A, b, x, F.solve)
        ET = acc.conditional_mean_time(A, x, F.solve)
        omega = acc.componentwise_backward_error(A, x, b)
        rows.append({"N": N, "n": S.n, "event": event, "method": F.method, "ordering": F.ordering,
                     "argmin_state": state_str(S, np.argmin(x)), "x_tiny": x[tiny], "N3_x_tiny": N ** 3 * x[tiny],
                     "cond_tiny": cond[tiny], "cond_tiny_over_N2": cond[tiny] / N ** 2,
                     "cond_max_over_N2": cond.max() / N ** 2, "argmax_cond_state": state_str(S, np.argmax(cond)),
                     "ET_tiny_over_N2": ET[tiny] / N ** 2, "omega_direct": omega,
                     "omega_over_u": omega / acc.U, "certified_bound": cond.max() * omega})
        r = rows[-1]
        print(f"N = {N:4d}  {event:11s}  N^3 x_tiny {r['N3_x_tiny']:.7f}  cond/N^2 {r['cond_tiny_over_N2']:.5f}  "
              f"omega {r['omega_over_u']:5.1f} u  bound {r['certified_bound']:.2e}  argmin {r['argmin_state']}  "
              f"argmax cond {r['argmax_cond_state']}", flush=True)
    del F
    gc.collect()
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    rows = []
    for N in QUICK if args.quick else FULL:
        rows += run_size(N)
    path = save_results(rows, "e04_condition", outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
