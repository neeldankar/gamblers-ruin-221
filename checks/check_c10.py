"""Chunk 10 check: compare results/e10_*.csv with the "Expected results" table of plan/c10_extras.md. Prints one
PASS/WARN/FAIL line per table row (plus automatic red-flag checks) and writes results/c10_report.md.
    python checks/check_c10.py [--results DIR]

Conventions (logged in notes/decisions.md, chunk 10):
  * A row gets its kind (FAIL or WARN) when it misses, and also when any N, order or method it lists is missing
    from the CSV (for example after a --quick run): never PASS without data.
  * Rows that list only observed values get these readings:
      ne_column_scaled: at least 10x the qr value and inside [1e-8, 1e-4] for each order ("does not rescue").
      degree sweep: degrees 2-6 within 1e-3 relative (FAIL); degree 8 within 10% (WARN); 213 never below 0.02.
      gmres30_A iters: 59 exactly for P(weakest wins); P(strongest wins) within 2% of 122, 291, 512 and within
        5% of "about 820".
      cg_S_1e-10 iters: in [61, 80] for every N and right-hand side.
      cg_S_1e-10 P(strongest wins): below 1e-3 at N = 40 and above 1e-3 at every N >= 80.
      cg_S_1e-10 E[rounds]: within a factor of 10 of 2.4e-8, 1.3e-2, 0.45 at N = 40, 80, 160.
"""
import argparse
import math
import pathlib
import sys

import numpy as np
import pandas as pd

ORDERS = ["321", "312", "213"]
SPEC_NS = [20, 40, 80, 160, 320]
SOLVE_NS = [40, 80, 160, 320]
SVD_RESID_NORM = dict(zip(ORDERS, [8.8633989e-05, 9.4584299e-05, 1.3297562e-01]))
SVD_MAX_RESID = dict(zip(ORDERS, [5.638098e-06, 6.657670e-06, 3.796276e-02]))
DEG = [2, 4, 6, 8]
DEG_COND = dict(zip(DEG, [2.106e2, 5.708e4, 1.684e7, 5.164e9]))
DEG_RESID = {"321": dict(zip(DEG, [1.814e-2, 4.662e-4, 5.638e-6, 1.368e-7])),
             "213": dict(zip(DEG, [6.430e-2, 5.004e-2, 3.796e-2, 2.661e-2]))}
LAM_MIN = dict(zip(SPEC_NS, [0.0608913, 0.0371848, 0.0312122, 0.0297162, 0.0293420]))
LAM_MAX = dict(zip(SPEC_NS, [1.469880, 1.481731, 1.484717, 1.485465, 1.485652]))
COND2_S = dict(zip(SPEC_NS, [24.1394, 39.8478, 47.5685, 49.9884, 50.6323]))
ROUNDS = dict(zip(SPEC_NS, [36.0536, 106.4723, 276.2373, 654.6066, 1465.9752]))
COND2_A = {20: 35.389, 40: 100.366}
GMRES_STRONG = {40: (122, 0.02), 80: (291, 0.02), 160: (512, 0.02), 320: (820, 0.05)}
CG_ROUNDS = {40: 2.4e-8, 80: 1.3e-2, 160: 0.45}


def status(ok, kind, have=True):
    return "PASS" if (have and ok) else kind


def rel(a, b):
    return a / b - 1


def missing(have, want, what="N"):
    lost = [w for w in want if w not in have]
    return f" (missing {what} = {', '.join(map(str, lost))})" if lost else ""


