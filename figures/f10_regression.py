"""Figure for chunk 10, part A: one least-squares problem solved three ways, and the degree sweep.

Left: coefficient error relative to the SVD's, per order and method (normal equations lose about cond(X) more
digits than QR). Middle: the largest difference between each method's fitted values and the SVD's (all below
1e-8: the coefficient error lies along directions X barely sees). Right: the largest residual of the SVD fit
against the polynomial degree, with cond(X) under each degree.
Reads results/e10_regression.csv and results/e10_degree_sweep.csv only.
    python figures/f10_regression.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
ORDERS = ["321", "312", "213"]
METHODS = [("qr", "Householder QR", "#2a78d6", "o"),
           ("normal_equations", "normal equations", "#eb6834", "s"),
           ("ne_column_scaled", "normal eq., scaled columns", "#1baf7a", "D")]
ORDER_STYLE = dict(zip(ORDERS, [("#eda100", "o"), ("#e87ba4", "s"), ("#008300", "D")]))


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
    results = pathlib.Path(args.results)
    rg = pd.read_csv(results / "e10_regression.csv", dtype={"order": str})
    dg = pd.read_csv(results / "e10_degree_sweep.csv", dtype={"order": str})

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6), dpi=150)
    xs = range(len(ORDERS))
    for col, ax, ylabel, title in (
            ("coef_relerr_vs_svd", axes[0], "||beta - beta_SVD|| / ||beta_SVD||", "Coefficients differ"),
            ("fitted_maxdiff_vs_svd", axes[1], "max |X beta - X beta_SVD|", "Fitted values agree")):
        for k, (m, label, color, marker) in enumerate(METHODS):
            d = rg[rg["method"] == m].set_index("order")
            ax.plot([x + (k - 1) * 0.12 for x in xs], [d.loc[o, col] for o in ORDERS], linestyle="none",
                    marker=marker, markersize=8, color=color, label=label)
        ax.set_yscale("log")
        ax.set_xticks(list(xs))
        ax.set_xticklabels([f"order {o}" for o in ORDERS])
        ax.set_xlim(-0.5, len(ORDERS) - 0.5)
        ax.set_ylabel(ylabel, color=INK)
        ax.set_title(title, color=INK, fontsize=10, loc="left")
        style(ax)
    cond = rg["cond_X"].iloc[0]
    axes[0].set_title(f"Coefficients differ (sextic, cond(X) = {cond:.3g})", color=INK, fontsize=10, loc="left")
    axes[1].axhline(1e-8, color=INK, linewidth=1, linestyle=(0, (3, 2)))
    axes[1].text(len(ORDERS) - 0.55, 1.3e-8, "1e-8", color=MUTED, fontsize=8, ha="right")
    axes[0].legend(frameon=False, fontsize=8, labelcolor=INK, loc="lower left")

    ax = axes[2]
    for o in ORDERS:
        d = dg[dg["order"] == o].sort_values("degree")
        color, marker = ORDER_STYLE[o]
        ax.plot(d["degree"], d["max_abs_resid"], color=color, marker=marker, markersize=8, linewidth=2,
                label=f"order {o}")
    degs = sorted(dg["degree"].unique())
    conds = dg.drop_duplicates("degree").set_index("degree")["cond_X"]
    ax.set_xticks(degs)
    ax.set_xticklabels([f"{g}\n{conds[g]:.1e}" for g in degs])
    ax.set_yscale("log")
    ax.set_xlabel("polynomial degree (cond(X) below)", color=INK)
    ax.set_ylabel("max |residual| of the SVD fit", color=INK)
    ax.set_title("213 has a boundary layer no polynomial follows", color=INK, fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK, loc="lower left")
    style(ax)

    fig.tight_layout()
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f10_regression.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
