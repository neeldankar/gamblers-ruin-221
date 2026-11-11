"""Figure for chunk 6: the FFT solver against splu.

Left: seconds_fft and seconds_splu against n (log-log), with an n log n guide line through the largest FFT point.
Right: p123_reldiff = |x_fft / x_splu - 1| at the smallest P(123), state (N-2, 1, 1), against N.
Reads results/e06_fft.csv only.
    python figures/f06_fft.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE = "#2a78d6", "#eb6834"  # categorical slots 1 and 2 (same palette as f08)


def style(ax):
    ax.set_xscale("log")
    ax.set_yscale("log")
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
    df = pd.read_csv(pathlib.Path(args.results) / "e06_fft.csv").sort_values("N")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), dpi=150)
    n = df["n"].to_numpy(float)
    ax1.plot(n, df["seconds_fft"], color=BLUE, marker="o", linewidth=2, label="FFT (method of images)")
    sp = df.dropna(subset=["seconds_splu"])
    ax1.plot(sp["n"], sp["seconds_splu"], color=ORANGE, marker="s", linewidth=2, label="splu (setup + solve)")
    guide = n * np.log(n)
    guide *= df["seconds_fft"].iloc[-1] / guide[-1] * 2  # a factor 2 above the last FFT point
    ax1.plot(n, guide, color=INK, linewidth=1, linestyle=(0, (3, 2)), label="guide: n log n")
    style(ax1)
    ax1.set_xlabel("n (live states)", color=INK)
    ax1.set_ylabel("seconds (median of 3, b = 1)", color=INK)
    ax1.set_title("Solve time", color=INK, fontsize=10, loc="left")
    ax1.legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper left")

    rd = df.dropna(subset=["p123_reldiff"])
    ax2.plot(rd["N"], rd["p123_reldiff"], color=BLUE, marker="o", linewidth=2)
    style(ax2)
    ax2.set_xticks(rd["N"])
    ax2.set_xticklabels([str(N) for N in rd["N"]])
    ax2.minorticks_off()
    ax2.set_xlabel("N (chips)", color=INK)
    ax2.set_ylabel("|x_fft / x_splu - 1| at state (N-2, 1, 1)", color=INK)
    ax2.set_title("FFT vs splu at the smallest P(123)", color=INK, fontsize=10, loc="left")

    fig.tight_layout()
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f06_fft.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
