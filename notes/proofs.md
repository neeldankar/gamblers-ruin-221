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
||g_i||_2 = 1.1702 for every N, ||b||_2 = sqrt(N-2)/3 for out_first, and x_tiny = 9.12 / N^3, so the best a
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
