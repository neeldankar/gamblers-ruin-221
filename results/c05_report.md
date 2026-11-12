# Chunk 5 report: stationary methods and the SOR 3/4 law

- `results/e05_iterations.csv`: git a9b0187, 2026-11-11T16:33:38
- `results/e05_omega_sweep.csv`: git a9b0187, 2026-11-11T16:34:28
- `results/e05_sor_spectra.csv`: git a9b0187, 2026-11-11T16:37:47
- macOS-15.6.1-arm64-arm-64bit-Mach-O, Python 3.13.18, numpy 2.5.4, scipy 1.18.1, OMP_NUM_THREADS=1.

| Check | Expected | Observed | Status |
|---|---|---|---|
| e05_iterations: converged | True in every row | 51 of 51 rows converged | PASS |
| forward_error | at most kappa2 x rtol (a theorem; measured 1e-5 to 0.6 of that bound) | forward_error / (kappa2 rtol) from 1.1e-05 to 0.59 over 51 rows | PASS |
| jacobi: iterations | at most predicted_iterations + 1 for every N and b (a theorem: Q is symmetric, so the residual shrinks by at least rho_J per sweep) | iterations - predicted from -12281.0 to -0.07 | PASS |
| jacobi, b = ones: iterations | between 0.98 x predicted_iterations and predicted_iterations + 1 (measured 0.990 to 0.9996 of predicted) | N=10: 0.9996, N=20: 0.9926, N=40: 0.9911, N=80: 0.9900, N=160: 0.9896 | PASS |
| b = ones, jacobi at N = 10, 20, 40, 80, 160 | 169, 689, 2769, 11081, 44322 iterations; 1% or 1 sweep, whichever is larger | N=10: 169, N=20: 689, N=40: 2769, N=80: 11081, N=160: 44322 | PASS |
| b = ones, gauss_seidel at N = 10, 20, 40, 80, 160 | 86, 346, 1386, 5542, 22163 iterations; 1% or 1 sweep, whichever is larger | N=10: 86, N=20: 346, N=40: 1386, N=80: 5542, N=160: 22163 | PASS |
| b = ones, sor at N = 10, 20, 40, 80, 160, 320, 640 | 31, 64, 129, 258, 515, 1030, 2062 iterations; 1% or 1 sweep, whichever is larger | N=10: 31, N=20: 64, N=40: 129, N=80: 258, N=160: 515, N=320: 1030, N=640: 2062 | PASS |
| gauss_seidel iterations / jacobi iterations (same N and b) | 0.45 to 0.55 (measured 0.497 to 0.529) | 0.4977 to 0.5286 over 15 pairs | PASS |
| jacobi: rate_measured / rho_jacobi | 1; 1e-6 (measured within 2e-8) | max |ratio - 1| = 1.3e-08 over 15 rows | PASS |
| gauss_seidel at N = 10, 20, 40, 80: rate_measured / rho_gs_dense (from e05_sor_spectra) | 1; 1e-6 (measured within 6e-8) | max |ratio - 1| = 5.1e-08 over 12 rows | PASS |
| sor, b = ones: iterations / predicted_iterations | 1.0 to 1.15 (measured 1.075 to 1.081) | N=10: 1.078, N=20: 1.080, N=40: 1.080, N=80: 1.078, N=160: 1.076, N=320: 1.076, N=640: 1.077 | PASS |
| sor, b = ones: iterations / young_predicted_iterations | at least 1.3 (measured 1.434 to 1.441) | N=10: 1.437, N=20: 1.440, N=40: 1.441, N=80: 1.438, N=160: 1.435, N=320: 1.434, N=640: 1.436 | PASS |
| sor, b = ones: exponent_ratio | 0.75; 0.01 (measured 0.7485 to 0.7502) | N=10: 0.7499, N=20: 0.7500, N=40: 0.7500, N=80: 0.7500, N=160: 0.7501, N=320: 0.7502, N=640: 0.7485 | PASS |
| sor, b = random: exponent_ratio | 0.74 to 0.82 (measured 0.761 to 0.790) | N=10: 0.7634, N=20: 0.7614, N=40: 0.7798, N=80: 0.7872, N=160: 0.7860, N=320: 0.7895, N=640: 0.7891 | PASS |
| sor, b = ones, N >= 20: iterations / N | 3.0 to 3.4 (measured 3.20 to 3.23) | N=20: 3.200, N=40: 3.225, N=80: 3.225, N=160: 3.219, N=320: 3.219, N=640: 3.222 | PASS |
| e05_omega_sweep, N = 20 and 40: argmin of rho_dense on the fine grid | offset 0 (omega* itself); exact | N=20: offset +0.0000, N=40: offset +0.0000 | PASS |
| rho_dense at offset 0 | 0.678068809 (N = 20), 0.824609363 (N = 40); 1e-9 relative | N=20: 0.678068809, N=40: 0.824609363 | PASS |
| rows with omega = 1.00 | iterations equal the gauss_seidel counts in e05_iterations (same N and b); 1 sweep | N=20: ones 346 vs 346, random 319 vs 319; N=40: ones 1386 vs 1386, random 1139 vs 1139; N=80: ones 5542 vs 5542, random 4285 vs 4285 | PASS |
| fine grid: best iterations_ones | at offset 0 to +0.025, with 10% to 20% fewer sweeps than at omega* (measured +0.0175 and 14% at N = 20, +0.0125 and 16% at N = 40, +0.0075 and 17% at N = 80) | N=20: 55 at +0.0175 vs 64 at 0 (14.1% fewer); N=40: 108 at +0.0125 vs 129 at 0 (16.3% fewer); N=80: 214 at +0.0075 vs 258 at 0 (17.1% fewer) | PASS |
| fine grid: best iterations_random | offset within 0.01 of 0, under 5% fewer sweeps (measured +0.005 and 2%, 0 and 0%, -0.005 and 3%) | N=20: 58 at +0.0050 vs 59 at 0 (1.7% fewer); N=40: 116 at +0.0000 vs 116 at 0 (0.0% fewer); N=80: 224 at -0.0050 vs 230 at 0 (2.6% fewer) | PASS |
| e05_sor_spectra: law_relerr | 0, every N; 1e-10 (measured at most 2.3e-14) | N=6: 2.2e-16, N=8: 1.8e-15, N=10: 2.2e-16, N=12: 1.1e-15, N=16: 4e-15, N=20: 4e-15, N=24: 8.2e-15, N=30: 4.7e-15, N=40: 9.3e-15, N=50: 8.9e-16, N=60: 1.3e-14, N=80: 1.5e-14, N=100: 1e-14 | PASS |
| rho_sor_dense at N = 6 | sqrt(5) - 2 = 0.2360679775; 1e-12 | 0.2360679774998 (diff -8.3e-17) | PASS |
| rho_sor_dense at N = 12, 20, 30, 40, 100 | 0.517356404, 0.678068809, 0.772896324, 0.824609363, 0.925906019; 1e-9 relative | N=12: 0.517356404, N=20: 0.678068809, N=30: 0.772896324, N=40: 0.824609363, N=100: 0.925906019 | PASS |
| sor_over_young | above 1 for every N (1.618 at N = 6 down to 1.026 at N = 100) | N=6: 1.6180, N=8: 1.4072, N=10: 1.3059, N=12: 1.2457, N=16: 1.1768, N=20: 1.1383, N=24: 1.1136, N=30: 1.0897, N=40: 1.0664, N=50: 1.0527, N=60: 1.0437, N=80: 1.0326, N=100: 1.0260 | PASS |
| abs(rho_jacobi_dense - rho_jacobi_formula) | 0; 1e-12 | max 1e-14 | PASS |
| gs_gap | positive for every N | N=6: 0.00782, N=8: 0.00332, N=10: 0.00155, N=12: 0.000799, N=16: 0.00027, N=20: 0.000114, N=24: 5.59e-05, N=30: 2.32e-05, N=40: 7.42e-06, N=50: 3.05e-06, N=60: 1.48e-06, N=80: 4.68e-07, N=100: 1.92e-07 | PASS |
| gs_gap_times_N4 | 10 to 20 and increasing in N (measured 10.13 at N = 6 up to 19.20 at N = 100) | N=6: 10.133, N=8: 13.607, N=10: 15.472, N=12: 16.560, N=16: 17.696, N=20: 18.241, N=24: 18.543, N=30: 18.792, N=40: 18.988, N=50: 19.079, N=60: 19.128, N=80: 19.178, N=100: 19.201 | PASS |
| seconds_dense at N = 100 | under 5 min (2.4 min on the 2-core cloud machine) | 147.6 s | PASS |

