# Checkpoint 3 fixes (chunk 11b): prompt and spec for Claude Code

Written in the Project chat on Nov 14, 2026 from `claude/review-triage-checkpoint3.md`. Every edit below was
approved there. Where this file gives exact text, use it verbatim. Where it describes an edit, make the smallest
change that does it and show the diff in your report.

How to give it to Claude Code (fresh session, `/clear` first):

```
Read CLAUDE.md, then review3_inputs/checkpoint3-fix-prompt.md, and follow it exactly. It is an approved spec change:
copy it to plan/c11b_review3_fixes.md first. Do Part A, commit, then Part B, commit, then stop and report.
Do not start the full run.
```

Files to download from the Project chat into ~/Downloads first: `checkpoint3-fix-prompt.md` (this file),
`sor-law-proof.md`, `test_c05_theorem.py`, `test_c11b_edges.py`, `c09-cone-fem.py`.

## Ground rules

- The final-run CSVs (results at ee2db14, code 2ef9083) are correct. Two outside reviews and an independent
  re-check found no wrong number. This chunk fixes wording, citations, checks, figures and robustness.
- **Part A must not touch anything under `gr/` or `experiments/`.** Before committing Part A, run
  `git diff --stat ee2db14 -- gr experiments` and confirm it prints nothing.
- Do not edit existing tests. Two new test files come from ~/Downloads, validated in the Project chat against an
  independent stand-in package. Move them into place unchanged.
- Never run `experiments/run_all.py` without `--quick`. Neel starts the full run himself.
- Report at the end: `git log --oneline -3`, pytest counts, the check_all summary table, and every diff this file
  asked you to show.

---

## Part A: wording, citations, checks, figures (no code under gr/ or experiments/)

### A1. notes/proofs.md

1. Section 1, append after "by 3 to 8% for N >= 80.":
   > Prior work: the expansion of the constant vector in these eigenvectors is published for this chain (Bruss,
   > Louchard and Turner, Adv. Appl. Probab. 35 (2003) 278-294, eq. (2.1) and Theorem 2.1, which gives P(T > n) as
   > the same sum with the factors [(1 + 2 cos(2 pi k/N))/3]^n). Ours is the corollary for CG.
2. Section 2, first line: replace "(Skeel; Higham, Accuracy and Stability, ch. 7)" by
   > (componentwise condition numbers: Skeel 1979; Higham, Accuracy and Stability, ch. 7. To confirm before the
   > report: a reviewer attributes this entrywise form with the b term to Rohn 1989, via Higham section 7.5 and
   > Problem 7.1.)
3. Section 3: replace "(x' - t)_i / t_i = d (e2 - 3)/4." by
   "(x' - t)_i / t_i = d (e2 - 3)/4 + O(d^2) (x' - t = d A_d^-1 Q t is exact; the polynomial replaces A_d by A)."
4. Section 6: replace the last sentence ("Our addition: ... measured, not proved.") by
   > Since then it is a theorem: Denisov and Wachtel, "Harmonic measure in a multidimensional gambler's problem",
   > Ann. Appl. Probab. 34 (2024) 4387-4407 (arXiv:2212.11526), Corollary 4: P_{y1,y2}(third player eliminated
   > first) ~ Gamma(1/3)^9/(16 pi^4) y1 y2 (y1 + y2)/N^3, which is C A B (A + B)/2 N^-3 and gives C at A = B = 1.
   > So Lee's constant is rigorous, and N^3 P/(C A B (A+B)/2) -> 1 at every fixed corner state is their corollary,
   > not a finding of ours. Their Proposition 5 proves the rate O(N^-3) only. Our addition: with a correctly
   > rounded reference the values follow C + K/N^4, (v - C) N^4 = 34.375, 34.388, 34.391 at N = 160, 320, 640
   > (measured, not proved). Conjecture (checkpoint 3 review): K = pi C^3/(40 sqrt 3) =
   > Gamma(1/3)^27/(20480 sqrt 3 pi^11) = 34.3918115. Richardson extrapolation of the measured values in 1/N^2
   > gives 34.39181, and the relative coefficient pi C^2/(40 sqrt 3) = 3.7712 is approached at six corner states.
