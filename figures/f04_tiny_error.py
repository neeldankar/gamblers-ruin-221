"""Figure for chunk 4: relative error of the tiny entry against the CG stopping tolerance, N = 640.

One line per CG kind (none, mic0, amg) and two horizontal marks:
  * the stored-data term |data_term_tiny| = (u/4) cond_tiny (e04_errors): storing 1/6 in float64 moves the tiny
    entry by this much, so it is the accuracy of the reference (a direct solve of the stored system);
  * the a posteriori bound max_i (omega + 8u) cond_i for the direct solve (e04_condition, column aposteriori_bound).
Points flagged at_reference_accuracy (error below 10 |data_term_tiny|) are drawn hollow: their error cannot be told
apart from the reference's own. Uses the largest N in the CSV if N = 640 is missing (--quick).
Reads results/e04_errors.csv and results/e04_condition.csv only.
    python figures/f04_tiny_error.py [--results DIR] [--outdir DIR]
"""
import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
STYLE = {"none": ("#2a78d6", "o"), "mic0": ("#eda100", "D"), "amg": ("#e87ba4", "^")}  # f03 colors per kind


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()
    results = pathlib.Path(args.results)
    err = pd.read_csv(results / "e04_errors.csv")
    cond = pd.read_csv(results / "e04_condition.csv")
    N = 640 if 640 in set(err["N"]) else int(err["N"].max())
    d = err[err["N"] == N]
    cg = d[d["method"] == "cg"]

    fig, ax = plt.subplots(figsize=(7.5, 5), dpi=150)
    for kind, (color, marker) in STYLE.items():
        e = cg[cg["kind"] == kind].sort_values("rtol")
        if len(e):
            ax.plot(e["rtol"], e["rel_err_tiny"], color=color, linewidth=2, label=f"CG, {kind}", zorder=3)
            hollow = e["at_reference_accuracy"].astype(str) == "True"
            ax.plot(e["rtol"][~hollow], e["rel_err_tiny"][~hollow], color=color, marker=marker, markersize=5,
                    linestyle="none", zorder=4)
            ax.plot(e["rtol"][hollow], e["rel_err_tiny"][hollow], color=color, marker=marker, markersize=6,
                    markerfacecolor="white", linestyle="none", zorder=4)

    dt = d["data_term_tiny"].abs()
    if len(dt):
        ax.axhline(float(dt.iloc[0]), color=MUTED, linewidth=1.5, linestyle=(0, (5, 2)), zorder=2,
                   label=rf"stored-data term (u/4) cond$_{{tiny}}$: accuracy of the reference ({float(dt.iloc[0]):.1e})")
    ab = cond[(cond["N"] == N) & (cond["event"] == "out_first_3")]["aposteriori_bound"]
    if len(ab):
        ax.axhline(float(ab.iloc[0]), color=INK, linewidth=1.2, linestyle=(0, (1, 2)), zorder=2,
                   label=f"a posteriori bound for the direct solve ({float(ab.iloc[0]):.1e})")
    ax.plot([], [], color=MUTED, marker="o", markerfacecolor="white", linestyle="none",
            label="hollow: error below 10x the reference's accuracy")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.invert_xaxis()  # tighter tolerance to the right
    ax.set_xlabel("CG stopping tolerance rtol (||r|| <= rtol ||b||)", color=INK)
    ax.set_ylabel("relative error of the tiny entry", color=INK)
    reference = d["reference"].iloc[0] if len(d) else ""
    ax.set_title(f"N = {N}, P(player 3 out first) at (1, 1, N-2); reference: {reference} solve",
                 color=INK, fontsize=10, loc="left")
    ax.grid(color=GRID, linewidth=0.8, which="major")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, which="both")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper right")
    fig.tight_layout()
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "f04_tiny_error.png"
    fig.savefig(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
