"""Chunk 3 check: compare results/e03_krylov.csv and results/e03_convergence.csv with the "Expected results"
table of plan/c03_krylov.md. Prints one PASS/WARN/FAIL line per table row (plus automatic red-flag checks) and
writes results/c03_report.md.
    python checks/check_c03.py [--results DIR]

Conventions:
  * Iteration counts vs the reference table: |observed / reference - 1| <= 3% PASS, <= 10% WARN, beyond FAIL.
  * An exponent is the least-squares slope of log iterations against log N over the rows with N = 160-1280.
  * "Six right-hand sides" = setup_time + 6 x solve_time on the random b (one preconditioner or factor reused).
  * If the rows a check needs are missing, the check gets its own kind (WARN or FAIL), never PASS.
"""
import argparse
import pathlib
import sys

import numpy as np
import pandas as pd

RTOL = 1e-10
NS = [20, 40, 80, 160, 320, 640, 1280]
REF = {
    "none": [39, 77, 154, 306, 603, 1198, 2368],
    "ic0": [15, 27, 49, 95, 183, 363, 714],
    "mic0": [15, 22, 33, 50, 73, 107, 157],
    "amg": [7, 8, 9, 11, 14, 16, 21],
    "ones": [9, 19, 40, 85, 172, 344, 686],
}


def its(df, kind, rhs="random"):
    """Series N -> iterations for one (kind, rhs)."""
    d = df[(df["kind"] == kind) & (df["rhs"] == rhs)]
    return d.set_index("N")["iterations"].sort_index()


def value(df, kind, rhs, N, col):
    d = df[(df["kind"] == kind) & (df["rhs"] == rhs) & (df["N"] == N)]
    return float(d[col].iloc[0]) if len(d) else np.nan


def slope(s, lo=160, hi=1280):
    s = s[(s.index >= lo) & (s.index <= hi)]
    if len(s) < 2:
        return np.nan, s
    return float(np.polyfit(np.log(s.index.values), np.log(s.values.astype(float)), 1)[0]), s


def table_check(df, kind):
    obs = its(df, kind)
    devs = {N: obs[N] / r - 1 for N, r in zip(NS, REF[kind]) if N in obs.index}
    if not devs:
        return (f"{kind} iteration counts vs the table (random b)", "as in the table", "no rows", "FAIL")
    worst = max(devs, key=lambda N: abs(devs[N]))
    w = abs(devs[worst])
    status = "PASS" if w <= 0.03 else ("WARN" if w <= 0.10 else "FAIL")
    exact = sum(int(obs[N]) == r for N, r in zip(NS, REF[kind]) if N in obs.index)
    return (f"{kind} iteration counts vs the table (random b)", "within 3% PASS; 3-10% WARN; beyond 10% FAIL",
            f"{exact}/{len(devs)} exact; worst {devs[worst]:+.1%} at N = {worst} ({int(obs[worst])} vs "
            f"{REF[kind][NS.index(worst)]})", status)


