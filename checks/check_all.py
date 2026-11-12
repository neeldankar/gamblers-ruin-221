"""Chunk 11: run every checks/check_cNN.py and collect the results in results/final_report.md.
    python checks/check_all.py [--results DIR] [--baseline 5de66f4]

The report has: a summary table (PASS/WARN/FAIL/FLAG counts per chunk), the chunk 11 "Expected results" rows of
plan/c11_final_run.md, every WARN, FAIL and FLAG line, the run log (DIR/run_all_log.csv), the machine metadata,
and a table of changes against the CSVs committed at --baseline. That table is not judged here: the Project chat
reviews it.

Changes table rules:
  * Rows are matched by N (if the CSV has it), the text columns that name a row (method, kind, rhs, ...; not
    the ones that hold a result, such as *_state, status, solver), and the occurrence number within that key.
    Experiments write rows in a fixed order, so this pairs the same rows of the old and new CSV.
  * Every column except the metadata stamp, timings and memory is compared. Numbers: largest
    |new - old| / |old| (0 if equal or both NaN; inf if only one is NaN or old is 0). Text and booleans: the
    number of matched rows that differ. Changes above 1e-12 (or any differing text) are marked.
"""
import argparse
import io
import os
import pathlib
import re
import subprocess
import sys

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gr.runlog import git_hash, metadata  # noqa: E402

META = ["git_hash", "timestamp", "platform", "machine", "python", "numpy", "scipy", "omp_num_threads"]
LOG_NAME = "run_all_log.csv"
BIG_NAME = "e02_direct_big"  # optional e02 --big output, rerun separately with run_all.py --e02-big
LINE = re.compile(r"^(PASS|WARN|FAIL|FLAG)\s+(.*)$")
RESULT_TEXT = {"status", "solver", "corrections", "at_reference_accuracy"}  # text columns that are results
TOLERANCE = 1e-12
HOURS_MIN, HOURS_MAX = 2.0, 4.0
PEAK_LIMIT_MB = 4096


# ---------------------------------------------------------------- the per-chunk check scripts
def run_check_scripts(results):
    """[(chunk, script name, exit code, [(status, text)], stderr tail)] for every check_cNN.py."""
    out = []
    for script in sorted((ROOT / "checks").glob("check_c[0-9][0-9].py")):
        p = subprocess.run([sys.executable, str(script), "--results", str(results)], cwd=ROOT,
                           env=dict(os.environ, PYTHONPATH=str(ROOT), MPLBACKEND="Agg"), capture_output=True, text=True)
        lines = [m.groups() for m in map(LINE.match, p.stdout.splitlines()) if m]
        out.append((script.stem[-3:], script.name, p.returncode, lines, p.stderr[-2000:]))
        print(f"{script.name}: exit {p.returncode}, " + ", ".join(
            f"{sum(s == k for s, _ in lines)} {k}" for k in ("PASS", "WARN", "FAIL", "FLAG")), flush=True)
    return out


# ---------------------------------------------------------------- run log and CSV hashes
def latest_log_rows(results):
    """The last log row per script, in the order the scripts first appear."""
    path = results / LOG_NAME
    if not path.exists():
        return pd.DataFrame(columns=["script"])
    log = pd.read_csv(path)
    return log.groupby("script", sort=False).tail(1).set_index("script", drop=False)


def csv_hashes(results):
    """{csv stem: sorted list of its git hashes} for every results CSV except the run log."""
    return {p.stem: sorted(pd.read_csv(p, usecols=["git_hash"])["git_hash"].astype(str).unique())
            for p in sorted(results.glob("*.csv")) if p.name != LOG_NAME}


