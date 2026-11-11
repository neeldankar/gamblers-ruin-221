"""Chunk 4 check: compare results/e04_condition.csv, e04_errors.csv, e04_perturbation.csv and (chunk 4b)
e04_mechanism_rhs.csv with the "Expected results" table of plan/c04_accuracy.md (which includes the chunk 4b rows
of plan/c04b_review_fixes.md). Prints one PASS/WARN/FAIL line per table row (plus automatic
red-flag checks) and writes results/c04_report.md.
    python checks/check_c04.py [--results DIR]

Conventions:
  * Each row gets the kind the spec lists (FAIL or WARN) when it misses, and also when the rows it needs are
    missing: never PASS without data.
  * N3_x_tiny: the spec gives the 2e-6 relative tolerance for N >= 160; it is applied to the listed values at
    N <= 80 too (they are printed to 7 digits, so rounding is far below 2e-6).
  * "Direct methods" = every row with method != "cg". "Exact-reference rows" = reference == "exact".
  * "max_rel_err <= 2 cond_i omega in every entry" uses the column max_err_over_bound
    = max_i rel_err_i / (2 cond_i max(omega, u)), which must be at most 1.
  * The mic0/amg ratio_tiny_to_prediction row uses every rtol.
  * The two backward-error rows (none: FAIL above 100; mic0 and amg: WARN above 10) both use N >= 80, the range
    the spec gives for plain CG and the sizes its mic0 numbers come from.
  * ratio_tiny_to_prediction for CG none: [0.5, 2] applies at N <= 640, [0.3, 8] at N = 1280 (and above).
  * Red flag "CG converged to 1e-14 with componentwise omega near u" reads "near u" as below 100 u and looks at
    N >= 80 only: at N <= 40, rtol 1e-14 is itself only about 90 u, so a small omega there is expected.
Chunk 4b rows:
  * data_term_tiny: each listed value with 1e-3 relative tolerance, as written. An information-only line also
    compares it with -(u/4) cond_tiny, the exact prediction, which does not depend on printed digits.
  * data_term_over_N2u: within 1% of -0.0971 at every N >= 80.
  * "Exact-reference direct rows" = reference == "exact" and method != "cg" (as above).
  * (N3_x_tiny - C) N^4 comes from e04_condition, out_first_3.
  * Mechanism rows "vs e04_errors" match every out_first_3 row of e04_mechanism_rhs with the e04_errors row of
    CG kind none at the same N and rtol; 1% relative on rel_err at the tiny entry.
  * g_norm: 1e-3 absolute. abs_err_smallest <= residual_bound_abs * (1 + 1e-6).
"""
import argparse
import math
import pathlib
import sys

import numpy as np
import pandas as pd

U = 2.0 ** -53
C = math.gamma(1 / 3) ** 9 / (8 * math.pi ** 4)  # 2c of Diaconis and Ethier (2022), Remark 4
N3_REF = {10: 9.122614, 20: 9.119797, 40: 9.119602, 80: 9.119590}  # N >= 160: 9.119589
COND_REF = {20: 0.3846, 40: 0.3874, 80: 0.3881, 160: 0.3883, 320: 0.3884, 640: 0.3884}
CG_REF = {1e-10: {20: 2.1e-8, 40: 3.7e-8, 80: 2.5e-8, 160: 6.8e-7, 320: 5.8e-6, 640: 1.4e-5},
          1e-14: {160: 7e-12, 320: 4e-10, 640: 1.6e-9}}
DATA_TERM_REF = {10: -1.036e-15, 20: -4.270e-15, 40: -1.7206e-14, 80: -6.895e-14, 160: -2.76e-13, 320: -1.1038e-12,
                 640: -4.4153e-12, 1280: -1.7661e-11}
MECH_RTOLS = [1e-6, 1e-8, 1e-10, 1e-12, 1e-14]


def status(ok, kind, have=True):
    return "PASS" if (have and ok) else kind


def tiny_state(N):
    return str((1, 1, int(N) - 2))


