"""Figure for chunk 8: where the ICM over- and underrates player 1's chance of 2nd place, N = 120.

A triangle heat map of P_ICM(2nd) - P(2nd) for player 1 over every live state. Each state (x1, x2, x3) sits at
its barycentric point: player 1's corner is at the top, players 2 and 3 at the bottom left and right. The
diverging map is blue (ICM too low) through gray (0) to red (ICM too high), symmetric about 0.
Reads results/e08_states_N120.csv only.
    python figures/f08_icm_map.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

INK, MUTED = "#0b0b0b", "#52514e"
# Diverging pair blue <-> red with a gray midpoint (dataviz reference palette), equal steps per arm.
DIVERGING = LinearSegmentedColormap.from_list(
    "blue_gray_red", ["#104281", "#3987e5", "#f0efec", "#e34948", "#8c1f1e"])
CORNERS = np.array([[0.5, np.sqrt(3) / 2], [0.0, 0.0], [1.0, 0.0]])  # players 1, 2, 3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()
    df = pd.read_csv(pathlib.Path(args.results) / "e08_states_N120.csv")
    X = df[["x1", "x2", "x3"]].to_numpy(dtype=float)
    N = int(X[0].sum())
    xy = (X / N) @ CORNERS
    d = df["dp2_player1"].to_numpy()
    lim = np.abs(d).max()

    fig, ax = plt.subplots(figsize=(7.5, 6.8), dpi=150)
    tri = mtri.Triangulation(xy[:, 0], xy[:, 1])
    im = ax.tripcolor(tri, d, cmap=DIVERGING, vmin=-lim, vmax=lim, shading="gouraud", rasterized=True)
    ax.plot(*np.vstack([CORNERS, CORNERS[:1]]).T, color=MUTED, linewidth=1)
    ax.tricontour(tri, d, levels=[0], colors=INK, linewidths=1, linestyles="dashed")
    for (cx, cy), text, ha, va, dy in [
        (CORNERS[0], "player 1 holds all chips", "center", "bottom", 0.02),
        (CORNERS[1], "player 2 holds all", "left", "top", -0.02),
        (CORNERS[2], "player 3 holds all", "right", "top", -0.02),
    ]:
        ax.text(cx, cy + dy, text, ha=ha, va=va, color=INK, fontsize=9)
    i = int(np.argmax(d))
    j = int(np.argmin(d))
    for k, word in ((i, "largest overrate"), (j, "largest underrate")):
        state = tuple(int(v) for v in X[k])
        ax.plot(*xy[k], marker="o", markersize=8, markerfacecolor="none", markeredgecolor=INK, markeredgewidth=1.5)
        ax.annotate(f"{word} {d[k]:+.4f}\nat {state}", xy[k], xytext=(12, 8), textcoords="offset points",
                    color=INK, fontsize=8)
    ax.set_aspect("equal")
    ax.axis("off")
    cb = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
    cb.set_label("P_ICM(2nd) - P(2nd), player 1  (red: ICM too high)", color=INK)
    cb.ax.tick_params(colors=MUTED)
    cb.outline.set_edgecolor(MUTED)
    ax.set_title(f"ICM error in player 1's chance of 2nd place, N = {N} (dashed: zero contour)",
                 color=INK, fontsize=10, loc="left", pad=24)
    fig.tight_layout()
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f08_icm_map.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
