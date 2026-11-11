"""Chunk 2 check: compare results/e02_direct.csv with the "Expected results" table of plan/c02_direct.md.
Prints one PASS/WARN/FAIL line per table row (plus a few automatic red-flag checks) and writes
results/c02_report.md.
    python checks/check_c02.py [--results DIR]

Conventions:
  * An exponent is the least-squares slope of log y against log n over every row in the stated N range
    (for two sizes this is the endpoint slope).
  * "Natural orders" are splu NATURAL and cholmod natural, the two orders the spec's envelope formula names.
  * If the rows a check needs are missing, the check gets its own kind (WARN or FAIL), never PASS.
"""
import argparse
import pathlib
import sys

import numpy as np
import pandas as pd

U = 2.0**-53
NATURAL = [("splu", "NATURAL"), ("cholmod", "natural")]


def natural_fill(N):
    n = (N - 1) * (N - 2) // 2
    return n + (N - 3) + (N - 1) * (N - 2) * (N - 3) // 3


def band_fill(N):
    n, p = (N - 1) * (N - 2) // 2, N - 2
    return n * (p + 1) - p * (p + 1) // 2


def rows_of(df, method, ordering, lo=None, hi=None, col=None):
    d = df[(df["method"] == method) & (df["ordering"] == ordering)]
    if lo is not None:
        d = d[(d["N"] >= lo) & (d["N"] <= hi)]
    if col is not None:
        d = d.dropna(subset=[col])
    return d.sort_values("N")


def slope(d, col):
    """Least-squares slope of log(col) vs log(n); NaN if fewer than two rows."""
    if len(d) < 2:
        return np.nan
    return float(np.polyfit(np.log(d["n"]), np.log(d[col]), 1)[0])


def value(df, method, ordering, N, col):
    d = df[(df["method"] == method) & (df["ordering"] == ordering) & (df["N"] == N)]
    return float(d[col].iloc[0]) if len(d) else np.nan


def exponent_check(df, label, pairs, lo, hi, col, ok_fn, expected, kind):
    parts, ok = [], True
    for method, ordering in pairs:
        d = rows_of(df, method, ordering, lo, hi, col)
        s = slope(d, col)
        good = len(d) >= 2 and ok_fn(s)
        ok &= good
        rng = f"N={int(d['N'].min())}-{int(d['N'].max())}" if len(d) else "no rows"
        parts.append(f"{ordering}: {s:.3f} ({rng})")
    return (label, expected, "; ".join(parts), "PASS" if ok else kind)


