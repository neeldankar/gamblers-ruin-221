"""Chunk 5 check: compare results/e05_iterations.csv, e05_omega_sweep.csv and e05_sor_spectra.csv with the
"Expected results" table of plan/c05_stationary.md. Prints one PASS/WARN/FAIL line per table row (plus automatic
red-flag checks) and writes results/c05_report.md.
    python checks/check_c05.py [--results DIR]

Conventions (logged in notes/decisions.md, chunk 5):
  * Each row gets the kind the spec lists when it misses, and also when an N it needs is missing from the CSV
    (for example after a --quick run): never PASS without data.
  * "jacobi: rate_measured / rho_jacobi" and "gauss_seidel ... rate_measured / rho_gs_dense" use every b kind.
  * Fine-grid "best" iterations: the minimum over the fine grid; ties go to the smallest |offset|. "Fewer sweeps"
    is 1 - best / (iterations at offset 0).
  * "rows with omega = 1.00" compare both iterations_ones and iterations_random with the gauss_seidel rows.
  * Count rows: tolerance max(1% of the expected count, 1 sweep).
"""
import argparse
import pathlib
import sys

import numpy as np
import pandas as pd

RTOL = 1e-10
JG_N = [10, 20, 40, 80, 160]
SOR_N = [10, 20, 40, 80, 160, 320, 640]
SWEEP_N = [20, 40, 80]
DENSE_SWEEP_N = [20, 40]
SPECTRA_N = [6, 8, 10, 12, 16, 20, 24, 30, 40, 50, 60, 80, 100]
KINDS = ["ones", "out_first", "random"]

COUNTS = {"jacobi": dict(zip(JG_N, [169, 689, 2769, 11081, 44322])),
          "gauss_seidel": dict(zip(JG_N, [86, 346, 1386, 5542, 22163])),
          "sor": dict(zip(SOR_N, [31, 64, 129, 258, 515, 1030, 2062]))}
RHO_SWEEP = {20: 0.678068809, 40: 0.824609363}
RHO_SOR = {12: 0.517356404, 20: 0.678068809, 30: 0.772896324, 40: 0.824609363, 100: 0.925906019}


def status(ok, kind, have=True):
    return "PASS" if (have and ok) else kind


def missing_text(lost):
    return f" (missing N = {', '.join(map(str, lost))})" if lost else ""


class Iter:
    """Lookup into e05_iterations by (method, b_kind, N)."""

    def __init__(self, df):
        self.df = df
        self.d = df.set_index(["method", "b_kind", "N"])

    def has(self, method, kind, N):
        return (method, kind, N) in self.d.index

    def get(self, method, kind, N, col):
        return self.d.loc[(method, kind, N), col]

    def lost(self, method, Ns, kinds=KINDS):
        return sorted({N for N in Ns for k in kinds if not self.has(method, k, N)})


