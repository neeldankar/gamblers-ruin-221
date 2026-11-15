# Chunk 11: final report

Results: `results`; code at git 2ef9083; HEAD ee2db14; generated 2026-11-14T20:45:35.

## Summary

| Chunk | Script | PASS | WARN | FAIL | FLAG | Exit |
|---|---|---|---|---|---|---|
| c01 | check_c01.py | 9 | 0 | 0 | 0 | 0 |
| c02 | check_c02.py | 16 | 1 | 0 | 0 | 0 |
| c03 | check_c03.py | 16 | 0 | 0 | 0 | 0 |
| c04 | check_c04.py | 33 | 0 | 0 | 0 | 0 |
| c05 | check_c05.py | 28 | 0 | 0 | 0 | 0 |
| c06 | check_c06.py | 10 | 0 | 0 | 0 | 0 |
| c07 | check_c07.py | 47 | 0 | 0 | 0 | 0 |
| c08 | check_c08.py | 18 | 0 | 0 | 0 | 0 |
| c09 | check_c09.py | 22 | 0 | 0 | 1 | 0 |
| c10 | check_c10.py | 30 | 0 | 0 | 0 | 0 |
| c11 | check_all.py | 5 | 4 | 0 | 0 |  |

FLAG lines are the chunk specs' red-flag checks (not counted as FAIL).

## Chunk 11 expected results

| Check | Expected | Observed | Status |
|---|---|---|---|
| every experiment exits 0 | yes | 20 of 20 full runs at git 2ef9083 exit 0 | PASS |
| every check script: no FAIL lines | all PASS or WARN | 0 FAIL lines | PASS |
| WARN lines | only timing rows and rows the chunk specs mark as machine-dependent | 1 WARN lines, listed below for review | WARN |
| one git hash across all CSVs | yes | 33 CSVs, hashes ['2ef9083'] | PASS |
| CSV hashes equal the code hash (last commit that touched gr/ or experiments/) | yes | code at git 2ef9083; CSV hashes ['2ef9083'] | PASS |
| total run time | 2-4 h (sum of the chunk compute times with 5 repeats) | 1.39 h | WARN |
| peak memory | under 4 GB without chunk 9's `--big` | 6375 MB (e04_errors); e02_direct_big (not counted): 4808 MB | WARN |
| results equal to the per-chunk runs | fill counts, iteration counts and errors identical or within the per-chunk tolerances; only times move (the values are judged by the per-chunk check scripts, which run on these CSVs; this row lists what moved, for the Project chat) | 33 columns changed by more than 1e-12; see the changes table (for review in the Project chat) | WARN |
| no row missing against the baseline run | yes | no rows or CSVs removed | PASS |

## WARN, FAIL and FLAG lines

- c02 **WARN** setup_time, cholmod amd, N = 1200: 1.90 s
- c09 **FLAG** direct solves stopped by the memory rules (60% of free memory, 3 GB projected factor): splu N=100: skipped: projected factor 3.5 GB > 3 GB; splu_mmd N=100: killed: rss over 4.7 GB (60% of free memory)

## Run log

Last row per script from `results/run_all_log.csv`.

| script | start | end | seconds | exit_code | peak_mb | free_mem_mb_start | quick | repeats | git_hash |
|---|---|---|---|---|---|---|---|---|---|
| e01_conditioning | 2026-11-14T11:08:58 | 2026-11-14T11:09:04 | 6.3 | 0 | 348.5 | 3881 | False | 5 | 2ef9083 |
| e02_direct | 2026-11-14T11:09:04 | 2026-11-14T11:20:48 | 703.7 | 0 | 4342.1 | 3811 | False | 5 | 2ef9083 |
| e03_convergence | 2026-11-14T11:20:48 | 2026-11-14T11:20:52 | 4.0 | 0 | 237.6 | 11399 | False | 5 | 2ef9083 |
| e03_krylov | 2026-11-14T11:20:52 | 2026-11-14T11:25:18 | 266.3 | 0 | 2935.5 | 11213 | False | 5 | 2ef9083 |
| e04_condition | 2026-11-14T11:25:18 | 2026-11-14T11:25:28 | 10.3 | 0 | 1608.3 | 10247 | False | 5 | 2ef9083 |
| e04_errors | 2026-11-14T11:25:28 | 2026-11-14T11:28:49 | 200.8 | 0 | 6374.8 | 10164 | False | 5 | 2ef9083 |
| e04_mechanism | 2026-11-14T11:28:49 | 2026-11-14T11:29:33 | 43.7 | 0 | 520.0 | 8777 | False | 5 | 2ef9083 |
| e04_perturbation | 2026-11-14T11:29:33 | 2026-11-14T11:29:34 | 1.1 | 0 | 94.6 | 8753 | False | 5 | 2ef9083 |
| e05_iterations | 2026-11-14T11:29:34 | 2026-11-14T11:31:03 | 89.1 | 0 | 786.8 | 8717 | False | 5 | 2ef9083 |
| e05_omega_sweep | 2026-11-14T11:31:03 | 2026-11-14T11:31:51 | 48.0 | 0 | 260.2 | 8671 | False | 5 | 2ef9083 |
| e05_sor_spectra | 2026-11-14T11:31:51 | 2026-11-14T11:35:13 | 202.0 | 0 | 2585.0 | 8686 | False | 5 | 2ef9083 |
| e06_fft | 2026-11-14T11:35:13 | 2026-11-14T11:36:27 | 73.3 | 0 | 1766.3 | 8572 | False | 5 | 2ef9083 |
| e07_baselines | 2026-11-14T11:36:27 | 2026-11-14T11:37:38 | 71.9 | 0 | 3358.7 | 8555 | False | 5 | 2ef9083 |
| e07_fft_check | 2026-11-14T11:37:39 | 2026-11-14T11:37:53 | 14.0 | 0 | 2547.9 | 8572 | False | 5 | 2ef9083 |
| e07_fixes | 2026-11-14T11:37:53 | 2026-11-14T12:12:13 | 2060.2 | 0 | 5432.3 | 8555 | False | 5 | 2ef9083 |
| e07_floor | 2026-11-14T12:12:13 | 2026-11-14T12:17:15 | 302.5 | 0 | 2094.1 | 10183 | False | 5 | 2ef9083 |
| e07_structured | 2026-11-14T12:17:15 | 2026-11-14T12:19:01 | 105.2 | 0 | 1309.1 | 8908 | False | 5 | 2ef9083 |
| e08_icm | 2026-11-14T12:19:01 | 2026-11-14T12:19:07 | 6.3 | 0 | 786.8 | 8931 | False | 5 | 2ef9083 |
| e09_four | 2026-11-14T12:19:07 | 2026-11-14T12:31:52 | 765.0 | 0 | 5008.5 | 8164 | False | 5 | 2ef9083 |
| e10_extras | 2026-11-14T12:31:52 | 2026-11-14T12:32:26 | 33.5 | 0 | 664.1 | 9003 | False | 5 | 2ef9083 |
| e02_direct_big | 2026-11-14T12:50:11 | 2026-11-14T12:52:02 | 111.3 | 0 | 4808.0 | 3037 | False | 5 | 2ef9083 |

