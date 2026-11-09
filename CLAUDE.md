# Math 221 project: three-player gambler's ruin as a sparse linear system

Neel Dankar and David Heli Collin, Fall 2026 (instructor Ming Gu). Main question: can solvers compute
tiny absorption probabilities to full relative accuracy, and which stopping rules make that work?
Supporting: solvers predicted vs observed (exact spectrum), ICM error, four players.

## The model
Three players hold chips (x1, x2, x3), sum N. Each round one of the 6 ordered pairs (a, b) is chosen
with probability 1/6 and one chip moves from b to a. A player at 0 is out; the other two then play fair
two-player ruin (P(win) = stack/N). Live states: all xi >= 1, so n = (N-1)(N-2)/2.
A = I - Q, Q = transient-to-transient transitions. A is sparse SPD, <= 7 nonzeros per row.

## Notation
- Order "ijk" = i out first, j out second, k wins (Diaconis-Ethier notation).
- P_x(ijk) solves A u = b with boundary value y_k/N on absorbing states where y_i = 0 (0 elsewhere).
- Relabeling: P_x(ijk) = u_123(x_i, x_j, x_k), so one solve gives all six orders.
- States ordered lexicographically by (x1, x2). State indexing lives ONLY in gr/states.py.

## How work is organized
The project is split into chunks. plan/README.md has the chunk index, the loop and the conventions; each chunk
has a spec plan/cNN_*.md (what to build, experiments, expected results, red flags) and acceptance tests in
tests/cNN_*/ that were validated against an independent reference implementation before you started. They
skip until the chunk's module exists. A session normally starts with "Do chunk NN. Read CLAUDE.md and
plan/cNN_*.md, then follow the spec exactly." For each chunk: build the module(s) the spec names (exact
names and signatures), make `pytest tests/c00_core ... tests/cNN_*` pass, run the experiments, write
checks/check_cNN.py from the spec's "Expected results" table (ranges copied exactly; print PASS/WARN/FAIL
honestly), save the output to results/cNN_report.md, log decisions in notes/decisions.md, commit.

## Rules
- Tests come first. No solver is benchmarked until it passes every test in tests/.
- NEVER edit anything in tests/ or plan/ to make something pass. If a test or an expected range looks wrong,
  stop and say why; it changes only after a sanity check in the Project chat.
- Every number in the report comes from a script in experiments/ that writes a CSV to results/
  (with git hash, machine info, library versions). No hand-typed numbers.
- Figures are generated only from results/*.csv by scripts in figures/.
- Benchmarks: fixed thread count, setup timed separately from solve, median of 3+ runs,
  same stopping rule for all iterative methods, report forward error not just residual.
- Never benchmark CG only on b = 1 (it finishes in ~N/2 steps by symmetry); also use random b
  and the real probability right-hand sides.
- Keep code simple and readable; Neel needs to understand and present every line of gr/.
- Log decisions (what was tried, what was decided, why) in notes/decisions.md.
- Commit order for every chunk: first commit the code and check script once the tests pass, then run the
  experiments (so CSVs carry a clean git hash), then commit the results and report in a second commit.

## Stack
Python 3.13 via conda (environment.yml): numpy, scipy (cg/gmres take rtol, not tol), pyamg
(its solve still takes tol), numba, scikit-sparse (CHOLMOD), python-flint or fractions for exact
solves. SciPy has no sparse or incomplete Cholesky; spilu is not a valid CG preconditioner.
- scikit-sparse 0.5 API: `sksparse.cholmod.cho_factor(A, order="amd")` returns a factor with `.solve(b)`
  and `.nnz`; `cholesky(A)` now returns a tuple, so the old `cholesky(A)(b)` pattern fails.
- `scipy.sparse.linalg.spsolve_triangular` is about 10x slower than a numba loop here; use numba for
  triangular solves inside iterations, and warm numba up on a tiny problem before timing.
- `np.longdouble` is float64 on Apple Silicon: never rely on it for extra precision. Extra precision comes from
  error-free transformations (chunk 7) or exact rationals (python-flint, N <= 80).
- Experiments take `--quick` and `--outdir`, pin threads before importing numpy, and seed with
  `np.random.default_rng(221)`.
- Always run Python through the gr221 env (conda run -n gr221 or its python directly); plain python may
  point at Homebrew.

## Commands
- conda env create -f environment.yml && conda activate gr221
- pytest -q                        run all tests (chunks not built yet are skipped)
- pytest tests/c00_core tests/c03_krylov   run the tests for one chunk plus the core
- python experiments/<name>.py [--quick]   run one experiment
- python checks/check_cNN.py       compare a chunk's CSVs with its expected results
- caffeinate -i python ...         keep the Mac awake for long runs
