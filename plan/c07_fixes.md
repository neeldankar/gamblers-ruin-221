# Chunk 7: Accuracy II, three fixes and the right condition number

- **Depends on:** chunk 4 (and chunks 2-3 for the solvers)
- **Learn first:** Theory Guide §8 (stopping rules, iterative refinement, GTH, Alfa-Xue-Ye) and §1 (floating point, error-free transformations)
- **Time:** build 60-90 min · compute 10-20 min (full), about 1 min (`--quick`) · your review about 2 h ·
  plug in: yes for the full run · memory about 1.5 GB (GTH band storage at N = 640)
- **Read this yourself:** all of `gr/refine.py`; make sure you can explain why every operation in the GTH
  loop adds numbers of one sign

## Goal

Chunk 4 showed that normwise stopping misses the tiny probabilities. This chunk builds and measures three
fixes, and explains why the third one works so well:

1. **Componentwise stopping.** Stop CG when the Oettli-Prager backward error of the true residual is below a
   tolerance. CG can reach omega of about 1e-15 here, so the tiny entry ends up as accurate as with a direct
   solve, for 1.3 to 2 times the iterations of the usual rtol 1e-10 rule.
2. **Iterative refinement with an accurate residual.** 6N A and 6N b are integers, so b - A x can be computed
   to one rounding per entry with error-free transformations. Two refinement steps after a direct solve (or
   four with a sloppy rtol 1e-6 CG inner solve) give every entry correctly rounded: error 0 against exact
   rationals.
3. **GTH elimination.** Compute each pivot as (row sum) + (minus the off-diagonals) instead of by subtraction.
   Every entry comes out to about 0.3 N u (34 u at N = 80, 120 u at N = 400) against about 0.07 N^2 u for
   ordinary elimination.

Why 3 works: perturb the off-diagonal entries, the row sums and b relatively by eps, and the solution entries
move by only about 2 to 5 eps, at every N. The componentwise condition number from chunk 4 (0.39 N^2) measures
sensitivity to perturbations of A's entries, which is the wrong parametrization for an M-matrix (Alfa, Xue and
Ye). A subtraction-free algorithm is stable in the right parametrization.

## What to build (the tests import exactly these names)

`gr/refine.py`

- `integer_system(A, b, scale) -> (Ai, B)`: Ai = scale * A as CSR with sorted indices and exactly integer
  values, B = scale * b; `ValueError` if either is not integer to 1e-9. With scale = 6N the entries of Ai are
  6N and -N.
- `accurate_residual(A, b, x, scale) -> np.ndarray`: r = b - A x, computed as (B - Ai x) / scale where each
  product Ai_ij x_j is split exactly into hi + lo (TwoProduct by Dekker splitting; exact because |Ai_ij| < 2^26)
  and the row sum is accumulated with TwoSum, adding the lo parts and the TwoSum errors into a compensation
  term. One numba loop over rows. Each entry is then correct to about 2u (a final rounding and the division).
- `iterative_refinement(A, b, solve, scale, x0=None, max_steps=10) -> (x, info)`: x = solve(b) unless x0 is
  given; repeat r = accurate_residual(...), d = solve(r), x = x + d, correction = max_i |d_i| / |x_i|; stop when
  correction <= 4u. `info = {"steps", "corrections" (array, one per step), "converged"}`.
- `gth_solve(A, b, row_sums) -> np.ndarray`: for a symmetric M-matrix with row sums `row_sums` >= 0 (pass them
  in exactly, from `boundary_rhs(S, lambda Y: np.ones(len(Y)))`, not as A @ 1) and b >= 0. Natural order, band
  storage of the upper triangle (p = bandwidth), numba loops. For k = 0..n-1: pivot = s_k - sum_{j>k} a_kj (all
  terms >= 0); for each i > k in the band with a_ik != 0: l = a_ik / pivot (<= 0), s_i -= l s_k, and
  a_ij -= l a_kj for j > i (every update adds numbers of one sign). The diagonal is never updated by
  subtraction: it is recomputed from the row sum when its row becomes the pivot row. Then forward and backward
  substitution (also subtraction-free because b >= 0). `ValueError` if A has a positive off-diagonal entry, a
  row sum is negative, or b has a negative entry.
- `cg_componentwise(A, b, tol, M=None, check_every=10, maxiter=None) -> (x, info)`: the CG recurrence of
  `gr.krylov.cg` with x0 = 0, but the stopping test is omega(x_k) = componentwise_backward_error(A, x_k, b) <= tol,
  evaluated at k = 0 and every `check_every` iterations (the true residual costs one extra product).
  `info = {"iterations", "omegas" (array: k = 0, check_every, 2 check_every, ...), "converged"}`.

## Experiments

`experiments/e07_fixes.py` -> `results/e07_fixes.csv`. b = rhs_out_first(S, 2). N in {20, 40, 60, 80} with
reference = `flint_solve` ("exact"), and N in {160, 320, 640, 1280} with reference = iterative refinement after
the CHOLMOD nesdis solve ("refined"; it is correctly rounded at N <= 80, which the exact rows show). Methods:
`direct` (CHOLMOD nesdis), `gth` (N <= 640), `cg` at rtol 1e-10 and `cg_componentwise` at tol 1e-12 and 1e-14 for
kinds none (check_every 10), mic0 (5) and amg (1), `ir_direct`, `ir_cg_mic0` and `ir_cg_amg` (inner CG at rtol
1e-6, max_steps 15). Columns: `N, method, kind, param, iterations_or_steps, seconds, reference, rel_err_tiny,
max_rel_err, max_rel_err_in_u, omega, cond_tiny`. `--quick`: N in {20, 40}.