def iteration_checks(it, spectra):
    out = []
    df = it.df

    def add(name, expected, observed, ok, kind, have):
        out.append((name, expected, observed, status(ok, kind, have)))

    # 1. converged
    lost = it.lost("jacobi", JG_N) + it.lost("gauss_seidel", JG_N) + it.lost("sor", SOR_N)
    bad = df[~df["converged"].astype(bool)]
    add("e05_iterations: converged", "True in every row",
        f"{len(df) - len(bad)} of {len(df)} rows converged" + missing_text(sorted(set(lost))), bad.empty, "FAIL",
        not lost)

    # 2. forward error
    ratio = df["forward_error"] / (df["kappa2"] * RTOL)
    add("forward_error", "at most kappa2 x rtol (a theorem; measured 1e-5 to 0.6 of that bound)",
        f"forward_error / (kappa2 rtol) from {ratio.min():.2g} to {ratio.max():.2g} over {len(df)} rows",
        bool((ratio <= 1).all()), "FAIL", not lost)

    # 3-4. Jacobi bound
    j = df[df["method"] == "jacobi"]
    lost_j = it.lost("jacobi", JG_N)
    excess = j["iterations"] - j["predicted_iterations"]
    add("jacobi: iterations", "at most predicted_iterations + 1 for every N and b (a theorem: Q is symmetric, so "
        "the residual shrinks by at least rho_J per sweep)",
        f"iterations - predicted from {excess.min():.1f} to {excess.max():.2f}" + missing_text(lost_j),
        bool((excess <= 1).all()), "FAIL", not lost_j)
    jo = j[j["b_kind"] == "ones"].sort_values("N")
    lost_jo = it.lost("jacobi", JG_N, ["ones"])
    r = jo["iterations"] / jo["predicted_iterations"]
    ok = bool(((jo["iterations"] >= 0.98 * jo["predicted_iterations"])
               & (jo["iterations"] <= jo["predicted_iterations"] + 1)).all())
    add("jacobi, b = ones: iterations", "between 0.98 x predicted_iterations and predicted_iterations + 1 "
        "(measured 0.990 to 0.9996 of predicted)",
        ", ".join(f"N={N}: {v:.4f}" for N, v in zip(jo["N"], r)) + missing_text(lost_jo), ok, "FAIL", not lost_jo)

    # 5-7. reference counts
    for method, Ns in (("jacobi", JG_N), ("gauss_seidel", JG_N), ("sor", SOR_N)):
        parts, ok = [], True
        for N in Ns:
            if not it.has(method, "ones", N):
                continue
            k, want = int(it.get(method, "ones", N, "iterations")), COUNTS[method][N]
            ok &= abs(k - want) <= max(0.01 * want, 1)
            parts.append(f"N={N}: {k}")
        lost_m = it.lost(method, Ns, ["ones"])
        add(f"b = ones, {method} at N = {', '.join(map(str, Ns))}",
            f"{', '.join(str(COUNTS[method][N]) for N in Ns)} iterations; 1% or 1 sweep, whichever is larger",
            ", ".join(parts) + missing_text(lost_m), ok, "FAIL", not lost_m)

    # 8. GS / Jacobi
    vals = []
    for N in JG_N:
        for k in KINDS:
            if it.has("jacobi", k, N) and it.has("gauss_seidel", k, N):
                vals.append(it.get("gauss_seidel", k, N, "iterations") / it.get("jacobi", k, N, "iterations"))
    lost_gj = sorted(set(it.lost("jacobi", JG_N) + it.lost("gauss_seidel", JG_N)))
    vals = np.array(vals)
    add("gauss_seidel iterations / jacobi iterations (same N and b)", "0.45 to 0.55 (measured 0.497 to 0.529)",
        f"{vals.min():.4f} to {vals.max():.4f} over {len(vals)} pairs" + missing_text(lost_gj),
        bool(((vals >= 0.45) & (vals <= 0.55)).all()), "FAIL", not lost_gj)

    # 9. Jacobi rate
    dev = (j["rate_measured"] / j["rho_jacobi"] - 1).abs()
    add("jacobi: rate_measured / rho_jacobi", "1; 1e-6 (measured within 2e-8)",
        f"max |ratio - 1| = {dev.max():.2g} over {len(j)} rows" + missing_text(lost_j), bool((dev <= 1e-6).all()),
        "FAIL", not lost_j)

    # 10. GS rate vs dense rho_GS
    gsN = [10, 20, 40, 80]
    sp = spectra.set_index("N")
    devs, lost_gs = [], sorted(set(it.lost("gauss_seidel", gsN) + [N for N in gsN if N not in sp.index]))
    for N in gsN:
        if N not in sp.index:
            continue
        for k in KINDS:
            if it.has("gauss_seidel", k, N):
                devs.append(abs(it.get("gauss_seidel", k, N, "rate_measured") / sp.loc[N, "rho_gs_dense"] - 1))
    add("gauss_seidel at N = 10, 20, 40, 80: rate_measured / rho_gs_dense (from e05_sor_spectra)",
        "1; 1e-6 (measured within 6e-8)", f"max |ratio - 1| = {max(devs):.2g} over {len(devs)} rows"
        + missing_text(lost_gs), max(devs) <= 1e-6, "FAIL", not lost_gs)

    # 11-15. SOR
    so = df[(df["method"] == "sor") & (df["b_kind"] == "ones")].sort_values("N")
    lost_so = it.lost("sor", SOR_N, ["ones"])
    r = so["iterations"] / so["predicted_iterations"]
    add("sor, b = ones: iterations / predicted_iterations", "1.0 to 1.15 (measured 1.075 to 1.081)",
        ", ".join(f"N={N}: {v:.3f}" for N, v in zip(so["N"], r)) + missing_text(lost_so),
        bool(((r >= 1.0) & (r <= 1.15)).all()), "FAIL", not lost_so)
    r = so["iterations"] / so["young_predicted_iterations"]
    add("sor, b = ones: iterations / young_predicted_iterations", "at least 1.3 (measured 1.434 to 1.441)",
        ", ".join(f"N={N}: {v:.3f}" for N, v in zip(so["N"], r)) + missing_text(lost_so), bool((r >= 1.3).all()),
        "FAIL", not lost_so)
    e = so["exponent_ratio"]
    add("sor, b = ones: exponent_ratio", "0.75; 0.01 (measured 0.7485 to 0.7502)",
        ", ".join(f"N={N}: {v:.4f}" for N, v in zip(so["N"], e)) + missing_text(lost_so),
        bool(((e - 0.75).abs() <= 0.01).all()), "FAIL", not lost_so)
    sr = df[(df["method"] == "sor") & (df["b_kind"] == "random")].sort_values("N")
    lost_sr = it.lost("sor", SOR_N, ["random"])
    e = sr["exponent_ratio"]
    add("sor, b = random: exponent_ratio", "0.74 to 0.82 (measured 0.761 to 0.790)",
        ", ".join(f"N={N}: {v:.4f}" for N, v in zip(sr["N"], e)) + missing_text(lost_sr),
        bool(((e >= 0.74) & (e <= 0.82)).all()), "WARN", not lost_sr)
    s20 = so[so["N"] >= 20]
    r = s20["iterations"] / s20["N"]
    add("sor, b = ones, N >= 20: iterations / N", "3.0 to 3.4 (measured 3.20 to 3.23)",
        ", ".join(f"N={N}: {v:.3f}" for N, v in zip(s20["N"], r)) + missing_text(lost_so),
        bool(((r >= 3.0) & (r <= 3.4)).all()), "WARN", not lost_so)
    return out