def cg_rows(err, kind=None, rtol=None, N=None):
    d = err[err["method"] == "cg"]
    if kind is not None:
        d = d[d["kind"].isin([kind] if isinstance(kind, str) else kind)]
    if rtol is not None:
        d = d[np.isclose(d["rtol"], rtol, rtol=1e-9, atol=0)]
    if N is not None:
        d = d[d["N"] == N]
    return d


def run_checks(cond, err, pert, mech):
    out = []
    of3 = cond[cond["event"] == "out_first_3"].set_index("N").sort_index()
    o321 = cond[cond["event"] == "order_321"].set_index("N").sort_index()

    # 1. N^3 x_tiny, out_first_3
    devs = {N: of3.loc[N, "N3_x_tiny"] / N3_REF.get(N, 9.119589) - 1 for N in of3.index}
    worst = max(devs, key=lambda N: abs(devs[N])) if devs else None
    out.append(("N3_x_tiny, out_first_3",
                "9.122614 (N=10), 9.119797 (20), 9.119602 (40), 9.119590 (80), 9.119589 (N >= 160); limit "
                "Gamma(1/3)^9 / (8 pi^4) = 9.1195890; 2e-6 relative",
                (", ".join(f"N={N}: {of3.loc[N, 'N3_x_tiny']:.7f}" for N in of3.index)
                 + f"; worst {devs[worst]:+.1e} at N = {worst}") if devs else "no rows",
                status(bool(devs) and all(abs(v) <= 2e-6 for v in devs.values()), "FAIL", bool(devs))))

    # 2. order_321 is half of out_first_3
    common = of3.index.intersection(o321.index)
    rel = (o321.loc[common, "N3_x_tiny"] / (of3.loc[common, "N3_x_tiny"] / 2) - 1).abs()
    v80 = f"; N = 80: {o321.loc[80, 'N3_x_tiny']:.6f}" if 80 in o321.index else ""
    out.append(("N3_x_tiny, order_321 = half of out_first_3", "4.559795 at N = 80; 1e-9 relative",
                f"max relative deviation {rel.max():.1e} over {len(common)} N{v80}" if len(common) else "no rows",
                status(bool(len(common)) and (rel <= 1e-9).all(), "FAIL", bool(len(common)))))

    # 3. argmin and argmax at the tiny state
    bad = [f"N={r.N} {r.event}" for r in cond.itertuples()
           if r.argmin_state != tiny_state(r.N) or r.argmax_cond_state != tiny_state(r.N)]
    out.append(("argmin_state and argmax_cond_state", "(1, 1, N-2) for both events, exact",
                f"{len(cond) - len(bad)}/{len(cond)} rows at (1, 1, N-2)" + (f"; off at {', '.join(bad)}" if bad else ""),
                status(len(cond) > 0 and not bad, "FAIL", len(cond) > 0)))

    # 4. cond_tiny / N^2 values and monotonicity
    s = of3["cond_tiny_over_N2"]
    devs = {N: s[N] - COND_REF[N] for N in COND_REF if N in s.index}
    inc = bool(len(s) > 1 and (np.diff(s.values) > 0).all())
    out.append(("cond_tiny_over_N2", "0.3846, 0.3874, 0.3881, 0.3883, 0.3884, 0.3884 for N = 20 ... 640; "
                "increasing; 1e-3 absolute",
                ", ".join(f"N={N}: {v:.4f}" for N, v in s.items()) + f"; increasing: {'yes' if inc else 'NO'}"
                if len(s) else "no rows",
                status(bool(devs) and all(abs(v) <= 1e-3 for v in devs.values()) and inc, "FAIL", bool(devs))))

    # 5. cond_tiny equal for both events
    rel = (o321.loc[common, "cond_tiny"] / of3.loc[common, "cond_tiny"] - 1).abs()
    out.append(("cond_tiny, order_321 vs out_first_3", "equal; 1e-9 relative",
                f"max relative difference {rel.max():.1e} over {len(common)} N" if len(common) else "no rows",
                status(bool(len(common)) and (rel <= 1e-9).all(), "FAIL", bool(len(common)))))

    # 6. E[T | event] = cond / 2
    rel = (cond["ET_tiny_over_N2"] / (cond["cond_tiny_over_N2"] / 2) - 1).abs()
    out.append(("ET_tiny_over_N2 = cond_tiny_over_N2 / 2", "1e-12 relative",
                f"max relative deviation {rel.max():.1e} over {len(cond)} rows" if len(cond) else "no rows",
                status(len(cond) > 0 and (rel <= 1e-12).all(), "FAIL", len(cond) > 0)))

    # 7. omega_direct
    w = cond["omega_direct"] / U
    out.append(("omega_direct", "3-20 u (8.5 u at N = 160, 17 u at N = 640); below 100 u",
                ", ".join(f"N={r.N} {r.event}: {r.omega_direct / U:.1f} u" for r in cond.itertuples()) or "no rows",
                status(len(w) > 0 and (w < 100).all(), "FAIL", len(w) > 0)))

    # 8. a posteriori bound
    out.append(("aposteriori_bound = max_i (omega_direct + 8u) cond_i",
                "1.5e-11 (160), 8.1e-11 (320), 3.8e-10 (640), 1.8e-9 (1280); below 1e-8",
                ", ".join(f"N={N}: {v:.2g}" for N, v in of3["aposteriori_bound"].items())
                + f"; max over both events {cond['aposteriori_bound'].max():.2g}" if len(cond) else "no rows",
                status(len(cond) > 0 and (cond["aposteriori_bound"] < 1e-8).all(), "FAIL", len(cond) > 0)))

    # 9-10. exact-reference rows, direct methods
    ex = err[(err["reference"] == "exact") & (err["method"] != "cg")]
    out.append(("exact-reference rows, direct methods: max_rel_err", "2e-15 to 8e-14; below 1e-13",
                f"{ex['max_rel_err'].min():.1e} to {ex['max_rel_err'].max():.1e} over {len(ex)} rows "
                f"(N = {', '.join(str(N) for N in sorted(ex['N'].unique()))})" if len(ex) else "no rows",
                status(len(ex) > 0 and (ex["max_rel_err"] < 1e-13).all(), "FAIL", len(ex) > 0)))
    out.append(("exact-reference rows, direct methods: rel_err_i <= 2 cond_i omega in every entry",
                "holds in every entry (max_err_over_bound <= 1)",
                f"max_err_over_bound {ex['max_err_over_bound'].min():.2g} to {ex['max_err_over_bound'].max():.2g} "
                f"over {len(ex)} rows" if len(ex) else "no rows",
                status(len(ex) > 0 and (ex["max_err_over_bound"] <= 1).all(), "FAIL", len(ex) > 0)))

    # 11. CG none, N >= 320, rtol <= 1e-8: ratio in [0.5, 2] for N <= 640, in [0.3, 8] at N = 1280
    d = cg_rows(err, "none")
    d = d[(d["N"] >= 320) & (d["rtol"] <= 1e-8 * (1 + 1e-9))]
    r = d["ratio_tiny_to_prediction"]
    ok = np.where(d["N"] <= 640, r.between(0.5, 2), r.between(0.3, 8))
    out.append(("empirical fit, this right-hand side only: CG none, N >= 320, rtol <= 1e-8: ratio_tiny_to_prediction",
                "0.9-1.6 (at N = 160 it ranges 0.07-1.3); at N = 1280 up to 6 at rtol 1e-8 and 2.1 at 1e-12; "
                "in [0.5, 2] for N <= 640; in [0.3, 8] at N = 1280",
                f"{r.min():.2f} to {r.max():.2f} over {len(d)} rows" + "".join(
                    f"; N={N}: {g['ratio_tiny_to_prediction'].min():.2f}-{g['ratio_tiny_to_prediction'].max():.2f}"
                    for N, g in d.groupby("N")) if len(d) else "no rows",
                status(len(d) > 0 and bool(ok.all()), "WARN", len(d) > 0)))

    # 12. CG none, rtol 1e-6, N = 640
    d = cg_rows(err, "none", 1e-6, 640)
    v = float(d["rel_err_tiny"].iloc[0]) if len(d) else np.nan
    out.append(("CG none, rtol 1e-6, N = 640: rel_err_tiny", "0.63 (ratio about 4); in [0.3, 1.0]",
                f"{v:.3g} (ratio {float(d['ratio_tiny_to_prediction'].iloc[0]):.2f})" if len(d) else "no rows",
                status(0.3 <= v <= 1.0, "WARN", len(d) > 0)))

    # 13. CG mic0 and amg, N >= 160: ratio below 1
    parts, ok, have = [], True, False
    for kind in ("mic0", "amg"):
        d = cg_rows(err, kind)
        d = d[d["N"] >= 160]
        if len(d):
            have = True
            r = d["ratio_tiny_to_prediction"]
            ok &= bool((r < 1).all())
            parts.append(f"{kind} {r.min():.2g} to {r.max():.2g} ({len(d)} rows)")
        else:
            ok = False
            parts.append(f"{kind} no rows")
    out.append(("empirical fit, this right-hand side only: CG mic0 and amg, N >= 160: ratio_tiny_to_prediction", "mic0 0.001-0.03, amg 0.02-0.2; below 1",
                "; ".join(parts), status(ok, "WARN", have)))

    # 14. CG none, rtol 1e-10, N = 640
    d = cg_rows(err, "none", 1e-10, 640)
    v = float(d["rel_err_tiny"].iloc[0]) if len(d) else np.nan
    out.append(("CG none, rtol 1e-10, N = 640: rel_err_tiny", "1.4e-5; in [3e-6, 6e-5]",
                f"{v:.3g}" if len(d) else "no rows", status(3e-6 <= v <= 6e-5, "WARN", len(d) > 0)))

    # 15-16. componentwise / normwise backward error at rtol 1e-10, N >= 80: plain CG (FAIL), mic0 and amg (WARN)
    for kinds, expected, floor, kind_of_miss in [
            (["none"], "above 1e3 for N >= 80 (9.8e3 to 1.2e7 measured); above 100", 100, "FAIL"),
            (["mic0", "amg"], "mic0 15-31 at N = 80-160 (its errors are already componentwise-small), amg 276 and "
                              "up; above 10", 10, "WARN")]:
        d = cg_rows(err, kinds, 1e-10)
        d = d[d["N"] >= 80]
        q = d["componentwise_backward_error"] / d["normwise_backward_error"]
        parts = []
        for k in kinds:
            qk, dk = q[d["kind"] == k], d[d["kind"] == k]
            parts.append(f"{k} {qk.min():.3g} to {qk.max():.3g} (min at N = {int(dk.loc[qk.idxmin(), 'N'])})"
                         if len(qk) else f"{k} no rows")
        label = "CG kind none" if kinds == ["none"] else "CG kinds mic0 and amg"
        out.append((f"{label} at rtol 1e-10, N >= 80: componentwise / normwise backward error", expected,
                    "; ".join(parts) + f" over {len(d)} rows",
                    status(len(d) > 0 and set(d["kind"]) == set(kinds) and (q > floor).all(), kind_of_miss, len(d) > 0)))

    # 16. CG none reaches rtol 1e-14
    d = cg_rows(err, "none", 1e-14).sort_values("N")
    out.append(("CG none, rtol 1e-14 reached (converged) for N <= 1280",
                "yes up to N = 640 (1331 iterations); N = 1280 not measured",
                ", ".join(f"N={r.N}: {'yes' if r.converged else 'NO'} ({int(r.iterations)})" for r in d.itertuples())
                or "no rows", status(len(d) > 0 and d["converged"].astype(bool).all(), "WARN", len(d) > 0)))

    # 17. worst-case perturbation ratio
    small = pert[pert["eps"] <= 1e-8 * (1 + 1e-9)]
    dev = np.maximum((small["worst_ratio_min"] - 1).abs(), (small["worst_ratio_max"] - 1).abs())
    e6 = pert[np.isclose(pert["eps"], 1e-6)]
    out.append(("worst-case perturbation ratio",
                "1.00000 for eps <= 1e-8; up to 1.0015 at eps = 1e-6, N = 80; within 1e-3 for eps <= 1e-8",
                f"eps <= 1e-8: max |ratio - 1| {dev.max():.1e} over {len(small)} rows; eps = 1e-6: "
                f"{e6['worst_ratio_min'].min():.5f} to {e6['worst_ratio_max'].max():.5f}" if len(small) else "no rows",
                status(len(small) > 0 and (dev <= 1e-3).all(), "FAIL", len(small) > 0)))

    # 18. random perturbations
    r = pert["random_max_ratio"]
    out.append(("random perturbation max ratio", "0.24-0.39; below 1 + 1e-3",
                f"{r.min():.3f} to {r.max():.3f} over {len(pert)} rows" if len(pert) else "no rows",
                status(len(pert) > 0 and (r <= 1 + 1e-3).all(), "FAIL", len(pert) > 0)))
    return out + checks_4b(of3, err, mech)


