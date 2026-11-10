"""Figure for chunk 4: the tiny entry and its condition number against N (log x).

(a) cond_tiny / N^2 for both events (equal by the 1 <-> 2 symmetry; order_321 drawn as hollow markers).
(b) N^3 x_tiny for out_first_3 and 2 x N^3 x_tiny for order_321, with the limit Gamma(1/3)^9 / (8 pi^4).
Reads results/e04_condition.csv only.
    python figures/f04_condition.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, NullFormatter, NullLocator
import pandas as pd

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE = "#2a78d6", "#eb6834"
LIMIT = 9.1195890  # Gamma(1/3)^9 / (8 pi^4)


def style_axes(ax, Ns, title, ylabel):
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(FixedLocator(Ns))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticklabels([str(N) for N in Ns])
    ax.set_xlabel("N (total chips)", color=INK)
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
    df = pd.read_csv(pathlib.Path(args.results) / "e04_condition.csv")
    a = df[df["event"] == "out_first_3"].sort_values("N")
    b = df[df["event"] == "order_321"].sort_values("N")
    Ns = sorted(df["N"].unique())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6), dpi=150)
    ax1.plot(a["N"], a["cond_tiny_over_N2"], color=BLUE, marker="o", linewidth=2, label="out_first_3", zorder=3)
    ax1.plot(b["N"], b["cond_tiny_over_N2"], color=ORANGE, marker="o", markerfacecolor="none", markersize=9,
             linestyle="none", label="order_321", zorder=4)
    style_axes(ax1, Ns, r"(a) cond$_{tiny}$ / N$^2$ = 2 E[T | event] / N$^2$ at (1, 1, N-2)", r"cond$_{tiny}$ / N$^2$")
    ax1.legend(frameon=False, fontsize=8, labelcolor=INK, loc="lower right")

    ax2.axhline(LIMIT, color=MUTED, linewidth=1.2, linestyle=(0, (5, 2)), label=r"limit $\Gamma(1/3)^9 / (8\pi^4)$ = 9.1195890")
    ax2.plot(a["N"], a["N3_x_tiny"], color=BLUE, marker="o", linewidth=2, label="out_first_3", zorder=3)
    ax2.plot(b["N"], 2 * b["N3_x_tiny"], color=ORANGE, marker="o", markerfacecolor="none", markersize=9,
             linestyle="none", label="2 x order_321", zorder=4)
    style_axes(ax2, Ns, r"(b) N$^3$ P$_{(1,1,N-2)}$(player 3 out first)", r"N$^3$ x$_{tiny}$")
    ax2.ticklabel_format(axis="y", useOffset=False)
    ax2.legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper right")

    fig.tight_layout()
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f04_condition.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