def sweep_checks(sw, it):
    out = []
    fine = sw[sw["grid"] == "fine"]
    lost = [N for N in SWEEP_N if N not in set(sw["N"])]
    lost_dense = [N for N in DENSE_SWEEP_N if N not in set(sw["N"])]

    # 16-17. argmin of rho_dense and its value
    parts, vparts, ok, vok = [], [], True, True
    for N in DENSE_SWEEP_N:
        f = fine[fine["N"] == N]
        if f.empty:
            continue
        best = f.loc[f["rho_dense"].idxmin()]
        ok &= best["offset"] == 0
        parts.append(f"N={N}: offset {best['offset']:+.4f}")
        at0 = f[f["offset"] == 0]
        v = at0["rho_dense"].iloc[0] if len(at0) else np.nan
        vok &= abs(v / RHO_SWEEP[N] - 1) <= 1e-9
        vparts.append(f"N={N}: {v:.9f}")
    out.append(("e05_omega_sweep, N = 20 and 40: argmin of rho_dense on the fine grid", "offset 0 (omega* itself); "
                "exact", ", ".join(parts) + missing_text(lost_dense), status(ok, "FAIL", not lost_dense)))
    out.append(("rho_dense at offset 0", "0.678068809 (N = 20), 0.824609363 (N = 40); 1e-9 relative",
                ", ".join(vparts) + missing_text(lost_dense), status(vok, "FAIL", not lost_dense)))

    # 18. omega = 1.00 rows against Gauss-Seidel
    parts, ok, lost_gs = [], True, []
    for N in SWEEP_N:
        row = sw[(sw["N"] == N) & (sw["grid"] == "coarse") & (np.isclose(sw["omega"], 1.0, atol=1e-12, rtol=0))]
        if row.empty or not (it.has("gauss_seidel", "ones", N) and it.has("gauss_seidel", "random", N)):
            lost_gs.append(N)
            continue
        ko, kr = int(row["iterations_ones"].iloc[0]), int(row["iterations_random"].iloc[0])
        go, gr = int(it.get("gauss_seidel", "ones", N, "iterations")), int(it.get("gauss_seidel", "random", N,
                                                                                   "iterations"))
        ok &= abs(ko - go) <= 1 and abs(kr - gr) <= 1
        parts.append(f"N={N}: ones {ko} vs {go}, random {kr} vs {gr}")
    out.append(("rows with omega = 1.00", "iterations equal the gauss_seidel counts in e05_iterations (same N and b); "
                "1 sweep", "; ".join(parts) + missing_text(lost_gs), status(ok, "FAIL", not lost_gs)))

    # 19-20. best iterations on the fine grid
    for col, expected, check in (
            ("iterations_ones", "at offset 0 to +0.025, with 10% to 20% fewer sweeps than at omega* (measured +0.0175 "
             "and 14% at N = 20, +0.0125 and 16% at N = 40, +0.0075 and 17% at N = 80)",
             lambda off, fewer: -1e-12 <= off <= 0.025 + 1e-12 and 0.10 <= fewer <= 0.20),
            ("iterations_random", "offset within 0.01 of 0, under 5% fewer sweeps (measured +0.005 and 2%, 0 and 0%, "
             "-0.005 and 3%)", lambda off, fewer: abs(off) <= 0.01 + 1e-12 and fewer < 0.05)):
        parts, ok = [], True
        for N in SWEEP_N:
            f = fine[fine["N"] == N]
            if f.empty:
                continue
            best_k = f[col].min()
            ties = f[f[col] == best_k]
            best = ties.loc[ties["offset"].abs().idxmin()]
            k0 = f.loc[f["offset"] == 0, col].iloc[0]
            fewer = 1 - best_k / k0
            ok &= check(best["offset"], fewer)
            parts.append(f"N={N}: {best_k} at {best['offset']:+.4f} vs {k0} at 0 ({100 * fewer:.1f}% fewer)")
        out.append((f"fine grid: best {col}", expected, "; ".join(parts) + missing_text(lost),
                    status(ok, "WARN", not lost)))
    return out