def chunk11_rows(checks, log, hashes, commit, changes_flagged):
    """(check, expected, observed, status) for each row of the chunk 11 Expected results table."""
    rows = []
    experiments = [p.stem for p in sorted((ROOT / "experiments").glob("e[0-9][0-9]_*.py"))]

    bad = []
    for name in experiments:
        if name not in log.index:
            bad.append(f"{name}: not in log")
            continue
        r = log.loc[name]
        if r["exit_code"] != 0 or str(r["quick"]) != "False" or str(r["git_hash"]) != commit:
            bad.append(f"{name}: exit {r['exit_code']}, quick {r['quick']}, git {r['git_hash']}")
    rows.append(("every experiment exits 0", "yes",
                 f"{len(experiments) - len(bad)} of {len(experiments)} full runs at git {commit} exit 0"
                 + (f"; {'; '.join(bad)}" if bad else ""), "FAIL" if bad else "PASS"))

    n_fail = sum(s == "FAIL" for c in checks for s, _ in c[3])
    crashed = [c[1] for c in checks if c[2] != 0 and not any(s == "FAIL" for s, _ in c[3])]
    rows.append(("every check script: no FAIL lines", "all PASS or WARN",
                 f"{n_fail} FAIL lines" + (f"; crashed: {', '.join(crashed)}" if crashed else ""),
                 "FAIL" if n_fail or crashed else "PASS"))

    n_warn = sum(s == "WARN" for c in checks for s, _ in c[3])
    rows.append(("WARN lines", "only timing rows and rows the chunk specs mark as machine-dependent",
                 f"{n_warn} WARN lines, listed below for review", "WARN" if n_warn else "PASS"))

    big_note = ""
    checked = dict(hashes)
    if BIG_NAME in checked and checked[BIG_NAME] != [commit]:
        big_note = (f"; {BIG_NAME}.csv left out: the e02 --big rerun was skipped, the file is from git "
                    f"{', '.join(checked[BIG_NAME])}, and no check or figure reads it")
        del checked[BIG_NAME]
    all_hashes = sorted({h for hs in checked.values() for h in hs})
    others = [f"{k} ({', '.join(v)})" for k, v in checked.items() if v != [commit]]
    rows.append(("one git hash across all CSVs", "yes",
                 f"{len(checked)} CSVs, hashes {all_hashes}" + (f"; not at {commit}: {', '.join(others)}" if others
                                                                else "") + big_note,
                 "PASS" if all_hashes == [commit] and "dirty" not in commit else "FAIL"))

    main = log[log["script"].isin(experiments)] if len(log) else log
    hours = float(main["seconds"].sum()) / 3600 if len(main) else float("nan")
    rows.append(("total run time", "2-4 h (sum of the chunk compute times with 5 repeats)", f"{hours:.2f} h",
                 "PASS" if HOURS_MIN <= hours <= HOURS_MAX else "WARN"))

    if len(main):
        peak = main.loc[main["peak_mb"].idxmax()]
        observed, ok = f"{peak['peak_mb']:.0f} MB ({peak['script']})", peak["peak_mb"] < PEAK_LIMIT_MB
    else:
        observed, ok = "no log rows", False
    if BIG_NAME in log.index:
        observed += f"; {BIG_NAME} (not counted): {log.loc[BIG_NAME, 'peak_mb']:.0f} MB"
    rows.append(("peak memory", "under 4 GB without chunk 9's `--big`", observed, "PASS" if ok else "WARN"))

    rows.append(("results equal to the per-chunk runs", "fill counts, iteration counts and errors identical or "
                 "within the per-chunk tolerances; only times move",
                 f"{changes_flagged} columns changed by more than {TOLERANCE:g}; see the changes table "
                 "(for review in the Project chat)", "WARN" if changes_flagged else "PASS"))
    return rows


# ---------------------------------------------------------------- changes against the baseline commit
def is_timing_or_memory(col):
    return bool(re.search(r"time|second|speedup|rss|mem|_mb|MB", col)) or col.endswith("_s")


def key_columns(df):
    text = [c for c in df.columns if c not in META and not is_numeric_dtype(df[c])]
    return (["N"] if "N" in df.columns else []) + [c for c in text if c not in RESULT_TEXT and "state" not in c]


def keyed(df, keys):
    """df indexed by (key columns as text, occurrence number within that key)."""
    k = df[keys].astype(object).fillna("").astype(str) if keys else pd.DataFrame(index=df.index)
    k["occurrence"] = k.groupby(keys).cumcount() if keys else np.arange(len(df))
    return df.set_index(pd.MultiIndex.from_frame(k))


def rel_change(old, new):
    old, new = old.astype(float), new.astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = np.abs(new - old) / np.abs(old)
    rel = np.where(old == new, 0.0, rel)
    rel = np.where(np.isnan(old) & np.isnan(new), 0.0, rel)
    rel = np.where(np.isnan(old) ^ np.isnan(new), np.inf, rel)
    return np.where(np.isnan(rel), np.inf, rel)


def where(label, keys):
    names = keys + ["occurrence"]
    return ", ".join(f"{k}={v}" for k, v in zip(names, label if isinstance(label, tuple) else (label,)))


def baseline_csv(baseline, name):
    p = subprocess.run(["git", "show", f"{baseline}:results/{name}.csv"], cwd=ROOT, capture_output=True, text=True)
    return pd.read_csv(io.StringIO(p.stdout)) if p.returncode == 0 else None


def compare(results, baseline):
    """(table rows, notes): table rows are (csv, column, rows compared, change, where, flagged)."""
    table, notes = [], []
    for path in sorted(results.glob("*.csv")):
        if path.name == LOG_NAME:
            continue
        new, old = pd.read_csv(path), baseline_csv(baseline, path.stem)
        if old is None:
            notes.append(f"{path.name}: new CSV (not at {baseline})")
            continue
        keys = key_columns(new)
        if keys != key_columns(old):
            notes.append(f"{path.name}: key columns differ (old {key_columns(old)}, new {keys}); rows by position")
            keys = []
        o, n = keyed(old, keys), keyed(new, keys)
        common = o.index.intersection(n.index, sort=False)
        if len(o) - len(common) or len(n) - len(common):
            notes.append(f"{path.name}: {len(n) - len(common)} rows added, {len(o) - len(common)} rows removed "
                         f"({len(common)} matched)")
        added = [c for c in new.columns if c not in old.columns]
        removed = [c for c in old.columns if c not in new.columns]
        if added:
            notes.append(f"{path.name}: new columns {added}")
        if removed:
            notes.append(f"{path.name}: removed columns {removed}")
        for col in new.columns:
            if col in META or col in keys or col in added or is_timing_or_memory(col):
                continue
            a, b = o.loc[common, col], n.loc[common, col]
            numeric = all(is_numeric_dtype(s) for s in (old[col], new[col]))
            if numeric:
                rel = rel_change(a.to_numpy(), b.to_numpy())
                i = int(np.argmax(rel)) if len(rel) else 0
                worst = float(rel[i]) if len(rel) else 0.0
                table.append((path.name, col, len(common), f"{worst:.2e}", where(common[i], keys) if worst else "",
                              worst > TOLERANCE))
            else:
                differ = a.astype(object).fillna("").astype(str).to_numpy() != b.astype(object).fillna("").astype(str).to_numpy()
                first = where(common[int(np.argmax(differ))], keys) if differ.any() else ""
                table.append((path.name, col, len(common), f"{int(differ.sum())} rows differ (text)", first,
                              bool(differ.any())))
    return table, notes


