# Chunk 4b: fixes from the external review of chunks 1-4

- **Depends on:** chunks 1-4 (all built)
- **Learn first:** the "Math to record" section at the end of this file (it is short, and it is what you defend on Nov 20)
- **Time:** build 60-90 min · compute about 5-10 min (reruns e04_condition and e04_errors, plus one new experiment) ·
  your review about 1.5 h · plug in: optional
- **Read this yourself:** the three new functions and `notes/proofs.md`

## Why this chunk exists

Two independent referee passes (Nov 10) found no error in the model, the spectrum, the fill formula, the
MIC(0) argument or the derivation cond_i = 2 E_i[T | event]. They found five things that must change. Every
item below was re-verified in the Project chat with separate code before it was accepted.

1. **The exact reference and the float solvers solve different systems.** `build_A` stores fl(1/6), and
   fl(1/6) = (1 - 2^-54)/6. So every float solver solves (I - (1+d)Q) x = (1+d) b with d = -2^-54. Its exact
   solution differs from the true probability by d E_i[T | event] = -(u/4) cond_i in entry i: -6.9e-14 at the
   tiny entry at N = 80, -4.4e-12 at N = 640. `flint_solve` solves the ideal system. So most of the "direct
   solver error" reported in chunks 2 and 4 is this data term, not solver error.
2. **"tiny-entry error ~ cond_tiny x rtol" is not a law.** The ratio is near 1 only for rhs_out_first at the
   corner state. With the same cond (0.39 N^2) it is 13 to 48 for the right-hand side "first bust lands at
   (N/2, N/2, 0)", and its median over all states is 2e-4 (N = 640). What a residual test controls is the
   absolute error of an entry.
3. **The constant Gamma(1/3)^9 / (8 pi^4) is published.** It is twice the constant c of Diaconis and Ethier
   (2022), section 2.6, Remark 4 (due to Sangchul Lee, via Ferguson's Brownian approximation; they say it is
   not rigorous). Cite it. Our addition is the rate: the true values follow C + 34.39 / N^4.
4. **"Certified bound" is not certified.** It is an a posteriori bound computed in floating point.
5. **Wrong or loose numbers:** the normwise error at N = 640, rtol 1e-10 is 1.6e-9 (the spec said 1e-10);
   "200% wrong" at N = 1280, rtol 1e-6 is a negative probability (-4.18e-9 for +4.35e-9); kappa(MIC(0)) / N is
   0.136, 0.140, 0.150, 0.160, 0.171 at N = 20 ... 320 (not a constant 0.15); chunk 2's forward errors span
   0.074 to 0.326 kappa_inf u.

Two results got stronger: CG on b = 1 stopping after exactly floor((N-1)/2) steps now has a proof, and the
data term in item 1 is an exact, checkable prediction of the chunk 4 condition number.

## Decisions (made in the Project chat)

- "The problem" is the ideal rational system. The stored float matrix is a perturbation of relative size
  2^-54 whose effect the condition number predicts exactly.
- **Do not change `build_A` or `boundary_rhs`.** Rescaling the matrix to integers does not remove the N^2 u
  error at N >= 160 (CHOLMOD on the exactly representable 36 A is still off by 0.045 N^2 u). Report the data
  term separately instead.
- Do not edit any existing test. The new tests are in `tests/c04_accuracy/test_c04b_review.py`.
- The `plan/` edits listed below are approved; make exactly those.

## What to build (the tests import exactly these names)

`gr/accuracy.py`
- `DELTA_SIXTH = -2.0 ** -54`, with a comment: fl(1/6) = (1 + DELTA_SIXTH) / 6 exactly.
- `data_error_term(x, solve) -> np.ndarray`: `DELTA_SIXTH * solve(x) / x`. The relative change of each entry
  caused by storing 1/6 in float64, to first order: (x_stored - x_ideal)_i / x_i = DELTA_SIXTH E_i[T | event].
  Exact (to 1e-15 relative) for right-hand sides built from 1/6 alone (`rhs_out_first`); for `rhs_order` the
  individually rounded entries of b add about u.
