"""Chunk 1 check: compare results/e01_conditioning.csv with the "Expected results" table of
plan/c01_spectrum.md. Prints one PASS/WARN/FAIL line per table row and writes results/c01_report.md.
    python checks/check_c01.py [--results DIR]
"""
import argparse
import math
import pathlib
import sys

import pandas as pd

LIMIT = 9 / (8 * math.pi**2)  # 0.1139863
KAPPA2_REF = {10: 11.28, 20: 45.47, 40: 182.25, 80: 729.39, 160: 2917.9, 320: 11672.1}


def status(ok, kind):
    return "PASS" if ok else kind


def run_checks(df):
    """Return a list of (check, expected, observed, status), one per row of the spec's table."""
    out = []
    by_N = df.set_index("N")

    # 1. eigsh agrees with the formula
    e = df.dropna(subset=["lambda_min_eigsh"])
    rel = (e["lambda_min_eigsh"] / e["lambda_min_formula"] - 1).abs()
    ok = len(e) > 0 and rel.max() <= 1e-9
    out.append(("lambda_min_eigsh / lambda_min_formula", "1, 1e-9 relative, every N with eigsh",
                f"max rel err {rel.max():.2e} over N = {list(e['N'])}", status(ok, "FAIL")))

    # 2. kappa2 reference values
    parts, ok = [], True
    for N, want in KAPPA2_REF.items():
        if N not in by_N.index:
            parts.append(f"N={N}: missing")
            ok = False
            continue
        r = abs(by_N.loc[N, "kappa2"] / want - 1)
        ok &= r <= 1e-3
        parts.append(f"N={N}: {by_N.loc[N, 'kappa2']:.6g} ({r:.1e})")
    out.append(("kappa2 at N = 10, 20, 40, 80, 160, 320",
                "11.28, 45.47, 182.25, 729.39, 2917.9, 11672.1, 1e-3 relative", "; ".join(parts),
                status(ok, "FAIL")))

    # 3. kappa2 / N^2 increasing and below the limit
    v = df.sort_values("N")["kappa2_over_N2"]
    ok = bool((v.diff().dropna() > 0).all() and (v < LIMIT).all())
    out.append(("kappa2_over_N2", "increasing in N, below 9/(8 pi^2) = 0.1139863, strict",
                f"min diff {v.diff().min():.3e}, max {v.max():.7f}", status(ok, "FAIL")))

    # 4. kappa2 / N^2 at N = 640
    if 640 in by_N.index:
        val = by_N.loc[640, "kappa2_over_N2"]
        r = abs(val / LIMIT - 1)
        out.append(("kappa2_over_N2 at N = 640", "0.1139863, 1e-5 relative", f"{val:.7f} (rel err {r:.1e})",
                    status(r <= 1e-5, "FAIL")))
    else:
        out.append(("kappa2_over_N2 at N = 640", "0.1139863, 1e-5 relative", "N = 640 missing", "FAIL"))

    # 5. kappa_inf / N^2 = 2/9 when 3 divides N
    d3 = df[df["N"] % 3 == 0]
    rel = (d3["kappa_inf_over_N2"] / (2 / 9) - 1).abs()
    ok = len(d3) > 0 and rel.max() <= 1e-9
    out.append(("kappa_inf_over_N2 when 3 divides N", "2/9 = 0.2222, 1e-9 relative",
                f"max rel err {rel.max():.1e} over N = {list(d3['N'])}" if len(d3) else "no such N",
                status(ok, "FAIL")))

    # 6. kappa_inf / N^2 below 2/9, and within 1% of it for N >= 40, when 3 does not divide N
    nd3 = df[df["N"] % 3 != 0]
    gap = 1 - nd3["kappa_inf_over_N2"] / (2 / 9)  # relative distance below 2/9
    ok = len(nd3) > 0 and (gap > 0).all() and (gap[nd3["N"] >= 40] <= 0.01).all()
    out.append(("kappa_inf_over_N2 when 3 does not divide N", "below 2/9, within 1% of it for N >= 40",
                f"gap below 2/9: {gap.min():.1e} to {gap.max():.1e} (N >= 40: max {gap[nd3['N'] >= 40].max():.1e})",
                status(ok, "FAIL")))

    # 7. kappa_inf / kappa2 near 16 pi^2 / 81 = 1.949
    big = df[df["N"] >= 40]
    ratio = big["kappa_inf"] / big["kappa2"]
    ok = len(big) > 0 and ratio.between(1.9, 2.0).all()
    out.append(("kappa_inf / kappa2", "between 1.9 and 2.0 for N >= 40",
                f"{ratio.min():.4f} to {ratio.max():.4f}", status(ok, "WARN")))

    # 8. Jacobi rate
    err = (df["jacobi_rate"] - (1 - df["lambda_min_formula"])).abs()
    out.append(("jacobi_rate", "1 - lambda_min_formula, 1e-15", f"max abs diff {err.max():.1e}",
                status(err.max() <= 1e-15, "FAIL")))

    # 9. eigsh time at N = 320
    if 320 in by_N.index:
        sec = by_N.loc[320, "seconds_eigsh"]
        out.append(("seconds_eigsh at N = 320", "under 10 s", f"{sec:.3f} s", status(sec < 10, "WARN")))
    else:
        out.append(("seconds_eigsh at N = 320", "under 10 s", "N = 320 missing", "WARN"))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    args = parser.parse_args()
    results = pathlib.Path(args.results)
    df = pd.read_csv(results / "e01_conditioning.csv")
    checks = run_checks(df)

    meta = df.iloc[0]
    lines = [
        "# Chunk 1 report: exact spectrum and conditioning",
        "",
        f"Source: `{results / 'e01_conditioning.csv'}` (git {meta['git_hash']}, {meta['timestamp']}, "
        f"{meta['platform']}, Python {meta['python']}, numpy {meta['numpy']}, scipy {meta['scipy']}, "
        f"OMP_NUM_THREADS={meta['omp_num_threads']}).",
        "",
        "| Check | Expected | Observed | Status |",
        "|---|---|---|---|",
    ]
    lines += [f"| {c} | {e} | {o} | {s} |" for c, e, o, s in checks]
    counts = {s: sum(row[3] == s for row in checks) for s in ("PASS", "WARN", "FAIL")}
    lines += ["", f"Summary: {counts['PASS']} PASS, {counts['WARN']} WARN, {counts['FAIL']} FAIL.", "",
              "## Data", ""]
    data = df.iloc[:, :11]  # the experiment's columns, without the metadata stamp
    lines += ["| " + " | ".join(data.columns) + " |", "|" + "---|" * len(data.columns)]
    lines += ["| " + " | ".join(f"{x:.10g}" for x in row) + " |" for row in data.itertuples(index=False)]
    lines.append("")

    for c, _, o, s in checks:
        print(f"{s:4s}  {c}: {o}")
    report = results / "c01_report.md"
    report.write_text("\n".join(lines))
    print(f"wrote {report}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
