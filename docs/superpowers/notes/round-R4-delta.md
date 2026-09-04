# Round R4 — Track Widenings — Delta

**Landed 2026-09-04.** Branch `round-R4-track-widenings`, 9 commits off `main` @ `477f39d`
(`ac9c90c` baseline, `60c84e0` + `c466e0b` Contract readers, `24e6c96`+`48a105a` Stackelberg
vector branch, `b323e51` Stackelberg FSS, `2b4bfb3` VCG monotone-threshold path,
`18aeed8` VCG transcription, `65c8e83` Track 3 + Kang2019/Tian2021, `f52b024` re-sweep +
adjudication).
Plan: `docs/superpowers/plans/2026-09-04-R4-track-widenings.md`. Authored *from* the
R2/R3 `MANUAL` catalogue (`round-R2-R3-delta.md` §"MANUAL catalogue").

## Per-slice — before / after

Baseline captured pre-sweep (`round-R4-baseline.md`). "After" is the merged result.

### VCG (33 entries)

| Verdict | Baseline | After R4 | Δ |
|---|---|---|---|
| VERIFIED (entry-specific) | 3 | **4** | +1 |
| VERIFIED_SHAPE (R6 candidates) | 10 | 10 | — |
| MANUAL | 20 | **19** | −1 |
| UNKNOWN | 0 | **0** | — |

### Contract (38 entries)

| Verdict | Baseline | After R4 | Δ |
|---|---|---|---|
| VERIFIED (entry-specific) | 5 | **6** | +1 |
| VERIFIED_TEMPLATE (R6 candidates) | 8 | 8 | — |
| MANUAL | 25 | **24** | −1 |
| UNKNOWN | 0 | **0** | — |

### Stackelberg (30 entries)

| Verdict | Baseline | After R4 | Δ |
|---|---|---|---|
| VERIFIED (entry-specific) | 1 | 1 | — |
| VERIFIED_TEMPLATE (R6 candidates) | 14 | 14 | — |
| MANUAL | 15 | 15 | — |
| UNKNOWN | 0 | **0** | — |

**In-scope UNKNOWN stays 0** (it was 0 entering R4). All three slice gates `GATE: PASS`.
Full suite 446 passed / 1 skipped / 3 xfailed / 0 failed. The 32 R6 formalization-miss
candidates did not grow. Non-attempted entries byte-identical.

## New VERIFIED (2) — both independently PDF-confirmed

Full cross-checks in `docs/superpowers/notes/round-R4-new-verified.md`.

### `Tian2021contract` — Contract, Track 2

- **Widening:** Task 8 corrected the entry's `type_variable` from the ambiguous prose
  *"data coverage quality θ_i and training willingness e_i"* (which made `_type_family()`
  match both the `theta` and `e` families → no type ordering → MANUAL) to just `\( θ_i \)`.
- **Sound because:** the paper's effort variable is a moral-hazard *action*, not a second
  screening type. Paper Eqs. 10–11: the client's own FOC gives `ê_i = (1/c)θ_i R_i`, and
  effort is substituted out *before* the screening IC. The operational IC/IR (Eqs. 12, 19)
  are one-dimensional in `θ_i` with single-crossing `(θ_i−θ_j)(R_i−R_j) ≥ 0` (Eq. 16).
  The Task 9 reviewer confirmed the substitution verbatim from PDF p.3.
- **Cross-check:** degree-0 Positivstellensatz (posynomial) certificate over
  ordered-increment coordinates, no SDP. IC gap dumped symbolically, signs
  `+0 / +0.5625 / +1.75 / +2.5` at concrete type pairs; IC(1,0)=IR(0)=0 binding, IR(1)≥0.
