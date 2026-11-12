"""Chunk 7 check: compare results/e07_fixes.csv, e07_structured.csv, e07_baselines.csv (chunk 7b), e07_floor.csv
and (if chunk 6 exists) e07_fft_check.csv with the "Expected results" table of plan/c07_fixes.md. Prints one PASS/WARN/FAIL line per table
row (plus automatic red-flag checks) and writes results/c07_report.md.
    python checks/check_c07.py [--results DIR]

Conventions (logged in notes/decisions.md, chunk 7 and its follow-up):
  * Each row gets the kind the spec lists (FAIL or WARN) when it misses, and also when the rows it needs are
    missing: never PASS without data. A row with kind "WARN/FAIL" is WARN above the first limit, FAIL above the second.
  * "cg rtol 1e-10 ... as in chunk 4": chunk 4's tolerance for N = 640 was [3e-6, 6e-5] around 1.4e-5, i.e. a factor
    1/4.67 to 4.29. The same factor band is applied around the listed values at N = 60 and 160.
  * The cg_componentwise rows use every kind (none, mic0, amg) at tol 1e-14. The err_vs_stored and iteration-ratio
    rows use converged runs only and name the excluded ones. "Converged" passes if every mic0 and amg run converged
    and every none run with N <= 640 did (plain CG stalls above 1e-14 at N = 1280: see e07_floor).
  * e07_floor rows: none min_omega_in_u within a factor 2.5 of the Linux values; none at N = 1280 above 1e-14;
    mic0 and amg at most 90 u at every N; none k_at_min_over_k10 in [1, 3.5].
  * direct err_vs_stored_tiny: |value| < 0.2 N^2 u at every N.
  * ir_direct seconds minus direct seconds is compared with the direct row's setup_seconds (the factor time).
  * e07_fft_check "which solver is off": PASS if at every N the FFT's rel_err_smallest is larger than splu's and
    splu's is within 0.1 N^2 u of ir_direct; "FFT at N = 800": PASS in [1e-8, 1e-4] (chunk 7b).
  * Chunk 7b rows (plan/c07b_review_fixes.md): a row with a list of values needs every listed N present. "Equals
    simplicial / supernodal" compares at the N where both rows exist (no simplicial/supernodal at N = 1280). The
    ir_direct ulp row needs N = 1280. "Within a factor 3" is 1/3 <= value / reference <= 3.
  * Information only, no check row (pre-chunk-11 fixes): e07_fixes `corrections` (ir_* rows) and e07_floor
    `max_x_corner_ratio`, `max_x_inf_ratio`. A CSV written before these columns existed prints "not measured".
"""
import argparse
import pathlib
import sys

import numpy as np
import pandas as pd

U = 2.0 ** -53
DATA_TERM_REF = {80: -6.895e-14, 160: -2.7592e-13, 320: -1.1038e-12, 640: -4.4153e-12, 1280: -1.7661e-11}
GTH_REF = {20: 8, 40: 12, 60: 25, 80: 34, 160: 46, 320: 60, 640: 200}
CG_REF = {60: 5e-8, 160: 6.8e-7, 640: 1.4e-5}
CG_BAND = (3e-6 / 1.4e-5, 6e-5 / 1.4e-5)  # chunk 4's tolerance at N = 640, as a factor
IT_RATIO_REF = {"none": "1.25-1.49", "mic0": "1.36-1.90", "amg": "1.38-1.86"}
PUSH_REF = {10: 3.8512, 20: 4.3001, 40: 4.5250, 80: 4.6375, 160: 4.6937, 320: 4.7219, 640: 4.7359}
STRUCT_N = [10, 20, 40, 80, 160, 320, 640]
KAPPA_REF = dict(zip(STRUCT_N, [11.35295, 23.79933, 48.30309, 97.09688, 194.5739, 389.4719, 779.2398]))
DRIFT_REF = dict(zip(STRUCT_N, [7.50173, 19.49928, 43.77809, 92.45941, 189.8802, 384.7504, 774.5056]))
SYMMETRIC_REF = dict(zip(STRUCT_N, [6.228720, 8.265100, 10.17282, 12.01203, 13.81435, 15.59815, 17.37261]))
BL_N = [20, 40, 80, 160, 320, 640]
BANDED_OWN_REF = dict(zip(BL_N, [28, 45, 40, 108, 496, 2324]))  # banded max_own_err_in_u (Linux)
BANDED_INT_REF = dict(zip(BL_N, [29, 56, 49, 194, 749, 3844]))  # banded_int max_true_err_in_u (Linux)
STORED_METHODS = ["cholmod_default", "cholmod_simplicial", "cholmod_supernodal", "splu_colamd", "splu_natural",
                  "banded"]