5. Section 7: replace from "Random perturbations: 1.5 to 3.1." through "is 0.16 to 0.34 kappa u." by
   > Random perturbations (every parameter times 1 + eps times an independent uniform(-1, 1) number): the relative
   > change of the tiny entry has standard deviation eps times 0.776, 0.835, 0.896, 0.959, 1.020, 1.079, 1.136 at
   > N = 10 ... 640 (the 2-norm of the sensitivities divided by sqrt 3). It still grows, by about 0.06 per doubling,
   > so it is not O(1) as far as we know. The largest change seen in 20 draws, over all states, was 1.5 to 3.1 eps
   > (structured_random_max); the largest is not always at the tiny entry. So there are four levels: 0.39 N^2
   > (entries of A, diagonal free), 1.22 N (structured), about log N (structured and symmetric), and an rms near 1
   > that grows slowly (random). The chunk 7 statement "2 to 5 eps at every N" described samples of the last one
   > only. The Alfa-Xue-Ye bound for this parametrization has a coefficient of order n; it does not promise O(1)
   > either. GTH's measured error is at most 0.42 N u at every entry (N = 20 ... 640). Divided entry by entry by
   > kappa_i u its maximum is 1.0, 1.7, 2.1, 2.3, 6.3, 6.9 at N = 20, 40, 60, 80, 160, 320 (checkpoint 3 review;
   > attained on the line x3 = 1, where kappa_i is about 3), so the data do not show an error bounded by a constant
   > times kappa_i u, and we do not claim stability in the structured sense.
6. Section 8, item 2: replace "about 3e-22 at N = 1280" by
   "about 2e-22 at N = 1280 (E[T^2 given event] = 0.0452 N^4 at the tiny entry)".
7. Section 8, item 3: replace the whole item by
   > 3. **The solver's own arithmetic.** Against the stored solution, at the tiny entry, in units of N^2 u (final
   >    run, Mac, N = 160, 320, 640): supernodal CHOLMOD +0.032, +0.032, +0.032; SuperLU COLAMD +0.025, +0.027,
   >    +0.028; simplicial CHOLMOD -0.018, -0.021, -0.022; SuperLU in natural order -0.048, -0.126 (N = 160, 320;
   >    -0.022 at N = 80), which grows faster than N^2 (about N^3.3); LAPACK band Cholesky +0.0001, -0.0010,
   >    -0.0054, small with changing sign. So the own error is a fraction of cond_i u (cond_tiny = 0.39 N^2) that
   >    depends on the algorithm, the ordering, the scaling (CHOLMOD on the integer matrix 6A: +0.14), the BLAS and
   >    the machine (Linux: supernodal +0.05, simplicial -0.006, COLAMD +0.03, natural -0.07 to -0.14). It is
   >    roughly a constant times N^2 u for supernodal CHOLMOD and COLAMD SuperLU only; it is not a law of direct
   >    solvers. Why these errors do not average out (identical local arithmetic on a regular lattice is our
   >    guess) is not established.
