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
Prior work: the expansion of the constant vector in these eigenvectors is published for this chain (Bruss,
Louchard and Turner, Adv. Appl. Probab. 35 (2003) 278-294, eq. (2.1) and Theorem 2.1, which gives P(T > n) as
the same sum with the factors [(1 + 2 cos(2 pi k/N))/3]^n). Ours is the corollary for CG.

### 2. cond_i = 2 E_i[T | event], with its hypotheses

cond_i = (|A^-1| (|A||x| + |b|))_i / |x_i| (componentwise condition numbers: Skeel 1979; Higham, Accuracy and
Stability, ch. 7. To confirm before the report: a reviewer attributes this entrywise form with the b term to Rohn
1989, via Higham section 7.5 and Problem 7.1.)
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
neighbours = 4 e3 and vanishes on the boundary), (x' - t)_i / t_i = d (e2 - 3)/4 + O(d^2) (x' - t = d A_d^-1 Q t
is exact; the polynomial replaces A_d by A). In chunk 2's metric that is
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
and duplication formulas; checked to 39 digits). Since then it is a theorem: Denisov and Wachtel, "Harmonic
measure in a multidimensional gambler's problem", Ann. Appl. Probab. 34 (2024) 4387-4407 (arXiv:2212.11526),
Corollary 4: P_{y1,y2}(third player eliminated first) ~ Gamma(1/3)^9/(16 pi^4) y1 y2 (y1 + y2)/N^3, which is
C A B (A + B)/2 N^-3 and gives C at A = B = 1. So Lee's constant is rigorous, and N^3 P/(C A B (A+B)/2) -> 1 at
every fixed corner state is their corollary, not a finding of ours. Their Proposition 5 proves the rate O(N^-3)
only. Our addition: with a correctly rounded reference the values follow C + K/N^4, (v - C) N^4 = 34.375, 34.388,
34.391 at N = 160, 320, 640 (measured, not proved). Conjecture (checkpoint 3 review): K = pi C^3/(40 sqrt 3) =
Gamma(1/3)^27/(20480 sqrt 3 pi^11) = 34.3918115. Richardson extrapolation of the measured values in 1/N^2 gives
34.39181, and the relative coefficient pi C^2/(40 sqrt 3) = 3.7712 is approached at six corner states.

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
6.2, 8.3, 10.2, 12.0, 13.8, 15.6, 17.4, about 1.8 more per doubling (log N). Random perturbations (every parameter
times 1 + eps times an independent uniform(-1, 1) number): the relative change of the tiny entry has standard
deviation eps times 0.776, 0.835, 0.896, 0.959, 1.020, 1.079, 1.136 at N = 10 ... 640 (the 2-norm of the
sensitivities divided by sqrt 3). It still grows, by about 0.06 per doubling, so it is not O(1) as far as we know.
The largest change seen in 20 draws, over all states, was 1.5 to 3.1 eps (structured_random_max); the largest is
not always at the tiny entry. So there are four levels: 0.39 N^2 (entries of A, diagonal free), 1.22 N
(structured), about log N (structured and symmetric), and an rms near 1 that grows slowly (random). The chunk 7
statement "2 to 5 eps at every N" described samples of the last one only. The Alfa-Xue-Ye bound for this
parametrization has a coefficient of order n; it does not promise O(1) either. GTH's measured error is at most
0.42 N u at every entry (N = 20 ... 640). Divided entry by entry by kappa_i u its maximum is 1.0, 1.7, 2.1, 2.3,
6.3, 6.9 at N = 20, 40, 60, 80, 160, 320 (checkpoint 3 review; attained on the line x3 = 1, where kappa_i is
about 3), so the data do not show an error bounded by a constant times kappa_i u, and we do not claim stability
in the structured sense.

### 8. Three sources of error at a tiny entry

