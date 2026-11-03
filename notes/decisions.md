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
