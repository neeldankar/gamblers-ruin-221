"""Figure for chunk 3: time to solution against N for each kind and the direct solver, random b, log-log.

(a) one right-hand side: setup_time + solve_time;
(b) six right-hand sides: setup_time + 6 x solve_time (one preconditioner or factor, reused six times).
Reads results/e03_krylov.csv only.
    python figures/f03_time.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator
import pandas as pd

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
STYLE = {
    "none": ("#2a78d6", "o", "-"),
    "jacobi": ("#eb6834", "x", ":"),
    "ic0": ("#1baf7a", "s", "-"),
    "mic0": ("#eda100", "D", "-"),
    "amg": ("#e87ba4", "^", "-"),
    "direct": ("#008300", "v", "--"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()
    df = pd.read_csv(pathlib.Path(args.results) / "e03_krylov.csv")
    df = df[df["rhs"] == "random"]
    Ns = sorted(int(N) for N in df["N"].unique())

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), dpi=150, sharey=True)
    for ax, count in zip(axes, [1, 6]):
        for kind, (color, marker, ls) in STYLE.items():
            d = df[df["kind"] == kind].sort_values("N")
            if d.empty:
                continue
            total = d["setup_time"] + count * d["solve_time"]
            ax.plot(d["N"], total, color=color, marker=marker, linestyle=ls, linewidth=2, markersize=7,
                    markeredgecolor="white" if marker != "x" else color, markeredgewidth=1, label=kind, zorder=3)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.xaxis.set_major_locator(FixedLocator(Ns))
        ax.xaxis.set_major_formatter(FixedFormatter([str(N) for N in Ns]))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xlabel("N (chips)", color=INK)
        rhs_word = "one right-hand side: setup + solve" if count == 1 else "six right-hand sides: setup + 6 x solve"
        ax.set_title(f"({'ab'[count == 6]}) {rhs_word}", color=INK, fontsize=10, loc="left")
        ax.grid(color=GRID, linewidth=0.8, which="major")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(MUTED)
        ax.tick_params(colors=MUTED, which="both")
    axes[0].set_ylabel("seconds (random b)", color=INK)
    axes[0].legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper left")
    fig.tight_layout()
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f03_time.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
