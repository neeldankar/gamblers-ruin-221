# Chunk 9: Four players

- **Depends on:** chunks 2 and 3 (direct and Krylov solvers, timing and memory conventions); chunk 1 for
  `gr.runlog`
- **Learn first:** Theory Guide §3 (sparse direct methods: why fill explodes in 3D) and §6 (Krylov
  methods: CG with an algebraic multigrid preconditioner)
- **Time:** build 60-90 min · compute 15-30 min (full; `--big` adds 15-20 min), about 1 min (`--quick`) ·
  your review about 1.5 h · plug in: yes · peak memory about 2.5 GB (5-6 GB with `--big`; do not use
  `--big` on an 8 GB machine)
- **Read this yourself:** `gr/four.py`, especially `build_lumped` (why sorting the first three stacks
  gives an exact smaller chain) and the two-line derivation of A (6 x1 x2 x3 x4) = e2

## Goal

Move from a 2D triangle of states to a 3D tetrahedron: chips (x1, x2, x3, x4), sum N, each round one of
the 12 ordered pairs (a, b) is chosen with probability 1/12 and a takes a chip from b. Live states have
every xi >= 1, so n = C(N-1, 3) (156,849 at N = 100). The matrix A = I - Q is still sparse SPD, now with
up to 13 nonzeros per row, and the questions are:

1. **Closed forms survive only partly.** P(i wins) = x_i/N still holds. The product identity becomes
   E[change in x1x2x3x4 per round] = -e2/6 with e2 = sum_{i<j} xi xj, so A (6 x1x2x3x4) = e2 exactly (a
   free accuracy test at any N). But E[rounds to the first bust] T = A^{-1} 1 has no product formula:
   T/(x1x2x3x4) varies by a factor of 2 to 6. Since A^{-1} >= 0 and 3N - 6 <= e2 <= 3N^2/8, we still get
   16 e4/N^2 <= T <= 2 e4/(N - 2), with e4 = x1x2x3x4.
2. **Direct solvers hit a memory wall in 3D.** Nested-dissection fill grows like n^(4/3) and work like n^2,
   so at the same size, n = 157k, the CHOLMOD (METIS) factor has 11 times the fill of the three-player one
   (74.5e6 at N = 100 against 6.6e6 at N = 561) and takes 127 times the flops (1.41e11 against 1.11e9).
   AMG-preconditioned CG stays near linear.
3. **Symmetry reduction.** For quantities symmetric in players 1-3 (like P(player 4 busts first)),
   lumping states by sorting (x1, x2, x3) gives an exact chain about 6 times smaller. It is not
   symmetric, but diag(orbit sizes) A_L is, so W^(1/2) A_L W^(-1/2) is SPD (W = orbit sizes, at most 6, so
   the scaling is harmless) and CHOLMOD or CG apply.
4. **A tiny probability with a new exponent.** From (1, 1, 1, N-3), P(the chip leader busts first)
   decays like N^-5.72 (three players, from (1, 1, N-2): exactly N^-3 with P N^3 -> 9.1196). The
   exponent is the harmonic exponent of the tetrahedron's vertex cone: alpha = sqrt(1/4 + lambda) - 1/2, with
   lambda the first Dirichlet eigenvalue of its spherical triangle (angles arccos(1/3)). O'Connor and
   Saloff-Coste (arXiv:2209.05264, 2022, Theorem 1.1) prove that P is of order N^-alpha and estimate
   lambda ~ 38.447; they print alpha ~ 5.68, which does not follow from their own lambda and formula (5.7207).
   Project chat, independent P1 finite elements with Richardson extrapolation (the octant gives 12 to 1e-8):
   lambda = 38.446962, alpha = 5.720688. The chain's local slopes approach it like alpha - 4.4 / N^2
   (three players: like N^-4).

## What to build (the tests import exactly these names)

`gr/four.py`
- `MOVES4`: the 12 ordered pairs (a, b), a != b, in the order `[(a, b) for a in range(4) for b in range(4) if a != b]`.
- `FourStateSpace(N)`: attributes `N`, `n`; `coords() -> (n, 4)` integer array; `index(x) -> int` for a
  live 4-tuple; `state(i) -> tuple` of 4 ints. Live states ordered lexicographically by (x1, x2, x3).
  Keep enumeration memory-light (loop over x1, vectorize the rest): N = 200 has 1.29 million states.
- `build_A4(S) -> scipy.sparse.csr_matrix`: A = I - Q, off-diagonals exactly -1/12.
- `boundary_rhs4(S, f)`: like `gr.matrix.boundary_rhs` with 12 moves and weight 1/12; f maps an (m, 4)
  array of landing states (one zero coordinate) to m values.
- `rhs_out_first4(S, i)` (boundary value 1 where y_i = 0) and `rhs_win4(S, i)` (boundary value y_i/N).
- `LumpedSpace(N)`: states with y1 <= y2 <= y3 and y4 = N - y1 - y2 - y3 >= 1; attributes `N`, `n`,
  `weights` (orbit size of (y1, y2, y3): 6, 3 or 1; they add up to C(N-1, 3)); `coords() -> (n, 4)`;
  `index(y) -> int` that accepts any live 4-tuple and sorts its first three entries.