def spectra_checks(sp):
    out = []
    d = sp.set_index("N")
    lost = [N for N in SPECTRA_N if N not in d.index]
    have = not lost

    def every(name, expected, col, ok_fn, fmt="{:.3g}", kind="FAIL"):
        ok = all(ok_fn(d.loc[N, col]) for N in d.index)
        obs = ", ".join(f"N={N}: {fmt.format(d.loc[N, col])}" for N in d.index)
        out.append((name, expected, obs + missing_text(lost), status(ok, kind, have)))

    every("e05_sor_spectra: law_relerr", "0, every N; 1e-10 (measured at most 2.3e-14)", "law_relerr",
          lambda v: v <= 1e-10, "{:.2g}")
    h6 = 6 in d.index
    v6 = d.loc[6, "rho_sor_dense"] if h6 else np.nan
    out.append(("rho_sor_dense at N = 6", "sqrt(5) - 2 = 0.2360679775; 1e-12",
                f"{v6:.13f} (diff {v6 - (np.sqrt(5) - 2):.2g})" if h6 else "no row at N = 6",
                status(abs(v6 - (np.sqrt(5) - 2)) <= 1e-12, "FAIL", h6)))
    lost_r = [N for N in RHO_SOR if N not in d.index]
    ok = all(abs(d.loc[N, "rho_sor_dense"] / v - 1) <= 1e-9 for N, v in RHO_SOR.items() if N in d.index)
    obs = ", ".join(f"N={N}: {d.loc[N, 'rho_sor_dense']:.9f}" for N in RHO_SOR if N in d.index)
    out.append(("rho_sor_dense at N = 12, 20, 30, 40, 100", "0.517356404, 0.678068809, 0.772896324, 0.824609363, "
                "0.925906019; 1e-9 relative", obs + missing_text(lost_r), status(ok, "FAIL", not lost_r)))
    every("sor_over_young", "above 1 for every N (1.618 at N = 6 down to 1.026 at N = 100)", "sor_over_young",
          lambda v: v > 1, "{:.4f}")
    diff = (d["rho_jacobi_dense"] - d["rho_jacobi_formula"]).abs()
    out.append(("abs(rho_jacobi_dense - rho_jacobi_formula)", "0; 1e-12", f"max {diff.max():.2g}" + missing_text(lost),
                status(bool((diff <= 1e-12).all()), "FAIL", have)))
    every("gs_gap", "positive for every N", "gs_gap", lambda v: v > 0, "{:.3g}")
    g = d["gs_gap_times_N4"]
    ok = bool(((g >= 10) & (g <= 20)).all() and (np.diff(g.to_numpy()) > 0).all())
    out.append(("gs_gap_times_N4", "10 to 20 and increasing in N (measured 10.13 at N = 6 up to 19.20 at N = 100)",
                ", ".join(f"N={N}: {v:.3f}" for N, v in g.items()) + missing_text(lost), status(ok, "FAIL", have)))
    h100 = 100 in d.index
    t = d.loc[100, "seconds_dense"] if h100 else np.nan
    out.append(("seconds_dense at N = 100", "under 5 min (2.4 min on the 2-core cloud machine)",
                f"{t:.1f} s" if h100 else "no row at N = 100", status(t < 300, "WARN", h100)))
    return out