Summary: 28 PASS, 0 WARN, 0 FAIL.

## Red flags (automatic checks of the spec's list)

| Red flag check | Observed | OK |
|---|---|---|
| SOR b = ones near Young's count or exponent_ratio near 1 (wrong order, rho_J or stencil) | iterations / young 1.434 to 1.441, exponent_ratio 0.7485 to 0.7502 | yes |
| forward_error above kappa2 x rtol, or a Jacobi count above predicted + 1 (residual not true) | max fwd / (kappa2 rtol) 0.59, max jacobi excess -0.07 | yes |
| law_relerr well above 1e-12 (iteration_matrix and sweeps disagree) | max 1.5e-14 | yes |
| rho_dense minimum away from offset 0 (young_omega or rho_J wrong) | +0.0000, +0.0000 | yes |
| SOR diverging for some 0 < omega < 2 (impossible for SPD A) | max rho_dense 0.984932, max sweeps 5542 | yes |
| Jacobi at N = 160 taking more than a few minutes (not compiled) | max 9.11 s | yes |

## SOR with b = out_first (printed without a range, as the spec says)

| N | iterations | predicted_iterations | young_predicted_iterations | iterations_over_young | exponent_ratio |
|---|---|---|---|---|---|
| 10 | 28 | 28.76 | 21.57 | 1.298 | 0.7501 |
| 20 | 55 | 59.27 | 44.45 | 1.237 | 0.7513 |
| 40 | 105 | 119.4 | 89.55 | 1.173 | 0.7578 |
| 80 | 198 | 239.2 | 179.4 | 1.104 | 0.7842 |
| 160 | 375 | 478.7 | 359 | 1.045 | 0.8446 |
| 320 | 713 | 957.5 | 718.1 | 0.993 | 0.9170 |
| 640 | 1377 | 1915 | 1436 | 0.959 | 0.9699 |

