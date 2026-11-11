"""Chunk 7 check: compare results/e07_fixes.csv, e07_structured.csv and (if chunk 6 exists) e07_fft_check.csv with
the "Expected results" table of plan/c07_fixes.md. Prints one PASS/WARN/FAIL line per table row (plus automatic
red-flag checks) and writes results/c07_report.md.
    python checks/check_c07.py [--results DIR]

Conventions (logged in notes/decisions.md, chunk 7):
  * Each row gets the kind the spec lists (FAIL or WARN) when it misses, and also when the rows it needs are
    missing: never PASS without data. A row with kind "WARN/FAIL" is WARN above the first limit, FAIL above the second.
  * Several rows quote values at N = 400, which is not in e07_fixes' N list (20, 40, 60, 80, 160, 320, 640, 1280).
    Their rules (gth below N u; direct / N^2 in [0.02, 0.2]; gth below direct at every N >= 80) are applied at the
    N that exist, and the N = 400 values are reported as not measured.
  * "cg rtol 1e-10 ... as in chunk 4": chunk 4's tolerance for N = 640 was [3e-6, 6e-5] around 1.4e-5, i.e. a factor
    1/4.67 to 4.29. The same factor band is applied around the listed values at N = 60 and 160.
  * The cg_componentwise rows use every kind (none, mic0, amg); the iteration ratio and "converged" rows use tol 1e-14
    (the tolerance the spec's story quotes) at every N.
  * direct err_vs_stored_tiny: |value| < 0.2 N^2 u at every N.
  * ir_direct seconds minus direct seconds is compared with the direct row's setup_seconds (the factor time).
  * e07_fft_check "which solver is off": PASS if at every N the FFT's rel_err_smallest is larger than splu's and
    splu's is within 0.1 N^2 u of ir_direct; "FFT at N = 800": PASS inside chunk 6's 6e-7 to 2e-6.
"""
import argparse
import pathlib
import sys

import numpy as np
import pandas as pd

U = 2.0 ** -53
DATA_TERM_REF = {80: -6.895e-14, 160: -2.7592e-13, 320: -1.1038e-12, 640: -4.4153e-12, 1280: -1.7661e-11}
GTH_REF = {20: 8, 40: 12, 60: 25, 80: 34, 160: 46, 400: 120}
DIRECT_REF = {20: 39, 60: 267, 80: 431, 400: 8018}
STORED_REF = {80: -1.1e-14, 160: 1.5e-13, 320: 5.9e-13, 640: 2.3e-12, 1280: 8.5e-12}
CG_REF = {60: 5e-8, 160: 6.8e-7, 640: 1.4e-5}
CG_BAND = (3e-6 / 1.4e-5, 6e-5 / 1.4e-5)  # chunk 4's tolerance at N = 640, as a factor
IT_RATIO_REF = {"none": "1.3-1.5", "mic0": "1.5-1.8", "amg": "1.4-2.2"}
PUSH_REF = {10: 3.9, 20: 4.3, 40: 4.5, 80: 4.6}
KINDS = ["none", "mic0", "amg"]


def status(ok, kind, have=True):
    return "PASS" if (have and ok) else kind


def truthy(col):
    return col.astype(str) == "True"


def rows(df, method, kind=None, param=None, N=None):
    d = df[df["method"] == method]
    if kind is not None:
        d = d[d["kind"] == kind]
    if param is not None:
        d = d[np.isclose(d["param"], param, rtol=1e-9, atol=0)]
    if N is not None:
        d = d[d["N"] == N]
    return d.sort_values("N")


def ir_methods(df):
    return [m for m in ("ir_direct", "ir_cg_mic0", "ir_cg_amg") if m in set(df["method"])]


