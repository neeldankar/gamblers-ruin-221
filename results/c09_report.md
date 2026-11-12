# Chunk 9 report: four players

Sources: `results/e09_identities.csv` (git e27cb2e, 2026-11-11T21:43:20), `results/e09_solvers.csv` (git e27cb2e, 2026-11-11T21:52:56), `results/e09_big_stack.csv` (git e27cb2e, 2026-11-11T21:53:20), `results/e09_alpha.csv` (git e27cb2e, 2026-11-11T21:53:20); macOS-15.6.1-arm64-arm-64bit-Mach-O, Python 3.13.18, numpy 2.5.4, scipy 1.18.1, OMP_NUM_THREADS=1.

Free memory at the start of the run: 4946 MB (free + inactive + speculative pages from vm_stat); workers were killed above 60% of it (2968 MB).

| Check | Expected | Observed | Status |
|---|---|---|---|
| e09_identities n | C(N-1, 3): 84, 969, 3654, 9139, 32509; exact | N=10: 84, N=20: 969, N=30: 3654, N=40: 9139, N=60: 32509 | PASS |
| max_nnz_row; max_abs_A_minus_AT | 13; 0; exact | N=10: 13; 0, N=20: 13; 0, N=30: 13; 0, N=40: 13; 0, N=60: 13; 0 | PASS |
| e2_identity_relerr, win_maxerr, out_first_sum_maxerr | below 1e-12 | N=10: 9.2e-16/4.4e-16/1.1e-15, N=20: 1.6e-15/1.0e-15/2.0e-15, N=30: 3.9e-15/1.9e-15/4.9e-15, N=40: 5.3e-15/3.3e-15/6.6e-15, N=60: 1.2e-14/5.8e-15/1.5e-14 | PASS |
| bounds_hold | True at every N | N=10: True, N=20: True, N=30: True, N=40: True, N=60: True | PASS |
| T_over_e4N_min, T_over_e4N_max at N = 20, 30, 40, 60 | [0.849036, 1.891425]; [0.567040, 1.787799]; [0.425240, 1.739744]; [0.283582, 1.694066]; 1e-5 abs | N=20: [0.849036, 1.891425] (-3e-07, +2e-07); N=30: [0.567040, 1.787799] (-3e-07, -4e-07); N=40: [0.425240, 1.739744] (-5e-07, +1e-07); N=60: [0.283582, 1.694066] (-5e-07, +1e-07) | PASS |
| T_e2_over_6e4 range at N = 20, 30, 40, 60 | [0.851141, 1.061295]; [0.834306, 1.061624]; [0.826378, 1.063099]; [0.818799, 1.063431]; 1e-5 abs | N=20: [0.851141, 1.061295] (+3e-07, -4e-07); N=30: [0.834306, 1.061624] (+8e-09, +2e-07); N=40: [0.826378, 1.063099] (+5e-07, -2e-07); N=60: [0.818799, 1.063431] (-4e-07, -2e-07) | PASS |
| T_max (at the equal-stacks state) at N = 20, 40, 60 | 26.5324, 106.3099, 239.2719; 1e-4 abs | N=20: 26.5324 at 5-5-5-5 (-3e-05); N=40: 106.3099 at 10-10-10-10 (-2e-05); N=60: 239.2719 at 15-15-15-15 (+3e-05) | PASS |
| e09_solvers rel_err | below 1e-10 for every method and N | largest 2.1e-13 over 22 runs; stopped by memory rules: splu N=100 | PASS |
| amg_cg iters | 9 to 14 for N = 40 ... 150, growing slowly | N=20: 7, N=40: 9, N=60: 10, N=80: 11, N=100: 12, N=120: 13, N=150: 13, N=200: 14 | PASS |
| amg_cg setup_s + solve_s against n | slope of log time vs log n between 0.8 and 1.4 | slope 0.972 over N = 20, 40, 60, 80, 100, 120, 150, 200 | PASS |
| cholmod nnz_factor against n (N = 60 to 100) | slope between 1.25 and 1.6 (theory n^(4/3)); 8.0e6, 2.76e7, 7.45e7 at N = 60, 80, 100; 10% | slope 1.417; N=60: 8e+06 (-0.0%), N=80: 2.76e+07 (-0.2%), N=100: 7.45e+07 (+0.0%) | PASS |
| cholmod flops against n (N = 60 to 100) | slope 2.09 (theory n^2); 5.2907e9, 3.1766e10, 1.4145e11 at N = 60, 80, 100 (Linux, independent builder; nnz identical to the Mac's); slope in [1.9, 2.3]; each value within 1% | slope 2.085; N=60: 5.2907e+09 (-0.00%), N=80: 3.1766e+10 (-0.00%), N=100: 1.4145e+11 (+0.00%) | PASS |
| cholmod setup_s against n (N = 60 to 100) | Mac 1.66 (flop rate 9.4 to 18.2 GFLOP/s), Linux 2.1 (3.0 GFLOP/s); slope in [1.4, 2.6] | slope 1.677; N=60: 0.55 s, N=80: 2.21 s, N=100: 7.71 s; flop rate 9.7, 14.4, 18.4 GFLOP/s | PASS |
| splu (COLAMD) peak memory vs cholmod at N = 60 | splu several times larger (about 1 GB vs 0.2 GB here); read as ratio >= 3 | splu 871 MB, cholmod 213 MB, ratio 4.10 | PASS |
| e09_big_stack P (four players) at N = 8, 10, 12, 16, 20, 24, 30, 40, 50 | 5.577821161394e-03, 1.571739438951e-03, 5.568973643914e-04, 1.080249783339e-04, 3.022376155052e-05, 1.066742330410e-05, 2.980150693207e-06, 5.753800975152e-07, 1.606108031016e-07; 1e-09 relative | N=8: 5.577821161394e-03 (-3.6e-14); N=10: 1.571739438951e-03 (-1.9e-13); N=12: 5.568973643914e-04 (-8.7e-14); N=16: 1.080249783339e-04 (+6.3e-14); N=20: 3.022376155052e-05 (-1.2e-13); N=24: 1.066742330410e-05 (-2.3e-13); N=30: 2.980150693207e-06 (+1.3e-13); N=40: 5.753800975152e-07 (-1.9e-14); N=50: 1.606108031016e-07 (-3.5e-14) | PASS |
| e09_big_stack P (four players) at N = 60, 80, 100, 120, 160, 200 | 5.661341422530e-08, 1.092193169790e-08, 3.047622700924e-09, 1.074036901898e-09, 2.071632598328e-10, 5.780085237687e-11; 1e-08 relative | N=60: 5.661341422530e-08 (-2.7e-14); N=80: 1.092193169790e-08 (-3.1e-13); N=100: 3.047622700924e-09 (-5.9e-14); N=120: 1.074036901898e-09 (+1.2e-13); N=160: 2.071632598328e-10 (+8.3e-14); N=200: 5.780085237687e-11 (-7.2e-15) | PASS |
| local_slope (four players) | increasing in N; 5.6762 (8 to 10), 5.7121 (20 to 24), 5.7171 (30 to 40), 5.7198 (60 to 80), 5.7201 (80 to 100), 5.7205 (120 to 160), 5.7206 (160 to 200); 1e-3 abs | 8 to 10: 5.6762 (+3.5e-05); 20 to 24: 5.7121 (-2.8e-05); 30 to 40: 5.7171 (-3.1e-05); 60 to 80: 5.7198 (-3.8e-05); 80 to 100: 5.7201 (+3.4e-05); 120 to 160: 5.7205 (-4.5e-05); 160 to 200: 5.7205 (-5.1e-05); increasing: yes | PASS |
| local_slope (three players) | 3.000; 1e-3 abs | N=20: 3.00045, N=40: 3.00003, N=80: 3.00000, N=160: 3.00000, N=320: 3.00000 | PASS |
| P N^3, three players, N >= 80 | 9.11959; 1e-5 relative | N=80: 9.119590 (-1.8e-08), N=160: 9.119589 (-1.0e-07), N=320: 9.119589 (-1.1e-07) | PASS |
| alpha_extrapolated (four players) | 5.720688 (cone eigenvalue lambda = 38.446962, Project chat FEM); the 1/N^2 fit of the Nov 11 slopes gives 5.720687; 1e-4 | 5.720687 (-1.2e-06; last slope 5.72055) | PASS |
| n_lumped / n_full | 41/165 at N = 12, 204/969 at N = 20, 27353/156849 at N = 100; ratio tends to 1/6; exact | N=12: 41/165; N=20: 204/969; N=100: 27353/156849; |ratio - 1/6| decreasing: yes, 0.17047 at N = 200 | PASS |
| seconds for the lumped CHOLMOD solve at N = 200 | under 2 min | 10.1 s (cholmod) | PASS |

Summary: 22 PASS, 0 WARN, 0 FAIL.

## Red flags (automatic checks of the spec's list)

| Red flag check | Observed | OK |
|---|---|---|
| A (6 e4) differs from e2 | largest relative deviation 1.2e-14 | yes |
| four-player local slope below 5.7 or above 5.73 (N >= 20) | 5.7081 to 5.7205 | yes |
| three-player slope not 3 | 3.00000 to 3.00045 | yes |
| direct solves stopped by the memory rules (60% of free memory, 3 GB projected factor) | splu N=100: skipped: projected factor 3.5 GB > 3 GB | yes |
| AMG-CG iterations growing like N | iters x2.00 while N x10 (flag if above sqrt of the N ratio) | yes |

## Data (e09_identities)

| N | n | max_nnz_row | max_abs_A_minus_AT | e2_identity_relerr | win_maxerr | out_first_sum_maxerr | T_max | T_max_state | T_over_e4N_min | T_over_e4N_max | T_e2_over_6e4_min | T_e2_over_6e4_max | bounds_hold |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 84 | 13 | 0 | 9.210739167e-16 | 4.440892099e-16 | 1.110223025e-15 | 6.100015558 | 2-3-2-3 | 1.694448766 | 2.267850884 | 0.9071403537 | 1.044910072 | True |
| 20 | 969 | 13 | 0 | 1.576457483e-15 | 9.992007222e-16 | 1.998401444e-15 | 26.53236508 | 5-5-5-5 | 0.8490356825 | 1.891425216 | 0.851141347 | 1.061294603 | True |
| 30 | 3654 | 13 | 0 | 3.866899242e-15 | 1.887379142e-15 | 4.884981308e-15 | 59.27454505 | 7-7-8-8 | 0.5670396529 | 1.787798589 | 0.8343060081 | 1.061624239 | True |
| 40 | 9139 | 13 | 0 | 5.33570225e-15 | 3.330669074e-15 | 6.550315845e-15 | 106.3098822 | 10-10-10-10 | 0.4252395289 | 1.739744136 | 0.8263784648 | 1.063098822 | True |
| 60 | 32509 | 13 | 0 | 1.168943972e-14 | 5.773159728e-15 | 1.487698853e-14 | 239.2719319 | 15-15-15-15 | 0.2835815489 | 1.694066126 | 0.8187986278 | 1.063430808 | True |

## Data (e09_solvers, right-hand side e2, exact answer 6 x1 x2 x3 x4)

| N | n | method | setup_s | solve_s | peak_rss_mb | nnz_factor | flops | iters | rel_err | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 20 | 969 | splu | 0.01244708407 | 0.0002238339512 | 55.0625 | 112102 |  |  | 1.818989404e-15 | ok (median of 3 processes) |
| 40 | 9139 | splu | 0.7300685421 | 0.004496000009 | 172.4375 | 5229384 |  |  | 6.427095893e-15 | ok (median of 3 processes) |
| 60 | 32509 | splu | 9.462833417 | 0.03074208391 | 870.75 | 36545796 |  |  | 1.264759052e-14 | ok (median of 3 processes) |
| 80 | 79079 | splu | 79.63058446 | 0.115664292 | 2089.703125 | 154131660 |  |  | 2.437445801e-14 | ok (1 run, over 60 s) |
| 100 | 156849 | splu |  |  |  |  |  |  |  | skipped: projected factor 3.5 GB > 3 GB |
| 20 | 969 | splu_mmd | 0.005965457996 | 0.0001704579918 | 54.359375 | 113816 |  |  | 8.488617217e-16 | ok (median of 3 processes) |
| 40 | 9139 | splu_mmd | 0.276186625 | 0.002388707944 | 134.296875 | 3247590 |  |  | 3.031649006e-15 | ok (median of 3 processes) |
| 60 | 32509 | splu_mmd | 4.724002042 | 0.01551824994 | 586.3125 | 23777668 |  |  | 5.653089702e-15 | ok (median of 3 processes) |
| 80 | 79079 | splu_mmd | 42.25372975 | 0.07626287499 | 1910.5625 | 97986420 |  |  | 7.761021455e-15 | ok (median of 3 processes) |
| 100 | 156849 | splu_mmd | 203.2260022 | 0.393587625 | 2922.0625 | 280867612 |  |  | 1.301368078e-14 | ok (1 run, over 60 s) |
| 20 | 969 | cholmod | 0.00523945794 | 8.783407975e-05 | 53.65625 | 47736 | 3500904 |  | 1.455191523e-15 | ok (median of 3 processes) |
| 40 | 9139 | cholmod | 0.08977816696 | 0.001743292087 | 84.03125 | 1232278 | 347335980 |  | 5.456968211e-15 | ok (median of 3 processes) |
| 60 | 32509 | cholmod | 0.545872 | 0.01029995899 | 212.59375 | 7999881 | 5290687335 |  | 1.168943972e-14 | ok (median of 3 processes) |
| 80 | 79079 | cholmod | 2.211404625 | 0.03466949996 | 602.484375 | 27551521 | 3.17658771e+10 |  | 2.158534092e-14 | ok (median of 3 processes) |
| 100 | 156849 | cholmod | 7.708648584 | 0.1123077499 | 1412.609375 | 74525420 | 1.414543034e+11 |  | 2.980232239e-14 | ok (median of 3 processes) |
| 20 | 969 | amg_cg | 0.004575125058 | 0.002711915993 | 57.171875 |  |  | 7 | 2.089412495e-13 | ok (median of 3 processes) |
| 40 | 9139 | amg_cg | 0.02148479107 | 0.01871137507 | 66.21875 |  |  | 9 | 7.178944846e-14 | ok (median of 3 processes) |
| 60 | 32509 | amg_cg | 0.06750899996 | 0.06909654196 | 104.9375 |  |  | 10 | 9.236573682e-14 | ok (median of 3 processes) |
| 80 | 79079 | amg_cg | 0.1543853331 | 0.183299333 | 151.28125 |  |  | 11 | 3.431826675e-14 | ok (median of 3 processes) |
| 100 | 156849 | amg_cg | 0.32198925 | 0.409431959 | 246.921875 |  |  | 12 | 3.616015116e-14 | ok (median of 3 processes) |
| 120 | 273819 | amg_cg | 0.588810917 | 0.779879958 | 514.671875 |  |  | 13 | 3.228968186e-14 | ok (median of 3 processes) |
| 150 | 540274 | amg_cg | 1.213453125 | 1.586702625 | 943.96875 |  |  | 13 | 6.203050683e-14 | ok (median of 3 processes) |
| 200 | 1293699 | amg_cg | 3.157330792 | 3.955288417 | 1401.4375 |  |  | 14 | 8.145968119e-14 | ok (median of 3 processes) |

## Data (e09_big_stack: P(chip leader busts first) from (1, 1, 1, N-3) and (1, 1, N-2))

| players | N | n_full | n_lumped | P | local_slope | seconds | solver |
|---|---|---|---|---|---|---|---|
| 4 | 8 | 35 | 11 | 0.005577821161 |  | 0.001256457996 | cholmod |
| 4 | 10 | 84 | 23 | 0.001571739439 | 5.676235279 | 0.001336792018 | cholmod |
| 4 | 12 | 165 | 41 | 0.0005568973644 | 5.690809514 | 0.001723333029 | cholmod |
| 4 | 16 | 455 | 102 | 0.0001080249783 | 5.700801801 | 0.001819083001 | cholmod |
| 4 | 20 | 969 | 204 | 3.022376155e-05 | 5.708137441 | 0.005251833005 | cholmod |
| 4 | 24 | 1771 | 358 | 1.06674233e-05 | 5.712072084 | 0.003420250025 | cholmod |
| 4 | 30 | 3654 | 710 | 2.980150693e-06 | 5.714799605 | 0.008848249912 | cholmod |
| 4 | 40 | 9139 | 1708 | 5.753800975e-07 | 5.717069092 | 0.01694170793 | cholmod |
| 4 | 50 | 18424 | 3364 | 1.606108031e-07 | 5.718501779 | 0.03190558404 | cholmod |
| 4 | 60 | 32509 | 5845 | 5.661341423e-08 | 5.719225566 | 0.06151945796 | cholmod |
| 4 | 80 | 79079 | 13949 | 1.09219317e-08 | 5.719762422 | 0.178429417 | cholmod |
| 4 | 100 | 156849 | 27353 | 3.047622701e-09 | 5.720133959 | 0.4128074171 | cholmod |
| 4 | 120 | 273819 | 47390 | 1.074036902e-09 | 5.720319132 | 0.870407583 | cholmod |
| 4 | 160 | 657359 | 112698 | 2.071632598e-10 | 5.720455371 | 3.369510292 | cholmod |
| 4 | 200 | 1293699 | 220539 | 5.780085238e-11 | 5.720549158 | 10.13087921 | cholmod |
| 3 | 10 | 36 |  | 0.00912261427 |  | 0.01459716598 | splu |
| 3 | 20 | 171 |  | 0.001139974666 | 3.000445554 | 0.001013500034 | splu |
| 3 | 40 | 741 |  | 0.0001424937864 | 3.000030848 | 0.002726375009 | splu |
| 3 | 80 | 3081 |  | 1.78116989e-05 | 3.000001976 | 0.01478312502 | splu |
| 3 | 160 | 12561 |  | 2.226462171e-06 | 3.000000124 | 0.05563058401 | splu |
| 3 | 320 | 50721 |  | 2.783077699e-07 | 3.000000008 | 0.365599417 | splu |

## Data (e09_alpha)

| players | alpha_last_slope | alpha_extrapolated |
|---|---|---|
| 3 | 3.000000008 | 2.999997409 |
| 4 | 5.720549158 | 5.720686778 |

Figures: `figures/f09_solvers.png`, `figures/f09_big_stack.png`.