def red_flags(it_df, sw, sp):
    out = []
    so = it_df[(it_df["method"] == "sor") & (it_df["b_kind"] == "ones")]
    near_young = so["iterations"] / so["young_predicted_iterations"]
    out.append(("SOR b = ones near Young's count or exponent_ratio near 1 (wrong order, rho_J or stencil)",
                f"iterations / young {near_young.min():.3f} to {near_young.max():.3f}, exponent_ratio "
                f"{so['exponent_ratio'].min():.4f} to {so['exponent_ratio'].max():.4f}",
                bool((near_young > 1.2).all() and (so["exponent_ratio"] < 0.9).all())))
    j = it_df[it_df["method"] == "jacobi"]
    worst_fwd = (it_df["forward_error"] / (it_df["kappa2"] * RTOL)).max()
    worst_j = (j["iterations"] - j["predicted_iterations"]).max()
    out.append(("forward_error above kappa2 x rtol, or a Jacobi count above predicted + 1 (residual not true)",
                f"max fwd / (kappa2 rtol) {worst_fwd:.2g}, max jacobi excess {worst_j:.2f}",
                bool(worst_fwd <= 1 and worst_j <= 1)))
    out.append(("law_relerr well above 1e-12 (iteration_matrix and sweeps disagree)",
                f"max {sp['law_relerr'].max():.2g}", bool((sp["law_relerr"] <= 1e-12).all())))
    fine = sw[(sw["grid"] == "fine") & sw["rho_dense"].notna()]
    offs = [fine.loc[fine[fine["N"] == N]["rho_dense"].idxmin(), "offset"] for N in sorted(set(fine["N"]))]
    out.append(("rho_dense minimum away from offset 0 (young_omega or rho_J wrong)",
                ", ".join(f"{o:+.4f}" for o in offs), all(o == 0 for o in offs)))
    rho_max = sw["rho_dense"].max()
    kmax = max(sw["iterations_ones"].max(), sw["iterations_random"].max())
    out.append(("SOR diverging for some 0 < omega < 2 (impossible for SPD A)",
                f"max rho_dense {rho_max:.6f}, max sweeps {kmax}", bool(rho_max < 1 and kmax < 10 ** 7)))
    j160 = j[j["N"] == 160]["seconds"]
    out.append(("Jacobi at N = 160 taking more than a few minutes (not compiled)",
                f"max {j160.max():.2f} s" if len(j160) else "no N = 160 rows",
                bool(len(j160) and j160.max() < 180)))
    return out


def fmt(x):
    if isinstance(x, (bool, np.bool_)):
        return str(bool(x))
    if isinstance(x, str):
        return x
    if isinstance(x, (int, np.integer)):
        return str(x)
    if isinstance(x, float) and np.isnan(x):
        return ""
    if isinstance(x, float) and x.is_integer() and abs(x) < 1e6:
        return str(int(x))
    return f"{x:.4g}"


