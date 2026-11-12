# Chunk 10 (optional): Extras: least squares by QR, and unequal skill

- **Depends on:** chunk 8 (uses `gr.icm.icm_orders`); chunk 3 for the GMRES and CG conventions; chunk 1
  for `gr.runlog`
- **Learn first:** Theory Guide §9 (least squares: normal equations versus QR versus SVD; nonsymmetric
  systems and GMRES) and §6 (Krylov methods: what CG's stopping test measures)
- **Time:** build 30-60 min · compute 2-5 min (full), under 30 s (`--quick`) · your review about 1 h ·
  plug in: no · peak memory about 1 GB (the N = 1030 overflow build)
- **Read this yourself:** the three `fit_*` functions (one least-squares problem solved three ways) and
  `symmetrize_bt`

## Goal

Two small projects that reuse the machinery on problems with different linear algebra.

**Part A: least squares.** Diaconis and Ethier summarize exact-versus-ICM results with a polynomial
regression of the ratio P/P_ICM in the stack fractions. We redo such a fit as a least-squares lab:
R_sigma = P_sigma / P_ICM_sigma for sigma in {321, 312, 213} over all 7500 states 1 <= A <= B <= C at
N = 300, modeled by a sextic in x = A/N, y = B/N (28 monomials). Facts to confirm:

1. cond(X) = 1.684e7, so X^T X has condition 2.84e14. The normal equations give coefficients that differ
   from the SVD's by 1e-7 to 4e-6 (relative), QR by 1e-13 to 2e-11, yet all three fitted curves agree to
   1e-8: the coefficient error lies along directions X barely sees. Coefficients are ill-determined; the
   fit is not.
2. The sextic fits 321 and 312 to about 1e-6 relative (max residual 5.6e-6 and 6.7e-6), and each two
   extra degrees gain one to two digits while cond(X) grows about 300-fold. It cannot fit 213 (max
   residual 0.038, still 0.027 at degree 8): R_213 = 1 exactly when A = B but drops to 0.956 at
   (1, 2, 297), a boundary layer at A = 1, 2 that no low-degree polynomial follows.

**Part B: unequal skill (Bradley-Terry).** Each round an unordered pair {a, b} is chosen with
probability 1/3 and a beats b with probability s_a / (s_a + s_b); skills s = (1, 1.5, 2). When a player
busts, the two survivors play biased two-player ruin. Facts to confirm:

1. A is not symmetric (max |A - A^T| = (1/3)(2 - 1)/(2 + 1) = 1/9) but the chain is reversible with
   pi(x) = prod s_i^{x_i}, so S = D^{1/2} A D^{-1/2} (D = diag(pi)) is symmetric with off-diagonals
   -(1/3) sqrt(s_a s_b)/(s_a + s_b) and the same (real, positive) eigenvalues. pi_max/pi_min = 2^(N-3),
   so pi itself overflows from N = 1026 on: build S from log pi.
2. lambda_min(S) decreases to the Gershgorin bound 1 - 2(0.15713 + 0.16330 + 0.16496) = 0.0292172 and
   cond2(S) stays near 51: the drift makes the chain easy.
3. **The trap.** CG on S converges in about 75 steps at every N, but its answer mapped back by D^{-1/2}
   is wrong where pi is small (error 0.33 at N = 80 and about 1 at N = 160 for P(strongest wins)): CG
   controls the residual in a norm that does not see those states. GMRES on A takes 59 to about
   820 steps but is accurate (below 3e-9). A direct solve of S mapped back is accurate too (1e-15): Gaussian
   elimination is unaffected by a diagonal similarity scaling, Krylov stopping tests are not.

## What to build (the tests import exactly these names)

`gr/extras.py`, regression part
- `regression_states(N) -> np.ndarray` of shape (m, 3), all (A, B, C) with 1 <= A <= B <= C and sum N
  (m = round(N^2/12), 7500 at N = 300).
- `monomials(degree=6) -> list[tuple[int, int]]`: exponents (i, j) of x^i y^j, by total degree d and
  then x^d, x^(d-1) y, ..., y^d (so (0,0), (1,0), (0,1), (2,0), (1,1), (0,2), ...; Diaconis-Ethier's
  beta_00, beta_10, beta_01, ... order).
- `design_matrix(states, N, degree=6) -> np.ndarray`: columns x^i y^j in that order, x = A/N, y = B/N.
- `ratio_targets(N, orders=("321", "312", "213")) -> (states, dict)`: states from `regression_states(N)`
  and, per order, P/P_ICM at those states (players 1, 2, 3 hold A, B, C).
- `fit_normal_equations(X, y)` (Cholesky on X^T X), `fit_qr(X, y)` (Householder: `np.linalg.qr`, then
  `scipy.linalg.solve_triangular`), `fit_svd(X, y)` (thin SVD); each returns the coefficient vector.

`gr/extras.py`, Bradley-Terry part
- `build_A_bt(S, skills) -> scipy.sparse.csr_matrix`: A = I - Q with Q(x, x + e_a - e_b) =
  (1/3) s_a/(s_a + s_b). With skills (1, 1, 1) it must equal `gr.matrix.build_A`.
- `p2_win(y, s_k, s_j, N)`: P(k reaches N before 0) from y chips when k beats j with probability
  s_k/(s_k + s_j); y may be an array. Must not overflow at N = 2000 (use expm1 / log forms).
- `rhs_win_bt(S, skills, i)`: right-hand side for P(player i wins) (boundary value from `p2_win` for the
  two survivors, 0 if i is the one busting).
- `log_pi(S, skills) -> np.ndarray`: sum_i x_i log s_i at every state.
- `symmetrize_bt(A, lp) -> csr_matrix`: S with entries A_xy exp((lp_x - lp_y)/2), never forming pi.

## Experiment

`experiments/e10_extras.py` writes, through `gr.runlog.save_results`:

1. `results/e10_regression.csv`: one row per (order, method), order in {321, 312, 213}, method in {svd,
   qr, normal_equations, ne_column_scaled} (the last: scale columns to unit norm, solve the normal
   equations, unscale). Columns: `order, method, cond_X, cond_XtX, coef_relerr_vs_svd, resid_norm,
   max_abs_resid, fitted_maxdiff_vs_svd, seconds`.
2. `results/e10_degree_sweep.csv`: degree in {2, 4, 6, 8} for each order, SVD fits. Columns: `order,
   degree, n_coef, cond_X, max_abs_resid`.
3. `results/e10_bt_spectrum.csv`: N in {20, 40, 80, 160, 320} (`--quick`: 20, 40). Columns: `N, n,
   max_abs_A_minus_AT, rel_asym_S, lam_min_S, lam_max_S, cond2_S, gershgorin_lower, log10_pi_range,
   max_expected_rounds, cond2_A_dense` (dense only for N <= 40, else blank). lam_min_S by shift-invert
   `eigsh(S, sigma=0)`, lam_max_S by `eigsh(S, which="LA")`.
4. `results/e10_bt_solvers.csv`: N in {40, 80, 160, 320} (`--quick`: 40, 80); right-hand sides
   P(weakest wins), P(strongest wins), E[rounds to the first bust] (b = 1); methods `gmres30_A`
   (`gmres(A, b, rtol=1e-10, atol=0, restart=30, maxiter=500)`), `cg_S_1e-10` and `cg_S_1e-15` (CG on S
   with b_S = D^{1/2} b, D^{1/2} = exp((lp - max lp)/2), answer y / D^{1/2}), and `splu_S` (direct solve of
   S, mapped back). Reference: `splu` on A. Columns: `N, rhs, method, iters, rel_residual_A, max_err_rel,
   max_err_lowpi_rel, seconds` (errors relative to max |u|; "lowpi" = the 10% of states with smallest pi).
5. `results/e10_bt_overflow.csv`: the first N at which naive pi (at its largest state (1, 1, N-2)) and
   naive sqrt(pi) overflow, and a build at N = 1030 counting non-finite entries of naive S versus the
   log-domain S. Columns: `N, quantity, value`.

Figures: `figures/f10_regression.py` (coefficient error and residual by method, and the degree sweep)
and `figures/f10_bt_errors.py` (error against state, colored by log pi, for CG on S and GMRES on A at
N = 80).

## Acceptance tests

`pytest tests/c00_core tests/c10_extras` (35 new tests: 19 in `test_c10_regression.py`, 16 in
`test_c10_bradley_terry.py`). Regression: the state count round(N^2/12), the monomial order, the
design matrix, cond(X), the targets at (1,1,298), the center and the line A = B, QR = SVD, normal
equations at least 10x worse than QR, identical fitted values, and the three max residuals. Bradley-
Terry: equal skill = fair game, matrix entries and 1/9, log pi, reversibility and the symmetrized
off-diagonals, overflow safety, equal spectra, lambda_min and cond2 of S at N = 20, 40, 80, `p2_win`
(boundary values, recurrence, monotone, N = 2000), exact rational win probabilities at N = 7 from an
independent Fraction solver, and GMRES on A against CG on S at N = 80.

## Expected results (the check script tests these against the CSV)

| Check | Expected | Tolerance | Kind |
|---|---|---|---|
| cond_X (degree 6) | 1.68436e7 | 1e-4 relative | FAIL |
| cond_XtX / cond_X^2 | 1 | between 0.5 and 2 | FAIL |
| qr coef_relerr_vs_svd | below 1e-7 (Linux 7e-14 to 2e-11; Mac 1.9e-13 to 1.6e-10: LAPACK dependent) | | FAIL |
| normal_equations coef_relerr_vs_svd | at least 10x the qr value for each order | | FAIL |
| normal_equations coef_relerr_vs_svd | Linux 1.2e-7 (213), 7.9e-7 (312), 3.8e-6 (321); Mac 5.6e-8, 8.9e-7, 5.6e-6 | between 1e-8 and 1e-4 | WARN |
| ne_column_scaled coef_relerr_vs_svd | Linux 4.8e-8 (213), 1.7e-6 (312), 3.8e-6 (321); Mac 2.5e-8, 2.0e-6, 9.6e-6: scaling does not rescue the normal equations here | at least 10x the qr value and in [1e-8, 1e-4] | WARN |
| fitted_maxdiff_vs_svd | below 1e-8 for every method | | FAIL |
| svd resid_norm for 321, 312, 213 | 8.8633989e-05, 9.4584299e-05, 1.3297562e-01 | 1e-6 relative | FAIL |
| svd max_abs_resid for 321, 312, 213 | 5.638098e-06, 6.657670e-06, 3.796276e-02 | 1e-3 relative | FAIL |
| degree sweep cond_X at degree 2, 4, 6, 8 | 2.106e2, 5.708e4, 1.684e7, 5.164e9 | 1e-3 relative | FAIL |
| degree sweep max_abs_resid, 321 | 1.814e-2, 4.662e-4, 5.638e-6, 1.368e-7 | 1e-3 relative (10% at degree 8) | FAIL (WARN at degree 8) |
| degree sweep max_abs_resid, 213 | 6.430e-2, 5.004e-2, 3.796e-2, 2.661e-2 (never below 0.02) | 1e-3 relative (10% at degree 8) | FAIL (WARN at degree 8) |
| max_abs_A_minus_AT | 1/9 = 0.1111111 | 1e-12 | FAIL |
| rel_asym_S | below 1e-14 | | FAIL |
| lam_min_S at N = 20, 40, 80, 160, 320 | 0.0608913, 0.0371848, 0.0312122, 0.0297162, 0.0293420 | 1e-5 relative | FAIL |
| lam_max_S, same N | 1.469880, 1.481731, 1.484717, 1.485465, 1.485652 | 1e-5 relative | FAIL |
| cond2_S, same N | 24.1394, 39.8478, 47.5685, 49.9884, 50.6323 | 1e-4 relative | FAIL |
| gershgorin_lower | 0.0292172 at every N, below every lam_min_S | 1e-7 | FAIL |
| log10_pi_range | (N - 3) log10 2: 5.1175, 11.1381, 23.1793, 47.2617, 95.4265 | 1e-9 abs | FAIL |
| max_expected_rounds | 36.0536, 106.4723, 276.2373, 654.6066, 1465.9752 | 1e-4 relative | FAIL |
| cond2_A_dense at N = 20, 40 | 35.389, 100.366 (above cond2_S: non-normality) | 1e-3 relative | FAIL |
| gmres30_A max_err_rel | below 1e-8 for every N and right-hand side (observed up to 3e-9) | | FAIL |
| gmres30_A iters | 59 (weakest wins, every N); 122, 291, 512, about 820 (strongest wins, N = 40 ... 320; Mac 819) | within 2% (5% for the N = 320 value) | WARN |
| cg_S_1e-10 iters | 61 to 80 at every N | | WARN |
| cg_S_1e-10 max_err_rel, P(strongest wins) | 7.3e-7 at N = 40; above 1e-3 at N >= 80 (0.33 at 80, about 1 at 160 and 320) | | FAIL |
| cg_S_1e-10 max_err_rel, E[rounds] | 2.4e-8 at N = 40, 1.3e-2 at 80, 0.45 at 160 (Mac 0.75 at 320) | each within a factor 10 | WARN |
| cg_S_1e-10 max_err_rel, P(weakest wins) | below 1e-11 (b sits where pi is small, so the residual sees it) | | WARN |
| splu_S max_err_rel | below 1e-12 | | FAIL |
| overflow: first N where naive pi, naive sqrt(pi) overflow | 1026, 2050 | exact | FAIL |
| N = 1030 build | naive S has non-finite entries; log-domain S all finite, symmetric to 1e-13 | | FAIL |

## Red flags (bring these to the Project chat)

- QR and SVD coefficients differing by more than 1e-7: a basis-ordering bug or an unstable QR (for
  example classical Gram-Schmidt).
- Normal equations matching QR to 1e-12: probably not actually forming X^T X.
- Bradley-Terry with skills (1, 1, 1) not reproducing `build_A` and `rhs_win` exactly.
- A non-real eigenvalue of A, or S not symmetric: wrong move probabilities (the pair is chosen with
  probability 1/3, not 1/6).
- CG on S accurate at N = 160: check that the answer is mapped back by D^{-1/2} and compared on all
  states, not only high-pi ones.
- We have not checked Diaconis and Ethier's exact regression design (their degree, state set and
  targets) against their paper; anything compared with their published coefficients is a hypothesis
  until checked.

## Done when

- [ ] `pytest tests/c00_core tests/c10_extras` passes.
- [ ] The five CSVs and both figures exist.
- [ ] `python checks/check_c10.py` prints every row PASS (WARN allowed only on WARN rows); report saved
  to `results/c10_report.md`.
- [ ] `notes/decisions.md` has a chunk 10 entry; committed as "chunk 10: extras".

## Paste back into the Project chat

`results/c10_report.md` and the Bradley-Terry error figure.