- `aposteriori_bound(A, b, x, solve) -> np.ndarray`:
  `(componentwise_backward_error(A, x, b) + 8 * U) * entry_condition(A, b, x, solve)`, entry by entry. It
  bounds |x_stored - x|_i / |x_i| for a computed x (see "Math to record"); the 8u covers the rounding in
  evaluating the residual of a row with at most 7 nonzeros. Add `abs(data_error_term)` to bound the distance
  to the true probability.

`gr/matrix.py`
- `rhs_landing(S, y) -> np.ndarray`: P(the first bust lands exactly on the boundary state y), that is
  `boundary_rhs(S, lambda Y: np.all(Y == np.asarray(y), axis=1).astype(float))`.

## Experiments

**`experiments/e04_condition.py` (change, rerun).** Rename the column `certified_bound` to `aposteriori_bound`
and compute it as `acc.aposteriori_bound(A, b, x, solve).max()`. Add `data_term_tiny` (signed, from
`data_error_term` at the tiny state) and `data_term_over_N2u` = data_term_tiny / (N^2 u).

**`experiments/e04_errors.py` (change, rerun).** Add columns:
- `value_tiny`: the computed entry itself (so a negative probability is visible);
- `data_term_tiny`: as above, every row;
- for rows with reference "exact": `signed_err_tiny` = (x - x_ref)/x_ref at the tiny state, `solver_err_tiny` =
  signed_err_tiny - data_term_tiny, and `max_solver_err` = max_i |signed_err_i - data_term_i|;
- for rows with reference "direct": `at_reference_accuracy` = rel_err_tiny < 10 |data_term_tiny| (the reference
  is a direct solve of the stored system, whose own error is of the order of the data term).
In the docstring replace "trusted to its certified bound" by "a direct solve of the stored system; its own
error is about the size of the data term, see at_reference_accuracy".

**`experiments/e04_mechanism.py` (new)** writes two CSVs. N in {320, 640} (`--quick`: 80), plain CG (kind none),
rtol in {1e-6, 1e-8, 1e-10, 1e-12, 1e-14}, reference = CHOLMOD nesdis on the stored A (SuperLU if CHOLMOD is
missing). Right-hand sides: `out_first_3`, `order_321`, `land_mid` = rhs_landing(S, (N/2, N/2, 0)),
`land_quarter` = rhs_landing(S, (N/4, 3N/4, 0)).
- `results/e04_mechanism_rhs.csv`, one row per (N, rhs, rtol): `N, rhs, rtol, iterations, smallest_state,
  x_smallest, cond_smallest, rel_err_smallest, ratio_to_cond_rtol, normwise_rel_err, abs_err_smallest,
  abs_err_median, abs_err_max, x_max, true_relres, g_norm, residual_bound_abs, median_ratio_all_states,
  q90_ratio_all_states`. Here "smallest" is the state where x_ref is smallest; g = A^-1 e_smallest and
  g_norm = ||g||_2; true_relres = ||b - A x||_2 / ||b||_2; residual_bound_abs = g_norm ||b - A x||_2;
  the two "all_states" columns are the median and 90th percentile over every state of
  err_i / (cond_i rtol).
- `results/e04_mechanism_states.csv`, for N = 640 (quick: 80), rhs out_first_3, rtol in {1e-8, 1e-10, 1e-12}:
  4000 states drawn with `np.random.default_rng(221)` plus the 200 states with the smallest x. Columns
  `N, rtol, x1, x2, x3, x, abs_err, rel_err, cond, ratio`.

## Figures

