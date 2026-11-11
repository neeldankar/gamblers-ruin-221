"""Figure for chunk 7: sensitivity in the right parametrization vs chunk 4's condition number, against N.

Lines: structured_random_max and structured_push (relative change of x per unit eps when the off-diagonals, the
row sums and b are perturbed) and cond_max (chunk 4's componentwise condition number, perturbing A's entries),
with 2n - 1 as a dashed guide. Reads results/e07_structured.csv only.
    python figures/f07_structured.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import NullFormatter, ScalarFormatter

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SERIES = [  # (column, label, color, marker): categorical slots 1-3
    ("structured_random_max", "structured, random (max over 20 draws)", "#2a78d6", "o"),
    ("structured_push", "structured push (row sums down, b up)", "#eb6834", "s"),
    ("cond_max", "cond_max (chunk 4: perturb A's entries)", "#1baf7a", "D"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()
    df = pd.read_csv(pathlib.Path(args.results) / "e07_structured.csv").sort_values("N")

    fig, ax = plt.subplots(figsize=(7.5, 5), dpi=150)
    for col, label, color, marker in SERIES:
        ax.plot(df["N"], df[col], color=color, marker=marker, markersize=6, linewidth=2, zorder=3, label=label)
    ax.plot(df["N"], df["two_n_minus_1"], color=MUTED, linewidth=1.5, linestyle=(0, (5, 2)), zorder=2,
            label="2n - 1")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(df["N"])
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("N (chips)", color=INK)
    ax.set_ylabel("max_i |x'_i - x_i| / x_i / eps   (eps = 1e-8)", color=INK)
    ax.set_title("Perturbing off-diagonals, row sums and b moves x by 2-5 eps at every N",
                 color=INK, fontsize=10, loc="left")
    ax.grid(color=GRID, linewidth=0.8, which="major")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, which="both")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper left")
    fig.tight_layout()
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f07_structured.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