- **Disclosed assumption:** the certificate treats `de_1 ≥ 0` (effort co-monotone with `θ`)
  as a declared solver assumption (`track2_sos.py:460`, `nonnegative=True`). This is
  *licensed by direct algebra* — Lemma 1 gives `θ` and `R` co-increasing, so `ê_i` is a
  product of two co-increasing positives — not merely by analogy to standard screening.
  Recorded under a ⚠ heading in the new-verified block. R6 note: the entry's raw
  `ic_screening_latex` still carries `e_i, e_j`, `num_types: 2`, `multidimensional_type: true`;
  an R6 consumer re-deriving from the raw field without importing Lemmas 1–2 will not
  reproduce the certificate.

### `Zheng2023fl_market` — VCG, Track 1 (monotone winner rule + critical-value payment)

- **Widening:** Task 6 landed the `MonotoneThreshold` DSIC path; Task 7 transcribed
  `winner_rule_monotone` + `critical_price_latex` from the All-in mechanism (Appendix B,
  Algorithm 4, Proposition 2 — Myerson: monotonicity + critical payment ⟹ truthfulness).
- **The eligibility gate is not the proof.** With no executable budget-greedy allocation
  semantics, `verify_monotone_threshold_dsic`'s grid check models the winner rule as
  `wins = b_i ≥ c*` — monotone by construction, so the grid loop can never fail. The real
  discriminators are: a `cite` present, `critical_price_latex` matching an infimum/critical-bid
  shape (here it matched the literal prose *"critical bid for i"*, not a structural form),
  and no anti-monotone prose. The flip decision is the **Task 9 hand-checked lemma**.
- **Cross-check (Task 9, independently re-derived by the Task 9 reviewer from Algorithm 4):**
  the paper argues sort-position monotonicity only *"intuitively"* and closes the
  self-referential moving threshold `B/Σ_{j∈W∪{i}} d_j·ε̄_j'` with a one-line inequality.
  The rigorous close: cross-multiply the acceptance test to `V_i·T_i ≤ (B−V_i)·w_i` where
  `T_i = Σ_{j∈W, j≺i} w_j` is a **prefix** quantity — `W` is append-only across the whole
  algorithm (no eviction, no backtracking, no fixed point), so when `i` is tested `W`
  contains only already-accepted `j` strictly earlier in the sort; the `∪{i}` is just `w_i`,
  moved to the RHS. Lowering `v_i^unit` (the manipulation direction: `V↓`/`d↑`/`ε̄↑`) weakly
  improves `i`'s sort position → `i`'s predecessor set shrinks → `T_i' ≤ T_i` → the
  inequality is preserved → `i` stays a winner. Monotone + critical payment ⟹ DSIC.
  Corroborated by ~1.4M randomized profiles, 0 violations.

## The four widenings — reclaimed vs attempted

