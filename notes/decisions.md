# Decisions log

## 2026-11-03: phase 1, core and tests
- Built gr/states.py (lexicographic live states, lookup array), gr/matrix.py (A = I - Q vectorized
  over the 6 moves; right-hand sides from boundary values), gr/exact.py (independent Fraction code),
  gr/montecarlo.py (full-game simulation).
- Tests (46, all passing): state count; <= 7 nonzeros per row; symmetry; Q row sums = (6 - busts)/6;
  positive definiteness; N = 4 hand example (1/7, 3/7) and its six orders; float vs exact rationals for
  N <= 15 to 1e-12; closed forms t = 3x1x2x3/N and P(win) = xi/N at N = 10, 50, 200 and exactly in
  rationals; six orders sum to 1; relabeling identity vs direct solves; orders ending in k sum to xk/N;
  Diaconis-Ethier values (569/9456, Table 9 at (2,3,5), Table 4 at N = 300); Monte Carlo within 4 SE.
- Order probabilities use boundary value y_k/N on the face y_i = 0 (not an indicator): the order
  depends on the stacks at the moment of the first bust.
- The only solver so far is scipy's splu as a reference. Benchmarked solvers come in phase 2.


## Scaffold: chunks, specs and acceptance tests (Nov 9)
- Split the remaining work into chunks 1-12 (plan/README.md), each with a spec and pre-written acceptance tests.
- Every test was run against an independent reference implementation written outside this repo; the reference
  code is deliberately not included, so the implementation here is a second, independent one. Tests skip until
  their module exists (pytest.importorskip).
- Expected-result tables in each spec come from measurements on the reference (Linux container). Iteration
  counts and fill counts are deterministic; times are machine-dependent and therefore WARN-level only.
- Findings made while validating, now built into the specs: natural-order fill is exactly
  n + (N-3) + (N-1)(N-2)(N-3)/3; CG on b = 1 stops after exactly floor((N-1)/2) steps; MIC(0) has smallest
  preconditioned eigenvalue exactly 1; cond of the tiny entry is 2 E[T | event] ~ 0.388 N^2; CG's tiny-entry error
  is about cond_tiny * rtol; refinement with an accurate residual is correctly rounded; GTH is accurate to ~0.3 N u;
  the structured condition number (off-diagonals, row sums, b) is O(1).
- The tiny-entry constant Gamma(1/3)^9 / (8 pi^4) = 9.1195890 is published (Diaconis and Ethier 2022, Remark 4):
  it is twice their c. It is not one of our findings (corrected in chunk 4b).


## Environment: python-flint from PyPI (Nov 9)
- environment.yml pinned `python-flint=0.9`, but conda-forge only has up to 0.8.0, so `conda env create` could
  not solve. PyPI has 0.9.0 with a cp313 macOS arm64 wheel.
- Decided: drop python-flint from the conda dependencies, add `pip`, and install `python-flint==0.9.0` through a
  pip subsection. Every other pin is unchanged and comes from conda-forge.
- Set up on Apple Silicon with Miniforge (Homebrew cask, conda 26.9.4). Versions: Python 3.13.18, numpy 2.5.4,
  scipy 1.18.1, pyamg 5.3.0, numba 0.68.1, scikit-sparse 0.5.0, python-flint 0.9.0. `pytest -q`: 46 passed, 17 skipped.


## Chunk 1 spec fix: N list (Nov 9)
- The chunk 1 check "kappa_inf_over_N2 = 2/9 when 3 divides N" had no data: none of N = 10, 20, 40, 80, 160,
  320, 640 is divisible by 3, so the check could never run.
- Sanity-checked in the Project chat. Decided: N list becomes {10, 20, 30, 40, 80, 90, 160, 300, 320, 640}
  (`--quick`: 10, 20, 30, 40), eigsh still capped at 320, and a new FAIL row: when 3 does not divide N,
  kappa_inf_over_N2 is below 2/9 and within 1% of it for N >= 40 (max x1 x2 x3 is then just under (N/3)^3;
  at N = 40 the ratio is 2366/2370.4 = 0.998).


## Chunk 1: exact spectrum (Nov 9)
- gr/spectrum.py implements the spec's formulas directly. lambda_max is attained at (k, l) = (1, N - 2)
  (checked by brute force for N = 10, 11, 12, 30, 31); the docstring derives the closed form from that mode.
- kappa_inf computes ||A||_inf from the matrix (max absolute row sum) instead of hard-coding 2: it is 5/3 at
  N = 5, where every live state has a coordinate equal to 1, and 2 for N >= 6. ||A^{-1}||_inf = max t because
  A^{-1} >= 0 and A^{-1} 1 = t = 3 x1 x2 x3 / N.
- jacobi_rate is literally 1 - lambda_min(N), so the 1e-15 check holds exactly.
- gr/runlog.py: git_hash is the short HEAD hash plus "-dirty" when gr/ or experiments/ have uncommitted or
  untracked changes. The chunk 1 CSV therefore says d67e602-dirty: it was produced by the code in the
  "chunk 1: exact spectrum" commit, run before that commit existed. Chunk 11's run_all refuses a dirty tree, so
  the final results will carry a clean hash. CSV floats are written with full repr precision.
- e01: eigsh time is the median of 3 calls with A built (and converted to CSC) outside the timer. Full run:
  eigsh at N = 320 takes 0.53 s; max relative difference from the formula 3.1e-13.
- check_c01.py: all 9 rows PASS. kappa2/N^2 at N = 640 is 2.7e-6 below 9/(8 pi^2), consistent with the
  -pi^2/(9 N^2) relative correction from expanding lambda_max/lambda_min. No red flags.
- The figure uses fixed x ticks at 10, 20, 40, ..., 640 (labels at 80/90 and 300/320 collided otherwise).
- The env has no `tabulate`, so check_c01 formats its markdown data table by hand instead of DataFrame.to_markdown.