## Data: e05_iterations

| N | n | method | omega | b_kind | iterations | converged | final_residual | predicted_iterations | young_predicted_iterations | rate_measured | exponent_ratio | rho_jacobi | kappa2 | forward_error | seconds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 36 | jacobi | nan | ones | 169 | True | 8.974e-11 | 169.1 | nan | 0.872677990 | nan | 0.872677996 | 11.28 | 1.002e-10 | 0.0003346 |
| 20 | 171 | jacobi | nan | ones | 689 | True | 9.908e-11 | 694.1 | nan | 0.967371003 | nan | 0.967371011 | 45.47 | 1.175e-10 | 0.002767 |
| 40 | 741 | jacobi | nan | ones | 2769 | True | 9.922e-11 | 2793.8 | nan | 0.991792220 | nan | 0.991792227 | 182.3 | 1.217e-10 | 0.03644 |
| 80 | 3081 | jacobi | nan | ones | 11081 | True | 9.993e-11 | 11192.7 | nan | 0.997944885 | nan | 0.997944889 | 729.4 | 1.248e-10 | 0.5538 |
| 160 | 12561 | jacobi | nan | ones | 44322 | True | 9.999e-11 | 44788.0 | nan | 0.999486021 | nan | 0.999486024 | 2918 | 1.26e-10 | 9.108 |
| 10 | 36 | jacobi | nan | out_first | 159 | True | 9.461e-11 | 169.1 | nan | 0.872677985 | nan | 0.872677996 | 11.28 | 2.857e-10 | 0.0002992 |
| 20 | 171 | jacobi | nan | out_first | 620 | True | 9.829e-11 | 694.1 | nan | 0.967371010 | nan | 0.967371011 | 45.47 | 7.639e-10 | 0.002475 |
| 40 | 741 | jacobi | nan | out_first | 2366 | True | 9.961e-11 | 2793.8 | nan | 0.991792227 | nan | 0.991792227 | 182.3 | 2.101e-09 | 0.03122 |
| 80 | 3081 | jacobi | nan | out_first | 8967 | True | 9.99e-11 | 11192.7 | nan | 0.997944889 | nan | 0.997944889 | 729.4 | 5.845e-09 | 0.4458 |
| 160 | 12561 | jacobi | nan | out_first | 33847 | True | 9.998e-11 | 44788.0 | nan | 0.999486024 | nan | 0.999486024 | 2918 | 1.639e-08 | 6.917 |
| 10 | 36 | jacobi | nan | random | 140 | True | 8.73e-11 | 169.1 | nan | 0.872677997 | nan | 0.872677996 | 11.28 | 6.507e-10 | 0.0002598 |
| 20 | 171 | jacobi | nan | random | 634 | True | 9.871e-11 | 694.1 | nan | 0.967371011 | nan | 0.967371011 | 45.47 | 6.821e-10 | 0.00252 |
| 40 | 741 | jacobi | nan | random | 2232 | True | 9.951e-11 | 2793.8 | nan | 0.991792227 | nan | 0.991792227 | 182.3 | 1.96e-09 | 0.02943 |
| 80 | 3081 | jacobi | nan | random | 8578 | True | 9.989e-11 | 11192.7 | nan | 0.997944889 | nan | 0.997944889 | 729.4 | 7.139e-09 | 0.4321 |
| 160 | 12561 | jacobi | nan | random | 32507 | True | 9.997e-11 | 44788.0 | nan | 0.999486024 | nan | 0.999486024 | 2918 | 1.303e-08 | 6.681 |
| 10 | 36 | gauss_seidel | nan | ones | 86 | True | 8.841e-11 | 84.5 | nan | 0.763114078 | nan | 0.872677996 | 11.28 | 9.029e-11 | 0.0001837 |
| 20 | 171 | gauss_seidel | nan | ones | 346 | True | 9.922e-11 | 347.1 | nan | 0.935920672 | nan | 0.967371011 | 45.47 | 1.146e-10 | 0.001665 |
| 40 | 741 | gauss_seidel | nan | ones | 1386 | True | 9.93e-11 | 1396.9 | nan | 0.983659232 | nan | 0.991792227 | 182.3 | 1.209e-10 | 0.02566 |
| 80 | 3081 | gauss_seidel | nan | ones | 5542 | True | 9.996e-11 | 5596.3 | nan | 0.995894465 | nan | 0.997944889 | 729.4 | 1.246e-10 | 0.4349 |
| 160 | 12561 | gauss_seidel | nan | ones | 22163 | True | 9.995e-11 | 22394.0 | nan | 0.998972337 | nan | 0.999486024 | 2918 | 1.259e-10 | 7.33 |
| 10 | 36 | gauss_seidel | nan | out_first | 80 | True | 8.662e-11 | 84.5 | nan | 0.763114075 | nan | 0.872677996 | 11.28 | 2.393e-10 | 0.0001573 |
| 20 | 171 | gauss_seidel | nan | out_first | 309 | True | 9.545e-11 | 347.1 | nan | 0.935920678 | nan | 0.967371011 | 45.47 | 7.225e-10 | 0.001496 |
| 40 | 741 | gauss_seidel | nan | out_first | 1178 | True | 9.997e-11 | 1396.9 | nan | 0.983659237 | nan | 0.991792227 | 182.3 | 2.094e-09 | 0.02209 |
| 80 | 3081 | gauss_seidel | nan | out_first | 4472 | True | 9.992e-11 | 5596.3 | nan | 0.995894470 | nan | 0.997944889 | 729.4 | 5.835e-09 | 0.3515 |
| 160 | 12561 | gauss_seidel | nan | out_first | 16899 | True | 9.995e-11 | 22394.0 | nan | 0.998972342 | nan | 0.999486024 | 2918 | 1.638e-08 | 5.579 |
| 10 | 36 | gauss_seidel | nan | random | 74 | True | 9.722e-11 | 84.5 | nan | 0.763114119 | nan | 0.872677996 | 11.28 | 6.63e-10 | 0.0001455 |
| 20 | 171 | gauss_seidel | nan | random | 319 | True | 9.438e-11 | 347.1 | nan | 0.935920680 | nan | 0.967371011 | 45.47 | 6.352e-10 | 0.001542 |
| 40 | 741 | gauss_seidel | nan | random | 1139 | True | 9.841e-11 | 1396.9 | nan | 0.983659245 | nan | 0.991792227 | 182.3 | 1.925e-09 | 0.02124 |
| 80 | 3081 | gauss_seidel | nan | random | 4285 | True | 9.992e-11 | 5596.3 | nan | 0.995894470 | nan | 0.997944889 | 729.4 | 7.128e-09 | 0.3392 |
| 160 | 12561 | gauss_seidel | nan | random | 16179 | True | 9.998e-11 | 22394.0 | nan | 0.998972341 | nan | 0.999486024 | 2918 | 1.303e-08 | 5.509 |
| 10 | 36 | sor | 1.343819 | ones | 31 | True | 9.208e-11 | 28.8 | 21.6 | 0.449027516 | 0.7499 | 0.872677996 | 11.28 | 6.093e-11 | 7.929e-05 |
| 20 | 171 | sor | 1.595706 | ones | 64 | True | 8.859e-11 | 59.3 | 44.5 | 0.678058213 | 0.7500 | 0.967371011 | 45.47 | 5.751e-11 | 0.0003198 |
| 40 | 741 | sor | 1.773270 | ones | 129 | True | 8.762e-11 | 119.4 | 89.6 | 0.824617019 | 0.7500 | 0.991792227 | 182.3 | 5.655e-11 | 0.002408 |
| 80 | 3081 | sor | 1.879561 | ones | 258 | True | 9.176e-11 | 239.2 | 179.4 | 0.908236663 | 0.7500 | 0.997944889 | 729.4 | 5.909e-11 | 0.02042 |
| 160 | 12561 | sor | 1.937876 | ones | 515 | True | 9.744e-11 | 478.7 | 359.0 | 0.953031788 | 0.7501 | 0.999486024 | 2918 | 6.269e-11 | 0.1708 |
| 320 | 50721 | sor | 1.968444 | ones | 1030 | True | 9.786e-11 | 957.5 | 718.1 | 0.976231020 | 0.7502 | 0.999871494 | 1.167e+04 | 6.292e-11 | 1.403 |
| 640 | 203841 | sor | 1.984096 | ones | 2062 | True | 9.916e-11 | 1915.0 | 1436.2 | 0.988071053 | 0.7485 | 0.999967873 | 4.669e+04 | 6.171e-11 | 11.44 |
| 10 | 36 | sor | 1.343819 | out_first | 28 | True | 9.241e-11 | 28.8 | 21.6 | 0.448965741 | 0.7501 | 0.872677996 | 11.28 | 1.654e-10 | 6.125e-05 |
| 20 | 171 | sor | 1.595706 | out_first | 55 | True | 8.393e-11 | 59.3 | 44.5 | 0.677603422 | 0.7513 | 0.967371011 | 45.47 | 3.57e-10 | 0.0002853 |
| 40 | 741 | sor | 1.773270 | out_first | 105 | True | 8.514e-11 | 119.4 | 89.6 | 0.822959490 | 0.7578 | 0.991792227 | 182.3 | 9.427e-10 | 0.002013 |
| 80 | 3081 | sor | 1.879561 | out_first | 198 | True | 9.64e-11 | 239.2 | 179.4 | 0.904259844 | 0.7842 | 0.997944889 | 729.4 | 2.875e-09 | 0.01563 |
| 160 | 12561 | sor | 1.937876 | out_first | 375 | True | 9.687e-11 | 478.7 | 359.0 | 0.947273568 | 0.8446 | 0.999486024 | 2918 | 7.66e-09 | 0.1242 |
| 320 | 50721 | sor | 1.968444 | out_first | 713 | True | 9.936e-11 | 957.5 | 718.1 | 0.971024652 | 0.9170 | 0.999871494 | 1.167e+04 | 1.833e-08 | 0.9712 |
| 640 | 203841 | sor | 1.984096 | out_first | 1377 | True | 9.879e-11 | 1915.0 | 1436.2 | 0.984570659 | 0.9699 | 0.999967873 | 4.669e+04 | 3.273e-08 | 7.64 |
| 10 | 36 | sor | 1.343819 | random | 29 | True | 6.299e-11 | 28.8 | 21.6 | 0.442636018 | 0.7634 | 0.872677996 | 11.28 | 1.937e-10 | 6.271e-05 |
| 20 | 171 | sor | 1.595706 | random | 59 | True | 8.747e-11 | 59.3 | 44.5 | 0.674069134 | 0.7614 | 0.967371011 | 45.47 | 2.874e-10 | 0.0002962 |
| 40 | 741 | sor | 1.773270 | random | 116 | True | 9.839e-11 | 119.4 | 89.6 | 0.818318908 | 0.7798 | 0.991792227 | 182.3 | 7.828e-10 | 0.002193 |
| 80 | 3081 | sor | 1.879561 | random | 230 | True | 9.478e-11 | 239.2 | 179.4 | 0.903913426 | 0.7872 | 0.997944889 | 729.4 | 2.037e-10 | 0.01828 |
| 160 | 12561 | sor | 1.937876 | random | 460 | True | 9.791e-11 | 478.7 | 359.0 | 0.950838806 | 0.7860 | 0.999486024 | 2918 | 3.538e-10 | 0.1526 |
| 320 | 50721 | sor | 1.968444 | random | 920 | True | 9.88e-11 | 957.5 | 718.1 | 0.975003576 | 0.7895 | 0.999871494 | 1.167e+04 | 1.296e-11 | 1.289 |
| 640 | 203841 | sor | 1.984096 | random | 1838 | True | 9.991e-11 | 1915.0 | 1436.2 | 0.987429504 | 0.7891 | 0.999967873 | 4.669e+04 | 4.397e-10 | 10.2 |

