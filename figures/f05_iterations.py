"""Figure for chunk 5: iterations against N (log-log) for Jacobi, Gauss-Seidel and SOR(omega*), b = ones.

Markers are measured counts; solid lines are the predictions ln(1/rtol) / (-ln rho) with rho = rho_J, rho_J^2 and
the 3/4 law (omega* - 1)^(3/4); the dashed line is Young's SOR prediction rho = omega* - 1.
Reads results/e05_iterations.csv only.
    python figures/f05_iterations.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, GREEN = "#2a78d6", "#eb6834", "#1baf7a"  # categorical slots 1-3 (same palette as f06, f07)
STYLE = {"jacobi": (BLUE, "o", "Jacobi"), "gauss_seidel": (ORANGE, "s", "Gauss-Seidel"),
         "sor": (GREEN, "^", "SOR(omega*)")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()
    df = pd.read_csv(pathlib.Path(args.results) / "e05_iterations.csv")
    df = df[df["b_kind"] == "ones"].sort_values("N")

    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    for method, (color, marker, label) in STYLE.items():
        d = df[df["method"] == method]
        ax.plot(d["N"], d["iterations"], color=color, marker=marker, linestyle="none", markersize=7,
                label=f"{label}: measured")
        pred = "3/4 law" if method == "sor" else ("rho_J^2" if method == "gauss_seidel" else "rho_J")
        ax.plot(d["N"], d["predicted_iterations"], color=color, linewidth=1.5, label=f"{label}: predicted ({pred})")
        if method == "sor":
            ax.plot(d["N"], d["young_predicted_iterations"], color=color, linewidth=1.5, linestyle=(0, (4, 3)),
                    label="SOR: Young's prediction (rho = omega* - 1)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    Ns = sorted(df["N"].unique())
    ax.set_xticks(Ns)
    ax.set_xticklabels([str(N) for N in Ns])
    ax.minorticks_off()
    ax.grid(color=GRID, linewidth=0.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED)
    ax.set_xlabel("N (chips)", color=INK)
    ax.set_ylabel("sweeps to relative residual 1e-10 (b = 1)", color=INK)
    ax.set_title("Stationary methods: O(N^2) sweeps for Jacobi and Gauss-Seidel, O(N) for SOR",
                 color=INK, fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper left")
    fig.tight_layout()
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f05_iterations.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
