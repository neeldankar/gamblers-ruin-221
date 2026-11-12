"""Chunk 9: four players.

Writes results/e09_identities.csv, e09_solvers.csv, e09_big_stack.csv and e09_alpha.csv.
    PYTHONPATH=. python experiments/e09_four.py [--quick] [--big] [--outdir DIR]

Every solver run of e09_solvers, and every four-player lumped solve of e09_big_stack, happens in a fresh process
(experiments/e09_worker.py), so its peak memory is its own. Memory safety (the spec's red flag: never let the laptop swap):
  * a direct method skips a size when its projected factor memory (8 bytes per stored entry, nnz_factor
    fitted against n on the sizes already done) exceeds 3 GB, and then skips every larger size too;
  * the parent watches each worker's resident memory and kills it above 60% of the free memory measured at
    the start of the run.
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import itertools
import json
import pathlib
import re
import subprocess
import sys
import time

import numpy as np

from gr import direct
from gr.four import FourStateSpace, build_A4, rhs_out_first4, rhs_win4
from gr.matrix import build_A, rhs_out_first, solve
from gr.runlog import save_results
from gr.states import StateSpace

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKER = ROOT / "experiments" / "e09_worker.py"

ID_N, ID_N_QUICK = [10, 20, 30, 40, 60], [10, 20]
DIRECT_N, AMG_N, SOLVER_N_QUICK = [20, 40, 60, 80, 100], [20, 40, 60, 80, 100, 120, 150, 200], [20, 40]
DIRECT_METHODS = ["splu", "splu_mmd", "cholmod"]
FOUR_N = [8, 10, 12, 16, 20, 24, 30, 40, 50, 60, 80, 100, 120, 160, 200]
THREE_N = [10, 20, 40, 80, 160, 320]
FACTOR_LIMIT_GB = 3.0
BYTES_PER_ENTRY = 8
SLOPE_ONE_POINT = 1.5  # fill exponent assumed when only one size has been factored
KILL_FRACTION = 0.6
POLL_S = 0.5


def free_memory_mb():
    """Memory the OS can hand out now: free + inactive + speculative pages (macOS), MemAvailable (Linux)."""
    try:
        text = subprocess.run(["vm_stat"], capture_output=True, text=True, check=True).stdout
        page = int(re.search(r"page size of (\d+) bytes", text).group(1))
        pages = {k: int(v) for k, v in re.findall(r"Pages (\w+):\s+(\d+)\.", text)}
        return page * (pages["free"] + pages["inactive"] + pages["speculative"]) / 2**20
    except (OSError, subprocess.CalledProcessError, AttributeError, KeyError):
        with open("/proc/meminfo") as fh:
            return int(re.search(r"MemAvailable:\s+(\d+) kB", fh.read()).group(1)) / 2**10


def e2_e4(S):
    X = S.coords().astype(float)
    e2 = sum(X[:, i] * X[:, j] for i, j in itertools.combinations(range(4), 2))
    return X, e2, X.prod(axis=1)


# ---------------------------------------------------------------- 1. identities
def identities_row(N):
    S = FourStateSpace(N)
    A = build_A4(S)
    X, e2, e4 = e2_e4(S)
    F = direct.factorize(A.tocsc(), "cholmod", "metis")
    B = np.column_stack([e2, np.ones(S.n)] + [rhs_win4(S, i) for i in range(4)]
                        + [rhs_out_first4(S, i) for i in range(4)])
    U = F.solve(B)
    u_e2, T, win, out = U[:, 0], U[:, 1], U[:, 2:6], U[:, 6:10]
    identity = np.max(np.abs(A @ (6 * e4) - e2)) / np.max(e2)
    solved = np.max(np.abs(u_e2 - 6 * e4)) / np.max(6 * e4)
    k = int(np.argmax(T))
    r1, r2 = T / (e4 / N), T * e2 / (6 * e4)
    nnz_row = np.diff(A.indptr)
    return {
        "N": N,
        "n": S.n,
        "max_nnz_row": int(nnz_row.max()),
        "max_abs_A_minus_AT": float(abs(A - A.T).max()),
        "e2_identity_relerr": float(max(identity, solved)),
        "win_maxerr": float(np.max(np.abs(win - X / N))),
        "out_first_sum_maxerr": float(np.max(np.abs(out.sum(axis=1) - 1))),
        "T_max": float(T[k]),
        "T_max_state": "-".join(str(v) for v in S.state(k)),
        "T_over_e4N_min": float(r1.min()),
        "T_over_e4N_max": float(r1.max()),
        "T_e2_over_6e4_min": float(r2.min()),
        "T_e2_over_6e4_max": float(r2.max()),
        "bounds_hold": bool(np.all(T >= 16 * e4 / N**2 - 1e-9) and np.all(T <= 2 * e4 / (N - 2) + 1e-9)),
    }


# ---------------------------------------------------------------- 2. solvers
def rss_mb(pid):
    out = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    return int(out) / 1024 if out else 0.0


def run_worker(method, N, kill_mb):
    """Run one worker; return its JSON result, or None and a status if it was killed or crashed."""
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    proc = subprocess.Popen([sys.executable, str(WORKER), "--method", method, "--N", str(N)], cwd=ROOT, env=env,
                            stdout=subprocess.PIPE, text=True)
    seen = 0.0
    while proc.poll() is None:
        seen = max(seen, rss_mb(proc.pid))
        if seen > kill_mb:
            proc.kill()
            proc.wait()
            return None, f"killed: rss over {kill_mb / 1024:.1f} GB (60% of free memory)"
        time.sleep(POLL_S)
    out = proc.stdout.read()
    if proc.returncode != 0:
        return None, f"failed: exit code {proc.returncode}"
    return json.loads(out.strip().splitlines()[-1]), None


def projected_factor_gb(done, n):
    """Factor memory at size n from a log-log fit of nnz_factor against n over the sizes done."""
    if not done:
        return 0.0
    ns, nnz = np.log([d[0] for d in done]), np.log([d[1] for d in done])
    slope = np.polyfit(ns, nnz, 1)[0] if len(done) > 1 else SLOPE_ONE_POINT
    return BYTES_PER_ENTRY * np.exp(nnz[-1] + slope * (np.log(n) - ns[-1])) / 2**30


def empty_row(N, n, method, status):
    return {"N": N, "n": n, "method": method, "setup_s": np.nan, "solve_s": np.nan, "peak_rss_mb": np.nan,
            "nnz_factor": np.nan, "iters": np.nan, "rel_err": np.nan, "status": status}


def solver_rows(quick, kill_mb):
    plan = [(m, SOLVER_N_QUICK if quick else DIRECT_N) for m in DIRECT_METHODS]
    plan.append(("amg_cg", SOLVER_N_QUICK if quick else AMG_N))
    rows = []
    for method, Ns in plan:
        done, stopped = [], None
        for N in Ns:
            n = (N - 1) * (N - 2) * (N - 3) // 6
            gb = projected_factor_gb(done, n) if method != "amg_cg" else 0.0
            if gb > FACTOR_LIMIT_GB:
                stopped = f"skipped: projected factor {gb:.1f} GB > {FACTOR_LIMIT_GB:.0f} GB"
            elif stopped is not None:
                stopped = f"skipped: a smaller N stopped ({stopped})"
            if stopped is not None:
                rows.append(empty_row(N, n, method, stopped))
                print(f"{method:8s} N = {N:3d}  {stopped}", flush=True)
                continue
            t0 = time.perf_counter()
            res, bad = run_worker(method, N, kill_mb)
            if res is None:
                rows.append(empty_row(N, n, method, bad))
                stopped = bad
            else:
                rows.append(res)
                if method != "amg_cg":
                    done.append((res["n"], res["nnz_factor"]))
            r = rows[-1]
            print(f"{method:8s} N = {N:3d}  n {n:>9,d}  setup {r['setup_s']:8.3f} s  solve {r['solve_s']:7.3f} s  "
                  f"rss {r['peak_rss_mb']:7.0f} MB  nnz {r['nnz_factor']:.3g}  iters {r['iters']}  "
                  f"err {r['rel_err']:.1e}  {r['status']}  ({time.perf_counter() - t0:.0f} s wall)", flush=True)
    return rows


# ---------------------------------------------------------------- 3. big stack and 4. alpha
def big_stack_rows(quick, kill_mb):
    rows = []
    for N in [N for N in FOUR_N if not quick or N <= 40]:
        res, bad = run_worker("lumped", N, kill_mb)  # its own process, under the same memory watch
        if res is None:
            res = {"N": N, "n_lumped": np.nan, "P": np.nan, "seconds": np.nan, "solver": bad, "peak_rss_mb": np.nan}
        rows.append({"players": 4, "n_full": (N - 1) * (N - 2) * (N - 3) // 6, **res})
        print(f"four players N = {N:3d}  n_lumped {res['n_lumped']}  P = {res['P']:.12e}  {res['seconds']:.2f} s  "
              f"rss {res['peak_rss_mb']:.0f} MB  {res['solver']}", flush=True)
    for N in THREE_N:
        t0 = time.perf_counter()
        S = StateSpace(N)
        P = float(solve(build_A(S), rhs_out_first(S, 2))[S.index((1, 1, N - 2))])
        rows.append({"players": 3, "N": N, "n_full": S.n, "n_lumped": np.nan, "P": P,
                     "seconds": time.perf_counter() - t0, "solver": "splu", "peak_rss_mb": np.nan})
        print(f"three players N = {N:3d}  P = {P:.12e}  P N^3 = {P * N**3:.6f}", flush=True)
    for players in (3, 4):  # local_slope = log(P(previous N) / P(N)) / log(N / previous N)
        group = [r for r in rows if r["players"] == players]
        group[0]["local_slope"] = np.nan
        for prev, r in zip(group, group[1:]):
            r["local_slope"] = np.log(prev["P"] / r["P"]) / np.log(r["N"] / prev["N"])
    cols = ["players", "N", "n_full", "n_lumped", "P", "local_slope", "seconds", "solver", "peak_rss_mb"]
    return [{c: r[c] for c in cols} for r in rows]


def alpha_rows(big):
    """alpha_extrapolated: least-squares line slope = a + c / N_mid through the last four local slopes,
    N_mid = sqrt(previous N * N); a is the slope at N = infinity."""
    rows = []
    for players in (3, 4):
        group = [r for r in big if r["players"] == players]
        Ns = np.array([r["N"] for r in group], dtype=float)
        slopes = np.array([r["local_slope"] for r in group])
        x = 1 / np.sqrt(Ns[1:] * Ns[:-1])[-4:]
        a = np.polyfit(x, slopes[1:][-4:], 1)[1]
        rows.append({"players": players, "alpha_last_slope": float(slopes[-1]), "alpha_extrapolated": float(a)})
        print(f"players {players}: last slope {slopes[-1]:.5f}, extrapolated {a:.5f}", flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--big", action="store_true", help="not implemented in this run (needs 5-6 GB)")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    if args.big:
        sys.exit("--big is not implemented: it needs 5-6 GB and this run was asked to stay without it")
    np.random.default_rng(221)  # project convention; every right-hand side here is deterministic

    free_mb = free_memory_mb()
    kill_mb = KILL_FRACTION * free_mb
    print(f"free memory at start: {free_mb:.0f} MB; workers are killed above {kill_mb:.0f} MB", flush=True)
    stamp = {"free_mem_mb_start": round(free_mb)}

    t0 = time.perf_counter()
    rows = []
    for N in ID_N_QUICK if args.quick else ID_N:
        rows.append({**identities_row(N), **stamp})
        print(rows[-1], flush=True)
    print(f"wrote {save_results(rows, 'e09_identities', outdir=args.outdir)} ({time.perf_counter() - t0:.0f} s)")

    rows = [{**r, **stamp} for r in solver_rows(args.quick, kill_mb)]
    print(f"wrote {save_results(rows, 'e09_solvers', outdir=args.outdir)} ({time.perf_counter() - t0:.0f} s)")

    big = big_stack_rows(args.quick, kill_mb)
    print(f"wrote {save_results([{**r, **stamp} for r in big], 'e09_big_stack', outdir=args.outdir)}")
    rows = [{**r, **stamp} for r in alpha_rows(big)]
    print(f"wrote {save_results(rows, 'e09_alpha', outdir=args.outdir)} ({time.perf_counter() - t0:.0f} s)")


if __name__ == "__main__":
    main()
