"""Figure for chunk 1: kappa2 / N^2 against N, approaching 9 / (8 pi^2) from below.

Reads results/e01_conditioning.csv only.
    python figures/f01_conditioning.py [--results DIR] [--outdir DIR]
"""
import argparse
import math
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

SERIES = "#2a78d6"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()

    df = pd.read_csv(pathlib.Path(args.results) / "e01_conditioning.csv").sort_values("N")
    limit = 9 / (8 * math.pi**2)

    fig, ax = plt.subplots(figsize=(6, 3.6), dpi=150)
    ax.axhline(limit, color=MUTED, linestyle="--", linewidth=1.2)
    ax.annotate(r"limit $9/(8\pi^2) \approx 0.11399$", xy=(df["N"].max(), limit), xytext=(0, -10),
                textcoords="offset points", color=MUTED, fontsize=9, ha="right", va="top")
    ax.plot(df["N"], df["kappa2_over_N2"], color=SERIES, linewidth=2, marker="o", markersize=5)

    ax.set_xscale("log")
    ticks = [N for N in (10, 20, 40, 80, 160, 320, 640) if df["N"].min() <= N <= df["N"].max()]
    ax.set_xticks(ticks)
    ax.set_xticklabels(ticks)
    ax.minorticks_off()
    ax.set_xlabel("N (total chips)", color=INK)
    ax.set_ylabel(r"$\kappa_2(A) / N^2$", color=INK)
    ax.set_title(r"$\kappa_2 / N^2$ increases to $9/(8\pi^2)$", color=INK, fontsize=11, loc="left")
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED)
    fig.tight_layout()

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f01_conditioning.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
