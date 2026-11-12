"""Chunk 11: run every figure script (figures/fNN_*.py) from the CSVs in --results.
    python figures/make_all.py [--results DIR] [--outdir DIR]
Runs them all even if one fails, lists the failures, and exits 1 if there were any.
"""
import argparse
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--outdir", default="figures")
    args = parser.parse_args()

    env = dict(os.environ, PYTHONPATH=str(ROOT), MPLBACKEND="Agg")
    failed = []
    for script in sorted((ROOT / "figures").glob("f[0-9][0-9]_*.py")):
        p = subprocess.run([sys.executable, str(script), "--results", args.results, "--outdir", args.outdir],
                           cwd=ROOT, env=env, capture_output=True, text=True)
        print(f"{'ok  ' if p.returncode == 0 else 'FAIL'}  {script.name}  {p.stdout.strip().splitlines()[-1:]}",
              flush=True)
        if p.returncode != 0:
            print(p.stderr[-3000:], flush=True)
            failed.append(script.name)
    print(f"{len(failed)} figure script(s) failed: {failed}" if failed else "every figure script ran")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
