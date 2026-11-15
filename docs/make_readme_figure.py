"""The README figure: the game's state space (left) and one answer, P(player 3 busts first), over it (right).

    PYTHONPATH=. python docs/make_readme_figure.py      # writes docs/game.png

Not part of the pipeline (it lives outside figures/ on purpose: it solves a small system itself instead of
reading results/*.csv).
"""
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, Polygon

from gr.matrix import build_A, rhs_out_first, solve
from gr.states import StateSpace

OUT = pathlib.Path(__file__).resolve().parent / "game.png"

# palette: one blue ramp for magnitude, text in ink tokens, recessive grays for structure
BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
ACCENT = "#2a78d6"
INK, INK2, MUTED, RULE = "#0b0b0b", "#52514e", "#8a8984", "#d6d5d0"
SURFACE = "#ffffff"

for name in ("Inter", "DejaVu Sans"):
    if any(name in f.name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = name
        break
plt.rcParams.update({"font.size": 10.5, "text.color": INK, "axes.edgecolor": RULE})

# corners of the simplex x1 + x2 + x3 = N, drawn as an equilateral triangle
V = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, np.sqrt(3) / 2]])  # x1 = N, x2 = N, x3 = N


def xy(X, N):
    return (np.asarray(X, float) / N) @ V


def frame(ax):
    ax.add_patch(Polygon(V, closed=True, fill=False, edgecolor=RULE, lw=1.2, zorder=0))
    ax.set_aspect("equal")
    ax.set_xlim(-0.12, 1.12)
    ax.set_ylim(-0.13, 0.98)
    ax.axis("off")


def corner_labels(ax, N_text):
    ax.text(*V[0] + [-0.02, -0.055], f"player 1\nhas all {N_text}", ha="center", va="top", color=INK2, fontsize=9)
    ax.text(*V[1] + [0.02, -0.055], f"player 2\nhas all {N_text}", ha="center", va="top", color=INK2, fontsize=9)
    ax.text(*V[2] + [0, 0.03], f"player 3 has all {N_text}", ha="center", va="bottom", color=INK2, fontsize=9)


def edge_labels(ax):
    mid = lambda i, j: (V[i] + V[j]) / 2  # noqa: E731
    ax.text(*mid(0, 1) + [0, -0.04], "player 3 is out", ha="center", va="top", color=MUTED, fontsize=9)
    ax.text(*mid(0, 2) + [-0.075, 0.02], "player 2 is out", ha="center", va="center", rotation=60, color=MUTED, fontsize=9)
    ax.text(*mid(1, 2) + [0.075, 0.02], "player 1 is out", ha="center", va="center", rotation=-60, color=MUTED, fontsize=9)


def panel_game(ax, N=9, here=(3, 3, 3)):
    frame(ax)
    live = [(a, b, N - a - b) for a in range(1, N) for b in range(1, N - a)]
    dead = [(a, b, N - a - b) for a in range(N + 1) for b in range(N + 1 - a) if min(a, b, N - a - b) == 0]
    P = xy(live, N)
    D = xy(dead, N)
    ax.scatter(D[:, 0], D[:, 1], s=26, facecolor=SURFACE, edgecolor=MUTED, lw=1.0, zorder=2)
    ax.scatter(P[:, 0], P[:, 1], s=26, color=INK2, zorder=3)
    h = xy([here], N)[0]
    moves = [(a, b) for a in range(3) for b in range(3) if a != b]
    for a, b in moves:
        y = list(here)
        y[a] += 1
        y[b] -= 1
        t = xy([y], N)[0]
        ax.add_patch(FancyArrowPatch(h, h + 0.86 * (t - h), arrowstyle="-|>", mutation_scale=11, lw=1.8,
                                     color=ACCENT, zorder=4, shrinkA=4, shrinkB=0))
    ax.scatter([h[0]], [h[1]], s=70, color=ACCENT, edgecolor=SURFACE, lw=2, zorder=5)
    ax.text(0, 1.015, "Each round one of the six ordered pairs is chosen (probability 1/6) and one chip moves.",
            transform=ax.transAxes, fontsize=9.5, color=INK2, va="bottom")
    corner_labels(ax, "N")
    edge_labels(ax)
    ax.scatter([], [], s=26, color=INK2, label="game still on: one unknown each")
    ax.scatter([], [], s=26, facecolor=SURFACE, edgecolor=MUTED, label="a player is out: known boundary value")
    ax.legend(loc="upper right", bbox_to_anchor=(1.10, 0.86), frameon=False, fontsize=9, handletextpad=0.3,
              labelcolor=INK2)
    ax.set_title("The game: three players, N chips", loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=22)


