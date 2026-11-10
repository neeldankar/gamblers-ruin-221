"""Figure for chunk 3: CG iterations against N, log-log, rtol 1e-10.

(a) random b, one line per kind, with dashed guides of slope 1 and 1/2;
(b) b = ones (plain CG) against floor((N-1)/2), the number of distinct eigenvalues that b touches.
Reads results/e03_krylov.csv only.
    python figures/f03_iterations.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, NullFormatter, NullLocator
import numpy as np
import pandas as pd

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
# kind -> (color, marker, linestyle); colors are the validated categorical slots in fixed order
STYLE = {
    "none": ("#2a78d6", "o", "-"),
    "jacobi": ("#eb6834", "x", ":"),
    "ic0": ("#1baf7a", "s", "-"),
    "mic0": ("#eda100", "D", "-"),
    "amg": ("#e87ba4", "^", "-"),
}


def style_axes(ax, Ns, title, ylabel):
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.xaxis.set_major_locator(FixedLocator(Ns))
    ax.xaxis.set_major_formatter(matplotlib.ticker.FixedFormatter([str(N) for N in Ns]))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("N (chips)", color=INK)
    ax.set_ylabel(ylabel, color=INK)
    ax.set_title(title, color=INK, fontsize=10, loc="left")
    ax.grid(color=GRID, linewidth=0.8, which="major")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, which="both")


def guide(ax, N, slope, anchor_N, anchor_y, label):
    y = anchor_y * (N / anchor_N) ** slope
    ax.plot(N, y, color=MUTED, linestyle=(0, (4, 3)), linewidth=1, zorder=1)
    ax.annotate(label, xy=(N[-1], y[-1]), xytext=(4, 0), textcoords="offset points", color=MUTED,
                fontsize=8, va="center")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()
    df = pd.read_csv(pathlib.Path(args.results) / "e03_krylov.csv")
    Ns = sorted(int(N) for N in df["N"].unique())
    Ngrid = np.geomspace(min(Ns), max(Ns), 50)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), dpi=150)
    ax = axes[0]
    for kind, (color, marker, ls) in STYLE.items():
        d = df[(df["kind"] == kind) & (df["rhs"] == "random")].sort_values("N")
        if d.empty:
            continue
        ax.plot(d["N"], d["iterations"], color=color, marker=marker, linestyle=ls, linewidth=2, markersize=7,
                markeredgecolor="white" if marker != "x" else color, markeredgewidth=1, label=kind, zorder=3)
        if kind != "jacobi":  # jacobi lies exactly on none; its legend entry says so
            ax.annotate(kind, xy=(d["N"].iloc[-1], d["iterations"].iloc[-1]), xytext=(6, 0),
                        textcoords="offset points", color=INK, fontsize=8, va="center")
    none = df[(df["kind"] == "none") & (df["rhs"] == "random")].sort_values("N")
    mic = df[(df["kind"] == "mic0") & (df["rhs"] == "random")].sort_values("N")
    guide(ax, Ngrid, 1.0, none["N"].iloc[0], none["iterations"].iloc[0] * 1.6, "slope 1")
    if len(mic):
        guide(ax, Ngrid, 0.5, mic["N"].iloc[0], mic["iterations"].iloc[0] * 0.6, "slope 1/2")
    style_axes(ax, Ns, "(a) random b: iterations to ||r|| <= 1e-10 ||b||", "CG iterations")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper left")

    ax = axes[1]
    ones = df[(df["kind"] == "none") & (df["rhs"] == "ones")].sort_values("N")
    floor_half = (ones["N"] - 1) // 2
    ax.plot(ones["N"], floor_half, color=MUTED, linestyle=(0, (4, 3)), linewidth=1.5, marker="o", markersize=5,
            markerfacecolor="white", label="floor((N-1)/2): distinct eigenvalues in b = 1", zorder=2)
    ax.plot(ones["N"], ones["iterations"], color=STYLE["none"][0], marker="o", linewidth=2, markersize=7,
            markeredgecolor="white", markeredgewidth=1, label="plain CG, b = 1", zorder=3)
    for N, its, f in zip(ones["N"], ones["iterations"], floor_half):
        ax.annotate(f"{its / f:.2f}", xy=(N, its), xytext=(0, 8), textcoords="offset points", color=MUTED,
                    fontsize=7, ha="center")
    style_axes(ax, Ns, "(b) b = 1: iterations vs floor((N-1)/2) (labels: ratio)", "CG iterations")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper left")

    fig.tight_layout()
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f03_iterations.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