| Widening | Code | Reclaimed / attempted | Why the rest didn't reclaim |
|---|---|---|---|
| **Contract positivity-domain + opaque-function inline** (`track1_z3.py` `_positivity_domain`, `_opaque_inline`, `_is_definitely_positive_sum` integer-power fix) | landed, fail-closed, 6 new tests | **0 / 5** | `Kang2019reliable_contract`: log admitted via `positivity_domain` but Z3 still returns UNKNOWN on IC+IR — the obstruction was never the log admissibility. `2102_03401`: R3a diagnosis was factually wrong — `u_3` is a *scalar* (unit energy cost), not an opaque function; re-diagnosed as a corpus transcription bug. `Nguyen2025right_reward`: `h(t_k)` is 2-branch piecewise; `opaque_function_forms` maps one name to one form. `2407_02845`: admitting `log(θ_m R_m)` needs `θ_m R_m ≥ 1`, unstated in the paper. `Han2025paid_models`: no source PDF exists. |
| **Stackelberg vector-decision stationarity system** (`_stackelberg_check_core` tuple branch, `_solve_stationarity_system`, `_br_components_match`, `_check_follower_ir_at`) | landed, fail-closed, 7 tests | **0 / 8** | The checker is **unreachable**: the deliberate R3b sibling-name guard at `track1_z3.py:1610-1620` returns `None` before the vector branch, and `_lx_parse` collapses superscript components (`x_i^r` → `x_{i}**r`). Ruled: keep the code + the 3 transcribed FSS (`2502_10765`, `Yu2022multi_leader_fl`, `Liu2026fedbud`) as R6 input; do not fix the blockers this round — routing past the guard is a redesign, and superscript disambiguation is the change class that produced R3a's reverted unsound flip. |
| **VCG monotone-threshold / critical-value DSIC** (`vcg_dsic.py` `MonotoneThreshold`, `verify_monotone_threshold_dsic`) | landed, fail-closed (eligibility gate), 4 tests | **1 / 7** (`Zheng2023fl_market`) | `Jiao2019auto_auction`: cross-paper provenance bug — the entry's `allocation_rule_latex`/`payment_rule_latex` are byte-identical to `Jin2023bara_budget`'s and absent from the Jiao2019 PDF (the paper proves monotonicity for a rule the entry doesn't record). `Jin2023bara_budget`: no theorems/proofs — BARA is budget allocation "orthogonal to incentive mechanisms". `Ahmed2023frimfl`, `2404_13841`: no monotonicity/critical-payment/Myerson content. `Lu2021cluster_auction`: fixed-point eviction (provisional set → `s_min` threshold → reselect) → not monotone in own report; BNE-strategy payment. `GPS2023afl_recruit`: no PDF, first-price `p_i = b_i − C_i(t)` (increasing in own bid, identical to `client_utility_latex` — degenerate); assessed for COUNTEREXAMPLE, fails closed to MANUAL (no model to build a witness). |
| **Track 3 fixed-constant box reduction** (`track3_dreal.py` `_fix_declared_constants`, `mech` kwarg on `track3_check_from_sympy`) | landed, fail-closed, 3 tests | **1 / 2** (`Tian2021contract`, via the bundled `type_variable` fix) | `Kang2019contract_mobile`: pinning the 3 paper-declared constants (`μ=1, c_n=5, s_n=20`) drops the IC box from 9→6 free vars and the IR box from 11→8, but IR is still over `_MAX_BOX_DIMS` and IC comes back inconclusive. `ζ` and the transmission sub-symbols (`σ, ρ_n, B, h_n`) have no per-symbol numeric values in the paper — only the composite `E^com = 20` — so they were left free (fail-closed). |

## Rejected flips

**None.** Both candidate flips cross-checked and held. `GPS2023afl_recruit` was assessed
for COUNTEREXAMPLE and fails closed to MANUAL (first-price, degenerate, no PDF).

## Still MANUAL after R4 — grouped by refreshed ceiling

Every R4-attempted entry that did not reclaim has its `manual_diagnosis` bumped to
`round: "R4"`, `date: "2026-09-04"`, with `human_task` stating what R4 tried and why it
did not close. Grouped:

- **R6 corpus re-extraction / transcription fix** (a data problem, not a math ceiling):
  `Jiao2019auto_auction` (cross-paper provenance — fields belong to `Jin2023`),
  `2102_03401` (`u_3` is a scalar written as a function call),
  `Han2025paid_models` (no source PDF, all id fields null),
  `Nguyen2025right_reward` (`h(t_k)` piecewise — needs a two-branch encoding).
- **R6 parser round** (the tooling exists, the parser can't reach it):
  the 8 Stackelberg vector-decision entries (`2101_05628`, `2101_12428`, `2502_10765`,
  `Guo2023stackelberg_industrial`, `Li2025split`, `Liu2026fedbud`, `Wang2022blockchain`,
  `Yu2022multi_leader_fl`) — need the sibling-name-guard bypass + superscript-component
  disambiguation before `_stackelberg_check_core`'s vector branch fires.
- **Genuine math ceiling absent new data/proof:**
  `2407_02845` (needs `θ_m R_m ≥ 1`, unstated),
  `Kang2019contract_mobile` (IR box still over `_MAX_BOX_DIMS` after fixing 3 constants),
  `Kang2019reliable_contract` (log admitted but Z3 UNKNOWN — deeper obstruction),
  `Wang2022blockchain` (corner solution; the paper prints `dU/dq < 0` in both variables
  then miscalls it concave; real stationarity is a time-constraint Lagrangian matching
  neither stored field — R6 re-derivation),
  `Jin2023bara_budget`, `Ahmed2023frimfl`, `2404_13841`, `Lu2021cluster_auction`
  (no monotonicity result / fixed-point eviction / first-price payment),
  `GPS2023afl_recruit` (first-price, degenerate, no PDF — a COUNTEREXAMPLE candidate for R6).

## Deferred minors cleared this round

- `scripts/snapshot_verdicts.py --out` is now **required** (no default) — a `--only <cat>`
  query can no longer silently clobber `round-R2-baseline.md`.
- `_BAYESIAN_RE` → `_STACK_BAYESIAN_RE` in `track1_z3.py` (was a cross-file name collision
  with the different pattern in `verifier.py:59`, which is untouched).
- 7th meta-field reader `follower_utility_latex` in `_try_stackelberg_latex` now goes
  through `_as_str()` (the last unguarded site from the R3b `_as_str` sweep).
- `_opaque_inline` now skips a `name(args)` substitution when the declared form references
  no symbol from `args` (prevents silently dropping a scalar's operand — the `2102_03401`
  `u_3` trap).

## What R4 built for R6

Four reviewed, fail-closed solver code paths, staged for R6 once the parser / provenance
fixes land:

1. **Contract Track-1 admissibility readers** — `_positivity_domain`, `_opaque_inline`,
   and `_is_definitely_positive_sum` now accepting `positive^int > 0`. Work correctly;
   the target entries have deeper obstructions.
2. **A full vector-follower Stackelberg checker** — `_stackelberg_check_core`'s tuple
   branch + `_solve_stationarity_system` + `_br_components_match` + `_check_follower_ir_at`.
   Unreachable until R6 bypasses the sibling-name guard and disambiguates superscript
   components. Plus 3 PDF-transcribed follower stationarity systems
   (`Liu2026fedbud`'s is caveated — it's a from-Eq.(17) reconstruction that does not
   reproduce the entry's own `best_response_latex` by a `√γ₂` factor, a paper-internal
   Eq.17-vs-Eq.38 inconsistency; reconcile before consuming).
3. **A VCG Myerson eligibility gate** — `verify_monotone_threshold_dsic`. Becomes a real
   proof with executable budget-greedy allocation semantics; otherwise it trusts a
   Task-9-vetted monotonicity cite.
4. **Track 3 box reduction** — `_fix_declared_constants`.

## Monotone gate

All three slice gates → `GATE: PASS`. Every moved entry `improved`
(`Zheng2023fl_market`: MANUAL → VERIFIED; `Tian2021contract`: MANUAL → VERIFIED). No
regression. Out-of-scope (`Valuation`/`RL`/`Naive`) and Shapley entries unchanged.

## Handoff

- **R5** (Shapley coalition track) — unchanged, independent of R4. The 4 Shapley entries
  stay `UNSUPPORTED`.
- **R6** (second-formalizer pass on residual `MANUAL`) — inputs: the R4-refreshed MANUAL
  diagnoses; the rejected/deferred data problems (`Jiao2019` cross-paper provenance,
  `2102_03401` transcription fix, `Han2025paid_models` missing PDF, `Nguyen2025right_reward`
  piecewise `h`); the `Liu2026fedbud` FSS `√γ₂` reconciliation; the Stackelberg-vector
  parser blockers (sibling-name guard + superscript collapse); `Wang2022blockchain` corner
  re-derivation; the `GPS2023afl_recruit` COUNTEREXAMPLE candidate; and the 32 R6
  formalization-miss candidate lists from R2/R3a/R3b, all held.