- `figures/f04_tiny_error.py` (change): keep the three CG curves. Remove the dashed "prediction" line and the
  "SuperLU vs CHOLMOD" line (agreement between two direct solvers is not either one's error). Add a horizontal
  line at |data_term_tiny| labelled "stored-data term (u/4) cond_tiny: accuracy of the reference", and relabel
  the bound line "a posteriori bound for the direct solve". Draw points flagged `at_reference_accuracy` hollow.
- `figures/f04_mechanism.py` (new), two panels from the two new CSVs: (a) rel_err against x for the sampled
  states at N = 640, rtol 1e-10 (log-log, the corner state marked, plus the guide line max_abs_err / x);
  (b) ratio_to_cond_rtol against rtol for the four right-hand sides at N = 640 (log y, a horizontal line at 1).

## Other edits

- `checks/check_c04.py`: use `C = math.gamma(1/3)**9 / (8 * math.pi**4)` instead of the literal 9.1195890;
  drop the sentence "N = 1280 vs limit" from the report; rename the bound row; add the new rows below; label
  the ratio rows "empirical fit, this right-hand side only".
- `notes/proofs.md` (new): copy the section "Math to record" from this file, verbatim.
- `notes/decisions.md`: a chunk 4b entry; in the earlier entries, mark the constant as "published (Diaconis
  and Ethier 2022, Remark 4)" and remove it from "findings made while validating".

## Approved edits to `plan/` (make exactly these)

`plan/c01_spectrum.md`, under Goal, add: "The eigenvalue formula is a theorem (method of images; Práger 2001),
not an empirical fit. kappa_inf = 2N^2/9 needs 3 | N and N >= 6."

`plan/c02_direct.md`:
- story point 2: replace "cut fill to about n^{1.1} (n log n in theory)" by "cut fill to n log n (George 1973);
  the fitted exponent 1.1 is a local slope".
- story point 3: replace "about 0.1 to 0.25 kappa_inf u here" by "0.07 to 0.33 kappa_inf u here. Of this,
  (3/16 - 27/(16 N^2)) kappa_inf u is not solver error: it is the rounding of 1/6 in the stored matrix,
  identical for every solver, because A^{-1} t = t (1 + e2)/4 (chunk 4b)".
- expected row "err_over_kappa_u": expected becomes "0.07-0.33 (data term 0.1875 plus a solver part of either sign)".

`plan/c03_krylov.md`:
- story point 2: after "distinct eigenvalues" add "(proved: notes/proofs.md)".
- story point 4: replace "MIC(0) makes kappa ~ N (Gustafsson), so iterations grow like N^{1/2}" by "MIC(0)
  makes kappa grow about linearly (Gustafsson 1978): kappa / N = 0.136, 0.140, 0.150, 0.160, 0.171 at
  N = 20, 40, 80, 160, 320, still creeping up, so iterations grow like N^{0.55}".

`plan/c04_accuracy.md`:
- Goal, second paragraph: after "about 9.1196 / N^3" add "(the constant is Gamma(1/3)^9 / (8 pi^4), twice the c
  of Diaconis and Ethier 2022, Remark 4)".
- story point 1: replace the last sentence by "So there is no extra 1/x_i penalty for a tiny entry: its
  condition number is 0.39 N^2, the same order as kappa(A). Hypotheses: unit diagonal, off-diagonals <= 0,
  A^{-1} >= 0, b >= 0. For order right-hand sides the boundary value is P(event | landing state) and the same
  reading holds (tower property)."
- replace story points 3 and 4 by:
  "3. Direct solvers are componentwise backward stable here (omega of 1 to 20 u). Against exact rationals
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
  test, not an estimate: cond times omega overestimates CG's actual error by about 10^5."
- everywhere: `certified_bound` -> `aposteriori_bound`, "certified first-order bound" -> "a posteriori bound".
- expected row "certified_bound": becomes "aposteriori_bound | 1.5e-11 (160), 8.1e-11 (320), 3.8e-10 (640),
  1.8e-9 (1280) | below 1e-8 | FAIL".
- expected rows on ratio_tiny_to_prediction: prefix the check name with "empirical fit, this rhs only:".
- add the rows of the table below.

## Acceptance tests

