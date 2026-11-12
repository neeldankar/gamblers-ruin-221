# Proofs and derivations

Copied verbatim from the section "Math to record" of plan/c04b_review_fixes.md (chunk 4b, Nov 10).

## Math to record (copy this section into `notes/proofs.md`)

Notation: A = I - Q on the live states, Q >= 0 with zero diagonal; T = the round on which the first bust
happens (T >= 1); u = 2^-53.

### 1. CG on b = 1 stops after exactly K = floor((N-1)/2) steps (exact arithmetic, x0 = 0)

For an integer k let theta = 2 pi k / N and v_k(x) = sin(theta x1) + sin(theta x2) + sin(theta x3).
- v_k vanishes on the boundary: if one coordinate is 0 the other two are m and N - m, and
  sin(theta m) + sin(theta (N - m)) = 0.
- The six moves change each coordinate by +1 twice, -1 twice and 0 twice, so
  (Q v_k)(x) = (1/6) sum_a sin(theta x_a)(4 cos theta + 2), and A v_k = (4/3) sin^2(pi k / N) v_k.
- Sawtooth: for m = 1..N-1, 1/2 - m/N = (1/N) sum_{k=1}^{K} cot(pi k / N) sin(2 pi k m / N).
  Summing over the three coordinates of a live state (they add up to N) gives
  1 = (2/N) sum_{k=1}^{K} cot(pi k / N) v_k.
- For 1 <= k <= K the coefficients are positive, the eigenvalues are distinct (increasing in k), and
  v_k(1, 1, N-2) = 2 sin(theta)(1 - cos(theta)) > 0, so v_k != 0.
So b = 1 is a combination with nonzero coefficients of K eigenvectors with K distinct eigenvalues; the Krylov
space has dimension exactly K, and CG is exact at step K and not before. In floating point the count stretches
by 3 to 8% for N >= 80.

### 2. cond_i = 2 E_i[T | event], with its hypotheses

cond_i = (|A^-1| (|A||x| + |b|))_i / |x_i| (Skeel; Higham, Accuracy and Stability, ch. 7).
- |A^-1| = A^-1 because A^-1 = sum_t Q^t >= 0.
- |A| = I + Q = 2I - A because the diagonal is 1 and the off-diagonals are <= 0.
- |x| = x and |b| = b because b >= 0. (True for out_first, order, win and b = 1; not for a random b.)
- Then |A||x| + |b| = 2x - Ax + b = 2x, so cond_i = 2 (A^-1 x)_i / x_i.
With f the boundary value, x_i = E_i[f(X_T)] and (Q^t x)_i = E_i[f(X_T); T > t]; summing over t gives
(A^-1 x)_i = E_i[T f(X_T)]. If f is the indicator of an event this is E_i[T; event]. For an order
probability, f(y) = P(event | X_T = y) and E_i[T f(X_T)] = E_i[T 1{event}] by the tower property (T is known at
time T). Either way cond_i = 2 E_i[T | event]. The worst case A - eps|A|, b + eps|b| raises every entry at once.
This treats the diagonal as free data: such perturbations change the row sums (compare chunk 7).

### 3. The stored system and the data term

