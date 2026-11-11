"""Chunk 8: the Independent Chip Model against the exact gambler's-ruin probabilities.

Writes four CSVs (plan/c08_icm.md):
  e08_wikipedia     N = 200, payouts 50/30/20, three stacks (player 1 first): exact, icm and the published rows.
  e08_icm_errors    one row per N: largest 2nd-place error, equity over/underrate, identity check, signs.
  e08_limit         stacks (N/5, 3N/10, N/2): the six exact probabilities and the observed convergence order.
  e08_states_N120   every state at N = 120: player 1's 2nd-place and equity errors (also in --quick mode,
                    because the figure needs it).
    python experiments/e08_icm.py [--quick] [--outdir DIR]

States in the CSVs are written sorted ascending as "a-b-c", except in e08_wikipedia, where player 1 comes first.
Relative errors are unsigned: |P_ICM - P| / P.
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import time

import numpy as np

from gr.icm import ORDERS, equity, icm_orders, place_probabilities
from gr.matrix import order_probabilities
from gr.runlog import save_results
from gr.states import StateSpace

RNG = np.random.default_rng(221)  # project convention; nothing here is random
PAYOUTS = (50, 30, 20)
IDENTITY_PAYOUTS = [(50, 30, 20), (65, 35, 0), (100, 0, 0), (50, 50, 0)]
# Wikipedia "Independent Chip Model" table, copied from PUBLISHED in tests/c08_icm/test_c08_icm.py.
# Columns P(1st), P(2nd), P(3rd), equity; "fem" is the exact answer.
PUBLISHED = {
    (25, 87, 88): dict(icm=(0.125, 0.1944, 0.6806, 25.69), fem=(0.125, 0.1584, 0.7166, 25.33)),
    (21, 89, 90): dict(icm=(0.105, 0.1701, 0.7249, 24.85), fem=(0.105, 0.1346, 0.7604, 24.50)),
    (198, 1, 1): dict(icm=(0.99, 0.009950, 0.000050, 49.80), fem=(0.99, 0.009999, 0.000001, 49.80)),
}
ERRORS_FULL, ERRORS_QUICK = [30, 60, 120, 240, 480], [30, 60]
LIMIT_FULL, LIMIT_QUICK = [10, 20, 40, 80, 160, 320, 640], [10, 20, 40, 80]


def fmt_state(x):
    return "-".join(str(int(v)) for v in sorted(x))


def places_all(P):
    """Array (3 players, 3 places, n)."""
    return np.array([place_probabilities(P, p) for p in range(3)])


def wikipedia_rows():
    S = StateSpace(200)
    P = order_probabilities(S)
    ex_all = place_probabilities(P, 0)
    rows = []
    for stacks, pub in PUBLISHED.items():
        name = "-".join(map(str, stacks))
        ex = ex_all[:, S.index(stacks)]
        mo = place_probabilities(icm_orders(np.array([stacks])), 0)[:, 0]
        for method, (p1, p2, p3, eq) in [
            ("exact", (*ex, equity(ex, PAYOUTS))),
            ("icm", (*mo, equity(mo, PAYOUTS))),
            ("published_exact", pub["fem"]),
            ("published_icm", pub["icm"]),
        ]:
            rows.append({"stacks": name, "method": method, "p1st": p1, "p2nd": p2, "p3rd": p3, "equity": eq})
        print(f"N = 200 {name}: exact p2nd {ex[1]:.10f} equity {equity(ex, PAYOUTS):.8f}", flush=True)
    return rows


def error_row(N):
    t0 = time.perf_counter()
    S = StateSpace(N)
    X = S.coords()
    ex = places_all(order_probabilities(S))
    mo = places_all(icm_orders(X))
    D = mo[:, 1] - ex[:, 1]  # (3, n): P_ICM(2nd) - P(2nd) per player
    absD = np.abs(D)
    p, i = np.unravel_index(np.argmax(absD), absD.shape)

    rel3 = np.abs(mo[:, 2] - ex[:, 2]) / ex[:, 2]
    pr, ir = np.unravel_index(np.argmax(rel3), rel3.shape)

    deq = equity(mo.transpose(1, 0, 2), PAYOUTS) - equity(ex.transpose(1, 0, 2), PAYOUTS)  # (3, n)
    po, io = np.unravel_index(np.argmax(deq), deq.shape)
    pu, iu = np.unravel_index(np.argmin(deq), deq.shape)

    dev = 0.0
    for w in IDENTITY_PAYOUTS:
        err = equity(mo.transpose(1, 0, 2), w) - equity(ex.transpose(1, 0, 2), w)
        dev = max(dev, float(np.max(np.abs(err - (w[1] - w[2]) * D))))

    Xt = X.T  # (3, n), same layout as D
    unequal = X.min(axis=1) < X.max(axis=1)
    short = (Xt == X.min(axis=1)) & unequal
    long_ = (Xt == X.max(axis=1)) & unequal
    distinct = (X[:, 0] != X[:, 1]) & (X[:, 1] != X[:, 2]) & (X[:, 0] != X[:, 2])
    middle = (Xt != X.min(axis=1)) & (Xt != X.max(axis=1)) & distinct  # one player per distinct state
    frac_mid = float((D[middle] > 0).sum() / distinct.sum())

    row = {
        "N": N, "n": S.n,
        "max_abs_err_p2": float(absD[p, i]), "argmax_state": fmt_state(X[i]),
        "mean_abs_err_p2": float(absD[0].mean()),
        "max_rel_err_p3": float(rel3[pr, ir]), "argmax_rel_state_p3": fmt_state(X[ir]),
        "max_equity_overrate": float(deq[po, io]), "overrate_state": fmt_state(X[io]),
        "max_equity_underrate": float(deq[pu, iu]), "underrate_state": fmt_state(X[iu]),
        "identity_max_dev": dev,
        "short_overrated_all": bool(np.all(D[short] > 0)),
        "long_underrated_all": bool(np.all(D[long_] < 0)),
        "frac_middle_overrated": frac_mid,
        "seconds": time.perf_counter() - t0,
    }
    print(f"N = {N:4d}  max |dP2| {row['max_abs_err_p2']:.10f} at {row['argmax_state']}  "
          f"rel p3 {row['max_rel_err_p3']:.7f} at {row['argmax_rel_state_p3']}  "
          f"underrate {row['max_equity_underrate']:.8f} at {row['underrate_state']}  "
          f"identity {dev:.1e}  {row['seconds']:.2f} s", flush=True)
    return row


def limit_rows(Ns):
    vals, rows = {}, []
    for N in Ns:
        t0 = time.perf_counter()
        S = StateSpace(N)
        P = order_probabilities(S)
        x = (N // 5, 3 * N // 10, N // 2)
        seconds = time.perf_counter() - t0
        v = np.array([P[o][S.index(x)] for o in ORDERS])
        vals[N] = v
        if N // 4 in vals:
            order = np.log2(np.abs(vals[N // 2] - vals[N // 4]) / np.abs(v - vals[N // 2]))
            omin, omax = float(order.min()), float(order.max())
        else:
            omin = omax = np.nan
        C = icm_orders(np.array([x]))
        row = {"N": N, "n": S.n, **{f"P{o}": float(v[k]) for k, o in enumerate(ORDERS)},
               "p1_second": float(P["213"][S.index(x)] + P["312"][S.index(x)]),
               "icm_p1_second": float(C["213"][0] + C["312"][0]),
               "obs_order_min": omin, "obs_order_max": omax, "seconds": seconds}
        print(f"N = {N:4d}  p1_second {row['p1_second']:.10f}  obs order {omin:.3f} to {omax:.3f}  "
              f"{seconds:.2f} s", flush=True)
        rows.append(row)
    return rows


def states_rows(N=120):
    S = StateSpace(N)
    X = S.coords()
    ex = place_probabilities(order_probabilities(S), 0)
    mo = place_probabilities(icm_orders(X), 0)
    dp2 = mo[1] - ex[1]
    deq = equity(mo, PAYOUTS) - equity(ex, PAYOUTS)
    return [{"x1": int(a), "x2": int(b), "x3": int(c), "dp2_player1": float(d), "dequity_player1": float(e)}
            for (a, b, c), d, e in zip(X, dp2, deq)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    out = args.outdir
    print(f"wrote {save_results(wikipedia_rows(), 'e08_wikipedia', outdir=out)}")
    errors = [error_row(N) for N in (ERRORS_QUICK if args.quick else ERRORS_FULL)]
    print(f"wrote {save_results(errors, 'e08_icm_errors', outdir=out)}")
    limit = limit_rows(LIMIT_QUICK if args.quick else LIMIT_FULL)
    print(f"wrote {save_results(limit, 'e08_limit', outdir=out)}")
    print(f"wrote {save_results(states_rows(), 'e08_states_N120', outdir=out)}")


if __name__ == "__main__":
    main()