8. Last paragraph of section 8: replace "GTH never forms 2 and has no N^2 term in 3: 0.19 to 0.42 N u, not
   correctly rounded. A band Cholesky of the integer matrix 6A also avoids 2 but keeps a small N^2 term (0.0094 N^2
   u at N = 640, 19 times GTH's error)." by
   > GTH never forms 2, and its measured error is at most 0.42 N u for N up to 640 (not correctly rounded; no bound
   > of this form is proved here). A band Cholesky of the integer matrix 6A also avoids 2; its error is 0.0100 N^2 u
   > at N = 640, 20.5 times GTH's (final run).
9. New section "### 10. The SOR 3/4 law (theorem)": the content of review3_inputs/sor-law-proof.md from "## Setting"
   to the end, with its headings demoted to bold run-in titles. Leave out only its first "Status" paragraph.

### A2. Specs (plan/)

- **c05_stationary.md, Goal.** Replace "(its graph has triangles)" by "(its graph has triangles, so it is not
  bipartite: A has no Property A and no consistent ordering exists)". Replace the paragraph from "So SOR at omega*
  converges with 3/4 of the exponent" through "its relevance here was not checked." by
  > So the spectral radius at omega* is (omega* - 1)^(3/4): asymptotically SOR needs 4/3 as many sweeps as Young's
  > theory promises, still O(N) against O(N^2) for Jacobi and Gauss-Seidel. This is a theorem (notes/proofs.md
  > section 10; proved in the Project chat on Nov 14 and checked by two outside reviewers): the eigenvalues of the
  > SOR matrix are the cubes of the roots of a cubic that replaces Young's quadratic, the Perron mode gives the
  > spectral radius for every 0 < omega < 2, and omega* is the unique minimizer. It holds for every ordering in
  > which each lattice triangle has two steps to earlier states (the six lexicographic orders, backward sweeps,
  > the 3-colourings) and fails for a snake or a random order. We did not find it in the literature (the
  > reviewers searched Varga's p-cyclic theory, generalized consistent orderings, LeVeque and Trefethen 1988, and
  > Adams, LeVeque and Young 1988 on the 9-point stencil): say "not found", never "new". The theorem is about the
  > spectral radius, not about sweep counts at a fixed tolerance. At rtol = 1e-10 the counts are 1.43 to 1.44
  > times Young's prediction for b = 1 (a transient constant of about 5.6 on top of the 4/3), 1.28 to 1.35 times
  > for a random b, and 1.30 down to 0.96 times for b = P(player 1 out first), N = 10 to 640, because that run
  > ends before the slowest mode dominates. For b = 1 the run at N = 640 stops only about 4 times above the
  > smallest residual the sweep can reach (about 2.5e-11, growing 5.5 times per doubling of N), so the counts must
  > not be extrapolated beyond N = 640.

  Under the Expected results table add: "The best finite-run omega (row 'fine grid: best iterations_ones') is a
  description of b = 1 at N = 20, 40, 80, not a tuning rule: at N = 160 and 320 the best offsets are +0.0050 and
  +0.0025, for P(out first) the gain falls from 9% to 0%, and for a random b the best offset is negative from
  N = 80." In the law_relerr row replace "measured at most 2.3e-14" by "final run: at most 1.5e-14".
- **c07_fixes.md, Goal.** In fix 1 replace the sentence "In every run that converges, the tiny entry ends up 2 to
  5 times closer ... rtol 1e-10 rule." by
  > For N >= 160, where default CHOLMOD is supernodal, every converged run ends 2.2 to 5.0 times closer to the
  > stored solution than the default CHOLMOD solve (Mac: 2.9e-14 against 9.1e-14 at N = 160, 3.0e-13 against
  > 1.5e-12 at N = 640, plain CG), and the AMG run at N = 160 11 times closer, for 1.25 to 1.9 times the
  > iterations of the usual rtol 1e-10 rule. For N <= 80 both errors are a few ulps of the reference and their
  > ratio is noise (0.18 to 44 over the 12 runs; 5 of them end farther than the direct solve).

  Fix 2 heading: "Iterative refinement with an exact residual." becomes "Iterative refinement with the compensated
  residual of the ideal system." Fix 3: "better by 1.4 to 5 for N <= 160" becomes "better by 2.0 to 4.8 for
  N <= 160". Last paragraph: replace "Random perturbations move x by only 1.5 to 3.1 eps and symmetric ones by
  about log N (17.4 at N = 640). GTH's measured error, 0.19 to 0.42 N u, is 0.16 to 0.34 kappa u: a
  subtraction-free algorithm is stable in this parametrization." by
  > Random perturbations move the tiny entry by an rms of 0.78 to 1.14 eps (N = 10 to 640, still growing slowly;
  > the largest of 20 draws over all states was 1.5 to 3.1 eps) and symmetric ones by about log N (17.4 at
  > N = 640). GTH's measured error is at most 0.42 N u at every entry, far below cond_i u, which is what this
  > parametrization suggests; but entry by entry it reaches 7 kappa_i u (N = 320), so we do not claim a stability
  > theorem in the structured sense.
- **c07b_review_fixes.md.** Add one line under the title: "Numbers in this file are from review 2 (Linux and
  earlier Mac runs). The final-run values and the corrected wording (rms in place of 'O(1)'; no N^2 u 'law') are
  in notes/proofs.md sections 7 and 8."
