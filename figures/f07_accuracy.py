"""Figure for chunk 7: relative error of the tiny entry (1, 1, N-2) against N, b = out_first_3.

(a) against the true probability (rel_err_tiny): direct (CHOLMOD), gth, ir_direct, cg_componentwise at tol 1e-14
    and cg at rtol 1e-10 (both kind none), with the data-term line (u/4) cond_tiny and guide lines u N and u N^2.
    ir_direct's error is exactly 0 at every N (correctly rounded at N <= 80; at N >= 160 it is the reference), so
    it is drawn hollow at a floor.
(b) against the stored solution (|err_vs_stored_tiny|): direct, cg_componentwise tol 1e-14 and cg rtol 1e-10.
    ir_* and gth are left out: they target the true probability.
Reads results/e07_fixes.csv only.
    python figures/f07_accuracy.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import NullFormatter, ScalarFormatter

U = 2.0 ** -53
FLOOR = 1e-17  # where exact zeros are drawn
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
# (method, param, label, color, marker), categorical slots 1-5 in fixed order (validated: scripts/validate_palette.js)
SERIES = [
    ("direct", None, "direct (CHOLMOD nesdis)", "#2a78d6", "o"),
    ("gth", None, "GTH", "#eb6834", "s"),
    ("ir_direct", None, "refinement (direct)", "#1baf7a", "D"),
    ("cg_componentwise", 1e-14, "CG, stop at omega <= 1e-14", "#eda100", "^"),
    ("cg", 1e-10, "CG, stop at rtol 1e-10", "#e87ba4", "v"),
]


def pick(df, method, param):
    d = df[df["method"] == method]
    if method.startswith("cg"):
        d = d[d["kind"] == "none"]
    if param is not None:
        d = d[np.isclose(d["param"], param, rtol=1e-9, atol=0)]
    return d.sort_values("N")


def style(ax, title, Ns):
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(Ns)
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())  # minor labels collide on a log axis
    ax.set_xlabel("N (chips)", color=INK)
    ax.set_title(title, color=INK, fontsize=10, loc="left")
    ax.grid(color=GRID, linewidth=0.8, which="major")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, which="both")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()
    df = pd.read_csv(pathlib.Path(args.results) / "e07_fixes.csv")
    Ns = np.array(sorted(df["N"].unique()), dtype=float)

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(12, 6.5), dpi=150, sharey=True)

    # (a) against the true probability
    for method, param, label, color, marker in SERIES:
        d = pick(df, method, param)
        if not len(d):
            continue
        y = d["rel_err_tiny"].to_numpy()
        zero = y == 0
        ax_a.plot(d["N"], np.where(zero, FLOOR, y), color=color, linewidth=2, zorder=3)
        ax_a.plot(d["N"][~zero], y[~zero], color=color, marker=marker, markersize=6, linestyle="none", zorder=4)
        ax_a.plot(d["N"][zero], np.full(zero.sum(), FLOOR), color=color, marker=marker, markersize=7,
                  markerfacecolor="white", linestyle="none", zorder=4)
        ax_a.plot([], [], color=color, marker=marker, markersize=6, linewidth=2,  # legend entry
                  markerfacecolor="white" if zero.all() else color,
                  label=label + (": error 0, drawn at 1e-17" if zero.all() else ""))
    dterm = pick(df, "direct", None)
    ax_a.plot(dterm["N"], U / 4 * dterm["cond_tiny"], color=MUTED, linewidth=1.5, linestyle=(0, (5, 2)), zorder=2,
              label="data term (u/4) cond_tiny")
    for power, ls, text in ((1, (0, (1, 2)), "u N"), (2, (0, (3, 1, 1, 1)), "u N$^2$")):
        ax_a.plot(Ns, U * Ns ** power, color=INK, linewidth=1, linestyle=ls, zorder=1, label=f"guide {text}")
    style(ax_a, "(a) against the true probability (exact rationals for N <= 80, refined above)", Ns)
    ax_a.set_ylabel("relative error at the tiny state (1, 1, N-2)", color=INK)
    ax_a.legend(frameon=False, fontsize=7.5, labelcolor=INK, loc="upper left", bbox_to_anchor=(0, -0.12),
                ncol=2).set_in_layout(False)

    # (b) against the stored solution x_ref (1 + data term)
    for method, param, label, color, marker in SERIES:
        if method in ("gth", "ir_direct"):
            continue
        d = pick(df, method, param)
        if len(d):
            ax_b.plot(d["N"], d["err_vs_stored_tiny"].abs(), color=color, marker=marker, markersize=6, linewidth=2,
                      zorder=3, label=label)
    ax_b.plot(Ns, U * Ns ** 2, color=INK, linewidth=1, linestyle=(0, (3, 1, 1, 1)), zorder=1, label="guide u N$^2$")
    style(ax_b, "(b) against the stored solution (what a float solver can reach)", Ns)
    ax_b.legend(frameon=False, fontsize=7.5, labelcolor=INK, loc="upper left", bbox_to_anchor=(0.35, -0.12),
                ncol=1).set_in_layout(False)

    fig.suptitle("P(player 3 out first) at (1, 1, N-2): three fixes for the tiny probability", color=INK,
                 fontsize=11, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.2, 1, 1))  # the bottom band holds the legends
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f07_accuracy.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
