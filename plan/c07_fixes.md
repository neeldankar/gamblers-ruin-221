# Chunk 7: Accuracy II, three fixes and the right condition number

- **Depends on:** chunk 4 (and chunks 2-3 for the solvers)
- **Learn first:** Theory Guide §8 (stopping rules, iterative refinement, GTH, Alfa-Xue-Ye) and §1 (floating point, error-free transformations)
- **Time:** build 60-90 min · compute 10-20 min (full), about 1 min (`--quick`) · your review about 2 h ·
  plug in: yes for the full run · memory about 1.5 GB (GTH band storage at N = 640)
- **Read this yourself:** all of `gr/refine.py`; make sure you can explain why every operation in the GTH
  loop adds numbers of one sign

## Goal

Chunk 4 (with 4b) showed that normwise stopping misses the tiny probabilities, and that every float solver
works on the stored matrix, whose exact solution is already off from the true probability by the data term
-(u/4) cond_i = -0.097 N^2 u at the tiny entry (chunk 4b). So there are two targets, and every result here is
reported against both:
- **the stored solution** x_stored (what a float solver can reach at best), approximated by
  x_ref (1 + data_error_term(x_ref)); and
- **the true probability** x_true (the ideal rational system: `flint_solve` for N <= 80, refinement with the
  exact integer residual above).

This chunk builds and measures three fixes:

1. **Componentwise stopping.** Stop CG when the Oettli-Prager backward error of the true residual is below a
   tolerance. MIC(0)- and AMG-preconditioned CG reach omega <= 1e-14 (90 u) at every N up to 1280. Plain CG
   does up to N = 640, but its smallest reachable omega grows with N (e07_floor: about 10 u at N = 80, 190-310 u
   at N = 1280, machine dependent), so at N = 1280 it stalls above the tolerance. In every run that converges,
   the tiny entry ends up closer to the stored solution than CHOLMOD's (Mac: 2.9e-14 against 9.1e-14 at
   N = 160, 3.0e-13 against 1.5e-12 at N = 640, plain CG), for 1.25 to 1.9 times the iterations of the usual
   rtol 1e-10 rule. Against the true probability both are limited by the data term.
2. **Iterative refinement with an exact residual.** 6N A and 6N b are integers that stand for the ideal system,
   so b - A x computed from them with error-free transformations is the residual of the true problem, not of
   the stored one. Refinement therefore removes the data error as well as the solver error: two steps after a
   direct solve (or 3 to 4 with a sloppy rtol 1e-6 CG inner solve) give every entry correctly rounded, error 0
   against exact rationals.
3. **GTH elimination.** Compute each pivot as (row sum) + (minus the off-diagonals) instead of by subtraction.
   Every entry comes out to 0.2 to 0.4 N u of the true probability (34 u at N = 80, 200 u at N = 640) against
   0.065 to 0.13 N^2 u for CHOLMOD (Mac), most of which is the data term. GTH is also nearly immune to the
   rounding of 1/6: storing 1/6 low
   scales the off-diagonals, the row sums and b by the same factor (up to a rounding of size u in a few row
   sums), and that common factor cancels in the solution.