- **c08_icm.md, Goal.** In fact 4 replace "so the ICM is off by a factor of about N/4.56." by "so the ICM is too
  large by the factor 2 N^2/(9.12 (N - 1)), about N/4.56 (max_rel_err_p3 is that factor minus 1: 5.806 at
  N = 30)." After fact 4 add:
  > Prior work for the maximum: the Wikipedia page "Independent Chip Model" (section "Comparison to gambler's
  > ruin") already states that 25/87/88 at N = 200 gives the largest probability difference (0.0360) and the
  > largest equity difference ($0.36). Ours: the scan over N (0.0359 to 0.0361 at N = 30 to 480; not monotone in
  > N: 0.0343 at N = 13 in the reviewers' scans), the sign pattern at every state, and the equity identity.
- **c09_four_players.md, Goal.** Fact 1: replace "T/(x1x2x3x4) varies by a factor of 2 to 6." by "T/(x1x2x3x4)
  varies by a factor that grows like N/10 (1.3 at N = 10, 6.0 at N = 60); the bounded normalization is
  T e2/(6 e4), which stays in [0.82, 1.06]." Fact 2: replace "Nested-dissection fill grows like n^(4/3) and work
  like n^2," by "For nested dissection of a 3D mesh the fill is of order n^(4/3) and the work of order n^2 (Lipton,
  Rose and Tarjan 1979; George 1973 is the 2D result). The measured local slopes are 1.39 to 1.47 and 2.0 to 2.2
  (N = 20 to 100): near those orders, not converging to them on this range;". Fact 4: title "A tiny probability
  with a new exponent." becomes "A tiny probability with an irrational exponent."; after "decays like N^-5.72"
  insert "(Diaconis and Ethier 2022, section 4.2 and Table 11, tabulate this probability divided by 6 for N = 10 to
  100 and estimate the exponent 5.72 from it; our values are 6 times theirs to 8 digits)"; at the end of fact 4
  add "Ours: the refinement to 5.720688 through the cone eigenvalue (experiments/e09_cone.py from part B on; two
  reviewers' independent spectral computations give 38.4469620), N up to 200, and the 1/N^2 rate with its
  coefficient." In the Expected results rows change "theory n^(4/3)" and "theory n^2" to "3D nested-dissection
  orders 4/3 and 2 (Lipton-Rose-Tarjan); local slopes 1.39 to 1.47 and 2.0 to 2.2".
- **c10_extras.md, Goal.** "We redo such a fit as a least-squares lab:" becomes "We reproduce their regression
  (their section 3 and Table 6: N = 300, the same 7500 states, targets, sextic and monomial order; the
  coefficients agree to the printed digits) and use it as a least-squares lab:". Fact A1: "by 1e-7 to 4e-6
  (relative), QR by 1e-13 to 2e-11, yet all three fitted curves agree to 1e-8" becomes "by 6e-8 to 6e-6
  (relative), QR by 2e-13 to 2e-10 (machine dependent; against an extended-precision solve the SVD is no more
  accurate than QR), yet all three fitted curves agree to 1e-9". Fact A2: "The sextic fits 321 and 312 to about
  1e-6 relative (max residual 5.6e-6 and 6.7e-6)" becomes "The sextic fits the ratios R_321 and R_312 with largest
  residual 5.6e-6 and 6.7e-6 (as a relative error of the probability the largest misfit is 2.1e-4 and 2.3e-4, at
  (1, 1, 298) where R = 0.015)"; "a boundary layer at A = 1, 2 that no low-degree polynomial follows" becomes
  "and to 0.665 along A = 1: a singularity at the corner A = B -> 0 (Diaconis and Ethier note it) that degrees 2
  to 8 do not resolve". Fact B3: "(1e-15): Gaussian elimination is unaffected by a diagonal similarity scaling,
  Krylov stopping tests are not." becomes "(2e-14): in exact arithmetic Gaussian elimination with a fixed pivot
  order commutes with a diagonal similarity scaling (bitwise in floating point only for powers of 2), while a
  Krylov stopping test does not."
- **c02_direct.md line 18 and c04b line 120.** Attach George 1973 to nested dissection only ("O(n log n) fill on a
  regular 2D mesh: a theorem for nested dissection"); describe AMD/COLAMD/MMD fill as measured. Show the diff.
- **c03_krylov.md.** "about 2.3 times too pessimistic" becomes "2.2 to 2.7 times too pessimistic (N = 20 to 1280;
  the factor grows slowly)". "MIC(0) makes kappa grow about linearly (Gustafsson 1978):" becomes "MIC(0) makes
  kappa grow about linearly in N here (measured; Gustafsson 1978 is cited for the method, his bound is for a
  perturbed factorization of 5-point-type matrices):".
- **c06_fft.md.** "At N = 800 the FFT and splu already disagree by about 1e-6 relative at the smallest P(123)."
  becomes "At N = 800 the FFT is off by 4.8e-7 relative at the smallest P(123) (final run; the figure depends on
  the FFT library's rounding: 1e-10 to 1e-8 at N = 100 to 320 across three implementations), while the direct
  solvers stay at 1e-13 to 5e-12."
- **c11_final_run.md.** Row "results equal to the per-chunk runs": kind FAIL becomes WARN, and append to its
  Expected cell "(the values are judged by the per-chunk check scripts, which run on these CSVs; this row lists
  what moved, for the Project chat)". Add rows: "no row missing against the baseline run | yes | FAIL" and "CSV
  hashes equal the code hash (last commit that touched gr/ or experiments/) | yes | FAIL".
