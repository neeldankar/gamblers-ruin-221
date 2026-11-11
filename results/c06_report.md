# Chunk 6 report: FFT fast solver (method of images)

Source: `results/e06_fft.csv` (git 84eec92, 2026-11-11T15:02:42); macOS-15.6.1-arm64-arm-64bit-Mach-O, Python 3.13.18, numpy 2.5.4, scipy 1.18.1, OMP_NUM_THREADS=1.

| Check | Expected | Observed | Status |
|---|---|---|---|
| fwd_err_over_eps_kappa | at most 10 for every N (measured 0.02 to 0.4) | N=50: 0.366, N=100: 0.017, N=200: 0.099, N=400: 0.148, N=800: 0.020, N=1600: 0.246 | PASS |
| resid_random | at most 1e-10 for every N (measured 1.4e-15 at N = 50 up to 3.1e-12 at N = 1600) | N=50: 1.9e-15, N=100: 6.3e-15, N=200: 1.3e-13, N=400: 4.4e-14, N=800: 5.3e-13, N=1600: 3.1e-12 | PASS |
| err_vs_splu / (eps kappa2) | at most 10 (measured 0.07 to 0.17) | N=50: 0.159, N=100: 0.086, N=200: 0.080, N=400: 0.098, N=800: 0.088 | PASS |
| sum_out_first_err / (eps kappa2) | at most 10 (measured 0.05 to 0.6) | N=50: 0.583, N=100: 0.100, N=200: 0.138, N=400: 0.218, N=800: 0.048, N=1600: 0.363 | PASS |
| min_p123 x N^3 | 4.5598 (at the state (N - 2, 1, 1)); 0.001 | N=50: 4.559797 at 48-1-1; N=100: 4.559795 at 98-1-1; N=200: 4.559795 at 198-1-1; N=400: 4.559795 at 398-1-1; N=800: 4.559794 at 798-1-1 | PASS |
| p123_reldiff at N = 800 | 1e-8 to 1e-4 (two reference implementations: 6e-7 and 2e-6; about 1e-11 at N = 50) | 4.8e-07 | PASS |
| p123_reldiff at N = 800 / p123_reldiff at N = 50 | above 100 (measured 3e4 and 4e5; single steps in N can dip) | N=50: 1.9e-12, N=100: 3e-10, N=200: 2.5e-10, N=400: 1.2e-07, N=800: 4.8e-07; ratio 2.45e+05 | PASS |
| slope of log(seconds_fft) against log(n), N >= 200 | 0.95 to 1.3 (n log n gives about 1.1; two reference implementations measured 1.09 and 1.14) | 1.172 (N=200: 0.0141 s, N=400: 0.0681 s, N=800: 0.34 s, N=1600: 1.89 s) | PASS |
| seconds_fft at N = 1600 | under 10 s (measured 2.7 to 4.3 s on a slow 2-core machine) | 1.89 s | PASS |
| speedup at N = 400 and 800 | at least 3 (measured 4.6 and 4.4 with complex FFTs; an rfft2 version was 1.6 to 3.6 times faster still) | N=400: 10.08 (fft 0.0681 s, splu 0.686 s); N=800: 22.19 (fft 0.34 s, splu 7.56 s) | PASS |

Summary: 10 PASS, 0 WARN, 0 FAIL.

## Red flags (automatic checks of the spec's list)

| Red flag check | Observed | OK |
|---|---|---|
| errors of 1e-3 or worse (group, sign or ordering wrong) | largest error column entry 4.8e-07 | yes |
| fwd_err_over_eps_kappa above 1 or growing steadily with N | 0.366, 0.017, 0.099, 0.148, 0.020, 0.246 | yes |
| NaN or inf in the FFT columns (division by sigma(0, 0)) | none | yes |
| timing slope near 1.5 or 2 (something quadratic) | slope 1.172 | yes |
| out of memory at N = 1600 (row missing) | N = 1600 present | yes |

## Data (e06_fft)

| N | n | P | seconds_fft | seconds_splu | speedup | fwd_err_t | kappa2 | fwd_err_over_eps_kappa | resid_random | err_vs_splu | sum_out_first_err | min_p123 | p123_reldiff | min_state |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 50 | 1176 | 150 | 0.0008846 | 0.002961 | 3.347 | 2.315e-14 | 284.8 | 0.3661 | 1.874e-15 | 1.006e-14 | 3.686e-14 | 3.648e-05 | 1.942e-12 | 48-1-1 |
| 100 | 4851 | 300 | 0.003744 | 0.01405 | 3.752 | 4.299e-15 | 1140 | 0.01699 | 6.304e-15 | 2.167e-14 | 2.52e-14 | 4.56e-06 | 3.033e-10 | 98-1-1 |
| 200 | 19701 | 600 | 0.01411 | 0.0882 | 6.25 | 1.001e-13 | 4559 | 0.09885 | 1.306e-13 | 8.105e-14 | 1.393e-13 | 5.7e-07 | 2.509e-10 | 198-1-1 |
| 400 | 79401 | 1200 | 0.06811 | 0.6864 | 10.08 | 5.98e-13 | 1.824e+04 | 0.1477 | 4.364e-14 | 3.968e-13 | 8.831e-13 | 7.125e-08 | 1.206e-07 | 398-1-1 |
| 800 | 318801 | 2400 | 0.3405 | 7.556 | 22.19 | 3.231e-13 | 7.295e+04 | 0.01995 | 5.344e-13 | 1.419e-12 | 7.703e-13 | 8.906e-09 | 4.759e-07 | 798-1-1 |
| 1600 | 1277601 | 4800 | 1.892 |  |  | 1.595e-11 | 2.918e+05 | 0.2462 | 3.052e-12 |  | 2.353e-11 |  |  |  |

Figure: `figures/f06_fft.png`.
