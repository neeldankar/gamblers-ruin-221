"""Figure for chunk 2: fill, flops and setup time of the direct solvers against n, log-log.

(a) nnz_chol_equiv with guides n^{3/2} and n log n; (b) flops with guides n^2 and n^{3/2}; (c) setup_time.
Color = method family, marker and line style = ordering. Reads results/e02_direct.csv only.
    python figures/f02_direct.py [--results DIR] [--outdir DIR]
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
FAMILY_COLOR = {"dense_cholesky": "#2a78d6", "banded_cholesky": "#eb6834", "splu": "#1baf7a", "cholmod": "#eda100"}
STYLE = {  # ordering -> (marker, linestyle)
    "natural": ("o", "-"), "NATURAL": ("o", "-"),
    "COLAMD": ("s", "--"), "MMD_ATA": ("D", "--"), "MMD_AT_PLUS_A": ("^", "-."),
    "amd": ("s", "-"), "metis": ("v", "-"), "nesdis": ("^", "-"),
}
SERIES = [("dense_cholesky", "natural"), ("banded_cholesky", "natural"), ("splu", "NATURAL"), ("splu", "COLAMD"),
          ("splu", "MMD_ATA"), ("splu", "MMD_AT_PLUS_A"), ("cholmod", "natural"), ("cholmod", "amd"),
          ("cholmod", "metis"), ("cholmod", "nesdis")]


def guide(ax, n, f, anchor_n, anchor_y, label):
    """Dashed grey guide c * f(n) through (anchor_n, anchor_y), labelled at its right end."""
    y = anchor_y * f(n) / f(anchor_n)
    ax.plot(n, y, color=MUTED, linestyle=(0, (4, 3)), linewidth=1, zorder=1)
    ax.annotate(label, xy=(n[-1], y[-1]), xytext=(3, 0), textcoords="offset points", color=MUTED,
                fontsize=8, va="center")


def panel(ax, df, col, title, ylabel):
    for method, ordering in SERIES:
        d = df[(df["method"] == method) & (df["ordering"] == ordering)].dropna(subset=[col]).sort_values("n")
        if d.empty:
            continue
        marker, ls = STYLE[ordering]
        ax.plot(d["n"], d[col], color=FAMILY_COLOR[method], marker=marker, linestyle=ls, linewidth=2,
                markersize=6, markeredgecolor="white", markeredgewidth=1, label=f"{method} {ordering}", zorder=3)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.xaxis.set_minor_formatter(NullFormatter())  # minor labels collide on a log axis
    ax.set_xlabel("n (live states)", color=INK)
    ax.set_ylabel(ylabel, color=INK)
    ax.set_title(title, color=INK, fontsize=10, loc="left")
    ax.grid(color=GRID, linewidth=0.8, which="major")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, which="both")


def anchor(df, method, ordering, col):
    """Smallest-n point of a series: the guides start there so their slopes are easy to compare."""
    d = df[(df["method"] == method) & (df["ordering"] == ordering)].dropna(subset=[col]).sort_values("n")
    return d["n"].iloc[0], d[col].iloc[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()

    df = pd.read_csv(pathlib.Path(args.results) / "e02_direct.csv")
    n = np.geomspace(df["n"].min(), df["n"].max(), 50)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), dpi=150)
    panel(axes[0], df, "nnz_chol_equiv", "(a) Cholesky-equivalent fill nnz(L)", "nnz(L)")
    guide(axes[0], n, lambda m: m**1.5, *anchor(df, "cholmod", "natural", "nnz_chol_equiv"), r"$n^{3/2}$")
    guide(axes[0], n, lambda m: m * np.log(m), *anchor(df, "cholmod", "metis", "nnz_chol_equiv"), r"$n \log n$")

    panel(axes[1], df, "flops", "(b) flops = sum of squared column counts", "flops")
    fl = df.dropna(subset=["flops"])
    m = np.geomspace(fl["n"].min(), fl["n"].max(), 50)
    guide(axes[1], m, lambda k: k**2, *anchor(df, "cholmod", "natural", "flops"), r"$n^2$")
    guide(axes[1], m, lambda k: k**1.5, *anchor(df, "cholmod", "metis", "flops"), r"$n^{3/2}$")

    panel(axes[2], df, "setup_time", "(c) setup time (median of 3)", "seconds")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, frameon=False, fontsize=9, labelcolor=INK)
    fig.tight_layout(rect=(0, 0.12, 1, 1))

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f02_direct.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