## Chunk 2: direct solvers, fill-in and orderings (Nov 9)
- gr/direct.py follows the spec's names and calls. Column counts: dense n - j and banded min(p+1, n-j) by
  formula; splu from a copy of SuperLU's L (`np.diff(L.tocsc().indptr)`); CHOLMOD from the factor's own
  `colcount` (equal to `L.nnz` per column and to `F.nnz` in total, checked at N = 20, 100, 400). CHOLMOD chose
  simplicial factors (`is_super` False) up to N = 400, so its `nnz` has no supernodal padding.
- scikit-sparse 0.5 (CHOLMOD) is installed and used; no CHOLMOD test skipped. tests c00-c02: 161 passed.
- SuperLU never pivoted: `perm_r == perm_c` and `L.nnz == U.nnz` for all four orders at N = 100, and splu
  NATURAL is exactly 2 x cholmod natural at every N. The module docstring gives the argument (column diagonal
  dominance survives elimination).
- Fill counts match the spec's reference table exactly for every order at N = 100-1200 (deterministic orderings,
  same counts on macOS arm64 as on the Linux reference).
- e02: A is built and converted to CSC outside the timer; the previous factor is freed before each of the three
  factorizations so only one big factor lives at a time. Backward error uses ||b||_inf = 1 in the denominator.
  `np.random.default_rng(221)` is created for convention only (this chunk uses b = 1 throughout).
- The gr package is not installed in the env, so experiments run as `PYTHONPATH=. python experiments/e02_direct.py`
  (same as chunk 1). check_c02 and f02 read only the CSV.
- check_c02 conventions: an exponent is the least-squares slope of log y vs log n over every row in the stated N
  range; "natural orders" = splu NATURAL and cholmod natural (the two the envelope formula names); missing rows give
  the check's own kind, never PASS. Added an automatic "red flags" section (splu = 2 x Cholesky, no ordering worse
  than natural, forward-error growth vs N^2, backward-error growth vs sqrt(n), err_over_kappa_u <= 1).
- Results (full run, git 7cd1f96): 16 PASS, 1 WARN, 0 FAIL; no red flags. Exponents: natural fill 1.500, flops
  2.000; metis/nesdis/MMD_AT_PLUS_A fill 1.118/1.116/1.123; amd/COLAMD/MMD_ATA 1.174/1.233/1.184; flops metis/nesdis
  1.529/1.532, amd 1.681. err_over_kappa_u 0.074-0.326 (max: splu NATURAL at N = 400); backward error 1.5-23.7 u.
- The WARN: cholmod amd setup at N = 1200 is 1.95 s against the spec's 2-30 s (reference: about 11 s). This Mac is
  faster than the reference container; amd is the cheapest ordering here (metis/nesdis take 5.4-5.6 s at N = 1200
  because the ordering itself costs more). Timing only; fill and flops are exact. Left as WARN for the Project chat.
- nesdis setup-time exponent is 1.15 over N = 400-1600 (reference about 1.24), inside [1.0, 1.7].
- Figure: one PNG with three panels; color = method family (4 validated hues), marker/line style = ordering. In
  panels (a) and (b) splu NATURAL lies exactly under cholmod natural (identical Cholesky-equivalent counts).
- Optional --big run (16 GB Mac, git 7cd1f96, results/e02_direct_big.csv): cholmod nesdis at N = 2400 has
  nnz 165,657,920, setup 29.3 s; at N = 3200 nnz 310,559,935, setup 65.3 s, solve 0.96 s. err_over_kappa_u 0.127
  at both, backward error 2.7e-15 to 3.2e-15 (12-14 u). Fill exponent from N = 1600 to 3200 is 1.10, still in the
  nested-dissection range. Not used by check_c02 (the spec has no expected rows for it).


## Chunk 3: conjugate gradients and preconditioners (Nov 10)
- gr/krylov.py follows the spec's names. cg is a textbook PCG. It sets r0 = b.copy() when x0 is None, so
  residuals[0] is exactly 1, and it stops on the recurrence residual, unpreconditioned for every M.
  ic0 is IKJ ILU(0) on the sorted CSR pattern of A in a numba loop. With MIC, dropped fill goes to the row's
  diagonal. The kernel returns the first non-positive pivot and Python raises ValueError. Then
  L = L_unit diag(sqrt(d)). AMG is `smoothed_aggregation_solver(A).aspreconditioner(cycle="V").matvec` with defaults.
  tests c00-c03: 205 passed (44 new).
- Numba: `@njit(cache=True)`; the cache lands in gr/__pycache__, which is git-ignored, so git_hash stays clean.
  `krylov.warmup()` (N = 10, ic0 + mic0 + cg) runs before any timer in both experiments.
- Triangular solves, a fix made after the first full run (commit 08efc8a). The first run (git 373ba4c) had
  ic0/none time per iteration at 4.3-5.1, which was a WARN at N = 640 (5.11 > 5). The spec reads that as slow
  triangular solves. Profiling at N = 1280: matvec 4.4 ms, but M(r) took 24.9 ms; the backward sweep
  (14.6 ms) reloaded z[i] on every inner step (numba cannot rule out aliasing), and the per-row divide sits on
  the row-to-row critical path. I kept z[i] in a local and multiplied by a precomputed 1/diag(L): M(r) is now
  16.8 ms and the ratio 3.1-3.7. Results agree with the old solve to 6e-15. Experiments were re-run on the
  new commit; the CSVs come from 08efc8a.
- e03_krylov conventions:
  - Direct rows use CHOLMOD nesdis, timed like everything else (median of 3 setups, median of 3 solves per rhs;
    a single run at N = 1280).
  - forward_error is NaN on direct rows (they are the reference), and their final_relres is the true residual.
  - bound is filled only for kind none.
  - time_per_iteration = solve_time / iterations.
- e03_convergence: x* is the CHOLMOD solution. The errors are computed inside the callback, so no iterates are
  stored. `--quick` uses N = 80 (the spec gives no quick size).