## Data: e05_omega_sweep (summary rows; all 273 rows are in the CSV)

Per N: the coarse row at omega = 1.00, the fine row at offset 0 (omega*), and the fine rows with the fewest sweeps for b = ones and b = random (ties to the smallest |offset|).

| N | row | grid | omega | offset | omega_star | iterations_ones | iterations_random | rho_dense |
|---|---|---|---|---|---|---|---|---|
| 20 | omega = 1.00 | coarse | 1.000000 | -0.5957 | 1.595706 | 346 | 319 | 0.935920682 |
| 20 | omega* | fine | 1.595706 | +0.0000 | 1.595706 | 64 | 59 | 0.678068809 |
| 20 | best ones | fine | 1.613206 | +0.0175 | 1.595706 | 55 | 61 | 0.692727991 |
| 20 | best random | fine | 1.600706 | +0.0050 | 1.595706 | 62 | 58 | 0.682264433 |
| 40 | omega = 1.00 | coarse | 1.000000 | -0.7733 | 1.773270 | 1386 | 1139 | 0.983659239 |
| 40 | omega* | fine | 1.773270 | +0.0000 | 1.773270 | 129 | 116 | 0.824609363 |
| 40 | best ones | fine | 1.785770 | +0.0125 | 1.773270 | 108 | 121 | 0.834549268 |
| 40 | best random | fine | 1.773270 | +0.0000 | 1.773270 | 129 | 116 | 0.824609363 |
| 80 | omega = 1.00 | coarse | 1.000000 | -0.8796 | 1.879561 | 5542 | 4285 | nan |
| 80 | omega* | fine | 1.879561 | +0.0000 | 1.879561 | 258 | 230 | nan |
| 80 | best ones | fine | 1.887061 | +0.0075 | 1.879561 | 214 | 245 | nan |
| 80 | best random | fine | 1.874561 | -0.0050 | 1.879561 | 284 | 224 | nan |