def run_checks(df):
    """Return a list of (check, expected, observed, status), one per row of the spec's table."""
    out = []

    # 1. banded fill formula, exact
    d = rows_of(df, "banded_cholesky", "natural")
    bad = [int(N) for N, v in zip(d["N"], d["nnz_factor"]) if int(v) != band_fill(int(N))]
    out.append(("nnz_factor, banded", "n(p+1) - p(p+1)/2, p = N - 2, exact",
                f"{len(d) - len(bad)}/{len(d)} rows exact" + (f"; off at N = {bad}" if bad else ""),
                "PASS" if len(d) and not bad else "FAIL"))

    # 2. natural-order envelope formula, exact
    parts, ok = [], True
    for method, ordering in NATURAL:
        d = rows_of(df, method, ordering)
        bad = [int(N) for N, v in zip(d["N"], d["nnz_chol_equiv"]) if v != natural_fill(int(N))]
        ok &= len(d) > 0 and not bad
        parts.append(f"{method} {ordering}: {len(d) - len(bad)}/{len(d)} exact" + (f", off at N = {bad}" if bad else ""))
    v400 = value(df, "cholmod", "natural", 400, "nnz_chol_equiv")
    parts.append(f"N=400: {v400:,.0f}")
    out.append(("nnz_chol_equiv, splu NATURAL and cholmod natural",
                "n + (N-3) + (N-1)(N-2)(N-3)/3 (N=400: 21,094,596), exact", "; ".join(parts),
                "PASS" if ok else "FAIL"))

    # 3. natural / banded at N = 400
    band = value(df, "banded_cholesky", "natural", 400, "nnz_factor")
    parts, ok = [], not np.isnan(band)
    for method, ordering in NATURAL:
        r = value(df, method, ordering, 400, "nnz_chol_equiv") / band
        ok &= abs(r - 0.6675) <= 0.005
        parts.append(f"{method} {ordering}: {r:.4f}")
    out.append(("natural / banded nnz at N = 400", "0.6675 (tends to 2/3), tolerance 0.005", "; ".join(parts),
                "PASS" if ok else "FAIL"))

    # 4-6. fill exponents
    out.append(exponent_check(df, "fill exponent, natural orders, N = 100-400", NATURAL, 100, 400,
                              "nnz_chol_equiv", lambda s: abs(s - 1.50) <= 0.03, "1.50, tolerance 0.03", "FAIL"))
    out.append(exponent_check(df, "fill exponent, metis, nesdis, MMD_AT_PLUS_A, N = 400-1600",
                              [("cholmod", "metis"), ("cholmod", "nesdis"), ("splu", "MMD_AT_PLUS_A")], 400, 1600,
                              "nnz_chol_equiv", lambda s: 1.03 <= s <= 1.22, "1.10-1.14, in [1.03, 1.22]", "WARN"))
    out.append(exponent_check(df, "fill exponent, amd, COLAMD, MMD_ATA, N = 400-1200 or 1600",
                              [("cholmod", "amd"), ("splu", "COLAMD"), ("splu", "MMD_ATA")], 400, 1600,
                              "nnz_chol_equiv", lambda s: 1.08 <= s <= 1.30, "1.16-1.23, in [1.08, 1.30]", "WARN"))

    # 7-9. flops exponents
    out.append(exponent_check(df, "flops exponent, natural orders, N = 100-400", NATURAL, 100, 400, "flops",
                              lambda s: abs(s - 2.00) <= 0.05, "2.00, tolerance 0.05", "FAIL"))
    out.append(exponent_check(df, "flops exponent, metis and nesdis, N = 100-800",
                              [("cholmod", "metis"), ("cholmod", "nesdis")], 100, 800, "flops",
                              lambda s: 1.40 <= s <= 1.65, "1.53, in [1.40, 1.65]", "WARN"))
    out.append(exponent_check(df, "flops exponent, amd, N = 100-800", [("cholmod", "amd")], 100, 800, "flops",
                              lambda s: 1.55 <= s <= 1.80, "1.68, in [1.55, 1.80]", "WARN"))

    # 10-12. fill ratios at N = 1200
    metis = value(df, "cholmod", "metis", 1200, "nnz_factor")
    for label, num, lo, hi, exp in [
        ("nnz at N = 1200: amd / metis", value(df, "cholmod", "amd", 1200, "nnz_factor"), 1.15, 1.65,
         "1.40, in [1.15, 1.65]"),
        ("nnz at N = 1200: (MMD_AT_PLUS_A / 2) / metis", value(df, "splu", "MMD_AT_PLUS_A", 1200, "nnz_factor") / 2,
         0.85, 1.15, "0.98, in [0.85, 1.15]"),
        ("nnz at N = 1200: (COLAMD / 2) / metis", value(df, "splu", "COLAMD", 1200, "nnz_factor") / 2, 1.8, 3.0,
         "2.41, in [1.8, 3.0]"),
    ]:
        r = num / metis
        out.append((label, exp, f"{r:.3f}", "PASS" if lo <= r <= hi else "WARN"))

    # 13. forward error relative to kappa_inf u
    d = df[df["N"] >= 100]
    e = d["err_over_kappa_u"]
    worst = d.loc[e.idxmax()] if len(d) else None
    status = "FAIL" if (not len(d) or (e > 10).any()) else ("PASS" if e.between(0.02, 1).all() else "WARN")
    n_out = int((~e.between(0.02, 1)).sum())
    out.append(("err_over_kappa_u, every row with N >= 100", "0.07-0.33; in [0.02, 1] WARN; above 10 FAIL",
                f"{e.min():.3f} to {e.max():.3f} over {len(d)} rows ({n_out} outside [0.02, 1]; max at N = "
                f"{int(worst['N'])} {worst['method']} {worst['ordering']})" if len(d) else "no rows", status))

    # 14. backward error
    be = df["backward_error"]
    status = "FAIL" if (be > 1e-13).any() else ("WARN" if (be > 50 * U).any() else "PASS")
    out.append(("backward_error, every row", "2-15 u (2e-16 to 2e-15); above 50 u WARN; above 1e-13 FAIL",
                f"{be.min():.2e} to {be.max():.2e} = {be.min() / U:.1f} to {be.max() / U:.1f} u over {len(df)} rows",
                status))

    # 15. solve / setup ratio
    d = df[df["method"].isin(["splu", "cholmod"]) & (df["N"] >= 400)]
    r = d["solve_time"] / d["setup_time"]
    worst = d.loc[r.idxmax()] if len(d) else None
    out.append(("solve_time / setup_time, splu and cholmod, N >= 400", "0.01-0.04, below 0.1",
                f"{r.min():.4f} to {r.max():.4f} over {len(d)} rows (max at N = {int(worst['N'])} "
                f"{worst['method']} {worst['ordering']})" if len(d) else "no rows",
                "PASS" if len(d) and (r < 0.1).all() else "WARN"))

    # 16. setup time, cholmod amd at N = 1200
    s = value(df, "cholmod", "amd", 1200, "setup_time")
    out.append(("setup_time, cholmod amd, N = 1200", "about 11 s on the reference, 2-30 s", f"{s:.2f} s",
                "PASS" if 2 <= s <= 30 else "WARN"))

    # 17. setup time exponent, cholmod nesdis
    out.append(exponent_check(df, "setup_time exponent, cholmod nesdis, N = 400-1600", [("cholmod", "nesdis")],
                              400, 1600, "setup_time", lambda s: 1.0 <= s <= 1.7, "about 1.24, in [1.0, 1.7]",
                              "WARN"))
    return out