- check_c03 conventions:
  - Reading of the iteration-count tolerance: within 3% PASS, 3-10% WARN, beyond 10% FAIL.
  - "Six rhs" = setup + 6 x solve_time on random b.
  - The time_per_iteration ratio checks use every rhs.
  - Missing rows get the check's own kind.
  - Red flags are automatic. "Forward error much larger than about 1e-9" is flagged above 3e-9, the top of the
    spec's expected band.
  - Extras: err_A <= the Chebyshev bound for plain CG, and the ranking without b = ones.
- Results (git 08efc8a): 14 PASS, 0 WARN, 1 FAIL.
  - Iteration counts match the reference table exactly for none, ic0 and amg at every N. mic0 matches except
    N = 1280 (158 vs 157); the old solve gave 157, so this is rounding.
  - Exponents: none 0.985, ic0 0.972, mic0 0.553, amg 0.299. iterations/N for none is 1.85-1.93, and
    iterations/bound is 0.37-0.45.
  - b = ones: ratio 1.00 at N = 20, 40 and 1.03-1.08 above.
  - At N = 1280 (random b): none 18.5 s; ic0 0.30 + 17.8 s; mic0 0.27 + 3.8 s; amg 1.26 + 2.36 s; CHOLMOD nesdis
    6.5 s setup + 0.06 s per solve. Plain CG is about 2x faster per iteration than on the reference machine
    (7.8 ms vs about 16 ms), which is why IC(0) is no faster than plain CG in wall time here.
- The FAIL is the ranking check "amg < mic0 < ic0 < none at every N >= 80, every rhs": at N = 80, b = ones,
  ic0 takes 47 iterations while plain CG takes 40. Plain CG on b = 1 terminates after floor((N-1)/2) steps,
  because b touches only that many eigenvalues. IC(0) in lexicographic order is not invariant under the
  triangle's symmetries, so the preconditioned system loses that and needs about 0.46 N steps.
  - b = ones iterations: N = 80 ic0 47 vs none 40; N = 160 84 vs 85; N = 320 157 vs 172; N = 1280 590 vs 686.
  - The margin is one iteration at N = 160.
  - On random, out_first and order321 the ranking holds at all 15 (N, rhs).
  - My reading: the expected row is wrong for b = ones (story point 2 is the reason). The check prints FAIL
    as written; it goes to the Project chat. I did not edit plan/ or loosen the check.
- Red flag: forward error max 4.85e-9 (ic0, out_first, N = 1280), above the spec's 1e-11 to 3e-9 band but below
  its 1e-8 WARN line. Every row above 1e-9 is a probability rhs (out_first or order321) at N >= 640; random b
  stays at or below 4.1e-10. The likely cause is that the smooth probability solutions sit mostly in low modes,
  where error/residual amplification is near 1/lambda_min. This is a chunk 4 topic; flagged for the Project
  chat.
- Figures: f03_iterations (two panels), f03_convergence (one panel per rhs, end labels with iteration counts),
  f03_time (legend only; end labels collided). Colors are the validated categorical slots in fixed order,
  plus a marker per kind, because three slots are below 3:1 contrast.
