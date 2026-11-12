# Chunk 7b: fixes from the external review of chunks 4b and 7

- **Depends on:** chunks 4b and 7 (all built)
- **Learn first:** "Math to record" at the end of this file (three short sections; this is what you defend on Nov 20)
- **Time:** build 45-75 min · compute about 5-8 min (one rerun of e07_structured, one new experiment) ·
  your review about 1 h · plug in: optional · memory about 1.5 GB (band storage at N = 640)
- **Read this yourself:** `structured_condition`, `exact_residual`, and `notes/proofs.md` sections 7 to 9

## Why this chunk exists

Two referee passes (Nov 11, commit 2a9fbe7, both read-only) found no error in `notes/proofs.md` sections 3 and 5,
in `integer_system`, in the Dot2 loop, in GTH (every operation one-signed), in "GTH is immune to the rounding of
1/6", or in any number they compared with the CSVs. They found four things that must change. Each one was
re-verified in the Project chat with independent code (its own matrix builder, SuperLU solves, and exact
Python-integer residuals validated against exact rational solves at N = 12, 20, 30).

1. **The structured sensitivity is not bounded in N.** Chunk 7 perturbed off-diagonals, row sums and b with 20
   random draws and one push, saw ratios of 1.5 to 5, and concluded "2-5 eps at every N". A condition number is a
   maximum, and the experiment never tried the worst direction. The exact first-order structured condition number
   is kappa_i = (A^-1 v)_i / x_i with v_i = b_i + s_i x_i + sum_j |a_ij| |x_i - x_j| (one extra solve). At the tiny
   entry it is 1.22 N (11.35, 23.80, 48.30, 97.10, 194.6, 389.5, 779.2 at N = 10 ... 640), and one perturbation
   attains it in every entry. A reviewer's explicit direction, A + eps (HA - AH) with H = diag(x3), moves the tiny
   entry by exactly N - 3. So the correct statement has four levels: 0.39 N^2 (entries of A, diagonal free),
   1.22 N (structured), about log N (structured and symmetric: 17.4 at N = 640), O(1) (random draws).
2. **"Ordinary elimination has an N^2 u error" was measured on one solver.** The own error of a direct solver
   (against the stored solution) depends on the algorithm, not only on the data. Tiny entry, N = 160 to 640,
   Linux: supernodal CHOLMOD +0.050 to +0.052 N^2 u (Mac: +0.032), SuperLU COLAMD +0.031 to +0.035, SuperLU in
   natural order -0.07 to -0.14, simplicial CHOLMOD -0.006, LAPACK band Cholesky under 0.005. CHOLMOD's sign flip
   between N = 80 and 160 is its switch from simplicial to supernodal. So "GTH beats direct by 25 to 133" is
   mostly the data term that GTH does not have, plus supernodal CHOLMOD's own error. Against a band Cholesky of
   the integer matrix 6A (no data term either) both are within tens of u for N <= 80 (29, 56, 49 u against GTH's
   8, 12, 34 u), and GTH is 4, 13, 19 times better at N = 160, 320, 640 (that solve keeps a small N^2 u term:
   194, 749, 3844 u; GTH: 46, 60, 200 u).
3. **The thesis named two error sources; the data show three:** the stopping rule, the stored data
   (-0.097 N^2 u), and the solver's own arithmetic (N^2 u with a constant between 0.005 and 0.14 that depends on
   the algorithm, the ordering, the scaling and the machine).