1. **The stopping rule.** A residual test bounds the absolute error (section 4): up to 100% relative error.
2. **The stored data.** x'_i = E_i[(1+d)^T; event] exactly, because x' = sum_t (1+d)^(t+1) Q^t b. Hence
   d E_i[T | event] <= (x' - x)_i / x_i <= d E_i[T | event] + (d^2 / 2) E_i[T^2 | event]; the second-order term is
   about 2e-22 at N = 1280 (E[T^2 given event] = 0.0452 N^4 at the tiny entry), and x' = x + d A_d^-1 x is an
   identity (section 3). In the parameters of section 7 the
   rounding of 1/6 is harmless (it scales w, s and b by the same factor: that is why GTH does not see it). It
   costs 0.097 N^2 u only because the stored matrix keeps its diagonal at 1: interior row sums go from 0 to
   2^-54, which is not a small relative change of a row sum.
3. **The solver's own arithmetic.** Against the stored solution, at the tiny entry, in units of N^2 u (final
   run, Mac, N = 160, 320, 640): supernodal CHOLMOD +0.032, +0.032, +0.032; SuperLU COLAMD +0.025, +0.027,
   +0.028; simplicial CHOLMOD -0.018, -0.021, -0.022; SuperLU in natural order -0.048, -0.126 (N = 160, 320;
   -0.022 at N = 80), which grows faster than N^2 (about N^3.3); LAPACK band Cholesky +0.0001, -0.0010,
   -0.0054, small with changing sign. So the own error is a fraction of cond_i u (cond_tiny = 0.39 N^2) that
   depends on the algorithm, the ordering, the scaling (CHOLMOD on the integer matrix 6A: +0.14), the BLAS and
   the machine (Linux: supernodal +0.05, simplicial -0.006, COLAMD +0.03, natural -0.07 to -0.14). It is
   roughly a constant times N^2 u for supernodal CHOLMOD and COLAMD SuperLU only; it is not a law of direct
   solvers. Why these errors do not average out (identical local arithmetic on a regular lattice is our
   guess) is not established.

What each fix removes: componentwise stopping removes 1 and leaves 2 and 3 (it lands as close to the stored
solution as the best direct solves). Refinement with the residual of the ideal integer system removes all three:
correctly rounded in every tested case (exact rationals for N <= 80; exact integer residuals for N = 160 to 1280).
GTH never forms 2, and its measured error is at most 0.42 N u for N up to 640 (not correctly rounded; no bound
of this form is proved here). A band Cholesky of the integer matrix 6A also avoids 2; its error is 0.0100 N^2 u
at N = 640, 20.5 times GTH's (final run).

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

### 10. The SOR 3/4 law (theorem)

**Setting.** Three-player matrix A = I - Q on the live states of the triangle x1 + x2 + x3 = N, states in lexicographic order
by (x1, x2). mu = rho(Q) = (1 + 2 cos(2 pi/N))/3. SOR iteration matrix S_w = (I - w L)^-1 ((1 - w) I + w U), where
Q = L + U (strictly lower and upper parts). Young's omega: w* = 2/(1 + sqrt(1 - mu^2)).

The six moves are +-a, +-b, +-c with a = (-1, +1, 0), b = (0, -1, +1), c = (+1, 0, -1), so a + b + c = 0 (three
directions at 120 degrees). For a move v let (T_v u)(x) = u(x + v), with u = 0 off the live states, and

    M = (1/6)(T_a + T_b + T_c)   (restricted to the live states),   so   Q = M + M^T.

The Perron cubic: g_w(z) = z^3 - (w mu/2)(z^2 + z) + w - 1.

**Theorem.**

1. **Cubic.** lambda != 0 is an eigenvalue of S_w if and only if lambda = z^3 for a root z of
   z^3 - w (m z^2 + conj(m) z) + w - 1 = 0 for some eigenvalue m of M. (Young's consistently ordered case has
   z^2 - w mu z + w - 1 = 0 and lambda = z^2.) lambda = 0 is an eigenvalue only for w = 1.
2. **Every w.** For 0 < w < 2, rho(S_w) = max(R+, R-)^3, where R+ is the largest positive root of g_w and R- the
   largest modulus of a negative root (0 if there is none). The Perron mode decides for every w.
3. **The law.** rho(S_w*) = (w* - 1)^(3/4). The dominant eigenvalues are the simple pair +q^(3/2), -q^(3/2),
   q = sqrt(w* - 1): two real roots of opposite sign, not a double root, so no Jordan block.
