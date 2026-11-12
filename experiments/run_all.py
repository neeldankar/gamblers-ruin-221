"""Chunk 11: run every experiment, in chunk order, one subprocess each, and log each run.

    python experiments/run_all.py                  full run into results/ (needs gr/ and experiments/ committed)
    python experiments/run_all.py --quick          quick sizes into /tmp/c11quick (never into results/)
    python experiments/run_all.py --e02-big        only e02_direct.py --big (writes only e02_direct_big.csv)
Options: --only e03,e04  --skip e09  --force  --repeats 5  --outdir DIR

Each experiment runs as `peak_wrapper.py OUT.json python eNN_*.py [--quick] --outdir DIR` with GR_REPEATS set,
so its peak memory is its own. One row per experiment is appended to DIR/run_all_log.csv as soon as it ends.
Resume rule: without --force, an experiment is skipped only if the log already has a row for it with exit code 0,
quick False and the current git hash, so a full run interrupted at 3 a.m. picks up where it stopped. The run stops
at the first experiment that fails.
"""
import argparse
import csv
import datetime
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gr.runlog import free_memory_mb, git_hash  # noqa: E402

EXPERIMENTS = ROOT / "experiments"
WRAPPER = EXPERIMENTS / "peak_wrapper.py"
QUICK_OUTDIR = "/tmp/c11quick"
LOG_NAME = "run_all_log.csv"
LOG_COLUMNS = ["script", "start", "end", "seconds", "exit_code", "peak_mb", "free_mem_mb_start", "quick",
               "repeats", "git_hash"]


def matches(stem, tokens):
    """True if a token is the script's stem (e03_krylov) or its chunk prefix (e03)."""
    return any(stem == t or stem.split("_")[0] == t for t in tokens)


def planned_runs(args):
    """(log name, command arguments after `python`) for every experiment this run should consider."""
    if args.e02_big:
        return [("e02_direct_big", [str(EXPERIMENTS / "e02_direct.py"), "--big"])]
    runs = []
    for script in sorted(EXPERIMENTS.glob("e[0-9][0-9]_*.py")):
        if args.only and not matches(script.stem, args.only):
            continue
        if args.skip and matches(script.stem, args.skip):
            continue
        runs.append((script.stem, [str(script)] + (["--quick"] if args.quick else [])))
    return runs


def read_log(path):
    if not path.exists():
        return []
    with open(path) as fh:
        return list(csv.DictReader(fh))


def already_done(log, name, commit):
    return any(r["script"] == name and r["exit_code"] == "0" and r["quick"] == "False" and r["git_hash"] == commit
               for r in log)


def append_log(path, row):
    new = not path.exists()
    with open(path, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=LOG_COLUMNS)
        if new:
            writer.writeheader()
        writer.writerow(row)


def run_one(name, command, outdir, env, quick):
    """Run one experiment through the wrapper; return its log row."""
    free_mb = free_memory_mb()
    start = datetime.datetime.now()
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory() as tmp:
        result = pathlib.Path(tmp) / "peak.json"
        subprocess.run([sys.executable, str(WRAPPER), str(result), sys.executable, *command, "--outdir", str(outdir)],
                       cwd=ROOT, env=env)
        try:
            measured = json.loads(result.read_text())
        except (OSError, ValueError):  # the wrapper itself died (for example killed by the OS)
            measured = {"exit_code": -1, "peak_mb": float("nan")}
    seconds = time.perf_counter() - t0
    return {"script": name, "start": start.isoformat(timespec="seconds"),
            "end": datetime.datetime.now().isoformat(timespec="seconds"), "seconds": round(seconds, 1),
            "exit_code": measured["exit_code"], "peak_mb": round(measured["peak_mb"], 1),
            "free_mem_mb_start": round(free_mb), "quick": quick, "repeats": env["GR_REPEATS"],
            "git_hash": git_hash()}


def print_table(rows):
    print(f"\n{'script':18s} {'seconds':>9s} {'peak MB':>9s} {'exit':>5s}")
    for r in rows:
        print(f"{r['script']:18s} {r['seconds']:9.1f} {r['peak_mb']:9.1f} {r['exit_code']:5d}")
    print(f"{'total':18s} {sum(r['seconds'] for r in rows):9.1f}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default=None, help=f"default results, or {QUICK_OUTDIR} with --quick")
    parser.add_argument("--only", type=lambda s: s.split(","), default=None)
    parser.add_argument("--skip", type=lambda s: s.split(","), default=None)
    parser.add_argument("--force", action="store_true", help="rerun even if the log says it is done")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--e02-big", action="store_true", help="run only e02_direct.py --big")
    args = parser.parse_args()
    if args.quick and args.e02_big:
        sys.exit("--e02-big has no quick mode")

    results = (ROOT / "results").resolve()
    outdir = pathlib.Path(args.outdir or (QUICK_OUTDIR if args.quick else ROOT / "results")).resolve()
    if args.quick and outdir == results:
        sys.exit("refusing: a --quick run must not write into results/ (use a scratch --outdir)")
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "gr", "experiments"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    if dirty and not args.quick:
        sys.exit(f"refusing: uncommitted changes in gr/ or experiments/; commit them first:\n{dirty}")
    if dirty:
        print(f"warning: uncommitted changes in gr/ or experiments/ (fine for --quick):\n{dirty}", flush=True)

    outdir.mkdir(parents=True, exist_ok=True)
    log_path = outdir / LOG_NAME
    commit = git_hash()
    env = dict(os.environ, PYTHONPATH=str(ROOT), GR_REPEATS=str(args.repeats), MPLBACKEND="Agg")
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        env[var] = "1"
    print(f"run_all: git {commit}, repeats {args.repeats}, quick {args.quick}, outdir {outdir}", flush=True)

    rows = []
    for name, command in planned_runs(args):
        if not args.force and not args.quick and already_done(read_log(log_path), name, commit):
            print(f"--- {name}: already done at git {commit}, skipping (use --force to rerun)", flush=True)
            continue
        print(f"\n=== {name}  ({datetime.datetime.now():%H:%M:%S})", flush=True)
        row = run_one(name, command, outdir, env, args.quick)
        append_log(log_path, row)
        rows.append(row)
        print(f"=== {name}: exit {row['exit_code']}, {row['seconds']:.0f} s, peak {row['peak_mb']:.0f} MB", flush=True)
        if row["exit_code"] != 0:
            print_table(rows)
            sys.exit(f"stopped: {name} failed with exit code {row['exit_code']}")
    print_table(rows)
    print(f"log: {log_path}")


if __name__ == "__main__":
    main()