def run_checks(rg, dg, sc, sv, ov):
    out = []
    reg = {(r.order, r.method): r for r in rg.itertuples()}
    have_reg = all((o, m) in reg for o in ORDERS for m in ("svd", "qr", "normal_equations", "ne_column_scaled"))
    err = lambda o, m: reg[(o, m)].coef_relerr_vs_svd if (o, m) in reg else np.nan

    # Part A ------------------------------------------------------------------------------------------
    c = rg["cond_X"].iloc[0] if len(rg) else np.nan
    out.append(("cond_X (degree 6)", "1.68436e7; 1e-4 relative", f"{c:.6e} ({rel(c, 1.68436e7):+.1e} rel)",
                status(abs(rel(c, 1.68436e7)) <= 1e-4, "FAIL", len(rg) > 0)))
    ratio = rg["cond_XtX"].iloc[0] / c ** 2 if len(rg) else np.nan
    out.append(("cond_XtX / cond_X^2", "1; between 0.5 and 2",
                f"{ratio:.4f} (cond_XtX {rg['cond_XtX'].iloc[0]:.4e})" if len(rg) else "no rows",
                status(0.5 < ratio < 2, "FAIL", len(rg) > 0)))
    out.append(("qr coef_relerr_vs_svd", "below 1e-7 (Linux 7e-14 to 2e-11; Mac 1.9e-13 to 1.6e-10: LAPACK dependent)",
                ", ".join(f"{o}: {err(o, 'qr'):.2e}" for o in ORDERS),
                status(all(err(o, "qr") < 1e-7 for o in ORDERS), "FAIL", have_reg)))
    out.append(("normal_equations coef_relerr_vs_svd", "at least 10x the qr value for each order",
                ", ".join(f"{o}: {err(o, 'normal_equations') / err(o, 'qr'):.3g}x" for o in ORDERS),
                status(all(err(o, "normal_equations") >= 10 * err(o, "qr") for o in ORDERS), "FAIL", have_reg)))
    out.append(("normal_equations coef_relerr_vs_svd",
                "Linux 1.2e-7 (213), 7.9e-7 (312), 3.8e-6 (321); Mac 5.6e-8, 8.9e-7, 5.6e-6; between 1e-8 and 1e-4",
                ", ".join(f"{o}: {err(o, 'normal_equations'):.2e}" for o in ORDERS),
                status(all(1e-8 <= err(o, "normal_equations") <= 1e-4 for o in ORDERS), "WARN", have_reg)))
    out.append(("ne_column_scaled coef_relerr_vs_svd",
                "Linux 4.8e-8 (213), 1.7e-6 (312), 3.8e-6 (321); Mac 2.5e-8, 2.0e-6, 9.6e-6: scaling does not "
                "rescue the normal equations here; at least 10x the qr value and in [1e-8, 1e-4]",
                ", ".join(f"{o}: {err(o, 'ne_column_scaled'):.2e} ({err(o, 'ne_column_scaled') / err(o, 'qr'):.3g}x qr)"
                          for o in ORDERS),
                status(all(1e-8 <= err(o, "ne_column_scaled") <= 1e-4 and err(o, "ne_column_scaled") >= 10 * err(o, "qr")
                           for o in ORDERS), "WARN", have_reg)))
    out.append(("fitted_maxdiff_vs_svd", "below 1e-8 for every method",
                f"largest {rg['fitted_maxdiff_vs_svd'].max():.2e} over {len(rg)} rows" if len(rg) else "no rows",
                status(bool((rg["fitted_maxdiff_vs_svd"] < 1e-8).all()), "FAIL", have_reg)))
    for col, ref, tol, label, fmt in (("resid_norm", SVD_RESID_NORM, 1e-6, "8.8633989e-05, 9.4584299e-05, "
                                       "1.3297562e-01; 1e-6 relative", "{:.8e}"),
                                      ("max_abs_resid", SVD_MAX_RESID, 1e-3, "5.638098e-06, 6.657670e-06, "
                                       "3.796276e-02; 1e-3 relative", "{:.6e}")):
        parts, ok = [], True
        for o in ORDERS:
            if (o, "svd") in reg:
                v = getattr(reg[(o, "svd")], col)
                ok &= abs(rel(v, ref[o])) <= tol
                parts.append(f"{o}: {fmt.format(v)} ({rel(v, ref[o]):+.1e})")
        out.append((f"svd {col} for 321, 312, 213", label, ", ".join(parts) or "no rows",
                    status(ok, "FAIL", len(parts) == 3)))

    # degree sweep
    d = {(r.order, r.degree): r for r in dg.itertuples()}
    parts, ok, have = [], True, True
    for g in DEG:
        rows = [d[(o, g)] for o in ORDERS if (o, g) in d]
        have &= len(rows) == 3
        if rows:
            v = max(rows, key=lambda r: abs(rel(r.cond_X, DEG_COND[g]))).cond_X
            ok &= abs(rel(v, DEG_COND[g])) <= 1e-3
            parts.append(f"{g}: {v:.4e} ({rel(v, DEG_COND[g]):+.1e})")
    out.append(("degree sweep cond_X at degree 2, 4, 6, 8", "2.106e2, 5.708e4, 1.684e7, 5.164e9; 1e-3 relative",
                ", ".join(parts) or "no rows", status(ok, "FAIL", have)))
    for o, extra in (("321", ""), ("213", " (never below 0.02)")):
        parts, hard, soft, have = [], True, True, True
        for g in DEG:
            if (o, g) not in d:
                have = False
                continue
            v = d[(o, g)].max_abs_resid
            e = rel(v, DEG_RESID[o][g])
            if g == 8:
                soft &= abs(e) <= 0.1
            else:
                hard &= abs(e) <= 1e-3
            if o == "213":
                hard &= v >= 0.02
            parts.append(f"{g}: {v:.4e} ({e:+.1e})")
        s = "FAIL" if not (have and hard) else ("WARN" if not soft else "PASS")
        out.append((f"degree sweep max_abs_resid, {o}",
                    ", ".join(f"{DEG_RESID[o][g]:.3e}" for g in DEG) + extra
                    + "; 1e-3 relative (10% at degree 8)", ", ".join(parts) or "no rows", s))

    # Part B: spectrum --------------------------------------------------------------------------------
    s = sc.set_index("N").sort_index()
    full = all(N in s.index for N in SPEC_NS)
    m = missing(s.index, SPEC_NS)

    def per_n(name, expected, col, ref, tol, relative=True, kind="FAIL", fmt="{:.7g}", Ns=SPEC_NS):
        idx = [N for N in Ns if N in s.index]
        dev = {N: (rel(s.loc[N, col], ref[N]) if relative else s.loc[N, col] - ref[N]) for N in idx}
        parts = [f"N={N}: {fmt.format(s.loc[N, col])} ({dev[N]:+.1e})" for N in idx]
        out.append((name, expected, (", ".join(parts) + missing(s.index, Ns)) if parts else "no rows",
                    status(all(abs(v) <= tol for v in dev.values()), kind, all(N in s.index for N in Ns))))

    out.append(("max_abs_A_minus_AT", "1/9 = 0.1111111; 1e-12",
                ", ".join(f"N={N}: {r.max_abs_A_minus_AT:.13f}" for N, r in s.iterrows()) + m,
                status(bool((abs(s["max_abs_A_minus_AT"] - 1 / 9) <= 1e-12).all()), "FAIL", full)))
    out.append(("rel_asym_S", "below 1e-14", ", ".join(f"N={N}: {r.rel_asym_S:.1e}" for N, r in s.iterrows()) + m,
                status(bool((s["rel_asym_S"] < 1e-14).all()), "FAIL", full)))
    per_n("lam_min_S at N = 20, 40, 80, 160, 320", "0.0608913, 0.0371848, 0.0312122, 0.0297162, 0.0293420; "
          "1e-5 relative", "lam_min_S", LAM_MIN, 1e-5)
    per_n("lam_max_S, same N", "1.469880, 1.481731, 1.484717, 1.485465, 1.485652; 1e-5 relative", "lam_max_S",
          LAM_MAX, 1e-5)
    per_n("cond2_S, same N", "24.1394, 39.8478, 47.5685, 49.9884, 50.6323; 1e-4 relative", "cond2_S", COND2_S, 1e-4)
    g = s["gershgorin_lower"]
    out.append(("gershgorin_lower", "0.0292172 at every N, below every lam_min_S; 1e-7",
                f"{g.min():.9f} to {g.max():.9f}; below lam_min_S: "
                f"{'yes' if bool((g < s['lam_min_S']).all()) else 'NO'}" + m,
                status(bool((abs(g - 0.0292172) <= 1e-7).all() and (g < s["lam_min_S"]).all()), "FAIL", full)))
    per_n("log10_pi_range", "(N - 3) log10 2: 5.1175, 11.1381, 23.1793, 47.2617, 95.4265; 1e-9 abs",
          "log10_pi_range", {N: (N - 3) * math.log10(2) for N in SPEC_NS}, 1e-9, relative=False, fmt="{:.10f}")
    per_n("max_expected_rounds", "36.0536, 106.4723, 276.2373, 654.6066, 1465.9752; 1e-4 relative",
          "max_expected_rounds", ROUNDS, 1e-4, fmt="{:.4f}")
    above = all(s.loc[N, "cond2_A_dense"] > s.loc[N, "cond2_S"] for N in COND2_A if N in s.index)
    per_n("cond2_A_dense at N = 20, 40", "35.389, 100.366 (above cond2_S: non-normality); 1e-3 relative",
          "cond2_A_dense", COND2_A, 1e-3, fmt="{:.3f}", Ns=[20, 40])
    if not above:
        out[-1] = (*out[-1][:2], out[-1][2] + "; NOT above cond2_S", "FAIL")

    # Part B: solvers ---------------------------------------------------------------------------------
    v = {(r.N, r.rhs, r.method): r for r in sv.itertuples()}
    Ns = sorted(sv["N"].unique())
    sm = missing(Ns, SOLVE_NS)
    sfull = all(N in Ns for N in SOLVE_NS)

    def sel(method, rhs=None):
        return [r for (N, h, mt), r in sorted(v.items()) if mt == method and (rhs is None or h == rhs)]

    g = sel("gmres30_A")
    out.append(("gmres30_A max_err_rel", "below 1e-8 for every N and right-hand side (observed up to 3e-9)",
                f"largest {max(r.max_err_rel for r in g):.2e} over {len(g)} runs" + sm if g else "no rows",
                status(bool(g) and all(r.max_err_rel < 1e-8 for r in g), "FAIL", sfull)))
    weak = sel("gmres30_A", "weakest_wins")
    strong = {r.N: r for r in sel("gmres30_A", "strongest_wins")}
    ok = all(r.iters == 59 for r in weak) and all(abs(rel(strong[N].iters, GMRES_STRONG[N][0])) <= GMRES_STRONG[N][1]
                                                   for N in strong if N in GMRES_STRONG)
    out.append(("gmres30_A iters", "59 (weakest wins, every N); 122, 291, 512, about 820 (strongest wins, "
                "N = 40 ... 320; Mac 819); within 2% (5% for the N = 320 value)",
                "weakest " + ", ".join(f"N={r.N}: {r.iters}" for r in weak) + "; strongest "
                + ", ".join(f"N={N}: {r.iters}" for N, r in strong.items()) + sm,
                status(ok, "WARN", sfull)))
    c10 = sel("cg_S_1e-10")
    it = [r.iters for r in c10]
    out.append(("cg_S_1e-10 iters", "61 to 80 at every N",
                f"{min(it)} to {max(it)} over {len(it)} runs (" + ", ".join(
                    f"N={N}: {min(r.iters for r in c10 if r.N == N)}-{max(r.iters for r in c10 if r.N == N)}"
                    for N in Ns) + ")" + sm if it else "no rows",
                status(bool(it) and min(it) >= 61 and max(it) <= 80, "WARN", sfull)))
    cs = {r.N: r for r in sel("cg_S_1e-10", "strongest_wins")}
    ok = all((cs[N].max_err_rel < 1e-3) if N == 40 else (cs[N].max_err_rel > 1e-3) for N in cs)
    out.append(("cg_S_1e-10 max_err_rel, P(strongest wins)",
                "7.3e-7 at N = 40; above 1e-3 at N >= 80 (0.33 at 80, about 1 at 160 and 320)",
                ", ".join(f"N={N}: {r.max_err_rel:.2e}" for N, r in cs.items()) + sm, status(ok, "FAIL", sfull)))
    cr = {r.N: r for r in sel("cg_S_1e-10", "rounds")}
    ok = all(abs(math.log10(cr[N].max_err_rel / ref)) <= 1 for N, ref in CG_ROUNDS.items() if N in cr)
    out.append(("cg_S_1e-10 max_err_rel, E[rounds]", "2.4e-8 at N = 40, 1.3e-2 at 80, 0.45 at 160 "
                "(Mac 0.75 at 320); each within a factor 10", ", ".join(f"N={N}: {r.max_err_rel:.2e}" for N, r in cr.items()) + sm,
                status(ok, "WARN", all(N in cr for N in CG_ROUNDS))))
    cw = sel("cg_S_1e-10", "weakest_wins")
    out.append(("cg_S_1e-10 max_err_rel, P(weakest wins)",
                "below 1e-11 (b sits where pi is small, so the residual sees it)",
                ", ".join(f"N={r.N}: {r.max_err_rel:.2e}" for r in cw) + sm,
                status(bool(cw) and all(r.max_err_rel < 1e-11 for r in cw), "WARN", sfull)))
    sp_ = sel("splu_S")
    out.append(("splu_S max_err_rel", "below 1e-12",
                f"largest {max(r.max_err_rel for r in sp_):.2e} over {len(sp_)} runs" + sm if sp_ else "no rows",
                status(bool(sp_) and all(r.max_err_rel < 1e-12 for r in sp_), "FAIL", sfull)))

    # overflow ----------------------------------------------------------------------------------------
    q = dict(zip(ov["quantity"], ov["value"]))
    a, b = q.get("first_N_naive_pi_overflows"), q.get("first_N_naive_sqrt_pi_overflows")
    out.append(("overflow: first N where naive pi, naive sqrt(pi) overflow", "1026, 2050; exact",
                f"{a:g}, {b:g}" if a is not None and b is not None else "no rows",
                status(a == 1026 and b == 2050, "FAIL", a is not None and b is not None)))
    keys = ("naive_S_nonfinite_entries", "logdomain_S_nonfinite_entries", "logdomain_S_rel_asym")
    have = all(k in q for k in keys)
    out.append(("N = 1030 build", "naive S has non-finite entries; log-domain S all finite, symmetric to 1e-13",
                f"naive S {q[keys[0]]:g} non-finite of {q.get('nnz_A', np.nan):g}; log-domain S {q[keys[1]]:g} "
                f"non-finite, rel asym {q[keys[2]]:.1e}" if have else "no rows",
                status(have and q[keys[0]] > 0 and q[keys[1]] == 0 and q[keys[2]] <= 1e-13, "FAIL", have)))
    return out


