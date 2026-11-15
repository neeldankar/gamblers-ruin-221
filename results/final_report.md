# Chunk 11: final report

Results: `results`; code at git 5a73f57; HEAD 5a73f57; generated 2026-11-14T22:25:21.

## Summary

| Chunk | Script | PASS | WARN | FAIL | FLAG | Exit |
|---|---|---|---|---|---|---|
| c01 | check_c01.py | 9 | 0 | 0 | 0 | 0 |
| c02 | check_c02.py | 16 | 1 | 0 | 0 | 0 |
| c03 | check_c03.py | 16 | 0 | 0 | 0 | 0 |
| c04 | check_c04.py | 33 | 0 | 0 | 0 | 0 |
| c05 | check_c05.py | 28 | 0 | 0 | 0 | 0 |
| c06 | check_c06.py | 10 | 0 | 0 | 0 | 0 |
| c07 | check_c07.py | 49 | 0 | 0 | 0 | 0 |
| c08 | check_c08.py | 18 | 0 | 0 | 0 | 0 |
| c09 | check_c09.py | 25 | 0 | 0 | 0 | 0 |
| c10 | check_c10.py | 30 | 0 | 0 | 0 | 0 |
| c11 | check_all.py | 6 | 4 | 0 | 0 |  |

FLAG lines are the chunk specs' red-flag checks (not counted as FAIL).

## Chunk 11 expected results

| Check | Expected | Observed | Status |
|---|---|---|---|
| every experiment exits 0 | yes | 21 of 21 full runs at git 5a73f57 exit 0 | PASS |
| every check script: no FAIL lines | all PASS or WARN | 0 FAIL lines | PASS |
| WARN lines | only timing rows and rows the chunk specs mark as machine-dependent | 1 WARN lines, listed below for review | WARN |
| one git hash across all CSVs | yes | 34 CSVs, hashes ['5a73f57'] | PASS |
| CSV hashes equal the code hash (last commit that touched gr/ or experiments/) | yes | code at git 5a73f57; CSV hashes ['5a73f57'] | PASS |
| total run time | 2-4 h (sum of the chunk compute times with 5 repeats) | 1.33 h | WARN |
| peak memory | under 4 GB without chunk 9's `--big` | 6292 MB (e04_errors); e02_direct_big (not counted): 6441 MB | WARN |
| results equal to the per-chunk runs | fill counts, iteration counts and errors identical or within the per-chunk tolerances; only times move (the values are judged by the per-chunk check scripts, which run on these CSVs; this row lists what moved, for the Project chat) | 4 columns changed by more than 1e-12; see the changes table (for review in the Project chat) | WARN |
| no row missing against the baseline run | yes | no rows or CSVs removed | PASS |
| CSVs match the run manifest | every CSV listed for the latest successful run of each experiment exists with the recorded sha256; unlisted CSVs are named (WARN) | 34 CSVs listed for 22 experiments; all present with the recorded sha256 | PASS |

## WARN, FAIL and FLAG lines

- c02 **WARN** setup_time, cholmod amd, N = 1200: 1.90 s

## Run log

Last row per script from `results/run_all_log.csv`.