def red_flags(df):
    """Automatic checks for the spec's red-flag list. Each returns (description, observed, ok)."""
    out = []
    # splu fill exactly twice the Cholesky count for the same order (only NATURAL is shared with CHOLMOD)
    s = rows_of(df, "splu", "NATURAL").set_index("N")["nnz_factor"]
    c = rows_of(df, "cholmod", "natural").set_index("N")["nnz_factor"]
    common = s.index.intersection(c.index)
    bad = [int(N) for N in common if s[N] != 2 * c[N]]
    out.append(("splu NATURAL nnz = 2 x cholmod natural nnz", f"{len(common) - len(bad)}/{len(common)} sizes exact",
                len(common) > 0 and not bad))
    # no fill-reducing order worse than natural at the same N
    nat = c
    worse = []
    for (method, ordering), d in df.groupby(["method", "ordering"]):
        if ordering.lower() == "natural":
            continue
        for N, v in zip(d["N"], d["nnz_chol_equiv"]):
            if N in nat.index and v >= nat[N]:
                worse.append(f"{method} {ordering} N={int(N)}")
    out.append(("every fill-reducing order beats natural where both ran",
                "none worse" if not worse else ", ".join(worse), not worse))
    # forward error growing faster than N^2: slope of log (max forward_error at each N) vs log N
    f = df.groupby("N")["forward_error"].max()
    g = float(np.polyfit(np.log(f.index), np.log(f.values), 1)[0]) if len(f) > 1 else np.nan
    out.append(("forward error grows no faster than N^2", f"slope of log max forward_error vs log N: {g:.2f}",
                bool(g <= 2.1)))
    # backward error growing faster than sqrt(n) u: compare max backward error per N
    m = df.groupby("n")["backward_error"].max()
    gb = float(np.polyfit(np.log(m.index), np.log(m.values), 1)[0]) if len(m) > 1 else np.nan
    out.append(("backward error grows no faster than sqrt(n) u", f"slope of log max backward_error vs log n: {gb:.2f}",
                bool(gb <= 0.5)))
    # err_over_kappa_u above 1 anywhere
    e = df["err_over_kappa_u"].max()
    out.append(("err_over_kappa_u never above 1", f"max {e:.3f}", bool(e <= 1)))
    return out


def fmt(x):
    if isinstance(x, str):
        return x
    if isinstance(x, (int, np.integer)):
        return str(x)
    return f"{x:.6g}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    args = parser.parse_args()
    results = pathlib.Path(args.results)
    df = pd.read_csv(results / "e02_direct.csv")
    checks = run_checks(df)
    flags = red_flags(df)

    meta = df.iloc[0]
    lines = [
        "# Chunk 2 report: direct solvers, fill-in and orderings",
        "",
        f"Source: `{results / 'e02_direct.csv'}` (git {meta['git_hash']}, {meta['timestamp']}, "
        f"{meta['platform']}, Python {meta['python']}, numpy {meta['numpy']}, scipy {meta['scipy']}, "
        f"OMP_NUM_THREADS={meta['omp_num_threads']}).",
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

    # fill table in the spec's layout, for comparing with the reference by eye
    order_cols = [("cholmod", "natural", "natural"), ("splu", "COLAMD", "COLAMD"), ("splu", "MMD_ATA", "MMD_ATA"),
                  ("splu", "MMD_AT_PLUS_A", "MMD_AT_PLUS_A"), ("cholmod", "amd", "amd"),
                  ("cholmod", "metis", "metis"), ("cholmod", "nesdis", "nesdis")]
    lines += ["", "## Fill counts (nnz_chol_equiv)", "",
              "| N | n | " + " | ".join(c[2] for c in order_cols) + " |", "|" + "---|" * (2 + len(order_cols))]
    for N in sorted(df["N"].unique()):
        n = int(df.loc[df["N"] == N, "n"].iloc[0])
        cells = [value(df, m, o, N, "nnz_chol_equiv") for m, o, _ in order_cols]
        lines.append(f"| {N} | {n:,} | " + " | ".join("" if np.isnan(v) else f"{v:,.0f}" for v in cells) + " |")

    lines += ["", "## Data", ""]
    data = df.loc[:, "N":"memory_MB_est"]  # the experiment's columns, without the metadata stamp
    lines += ["| " + " | ".join(data.columns) + " |", "|" + "---|" * len(data.columns)]
    lines += ["| " + " | ".join(fmt(x) for x in row) + " |" for row in data.itertuples(index=False)]
    lines.append("")

    for c, _, o, s in checks:
        print(f"{s:4s}  {c}: {o}")
    for c, o, ok in flags:
        print(f"{'ok' if ok else 'FLAG':4s}  {c}: {o}")
    report = results / "c02_report.md"
    report.write_text("\n".join(lines))
    print(f"wrote {report}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
