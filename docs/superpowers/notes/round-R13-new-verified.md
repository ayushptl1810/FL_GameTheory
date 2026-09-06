# R13 — New VERIFIED / COUNTEREXAMPLE flips, with independent cross-checks

**Flip count: 0.**

R13 shipped two fail-closed solver-encoding capabilities and re-swept the 6
transcendental-cluster entries R9 catalogued. No corpus entry flipped: in
every case the entry's real blocker sits outside what the new capability
removes, and the fail-closed rule leaves it `MANUAL` (now with a corrected
R13 `manual_diagnosis`, Task 7).

## What shipped

1. **`_sp_to_z3` monotone-opaque-function admission** (`src/tracks/track1_z3.py`).
   A new optional `monotone_functions` parameter lets an otherwise-unsupported
   `Function` node become an opaque Z3 auxiliary real, *only* when the caller
   (`_contract_check_core`) has confirmed via `_monotone_difference_functions`
   that the function appears in the symbolic IC gap `U_ir - U_rhs` solely as a
   sign-determinate constant multiple of a same-function two-point difference
   `C * (f(a) - f(b))`. The monotonicity fact itself is never encoded as a Z3
   constraint (the aux reals stay free); a residual `COUNTEREXAMPLE` from
   those free reals is downgraded to `UNKNOWN` (extended `used_transcendental`),
   and the blanket `var > 0` precondition explicitly skips the opaque-fn aux
   reals so no unwarranted positivity is asserted. A `VERIFIED`, if reached,
   is sound: it would hold for *every* `f`, which includes the true monotone
   one. Unit-tested in `tests/tracks/test_sp_to_z3_monotone.py`.

2. **Scalar transcendental/implicit FOC numeric-root fallback**
   (`_stackelberg_check_core`, `src/tracks/track1_z3.py`). When
   `sp.solve(foc, e_sym)` yields nothing (or raises `NotImplementedError` on a
   multi-generator transcendental FOC), the scalar branch now calls R11's
   `_numeric_solve_stationarity` verbatim with a 1-element decision list. Its
   existing fail-closed discipline is unchanged: >=2 of 3 fixed start points
   must agree within `1e-6` with residual `< 1e-8`, any un-pinned free
   parameter symbol returns `None`. A found root is fed to the same
   downstream second-order / IR / best-response checks as an exact critical
   point — no new trust path. Tested in
   `tests/tracks/test_stackelberg_scalar_numeric.py` (a synthetic
   `U = -e^2/40 - e/5 + 2 log(1+e) + e^{-e}` whose FOC SymPy cannot close;
   numeric root `e* ~= 3.8376`, `U''(e*) ~= -0.114 < 0`, `U(e*) ~= 2.039 > 0`
   -> `VERIFIED`; plus an un-pinned-parameter case that returns `None`, and a
   closed-form-FOC regression guard).

## Why zero flips — per entry

### Contract

- **`2407_02845`** — blocker is the log *argument* sign, not an opaque
  function. `_is_definitely_positive_sum(theta_m R_m - 1)` must hold for the
  log encoding; the positivity-domain reader can supply `theta_m > 0`,
  `R_m > 0` but not the product lower bound `> 1`, which R4 confirmed the
  paper never states (and no PDF is in the repo to re-check). R13's
  monotone-opaque-function path does not apply. Stays `MANUAL`.
- **`Han2025paid_models`** — `v` is stated increasing (key_assumptions) and
  the parsed IC gap *does* have the difference shape
  `E*(v(r_i) - v(r_j)) + c_i*(m_j - m_i)`, so `_monotone_difference_functions`
  would admit it. But the `E` there is the LaTeX parser's misread of the
  expectation operator `E[.]` as Euler's number: the mechanism is
  `E[v(r_i)]`, and "`v` increasing" does not give "`E[v(.)]` increasing"
  without a monotone-report assumption the transcription does not carry.
  Admitting it would certify against a misparse. No
  `opaque_function_monotonicity` field added. Stays `MANUAL`; ceiling now
  identified precisely as the expectation operator.
- **`Nguyen2025right_reward`** — `h(t_k)` appears in the IC gap as
  `theta_k*e_k*h(t_k) - theta_k*e_{k'}*h(t_{k'})`, i.e. scaled by a
  type/menu-dependent coefficient, not a constant-multiple difference.
  `_monotone_difference_functions` correctly rejects it (`theta_k*e_k` is not
  a sign-determinate constant). The paper also states no monotonicity for
  `h` (R4 found it 2-branch piecewise), and the type `(theta_k, t_k)` is
  genuinely 2-D. Independent ceilings; stays `MANUAL`.

### Stackelberg

- **`Chu2023hierarchical`** — FOC in `K_l` carries un-pinned paper
  parameters (`chi_l, G, lambda, A_l, F_l, B_l, xi, rho_l, |S_l|, x_l`) plus
  the leader reward. `_numeric_solve_stationarity` returns `None` while any
  free non-decision symbol remains. No `fixed_constants` added — no source
  PDF for a numerical setup, and pinning the leader variable would make a
  verdict valid at one reward only. Stays `MANUAL`.
- **`Luo2023unbiased`** — the follower utility contains
  `v_n*(F(w_n*) - E[F(w^R(q))])`, an opaque expectation of an opaque
  objective; `sp.diff` leaves a `Derivative` node and `_stackelberg_check_core`
  hard-bails (`foc.has(Derivative)`) *before* the numeric fallback. The
  recorded cubic `follower_foc_latex` is not consumed (the checker
  differentiates the utility itself), and the true optimum is box-clipped.
  Stays `MANUAL`.
- **`Pandey2019crowd`** — the FOC (`1/theta_k - log(1/theta_k) = const`) is
  exactly R13's target shape and the fallback *does* trigger (`sp.solve`
  raises), but it fails closed: the FOC carries un-pinned `r, nu_k, T_k,
  gamma_k`, where `r` is the leader's reward choice. No `fixed_constants`
  added (no source; `r` is a decision variable). The `theta_th` min-clip is
  also unmodelled. Stays `MANUAL`.

## Cross-check status

No flip to cross-check. Both new capabilities have runnable
`assert`-based tests pinned to the motivating shapes; the full suite is
green (492 passed) and both monotone corpus gates
(`--only Contract`, `--only Stackelberg`) print `GATE: PASS`.