| script | start | end | seconds | exit_code | peak_mb | free_mem_mb_start | quick | repeats | git_hash |
|---|---|---|---|---|---|---|---|---|---|
| e01_conditioning | 2026-11-14T21:03:08 | 2026-11-14T21:03:14 | 5.9 | 0 | 388.9 | 9113 | False | 5 | 5a73f57 |
| e02_direct | 2026-11-14T21:03:14 | 2026-11-14T21:14:49 | 695.2 | 0 | 5655.9 | 8438 | False | 5 | 5a73f57 |
| e03_convergence | 2026-11-14T21:14:49 | 2026-11-14T21:14:53 | 3.8 | 0 | 226.1 | 12182 | False | 5 | 5a73f57 |
| e03_krylov | 2026-11-14T21:14:53 | 2026-11-14T21:19:19 | 266.1 | 0 | 2971.3 | 11821 | False | 5 | 5a73f57 |
| e04_condition | 2026-11-14T21:19:19 | 2026-11-14T21:19:30 | 10.3 | 0 | 1618.7 | 10682 | False | 5 | 5a73f57 |
| e04_errors | 2026-11-14T21:19:30 | 2026-11-14T21:22:51 | 200.9 | 0 | 6291.8 | 10682 | False | 5 | 5a73f57 |
| e04_mechanism | 2026-11-14T21:22:51 | 2026-11-14T21:23:32 | 41.6 | 0 | 513.7 | 9824 | False | 5 | 5a73f57 |
| e04_perturbation | 2026-11-14T21:23:32 | 2026-11-14T21:23:33 | 1.1 | 0 | 95.1 | 9818 | False | 5 | 5a73f57 |
| e05_iterations | 2026-11-14T21:23:33 | 2026-11-14T21:25:02 | 88.7 | 0 | 796.8 | 9777 | False | 5 | 5a73f57 |
| e05_omega_sweep | 2026-11-14T21:25:02 | 2026-11-14T21:25:50 | 48.0 | 0 | 253.0 | 9758 | False | 5 | 5a73f57 |
| e05_sor_spectra | 2026-11-14T21:25:50 | 2026-11-14T21:29:12 | 201.7 | 0 | 2547.2 | 9746 | False | 5 | 5a73f57 |
| e06_fft | 2026-11-14T21:29:12 | 2026-11-14T21:30:25 | 72.8 | 0 | 1723.4 | 9744 | False | 5 | 5a73f57 |
| e07_baselines | 2026-11-14T21:30:25 | 2026-11-14T21:31:37 | 71.9 | 0 | 3382.2 | 9733 | False | 5 | 5a73f57 |
| e07_fft_check | 2026-11-14T21:31:37 | 2026-11-14T21:31:51 | 14.1 | 0 | 2518.9 | 9759 | False | 5 | 5a73f57 |
| e07_fixes | 2026-11-14T21:31:51 | 2026-11-14T22:02:51 | 1860.2 | 0 | 5618.3 | 9726 | False | 5 | 5a73f57 |
| e07_floor | 2026-11-14T22:02:51 | 2026-11-14T22:07:48 | 297.3 | 0 | 2140.9 | 9318 | False | 5 | 5a73f57 |
| e07_structured | 2026-11-14T22:07:48 | 2026-11-14T22:09:33 | 105.1 | 0 | 1308.5 | 9239 | False | 5 | 5a73f57 |
| e08_icm | 2026-11-14T22:09:33 | 2026-11-14T22:09:40 | 6.3 | 0 | 808.6 | 9286 | False | 5 | 5a73f57 |
| e09_cone | 2026-11-14T22:09:40 | 2026-11-14T22:09:48 | 8.5 | 0 | 873.4 | 9278 | False | 5 | 5a73f57 |
| e09_four | 2026-11-14T22:09:48 | 2026-11-14T22:22:40 | 771.5 | 0 | 3937.0 | 9260 | False | 5 | 5a73f57 |
| e10_extras | 2026-11-14T22:22:40 | 2026-11-14T22:23:14 | 34.2 | 0 | 671.0 | 8671 | False | 5 | 5a73f57 |
| e02_direct_big | 2026-11-14T22:23:14 | 2026-11-14T22:24:52 | 97.4 | 0 | 6441.3 | 8636 | False | 5 | 5a73f57 |

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

## Changes against the previous run (git ee2db14)

Each CSV in `results` against `git show ee2db14:results/<name>.csv`. Timings, memory, git_hash and timestamp are left out. Rows are matched by N, the text columns that name a row, and the occurrence number within that key. Numbers: largest |new - old| / |old|. Text and booleans: rows that differ. Not judged here.

### Changed by more than 1e-12

| CSV | Column | Rows | Largest change | Where |
|---|---|---|---|---|
| e09_alpha.csv | alpha_extrapolated | 2 | 8.69e-07 | occurrence=0 |
| e09_solvers.csv | nnz_factor | 23 | inf | N=100, method=splu_mmd, occurrence=0 |
| e09_solvers.csv | rel_err | 23 | inf | N=100, method=splu_mmd, occurrence=0 |
| e09_solvers.csv | status | 23 | 1 rows differ (text) | N=100, method=splu_mmd, occurrence=0 |

### Rows, columns and CSVs added or removed

- e07_structured.csv: new columns ['rms_random_tiny']
- e09_cone.csv: new CSV (not at ee2db14)

### Every compared column