## Machine

- platform: macOS-15.6.1-arm64-arm-64bit-Mach-O
- machine: arm64
- python: 3.13.18
- numpy: 2.5.4
- scipy: 1.18.1
- omp_num_threads: unset
- total_ram_gb: 16
- scikit-sparse: 0.5.0
- pyamg: 5.3.0
- numba: 0.68.1
- python-flint: 0.9.0
- pandas: 3.1.1
- matplotlib: 3.11.2
- OMP_NUM_THREADS: unset
- OPENBLAS_NUM_THREADS: unset
- VECLIB_MAXIMUM_THREADS: unset

## Changes against the previous run (git 5de66f4)

Each CSV in `results` against `git show 5de66f4:results/<name>.csv`. Timings, memory, git_hash and timestamp are left out. Rows are matched by N, the text columns that name a row, and the occurrence number within that key. Numbers: largest |new - old| / |old|. Text and booleans: rows that differ. Not judged here.

### Changed by more than 1e-12

| CSV | Column | Rows | Largest change | Where |
|---|---|---|---|---|
| e03_convergence.csv | relres | 1726 | 1.10e-03 | N=320, kind=amg, rhs=order321, occurrence=7 |
| e03_convergence.csv | err_A | 1726 | 4.72e-04 | N=320, kind=amg, rhs=order321, occurrence=10 |
| e03_convergence.csv | err_inf | 1726 | 8.50e-04 | N=320, kind=amg, rhs=random, occurrence=12 |
| e03_krylov.csv | iterations | 160 | 6.67e-02 | N=640, kind=amg, rhs=out_first, occurrence=0 |
| e03_krylov.csv | iterations_over_N | 160 | 6.67e-02 | N=640, kind=amg, rhs=out_first, occurrence=0 |
| e03_krylov.csv | final_relres | 160 | 1.27e+00 | N=640, kind=amg, rhs=out_first, occurrence=0 |
| e03_krylov.csv | forward_error | 160 | 2.21e+00 | N=640, kind=amg, rhs=out_first, occurrence=0 |
| e04_errors.csv | rel_err_tiny | 124 | 4.55e-01 | N=20, method=cg, kind=amg, reference=exact, occurrence=4 |
| e04_errors.csv | max_rel_err | 124 | 1.46e-01 | N=640, method=cg, kind=amg, reference=direct, occurrence=2 |
| e04_errors.csv | normwise_rel_err | 124 | 1.61e-01 | N=640, method=cg, kind=amg, reference=direct, occurrence=2 |
| e04_errors.csv | normwise_backward_error | 124 | 2.00e-01 | N=20, method=cg, kind=amg, reference=exact, occurrence=4 |
| e04_errors.csv | componentwise_backward_error | 124 | 1.26e-01 | N=640, method=cg, kind=amg, reference=direct, occurrence=2 |
| e04_errors.csv | ratio_tiny_to_prediction | 124 | 4.55e-01 | N=20, method=cg, kind=amg, reference=exact, occurrence=4 |
| e04_errors.csv | max_err_over_bound | 124 | 2.30e-01 | N=20, method=cg, kind=amg, reference=exact, occurrence=4 |
| e04_errors.csv | value_tiny | 124 | 2.84e-05 | N=1280, method=cg, kind=amg, reference=direct, occurrence=0 |
| e04_errors.csv | signed_err_tiny | 124 | 4.55e-01 | N=20, method=cg, kind=amg, reference=exact, occurrence=4 |
| e04_errors.csv | solver_err_tiny | 124 | 4.37e-01 | N=20, method=cg, kind=amg, reference=exact, occurrence=4 |
| e04_errors.csv | max_solver_err | 124 | 1.85e-01 | N=20, method=cg, kind=amg, reference=exact, occurrence=4 |
| e07_fixes.csv | rel_err_tiny | 111 | 4.55e-01 | N=20, method=cg_componentwise, kind=amg, reference=exact, occurrence=1 |
| e07_fixes.csv | max_rel_err | 111 | 6.67e-02 | N=20, method=cg_componentwise, kind=amg, reference=exact, occurrence=1 |
| e07_fixes.csv | max_rel_err_in_u | 111 | 6.67e-02 | N=20, method=cg_componentwise, kind=amg, reference=exact, occurrence=1 |
| e07_fixes.csv | omega | 111 | 1.41e-01 | N=1280, method=cg_componentwise, kind=amg, reference=refined, occurrence=1 |
| e07_fixes.csv | err_vs_stored_tiny | 111 | 4.50e+00 | N=80, method=cg_componentwise, kind=amg, reference=exact, occurrence=1 |
| e07_fixes.csv | max_err_vs_stored | 111 | 3.00e-01 | N=80, method=cg_componentwise, kind=amg, reference=exact, occurrence=1 |
| e07_fixes.csv | signed_err_tiny | 111 | 4.55e-01 | N=20, method=cg_componentwise, kind=amg, reference=exact, occurrence=1 |
| e07_floor.csv | min_omega | 15 | 6.76e-01 | N=1280, kind=amg, occurrence=0 |
| e07_floor.csv | min_omega_in_u | 15 | 6.76e-01 | N=1280, kind=amg, occurrence=0 |
| e07_floor.csv | k_at_min | 15 | 8.00e-02 | N=320, kind=amg, occurrence=0 |
| e07_floor.csv | k_at_min_over_k10 | 15 | 8.00e-02 | N=320, kind=amg, occurrence=0 |
| e07_floor.csv | final_omega_in_u | 15 | 7.34e-01 | N=1280, kind=amg, occurrence=0 |
| e09_solvers.csv | nnz_factor | 23 | inf | N=100, method=splu_mmd, occurrence=0 |
| e09_solvers.csv | rel_err | 23 | inf | N=100, method=splu_mmd, occurrence=0 |
| e09_solvers.csv | status | 23 | 21 rows differ (text) | N=20, method=splu, occurrence=0 |