FLOOR_REF = {80: 9.9, 160: 17.7, 320: 26.5, 640: 57.4, 1280: 193}  # none, min_omega_in_u (Linux)
KINDS = ["none", "mic0", "amg"]
FFT_800_EXPECTED = "4.8e-7 on the Mac (6e-7 and 2e-6 on two Linux reference implementations); in [1e-8, 1e-4]"
NONE_CONVERGES_UP_TO = 640  # plain CG reaches omega <= 1e-14 up to this N


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


def ref_ok(df, col, ref, rtol):
    """Every reference N present, and each value within rtol of its reference."""
    got = df.set_index("N")[col]
    return all(N in got.index for N in ref) and all(abs(got[N] / v - 1) <= rtol for N, v in ref.items())


def ir_methods(df):
    return [m for m in ("ir_direct", "ir_cg_mic0", "ir_cg_amg") if m in set(df["method"])]


def must_converge(d):
    """Runs the spec expects to reach tol 1e-14: every mic0 and amg run, and plain CG up to N = 640."""
    return (d["kind"] != "none") | (d["N"] <= NONE_CONVERGES_UP_TO)


def excluded_text(d):
    nc = d[~truthy(d["converged"])]
    return (" (excluded, not converged: " + ", ".join(f"N={r.N} {r.kind}" for r in nc.itertuples()) + ")"
            if len(nc) else "")


