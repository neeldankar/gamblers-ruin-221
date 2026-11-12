"""Chunk 9 check: compare results/e09_identities.csv, e09_solvers.csv, e09_big_stack.csv and e09_alpha.csv with the
"Expected results" table of plan/c09_four_players.md. Prints one PASS/WARN/FAIL line per table row (plus automatic
red-flag checks) and writes results/c09_report.md.
    python checks/check_c09.py [--results DIR]

Conventions (logged in notes/decisions.md, chunk 9):
  * Each row gets the kind the spec lists (FAIL or WARN) when it misses, and also when any N it lists is missing.
  * e09_solvers: a run whose status starts with "skipped" or "killed" was stopped by the memory rules; it is listed
    but does not count as missing data. Every other planned (method, N) must have status "ok ...".
  * amg_cg iters "growing slowly": every N in 40..150 in [9, 14] and iters(150) >= iters(40).
  * Time slopes are least-squares slopes of log time against log n: amg_cg over all its sizes, cholmod over
    N = 60, 80, 100 (the same sizes as the nnz row).
  * "splu several times larger": peak_rss_mb(splu) >= 3 x peak_rss_mb(cholmod) at N = 60.
  * "ratio tends to 1/6": the three exact fractions, and |n_lumped / n_full - 1/6| decreasing in N.
"""
import argparse
import math
import pathlib
import sys

import numpy as np
import pandas as pd

ID_N = [10, 20, 30, 40, 60]
ID_COUNTS = dict(zip(ID_N, [84, 969, 3654, 9139, 32509]))
T_E4N = {20: (0.849036, 1.891425), 30: (0.567040, 1.787799), 40: (0.425240, 1.739744), 60: (0.283582, 1.694066)}
T_E2 = {20: (0.851141, 1.061295), 30: (0.834306, 1.061624), 40: (0.826378, 1.063099), 60: (0.818799, 1.063431)}
T_MAX = {20: 26.5324, 40: 106.3099, 60: 239.2719}
DIRECT_N, AMG_N = [20, 40, 60, 80, 100], [20, 40, 60, 80, 100, 120, 150, 200]
METHOD_N = {"splu": DIRECT_N, "splu_mmd": DIRECT_N, "cholmod": DIRECT_N, "amg_cg": AMG_N}
CHOLMOD_NNZ = {60: 8.0e6, 80: 2.76e7, 100: 7.45e7}
P_SMALL = dict(zip([8, 10, 12, 16, 20, 24, 30, 40, 50],
                   [5.577821161394e-03, 1.571739438951e-03, 5.568973643914e-04, 1.080249783339e-04,
                    3.022376155052e-05, 1.066742330410e-05, 2.980150693207e-06, 5.753800975152e-07,
                    1.606108031016e-07]))
P_LARGE = dict(zip([60, 80, 100, 120, 160, 200],
                   [5.661341422530e-08, 1.092193169790e-08, 3.047622700924e-09, 1.074036901898e-09,
                    2.071632598328e-10, 5.780085237687e-11]))
SLOPES4 = {(8, 10): 5.6762, (20, 24): 5.7121, (30, 40): 5.7171, (60, 80): 5.7198, (80, 100): 5.7201,
           (120, 160): 5.7205, (160, 200): 5.7206}
LUMP = {12: (41, 165), 20: (204, 969), 100: (27353, 156849)}


def status(ok, kind, have=True):
    return "PASS" if (have and ok) else kind


def missing(have, want):
    lost = [str(x) for x in want if x not in have]
    return f" (missing N = {', '.join(lost)})" if lost else ""


def slope(x, y):
    return float(np.polyfit(np.log(x), np.log(y), 1)[0]) if len(x) > 1 else float("nan")


