"""Figure for chunk 5: SOR as a function of omega.

Left: rho_dense = rho(SOR(omega)) at N = 20 and 40 (coarse and fine grids merged), with a vertical line at each
omega*. Right: iterations_ones (b = 1, rtol 1e-10) against omega for every N in the CSV.
Reads results/e05_omega_sweep.csv only.
    python figures/f05_omega.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
COLORS = {20: "#2a78d6", 40: "#eb6834", 80: "#1baf7a"}  # categorical slots 1-3


def style(ax):
    ax.grid(color=GRID, linewidth=0.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()
    df = pd.read_csv(pathlib.Path(args.results) / "e05_omega_sweep.csv").sort_values("omega")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), dpi=150)
    for N in sorted(df["N"].unique()):
        d = df[df["N"] == N]
        color = COLORS.get(N, INK)
        w = d["omega_star"].iloc[0]
        if d["rho_dense"].notna().any():
            ax1.plot(d["omega"], d["rho_dense"], color=color, linewidth=1.5, label=f"N = {N}")
            ax1.axvline(w, color=color, linewidth=1, linestyle=(0, (3, 2)))
        ax2.plot(d["omega"], d["iterations_ones"], color=color, linewidth=1.5, label=f"N = {N}")
        ax2.axvline(w, color=color, linewidth=1, linestyle=(0, (3, 2)))
    style(ax1)
    ax1.set_xlabel("omega (dashed: Young's omega*)", color=INK)
    ax1.set_ylabel("rho(SOR(omega)), dense eigenvalues", color=INK)
    ax1.set_title("Spectral radius: minimized at omega*", color=INK, fontsize=10, loc="left")
    ax1.legend(frameon=False, fontsize=8, labelcolor=INK)
    style(ax2)
    ax2.set_yscale("log")
    ax2.set_xlabel("omega (dashed: Young's omega*)", color=INK)
    ax2.set_ylabel("sweeps to relative residual 1e-10 (b = 1)", color=INK)
    ax2.set_title("Iteration count", color=INK, fontsize=10, loc="left")
    ax2.legend(frameon=False, fontsize=8, labelcolor=INK)
    fig.tight_layout()
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f05_omega.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
