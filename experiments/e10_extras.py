"""Chunk 10 extras: least squares by QR, and unequal skill (Bradley-Terry). See plan/c10_extras.md.

Writes six CSVs:
  e10_regression       N = 300, sextic fit of P/P_ICM per order, by svd, qr, normal_equations, ne_column_scaled.
  e10_degree_sweep     SVD fits of degree 2, 4, 6, 8 per order.
  e10_bt_spectrum      Bradley-Terry, skills (1, 1.5, 2): asymmetry, spectrum of S, pi range, expected rounds.
  e10_bt_solvers       GMRES(30) on A, CG on S (two tolerances), splu on S, against splu on A.
  e10_bt_overflow      first N where naive pi and naive sqrt(pi) overflow; a build at N = 1030.
  e10_bt_states_N80    per-state errors of CG on S and GMRES on A at N = 80, P(strongest wins) (for the figure).
    python experiments/e10_extras.py [--quick] [--outdir DIR]

Errors in e10_bt_solvers are max |u - u_ref| / max |u_ref| with u_ref = splu on A; "lowpi" restricts the max
to the 10% of states with the smallest pi. seconds is the median of 3 solves; building A and S is not timed,
and for splu_S the factorization is counted with the solve.
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse
import math
import time

import numpy as np
import scipy.sparse.linalg as spla

from gr.extras import (build_A_bt, design_matrix, fit_normal_equations, fit_qr, fit_svd, log_pi, monomials,
                       ratio_targets, rhs_win_bt, symmetrize_bt)
from gr.krylov import cg
from gr.runlog import save_results
from gr.states import StateSpace

RNG = np.random.default_rng(221)  # project convention; nothing here is random
SKILLS = (1.0, 1.5, 2.0)
ORDERS = ("321", "312", "213")
REG_N = 300
SPECTRUM_FULL, SPECTRUM_QUICK = [20, 40, 80, 160, 320], [20, 40]
SOLVERS_FULL, SOLVERS_QUICK = [40, 80, 160, 320], [40, 80]
RHS = {"weakest_wins": 0, "strongest_wins": 2, "rounds": None}
OVERFLOW_BUILD_N = 1030
REPEATS = 3


def timed(f, repeats=REPEATS):
    """Result of f() and the median wall time of `repeats` calls."""
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        out = f()
        times.append(time.perf_counter() - t0)
    return out, float(np.median(times))


# ---------------------------------------------------------------- Part A

def fit_ne_column_scaled(X, y):
    """Scale columns to unit norm, solve the normal equations, unscale."""
    c = np.linalg.norm(X, axis=0)
    return fit_normal_equations(X / c, y) / c


METHODS = {"svd": fit_svd, "qr": fit_qr, "normal_equations": fit_normal_equations,
           "ne_column_scaled": fit_ne_column_scaled}


def regression_rows(states, R):
    X = design_matrix(states, REG_N)
    s = np.linalg.svd(X, compute_uv=False)
    cond_X = float(s[0] / s[-1])
    cond_XtX = float(np.linalg.cond(X.T @ X))
    rows = []
    for o in ORDERS:
        y = R[o]
        b_svd = fit_svd(X, y)
        f_svd = X @ b_svd
        for name, fit in METHODS.items():
            beta, sec = timed(lambda: fit(X, y))
            r = y - X @ beta
            rows.append({
                "order": o, "method": name, "cond_X": cond_X, "cond_XtX": cond_XtX,
                "coef_relerr_vs_svd": float(np.linalg.norm(beta - b_svd) / np.linalg.norm(b_svd)),
                "resid_norm": float(np.linalg.norm(r)), "max_abs_resid": float(np.abs(r).max()),
                "fitted_maxdiff_vs_svd": float(np.abs(X @ beta - f_svd).max()), "seconds": sec,
            })
            print(f"{o} {name:17s} coef err {rows[-1]['coef_relerr_vs_svd']:.2e}  "
                  f"max resid {rows[-1]['max_abs_resid']:.6e}  fit diff {rows[-1]['fitted_maxdiff_vs_svd']:.1e}",
                  flush=True)
    print(f"cond(X) = {cond_X:.6e}, cond(X^T X) = {cond_XtX:.4e}", flush=True)
    return rows


def degree_rows(states, R):
    rows = []
    for o in ORDERS:
        for d in (2, 4, 6, 8):
            X = design_matrix(states, REG_N, degree=d)
            s = np.linalg.svd(X, compute_uv=False)
            r = R[o] - X @ fit_svd(X, R[o])
            rows.append({"order": o, "degree": d, "n_coef": len(monomials(d)), "cond_X": float(s[0] / s[-1]),
                         "max_abs_resid": float(np.abs(r).max())})
            print(f"{o} degree {d}: cond {rows[-1]['cond_X']:.4e}  max resid {rows[-1]['max_abs_resid']:.4e}",
                  flush=True)
    return rows


# ---------------------------------------------------------------- Part B

def bt_system(N):
    S = StateSpace(N)
    A = build_A_bt(S, SKILLS)
    lp = log_pi(S, SKILLS)
    return S, A, lp, symmetrize_bt(A, lp)


def gershgorin_lower(skills=SKILLS):
    """Each state has at most two neighbours per pair, each with |S_xy| = (1/3) sqrt(s_a s_b) / (s_a + s_b)."""
    w = [math.sqrt(skills[a] * skills[b]) / (3 * (skills[a] + skills[b])) for a, b in ((0, 1), (0, 2), (1, 2))]
    return 1 - 2 * sum(w)


def spectrum_row(N):
    t0 = time.perf_counter()
    S, A, lp, Ssym = bt_system(N)
    lam_min = float(spla.eigsh(Ssym.tocsc(), k=1, sigma=0, which="LM", return_eigenvectors=False)[0])
    lam_max = float(spla.eigsh(Ssym, k=1, which="LA", return_eigenvectors=False)[0])
    t = spla.splu(A.tocsc()).solve(np.ones(S.n))
    row = {
        "N": N, "n": S.n,
        "max_abs_A_minus_AT": float(abs(A - A.T).max()),
        "rel_asym_S": float(abs(Ssym - Ssym.T).max() / abs(Ssym).max()),
        "lam_min_S": lam_min, "lam_max_S": lam_max, "cond2_S": lam_max / lam_min,
        "gershgorin_lower": gershgorin_lower(),
        "log10_pi_range": float((lp.max() - lp.min()) / math.log(10)),
        "max_expected_rounds": float(t.max()),
        "cond2_A_dense": float(np.linalg.cond(A.toarray())) if N <= 40 else np.nan,
    }
    print(f"N = {N:4d}  lam_min {lam_min:.7f}  lam_max {lam_max:.6f}  cond2_S {row['cond2_S']:.4f}  "
          f"max rounds {row['max_expected_rounds']:.4f}  {time.perf_counter() - t0:.2f} s", flush=True)
    return row


def gmres_A(A, b):
    count = [0]

    def cb(_):
        count[0] += 1

    u, info = spla.gmres(A, b, rtol=1e-10, atol=0.0, restart=30, maxiter=500, callback=cb, callback_type="pr_norm")
    return u, count[0], info == 0


def cg_S(Ssym, dh, rtol):
    def run(b):
        y, info = cg(Ssym, dh * b, rtol=rtol)
        return y / dh, info["iterations"], info["converged"]
    return run


def splu_S(Ssym, dh):
    def run(b):
        return spla.splu(Ssym.tocsc()).solve(dh * b) / dh, 0, True
    return run


def solver_rows(N, states_out):
    S, A, lp, Ssym = bt_system(N)
    dh = np.exp(0.5 * (lp - lp.max()))  # D^{1/2} up to a constant factor
    lowpi = np.argsort(lp)[: math.ceil(0.1 * S.n)]
    ref = spla.splu(A.tocsc())
    methods = {
        "gmres30_A": lambda b: gmres_A(A, b),
        "cg_S_1e-10": cg_S(Ssym, dh, 1e-10),
        "cg_S_1e-15": cg_S(Ssym, dh, 1e-15),
        "splu_S": splu_S(Ssym, dh),
    }
    rows = []
    for rhs, i in RHS.items():
        b = np.ones(S.n) if i is None else rhs_win_bt(S, SKILLS, i)
        u_ref = ref.solve(b)
        scale = np.abs(u_ref).max()
        for name, solve in methods.items():
            (u, iters, converged), sec = timed(lambda: solve(b))
            err = np.abs(u - u_ref) / scale
            rows.append({
                "N": N, "rhs": rhs, "method": name, "iters": iters,
                "rel_residual_A": float(np.linalg.norm(b - A @ u) / np.linalg.norm(b)),
                "max_err_rel": float(err.max()), "max_err_lowpi_rel": float(err[lowpi].max()),
                "seconds": sec,
            })
            print(f"N = {N:4d} {rhs:15s} {name:11s} iters {iters:4d}{'' if converged else ' (not converged)'}  "
                  f"err {err.max():.2e}  lowpi {err[lowpi].max():.2e}  res_A {rows[-1]['rel_residual_A']:.1e}  "
                  f"{sec:.3f} s", flush=True)
            if N == 80 and rhs == "strongest_wins" and name in ("gmres30_A", "cg_S_1e-10"):
                states_out[name] = err
    if N == 80:
        X = S.coords()
        states_out["rows"] = [{"x1": int(a), "x2": int(bb), "x3": int(c), "log_pi": float(l),
                               "err_cg_S": float(ec), "err_gmres_A": float(eg)}
                              for (a, bb, c), l, ec, eg in zip(X, lp, states_out["cg_S_1e-10"],
                                                               states_out["gmres30_A"])]
    return rows


def first_overflow(vals_at):
    """First N >= 3 at which vals_at(N) (a naive product at the state (1, 1, N - 2)) is not finite."""
    with np.errstate(over="ignore"):
        for N in range(3, 5000):
            if not np.isfinite(vals_at(N)):
                return N
    return -1


def overflow_rows():
    s = np.array(SKILLS)
    top = lambda N: np.array([1, 1, N - 2])  # the state with the largest pi
    n_pi = first_overflow(lambda N: np.prod(s ** top(N)))
    n_sqrt = first_overflow(lambda N: np.prod(np.sqrt(s) ** top(N)))
    rows = [{"N": n_pi, "quantity": "first_N_naive_pi_overflows", "value": n_pi},
            {"N": n_sqrt, "quantity": "first_N_naive_sqrt_pi_overflows", "value": n_sqrt}]
    print(f"naive pi overflows from N = {n_pi}, naive sqrt(pi) from N = {n_sqrt}", flush=True)

    t0 = time.perf_counter()
    N = OVERFLOW_BUILD_N
    S, A, lp, Ssym = bt_system(N)
    with np.errstate(over="ignore", invalid="ignore"):
        pi = np.prod(s ** S.coords(), axis=1)  # naive pi: inf at the large-pi states (N >= 1026)
        sqrt_pi = np.sqrt(pi)
        C = A.tocoo()
        naive = sqrt_pi[C.row] * C.data / sqrt_pi[C.col]  # entries of D^{1/2} A D^{-1/2} from naive pi
        naive_bad = int((~np.isfinite(naive)).sum())
    asym = float(abs(Ssym - Ssym.T).max() / abs(Ssym).max())
    rows += [
        {"N": N, "quantity": "n", "value": S.n},
        {"N": N, "quantity": "nnz_A", "value": A.nnz},
        {"N": N, "quantity": "naive_pi_nonfinite_states", "value": int((~np.isfinite(pi)).sum())},
        {"N": N, "quantity": "naive_S_nonfinite_entries", "value": naive_bad},
        {"N": N, "quantity": "logdomain_S_nonfinite_entries", "value": int((~np.isfinite(Ssym.data)).sum())},
        {"N": N, "quantity": "logdomain_S_rel_asym", "value": asym},
    ]
    print(f"N = {N}: naive S has {naive_bad} non-finite entries of {naive.size}; log-domain S "
          f"{rows[-2]['value']} non-finite, rel asym {asym:.1e}  {time.perf_counter() - t0:.1f} s", flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    out = args.outdir

    states, R = ratio_targets(REG_N, ORDERS)
    print(f"wrote {save_results(regression_rows(states, R), 'e10_regression', outdir=out)}")
    print(f"wrote {save_results(degree_rows(states, R), 'e10_degree_sweep', outdir=out)}")

    spec = [spectrum_row(N) for N in (SPECTRUM_QUICK if args.quick else SPECTRUM_FULL)]
    print(f"wrote {save_results(spec, 'e10_bt_spectrum', outdir=out)}")

    states_out, rows = {}, []
    for N in (SOLVERS_QUICK if args.quick else SOLVERS_FULL):
        rows += solver_rows(N, states_out)
    print(f"wrote {save_results(rows, 'e10_bt_solvers', outdir=out)}")
    print(f"wrote {save_results(states_out['rows'], 'e10_bt_states_N80', outdir=out)}")

    print(f"wrote {save_results(overflow_rows(), 'e10_bt_overflow', outdir=out)}")


if __name__ == "__main__":
    main()