def run_checks(fx, st, fft, fl, bl):
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
    out.append(("ir_cg_mic0 and ir_cg_amg steps", "3 (N <= 320), 4 (N >= 640); at most 8",
                "; ".join(f"{m}: " + ", ".join(f"N={r.N}: {r.iterations_or_steps:g}" for r in g.itertuples())
                          for m, g in d.groupby("method")) if len(d) else "no rows",
                status(len(d) > 0 and (d["iterations_or_steps"] <= 8).all(), "WARN", len(d) > 0)))

    # 5. gth max_rel_err_in_u
    d = rows(fx, "gth")
    over_n = d[d["max_rel_err_in_u"] >= d["N"]]
    over_10n = d[d["max_rel_err_in_u"] > 10 * d["N"]]
    kind = "FAIL" if len(over_10n) else "WARN"
    out.append(("gth max_rel_err_in_u",
                "8 (20), 12 (40), 25 (60), 34 (80), 46 (160), 60 (320), 200 (640): 0.19-0.42 N; below N; above 10 N "
                "is FAIL",
                ", ".join(f"N={r.N}: {r.max_rel_err_in_u:.1f} u ({r.max_rel_err_in_u / r.N:.2f} N)" for r in d.itertuples())
                if len(d) else "no rows",
                status(len(d) > 0 and over_n.empty, kind, len(d) > 0)))

    # 6. direct max_rel_err_in_u / N^2
    d = rows(fx, "direct")
    ratio = d["max_rel_err_in_u"] / d["N"] ** 2
    out.append(("direct max_rel_err_in_u / N^2 (against the true probability; mostly the data term, 0.097)",
                "Mac: 0.065 for N >= 160, 0.09-0.13 for N <= 80 (37, 190, 428, 848 u at N = 20, 40, 60, 80); the Linux "
                "reference had 39, 267, 431 u at N = 20, 60, 80 (CHOLMOD's own part differs by machine); in [0.02, 0.2]",
                ", ".join(f"N={r.N}: {r.max_rel_err_in_u:.0f} u ({q:.3f})" for r, q in zip(d.itertuples(), ratio))
                if len(d) else "no rows",
                status(len(d) > 0 and ((ratio >= 0.02) & (ratio <= 0.2)).all(), "WARN", len(d) > 0)))

    # 7. direct err_vs_stored_tiny
    lim = 0.2 * d["N"] ** 2 * U
    out.append(("direct err_vs_stored_tiny (the solver's own error)",
                "Mac: +3.8e-16 (20), -4.0e-15 (40), -8.8e-15 (60), -2.5e-14 (80), +9.1e-14 (160), +3.7e-13 (320), "
                "+1.5e-12 (640), +5.7e-12 (1280): +0.032 N^2 u for N >= 160, opposite in sign to the data term; either "
                "sign for N <= 80. Linux reference: -1.1e-14 (80), about +0.05 N^2 u for N >= 160; absolute value below "
                "0.2 N^2 u",
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
                "by a factor growing with N: 25 (80), 37 (160), 112 (320), 133 (640) on the Mac (13 at N = 80 on "
                "Linux); gth smaller at every N >= 80",
                ", ".join(f"N={N}: factor {dr[N] / g[N]:.1f}" for N in common) if common else "no rows",
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
    d160c = d160[truthy(d160["converged"])]
    dirs = rows(fx, "direct").set_index("N")["err_vs_stored_tiny"].abs()
    cmp = [(r.kind, r.N, abs(r.err_vs_stored_tiny), dirs.get(r.N, np.nan)) for r in d160c.itertuples()]
    out.append(("cg_componentwise tol 1e-14: err_vs_stored_tiny, N >= 160, converged runs only",
                "0.05-0.46 of the direct solver's (Mac): none 2.9e-14, 8.0e-14, 3.0e-13; mic0 3.5e-14, 1.0e-13, "
                "6.8e-13, 2.6e-12; amg 4.6e-15, 1.5e-13, 6.2e-13, 1.9e-12 (N = 160, 320, 640, 1280); below the direct "
                "solver's err_vs_stored_tiny at the same N",
                ("; ".join(f"N={N} {k}: {e:.2g} vs direct {de:.2g} ({e / de:.2f})" for k, N, e, de in cmp)
                 + excluded_text(d160)) if cmp else "no rows",
                status(bool(cmp) and all(e < de for _, _, e, de in cmp), "WARN", bool(cmp))))

    # 13. iteration ratio
    parts, ok, have = [], True, False
    for k in KINDS:
        cw = rows(fx, "cg_componentwise", k, 1e-14)
        a = cw[truthy(cw["converged"])].set_index("N")["iterations_or_steps"]
        b = rows(fx, "cg", k, 1e-10).set_index("N")["iterations_or_steps"]
        Ns = [N for N in a.index if N in b.index]
        if not Ns:
            continue
        have = True
        q = {N: a[N] / b[N] for N in Ns}
        ok &= all(1.1 <= v <= 2.5 for v in q.values())
        parts.append(f"{k} (spec {IT_RATIO_REF[k]}): " + ", ".join(f"N={N}: {v:.2f}" for N, v in q.items()))
    out.append(("cg_componentwise iterations / cg rtol 1e-10 iterations, converged runs only (tol 1e-14)",
                "none 1.25-1.49, mic0 1.36-1.90, amg 1.38-1.86; in [1.1, 2.5]",
                ("; ".join(parts) + excluded_text(d)) if parts else "no rows", status(have and ok, "WARN", have)))

    # 14. converged
    nc = d[~truthy(d["converged"])]
    req = d[must_converge(d)]
    req_nc = req[~truthy(req["converged"])]
    out.append(("cg_componentwise tol 1e-14 converged",
                "mic0 and amg at every N up to 1280; none up to N = 640 (not at 1280: see e07_floor)",
                f"{len(d) - len(nc)}/{len(d)} rows converged (N up to {d['N'].max() if len(d) else '-'}); required "
                f"runs: {len(req) - len(req_nc)}/{len(req)}"
                + (f"; not converged: {', '.join(f'N={r.N} {r.kind} (final omega {r.omega / U:.0f} u)' for r in nc.itertuples())}"
                   if len(nc) else ""),
                status(len(req) > 0 and req_nc.empty and d["N"].max() >= 1280, "WARN", len(d) > 0)))

    # 15. ir_direct overhead at N = 640
    a, b = rows(fx, "ir_direct", N=640), rows(fx, "direct", N=640)
    have = len(a) > 0 and len(b) > 0
    if have:
        extra, factor = float(a["seconds"].iloc[0] - b["seconds"].iloc[0]), float(b["setup_seconds"].iloc[0])
        obs = f"ir_direct - direct = {extra:.3f} s, factor {factor:.2f} s ({extra / factor:.0%})"
    out.append(("ir_direct seconds minus direct seconds at N = 640", "about 0.06 s (factor 1.3 s, Mac); under 50% "
                "of the factor time", obs if have else "no rows", status(have and extra < 0.5 * factor, "WARN", have)))

    # 16-17. fft check
    if fft is None:
        msg = "no e07_fft_check.csv (chunk 6's gr.fft_solver is not built yet)"
        out.append(("e07_fft_check: which solver is off at (N-2, 1, 1)", "the FFT (normwise accurate only); splu "
                    "within about 0.1 N^2 u of ir_direct, and near data_term_smallest", msg, "WARN"))
        out.append(("e07_fft_check: FFT rel_err_smallest at N = 800", FFT_800_EXPECTED, msg, "WARN"))
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
        out.append(("e07_fft_check: FFT rel_err_smallest at N = 800", FFT_800_EXPECTED,
                    f"{v:.2g}" if len(ff) else "no row at N = 800",
                    status(len(ff) > 0 and 1e-8 <= v <= 1e-4, "WARN", len(ff) > 0)))

    # 18-28. structured (chunk 7b rows; values from the Project chat's independent Linux code)
    st = st.sort_values("N")
    have = len(st) > 0
    out.append(("structured_cond_tiny, N = 10 ... 640",
                "11.35295, 23.79933, 48.30309, 97.09688, 194.5739, 389.4719, 779.2398; 1e-4 relative",
                ", ".join(f"N={r.N}: {r.structured_cond_tiny:.7g}" for r in st.itertuples()) if have else "no rows",
                status(ref_ok(st, "structured_cond_tiny", KAPPA_REF, 1e-4), "FAIL", have)))
    ok = have and bool(np.allclose(st["structured_cond_max"], st["structured_cond_tiny"], rtol=1e-9, atol=0)) and \
        all(r.structured_argmax_state == str((1, 1, r.N - 2)) for r in st.itertuples())
    out.append(("structured_cond_max and structured_argmax_state",
                "equal to structured_cond_tiny, at (1, 1, N-2); 1e-9 relative; exact",
                ", ".join(f"N={r.N}: {r.structured_cond_max / r.structured_cond_tiny - 1:+.1e} at {r.structured_argmax_state}"
                          for r in st.itertuples()) if have else "no rows", status(ok, "FAIL", have)))
    q = st["structured_cond_over_N"].to_numpy()
    out.append(("structured_cond_over_N",
                "1.1353, 1.1900, 1.2076, 1.2137, 1.2161, 1.2171, 1.2176: increasing, below 1.22; in [1.13, 1.22], "
                "increasing", ", ".join(f"N={r.N}: {r.structured_cond_over_N:.4f}" for r in st.itertuples())
                if have else "no rows",
                status(have and bool(((q >= 1.13) & (q <= 1.22)).all()) and bool((np.diff(q) > 0).all()), "FAIL", have)))
    att = (st["attained_tiny"] / st["structured_cond_tiny"]).to_numpy()
    out.append(("attained_tiny / structured_cond_tiny; attained_max_dev",
                "1; at most 3.5e-6; within 1e-4; below 1e-4",
                ", ".join(f"N={r.N}: {a:.7f}, dev {r.attained_max_dev:.1e}" for r, a in zip(st.itertuples(), att))
                if have else "no rows",
                status(have and bool((np.abs(att - 1) <= 1e-4).all()) and bool((st["attained_max_dev"] < 1e-4).all()),
                       "FAIL", have)))
    co = (st["coherent_tiny"] / (st["N"] - 3)).to_numpy()
    out.append(("coherent_tiny", "N - 3: 7, 17, 37, 77, 157, 317, 637; 1e-4 relative",
                ", ".join(f"N={r.N}: {r.coherent_tiny:.5f}" for r in st.itertuples()) if have else "no rows",
                status(have and bool((np.abs(co - 1) <= 1e-4).all()), "FAIL", have)))
    out.append(("drift_tiny", "7.50173, 19.49928, 43.77809, 92.45941, 189.8802, 384.7504, 774.5056; 1e-4 relative",
                ", ".join(f"N={r.N}: {r.drift_tiny:.7g}" for r in st.itertuples()) if have else "no rows",
                status(ref_ok(st, "drift_tiny", DRIFT_REF, 1e-4), "FAIL", have)))
    out.append(("symmetric_cond_tiny",
                "6.228720, 8.265100, 10.17282, 12.01203, 13.81435, 15.59815, 17.37261 (about 1.8 more per doubling: "
                "log N); 1e-4 relative",
                ", ".join(f"N={r.N}: {r.symmetric_cond_tiny:.7g}" for r in st.itertuples()) if have else "no rows",
                status(ref_ok(st, "symmetric_cond_tiny", SYMMETRIC_REF, 1e-4), "FAIL", have)))
    cq = (st["cond_tiny"] / st["structured_cond_tiny"] / st["N"]).to_numpy()
    out.append(("cond_tiny / structured_cond_tiny / N",
                "0.3289, 0.3232, 0.3208, 0.3198, 0.3193, 0.3191, 0.3190; in [0.31, 0.33]",
                ", ".join(f"N={r.N}: {v:.4f}" for r, v in zip(st.itertuples(), cq)) if have else "no rows",
                status(have and bool(((cq >= 0.31) & (cq <= 0.33)).all()), "FAIL", have)))
    out.append(("structured_random_max", "1.48, 1.96, 2.21, 2.94, 2.41, 2.85, 3.07 (N = 10 ... 640; a max over 20 "
                "draws, not monotone); below 10",
                ", ".join(f"N={r.N}: {r.structured_random_max:.2f}" for r in st.itertuples()) if have else "no rows",
                status(have and bool((st["structured_random_max"] < 10).all()), "FAIL", have)))
    out.append(("structured_push", "3.8512, 4.3001, 4.5250, 4.6375, 4.6937, 4.7219, 4.7359; 1e-3 relative",
                ", ".join(f"N={r.N}: {r.structured_push:.4f}" for r in st.itertuples()) if have else "no rows",
                status(ref_ok(st, "structured_push", PUSH_REF, 1e-3), "WARN", have)))
    rq = (st["structured_cond_max"] / st["structured_random_max"]).to_numpy()
    out.append(("structured_cond_max / structured_random_max", "grows like N: 7.7 (10), 33 (80), 254 (640); above 0.3 N",
                ", ".join(f"N={r.N}: {v:.1f} ({v / r.N:.2f} N)" for r, v in zip(st.itertuples(), rq))
                if have else "no rows",
                status(have and bool((rq > 0.3 * st["N"].to_numpy()).all()), "FAIL", have)))

    # 29-43. e07_baselines (chunk 7b)
    out += baseline_checks(fx, bl)

    # 21-24. e07_floor
    fl = fl if fl is not None else pd.DataFrame(columns=["N", "kind"])
    nf = fl[fl["kind"] == "none"].sort_values("N")
    devs = {r.N: r.min_omega_in_u / FLOOR_REF[r.N] for r in nf.itertuples() if r.N in FLOOR_REF}
    inc = len(nf) > 1 and bool((np.diff(nf["min_omega_in_u"].to_numpy()) > 0).all())
    out.append(("e07_floor, none: min_omega_in_u",
                "increasing in N: 9.9 (80), 17.7 (160), 26.5 (320), 57.4 (640), 193 (1280) on Linux with independent "
                "code; the Mac run log had 312 at 1280; each within a factor 2.5 of these",
                (", ".join(f"N={N}: {v * FLOOR_REF[N]:.1f} u ({v:.2f}x)" for N, v in devs.items())
                 + f"; increasing: {'yes' if inc else 'NO'}") if devs else "no e07_floor rows",
                status(bool(devs) and all(1 / 2.5 <= v <= 2.5 for v in devs.values()), "WARN", bool(devs))))
    r1280 = nf[nf["N"] == 1280]
    v = float(r1280["min_omega"].iloc[0]) if len(r1280) else np.nan
    out.append(("e07_floor, none, N = 1280: min_omega", "above 1e-14 (plain CG cannot reach tol 1e-14 there)",
                f"{v:.3g} ({v / U:.0f} u)" if len(r1280) else "no row at N = 1280",
                status(len(r1280) > 0 and v > 1e-14, "WARN", len(r1280) > 0)))
    pf = fl[fl["kind"].isin(["mic0", "amg"])].sort_values(["kind", "N"])
    out.append(("e07_floor, mic0 and amg: min_omega_in_u",
                "at most 90 at every N (they reach tol 1e-14 in e07_fixes)",
                "; ".join(f"{k}: " + ", ".join(f"N={r.N}: {r.min_omega_in_u:.1f} u" for r in g.itertuples())
                          for k, g in pf.groupby("kind", sort=False)) if len(pf) else "no e07_floor rows",
                status(len(pf) > 0 and bool((pf["min_omega_in_u"] <= 90).all()), "FAIL", len(pf) > 0)))
    out.append(("e07_floor, none: k_at_min_over_k10",
                "1.40, 1.45, 1.49, 1.61, 1.54 (Linux); in [1, 3.5]; above 3.5 means maxiter cut the run before the floor",
                ", ".join(f"N={r.N}: {r.k_at_min_over_k10:.2f}" for r in nf.itertuples()) if len(nf) else "no e07_floor rows",
                status(len(nf) > 0 and bool(nf["k_at_min_over_k10"].between(1, 3.5).all()), "WARN", len(nf) > 0)))
    return out


def baseline_checks(fx, bl):
    """The e07_baselines rows of the Expected table (chunk 7b)."""
    out = []
    if bl is None:
        bl = pd.DataFrame(columns=["N", "method"])

    def m(method):
        return bl[bl["method"] == method].sort_values("N")

    def series(method, col, Ns=None):
        d = m(method)
        if Ns is not None:
            d = d[d["N"].isin(Ns)]
        return d.set_index("N")[col]

    # true - own = data term, for the stored-system methods
    d = bl[bl["method"].isin(STORED_METHODS)].sort_values(["N", "method"])
    dev = ((d["true_err_tiny"] - d["own_err_tiny"]) / d["data_term_tiny"] - 1).abs()
    worst = d.assign(dev=dev).sort_values("dev").iloc[-1] if len(d) else None
    dt = m("cholmod_default").set_index("N")["data_term_tiny"]
    out.append(("baselines, stored-system methods: true_err_tiny - own_err_tiny",
                "= data_term_tiny (-4.270e-15 at N = 20 ... -4.4153e-12 at 640, -1.7661e-11 at 1280); 1e-3 relative",
                (f"{len(d)} rows, worst deviation {worst.dev:.1e} (N={worst.N} {worst.method}); data_term_tiny "
                 + ", ".join(f"N={N}: {v:.5g}" for N, v in dt.items())) if len(d) else "no rows",
                status(len(d) > 0 and bool((dev <= 1e-3).all()), "FAIL", len(d) > 0)))

    # ir_direct within half an ulp
    d = m("ir_direct")
    out.append(("baselines, ir_direct: max_true_err_in_ulp, every N up to 1280",
                "at most 0.5 (correctly rounded; 0.500 in the Project chat's independent refinement); 1e-6",
                ", ".join(f"N={r.N}: {r.max_true_err_in_ulp:.6f}" for r in d.itertuples()) if len(d) else "no rows",
                status(len(d) > 0 and bool((d["max_true_err_in_ulp"] <= 0.5 + 1e-6).all()) and d["N"].max() >= 1280,
                       "FAIL", len(d) > 0)))

    # cholmod_default own error against e07_fixes' direct err_vs_stored_tiny
    own = series("cholmod_default", "own_err_tiny")
    fd = rows(fx, "direct").set_index("N")["err_vs_stored_tiny"]
    Ns = [N for N in own.index if N >= 160 and N in fd.index]
    out.append(("baselines, cholmod_default own_err_tiny against e07_fixes direct err_vs_stored_tiny, N >= 160",
                "equal (same solve, two ways of measuring: exact integers here, x_ref there); 2%",
                ", ".join(f"N={N}: {own[N]:+.4g} vs {fd[N]:+.4g} ({own[N] / fd[N] - 1:+.1e})" for N in Ns)
                if Ns else "no rows",
                status(bool(Ns) and all(abs(own[N] / fd[N] - 1) <= 0.02 for N in Ns), "FAIL", bool(Ns))))

    # gth against e07_fixes
    g = series("gth", "max_true_err_in_u")
    fg = rows(fx, "gth").set_index("N")["max_rel_err_in_u"]
    Ns = [N for N in g.index if N in fg.index]
    out.append(("baselines, gth max_true_err_in_u against e07_fixes gth max_rel_err_in_u",
                "equal; 1.5 u or 2%, whichever is larger",
                ", ".join(f"N={N}: {g[N]:.2f} vs {fg[N]:.2f} u" for N in Ns) if Ns else "no rows",
                status(bool(Ns) and all(abs(g[N] - fg[N]) <= max(1.5, 0.02 * fg[N]) for N in Ns), "FAIL", bool(Ns))))

    # cholmod_default = simplicial (N <= 80) or supernodal (N >= 160)
    simp, sup = series("cholmod_simplicial", "own_err_tiny"), series("cholmod_supernodal", "own_err_tiny")
    parts, ok = [], True
    for N in own.index:
        other, name = (simp, "simplicial") if N <= 80 else (sup, "supernodal")
        if N not in other.index:
            continue
        rel = abs(own[N] / other[N] - 1) if other[N] != 0 else abs(own[N])
        ok &= rel <= 1e-9
        parts.append(f"N={N}: {name} {rel:.1e}")
    out.append(("baselines, cholmod_default own_err_tiny",
                "equals cholmod_simplicial for N <= 80 and cholmod_supernodal for N >= 160 (that switch is the sign "
                "flip between 80 and 160); 1e-9 relative", ", ".join(parts) if parts else "no rows",
                status(bool(parts) and ok, "WARN", bool(parts))))

    def over_n2u_row(method, Nmin, Nmax, expected, test, kind="WARN", label=None):
        v = series(method, "own_err_over_N2u")
        v = v[(v.index >= Nmin) & (v.index <= Nmax)]
        out.append((label or f"baselines, {method} own_err_over_N2u, N >= {Nmin}", expected,
                    ", ".join(f"N={N}: {x:+.4f}" for N, x in v.items()) if len(v) else "no rows",
                    status(len(v) > 0 and all(test(x) for x in v), kind, len(v) > 0)))

    over_n2u_row("cholmod_supernodal", 160, 640, "+0.052, +0.052, +0.050 on Linux; expect +0.032 on the Mac; "
                 "in [0.01, 0.1]", lambda x: 0.01 <= x <= 0.1)
    over_n2u_row("cholmod_simplicial", 160, 640, "-0.0056, -0.0058, -0.0066 on Linux; -0.018 to -0.022 on the Mac; "
                 "absolute value below 0.05", lambda x: abs(x) < 0.05)
    over_n2u_row("banded", 80, 640, "+0.0009, +0.0014, -0.0004, -0.0048 on Linux; absolute value below 0.02",
                 lambda x: abs(x) < 0.02)

    v = series("banded", "max_own_err_in_u")
    have = all(N in v.index for N in BANDED_OWN_REF)
    out.append(("baselines, banded max_own_err_in_u", "28, 45, 40, 108, 496, 2324 on Linux; each within a factor 3",
                ", ".join(f"N={N}: {x:.0f}" for N, x in v.items()) if len(v) else "no rows",
                status(have and all(1 / 3 <= v[N] / r <= 3 for N, r in BANDED_OWN_REF.items()), "WARN", len(v) > 0)))

    over_n2u_row("splu_colamd", 80, 640, "+0.030, +0.031, +0.033, +0.035 on Linux; in [0.005, 0.1]",
                 lambda x: 0.005 <= x <= 0.1)
    over_n2u_row("splu_natural", 160, 320, "-0.067, -0.143 on Linux: natural order does not make SuperLU accurate; "
                 "absolute value above 0.02", lambda x: abs(x) > 0.02,
                 label="baselines, splu_natural own_err_over_N2u, N = 160, 320")

    v = series("banded_int", "max_true_err_in_u")
    have = all(N in v.index for N in BANDED_INT_REF)
    out.append(("baselines, banded_int max_true_err_in_u",
                "29, 56, 49, 194, 749, 3844 on Linux (0.0094 N^2 at N = 640); each within a factor 3",
                ", ".join(f"N={N}: {x:.0f}" for N, x in v.items()) if len(v) else "no rows",
                status(have and all(1 / 3 <= v[N] / r <= 3 for N, r in BANDED_INT_REF.items()), "WARN", len(v) > 0)))

    b = series("banded", "max_true_err_in_u")
    have = 640 in v.index and 640 in b.index
    q = v[640] / b[640] if have else np.nan
    out.append(("baselines, banded_int / banded: max_true_err_in_u at N = 640",
                "0.09 on Linux (integer data removes the data term for a band solve); below 0.5",
                f"{v[640]:.0f} / {b[640]:.0f} = {q:.3f}" if have else "no row at N = 640",
                status(have and q < 0.5, "WARN", have)))

    g = series("gth", "max_true_err_in_u")
    Ns = [N for N in (160, 320, 640) if N in g.index and N in v.index]
    q = [g[N] / v[N] for N in Ns]
    out.append(("baselines, gth / banded_int: max_true_err_in_u at N = 160, 320, 640",
                "0.24, 0.08, 0.05 (Mac GTH over Linux band solve); below 1, decreasing",
                ", ".join(f"N={N}: {g[N]:.0f} / {v[N]:.0f} = {x:.3f}" for N, x in zip(Ns, q)) if Ns else "no rows",
                status(len(Ns) == 3 and all(x < 1 for x in q) and bool((np.diff(q) < 0).all()), "WARN", bool(Ns))))

    v = series("cholmod_int", "true_err_over_N2u")
    v = v[v.index >= 160]
    out.append(("baselines, cholmod_int true_err_over_N2u, N >= 160",
                "+0.18 on Linux: integer scaling does not help CHOLMOD (worse than the data term's 0.097); absolute "
                "value above 0.02", ", ".join(f"N={N}: {x:+.4f}" for N, x in v.items()) if len(v) else "no rows",
                status(len(v) > 0 and all(abs(x) > 0.02 for x in v), "WARN", len(v) > 0)))
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
                f"slope {s:.2f} (the default CHOLMOD solve grows like N^2: slope 2)", bool(s < 1.5)))
    c = rows(fx, "cg_componentwise", param=1e-14)
    req = c[must_converge(c)]
    req_nc = req[~truthy(req["converged"])]
    other = c[~must_converge(c) & ~truthy(c["converged"])]
    out.append(("cg_componentwise with mic0 or amg not reaching tol 1e-14 at some N, or plain CG not reaching it at "
                "N <= 640 (smallest omega: e07_floor)",
                ("all required runs converged" if req_nc.empty else
                 "; ".join(f"N={r.N} {r.kind}: final omega {r.omega:.2e}" for r in req_nc.itertuples()))
                + ("; expected, not required: " + ", ".join(f"N={r.N} {r.kind} (final omega {r.omega / U:.0f} u)"
                                                            for r in other.itertuples()) if len(other) else ""),
                len(req) > 0 and req_nc.empty))
    gr = g[g["N"] >= 160]
    out.append(("refinement landing on the stored solution (N >= 160): GTH, which does not use refinement, must sit "
                "far closer to the refined reference than the data term",
                ", ".join(f"N={r.N}: gth rel_err_tiny {r.rel_err_tiny:.2g} vs |data term| {abs(r.data_term_tiny):.2g}"
                          for r in gr.itertuples()) if len(gr) else "no gth rows at N >= 160",
                len(gr) > 0 and bool((gr["rel_err_tiny"] < 0.1 * gr["data_term_tiny"].abs()).all())))
    q = st["structured_cond_over_N"]
    att = st["attained_tiny"] / st["structured_cond_tiny"]
    co = st["coherent_tiny"] / (st["N"] - 3)
    out.append(("structured_cond_over_N outside [1.1, 1.25], or the attaining perturbation not reaching kappa, or "
                "coherent_tiny not N - 3: the formula or the perturbation is wrong (kappa itself grows like N; that is "
                "the result)",
                f"structured_cond_over_N {q.min():.4f} to {q.max():.4f}; attained / kappa {att.min():.7f} to "
                f"{att.max():.7f}; coherent / (N - 3) {co.min():.6f} to {co.max():.6f}" if len(st) else "no rows",
                len(st) > 0 and bool(q.between(1.1, 1.25).all()) and bool((att >= 1 - 1e-4).all())
                and bool(((co - 1).abs() <= 1e-4).all())))
    cg = fx[fx["method"].isin(["cg", "cg_componentwise"])]
    skip = ((cg["method"] == "cg_componentwise") & np.isclose(cg["param"], 1e-14) & (cg["kind"] == "none")
            & (cg["N"] == 1280))
    cg = cg[~skip]
    nc = cg[~truthy(cg["converged"])]
    out.append(("extra: every CG row converged within maxiter (excluding plain CG, tol 1e-14, N = 1280, which "
                "stalls above the tolerance: see e07_floor)", f"{len(cg) - len(nc)}/{len(cg)} rows", nc.empty))
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


