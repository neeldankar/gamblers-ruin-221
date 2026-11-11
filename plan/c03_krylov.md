# Chunk 3: Conjugate gradients and preconditioners

- **Depends on:** chunk 1 (spectrum, runlog); chunk 2 for the direct reference solution and timing
- **Learn first:** Theory Guide §6 (Krylov methods) and the multigrid half of §7
- **Time:** build 60-90 min · compute 10-20 min (full), under 1 min (`--quick`) · your review about 1.5 h ·
  plug in: recommended · memory under 1 GB
- **Read this yourself:** `cg` and `ic0` in `gr/krylov.py` (about 30 lines each)

## Goal

Measure CG against its theory on a matrix whose spectrum you know exactly, and see what each
preconditioner buys. The story after this chunk:

1. Unpreconditioned CG needs about 1.9 N iterations for a random right-hand side at rtol 1e-10, because
   sqrt(kappa) = 0.34 N. The Chebyshev bound is correct but about 2.3 times too pessimistic.
2. For b = 1 (expected rounds), CG stops after exactly floor((N-1)/2) iterations, because that b has weight
   on only floor((N-1)/2) distinct eigenvalues (proved: notes/proofs.md). In floating point this stretches by about 7% for large N.
   That is why no benchmark may use b = 1 alone.
3. Jacobi preconditioning does nothing here (the diagonal of A is exactly 1).
4. IC(0) cuts kappa by about 12 but keeps kappa ~ N^2, so iterations still grow like N.
   MIC(0) makes kappa grow about linearly (Gustafsson 1978): kappa / N = 0.136, 0.140, 0.150, 0.160, 0.171 at
   N = 20, 40, 80, 160, 320, still creeping up, so iterations grow like N^{0.55}; its smallest preconditioned
   eigenvalue is exactly 1. Smoothed aggregation AMG keeps iterations nearly flat (7 to 21 for N = 20 to 1280).
5. Iterations are not time: an IC(0) step costs 2 to 4 plain steps, an AMG V-cycle about 10.

## What to build (the tests import exactly these names)

`gr/krylov.py`