def red_flags(rg, sc, sv):
    out = []
    qr = rg[rg["method"] == "qr"]["coef_relerr_vs_svd"]
    out.append(("QR and SVD coefficients differ by more than 1e-7", f"largest {qr.max():.2e}",
                len(qr) > 0 and bool((qr <= 1e-7).all())))
    ne = rg[rg["method"] == "normal_equations"].set_index("order")["coef_relerr_vs_svd"]
    q = rg[rg["method"] == "qr"].set_index("order")["coef_relerr_vs_svd"]
    gap = (ne - q).abs()
    out.append(("normal equations match QR to 1e-12 (X^T X not formed?)", f"smallest |NE - QR| {gap.min():.2e}",
                len(gap) > 0 and bool((gap > 1e-12).all())))
    out.append(("S not symmetric", f"largest rel_asym_S {sc['rel_asym_S'].max():.1e}",
                bool((sc["rel_asym_S"] < 1e-14).all())))
    r = sv[(sv["method"] == "cg_S_1e-10") & (sv["rhs"] == "strongest_wins") & (sv["N"] == 160)]
    out.append(("CG on S accurate at N = 160 (P(strongest wins))",
                f"max_err_rel {r['max_err_rel'].iloc[0]:.2e}" if len(r) else "no N = 160 row",
                len(r) > 0 and bool(r["max_err_rel"].iloc[0] > 1e-3)))
    return out


