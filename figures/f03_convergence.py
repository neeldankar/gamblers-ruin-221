"""Figure for chunk 3: CG convergence histories at N = 320 (or whatever N the CSV holds).

One panel per right-hand side (random, order321): relative residual (solid) and relative A-norm error (dashed)
against k for each kind, plus the Chebyshev bound 2 rho^k for plain CG (grey dotted). Semilog y.
Reads results/e03_convergence.csv only.
    python figures/f03_convergence.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
COLOR = {"none": "#2a78d6", "ic0": "#1baf7a", "mic0": "#eda100", "amg": "#e87ba4"}
LABEL_OFFSET = {"none": (4, -10), "ic0": (4, -10), "mic0": (4, -10), "amg": (4, 10)}  # amg ends next to mic0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()
    df = pd.read_csv(pathlib.Path(args.results) / "e03_convergence.csv")
    N = int(df["N"].iloc[0])

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), dpi=150, sharey=True)
    for ax, rhs in zip(axes, ["random", "order321"]):
        d = df[df["rhs"] == rhs]
        for kind, color in COLOR.items():
            e = d[d["kind"] == kind].sort_values("k")
            if e.empty:
                continue
            ax.plot(e["k"], e["relres"], color=color, linewidth=2, zorder=3)
            ax.plot(e["k"], e["err_A"], color=color, linewidth=1.5, linestyle=(0, (5, 2)), zorder=3)
            ax.annotate(f"{kind} ({int(e['k'].max())})", xy=(e["k"].iloc[-1], e["relres"].iloc[-1]),
                        xytext=LABEL_OFFSET[kind], textcoords="offset points", color=INK, fontsize=8)
        c = d[d["kind"] == "none"].dropna(subset=["chebyshev"]).sort_values("k")
        ax.plot(c["k"], c["chebyshev"], color=MUTED, linewidth=1.5, linestyle=(0, (1, 2)), zorder=2)
        ax.set_yscale("log")
        ax.set_ylim(1e-12, 1e2)
        ax.axhline(1e-10, color=MUTED, linewidth=0.8, zorder=1)
        ax.set_xlabel("iteration k", color=INK)
        ax.set_title(f"({'ab'[rhs == 'order321']}) N = {N}, rhs = {rhs}", color=INK, fontsize=10, loc="left")
        ax.grid(color=GRID, linewidth=0.8, which="major")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(MUTED)
        ax.tick_params(colors=MUTED, which="both")
    axes[0].set_ylabel("relative residual / error", color=INK)

    handles = [Line2D([], [], color=c, linewidth=2, label=k) for k, c in COLOR.items()]
    handles += [Line2D([], [], color=INK, linewidth=2, label="||r_k|| / ||b||"),
                Line2D([], [], color=INK, linewidth=1.5, linestyle=(0, (5, 2)), label="||x_k - x*||_A / ||x*||_A"),
                Line2D([], [], color=MUTED, linewidth=1.5, linestyle=(0, (1, 2)),
                       label=r"Chebyshev bound $2\rho^k$, $\rho = (\sqrt{\kappa}-1)/(\sqrt{\kappa}+1)$ (plain CG)"),
                Line2D([], [], color=MUTED, linewidth=0.8, label="rtol = 1e-10")]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=8, labelcolor=INK)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f03_convergence.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