def identity_checks(idt):
    out = []
    d = idt.set_index("N").sort_index()
    have = set(d.index)
    full = all(N in have for N in ID_N)
    obs = ", ".join(f"N={N}: {int(d.loc[N, 'n'])}" for N in d.index) + missing(have, ID_N)
    out.append(("e09_identities n", "C(N-1, 3): 84, 969, 3654, 9139, 32509; exact", obs,
                status(all(d.loc[N, "n"] == ID_COUNTS.get(N, -1) for N in d.index), "FAIL", full)))
    ok = bool((d["max_nnz_row"] == 13).all() and (d["max_abs_A_minus_AT"] == 0).all())
    out.append(("max_nnz_row; max_abs_A_minus_AT", "13; 0; exact",
                ", ".join(f"N={N}: {int(r.max_nnz_row)}; {r.max_abs_A_minus_AT:g}" for N, r in d.iterrows())
                + missing(have, ID_N), status(ok, "FAIL", full)))
    cols = ["e2_identity_relerr", "win_maxerr", "out_first_sum_maxerr"]
    ok = bool((d[cols] < 1e-12).all().all())
    out.append(("e2_identity_relerr, win_maxerr, out_first_sum_maxerr", "below 1e-12",
                ", ".join(f"N={N}: " + "/".join(f"{r[c]:.1e}" for c in cols) for N, r in d.iterrows())
                + missing(have, ID_N), status(ok, "FAIL", full)))
    out.append(("bounds_hold", "True at every N",
                ", ".join(f"N={N}: {r.bounds_hold}" for N, r in d.iterrows()) + missing(have, ID_N),
                status(bool((d["bounds_hold"].astype(str) == "True").all()), "FAIL", full)))
    for cmin, cmax, ref, text in (("T_over_e4N_min", "T_over_e4N_max", T_E4N, "T_over_e4N_min, T_over_e4N_max"),
                                  ("T_e2_over_6e4_min", "T_e2_over_6e4_max", T_E2, "T_e2_over_6e4 range")):
        parts, ok = [], True
        for N, (lo, hi) in ref.items():
            if N in have:
                a, b = d.loc[N, cmin], d.loc[N, cmax]
                ok &= abs(a - lo) <= 1e-5 and abs(b - hi) <= 1e-5
                parts.append(f"N={N}: [{a:.6f}, {b:.6f}] ({a - lo:+.0e}, {b - hi:+.0e})")
        out.append((f"{text} at N = 20, 30, 40, 60",
                    "; ".join(f"[{lo:.6f}, {hi:.6f}]" for lo, hi in ref.values()) + "; 1e-5 abs",
                    "; ".join(parts) + missing(have, ref), status(ok, "FAIL", all(N in have for N in ref))))
    parts, ok = [], True
    for N, ref in T_MAX.items():
        if N in have:
            q = N // 4
            st = d.loc[N, "T_max_state"]
            ok &= abs(d.loc[N, "T_max"] - ref) <= 1e-4 and st == f"{q}-{q}-{q}-{q}"
            parts.append(f"N={N}: {d.loc[N, 'T_max']:.4f} at {st} ({d.loc[N, 'T_max'] - ref:+.0e})")
    out.append(("T_max (at the equal-stacks state) at N = 20, 40, 60", "26.5324, 106.3099, 239.2719; 1e-4 abs",
                "; ".join(parts) + missing(have, T_MAX), status(ok, "FAIL", all(N in have for N in T_MAX))))
    return out


