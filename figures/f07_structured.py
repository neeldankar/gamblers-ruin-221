"""Figure for chunks 7 and 7b: the four sensitivities of the tiny probability, against N.

Lines: cond_max (chunk 4: perturb A's entries, diagonal free) with a 0.39 N^2 guide; structured_cond_max (the
structured condition number: off-diagonals, row sums and b, worst case) with a 1.22 N guide; symmetric_cond_tiny
(the same, symmetric perturbations only); structured_push and structured_random_max (measured ratios for one push
and the max over 20 random draws). Reads results/e07_structured.csv only.
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
SERIES = [  # (column, label, color, marker): categorical slots 1-5 (slots 1-3 as in chunk 7's version)
    ("cond_max", "cond_max (chunk 4: perturb A's entries)", "#1baf7a", "D"),
    ("structured_cond_max", "structured condition number (worst case)", "#eda100", "^"),
    ("symmetric_cond_tiny", "structured, symmetric perturbations only", "#e87ba4", "v"),
    ("structured_push", "structured push (row sums down, b up)", "#eb6834", "s"),
    ("structured_random_max", "structured, random (max over 20 draws)", "#2a78d6", "o"),
]
GUIDES = [(0.39, 2, "0.39 N^2", (0, (5, 2))), (1.22, 1, "1.22 N", (0, (1, 2)))]  # (coefficient, power, label, dash)
TITLE = ("Sensitivity of the tiny probability: N^2 for A's entries, N for off-diagonals and row sums,\n"
         "log N if symmetric, O(1) for random perturbations")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()
    df = pd.read_csv(pathlib.Path(args.results) / "e07_structured.csv").sort_values("N")

    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)
    for col, label, color, marker in SERIES:
        ax.plot(df["N"], df[col], color=color, marker=marker, markersize=6, linewidth=2, zorder=3, label=label)
    for coef, power, label, dash in GUIDES:
        ax.plot(df["N"], coef * df["N"] ** power, color=MUTED, linewidth=1.2, linestyle=dash, zorder=2,
                label=f"guide {label}")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(df["N"])
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("N (chips)", color=INK)
    ax.set_ylabel("relative change of x per unit eps   (eps = 1e-8)", color=INK)
    ax.set_title(TITLE, color=INK, fontsize=9.5, loc="left")
    ax.grid(color=GRID, linewidth=0.8, which="major")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, which="both")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper left", bbox_to_anchor=(1.01, 1))
    fig.tight_layout()
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f07_structured.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
