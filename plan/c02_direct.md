# Chunk 2: Direct solvers, fill-in and orderings

- **Depends on:** chunk 1 (uses `gr.runlog` and `gr.spectrum.kappa_inf`)
- **Learn first:** Theory Guide §2 (Gaussian elimination and Cholesky) and §3 (sparse direct methods)
- **Time:** build 45-60 min · compute 10-20 min (full), under 1 min (`--quick`) · your review about 1.5 h ·
  plug in: yes for the full run · peak memory about 3 GB (SuperLU with COLAMD at N = 1200)
- **Read this yourself:** `gr/direct.py`, especially the band storage and why `splu`'s fill count is
  exactly twice the Cholesky count

## Goal

Measure what the ordering does to a direct solver: fill (memory), flops (time) and accuracy. The
story you should be able to tell after this chunk:

1. With the natural (lexicographic) order the factor fills its whole envelope:
   nnz(L) = n + (N-3) + (N-1)(N-2)(N-3)/3, which is about (2/3) of the band and grows like n^{3/2}.
   Flops grow like n^2.
2. Fill-reducing orders (minimum degree, nested dissection) cut fill to n log n (George 1973; the fitted exponent
   1.1 is a local slope) and flops to n^{3/2}.
3. Every method is backward stable (backward error a few u), and the forward error grows like
   kappa_inf * u, 0.07 to 0.33 kappa_inf u here. Of this, (3/16 - 27/(16 N^2)) kappa_inf u is not solver error:
   it is the rounding of 1/6 in the stored matrix, identical for every solver, because A^{-1} t = t (1 + e2)/4
   (chunk 4b). Normwise accuracy is therefore fine; chunk 4 asks
   whether the tiny entries are accurate.

## What to build (the tests import exactly these names)

`gr/direct.py`

- `ORDERINGS: dict[str, list[str]]`, exactly:
  `{"dense_cholesky": ["natural"], "banded_cholesky": ["natural"],
  "splu": ["NATURAL", "COLAMD", "MMD_AT_PLUS_A", "MMD_ATA"], "cholmod": ["natural", "amd", "metis", "nesdis"]}`
  (adding more CHOLMOD orders is allowed; removing any is not).