- `build_lumped(L) -> (A_L, b)`: A_L = I - Q_L as CSR, where each of the 12 moves from the sorted state y
  lands on the sorted version of the result; b is the right-hand side for P(player 4 busts first).
  Rows follow `L.coords()`.
- `big_stack_out_first(N) -> float`: P(player 4 busts first) from (1, 1, 1, N - 3), from the lumped chain.

## Experiment

`experiments/e09_four.py` (and `experiments/e09_worker.py`: each solver run happens in a fresh subprocess
so peak memory is measured per run, the way the prototype did it). Writes, through `gr.runlog.save_results`:

1. `results/e09_identities.csv`: N in {10, 20, 30, 40, 60} (`--quick`: 10, 20). Columns: `N, n,
   max_nnz_row, max_abs_A_minus_AT, e2_identity_relerr, win_maxerr, out_first_sum_maxerr, T_max,
   T_max_state, T_over_e4N_min, T_over_e4N_max, T_e2_over_6e4_min, T_e2_over_6e4_max, bounds_hold`.
   T_over_e4N = T / (e4/N); T_e2_over_6e4 = T e2 / (6 e4).
2. `results/e09_solvers.csv`: right-hand side e2, so the exact answer 6 e4 is known. Methods: `splu`
   (default COLAMD), `splu_mmd` (`permc_spec="MMD_AT_PLUS_A"`), `cholmod`, `amg_cg` (pyamg
   `smoothed_aggregation_solver(A).solve(b, tol=1e-12, accel="cg")`). Sizes: direct methods N in
   {20, 40, 60, 80, 100} but skip a run when its projected factor memory (fit nnz(L) against n on the
   sizes already done) exceeds 3 GB; `amg_cg` N in {20, 40, 60, 80, 100, 120, 150, 200}. `--big` adds
   N = 120 for `cholmod` (needs about 5 GB) and N = 250 for `amg_cg`. `--quick`: N in {20, 40}.
   Columns: `N, n, method, setup_s, solve_s, peak_rss_mb, nnz_factor, flops, iters, rel_err, status`, with
   flops = the sum of column_counts()^2 of the factor for cholmod (NaN for the other methods).
   Median of 3 timings when a run takes under 60 s, else 1 run (say so in `status`).
3. `results/e09_big_stack.csv`: lumped chain, N in {8, 10, 12, 16, 20, 24, 30, 40, 50, 60, 80, 100, 120,
   160, 200} (`--quick`: up to 40; `--big` adds 240). Solve with CHOLMOD on W^(1/2) A_L W^(-1/2) (N = 200:
   about 1 min and 2 GB), falling back to `splu` up to N = 120 if CHOLMOD is missing. Also the
   three-player value from (1, 1, N-2) with `gr.matrix` for N in {10, 20, 40, 80, 160, 320}. Columns:
   `players, N, n_full, n_lumped, P, local_slope, seconds, solver`, where local_slope =
   log(P(previous N) / P(N)) / log(N / previous N).
4. Fit alpha from the last four local slopes (least-squares line slope = a + c / N_mid^2,
   N_mid = sqrt(previous N * N), because the four-player slopes approach alpha like 1/N^2) and write it to
   `results/e09_alpha.csv` with columns `players, alpha_last_slope, alpha_extrapolated`.

Figures: `figures/f09_solvers.py` (setup + solve time and peak memory against n, log-log, one line per
method, with n^1 and n^2 guides) and `figures/f09_big_stack.py` (P against N, log-log, three and four
players, slopes -3 and -5.72 marked).

## Acceptance tests

`pytest tests/c00_core tests/c09_four` (37 new tests). They check the 12 moves, the state count and
order, the matrix structure (symmetric, unit diagonal, -1/12 off-diagonals, <= 13 nonzeros, Q row sums),
positive definiteness, A (6 e4) = e2, P(win) = x/N, out-first probabilities summing to 1 and permuting
with the players, exact rationals for P(leader busts first) at N = 5..8 (1/13, 2/71, 38/3203,
11017/1975144) from an independent Fraction solver, the lumped space (sizes 11, 41, 204; weights adding
to C(N-1, 3)), lumped = full at N = 8..30, the weighted symmetry, reference values at N = 12..80, the
decay exponent, the T bounds, and one AMG-CG solve (skipped if pyamg is missing).

## Expected results (the check script tests these against the CSV)