def table_rows(df, cols, blank=False):
    """A markdown table of the named columns (for columns added after a table's last column)."""
    data = df[cols]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    return ([""] if blank else []) + lines + ["| " + " | ".join(fmt(x) for x in row) + " |"
                                              for row in data.itertuples(index=False)]


def info_lines(fx, fl):
    """Printed and reported, never counted: refinement corrections and the plain-CG iterate overshoot."""
    out = []
    if "corrections" in fx.columns:
        ir = fx[fx["method"].str.startswith("ir_")]
        out += [f"e07_fixes N={r.N} {r.method}: corrections {r.corrections}" for r in ir.itertuples()]
    else:
        out.append("e07_fixes corrections: not measured (column absent in this CSV)")
    if fl is not None and {"max_x_corner_ratio", "max_x_inf_ratio"} <= set(fl.columns):
        out += [f"e07_floor N={r.N} {r.kind}: max_x_corner_ratio {r.max_x_corner_ratio:.4f}, "
                f"max_x_inf_ratio {r.max_x_inf_ratio:.4f}" for r in fl.itertuples()]
    else:
        out.append("e07_floor max_x_corner_ratio, max_x_inf_ratio: not measured (column absent in this CSV)")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    args = parser.parse_args()
    results = pathlib.Path(args.results)
    fx = pd.read_csv(results / "e07_fixes.csv")
    st = pd.read_csv(results / "e07_structured.csv")
    fft_path = results / "e07_fft_check.csv"
    fft = pd.read_csv(fft_path) if fft_path.exists() else None
    bl_path = results / "e07_baselines.csv"
    bl = pd.read_csv(bl_path) if bl_path.exists() else None
    floor_path = results / "e07_floor.csv"
    fl = pd.read_csv(floor_path) if floor_path.exists() else None
    checks = run_checks(fx, st, fft, fl, bl)
    flags = red_flags(fx, st)
    info = info_lines(fx, fl)

    sources = [("e07_fixes", fx), ("e07_structured", st)] + ([("e07_baselines", bl)] if bl is not None else []) \
        + ([("e07_floor", fl)] if fl is not None else []) \
        + ([("e07_fft_check", fft)] if fft is not None else [])
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
    lines += ["", "## Information (not checked)", ""] + [f"- {x}" for x in info]
    lines += ["", "## Data (e07_fixes)", ""] + table(fx, "N", "signed_err_tiny")
    lines += ["", "## Data (e07_structured)", ""] + table(st, "N", "draws")
    lines += table_rows(st, ["N", "structured_cond_tiny", "structured_cond_max", "structured_argmax_state",
                             "structured_cond_over_N", "attained_tiny", "attained_max_dev", "coherent_tiny",
                             "drift_tiny", "symmetric_cond_tiny", "cond_tiny"], blank=True)
    if bl is not None:
        lines += ["", "## Data (e07_baselines)", ""] + table(bl, "N", "seconds")
    if fl is not None:
        lines += ["", "## Data (e07_floor)", ""] + table(fl, "N", "final_omega_in_u")
    if fft is not None:
        lines += ["", "## Data (e07_fft_check)", ""] + table(fft, "N", "signed_err_smallest")
    lines.append("")

    for c, _, o, s in checks:
        print(f"{s:4s}  {c}: {o}")
    for c, o, ok in flags:
        print(f"{'ok' if ok else 'FLAG':4s}  {c}: {o}")
    for x in info:
        print(f"info  {x}")
    report = results / "c07_report.md"
    report.write_text("\n".join(lines))
    print(f"wrote {report}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