def table(df, cols, formats=None):
    formats = formats or {}
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(formats[c].format(row[c]) if c in formats else fmt(row[c]) for c in cols)
                     + " |")
    return lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    args = parser.parse_args()
    results = pathlib.Path(args.results)
    it_df = pd.read_csv(results / "e05_iterations.csv")
    sw = pd.read_csv(results / "e05_omega_sweep.csv")
    sp = pd.read_csv(results / "e05_sor_spectra.csv").sort_values("N")
    it = Iter(it_df)

    checks = iteration_checks(it, sp) + sweep_checks(sw, it) + spectra_checks(sp)
    flags = red_flags(it_df, sw, sp)

    lines = ["# Chunk 5 report: stationary methods and the SOR 3/4 law", ""]
    for name, df in (("e05_iterations", it_df), ("e05_omega_sweep", sw), ("e05_sor_spectra", sp)):
        m = df.iloc[0]
        lines.append(f"- `{results / (name + '.csv')}`: git {m['git_hash']}, {m['timestamp']}")
    m = it_df.iloc[0]
    lines += [f"- {m['platform']}, Python {m['python']}, numpy {m['numpy']}, scipy {m['scipy']}, "
              f"OMP_NUM_THREADS={m['omp_num_threads']}.", "",
              "| Check | Expected | Observed | Status |", "|---|---|---|---|"]
    lines += [f"| {c} | {e} | {o} | {s} |" for c, e, o, s in checks]
    counts = {s: sum(row[3] == s for row in checks) for s in ("PASS", "WARN", "FAIL")}
    lines += ["", f"Summary: {counts['PASS']} PASS, {counts['WARN']} WARN, {counts['FAIL']} FAIL.", "",
              "## Red flags (automatic checks of the spec's list)", "",
              "| Red flag check | Observed | OK |", "|---|---|---|"]
    lines += [f"| {c} | {o} | {'yes' if ok else 'NO'} |" for c, o, ok in flags]

    of = it_df[(it_df["method"] == "sor") & (it_df["b_kind"] == "out_first")].sort_values("N").copy()
    of["iterations_over_young"] = of["iterations"] / of["young_predicted_iterations"]
    lines += ["", "## SOR with b = out_first (printed without a range, as the spec says)", ""]
    lines += table(of, ["N", "iterations", "predicted_iterations", "young_predicted_iterations",
                        "iterations_over_young", "exponent_ratio"],
                   {"iterations_over_young": "{:.3f}", "exponent_ratio": "{:.4f}"})

    lines += ["", "## Data: e05_iterations", ""]
    cols = ["N", "n", "method", "omega", "b_kind", "iterations", "converged", "final_residual",
            "predicted_iterations", "young_predicted_iterations", "rate_measured", "exponent_ratio", "rho_jacobi",
            "kappa2", "forward_error", "seconds"]
    order = {"jacobi": 0, "gauss_seidel": 1, "sor": 2}
    lines += table(it_df.sort_values(["method", "b_kind", "N"], key=lambda s: s.map(order) if s.name == "method"
                                     else s), cols,
                   {"rate_measured": "{:.9f}", "exponent_ratio": "{:.4f}", "predicted_iterations": "{:.1f}",
                    "young_predicted_iterations": "{:.1f}", "omega": "{:.6f}", "rho_jacobi": "{:.9f}"})

    lines += ["", "## Data: e05_omega_sweep (summary rows; all 273 rows are in the CSV)", "",
              "Per N: the coarse row at omega = 1.00, the fine row at offset 0 (omega*), and the fine rows with the "
              "fewest sweeps for b = ones and b = random (ties to the smallest |offset|).", ""]
    picks = []
    for N in sorted(set(sw["N"])):
        s = sw[sw["N"] == N]
        fine = s[s["grid"] == "fine"]
        picks.append(("omega = 1.00", s[(s["grid"] == "coarse") & np.isclose(s["omega"], 1.0, atol=1e-12)].iloc[0]))
        picks.append(("omega*", fine[fine["offset"] == 0].iloc[0]))
        for col, label in (("iterations_ones", "best ones"), ("iterations_random", "best random")):
            ties = fine[fine[col] == fine[col].min()]
            picks.append((label, ties.loc[ties["offset"].abs().idxmin()]))
    summary = pd.DataFrame([{"row": label, **r.to_dict()} for label, r in picks])
    lines += table(summary, ["N", "row", "grid", "omega", "offset", "omega_star", "iterations_ones",
                             "iterations_random", "rho_dense"],
                   {"omega": "{:.6f}", "offset": "{:+.4f}", "omega_star": "{:.6f}", "rho_dense": "{:.9f}"})
    lines += ["", "## Data: e05_sor_spectra", ""]
    lines += table(sp, ["N", "n", "omega_star", "rho_jacobi_formula", "rho_jacobi_dense", "rho_gs_dense", "gs_gap",
                        "gs_gap_times_N4", "rho_sor_dense", "law_value", "young_value", "law_relerr",
                        "sor_over_young", "seconds_dense"],
                   {"omega_star": "{:.9f}", "rho_jacobi_formula": "{:.12f}", "rho_jacobi_dense": "{:.12f}",
                    "rho_gs_dense": "{:.12f}", "gs_gap_times_N4": "{:.3f}", "rho_sor_dense": "{:.12f}",
                    "law_value": "{:.12f}", "young_value": "{:.12f}", "law_relerr": "{:.2g}",
                    "sor_over_young": "{:.4f}", "seconds_dense": "{:.2f}"})
    lines += ["", "Figures: `figures/f05_iterations.png`, `figures/f05_omega.png`.", ""]

    for c, _, o, s in checks:
        print(f"{s:4s}  {c}: {o}")
    for c, o, ok in flags:
        print(f"{'ok' if ok else 'FLAG':4s}  {c}: {o}")
    print(f"Summary: {counts['PASS']} PASS, {counts['WARN']} WARN, {counts['FAIL']} FAIL.")
    report = results / "c05_report.md"
    report.write_text("\n".join(lines))
    print(f"wrote {report}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