## Data: e05_sor_spectra

| N | n | omega_star | rho_jacobi_formula | rho_jacobi_dense | rho_gs_dense | gs_gap | gs_gap_times_N4 | rho_sor_dense | law_value | young_value | law_relerr | sor_over_young | seconds_dense |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 6 | 10 | 1.145898034 | 0.666666666667 | 0.666666666667 | 0.452263057442 | 0.007819 | 10.133 | 0.236067977500 | 0.236067977500 | 0.145898033750 | 2.2e-16 | 1.6180 | 0.00 |
| 8 | 21 | 1.254996183 | 0.804737854124 | 0.804737854124 | 0.650924959828 | 0.003322 | 13.607 | 0.358839514102 | 0.358839514102 | 0.254996183187 | 1.8e-15 | 1.4072 | 0.00 |
| 10 | 36 | 1.343818581 | 0.872677996250 | 0.872677996250 | 0.763114079719 | 0.001547 | 15.472 | 0.449000689633 | 0.449000689633 | 0.343818581386 | 2.2e-16 | 1.3059 | 0.00 |
| 12 | 55 | 1.415323437 | 0.910683602523 | 0.910683602523 | 0.830143226596 | 0.0007986 | 16.560 | 0.517356404064 | 0.517356404064 | 0.415323436783 | 1.1e-15 | 1.2457 | 0.00 |
| 16 | 105 | 1.521475511 | 0.949253021674 | 0.949253021674 | 0.901351323502 | 0.00027 | 17.696 | 0.613656641108 | 0.613656641108 | 0.521475510736 | 4e-15 | 1.1768 | 0.01 |
| 20 | 171 | 1.595705610 | 0.967371010863 | 0.967371010863 | 0.935920681696 | 0.000114 | 18.241 | 0.678068808994 | 0.678068808994 | 0.595705609742 | 4e-15 | 1.1383 | 0.02 |
| 24 | 253 | 1.650254274 | 0.977283884193 | 0.977283884193 | 0.955139679653 | 5.589e-05 | 18.543 | 0.724123115650 | 0.724123115650 | 0.650254273611 | 8.2e-15 | 1.1136 | 0.06 |
| 30 | 406 | 1.709297326 | 0.985431733823 | 0.985431733823 | 0.971098902033 | 2.32e-05 | 18.792 | 0.772896324321 | 0.772896324321 | 0.709297325946 | 4.7e-15 | 1.0897 | 0.18 |
| 40 | 741 | 1.773269740 | 0.991792227063 | 0.991792227063 | 0.983659238694 | 7.417e-06 | 18.988 | 0.824609362722 | 0.824609362722 | 0.773269739827 | 9.3e-15 | 1.0664 | 0.87 |
| 50 | 1176 | 1.814220805 | 0.994743134210 | 0.994743134210 | 0.989516955640 | 3.053e-06 | 19.079 | 0.857149638657 | 0.857149638657 | 0.814220804805 | 8.9e-16 | 1.0527 | 2.51 |
| 60 | 1711 | 1.842662099 | 0.996347930246 | 0.996347930246 | 0.992710674048 | 1.476e-06 | 19.128 | 0.879508610486 | 0.879508610486 | 0.842662099022 | 1.3e-14 | 1.0437 | 6.85 |
| 80 | 3081 | 1.879561349 | 0.997944889155 | 0.997944889155 | 0.995894469996 | 4.682e-07 | 19.178 | 0.908237861805 | 0.908237861805 | 0.879561348739 | 1.5e-14 | 1.0326 | 39.34 |
| 100 | 4851 | 1.902448740 | 0.998684485619 | 0.998684485619 | 0.997370893821 | 1.92e-07 | 19.201 | 0.925906018512 | 0.925906018512 | 0.902448739705 | 1e-14 | 1.0260 | 147.61 |

Figures: `figures/f05_iterations.png`, `figures/f05_omega.png`.