| CSV | Column | Rows | Largest change | Where | Changed |
|---|---|---|---|---|---|
| e01_conditioning.csv | n | 10 | 0.00e+00 |  |  |
| e01_conditioning.csv | lambda_min_formula | 10 | 0.00e+00 |  |  |
| e01_conditioning.csv | lambda_min_eigsh | 10 | 2.22e-15 | N=300, occurrence=0 |  |
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
| e03_convergence.csv | relres | 1726 | 0.00e+00 |  |  |
| e03_convergence.csv | err_A | 1726 | 0.00e+00 |  |  |
| e03_convergence.csv | err_inf | 1726 | 0.00e+00 |  |  |
| e03_convergence.csv | chebyshev | 1726 | 0.00e+00 |  |  |
| e03_krylov.csv | n | 160 | 0.00e+00 |  |  |
| e03_krylov.csv | iterations | 160 | 0.00e+00 |  |  |
| e03_krylov.csv | bound | 160 | 0.00e+00 |  |  |
| e03_krylov.csv | iterations_over_N | 160 | 0.00e+00 |  |  |
| e03_krylov.csv | final_relres | 160 | 0.00e+00 |  |  |
| e03_krylov.csv | forward_error | 160 | 0.00e+00 |  |  |
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
| e04_errors.csv | rel_err_tiny | 124 | 0.00e+00 |  |  |
| e04_errors.csv | max_rel_err | 124 | 0.00e+00 |  |  |
| e04_errors.csv | argmax_rel_err_state | 124 | 0 rows differ (text) |  |  |
| e04_errors.csv | normwise_rel_err | 124 | 0.00e+00 |  |  |
| e04_errors.csv | normwise_backward_error | 124 | 0.00e+00 |  |  |
| e04_errors.csv | componentwise_backward_error | 124 | 0.00e+00 |  |  |
| e04_errors.csv | cond_tiny | 124 | 0.00e+00 |  |  |
| e04_errors.csv | ratio_tiny_to_prediction | 124 | 0.00e+00 |  |  |
| e04_errors.csv | max_err_over_bound | 124 | 0.00e+00 |  |  |
| e04_errors.csv | value_tiny | 124 | 0.00e+00 |  |  |
| e04_errors.csv | data_term_tiny | 124 | 0.00e+00 |  |  |
| e04_errors.csv | signed_err_tiny | 124 | 0.00e+00 |  |  |
| e04_errors.csv | solver_err_tiny | 124 | 0.00e+00 |  |  |
| e04_errors.csv | max_solver_err | 124 | 0.00e+00 |  |  |
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
| e07_fixes.csv | rel_err_tiny | 111 | 0.00e+00 |  |  |
| e07_fixes.csv | max_rel_err | 111 | 0.00e+00 |  |  |
| e07_fixes.csv | max_rel_err_in_u | 111 | 0.00e+00 |  |  |
| e07_fixes.csv | omega | 111 | 0.00e+00 |  |  |
| e07_fixes.csv | cond_tiny | 111 | 0.00e+00 |  |  |
| e07_fixes.csv | data_term_tiny | 111 | 0.00e+00 |  |  |
| e07_fixes.csv | err_vs_stored_tiny | 111 | 0.00e+00 |  |  |
| e07_fixes.csv | max_err_vs_stored | 111 | 0.00e+00 |  |  |
| e07_fixes.csv | signed_err_tiny | 111 | 0.00e+00 |  |  |
| e07_fixes.csv | corrections | 111 | 0 rows differ (text) |  |  |
| e07_floor.csv | check_every | 15 | 0.00e+00 |  |  |
| e07_floor.csv | iters_rtol_1e10 | 15 | 0.00e+00 |  |  |
| e07_floor.csv | maxiter | 15 | 0.00e+00 |  |  |
| e07_floor.csv | min_omega | 15 | 0.00e+00 |  |  |
| e07_floor.csv | min_omega_in_u | 15 | 0.00e+00 |  |  |
| e07_floor.csv | k_at_min | 15 | 0.00e+00 |  |  |
| e07_floor.csv | k_at_min_over_k10 | 15 | 0.00e+00 |  |  |
| e07_floor.csv | final_omega_in_u | 15 | 0.00e+00 |  |  |
| e07_floor.csv | max_x_corner_ratio | 15 | 0.00e+00 |  |  |
| e07_floor.csv | max_x_inf_ratio | 15 | 0.00e+00 |  |  |
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
| e09_alpha.csv | alpha_extrapolated | 2 | 8.69e-07 | occurrence=0 | **changed** |
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
| e09_solvers.csv | status | 23 | 1 rows differ (text) | N=100, method=splu_mmd, occurrence=0 | **changed** |
| e10_bt_overflow.csv | value | 8 | 0.00e+00 |  |  |
| e10_bt_solvers.csv | iters | 48 | 0.00e+00 |  |  |
| e10_bt_solvers.csv | rel_residual_A | 48 | 0.00e+00 |  |  |
| e10_bt_solvers.csv | max_err_rel | 48 | 0.00e+00 |  |  |
| e10_bt_solvers.csv | max_err_lowpi_rel | 48 | 0.00e+00 |  |  |
| e10_bt_spectrum.csv | n | 5 | 0.00e+00 |  |  |
| e10_bt_spectrum.csv | max_abs_A_minus_AT | 5 | 0.00e+00 |  |  |
| e10_bt_spectrum.csv | rel_asym_S | 5 | 0.00e+00 |  |  |
| e10_bt_spectrum.csv | lam_min_S | 5 | 1.49e-15 | N=40, occurrence=0 |  |
| e10_bt_spectrum.csv | lam_max_S | 5 | 1.36e-14 | N=320, occurrence=0 |  |
| e10_bt_spectrum.csv | cond2_S | 5 | 1.31e-14 | N=320, occurrence=0 |  |
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
