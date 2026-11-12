"""Figure for chunk 9: P(the chip leader busts first) against N, log-log.

Three players from (1, 1, N-2) (exactly N^-3 asymptotically) and four players from (1, 1, 1, N-3) (measured
exponent 5.72), with dashed guides of slope -3 and -5.72, drawn a factor 4 below each curve so both stay visible.
Reads results/e09_big_stack.csv only.
    python figures/f09_big_stack.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SERIES = {3: ("#eb6834", "o", "three players, from (1, 1, N-2)", 3.0, r"slope $-3$"),
          4: ("#2a78d6", "s", "four players, from (1, 1, 1, N-3)", 5.72, r"slope $-5.72$")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()
    df = pd.read_csv(pathlib.Path(args.results) / "e09_big_stack.csv")

    fig, ax = plt.subplots(figsize=(6.5, 4.8), dpi=150)
    for players, (color, marker, label, alpha, glabel) in SERIES.items():
        d = df[df["players"] == players].sort_values("N")
        if d.empty:
            continue
        ax.plot(d["N"], d["P"], color=color, marker=marker, linewidth=2, markersize=6, markeredgecolor="white",
                markeredgewidth=1, label=label, zorder=3)
        N = np.geomspace(d["N"].min(), d["N"].max(), 50)
        y = 0.25 * d["P"].iloc[-1] * (N / d["N"].iloc[-1]) ** -alpha
        ax.plot(N, y, color=MUTED, linestyle=(0, (4, 3)), linewidth=1, zorder=2)
        ax.annotate(glabel, xy=(N[-1], y[-1]), xytext=(4, 0), textcoords="offset points", color=MUTED, fontsize=8,
                    ha="left", va="center")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(right=ax.get_xlim()[1] * 1.6)  # room for the guide labels
    ax.set_xlabel("N (total chips)", color=INK)
    ax.set_ylabel("P(chip leader busts first)", color=INK)
    ax.set_title("A tiny probability: the big stack is out first", color=INK, fontsize=10, loc="left")
    ax.grid(color=GRID, linewidth=0.8, which="major")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, which="both")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    fig.tight_layout()

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f09_big_stack.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