def solver_checks(sv):
    out = []
    stopped = sv["status"].str.startswith(("skipped", "killed"))
    okrows = sv[sv["status"].str.startswith("ok")]
    planned = [(m, N) for m, Ns in METHOD_N.items() for N in Ns]
    present = set(zip(sv["method"], sv["N"]))
    accounted = all(p in present for p in planned)
    bad_status = sv[~stopped & ~sv["status"].str.startswith("ok")]
    worst = okrows["rel_err"].max() if len(okrows) else float("nan")
    ok = bool((okrows["rel_err"] < 1e-10).all()) and bad_status.empty
    lost = [f"{m} {N}" for m, N in planned if (m, N) not in present]
    obs = f"largest {worst:.1e} over {len(okrows)} runs"
    if stopped.any():
        obs += "; stopped by memory rules: " + ", ".join(f"{r.method} N={r.N}" for r in sv[stopped].itertuples())
    if not bad_status.empty:
        obs += "; failed: " + ", ".join(f"{r.method} N={r.N} ({r.status})" for r in bad_status.itertuples())
    if lost:
        obs += "; missing: " + ", ".join(lost)
    out.append(("e09_solvers rel_err", "below 1e-10 for every method and N", obs, status(ok, "FAIL", accounted)))

    amg = okrows[okrows["method"] == "amg_cg"].set_index("N").sort_index()
    want = [40, 60, 80, 100, 120, 150]
    have = [N for N in want if N in amg.index]
    it = amg.loc[have, "iters"] if have else pd.Series(dtype=float)
    ok = len(have) == len(want) and bool(((it >= 9) & (it <= 14)).all()) and it.iloc[-1] >= it.iloc[0]
    out.append(("amg_cg iters", "9 to 14 for N = 40 ... 150, growing slowly",
                ", ".join(f"N={N}: {int(amg.loc[N, 'iters'])}" for N in amg.index) + missing(set(have), want),
                status(ok, "WARN", len(have) == len(want))))

    s = slope(amg["n"], amg["setup_s"] + amg["solve_s"])
    out.append(("amg_cg setup_s + solve_s against n", "slope of log time vs log n between 0.8 and 1.4",
                f"slope {s:.3f} over N = {', '.join(map(str, amg.index))}" + missing(set(amg.index), AMG_N),
                status(0.8 <= s <= 1.4, "WARN", all(N in amg.index for N in AMG_N))))

    ch = okrows[okrows["method"] == "cholmod"].set_index("N").sort_index()
    big = [N for N in CHOLMOD_NNZ if N in ch.index]
    s = slope(ch.loc[big, "n"], ch.loc[big, "nnz_factor"]) if big else float("nan")
    vals_ok = all(abs(ch.loc[N, "nnz_factor"] / CHOLMOD_NNZ[N] - 1) <= 0.10 for N in big)
    out.append(("cholmod nnz_factor against n (N = 60 to 100)",
                "slope between 1.25 and 1.6 (theory n^(4/3)); 8.0e6, 2.76e7, 7.45e7 at N = 60, 80, 100; 10%",
                f"slope {s:.3f}; " + ", ".join(f"N={N}: {ch.loc[N, 'nnz_factor']:.3g} "
                                               f"({ch.loc[N, 'nnz_factor'] / CHOLMOD_NNZ[N] - 1:+.1%})" for N in big)
                + missing(set(big), CHOLMOD_NNZ),
                status(1.25 <= s <= 1.6 and vals_ok, "WARN", len(big) == len(CHOLMOD_NNZ))))
    s = slope(ch.loc[big, "n"], ch.loc[big, "setup_s"]) if big else float("nan")
    out.append(("cholmod setup_s against n", "slope between 1.7 and 2.6 (theory n^2); fitted on N = 60, 80, 100",
                f"slope {s:.3f}; " + ", ".join(f"N={N}: {ch.loc[N, 'setup_s']:.2f} s" for N in big)
                + missing(set(big), CHOLMOD_NNZ),
                status(1.7 <= s <= 2.6, "WARN", len(big) == len(CHOLMOD_NNZ))))

    sp_ = okrows[(okrows["method"] == "splu") & (okrows["N"] == 60)]
    c60 = okrows[(okrows["method"] == "cholmod") & (okrows["N"] == 60)]
    have = len(sp_) and len(c60)
    ratio = sp_["peak_rss_mb"].iloc[0] / c60["peak_rss_mb"].iloc[0] if have else float("nan")
    out.append(("splu (COLAMD) peak memory vs cholmod at N = 60",
                "splu several times larger (about 1 GB vs 0.2 GB here); read as ratio >= 3",
                f"splu {sp_['peak_rss_mb'].iloc[0]:.0f} MB, cholmod {c60['peak_rss_mb'].iloc[0]:.0f} MB, ratio "
                f"{ratio:.2f}" if have else "no rows", status(ratio >= 3, "WARN", bool(have))))
    return out


