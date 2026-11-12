"""Results logger: every experiment writes its CSV through save_results, which stamps each row
with the git commit, machine and library versions, so every number can be traced to its source."""
import csv
import datetime
import os
import pathlib
import platform
import re
import subprocess

import numpy as np
import scipy

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def git_hash():
    """Short commit hash, with "-dirty" if gr/ or experiments/ have uncommitted (or untracked) changes."""
    try:
        h = _git("rev-parse", "--short", "HEAD")
        if _git("status", "--porcelain", "--", "gr", "experiments"):
            h += "-dirty"
        return h
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def metadata():
    return {
        "git_hash": git_hash(),
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS", "unset"),
    }


def repeats():
    """Number of timing repeats: 3 by default, GR_REPEATS=5 in the chunk 11 final run (set by run_all.py)."""
    return int(os.environ.get("GR_REPEATS", 3))


def free_memory_mb():
    """Memory the OS can hand out now: free + inactive + speculative pages (macOS), MemAvailable (Linux)."""
    try:
        text = subprocess.run(["vm_stat"], capture_output=True, text=True, check=True).stdout
        page = int(re.search(r"page size of (\d+) bytes", text).group(1))
        pages = {k: int(v) for k, v in re.findall(r"Pages (\w+):\s+(\d+)\.", text)}
        return page * (pages["free"] + pages["inactive"] + pages["speculative"]) / 2**20
    except (OSError, subprocess.CalledProcessError, AttributeError, KeyError):
        with open("/proc/meminfo") as fh:
            return int(re.search(r"MemAvailable:\s+(\d+) kB", fh.read()).group(1)) / 2**10


def save_results(rows, name, outdir="results"):
    """Write rows (a list of dicts) to outdir/name.csv, each row stamped with metadata()."""
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    meta = metadata()
    stamped = [{**row, **meta} for row in rows]
    fields = list(dict.fromkeys(key for row in stamped for key in row))  # first-seen order
    path = outdir / f"{name}.csv"
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(stamped)
    return path