- `PRECONDITIONERS = ["none", "jacobi", "ic0", "mic0", "amg"]`.
- `cg(A, b, rtol=1e-10, maxiter=None, M=None, x0=None, callback=None) -> (x, info)`: your own preconditioned
  CG (do not wrap scipy's). `M` is a callable r -> z approximating A^{-1} r, or None. `maxiter` defaults to
  10 n. Stop at the first k with ||r_k||_2 <= rtol ||b||_2, where r_k is the residual from the CG recurrence,
  the unpreconditioned residual even when M is given (so every method stops on the same test).
  `callback(x_k)` is called after every iteration. `info = {"iterations": k, "residuals": np.ndarray of
  ||r_j||_2 / ||b||_2 for j = 0..k, "converged": bool}`.
- `cg_iteration_bound(kappa, rtol) -> int`: ceil( (sqrt(kappa)/2) ln(2 sqrt(kappa) / rtol) ). (From
  ||e_k||_A <= 2 ((sqrt(kappa)-1)/(sqrt(kappa)+1))^k ||e_0||_A and ||r|| <= sqrt(kappa) times that in the
  right norms; derive it.)
- `ic0(A, modified=False) -> scipy.sparse.csr_matrix L`: incomplete Cholesky with zero fill, lower
  triangular, same pattern as tril(A), positive diagonal. With `modified=False`, (L L^T)_ij = A_ij on the
  whole pattern of A. With `modified=True` (MIC(0)), every fill entry that IC(0) would drop is subtracted
  from the diagonal of its row instead, so off-diagonal pattern entries stay exact and (L L^T) 1 = A 1.
  Raise `ValueError` if a pivot is not positive. Write the factorization loop with numba (`@njit`); the
  row-by-row (IKJ) form of incomplete LU on the CSR pattern of A is the easiest, then L = L_unit * diag(sqrt(d)).
- `ic_preconditioner(L) -> callable`: r -> (L L^T)^{-1} r by one forward and one backward substitution, both
  numba loops over CSR. Do not use `scipy.sparse.linalg.spsolve_triangular`: it is about 10 times slower here
  and would make IC look bad for the wrong reason.
- `make_preconditioner(A, kind) -> (M, setup_time)`: `None` for "none"; r -> r / diag(A) for "jacobi";
  `ic_preconditioner(ic0(A, modified=...))` for "ic0" and "mic0"; for "amg", `pyamg.smoothed_aggregation_solver(A)`
  with default settings and `ml.aspreconditioner(cycle="V")` (symmetric, so valid for CG). `ValueError` for
  anything else. `setup_time` is wall time in seconds.

Warm up the numba functions on a tiny problem (N = 10) before timing anything, so compile time is not counted.

## Experiments

`experiments/e03_krylov.py` writes `results/e03_krylov.csv`. N in {20, 40, 80, 160, 320, 640, 1280}
(`--quick`: 20, 40, 80). Right-hand sides: `ones` (rhs_rounds), `random` (standard normal from
`np.random.default_rng(221)`), `out_first` (rhs_out_first(S, 2), player 3 out first) and `order321`
(rhs_order(S, 2, 1, 0)). Kinds: all of PRECONDITIONERS, but `jacobi` only up to N = 320 (it is identical to
none). rtol = 1e-10. Also one `direct` row per (N, rhs): CHOLMOD nesdis from `gr.direct` (SuperLU MMD_AT_PLUS_A
if CHOLMOD is missing), setup and solve timed the same way. Columns:
`N, n, kind, rhs, iterations, bound, iterations_over_N, setup_time, solve_time, time_per_iteration,
final_relres, forward_error, kappa2`
with forward_error = max|x - x_direct| / max|x_direct| and bound = cg_iteration_bound(kappa2(N), 1e-10)
(fill bound only for kind none). Timings: median of 3 for N <= 640, a single run at N = 1280.

`experiments/e03_convergence.py` writes `results/e03_convergence.csv`: N = 320, rhs `random` and `order321`,
kinds none, ic0, mic0, amg, one row per iteration k with `relres`, `err_A` (||x_k - x*||_A / ||x*||_A) and
`err_inf` (max|x_k - x*| / max|x*|), plus `chebyshev` = 2((sqrt(kappa)-1)/(sqrt(kappa)+1))^k for kind none.

Figures (from the CSVs only): `figures/f03_iterations.py` (iterations vs N, log-log, random b, one line per
kind, guide slopes 1 and 1/2, plus b = ones against floor((N-1)/2)); `figures/f03_convergence.py` (relres,
err_A and the Chebyshev line vs k at N = 320); `figures/f03_time.py` (time to solution vs N for each kind and
direct, one right-hand side and six right-hand sides, where direct reuses its factor).

## Acceptance tests

`pytest tests/c00_core tests/c01_spectrum tests/c02_direct tests/c03_krylov` (44 new tests, about 2 s).
They check CG against a direct solve and against scipy's CG (same iterates), the residual history and
stopping rule, x0 and maxiter, monotone A-norm error, the bound formula and that iterations stay below it,
the floor((N-1)/2) eigenvalue fact and exact finite termination for N up to 41, Jacobi being the identity,
the IC(0) and MIC(0) defining identities, lambda_min = 1 for MIC(0), preconditioned condition numbers,
breakdown on Kershaw's matrix, every preconditioner's accuracy, and iteration ranking and growth.

## Expected results (the check script tests these against the CSV)

Reference iteration counts, random b, rtol 1e-10 (deterministic; counts may move by 1 or 2 across machines
because dot products round differently, AMG may move more across pyamg versions):

| N | 20 | 40 | 80 | 160 | 320 | 640 | 1280 |
|---|---|---|---|---|---|---|---|
| none | 39 | 77 | 154 | 306 | 603 | 1198 | 2368 |
| ic0 | 15 | 27 | 49 | 95 | 183 | 363 | 714 |
| mic0 | 15 | 22 | 33 | 50 | 73 | 107 | 157 |
| amg | 7 | 8 | 9 | 11 | 14 | 16 | 21 |
| none, b = ones | 9 | 19 | 40 | 85 | 172 | 344 | 686 |
| floor((N-1)/2) | 9 | 19 | 39 | 79 | 159 | 319 | 639 |

| Check | Expected | Tolerance | Kind |
|---|---|---|---|
| none, ic0, mic0 iteration counts vs the table (random b) | as above | within 3% WARN; beyond 10% FAIL | WARN/FAIL |
| amg iteration counts | as above | factor 0.7 to 1.4 | WARN |
| jacobi iterations = none iterations, every (N, rhs) | equal | exact | FAIL |
| none, random b: iterations / N for N >= 80 | 1.85-1.93 | in [1.75, 2.05] | FAIL |
| none: iterations / bound | 0.39-0.45 | below 1 | FAIL |
| b = ones: iterations / floor((N-1)/2) | 1.00 (N <= 41), 1.03-1.08 above | in [1.0, 1.15] | WARN |
| fitted exponent of iterations vs N, N = 160-1280, random b | none 0.98, ic0 0.97, mic0 0.55, amg 0.2-0.4 | none, ic0 in [0.9, 1.05]; mic0 in [0.45, 0.65]; amg below 0.5 | WARN |
| ranking at every N >= 80, every rhs except ones | amg < mic0 < ic0 < none | strict | FAIL |
| b = ones: ic0 vs none | ic0 needs more iterations at N <= 80 (47 vs 40 at N = 80), about equal at N = 160 (84 vs 85): IC(0) in lexicographic order breaks the symmetry that gives plain CG its floor((N-1)/2) termination | | WARN |
| forward_error at rtol 1e-10 | 1e-11 to 3e-9 up to N = 640, about 5e-9 at N = 1280 | below kappa2(N) * 1e-10 FAIL; above 1e-8 WARN | WARN/FAIL |
| time_per_iteration ratio ic0 / none, N >= 640 | 2-4 here | in [1.5, 5] (higher means slow triangular solves) | WARN |
| amg time_per_iteration / none, N = 1280 | about 10 | in [4, 25] | WARN |
| one rhs at N = 1280, total time (setup + solve): amg and mic0 vs none | 5-7 times faster | at least 3 times | WARN |
| six rhs at N = 1280: direct (one factor, six solves) vs amg (one setup, six solves) | direct faster | | WARN |

Times measured here at N = 1280, random b: none 39 s, ic0 26 s, mic0 5.7 s, amg 3.6 s plus 2.1 s setup,
CHOLMOD nesdis about 10 s setup and 0.1 s per solve.

## Red flags (bring these to the Project chat)

- IC(0) not reducing iterations, or MIC(0) growing like N instead of N^{1/2}: the factorization is wrong.
- Any breakdown (negative pivot) in IC(0) or MIC(0) on our matrix: it is an M-matrix, so this should not happen.
- b = ones not terminating near floor((N-1)/2): the right-hand side or the matrix is off.
- Forward errors above about 1e-8 at rtol 1e-10.
- AMG above about 30 iterations.

## Done when

- [ ] `pytest tests/c00_core tests/c01_spectrum tests/c02_direct tests/c03_krylov` passes.
- [ ] Both CSVs and the three figures exist.
- [ ] `python checks/check_c03.py` prints a line per check; report saved to `results/c03_report.md`.
- [ ] `notes/decisions.md` has a chunk 3 entry; committed as "chunk 3: Krylov methods".

## Paste back into the Project chat

`results/c03_report.md`, plus `f03_iterations` and `f03_convergence`.