def big_stack_checks(bs, al):
    out = []
    four = bs[bs["players"] == 4].set_index("N").sort_index()
    three = bs[bs["players"] == 3].set_index("N").sort_index()
    for ref, tol, text in ((P_SMALL, 1e-9, "N = 8, 10, 12, 16, 20, 24, 30, 40, 50"),
                           (P_LARGE, 1e-8, "N = 60, 80, 100, 120, 160, 200")):
        parts, ok = [], True
        for N, v in ref.items():
            if N in four.index:
                rel = four.loc[N, "P"] / v - 1
                ok &= abs(rel) <= tol
                parts.append(f"N={N}: {four.loc[N, 'P']:.12e} ({rel:+.1e})")
        out.append((f"e09_big_stack P (four players) at {text}",
                    ", ".join(f"{v:.12e}" for v in ref.values()) + f"; {tol:g} relative",
                    "; ".join(parts) + missing(set(four.index), ref),
                    status(ok, "FAIL", all(N in four.index for N in ref))))

    sl = four["local_slope"].dropna()
    inc = len(sl) > 1 and bool((np.diff(sl.to_numpy()) > 0).all())
    Ns = list(four.index)
    parts, ok, have = [], inc, True
    for (a, b), v in SLOPES4.items():
        if b in four.index and a in four.index and Ns.index(b) == Ns.index(a) + 1:
            got = four.loc[b, "local_slope"]
            ok &= abs(got - v) <= 1e-3
            parts.append(f"{a} to {b}: {got:.4f} ({got - v:+.1e})")
        else:
            have = False
            parts.append(f"{a} to {b}: missing")
    out.append(("local_slope (four players)", "increasing in N; 5.6762 (8 to 10), 5.7121 (20 to 24), 5.7171 (30 to "
                "40), 5.7198 (60 to 80), 5.7201 (80 to 100), 5.7205 (120 to 160), 5.7206 (160 to 200); 1e-3 abs",
                "; ".join(parts) + f"; increasing: {'yes' if inc else 'NO'}", status(ok, "FAIL", have)))

    s3 = three["local_slope"].dropna()
    out.append(("local_slope (three players)", "3.000; 1e-3 abs",
                ", ".join(f"N={N}: {v:.5f}" for N, v in s3.items()) if len(s3) else "no rows",
                status(bool((abs(s3 - 3) <= 1e-3).all()), "FAIL", len(s3) == 5)))
    big3 = three[three.index >= 80]
    pn3 = big3["P"] * big3.index.to_numpy(dtype=float) ** 3
    out.append(("P N^3, three players, N >= 80", "9.11959; 1e-5 relative",
                ", ".join(f"N={N}: {v:.6f} ({v / 9.11959 - 1:+.1e})" for N, v in pn3.items()) if len(pn3)
                else "no rows", status(bool((abs(pn3 / 9.11959 - 1) <= 1e-5).all()), "FAIL", len(pn3) == 3)))

    a4 = al[al["players"] == 4]
    if len(a4):
        a = a4["alpha_extrapolated"].iloc[0]
        obs = f"{a:.4f} (last slope {a4['alpha_last_slope'].iloc[0]:.4f})"
    out.append(("alpha_extrapolated (four players)", "5.721; 0.003", obs if len(a4) else "no row",
                status(len(a4) and abs(a - 5.721) <= 0.003, "WARN", bool(len(a4)) and 200 in four.index)))

    parts, ok = [], True
    for N, (nl, nf) in LUMP.items():
        if N in four.index:
            got = (int(four.loc[N, "n_lumped"]), int(four.loc[N, "n_full"]))
            ok &= got == (nl, nf)
            parts.append(f"N={N}: {got[0]}/{got[1]}")
    dev = (four["n_lumped"] / four["n_full"] - 1 / 6).abs().to_numpy()
    toward = len(dev) > 1 and bool((np.diff(dev) < 0).all())
    ok &= toward
    out.append(("n_lumped / n_full", "41/165 at N = 12, 204/969 at N = 20, 27353/156849 at N = 100; ratio tends to "
                "1/6; exact", "; ".join(parts) + f"; |ratio - 1/6| decreasing: {'yes' if toward else 'NO'}"
                + (f", {four['n_lumped'].iloc[-1] / four['n_full'].iloc[-1]:.5f} at N = {four.index[-1]}"
                   if len(four) else "") + missing(set(four.index), LUMP),
                status(ok, "FAIL", all(N in four.index for N in LUMP))))
    have = 200 in four.index
    out.append(("seconds for the lumped CHOLMOD solve at N = 200", "under 2 min",
                f"{four.loc[200, 'seconds']:.1f} s ({four.loc[200, 'solver']})" if have else "no row at 200",
                status(have and four.loc[200, "seconds"] < 120 and four.loc[200, "solver"] == "cholmod", "WARN",
                       have)))
    return out


