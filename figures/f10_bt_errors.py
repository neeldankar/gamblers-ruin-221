"""Figure for chunk 10, part B: CG on the symmetrized S is wrong where pi is small; GMRES on A is not.

Bradley-Terry, skills (1, 1.5, 2), N = 80, P(strongest wins). Each dot is one state (lexicographic index), its
height the error |u - u_ref| / max |u_ref| (u_ref = splu on A), its color log10 pi. Both solvers stop at
relative residual 1e-10, CG in the S-residual, GMRES in the A-residual.
Reads results/e10_bt_states_N80.csv only.
    python figures/f10_bt_errors.py [--results DIR] [--outdir DIR]
"""
import argparse
import math
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
# sequential blue ramp, steps 250 -> 700 (dataviz reference palette): light = small pi, dark = large pi
BLUES = LinearSegmentedColormap.from_list("blues", ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281",
                                                    "#0d366b"])
FLOOR = 1e-17  # exact zeros are drawn here


def style(ax):
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
    df = pd.read_csv(pathlib.Path(args.results) / "e10_bt_states_N80.csv")
    lp10 = df["log_pi"].to_numpy() / math.log(10)
    idx = np.arange(len(df))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), dpi=150, sharey=True)
    for ax, col, title in ((axes[0], "err_cg_S", "CG on S, mapped back"),
                           (axes[1], "err_gmres_A", "GMRES(30) on A")):
        err = np.maximum(df[col].to_numpy(), FLOOR)
        sc = ax.scatter(idx, err, c=lp10, cmap=BLUES, s=4, linewidths=0, rasterized=True)
        ax.set_yscale("log")
        ax.set_xlabel("state index (lexicographic in (x1, x2))", color=INK)
        ax.set_title(f"{title}: max error {df[col].max():.2g}", color=INK, fontsize=10, loc="left")
        style(ax)
    axes[0].set_ylabel("|u - u_ref| / max |u_ref|", color=INK)
    cb = fig.colorbar(sc, ax=axes, pad=0.015)
    cb.set_label("log10 pi(x)  (pi = 1^x1 1.5^x2 2^x3)", color=INK)
    cb.ax.tick_params(colors=MUTED)
    cb.outline.set_edgecolor(MUTED)
    fig.suptitle("P(strongest wins), N = 80, both stopped at relative residual 1e-10. CG runs on S = D^1/2 A D^-1/2 "
                 "and its answer is mapped back by D^-1/2:\nits S-residual does not see the low-pi (light) states",
                 color=INK, fontsize=10, x=0.01, y=1.04, ha="left")
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f10_bt_errors.png"
    fig.savefig(path, bbox_inches="tight")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