4. **Optimality.** rho(S_w) > rho(S_w*) for every real w != w*: Young's w* is the unique minimizer.
5. **Gauss-Seidel.** For 0 < w <= 1, rho(S_w) = t^3 with t the positive root of t^3 - (w mu/2)(t^2 + t) - (1 - w) = 0;
   rho_GS = [(mu/4)(1 + sqrt(1 + 8/mu))]^3, and N^4 (rho_GS - mu^2) -> 16 pi^4/81 = 19.2413.
6. **Orderings.** The same spectrum holds for every ordering in which each lattice triangle, walked in the
   a, b, c direction, has exactly two steps to earlier states (or every triangle exactly one): the six
   lexicographic orders, backward sweeps, the two 3-colourings by (x1 - x2) mod 3, odd/even lines. It fails for
   a snake order and for a random order.

**Proof.**

**Step 1 (which neighbours come first).** In lexicographic order the neighbours of x that precede it are
x + a = (x1 - 1, x2 + 1), x + b = (x1, x2 - 1) and x - c = (x1 - 1, x2). So
L = (1/6)(T_a + T_b + T_{-c}) and U = (1/6)(T_{-a} + T_{-b} + T_c).

**Step 2 (a diagonal similarity).** Let f(x) = -2 x1 - x2, so f(a) = f(b) = 1 and f(c) = -2. For alpha != 0 let
D = diag(alpha^f(x)). Then D T_v D^-1 = alpha^(-f(v)) T_v, and with alpha^3 = lambda

    D (lambda L + U) D^-1 = (1/6)[lambda alpha^-1 (T_a + T_b) + lambda alpha^-2 T_{-c} + alpha (T_{-a} + T_{-b}) + alpha^2 T_c]
                          = alpha^2 M + alpha M^T.

**Step 3 (M is normal).** Each reflection of the triangle's reflection group permutes {a, b, c} (the reflection
across x1 = 0 swaps a and c and fixes b). So on the full lattice M and M^T commute with the group, and every
antisymmetrized plane wave (the eigenvectors of Q from the method of images, chunk 1) is an eigenvector of both,
with eigenvalues m and conj(m):

    m_kl = (1/6)(e^{i p1} + e^{-i p2} + e^{-i p3}),  p1 = 2 pi (2k + l)/(3N), p2 = 2 pi (k + 2l)/(3N), p3 = 2 pi (k - l)/(3N),

k, l >= 1, k + l <= N - 1 (2 Re m_kl = 1 - lambda_kl). These n vectors are a complete orthogonal basis (Prager
2001, completeness theorem; repeated eigenvalues of Q do not matter because the basis is given explicitly). So M
is normal and alpha^2 M + alpha M^T has the eigenvalues alpha^2 m + alpha conj(m).

**Step 4 (the largest |m|).** M commutes with Q and the Perron eigenspace of Q is one-dimensional, so the Perron
vector v > 0 satisfies M v = m v. M >= 0 forces m = mu/2, and a non-negative matrix with a positive eigenvector
has that eigenvalue as its spectral radius: |m| <= mu/2 for every m. Remark (found in the triage): every closed
walk made of the moves a, b, c has length 3k, so M has period 3 and exactly three eigenvalues of modulus mu/2,
namely (mu/2) times the cube roots of unity. If m = (mu/2) e^{2 pi i j/3}, the substitution z = zeta e^{2 pi i j/3}
turns its cubic into the Perron cubic in zeta, and z^3 = zeta^3: the three modes give the same eigenvalues lambda.

**Step 5 (part 1).** S_w u = lambda u means (lambda + w - 1) u = w (lambda L + U) u. By steps 2 and 3 this holds
for some u != 0 exactly when lambda + w - 1 = w (alpha^2 m + alpha conj(m)) for some m, with alpha = z,
lambda = z^3. For lambda = 0: det((1 - w) I + w U) = (1 - w)^n, zero only for w = 1.

**Step 6 (part 3).** Let q = sqrt(w* - 1) = (1 - sqrt(1 - mu^2))/mu, so 0 < q < 1, mu = 2q/(1 + q^2) and
w* mu/2 = q. Write m = (mu/2) c with |c| <= 1 and z = sqrt(q) y. The cubic becomes

    y (y^2 - conj(c)) = sqrt(q) (c y^2 - 1).

