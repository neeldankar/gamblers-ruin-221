"""Figure for chunk 7b: the own error of several direct solvers, and every method against the true probability.

Two panels from results/e07_baselines.csv (N <= 640), log-log against N:
  (a) |own_err_tiny| (against the stored solution) for the methods that solve the stored system, with the
      |data_term_tiny| line and guides u N and u N^2;
  (b) max_true_err_in_u (against the true probability, every entry) for cholmod_default, banded, banded_int,
      cholmod_int and gth, with guides N and N^2.
Each method keeps one color in both panels. cholmod_int is drawn in ink (no categorical slot left), with its
own marker and dash.
    python figures/f07_baselines.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import NullFormatter, ScalarFormatter

U = 2.0 ** -53
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
STYLE = {  # method: (label, color, marker, line style); colors validated per panel in slot order
    "cholmod_default": ("CHOLMOD default (nesdis)", "#2a78d6", "o", "-"),
    "cholmod_simplicial": ("CHOLMOD simplicial", "#1baf7a", "D", "-"),
    "cholmod_supernodal": ("CHOLMOD supernodal", "#eda100", "^", "-"),
    "splu_colamd": ("SuperLU COLAMD", "#e87ba4", "v", "-"),
    "splu_natural": ("SuperLU natural", "#008300", "P", "-"),
    "banded": ("band Cholesky", "#6250d6", "s", "-"),
    "gth": ("GTH", "#eb6834", "X", "-"),
    "banded_int": ("band Cholesky of 6A", "#e34948", "h", "-"),
    "cholmod_int": ("CHOLMOD of 6A", INK, "*", (0, (4, 1, 1, 1))),
}
PANEL_A = ["cholmod_default", "cholmod_simplicial", "cholmod_supernodal", "splu_colamd", "splu_natural", "banded"]
PANEL_B = ["cholmod_default", "gth", "banded", "banded_int", "cholmod_int"]


def style_axes(ax, Ns, ylabel, title):
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(Ns)
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("N (chips)", color=INK)
    ax.set_ylabel(ylabel, color=INK)
    ax.set_title(title, color=INK, fontsize=9.5, loc="left")
    ax.grid(color=GRID, linewidth=0.8, which="major")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, which="both")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3)


def plot_method(ax, d, column, method, absolute=False):
    label, color, marker, dash = STYLE[method]
    m = d[d["method"] == method].sort_values("N")
    y = m[column].abs() if absolute else m[column]
    if method == "cholmod_default":  # hollow and larger: it coincides with simplicial (N <= 80) or supernodal
        ax.plot(m["N"], y, color=color, marker=marker, markersize=10, markerfacecolor="none", markeredgewidth=2,
                linewidth=2, linestyle=dash, zorder=2.5, label=label)
        return
    ax.plot(m["N"], y, color=color, marker=marker, markersize=6, linewidth=2, linestyle=dash, zorder=3, label=label)


def guide(ax, Ns, values, label, dash):
    ax.plot(Ns, values, color=MUTED, linewidth=1.2, linestyle=dash, zorder=2, label=label)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()
    df = pd.read_csv(pathlib.Path(args.results) / "e07_baselines.csv")
    df = df[df["N"] <= 640]
    Ns = sorted(df["N"].unique())
    N = pd.Series(Ns, dtype=float)

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 6.4), dpi=150)
    for method in PANEL_A:
        plot_method(ax_a, df, "own_err_tiny", method, absolute=True)
    dt = df[df["method"] == "cholmod_default"].sort_values("N")
    ax_a.plot(dt["N"], dt["data_term_tiny"].abs(), color=INK, linewidth=1.5, linestyle=(0, (6, 2)), zorder=2,
              label="|data term| (u/4) cond_tiny")
    guide(ax_a, N, U * N, "guide u N", (0, (1, 2)))
    guide(ax_a, N, U * N ** 2, "guide u N^2", (0, (5, 2)))
    style_axes(ax_a, Ns, "|xhat - x_stored| / xhat at (1, 1, N-2)",
               "(a) Own error of a direct solve at the tiny entry: it depends on the algorithm")

    for method in PANEL_B:
        plot_method(ax_b, df, "max_true_err_in_u", method)
    guide(ax_b, N, N, "guide N", (0, (1, 2)))
    guide(ax_b, N, N ** 2, "guide N^2", (0, (5, 2)))
    style_axes(ax_b, Ns, "max_i |xhat_i - x_true_i| / xhat_i   (units of u)",
               "(b) Error against the true probability, every entry")

    fig.tight_layout()
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f07_baselines.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
