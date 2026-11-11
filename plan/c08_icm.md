# Chunk 8: ICM application

- **Depends on:** chunk 0 (uses `gr.matrix.order_probabilities`); chunk 1 for `gr.runlog`
- **Learn first:** Theory Guide §8 (absolute versus relative error: a small absolute ICM error can be a
  huge relative one). The ICM formula itself is in this spec.
- **Time:** build 30-45 min · compute about 1 min (full), under 10 s (`--quick`) · your review about 1 h ·
  plug in: no · peak memory about 0.5 GB (N = 640)
- **Read this yourself:** `gr/icm.py` (about 30 lines) and the two-line proof of the equity identity below

## Goal

The Independent Chip Model (Malmuth-Harville) is what poker players use to turn chip stacks into prize
money: player k wins with probability x_k/N, then among the rest, j takes 2nd with probability
x_j/(N - x_k). So P_ICM(ijk) = (x_k/N) * x_j/(N - x_k), with "ijk" = i out first, j out second, k wins
(the same labels as `gr.matrix`). Compare it with the exact gambler's-ruin probabilities at every
state, reproduce the Wikipedia table, and measure where and how badly the ICM errs. Four facts to
confirm with numbers:

1. **First place is exact** (P(win) = x/N in both models), so for payouts (w1, w2, w3) the equity error
   is exactly (w2 - w3) * (P_ICM(2nd) - P(2nd)). Proof: place probabilities sum to 1 and 1st is exact, so
   the 2nd- and 3rd-place errors cancel. Every ICM equity error is a second-place error.
2. The ICM **overrates short stacks and underrates big stacks** (sign checked at every state).
3. The error **does not vanish as N grows**: at fixed proportions the exact probabilities converge (at
   rate N^-4, as Diaconis and Ethier conjecture: arXiv:2011.07610v2, Conjecture 4.2(b); their Table 9 uses the same
   2:3:5 stacks) to a limit that differs from the ICM.
4. **Relative** error explodes where probabilities are tiny: from (N-2, 1, 1) the exact P(leader busts
   first) is about 9.12/N^3, the ICM says 2/(N(N-1)), so the ICM is off by a factor of about N/4.56. (Diaconis and Ethier, section 2.7, Remark 2, already note the two are of different orders, 1/N^3 against 1/N^2.)

## What to build (the tests import exactly these names)

`gr/icm.py`
- `icm_orders(X) -> dict[str, np.ndarray]`: X is an integer or float array of shape (m, 3) of stacks;
  returns the six keys "123", "132", "213", "231", "312", "321", each an array of shape (m,), with
  P_ICM(ijk) = (x_k/N) * x_j/(N - x_k) and N = the row sum.
- `place_probabilities(P, player) -> np.ndarray` of shape (3, m): rows P(1st), P(2nd), P(3rd) for
  `player` in {0, 1, 2}, from any dict of six order arrays (exact ones from `order_probabilities`, or
  ICM ones). 1st = orders whose last digit is the player, 2nd = middle digit, 3rd = first digit.
- `equity(places, payouts) -> np.ndarray`: w1 * places[0] + w2 * places[1] + w3 * places[2]; must work for
  places of shape (3,) and (3, m).

## Experiment

`experiments/e08_icm.py` writes, through `gr.runlog.save_results`:

1. `results/e08_wikipedia.csv`: N = 200, payouts 50/30/20, stacks (25,87,88), (21,89,90), (198,1,1)
   with player 1's stack listed first. One row per (stacks, method), method in {exact, icm,
   published_exact, published_icm} (published values copied from `PUBLISHED` in the test file). Columns:
   `stacks, method, p1st, p2nd, p3rd, equity`.
2. `results/e08_icm_errors.csv`: one row per N in {30, 60, 120, 240, 480} (`--quick`: 30, 60). Columns:
   `N, n, max_abs_err_p2, argmax_state, mean_abs_err_p2, max_rel_err_p3, argmax_rel_state_p3,
   max_equity_overrate, overrate_state, max_equity_underrate, underrate_state, identity_max_dev,
   short_overrated_all, long_underrated_all, frac_middle_overrated, seconds`.
   Maxima are over all states and all three players; states are written sorted ascending as "a-b-c".
   Equity columns use payouts 50/30/20. `mean_abs_err_p2` is over all states for player 1.
   `identity_max_dev` = max |equity error - (w2 - w3)(P_ICM(2nd) - P(2nd))| over the payouts
   (50,30,20), (65,35,0), (100,0,0), (50,50,0). `short_overrated_all` is True when every shortest stack
   (ties allowed, all-equal state skipped) has P_ICM(2nd) > P(2nd); `long_underrated_all` likewise with
   the largest stack and <. `frac_middle_overrated` is over states with three distinct stacks.
3. `results/e08_limit.csv`: stacks (N/5, 3N/10, N/2) for N in {10, 20, 40, 80, 160, 320, 640} (`--quick`:
   up to 80). Columns: `N, n, P123, P132, P213, P231, P312, P321, p1_second, icm_p1_second,
   obs_order_min, obs_order_max, seconds`, where obs_order = log2(|P(N/2) - P(N/4)| / |P(N) - P(N/2)|) over
   the six orders (blank for N < 40).
