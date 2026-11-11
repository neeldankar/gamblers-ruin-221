# Chunk 4: Accuracy I, diagnosing tiny probabilities

- **Depends on:** chunks 2 and 3
- **Learn first:** Theory Guide §8 (accuracy of tiny entries) and §1 (componentwise conditioning, backward error)
- **Time:** build 45-60 min · compute 5-15 min (full), under 1 min (`--quick`) · your review about 2 h (this is
  the heart of the project) · plug in: optional · memory under 2 GB
- **Read this yourself:** all of `gr/accuracy.py` (short) and the derivation of cond_i = 2 E_x[T | event] below

## Goal

Answer the main question in diagnostic form: which solvers get the tiny probabilities right, and why.
The running example is b = rhs_out_first(S, 2): the probability that player 3 (the big stack) is out first.
Its smallest entry sits at the state (1, 1, N-2) and is about 9.1196 / N^3 (the constant is Gamma(1/3)^9 / (8 pi^4),
twice the c of Diaconis and Ethier 2022, Remark 4) (3.5e-8 at N = 640).

The story after this chunk:

1. The componentwise condition number of entry i is cond_i = (|A^{-1}| (|A||x| + |b|))_i / x_i. Because
   A^{-1} >= 0 and |A| = 2I - A, it simplifies to cond_i = 2 (A^{-1} x)_i / x_i = 2 E_x[T | event]: twice the
   expected number of rounds until the first bust, conditioned on the event. At the tiny entry it is about
   0.388 N^2. So there is no extra 1/x_i penalty for a tiny entry: its
   condition number is 0.39 N^2, the same order as kappa(A). Hypotheses: unit diagonal, off-diagonals <= 0,
   A^{-1} >= 0, b >= 0. For order right-hand sides the boundary value is P(event | landing state) and the same
   reading holds (tower property).
2. The worst-case perturbation A -> A - eps|A|, b -> b + eps|b| attains that bound in every entry at once.
3. Direct solvers are componentwise backward stable here (omega of 1 to 20 u). Against exact rationals
   (N <= 80) every entry is within 1e-13, and most of that is not solver error: storing 1/6 in float64 moves
   entry i by -2^-54 E_i[T | event] = -(u/4) cond_i (-6.9e-14 at the tiny entry at N = 80), exactly as the
   condition number predicts. The solvers' own errors are a few times smaller. For N >= 160 the reference is a
   direct solve of the stored system; the a posteriori bound (omega + 8u) max_i cond_i is 1.8e-9 at N = 1280.
4. CG with the usual normwise stopping rule gets the tiny entry badly wrong: relative error 1.4e-5 at N = 640
   with rtol 1e-10, while the normwise error is 1.6e-9 (a 9,000-fold gap); 63% at rtol 1e-6; a negative
   probability at N = 1280. The mechanism: e_i = (A^{-1} e_i) . r, so a residual test bounds the absolute error
   of entry i by ||A^{-1} e_i||_2 rtol ||b||_2 (1.17 rtol ||b||_2 at the corner), which says nothing about an
   entry of size 9.12 / N^3. From the bulk to the corner the solution falls by 10^7 and the error by about 10^3.
   The ratio error / (cond_tiny rtol) is near 1 for this right-hand side at this state only (0.5 to 6); it is not a law.
5. The componentwise backward error is the right alarm: omega <= tol guarantees every entry to cond_i tol,
   while the normwise backward error (5e-12 here) guarantees nothing about small entries. It is a sufficient
   test, not an estimate: cond times omega overestimates CG's actual error by about 10^5.

## What to build (the tests import exactly these names)

`gr/accuracy.py`

- `U = 2.0 ** -53` (unit roundoff).
- `relative_errors(x, x_true) -> np.ndarray`: |x - x_true| / |x_true|, entrywise.
- `normwise_backward_error(A, x, b) -> float`: ||b - Ax||_inf / (||A||_inf ||x||_inf + ||b||_inf) (Rigal-Gaches).
- `componentwise_backward_error(A, x, b) -> float`: max_i |b - Ax|_i / (|A||x| + |b|)_i (Oettli-Prager). A row
  whose denominator is 0 has residual 0 too; count it as 0 (0/0 = 0), never as NaN. This matters at x = 0,
  where many rows of b are 0.
