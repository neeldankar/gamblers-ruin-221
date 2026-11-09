# Chunk 11: Final benchmark run and figures

- **Depends on:** every earlier chunk you are keeping (chunk 10 is optional)
- **Learn first:** nothing new; reread the "Expected results" tables of chunks 1-10
- **Time:** build 45-60 min · compute 2-4 h (full run, overnight), 10-15 min (`--quick`) · your review about
  1.5 h · plug in: **yes, overnight** · memory: the largest single experiment, about 3 GB (5-6 GB only if you
  include chunk 9's `--big`)
- **Read this yourself:** `experiments/run_all.py` and the final report it produces

## Goal

One reproducible run, from a clean commit, that regenerates every CSV and figure at full size with 5 timing
repeats, re-runs every check script, and leaves a single summary you can trust for the report. Nothing in the
report may come from an earlier, partial run.

## What to build

- `gr/runlog.py`: add `repeats() -> int`, returning `int(os.environ.get("GR_REPEATS", 3))`, and use it in every
  experiment that times something (replace hard-coded 3s).
- Every figure script takes `--results DIR` (default `results`) and `--outdir DIR` (default `figures`).
  Every experiment already takes `--quick` and `--outdir` (README conventions); fix any that do not.
- `experiments/run_all.py`: runs every `experiments/eNN_*.py` in chunk order as a subprocess with
  `GR_REPEATS=5` (or `--repeats`), logs one row per experiment to `results/run_all_log.csv` (script, start,
  end, seconds, exit code, peak memory from `resource.getrusage(RUSAGE_CHILDREN).ru_maxrss`, git hash), and
  stops on the first failure. Options: `--quick`, `--only e03,e04`, `--skip e09`, `--force`. Without `--force`
  it skips an experiment whose CSVs already carry the current git hash, so a run interrupted at 3 a.m. resumes.
  Refuse to start if `git status --porcelain` shows uncommitted changes in `gr/` or `experiments/`.
- `figures/make_all.py`: runs every figure script.
- `checks/check_all.py`: runs every `checks/check_cNN.py`, collects their PASS/WARN/FAIL lines into
  `results/final_report.md` with a summary table (counts per chunk), the run log, and the machine metadata.

## Running it on the Mac

1. Commit everything. `git status` must be clean.
2. Plug in, close other heavy apps, and run
   `caffeinate -i python experiments/run_all.py 2>&1 | tee results/run_all_console.txt`.
3. In the morning: `python figures/make_all.py && python checks/check_all.py`.
4. Commit the results as "chunk 11: final run".

Do a `--quick` run first (10-15 min) to catch crashes before the overnight run.

## Acceptance tests

`GR_PIPELINE=1 pytest tests/c11_pipeline -v` (opt-in, about 10-15 min). It runs every experiment with
`--quick --outdir <tmp>` and checks the exit code, that every CSV carries the metadata columns and a single git
hash, and that every figure script runs from those CSVs alone. Also run the whole normal suite: `pytest -q`.

## Expected results

| Check | Expected | Kind |
|---|---|---|
| every experiment exits 0 | yes | FAIL |
| every check script: no FAIL lines | all PASS or WARN | FAIL |
| WARN lines | only timing rows and rows the chunk specs mark as machine-dependent | WARN |
| one git hash across all CSVs | yes | FAIL |
| total run time | 2-4 h (sum of the chunk compute times with 5 repeats) | WARN |
| peak memory | under 4 GB without chunk 9's `--big` | WARN |
| results equal to the per-chunk runs | fill counts, iteration counts and errors identical or within the per-chunk tolerances; only times move | FAIL |

## Red flags (bring these to the Project chat)

- Any result that differs from its chunk's earlier run by more than that chunk's tolerance: something changed
  in `gr/` without a test catching it. Find the commit.
- The run dying from memory pressure: rerun the failing experiment alone and report its peak.

## Done when

- [ ] `pytest -q` and the pipeline test pass.
- [ ] `results/final_report.md` has no FAIL; committed with all CSVs and figures as "chunk 11: final run".

## Paste back into the Project chat

`results/final_report.md`.