- Spec fix after the Project chat sanity check (Nov 10). Both chunk 3 findings were judged spec mistakes, and
  plan/c03_krylov.md was edited as agreed:
  1. The ranking row now reads "every rhs except ones". A new WARN row "b = ones: ic0 vs none" was added
     (IC(0) in lexicographic order breaks the symmetry behind plain CG's floor((N-1)/2) termination).
  2. The forward_error expected value is now "1e-11 to 3e-9 up to N = 640, about 5e-9 at N = 1280". Its
     tolerances are unchanged. The red flag is now "Forward errors above about 1e-8 at rtol 1e-10".
- check_c03 follows suit:
  - The ranking skips b = ones.
  - The new row passes if ic0 > none at every N <= 80 and the two are within 5% at N = 160. The spec says
    "about equal", and 5% is my reading of that. Observed: N = 160 84 vs 85.
  - The red-flag threshold is now 1e-8.
  - The information-only "ranking without ones" extra is dropped, since it is now the main check.
- Re-ran check_c03 on the same CSVs (git 08efc8a; experiments not re-run): 16 PASS, 0 WARN, 0 FAIL, no red
  flags.

## Chunk 4: accuracy diagnosis of the tiny probabilities (Nov 10)
- Derivation of cond_i = 2 E_x[T | event] (in my words):
  - A = I - Q, where Q >= 0 has a zero diagonal. So |A| has the same entries as A except the off-diagonals
    flip sign: |A| = I + Q = 2I - A.
  - For the exact solution, A x = b with x, b >= 0. So |A||x| + |b| = (2I - A) x + b = 2x - b + b = 2x.
  - A is an M-matrix, so A^{-1} >= 0 and |A^{-1}| = A^{-1}. The componentwise condition number
    (|A^{-1}|(|A||x| + |b|))_i / x_i is therefore 2 (A^{-1} x)_i / x_i.
  - Meaning: A^{-1} = sum_k Q^k (the chain is absorbed, so the series converges). (Q^k x)_i = E_i[1{T > k} x(X_k)]
    = P_i(T > k and the event happens), by the Markov property at time k. Here T is the number of rounds until
    the first bust.
  - Summing over k >= 0 gives E_i[T 1{event}], since T > k holds for exactly T values of k. Dividing by
    x_i = P_i(event) gives E_i[T | event]. conditional_mean_time computes that ratio, and the test checks it
    against E[T] = 3 x1 x2 x3 / N for the sure event (x = 1).
  - Consequence: the tiny entry at (1, 1, N-2) has cond about 0.388 N^2. The event "the big stack goes out
    first" forces a long game, but the tiny number is still well conditioned: about N^2 u relative accuracy is
    possible.
- gr/accuracy.py follows the spec's names exactly.
  - componentwise_backward_error counts 0/0 rows as 0 (np.divide with where=den > 0).
  - flint_solve builds a dense fmpz_mat from 6N A and 6N b. It turns each fmpq result into a Fraction and then
    a float (correctly rounded), and raises ValueError when scale * A or scale * b is more than 1e-9 from an
    integer. Timing: N = 80 takes 25 s.
- Experiments:
  - Full runs took about 4 min on 1 thread. Experiments run as `PYTHONPATH=. python experiments/...`, as in
    earlier chunks.
  - e04_condition has extra columns n, method, ordering and omega_over_u. States are written as "(x1, x2, x3)".
  - e04_errors: on direct rows, kind holds the ordering and rtol/iterations are NaN.
  - e04_errors has one added column, max_err_over_bound = max_i rel_err_i / (2 cond_i max(omega, u)). The spec
    row "max_rel_err <= 2 cond_i omega in every entry" cannot be checked from the scalar max_rel_err. The
    max(omega, u) is the same convention the acceptance test uses.
  - At N >= 160, the cholmod row is its own reference, so its errors are exactly 0. splu and banded are
    measured against it.
  - e04_perturbation: rng = default_rng(221), fresh for each (N, eps), so a --quick row equals the full-run row.
    Its columns are worst_ratio_min/max and random_max_ratio (plus eps_cond_max and draws).
- f04_tiny_error: the "direct solver's error" mark needed a choice. At N = 640 the reference is the CHOLMOD
  solve, so CHOLMOD's own error is 0. I drew two horizontal marks instead: SuperLU's tiny-entry error against
  CHOLMOD (2.0e-13, two independent direct solves), and the certified bound max_i cond_i omega_direct (2.4e-10).
- check_c04 readings:
  - The 2e-6 relative tolerance on N3_x_tiny is also applied at N <= 80.
  - "Direct methods" means every method other than cg.
  - The mic0/amg ratio row covers every rtol.
  - The backward-error row ("CG at rtol 1e-10") covers every CG kind.
  - The red flag "CG at 1e-14 with componentwise omega near u" reads "near u" as below 100 u and looks only at
    N >= 80. At N <= 40, rtol 1e-14 is itself about 90 u.
  - I set all of these readings before the full run.
- Results (git 2567b4c): 16 PASS, 1 WARN, 1 FAIL, no red flags.
  - N^3 x_tiny = 9.1195890 at N >= 320 (N = 1280 is -1.9e-11 from the Gamma(1/3)^9 / (8 pi^4) limit; the
    constant is published (Diaconis and Ethier 2022, Remark 4)).
    order_321 is exactly half.
  - argmin and argmax cond are at (1, 1, N-2) for every N and both events. cond_tiny / N^2 rises from 0.3733 to
    0.3884, and its fitted exponent over N >= 160 is 2.0001.
  - omega_direct is 1.4-20.4 u. The certified bound is 6.2e-12 (N = 160), 4.6e-11 (320), 2.4e-10 (640) and
    1.2e-9 (1280; out_first_3, measured).
  - Direct solvers against the exact rationals (N <= 80): max relative error 1.9e-15 to 9.4e-14, at 4-13% of
    the per-entry bound 2 cond_i omega.
  - CG none matches the reference numbers: rel_err_tiny at rtol 1e-10 is 2.1e-8, 3.7e-8, 2.5e-8, 6.8e-7,
    5.8e-6 and 1.4e-5 (N = 20 to 640). rtol 1e-14 converged at every N, in 1331 iterations at N = 640 and 2623
    at N = 1280. At N = 1280, rtol 1e-6, the tiny entry is off by 196%.
  - mic0's ratio to the prediction is 0.00075-0.016 and amg's is 0.019-0.2. Perturbation ratios are within
    1.5e-5 of 1 for eps <= 1e-8 and 1.0015 at eps = 1e-6, N = 80. Random perturbations give 0.24-0.39.
- WARN: CG none, ratio_tiny_to_prediction for N >= 320 and rtol <= 1e-8. The range is 0.54-6.01; N = 320 and
  N = 640 sit inside [0.5, 2] (1.01-1.63 and 0.90-1.00).
  - The misses are at N = 1280: 6.01 at rtol 1e-8 and 2.11 at rtol 1e-12.
  - The spec's 0.9-1.6 band was measured up to N = 640. It already notes that the law underestimates at loose
    rtol (ratio about 4 at rtol 1e-6, N = 640). At N = 1280, rtol 1e-8 is loose in the same sense:
    cond_tiny * rtol is 6.4e-3, and CG's error has not yet settled into the lowest modes.
  - For the Project chat.
- FAIL: componentwise / normwise backward error at rtol 1e-10, N >= 80, must be above 100.
  - Plain CG passes easily: minimum 9.8e3, up to 1.2e7 at N = 1280. amg passes too (minimum 276).
  - mic0 fails at two rows: 14.7 (N = 80) and 30.9 (N = 160). It is above 100 from N = 320 on.
  - This fits the diagnosis rather than contradicting it. MIC(0) already gets the tiny entry 60-1300x better
    than cond_tiny * rtol, so its residual is spread less unevenly against |A||x| + |b|.
  - I think the spec row means plain CG ("CG with the usual normwise stopping rule", story point 4). I applied
    it to every kind because that was the literal reading, chosen before the data. I did not edit plan/ or
    loosen the check. For the Project chat.
- Spec fix after the Project chat sanity check (Nov 10). Both chunk 4 findings were judged spec wording issues,
  and plan/c04_accuracy.md was edited as agreed:
  1. The backward-error ratio row is now two rows. "CG kind none at rtol 1e-10" keeps above 100 (FAIL) and
     records the measured 9.8e3 to 1.2e7. A new row "CG kinds mic0 and amg at rtol 1e-10" requires above 10
     (WARN): mic0 is 15-31 at N = 80-160 because its errors are already componentwise-small, and amg is 276 and up.
  2. The ratio_tiny_to_prediction row (CG none) now records "at N = 1280 up to 6 at rtol 1e-8 and 2.1 at 1e-12".
     Its tolerance is [0.5, 2] for N <= 640 and [0.3, 8] at N = 1280.
- check_c04 follows suit:
  - Both backward-error rows use N >= 80. The mic0/amg row says no N; N >= 80 is the plain-CG range and covers
    the sizes its mic0 numbers come from.
  - The per-kind breakdown is now part of each row.
- Re-ran only check_c04, on the same CSVs (git 2567b4c; experiments not re-run): 19 PASS, 0 WARN, 0 FAIL, no
  red flags.


## Chunk 4b: fixes from the external review of chunks 1-4 (Nov 10)
- Why: two referee passes found five things to change (plan/c04b_review_fixes.md). The biggest: fl(1/6) =
  (1 - 2^-54)/6, so every float solver solves the stored system (I - (1+d)Q) x = (1+d) b, d = -2^-54. Its
  solution differs from the true probability by d E_i[T | event] = -(u/4) cond_i in entry i. flint_solve
  solves the ideal system, so most of the "direct solver error" in chunks 2 and 4 is this data term.
- Kept build_A and boundary_rhs unchanged, as the spec decided. The data term is reported in its own columns.
- gr/accuracy.py: DELTA_SIXTH, data_error_term(x, solve) = DELTA_SIXTH solve(x) / x, and
  aposteriori_bound(A, b, x, solve) = (omega + 8u) cond_i. gr/matrix.py: rhs_landing(S, y). All three follow
  the spec's one-line definitions exactly. All 15 new tests pass, and nothing in chunks 0-4 regressed
  (239 passed).
- e04_condition: certified_bound is renamed to aposteriori_bound, and its value now includes the + 8u.
  New columns: data_term_tiny and data_term_over_N2u.
- e04_errors:
  - The data-term vector is computed from x_ref with the reference factor, before the factor is freed.
  - Every row now has signed_err_tiny, solver_err_tiny, max_solver_err and at_reference_accuracy. The columns
    that do not apply to a row's reference are NaN or empty, which keeps the CSV column order fixed.
- e04_mechanism (new), my readings:
  - "Plain CG" is krylov.cg with M = None, the same as kind none in e04_errors.
  - The sampled states come from one default_rng(221) per N: rng.choice(n, 4000, replace=False), joined with
    the 200 smallest-x states (duplicates removed). The same states are used for all three rtols.
  - At --quick (N = 80, n = 3081) that is every state.
- f04_tiny_error:
  - Removed the prediction line and the "SuperLU vs CHOLMOD" line.
  - Added the dashed |data_term_tiny| line. The bound line is now the a posteriori bound.
  - A hollow marker means at_reference_accuracy; a legend entry says so.
- f04_mechanism: panel (a) uses abs_err_max from the rhs CSV (the true maximum over all states) for the
  1/x guide line, and marks the corner with a star. Panel (b) inverts the x axis to match f04_tiny_error.
- check_c04 readings (fixed before the full run):
  - The data_term_tiny row applies the 1e-3 relative tolerance to the listed values literally.
  - Before writing the check I found a problem: at N = 320, 640 and 1280 the spec lists only 3 significant
    figures (-1.10e-12, -4.42e-12, -1.77e-11). The values implied by the existing cond_tiny are -1.1038e-12,
    -4.4153e-12 and -1.7661e-11, which are 3.5e-3, 1.1e-3 and 2.2e-3 away. That is rounding in the spec, not
    an error in the formula.
  - The row therefore FAILs as written. I added an information-only line comparing the column with the exact
    prediction -(u/4) cond_tiny. I did not loosen the tolerance or edit plan/. This goes to the Project chat.
  - The g_norm tolerance is 1e-3 absolute, as in the acceptance test.
  - "Mechanism vs e04_errors" matches each out_first_3 row with the CG-none e04_errors row at the same N and rtol.
- plan/ edits: exactly the approved list.
  - The c02 point-2 replacement text has no comma before "and flops", so the sentence now reads "...is a
    local slope and flops to n^{3/2}". I left it word for word.
  - c04 line 75 (spec text for e04_errors) still says "trusted to its certified bound". That phrase is not
    on the approved list, so I left it (it is the only remaining "certified" in plan/c04_accuracy.md).
  - check_c02's expected text for err_over_kappa_u still says 0.10-0.25. The spec did not list check_c02, so
    it is unchanged; its tolerance [0.02, 1] is the same either way.

- Results (git 0328a23; e04_condition 11 s, e04_errors 3.7 min, e04_mechanism 41 s on 1 thread):
  32 PASS, 0 WARN, 1 FAIL; the only red flag is the data-term flag below. (The commit message of
  083d5ab says "33 PASS": that was my miscount. There are 33 rows: 19 from chunk 4 plus 14 new, because
  the spec's aposteriori_bound row renames an existing row.)
  - data_term_tiny = -(u/4) cond_tiny to 2.2e-16 relative at every N, and data_term_over_N2u -> -0.09709.
  - The solvers' own error at the tiny entry (exact reference, N <= 80) is 8.5e-17 to 2.5e-14. At N = 80
    that is -2.5e-14 for CHOLMOD and +2.3e-14 for SuperLU, against a data term of -6.9e-14. Every solver-only
    error at N = 40 and 80 is below the data term.
  - aposteriori_bound: 1.5e-11 (160), 8.1e-11 (320), 3.8e-10 (640), 1.8e-9 (1280). Up to rounding these are
    the spec's values.
  - (N3_x_tiny - C) N^4 = 34.325, 34.374, 34.317 at N = 80, 160, 320.
  - CG none, rtol 1e-6, N = 1280 gives a negative probability: -4.18e-9.
  - e04_mechanism:
    - Its out_first_3 rows match e04_errors exactly.
    - g_norm = 1.17023 in all 40 rows; the smallest state is (1, 1, N-2) for all four right-hand sides.
    - abs_err_smallest is 4.5e-5 to 0.022 of g_norm ||r||_2. That is wider than the spec's "observed 5e-4 to
      1.5e-2", but the row's test (the bound holds) passes.
    - Ratios at N = 640 are exactly the spec's: land_mid 34-48, land_quarter 440 to 8.0, order_321 10.3 to
      0.385. The median over all states is 1.8e-4 to 4.0e-4.
    - At N = 640, rtol 1e-10, the absolute error is 5e-13 at the corner, 1.9e-10 at the median and 1.6e-9 at
      the maximum.
- FAIL (for the Project chat): the data_term_tiny row, through rounding in the spec's listed values only.
  - The measured -1.1038e-12 (320), -4.4153e-12 (640) and -1.7661e-11 (1280) sit 3.4e-3, 1.1e-3 and 2.2e-3
    from the 3-figure values -1.10e-12, -4.42e-12 and -1.77e-11.
  - N <= 160 agree to 3e-4 or better. Matching the information-only line, the column agrees with the exact
    prediction -(u/4) cond_tiny to 2.2e-16.
  - Suggested fix: list N = 320, 640, 1280 to 5 figures (-1.1038e-12, -4.4153e-12, -1.7661e-11).


## Plan: 4b cleanups and chunk 7 revision (Nov 10)
- The Project chat sanity-checked the chunk 4b report and approved these edits; I made exactly these.
  1. data_term_tiny row: N = 320, 640, 1280 are now printed as -1.1038e-12, -4.4153e-12, -1.7661e-11, with
     the tolerance unchanged (1e-3 relative). The mechanism bound row now reads "observed 4.5e-5 to 2.2e-2".
     - Both rows were edited in plan/c04b_review_fixes.md and also in plan/c04_accuracy.md, which holds copies
       of the same rows (the user confirmed this).
     - Mirrored in check_c04.py (DATA_TERM_REF and the expected-text strings).
  2. plan/c02_direct.md story point 2 now reads: "Fill-reducing orders (minimum degree, nested dissection) cut
     fill to n log n (George 1973; the fitted exponent 1.1 is a local slope) and flops to n^{3/2}." The old
     "(George's nested dissection theorem for 2D meshes)" is gone, as in the approved text.
  3. plan/c04_accuracy.md (e04_errors spec): "trusted to its certified bound" became "a direct solve of the
     stored system; its own error is about the size of the data term". No "certified" is left in that file.
  4. check_c02.py: the expected text for err_over_kappa_u is now "0.07-0.33", with tolerances unchanged.
  5. plan/c07_fixes.md was replaced by the revised spec from the Project chat (moved, no copy left behind).
     The revision reports every chunk 7 result against both the stored solution and the true probability,
     and adds data_term_tiny and err_vs_stored_* columns and rows.
     - tests/c07_fixes/ was not part of this change. Before chunk 7, check that its tests still fit the
       revised spec.
- Reran only the checks, on the same CSVs (no experiment was rerun).
  - check_c04: 33 PASS, 0 WARN, 0 FAIL, no red flags. data_term_tiny now agrees with the listed values to 3e-4
    or better at every N.
  - check_c02: unchanged except for the expected text. err_over_kappa_u is 0.074 to 0.326, PASS.



## Chunk 7: accuracy fixes (Nov 10)
- Tests first: tests/c07_fixes (18 tests) still fit the revised spec. The names and signatures match, and 18 is
  the count the spec gives. All 257 tests in c00-c04 + c07 pass. GTH max errors at N = 20, 40, 60 are 8.0 u,
  11.7 u and 24.7 u: the spec's 8, 12, 25 u.
- gr/refine.py
  - accurate_residual: Dot2 (Ogita, Rump and Oishi) over the integer system (6N A, 6N b).
    - Why TwoProduct is exact here: Dekker's split cuts each factor into a high and a low half of at most 26
      significant bits. Each of the four partial products then has at most 52 bits and is exact in float64, so
      p + e = a x exactly. That holds for any doubles without overflow. Here it is even simpler: |Ai_ij| <= 6N
      < 2^26, so the split of Ai_ij is exact with a zero low half.
    - TwoSum is exact for any doubles. So B_i - sum_j Ai_ij x_j = s + (sum of the error terms) exactly, and the
      only roundings are the compensation sum (of size u times the errors, about u^2 times the terms), s + c,
      and the division by the scale. The result is about 2u per entry.
    - The integer system is the IDEAL one: rint(6N fl(1/6)) = N. So this residual belongs to the true problem,
      and refinement removes the data term as well as the solver's own error.
  - Refinement builds (Ai, B) once and computes x = solve(b) unless x0 is given. Its steps count residual
    corrections only (the initial solve is not a step), matching the tests: "2 steps" after a direct solve.
  - gth_solve: why it is subtraction-free.
    - Off-diagonals are <= 0, row sums >= 0 and b >= 0. Every multiplier l = a_ik / pivot is <= 0. The code
      writes every update as x += (nonnegative) * (same sign as x):
      - pivot = s_k + sum(-a_kj) (all terms >= 0);
      - s_i += (-l) s_k (both >= 0);
      - a_ij += (-l) a_kj (a_ij and a_kj both <= 0);
      - y_i += (-l) y_k;
      - x_k = (y_k + sum(-a_kj) x_j) / pivot.
    - The diagonal is never updated: it is rebuilt from the row sum when its row pivots. The row sums of the
      Schur complement are s_i - l s_k, because a_k. 1 = s_k - pivot_k.
    - No cancellation means every operation has relative error u, so the error grows like the number of
      operations along a path (about N), not like N^2.
    - Storage is the upper band, row-contiguous (ub[k, d] = a_{k,k+d}), so the inner update loop is contiguous
      in both rows. Forward substitution recomputes l = a_ki / pivot_k from the final row k (the same rounding as
      in the factorization), so no L is stored.
  - cg_componentwise: the krylov.cg recurrence, with omega checked at k = 0 and at every multiple of
    check_every. It stops early (rz = 0) if the recurrence residual is exactly 0. The experiments pass maxiter
    30000, as in chunk 4: the default 10 n would run for ages if omega stalled.
- e07_fixes
  - Rows are direct and ir_direct (they share one CHOLMOD factor, so ir_direct seconds = factor time + refinement
    time), gth (N <= 640), and for each kind cg 1e-10, cg_componentwise 1e-12 and 1e-14, ir_cg_mic0 / ir_cg_amg.
  - Timings are the median of 3 runs. The accuracy columns come from the last run (every method is
    deterministic).
  - At N >= 160 the reference is refinement from x_direct with the same factor, so the ir_direct row equals the
    reference: its errors are 0 by construction. GTH is the independent check there (see the red flags).
  - Extra columns: n, converged, setup_seconds (needed for the "under 50% of the factor time" row) and
    signed_err_tiny. err_vs_stored_tiny is signed (the spec's values carry signs); rel_err_tiny is absolute, as in
    chunk 4.
- e07_fft_check: chunk 6 is not built, so the script prints a message and writes no CSV. Its code path follows
  the spec and chunk 6's API fft_solve(N, b), but it is untested until chunk 6 lands. Its two check rows WARN with
  "no CSV".
- e07_structured: "each off-diagonal entry" is read literally. Every entry gets its own factor, so A' is
  not symmetric and the solves use SuperLU (gr.matrix.solve), not GTH.
  - The base system is rebuilt the same way (diagonal = row sum + sum|a_ij|), so only eps differs between x
    and x'.
  - Solver noise in the ratio is about 2 * 0.07 N^2 u / eps, about 4e-5 at N = 160.
  - Quick run: random max 1.48, 1.96, 2.21, 2.94, 2.41 (N = 10 ... 160). N = 80 is above the spec's
    "1.5-2.4", but far below the limit of 10. It may depend on the draw order or on the symmetric vs
    nonsymmetric reading. Push 3.85, 4.30, 4.53, 4.64 match the spec's 3.9, 4.3, 4.5, 4.6.
- check_c07 readings (fixed before the full run)
  - N = 400 values: the spec's gth (120 u), direct (8018 u) and factor (67) values are quoted at N = 400, which
    is not in e07_fixes' N list. The rules are applied at the N that exist, and N = 400 is printed "not
    measured". Not changed in plan/; it goes to the Project chat.
  - "cg rtol 1e-10 as in chunk 4": chunk 4's band at N = 640 ([3e-6, 6e-5] around 1.4e-5, a factor 0.21 to
    4.3) is applied around each listed value (60, 160, 640).
  - The cg_componentwise rows cover every kind. The iteration-ratio and converged rows use tol 1e-14 at every N.
  - Figures: f07_accuracy uses kind none for both CG lines. ir_direct (error exactly 0) is drawn hollow at
    1e-17. Colors are categorical slots 1-5 of the dataviz palette (validated; the low-contrast slots get
    markers + legend).
- Results (git 522a5a2; e07_fixes 24 min, e07_structured 2 s, 1 thread): 16 PASS, 4 WARN, 0 FAIL, plus one
  real red flag.
  - Refinement:
    - Every ir_* row at N <= 80 equals the exact rationals rounded to double (0 u).
    - ir_direct takes 2 steps at every N; ir_cg_mic0 and ir_cg_amg take 3, or 4 at N >= 640.
    - At N >= 160, ir_cg_* agree with ir_direct to 0-2 u.
    - Refinement costs 0.056 s at N = 640 against a 1.34 s factorization.
  - GTH:
    - 8, 12, 25, 34, 46, 60, 200 u at N = 20 ... 640 (0.19-0.42 N). The log-log slope is 0.86.
    - At N >= 160 it sits within 2e-15 to 2e-14 of the refined reference, against a data term of 3e-13 to
      4e-12. GTH never uses refinement, so this confirms that refinement lands on the TRUE probability, not
      the stored one.
  - Direct against the true probability: 0.065-0.13 N^2 u.
    - At N = 80 that is 848 u, against the spec's 431 u. The spec number is probably SuperLU or Linux; chunk 4
      saw the same CHOLMOD-on-Mac difference.
    - That is why the GTH factor at N = 80 is 25, not 13.
  - Direct err_vs_stored_tiny: +0.032 N^2 u at N >= 160, opposite in sign to the data term, as the spec says.
    At N <= 80 it is smaller and has the same sign (-2.5e-14 at N = 80, as chunk 4 measured on this Mac).
  - cg_componentwise tol 1e-14:
    - Within N >= 160, every kind's err_vs_stored_tiny is below the direct solver's.
    - Its rel_err_tiny is the data term (at most 0.005 cond_tiny tol).
    - Iteration ratios: none 1.25-1.49, mic0 1.36-1.90, amg 1.38-1.86, except one row below.
- Red flag (for the Project chat): plain CG (kind none) at N = 1280 never reaches omega <= 1e-14.
  - It hit maxiter 30000; the run log says the smallest omega on its history was 3.46e-14 (312 u), and the final
    omega in the CSV is 4.0e-14 (360 u).
  - mic0 and amg reach it at N = 1280 (64 u each). At N = 640, none only just made it (89.2 u, against a
    threshold of 1e-14 = 90 u).
  - So plain CG's attainable omega rises with N past 90 u somewhere between N = 640 and 1280. The spec's "CG can
    reach omega of 10 to 70 u" holds for the preconditioned kinds, not for plain CG at the largest N.
  - The accuracy cost is small: rel_err_tiny is 1.6e-11, about the data term, and err_vs_stored_tiny is
    1.3e-12, still below direct's 5.7e-12.
  - This failure also causes two WARNs: the iteration ratio at N = 1280 is 13.97 (= 30000 / 2147), and
    "converged" holds in 23/24 rows.
  - The smallest omega is only in the run log, not in the CSV. A min_omega column needs a ~25 min rerun; not
    done without asking.
- The other WARNs are the two e07_fft_check rows (no CSV, chunk 6 missing).
- f07_accuracy now draws the non-converged point hollow. This is a figure-script change only; the CSVs are
  unchanged.
- Side check in a scratch script, NOT in the CSVs: perturbing the off-diagonal pairs symmetrically gives
  structured_random_max of 1.1-1.6 over three seeds. The literal nonsymmetric reading (in the CSV) gives
  1.5-2.9, closer to the spec's 1.5-2.4. Either way the ratio stays O(1) while cond_max grows like N^2.

## Chunk 7 follow-up: spec fixes and e07_floor (Nov 11)
- The Project chat approved a list of edits; I made exactly those.
  - The deleted root c07_fixes.md was identical to plan/c07_fixes.md.
  - The chunk 7 entry now says 16 PASS: the report was right, I miscounted.
  - The pushed commit 145e515 still says "17 PASS" in its message. History was not rewritten.
  - plan/c07_fixes.md: goal text for fixes 1-3, "why 3 works", the e07_floor paragraph, 12 rows replaced,
    4 e07_floor rows added, red flag and "done when". Rewrapped to the file's line width; no wording changed.
  - The g_norm sentence ("1.1702 for N >= 40 ...") is fixed in notes/proofs.md section 4 and in
    plan/c04b_review_fixes.md "Math to record".
    - The docstring of tests/c04_accuracy/test_c04b_review.py (line 196) still says "for every N". tests/ is off
      limits, so it is left for the Project chat. The test itself uses N >= 160 and passes.
- check_c07 mirrors the new rows.
  - Rows using converged runs only name what they exclude.
  - The converged row and the red flag share the rule "every mic0 and amg run, and none up to N = 640" (must_converge).
  - The "extra" CG check skips plain CG, tol 1e-14, N = 1280, and says so.
  - N = 400 is gone (GTH_REF, DIRECT_REF, strings). DIRECT_REF and STORED_REF are deleted: they were unused.
- f07_accuracy panel (b) adds "CG + AMG, stop at omega <= 1e-14" in categorical slot 7 (violet), validated
  together with the panel's other line colors.
- e07_floor (git c7eebd8, 3.0 min, 1 thread). min_omega_in_u:
  | N | none | mic0 | amg |
  |---|---|---|---|
  | 80 | 10.1 | 6.0 | 3.9 |
  | 160 | 15.5 | 9.9 | 4.6 |
  | 320 | 25.0 | 19.3 | 7.1 |
  | 640 | 50.8 | 26.0 | 15.1 |
  | 1280 | 311.8 | 62.2 | 23.9 |
  - Plain CG's minimum falls at k = 1.40-1.60 k10, matching the Linux 1.40-1.61.
  - Plain CG at N = 1280 bottoms out at 3.46e-14, the value e07_fixes' run log showed over 30000 iterations.
    The floor is reached within 1.6 k10, so maxiter did not cut it.
  - The floor is not always the final value. Plain CG at N = 640 reaches 50.8 u at k = 1680 and then drifts
    back up to 90.2 u. e07_fixes stopped at 89.2 u, just under 90 u, because it checks every 10 iterations and
    stops at the first omega below tol.
  - amg at N = 80 gave 3.9 u here and 4.3 u in the --quick smoke test (same code), and 5.0 vs 4.6 u at 160.
    pyamg's setup is not bitwise reproducible from run to run, probably through its random spectral-radius
    estimate. The effect is within the tolerances. Not fixed: it would need a pyamg seed in gr/krylov.py.
- check_c07 (only the check was rerun; e07_fixes and e07_structured are unchanged): 22 PASS, 2 WARN, 0 FAIL,
  no red flags. The two WARNs are the e07_fft_check rows (chunk 6 not built).

## Chunk 8: ICM application (Nov 11)
- gr/icm.py: `icm_orders`, `place_probabilities`, `equity`, plus `ORDERS`. Labels as in gr.matrix: "ijk" = i out
  first, k wins. The docstring carries the two-line proof of the equity identity.
  `pytest tests/c00_core tests/c08_icm`: 80 passed (34 new).
- Spec readings in experiments/e08_icm.py:
  - States in e08_icm_errors are sorted strings "a-b-c". e08_wikipedia keeps player 1 first ("198-1-1").
  - max_rel_err_p3 is unsigned, |P_ICM(3rd) - P(3rd)| / P(3rd). The ICM overrates it, so the sign is +.
  - Maxima are over all three players: `np.argmax` on (3, n) arrays. Ties would go to the first in C order.
    The spec gives runner-up gaps of at least 1.3e-6, so this does not matter.
  - frac_middle_overrated: the denominator is the number of states with three distinct stacks.
  - `seconds` in e08_icm_errors covers the solve plus the analysis. In e08_limit it is the solve only.
  - e08_states_N120 is also written under --quick, so the chunk 11 pipeline can draw f08_icm_map from quick
    results.
  - PUBLISHED is copied into the experiment from the test file, not imported (experiments do not import tests).
- check_c08: a row whose listed N is missing gets the row's kind, never PASS. So a --quick results folder
  shows FAIL on the per-N rows; that is the intended behaviour.
- f08_limit: orders with the same winner k sum to x_k/N, the same at every N, so their |P(N) - P(N/2)| are
  equal and the lines coincide. The second order of each pair is drawn dashed with hollow markers and labelled
  "same as". The six colors are categorical slots 1-6. They pass the validator's adjacent-pair gates; three are
  below 3:1 contrast, so each series also gets its own marker shape and the data is in the report.
- f08_icm_map: barycentric triangle, `tripcolor` (gouraud) on the lattice. Blue-gray-red diverging, symmetric
  about 0. The zero contour is dashed, and the extreme over- and underrate states are marked.
- Full run (git b9c10ec, 7 s in total, 1 thread): check_c08 gives 18 PASS, 0 WARN, 0 FAIL, no red flags.
  - Every value matches the spec to well inside its tolerance. max_abs_err_p2 rises 0.035889 -> 0.036050.
  - obs_order is 3.998-4.000 at N = 320 and 3.979-4.030 at N = 640 (rounding shows there, as the spec says).
  - The N = 640 solve took 3.8 s.
  - identity_max_dev grows about 4x per doubling of N: 2.3e-13 (30) to 3.8e-11 (480). It is a rounding residue
    of differences of O(1) sums, still under the 1e-10 limit at 480, but would pass it near N = 960. Fine for
    the spec's N list; worth knowing if chunk 10 reuses it at larger N.