def run_checks(fx, st, fft):
    out = []

    # 1. ir_* vs exact
    d = fx[fx["method"].isin(ir_methods(fx)) & (fx["reference"] == "exact")]
    out.append(("ir_direct, ir_cg_mic0, ir_cg_amg vs exact (N <= 80): max_rel_err",
                "0 (correctly rounded); at most 2 u",
                (f"{len(d)} rows, max_rel_err {d['max_rel_err_in_u'].max():.2g} u; "
                 + ", ".join(f"N={r.N} {r.method}: {r.max_rel_err_in_u:.2g} u" for r in d.itertuples()))
                if len(d) else "no rows",
                status(len(d) > 0 and (d["max_rel_err"] <= 2 * U).all(), "FAIL", len(d) > 0)))

    # 2. ir_* agree with each other at N >= 160 (the reference there is ir_direct itself)
    d = fx[fx["method"].isin(["ir_cg_mic0", "ir_cg_amg"]) & (fx["N"] >= 160)]
    out.append(("ir_* agree with each other, N >= 160 (ir_cg_* vs ir_direct, the reference)",
                "identical or 1 ulp; at most 4 u",
                (", ".join(f"N={r.N} {r.method}: {r.max_rel_err_in_u:.2g} u" for r in d.itertuples())) if len(d)
                else "no rows (N >= 160 not run)",
                status(len(d) > 0 and (d["max_rel_err"] <= 4 * U).all(), "FAIL", len(d) > 0)))

    # 3-4. steps
    d = rows(fx, "ir_direct")
    out.append(("ir_direct steps", "2; at most 3",
                ", ".join(f"N={r.N}: {r.iterations_or_steps:g}" for r in d.itertuples()) if len(d) else "no rows",
                status(len(d) > 0 and (d["iterations_or_steps"] <= 3).all(), "WARN", len(d) > 0)))
    d = fx[fx["method"].isin(["ir_cg_mic0", "ir_cg_amg"])].sort_values(["method", "N"])
    out.append(("ir_cg_mic0 and ir_cg_amg steps", "4; at most 8",
                "; ".join(f"{m}: " + ", ".join(f"N={r.N}: {r.iterations_or_steps:g}" for r in g.itertuples())
                          for m, g in d.groupby("method")) if len(d) else "no rows",
                status(len(d) > 0 and (d["iterations_or_steps"] <= 8).all(), "WARN", len(d) > 0)))

    # 5. gth max_rel_err_in_u
    d = rows(fx, "gth")
    over_n = d[d["max_rel_err_in_u"] >= d["N"]]
    over_10n = d[d["max_rel_err_in_u"] > 10 * d["N"]]
    kind = "FAIL" if len(over_10n) else "WARN"
    missing = [N for N in GTH_REF if N not in set(d["N"])]
    out.append(("gth max_rel_err_in_u",
                "8 (20), 12 (40), 25 (60), 34 (80), 46 (160), 120 (400); below N; above 10 N is FAIL",
                (", ".join(f"N={r.N}: {r.max_rel_err_in_u:.1f} u ({r.max_rel_err_in_u / r.N:.2f} N)" for r in d.itertuples())
                 + (f"; not measured: N = {', '.join(map(str, missing))}" if missing else "")) if len(d) else "no rows",
                status(len(d) > 0 and over_n.empty, kind, len(d) > 0)))

    # 6. direct max_rel_err_in_u / N^2
    d = rows(fx, "direct")
    ratio = d["max_rel_err_in_u"] / d["N"] ** 2
    missing = [N for N in DIRECT_REF if N not in set(d["N"])]
    out.append(("direct max_rel_err_in_u / N^2 (against the true probability)",
                "about 0.07 (39 u at 20, 267 u at 60, 431 u at 80, 8018 u at 400); in [0.02, 0.2]",
                (", ".join(f"N={r.N}: {r.max_rel_err_in_u:.0f} u ({q:.3f})" for r, q in zip(d.itertuples(), ratio))
                 + (f"; not measured: N = {', '.join(map(str, missing))}" if missing else "")) if len(d) else "no rows",
                status(len(d) > 0 and ((ratio >= 0.02) & (ratio <= 0.2)).all(), "WARN", len(d) > 0)))

    # 7. direct err_vs_stored_tiny
    lim = 0.2 * d["N"] ** 2 * U
    out.append(("direct err_vs_stored_tiny (the solver's own error)",
                "-1.1e-14 (80), +1.5e-13 (160), +5.9e-13 (320), +2.3e-12 (640), +8.5e-12 (1280): about +0.05 N^2 u, "
                "opposite in sign to the data term; absolute value below 0.2 N^2 u",
                ", ".join(f"N={r.N}: {r.err_vs_stored_tiny:+.2g} ({r.err_vs_stored_tiny / (r.N ** 2 * U):+.3f} N^2 u, "
                          f"{'opposite' if r.err_vs_stored_tiny * r.data_term_tiny < 0 else 'same'} sign)"
                          for r in d.itertuples()) if len(d) else "no rows",
                status(len(d) > 0 and (d["err_vs_stored_tiny"].abs() < lim).all(), "WARN", len(d) > 0)))

    # 8. data_term_tiny
    devs = {N: float(d.loc[d["N"] == N, "data_term_tiny"].iloc[0]) / ref - 1
            for N, ref in DATA_TERM_REF.items() if N in set(d["N"])}
    out.append(("data_term_tiny",
                "-6.895e-14 (80), -2.7592e-13 (160), -1.1038e-12 (320), -4.4153e-12 (640), -1.7661e-11 (1280); "
                "1e-3 relative",
                ", ".join(f"N={N}: {DATA_TERM_REF[N] * (1 + v):.5g} ({v:+.1e})" for N, v in devs.items()) if devs
                else "no rows",
                status(bool(devs) and all(abs(v) <= 1e-3 for v in devs.values()), "FAIL", bool(devs))))

    # 9. gth beats direct
    g = rows(fx, "gth").set_index("N")["max_rel_err"]
    dr = d.set_index("N")["max_rel_err"]
    common = [N for N in g.index if N >= 80 and N in dr.index]
    out.append(("gth beats direct (true probability, max_rel_err), N >= 80",
                "by a factor growing with N: 13 at N = 80, 67 at N = 400; gth smaller at every N >= 80",
                ", ".join(f"N={N}: factor {dr[N] / g[N]:.1f}" for N in common) + " (N = 400 not measured)"
                if common else "no rows",
                status(bool(common) and all(g[N] < dr[N] for N in common), "WARN", bool(common))))

    # 10. cg rtol 1e-10 none
    d = rows(fx, "cg", "none", 1e-10)
    vals = {N: float(d.loc[d["N"] == N, "rel_err_tiny"].iloc[0]) for N in CG_REF if N in set(d["N"])}
    ok = all(CG_BAND[0] * CG_REF[N] <= v <= CG_BAND[1] * CG_REF[N] for N, v in vals.items())
    out.append(("cg rtol 1e-10, kind none: rel_err_tiny",
                "5e-8 (60), 6.8e-7 (160), 1.4e-5 (640); as in chunk 4 ([3e-6, 6e-5] at 640, the same factor band "
                "at 60 and 160)",
                ", ".join(f"N={N}: {v:.2g} ({v / CG_REF[N]:.2f}x)" for N, v in vals.items()) if vals else "no rows",
                status(bool(vals) and ok, "WARN", bool(vals))))

    # 11. cg_componentwise 1e-14 rel_err_tiny below cond_tiny * tol
    d = rows(fx, "cg_componentwise", param=1e-14)
    bound = d["cond_tiny"] * 1e-14
    worst = (d["rel_err_tiny"] / bound).max() if len(d) else np.nan
    out.append(("cg_componentwise tol 1e-14: rel_err_tiny (true probability)",
                "4e-14 to 6e-14 (60), 3e-13 (160), 5e-12 (640): at N >= 160 this is the data term; below cond_tiny * tol",
                ("; ".join(f"{k}: " + ", ".join(f"N={r.N}: {r.rel_err_tiny:.2g}" for r in g.itertuples())
                           for k, g in d.groupby("kind", sort=False)) + f"; worst rel_err / (cond_tiny tol) {worst:.2g}")
                if len(d) else "no rows",
                status(len(d) > 0 and (d["rel_err_tiny"] < bound).all(), "FAIL", len(d) > 0)))

    # 12. cg_componentwise 1e-14 err_vs_stored vs direct, N >= 160
    d160 = d[d["N"] >= 160]
    dirs = rows(fx, "direct").set_index("N")["err_vs_stored_tiny"].abs()
    cmp = [(r.kind, r.N, abs(r.err_vs_stored_tiny), dirs.get(r.N, np.nan)) for r in d160.itertuples()]
    out.append(("cg_componentwise tol 1e-14: err_vs_stored_tiny, N >= 160",
                "3e-14 (160), 1e-13 (320), about 5e-13 (640); below the direct solver's err_vs_stored_tiny at the same N",
                "; ".join(f"N={N} {k}: {e:.2g} vs direct {de:.2g}" for k, N, e, de in cmp) if cmp else "no rows",
                status(bool(cmp) and all(e < de for _, _, e, de in cmp), "WARN", bool(cmp))))

    # 13. iteration ratio
    parts, ok, have = [], True, False
    for k in KINDS:
        a = rows(fx, "cg_componentwise", k, 1e-14).set_index("N")["iterations_or_steps"]
        b = rows(fx, "cg", k, 1e-10).set_index("N")["iterations_or_steps"]
        Ns = [N for N in a.index if N in b.index]
        if not Ns:
            continue
        have = True
        q = {N: a[N] / b[N] for N in Ns}
        ok &= all(1.1 <= v <= 2.5 for v in q.values())
        parts.append(f"{k} (spec {IT_RATIO_REF[k]}): " + ", ".join(f"N={N}: {v:.2f}" for N, v in q.items()))
    out.append(("cg_componentwise iterations / cg rtol 1e-10 iterations (tol 1e-14)",
                "none 1.3-1.5, mic0 1.5-1.8, amg 1.4-2.2; in [1.1, 2.5]",
                "; ".join(parts) if parts else "no rows", status(have and ok, "WARN", have)))

    # 14. converged
    nc = d[~truthy(d["converged"])]
    out.append(("cg_componentwise tol 1e-14 converged, every N up to 1280", "yes",
                f"{len(d) - len(nc)}/{len(d)} rows converged (N up to {d['N'].max() if len(d) else '-'})"
                + (f"; not: {', '.join(f'N={r.N} {r.kind} (omega {r.omega / U:.0f} u)' for r in nc.itertuples())}"
                   if len(nc) else ""),
                status(len(d) > 0 and nc.empty and d["N"].max() >= 1280, "WARN", len(d) > 0)))

    # 15. ir_direct overhead at N = 640
    a, b = rows(fx, "ir_direct", N=640), rows(fx, "direct", N=640)
    have = len(a) > 0 and len(b) > 0
    if have:
        extra, factor = float(a["seconds"].iloc[0] - b["seconds"].iloc[0]), float(b["setup_seconds"].iloc[0])
        obs = f"ir_direct - direct = {extra:.3f} s, factor {factor:.2f} s ({extra / factor:.0%})"
    out.append(("ir_direct seconds minus direct seconds at N = 640", "about 0.1 s (factor 2.2 s); under 50% of the "
                "factor time", obs if have else "no rows", status(have and extra < 0.5 * factor, "WARN", have)))

    # 16-17. fft check
    if fft is None:
        msg = "no e07_fft_check.csv (chunk 6's gr.fft_solver is not built yet)"
        out.append(("e07_fft_check: which solver is off at (N-2, 1, 1)", "the FFT (normwise accurate only); splu "
                    "within about 0.1 N^2 u of ir_direct, and near data_term_smallest", msg, "WARN"))
        out.append(("e07_fft_check: FFT rel_err_smallest at N = 800", "about 1e-6 (chunk 6's disagreement)", msg, "WARN"))
    else:
        f = fft[fft["reference"] == "refined"]
        Ns = sorted(f["N"].unique())
        parts, ok = [], bool(Ns)
        for N in Ns:
            ff = f[(f["N"] == N) & (f["method"] == "fft")]
            sl = f[(f["N"] == N) & (f["method"] == "splu")]
            if not len(ff) or not len(sl):
                ok = False
                continue
            fe, se = float(ff["rel_err_smallest"].iloc[0]), float(sl["rel_err_smallest"].iloc[0])
            ok &= fe > se and se <= 0.1 * N ** 2 * U
            parts.append(f"N={N}: fft {fe:.2g}, splu {se:.2g} ({se / (N ** 2 * U):.3f} N^2 u; signed "
                         f"{float(sl['signed_err_smallest'].iloc[0]):+.2g} vs data term "
                         f"{float(sl['data_term_smallest'].iloc[0]):+.2g})")
        out.append(("e07_fft_check: which solver is off at (N-2, 1, 1)", "the FFT (normwise accurate only); splu "
                    "within about 0.1 N^2 u of ir_direct, and near data_term_smallest",
                    "; ".join(parts) if parts else "no rows", status(ok, "WARN", bool(parts))))
        ff = f[(f["N"] == 800) & (f["method"] == "fft")]
        v = float(ff["rel_err_smallest"].iloc[0]) if len(ff) else np.nan
        out.append(("e07_fft_check: FFT rel_err_smallest at N = 800", "about 1e-6 (chunk 6's disagreement, "
                    "6e-7 to 2e-6)", f"{v:.2g}" if len(ff) else "no row at N = 800",
                    status(len(ff) > 0 and 6e-7 <= v <= 2e-6, "WARN", len(ff) > 0)))

    # 18-20. structured
    out.append(("structured_random_max", "1.5-2.4 at every N; below 10",
                ", ".join(f"N={r.N}: {r.structured_random_max:.2f}" for r in st.itertuples()) if len(st) else "no rows",
                status(len(st) > 0 and (st["structured_random_max"] < 10).all(), "FAIL", len(st) > 0)))
    out.append(("structured_push", "3.9, 4.3, 4.5, 4.6 (N = 10 ... 80); below 10",
                ", ".join(f"N={r.N}: {r.structured_push:.2f}" + (f" ({PUSH_REF[r.N]})" if r.N in PUSH_REF else "")
                          for r in st.itertuples()) if len(st) else "no rows",
                status(len(st) > 0 and (st["structured_push"] < 10).all(), "WARN", len(st) > 0)))
    q = (st["cond_max"] / st["structured_push"]).to_numpy()
    out.append(("cond_max / structured_push", "grows like N^2 (37/3.9 at N = 10, 2484/4.6 at N = 80); increasing",
                ", ".join(f"N={r.N}: {r.cond_max:.0f}/{r.structured_push:.2f} = {v:.1f}" for r, v in zip(st.itertuples(), q))
                if len(st) else "no rows",
                status(len(q) > 1 and bool((np.diff(q) > 0).all()), "FAIL", len(q) > 1)))
    return out


