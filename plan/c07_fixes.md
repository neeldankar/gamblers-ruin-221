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
- **the stored solution** x_stored (what a float solver can reach at best), computed as
  x_ref (1 + data_error_term(x_ref)), which is the exact identity x' = x + d A_d^-1 x evaluated in floating point
  (notes/proofs.md section 3), not a first-order formula; and
- **the true probability** x_true (the ideal rational system: `flint_solve` for N <= 80, refinement with the
  exact integer residual above).

This chunk builds and measures three fixes:

1. **Componentwise stopping.** Stop CG when the Oettli-Prager backward error of the true residual is below a
   tolerance. MIC(0)- and AMG-preconditioned CG reach omega <= 1e-14 (90 u) at every N up to 1280. Plain CG
   does up to N = 640, but its smallest reachable omega grows with N (e07_floor: about 10 u at N = 80, 190-310 u
   at N = 1280, machine dependent), so at N = 1280 it stalls above the tolerance. In every run that converges,
   the tiny entry ends up 2 to 5 times closer to the stored solution than the default CHOLMOD solve's (Mac:
   2.9e-14 against 9.1e-14 at N = 160, 3.0e-13 against 1.5e-12 at N = 640, plain CG; one AMG run is 20 times
   closer), for 1.25 to 1.9 times the iterations of the usual rtol 1e-10 rule. That is the size of the own error
   of the most accurate direct solves (band Cholesky, simplicial CHOLMOD), not better: CHOLMOD's default from
   N = 160 is supernodal and carries an own error of +0.03 to +0.05 N^2 u (chunk 7b). Against the true
   probability both are limited by the data term.
2. **Iterative refinement with an exact residual.** 6N A and 6N b are integers that stand for the ideal system,
   so b - A x computed from them with error-free transformations is the residual of the true problem, not of
   the stored one. Refinement therefore removes the data error as well as the solver error: two steps after a
   direct solve (or 3 to 4 with a sloppy rtol 1e-6 CG inner solve) give every entry correctly rounded in every
   tested case: error 0 against exact rationals for N <= 80, and within half an ulp at N = 160 to 1280 by exact
   integer residuals (chunk 7b). The 4u stopping test is not a proof of that.
3. **GTH elimination.** Compute each pivot as (row sum) + (minus the off-diagonals) instead of by subtraction.
   Every entry comes out to 0.2 to 0.4 N u of the true probability (34 u at N = 80, 200 u at N = 640) against
   0.065 to 0.13 N^2 u for CHOLMOD (Mac), most of which is the data term. GTH is also nearly immune to the
   rounding of 1/6: storing 1/6 low
   scales the off-diagonals, the row sums and b by the same factor (up to a rounding of size u in a few row
   sums), and that common factor cancels in the solution. Most of GTH's 25- to 133-fold gain over CHOLMOD is
   that missing data term plus supernodal CHOLMOD's own error. Against a band Cholesky of the integer matrix 6A,
   which has no data term either, GTH is better by 1.4 to 5 for N <= 160 and by a factor that grows with N above
   (about 11 at N = 320 and 20 at N = 640 on the Mac: e07_baselines).

