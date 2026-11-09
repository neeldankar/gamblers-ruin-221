# Decisions log

## 2026-11-03: phase 1, core and tests
- Built gr/states.py (lexicographic live states, lookup array), gr/matrix.py (A = I - Q vectorized
  over the 6 moves; right-hand sides from boundary values), gr/exact.py (independent Fraction code),
  gr/montecarlo.py (full-game simulation).
- Tests (46, all passing): state count; <= 7 nonzeros per row; symmetry; Q row sums = (6 - busts)/6;
  positive definiteness; N = 4 hand example (1/7, 3/7) and its six orders; float vs exact rationals for
  N <= 15 to 1e-12; closed forms t = 3x1x2x3/N and P(win) = xi/N at N = 10, 50, 200 and exactly in
  rationals; six orders sum to 1; relabeling identity vs direct solves; orders ending in k sum to xk/N;
  Diaconis-Ethier values (569/9456, Table 9 at (2,3,5), Table 4 at N = 300); Monte Carlo within 4 SE.
- Order probabilities use boundary value y_k/N on the face y_i = 0 (not an indicator): the order
  depends on the stacks at the moment of the first bust.
- The only solver so far is scipy's splu as a reference. Benchmarked solvers come in phase 2.


## Scaffold: chunks, specs and acceptance tests (Nov 9)
- Split the remaining work into chunks 1-12 (plan/README.md), each with a spec and pre-written acceptance tests.
- Every test was run against an independent reference implementation written outside this repo; the reference
  code is deliberately not included, so the implementation here is a second, independent one. Tests skip until
  their module exists (pytest.importorskip).
- Expected-result tables in each spec come from measurements on the reference (Linux container). Iteration
  counts and fill counts are deterministic; times are machine-dependent and therefore WARN-level only.
- Findings made while validating, now built into the specs: natural-order fill is exactly
  n + (N-3) + (N-1)(N-2)(N-3)/3; CG on b = 1 stops after exactly floor((N-1)/2) steps; MIC(0) has smallest
  preconditioned eigenvalue exactly 1; cond of the tiny entry is 2 E[T | event] ~ 0.388 N^2; CG's tiny-entry error
  is about cond_tiny * rtol; refinement with an accurate residual is correctly rounded; GTH is accurate to ~0.3 N u;
  the structured condition number (off-diagonals, row sums, b) is O(1); the tiny-entry constant is
  Gamma(1/3)^9 / (8 pi^4) = 9.1195890.


## Environment: python-flint from PyPI (Nov 9)
- environment.yml pinned `python-flint=0.9`, but conda-forge only has up to 0.8.0, so `conda env create` could
  not solve. PyPI has 0.9.0 with a cp313 macOS arm64 wheel.
- Decided: drop python-flint from the conda dependencies, add `pip`, and install `python-flint==0.9.0` through a
  pip subsection. Every other pin is unchanged and comes from conda-forge.
- Set up on Apple Silicon with Miniforge (Homebrew cask, conda 26.9.4). Versions: Python 3.13.18, numpy 2.5.4,
  scipy 1.18.1, pyamg 5.3.0, numba 0.68.1, scikit-sparse 0.5.0, python-flint 0.9.0. `pytest -q`: 46 passed, 17 skipped.


## Chunk 1 spec fix: N list (Nov 9)
- The chunk 1 check "kappa_inf_over_N2 = 2/9 when 3 divides N" had no data: none of N = 10, 20, 40, 80, 160,
  320, 640 is divisible by 3, so the check could never run.
- Sanity-checked in the Project chat. Decided: N list becomes {10, 20, 30, 40, 80, 90, 160, 300, 320, 640}
  (`--quick`: 10, 20, 30, 40), eigsh still capped at 320, and a new FAIL row: when 3 does not divide N,
  kappa_inf_over_N2 is below 2/9 and within 1% of it for N >= 40 (max x1 x2 x3 is then just under (N/3)^3;
  at N = 40 the ratio is 2366/2370.4 = 0.998).


## Chunk 1: exact spectrum (Nov 9)
- gr/spectrum.py implements the spec's formulas directly. lambda_max is attained at (k, l) = (1, N - 2)
  (checked by brute force for N = 10, 11, 12, 30, 31); the docstring derives the closed form from that mode.
- kappa_inf computes ||A||_inf from the matrix (max absolute row sum) instead of hard-coding 2: it is 5/3 at
  N = 5, where every live state has a coordinate equal to 1, and 2 for N >= 6. ||A^{-1}||_inf = max t because
  A^{-1} >= 0 and A^{-1} 1 = t = 3 x1 x2 x3 / N.
- jacobi_rate is literally 1 - lambda_min(N), so the 1e-15 check holds exactly.
- gr/runlog.py: git_hash is the short HEAD hash plus "-dirty" when gr/ or experiments/ have uncommitted or
  untracked changes. The chunk 1 CSV therefore says d67e602-dirty: it was produced by the code in the
  "chunk 1: exact spectrum" commit, run before that commit existed. Chunk 11's run_all refuses a dirty tree, so
  the final results will carry a clean hash. CSV floats are written with full repr precision.
- e01: eigsh time is the median of 3 calls with A built (and converted to CSC) outside the timer. Full run:
  eigsh at N = 320 takes 0.53 s; max relative difference from the formula 3.1e-13.
- check_c01.py: all 9 rows PASS. kappa2/N^2 at N = 640 is 2.7e-6 below 9/(8 pi^2), consistent with the
  -pi^2/(9 N^2) relative correction from expanding lambda_max/lambda_min. No red flags.
- The figure uses fixed x ticks at 10, 20, 40, ..., 640 (labels at 80/90 and 300/320 collided otherwise).
- The env has no `tabulate`, so check_c01 formats its markdown data table by hand instead of DataFrame.to_markdown.
