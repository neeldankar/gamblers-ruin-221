"""Chunk 8 check: compare results/e08_wikipedia.csv, e08_icm_errors.csv and e08_limit.csv with the "Expected results"
table of plan/c08_icm.md. Prints one PASS/WARN/FAIL line per table row (plus automatic red-flag checks) and writes
results/c08_report.md.
    python checks/check_c08.py [--results DIR]

Conventions (logged in notes/decisions.md, chunk 8):
  * Each row gets the kind the spec lists (FAIL or WARN) when it misses, and also when any N or row it lists is
    missing from the CSV (for example after a --quick run): never PASS without data.
  * States are compared as the sorted strings "a-b-c" that e08_icm writes.
  * max_rel_err_p3 is unsigned, |P_ICM(3rd) - P(3rd)| / P(3rd); its tolerance is 1e-6 relative to the listed value.
"""
import argparse
import pathlib
import sys

import numpy as np
import pandas as pd

ERR_NS = [30, 60, 120, 240, 480]
WIKI = {  # stacks: (exact p2nd, exact equity, print precision of the published table)
    "25-87-88": (0.1584080071, 25.33408007, 1e-4),
    "21-89-90": (0.1346400128, 24.49640013, 1e-4),
    "198-1-1": (0.0099988601, 49.79998860, 1e-6),
}
MAX_ABS = dict(zip(ERR_NS, [0.0358888708, 0.0359655670, 0.0360434580, 0.0360462040, 0.0360502475]))
ARGMAX = dict(zip(ERR_NS, ["4-13-13", "7-26-27", "15-52-53", "30-105-105", "59-210-211"]))
MEAN_ABS = dict(zip(ERR_NS, [0.01655161, 0.01604887, 0.01574379, 0.01557549, 0.01548642]))
UNDER = dict(zip(ERR_NS, [-0.27088621, -0.27220714, -0.27253356, -0.27257953, -0.27259922]))
UNDER_STATE = dict(zip(ERR_NS, ["6-6-18", "12-13-35", "25-25-70", "50-51-139", "101-101-278"]))
REL_P3 = dict(zip(ERR_NS, [5.8060831, 12.3815091, 25.5381260, 51.8541766, 104.4876678]))
FRAC_MID = dict(zip(ERR_NS, [0.1639, 0.1808, 0.1876, 0.1921, 0.1935]))
LIMIT_640 = {"P123": 0.3096287142, "P213": 0.1903712858, "P321": 0.0662037586}
P1_SECOND_640 = 0.2607768223


def status(ok, kind, have=True):
    return "PASS" if (have and ok) else kind


def truthy(col):
    return col.astype(str) == "True"


def by_n(df, Ns):
    """Rows of df for the listed N, indexed by N, and whether every listed N is present."""
    d = df[df["N"].isin(Ns)].set_index("N").sort_index()
    return d, all(N in d.index for N in Ns)


def missing(d, Ns):
    lost = [N for N in Ns if N not in d.index]
    return f" (missing N = {', '.join(map(str, lost))})" if lost else ""


def wiki_row(wk, stacks, method):
    d = wk[(wk["stacks"] == stacks) & (wk["method"] == method)]
    return d.iloc[0] if len(d) else None


