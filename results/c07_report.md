# Chunk 7 report: three fixes for the tiny probabilities

Sources: `results/e07_fixes.csv` (git 522a5a2, 2026-11-10T23:57:45), `results/e07_structured.csv` (git 3ccfc4e, 2026-11-11T16:05:40), `results/e07_baselines.csv` (git 3ccfc4e, 2026-11-11T16:06:57), `results/e07_floor.csv` (git c7eebd8, 2026-11-11T09:45:58), `results/e07_fft_check.csv` (git 86834dc, 2026-11-11T15:03:18); macOS-15.6.1-arm64-arm-64bit-Mach-O, Python 3.13.18, numpy 2.5.4, scipy 1.18.1, OMP_NUM_THREADS=1.

| Check | Expected | Observed | Status |
|---|---|---|---|
| ir_direct, ir_cg_mic0, ir_cg_amg vs exact (N <= 80): max_rel_err | 0 (correctly rounded); at most 2 u | 12 rows, max_rel_err 0 u; N=20 ir_direct: 0 u, N=20 ir_cg_mic0: 0 u, N=20 ir_cg_amg: 0 u, N=40 ir_direct: 0 u, N=40 ir_cg_mic0: 0 u, N=40 ir_cg_amg: 0 u, N=60 ir_direct: 0 u, N=60 ir_cg_mic0: 0 u, N=60 ir_cg_amg: 0 u, N=80 ir_direct: 0 u, N=80 ir_cg_mic0: 0 u, N=80 ir_cg_amg: 0 u | PASS |
| ir_* agree with each other, N >= 160 (ir_cg_* vs ir_direct, the reference) | identical or 1 ulp; at most 4 u | N=160 ir_cg_mic0: 0 u, N=160 ir_cg_amg: 1.1 u, N=320 ir_cg_mic0: 0 u, N=320 ir_cg_amg: 0 u, N=640 ir_cg_mic0: 0 u, N=640 ir_cg_amg: 1.9 u, N=1280 ir_cg_mic0: 2 u, N=1280 ir_cg_amg: 2 u | PASS |
| ir_direct steps | 2; at most 3 | N=20: 2, N=40: 2, N=60: 2, N=80: 2, N=160: 2, N=320: 2, N=640: 2, N=1280: 2 | PASS |
| ir_cg_mic0 and ir_cg_amg steps | 3 (N <= 320), 4 (N >= 640); at most 8 | ir_cg_amg: N=20: 3, N=40: 3, N=60: 3, N=80: 3, N=160: 3, N=320: 3, N=640: 4, N=1280: 4; ir_cg_mic0: N=20: 3, N=40: 3, N=60: 3, N=80: 3, N=160: 3, N=320: 3, N=640: 4, N=1280: 4 | PASS |
| gth max_rel_err_in_u | 8 (20), 12 (40), 25 (60), 34 (80), 46 (160), 60 (320), 200 (640): 0.19-0.42 N; below N; above 10 N is FAIL | N=20: 8.0 u (0.40 N), N=40: 11.7 u (0.29 N), N=60: 24.7 u (0.41 N), N=80: 33.8 u (0.42 N), N=160: 45.8 u (0.29 N), N=320: 59.5 u (0.19 N), N=640: 199.8 u (0.31 N) | PASS |
| direct max_rel_err_in_u / N^2 (against the true probability; mostly the data term, 0.097) | Mac: 0.065 for N >= 160, 0.09-0.13 for N <= 80 (37, 190, 428, 848 u at N = 20, 40, 60, 80); the Linux reference had 39, 267, 431 u at N = 20, 60, 80 (CHOLMOD's own part differs by machine); in [0.02, 0.2] | N=20: 37 u (0.091), N=40: 190 u (0.119), N=60: 428 u (0.119), N=80: 848 u (0.133), N=160: 1669 u (0.065), N=320: 6661 u (0.065), N=640: 26528 u (0.065), N=1280: 107357 u (0.066) | PASS |
| direct err_vs_stored_tiny (the solver's own error) | Mac: +3.8e-16 (20), -4.0e-15 (40), -8.8e-15 (60), -2.5e-14 (80), +9.1e-14 (160), +3.7e-13 (320), +1.5e-12 (640), +5.7e-12 (1280): +0.032 N^2 u for N >= 160, opposite in sign to the data term; either sign for N <= 80. Linux reference: -1.1e-14 (80), about +0.05 N^2 u for N >= 160; absolute value below 0.2 N^2 u | N=20: +3.8e-16 (+0.009 N^2 u, opposite sign), N=40: -4e-15 (-0.022 N^2 u, same sign), N=60: -8.8e-15 (-0.022 N^2 u, same sign), N=80: -2.5e-14 (-0.036 N^2 u, same sign), N=160: +9.1e-14 (+0.032 N^2 u, opposite sign), N=320: +3.7e-13 (+0.032 N^2 u, opposite sign), N=640: +1.5e-12 (+0.032 N^2 u, opposite sign), N=1280: +5.7e-12 (+0.032 N^2 u, opposite sign) | PASS |
| data_term_tiny | -6.895e-14 (80), -2.7592e-13 (160), -1.1038e-12 (320), -4.4153e-12 (640), -1.7661e-11 (1280); 1e-3 relative | N=80: -6.8948e-14 (-2.9e-05), N=160: -2.7592e-13 (-1.1e-05), N=320: -1.1038e-12 (-6.9e-06), N=640: -4.4153e-12 (-1.2e-06), N=1280: -1.7661e-11 (+1.7e-05) | PASS |
| gth beats direct (true probability, max_rel_err), N >= 80 | by a factor growing with N: 25 (80), 37 (160), 112 (320), 133 (640) on the Mac (13 at N = 80 on Linux); gth smaller at every N >= 80 | N=80: factor 25.1, N=160: factor 36.5, N=320: factor 111.9, N=640: factor 132.8 | PASS |
| cg rtol 1e-10, kind none: rel_err_tiny | 5e-8 (60), 6.8e-7 (160), 1.4e-5 (640); as in chunk 4 ([3e-6, 6e-5] at 640, the same factor band at 60 and 160) | N=60: 4.9e-08 (0.99x), N=160: 6.8e-07 (1.00x), N=640: 1.4e-05 (1.02x) | PASS |
| cg_componentwise tol 1e-14: rel_err_tiny (true probability) | 4e-14 to 6e-14 (60), 3e-13 (160), 5e-12 (640): at N >= 160 this is the data term; below cond_tiny * tol | none: N=20: 4e-15, N=40: 1.7e-14, N=60: 5.2e-14, N=80: 6.9e-14, N=160: 2.5e-13, N=320: 1e-12, N=640: 4.1e-12, N=1280: 1.6e-11; mic0: N=20: 6.3e-15, N=40: 1.6e-14, N=60: 3.7e-14, N=80: 8e-14, N=160: 2.4e-13, N=320: 1e-12, N=640: 3.7e-12, N=1280: 1.5e-11; amg: N=20: 2.1e-15, N=40: 3.1e-14, N=60: 5.9e-14, N=80: 6.8e-14, N=160: 2.8e-13, N=320: 9.5e-13, N=640: 3.8e-12, N=1280: 1.6e-11; worst rel_err / (cond_tiny tol) 0.005 | PASS |
| cg_componentwise tol 1e-14: err_vs_stored_tiny, N >= 160, converged runs only | 0.05-0.46 of the direct solver's (Mac): none 2.9e-14, 8.0e-14, 3.0e-13; mic0 3.5e-14, 1.0e-13, 6.8e-13, 2.6e-12; amg 4.6e-15, 1.5e-13, 6.2e-13, 1.9e-12 (N = 160, 320, 640, 1280); below the direct solver's err_vs_stored_tiny at the same N | N=160 none: 2.9e-14 vs direct 9.1e-14 (0.33); N=160 mic0: 3.5e-14 vs direct 9.1e-14 (0.39); N=160 amg: 4.6e-15 vs direct 9.1e-14 (0.05); N=320 none: 8e-14 vs direct 3.7e-13 (0.22); N=320 mic0: 1e-13 vs direct 3.7e-13 (0.28); N=320 amg: 1.5e-13 vs direct 3.7e-13 (0.42); N=640 none: 3e-13 vs direct 1.5e-12 (0.20); N=640 mic0: 6.8e-13 vs direct 1.5e-12 (0.46); N=640 amg: 6.2e-13 vs direct 1.5e-12 (0.42); N=1280 mic0: 2.6e-12 vs direct 5.7e-12 (0.45); N=1280 amg: 1.9e-12 vs direct 5.7e-12 (0.34) (excluded, not converged: N=1280 none) | PASS |
| cg_componentwise iterations / cg rtol 1e-10 iterations, converged runs only (tol 1e-14) | none 1.25-1.49, mic0 1.36-1.90, amg 1.38-1.86; in [1.1, 2.5] | none (spec 1.25-1.49): N=20: 1.43, N=40: 1.25, N=60: 1.31, N=80: 1.33, N=160: 1.35, N=320: 1.37, N=640: 1.49; mic0 (spec 1.36-1.90): N=20: 1.43, N=40: 1.36, N=60: 1.48, N=80: 1.45, N=160: 1.67, N=320: 1.67, N=640: 1.79, N=1280: 1.90; amg (spec 1.38-1.86): N=20: 1.43, N=40: 1.38, N=60: 1.44, N=80: 1.67, N=160: 1.70, N=320: 1.69, N=640: 1.86, N=1280: 1.79 (excluded, not converged: N=1280 none) | PASS |
| cg_componentwise tol 1e-14 converged | mic0 and amg at every N up to 1280; none up to N = 640 (not at 1280: see e07_floor) | 23/24 rows converged (N up to 1280); required runs: 23/23; not converged: N=1280 none (final omega 360 u) | PASS |
| ir_direct seconds minus direct seconds at N = 640 | about 0.06 s (factor 1.3 s, Mac); under 50% of the factor time | ir_direct - direct = 0.056 s, factor 1.34 s (4%) | PASS |
| e07_fft_check: which solver is off at (N-2, 1, 1) | the FFT (normwise accurate only); splu within about 0.1 N^2 u of ir_direct, and near data_term_smallest | N=50: fft 1.9e-12, splu 2.1e-14 (0.077 N^2 u; signed -2.1e-14 vs data term -2.7e-14); N=100: fft 3e-10, splu 8.3e-14 (0.075 N^2 u; signed -8.3e-14 vs data term -1.1e-13); N=200: fft 2.5e-10, splu 3.2e-13 (0.073 N^2 u; signed -3.2e-13 vs data term -4.3e-13); N=400: fft 1.2e-07, splu 1.3e-12 (0.071 N^2 u; signed -1.3e-12 vs data term -1.7e-12); N=800: fft 4.8e-07, splu 5e-12 (0.070 N^2 u; signed -5e-12 vs data term -6.9e-12) | PASS |
| e07_fft_check: FFT rel_err_smallest at N = 800 | 4.8e-7 on the Mac (6e-7 and 2e-6 on two Linux reference implementations); in [1e-8, 1e-4] | 4.8e-07 | PASS |
| structured_cond_tiny, N = 10 ... 640 | 11.35295, 23.79933, 48.30309, 97.09688, 194.5739, 389.4719, 779.2398; 1e-4 relative | N=10: 11.35295, N=20: 23.79933, N=40: 48.30309, N=80: 97.09688, N=160: 194.5739, N=320: 389.4719, N=640: 779.2398 | PASS |
| structured_cond_max and structured_argmax_state | equal to structured_cond_tiny, at (1, 1, N-2); 1e-9 relative; exact | N=10: +0.0e+00 at (1, 1, 8), N=20: +0.0e+00 at (1, 1, 18), N=40: +0.0e+00 at (1, 1, 38), N=80: +0.0e+00 at (1, 1, 78), N=160: +0.0e+00 at (1, 1, 158), N=320: +0.0e+00 at (1, 1, 318), N=640: +0.0e+00 at (1, 1, 638) | PASS |
| structured_cond_over_N | 1.1353, 1.1900, 1.2076, 1.2137, 1.2161, 1.2171, 1.2176: increasing, below 1.22; in [1.13, 1.22], increasing | N=10: 1.1353, N=20: 1.1900, N=40: 1.2076, N=80: 1.2137, N=160: 1.2161, N=320: 1.2171, N=640: 1.2176 | PASS |
| attained_tiny / structured_cond_tiny; attained_max_dev | 1; at most 3.5e-6; within 1e-4; below 1e-4 | N=10: 1.0000001, dev 5.1e-08, N=20: 1.0000001, dev 7.7e-08, N=40: 1.0000002, dev 1.5e-07, N=80: 1.0000003, dev 3.1e-07, N=160: 1.0000006, dev 6.9e-07, N=320: 1.0000012, dev 1.6e-06, N=640: 1.0000023, dev 3.4e-06 | PASS |
| coherent_tiny | N - 3: 7, 17, 37, 77, 157, 317, 637; 1e-4 relative | N=10: 7.00000, N=20: 17.00000, N=40: 37.00001, N=80: 77.00002, N=160: 157.00010, N=320: 317.00042, N=640: 637.00169 | PASS |
| drift_tiny | 7.50173, 19.49928, 43.77809, 92.45941, 189.8802, 384.7504, 774.5056; 1e-4 relative | N=10: 7.501732, N=20: 19.49928, N=40: 43.77809, N=80: 92.45941, N=160: 189.8802, N=320: 384.7504, N=640: 774.5057 | PASS |
| symmetric_cond_tiny | 6.228720, 8.265100, 10.17282, 12.01203, 13.81435, 15.59815, 17.37261 (about 1.8 more per doubling: log N); 1e-4 relative | N=10: 6.22872, N=20: 8.2651, N=40: 10.17282, N=80: 12.01203, N=160: 13.81435, N=320: 15.59815, N=640: 17.37261 | PASS |
| cond_tiny / structured_cond_tiny / N | 0.3289, 0.3232, 0.3208, 0.3198, 0.3193, 0.3191, 0.3190; in [0.31, 0.33] | N=10: 0.3289, N=20: 0.3232, N=40: 0.3208, N=80: 0.3198, N=160: 0.3193, N=320: 0.3191, N=640: 0.3190 | PASS |
| structured_random_max | 1.48, 1.96, 2.21, 2.94, 2.41, 2.85, 3.07 (N = 10 ... 640; a max over 20 draws, not monotone); below 10 | N=10: 1.48, N=20: 1.96, N=40: 2.21, N=80: 2.94, N=160: 2.41, N=320: 2.85, N=640: 3.07 | PASS |
| structured_push | 3.8512, 4.3001, 4.5250, 4.6375, 4.6937, 4.7219, 4.7359; 1e-3 relative | N=10: 3.8512, N=20: 4.3001, N=40: 4.5250, N=80: 4.6375, N=160: 4.6937, N=320: 4.7219, N=640: 4.7359 | PASS |
| structured_cond_max / structured_random_max | grows like N: 7.7 (10), 33 (80), 254 (640); above 0.3 N | N=10: 7.7 (0.77 N), N=20: 12.2 (0.61 N), N=40: 21.8 (0.55 N), N=80: 33.0 (0.41 N), N=160: 80.8 (0.51 N), N=320: 136.6 (0.43 N), N=640: 253.7 (0.40 N) | PASS |
| baselines, stored-system methods: true_err_tiny - own_err_tiny | = data_term_tiny (-4.270e-15 at N = 20 ... -4.4153e-12 at 640, -1.7661e-11 at 1280); 1e-3 relative | 36 rows, worst deviation 1.2e-12 (N=320 splu_natural); data_term_tiny N=20: -4.2702e-15, N=40: -1.7206e-14, N=80: -6.8948e-14, N=160: -2.7592e-13, N=320: -1.1038e-12, N=640: -4.4153e-12, N=1280: -1.7661e-11 | PASS |
| baselines, ir_direct: max_true_err_in_ulp, every N up to 1280 | at most 0.5 (correctly rounded; 0.500 in the Project chat's independent refinement); 1e-6 | N=20: 0.498968, N=40: 0.499467, N=80: 0.499025, N=160: 0.499976, N=320: 0.499975, N=640: 0.499996, N=1280: 0.499999 | PASS |
| baselines, cholmod_default own_err_tiny against e07_fixes direct err_vs_stored_tiny, N >= 160 | equal (same solve, two ways of measuring: exact integers here, x_ref there); 2% | N=160: +9.071e-14 vs +9.054e-14 (+1.8e-03), N=320: +3.649e-13 vs +3.65e-13 (-3.3e-04), N=640: +1.47e-12 vs +1.47e-12 (+1.2e-04), N=1280: +5.743e-12 vs +5.743e-12 (-1.4e-05) | PASS |
| baselines, gth max_true_err_in_u against e07_fixes gth max_rel_err_in_u | equal; 1.5 u or 2%, whichever is larger | N=20: 7.60 vs 8.00 u, N=40: 11.20 vs 11.75 u, N=80: 33.91 vs 33.84 u, N=160: 45.40 vs 45.76 u, N=320: 60.29 vs 59.54 u, N=640: 199.60 vs 199.82 u | PASS |
| baselines, cholmod_default own_err_tiny | equals cholmod_simplicial for N <= 80 and cholmod_supernodal for N >= 160 (that switch is the sign flip between 80 and 160); 1e-9 relative | N=20: simplicial 0.0e+00, N=40: simplicial 0.0e+00, N=80: simplicial 0.0e+00, N=160: supernodal 0.0e+00, N=320: supernodal 0.0e+00, N=640: supernodal 0.0e+00 | PASS |
| baselines, cholmod_supernodal own_err_over_N2u, N >= 160 | +0.052, +0.052, +0.050 on Linux; expect +0.032 on the Mac; in [0.01, 0.1] | N=160: +0.0319, N=320: +0.0321, N=640: +0.0323 | PASS |
| baselines, cholmod_simplicial own_err_over_N2u, N >= 160 | -0.0056, -0.0058, -0.0066 on Linux; absolute value below 0.02 | N=160: -0.0179, N=320: -0.0207, N=640: -0.0215 | WARN |
| baselines, banded own_err_over_N2u, N >= 80 | +0.0009, +0.0014, -0.0004, -0.0048 on Linux; absolute value below 0.02 | N=80: +0.0009, N=160: +0.0001, N=320: -0.0010, N=640: -0.0054 | PASS |
| baselines, banded max_own_err_in_u | 28, 45, 40, 108, 496, 2324 on Linux; each within a factor 3 | N=20: 31, N=40: 45, N=80: 35, N=160: 91, N=320: 446, N=640: 2247 | PASS |
| baselines, splu_colamd own_err_over_N2u, N >= 80 | +0.030, +0.031, +0.033, +0.035 on Linux; in [0.005, 0.1] | N=80: +0.0325, N=160: +0.0252, N=320: +0.0273, N=640: +0.0280 | PASS |
| baselines, splu_natural own_err_over_N2u, N = 160, 320 | -0.067, -0.143 on Linux: natural order does not make SuperLU accurate; absolute value above 0.02 | N=160: -0.0481, N=320: -0.1261 | PASS |
| baselines, banded_int max_true_err_in_u | 29, 56, 49, 194, 749, 3844 on Linux (0.0094 N^2 at N = 640); each within a factor 3 | N=20: 27, N=40: 54, N=80: 67, N=160: 156, N=320: 653, N=640: 4085 | PASS |
| baselines, banded_int / banded: max_true_err_in_u at N = 640 | 0.09 on Linux (integer data removes the data term for a band solve); below 0.5 | 4085 / 41973 = 0.097 | PASS |
| baselines, gth / banded_int: max_true_err_in_u at N = 160, 320, 640 | 0.24, 0.08, 0.05 (Mac GTH over Linux band solve); below 1, decreasing | N=160: 45 / 156 = 0.291, N=320: 60 / 653 = 0.092, N=640: 200 / 4085 = 0.049 | PASS |
| baselines, cholmod_int true_err_over_N2u, N >= 160 | +0.18 on Linux: integer scaling does not help CHOLMOD (worse than the data term's 0.097); absolute value above 0.02 | N=160: +0.1385, N=320: +0.1416, N=640: +0.1421 | PASS |
| e07_floor, none: min_omega_in_u | increasing in N: 9.9 (80), 17.7 (160), 26.5 (320), 57.4 (640), 193 (1280) on Linux with independent code; the Mac run log had 312 at 1280; each within a factor 2.5 of these | N=80: 10.1 u (1.02x), N=160: 15.5 u (0.88x), N=320: 25.0 u (0.94x), N=640: 50.8 u (0.89x), N=1280: 311.8 u (1.62x); increasing: yes | PASS |
| e07_floor, none, N = 1280: min_omega | above 1e-14 (plain CG cannot reach tol 1e-14 there) | 3.46e-14 (312 u) | PASS |
| e07_floor, mic0 and amg: min_omega_in_u | at most 90 at every N (they reach tol 1e-14 in e07_fixes) | amg: N=80: 3.9 u, N=160: 4.6 u, N=320: 7.1 u, N=640: 15.1 u, N=1280: 23.9 u; mic0: N=80: 6.0 u, N=160: 9.9 u, N=320: 19.3 u, N=640: 26.0 u, N=1280: 62.2 u | PASS |
| e07_floor, none: k_at_min_over_k10 | 1.40, 1.45, 1.49, 1.61, 1.54 (Linux); in [1, 3.5]; above 3.5 means maxiter cut the run before the floor | N=80: 1.40, N=160: 1.42, N=320: 1.51, N=640: 1.54, N=1280: 1.60 | PASS |

Summary: 46 PASS, 1 WARN, 0 FAIL.

## Red flags (automatic checks of the spec's list)

| Red flag check | Observed | OK |
|---|---|---|
| refinement converged but not to the exact answer (N <= 80) | 0 of 12 converged ir rows above 2 u | yes |
| GTH error growing like N^2 (log-log slope of max_rel_err_in_u, N >= 40) | slope 0.86 (the default CHOLMOD solve grows like N^2: slope 2) | yes |
| cg_componentwise with mic0 or amg not reaching tol 1e-14 at some N, or plain CG not reaching it at N <= 640 (smallest omega: e07_floor) | all required runs converged; expected, not required: N=1280 none (final omega 360 u) | yes |
| refinement landing on the stored solution (N >= 160): GTH, which does not use refinement, must sit far closer to the refined reference than the data term | N=160: gth rel_err_tiny 2.3e-15 vs |data term| 2.8e-13, N=320: gth rel_err_tiny 4.4e-15 vs |data term| 1.1e-12, N=640: gth rel_err_tiny 1.8e-14 vs |data term| 4.4e-12 | yes |
| structured_cond_over_N outside [1.1, 1.25], or the attaining perturbation not reaching kappa, or coherent_tiny not N - 3: the formula or the perturbation is wrong (kappa itself grows like N; that is the result) | structured_cond_over_N 1.1353 to 1.2176; attained / kappa 1.0000001 to 1.0000023; coherent / (N - 3) 1.000000 to 1.000003 | yes |
| extra: every CG row converged within maxiter (excluding plain CG, tol 1e-14, N = 1280, which stalls above the tolerance: see e07_floor) | 70/70 rows | yes |

## Data (e07_fixes)

| N | n | method | kind | param | iterations_or_steps | converged | setup_seconds | seconds | reference | rel_err_tiny | max_rel_err | max_rel_err_in_u | omega | cond_tiny | data_term_tiny | err_vs_stored_tiny | max_err_vs_stored | signed_err_tiny |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | 171 | direct | nesdis |  |  | True | 0.0002543 | 0.0002731 | exact | 3.804e-15 | 4.058e-15 | 36.55 | 2.763e-16 | 153.8 | -4.27e-15 | 3.804e-16 | 7.927e-16 | -3.804e-15 |
| 20 | 171 | ir_direct | nesdis |  | 2 | True | 0.0002543 | 0.0003771 | exact | 0 | 0 | 0 | 1.199e-16 | 153.8 | -4.27e-15 | 4.185e-15 | 4.185e-15 | 0 |
| 20 | 171 | gth | natural |  |  | True |  | 0.00031 | exact | 3.804e-16 | 8.877e-16 | 7.995 | 2.655e-16 | 153.8 | -4.27e-15 | 4.565e-15 | 4.819e-15 | 3.804e-16 |
| 20 | 171 | cg | none | 1e-10 | 35 | True | 2.209e-06 | 0.0003786 | exact | 2.09e-08 | 2.09e-08 | 1.882e+08 | 6.944e-09 | 153.8 | -4.27e-15 | 2.09e-08 | 2.09e-08 | 2.09e-08 |
| 20 | 171 | cg_componentwise | none | 1e-12 | 50 | True | 2.209e-06 | 0.0006227 | exact | 3.995e-15 | 4.185e-15 | 37.69 | 4.392e-16 | 153.8 | -4.27e-15 | 1.902e-16 | 1.318e-15 | -3.995e-15 |
| 20 | 171 | cg_componentwise | none | 1e-14 | 50 | True | 2.209e-06 | 0.0006214 | exact | 3.995e-15 | 4.185e-15 | 37.69 | 4.392e-16 | 153.8 | -4.27e-15 | 1.902e-16 | 1.318e-15 | -3.995e-15 |
| 20 | 171 | cg | mic0 | 1e-10 | 14 | True | 0.0001634 | 0.0003874 | exact | 8.582e-11 | 3.527e-10 | 3.177e+06 | 6.717e-11 | 153.8 | -4.27e-15 | -8.581e-11 | 3.527e-10 | -8.582e-11 |
| 20 | 171 | cg_componentwise | mic0 | 1e-12 | 20 | True | 0.0001634 | 0.0005995 | exact | 6.277e-15 | 9.323e-15 | 83.97 | 1.921e-15 | 153.8 | -4.27e-15 | -2.092e-15 | 5.854e-15 | -6.277e-15 |
| 20 | 171 | cg_componentwise | mic0 | 1e-14 | 20 | True | 0.0001634 | 0.0005944 | exact | 6.277e-15 | 9.323e-15 | 83.97 | 1.921e-15 | 153.8 | -4.27e-15 | -2.092e-15 | 5.854e-15 | -6.277e-15 |
| 20 | 171 | ir_cg_mic0 | mic0 | 1e-06 | 3 | True | 0.0001634 | 0.0008814 | exact | 0 | 0 | 0 | 1.199e-16 | 153.8 | -4.27e-15 | 4.185e-15 | 4.185e-15 | 0 |
| 20 | 171 | cg | amg | 1e-10 | 7 | True | 0.002822 | 0.003825 | exact | 2.367e-11 | 2.431e-10 | 2.19e+06 | 1.087e-10 | 153.8 | -4.27e-15 | 2.368e-11 | 2.431e-10 | 2.367e-11 |
| 20 | 171 | cg_componentwise | amg | 1e-12 | 9 | True | 0.002822 | 0.004415 | exact | 3.479e-13 | 5.003e-13 | 4506 | 1.148e-13 | 153.8 | -4.27e-15 | -3.437e-13 | 4.962e-13 | -3.479e-13 |
| 20 | 171 | cg_componentwise | amg | 1e-14 | 10 | True | 0.002822 | 0.00462 | exact | 2.092e-15 | 8.686e-15 | 78.24 | 1.216e-15 | 153.8 | -4.27e-15 | 2.092e-15 | 5.067e-15 | -2.092e-15 |
| 20 | 171 | ir_cg_amg | amg | 1e-06 | 3 | True | 0.002822 | 0.005551 | exact | 0 | 0 | 0 | 1.199e-16 | 153.8 | -4.27e-15 | 4.185e-15 | 4.185e-15 | 0 |
| 40 | 741 | direct | nesdis |  |  | True | 0.001599 | 0.001628 | exact | 2.111e-14 | 2.111e-14 | 190.2 | 4.238e-16 | 619.9 | -1.721e-14 | -3.995e-15 | 4.427e-15 | -2.111e-14 |
| 40 | 741 | ir_direct | nesdis |  | 2 | True | 0.001599 | 0.001879 | exact | 0 | 0 | 0 | 1.285e-16 | 619.9 | -1.721e-14 | 1.712e-14 | 1.712e-14 | 0 |
| 40 | 741 | gth | natural |  |  | True |  | 0.0006416 | exact | 1.902e-16 | 1.304e-15 | 11.75 | 3.909e-16 | 619.9 | -1.721e-14 | 1.693e-14 | 1.783e-14 | -1.902e-16 |
| 40 | 741 | cg | none | 1e-10 | 72 | True | 1.333e-06 | 0.001071 | exact | 3.736e-08 | 3.736e-08 | 3.365e+08 | 4.461e-09 | 619.9 | -1.721e-14 | 3.736e-08 | 3.736e-08 | 3.736e-08 |
| 40 | 741 | cg_componentwise | none | 1e-12 | 90 | True | 1.333e-06 | 0.001584 | exact | 1.655e-14 | 2.866e-14 | 258.1 | 6.069e-15 | 619.9 | -1.721e-14 | 5.707e-16 | 1.154e-14 | -1.655e-14 |
| 40 | 741 | cg_componentwise | none | 1e-14 | 90 | True | 1.333e-06 | 0.001568 | exact | 1.655e-14 | 2.866e-14 | 258.1 | 6.069e-15 | 619.9 | -1.721e-14 | 5.707e-16 | 1.154e-14 | -1.655e-14 |
| 40 | 741 | cg | mic0 | 1e-10 | 22 | True | 0.0005102 | 0.001165 | exact | 8.012e-11 | 4.523e-10 | 4.074e+06 | 5.831e-11 | 619.9 | -1.721e-14 | 8.014e-11 | 4.523e-10 | 8.012e-11 |
| 40 | 741 | cg_componentwise | mic0 | 1e-12 | 30 | True | 0.0005102 | 0.001627 | exact | 1.579e-14 | 2.449e-14 | 220.6 | 1.426e-15 | 619.9 | -1.721e-14 | 1.332e-15 | 7.862e-15 | -1.579e-14 |
| 40 | 741 | cg_componentwise | mic0 | 1e-14 | 30 | True | 0.0005102 | 0.001601 | exact | 1.579e-14 | 2.449e-14 | 220.6 | 1.426e-15 | 619.9 | -1.721e-14 | 1.332e-15 | 7.862e-15 | -1.579e-14 |
| 40 | 741 | ir_cg_mic0 | mic0 | 1e-06 | 3 | True | 0.0005102 | 0.002627 | exact | 0 | 0 | 0 | 1.285e-16 | 619.9 | -1.721e-14 | 1.712e-14 | 1.712e-14 | 0 |
| 40 | 741 | cg | amg | 1e-10 | 8 | True | 0.004733 | 0.006754 | exact | 1.275e-09 | 1.546e-09 | 1.393e+07 | 2.236e-10 | 619.9 | -1.721e-14 | 1.275e-09 | 1.546e-09 | 1.275e-09 |
| 40 | 741 | cg_componentwise | amg | 1e-12 | 10 | True | 0.004733 | 0.007779 | exact | 2.212e-12 | 2.818e-12 | 2.539e+04 | 4.856e-13 | 619.9 | -1.721e-14 | 2.229e-12 | 2.836e-12 | 2.212e-12 |
| 40 | 741 | cg_componentwise | amg | 1e-14 | 11 | True | 0.004733 | 0.007983 | exact | 3.082e-14 | 3.397e-14 | 305.9 | 3.71e-15 | 619.9 | -1.721e-14 | -1.37e-14 | 1.758e-14 | -3.082e-14 |
| 40 | 741 | ir_cg_amg | amg | 1e-06 | 3 | True | 0.004733 | 0.00966 | exact | 0 | 0 | 0 | 1.285e-16 | 619.9 | -1.721e-14 | 1.712e-14 | 1.712e-14 | 0 |
| 60 | 1711 | direct | nesdis |  |  | True | 0.005202 | 0.005263 | exact | 4.751e-14 | 4.751e-14 | 427.9 | 5.882e-16 | 1397 | -3.877e-14 | -8.827e-15 | 9.049e-15 | -4.751e-14 |
| 60 | 1711 | ir_direct | nesdis |  | 2 | True | 0.005202 | 0.005645 | exact | 0 | 0 | 0 | 1.276e-16 | 1397 | -3.877e-14 | 3.868e-14 | 3.873e-14 | 0 |
| 60 | 1711 | gth | natural |  |  | True |  | 0.002171 | exact | 8.025e-16 | 2.739e-15 | 24.67 | 3.824e-16 | 1397 | -3.877e-14 | 3.948e-14 | 4.006e-14 | 8.025e-16 |
| 60 | 1711 | cg | none | 1e-10 | 107 | True | 1.083e-06 | 0.002388 | exact | 4.925e-08 | 6.016e-08 | 5.419e+08 | 8.521e-09 | 1397 | -3.877e-14 | 4.925e-08 | 6.016e-08 | 4.925e-08 |
| 60 | 1711 | cg_componentwise | none | 1e-12 | 130 | True | 1.083e-06 | 0.003816 | exact | 2.825e-13 | 1.199e-12 | 1.08e+04 | 7.408e-13 | 1397 | -3.877e-14 | -2.438e-13 | 1.238e-12 | -2.825e-13 |
| 60 | 1711 | cg_componentwise | none | 1e-14 | 140 | True | 1.083e-06 | 0.00406 | exact | 5.152e-14 | 5.152e-14 | 464 | 5.483e-15 | 1397 | -3.877e-14 | -1.284e-14 | 1.284e-14 | -5.152e-14 |
| 60 | 1711 | cg | mic0 | 1e-10 | 27 | True | 0.0005102 | 0.00197 | exact | 1.278e-10 | 5.893e-10 | 5.308e+06 | 1.155e-10 | 1397 | -3.877e-14 | 1.278e-10 | 5.893e-10 | 1.278e-10 |
| 60 | 1711 | cg_componentwise | mic0 | 1e-12 | 35 | True | 0.0005102 | 0.002765 | exact | 2.687e-13 | 4.744e-13 | 4273 | 7.032e-14 | 1397 | -3.877e-14 | -2.3e-13 | 4.363e-13 | -2.687e-13 |
| 60 | 1711 | cg_componentwise | mic0 | 1e-14 | 40 | True | 0.0005102 | 0.00308 | exact | 3.675e-14 | 3.702e-14 | 333.5 | 8.084e-16 | 1397 | -3.877e-14 | 1.926e-15 | 6.953e-15 | -3.675e-14 |
| 60 | 1711 | ir_cg_mic0 | mic0 | 1e-06 | 3 | True | 0.0005102 | 0.004487 | exact | 0 | 0 | 0 | 1.276e-16 | 1397 | -3.877e-14 | 3.868e-14 | 3.873e-14 | 0 |
| 60 | 1711 | cg | amg | 1e-10 | 9 | True | 0.006847 | 0.01056 | exact | 1.285e-09 | 1.824e-09 | 1.643e+07 | 3.477e-10 | 1397 | -3.877e-14 | -1.285e-09 | 1.824e-09 | -1.285e-09 |
| 60 | 1711 | cg_componentwise | amg | 1e-12 | 12 | True | 0.006847 | 0.01212 | exact | 6.617e-13 | 7.356e-13 | 6625 | 1.071e-13 | 1397 | -3.877e-14 | 7.004e-13 | 7.742e-13 | 6.617e-13 |
| 60 | 1711 | cg_componentwise | amg | 1e-14 | 13 | True | 0.006847 | 0.0125 | exact | 5.89e-14 | 6.142e-14 | 553.2 | 2.131e-15 | 1397 | -3.877e-14 | -2.022e-14 | 2.268e-14 | -5.89e-14 |
| 60 | 1711 | ir_cg_amg | amg | 1e-06 | 3 | True | 0.006847 | 0.01593 | exact | 0 | 0 | 0 | 1.276e-16 | 1397 | -3.877e-14 | 3.868e-14 | 3.873e-14 | 0 |
| 80 | 3081 | direct | nesdis |  |  | True | 0.009844 | 0.009953 | exact | 9.416e-14 | 9.416e-14 | 848.1 | 7.636e-16 | 2484 | -6.895e-14 | -2.53e-14 | 2.645e-14 | -9.416e-14 |
| 80 | 3081 | ir_direct | nesdis |  | 2 | True | 0.009844 | 0.01076 | exact | 0 | 0 | 0 | 1.385e-16 | 2484 | -6.895e-14 | 6.886e-14 | 6.899e-14 | 0 |
| 80 | 3081 | gth | natural |  |  | True |  | 0.006681 | exact | 3.234e-15 | 3.757e-15 | 33.84 | 5.511e-16 | 2484 | -6.895e-14 | 7.209e-14 | 7.244e-14 | 3.234e-15 |
| 80 | 3081 | cg | none | 1e-10 | 143 | True | 8.75e-07 | 0.004536 | exact | 2.534e-08 | 8.491e-08 | 7.648e+08 | 5.512e-08 | 2484 | -6.895e-14 | -2.534e-08 | 8.491e-08 | -2.534e-08 |
| 80 | 3081 | cg_componentwise | none | 1e-12 | 180 | True | 8.75e-07 | 0.006767 | exact | 2.557e-13 | 2.557e-13 | 2303 | 1.068e-13 | 2484 | -6.895e-14 | -1.868e-13 | 1.868e-13 | -2.557e-13 |
| 80 | 3081 | cg_componentwise | none | 1e-14 | 190 | True | 8.75e-07 | 0.007328 | exact | 6.943e-14 | 6.943e-14 | 625.4 | 2.522e-15 | 2484 | -6.895e-14 | -5.707e-16 | 6.957e-15 | -6.943e-14 |
| 80 | 3081 | cg | mic0 | 1e-10 | 31 | True | 0.0007298 | 0.003473 | exact | 7.64e-11 | 1.272e-09 | 1.146e+07 | 2.405e-10 | 2484 | -6.895e-14 | -7.633e-11 | 1.272e-09 | -7.64e-11 |
| 80 | 3081 | cg_componentwise | mic0 | 1e-12 | 40 | True | 0.0007298 | 0.004862 | exact | 3.631e-13 | 1.843e-12 | 1.66e+04 | 3.871e-13 | 2484 | -6.895e-14 | -2.943e-13 | 1.775e-12 | -3.631e-13 |
| 80 | 3081 | cg_componentwise | mic0 | 1e-14 | 45 | True | 0.0007298 | 0.005355 | exact | 8.046e-14 | 9.054e-14 | 815.6 | 4.939e-15 | 2484 | -6.895e-14 | -1.16e-14 | 2.479e-14 | -8.046e-14 |
| 80 | 3081 | ir_cg_mic0 | mic0 | 1e-06 | 3 | True | 0.0007298 | 0.008326 | exact | 0 | 0 | 0 | 1.385e-16 | 2484 | -6.895e-14 | 6.886e-14 | 6.899e-14 | 0 |
| 80 | 3081 | cg | amg | 1e-10 | 9 | True | 0.008106 | 0.01304 | exact | 9.58e-09 | 1.037e-08 | 9.339e+07 | 1.798e-09 | 2484 | -6.895e-14 | 9.58e-09 | 1.037e-08 | 9.58e-09 |
| 80 | 3081 | cg_componentwise | amg | 1e-12 | 13 | True | 0.008106 | 0.01652 | exact | 2.051e-12 | 2.245e-12 | 2.022e+04 | 2.493e-13 | 2484 | -6.895e-14 | -1.982e-12 | 2.176e-12 | -2.051e-12 |
| 80 | 3081 | cg_componentwise | amg | 1e-14 | 15 | True | 0.008106 | 0.01745 | exact | 6.81e-14 | 6.848e-14 | 616.8 | 6.182e-16 | 2484 | -6.895e-14 | 7.609e-16 | 7.747e-15 | -6.81e-14 |
| 80 | 3081 | ir_cg_amg | amg | 1e-06 | 3 | True | 0.008106 | 0.0214 | exact | 0 | 0 | 0 | 1.385e-16 | 2484 | -6.895e-14 | 6.886e-14 | 6.899e-14 | 0 |
| 160 | 12561 | direct | nesdis |  |  | True | 0.05245 | 0.05298 | refined | 1.853e-13 | 1.853e-13 | 1669 | 6.234e-16 | 9941 | -2.759e-13 | 9.054e-14 | 9.116e-14 | -1.853e-13 |
| 160 | 12561 | ir_direct | nesdis |  | 2 | True | 0.05245 | 0.05523 | refined | 0 | 0 | 0 | 1.429e-16 | 9941 | -2.759e-13 | 2.758e-13 | 2.759e-13 | 0 |
| 160 | 12561 | gth | natural |  |  | True |  | 0.09395 | refined | 2.283e-15 | 5.081e-15 | 45.76 | 9.658e-16 | 9941 | -2.759e-13 | 2.781e-13 | 2.789e-13 | 2.283e-15 |
| 160 | 12561 | cg | none | 1e-10 | 282 | True | 9.59e-07 | 0.02855 | refined | 6.802e-07 | 6.802e-07 | 6.127e+09 | 3.721e-07 | 9941 | -2.759e-13 | 6.802e-07 | 6.802e-07 | 6.802e-07 |
| 160 | 12561 | cg_componentwise | none | 1e-12 | 350 | True | 9.59e-07 | 0.04613 | refined | 5.691e-13 | 1.177e-12 | 1.061e+04 | 8.139e-13 | 9941 | -2.759e-13 | -2.933e-13 | 1.453e-12 | -5.691e-13 |
| 160 | 12561 | cg_componentwise | none | 1e-14 | 380 | True | 9.59e-07 | 0.04618 | refined | 2.463e-13 | 2.629e-13 | 2368 | 7.876e-15 | 9941 | -2.759e-13 | 2.948e-14 | 2.948e-14 | -2.463e-13 |
| 160 | 12561 | cg | mic0 | 1e-10 | 45 | True | 0.002762 | 0.01769 | refined | 5.278e-09 | 7.845e-09 | 7.066e+07 | 1.56e-09 | 9941 | -2.759e-13 | 5.278e-09 | 7.845e-09 | 5.278e-09 |
| 160 | 12561 | cg_componentwise | mic0 | 1e-12 | 60 | True | 0.002762 | 0.02539 | refined | 1.838e-12 | 4.146e-12 | 3.734e+04 | 7.72e-13 | 9941 | -2.759e-13 | -1.562e-12 | 3.87e-12 | -1.838e-12 |
| 160 | 12561 | cg_componentwise | mic0 | 1e-14 | 75 | True | 0.002762 | 0.03178 | refined | 2.408e-13 | 2.427e-13 | 2186 | 1.15e-15 | 9941 | -2.759e-13 | 3.5e-14 | 3.952e-14 | -2.408e-13 |
| 160 | 12561 | ir_cg_mic0 | mic0 | 1e-06 | 3 | True | 0.002762 | 0.04392 | refined | 0 | 0 | 0 | 1.429e-16 | 9941 | -2.759e-13 | 2.758e-13 | 2.759e-13 | 0 |
| 160 | 12561 | cg | amg | 1e-10 | 10 | True | 0.02163 | 0.04024 | refined | 1.33e-07 | 1.434e-07 | 1.292e+09 | 1.676e-08 | 9941 | -2.759e-13 | -1.33e-07 | 1.434e-07 | -1.33e-07 |
| 160 | 12561 | cg_componentwise | amg | 1e-12 | 15 | True | 0.02163 | 0.05311 | refined | 2.562e-12 | 2.786e-12 | 2.509e+04 | 2.687e-13 | 9941 | -2.759e-13 | -2.287e-12 | 2.51e-12 | -2.562e-12 |
| 160 | 12561 | cg_componentwise | amg | 1e-14 | 17 | True | 0.02163 | 0.0583 | refined | 2.804e-13 | 2.82e-13 | 2540 | 2.266e-15 | 9941 | -2.759e-13 | -4.565e-15 | 2.858e-14 | -2.804e-13 |
| 160 | 12561 | ir_cg_amg | amg | 1e-06 | 3 | True | 0.02163 | 0.06894 | refined | 0 | 1.264e-16 | 1.138 | 1.429e-16 | 9941 | -2.759e-13 | 2.758e-13 | 2.759e-13 | 0 |
| 320 | 50721 | direct | nesdis |  |  | True | 0.2709 | 0.2737 | refined | 7.388e-13 | 7.396e-13 | 6661 | 1.154e-15 | 3.977e+04 | -1.104e-12 | 3.65e-13 | 3.652e-13 | -7.388e-13 |
| 320 | 50721 | ir_direct | nesdis |  | 2 | True | 0.2709 | 0.2854 | refined | 0 | 0 | 0 | 1.554e-16 | 3.977e+04 | -1.104e-12 | 1.104e-12 | 1.104e-12 | 0 |
| 320 | 50721 | gth | natural |  |  | True |  | 1.365 | refined | 4.375e-15 | 6.61e-15 | 59.54 | 1.269e-15 | 3.977e+04 | -1.104e-12 | 1.108e-12 | 1.109e-12 | 4.375e-15 |
| 320 | 50721 | cg | none | 1e-10 | 556 | True | 1.209e-06 | 0.203 | refined | 5.793e-06 | 5.793e-06 | 5.218e+10 | 3.648e-06 | 3.977e+04 | -1.104e-12 | 5.793e-06 | 5.793e-06 | 5.793e-06 |
| 320 | 50721 | cg_componentwise | none | 1e-12 | 710 | True | 1.209e-06 | 0.327 | refined | 1.193e-12 | 1.377e-12 | 1.241e+04 | 3.692e-13 | 3.977e+04 | -1.104e-12 | -8.921e-14 | 6.523e-13 | -1.193e-12 |
| 320 | 50721 | cg_componentwise | none | 1e-14 | 760 | True | 1.209e-06 | 0.3545 | refined | 1.024e-12 | 1.042e-12 | 9388 | 7.269e-15 | 3.977e+04 | -1.104e-12 | 7.989e-14 | 8.084e-14 | -1.024e-12 |
| 320 | 50721 | cg | mic0 | 1e-10 | 66 | True | 0.01037 | 0.09777 | refined | 3.746e-09 | 3.086e-08 | 2.78e+08 | 5.959e-09 | 3.977e+04 | -1.104e-12 | 3.747e-09 | 3.086e-08 | 3.746e-09 |
| 320 | 50721 | cg_componentwise | mic0 | 1e-12 | 95 | True | 0.01037 | 0.1588 | refined | 1.102e-12 | 3.591e-12 | 3.234e+04 | 5.677e-13 | 3.977e+04 | -1.104e-12 | 2.206e-12 | 3.323e-12 | 1.102e-12 |
| 320 | 50721 | cg_componentwise | mic0 | 1e-14 | 110 | True | 0.01037 | 0.1846 | refined | 1.003e-12 | 1.006e-12 | 9064 | 6.193e-15 | 3.977e+04 | -1.104e-12 | 1.004e-13 | 1.384e-13 | -1.003e-12 |
| 320 | 50721 | ir_cg_mic0 | mic0 | 1e-06 | 3 | True | 0.01037 | 0.244 | refined | 0 | 0 | 0 | 1.554e-16 | 3.977e+04 | -1.104e-12 | 1.104e-12 | 1.104e-12 | 0 |
| 320 | 50721 | cg | amg | 1e-10 | 13 | True | 0.07273 | 0.1612 | refined | 1.913e-07 | 2.031e-07 | 1.829e+09 | 1.815e-08 | 3.977e+04 | -1.104e-12 | 1.913e-07 | 2.031e-07 | 1.913e-07 |
| 320 | 50721 | cg_componentwise | amg | 1e-12 | 19 | True | 0.07273 | 0.2292 | refined | 7.139e-12 | 7.739e-12 | 6.971e+04 | 6.387e-13 | 3.977e+04 | -1.104e-12 | -6.035e-12 | 6.635e-12 | -7.139e-12 |
| 320 | 50721 | cg_componentwise | amg | 1e-14 | 22 | True | 0.07273 | 0.2493 | refined | 9.52e-13 | 9.823e-13 | 8848 | 1.622e-15 | 3.977e+04 | -1.104e-12 | 1.518e-13 | 1.529e-13 | -9.52e-13 |
| 320 | 50721 | ir_cg_amg | amg | 1e-06 | 3 | True | 0.07273 | 0.2904 | refined | 0 | 0 | 0 | 1.554e-16 | 3.977e+04 | -1.104e-12 | 1.104e-12 | 1.104e-12 | 0 |
| 640 | 203841 | direct | nesdis |  |  | True | 1.337 | 1.351 | refined | 2.945e-12 | 2.945e-12 | 2.653e+04 | 1.486e-15 | 1.591e+05 | -4.415e-12 | 1.47e-12 | 1.471e-12 | -2.945e-12 |
| 640 | 203841 | ir_direct | nesdis |  | 2 | True | 1.337 | 1.407 | refined | 0 | 0 | 0 | 1.568e-16 | 1.591e+05 | -4.415e-12 | 4.415e-12 | 4.415e-12 | 0 |
| 640 | 203841 | gth | natural |  |  | True |  | 20.77 | refined | 1.769e-14 | 2.218e-14 | 199.8 | 2.017e-15 | 1.591e+05 | -4.415e-12 | 4.433e-12 | 4.433e-12 | 1.769e-14 |
| 640 | 203841 | cg | none | 1e-10 | 1094 | True | 1.459e-06 | 1.592 | refined | 1.425e-05 | 1.425e-05 | 1.283e+11 | 8.951e-06 | 1.591e+05 | -4.415e-12 | 1.425e-05 | 1.425e-05 | 1.425e-05 |
| 640 | 203841 | cg_componentwise | none | 1e-12 | 1450 | True | 1.459e-06 | 2.785 | refined | 3.014e-12 | 4.902e-12 | 4.416e+04 | 7.09e-13 | 1.591e+05 | -4.415e-12 | 1.402e-12 | 1.402e-12 | -3.014e-12 |
| 640 | 203841 | cg_componentwise | none | 1e-14 | 1630 | True | 1.459e-06 | 3.085 | refined | 4.119e-12 | 4.142e-12 | 3.731e+04 | 9.901e-15 | 1.591e+05 | -4.415e-12 | 2.966e-13 | 3.054e-13 | -4.119e-12 |
| 640 | 203841 | cg | mic0 | 1e-10 | 95 | True | 0.04777 | 0.561 | refined | 8.181e-08 | 1.485e-07 | 1.338e+09 | 3.049e-08 | 1.591e+05 | -4.415e-12 | -8.181e-08 | 1.485e-07 | -8.181e-08 |
| 640 | 203841 | cg_componentwise | mic0 | 1e-12 | 150 | True | 0.04777 | 1.045 | refined | 4.906e-12 | 5.109e-12 | 4.602e+04 | 3.87e-13 | 1.591e+05 | -4.415e-12 | -4.911e-13 | 2.54e-12 | -4.906e-12 |
| 640 | 203841 | cg_componentwise | mic0 | 1e-14 | 170 | True | 0.04777 | 1.18 | refined | 3.735e-12 | 3.763e-12 | 3.389e+04 | 4.825e-15 | 1.591e+05 | -4.415e-12 | 6.802e-13 | 7.034e-13 | -3.735e-12 |
| 640 | 203841 | ir_cg_mic0 | mic0 | 1e-06 | 4 | True | 0.04777 | 1.75 | refined | 0 | 0 | 0 | 1.568e-16 | 1.591e+05 | -4.415e-12 | 4.415e-12 | 4.415e-12 | 0 |
| 640 | 203841 | cg | amg | 1e-10 | 14 | True | 0.2839 | 0.6613 | refined | 1.63e-06 | 1.736e-06 | 1.564e+10 | 1.605e-07 | 1.591e+05 | -4.415e-12 | -1.63e-06 | 1.736e-06 | -1.63e-06 |
| 640 | 203841 | cg_componentwise | amg | 1e-12 | 24 | True | 0.2839 | 1.092 | refined | 1.746e-12 | 3.894e-12 | 3.508e+04 | 1.488e-13 | 1.591e+05 | -4.415e-12 | 2.669e-12 | 2.815e-12 | -1.746e-12 |
| 640 | 203841 | cg_componentwise | amg | 1e-14 | 26 | True | 0.2839 | 1.15 | refined | 3.795e-12 | 3.871e-12 | 3.487e+04 | 8.95e-15 | 1.591e+05 | -4.415e-12 | 6.197e-13 | 6.229e-13 | -3.795e-12 |
| 640 | 203841 | ir_cg_amg | amg | 1e-06 | 4 | True | 0.2839 | 1.467 | refined | 0 | 2.147e-16 | 1.934 | 1.568e-16 | 1.591e+05 | -4.415e-12 | 4.415e-12 | 4.415e-12 | 0 |
| 1280 | 817281 | direct | nesdis |  |  | True | 6.461 | 6.519 | refined | 1.192e-11 | 1.192e-11 | 1.074e+05 | 1.905e-15 | 6.363e+05 | -1.766e-11 | 5.743e-12 | 5.743e-12 | -1.192e-11 |
| 1280 | 817281 | ir_direct | nesdis |  | 2 | True | 6.461 | 6.805 | refined | 0 | 0 | 0 | 1.603e-16 | 6.363e+05 | -1.766e-11 | 1.766e-11 | 1.766e-11 | 0 |
| 1280 | 817281 | cg | none | 1e-10 | 2147 | True | 1.25e-06 | 17.01 | refined | 9.608e-05 | 9.608e-05 | 8.654e+11 | 5.767e-05 | 6.363e+05 | -1.766e-11 | 9.608e-05 | 9.608e-05 | 9.608e-05 |
| 1280 | 817281 | cg_componentwise | none | 1e-12 | 3150 | True | 1.25e-06 | 35.05 | refined | 1.57e-11 | 1.649e-11 | 1.486e+05 | 3.554e-13 | 6.363e+05 | -1.766e-11 | 1.966e-12 | 1.966e-12 | -1.57e-11 |
| 1280 | 817281 | cg_componentwise | none | 1e-14 | 30000 | False | 1.25e-06 | 323.9 | refined | 1.637e-11 | 1.64e-11 | 1.477e+05 | 4e-14 | 6.363e+05 | -1.766e-11 | 1.293e-12 | 1.371e-12 | -1.637e-11 |
| 1280 | 817281 | cg | mic0 | 1e-10 | 137 | True | 0.2199 | 3.579 | refined | 4.452e-07 | 7.032e-07 | 6.334e+09 | 8.846e-08 | 6.363e+05 | -1.766e-11 | -4.452e-07 | 7.032e-07 | -4.452e-07 |
| 1280 | 817281 | cg_componentwise | mic0 | 1e-12 | 225 | True | 0.2199 | 6.59 | refined | 1.554e-11 | 1.97e-11 | 1.774e+05 | 8.379e-13 | 6.363e+05 | -1.766e-11 | 2.125e-12 | 4.501e-12 | -1.554e-11 |
| 1280 | 817281 | cg_componentwise | mic0 | 1e-14 | 260 | True | 0.2199 | 7.784 | refined | 1.507e-11 | 1.519e-11 | 1.368e+05 | 7.12e-15 | 6.363e+05 | -1.766e-11 | 2.593e-12 | 2.711e-12 | -1.507e-11 |
| 1280 | 817281 | ir_cg_mic0 | mic0 | 1e-06 | 4 | True | 0.2199 | 11.09 | refined | 0 | 2.198e-16 | 1.98 | 1.603e-16 | 6.363e+05 | -1.766e-11 | 1.766e-11 | 1.766e-11 | 0 |
| 1280 | 817281 | cg | amg | 1e-10 | 19 | True | 1.226 | 3.387 | refined | 1.423e-06 | 1.879e-06 | 1.693e+10 | 3.206e-07 | 6.363e+05 | -1.766e-11 | -1.423e-06 | 1.879e-06 | -1.423e-06 |
| 1280 | 817281 | cg_componentwise | amg | 1e-12 | 31 | True | 1.226 | 5.601 | refined | 1.811e-11 | 1.826e-11 | 1.645e+05 | 3.619e-13 | 6.363e+05 | -1.766e-11 | -4.464e-13 | 2.074e-12 | -1.811e-11 |
| 1280 | 817281 | cg_componentwise | amg | 1e-14 | 34 | True | 1.226 | 6.023 | refined | 1.573e-11 | 1.576e-11 | 1.419e+05 | 7.111e-15 | 6.363e+05 | -1.766e-11 | 1.935e-12 | 1.942e-12 | -1.573e-11 |
| 1280 | 817281 | ir_cg_amg | amg | 1e-06 | 4 | True | 1.226 | 7.435 | refined | 0 | 2.198e-16 | 1.98 | 1.603e-16 | 6.363e+05 | -1.766e-11 | 1.766e-11 | 1.766e-11 | 0 |

## Data (e07_structured)

| N | n | structured_random_max | structured_push | cond_max | two_n_minus_1 | eps | draws |
|---|---|---|---|---|---|---|---|
| 10 | 36 | 1.476 | 3.851 | 37.33 | 71 | 1e-08 | 20 |
| 20 | 171 | 1.959 | 4.3 | 153.8 | 341 | 1e-08 | 20 |
| 40 | 741 | 2.211 | 4.525 | 619.9 | 1481 | 1e-08 | 20 |
| 80 | 3081 | 2.942 | 4.637 | 2484 | 6161 | 1e-08 | 20 |
| 160 | 12561 | 2.407 | 4.694 | 9941 | 25121 | 1e-08 | 20 |
| 320 | 50721 | 2.851 | 4.722 | 3.977e+04 | 101441 | 1e-08 | 20 |
| 640 | 203841 | 3.071 | 4.736 | 1.591e+05 | 407681 | 1e-08 | 20 |

| N | structured_cond_tiny | structured_cond_max | structured_argmax_state | structured_cond_over_N | attained_tiny | attained_max_dev | coherent_tiny | drift_tiny | symmetric_cond_tiny | cond_tiny |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 11.35 | 11.35 | (1, 1, 8) | 1.135 | 11.35 | 5.073e-08 | 7 | 7.502 | 6.229 | 37.33 |
| 20 | 23.8 | 23.8 | (1, 1, 18) | 1.19 | 23.8 | 7.742e-08 | 17 | 19.5 | 8.265 | 153.8 |
| 40 | 48.3 | 48.3 | (1, 1, 38) | 1.208 | 48.3 | 1.545e-07 | 37 | 43.78 | 10.17 | 619.9 |
| 80 | 97.1 | 97.1 | (1, 1, 78) | 1.214 | 97.1 | 3.086e-07 | 77 | 92.46 | 12.01 | 2484 |
| 160 | 194.6 | 194.6 | (1, 1, 158) | 1.216 | 194.6 | 6.867e-07 | 157 | 189.9 | 13.81 | 9941 |
| 320 | 389.5 | 389.5 | (1, 1, 318) | 1.217 | 389.5 | 1.56e-06 | 317 | 384.8 | 15.6 | 3.977e+04 |
| 640 | 779.2 | 779.2 | (1, 1, 638) | 1.218 | 779.2 | 3.4e-06 | 637 | 774.5 | 17.37 | 1.591e+05 |

## Data (e07_baselines)

| N | n | method | own_err_tiny | own_err_over_N2u | max_own_err_in_u | true_err_tiny | true_err_over_N2u | max_true_err_in_u | max_true_err_in_ulp | data_term_tiny | seconds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | 171 | cholmod_default | 4.228e-16 | 0.009521 | 7.097 | -3.847e-15 | -0.08664 | 36.37 | 31.84 | -4.27e-15 | 0.02785 |
| 20 | 171 | cholmod_simplicial | 4.228e-16 | 0.009521 | 7.097 | -3.847e-15 | -0.08664 | 36.37 | 31.84 | -4.27e-15 | 0.0004175 |
| 20 | 171 | cholmod_supernodal | -1.478e-16 | -0.003329 | 5.966 | -4.418e-15 | -0.09949 | 41.18 | 36.63 | -4.27e-15 | 0.000926 |
| 20 | 171 | splu_colamd | 4.237e-17 | 0.000954 | 6.365 | -4.228e-15 | -0.0952 | 38.65 | 33.84 | -4.27e-15 | 0.0007962 |
| 20 | 171 | splu_natural | 1.374e-15 | 0.03094 | 18.47 | -2.896e-15 | -0.06522 | 27.66 | 23.06 | -4.27e-15 | 0.0004792 |
| 20 | 171 | banded | 2.896e-15 | 0.0652 | 30.76 | -1.375e-15 | -0.03095 | 16.33 | 13.67 | -4.27e-15 | 0.0005953 |
| 20 | 171 | banded_int |  |  |  | 2.239e-15 | 0.05043 | 27.46 | 25.37 | -4.27e-15 | 0.0004587 |
| 20 | 171 | cholmod_int |  |  |  | 8.517e-15 | 0.1918 | 80.66 | 76.37 | -4.27e-15 | 0.000482 |
| 20 | 171 | gth |  |  |  | 3.373e-16 | 0.007596 | 7.599 | 6.653 | -4.27e-15 | 0.0003783 |
| 20 | 171 | ir_direct |  |  |  | -4.309e-17 | -0.0009703 | 0.8443 | 0.499 | -4.27e-15 | 0.02816 |
| 40 | 741 | cholmod_default | -3.838e-15 | -0.02161 | 38.84 | -2.104e-14 | -0.1185 | 189.5 | 183.3 | -1.721e-14 | 0.002487 |
| 40 | 741 | cholmod_simplicial | -3.838e-15 | -0.02161 | 38.84 | -2.104e-14 | -0.1185 | 189.5 | 183.3 | -1.721e-14 | 0.00174 |
| 40 | 741 | cholmod_supernodal | 3.581e-15 | 0.02016 | 35.22 | -1.363e-14 | -0.0767 | 122.7 | 117.3 | -1.721e-14 | 0.001941 |
| 40 | 741 | splu_colamd | 2.059e-15 | 0.01159 | 36.86 | -1.515e-14 | -0.08527 | 137.6 | 133.3 | -1.721e-14 | 0.002092 |
| 40 | 741 | splu_natural | 5.673e-15 | 0.03194 | 61.2 | -1.153e-14 | -0.06492 | 116.7 | 104.4 | -1.721e-14 | 0.001801 |
| 40 | 741 | banded | 3.2e-15 | 0.01802 | 45.24 | -1.401e-14 | -0.07884 | 132.8 | 118.4 | -1.721e-14 | 0.0008923 |
| 40 | 741 | banded_int |  |  |  | -5.826e-15 | -0.0328 | 54.19 | 47.44 | -1.721e-14 | 0.001007 |
| 40 | 741 | cholmod_int |  |  |  | 3.659e-14 | 0.206 | 334.3 | 324.7 | -1.721e-14 | 0.001843 |
| 40 | 741 | gth |  |  |  | -1.196e-16 | -0.0006733 | 11.2 | 9.396 | -1.721e-14 | 0.0007728 |
| 40 | 741 | ir_direct |  |  |  | 7.062e-17 | 0.0003976 | 0.9894 | 0.4995 | -1.721e-14 | 0.002882 |
| 80 | 3081 | cholmod_default | -2.525e-14 | -0.03553 | 238.1 | -9.42e-14 | -0.1326 | 848.4 | 830.1 | -6.895e-14 | 0.009519 |
| 80 | 3081 | cholmod_simplicial | -2.525e-14 | -0.03553 | 238.1 | -9.42e-14 | -0.1326 | 848.4 | 830.1 | -6.895e-14 | 0.009742 |
| 80 | 3081 | cholmod_supernodal | 3.144e-14 | 0.04424 | 284.5 | -3.751e-14 | -0.05279 | 339.6 | 332.1 | -6.895e-14 | 0.009943 |
| 80 | 3081 | splu_colamd | 2.307e-14 | 0.03246 | 228.4 | -4.588e-14 | -0.06457 | 413.8 | 403.1 | -6.895e-14 | 0.009773 |
| 80 | 3081 | splu_natural | -1.555e-14 | -0.02188 | 166.9 | -8.45e-14 | -0.1189 | 767.7 | 748.1 | -6.895e-14 | 0.0145 |
| 80 | 3081 | banded | 6.211e-16 | 0.0008741 | 34.56 | -6.833e-14 | -0.09616 | 617.6 | 602.1 | -6.895e-14 | 0.004855 |
| 80 | 3081 | banded_int |  |  |  | 3.576e-15 | 0.005033 | 67.01 | 60.86 | -6.895e-14 | 0.00503 |
| 80 | 3081 | cholmod_int |  |  |  | 1.828e-13 | 0.2572 | 1652 | 1623 | -6.895e-14 | 0.009894 |
| 80 | 3081 | gth |  |  |  | 3.196e-15 | 0.004497 | 33.91 | 31.12 | -6.895e-14 | 0.006601 |
| 80 | 3081 | ir_direct |  |  |  | -3.815e-17 | -5.37e-05 | 0.9568 | 0.499 | -6.895e-14 | 0.01018 |
| 160 | 12561 | cholmod_default | 9.071e-14 | 0.03192 | 821 | -1.852e-13 | -0.06516 | 1669 | 1641 | -2.759e-13 | 0.05206 |
| 160 | 12561 | cholmod_simplicial | -5.081e-14 | -0.01788 | 469.4 | -3.267e-13 | -0.115 | 2944 | 2896 | -2.759e-13 | 0.05638 |
| 160 | 12561 | cholmod_supernodal | 9.071e-14 | 0.03192 | 821 | -1.852e-13 | -0.06516 | 1669 | 1641 | -2.759e-13 | 0.0526 |
| 160 | 12561 | splu_colamd | 7.169e-14 | 0.02522 | 669.7 | -2.042e-13 | -0.07186 | 1840 | 1810 | -2.759e-13 | 0.05475 |
| 160 | 12561 | splu_natural | -1.368e-13 | -0.04813 | 1247 | -4.127e-13 | -0.1452 | 3724 | 3657 | -2.759e-13 | 0.1601 |
| 160 | 12561 | banded | 3.57e-16 | 0.0001256 | 90.66 | -2.756e-13 | -0.09695 | 2489 | 2443 | -2.759e-13 | 0.04219 |
| 160 | 12561 | banded_int |  |  |  | -8.302e-15 | -0.002921 | 156.1 | 150.1 | -2.759e-13 | 0.04471 |
| 160 | 12561 | cholmod_int |  |  |  | 3.936e-13 | 0.1385 | 3546 | 3486 | -2.759e-13 | 0.05181 |
| 160 | 12561 | gth |  |  |  | 2.351e-15 | 0.0008271 | 45.4 | 41.89 | -2.759e-13 | 0.09353 |
| 160 | 12561 | ir_direct |  |  |  | 6.816e-17 | 2.398e-05 | 0.9743 | 0.5 | -2.759e-13 | 0.05466 |
| 320 | 50721 | cholmod_default | 3.649e-13 | 0.0321 | 3290 | -7.389e-13 | -0.06499 | 6661 | 6613 | -1.104e-12 | 0.2642 |
| 320 | 50721 | cholmod_simplicial | -2.352e-13 | -0.02069 | 2137 | -1.339e-12 | -0.1178 | 1.206e+04 | 1.197e+04 | -1.104e-12 | 0.3216 |
| 320 | 50721 | cholmod_supernodal | 3.649e-13 | 0.0321 | 3290 | -7.389e-13 | -0.06499 | 6661 | 6613 | -1.104e-12 | 0.27 |
| 320 | 50721 | splu_colamd | 3.099e-13 | 0.02726 | 2813 | -7.939e-13 | -0.06983 | 7151 | 7071 | -1.104e-12 | 0.372 |
| 320 | 50721 | splu_natural | -1.434e-12 | -0.1261 | 1.294e+04 | -2.538e-12 | -0.2232 | 2.287e+04 | 2.269e+04 | -1.104e-12 | 2.191 |
| 320 | 50721 | banded | -1.135e-14 | -0.0009979 | 445.9 | -1.115e-12 | -0.09809 | 1.005e+04 | 9967 | -1.104e-12 | 0.4808 |
| 320 | 50721 | banded_int |  |  |  | -6.893e-14 | -0.006063 | 653.4 | 636.8 | -1.104e-12 | 0.4337 |
| 320 | 50721 | cholmod_int |  |  |  | 1.61e-12 | 0.1416 | 1.45e+04 | 1.436e+04 | -1.104e-12 | 0.2716 |
| 320 | 50721 | gth |  |  |  | 4.304e-15 | 0.0003786 | 60.29 | 54.57 | -1.104e-12 | 1.382 |
| 320 | 50721 | ir_direct |  |  |  | -7.091e-17 | -6.237e-06 | 0.9937 | 0.5 | -1.104e-12 | 0.2761 |
| 640 | 203841 | cholmod_default | 1.47e-12 | 0.03233 | 1.325e+04 | -2.945e-12 | -0.06476 | 2.653e+04 | 2.64e+04 | -4.415e-12 | 1.339 |
| 640 | 203841 | cholmod_simplicial | -9.795e-13 | -0.02154 | 8833 | -5.395e-12 | -0.1186 | 4.859e+04 | 4.835e+04 | -4.415e-12 | 1.808 |
| 640 | 203841 | cholmod_supernodal | 1.47e-12 | 0.03233 | 1.325e+04 | -2.945e-12 | -0.06476 | 2.653e+04 | 2.64e+04 | -4.415e-12 | 1.44 |
| 640 | 203841 | splu_colamd | 1.273e-12 | 0.02799 | 1.149e+04 | -3.143e-12 | -0.06911 | 2.831e+04 | 2.815e+04 | -4.415e-12 | 3.792 |
| 640 | 203841 | banded | -2.441e-13 | -0.005367 | 2247 | -4.659e-12 | -0.1025 | 4.197e+04 | 4.178e+04 | -4.415e-12 | 6.341 |
| 640 | 203841 | banded_int |  |  |  | -4.481e-13 | -0.009854 | 4085 | 4043 | -4.415e-12 | 5.72 |
| 640 | 203841 | cholmod_int |  |  |  | 6.464e-12 | 0.1421 | 5.822e+04 | 5.793e+04 | -4.415e-12 | 1.293 |
| 640 | 203841 | gth |  |  |  | 1.776e-14 | 0.0003905 | 199.6 | 189.1 | -4.415e-12 | 21.25 |
| 640 | 203841 | ir_direct |  |  |  | 6.732e-17 | 1.48e-06 | 0.9957 | 0.5 | -4.415e-12 | 1.405 |
| 1280 | 817281 | cholmod_default | 5.743e-12 | 0.03157 | 5.173e+04 | -1.192e-11 | -0.06552 | 1.074e+05 | 1.071e+05 | -1.766e-11 | 6.587 |
| 1280 | 817281 | ir_direct |  |  |  | -7.794e-17 | -4.285e-07 | 0.998 | 0.5 | -1.766e-11 | 6.855 |

## Data (e07_floor)

| N | kind | check_every | iters_rtol_1e10 | maxiter | min_omega | min_omega_in_u | k_at_min | k_at_min_over_k10 | final_omega_in_u |
|---|---|---|---|---|---|---|---|---|---|
| 80 | none | 10 | 143 | 572 | 1.126e-15 | 10.14 | 200 | 1.399 | 10.14 |
| 80 | mic0 | 5 | 31 | 124 | 6.667e-16 | 6.005 | 50 | 1.613 | 6.005 |
| 80 | amg | 1 | 9 | 36 | 4.36e-16 | 3.927 | 16 | 1.778 | 3.927 |
| 160 | none | 10 | 282 | 1128 | 1.72e-15 | 15.49 | 400 | 1.418 | 15.49 |
| 160 | mic0 | 5 | 45 | 180 | 1.099e-15 | 9.903 | 80 | 1.778 | 9.903 |
| 160 | amg | 1 | 10 | 40 | 5.058e-16 | 4.556 | 18 | 1.8 | 4.556 |
| 320 | none | 10 | 556 | 2224 | 2.773e-15 | 24.98 | 840 | 1.511 | 24.98 |
| 320 | mic0 | 5 | 66 | 264 | 2.145e-15 | 19.32 | 115 | 1.742 | 21.41 |
| 320 | amg | 1 | 13 | 52 | 7.867e-16 | 7.086 | 25 | 1.923 | 7.086 |
| 640 | none | 10 | 1094 | 4376 | 5.642e-15 | 50.82 | 1680 | 1.536 | 90.22 |
| 640 | mic0 | 5 | 95 | 380 | 2.889e-15 | 26.02 | 180 | 1.895 | 26.77 |
| 640 | amg | 1 | 14 | 56 | 1.675e-15 | 15.09 | 28 | 2 | 15.54 |
| 1280 | none | 10 | 2147 | 8588 | 3.462e-14 | 311.8 | 3440 | 1.602 | 360.3 |
| 1280 | mic0 | 5 | 137 | 548 | 6.91e-15 | 62.24 | 265 | 1.934 | 63.26 |
| 1280 | amg | 1 | 19 | 76 | 2.655e-15 | 23.91 | 35 | 1.842 | 24.86 |

## Data (e07_fft_check)

| N | n | method | reference | rel_err_smallest | max_rel_err | normwise_rel_err | data_term_smallest | signed_err_smallest |
|---|---|---|---|---|---|---|---|---|
| 50 | 1176 | fft | refined | 1.921e-12 | 1.921e-12 | 1.053e-14 | -2.691e-14 | 1.921e-12 |
| 50 | 1176 | cholmod | refined | 3.269e-14 | 3.283e-14 | 4.936e-15 | -2.691e-14 | -3.269e-14 |
| 50 | 1176 | splu | refined | 2.136e-14 | 2.142e-14 | 3.684e-15 | -2.691e-14 | -2.136e-14 |
| 50 | 1176 | fft | exact | 1.921e-12 | 1.921e-12 | 1.053e-14 | -2.691e-14 | 1.921e-12 |
| 50 | 1176 | cholmod | exact | 3.269e-14 | 3.283e-14 | 4.936e-15 | -2.691e-14 | -3.269e-14 |
| 50 | 1176 | splu | exact | 2.136e-14 | 2.142e-14 | 3.684e-15 | -2.691e-14 | -2.136e-14 |
| 50 | 1176 | ir_direct | exact | 0 | 0 | 0 | -2.691e-14 | 0 |
| 100 | 4851 | fft | refined | 3.034e-10 | 3.034e-10 | 1.072e-14 | -1.078e-13 | -3.034e-10 |
| 100 | 4851 | cholmod | refined | 6.464e-14 | 6.477e-14 | 1.005e-14 | -1.078e-13 | -6.464e-14 |
| 100 | 4851 | splu | refined | 8.304e-14 | 8.31e-14 | 1.086e-14 | -1.078e-13 | -8.304e-14 |
| 200 | 19701 | fft | refined | 2.506e-10 | 5.016e-10 | 3.513e-14 | -4.311e-13 | 2.506e-10 |
| 200 | 19701 | cholmod | refined | 2.933e-13 | 2.934e-13 | 3.976e-14 | -4.311e-13 | -2.933e-13 |
| 200 | 19701 | splu | refined | 3.225e-13 | 3.226e-13 | 4.173e-14 | -4.311e-13 | -3.225e-13 |
| 400 | 79401 | fft | refined | 1.206e-07 | 1.206e-07 | 2.111e-13 | -1.725e-12 | -1.206e-07 |
| 400 | 79401 | cholmod | refined | 1.179e-12 | 1.179e-12 | 1.449e-13 | -1.725e-12 | -1.179e-12 |
| 400 | 79401 | splu | refined | 1.267e-12 | 1.267e-12 | 1.515e-13 | -1.725e-12 | -1.267e-12 |
| 800 | 318801 | fft | refined | 4.759e-07 | 4.759e-07 | 1.592e-13 | -6.899e-12 | -4.759e-07 |
| 800 | 318801 | cholmod | refined | 4.755e-12 | 4.755e-12 | 5.694e-13 | -6.899e-12 | -4.755e-12 |
| 800 | 318801 | splu | refined | 4.962e-12 | 4.962e-12 | 5.803e-13 | -6.899e-12 | -4.962e-12 |
