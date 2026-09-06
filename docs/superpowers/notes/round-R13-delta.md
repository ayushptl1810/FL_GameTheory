## Round R13 — Transcendental / Implicit Root-Finding Fallback — Delta

**Landed 2026-09-06.** No branch this round (program-level deviation, see
umbrella spec). Plan:
`docs/superpowers/plans/2026-09-05-R13-transcendental-rootfinding.md`.
Flip cross-check: `docs/superpowers/notes/round-R13-new-verified.md`.
Baseline: `docs/superpowers/notes/round-R13-baseline.md`.

**This is the final round of the R11-R13 solver-capability-expansion
program.** The umbrella spec's `## Program summary (post-R13)` section is
written by this round's Task 8.

### Targeted entries -- before / after

| paper_id | category | before | after | blocker R13 hit |
|---|---|---|---|---|
| 2407_02845 | Contract | MANUAL | MANUAL | log *argument* sign unprovable (`theta_m R_m > 1`), not an opaque function |
| Han2025paid_models | Contract | MANUAL | MANUAL | `E[.]` expectation operator misparsed as Euler's `E`; monotone-`v` != monotone-`E[v]` |
| Nguyen2025right_reward | Contract | MANUAL | MANUAL | `h(t_k)` scaled by non-constant `theta_k e_k` (guard rejects); + genuinely 2-D type |
| Chu2023hierarchical | Stackelberg | MANUAL | MANUAL | FOC has un-pinned paper params + leader reward; numeric solver fails closed |
| Luo2023unbiased | Stackelberg | MANUAL | MANUAL | utility carries opaque `E[F(w^R(q))]`; `foc.has(Derivative)` hard-bails before numeric |
| Pandey2019crowd | Stackelberg | MANUAL | MANUAL | fallback triggers but FOC has un-pinned `r, nu_k, T_k, gamma_k` (`r` is leader's choice) |

**0 flips.** Valid per the umbrella spec ("any round that reclaims 0 entries
but lands correct, tested, fail-closed capability is still a valid
outcome" -- R3a/R3b/R5 precedent).

### What shipped (`src/tracks/track1_z3.py`)

1. **`_sp_to_z3(expr, cache, monotone_functions=None)`** -- new optional
   third parameter. A `Function` call node whose name is a key in
   `monotone_functions` becomes a fresh opaque Z3 auxiliary real (distinct
   arguments -> distinct reals), same treatment as `log`/`exp`. The
   monotonicity fact is *not* encoded as a Z3 constraint. Existing 2-arg
   call sites are unchanged; the `Add`/`Mul`/`Pow` recursions thread the
   parameter through. Tests: `tests/tracks/test_sp_to_z3_monotone.py`.

2. **`_monotone_difference_functions(gap, declared)`** -- new module-private
   guard. Returns the subset of `mechanism["opaque_function_monotonicity"]`
   that appears in the symbolic IC gap `U_ir - U_rhs` *only* as a
   sign-determinate constant multiple of a same-function two-point
   difference `C * (f(a) - f(b))` (structural: substitute a placeholder per
   distinct argument, require total degree <= 1 in the placeholders, and
   require the two coefficients to be equal-and-opposite sign-determinate
   numbers). Conservative -- returns `{}` on anything else, including a
   function multiplied by a type/menu-dependent coefficient.

3. **`_contract_check_core` wiring** -- computes `safe_mono` from the guard
   and threads it into every `_sp_to_z3` call. The opaque-fn aux reals are
   left **free**: `used_transcendental` is extended so any residual
   `COUNTEREXAMPLE` off those free reals is downgraded to `UNKNOWN`, and the
   blanket `var > 0` precondition loop explicitly skips them (no unwarranted
   positivity). A `VERIFIED`, if reached, is sound -- it would hold for every
   `f`, the true monotone one included.

4. **Scalar numeric-root fallback in `_stackelberg_check_core`** -- when
   `sp.solve(foc, e_sym)` returns nothing or raises (`NotImplementedError`
   on a multi-generator transcendental FOC), and `foc` still contains
   `e_sym`, the scalar branch calls R11's `_numeric_solve_stationarity`
   verbatim with a 1-element decision list. R11's fail-closed discipline is
   unchanged (>=2 of 3 fixed starts agree within `1e-6`, residual `< 1e-8`,
   any un-pinned free parameter -> `None`). The root is fed to the same
   downstream second-order / IR / best-response checks as an exact critical
   point. Tests: `tests/tracks/test_stackelberg_scalar_numeric.py`.

### Corpus data

No `corpus.json` field additions. Task 2 (`2407_02845` positivity domain),
Task 4 (`opaque_function_monotonicity` for the two Contract entries) and
Task 6 (`fixed_constants` for the three Stackelberg entries) all resolved to
"no honest field to add" -- no source PDFs are in the repo, and in every
Stackelberg case the un-pinned symbols include a leader decision variable
that pinning would make the verdict unsound. The 6 `manual_diagnosis` dicts
were refreshed to `round: "R13"` with the specific reason each remains
`MANUAL` (`prior_round` breadcrumb kept). `MANUAL-backlog.md` was
regenerated from the corpus (that commit also clears pre-existing generator
drift left by R11/R12 not re-running the script).

### Corpus totals

| verdict | R13 baseline | after R13 |
|---|---|---|
| VERIFIED | 12 | 12 |
| VERIFIED_TEMPLATE | 0 | 0 |
| MANUAL | 93 | 93 |
| UNKNOWN | 0 | 0 |

`--only Contract` and `--only Stackelberg` gates: `GATE: PASS`. Full test
suite: 492 passed, 2 skipped, 3 xfailed.

### Handoff

None -- last round of the program. See the umbrella spec's
`## Program summary (post-R13)` for the R11+R12+R13 wrap-up and the named
residual gaps.