Since |y^2 - conj(c)|^2 - |c y^2 - 1|^2 = (|y|^4 - 1)(1 - |c|^2), a root with |y| > 1 would give
|y| |y^2 - conj(c)| > sqrt(q) |c y^2 - 1| (both sides vanish together only if |c| = |y| = 1). So every root has
|y| <= 1, that is |lambda| <= q^(3/2). For c = 1 the cubic is (y^2 - 1)(y - sqrt(q)) = 0, so lambda = +q^(3/2),
-q^(3/2) and q^3 are eigenvalues. Hence rho(S_w*) = q^(3/2) = (w* - 1)^(3/4). By the remark in step 4 the other
two modes with |c| = 1 give the same three eigenvalues, so +q^(3/2) and -q^(3/2) are simple.

**Step 7 (part 4).** g_w is linear in w, with g_w*(+-sqrt(q)) = 0. Its w-derivative is 1 - (mu/2)(q + sqrt(q)) > 0
at z = sqrt(q) and 1 + (mu/2)(sqrt(q) - q) > 0 at z = -sqrt(q). So for w < w*, g_w(sqrt(q)) < 0 and there is a real
root above sqrt(q); for w > w*, g_w(-sqrt(q)) > 0 and there is a real root below -sqrt(q). Either way
rho(S_w) > q^(3/2). (For w outside (0, 2), rho(S_w) >= |w - 1| >= 1.)

**Step 8 (part 5).** For 0 < w <= 1 any root satisfies |z|^3 <= (w mu/2)(|z|^2 + |z|) + (1 - w), so |z| <= t, and the
Perron mode attains t. At w = 1: t^2 = (mu/2)(t + 1). Expanding in 1/N gives the limit 16 pi^4/81.