| Check | Expected | Tolerance | Kind |
|---|---|---|---|
| e09_identities n | C(N-1, 3): 84, 969, 3654, 9139, 32509 | exact | FAIL |
| max_nnz_row; max_abs_A_minus_AT | 13; 0 | exact | FAIL |
| e2_identity_relerr, win_maxerr, out_first_sum_maxerr | below 1e-12 | | FAIL |
| bounds_hold | True at every N | | FAIL |
| T_over_e4N_min, T_over_e4N_max at N = 20, 30, 40, 60 | [0.849036, 1.891425], [0.567040, 1.787799], [0.425240, 1.739744], [0.283582, 1.694066] | 1e-5 abs | FAIL |
| T_e2_over_6e4 range at N = 20, 30, 40, 60 | [0.851141, 1.061295], [0.834306, 1.061624], [0.826378, 1.063099], [0.818799, 1.063431] | 1e-5 abs | FAIL |
| T_max (at the equal-stacks state) at N = 20, 40, 60 | 26.5324, 106.3099, 239.2719 | 1e-4 abs | FAIL |
| e09_solvers rel_err | below 1e-10 for every method and N | | FAIL |
| amg_cg iters | 9 to 14 for N = 40 ... 150, growing slowly | | WARN |
| amg_cg setup_s + solve_s against n | slope of log time vs log n between 0.8 and 1.4 | | WARN |
| cholmod nnz_factor against n (N = 60 to 100) | slope between 1.25 and 1.6 (theory n^(4/3)); 8.0e6, 2.76e7, 7.45e7 at N = 60, 80, 100 | 10% | WARN |
| cholmod flops against n (N = 60 to 100) | slope 2.09 (theory n^2); 5.2907e9, 3.1766e10, 1.4145e11 at N = 60, 80, 100 (Linux, independent builder; nnz identical to the Mac's) | slope in [1.9, 2.3]; each value within 1% | FAIL |
| cholmod setup_s against n (N = 60 to 100) | Mac 1.66 (flop rate 9.4 to 18.2 GFLOP/s), Linux 2.1 (3.0 GFLOP/s) | slope in [1.4, 2.6] | WARN |
| splu (COLAMD) peak memory vs cholmod at N = 60 | splu several times larger (about 1 GB vs 0.2 GB here) | | WARN |
| e09_big_stack P (four players) at N = 8, 10, 12, 16, 20, 24, 30, 40, 50 | 5.577821161394e-03 (= 11017/1975144), 1.571739438951e-03, 5.568973643914e-04, 1.080249783339e-04, 3.022376155052e-05, 1.066742330410e-05, 2.980150693207e-06, 5.753800975152e-07, 1.606108031016e-07 | 1e-9 relative | FAIL |
| P at N = 60, 80, 100, 120, 160, 200 | 5.661341422530e-08, 1.092193169790e-08, 3.047622700924e-09, 1.074036901898e-09, 2.071632598328e-10, 5.780085237687e-11 | 1e-8 relative | FAIL |
| local_slope (four players) | increasing in N; 5.6762 (8 to 10), 5.7121 (20 to 24), 5.7171 (30 to 40), 5.7198 (60 to 80), 5.7201 (80 to 100), 5.7205 (120 to 160), 5.7206 (160 to 200) | 1e-3 abs | FAIL |
| local_slope (three players) | 3.000 | 1e-3 abs | FAIL |
| P N^3, three players, N >= 80 | 9.11959 | 1e-5 relative | FAIL |
| alpha_extrapolated (four players) | 5.720688 (cone eigenvalue lambda = 38.446962, Project chat FEM); the 1/N^2 fit of the Nov 11 slopes gives 5.720687 | 1e-4 | FAIL |
| n_lumped / n_full | 41/165 at N = 12, 204/969 at N = 20, 27353/156849 at N = 100; ratio tends to 1/6 | exact | FAIL |
| seconds for the lumped CHOLMOD solve at N = 200 | under 2 min | | WARN |

Reference timings from the validation machine (a 2-core Linux container, one thread; an Apple Silicon
laptop should be similar or faster): AMG-CG at N = 150 (n = 540k) 2 s setup + 2.6 s solve, 0.8 GB;
CHOLMOD at N = 80 14 s, 0.65 GB, at N = 100 73 s, 1.7 GB, at N = 120 killed for lack of memory (about
4.5 GB was free); SuperLU COLAMD at N = 60 6 s, 1 GB (about 2 GB at N = 80 per the prototype); lumped
chain at N = 160 with CHOLMOD 16 s and 0.74 GB, against 80 s and 4.1 GB with SuperLU COLAMD.

## Red flags (bring these to the Project chat)

- A (6 e4) differs from e2 at all: the move list or the 1/12 weight is wrong.
- Lumped and full answers differ beyond 1e-13, or diag(weights) A_L is not symmetric: the orbit sizes
  or the sorting is wrong (the usual bug: sorting all four coordinates instead of the first three).
- The four-player local slope drifting below 5.7 or above 5.73, or the three-player slope not 3.
- Any direct solve that would exceed about 60% of free memory: stop it; do not let the laptop swap.
- AMG-CG iteration counts growing like N rather than staying near 10.

## Done when

- [ ] `pytest tests/c00_core tests/c09_four` passes.
- [ ] The four CSVs and both figures exist.
- [ ] `python checks/check_c09.py` prints every row PASS (WARN allowed only on WARN rows); report saved
  to `results/c09_report.md`, with the machine's free memory at the start of the run.
- [ ] `notes/decisions.md` has a chunk 9 entry (which runs were skipped for memory and why); committed as
  "chunk 9: four players".

## Paste back into the Project chat

`results/c09_report.md` and both figures.