def slope(x, y):
    return float(np.polyfit(np.log(x), np.log(y), 1)[0]) if len(x) > 1 else np.nan


def red_flags(fx, st):
    out = []
    d = fx[fx["method"].isin(ir_methods(fx)) & (fx["reference"] == "exact") & truthy(fx["converged"])]
    bad = d[d["max_rel_err"] > 2 * U]
    out.append(("refinement converged but not to the exact answer (N <= 80)",
                f"{len(bad)} of {len(d)} converged ir rows above 2 u", len(d) > 0 and bad.empty))
    g = rows(fx, "gth")
    g40 = g[g["N"] >= 40]
    s = slope(g40["N"], g40["max_rel_err_in_u"])
    out.append(("GTH error growing like N^2 (log-log slope of max_rel_err_in_u, N >= 40)",
                f"slope {s:.2f} (ordinary elimination grows like N^2: slope 2)", bool(s < 1.5)))
    c = rows(fx, "cg_componentwise", param=1e-14)
    nc = c[~truthy(c["converged"])]
    out.append(("cg_componentwise never reaching tol 1e-14",
                "all converged" if nc.empty else
                "; ".join(f"N={r.N} {r.kind}: final omega {r.omega:.2e}" for r in nc.itertuples()), nc.empty))
    gr = g[g["N"] >= 160]
    out.append(("refinement landing on the stored solution (N >= 160): GTH, which does not use refinement, must sit "
                "far closer to the refined reference than the data term",
                ", ".join(f"N={r.N}: gth rel_err_tiny {r.rel_err_tiny:.2g} vs |data term| {abs(r.data_term_tiny):.2g}"
                          for r in gr.itertuples()) if len(gr) else "no gth rows at N >= 160",
                len(gr) > 0 and bool((gr["rel_err_tiny"] < 0.1 * gr["data_term_tiny"].abs()).all())))
    sr, sp_ = slope(st["N"], st["structured_random_max"]), slope(st["N"], st["structured_push"])
    out.append(("a structured ratio growing with N (log-log slope; cond_max's is about 2)",
                f"random max slope {sr:.2f}, push slope {sp_:.2f}, cond_max slope {slope(st['N'], st['cond_max']):.2f}",
                bool(sr < 0.3 and sp_ < 0.3)))
    cg = fx[fx["method"].isin(["cg", "cg_componentwise"])]
    nc = cg[~truthy(cg["converged"])]
    out.append(("extra: every CG row converged within maxiter", f"{len(cg) - len(nc)}/{len(cg)} rows", nc.empty))
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
    return f"{x:.4g}"