**Step 9 (part 2, the case 1 < w < 2; Fable's nested-ellipse argument, re-derived here).** Put p = w mu/2,
s = w - 1 in (0, 1), m = (mu/2) c with c = |c| e^{i gamma}, |c| <= 1, and let z = rho e^{i theta} be a root. z != 0
because s != 0, and rho < 1 because SOR converges for a symmetric positive definite matrix when 0 < w < 2
(Ostrowski-Reich). Divide z^3 + s = p (c z^2 + conj(c) z) by z^(3/2):

    (rho^1.5 + s rho^-1.5) cos(3 theta/2) + i (rho^1.5 - s rho^-1.5) sin(3 theta/2)
        = p |c| [ (rho^0.5 + rho^-0.5) cos(phi) + i (rho^0.5 - rho^-0.5) sin(phi) ],   phi = theta/2 + gamma.

The left side is a point of the ellipse E1 with semi-axes a1 = rho^1.5 + s rho^-1.5 and b1 = |rho^1.5 - s rho^-1.5|.
The right side lies in the filled ellipse E2 with the same axes and semi-axes a2 = p (rho^0.5 + rho^-0.5) and
b2 = p (rho^-0.5 - rho^0.5). If a1 > a2 and b1 > b2, E2 is strictly inside E1 and the two sides cannot be equal.
Multiply by rho^1.5: a1 > a2 is g_w(rho) > 0, and -g_w(-rho) = rho^3 - s - p (rho - rho^2) > 0 implies b1 > b2.
g_w(rho) is a monic cubic in rho whose largest positive root is R+ (g_w(0) = s > 0, so g_w > 0 on (0, inf) if it
has no positive root), and -g_w(-rho) is a monic cubic whose largest positive root is R-. So both inequalities
hold for every rho > max(R+, R-): no mode has a root of larger modulus, and the Perron mode (c = 1) attains it.
(Codex gave a different proof, by Rouche's theorem; its text was not available to the Project chat.)

**Step 10 (part 6, orderings).** Steps 2 and 5 need only a function f on the states with f(x + v) - f(x) = +1 when
x + v comes before x and -2 when it comes after, for v in {a, b, c}. Around a lattice triangle
x -> x + a -> x + a + b -> x the three increments must sum to 0, which forces two steps to earlier states and one
to a later state; conversely that rule on every triangle defines f. If every triangle has exactly one step to an
earlier state, the same argument works with M and M^T exchanged (m and conj(m) swap; the set of cubics is the
same). A 3-colouring by (x1 - x2) mod 3 (each of a, b, c raises the colour by 1) is such an ordering.

**What the theorem does not say.** It is a statement about the spectral radius, not about sweep counts at a fixed tolerance. For b = 1 SOR(w*) needs
1.43 to 1.44 times Young's predicted sweeps at rtol 1e-10 (the 4/3 from the exponent times a transient constant
about 5.6). For the probability right-hand side P(player 1 out first) the run ends before the slowest mode
dominates and the count is 1.30 down to 0.96 times Young's prediction (N = 10 ... 640). Orderings with the same
spectrum have different transients: the 3-colour order needs 65, 134, 275, 564, 1157 sweeps for b = 1 at
N = 20 ... 320 against 64, 129, 258, 515, 1030 lexicographic. Above w* the radius is larger than Young's w - 1
(0.9234 at w = 1.9, N = 20).

**Numerical checks (three independent codes: Fable, Codex, the Project chat).** Project chat, own code (lexicographic order, dense matrices):
- 6M is an integer matrix with M M^T - M^T M = 0 exactly (N = 6, 7, 9, 12, 13, 16, 20, 25, 31); spec(M) equals the
  formula as a multiset to 3.3e-15; max |m| = mu/2, attained by exactly three eigenvalues, (mu/2) times the cube
  roots of unity.
- det((lambda + w - 1) I - w (lambda L + U)) = prod over m of (lambda + w - 1 - w (alpha^2 m + alpha conj(m))) at random
  complex lambda and random w: log|det| per unknown and phase agree to 1e-12 (N = 6 ... 40).
- rho(S_w) = max(R+, R-)^3 to 2.4e-14 at 118 values of w in (0.05, 1.95) for N = 7, 12, 13, 20, 30; the minimum over
  that grid is at w*; rho(S_w*) = q^(3/2) to 5e-15.
- All modes: over 98 values of w in (0.03, 1.97) no root of any mode cubic exceeds max(R+, R-) (N = 12, 31, 60, 97,
  150; largest excess 1.3e-14).
- Orderings (N = 12, 20; w = 1, w*, 1.7): the six lexicographic orders, the backward sweep, both 3-colourings and
  odd/even lines have the same traces tr(S^k), k <= 8, to 1.4e-14, and their triangles all have two (or all one)
  steps to earlier states. Snake: rho(S_w*) = 0.7189 against 0.6781 at N = 20. A random order: 0.7024 at w*, best
  0.6605 near w* + 0.02 (so lexicographic is not the best possible ordering).
- N^4 (rho_GS - mu^2) = 10.1329 (N = 6), 19.2005 (100), 19.2413 (1e5); N = 6: w* - 1 = (7 - 3 sqrt 5)/2 and
  rho = sqrt(5) - 2 exactly.
Reviewers: Fable verified N = 6 exactly in Q(sqrt 5) and the cubic to N = 150; Codex verified dense spectra at
N = 6 ... 40 including primes, and determinants to n = 741.

**Literature (searched by the reviewers; sources not re-opened in the Project chat unless marked).** Not found: the cubic, the exponent 3/4, or any SOR analysis of the six-neighbour triangular stencil. Related work
to cite: Varga 1959 (p-cyclic matrices; the one-sided operator M is 3-cyclic, and A is its symmetrization: period 3
confirmed here); LeVeque and Trefethen 1988 (the diagonal "tilt" of step 2, for the 5-point stencil); Adams,
LeVeque and Young 1988 (the 9-point stencil, another matrix that is not consistently ordered: a quartic, no closed
form); L. Adams' 1982 thesis (per Fable's literature agent: it names this stencil with three colours as not
consistently ordered in the generalized sense and says the theory for its optimal omega is still to be found; not
re-opened here). Not opened by anyone: Young 1971 ch. 13, Varga's book, the Adams-Jordan 1986 full text. So the
safe wording is "we did not find this result in the literature".

Wording for "why Young's theory does not apply": the graph of A is not bipartite (it has triangles), so A does not
have Property A and is not consistently ordered in any ordering.
