"""Figure for chunk 9: four-player solvers against n, log-log.

(a) setup_s + solve_s, (b) peak_rss_mb (each run in its own process), one line per method, dashed n^1 and n^2
guides. Runs stopped by the memory rules are left out. Reads results/e09_solvers.csv only.
    python figures/f09_solvers.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
import numpy as np
import pandas as pd

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
STYLE = {  # method -> (color, marker, linestyle, label)
    "splu": ("#1baf7a", "s", "--", "SuperLU, COLAMD"),
    "splu_mmd": ("#1baf7a", "^", "-.", "SuperLU, MMD_AT_PLUS_A"),
    "cholmod": ("#eda100", "o", "-", "CHOLMOD, METIS"),
    "amg_cg": ("#2a78d6", "D", "-", "CG + smoothed-aggregation AMG"),
}


def guide(ax, n, power, anchor_n, anchor_y, label):
    """Dashed grey guide c * n^power through (anchor_n, anchor_y), labelled at its right end."""
    y = anchor_y * (n / anchor_n) ** power
    ax.plot(n, y, color=MUTED, linestyle=(0, (4, 3)), linewidth=1, zorder=1)
    ax.annotate(label, xy=(n[-1], y[-1]), xytext=(3, 0), textcoords="offset points", color=MUTED, fontsize=8,
                va="center")


def panel(ax, df, col, title, ylabel):
    for method, (color, marker, ls, label) in STYLE.items():
        d = df[df["method"] == method].sort_values("n")
        if d.empty:
            continue
        ax.plot(d["n"], d[col], color=color, marker=marker, linestyle=ls, linewidth=2, markersize=6,
                markeredgecolor="white", markeredgewidth=1, label=label, zorder=3)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("n (live states)", color=INK)
    ax.set_ylabel(ylabel, color=INK)
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

    df = pd.read_csv(pathlib.Path(args.results) / "e09_solvers.csv")
    df = df[df["status"].str.startswith("ok")].copy()
    df["total_s"] = df["setup_s"] + df["solve_s"]
    n = np.geomspace(df["n"].min(), df["n"].max(), 50)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), dpi=150)
    panel(axes[0], df, "total_s", "(a) setup + solve time (right-hand side e2)", "seconds")
    first = df.sort_values("n").groupby("method").first()
    if "amg_cg" in first.index:
        guide(axes[0], n, 1, first.loc["amg_cg", "n"], first.loc["amg_cg", "total_s"], r"$n$")
    if "cholmod" in first.index:
        guide(axes[0], n, 2, first.loc["cholmod", "n"], first.loc["cholmod", "total_s"], r"$n^2$")
    panel(axes[1], df, "peak_rss_mb", "(b) peak resident memory of the run's process", "MB")
    last = df.sort_values("n").groupby("method").last()  # memory: anchor at the largest run, past the
    if "amg_cg" in last.index:                            # fixed cost of a Python process with its libraries
        guide(axes[1], n, 1, last.loc["amg_cg", "n"], last.loc["amg_cg", "peak_rss_mb"], r"$n$")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, fontsize=9, labelcolor=INK)
    fig.tight_layout(rect=(0, 0.08, 1, 1))

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f09_solvers.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