def data_term_devs(of3):
    """Relative deviation of data_term_tiny from the spec's listed values, per N."""
    return {N: of3.loc[N, "data_term_tiny"] / v - 1 for N, v in DATA_TERM_REF.items() if N in of3.index}


def mech_rows(mech, name, N=None):
    d = mech[mech["rhs"] == name]
    return (d if N is None else d[d["N"] == N]).sort_values("rtol", ascending=False)


def ratio_row(mech, name, check, expected, lo, hi):
    """Each ratio_to_cond_rtol at N = 640 for one right-hand side must lie in [lo, hi] (WARN)."""
    d = mech_rows(mech, name, 640)
    r = d["ratio_to_cond_rtol"]
    have = len(d) == len(MECH_RTOLS)
    return (check, expected, ", ".join(f"{v:.3g}" for v in r) + " (rtol 1e-6 ... 1e-14)" if len(d) else "no rows",
            status(bool(r.between(lo, hi).all()), "WARN", have))


def checks_4b(of3, err, mech):
    out = []
    # 4b-1. data_term_tiny against the listed values
    devs = data_term_devs(of3)
    out.append(("data_term_tiny (e04_condition, out_first_3)",
                "-1.036e-15 (10), -4.270e-15 (20), -1.7206e-14 (40), -6.895e-14 (80), -2.76e-13 (160), -1.1038e-12 (320), "
                "-4.4153e-12 (640), -1.7661e-11 (1280); 1e-3 relative",
                ", ".join(f"N={N}: {of3.loc[N, 'data_term_tiny']:.5g} ({devs[N]:+.1e})" for N in devs) if devs else "no rows",
                status(len(devs) == len(DATA_TERM_REF) and all(abs(v) <= 1e-3 for v in devs.values()), "FAIL",
                       bool(devs))))

    # 4b-2. data_term_over_N2u
    s = of3.loc[of3.index >= 80, "data_term_over_N2u"]
    out.append(("data_term_over_N2u", "tends to -0.0971 (= -cond_tiny / (4 N^2)); within 1% for N >= 80",
                ", ".join(f"N={N}: {v:.5f}" for N, v in of3["data_term_over_N2u"].items()) if len(s) else "no rows",
                status(len(s) > 0 and bool(((s / -0.0971 - 1).abs() <= 0.01).all()), "FAIL", len(s) > 0)))

    # 4b-3, 4. exact-reference direct rows: the solver's own error at the tiny entry
    ex = err[(err["reference"] == "exact") & (err["method"] != "cg")]
    se = ex["solver_err_tiny"].abs()
    out.append(("exact-reference direct rows: abs(solver_err_tiny)",
                "4e-17 to 2.5e-14 (N = 80: +2.1e-14 SuperLU, -1.1e-14 CHOLMOD on Linux); below 5e-14",
                f"{se.min():.2g} to {se.max():.2g} over {len(ex)} rows; "
                + ", ".join(f"N={r.N} {r.method}: {r.solver_err_tiny:+.2g}" for r in ex.itertuples()) if len(ex) else "no rows",
                status(len(ex) > 0 and bool((se < 5e-14).all()), "WARN", len(ex) > 0)))
    d = ex[ex["N"].isin([40, 80])]
    ok = (d["solver_err_tiny"].abs() < d["data_term_tiny"].abs())
    out.append(("exact-reference direct rows, N = 40 and 80: abs(solver_err_tiny) < abs(data_term_tiny)", "yes",
                ", ".join(f"N={r.N} {r.method}: {abs(r.solver_err_tiny):.2g} vs {abs(r.data_term_tiny):.2g}"
                          for r in d.itertuples()) if len(d) else "no rows",
                status(len(d) > 0 and bool(ok.all()), "WARN", len(d) > 0)))

    # 4b-5. (N3_x_tiny - C) N^4
    want = [80, 160, 320]
    v = {N: (of3.loc[N, "N3_x_tiny"] - C) * N ** 4 for N in want if N in of3.index}
    out.append(("(N3_x_tiny - C) N^4, N = 80, 160, 320",
                "34.32, 34.37, 34.32 (true values 34.325, 34.375, 34.388; the last is already bent by the solver's "
                "bias); in [34.2, 34.5]",
                ", ".join(f"N={N}: {x:.3f}" for N, x in v.items()) + f" (C = {C:.11f})" if v else "no rows",
                status(len(v) == len(want) and all(34.2 <= x <= 34.5 for x in v.values()), "WARN", bool(v))))

    # 4b-6. a negative probability
    d = cg_rows(err, "none", 1e-6, 1280)
    val = float(d["value_tiny"].iloc[0]) if len(d) else np.nan
    out.append(("CG none, rtol 1e-6, N = 1280: value_tiny", "negative (-4.18e-9 for a probability of +4.35e-9); negative",
                f"{val:.3g} (relative error {float(d['rel_err_tiny'].iloc[0]):.3g})" if len(d) else "no rows",
                status(val < 0, "WARN", len(d) > 0)))

    # 4b-7. mechanism out_first_3 agrees with e04_errors
    m = mech_rows(mech, "out_first_3")
    pairs = []
    for r in m.itertuples():
        e = cg_rows(err, "none", r.rtol, r.N)
        pairs.append((r.N, r.rtol, r.rel_err_smallest, float(e["rel_err_tiny"].iloc[0]) if len(e) else np.nan))
    dev = [abs(a / b - 1) for _, _, a, b in pairs]  # NaN where e04_errors has no matching row
    matched = [x for x in dev if not np.isnan(x)]
    out.append(("mechanism: out_first_3 rows vs e04_errors (same N, rtol)", "same rel_err at the tiny entry; 1%",
                (f"max relative difference {max(matched):.1e}" if matched else "no matching rows")
                + f" over {len(pairs)} (N, rtol) pairs"
                + (f"; {len(dev) - len(matched)} without a match" if len(matched) < len(dev) else ""),
                status(len(pairs) > 0 and all(x <= 0.01 for x in dev), "FAIL", len(pairs) > 0)))

    # 4b-8. the rigorous bound abs_err <= g_norm ||r||
    frac = mech["abs_err_smallest"] / mech["residual_bound_abs"]
    out.append(("mechanism: abs_err_smallest <= residual_bound_abs, every row",
                "holds (observed 4.5e-5 to 2.2e-2 of the bound); 1e-6 relative slack",
                f"abs_err / bound {frac.min():.2g} to {frac.max():.2g} over {len(mech)} rows" if len(mech) else "no rows",
                status(len(mech) > 0 and bool((frac <= 1 + 1e-6).all()), "FAIL", len(mech) > 0)))

    # 4b-9. g_norm
    g = mech["g_norm"]
    out.append(("mechanism: g_norm, every row", "1.1702; 1e-3",
                f"{g.min():.5f} to {g.max():.5f} over {len(mech)} rows (smallest states: "
                f"{', '.join(sorted(mech['smallest_state'].unique()))})" if len(mech) else "no rows",
                status(len(mech) > 0 and bool(((g - 1.1702).abs() <= 1e-3).all()), "FAIL", len(mech) > 0)))

    # 4b-10 to 12. ratios for the other right-hand sides at N = 640
    out.append(ratio_row(mech, "land_mid", "mechanism: land_mid ratio_to_cond_rtol, N = 640",
                         "34, 48, 16, 18, 13 for rtol 1e-6 ... 1e-14; each in [3, 150]", 3, 150))
    out.append(ratio_row(mech, "land_quarter", "mechanism: land_quarter ratio, N = 640",
                         "440, 12, 24, 8.0, 18; each above 3", 3, np.inf))
    out.append(ratio_row(mech, "order_321", "mechanism: order_321 ratio, N = 640",
                         "10.3, 2.4, 1.8, 0.74, 0.38; each in [0.1, 30]", 0.1, 30))

    # 4b-13. median over all states
    d = mech_rows(mech, "out_first_3", 640)
    d = d[np.isclose(d["rtol"].values[:, None], [1e-8, 1e-10, 1e-12], rtol=1e-9, atol=0).any(axis=1)]
    med = d["median_ratio_all_states"]
    out.append(("mechanism: out_first_3 median_ratio_all_states, N = 640",
                "4.0e-4, 1.8e-4, 1.9e-4 at rtol 1e-8, 1e-10, 1e-12; below 0.01",
                ", ".join(f"rtol {r.rtol:g}: {r.median_ratio_all_states:.2g}" for r in d.itertuples()) if len(d) else "no rows",
                status(len(d) == 3 and bool((med < 0.01).all()), "WARN", len(d) > 0)))

    # 4b-14. absolute errors at N = 640, rtol 1e-10
    d = mech_rows(mech, "out_first_3", 640)
    d = d[np.isclose(d["rtol"], 1e-10, rtol=1e-9, atol=0)]
    r = d.iloc[0] if len(d) else None
    out.append(("mechanism: out_first_3, N = 640, rtol 1e-10: absolute errors",
                "corner 5.0e-13, median 1.9e-10, max 1.6e-9; corner below median",
                f"corner {r['abs_err_smallest']:.2g}, median {r['abs_err_median']:.2g}, max {r['abs_err_max']:.2g}"
                if r is not None else "no rows",
                status(r is not None and r["abs_err_smallest"] < r["abs_err_median"], "WARN", r is not None)))
    return out