Why 3 works: perturb the off-diagonal entries, the row sums and b relatively by eps, and the solution entries
move by only about 1.5 to 5 eps at every N measured (10 to 160). The componentwise condition number from chunk 4 (0.39 N^2) measures
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
max_rel_err, max_rel_err_in_u, omega, cond_tiny, data_term_tiny, err_vs_stored_tiny, max_err_vs_stored`.
rel_err_* and max_rel_err are against the true probability (the reference). data_term_tiny =
`data_error_term(x_ref, solve)` at the tiny state; the stored solution is x_ref (1 + data_error_term(x_ref, solve))
(first order in 2^-54, accurate to about u); err_vs_stored_* are relative errors against it. `--quick`: N in {20, 40}.

`experiments/e07_fft_check.py` -> `results/e07_fft_check.csv` (needs chunk 6's `gr.fft_solver`; skip with a
message if it is missing). Chunk 6 found that for b = rhs_order(S, 0, 1, 2) (order 123) the FFT and splu
disagree at the smallest entry, the state (N-2, 1, 1), by 6e-7 to 2e-6 at N = 800. Settle which one is off:
for N in {50, 100, 200, 400, 800}, compare `fft_solve`, splu (COLAMD) and CHOLMOD against `ir_direct` (and
against `flint_solve` for N <= 60) at that state and over all entries. Columns: `N, method, rel_err_smallest,
max_rel_err, normwise_rel_err, data_term_smallest`. Note: the data term for an order right-hand side is the same
-2^-54 E_i[T | event] plus a rounding of size u (chunk 4b), so splu should sit near it.

`experiments/e07_structured.py` -> `results/e07_structured.csv`. N in {10, 20, 40, 80, 160}, eps = 1e-8:
(a) 20 random structured perturbations: each off-diagonal entry, each row sum and each b_i multiplied by
1 + eps * uniform(-1, 1) (`default_rng(221)`), the diagonal rebuilt as row sum minus the off-diagonal sum;
record max_i |x'_i - x_i| / x_i / eps over all trials; (b) the structured push: row sums times (1 - eps) and b
times (1 + eps); (c) for comparison, cond_max from chunk 4's entry_condition. Columns: `N, n,
structured_random_max, structured_push, cond_max, two_n_minus_1`.

`experiments/e07_floor.py` -> `results/e07_floor.csv`. How small can omega get? b = rhs_out_first(S, 2),
N in {80, 160, 320, 640, 1280} (`--quick`: 80, 160), kinds none (check_every 10), mic0 (5), amg (1). For each:
k10 = the iterations of `gr.krylov.cg` at rtol 1e-10 with the same preconditioner; then
`cg_componentwise(A, b, tol=0.0, M=M, check_every=c, maxiter=4 * k10)` (tol 0 never triggers, so it runs to
maxiter); record the smallest omega after k = 0 and the iteration where it occurred. Columns: `N, kind,
check_every, iters_rtol_1e10, maxiter, min_omega, min_omega_in_u, k_at_min, k_at_min_over_k10,
final_omega_in_u`. One run, no timing repeats.

Figures: `figures/f07_accuracy.py`, two panels: (a) error at the tiny entry against the true probability vs N
for direct, gth, ir_direct, cg_componentwise (tol 1e-14) and cg (rtol 1e-10), log-log, with the data-term line
(u/4) cond_tiny and guide lines u N and u N^2; (b) the same methods against the stored solution
(err_vs_stored_tiny), without ir_* and gth (they target the true probability). `figures/f07_structured.py`
(structured ratios vs cond_max against N).

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
| ir_cg_mic0 and ir_cg_amg steps | 3 (N <= 320), 4 (N >= 640) | at most 8 | WARN |
| gth max_rel_err_in_u | 8 (20), 12 (40), 25 (60), 34 (80), 46 (160), 60 (320), 200 (640): 0.19-0.42 N | below N; above 10 N is FAIL | WARN/FAIL |
| direct max_rel_err_in_u / N^2 (against the true probability; mostly the data term, 0.097) | Mac: 0.065 for N >= 160, 0.09-0.13 for N <= 80 (37, 190, 428, 848 u at N = 20, 40, 60, 80); the Linux reference had 39, 267, 431 u at N = 20, 60, 80 (CHOLMOD's own part differs by machine) | in [0.02, 0.2] | WARN |
| direct err_vs_stored_tiny (the solver's own error) | Mac: +3.8e-16 (20), -4.0e-15 (40), -8.8e-15 (60), -2.5e-14 (80), +9.1e-14 (160), +3.7e-13 (320), +1.5e-12 (640), +5.7e-12 (1280): +0.032 N^2 u for N >= 160, opposite in sign to the data term; either sign for N <= 80. Linux reference: -1.1e-14 (80), about +0.05 N^2 u for N >= 160 | absolute value below 0.2 N^2 u | WARN |
| data_term_tiny | as in chunk 4b: -6.895e-14 (80), -2.7592e-13 (160), -1.1038e-12 (320), -4.4153e-12 (640), -1.7661e-11 (1280) | 1e-3 relative | FAIL |
| gth beats direct (true probability), N >= 80 | by a factor growing with N: 25 (80), 37 (160), 112 (320), 133 (640) on the Mac (13 at N = 80 on Linux) | gth smaller at every N >= 80 | WARN |
| cg rtol 1e-10, kind none: rel_err_tiny | 5e-8 (60), 6.8e-7 (160), 1.4e-5 (640) | as in chunk 4 | WARN |
| cg_componentwise tol 1e-14: rel_err_tiny (true probability) | 4e-14 to 6e-14 (60), 3e-13 (160), 5e-12 (640): at N >= 160 this is the data term | below cond_tiny * tol | FAIL |
| cg_componentwise tol 1e-14: err_vs_stored_tiny, N >= 160, converged runs only | 0.05-0.46 of the direct solver's (Mac): none 2.9e-14, 8.0e-14, 3.0e-13; mic0 3.5e-14, 1.0e-13, 6.8e-13, 2.6e-12; amg 4.6e-15, 1.5e-13, 6.2e-13, 1.9e-12 (N = 160, 320, 640, 1280) | below the direct solver's err_vs_stored_tiny at the same N | WARN |
| cg_componentwise iterations / cg rtol 1e-10 iterations, converged runs only | none 1.25-1.49, mic0 1.36-1.90, amg 1.38-1.86 | in [1.1, 2.5] | WARN |
| cg_componentwise tol 1e-14 converged | mic0 and amg at every N up to 1280; none up to N = 640 (not at 1280: see e07_floor) | | WARN |
| ir_direct seconds minus direct seconds at N = 640 | about 0.06 s (factor 1.3 s, Mac) | under 50% of the factor time | WARN |
| e07_fft_check: which solver is off at (N-2, 1, 1) | expected: the FFT (normwise accurate only); splu within about 0.1 N^2 u of ir_direct, and near data_term_smallest | | WARN |
| e07_fft_check: FFT rel_err_smallest at N = 800 | about 1e-6 (chunk 6's disagreement) | | WARN |
| structured_random_max | 1.48, 1.96, 2.21, 2.94, 2.41 (N = 10 ... 160; a max over 20 random draws, so not monotone) | below 10 | FAIL |
| structured_push | 3.85, 4.30, 4.53, 4.64, 4.69 (N = 10 ... 160) | below 10 | WARN |
| cond_max / structured_push | grows like N^2: 37/3.85 (10), 2484/4.64 (80), 9941/4.69 (160) | increasing | FAIL |
| e07_floor, none: min_omega_in_u | increasing in N: 9.9 (80), 17.7 (160), 26.5 (320), 57.4 (640), 193 (1280) on Linux with independent code; the Mac run log had 312 at 1280 | each within a factor 2.5 of these | WARN |
| e07_floor, none, N = 1280: min_omega | above 1e-14 (plain CG cannot reach tol 1e-14 there) | | WARN |
| e07_floor, mic0 and amg: min_omega_in_u | at most 90 at every N (they reach tol 1e-14 in e07_fixes) | | FAIL |
| e07_floor, none: k_at_min_over_k10 | 1.40, 1.45, 1.49, 1.61, 1.54 (Linux) | in [1, 3.5]; above 3.5 means maxiter cut the run before the floor | WARN |

## Red flags (bring these to the Project chat)

- Refinement converging but not to the exact answer at N <= 80: the residual is not accurate (check the
  TwoProduct split and that the scale makes the system integer).
- GTH error growing like N^2: some step is subtracting (usually the diagonal is being updated instead of
  recomputed from the row sum).
- cg_componentwise with mic0 or amg not reaching tol 1e-14 at some N, or plain CG not reaching it at N <= 640:
  that would change the story; report the smallest omega reached (e07_floor).
- Refinement landing on the stored solution instead of the true one (error near data_term_tiny at N >= 160):
  the residual is being computed from the stored A, not from the integer system.
- A structured ratio growing with N.

## Done when

- [ ] The listed tests pass.
- [ ] e07_fixes.csv, e07_structured.csv, e07_floor.csv and both figures exist.
- [ ] `python checks/check_c07.py` prints a line per check; report saved to `results/c07_report.md`.
- [ ] `notes/decisions.md` has a chunk 7 entry (why TwoProduct is exact here, why GTH is subtraction-free);
      committed as "chunk 7: accuracy fixes".

## Paste back into the Project chat

`results/c07_report.md` and `f07_accuracy`.