def fmt(x):
    if isinstance(x, str):
        return x
    if isinstance(x, (bool, np.bool_)):
        return str(bool(x))
    if isinstance(x, (int, np.integer)):
        return str(x)
    if isinstance(x, float) and np.isnan(x):
        return ""
    if isinstance(x, float) and x.is_integer() and abs(x) < 1e6:
        return str(int(x))
    return f"{x:.10g}"


def table(df, first, last):
    data = df.loc[:, first:last]
    lines = ["| " + " | ".join(data.columns) + " |", "|" + "---|" * len(data.columns)]
    return lines + ["| " + " | ".join(fmt(x) for x in row) + " |" for row in data.itertuples(index=False)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    args = parser.parse_args()
    results = pathlib.Path(args.results)
    read = lambda name: pd.read_csv(results / f"{name}.csv", dtype={"order": str})
    rg, dg, sc, sv, ov = (read(n) for n in ("e10_regression", "e10_degree_sweep", "e10_bt_spectrum",
                                            "e10_bt_solvers", "e10_bt_overflow"))
    checks = run_checks(rg, dg, sc, sv, ov)
    flags = red_flags(rg, sc, sv)

    sources = [("e10_regression", rg), ("e10_degree_sweep", dg), ("e10_bt_spectrum", sc), ("e10_bt_solvers", sv),
               ("e10_bt_overflow", ov)]
    src = ", ".join(f"`{results / (name + '.csv')}` (git {df.iloc[0]['git_hash']}, {df.iloc[0]['timestamp']})"
                    for name, df in sources)
    m = sc.iloc[0]
    lines = [
        "# Chunk 10 report: least squares by QR, and unequal skill (Bradley-Terry)",
        "",
        f"Sources: {src}; {m['platform']}, Python {m['python']}, numpy {m['numpy']}, scipy {m['scipy']}, "
        f"OMP_NUM_THREADS={m['omp_num_threads']}.",
        "",
        "| Check | Expected | Observed | Status |",
        "|---|---|---|---|",
    ]
    lines += [f"| {c} | {e} | {o} | {s} |" for c, e, o, s in checks]
    counts = {s: sum(row[3] == s for row in checks) for s in ("PASS", "WARN", "FAIL")}
    lines += ["", f"Summary: {counts['PASS']} PASS, {counts['WARN']} WARN, {counts['FAIL']} FAIL.", "",
              "## Red flags (automatic checks of the spec's list)", "",
              "| Red flag check | Observed | OK |", "|---|---|---|"]
    lines += [f"| {c} | {o} | {'yes' if ok else 'NO'} |" for c, o, ok in flags]
    lines += ["", "Not checked automatically: Diaconis and Ethier's exact regression design (degree, state set, "
              "targets) has not been compared with their paper, so nothing here is a claim about their published "
              "coefficients.", ""]
    lines += ["## Data (e10_regression, N = 300, sextic, 7500 states)", ""] + table(rg, "order", "seconds")
    lines += ["", "## Data (e10_degree_sweep, SVD fits)", ""] + table(dg, "order", "max_abs_resid")
    lines += ["", "## Data (e10_bt_spectrum, skills (1, 1.5, 2))", ""] + table(sc, "N", "cond2_A_dense")
    lines += ["", "## Data (e10_bt_solvers; errors relative to max |u|, reference splu on A)", ""]
    lines += table(sv, "N", "seconds")
    lines += ["", "## Data (e10_bt_overflow)", ""] + table(ov, "N", "value")
    lines += ["", "Figures: `figures/f10_regression.png` (from e10_regression.csv and e10_degree_sweep.csv), "
              "`figures/f10_bt_errors.png` (from e10_bt_states_N80.csv).", ""]

    for c, _, o, s in checks:
        print(f"{s:4s}  {c}: {o}")
    for c, o, ok in flags:
        print(f"{'ok' if ok else 'FLAG':4s}  {c}: {o}")
    report = results / "c10_report.md"
    report.write_text("\n".join(lines))
    print(f"Summary: {counts['PASS']} PASS, {counts['WARN']} WARN, {counts['FAIL']} FAIL.")
    print(f"wrote {report}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
