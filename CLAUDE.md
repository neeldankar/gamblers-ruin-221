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

## Rules
- Tests come first. No solver is benchmarked until it passes every test in tests/.
- NEVER edit a test to make it pass. If a test looks wrong, stop and ask.
- Every number in the report comes from a script in experiments/ that writes a CSV to results/
  (with git hash, machine info, library versions). No hand-typed numbers.
- Figures are generated only from results/*.csv by scripts in figures/.
- Benchmarks: fixed thread count, setup timed separately from solve, median of 3+ runs,
  same stopping rule for all iterative methods, report forward error not just residual.
- Never benchmark CG only on b = 1 (it finishes in ~N/2 steps by symmetry); also use random b
  and the real probability right-hand sides.
- Keep code simple and readable; Neel needs to understand and present every line of gr/.
- Log decisions (what was tried, what was decided, why) in notes/decisions.md.

## Stack
Python 3.13 via conda (environment.yml): numpy, scipy (cg/gmres take rtol, not tol), pyamg
(its solve still takes tol), numba, scikit-sparse (CHOLMOD), python-flint or fractions for exact
solves. SciPy has no sparse or incomplete Cholesky; spilu is not a valid CG preconditioner.

## Commands
- conda env create -f environment.yml && conda activate gr221
- pytest -q                        run all tests
- python experiments/<name>.py     run one experiment
