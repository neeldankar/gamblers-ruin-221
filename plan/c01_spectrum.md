# Chunk 1: Exact spectrum and conditioning

- **Depends on:** chunk 0
- **Learn first:** Theory Guide §1 (conditioning) and §4 (model problems and exact spectra)
- **Time:** build 20-30 min · compute under 2 min · your review about 1 h · plug in: no
- **Read this yourself:** `gr/spectrum.py` (it is short; you must be able to derive every line)

## Goal

Pin down the matrix's spectrum exactly, so every later chunk can compare measured convergence
against a prediction. Also build the results logger every experiment uses.

## What to build (the tests import exactly these names)

`gr/spectrum.py`
- `eigenvalues(N) -> np.ndarray`: all n = (N-1)(N-2)/2 eigenvalues of A, sorted ascending, from
  lambda_kl = 1 - (1/3)[cos(2pi(2k+l)/(3N)) + cos(2pi(k+2l)/(3N)) + cos(2pi(k-l)/(3N))],
  k, l >= 1, k + l <= N - 1.
- `lambda_min(N) = (4/3) sin^2(pi/N)` and `lambda_max(N) = 3/2 - (1 - cos(2pi/N))/3`.
- `kappa2(N) = lambda_max(N) / lambda_min(N)`.
- `kappa_inf(N) = ||A||_inf * max_x t(x)`, with t = 3 x1 x2 x3 / N (because A^{-1} 1 = t and A^{-1} >= 0).
- `perron_vector(S) -> np.ndarray`: v(x) = sum_a sin(2 pi x_a / N), the eigenvector for lambda_min.
- `jacobi_rate(N) = 1 - lambda_min(N)`, the spectral radius of Q.

`gr/runlog.py`
- `metadata() -> dict[str, str]` with keys git_hash, timestamp, platform, machine, python, numpy,
  scipy, omp_num_threads.
- `save_results(rows: list[dict], name: str, outdir="results") -> pathlib.Path`: writes
  `outdir/name.csv`, every row stamped with `metadata()`.

## Experiment

`experiments/e01_conditioning.py` writes `results/e01_conditioning.csv`, one row per
N in {10, 20, 40, 80, 160, 320, 640} (`--quick`: 10, 20, 40), columns:
`N, n, lambda_min_formula, lambda_min_eigsh, lambda_max_formula, kappa2, kappa2_over_N2, kappa_inf,
kappa_inf_over_N2, jacobi_rate, seconds_eigsh`.
`lambda_min_eigsh` comes from `scipy.sparse.linalg.eigsh(A, k=1, sigma=0, which="LM")`, an independent
measurement. Skip eigsh above N = 320 (write NaN).

Figure: `figures/f01_conditioning.py` plots kappa2/N^2 against N with the limit 9/(8 pi^2) as a dashed
line (log x axis).

## Acceptance tests

`pytest tests/c00_core tests/c01_spectrum` (40 new tests). They check the eigenvalue formula against
dense eigenvalues for N = 5..30, the closed forms for lambda_min and lambda_max, that every eigenvalue
lies in (0, 3/2), the Perron vector, kappa2 against reference values, kappa2/N^2 increasing to
9/(8 pi^2), kappa_inf against dense inverses (and = 2N^2/9 when 3 divides N), the Jacobi rate against
dense eigenvalues of Q, shift-invert Lanczos at N = 80, and the logger.

## Expected results (the check script tests these against the CSV)

| Check | Expected | Tolerance | Kind |
|---|---|---|---|
| lambda_min_eigsh / lambda_min_formula | 1 | 1e-9 relative, every N with eigsh | FAIL |
| kappa2 at N = 10, 20, 40, 80, 160, 320 | 11.28, 45.47, 182.25, 729.39, 2917.9, 11672.1 | 1e-3 relative | FAIL |
| kappa2_over_N2 | increasing in N, below 9/(8 pi^2) = 0.1139863 | strict | FAIL |
| kappa2_over_N2 at N = 640 | 0.1139863 | 1e-5 relative | FAIL |
| kappa_inf_over_N2 when 3 divides N | 2/9 = 0.2222 | 1e-9 relative | FAIL |
| kappa_inf / kappa2 | between 1.9 and 2.0 for N >= 40 | | WARN |
| jacobi_rate | 1 - lambda_min_formula | 1e-15 | FAIL |
| seconds_eigsh at N = 320 | under 10 s | | WARN |

Why the kappa_inf / kappa2 ratio sits near 1.95: kappa_inf -> (2/9) N^2 and kappa2 -> (9/(8 pi^2)) N^2,
and (2/9)/(9/(8pi^2)) = 16 pi^2/81 = 1.949.

## Red flags (bring these to the Project chat)

- Any eigenvalue at or below 0, or at or above 3/2.
- eigsh disagreeing with the formula: the matrix builder or the formula has an indexing bug.
- kappa2/N^2 decreasing with N.

## Done when

- [ ] `pytest tests/c00_core tests/c01_spectrum` passes.
- [ ] `results/e01_conditioning.csv` and the figure exist.
- [ ] `python checks/check_c01.py` prints every row PASS; report saved to `results/c01_report.md`.
- [ ] `notes/decisions.md` has a chunk 1 entry; committed as "chunk 1: exact spectrum".

## Paste back into the Project chat

`results/c01_report.md`.