def panel_answer(fig, ax, N=60):
    frame(ax)
    S = StateSpace(N)
    x = solve(build_A(S), rhs_out_first(S, 2))  # P(player 3 busts first)
    # add the boundary: 1 where player 3 is out, 0 where player 1 or 2 is out first
    dead = [(a, b, N - a - b) for a in range(N + 1) for b in range(N + 1 - a) if min(a, b, N - a - b) == 0]
    dval = [1.0 if c == 0 and min(a, b) > 0 else (0.0 if c > 0 else 0.5) for a, b, c in dead]
    X = np.vstack([S.coords(), dead])
    vals = np.concatenate([x, dval])
    P = xy(X, N)
    tri = mtri.Triangulation(P[:, 0], P[:, 1])
    cmap = LinearSegmentedColormap.from_list("blue", BLUE)
    tpc = ax.tripcolor(tri, vals, shading="gouraud", cmap=cmap, vmin=0, vmax=1, zorder=1)
    live = mtri.Triangulation(*xy(S.coords(), N).T)
    levels = [1e-4, 1e-3, 1e-2, 1e-1]
    cs = ax.tricontour(live, np.log10(x), levels=np.log10(levels), colors=INK, linewidths=0.8, linestyles="solid", zorder=3)
    ax.clabel(cs, fmt={np.log10(v): t for v, t in zip(levels, ["10$^{-4}$", "10$^{-3}$", "0.01", "0.1"])},
              fontsize=8.5, inline_spacing=3)
    k = S.index((1, 1, N - 2))
    p = xy([S.state(k)], N)[0]
    ax.scatter([p[0]], [p[1]], s=90, facecolor="none", edgecolor=INK, lw=1.4, zorder=5)
    m, e = f"{x[k]:.1e}".split("e")
    ax.annotate(f"P = {m} × 10$^{{{int(e)}}}$ at (1, 1, {N - 2}):\nthe chip leader busts first",
                xy=p + [0.025, -0.01], xytext=(0.72, 0.80), ha="left", va="center", fontsize=9.5, color=INK,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkA=2, shrinkB=4))
    ax.text(0, 1.015, "Colour: P(player 3 busts first) from every state. Lines: where it equals 0.1, 0.01, ...",
            transform=ax.transAxes, fontsize=9.5, color=INK2, va="bottom")
    corner_labels(ax, "N")
    edge_labels(ax)
    cax = ax.inset_axes([0.0, 0.86, 0.30, 0.03])
    cb = fig.colorbar(tpc, cax=cax, orientation="horizontal", ticks=[0, 0.25, 0.5, 0.75, 1])
    cb.ax.set_xticklabels(["0", "0.25", "0.5", "0.75", "1"], fontsize=8.5, color=INK2)
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=0, pad=3)
    cax.set_title("P(player 3 busts first)", fontsize=9, color=INK2, loc="left", pad=4)
    ax.set_title(f"One answer = one sparse solve (N = {N}, {S.n:,} unknowns)", loc="left", fontsize=12.5,
                 fontweight="bold", color=INK, pad=22)
    return x[k]


def main():
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.0), facecolor=SURFACE)
    fig.subplots_adjust(left=0.03, right=0.97, top=0.86, bottom=0.04, wspace=0.12)
    panel_game(axes[0])
    tiny = panel_answer(fig, axes[1])
    fig.savefig(OUT, dpi=170, facecolor=SURFACE)
    print(f"wrote {OUT} (tiny entry {tiny:.6e})")


if __name__ == "__main__":
    main()