def run_checks(df):
    out = []
    cg = df[df["kind"] != "direct"]

    # 1-3. none, ic0, mic0 counts vs the reference table
    for kind in ("none", "ic0", "mic0"):
        out.append(table_check(df, kind))

    # 4. amg counts within a factor 0.7-1.4
    obs = its(df, "amg")
    r = {N: obs[N] / ref for N, ref in zip(NS, REF["amg"]) if N in obs.index}
    ok = len(r) > 0 and all(0.7 <= v <= 1.4 for v in r.values())
    out.append(("amg iteration counts vs the table (random b)", "factor 0.7 to 1.4",
                ", ".join(f"N={N}: {int(obs[N])} ({v:.2f})" for N, v in r.items()) or "no rows",
                "PASS" if ok else "WARN"))

    # 5. jacobi = none exactly
    j = cg[cg["kind"] == "jacobi"].set_index(["N", "rhs"])["iterations"]
    n_ = cg[cg["kind"] == "none"].set_index(["N", "rhs"])["iterations"]
    common = j.index.intersection(n_.index)
    bad = [f"N={N} {rhs}" for N, rhs in common if j[(N, rhs)] != n_[(N, rhs)]]
    out.append(("jacobi iterations = none iterations, every (N, rhs)", "equal, exact",
                f"{len(common) - len(bad)}/{len(common)} equal" + (f"; differ at {', '.join(bad)}" if bad else ""),
                "PASS" if len(common) and not bad else "FAIL"))

    # 6. none, random: iterations / N for N >= 80
    s = its(df, "none")
    s = s[s.index >= 80]
    ratio = s / s.index
    out.append(("none, random b: iterations / N for N >= 80", "1.85-1.93, in [1.75, 2.05]",
                ", ".join(f"N={N}: {v:.3f}" for N, v in ratio.items()) or "no rows",
                "PASS" if len(ratio) and ratio.between(1.75, 2.05).all() else "FAIL"))

    # 7. none: iterations / bound below 1 (every rhs)
    d = cg[cg["kind"] == "none"]
    rb = d["iterations"] / d["bound"]
    rr = rb[d["rhs"] == "random"]
    out.append(("none: iterations / bound", "0.39-0.45 (random b), below 1 (every rhs)",
                f"random b {rr.min():.3f}-{rr.max():.3f}; every rhs max {rb.max():.3f} over {len(rb)} rows"
                if len(rb) else "no rows", "PASS" if len(rb) and (rb < 1).all() else "FAIL"))

    # 8. b = ones: iterations / floor((N-1)/2)
    s = its(df, "none", "ones")
    ratio = s / ((s.index.values - 1) // 2)
    out.append(("b = ones: iterations / floor((N-1)/2)", "1.00 (N <= 41), 1.03-1.08 above; in [1.0, 1.15]",
                ", ".join(f"N={N}: {v:.3f}" for N, v in ratio.items()) or "no rows",
                "PASS" if len(ratio) and ratio.between(1.0, 1.15).all() else "WARN"))

    # 9. fitted exponents, N = 160-1280, random b
    parts, ok = [], True
    for kind, good in [("none", lambda e: 0.9 <= e <= 1.05), ("ic0", lambda e: 0.9 <= e <= 1.05),
                       ("mic0", lambda e: 0.45 <= e <= 0.65), ("amg", lambda e: e < 0.5)]:
        e, used = slope(its(df, kind))
        ok &= bool(len(used) >= 2 and good(e))
        rng = f"N={int(used.index.min())}-{int(used.index.max())}" if len(used) else "no rows"
        parts.append(f"{kind} {e:.3f} ({rng})")
    out.append(("fitted exponent of iterations vs N, N = 160-1280, random b",
                "none 0.98, ic0 0.97, mic0 0.55, amg 0.2-0.4; none, ic0 in [0.9, 1.05]; mic0 in [0.45, 0.65]; "
                "amg below 0.5", "; ".join(parts), "PASS" if ok else "WARN"))

    # 10. ranking amg < mic0 < ic0 < none at every N >= 80, every rhs except ones
    bad, total = [], 0
    for (N, rhs), g in cg[(cg["N"] >= 80) & (cg["rhs"] != "ones")].groupby(["N", "rhs"]):
        k = g.set_index("kind")["iterations"]
        if not all(x in k for x in ("amg", "mic0", "ic0", "none")):
            continue
        total += 1
        if not (k["amg"] < k["mic0"] < k["ic0"] < k["none"]):
            bad.append(f"N={N} {rhs} (amg {int(k['amg'])}, mic0 {int(k['mic0'])}, ic0 {int(k['ic0'])}, "
                       f"none {int(k['none'])})")
    out.append(("ranking at every N >= 80, every rhs except ones", "amg < mic0 < ic0 < none, strict",
                f"{total - len(bad)}/{total} (N, rhs) ranked" + (f"; broken at {'; '.join(bad)}" if bad else ""),
                "PASS" if total and not bad else "FAIL"))

    # 11. b = ones: ic0 vs none (IC(0) breaks the symmetry behind plain CG's floor((N-1)/2) termination)
    ic1, none1 = its(df, "ic0", "ones"), its(df, "none", "ones")
    common = ic1.index.intersection(none1.index)
    small = [N for N in common if N <= 80]
    ok = len(small) > 0 and all(ic1[N] > none1[N] for N in small) and 160 in common \
        and abs(ic1[160] / none1[160] - 1) <= 0.05
    out.append(("b = ones: ic0 vs none",
                "ic0 needs more iterations at N <= 80 (47 vs 40 at N = 80), about equal at N = 160 (84 vs 85) "
                "(read here as: ic0 > none at every N <= 80, within 5% at N = 160)",
                ", ".join(f"N={N}: {int(ic1[N])} vs {int(none1[N])}" for N in common) or "no rows",
                "PASS" if ok else "WARN"))

    # 12. forward error
    fe, cap = cg["forward_error"], cg["kappa2"] * RTOL
    worst = cg.loc[fe.idxmax()] if len(cg) else None
    status = "FAIL" if (not len(cg) or (fe > cap).any()) else ("WARN" if (fe > 1e-8).any() else "PASS")
    out.append(("forward_error at rtol 1e-10", "1e-11 to 3e-9 up to N = 640, about 5e-9 at N = 1280; below kappa2(N) * 1e-10 FAIL; above 1e-8 WARN",
                f"{fe.min():.2e} to {fe.max():.2e} over {len(cg)} rows (max at N = {int(worst['N'])} {worst['kind']} "
                f"{worst['rhs']}); {int((fe > cap).sum())} above kappa2 * 1e-10" if len(cg) else "no rows", status))

    # 13. time per iteration ic0 / none, N >= 640
    parts, vals = [], []
    for N in sorted(cg[cg["N"] >= 640]["N"].unique()):
        for rhs in ("ones", "random", "out_first", "order321"):
            v = value(cg, "ic0", rhs, N, "time_per_iteration") / value(cg, "none", rhs, N, "time_per_iteration")
            if not np.isnan(v):
                vals.append(v)
        parts.append(f"N={N}: {min(vals[-4:]):.2f}-{max(vals[-4:]):.2f}" if vals else f"N={N}: no rows")
    vals = np.array(vals)
    out.append(("time_per_iteration ratio ic0 / none, N >= 640 (every rhs)", "2-4 here, in [1.5, 5]",
                "; ".join(parts) or "no rows",
                "PASS" if len(vals) and ((vals >= 1.5) & (vals <= 5)).all() else "WARN"))

    # 14. amg time per iteration / none at N = 1280
    vals = [value(cg, "amg", rhs, 1280, "time_per_iteration") / value(cg, "none", rhs, 1280, "time_per_iteration")
            for rhs in ("ones", "random", "out_first", "order321")]
    vals = np.array([v for v in vals if not np.isnan(v)])
    out.append(("amg time_per_iteration / none, N = 1280 (every rhs)", "about 10, in [4, 25]",
                f"{vals.min():.1f}-{vals.max():.1f} over {len(vals)} rhs" if len(vals) else "no rows",
                "PASS" if len(vals) and ((vals >= 4) & (vals <= 25)).all() else "WARN"))

    # 15. one rhs at N = 1280: total time, amg and mic0 vs none
    def total(kind, count=1):
        return value(df, kind, "random", 1280, "setup_time") + count * value(df, kind, "random", 1280, "solve_time")

    t_none = total("none")
    sp = {k: t_none / total(k) for k in ("amg", "mic0")}
    ok = all(not np.isnan(v) and v >= 3 for v in sp.values())
    out.append(("one rhs at N = 1280, total time (setup + solve): amg and mic0 vs none", "5-7 times faster; at least 3",
                f"none {t_none:.2f} s; amg {total('amg'):.2f} s ({sp['amg']:.1f}x); mic0 {total('mic0'):.2f} s "
                f"({sp['mic0']:.1f}x)", "PASS" if ok else "WARN"))

    # 16. six rhs at N = 1280: direct vs amg
    t_d, t_a = total("direct", 6), total("amg", 6)
    out.append(("six rhs at N = 1280: direct (one factor, six solves) vs amg (one setup, six solves)", "direct faster",
                f"direct {t_d:.2f} s, amg {t_a:.2f} s", "PASS" if t_d < t_a else "WARN"))
    return out


def red_flags(df, conv):
    """Automatic checks of the spec's red-flag list (plus two extras). Each returns (description, observed, ok)."""
    out = []
    cg = df[df["kind"] != "direct"]
    none, ic = its(df, "none"), its(df, "ic0")
    common = none.index.intersection(ic.index)
    out.append(("IC(0) reduces iterations at every N (random b)",
                ", ".join(f"N={N}: {none[N] / ic[N]:.2f}x" for N in common), bool((ic[common] < none[common]).all())))
    e, _ = slope(its(df, "mic0"))
    out.append(("MIC(0) grows like N^{1/2}, not N", f"exponent {e:.3f} over N = 160-1280", bool(e < 0.75)))
    s = its(df, "none", "ones")
    r = s / ((s.index.values - 1) // 2)
    out.append(("b = ones terminates near floor((N-1)/2)", f"ratio {r.min():.3f}-{r.max():.3f}",
                bool(len(r) and (r <= 1.15).all())))
    fe = cg["forward_error"].max()
    out.append(("forward errors not above about 1e-8", f"max {fe:.2e}", bool(fe <= 1e-8)))
    a = cg[cg["kind"] == "amg"]["iterations"]
    out.append(("AMG never above about 30 iterations", f"max {int(a.max())} over {len(a)} rows" if len(a) else "no rows",
                bool(len(a) and a.max() <= 30)))
    conv_bad = cg[cg["final_relres"] > RTOL]
    out.append(("every CG row converged (final_relres <= 1e-10)", f"{len(cg) - len(conv_bad)}/{len(cg)} rows",
                conv_bad.empty))
    c = conv[(conv["kind"] == "none")].dropna(subset=["chebyshev"])
    ratio = (c["err_A"] / c["chebyshev"]).max() if len(c) else np.nan
    out.append(("extra: plain CG err_A never above the Chebyshev bound (e03_convergence)",
                f"max err_A / bound {ratio:.3g} over {len(c)} rows", bool(len(c) and ratio <= 1)))
    return out


def fmt(x):
    if isinstance(x, str):
        return x
    if isinstance(x, (int, np.integer)):
        return str(x)
    if isinstance(x, float) and np.isnan(x):
        return ""
    if isinstance(x, float) and x.is_integer() and abs(x) < 1e6:
        return str(int(x))
    return f"{x:.4g}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    args = parser.parse_args()
    results = pathlib.Path(args.results)
    df = pd.read_csv(results / "e03_krylov.csv")
    conv = pd.read_csv(results / "e03_convergence.csv")
    checks = run_checks(df)
    flags = red_flags(df, conv)

    meta, cmeta = df.iloc[0], conv.iloc[0]
    lines = [
        "# Chunk 3 report: conjugate gradients and preconditioners",
        "",
        f"Sources: `{results / 'e03_krylov.csv'}` (git {meta['git_hash']}, {meta['timestamp']}) and "
        f"`{results / 'e03_convergence.csv'}` (git {cmeta['git_hash']}, {cmeta['timestamp']}); "
        f"{meta['platform']}, Python {meta['python']}, numpy {meta['numpy']}, scipy {meta['scipy']}, "
        f"OMP_NUM_THREADS={meta['omp_num_threads']}.",
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

    # iteration table in the spec's layout: observed (reference)
    Ns = [N for N in NS if N in set(df["N"])]
    lines += ["", "## Iterations, rtol 1e-10: observed (reference)", "",
              "| | " + " | ".join(str(N) for N in Ns) + " |", "|---|" + "---|" * len(Ns)]
    for label, kind, rhs, key in [("none", "none", "random", "none"), ("ic0", "ic0", "random", "ic0"),
                                  ("mic0", "mic0", "random", "mic0"), ("amg", "amg", "random", "amg"),
                                  ("none, b = ones", "none", "ones", "ones")]:
        s = its(df, kind, rhs)
        cells = [f"{int(s[N])} ({REF[key][NS.index(N)]})" if N in s.index else "" for N in Ns]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines.append("| floor((N-1)/2) | " + " | ".join(str((N - 1) // 2) for N in Ns) + " |")

    # convergence summary
    lines += ["", f"## Convergence histories (e03_convergence, N = {int(cmeta['N'])})", "",
              "| kind | rhs | iterations | final relres | final err_A | final err_inf |", "|---|---|---|---|---|---|"]
    for (kind, rhs), g in conv.groupby(["kind", "rhs"], sort=False):
        last = g.sort_values("k").iloc[-1]
        lines.append(f"| {kind} | {rhs} | {int(last['k'])} | {last['relres']:.2e} | {last['err_A']:.2e} | "
                     f"{last['err_inf']:.2e} |")

    lines += ["", "## Data (e03_krylov)", ""]
    data = df.loc[:, "N":"kappa2"]
    lines += ["| " + " | ".join(data.columns) + " |", "|" + "---|" * len(data.columns)]
    lines += ["| " + " | ".join(fmt(x) for x in row) + " |" for row in data.itertuples(index=False)]
    lines.append("")

    for c, _, o, s in checks:
        print(f"{s:4s}  {c}: {o}")
    for c, o, ok in flags:
        print(f"{'ok' if ok else 'FLAG':4s}  {c}: {o}")
    report = results / "c03_report.md"
    report.write_text("\n".join(lines))
    print(f"wrote {report}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
