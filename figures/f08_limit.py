"""Figure for chunk 8: the exact probabilities at fixed proportions (N/5, 3N/10, N/2) converge like N^-4.

Plots |P(N) - P(N/2)| against N, log-log, for each of the six elimination orders, with a slope -4 guide line.
Orders with the same winner k come in pairs whose sum is x_k / N, the same at every N, so their differences are
equal and opposite: the second order of each pair is drawn dashed with hollow markers on top of the first.
Reads results/e08_limit.csv only.
    python figures/f08_limit.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import NullFormatter, ScalarFormatter

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
ORDERS = ["123", "132", "213", "231", "312", "321"]
# categorical slots 1-6 in fixed order (dataviz reference palette; passes the adjacent-pair gates)
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
MARKERS = ["o", "s", "D", "^", "v", "P"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()
    df = pd.read_csv(pathlib.Path(args.results) / "e08_limit.csv").sort_values("N").set_index("N")
    Ns = [N for N in df.index if N // 2 in df.index]

    fig, ax = plt.subplots(figsize=(7.5, 5.5), dpi=150)
    for o, color, marker in zip(ORDERS, COLORS, MARKERS):
        diff = [abs(df.loc[N, f"P{o}"] - df.loc[N // 2, f"P{o}"]) for N in Ns]
        partner = [p for p in ORDERS if p[2] == o[2] and p != o][0]
        second = ORDERS.index(o) > ORDERS.index(partner)  # drawn on top of its partner
        label = f"order {o}" + (" (out first, out second, wins)" if o == "123" else "")
        if second:
            label += f": same as {partner}"
        ax.plot(Ns, diff, color=color, marker=marker, markersize=9 if second else 6, linewidth=2,
                linestyle=(0, (4, 3)) if second else "-", markerfacecolor="white" if second else color,
                zorder=4 if second else 3, label=label)
    # slope -4 guide, a factor 2 above the largest difference at the first N
    first = max(abs(df.loc[Ns[0], f"P{o}"] - df.loc[Ns[0] // 2, f"P{o}"]) for o in ORDERS)
    guide = first * 2 * (np.array(Ns, float) / Ns[0]) ** -4
    ax.plot(Ns, guide, color=INK, linewidth=1, linestyle=(0, (3, 2)), label="guide: slope -4")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(Ns)
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("N (chips)", color=INK)
    ax.set_ylabel("|P(N) - P(N/2)| at stacks (N/5, 3N/10, N/2)", color=INK)
    ax.set_title("Exact order probabilities at fixed proportions converge like N$^{-4}$", color=INK,
                 fontsize=10, loc="left")
    ax.grid(color=GRID, linewidth=0.8, which="major")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, which="both")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK, loc="lower left")
    fig.tight_layout()
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f08_limit.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