1/6 in binary is 0.0010101..., and rounding to 53 bits rounds down: fl(1/6) = (1 + d)/6 with d = -2^-54 exactly.
For rhs_out_first the stored system is (I - (1+d)Q) x' = (1+d) b. With A_d = I - (1+d)Q and Qx = x - b:
x' - x = A_d^-1 [(1+d) b - A_d x] = d A_d^-1 (b + Qx) = d A_d^-1 x, so
(x' - x)_i / x_i = d E_i[T | event] + O(d^2) = -(u/4) cond_i.
At the tiny entry this is -0.0971 N^2 u. Every float solver inherits it, at any stopping rule; exact rational
solves of the ideal system do not. For b = 1 only Q is perturbed: x' - t = d A_d^-1 Q t, and because
A^-1 t = t (1 + e2)/4 (e2 = x1 x2 + x1 x3 + x2 x3; p = e3 (1 + e2) satisfies p - mean of p over the six
neighbours = 4 e3 and vanishes on the boundary), (x' - t)_i / t_i = d (e2 - 3)/4. In chunk 2's metric that is
(3/16 - 27/(16 N^2)) kappa_inf u when 3 | N.

### 4. What a residual stopping rule controls

With r = b - A x_hat, x - x_hat = A^-1 r, so e_i = g_i . r with g_i = A^-1 e_i (row i of A^-1: expected visits
to each state from i). By Cauchy-Schwarz |e_i| <= ||g_i||_2 ||r||_2 <= ||g_i||_2 rtol ||b||_2. At the corner
||g_i||_2 = 1.1702 for N >= 40 (it converges in N: 1.1687 at N = 10, 1.1701 at N = 20), ||b||_2 = sqrt(N-2)/3
for out_first, and x_tiny = 9.12 / N^3, so the best a
residual test can promise there is a relative error of 0.043 N^3.5 rtol. The observed error is 5e-4 to 1.5e-2
of that bound. The componentwise condition number does not enter: cond_i measures the response to
perturbations |dA| <= eps|A|, |db| <= eps|b|, and a normwise-small residual is not of that form.

### 5. The a posteriori bound

For a computed x_hat, x' - x_hat = A^-1 r exactly, so |x' - x_hat| <= A^-1 |r| (A^-1 >= 0), and by the
definition of omega, |r| <= omega (|A||x_hat| + |b|). Hence |x' - x_hat|_i / x_hat_i <= omega cond_i(x_hat), with
no first-order approximation. In floating point the residual of a row with 7 nonzeros is itself only accurate
to 8u (|A||x_hat| + |b|), which gives (omega + 8u) cond_i(x_hat). This bounds the distance to the stored
solution x'; add (u/4) cond_i for the distance to the true probability. It is computed in floating point, so
it is a bound to trust, not a machine-checked certificate.

### 6. The constant

Diaconis and Ethier, "Gambler's ruin and the ICM", Statist. Sci. 37 (2022), section 2.6: Theorem 2.5 proves
P_{1,1,N-2}(player 3 out first) is of order N^-3. Remark 4 gives P_{1,1,N-2}(321) ~ c / N^3 with
c = (sqrt(pi) / (3 sqrt 3)) (Gamma(1/3) / Gamma(5/6))^3 = 4.55979449996, from unpublished work of Sangchul Lee
using Ferguson's Brownian approximation, and says the approximation is not rigorously justified to this degree.
By symmetry P(3 out first) = 2 P(321) at (1, 1, N-2), and 2c = Gamma(1/3)^9 / (8 pi^4) = 9.11958899992 (reflection
and duplication formulas; checked to 39 digits). Our addition: with a correctly rounded reference the values
follow C + 34.39 / N^4 ((v - C) N^4 = 34.375, 34.388, 34.391 at N = 160, 320, 640), measured, not proved.

### 7. The structured condition number

Describe the M-matrix by its off-diagonal weights w_ij = -a_ij >= 0 (each ordered pair separately), its row sums
s_i >= 0 and the right-hand side b_i >= 0; the diagonal is a_ii = s_i + sum_j w_ij, never data. Perturb every
parameter by a relative amount of at most eps. With x = A^-1 b,
(dA x)_i = ds_i x_i + sum_j dw_ij (x_i - x_j), and dx = A^-1 (db - dA x).
Because A^-1 >= 0, the largest first-order change of entry k is eps (A^-1 v)_k with
v_i = b_i + s_i x_i + sum_j w_ij |x_i - x_j|,
and one perturbation attains it in every entry at once: dw_ij = eps w_ij sign(x_j - x_i) (a drift toward the
event), ds = -eps s, db = +eps b. So kappa_k = (A^-1 v)_k / x_k. Since A^-1 b = x, the b term contributes exactly 1.
Reading it as in section 2 (G(k, i) x_i / x_k is the expected number of visits to i of the walk conditioned on the
event): kappa_k = 1 + E_k[ sum_{t < T} ( s(X_t) + sum_j w |x_j - x(X_t)| / x(X_t) ) | event ]. The componentwise
number charges 2 per step (cond = 2 E[T | event]); the structured one charges the relative variation of x across
one step, which near the corner is of order 1/r at distance r (x grows like r^3 there), and that adds up to order N
(a heuristic for the growth; the numbers below are measured).

Lower bound with no computation (review 2): let h_i = x3 at state i and H = diag(h). A(eps) = A + eps (HA - AH)
has a_ij(eps) = a_ij (1 + eps (h_i - h_j)) with h_i - h_j in {-1, 0, 1}, the same diagonal, and row sums that move by
eps (1/6) sum over busting moves of (h_i - h_y), at most eps s_i (h is harmonic for the six moves). So it is an
admissible perturbation. For out_first_3, b lives where h = 1, so Hb = b and differentiating A(eps) x(eps) = b
gives dx/deps = (H - I) x: entry i moves by (h_i - 1) eps x_i, that is N - 3 at (1, 1, N-2). Hence kappa_tiny >= N - 3.

Measured (N = 10 ... 640): kappa_tiny = max_i kappa_i = 11.35, 23.80, 48.30, 97.10, 194.6, 389.5, 779.2, that is
1.1353 N rising to 1.2176 N; the smallest kappa_i over all states is 2.5. If only symmetric perturbations are
allowed (w_ij and w_ji move together), the tiny entry's number is
(sum_i g_i (b_i + s_i x_i) + sum_{i<j} w_ij |g_i - g_j| |x_i - x_j|) / x_tiny with g = A^-1 e_tiny:
6.2, 8.3, 10.2, 12.0, 13.8, 15.6, 17.4, about 1.8 more per doubling (log N). Random perturbations: 1.5 to 3.1.
So there are four levels: 0.39 N^2 (entries of A, diagonal free), 1.22 N (structured), log N (structured and
symmetric), O(1) (random). The chunk 7 statement "2 to 5 eps at every N" described the last one only.
The Alfa-Xue-Ye bound for this parametrization has a coefficient of order n; it does not promise O(1) either.
GTH's measured error, 0.19 to 0.42 N u, is 0.16 to 0.34 kappa u.

### 8. Three sources of error at a tiny entry

1. **The stopping rule.** A residual test bounds the absolute error (section 4): up to 100% relative error.
2. **The stored data.** x'_i = E_i[(1+d)^T; event] exactly, because x' = sum_t (1+d)^(t+1) Q^t b. Hence
   d E_i[T | event] <= (x' - x)_i / x_i <= d E_i[T | event] + (d^2 / 2) E_i[T^2 | event]; the second-order term is
   about 3e-22 at N = 1280, and x' = x + d A_d^-1 x is an identity (section 3). In the parameters of section 7 the
   rounding of 1/6 is harmless (it scales w, s and b by the same factor: that is why GTH does not see it). It
   costs 0.097 N^2 u only because the stored matrix keeps its diagonal at 1: interior row sums go from 0 to
   2^-54, which is not a small relative change of a row sum.
3. **The solver's own arithmetic.** Against the stored solution, at the tiny entry, N = 160 to 640 (Linux):
   supernodal CHOLMOD +0.05 N^2 u (Mac +0.032), SuperLU COLAMD +0.03, SuperLU natural -0.07 to -0.14, simplicial
   CHOLMOD -0.006, LAPACK band Cholesky below 0.005. The N^2 growth means the rounding errors do not average
   out; why they are coherent (identical local arithmetic on a regular lattice is our guess) is not established.
   The constant changes with the algorithm, the ordering, the scaling (CHOLMOD on the integer matrix 6A:
   +0.18 N^2 u) and the machine.

What each fix removes: componentwise stopping removes 1 and leaves 2 and 3 (it lands as close to the stored
solution as the best direct solves). Refinement with the residual of the ideal integer system removes all three:
correctly rounded in every tested case (exact rationals for N <= 80; exact integer residuals for N = 160 to 1280).
GTH never forms 2 and has no N^2 term in 3: 0.19 to 0.42 N u, not correctly rounded. A band Cholesky of the
integer matrix 6A also avoids 2 but keeps a small N^2 term (0.0094 N^2 u at N = 640, 19 times GTH's error).

### 9. What the compensated residual guarantees

Dot2 (Ogita, Rump and Oishi 2005, Proposition 5.5) gives |r_hat - r| <= u |r| + gamma_m^2 sum_k |a_k x_k| with
gamma_m = m u / (1 - m u): for a row with 7 nonzeros, about 2u |r_i| + 64 u^2 (|A||x| + |b|)_i after the division.
It is not exact: for the row of state (2, 2, 16) at N = 20, coefficients (-20, -20, -20, 120, -20, -20, -20), and
x = (q, t, 1, 3002399751580331 q, q, 0, 0) with q = 2^-54, t = 2^-174, the exact residual is 20 t and the loop
returns 0 (review 2; reproduced). Near a solution the bound is far more than refinement needs, and in every
case checked there (N = 12, 40, 160, the Project chat's transcription of the loop) the result equals the correctly
rounded residual. The stopping
test of the refinement (last correction at most 4u) is a stopping rule. Correct rounding is a measured result:
after the last step the error is the inner solve's error on a correction of size u, plus one rounding.