def run_checks(wk, er, lm):
    out = []
    have_wiki = all(wiki_row(wk, s, m) is not None for s in WIKI
                    for m in ("exact", "icm", "published_exact", "published_icm"))

    # 1-2. our exact values at N = 200
    for col, idx, tol, text in (("p2nd", 0, 1e-9, "p2nd"), ("equity", 1, 1e-7, "equity")):
        parts, ok = [], True
        for s, ref in WIKI.items():
            r = wiki_row(wk, s, "exact")
            if r is None:
                continue
            ok &= abs(r[col] - ref[idx]) <= tol
            parts.append(f"{s}: {r[col]:.10f} ({r[col] - ref[idx]:+.1e})")
        out.append((f"e08_wikipedia exact {text} at (25,87,88), (21,89,90), (198,1,1)",
                    ", ".join(f"{v[idx]:.10g}" for v in WIKI.values()) + f"; {tol:g} abs",
                    "; ".join(parts) if parts else "no rows", status(ok, "FAIL", bool(parts) and have_wiki)))

    # 3-4. against the published table
    for ours, pub, unit, label in (("exact", "published_exact", 0.5, "half a printed digit (5e-5; 5e-7 for "
                                    "(198,1,1))"), ("icm", "published_icm", 1.0, "one printed digit (1e-4; 1e-6 for "
                                                    "(198,1,1))")):
        parts, ok = [], True
        for s, ref in WIKI.items():
            a, b = wiki_row(wk, s, ours), wiki_row(wk, s, pub)
            if a is None or b is None:
                continue
            dev = max(abs(a[c] - b[c]) for c in ("p1st", "p2nd", "p3rd"))
            deq = abs(a["equity"] - b["equity"])
            ok &= dev <= unit * ref[2] + 1e-12 and deq <= 0.005
            parts.append(f"{s}: places {dev:.2g} (limit {unit * ref[2]:g}), equity {deq:.4f}")
        out.append((f"{ours} vs {pub} rows", f"p1st, p2nd, p3rd within {label}; equity within 0.005",
                    "; ".join(parts) if parts else "no rows", status(ok, "FAIL", bool(parts) and have_wiki)))

    d, full = by_n(er, ERR_NS)

    def per_n(name, expected, col, ref, tol, kind="FAIL", fmt="{:.10f}"):
        parts = [f"N={N}: {fmt.format(d.loc[N, col])} ({d.loc[N, col] - ref[N]:+.1e})" for N in d.index]
        ok = all(abs(d.loc[N, col] - ref[N]) <= tol for N in d.index)
        out.append((name, expected, (", ".join(parts) + missing(d, ERR_NS)) if parts else "no rows",
                    status(ok, kind, full)))

    # 5-7.
    per_n("max_abs_err_p2 at N = 30, 60, 120, 240, 480",
          "0.0358888708, 0.0359655670, 0.0360434580, 0.0360462040, 0.0360502475; 1e-9 abs",
          "max_abs_err_p2", MAX_ABS, 1e-9)
    out.append(("argmax_state", "4-13-13, 7-26-27, 15-52-53, 30-105-105, 59-210-211 (runner-up gaps 2e-4 to 1.3e-6); "
                "exact", (", ".join(f"N={N}: {d.loc[N, 'argmax_state']}" for N in d.index) + missing(d, ERR_NS))
                if len(d) else "no rows",
                status(all(d.loc[N, "argmax_state"] == ARGMAX[N] for N in d.index), "FAIL", full)))
    per_n("mean_abs_err_p2", "0.01655161, 0.01604887, 0.01574379, 0.01557549, 0.01548642; 1e-7 abs",
          "mean_abs_err_p2", MEAN_ABS, 1e-7, fmt="{:.8f}")

    # 8. overrate = 10 x max_abs_err_p2 at the same state
    parts, ok = [], True
    for N in d.index:
        r = d.loc[N]
        dev = r["max_equity_overrate"] - 10 * r["max_abs_err_p2"]
        ok &= abs(dev) <= 1e-8 and r["overrate_state"] == r["argmax_state"]
        parts.append(f"N={N}: {r['max_equity_overrate']:.8f} at {r['overrate_state']} ({dev:+.1e})")
    out.append(("max_equity_overrate", "10 x max_abs_err_p2 (w2 - w3 = 10), at the same states; 1e-8 abs",
                ("; ".join(parts) + missing(d, ERR_NS)) if parts else "no rows", status(ok, "FAIL", full)))

    # 9. underrate values and states
    parts, ok = [], True
    for N in d.index:
        r = d.loc[N]
        dev = r["max_equity_underrate"] - UNDER[N]
        ok &= abs(dev) <= 1e-8 and r["underrate_state"] == UNDER_STATE[N]
        parts.append(f"N={N}: {r['max_equity_underrate']:.8f} at {r['underrate_state']} ({dev:+.1e})")
    out.append(("max_equity_underrate", "-0.27088621, -0.27220714, -0.27253356, -0.27257953, -0.27259922 at 6-6-18, "
                "12-13-35, 25-25-70, 50-51-139, 101-101-278; 1e-8 abs, state exact",
                ("; ".join(parts) + missing(d, ERR_NS)) if parts else "no rows", status(ok, "FAIL", full)))

    # 10-11.
    out.append(("identity_max_dev", "below 1e-10",
                (", ".join(f"N={N}: {d.loc[N, 'identity_max_dev']:.2g}" for N in d.index) + missing(d, ERR_NS))
                if len(d) else "no rows", status(bool((d["identity_max_dev"] < 1e-10).all()), "FAIL", full)))
    both = truthy(d["short_overrated_all"]) & truthy(d["long_underrated_all"])
    out.append(("short_overrated_all, long_underrated_all", "True at every N",
                (", ".join(f"N={N}: {d.loc[N, 'short_overrated_all']}, {d.loc[N, 'long_underrated_all']}"
                           for N in d.index) + missing(d, ERR_NS)) if len(d) else "no rows",
                status(bool(both.all()), "FAIL", full)))

    # 12. relative error of P(3rd), at (N-2)-1-1
    parts, ok = [], True
    for N in d.index:
        r = d.loc[N]
        rel = r["max_rel_err_p3"] / REL_P3[N] - 1
        ok &= abs(rel) <= 1e-6 and r["argmax_rel_state_p3"] == f"1-1-{N - 2}"
        parts.append(f"N={N}: {r['max_rel_err_p3']:.7f} at {r['argmax_rel_state_p3']} ({rel:+.1e} rel)")
    out.append(("max_rel_err_p3", "5.8060831, 12.3815091, 25.5381260, 51.8541766, 104.4876678, all at (N-2)-1-1; "
                "1e-6 relative", ("; ".join(parts) + missing(d, ERR_NS)) if parts else "no rows",
                status(ok, "FAIL", full)))

    # 13. fraction of middle stacks overrated
    vals = d["frac_middle_overrated"].to_numpy()
    inc = len(vals) > 1 and bool((np.diff(vals) > 0).all())
    ok = all(abs(d.loc[N, "frac_middle_overrated"] - FRAC_MID[N]) <= 1e-3 for N in d.index) and inc
    out.append(("frac_middle_overrated", "0.1639, 0.1808, 0.1876, 0.1921, 0.1935 (increasing); 1e-3 abs",
                (", ".join(f"N={N}: {d.loc[N, 'frac_middle_overrated']:.4f}" for N in d.index)
                 + f"; increasing: {'yes' if inc else 'NO'}" + missing(d, ERR_NS)) if len(d) else "no rows",
                status(ok, "WARN", full)))

    # 14-15. observed order
    lim, lfull = by_n(lm, [80, 160, 320])
    out.append(("obs_order_min, obs_order_max at N = 80, 160, 320", "in [3.9, 4.1]",
                (", ".join(f"N={N}: {r.obs_order_min:.3f} to {r.obs_order_max:.3f}" for N, r in lim.iterrows())
                 + missing(lim, [80, 160, 320])) if len(lim) else "no rows",
                status(bool(((lim["obs_order_min"] >= 3.9) & (lim["obs_order_max"] <= 4.1)).all()), "FAIL", lfull)))
    l640 = lm[lm["N"] == 640]
    r640 = l640.iloc[0] if len(l640) else None
    out.append(("obs_order at N = 640", "in [3.8, 4.2] (differences are near 5e-11, so rounding shows)",
                f"{r640['obs_order_min']:.3f} to {r640['obs_order_max']:.3f}" if r640 is not None else "no row at 640",
                status(r640 is not None and r640["obs_order_min"] >= 3.8 and r640["obs_order_max"] <= 4.2, "WARN",
                       r640 is not None)))

    # 16-18. the limit at N = 640
    if r640 is not None:
        devs = {c: r640[c] - v for c, v in LIMIT_640.items()}
        obs = ", ".join(f"{c} {r640[c]:.10f} ({v:+.1e})" for c, v in devs.items())
        ok = all(abs(v) <= 1e-9 for v in devs.values())
    out.append(("P123, P213, P321 at N = 640", "0.3096287142, 0.1903712858, 0.0662037586; 1e-9 abs",
                obs if r640 is not None else "no row at 640", status(r640 is not None and ok, "FAIL", r640 is not None)))
    if r640 is not None:
        d1, d2 = r640["p1_second"] - P1_SECOND_640, r640["icm_p1_second"] - 2 / 7
        obs = f"p1_second {r640['p1_second']:.10f} ({d1:+.1e}); icm_p1_second {r640['icm_p1_second']:.16f} ({d2:+.1e})"
    out.append(("p1_second at N = 640; icm_p1_second", "0.2607768223; 2/7 = 0.2857142857; 1e-9; 1e-15",
                obs if r640 is not None else "no row at 640",
                status(r640 is not None and abs(d1) <= 1e-9 and abs(d2) <= 1e-15, "FAIL", r640 is not None)))
    out.append(("seconds at N = 640", "under 30 s", f"{r640['seconds']:.2f} s" if r640 is not None else "no row at 640",
                status(r640 is not None and r640["seconds"] < 30, "WARN", r640 is not None)))
    return out