- `MAX_DENSE_N = 6000`.
- `bandwidth(A) -> int`: max |i - j| over the nonzeros of A (equals N - 2).
- `class Factor` with attributes `method`, `ordering`, `nnz` (int), `setup_time` (float seconds) and methods
  - `solve(b)`: accepts shape (n,) or (n, k) and returns the same shape;
  - `column_counts() -> np.ndarray`: length n, entry j = stored entries in column j of L, diagonal included
    (for `splu`, the columns of SuperLU's L).
- `factorize(A, method, ordering) -> Factor`. Raises `ValueError` for an unknown method or an ordering not in
  `ORDERINGS[method]`. `setup_time` is wall time (`time.perf_counter`) for everything in the call: conversions,
  ordering, symbolic and numeric factorization.
  - `dense_cholesky`: refuse with `ValueError` if n > MAX_DENSE_N before allocating anything; then
    `scipy.linalg.cho_factor(A.toarray(), lower=True)`. nnz = n(n+1)/2 (the whole triangle is stored).
  - `banded_cholesky`: put the band (p = bandwidth) into (p+1) x n storage and call
    `scipy.linalg.cholesky_banded`; solve with `cho_solve_banded`. nnz = n(p+1) - p(p+1)/2 (do not count the
    p(p+1)/2 unused corner slots of the storage array).
  - `splu`: `scipy.sparse.linalg.splu(A.tocsc(), permc_spec=ordering)`. nnz = L.nnz + U.nnz. A is diagonally
    dominant, so SuperLU never pivots off the diagonal and this is exactly 2 x the Cholesky fill for the same
    column order.
  - `cholmod`: `sksparse.cholmod.cho_factor(A.tocsc(), order=ordering)` (scikit-sparse 0.5 API). nnz = the
    factor's `nnz`. Import `sksparse` inside this branch so the rest of the module works without it.
- `direct_solve(A, b, method, ordering) -> (x, info)`, info = `{"setup_time", "solve_time", "nnz_factor"}`.

## Experiment

`experiments/e02_direct.py` writes `results/e02_direct.csv`. Sizes N in {25, 50, 100, 200, 400, 800, 1200, 1600}
(`--quick`: 25, 50, 100). Size caps (skip the row above them):

| method, ordering | largest N |
|---|---|
| dense_cholesky | 100 (n <= 6000) |
| banded_cholesky, splu NATURAL, cholmod natural | 400 |
| splu COLAMD, splu MMD_ATA | 1200 |
| splu MMD_AT_PLUS_A, cholmod amd, metis, nesdis | 1600 |

One row per (N, method, ordering), columns:
`N, n, method, ordering, nnz_A, nnz_factor, nnz_chol_equiv, fill_ratio, flops, setup_time, solve_time,
forward_error, kappa_inf, err_over_kappa_u, backward_error, memory_MB_est`

- `nnz_chol_equiv` = nnz_factor / 2 for splu, nnz_factor otherwise; `fill_ratio` = nnz_chol_equiv / nnz(tril(A)).
- `flops` = sum over j of column_counts()[j]^2, only for N <= 800 (NaN above; it needs a copy of L).
- Timings: median of 3 factorizations and median of 3 solves of A x = 1.
- `forward_error` = max|x - t| / max t with t = 3 x1 x2 x3 / N (exact). `kappa_inf` from `gr.spectrum`.
  `err_over_kappa_u` = forward_error / (kappa_inf * 2^-53).
- `backward_error` = ||1 - A x||_inf / (||A||_inf ||x||_inf + 1) (normwise, Rigal-Gaches).
- `memory_MB_est` = 8 * nnz_factor / 1e6.

Optional `--big`: N = 2400 and 3200, cholmod nesdis only, one repeat, to `results/e02_direct_big.csv`. Needs about
6 GB free RAM and a few minutes; skip it on an 8 GB Mac.

Figures (`figures/f02_direct.py`, from the CSV only): (a) nnz_chol_equiv vs n, log-log, one line per
(method, ordering), with guide lines proportional to n^{3/2} and n log n; (b) flops vs n with n^2 and n^{3/2}
guides; (c) setup_time vs n.

## Acceptance tests

`pytest tests/c00_core tests/c01_spectrum tests/c02_direct` (75 new tests, about 3 s). They check the interface, the
bandwidth, the exact fill formulas (dense, band, envelope), that the dense factor has no cancellation, ordering
rankings and growth exponents at N = 100 and 200, forward error on A t = 1, agreement with `gr.matrix.solve` on
probability right-hand sides, one factorization reused for an n x 6 block of right-hand sides (the six order
probabilities must sum to 1), and the column counts. CHOLMOD tests skip if scikit-sparse is missing; if it
will not install, say so in the report rather than working around it.

## Expected results (the check script tests these against the CSV)

Measured on the reference implementation (Linux container); orderings are deterministic, so fill counts
should match on your Mac to within a few percent, and times will differ.

| Check | Expected | Tolerance | Kind |
|---|---|---|---|
| nnz_factor, banded | n(p+1) - p(p+1)/2, p = N - 2 | exact | FAIL |
| nnz_chol_equiv, splu NATURAL and cholmod natural | n + (N-3) + (N-1)(N-2)(N-3)/3 (N=400: 21,094,596) | exact | FAIL |
| natural / banded nnz at N = 400 | 0.6675 (tends to 2/3) | 0.005 | FAIL |
| fill exponent (slope of log nnz_chol_equiv vs log n), natural orders, N = 100-400 | 1.50 | 0.03 | FAIL |
| fill exponent, metis, nesdis, MMD_AT_PLUS_A, N = 400-1600 | 1.10-1.14 | in [1.03, 1.22] | WARN |
| fill exponent, amd, COLAMD, MMD_ATA, N = 400-1200 or 1600 | 1.16-1.23 | in [1.08, 1.30] | WARN |
| flops exponent, natural orders, N = 100-400 | 2.00 | 0.05 | FAIL |
| flops exponent, metis and nesdis, N = 100-800 | 1.53 | in [1.40, 1.65] | WARN |
| flops exponent, amd, N = 100-800 | 1.68 | in [1.55, 1.80] | WARN |
| nnz at N = 1200: amd / metis | 1.40 | in [1.15, 1.65] | WARN |
| nnz at N = 1200: (MMD_AT_PLUS_A / 2) / metis | 0.98 | in [0.85, 1.15] | WARN |
| nnz at N = 1200: (COLAMD / 2) / metis | 2.41 | in [1.8, 3.0] | WARN |
| err_over_kappa_u, every row with N >= 100 | 0.07-0.33 (data term 0.1875 plus a solver part of either sign) | in [0.02, 1] WARN; above 10 FAIL | WARN/FAIL |
| backward_error, every row | 2-15 u (2e-16 to 2e-15) | above 50 u WARN; above 1e-13 FAIL | WARN/FAIL |
| solve_time / setup_time, splu and cholmod, N >= 400 | 0.01-0.04 | below 0.1 | WARN |
| setup_time, cholmod amd, N = 1200 | about 11 s here | 2-30 s | WARN |
| setup_time exponent, cholmod nesdis, N = 400-1600 | about 1.24 here | in [1.0, 1.7] | WARN |

Reference fill counts (nnz_chol_equiv) to compare by eye:

| N | n | natural | COLAMD | MMD_ATA | MMD_AT_PLUS_A | amd | metis | nesdis |
|---|---|---|---|---|---|---|---|---|
| 100 | 4,851 | 318,646 | 170,961 | 160,756 | 113,305 | 120,237 | 120,831 | 117,398 |
| 200 | 19,701 | 2,607,296 | 1,019,480 | 1,004,611 | 597,948 | 683,804 | 622,487 | 620,225 |
| 400 | 79,401 | 21,094,596 | 5,832,195 | 5,609,897 | 2,975,432 | 3,750,523 | 3,078,404 | 3,060,841 |
| 800 | 318,801 | | 33,047,759 | 29,686,269 | 14,544,930 | 19,401,349 | 14,659,739 | 14,583,368 |
| 1200 | 718,201 | | 87,686,028 | 75,833,671 | 35,575,491 | 50,925,514 | 36,351,321 | 35,936,492 |

Why the time exponent (about 1.24) is below the flops exponent (about 1.5): at these sizes the ordering and
symbolic steps (nearly linear in n) are a large share, and dense kernels run faster on bigger supernodes.

## Red flags (bring these to the Project chat)

- Any exact fill formula off by even one entry: the matrix builder or the nnz definition is wrong.
- splu nnz not exactly twice the Cholesky count for the same order: SuperLU pivoted, which should be impossible
  for this matrix.
- err_over_kappa_u above 1, or forward error growing faster than N^2.
- Backward error growing with N faster than about sqrt(n) u.
- A fill-reducing order that is worse than natural.

## Done when

- [ ] `pytest tests/c00_core tests/c01_spectrum tests/c02_direct` passes.
- [ ] `results/e02_direct.csv` and the three figure panels exist.
- [ ] `python checks/check_c02.py` prints a line per check; report saved to `results/c02_report.md`.
- [ ] `notes/decisions.md` has a chunk 2 entry; committed as "chunk 2: direct solvers".

## Paste back into the Project chat

`results/c02_report.md`, plus the fill and flops figures.