- **c12_report.md.** Line 27: "the SOR 3/4 law" becomes "the SOR 3/4 law (a theorem: proofs section 10)". Line 29:
  "normwise stopping fails as cond_tiny * rtol" becomes "normwise stopping fails (a residual test bounds absolute,
  not relative, error)". Line 31 becomes "7. What is ours, what was already published (cite), what is measured,
  and what is conjecture (the N^-4 rate; the closed form of its coefficient)." Add to What to build: "README.md
  rewritten: purpose and headline results; setup; `PYTHONPATH=.` for experiments; how to run tests, one
  experiment, the pipeline, checks and figures; hardware and time; the map chunk -> spec -> experiment -> CSV ->
  check -> figure; the code and results commits; known limits (memory figures, machine-dependent constants)."
- **CLAUDE.md line 65:** `PYTHONPATH=. python experiments/<name>.py [--quick] [--outdir DIR]`.

### A3. notes/decisions.md

Append a dated entry "Checkpoint 3 review (Nov 14)" that says, in your own words: two outside reviews of ee2db14
found no wrong number; and lists these corrections to earlier entries: (1) lines 26-28: "CG's tiny-entry error is
about cond_tiny * rtol", "correctly rounded" as a finding of the scaffold, and "the structured condition number is
O(1)" are superseded (chunks 4b, 7b and this entry); (2) "Not found in their paper, so ours: the largest
second-place error" is wrong: the Wikipedia page states it; (3) exponent credit: Diaconis-Ethier Table 11 has the
values and 5.72; (4) the regression is Diaconis-Ethier's section 3, reproduced; (5) the CG expansion is Bruss,
Louchard and Turner's; (6) C is a theorem (Denisov-Wachtel); (7) the memory guard cannot prevent swapping (peak
RSS levels off under memory pressure: SuperLU-MMD at N = 100 "finished" at 2922 MB on Nov 11 and passed 4.7 GB
on Nov 14), so memory is reported as nnz and the Nov 11 time of 203 s is not quoted; (8) "nnz grows like n^1.42, as
the theory says" becomes "near the 3D order 4/3"; (9) the 3/4 law is a theorem.

### A4. checks/

- **check_all.py.** Add `code_hash()`: the short hash of `git log -1 --format=%h -- gr experiments`, plus "-dirty"
  under the same rule as `gr.runlog.git_hash`. Use it in place of `commit` in the rows "every experiment exits 0"
  and "one git hash across all CSVs", and print both hashes in the report's first line ("code at git X; HEAD Y").
  Reason: at the results commit HEAD differs from the CSV hash, and the present code reports 2 FAIL. Add the row
  "no row missing against the baseline run" (FAIL if `compare` finds rows removed from any CSV). Change nothing in
  how the "results equal" row is computed. In the "Machine" section also print the versions of scikit-sparse,
  pyamg, numba, python-flint, pandas and matplotlib (`importlib.metadata.version`) and the values of
  OMP_NUM_THREADS, OPENBLAS_NUM_THREADS and VECLIB_MAXIMUM_THREADS.
- **check_c07.py.** Row 1 expected text becomes "0 against exact rationals; tolerance 2 u (a regression band, not
  a proof of correct rounding: that is e07_baselines' half-ulp row)". Row 12 expected text: "0.05-0.46" becomes
  "0.09-0.46" and "amg 4.6e-15" becomes "amg 8.0e-15" (the seeded run).
- Run `python checks/check_all.py`. Expected: 0 FAIL in every row (code hash 2ef9083). If any FAIL appears, stop
  and report it.

