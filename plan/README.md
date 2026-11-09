# Project plan: chunks for Claude Code

Every chunk has a spec in this folder (`plan/cNN_*.md`) and acceptance tests in `tests/cNN_*/`.
The tests were written and checked against an independent reference implementation before you
started, so a correct implementation passes them. They are skipped until the chunk's module exists.

## The loop for each chunk

1. **Learn first** (optional but recommended): the Theory Guide sections listed at the top of the spec.
2. **Run it in Claude Code**, from the repo root:
   > Do chunk NN. Read CLAUDE.md and plan/cNN_*.md, then follow the spec exactly.
3. Claude Code builds the module(s) in the spec, makes `pytest tests/c00_core tests/cNN_*` pass, runs
   the experiment script(s), writes `checks/check_cNN.py` from the spec's "Expected results" table,
   runs it, saves the report to `results/cNN_report.md`, logs decisions in `notes/decisions.md`, and
   commits.
4. **You** read the report and the module code the spec marks "read this yourself".
5. **Paste `results/cNN_report.md` into the Claude Project chat** for a sanity check. Anything marked
   WARN or FAIL, or anything in the spec's "Red flags" list, goes there before you move on.

## Rules (also in CLAUDE.md)

- Never edit anything in `tests/` or `plan/`. If a test or an expected range looks wrong, stop and say
  why. Tests and expectations change only after a sanity check in the Project chat.
- No solver is benchmarked until it passes its tests.
- Every number in the report comes from a script in `experiments/` that writes a CSV to `results/`
  through `gr.runlog.save_results` (which stamps git hash, machine, versions, thread settings).
- Figures are made only from `results/*.csv`, by scripts in `figures/`.
- Check scripts copy the expected ranges from the spec exactly and print PASS, WARN or FAIL honestly.
  WARN = outside the range but plausibly machine noise (timings); FAIL = a correctness or theory miss.

## Chunk index

Times are for an Apple Silicon MacBook. "Build" is Claude Code's working time (you can do other
things). "Compute" is how long the experiment scripts run. Plug in whenever compute is over ~15 min.

| # | Chunk | Depends on | Build | Compute | Plug in | Target |
|---|---|---|---|---|---|---|
| 0 | Setup and core (done) | none | 0 | 1 min | no | Nov 9 |
| 1 | Exact spectrum and conditioning | 0 | 20-30 min | < 2 min | no | Nov 10 |
| 2 | Direct solvers and orderings | 1 | 45-60 min | 10-20 min, ~3 GB peak | yes | Nov 11-12 |
| 3 | Krylov methods and preconditioners | 1, 2 | 60-90 min | 10-20 min | recommended | Nov 13-14 |
| 4 | Accuracy I: diagnosing tiny probabilities | 2, 3 | 45-60 min | 5-15 min | optional | Nov 15-17 |
| - | Progress report talk | 1-4 | | | | Nov 20 |
| 5 | Stationary methods and the SOR 3/4 law | 1 | 45-60 min | 5-10 min, ~2 GB | no | Nov 21-22 |
| 6 | FFT fast solver | 1 | 30-45 min | 1-2 min, ~2.5 GB | no | Nov 23 |
| 7 | Accuracy II: three fixes and the right condition number | 4 (6 optional) | 60-90 min | 10-20 min, ~1.5 GB | yes | Nov 24-27 |
| 8 | ICM application | 0, 1 | 30-45 min | ~1 min | no | Nov 28-29 |
| 9 | Four players | 2, 3 | 60-90 min | 15-30 min, ~2.5 GB (`--big`: +15-20 min, 5-6 GB) | yes | Nov 30-Dec 3 |
| 10 | Extras (optional): regression, unequal skill | 8, 3 | 30-60 min | 2-5 min | no | Dec 4-5 |
| 11 | Final benchmark run and figures | all | 45-60 min | 2-4 h | yes (overnight) | Dec 6 |
| 12 | Report and final slides | 11 | 2-3 sessions | none | no | Dec 7-14 |

Final talk Dec 15, report Dec 18.

## Conventions every chunk follows

- Module code in `gr/`, one experiment per script in `experiments/eNN_name.py`, CSVs in `results/`.
- Experiments take `--quick` (small sizes, under a minute, for checking the pipeline) and run the full
  sizes by default. They also take `--outdir DIR` (default `results`), passed through to `save_results`,
  so the chunk 11 pipeline test can run them into a temporary folder.
- Thread pinning at the top of every experiment, before importing numpy:
  `os.environ.setdefault("OMP_NUM_THREADS", "1")` (and OPENBLAS, MKL, VECLIB_MAXIMUM_THREADS).
- Timings: setup and solve timed separately, median of 3 runs (5 in chunk 11).
- Random right-hand sides: `np.random.default_rng(221).standard_normal(n)` unless a spec says otherwise.
- Warm up numba functions on a tiny problem before timing them.
- scikit-sparse 0.5 API: `sksparse.cholmod.cho_factor(A, order=...)` returns a factor with `.solve(b)` and `.nnz`.
  The old pattern `cholesky(A)(b)` no longer works (`cholesky` now returns a tuple).
- Long runs on the Mac: `caffeinate -i python experiments/eNN_name.py` keeps it awake.
- `np.longdouble` is plain float64 on Apple Silicon. Never rely on it for extra precision.