### Rows, columns and CSVs added or removed

- e07_fixes.csv: new columns ['corrections']
- e07_floor.csv: new columns ['max_x_corner_ratio', 'max_x_inf_ratio']

### Every compared column

| CSV | Column | Rows | Largest change | Where | Changed |
|---|---|---|---|---|---|
| e01_conditioning.csv | n | 10 | 0.00e+00 |  |  |
| e01_conditioning.csv | lambda_min_formula | 10 | 0.00e+00 |  |  |
| e01_conditioning.csv | lambda_min_eigsh | 10 | 1.05e-15 | N=320, occurrence=0 |  |
| e01_conditioning.csv | lambda_max_formula | 10 | 0.00e+00 |  |  |
| e01_conditioning.csv | kappa2 | 10 | 0.00e+00 |  |  |
| e01_conditioning.csv | kappa2_over_N2 | 10 | 0.00e+00 |  |  |
| e01_conditioning.csv | kappa_inf | 10 | 0.00e+00 |  |  |
| e01_conditioning.csv | kappa_inf_over_N2 | 10 | 0.00e+00 |  |  |
| e01_conditioning.csv | jacobi_rate | 10 | 0.00e+00 |  |  |
| e02_direct.csv | n | 64 | 0.00e+00 |  |  |
| e02_direct.csv | nnz_A | 64 | 0.00e+00 |  |  |
| e02_direct.csv | nnz_factor | 64 | 0.00e+00 |  |  |
| e02_direct.csv | nnz_chol_equiv | 64 | 0.00e+00 |  |  |
| e02_direct.csv | fill_ratio | 64 | 0.00e+00 |  |  |
| e02_direct.csv | flops | 64 | 0.00e+00 |  |  |
| e02_direct.csv | forward_error | 64 | 0.00e+00 |  |  |
| e02_direct.csv | kappa_inf | 64 | 0.00e+00 |  |  |
| e02_direct.csv | err_over_kappa_u | 64 | 0.00e+00 |  |  |
| e02_direct.csv | backward_error | 64 | 0.00e+00 |  |  |
| e02_direct_big.csv | n | 2 | 0.00e+00 |  |  |
| e02_direct_big.csv | nnz_A | 2 | 0.00e+00 |  |  |
| e02_direct_big.csv | nnz_factor | 2 | 0.00e+00 |  |  |
| e02_direct_big.csv | nnz_chol_equiv | 2 | 0.00e+00 |  |  |
| e02_direct_big.csv | fill_ratio | 2 | 0.00e+00 |  |  |
| e02_direct_big.csv | flops | 2 | 0.00e+00 |  |  |
| e02_direct_big.csv | forward_error | 2 | 0.00e+00 |  |  |
| e02_direct_big.csv | kappa_inf | 2 | 0.00e+00 |  |  |
| e02_direct_big.csv | err_over_kappa_u | 2 | 0.00e+00 |  |  |
| e02_direct_big.csv | backward_error | 2 | 0.00e+00 |  |  |
| e03_convergence.csv | n | 1726 | 0.00e+00 |  |  |
| e03_convergence.csv | k | 1726 | 0.00e+00 |  |  |
| e03_convergence.csv | relres | 1726 | 1.10e-03 | N=320, kind=amg, rhs=order321, occurrence=7 | **changed** |
| e03_convergence.csv | err_A | 1726 | 4.72e-04 | N=320, kind=amg, rhs=order321, occurrence=10 | **changed** |
| e03_convergence.csv | err_inf | 1726 | 8.50e-04 | N=320, kind=amg, rhs=random, occurrence=12 | **changed** |
| e03_convergence.csv | chebyshev | 1726 | 0.00e+00 |  |  |
| e03_krylov.csv | n | 160 | 0.00e+00 |  |  |
| e03_krylov.csv | iterations | 160 | 6.67e-02 | N=640, kind=amg, rhs=out_first, occurrence=0 | **changed** |
| e03_krylov.csv | bound | 160 | 0.00e+00 |  |  |
| e03_krylov.csv | iterations_over_N | 160 | 6.67e-02 | N=640, kind=amg, rhs=out_first, occurrence=0 | **changed** |
| e03_krylov.csv | final_relres | 160 | 1.27e+00 | N=640, kind=amg, rhs=out_first, occurrence=0 | **changed** |
| e03_krylov.csv | forward_error | 160 | 2.21e+00 | N=640, kind=amg, rhs=out_first, occurrence=0 | **changed** |
| e03_krylov.csv | kappa2 | 160 | 0.00e+00 |  |  |
| e04_condition.csv | n | 16 | 0.00e+00 |  |  |
| e04_condition.csv | argmin_state | 16 | 0 rows differ (text) |  |  |
| e04_condition.csv | x_tiny | 16 | 0.00e+00 |  |  |
| e04_condition.csv | N3_x_tiny | 16 | 0.00e+00 |  |  |
| e04_condition.csv | cond_tiny | 16 | 0.00e+00 |  |  |
| e04_condition.csv | cond_tiny_over_N2 | 16 | 0.00e+00 |  |  |
| e04_condition.csv | cond_max_over_N2 | 16 | 0.00e+00 |  |  |
| e04_condition.csv | argmax_cond_state | 16 | 0 rows differ (text) |  |  |
| e04_condition.csv | ET_tiny_over_N2 | 16 | 0.00e+00 |  |  |
| e04_condition.csv | omega_direct | 16 | 0.00e+00 |  |  |
| e04_condition.csv | omega_over_u | 16 | 0.00e+00 |  |  |
| e04_condition.csv | aposteriori_bound | 16 | 0.00e+00 |  |  |
| e04_condition.csv | data_term_tiny | 16 | 0.00e+00 |  |  |
| e04_condition.csv | data_term_over_N2u | 16 | 0.00e+00 |  |  |
| e04_errors.csv | n | 124 | 0.00e+00 |  |  |
| e04_errors.csv | rtol | 124 | 0.00e+00 |  |  |
| e04_errors.csv | iterations | 124 | 0.00e+00 |  |  |
| e04_errors.csv | converged | 124 | 0.00e+00 |  |  |
| e04_errors.csv | rel_err_tiny | 124 | 4.55e-01 | N=20, method=cg, kind=amg, reference=exact, occurrence=4 | **changed** |
| e04_errors.csv | max_rel_err | 124 | 1.46e-01 | N=640, method=cg, kind=amg, reference=direct, occurrence=2 | **changed** |
| e04_errors.csv | argmax_rel_err_state | 124 | 0 rows differ (text) |  |  |
| e04_errors.csv | normwise_rel_err | 124 | 1.61e-01 | N=640, method=cg, kind=amg, reference=direct, occurrence=2 | **changed** |
| e04_errors.csv | normwise_backward_error | 124 | 2.00e-01 | N=20, method=cg, kind=amg, reference=exact, occurrence=4 | **changed** |
| e04_errors.csv | componentwise_backward_error | 124 | 1.26e-01 | N=640, method=cg, kind=amg, reference=direct, occurrence=2 | **changed** |
| e04_errors.csv | cond_tiny | 124 | 0.00e+00 |  |  |
| e04_errors.csv | ratio_tiny_to_prediction | 124 | 4.55e-01 | N=20, method=cg, kind=amg, reference=exact, occurrence=4 | **changed** |
| e04_errors.csv | max_err_over_bound | 124 | 2.30e-01 | N=20, method=cg, kind=amg, reference=exact, occurrence=4 | **changed** |
| e04_errors.csv | value_tiny | 124 | 2.84e-05 | N=1280, method=cg, kind=amg, reference=direct, occurrence=0 | **changed** |
| e04_errors.csv | data_term_tiny | 124 | 0.00e+00 |  |  |
| e04_errors.csv | signed_err_tiny | 124 | 4.55e-01 | N=20, method=cg, kind=amg, reference=exact, occurrence=4 | **changed** |
| e04_errors.csv | solver_err_tiny | 124 | 4.37e-01 | N=20, method=cg, kind=amg, reference=exact, occurrence=4 | **changed** |
| e04_errors.csv | max_solver_err | 124 | 1.85e-01 | N=20, method=cg, kind=amg, reference=exact, occurrence=4 | **changed** |
| e04_errors.csv | at_reference_accuracy | 124 | 0 rows differ (text) |  |  |
| e04_mechanism_rhs.csv | rtol | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | iterations | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | converged | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | smallest_state | 40 | 0 rows differ (text) |  |  |
| e04_mechanism_rhs.csv | x_smallest | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | cond_smallest | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | rel_err_smallest | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | ratio_to_cond_rtol | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | normwise_rel_err | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | abs_err_smallest | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | abs_err_median | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | abs_err_max | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | x_max | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | true_relres | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | g_norm | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | residual_bound_abs | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | median_ratio_all_states | 40 | 0.00e+00 |  |  |
| e04_mechanism_rhs.csv | q90_ratio_all_states | 40 | 0.00e+00 |  |  |
| e04_mechanism_states.csv | rtol | 12585 | 0.00e+00 |  |  |
| e04_mechanism_states.csv | x1 | 12585 | 0.00e+00 |  |  |
| e04_mechanism_states.csv | x2 | 12585 | 0.00e+00 |  |  |
| e04_mechanism_states.csv | x3 | 12585 | 0.00e+00 |  |  |
| e04_mechanism_states.csv | x | 12585 | 0.00e+00 |  |  |
| e04_mechanism_states.csv | abs_err | 12585 | 0.00e+00 |  |  |
| e04_mechanism_states.csv | rel_err | 12585 | 0.00e+00 |  |  |
| e04_mechanism_states.csv | cond | 12585 | 0.00e+00 |  |  |
| e04_mechanism_states.csv | ratio | 12585 | 0.00e+00 |  |  |
| e04_perturbation.csv | n | 12 | 0.00e+00 |  |  |
| e04_perturbation.csv | eps | 12 | 0.00e+00 |  |  |
| e04_perturbation.csv | eps_cond_max | 12 | 0.00e+00 |  |  |
| e04_perturbation.csv | worst_ratio_min | 12 | 0.00e+00 |  |  |
| e04_perturbation.csv | worst_ratio_max | 12 | 0.00e+00 |  |  |
| e04_perturbation.csv | random_max_ratio | 12 | 0.00e+00 |  |  |
| e04_perturbation.csv | draws | 12 | 0.00e+00 |  |  |
| e05_iterations.csv | n | 51 | 0.00e+00 |  |  |
| e05_iterations.csv | omega | 51 | 0.00e+00 |  |  |
| e05_iterations.csv | iterations | 51 | 0.00e+00 |  |  |
| e05_iterations.csv | converged | 51 | 0.00e+00 |  |  |
| e05_iterations.csv | final_residual | 51 | 0.00e+00 |  |  |
| e05_iterations.csv | predicted_iterations | 51 | 0.00e+00 |  |  |
| e05_iterations.csv | young_predicted_iterations | 51 | 0.00e+00 |  |  |
| e05_iterations.csv | rate_measured | 51 | 0.00e+00 |  |  |
| e05_iterations.csv | exponent_ratio | 51 | 0.00e+00 |  |  |
| e05_iterations.csv | rho_jacobi | 51 | 0.00e+00 |  |  |
| e05_iterations.csv | kappa2 | 51 | 0.00e+00 |  |  |
| e05_iterations.csv | forward_error | 51 | 0.00e+00 |  |  |
| e05_omega_sweep.csv | n | 273 | 0.00e+00 |  |  |
| e05_omega_sweep.csv | omega | 273 | 0.00e+00 |  |  |
| e05_omega_sweep.csv | offset | 273 | 0.00e+00 |  |  |
| e05_omega_sweep.csv | omega_star | 273 | 0.00e+00 |  |  |
| e05_omega_sweep.csv | iterations_ones | 273 | 0.00e+00 |  |  |
| e05_omega_sweep.csv | iterations_random | 273 | 0.00e+00 |  |  |
| e05_omega_sweep.csv | rho_dense | 273 | 0.00e+00 |  |  |
| e05_sor_spectra.csv | n | 13 | 0.00e+00 |  |  |
| e05_sor_spectra.csv | omega_star | 13 | 0.00e+00 |  |  |
| e05_sor_spectra.csv | rho_jacobi_formula | 13 | 0.00e+00 |  |  |
| e05_sor_spectra.csv | rho_jacobi_dense | 13 | 0.00e+00 |  |  |
| e05_sor_spectra.csv | rho_gs_dense | 13 | 0.00e+00 |  |  |
| e05_sor_spectra.csv | gs_gap | 13 | 0.00e+00 |  |  |
| e05_sor_spectra.csv | rho_sor_dense | 13 | 0.00e+00 |  |  |
| e05_sor_spectra.csv | law_value | 13 | 0.00e+00 |  |  |
| e05_sor_spectra.csv | young_value | 13 | 0.00e+00 |  |  |
| e05_sor_spectra.csv | law_relerr | 13 | 0.00e+00 |  |  |
| e05_sor_spectra.csv | sor_over_young | 13 | 0.00e+00 |  |  |
| e06_fft.csv | n | 6 | 0.00e+00 |  |  |
| e06_fft.csv | P | 6 | 0.00e+00 |  |  |
| e06_fft.csv | fwd_err_t | 6 | 0.00e+00 |  |  |
| e06_fft.csv | kappa2 | 6 | 0.00e+00 |  |  |
| e06_fft.csv | fwd_err_over_eps_kappa | 6 | 0.00e+00 |  |  |
| e06_fft.csv | resid_random | 6 | 0.00e+00 |  |  |
| e06_fft.csv | err_vs_splu | 6 | 0.00e+00 |  |  |
| e06_fft.csv | sum_out_first_err | 6 | 0.00e+00 |  |  |
| e06_fft.csv | min_p123 | 6 | 0.00e+00 |  |  |
| e06_fft.csv | p123_reldiff | 6 | 0.00e+00 |  |  |
| e06_fft.csv | min_state | 6 | 0 rows differ (text) |  |  |
| e07_baselines.csv | n | 61 | 0.00e+00 |  |  |
| e07_baselines.csv | own_err_tiny | 61 | 0.00e+00 |  |  |
| e07_baselines.csv | own_err_over_N2u | 61 | 0.00e+00 |  |  |
| e07_baselines.csv | max_own_err_in_u | 61 | 0.00e+00 |  |  |
| e07_baselines.csv | true_err_tiny | 61 | 0.00e+00 |  |  |
| e07_baselines.csv | true_err_over_N2u | 61 | 0.00e+00 |  |  |
| e07_baselines.csv | max_true_err_in_u | 61 | 0.00e+00 |  |  |
| e07_baselines.csv | max_true_err_in_ulp | 61 | 0.00e+00 |  |  |
| e07_baselines.csv | data_term_tiny | 61 | 0.00e+00 |  |  |
| e07_fft_check.csv | n | 19 | 0.00e+00 |  |  |
| e07_fft_check.csv | rel_err_smallest | 19 | 0.00e+00 |  |  |
| e07_fft_check.csv | max_rel_err | 19 | 0.00e+00 |  |  |
| e07_fft_check.csv | normwise_rel_err | 19 | 0.00e+00 |  |  |
| e07_fft_check.csv | data_term_smallest | 19 | 0.00e+00 |  |  |
| e07_fft_check.csv | signed_err_smallest | 19 | 0.00e+00 |  |  |
| e07_fixes.csv | n | 111 | 0.00e+00 |  |  |
| e07_fixes.csv | param | 111 | 0.00e+00 |  |  |
| e07_fixes.csv | iterations_or_steps | 111 | 0.00e+00 |  |  |
| e07_fixes.csv | converged | 111 | 0.00e+00 |  |  |
| e07_fixes.csv | rel_err_tiny | 111 | 4.55e-01 | N=20, method=cg_componentwise, kind=amg, reference=exact, occurrence=1 | **changed** |
| e07_fixes.csv | max_rel_err | 111 | 6.67e-02 | N=20, method=cg_componentwise, kind=amg, reference=exact, occurrence=1 | **changed** |
| e07_fixes.csv | max_rel_err_in_u | 111 | 6.67e-02 | N=20, method=cg_componentwise, kind=amg, reference=exact, occurrence=1 | **changed** |
| e07_fixes.csv | omega | 111 | 1.41e-01 | N=1280, method=cg_componentwise, kind=amg, reference=refined, occurrence=1 | **changed** |
| e07_fixes.csv | cond_tiny | 111 | 0.00e+00 |  |  |
| e07_fixes.csv | data_term_tiny | 111 | 0.00e+00 |  |  |
| e07_fixes.csv | err_vs_stored_tiny | 111 | 4.50e+00 | N=80, method=cg_componentwise, kind=amg, reference=exact, occurrence=1 | **changed** |
| e07_fixes.csv | max_err_vs_stored | 111 | 3.00e-01 | N=80, method=cg_componentwise, kind=amg, reference=exact, occurrence=1 | **changed** |
| e07_fixes.csv | signed_err_tiny | 111 | 4.55e-01 | N=20, method=cg_componentwise, kind=amg, reference=exact, occurrence=1 | **changed** |
| e07_floor.csv | check_every | 15 | 0.00e+00 |  |  |
| e07_floor.csv | iters_rtol_1e10 | 15 | 0.00e+00 |  |  |
| e07_floor.csv | maxiter | 15 | 0.00e+00 |  |  |
| e07_floor.csv | min_omega | 15 | 6.76e-01 | N=1280, kind=amg, occurrence=0 | **changed** |
| e07_floor.csv | min_omega_in_u | 15 | 6.76e-01 | N=1280, kind=amg, occurrence=0 | **changed** |
| e07_floor.csv | k_at_min | 15 | 8.00e-02 | N=320, kind=amg, occurrence=0 | **changed** |
| e07_floor.csv | k_at_min_over_k10 | 15 | 8.00e-02 | N=320, kind=amg, occurrence=0 | **changed** |
| e07_floor.csv | final_omega_in_u | 15 | 7.34e-01 | N=1280, kind=amg, occurrence=0 | **changed** |
| e07_structured.csv | n | 7 | 0.00e+00 |  |  |
| e07_structured.csv | structured_random_max | 7 | 0.00e+00 |  |  |
| e07_structured.csv | structured_push | 7 | 0.00e+00 |  |  |
| e07_structured.csv | cond_max | 7 | 0.00e+00 |  |  |
| e07_structured.csv | two_n_minus_1 | 7 | 0.00e+00 |  |  |
| e07_structured.csv | eps | 7 | 0.00e+00 |  |  |
| e07_structured.csv | draws | 7 | 0.00e+00 |  |  |
| e07_structured.csv | structured_cond_tiny | 7 | 0.00e+00 |  |  |
| e07_structured.csv | structured_cond_max | 7 | 0.00e+00 |  |  |
| e07_structured.csv | structured_argmax_state | 7 | 0 rows differ (text) |  |  |
| e07_structured.csv | structured_cond_over_N | 7 | 0.00e+00 |  |  |
| e07_structured.csv | attained_tiny | 7 | 0.00e+00 |  |  |
| e07_structured.csv | attained_max_dev | 7 | 0.00e+00 |  |  |
| e07_structured.csv | coherent_tiny | 7 | 0.00e+00 |  |  |
| e07_structured.csv | drift_tiny | 7 | 0.00e+00 |  |  |
| e07_structured.csv | symmetric_cond_tiny | 7 | 0.00e+00 |  |  |
| e07_structured.csv | cond_tiny | 7 | 0.00e+00 |  |  |
| e08_icm_errors.csv | n | 5 | 0.00e+00 |  |  |
| e08_icm_errors.csv | max_abs_err_p2 | 5 | 0.00e+00 |  |  |
| e08_icm_errors.csv | argmax_state | 5 | 0 rows differ (text) |  |  |
| e08_icm_errors.csv | mean_abs_err_p2 | 5 | 0.00e+00 |  |  |
| e08_icm_errors.csv | max_rel_err_p3 | 5 | 0.00e+00 |  |  |
| e08_icm_errors.csv | argmax_rel_state_p3 | 5 | 0 rows differ (text) |  |  |
| e08_icm_errors.csv | max_equity_overrate | 5 | 0.00e+00 |  |  |
| e08_icm_errors.csv | overrate_state | 5 | 0 rows differ (text) |  |  |
| e08_icm_errors.csv | max_equity_underrate | 5 | 0.00e+00 |  |  |
| e08_icm_errors.csv | underrate_state | 5 | 0 rows differ (text) |  |  |
| e08_icm_errors.csv | identity_max_dev | 5 | 0.00e+00 |  |  |
| e08_icm_errors.csv | short_overrated_all | 5 | 0.00e+00 |  |  |
| e08_icm_errors.csv | long_underrated_all | 5 | 0.00e+00 |  |  |
| e08_icm_errors.csv | frac_middle_overrated | 5 | 0.00e+00 |  |  |
| e08_limit.csv | n | 7 | 0.00e+00 |  |  |
| e08_limit.csv | P123 | 7 | 0.00e+00 |  |  |
| e08_limit.csv | P132 | 7 | 0.00e+00 |  |  |
| e08_limit.csv | P213 | 7 | 0.00e+00 |  |  |
| e08_limit.csv | P231 | 7 | 0.00e+00 |  |  |
| e08_limit.csv | P312 | 7 | 0.00e+00 |  |  |
| e08_limit.csv | P321 | 7 | 0.00e+00 |  |  |
| e08_limit.csv | obs_order_min | 7 | 0.00e+00 |  |  |
| e08_limit.csv | obs_order_max | 7 | 0.00e+00 |  |  |
| e08_states_N120.csv | x1 | 7021 | 0.00e+00 |  |  |
| e08_states_N120.csv | x2 | 7021 | 0.00e+00 |  |  |
| e08_states_N120.csv | x3 | 7021 | 0.00e+00 |  |  |
| e08_states_N120.csv | dp2_player1 | 7021 | 0.00e+00 |  |  |
| e08_states_N120.csv | dequity_player1 | 7021 | 0.00e+00 |  |  |
| e08_wikipedia.csv | p1st | 12 | 0.00e+00 |  |  |
| e08_wikipedia.csv | p2nd | 12 | 0.00e+00 |  |  |
| e08_wikipedia.csv | p3rd | 12 | 0.00e+00 |  |  |
| e08_wikipedia.csv | equity | 12 | 0.00e+00 |  |  |
| e09_alpha.csv | players | 2 | 0.00e+00 |  |  |
| e09_alpha.csv | alpha_last_slope | 2 | 0.00e+00 |  |  |
| e09_alpha.csv | alpha_extrapolated | 2 | 0.00e+00 |  |  |
| e09_big_stack.csv | players | 21 | 0.00e+00 |  |  |
| e09_big_stack.csv | n_full | 21 | 0.00e+00 |  |  |
| e09_big_stack.csv | n_lumped | 21 | 0.00e+00 |  |  |
| e09_big_stack.csv | P | 21 | 0.00e+00 |  |  |
| e09_big_stack.csv | local_slope | 21 | 0.00e+00 |  |  |
| e09_big_stack.csv | solver | 21 | 0 rows differ (text) |  |  |
| e09_identities.csv | n | 5 | 0.00e+00 |  |  |
| e09_identities.csv | max_nnz_row | 5 | 0.00e+00 |  |  |
| e09_identities.csv | max_abs_A_minus_AT | 5 | 0.00e+00 |  |  |
| e09_identities.csv | e2_identity_relerr | 5 | 0.00e+00 |  |  |
| e09_identities.csv | win_maxerr | 5 | 0.00e+00 |  |  |
| e09_identities.csv | out_first_sum_maxerr | 5 | 0.00e+00 |  |  |
| e09_identities.csv | T_max | 5 | 0.00e+00 |  |  |
| e09_identities.csv | T_max_state | 5 | 0 rows differ (text) |  |  |
| e09_identities.csv | T_over_e4N_min | 5 | 0.00e+00 |  |  |
| e09_identities.csv | T_over_e4N_max | 5 | 0.00e+00 |  |  |
| e09_identities.csv | T_e2_over_6e4_min | 5 | 0.00e+00 |  |  |
| e09_identities.csv | T_e2_over_6e4_max | 5 | 0.00e+00 |  |  |
| e09_identities.csv | bounds_hold | 5 | 0.00e+00 |  |  |
| e09_solvers.csv | n | 23 | 0.00e+00 |  |  |
| e09_solvers.csv | nnz_factor | 23 | inf | N=100, method=splu_mmd, occurrence=0 | **changed** |
| e09_solvers.csv | flops | 23 | 0.00e+00 |  |  |
| e09_solvers.csv | iters | 23 | 0.00e+00 |  |  |
| e09_solvers.csv | rel_err | 23 | inf | N=100, method=splu_mmd, occurrence=0 | **changed** |
| e09_solvers.csv | status | 23 | 21 rows differ (text) | N=20, method=splu, occurrence=0 | **changed** |
| e10_bt_overflow.csv | value | 8 | 0.00e+00 |  |  |
| e10_bt_solvers.csv | iters | 48 | 0.00e+00 |  |  |
| e10_bt_solvers.csv | rel_residual_A | 48 | 0.00e+00 |  |  |
| e10_bt_solvers.csv | max_err_rel | 48 | 0.00e+00 |  |  |
| e10_bt_solvers.csv | max_err_lowpi_rel | 48 | 0.00e+00 |  |  |
| e10_bt_spectrum.csv | n | 5 | 0.00e+00 |  |  |
| e10_bt_spectrum.csv | max_abs_A_minus_AT | 5 | 0.00e+00 |  |  |
| e10_bt_spectrum.csv | rel_asym_S | 5 | 0.00e+00 |  |  |
| e10_bt_spectrum.csv | lam_min_S | 5 | 1.42e-15 | N=320, occurrence=0 |  |
| e10_bt_spectrum.csv | lam_max_S | 5 | 1.96e-14 | N=160, occurrence=0 |  |
| e10_bt_spectrum.csv | cond2_S | 5 | 1.93e-14 | N=160, occurrence=0 |  |
| e10_bt_spectrum.csv | gershgorin_lower | 5 | 0.00e+00 |  |  |
| e10_bt_spectrum.csv | log10_pi_range | 5 | 0.00e+00 |  |  |
| e10_bt_spectrum.csv | max_expected_rounds | 5 | 0.00e+00 |  |  |
| e10_bt_spectrum.csv | cond2_A_dense | 5 | 0.00e+00 |  |  |
| e10_bt_states_N80.csv | x1 | 3081 | 0.00e+00 |  |  |
| e10_bt_states_N80.csv | x2 | 3081 | 0.00e+00 |  |  |
| e10_bt_states_N80.csv | x3 | 3081 | 0.00e+00 |  |  |
| e10_bt_states_N80.csv | log_pi | 3081 | 0.00e+00 |  |  |
| e10_bt_states_N80.csv | err_cg_S | 3081 | 0.00e+00 |  |  |
| e10_bt_states_N80.csv | err_gmres_A | 3081 | 0.00e+00 |  |  |
| e10_degree_sweep.csv | order | 12 | 0.00e+00 |  |  |
| e10_degree_sweep.csv | degree | 12 | 0.00e+00 |  |  |
| e10_degree_sweep.csv | n_coef | 12 | 0.00e+00 |  |  |
| e10_degree_sweep.csv | cond_X | 12 | 0.00e+00 |  |  |
| e10_degree_sweep.csv | max_abs_resid | 12 | 0.00e+00 |  |  |
| e10_regression.csv | order | 12 | 0.00e+00 |  |  |
| e10_regression.csv | cond_X | 12 | 0.00e+00 |  |  |
| e10_regression.csv | cond_XtX | 12 | 0.00e+00 |  |  |
| e10_regression.csv | coef_relerr_vs_svd | 12 | 0.00e+00 |  |  |
| e10_regression.csv | resid_norm | 12 | 0.00e+00 |  |  |
| e10_regression.csv | max_abs_resid | 12 | 0.00e+00 |  |  |
| e10_regression.csv | fitted_maxdiff_vs_svd | 12 | 0.00e+00 |  |  |