### A5. figures/ (titles and labels only; rerun `python figures/make_all.py`)

- f02_direct.py:86 and f06_fft.py:50: "median of 3" becomes "median of the timing repeats (5 in the final run)".
- f07_structured.py title: "... log N if symmetric, O(1) for random perturbations" becomes "... about log N if
  symmetric; random draws: largest of 20" (part B adds the rms curve).
- f10_regression.py:80: "213 has a boundary layer no polynomial follows" becomes "213: a corner singularity that
  degrees 2 to 8 do not resolve".
- f04_mechanism.py:66: "every entry" becomes the number of plotted states ("{n} sampled states").
- f07_accuracy.py panel (a): draw refinement (ir_direct) from e07_baselines.csv column max_true_err_in_u (0.84 to
  1.00 u, the independent exact-residual measurement) instead of the "error 0" of e07_fixes, which for N >= 160
  compares the refined vector with itself. Legend: "refinement: within half an ulp (exact integer residuals)".
- f09_solvers.py panel (b): plot nnz_factor instead of peak_rss_mb (axis "nonzeros of the factor"); note in the
  title that SuperLU-MMD at N = 100 was stopped by the memory guard.
- f07_baselines.py panel (a): filled markers for positive own errors, hollow for negative; say so in the legend.
- f05_iterations.py: add the SOR counts for b = out_first and b = random (already in e05_iterations.csv) as
  thinner lines, and Young's predicted count as a guide; title unchanged.

### A6. tests

`mv review3_inputs/test_c05_theorem.py tests/c05_stationary/`. `pytest -q` must give 513 passed, 42 skipped (470 + 43).

### Commit A

`git diff --stat ee2db14 -- gr experiments` prints nothing. Commit everything, including the regenerated figures
and reports, as "checkpoint 3 fixes A: wording, citations, checks, figures".

---

## Part B: code (gr/ and experiments/), then one full rerun by Neel

### B1. New experiment experiments/e09_cone.py (the cone eigenvalue now comes from the repo)

Build it from review3_inputs/c09-cone-fem.py: keep `lam1(V, m)` and `alpha(lam)` unchanged. Options `--quick` and
`--outdir` like every experiment; write `e09_cone.csv` through `save_results`, one row per domain with columns
domain ("octant", "tetrahedron_vertex"), m_finest, lambda_finest, lambda_h2 (one Richardson step on the two
finest meshes), lambda (two steps), alpha, lambda_exact (12 for the octant, NaN otherwise). Meshes m = 64, 128,
256, 512 (full, about 10 s) and 16, 32, 64 (quick).

checks/check_c09.py: read ALPHA from e09_cone.csv (row tetrahedron_vertex) instead of the typed constant, and add
the first three rows of the table below.

### B2. experiments/e07_structured.py: new column rms_random_tiny

After `g = base.solve(e)`:

```python
sens2 = np.sum((g * b) ** 2) + np.sum((g * sums * x) ** 2) + np.sum((g[r] * v * (x[r] - x[c])) ** 2)
rms_random_tiny = np.sqrt(sens2 / 3) / x[tiny]
```

(the standard deviation, per unit eps, of the tiny entry's relative change when every off-diagonal entry, row sum
and b_i is multiplied by 1 + eps * uniform(-1, 1)). Existing columns and the order of the random draws must not
change. checks/check_c07.py: new FAIL row from the table. figures/f07_structured.py: plot rms_random_tiny as the
"random" curve, keep structured_random_max as hollow markers labelled "largest of 20 draws (all states)"; title
ends "... about log N if symmetric, rms near 1 for random perturbations".

### B3. experiments/e09_four.py, alpha_rows

The three-player slopes approach 3 like 1/N^4, the four-player slopes approach alpha like 1/N^2. Use
`x = 1 / (Ns[1:] * Ns[:-1]) ** (power / 2)` with power = 4 for players == 3 and 2 for players == 4, and fix the
docstring. Nothing else in e09 changes.

### B4. experiments/run_all.py and checks/check_all.py: outputs are verified, not assumed

- After an experiment exits 0, record in `<outdir>/run_all_manifest.json`, under the script's log name:
  {"git_hash", "quick", "csv": {file name: sha256}} for every `*.csv` in outdir (except the log) modified since
  that experiment started.