Why 3 works: the componentwise condition number from chunk 4 (0.39 N^2) measures sensitivity to perturbations
of A's entries with the diagonal free, which is the wrong parametrization for an M-matrix (Alfa, Xue and Ye).
Perturb instead each off-diagonal entry, each row sum and each b_i relatively by eps, diagonal rebuilt: the
worst case moves entry i by eps kappa_i, kappa_i = (A^-1 v)_i / x_i with v_i = b_i + s_i x_i + sum_j |a_ij| |x_i - x_j|
(chunk 7b). At the tiny entry kappa = 1.22 N. It is not bounded in N (a coherent drift toward the event attains
it; the reviewer's direction A + eps (HA - AH) alone gives N - 3), but it is a factor 0.32 N below the
componentwise number. Random perturbations move x by only 1.5 to 3.1 eps and symmetric ones by about log N
(17.4 at N = 640). GTH's measured error, 0.19 to 0.42 N u, is 0.16 to 0.34 kappa u: a subtraction-free
algorithm is stable in this parametrization.

## What to build (the tests import exactly these names)

`gr/refine.py`

- `integer_system(A, b, scale) -> (Ai, B)`: Ai = scale * A as CSR with sorted indices and exactly integer
  values, B = scale * b; `ValueError` if either is not integer to 1e-9. With scale = 6N the entries of Ai are
  6N and -N.
- `accurate_residual(A, b, x, scale) -> np.ndarray`: r = b - A x, computed as (B - Ai x) / scale where each
  product Ai_ij x_j is split exactly into hi + lo (TwoProduct by Dekker splitting; exact because |Ai_ij| < 2^26)
  and the row sum is accumulated with TwoSum, adding the lo parts and the TwoSum errors into a compensation
  term. One numba loop over rows. The error of entry i is at most 2u |r_i| + about 64 u^2 (|A||x| + |b|)_i (the
  Dot2 bound), which is about 2u only while the first term dominates.
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
max_rel_err, max_rel_err_in_u, omega, cond_tiny, data_term_tiny, err_vs_stored_tiny, max_err_vs_stored,
corrections` (ir_* rows: the size of each refinement correction relative to x, one per step, %.3e joined by ";";
empty otherwise).
rel_err_* and max_rel_err are against the true probability (the reference). data_term_tiny =
`data_error_term(x_ref, solve)` at the tiny state; the stored solution is x_ref (1 + data_error_term(x_ref, solve))
(an exact identity evaluated in floating point, accurate to about u); err_vs_stored_* are relative errors against it. `--quick`: N in {20, 40}.

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
structured_random_max, structured_push, cond_max, two_n_minus_1`. Chunk 7b extends this to N = 640 and adds the
structured condition number and the directions that attain it (plan/c07b_review_fixes.md).

`experiments/e07_floor.py` -> `results/e07_floor.csv`. How small can omega get? b = rhs_out_first(S, 2),
N in {80, 160, 320, 640, 1280} (`--quick`: 80, 160), kinds none (check_every 10), mic0 (5), amg (1). For each:
k10 = the iterations of `gr.krylov.cg` at rtol 1e-10 with the same preconditioner; then
`cg_componentwise(A, b, tol=0.0, M=M, check_every=c, maxiter=4 * k10)` (tol 0 never triggers, so it runs to
maxiter); record the smallest omega after k = 0 and the iteration where it occurred. Columns: `N, kind,
check_every, iters_rtol_1e10, maxiter, min_omega, min_omega_in_u, k_at_min, k_at_min_over_k10,
final_omega_in_u, max_x_corner_ratio, max_x_inf_ratio`. The last two come from a second run,
`gr.krylov.cg(A, b, rtol=0.0, M=M, maxiter=4 * k10)` from x0 = 0 with a callback on every iterate:
max_x_corner_ratio = max_k |x_k[tiny]| / x_ref[tiny] and max_x_inf_ratio = max_k max |x_k| / max |x_ref|, tiny =
(1, 1, N-2), x_ref = the CHOLMOD nesdis solve. Greenbaum (1997): rounding in the recursively updated residual grows
with the largest iterate, so an iterate that overshoots at the corner can explain plain CG's componentwise floor;
these two columns test that (review 2, question 4). One run, no timing repeats.

Figures: `figures/f07_accuracy.py`, two panels: (a) error at the tiny entry against the true probability vs N
for direct, gth, ir_direct, cg_componentwise (tol 1e-14) and cg (rtol 1e-10), log-log, with the data-term line
(u/4) cond_tiny and guide lines u N and u N^2; (b) the same methods against the stored solution
(err_vs_stored_tiny), without ir_* and gth (they target the true probability). `figures/f07_structured.py`
(the four sensitivities against N: see plan/c07b_review_fixes.md).

## Acceptance tests

`pytest tests/c00_core tests/c01_spectrum tests/c02_direct tests/c03_krylov tests/c04_accuracy tests/c07_fixes`
(18 new tests, about 8 s). They check the integer system, the row sums, the accurate residual against exact
Fraction arithmetic (and that the naive residual is wrong by over 50% at the solution), correctly rounded
refinement with direct and with sloppy CG inner solves, non-convergence reporting, GTH accuracy at N = 20, 40, 60
and its advantage over plain elimination, input validation, GTH vs refinement at N = 200, and the componentwise
CG stopping rule.

## Expected results (the check script tests these against the CSVs)

Rows that quote Mac values were rewritten from this run on Nov 11: they are regression checks. The independent
confirmations are the exact-rational tests (N <= 80), GTH against refinement, the exact-integer rows of
e07_baselines, and the Project chat's Linux recomputations.

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
| e07_fft_check: FFT rel_err_smallest at N = 800 | 4.8e-7 on the Mac (6e-7 and 2e-6 on two Linux reference implementations) | in [1e-8, 1e-4] | WARN |
| structured_cond_tiny, N = 10 ... 640 | 11.35295, 23.79933, 48.30309, 97.09688, 194.5739, 389.4719, 779.2398 | 1e-4 relative | FAIL |
| structured_cond_max and structured_argmax_state | equal to structured_cond_tiny, at (1, 1, N-2) | 1e-9 relative; exact | FAIL |
| structured_cond_over_N | 1.1353, 1.1900, 1.2076, 1.2137, 1.2161, 1.2171, 1.2176: increasing, below 1.22 | in [1.13, 1.22], increasing | FAIL |
| attained_tiny / structured_cond_tiny; attained_max_dev | 1; at most 3.5e-6 | 1e-4; below 1e-4 | FAIL |
| coherent_tiny | N - 3: 7, 17, 37, 77, 157, 317, 637 | 1e-4 relative | FAIL |
| drift_tiny | 7.50173, 19.49928, 43.77809, 92.45941, 189.8802, 384.7504, 774.5056 | 1e-4 relative | FAIL |
| symmetric_cond_tiny | 6.228720, 8.265100, 10.17282, 12.01203, 13.81435, 15.59815, 17.37261 (about 1.8 more per doubling: log N) | 1e-4 relative | FAIL |
| cond_tiny / structured_cond_tiny / N | 0.3289, 0.3232, 0.3208, 0.3198, 0.3193, 0.3191, 0.3190 | in [0.31, 0.33] | FAIL |
| structured_random_max | 1.48, 1.96, 2.21, 2.94, 2.41, 2.85, 3.07 (N = 10 ... 640; a max over 20 draws, not monotone) | below 10 | FAIL |
| structured_push | 3.8512, 4.3001, 4.5250, 4.6375, 4.6937, 4.7219, 4.7359 | 1e-3 relative | WARN |
| structured_cond_max / structured_random_max | grows like N: 7.7 (10), 33 (80), 254 (640) | above 0.3 N | FAIL |
| e07_floor, none: min_omega_in_u | increasing in N: 9.9 (80), 17.7 (160), 26.5 (320), 57.4 (640), 193 (1280) on Linux with independent code; the Mac run log had 312 at 1280 | each within a factor 2.5 of these | WARN |
| e07_floor, none, N = 1280: min_omega | above 1e-14 (plain CG cannot reach tol 1e-14 there) | | WARN |
| e07_floor, mic0 and amg: min_omega_in_u | at most 90 at every N (they reach tol 1e-14 in e07_fixes) | | FAIL |
| e07_floor, none: k_at_min_over_k10 | 1.40, 1.45, 1.49, 1.61, 1.54 (Linux) | in [1, 3.5]; above 3.5 means maxiter cut the run before the floor | WARN |
| baselines, stored-system methods: true_err_tiny - own_err_tiny | = data_term_tiny (-4.270e-15 at N = 20 ... -4.4153e-12 at 640, -1.7661e-11 at 1280) | 1e-3 relative | FAIL |
| baselines, ir_direct: max_true_err_in_ulp, every N up to 1280 | at most 0.5 (correctly rounded; 0.500 in the Project chat's independent refinement) | 1e-6 | FAIL |
| baselines, cholmod_default own_err_tiny against e07_fixes direct err_vs_stored_tiny, N >= 160 | equal (same solve, two ways of measuring: exact integers here, x_ref there) | 2% | FAIL |
| baselines, gth max_true_err_in_u against e07_fixes gth max_rel_err_in_u | equal | 1.5 u or 2%, whichever is larger | FAIL |
| baselines, cholmod_default own_err_tiny | equals cholmod_simplicial for N <= 80 and cholmod_supernodal for N >= 160 (that switch is the sign flip between 80 and 160) | 1e-9 relative | WARN |
| baselines, cholmod_supernodal own_err_over_N2u, N >= 160 | +0.052, +0.052, +0.050 on Linux; expect +0.032 on the Mac | in [0.01, 0.1] | WARN |
| baselines, cholmod_simplicial own_err_over_N2u, N >= 160 | -0.0056, -0.0058, -0.0066 on Linux; -0.018 to -0.022 on the Mac | absolute value below 0.05 | WARN |
| baselines, banded own_err_over_N2u, N >= 80 | +0.0009, +0.0014, -0.0004, -0.0048 on Linux | absolute value below 0.02 | WARN |
| baselines, banded max_own_err_in_u | 28, 45, 40, 108, 496, 2324 on Linux | each within a factor 3 | WARN |
| baselines, splu_colamd own_err_over_N2u, N >= 80 | +0.030, +0.031, +0.033, +0.035 on Linux | in [0.005, 0.1] | WARN |
| baselines, splu_natural own_err_over_N2u, N = 160, 320 | -0.067, -0.143 on Linux: natural order does not make SuperLU accurate | absolute value above 0.02 | WARN |
| baselines, banded_int max_true_err_in_u | 29, 56, 49, 194, 749, 3844 on Linux (0.0094 N^2 at N = 640) | each within a factor 3 | WARN |
| baselines, banded_int / banded: max_true_err_in_u at N = 640 | 0.09 on Linux (integer data removes the data term for a band solve) | below 0.5 | WARN |
| baselines, gth / banded_int: max_true_err_in_u at N = 160, 320, 640 | 0.24, 0.08, 0.05 (Mac GTH over Linux band solve) | below 1, decreasing | WARN |
| baselines, cholmod_int true_err_over_N2u, N >= 160 | +0.18 on Linux: integer scaling does not help CHOLMOD (worse than the data term's 0.097) | absolute value above 0.02 | WARN |

## Red flags (bring these to the Project chat)

- Refinement converging but not to the exact answer at N <= 80: the residual is not accurate (check the
  TwoProduct split and that the scale makes the system integer).
- GTH error growing like N^2: some step is subtracting (usually the diagonal is being updated instead of
  recomputed from the row sum).
- cg_componentwise with mic0 or amg not reaching tol 1e-14 at some N, or plain CG not reaching it at N <= 640:
  that would change the story; report the smallest omega reached (e07_floor).
- Refinement landing on the stored solution instead of the true one (error near data_term_tiny at N >= 160):
  the residual is being computed from the stored A, not from the integer system.
- structured_cond_over_N outside [1.1, 1.25], or the attaining perturbation not reaching kappa: the formula or the
  perturbation is wrong. (kappa itself grows like N; that is the result.)

## Done when

- [ ] The listed tests pass.
- [ ] e07_fixes.csv, e07_structured.csv, e07_floor.csv, e07_baselines.csv and the three figures exist.
- [ ] `python checks/check_c07.py` prints a line per check; report saved to `results/c07_report.md`.
- [ ] `notes/decisions.md` has a chunk 7 entry (why TwoProduct is exact here, why GTH is subtraction-free);
      committed as "chunk 7: accuracy fixes".

## Paste back into the Project chat

`results/c07_report.md` and `f07_accuracy`.