4. `results/e08_states_N120.csv`: every state at N = 120 with `x1, x2, x3, dp2_player1, dequity_player1`.

Figures: `figures/f08_icm_map.py` (triangle heat map of P_ICM(2nd) - P(2nd) for player 1 at N = 120,
diverging color map centered at 0) and `figures/f08_limit.py` (|P(N) - P(N/2)| against N, log-log, with
a slope -4 guide line).

## Acceptance tests

`pytest tests/c00_core tests/c08_icm` (34 new tests). They check the ICM formula by hand at (2,1,1),
that ICM orders sum to 1 and give P(1st) = x/N, the relabeling symmetry, place probabilities by hand at
N = 4 (exact 1/2, 5/14, 1/7; ICM 1/2, 1/3, 1/6), the equity identity for four payout vectors, the
Wikipedia table (to print precision) and our own 10-digit values at N = 200, the largest second-place
error at N = 60 and where it is, the short-stack / big-stack sign at every state for N = 30 and 61, the
center state, the leader-busts-first relative error at N = 60 and 120, fourth-order convergence at
fixed proportions, and the nonzero limiting error.

## Expected results (the check script tests these against the CSV)

| Check | Expected | Tolerance | Kind |
|---|---|---|---|
| e08_wikipedia exact p2nd at (25,87,88), (21,89,90), (198,1,1) | 0.1584080071, 0.1346400128, 0.0099988601 | 1e-9 abs | FAIL |
| e08_wikipedia exact equity, same rows | 25.33408007, 24.49640013, 49.79998860 | 1e-7 abs | FAIL |
| exact vs published_exact rows | p1st, p2nd, p3rd within half a printed digit (5e-5; 5e-7 for (198,1,1)); equity within 0.005 | | FAIL |
| icm vs published_icm rows | within one printed digit (1e-4; 1e-6 for (198,1,1)); equity within 0.005 | | FAIL |
| max_abs_err_p2 at N = 30, 60, 120, 240, 480 | 0.0358888708, 0.0359655670, 0.0360434580, 0.0360462040, 0.0360502475 | 1e-9 abs | FAIL |
| argmax_state | 4-13-13, 7-26-27, 15-52-53, 30-105-105, 59-210-211 (runner-up gaps 2e-4 to 1.3e-6) | exact | FAIL |
| mean_abs_err_p2 | 0.01655161, 0.01604887, 0.01574379, 0.01557549, 0.01548642 | 1e-7 abs | FAIL |
| max_equity_overrate | 10 x max_abs_err_p2 (w2 - w3 = 10), at the same states | 1e-8 abs | FAIL |
| max_equity_underrate | -0.27088621, -0.27220714, -0.27253356, -0.27257953, -0.27259922 at 6-6-18, 12-13-35, 25-25-70, 50-51-139, 101-101-278 | 1e-8 abs, state exact | FAIL |
| identity_max_dev | below 1e-10 | | FAIL |
| short_overrated_all, long_underrated_all | True at every N | | FAIL |
| max_rel_err_p3 | 5.8060831, 12.3815091, 25.5381260, 51.8541766, 104.4876678, all at (N-2)-1-1 | 1e-6 relative | FAIL |
| frac_middle_overrated | 0.1639, 0.1808, 0.1876, 0.1921, 0.1935 (increasing) | 1e-3 abs | WARN |
| obs_order_min, obs_order_max at N = 80, 160, 320 | in [3.9, 4.1] | | FAIL |
| obs_order at N = 640 | in [3.8, 4.2] (differences are near 5e-11, so rounding shows) | | WARN |
| P123, P213, P321 at N = 640 | 0.3096287142, 0.1903712858, 0.0662037586 | 1e-9 abs | FAIL |
| p1_second at N = 640; icm_p1_second | 0.2607768223; 2/7 = 0.2857142857 | 1e-9; 1e-15 | FAIL |
| seconds at N = 640 | under 30 s | | WARN |

Why fourth order: the six-neighbor stencil is isotropic to fourth order (z^m is discrete harmonic on
the triangular lattice for m <= 5), so for these harmonic probabilities the local error is O(h^6) and
the global error O(N^-4). The rate is Diaconis and Ethier's Conjecture 4.2(b) (they call the convergence surprising and test it with one comparison at N = 300); we measure orders 3.96 to 4.03 for all six orders at N = 80 to 640. The isotropy argument is our heuristic explanation, not a proof.

## Red flags (bring these to the Project chat)

- Any P_ICM(1st) different from x/N, or identity_max_dev above 1e-10: the order labels are mixed up
  (the most common bug: reading "ijk" as i wins).
- A short stack underrated anywhere, or a big stack overrated.
- max_abs_err_p2 decreasing in N, or obs_order near 2 (that would mean a wrong stencil or boundary).
- The Wikipedia exact row off by more than print precision: check that player 1's stack is listed first.

## Done when

- [ ] `pytest tests/c00_core tests/c08_icm` passes.
- [ ] The four CSVs and both figures exist.
- [ ] `python checks/check_c08.py` prints every row PASS (WARN allowed only on WARN rows); report saved
  to `results/c08_report.md`.
- [ ] `notes/decisions.md` has a chunk 8 entry; committed as "chunk 8: ICM application".

## Paste back into the Project chat

`results/c08_report.md` and the N = 120 heat map.
