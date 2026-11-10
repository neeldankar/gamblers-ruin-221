"""Figure for chunk 4: relative error of the tiny entry against the CG stopping tolerance, N = 640.

One line per CG kind (none, mic0, amg), the prediction cond_tiny * rtol (grey dashed), and two horizontal
marks for the direct solver: SuperLU's tiny-entry error against the CHOLMOD reference (the cholmod row is its
own reference at N >= 160, so it has error 0), and the certified first-order bound max_i cond_i omega_direct
from e04_condition. Uses the largest N in the CSV if N = 640 is missing (--quick).
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
            ax.plot(e["rtol"], e["rel_err_tiny"], color=color, marker=marker, linewidth=2, markersize=5,
                    label=f"CG, {kind}", zorder=3)
    e = cg.drop_duplicates("rtol").sort_values("rtol")
    ax.plot(e["rtol"], e["cond_times_rtol"], color=MUTED, linewidth=1.5, linestyle=(0, (5, 2)),
            label=r"prediction cond$_{tiny}$ $\times$ rtol", zorder=2)

    splu = d[d["method"] == "splu"]["rel_err_tiny"]
    if len(splu) and float(splu.iloc[0]) > 0:
        ax.axhline(float(splu.iloc[0]), color=INK, linewidth=1.2,
                   label=f"direct: SuperLU vs CHOLMOD ({float(splu.iloc[0]):.1e})", zorder=2)
    cb = cond[(cond["N"] == N) & (cond["event"] == "out_first_3")]["certified_bound"]
    if len(cb):
        ax.axhline(float(cb.iloc[0]), color=INK, linewidth=1.2, linestyle=(0, (1, 2)),
                   label=rf"direct: certified bound max$_i$ cond$_i$ $\omega$ ({float(cb.iloc[0]):.1e})", zorder=2)

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