# ---------------------------------------------------------------- report
def md_table(header, rows):
    return ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)] + [
        "| " + " | ".join(str(x).replace("|", "/") for x in r) + " |" for r in rows]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--baseline", default="5de66f4")
    args = parser.parse_args()
    results = pathlib.Path(args.results)
    commit = git_hash()

    checks = run_check_scripts(results)
    log = latest_log_rows(results)
    hashes = csv_hashes(results)
    table, notes = compare(results, args.baseline)
    flagged = [r for r in table if r[5]]
    c11 = chunk11_rows(checks, log, hashes, commit, len(flagged))

    meta = metadata()
    try:
        ram = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout) / 2**30
        meta["total_ram_gb"] = f"{ram:.0f}"
    except ValueError:
        pass

    lines = ["# Chunk 11: final report", "",
             f"Results: `{results}`; code at git {commit}; generated {meta['timestamp']}.", "",
             "## Summary", ""]
    summary = []
    for chunk, name, code, found, _ in checks:
        counts = [sum(s == k for s, _ in found) for k in ("PASS", "WARN", "FAIL", "FLAG")]
        summary.append((chunk, name, *counts, code))
    summary.append(("c11", "check_all.py", *[sum(r[3] == k for r in c11) for k in ("PASS", "WARN", "FAIL")], 0, ""))
    lines += md_table(["Chunk", "Script", "PASS", "WARN", "FAIL", "FLAG", "Exit"], summary)
    lines += ["", "FLAG lines are the chunk specs' red-flag checks (not counted as FAIL).", "",
              "## Chunk 11 expected results", ""]
    lines += md_table(["Check", "Expected", "Observed", "Status"], c11)

    lines += ["", "## WARN, FAIL and FLAG lines", ""]
    listed = [(chunk, s, text) for chunk, _, _, found, _ in checks for s, text in found if s != "PASS"]
    lines += [f"- {chunk} **{s}** {text}" for chunk, s, text in listed] or ["None."]
    for chunk, name, code, found, err in checks:
        if code != 0 and not any(s == "FAIL" for s, _ in found):
            lines += ["", f"{name} exited {code} without FAIL lines; stderr:", "", "```", err, "```"]

    lines += ["", "## Run log", "", f"Last row per script from `{results / LOG_NAME}`.", ""]
    cols = ["script", "start", "end", "seconds", "exit_code", "peak_mb", "free_mem_mb_start", "quick", "repeats",
            "git_hash"]
    lines += (md_table(cols, log[cols].itertuples(index=False)) if len(log) else ["No run log."])

    lines += ["", "## Machine", ""] + [f"- {k}: {v}" for k, v in meta.items() if k not in ("git_hash", "timestamp")]

    lines += ["", f"## Changes against the previous run (git {args.baseline})", "",
              f"Each CSV in `{results}` against `git show {args.baseline}:results/<name>.csv`. Timings, memory, "
              "git_hash and timestamp are left out. Rows are matched by N, the text columns that name a row, and "
              "the occurrence number within that key. Numbers: largest |new - old| / |old|. Text and booleans: "
              f"rows that differ. Not judged here.", "", f"### Changed by more than {TOLERANCE:g}", ""]
    lines += (md_table(["CSV", "Column", "Rows", "Largest change", "Where"], [r[:5] for r in flagged])
              if flagged else ["None."])
    lines += ["", "### Rows, columns and CSVs added or removed", ""] + ([f"- {x}" for x in notes] or ["None."])
    lines += ["", "### Every compared column", ""]
    lines += md_table(["CSV", "Column", "Rows", "Largest change", "Where", "Changed"],
                      [(*r[:5], "**changed**" if r[5] else "") for r in table])
    lines.append("")

    report = results / "final_report.md"
    report.write_text("\n".join(lines))
    for c, _, o, s in c11:
        print(f"{s:4s}  {c}: {o}")
    print(f"{len(flagged)} columns changed by more than {TOLERANCE:g} against {args.baseline}")
    print(f"wrote {report}")
    return 1 if any(r[3] == "FAIL" for r in c11) else 0


if __name__ == "__main__":
    sys.exit(main())
