"""Figure for chunk 4b: what a residual stopping rule controls (plain CG, N = 640).

(a) Relative error against the value x for the sampled states of the out_first_3 run at rtol 1e-10 (log-log), with
    the corner state (1, 1, N-2) marked and the guide line abs_err_max / x: a residual test bounds the absolute
    error, so the relative error of an entry grows like 1 / x towards the small entries.
(b) error / (cond_smallest rtol) at the smallest entry against rtol for the four right-hand sides (log y), with a
    line at 1: the ratio is near 1 only for out_first_3, so "error ~ cond x rtol" is not a law.
Uses the largest N in the CSVs if N = 640 is missing (--quick).
Reads results/e04_mechanism_states.csv and results/e04_mechanism_rhs.csv only.
    python figures/f04_mechanism.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
RHS_STYLE = {"out_first_3": ("#2a78d6", "o"), "order_321": ("#1baf7a", "s"),
             "land_mid": ("#eda100", "D"), "land_quarter": ("#e87ba4", "^")}
STATES_RTOL = 1e-10


def style_axes(ax, title, xlabel, ylabel):
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_title(title, color=INK, fontsize=10, loc="left")
    ax.set_xlabel(xlabel, color=INK)
    ax.set_ylabel(ylabel, color=INK)
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
    results = pathlib.Path(args.results)
    states = pd.read_csv(results / "e04_mechanism_states.csv")
    rhs = pd.read_csv(results / "e04_mechanism_rhs.csv")
    N = 640 if 640 in set(rhs["N"]) else int(rhs["N"].max())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8), dpi=150)

    # (a) every sampled state at rtol 1e-10
    s = states[(states["N"] == N) & np.isclose(states["rtol"], STATES_RTOL, rtol=1e-9, atol=0)]
    ax1.plot(s["x"], s["rel_err"], color="#2a78d6", marker="o", markersize=2.5, linestyle="none", alpha=0.5,
             markeredgewidth=0, label=f"sampled states ({len(s)})", zorder=2)
    row = rhs[(rhs["N"] == N) & (rhs["rhs"] == "out_first_3") & np.isclose(rhs["rtol"], STATES_RTOL, rtol=1e-9, atol=0)]
    if len(row):
        r = row.iloc[0]
        xs = np.geomspace(s["x"].min(), s["x"].max(), 50) if len(s) else np.array([])
        ax1.plot(xs, r["abs_err_max"] / xs, color=MUTED, linewidth=1.5, linestyle=(0, (5, 2)),
                 label=f"guide: max abs error / x ({r['abs_err_max']:.1e} / x)", zorder=3)
        ax1.plot([r["x_smallest"]], [r["rel_err_smallest"]], color=INK, marker="*", markersize=12, linestyle="none",
                 label=f"corner {r['smallest_state']}: rel err {r['rel_err_smallest']:.1e}", zorder=4)
    style_axes(ax1, f"(a) N = {N}, out_first_3, plain CG, rtol {STATES_RTOL:g}: every entry",
               "x = P(player 3 out first) at the state", "relative error of the entry")
    ax1.legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper right")

    # (b) ratio at the smallest entry, four right-hand sides
    d = rhs[rhs["N"] == N]
    for name, (color, marker) in RHS_STYLE.items():
        e = d[d["rhs"] == name].sort_values("rtol")
        if len(e):
            ax2.plot(e["rtol"], e["ratio_to_cond_rtol"], color=color, marker=marker, linewidth=2, markersize=5,
                     label=name, zorder=3)
    ax2.axhline(1.0, color=MUTED, linewidth=1.2, linestyle=(0, (5, 2)), label="ratio 1 (error = cond x rtol)", zorder=2)
    style_axes(ax2, f"(b) N = {N}, plain CG: error / (cond rtol) at the smallest entry",
               "CG stopping tolerance rtol (||r|| <= rtol ||b||)", r"rel err$_{smallest}$ / (cond$_{smallest}$ rtol)")
    ax2.invert_xaxis()  # tighter tolerance to the right, as in f04_tiny_error
    ax2.legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper right")

    fig.tight_layout()
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f04_mechanism.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