4. **Wording.** The stored solution x' = x + d A_d^-1 x is an exact identity, not first order
   (x'_i = E_i[(1+d)^T; event]). The Dot2 residual is not "correct to about 2u" in general: its bound is
   2u |r_i| + about 64 u^2 (|A||x| + |b|)_i, and a reviewer built an input where the loop returns 0 for a nonzero
   residual. The 4u stopping test does not prove correct rounding. "2 to 20 times closer than CHOLMOD" is "2 to 5
   times" with one AMG outlier. Many "Expected" values in `plan/c07_fixes.md` were rewritten from the Mac run, so
   "22 PASS" is a regression result, not an independent confirmation.

One result got stronger: refinement is now checked beyond N = 80. With exact integer residuals, the error of
every entry is known to about 10 digits, and the refined solution is within half an ulp of the true probability
in every entry at N = 160, 320, 640 and 1280 (Project chat, independent code; this chunk repeats it in the repo).

## Decisions (made in the Project chat)

- The perturbation model stays as in chunk 7: every off-diagonal entry, every row sum and every b_i independent
  (so A' need not be symmetric), diagonal rebuilt. The symmetric model is reported as one extra column.
- **Do not rerun `e07_fixes`.** The new numbers go to a new CSV, `e07_baselines.csv`.
- **Do not change `build_A`, `gth_solve`, `accurate_residual` or `iterative_refinement`** (only docstrings).
- Do not edit any existing test, except the one docstring listed under "Approved edits". The new tests are in
  `tests/c07_fixes/test_c07b_review.py` (20 tests, validated in the Project chat against an independent
  stand-in implementation).
- The `plan/` edits listed below are approved; make exactly those.

## What to build (the tests import exactly these names)

`gr/accuracy.py`
- `structured_condition(A, b, x, row_sums, solve) -> np.ndarray`: kappa_i = (A^-1 v)_i / x_i with
  v_i = b_i + row_sums_i x_i + sum_{j != i} |a_ij| |x_i - x_j|. `solve(r)` applies A^-1. Hypotheses: off-diagonals
  <= 0, row sums >= 0, b >= 0, A^-1 >= 0, x > 0. Reference implementation:
  ```python
  C = sp.coo_matrix(A); off = C.row != C.col
  r, c, w = C.row[off], C.col[off], -C.data[off]
  v = b + row_sums * x + np.bincount(r, weights=w * np.abs(x[r] - x[c]), minlength=C.shape[0])
  return solve(v) / x
  ```

`gr/refine.py`
- `exact_residual(A, b, x, denom=1) -> np.ndarray`: (b - A x) / denom with every entry correctly rounded. The
  float values of A, b and x are converted to exact Python integers, each row is summed exactly, and one integer
  division rounds once. A Python loop, slow, for checks only. `denom` must be a positive integer. Works for any
  CSR shape. Reference implementation (validated; keep the arithmetic as it is):
  ```python
  def _scaled_ints(v):
      """Python integers V and a shift s with v[i] = V[i] / 2**s exactly."""
      v = np.asarray(v, dtype=float)
      m, e = np.frexp(v)
      M = np.ldexp(m, 53).astype(np.int64)  # exact: m has 53 significant bits
      s = int((53 - e).max())
      return [int(a) << (s - 53 + int(k)) for a, k in zip(M.tolist(), e.tolist())], s

  def exact_residual(A, b, x, denom=1):
      A = sp.csr_matrix(A)
      ip, ix = A.indptr, A.indices
      Ad, sa = _scaled_ints(A.data)
      X, sx = _scaled_ints(x)
      Bv, sb = _scaled_ints(b)
      if int(denom) != denom or denom < 1 or sa + sx < sb:
          raise ValueError("denom must be a positive integer (and b must not need more bits than A x)")
      up, D = sa + sx - sb, int(denom) << (sa + sx)
      r = np.empty(A.shape[0])
      for i in range(A.shape[0]):
          R = Bv[i] << up
          for k in range(ip[i], ip[i + 1]):
              R -= Ad[k] * X[ix[k]]
          r[i] = R / D  # Python's int / int is correctly rounded
      return r
  ```
  Use: `exact_residual(A, b, xhat)` is the residual of the stored system; with
  `Ai, B = integer_system(A, b, 6 * N)`, `exact_residual(Ai, B, xhat, denom=6 * N)` is the residual of the ideal
  system. Then, with any float solve, `xhat - x_stored = -solve(residual of the stored system)` and
  `xhat - x_true = -solve(residual of the ideal system)`, each accurate to about 10 digits.
- Docstrings only:
  - module docstring, item 2: replace "computed from them without rounding error" by "computed from them with a
    compensated (Dot2) sum".
  - `accurate_residual`: replace "Each entry is correct to about 2u (one rounding of s + c, one of the division)."
    by "Error of entry i: at most 2u |r_i| + about 64 u^2 (|A||x| + |b|)_i (Ogita, Rump and Oishi's Dot2 bound).
    That is about 2u only while the first term dominates; `exact_residual` is the exact (slow) version."
  - `iterative_refinement`: add "The 4u test is a stopping rule, not a proof of correct rounding."

`gr/accuracy.py`, docstring of `data_error_term`: replace "to first order" by "(exactly: x' - x = d A_d^-1 x, and
`solve` applies the stored inverse A_d^-1, so x (1 + data_error_term(x)) is the stored solution up to rounding)".

## Experiments

**`experiments/e07_structured.py` (change, rerun).** N in {10, 20, 40, 80, 160, 320, 640} (`--quick`: 10, 20).
Keep the existing computations and their order (so the old columns do not change for N <= 160) and add, with x the
base solution and tiny = (1, 1, N-2):
- `structured_cond_tiny`, `structured_cond_max`, `structured_argmax_state`, `structured_cond_over_N`
  (= structured_cond_max / N), from `acc.structured_condition` on the base system;
- `attained_tiny` and `attained_max_dev`: solve the system with off-diagonal weights times
  1 + eps sign(x_j - x_i), row sums times (1 - eps) and b times (1 + eps) (eps = 1e-8, `structured_matrix`);
  ratio_i = (x'_i - x_i) / x_i / eps; record the ratio at tiny and max_i |ratio_i / kappa_i - 1|;
- `coherent_tiny`: solve (A + eps (H A - A H)) x' = b with H = diag(S.x3) and A from `build_A`; the ratio
  (x' - x0) / x0 / eps at tiny, with x0 = solve(A, b) (the same A, so no diagonal rounding enters);
- `drift_tiny`: off-diagonal weights times 1 + eps sign(x_j - x_i) only (row sums and b unchanged); ratio at tiny;
- `symmetric_cond_tiny`: with g = solve(e_tiny) and each unordered pair {i, j} counted once,
  (sum_i g_i (b_i + s_i x_i) + sum_{i<j} |a_ij| |g_i - g_j| |x_i - x_j|) / x_tiny;
- `cond_tiny` (chunk 4's componentwise number at tiny) next to the existing `cond_max`.

**`experiments/e07_baselines.py` (new)** writes `results/e07_baselines.csv`. b = rhs_out_first(S, 2). N in
{20, 40, 80, 160, 320, 640} (`--quick`: 20, 40), plus N = 1280 for `cholmod_default` and `ir_direct` only. One
CHOLMOD nesdis factor F per N (`gr.direct.factorize(A, "cholmod", "nesdis")`) supplies `solve` for the error
formulas. Methods (each returns xhat):

| method | how | sizes |
|---|---|---|
| `cholmod_default` | F.solve(b) (this is e07_fixes' "direct") | all, and 1280 |
| `cholmod_simplicial`, `cholmod_supernodal` | `sksparse.cholmod.cho_factor(A.tocsc(), order="nesdis", supernodal_mode=...)` with "simplicial" / "supernodal" | all |
| `splu_colamd`, `splu_natural` | `gr.direct.factorize(A, "splu", "COLAMD" / "NATURAL")` | all; natural only N <= 320 |
| `banded` | `gr.direct.factorize(A, "banded_cholesky", "natural")` | all (1 GB at 640) |
| `banded_int` | A6, B6 = `integer_system(A, b, 6)` (entries 6 and -1, right-hand side 0, 1, 2: exact in float64, so no data term); band Cholesky of A6, solve with B6 | all |
| `cholmod_int` | CHOLMOD nesdis on A6, B6 | all |
| `gth` | `refine.gth_solve(A, b, row_sums)` | all |
| `ir_direct` | `refine.iterative_refinement(A, b, F.solve, 6 * N)` | all, and 1280 |

If this scikit-sparse has no `supernodal_mode` keyword, skip those two rows and say so in the report.

Errors, with `Ai, B = integer_system(A, b, 6 * N)`:
- `true_err = -F.solve(exact_residual(Ai, B, xhat, denom=6 * N)) / xhat` (signed, every entry), for every method;
- `own_err = -F.solve(exact_residual(A, b, xhat)) / xhat`, only for the methods that solve the stored system
  (`cholmod_*` except `cholmod_int`, `splu_*`, `banded`); NaN for the others.

Columns: `N, n, method, own_err_tiny, own_err_over_N2u, max_own_err_in_u, true_err_tiny, true_err_over_N2u,
max_true_err_in_u, max_true_err_in_ulp, data_term_tiny, seconds`. Here `*_over_N2u` = the tiny-entry error divided
by N^2 u; `max_true_err_in_ulp` = max_i |true_err_i xhat_i| / np.spacing(xhat_i); `data_term_tiny` =
`acc.data_error_term(x, F.solve)` at tiny with x = F.solve(b); `seconds` = one run of the solve (not a benchmark).

## Figures

- `figures/f07_structured.py` (change): log-log against N, from e07_structured.csv: `cond_max` with a guide
  0.39 N^2, `structured_cond_max` with a guide 1.22 N, `symmetric_cond_tiny`, `structured_push`,
  `structured_random_max`. Title: "Sensitivity of the tiny probability: N^2 for A's entries, N for off-diagonals
  and row sums, log N if symmetric, O(1) for random perturbations". Remove the old title.
- `figures/f07_baselines.py` (new), two panels from e07_baselines.csv (N <= 640): (a) |own_err_tiny| against N for
  the stored-system methods, with the line |data_term_tiny| and guides u N and u N^2; (b) max_true_err_in_u
  against N for `cholmod_default`, `banded`, `banded_int`, `cholmod_int`, `gth`, with guides N and N^2.

## Approved edits (make exactly these)

`plan/c07_fixes.md`
1. Goal, first bullet: replace "approximated by\n  x_ref (1 + data_error_term(x_ref)); and" by "computed as
   x_ref (1 + data_error_term(x_ref)), which is the exact identity x' = x + d A_d^-1 x evaluated in floating point
   (notes/proofs.md section 3), not a first-order formula; and".
2. Fix 1: replace the sentence that starts "In every run that converges," and ends "rtol 1e-10 rule." by
   "In every run that converges, the tiny entry ends up 2 to 5 times closer to the stored solution than the
   default CHOLMOD solve's (Mac: 2.9e-14 against 9.1e-14 at N = 160, 3.0e-13 against 1.5e-12 at N = 640, plain CG;
   one AMG run is 20 times closer), for 1.25 to 1.9 times the iterations of the usual rtol 1e-10 rule. That is the
   size of the own error of the most accurate direct solves (band Cholesky, simplicial CHOLMOD), not better:
   CHOLMOD's default from N = 160 is supernodal and carries an own error of +0.03 to +0.05 N^2 u (chunk 7b)."
3. Fix 2: replace "give every entry correctly rounded, error 0\n   against exact rationals." by "give every entry
   correctly rounded in every tested case: error 0 against exact rationals for N <= 80, and within half an ulp at
   N = 160 to 1280 by exact integer residuals (chunk 7b). The 4u stopping test is not a proof of that."
4. Fix 3: after "and that common factor cancels in the solution." add " Most of GTH's 25- to 133-fold gain over
   CHOLMOD is that missing data term plus supernodal CHOLMOD's own error. Against a band Cholesky of the integer
   matrix 6A, which has no data term either, GTH is better by 1.4 to 5 for N <= 160 and by a factor that grows
   with N above (about 11 at N = 320 and 20 at N = 640 on the Mac: e07_baselines)."
5. Replace the whole paragraph that starts "Why 3 works:" by:
   "Why 3 works: the componentwise condition number from chunk 4 (0.39 N^2) measures sensitivity to perturbations
   of A's entries with the diagonal free, which is the wrong parametrization for an M-matrix (Alfa, Xue and Ye).
   Perturb instead each off-diagonal entry, each row sum and each b_i relatively by eps, diagonal rebuilt: the
   worst case moves entry i by eps kappa_i, kappa_i = (A^-1 v)_i / x_i with v_i = b_i + s_i x_i + sum_j |a_ij| |x_i - x_j|
   (chunk 7b). At the tiny entry kappa = 1.22 N. It is not bounded in N (a coherent drift toward the event attains
   it; the reviewer's direction A + eps (HA - AH) alone gives N - 3), but it is a factor 0.32 N below the
   componentwise number. Random perturbations move x by only 1.5 to 3.1 eps and symmetric ones by about log N
   (17.4 at N = 640). GTH's measured error, 0.19 to 0.42 N u, is 0.16 to 0.34 kappa u: a subtraction-free
   algorithm is stable in this parametrization."
6. `accurate_residual` bullet: replace "Each entry is then correct to about 2u (a final rounding and the
   division)." by "The error of entry i is at most 2u |r_i| + about 64 u^2 (|A||x| + |b|)_i (the Dot2 bound), which
   is about 2u only while the first term dominates."
7. e07_fixes paragraph: replace "(first order in 2^-54, accurate to about u)" by "(an exact identity evaluated in
   floating point, accurate to about u)".
8. e07_structured paragraph: after the sentence that ends "`structured_random_max, structured_push, cond_max,
   two_n_minus_1`." add " Chunk 7b extends this to N = 640 and adds the structured condition number and the
   directions that attain it (plan/c07b_review_fixes.md)."
9. Figures: replace "(structured ratios vs cond_max against N)" by "(the four sensitivities against N: see
   plan/c07b_review_fixes.md)".
10. Expected results: replace the row "e07_fft_check: FFT rel_err_smallest at N = 800" by
    "| e07_fft_check: FFT rel_err_smallest at N = 800 | 4.8e-7 on the Mac (6e-7 and 2e-6 on two Linux reference implementations) | in [1e-8, 1e-4] | WARN |".
11. Expected results: replace the three rows "structured_random_max", "structured_push" and
    "cond_max / structured_push" by the e07_structured rows of the table below, and add the e07_baselines rows.
    Above the table add: "Rows that quote Mac values were rewritten from this run on Nov 11: they are regression
    checks. The independent confirmations are the exact-rational tests (N <= 80), GTH against refinement, the
    exact-integer rows of e07_baselines, and the Project chat's Linux recomputations."
12. Red flags: replace "A structured ratio growing with N." by "structured_cond_over_N outside [1.1, 1.25], or the
    attaining perturbation not reaching kappa: the formula or the perturbation is wrong. (kappa itself grows like
    N; that is the result.)"
13. Done when: replace "e07_fixes.csv, e07_structured.csv, e07_floor.csv and both figures exist." by
    "e07_fixes.csv, e07_structured.csv, e07_floor.csv, e07_baselines.csv and the three figures exist."

`notes/proofs.md`: append the three sections of "Math to record" below, verbatim, as sections 7, 8 and 9.

`tests/c04_accuracy/test_c04b_review.py`, one docstring only (the line that says 1.1702 holds "for every N"):
replace "for every N" by "for N >= 40".

`checks/check_c07.py`: mirror edits 10 to 12; add the rows below; in the red-flag text replace "(ordinary
elimination grows like N^2: slope 2)" by "(the default CHOLMOD solve grows like N^2: slope 2)".

`notes/decisions.md`: a chunk 7b entry (what changed and why; which rows are regression checks).

## Acceptance tests

`pytest tests/c00_core tests/c04_accuracy tests/c07_fixes` (20 new tests in `test_c07b_review.py`, about 3 s; they
skip until both new functions exist). They check the structured condition number against reference values at
N = 10, 20, 40, 80, that one perturbation attains it in every entry, the reviewer's direction (admissible, and
N - 3 at the tiny entry), random draws far below it, the ordering N - 3 < kappa < 1.25 N and cond / kappa = 0.32 N,
`exact_residual` against Fraction arithmetic and on the reviewer's row, the Dot2 bound for `accurate_residual`,
correct rounding of refinement at N = 160, and the exact stored-solution identity.

## Expected results (add these rows to check_c07; values are from the Project chat's independent Linux code)

| Check | Expected | Tolerance | Kind |
|---|---|---|---|
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

- Any FAIL row above. In particular `ir_direct` not within half an ulp, or `cholmod_default` disagreeing with
  e07_fixes: then the reference of chunk 7 is in question.
- `attained_tiny` below `structured_cond_tiny`, or `coherent_tiny` not N - 3: the formula or a perturbation is wrong.
- A test in `test_c07b_review.py` failing: do not edit it; say which and why.
- Any existing test failing after the docstring edits.

## Done when

- [ ] `pytest tests/c00_core tests/c04_accuracy tests/c07_fixes` passes, including the 20 new tests.
- [ ] `e07_structured` rerun and `e07_baselines` run from a clean commit; `f07_structured` regenerated and
      `f07_baselines` made.
- [ ] `python checks/check_c07.py` has no FAIL; `results/c07_report.md` regenerated.
- [ ] `notes/proofs.md` has sections 7 to 9; the `plan/` and docstring edits are made exactly as listed;
      committed as "chunk 7b: review fixes" (code) and "chunk 7b: results", and pushed.

## Paste back into the Project chat

The summary line of `results/c07_report.md`, every WARN or FAIL line, the e07_baselines data table, both commit
hashes, and `figures/f07_structured.png` and `figures/f07_baselines.png`.

---

## Math to record (append to `notes/proofs.md` as sections 7, 8 and 9)

### 7. The structured condition number

Describe the M-matrix by its off-diagonal weights w_ij = -a_ij >= 0 (each ordered pair separately), its row sums
s_i >= 0 and the right-hand side b_i >= 0; the diagonal is a_ii = s_i + sum_j w_ij, never data. Perturb every
parameter by a relative amount of at most eps. With x = A^-1 b,
(dA x)_i = ds_i x_i + sum_j dw_ij (x_i - x_j), and dx = A^-1 (db - dA x).
Because A^-1 >= 0, the largest first-order change of entry k is eps (A^-1 v)_k with
v_i = b_i + s_i x_i + sum_j w_ij |x_i - x_j|,
and one perturbation attains it in every entry at once: dw_ij = eps w_ij sign(x_j - x_i) (a drift toward the
event), ds = -eps s, db = +eps b. So kappa_k = (A^-1 v)_k / x_k. Since A^-1 b = x, the b term contributes exactly 1.
Reading it as in section 2 (G(k, i) x_i / x_k is the expected number of visits to i of the walk conditioned on the
event): kappa_k = 1 + E_k[ sum_{t < T} ( s(X_t) + sum_j w |x_j - x(X_t)| / x(X_t) ) | event ]. The componentwise
number charges 2 per step (cond = 2 E[T | event]); the structured one charges the relative variation of x across
one step, which near the corner is of order 1/r at distance r (x grows like r^3 there), and that adds up to order N
(a heuristic for the growth; the numbers below are measured).

Lower bound with no computation (review 2): let h_i = x3 at state i and H = diag(h). A(eps) = A + eps (HA - AH)
has a_ij(eps) = a_ij (1 + eps (h_i - h_j)) with h_i - h_j in {-1, 0, 1}, the same diagonal, and row sums that move by
eps (1/6) sum over busting moves of (h_i - h_y), at most eps s_i (h is harmonic for the six moves). So it is an
admissible perturbation. For out_first_3, b lives where h = 1, so Hb = b and differentiating A(eps) x(eps) = b
gives dx/deps = (H - I) x: entry i moves by (h_i - 1) eps x_i, that is N - 3 at (1, 1, N-2). Hence kappa_tiny >= N - 3.

Measured (N = 10 ... 640): kappa_tiny = max_i kappa_i = 11.35, 23.80, 48.30, 97.10, 194.6, 389.5, 779.2, that is
1.1353 N rising to 1.2176 N; the smallest kappa_i over all states is 2.5. If only symmetric perturbations are
allowed (w_ij and w_ji move together), the tiny entry's number is
(sum_i g_i (b_i + s_i x_i) + sum_{i<j} w_ij |g_i - g_j| |x_i - x_j|) / x_tiny with g = A^-1 e_tiny:
6.2, 8.3, 10.2, 12.0, 13.8, 15.6, 17.4, about 1.8 more per doubling (log N). Random perturbations: 1.5 to 3.1.
So there are four levels: 0.39 N^2 (entries of A, diagonal free), 1.22 N (structured), log N (structured and
symmetric), O(1) (random). The chunk 7 statement "2 to 5 eps at every N" described the last one only.
The Alfa-Xue-Ye bound for this parametrization has a coefficient of order n; it does not promise O(1) either.
GTH's measured error, 0.19 to 0.42 N u, is 0.16 to 0.34 kappa u.

### 8. Three sources of error at a tiny entry

1. **The stopping rule.** A residual test bounds the absolute error (section 4): up to 100% relative error.
2. **The stored data.** x'_i = E_i[(1+d)^T; event] exactly, because x' = sum_t (1+d)^(t+1) Q^t b. Hence
   d E_i[T | event] <= (x' - x)_i / x_i <= d E_i[T | event] + (d^2 / 2) E_i[T^2 | event]; the second-order term is
   about 3e-22 at N = 1280, and x' = x + d A_d^-1 x is an identity (section 3). In the parameters of section 7 the
   rounding of 1/6 is harmless (it scales w, s and b by the same factor: that is why GTH does not see it). It
   costs 0.097 N^2 u only because the stored matrix keeps its diagonal at 1: interior row sums go from 0 to
   2^-54, which is not a small relative change of a row sum.
3. **The solver's own arithmetic.** Against the stored solution, at the tiny entry, N = 160 to 640 (Linux):
   supernodal CHOLMOD +0.05 N^2 u (Mac +0.032), SuperLU COLAMD +0.03, SuperLU natural -0.07 to -0.14, simplicial
   CHOLMOD -0.006, LAPACK band Cholesky below 0.005. The N^2 growth means the rounding errors do not average
   out; why they are coherent (identical local arithmetic on a regular lattice is our guess) is not established.
   The constant changes with the algorithm, the ordering, the scaling (CHOLMOD on the integer matrix 6A:
   +0.18 N^2 u) and the machine.

What each fix removes: componentwise stopping removes 1 and leaves 2 and 3 (it lands as close to the stored
solution as the best direct solves). Refinement with the residual of the ideal integer system removes all three:
correctly rounded in every tested case (exact rationals for N <= 80; exact integer residuals for N = 160 to 1280).
GTH never forms 2 and has no N^2 term in 3: 0.19 to 0.42 N u, not correctly rounded. A band Cholesky of the
integer matrix 6A also avoids 2 but keeps a small N^2 term (0.0094 N^2 u at N = 640, 19 times GTH's error).

### 9. What the compensated residual guarantees

Dot2 (Ogita, Rump and Oishi 2005, Proposition 5.5) gives |r_hat - r| <= u |r| + gamma_m^2 sum_k |a_k x_k| with
gamma_m = m u / (1 - m u): for a row with 7 nonzeros, about 2u |r_i| + 64 u^2 (|A||x| + |b|)_i after the division.
It is not exact: for the row of state (2, 2, 16) at N = 20, coefficients (-20, -20, -20, 120, -20, -20, -20), and
x = (q, t, 1, 3002399751580331 q, q, 0, 0) with q = 2^-54, t = 2^-174, the exact residual is 20 t and the loop
returns 0 (review 2; reproduced). Near a solution the bound is far more than refinement needs, and in every
case checked there (N = 12, 40, 160, the Project chat's transcription of the loop) the result equals the correctly
rounded residual. The stopping
test of the refinement (last correction at most 4u) is a stopping rule. Correct rounding is a measured result:
after the last step the error is the inner solve's error on a correction of size u, plus one rounding.