- `entry_condition(A, b, x, solve) -> np.ndarray`: cond_i = (A^{-1}(|A||x| + |b|))_i / |x_i|, where `solve(r)`
  applies A^{-1} (one extra solve; valid because A^{-1} >= 0 for an M-matrix).
- `conditional_mean_time(A, x, solve) -> np.ndarray`: (A^{-1} x)_i / x_i.
- `worst_case_perturbation(A, b, eps) -> (A_pert, b_pert)` = (A - eps|A|, b + eps|b|), A_pert as CSR.
- `flint_solve(A, b, scale) -> np.ndarray`: exact rational solve of (scale A) u = (scale b) with python-flint
  (`flint.fmpz_mat(...).solve(...)`), each entry rounded correctly to float64 (convert numerator and denominator
  to a `fractions.Fraction`, then `float`). Use scale = 6N, which makes both sides integer. Raise `ValueError`
  if scale * A or scale * b is not integer (to 1e-9). Practical up to N = 80 (about 30 s); do not go higher.

Derivation to write in `notes/decisions.md` in your own words: with A x = b, |A||x| + |b| = (2I - A) x + b = 2x,
so cond_i = 2 (A^{-1}x)_i / x_i; and A^{-1}x is the expected number of rounds to the first bust weighted by the
event, which is what conditional_mean_time divides out.

## Experiments

`experiments/e04_condition.py` -> `results/e04_condition.csv`. N in {10, 20, 40, 80, 160, 320, 640, 1280}
(`--quick`: 10, 20, 40); events `out_first_3` (rhs_out_first(S, 2)) and `order_321` (rhs_order(S, 2, 1, 0)).
Solve with one CHOLMOD nesdis factor per N (SuperLU MMD_AT_PLUS_A if CHOLMOD is missing), reused for the extra
solves. Columns: `N, event, argmin_state, x_tiny, N3_x_tiny, cond_tiny, cond_tiny_over_N2, cond_max_over_N2,
argmax_cond_state, ET_tiny_over_N2, omega_direct, aposteriori_bound` with tiny = (1, 1, N-2),
aposteriori_bound = max_i cond_i * omega_direct.

`experiments/e04_errors.py` -> `results/e04_errors.csv`. Event `out_first_3`. Reference: `flint_solve` for
N in {20, 40, 80} (reference = "exact"), the direct solve for N in {160, 320, 640, 1280} (reference = "direct",
trusted to its certified bound). Methods: `cholmod` (nesdis), `splu` (COLAMD), `banded` (N <= 400), and CG with
kinds none, mic0, amg at rtol in {1e-6, 1e-8, 1e-10, 1e-12, 1e-14} (maxiter 30000). Columns: `N, method, kind,
rtol, iterations, converged, reference, rel_err_tiny, max_rel_err, argmax_rel_err_state, normwise_rel_err,
normwise_backward_error, componentwise_backward_error, cond_tiny, cond_times_rtol, ratio_tiny_to_prediction`
with cond_times_rtol = cond_tiny * rtol and ratio = rel_err_tiny / cond_times_rtol (CG rows only).
`--quick`: N in {20, 40}.

`experiments/e04_perturbation.py` -> `results/e04_perturbation.csv`. N in {10, 20, 40, 80}, eps in {1e-10, 1e-8,
1e-6}: the worst-case ratio (x_pert - x)_i / x_i / (eps cond_i), min and max over i, and the largest ratio over
20 random perturbations (|dA_ij| <= eps|A_ij| and |db_i| <= eps|b_i|, uniform random signs and sizes,
`default_rng(221)`).