def table(df, first, last):
    data = df.loc[:, first:last]
    lines = ["| " + " | ".join(data.columns) + " |", "|" + "---|" * len(data.columns)]
    return lines + ["| " + " | ".join(fmt(x) for x in row) + " |" for row in data.itertuples(index=False)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    args = parser.parse_args()
    results = pathlib.Path(args.results)
    fx = pd.read_csv(results / "e07_fixes.csv")
    st = pd.read_csv(results / "e07_structured.csv")
    fft_path = results / "e07_fft_check.csv"
    fft = pd.read_csv(fft_path) if fft_path.exists() else None
    checks = run_checks(fx, st, fft)
    flags = red_flags(fx, st)

    sources = [("e07_fixes", fx), ("e07_structured", st)] + ([("e07_fft_check", fft)] if fft is not None else [])
    src = ", ".join(f"`{results / (name + '.csv')}` (git {df.iloc[0]['git_hash']}, {df.iloc[0]['timestamp']})"
                    for name, df in sources)
    m = fx.iloc[0]
    lines = [
        "# Chunk 7 report: three fixes for the tiny probabilities",
        "",
        f"Sources: {src}; {m['platform']}, Python {m['python']}, numpy {m['numpy']}, scipy {m['scipy']}, "
        f"OMP_NUM_THREADS={m['omp_num_threads']}."
        + ("" if fft is not None else " `e07_fft_check.csv` is absent: chunk 6 (gr.fft_solver) is not built yet."),
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
    lines += ["", "## Data (e07_fixes)", ""] + table(fx, "N", "signed_err_tiny")
    lines += ["", "## Data (e07_structured)", ""] + table(st, "N", "draws")
    if fft is not None:
        lines += ["", "## Data (e07_fft_check)", ""] + table(fft, "N", "signed_err_smallest")
    lines.append("")

    for c, _, o, s in checks:
        print(f"{s:4s}  {c}: {o}")
    for c, o, ok in flags:
        print(f"{'ok' if ok else 'FLAG':4s}  {c}: {o}")
    report = results / "c07_report.md"
    report.write_text("\n".join(lines))
    print(f"wrote {report}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