`pytest tests/c00_core tests/c01_spectrum tests/c02_direct tests/c03_krylov tests/c04_accuracy` (15 new tests,
about 3 s; they skip until the three new functions exist). They check that 1/6 is stored low by exactly 2^-54;
that the exact solution of the stored system differs from the ideal one by the data term in every entry
(N = 12, 20, exact rationals on both sides); the same for order right-hand sides and for b = 1 (through the
identity A^{-1} t = t (1 + e2)/4); that SuperLU's error at the tiny entry at N = 40 is mostly the data term;
that the a posteriori bound holds against the exact stored solution; `rhs_landing`; the identity
e_i = (A^{-1} e_i) . r with ||A^{-1} e_corner||_2 = 1.1702; and that the cond x rtol fit fails for another
right-hand side and at typical states (N = 320).

## Expected results (add these rows to check_c04; reference values are from a Linux run)

| Check | Expected | Tolerance | Kind |
|---|---|---|---|
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

## Red flags (bring these to the Project chat)

- data_term_tiny off by more than 1e-3: the formula or the solve is wrong (it is platform independent).
- A solver-only error larger than the data term at N = 80.
- The rigorous bound abs_err <= g_norm ||r||_2 violated.
- Any existing chunk 1-4 test failing after the change.

## Done when

- [ ] All chunk 0-4 tests pass, including the 15 new ones.
- [ ] `e04_condition`, `e04_errors` and `e04_mechanism` rerun from a clean commit; both figures regenerated.
- [ ] `python checks/check_c04.py` has no FAIL; `results/c04_report.md` regenerated.
- [ ] `notes/proofs.md` exists; `plan/` edits made exactly as listed; committed as "chunk 4b: review fixes" and pushed.

## Paste back into the Project chat

`results/c04_report.md`, `figures/f04_tiny_error.png` and `figures/f04_mechanism.png`.

---

## Math to record (copy this section into `notes/proofs.md`)

Notation: A = I - Q on the live states, Q >= 0 with zero diagonal; T = the round on which the first bust
happens (T >= 1); u = 2^-53.

### 1. CG on b = 1 stops after exactly K = floor((N-1)/2) steps (exact arithmetic, x0 = 0)

For an integer k let theta = 2 pi k / N and v_k(x) = sin(theta x1) + sin(theta x2) + sin(theta x3).
- v_k vanishes on the boundary: if one coordinate is 0 the other two are m and N - m, and
  sin(theta m) + sin(theta (N - m)) = 0.
- The six moves change each coordinate by +1 twice, -1 twice and 0 twice, so
  (Q v_k)(x) = (1/6) sum_a sin(theta x_a)(4 cos theta + 2), and A v_k = (4/3) sin^2(pi k / N) v_k.
- Sawtooth: for m = 1..N-1, 1/2 - m/N = (1/N) sum_{k=1}^{K} cot(pi k / N) sin(2 pi k m / N).
  Summing over the three coordinates of a live state (they add up to N) gives
  1 = (2/N) sum_{k=1}^{K} cot(pi k / N) v_k.
- For 1 <= k <= K the coefficients are positive, the eigenvalues are distinct (increasing in k), and
  v_k(1, 1, N-2) = 2 sin(theta)(1 - cos(theta)) > 0, so v_k != 0.
So b = 1 is a combination with nonzero coefficients of K eigenvectors with K distinct eigenvalues; the Krylov
space has dimension exactly K, and CG is exact at step K and not before. In floating point the count stretches
by 3 to 8% for N >= 80.

### 2. cond_i = 2 E_i[T | event], with its hypotheses

cond_i = (|A^-1| (|A||x| + |b|))_i / |x_i| (Skeel; Higham, Accuracy and Stability, ch. 7).
- |A^-1| = A^-1 because A^-1 = sum_t Q^t >= 0.
- |A| = I + Q = 2I - A because the diagonal is 1 and the off-diagonals are <= 0.
- |x| = x and |b| = b because b >= 0. (True for out_first, order, win and b = 1; not for a random b.)
- Then |A||x| + |b| = 2x - Ax + b = 2x, so cond_i = 2 (A^-1 x)_i / x_i.
With f the boundary value, x_i = E_i[f(X_T)] and (Q^t x)_i = E_i[f(X_T); T > t]; summing over t gives
(A^-1 x)_i = E_i[T f(X_T)]. If f is the indicator of an event this is E_i[T; event]. For an order
probability, f(y) = P(event | X_T = y) and E_i[T f(X_T)] = E_i[T 1{event}] by the tower property (T is known at
time T). Either way cond_i = 2 E_i[T | event]. The worst case A - eps|A|, b + eps|b| raises every entry at once.
This treats the diagonal as free data: such perturbations change the row sums (compare chunk 7).

