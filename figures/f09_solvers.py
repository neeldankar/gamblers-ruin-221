"""Figure for chunk 9: four-player solvers against n, log-log.

(a) setup_s + solve_s, one line per method, dashed n^1 and n^2 guides. (b) nnz_factor, the nonzeros of the
factor (direct methods only; amg_cg has none), with a dashed n^(4/3) guide (the 3D nested-dissection order)
through CHOLMOD's largest run. Memory is not plotted: peak RSS levels off under memory pressure, so it is not a
reliable measure here. Runs stopped by the memory rules are left out, and panel (b)'s title names the runs the
memory guard killed (status "killed: ..."). Reads results/e09_solvers.csv only.
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
SHORT = {"splu": "SuperLU-COLAMD", "splu_mmd": "SuperLU-MMD", "cholmod": "CHOLMOD", "amg_cg": "AMG-CG"}


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

    raw = pd.read_csv(pathlib.Path(args.results) / "e09_solvers.csv")
    df = raw[raw["status"].str.startswith("ok")].copy()
    df["total_s"] = df["setup_s"] + df["solve_s"]
    n = np.geomspace(df["n"].min(), df["n"].max(), 50)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), dpi=150)
    panel(axes[0], df, "total_s", "(a) setup + solve time (right-hand side e2)", "seconds")
    first = df.sort_values("n").groupby("method").first()
    if "amg_cg" in first.index:
        guide(axes[0], n, 1, first.loc["amg_cg", "n"], first.loc["amg_cg", "total_s"], r"$n$")
    if "cholmod" in first.index:
        guide(axes[0], n, 2, first.loc["cholmod", "n"], first.loc["cholmod", "total_s"], r"$n^2$")
    killed = raw[raw["status"].str.startswith("killed")].sort_values(["method", "N"])
    stopped = ", ".join(f"{SHORT.get(m, m)} at N = {N}" for m, N in zip(killed["method"], killed["N"]))
    title_b = "(b) nonzeros of the factor" + (f"\n{stopped}: stopped by the memory guard" if stopped else "")
    panel(axes[1], df, "nnz_factor", title_b, "nonzeros of the factor")
    ch = df[df["method"] == "cholmod"].sort_values("n")
    if len(ch):  # anchor at CHOLMOD's largest run, over the range of the direct runs
        direct = df[df["nnz_factor"].notna()]
        nd = np.geomspace(direct["n"].min(), direct["n"].max(), 50)
        guide(axes[1], nd, 4 / 3, ch["n"].iloc[-1], ch["nnz_factor"].iloc[-1], r"$n^{4/3}$")

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