`experiments/e07_fft_check.py` -> `results/e07_fft_check.csv` (needs chunk 6's `gr.fft_solver`; skip with a
message if it is missing). Chunk 6 found that for b = rhs_order(S, 0, 1, 2) (order 123) the FFT and splu
disagree at the smallest entry, the state (N-2, 1, 1), by 6e-7 to 2e-6 at N = 800. Settle which one is off:
for N in {50, 100, 200, 400, 800}, compare `fft_solve`, splu (COLAMD) and CHOLMOD against `ir_direct` (and
against `flint_solve` for N <= 60) at that state and over all entries. Columns: `N, method, rel_err_smallest,
max_rel_err, normwise_rel_err`.

`experiments/e07_structured.py` -> `results/e07_structured.csv`. N in {10, 20, 40, 80, 160}, eps = 1e-8:
(a) 20 random structured perturbations: each off-diagonal entry, each row sum and each b_i multiplied by
1 + eps * uniform(-1, 1) (`default_rng(221)`), the diagonal rebuilt as row sum minus the off-diagonal sum;
record max_i |x'_i - x_i| / x_i / eps over all trials; (b) the structured push: row sums times (1 - eps) and b
times (1 + eps); (c) for comparison, cond_max from chunk 4's entry_condition. Columns: `N, n,
structured_random_max, structured_push, cond_max, two_n_minus_1`.

Figures: `figures/f07_accuracy.py` (max_rel_err_in_u vs N for direct, gth, ir_*, cg_componentwise, log-log, with
guide lines u N and u N^2); `figures/f07_structured.py` (structured ratios vs cond_max against N).

## Acceptance tests

`pytest tests/c00_core tests/c01_spectrum tests/c02_direct tests/c03_krylov tests/c04_accuracy tests/c07_fixes`
(18 new tests, about 8 s). They check the integer system, the row sums, the accurate residual against exact
Fraction arithmetic (and that the naive residual is wrong by over 50% at the solution), correctly rounded
refinement with direct and with sloppy CG inner solves, non-convergence reporting, GTH accuracy at N = 20, 40, 60
and its advantage over plain elimination, input validation, GTH vs refinement at N = 200, and the componentwise
CG stopping rule.

## Expected results (the check script tests these against the CSVs)

| Check | Expected | Tolerance | Kind |
|---|---|---|---|
| ir_direct, ir_cg_mic0, ir_cg_amg vs exact (N <= 80) | max_rel_err 0 (correctly rounded) | at most 2 u | FAIL |
| ir_* agree with each other, N >= 160 | identical or 1 ulp | at most 4 u | FAIL |
| ir_direct steps | 2 | at most 3 | WARN |
| ir_cg_mic0 and ir_cg_amg steps | 4 | at most 8 | WARN |
| gth max_rel_err_in_u | 8 (20), 12 (40), 25 (60), 34 (80), 46 (160), 120 (400) | below N; above 10 N is FAIL | WARN/FAIL |
| direct max_rel_err_in_u / N^2 | about 0.07 (39 u at 20, 267 u at 60, 431 u at 80, 8018 u at 400) | in [0.02, 0.2] | WARN |
| gth beats direct by N/4 or more, N >= 80 | yes | | WARN |
| cg rtol 1e-10, kind none: rel_err_tiny | 5e-8 (60), 6.8e-7 (160), 1.4e-5 (640) | as in chunk 4 | WARN |
| cg_componentwise tol 1e-14: rel_err_tiny | 4e-14 to 6e-14 (60), 3e-13 (160), 5e-12 (640) | below cond_tiny * tol | FAIL |
| cg_componentwise iterations / cg rtol 1e-10 iterations | none 1.3-1.5, mic0 1.5-1.8, amg 1.4-2.2 | in [1.1, 2.5] | WARN |
| cg_componentwise tol 1e-14 converged, every N up to 1280 | yes | | WARN |
| ir_direct seconds minus direct seconds at N = 640 | about 0.1 s (factor 2.2 s) | under 50% of the factor time | WARN |
| e07_fft_check: which solver is off at (N-2, 1, 1) | expected: the FFT (normwise accurate only), splu within about 0.07 N^2 u of ir_direct | | WARN |
| e07_fft_check: FFT rel_err_smallest at N = 800 | about 1e-6 (chunk 6's disagreement) | | WARN |
| structured_random_max | 1.5-2.4 at every N | below 10 | FAIL |
| structured_push | 3.9, 4.3, 4.5, 4.6 (N = 10 ... 80) | below 10 | WARN |
| cond_max / structured_push | grows like N^2 (37/3.9 at N = 10, 2484/4.6 at N = 80) | increasing | FAIL |

## Red flags (bring these to the Project chat)

- Refinement converging but not to the exact answer at N <= 80: the residual is not accurate (check the
  TwoProduct split and that the scale makes the system integer).
- GTH error growing like N^2: some step is subtracting (usually the diagonal is being updated instead of
  recomputed from the row sum).
- cg_componentwise never reaching tol 1e-14: that would change the story; report the smallest omega reached.
- A structured ratio growing with N.

## Done when

- [ ] The listed tests pass.
- [ ] Both CSVs and both figures exist.
- [ ] `python checks/check_c07.py` prints a line per check; report saved to `results/c07_report.md`.
- [ ] `notes/decisions.md` has a chunk 7 entry (why TwoProduct is exact here, why GTH is subtraction-free);
      committed as "chunk 7: accuracy fixes".

## Paste back into the Project chat

`results/c07_report.md` and `f07_accuracy`.