Figures (from the CSVs only): `figures/f04_tiny_error.py` (rel_err_tiny vs rtol at N = 640 for each CG kind,
the line cond_tiny * rtol, and the direct solver's error as a horizontal mark); `figures/f04_condition.py`
(cond_tiny / N^2 and N^3 x_tiny vs N).

## Acceptance tests

`pytest tests/c00_core tests/c01_spectrum tests/c02_direct tests/c03_krylov tests/c04_accuracy` (19 new tests,
about 2 s). They check the backward errors on a hand example, the condition number against a dense formula and
against 2 E[T | event], E[T] = 3 x1 x2 x3 / N for the sure event, the worst-case perturbation attaining the
bound, random perturbations staying under it, the tiny entry's location, size and conditioning, `flint_solve`
against the Fraction solver, componentwise accuracy of the direct solve, and CG missing the tiny entry.

## Expected results (the check script tests these against the CSVs)

| Check | Expected | Tolerance | Kind |
|---|---|---|---|
| N3_x_tiny, out_first_3 | 9.122614 (N=10), 9.119797 (20), 9.119602 (40), 9.119590 (80), 9.119589 (N >= 160); the limit is Gamma(1/3)^9 / (8 pi^4) = 9.1195890 | 2e-6 relative for N >= 160 | FAIL |
| N3_x_tiny, order_321 | half of the out_first_3 value (1 <-> 2 symmetry): 4.559795 at N = 80 | 1e-9 relative | FAIL |
| argmin_state and argmax_cond_state | (1, 1, N-2) for both events | exact | FAIL |
| cond_tiny_over_N2 | 0.3846, 0.3874, 0.3881, 0.3883, 0.3884, 0.3884 for N = 20 ... 640; increasing | 1e-3 absolute | FAIL |
| cond_tiny, order_321 vs out_first_3 | equal (same symmetry) | 1e-9 relative | FAIL |
| ET_tiny_over_N2 | cond_tiny_over_N2 / 2 | 1e-12 relative | FAIL |
| omega_direct | 3-20 u (8.5 u at N = 160, 17 u at N = 640) | below 100 u | FAIL |
| aposteriori_bound | 1.5e-11 (160), 8.1e-11 (320), 3.8e-10 (640), 1.8e-9 (1280) | below 1e-8 | FAIL |
| exact-reference rows, direct methods: max_rel_err | 2e-15 to 8e-14 | below 1e-13 | FAIL |
| exact-reference rows, direct methods: max_rel_err <= 2 cond_i omega | holds in every entry | | FAIL |
| empirical fit, this rhs only: CG none, N >= 320, rtol <= 1e-8: ratio_tiny_to_prediction | 0.9-1.6 (at N = 160 it ranges 0.07-1.3); at N = 1280 up to 6 at rtol 1e-8 and 2.1 at 1e-12 | in [0.5, 2] for N <= 640; in [0.3, 8] at N = 1280 | WARN |
| CG none, rtol 1e-6, N = 640: rel_err_tiny | 0.63 (63% wrong; ratio about 4, the law underestimates at loose rtol) | in [0.3, 1.0] | WARN |
| empirical fit, this rhs only: CG mic0 and amg, N >= 160: ratio_tiny_to_prediction | mic0 0.001-0.03, amg 0.02-0.2 | below 1 | WARN |
| CG none, rtol 1e-10, N = 640: rel_err_tiny | 1.4e-5 | in [3e-6, 6e-5] | WARN |
| CG kind none at rtol 1e-10: componentwise / normwise backward error | above 1e3 for N >= 80 (9.8e3 to 1.2e7 measured) | above 100 | FAIL |
| CG kinds mic0 and amg at rtol 1e-10: same ratio | mic0 15-31 at N = 80-160 (its errors are already componentwise-small), amg 276 and up | above 10 | WARN |
| CG none, rtol 1e-14 reached (converged) for N <= 1280 | yes up to N = 640 (1331 iterations); N = 1280 not measured | | WARN |
| worst-case perturbation ratio | 1.00000 for eps <= 1e-8; up to 1.0015 at eps = 1e-6, N = 80 | within 1e-3 for eps <= 1e-8 | FAIL |
| random perturbation max ratio | 0.24-0.39 | below 1 + 1e-3 | FAIL |
| data_term_tiny (e04_condition, out_first_3) | -1.036e-15 (10), -4.270e-15 (20), -1.7206e-14 (40), -6.895e-14 (80), -2.76e-13 (160), -1.10e-12 (320), -4.42e-12 (640), -1.77e-11 (1280) | 1e-3 relative | FAIL |
| data_term_over_N2u | tends to -0.0971 (= -cond_tiny / (4 N^2)) | within 1% for N >= 80 | FAIL |
| exact-reference direct rows: abs(solver_err_tiny) | 4e-17 to 2.5e-14 (N = 80: +2.1e-14 SuperLU, -1.1e-14 CHOLMOD on Linux) | below 5e-14 | WARN |
| exact-reference direct rows, N = 40 and 80: abs(solver_err_tiny) < abs(data_term_tiny) | yes | | WARN |
| aposteriori_bound | 1.5e-11 (160), 8.1e-11 (320), 3.8e-10 (640), 1.8e-9 (1280) | below 1e-8 | FAIL |
| (N3_x_tiny - C) N^4, N = 80, 160, 320 | 34.32, 34.37, 34.32 (true values 34.325, 34.375, 34.388; the last is already bent by the solver's bias) | in [34.2, 34.5] | WARN |
| CG none, rtol 1e-6, N = 1280: value_tiny | negative (-4.18e-9 for a probability of +4.35e-9) | negative | WARN |
| mechanism: out_first_3 rows vs e04_errors (same N, rtol) | same rel_err at the tiny entry | 1% | FAIL |
| mechanism: abs_err_smallest <= residual_bound_abs, every row | holds (observed 5e-4 to 1.5e-2 of the bound) | 1e-6 relative slack | FAIL |
| mechanism: g_norm, every row | 1.1702 | 1e-3 | FAIL |
| mechanism: land_mid ratio_to_cond_rtol, N = 640 | 34, 48, 16, 18, 13 for rtol 1e-6 ... 1e-14 | each in [3, 150] | WARN |
| mechanism: land_quarter ratio, N = 640 | 440, 12, 24, 8.0, 18 | each above 3 | WARN |
| mechanism: order_321 ratio, N = 640 | 10.3, 2.4, 1.8, 0.74, 0.38 | each in [0.1, 30] | WARN |
| mechanism: out_first_3 median_ratio_all_states, N = 640 | 4.0e-4, 1.8e-4, 1.9e-4 at rtol 1e-8, 1e-10, 1e-12 | below 0.01 | WARN |
| mechanism: out_first_3, N = 640, rtol 1e-10: absolute errors | corner 5.0e-13, median 1.9e-10, max 1.6e-9 | corner below median | WARN |

Reference CG numbers (out_first_3, kind none): rel_err_tiny at rtol 1e-10 is 2.1e-8 (N=20), 3.7e-8 (40),
2.5e-8 (80), 6.8e-7 (160), 5.8e-6 (320), 1.4e-5 (640); at rtol 1e-14 it is 7e-12 (160), 4e-10 (320), 1.6e-9 (640).

## Red flags (bring these to the Project chat)

- A direct solver with relative error above 1e-12 in any entry at N <= 80: the solve or the reference is wrong.
- cond_tiny not growing like N^2, or the argmax of cond not at (1, 1, N-2).
- The worst-case ratio not 1: the condition formula or the perturbation is wrong.
- CG converging to rtol 1e-14 but with componentwise backward error near u: that would contradict the
  diagnosis and is worth discussing.

## Done when

- [ ] `pytest tests/c00_core tests/c01_spectrum tests/c02_direct tests/c03_krylov tests/c04_accuracy` passes.
- [ ] Three CSVs and two figures exist.
- [ ] `python checks/check_c04.py` prints a line per check; report saved to `results/c04_report.md`.
- [ ] `notes/decisions.md` has a chunk 4 entry with the cond = 2 E[T | event] derivation; committed as
      "chunk 4: accuracy diagnosis".

## Paste back into the Project chat

`results/c04_report.md` and `f04_tiny_error`. This is the result the progress report (Nov 20) is built on.