- `already_done` returns True only if the LAST log row for the script has exit code 0, quick False and the
  current hash, AND the manifest has that script at that hash, AND every listed CSV exists with the same sha256.
  Otherwise the experiment runs again. Fix the docstring's resume rule.
- check_all.py: new FAIL row "CSVs match the run manifest": every CSV listed for the latest successful run of
  each experiment exists and has the recorded sha256; a CSV in results/ that no manifest entry lists is named in
  the row (WARN). Skip the row with a note when there is no manifest (the ee2db14 results).
- Before the full run delete results/run_all_log.csv (it stays in git history) so the new log starts clean.

### B5. Edge cases (tests: `mkdir tests/c11b_review3 && mv review3_inputs/test_c11b_edges.py tests/c11b_review3/`;
8 tests, not opt-in, all must pass after these edits)

- gr/stationary.py `_iterate`: divide the residual by `scale = bnorm if bnorm > 0 else 1.0`.
- gr/refine.py `cg_componentwise`: after the loop, `if k % check_every != 0: omegas.append(...)` for the final x,
  so `converged` and the last omega describe the returned iterate. Update the docstring.
- gr/four.py `_Keyed._check`: also raise ValueError unless every entry of x is an integer (`int(v) == v`).
- Docstrings only: gr/refine.py error-free transformations assume no overflow or underflow (normal range);
  `iterative_refinement` assumes x has no zero entry; gr/krylov.py `make_preconditioner` reseeds NumPy's global
  generator (say so); gr/direct.py `_banded`: "The Cholesky factor fills the whole band" becomes "nnz counts the
  band storage; the factor's nonzeros are the envelope (394 of 550 slots at N = 12)".

### B6. Expected results (add to plan/c11b_review3_fixes.md as written; checked after the full rerun)

| Check | Expected | Tolerance | Kind |
|---|---|---|---|
| e09_cone lambda, octant | 12.000000 | 1e-6 abs | FAIL |
| e09_cone lambda, tetrahedron_vertex | 38.446962 (Project chat 38.446962018; reviewers 38.4469620) | 2e-6 abs | FAIL |
| e09_cone alpha, tetrahedron_vertex | 5.720688 | 1e-6 abs | FAIL |
| e09_alpha, players 3, alpha_extrapolated (1/N^4 fit) | 3.0000000 (Project chat: 3.0000000171 from the ee2db14 slopes) | 1e-6 abs | FAIL |
| e09_alpha, players 4, alpha_extrapolated | 5.7206868, unchanged; within 1e-4 of e09_cone alpha | | FAIL |
| e07_structured rms_random_tiny, N = 10 ... 640 | 0.7761, 0.8348, 0.8964, 0.9588, 1.0201, 1.0793, 1.1361 | 1e-3 relative | FAIL |
| rms_random_tiny | increasing in N | | FAIL |
| changes against ee2db14 (`check_all.py --baseline ee2db14`) | only: e09_alpha players 3 alpha_extrapolated; the e09_solvers rows whose status depends on the memory guard; the new column and the new CSV. e07_floor.csv must be bit-identical (added Nov 14 with Neel's approval: e07_floor keeps only the check-point omegas of cg_componentwise) | anything else that moves: stop and bring it to the Project chat | FAIL |
| pytest -q | 521 passed, 42 skipped (513 + 8) | | FAIL |
| pipeline test (GR_PIPELINE=1) | passes with e09_cone included | | FAIL |

Quick-run sanity (not a check row): e09_cone --quick gives lambda 38.44696 and alpha 5.72069 for the tetrahedron
vertex and 12.00000 for the octant.

### Commit B, then stop

Run `pytest -q`, `GR_PIPELINE=1 pytest tests/c11_pipeline -q`, and `python experiments/run_all.py --quick`. Commit
as "checkpoint 3 fixes B: code". Report and stop.

### The rerun (Neel, in a separate terminal tab, Mac restarted, nothing else open)

```
caffeinate -i python experiments/run_all.py 2>&1 | tee results/run_all_console.txt
python experiments/run_all.py --e02-big
python figures/make_all.py && python checks/check_all.py --baseline ee2db14
```

Then a Claude Code session commits the results as "checkpoint 3: final rerun" and pastes results/final_report.md
into the Project chat. With AMG seeded, every number except those named in the "changes against ee2db14" row of
B6 should come back bit-identical; the report can cite that as its reproducibility check.
