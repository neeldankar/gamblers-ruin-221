"""Chunk 6 check: compare results/e06_fft.csv with the "Expected results" table of plan/c06_fft.md. Prints one
PASS/WARN/FAIL line per table row (plus automatic red-flag checks) and writes results/c06_report.md.
    python checks/check_c06.py [--results DIR]

Conventions (logged in notes/decisions.md, chunk 6):
  * Each row gets the kind the spec lists (FAIL or WARN) when it misses, and also when an N it needs is missing
    from the CSV (for example after a --quick run): never PASS without data.
  * "For every N" rows need all of N = 50 ... 1600; rows built on splu need N = 50 ... 800 (splu is NaN at 1600).
  * min_p123 x N^3: absolute tolerance 0.001 at every N with a splu value, and the minimum must sit at (N-2, 1, 1).
  * Timing slope: least-squares slope of log(seconds_fft) against log(n) over N = 200, 400, 800, 1600.
"""
import argparse
import pathlib
import sys

import numpy as np
import pandas as pd

EPS = 2.0 ** -52
ALL_N = [50, 100, 200, 400, 800, 1600]
SPLU_N = [50, 100, 200, 400, 800]
SLOPE_N = [200, 400, 800, 1600]


def status(ok, kind, have=True):
    return "PASS" if (have and ok) else kind


def missing(d, Ns):
    lost = [N for N in Ns if N not in d.index]
    return f" (missing N = {', '.join(map(str, lost))})" if lost else ""


def has(d, Ns):
    return all(N in d.index for N in Ns)


def slope(d):
    Ns = [N for N in SLOPE_N if N in d.index]
    if len(Ns) < 2:
        return np.nan
    return float(np.polyfit(np.log(d.loc[Ns, "n"]), np.log(d.loc[Ns, "seconds_fft"]), 1)[0])


def run_checks(d):
    out = []

    def every(name, expected, values, limit, Ns, fmt="{:.2g}"):
        parts = [f"N={N}: {fmt.format(values[N])}" for N in Ns if N in d.index]
        ok = all(values[N] <= limit for N in Ns if N in d.index)
        out.append((name, expected, (", ".join(parts) + missing(d, Ns)) if parts else "no rows",
                    status(ok, "FAIL", has(d, Ns))))

    ek = EPS * d["kappa2"]
    # 1-4. normwise accuracy
    every("fwd_err_over_eps_kappa", "at most 10 for every N (measured 0.02 to 0.4)",
          d["fwd_err_over_eps_kappa"], 10, ALL_N, "{:.3f}")
    every("resid_random", "at most 1e-10 for every N (measured 1.4e-15 at N = 50 up to 3.1e-12 at N = 1600)",
          d["resid_random"], 1e-10, ALL_N)
    every("err_vs_splu / (eps kappa2)", "at most 10 (measured 0.07 to 0.17)", d["err_vs_splu"] / ek, 10,
          SPLU_N, "{:.3f}")
    every("sum_out_first_err / (eps kappa2)", "at most 10 (measured 0.05 to 0.6)", d["sum_out_first_err"] / ek,
          10, ALL_N, "{:.3f}")

    # 5. min_p123 x N^3
    parts, ok = [], True
    for N in SPLU_N:
        if N not in d.index:
            continue
        v = d.loc[N, "min_p123"] * N ** 3
        at = d.loc[N, "min_state"] == f"{N - 2}-1-1"
        ok &= abs(v - 4.5598) <= 0.001 and at
        parts.append(f"N={N}: {v:.6f} at {d.loc[N, 'min_state']}")
    out.append(("min_p123 x N^3", "4.5598 (at the state (N - 2, 1, 1)); 0.001",
                ("; ".join(parts) + missing(d, SPLU_N)) if parts else "no rows", status(ok, "FAIL", has(d, SPLU_N))))

    # 6-7. p123_reldiff
    have = has(d, [800])
    v800 = d.loc[800, "p123_reldiff"] if have else np.nan
    out.append(("p123_reldiff at N = 800", "1e-8 to 1e-4 (two reference implementations: 6e-7 and 2e-6; about "
                "1e-11 at N = 50)", f"{v800:.2g}" if have else "no row at N = 800",
                status(1e-8 <= v800 <= 1e-4, "WARN", have)))
    have = has(d, [50, 800])
    ratio = v800 / d.loc[50, "p123_reldiff"] if have else np.nan
    obs = (", ".join(f"N={N}: {d.loc[N, 'p123_reldiff']:.2g}" for N in SPLU_N if N in d.index)
           + f"; ratio {ratio:.3g}") if have else "needs N = 50 and 800" + missing(d, [50, 800])
    out.append(("p123_reldiff at N = 800 / p123_reldiff at N = 50", "above 100 (measured 3e4 and 4e5; single "
                "steps in N can dip)", obs, status(ratio > 100, "WARN", have)))

    # 8-10. timing
    s = slope(d)
    out.append(("slope of log(seconds_fft) against log(n), N >= 200", "0.95 to 1.3 (n log n gives about 1.1; two "
                "reference implementations measured 1.09 and 1.14)",
                f"{s:.3f} (" + ", ".join(f"N={N}: {d.loc[N, 'seconds_fft']:.3g} s" for N in SLOPE_N if N in d.index)
                + ")" + missing(d, SLOPE_N), status(0.95 <= s <= 1.3, "WARN", has(d, SLOPE_N))))
    have = has(d, [1600])
    t = d.loc[1600, "seconds_fft"] if have else np.nan
    out.append(("seconds_fft at N = 1600", "under 10 s (measured 2.7 to 4.3 s on a slow 2-core machine)",
                f"{t:.3g} s" if have else "no row at N = 1600", status(t < 10, "WARN", have)))
    have = has(d, [400, 800])
    parts = [f"N={N}: {d.loc[N, 'speedup']:.2f} (fft {d.loc[N, 'seconds_fft']:.3g} s, splu "
             f"{d.loc[N, 'seconds_splu']:.3g} s)" for N in (400, 800) if N in d.index]
    ok = all(d.loc[N, "speedup"] >= 3 for N in (400, 800) if N in d.index)
    out.append(("speedup at N = 400 and 800", "at least 3 (measured 4.6 and 4.4 with complex FFTs; an rfft2 "
                "version was 1.6 to 3.6 times faster still)", ("; ".join(parts) + missing(d, [400, 800]))
                if parts else "no rows", status(ok, "WARN", have)))
    return out