### 3. The stored system and the data term

1/6 in binary is 0.0010101..., and rounding to 53 bits rounds down: fl(1/6) = (1 + d)/6 with d = -2^-54 exactly.
For rhs_out_first the stored system is (I - (1+d)Q) x' = (1+d) b. With A_d = I - (1+d)Q and Qx = x - b:
x' - x = A_d^-1 [(1+d) b - A_d x] = d A_d^-1 (b + Qx) = d A_d^-1 x, so
(x' - x)_i / x_i = d E_i[T | event] + O(d^2) = -(u/4) cond_i.
At the tiny entry this is -0.0971 N^2 u. Every float solver inherits it, at any stopping rule; exact rational
solves of the ideal system do not. For b = 1 only Q is perturbed: x' - t = d A_d^-1 Q t, and because
A^-1 t = t (1 + e2)/4 (e2 = x1 x2 + x1 x3 + x2 x3; p = e3 (1 + e2) satisfies p - mean of p over the six
neighbours = 4 e3 and vanishes on the boundary), (x' - t)_i / t_i = d (e2 - 3)/4. In chunk 2's metric that is
(3/16 - 27/(16 N^2)) kappa_inf u when 3 | N.

### 4. What a residual stopping rule controls

With r = b - A x_hat, x - x_hat = A^-1 r, so e_i = g_i . r with g_i = A^-1 e_i (row i of A^-1: expected visits
to each state from i). By Cauchy-Schwarz |e_i| <= ||g_i||_2 ||r||_2 <= ||g_i||_2 rtol ||b||_2. At the corner
||g_i||_2 = 1.1702 for every N, ||b||_2 = sqrt(N-2)/3 for out_first, and x_tiny = 9.12 / N^3, so the best a
residual test can promise there is a relative error of 0.043 N^3.5 rtol. The observed error is 5e-4 to 1.5e-2
of that bound. The componentwise condition number does not enter: cond_i measures the response to
perturbations |dA| <= eps|A|, |db| <= eps|b|, and a normwise-small residual is not of that form.

### 5. The a posteriori bound

For a computed x_hat, x' - x_hat = A^-1 r exactly, so |x' - x_hat| <= A^-1 |r| (A^-1 >= 0), and by the
definition of omega, |r| <= omega (|A||x_hat| + |b|). Hence |x' - x_hat|_i / x_hat_i <= omega cond_i(x_hat), with
no first-order approximation. In floating point the residual of a row with 7 nonzeros is itself only accurate
to 8u (|A||x_hat| + |b|), which gives (omega + 8u) cond_i(x_hat). This bounds the distance to the stored
solution x'; add (u/4) cond_i for the distance to the true probability. It is computed in floating point, so
it is a bound to trust, not a machine-checked certificate.

### 6. The constant

Diaconis and Ethier, "Gambler's ruin and the ICM", Statist. Sci. 37 (2022), section 2.6: Theorem 2.5 proves
P_{1,1,N-2}(player 3 out first) is of order N^-3. Remark 4 gives P_{1,1,N-2}(321) ~ c / N^3 with
c = (sqrt(pi) / (3 sqrt 3)) (Gamma(1/3) / Gamma(5/6))^3 = 4.55979449996, from unpublished work of Sangchul Lee
using Ferguson's Brownian approximation, and says the approximation is not rigorously justified to this degree.
By symmetry P(3 out first) = 2 P(321) at (1, 1, N-2), and 2c = Gamma(1/3)^9 / (8 pi^4) = 9.11958899992 (reflection
and duplication formulas; checked to 39 digits). Our addition: with a correctly rounded reference the values
follow C + 34.39 / N^4 ((v - C) N^4 = 34.375, 34.388, 34.391 at N = 160, 320, 640), measured, not proved.