def red_flags(wk, er, lm):
    out = []
    icm = wk[wk["method"] == "icm"]
    x1 = icm["stacks"].str.split("-").str[0].astype(float) / 200
    dev = float((icm["p1st"] - x1).abs().max()) if len(icm) else np.nan
    out.append(("P_ICM(1st) different from x/N (e08_wikipedia icm rows)", f"max |p1st - x1/N| = {dev:.1e}",
                len(icm) > 0 and dev < 1e-15))
    out.append(("identity_max_dev above 1e-10", f"largest {er['identity_max_dev'].max():.2g}",
                bool((er["identity_max_dev"] <= 1e-10).all())))
    bad = er[~(truthy(er["short_overrated_all"]) & truthy(er["long_underrated_all"]))]
    out.append(("a short stack underrated anywhere, or a big stack overrated",
                "none" if bad.empty else "at N = " + ", ".join(map(str, bad["N"])), bad.empty))
    e = er.sort_values("N")["max_abs_err_p2"].to_numpy()
    out.append(("max_abs_err_p2 decreasing in N", ", ".join(f"{v:.6f}" for v in e), bool((np.diff(e) > 0).all())))
    o = lm.dropna(subset=["obs_order_min"])
    out.append(("obs_order near 2 (a wrong stencil or boundary)",
                f"observed orders {o['obs_order_min'].min():.3f} to {o['obs_order_max'].max():.3f}" if len(o)
                else "no observed orders", len(o) > 0 and bool((o["obs_order_min"] > 3).all())))
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
    wk = pd.read_csv(results / "e08_wikipedia.csv")
    er = pd.read_csv(results / "e08_icm_errors.csv", dtype={"argmax_state": str})
    lm = pd.read_csv(results / "e08_limit.csv")
    checks = run_checks(wk, er, lm)
    flags = red_flags(wk, er, lm)

    sources = [("e08_wikipedia", wk), ("e08_icm_errors", er), ("e08_limit", lm)]
    src = ", ".join(f"`{results / (name + '.csv')}` (git {df.iloc[0]['git_hash']}, {df.iloc[0]['timestamp']})"
                    for name, df in sources)
    m = er.iloc[0]
    lines = [
        "# Chunk 8 report: the Independent Chip Model against the exact probabilities",
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
    lines += ["", "## Data (e08_wikipedia, N = 200, payouts 50/30/20, player 1 listed first)", ""]
    lines += table(wk, "stacks", "equity")
    lines += ["", "## Data (e08_icm_errors)", ""] + table(er, "N", "seconds")
    lines += ["", "## Data (e08_limit, stacks (N/5, 3N/10, N/2))", ""] + table(lm, "N", "seconds")
    lines += ["", "Figures: `figures/f08_icm_map.png` (from e08_states_N120.csv), `figures/f08_limit.png`.", ""]

    for c, _, o, s in checks:
        print(f"{s:4s}  {c}: {o}")
    for c, o, ok in flags:
        print(f"{'ok' if ok else 'FLAG':4s}  {c}: {o}")
    report = results / "c08_report.md"
    report.write_text("\n".join(lines))
    print(f"wrote {report}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
