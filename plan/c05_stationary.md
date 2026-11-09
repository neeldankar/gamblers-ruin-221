# Chunk 5: Stationary methods and the SOR 3/4 law

- **Depends on:** chunk 1 (rho_J comes from the exact spectrum; `gr.spectrum.kappa2` bounds the forward error)
- **Learn first:** Theory Guide §5 (splitting methods: Jacobi, Gauss-Seidel, SOR, Young's theory) and §4 (model problems and exact spectra)
- **Time:** build 45-60 min · compute about 5-10 min (6 min on a slow 2-core cloud machine) · your review about 1.5 h · plug in: no
- **Read this yourself:** `gr/stationary.py` (the three sweeps, the stopping rule and `iteration_matrix`; you will present the 3/4 law, so you must be able to explain every line)

## Goal

Measure Jacobi, Gauss-Seidel and SOR against exact predictions, and pin down one result that Young's
textbook theory does not cover for this matrix.

The predictions come from chunk 1. The diagonal of A is 1, so a Jacobi sweep is x <- Q x + b and the
Jacobi iteration matrix is Q = I - A, with spectral radius rho_J = 1 - lambda_min = (1 + 2 cos(2 pi/N))/3.
Young's theory then predicts rho_GS = rho_J^2, the best omega* = 2/(1 + sqrt(1 - rho_J^2)), and
rho(SOR(omega*)) = omega* - 1. But Young's theory assumes a consistently ordered matrix, and the
7-point triangular stencil in lexicographic order is not consistently ordered (its graph has
triangles). What happens instead, measured to rounding with dense eigenvalues at 13 sizes from N = 6
to N = 100:

- rho_GS is slightly above rho_J^2 (N^4 times the gap rises from 10 at N = 6 to 19.2 at N = 100).
- Young's omega* is still exactly the minimizer of rho(SOR(omega)).
- **rho(SOR(omega*)) = (omega* - 1)^(3/4)**, not omega* - 1. At N = 6 it is a closed form:
  omega* - 1 = phi^-4 and rho = phi^-3 = sqrt(5) - 2, with phi the golden ratio.

So SOR at omega* converges with 3/4 of the exponent Young's theory promises and needs 4/3 as many
sweeps asymptotically (1.44 times as many at rtol = 1e-10, see below): still O(N) sweeps, against
O(N^2) for Jacobi and Gauss-Seidel. This chunk establishes the law numerically in two
independent ways (dense eigenvalues, and residual histories of the real sweeps up to N = 640). There
is no proof here, and we did not find the law stated anywhere; treat it as a computational finding
until the Project chat has looked at the literature. A possible starting point is the SOR analysis of
another stencil that is not consistently ordered, the 9-point Laplacian (Adams, LeVeque and Young,
SIAM J. Numer. Anal. 25, 1988, doi 10.1137/0725066); its relevance here was not checked.

A side result worth a slide: from x0 = 0 the k-th Jacobi iterate is sum over m < k of Q^m b, the game
played forward k rounds. For b = 1 it is E[min(T, k)], T = rounds to the first bust; for
b = `rhs_out_first(S, 0)` it is P(player 1 is out first within k rounds).

## What to build (the tests import exactly these names)

`gr/stationary.py`
- `jacobi(A, b, rtol=1e-10, maxiter=None, x0=None) -> (x, info)`
- `gauss_seidel(A, b, rtol=1e-10, maxiter=None, x0=None) -> (x, info)`, the same as `sor` with omega = 1.
- `sor(A, b, omega, rtol=1e-10, maxiter=None, x0=None) -> (x, info)`. Raises `ValueError` unless
  0 < omega < 2 (outside that interval SOR cannot converge, since rho(SOR(omega)) >= |omega - 1|).
- Rules shared by all three:
  - A is the CSR matrix from `build_A`; b, x0 and x are float arrays of length n. Never modify b or x0.
  - x0 = None means the zero vector.
  - Jacobi updates every unknown from the old iterate: x_i <- (b_i - sum_{j != i} a_ij x_j) / a_ii.
    Gauss-Seidel and SOR sweep forward in StateSpace index order, i = 0, 1, ..., n - 1, always using
    the newest values: x_i <- (1 - omega) x_i + omega (b_i - sum_{j != i} a_ij x_j) / a_ii.
    The order matters: the 3/4 law is a statement about this lexicographic order.
  - Stopping rule: compute the relative residual ||b - A x_k||_2 / ||b||_2 for k = 0, 1, 2, ... and stop
    at the first k where it is <= rtol, or when k = maxiter. The check happens before every sweep,
    including the first, so an x0 that already meets rtol returns after 0 sweeps, and rtol = 0 with
    maxiter = k returns the k-th iterate.
  - maxiter = None means no cap that matters here (use 10**7).
  - info is a dict with at least `iterations` (int: the number of sweeps k), `converged` (bool) and
    `residual_norms` (float array of length iterations + 1: the relative residuals of x_0, ..., x_k, so
    residual_norms[0] = 1 when x0 = 0).
  - The sweeps and the residual run in numba `@njit` kernels over the CSR arrays (indptr, indices,
    data). Plain Python loops are far too slow for N = 160 to 640. Computing the residual every sweep
    doubles the cost; that is fine.
- `young_omega(rho_j)`: 2 / (1 + sqrt(1 - rho_j^2)).
- `iteration_matrix(A, method, omega=None) -> np.ndarray`: the dense iteration matrix for method
  "jacobi" (I - D^-1 A), "gauss_seidel" (omega = 1) or "sor":
  M = (D + omega L)^-1 ((1 - omega) D - omega U), with A = D + L + U split into its diagonal, strictly
  lower and strictly upper parts in StateSpace order. One sweep maps x to M x + c. Small n only (N <= 100).
- `spectral_radius(M) -> float`: the largest |eigenvalue| of a dense matrix (`np.linalg.eigvals`).

## Experiments

All three scripts take `--quick` and write through `gr.runlog.save_results`. Fixed for the whole chunk:
rtol = 1e-10; rho_J from the formula; omega* = `young_omega(rho_J)`; and three right-hand sides per N,
`ones` = `rhs_rounds(S)` (solution t, the expected rounds), `out_first` = `rhs_out_first(S, 0)`
(solution P(player 1 is out first)) and `random` = `np.random.default_rng(221).standard_normal(S.n)`
(a fresh generator for every N). This chunk measures iteration counts and rates, not speed: `seconds`
is one run and is not a benchmark (chunk 11 does the median-of-5 timings).

1. `experiments/e05_iterations.py` writes `results/e05_iterations.csv`, one row per (N, method, b_kind):
   jacobi and gauss_seidel for N in {10, 20, 40, 80, 160}, sor at omega* for
   N in {10, 20, 40, 80, 160, 320, 640} (`--quick`: N in {10, 20, 40} for all three). Columns:
   `N, n, method, omega, b_kind, iterations, converged, final_residual, predicted_iterations,
   young_predicted_iterations, rate_measured, exponent_ratio, rho_jacobi, kappa2, forward_error, seconds`.
   - `predicted_iterations` = ln(1/rtol) / (-ln rho) with rho = rho_J (jacobi), rho_J^2 (gauss_seidel)
     or (omega* - 1)^(3/4) (sor).
   - `young_predicted_iterations` = ln(1/rtol) / (-ln(omega* - 1)) for sor, NaN otherwise.
   - `rate_measured` = (r_k / r_h)^(1/(k - h)) with r = residual_norms, k = iterations, h = k // 2: the
     average contraction per sweep over the second half of the run.
   - `exponent_ratio` = ln(rate_measured) / ln(omega* - 1) for sor (the 3/4 law says 0.75, Young says 1),
     NaN otherwise.
   - `forward_error` = ||x - x_direct||_2 / ||x_direct||_2 with x_direct = `gr.matrix.solve(A, b)`;
     `kappa2` = `gr.spectrum.kappa2(N)`.
2. `experiments/e05_omega_sweep.py` writes `results/e05_omega_sweep.csv` for N in {20, 40, 80}
   (`--quick`: 20), one row per omega on two grids: `coarse`, omega = 1.00 + 0.02 j for j = 0, ..., 49
   (1.00 to 1.98), and `fine`, omega = omega* + 0.0025 j for j = -20, ..., 20 (offset 0 included exactly).
   Columns: `N, n, grid, omega, offset, omega_star, iterations_ones, iterations_random, rho_dense, seconds`,
   with offset = omega - omega* and rho_dense = `spectral_radius(iteration_matrix(A, "sor", omega))`
   for N <= 40 (NaN at N = 80).
3. `experiments/e05_sor_spectra.py` writes `results/e05_sor_spectra.csv`, one row per
   N in {6, 8, 10, 12, 16, 20, 24, 30, 40, 50, 60, 80, 100} (`--quick`: N <= 30). Columns:
   `N, n, omega_star, rho_jacobi_formula, rho_jacobi_dense, rho_gs_dense, gs_gap, gs_gap_times_N4,
   rho_sor_dense, law_value, young_value, law_relerr, sor_over_young, seconds_dense`,
   with gs_gap = rho_gs_dense - rho_jacobi_dense^2, law_value = (omega* - 1)^(3/4),
   young_value = omega* - 1, law_relerr = |rho_sor_dense / law_value - 1|, and
   sor_over_young = rho_sor_dense / young_value. Dense cost: about 10 s per eigenvalue problem at
   N = 80 and 50 s at N = 100 (n = 4851, 1.8 GB peak).

Figures:
- `figures/f05_iterations.py`: iterations against N (log-log) for the three methods with b = ones, each
  with its predicted line; for SOR draw both the 3/4-law prediction and Young's prediction (dashed),
  which shows the gap.
- `figures/f05_omega.py`: rho_dense against omega at N = 20 and 40 (both grids) with a vertical line at
  omega*, and iterations_ones against omega on a second panel.

## Acceptance tests

`pytest tests/c00_core tests/c05_stationary` (67 new tests in two files). `test_c05_stationary.py`:
agreement with splu for all three methods and all three right-hand sides, the info dict and stopping
rule, maxiter, an exact x0 needing 0 sweeps, inputs left unmodified, sor with omega = 1 equal to
gauss_seidel, omega outside (0, 2) rejected, Jacobi iterates as the game played forward, the Jacobi
residual contracting by rho_J every sweep, the Jacobi iteration bound and reference counts,
Gauss-Seidel at half the Jacobi sweeps, SOR counts following the 3/4 law, and the SOR residual rate.
`test_c05_sor_law.py`: spectral_radius, iteration matrices against single sweeps, rho_J, the
Gauss-Seidel gap, young_omega, the 3/4 law (including the golden-ratio case N = 6) and omega* as the
minimizer of rho.

## Expected results (the check script tests these against the CSVs)

| Check | Expected | Tolerance | Kind |
|---|---|---|---|
| e05_iterations: converged | True in every row | | FAIL |
| forward_error | at most kappa2 x rtol (a theorem; measured 1e-5 to 0.6 of that bound) | | FAIL |
| jacobi: iterations | at most predicted_iterations + 1 for every N and b (a theorem: Q is symmetric, so the residual shrinks by at least rho_J per sweep) | | FAIL |
| jacobi, b = ones: iterations | between 0.98 x predicted_iterations and predicted_iterations + 1 (measured 0.990 to 0.9996 of predicted) | | FAIL |
| b = ones, jacobi at N = 10, 20, 40, 80, 160 | 169, 689, 2769, 11081, 44322 iterations | 1% or 1 sweep, whichever is larger | FAIL |
| b = ones, gauss_seidel at N = 10, 20, 40, 80, 160 | 86, 346, 1386, 5542, 22163 iterations | 1% or 1 sweep, whichever is larger | FAIL |
| b = ones, sor at N = 10, 20, 40, 80, 160, 320, 640 | 31, 64, 129, 258, 515, 1030, 2062 iterations | 1% or 1 sweep, whichever is larger | FAIL |
| gauss_seidel iterations / jacobi iterations (same N and b) | 0.45 to 0.55 (measured 0.497 to 0.529) | | FAIL |
| jacobi: rate_measured / rho_jacobi | 1 | 1e-6 (measured within 2e-8) | FAIL |
| gauss_seidel at N = 10, 20, 40, 80: rate_measured / rho_gs_dense (from e05_sor_spectra) | 1 | 1e-6 (measured within 6e-8) | FAIL |
| sor, b = ones: iterations / predicted_iterations | 1.0 to 1.15 (measured 1.075 to 1.081) | | FAIL |
| sor, b = ones: iterations / young_predicted_iterations | at least 1.3 (measured 1.434 to 1.441) | | FAIL |
| sor, b = ones: exponent_ratio | 0.75 | 0.01 (measured 0.7485 to 0.7502) | FAIL |
| sor, b = random: exponent_ratio | 0.74 to 0.82 (measured 0.761 to 0.790) | | WARN |
| sor, b = ones, N >= 20: iterations / N | 3.0 to 3.4 (measured 3.20 to 3.23) | | WARN |
| e05_omega_sweep, N = 20 and 40: argmin of rho_dense on the fine grid | offset 0 (omega* itself) | exact | FAIL |
| rho_dense at offset 0 | 0.678068809 (N = 20), 0.824609363 (N = 40) | 1e-9 relative | FAIL |
| rows with omega = 1.00 | iterations equal the gauss_seidel counts in e05_iterations (same N and b) | 1 sweep | FAIL |
| fine grid: best iterations_ones | at offset 0 to +0.025, with 10% to 20% fewer sweeps than at omega* (measured +0.0175 and 14% at N = 20, +0.0125 and 16% at N = 40, +0.0075 and 17% at N = 80) | | WARN |
| fine grid: best iterations_random | offset within 0.01 of 0, under 5% fewer sweeps (measured +0.005 and 2%, 0 and 0%, -0.005 and 3%) | | WARN |
| e05_sor_spectra: law_relerr | 0, every N | 1e-10 (measured at most 2.3e-14) | FAIL |
| rho_sor_dense at N = 6 | sqrt(5) - 2 = 0.2360679775 | 1e-12 | FAIL |
| rho_sor_dense at N = 12, 20, 30, 40, 100 | 0.517356404, 0.678068809, 0.772896324, 0.824609363, 0.925906019 | 1e-9 relative | FAIL |
| sor_over_young | above 1 for every N (1.618 at N = 6 down to 1.026 at N = 100) | | FAIL |
| abs(rho_jacobi_dense - rho_jacobi_formula) | 0 | 1e-12 | FAIL |
| gs_gap | positive for every N | | FAIL |
| gs_gap_times_N4 | 10 to 20 and increasing in N (measured 10.13 at N = 6 up to 19.20 at N = 100) | | FAIL |
| seconds_dense at N = 100 | under 5 min (2.4 min on the 2-core cloud machine) | | WARN |

Why b = ones is the clean test of the 3/4 law: it lines up with the slowest mode, so the run reaches
the asymptotic rate long before rtol. For `random` the slowest mode starts with weight about 1/sqrt(n),
so the second half of the run still mixes in faster modes (exponent ratio 0.76 to 0.79). For
`out_first` the effect is stronger and grows with N: the exponent ratio climbs from 0.75 at N = 10 to
0.97 at N = 640, and the SOR count drops below Young's prediction for N >= 320. That is the run
stopping before the slowest mode takes over, not evidence for Young's law. The check script prints
these out_first values without a range.

Why the iteration count sits 8% above the 3/4-law prediction even for b = ones: the SOR iteration
matrix is not symmetric, so the residual follows C rho^k with a constant C above 1. Measured C is
about 5.6 at N = 20, 80 and 320, and ln(5.6) / ln(1e10) = 0.075. The rate itself (exponent_ratio)
matches 0.75 to three digits.

## Red flags (bring these to the Project chat)

- SOR counts near young_predicted_iterations for b = ones, or exponent_ratio near 1: the sweep order is
  not StateSpace order, omega* came from the wrong rho_J, or A is not the triangular stencil.
- A forward_error above kappa2 x rtol, or a Jacobi count above predicted + 1: residual_norms is not the
  true residual.
- Gauss-Seidel far from half the Jacobi sweeps: the "Gauss-Seidel" sweep is reading the old iterate
  (that is Jacobi).
- law_relerr well above 1e-12: `iteration_matrix` uses a different splitting or order than the sweeps
  (the single-sweep test should have caught it).
- The rho_dense minimum away from offset 0: young_omega or rho_J is wrong.
- SOR diverging for some 0 < omega < 2: impossible for a symmetric positive definite A
  (Ostrowski-Reich), so it is a bug.
- Jacobi at N = 160 taking more than a few minutes: the sweeps are not compiled with numba.

## Done when

- [ ] `pytest tests/c00_core tests/c05_stationary` passes.
- [ ] `results/e05_iterations.csv`, `results/e05_omega_sweep.csv`, `results/e05_sor_spectra.csv` and both
      figures exist.
- [ ] `python checks/check_c05.py` prints every row PASS; report saved to `results/c05_report.md`.
- [ ] `notes/decisions.md` has a chunk 5 entry; committed as "chunk 5: stationary methods and the SOR 3/4 law".

## Paste back into the Project chat

`results/c05_report.md`.