def red_flags(idt, sv, bs):
    out = []
    dev = idt["e2_identity_relerr"].max()
    out.append(("A (6 e4) differs from e2", f"largest relative deviation {dev:.1e}", dev < 1e-12))
    four = bs[bs["players"] == 4].dropna(subset=["local_slope"])
    big = four[four["N"] >= 20]
    out.append(("four-player local slope below 5.7 or above 5.73 (N >= 20)",
                f"{big['local_slope'].min():.4f} to {big['local_slope'].max():.4f}" if len(big) else "no rows",
                len(big) > 0 and bool(((big["local_slope"] >= 5.7) & (big["local_slope"] <= 5.73)).all())))
    three = bs[bs["players"] == 3].dropna(subset=["local_slope"])
    out.append(("three-player slope not 3", f"{three['local_slope'].min():.5f} to {three['local_slope'].max():.5f}",
                bool((abs(three["local_slope"] - 3) <= 1e-3).all())))
    stopped = sv[sv["status"].str.startswith(("skipped", "killed"))]
    out.append(("direct solves stopped by the memory rules (60% of free memory, 3 GB projected factor)",
                "; ".join(f"{r.method} N={r.N}: {r.status}" for r in stopped.itertuples()) or "none",
                not stopped["status"].str.startswith("killed").any()))
    amg = sv[(sv["method"] == "amg_cg") & sv["status"].str.startswith("ok")].sort_values("N")
    if len(amg) > 1:
        grow = amg["iters"].iloc[-1] / amg["iters"].iloc[0]
        nr = amg["N"].iloc[-1] / amg["N"].iloc[0]
        out.append(("AMG-CG iterations growing like N", f"iters x{grow:.2f} while N x{nr:.0f} (flag if above sqrt of the N ratio)", grow < nr ** 0.5))
    return out


def fmt(x):
    if isinstance(x, str):
        return x
    if isinstance(x, (bool, np.bool_)):
        return str(bool(x))
    if isinstance(x, (int, np.integer)):
        return str(x)
    if isinstance(x, float) and math.isnan(x):
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
    idt = pd.read_csv(results / "e09_identities.csv")
    sv = pd.read_csv(results / "e09_solvers.csv")
    bs = pd.read_csv(results / "e09_big_stack.csv")
    al = pd.read_csv(results / "e09_alpha.csv")
    checks = identity_checks(idt) + solver_checks(sv) + big_stack_checks(bs, al)
    flags = red_flags(idt, sv, bs)

    sources = [("e09_identities", idt), ("e09_solvers", sv), ("e09_big_stack", bs), ("e09_alpha", al)]
    src = ", ".join(f"`{results / (name + '.csv')}` (git {df.iloc[0]['git_hash']}, {df.iloc[0]['timestamp']})"
                    for name, df in sources)
    m = idt.iloc[0]
    lines = [
        "# Chunk 9 report: four players",
        "",
        f"Sources: {src}; {m['platform']}, Python {m['python']}, numpy {m['numpy']}, scipy {m['scipy']}, "
        f"OMP_NUM_THREADS={m['omp_num_threads']}.",
        "",
        f"Free memory at the start of the run: {m['free_mem_mb_start']:.0f} MB (free + inactive + speculative "
        f"pages from vm_stat); workers were killed above 60% of it ({0.6 * m['free_mem_mb_start']:.0f} MB).",
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
    lines += ["", "## Data (e09_identities)", ""] + table(idt, "N", "bounds_hold")
    lines += ["", "## Data (e09_solvers, right-hand side e2, exact answer 6 x1 x2 x3 x4)", ""]
    lines += table(sv, "N", "status")
    lines += ["", "## Data (e09_big_stack: P(chip leader busts first) from (1, 1, 1, N-3) and (1, 1, N-2))", ""]
    lines += table(bs, "players", "solver")
    lines += ["", "## Data (e09_alpha)", ""] + table(al, "players", "alpha_extrapolated")
    lines += ["", "Figures: `figures/f09_solvers.png`, `figures/f09_big_stack.png`.", ""]

    for c, _, o, s in checks:
        print(f"{s:4s}  {c}: {o}")
    for c, o, ok in flags:
        print(f"{'ok' if ok else 'FLAG':4s}  {c}: {o}")
    print(f"Summary: {counts['PASS']} PASS, {counts['WARN']} WARN, {counts['FAIL']} FAIL.")
    report = results / "c09_report.md"
    report.write_text("\n".join(lines))
    print(f"wrote {report}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