def red_flags(cond, err, pert, mech):
    """Automatic checks of the spec's red-flag list. Each returns (description, observed, ok)."""
    out = []
    d = err[(err["method"] != "cg") & (err["N"] <= 80)]
    out.append(("direct solver relative error above 1e-12 in any entry at N <= 80",
                f"max {d['max_rel_err'].max():.1e} over {len(d)} rows", bool(len(d) and (d["max_rel_err"] <= 1e-12).all())))
    of3 = cond[cond["event"] == "out_first_3"].set_index("N").sort_index()
    big = of3[of3.index >= 160]
    e = float(np.polyfit(np.log(big.index.values), np.log(big["cond_tiny"].values), 1)[0]) if len(big) > 1 else np.nan
    off = [f"N={r.N} {r.event}" for r in cond.itertuples() if r.argmax_cond_state != tiny_state(r.N)]
    out.append(("cond_tiny grows like N^2 (fitted exponent over N >= 160 in [1.95, 2.05]) and argmax cond at "
                "(1, 1, N-2)", f"exponent {e:.4f}; argmax off the tiny state at {len(off)} rows",
                bool(1.95 <= e <= 2.05 and not off)))
    small = pert[pert["eps"] <= 1e-8 * (1 + 1e-9)]
    dev = np.maximum((small["worst_ratio_min"] - 1).abs(), (small["worst_ratio_max"] - 1).abs())
    out.append(("worst-case ratio not 1 (eps <= 1e-8, beyond 1e-3)", f"max |ratio - 1| {dev.max():.1e}",
                bool(len(small) and (dev <= 1e-3).all())))
    d = cg_rows(err, rtol=1e-14)
    d = d[d["converged"].astype(bool) & (d["N"] >= 80)]  # at N <= 40, rtol 1e-14 is itself only about 90 u
    w = d["componentwise_backward_error"] / U
    out.append(("CG converged to rtol 1e-14 with componentwise backward error near u (read: below 100 u, N >= 80)",
                f"componentwise omega {w.min():.0f} u to {w.max():.3g} u over {len(d)} converged rows "
                f"(min: N = {int(d.loc[w.idxmin(), 'N'])} {d.loc[w.idxmin(), 'kind']})" if len(d) else "no rows",
                bool(len(d) == 0 or (w >= 100).all())))
    # chunk 4b red flags
    of3 = cond[cond["event"] == "out_first_3"].set_index("N").sort_index()
    devs = data_term_devs(of3)
    out.append(("data_term_tiny off by more than 1e-3 from the listed values",
                ", ".join(f"N={N}: {v:+.1e}" for N, v in devs.items()) if devs else "no rows",
                bool(devs) and all(abs(v) <= 1e-3 for v in devs.values())))
    pred = (of3["data_term_tiny"] / (-(U / 4) * of3["cond_tiny"]) - 1).abs()
    out.append(("info: data_term_tiny vs the exact prediction -(u/4) cond_tiny (no printed digits involved; "
                "within 1e-12 relative)", f"max relative deviation {pred.max():.1e} over {len(pred)} N" if len(pred)
                else "no rows", bool(len(pred)) and bool((pred <= 1e-12).all())))
    d = err[(err["reference"] == "exact") & (err["method"] != "cg") & (err["N"] == 80)]
    big = d[d["solver_err_tiny"].abs() > d["data_term_tiny"].abs()]
    out.append(("a solver-only error larger than the data term at N = 80 (tiny entry, direct rows)",
                ", ".join(f"{r.method}: {abs(r.solver_err_tiny):.2g} vs {abs(r.data_term_tiny):.2g}" for r in d.itertuples())
                or "no rows", bool(len(d)) and big.empty))
    frac = mech["abs_err_smallest"] / mech["residual_bound_abs"]
    out.append(("rigorous bound abs_err_smallest <= g_norm ||r||_2 violated (e04_mechanism)",
                f"largest abs_err / bound {frac.max():.2g} over {len(mech)} rows" if len(mech) else "no rows",
                bool(len(mech)) and bool((frac <= 1 + 1e-6).all())))
    d = cg_rows(err)
    nc = d[~d["converged"].astype(bool)]
    out.append(("extra: every CG row converged within maxiter", f"{len(d) - len(nc)}/{len(d)} rows"
                + (f"; not at {', '.join(f'N={r.N} {r.kind} {r.rtol:g}' for r in nc.itertuples())}" if len(nc) else ""),
                nc.empty))
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
    cond = pd.read_csv(results / "e04_condition.csv")
    err = pd.read_csv(results / "e04_errors.csv")
    pert = pd.read_csv(results / "e04_perturbation.csv")
    mech = pd.read_csv(results / "e04_mechanism_rhs.csv")
    checks = run_checks(cond, err, pert, mech)
    flags = red_flags(cond, err, pert, mech)

    src = ", ".join(f"`{results / (name + '.csv')}` (git {df.iloc[0]['git_hash']}, {df.iloc[0]['timestamp']})"
                    for name, df in (("e04_condition", cond), ("e04_errors", err), ("e04_perturbation", pert),
                                     ("e04_mechanism_rhs", mech)))
    m = cond.iloc[0]
    lines = [
        "# Chunk 4 report: accuracy of the tiny probabilities",
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

    # CG kind none vs the spec's reference numbers
    lines += ["", "## CG (kind none, out_first_3): rel_err_tiny observed (reference)", "",
              "| rtol | " + " | ".join(f"N={N}" for N in sorted(err["N"].unique())) + " |",
              "|---|" + "---|" * err["N"].nunique()]
    for rtol in (1e-6, 1e-8, 1e-10, 1e-12, 1e-14):
        cells = []
        for N in sorted(err["N"].unique()):
            d = cg_rows(err, "none", rtol, N)
            ref = CG_REF.get(rtol, {}).get(N)
            cells.append((f"{float(d['rel_err_tiny'].iloc[0]):.2g}" if len(d) else "") + (f" ({ref:g})" if ref else ""))
        lines.append(f"| {rtol:g} | " + " | ".join(cells) + " |")

    lines += ["", "## Data (e04_condition)", ""] + table(cond, "N", "data_term_over_N2u")
    lines += ["", "## Data (e04_perturbation)", ""] + table(pert, "N", "draws")
    lines += ["", "## Data (e04_errors)", ""] + table(err, "N", "at_reference_accuracy")
    lines += ["", "## Data (e04_mechanism_rhs)", ""] + table(mech, "N", "q90_ratio_all_states")
    lines.append("")

    for c, _, o, s in checks:
        print(f"{s:4s}  {c}: {o}")
    for c, o, ok in flags:
        print(f"{'ok' if ok else 'FLAG':4s}  {c}: {o}")
    report = results / "c04_report.md"
    report.write_text("\n".join(lines))
    print(f"wrote {report}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