def red_flags(d):
    out = []
    errs = d[["fwd_err_t", "resid_random", "err_vs_splu", "sum_out_first_err", "p123_reldiff"]]
    worst = float(np.nanmax(errs.to_numpy()))
    out.append(("errors of 1e-3 or worse (group, sign or ordering wrong)", f"largest error column entry {worst:.2g}",
                worst < 1e-3))
    f = d["fwd_err_over_eps_kappa"].to_numpy()
    growing = len(f) > 2 and bool((np.diff(f) > 0).all())
    out.append(("fwd_err_over_eps_kappa above 1 or growing steadily with N", ", ".join(f"{v:.3f}" for v in f),
                bool((f <= 1).all()) and not growing))
    fft_cols = d[["seconds_fft", "fwd_err_t", "resid_random", "sum_out_first_err"]].to_numpy()
    out.append(("NaN or inf in the FFT columns (division by sigma(0, 0))",
                "none" if np.isfinite(fft_cols).all() else "found", bool(np.isfinite(fft_cols).all())))
    s = slope(d)
    out.append(("timing slope near 1.5 or 2 (something quadratic)", f"slope {s:.3f}", bool(s < 1.4)))
    out.append(("out of memory at N = 1600 (row missing)", "N = 1600 present" if 1600 in d.index else "missing",
                1600 in d.index))
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


def table(df, first, last):
    data = df.loc[:, first:last]
    lines = ["| " + " | ".join(data.columns) + " |", "|" + "---|" * len(data.columns)]
    return lines + ["| " + " | ".join(fmt(x) for x in row) + " |" for row in data.itertuples(index=False)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    args = parser.parse_args()
    results = pathlib.Path(args.results)
    raw = pd.read_csv(results / "e06_fft.csv", dtype={"min_state": str})
    d = raw.sort_values("N").set_index("N", drop=False)
    checks = run_checks(d)
    flags = red_flags(d)

    m = raw.iloc[0]
    lines = [
        "# Chunk 6 report: FFT fast solver (method of images)",
        "",
        f"Source: `{results / 'e06_fft.csv'}` (git {m['git_hash']}, {m['timestamp']}); {m['platform']}, "
        f"Python {m['python']}, numpy {m['numpy']}, scipy {m['scipy']}, OMP_NUM_THREADS={m['omp_num_threads']}.",
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
    lines += ["", "## Data (e06_fft)", ""] + table(raw.sort_values("N"), "N", "min_state")
    lines += ["", "Figure: `figures/f06_fft.png`.", ""]

    for c, _, o, s in checks:
        print(f"{s:4s}  {c}: {o}")
    for c, o, ok in flags:
        print(f"{'ok' if ok else 'FLAG':4s}  {c}: {o}")
    report = results / "c06_report.md"
    report.write_text("\n".join(lines))
    print(f"wrote {report}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
