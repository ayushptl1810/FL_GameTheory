# Rounds R2 + R3 — Corpus Sweep — Combined Delta

Plan: `docs/superpowers/plans/2026-09-02-zero-unknown-r2-r3-corpus-sweep.md`.
This file gathers the per-round deltas for the R2 (VCG) and R3 (Contract, Stackelberg)
corpus sweeps. The standalone VCG write-up lives in `round-R2-delta.md`; the sections
below summarise each round and Task 16 finalises the combined counts + R4 handoff.

---

## VCG (R2)

**Landed 2026-09-03.** Branch `round-R2-vcg-sweep` (merged to `main` @ `fbdb29d`).
Full detail: `round-R2-delta.md`.

| Verdict | Baseline | After R2 | Δ |
|---|---|---|---|
| VERIFIED (entry-specific) | 0 | 3 | +3 |
| VERIFIED_SHAPE | 33 | 10 | −23 |
| MANUAL (diagnosed) | 0 | 20 | +20 |
| UNKNOWN | 0 | 0 | — |

VCG UNKNOWN = 0. 10 VERIFIED_SHAPE entries parked as R6 formalization-miss
candidates. Monotone gate `PASS`, no regression.

---

## Contract (R3a)

**Landed 2026-09-03.** Branch `round-R3-contract-sweep`, 5 commits off `main` @ `fbdb29d`
(`089d5c5` baseline, `c237588` + `95fd3cc` Task 11-pre, `3f68e1f` sweep, `85bff9c` adjudication).

### Contract slice (38 entries) — before / after

| Verdict | Baseline (`main`) | After R3a | Δ |
|---|---|---|---|
| VERIFIED (entry-specific) | 5 | **5** | — |
| VERIFIED_TEMPLATE | 31 | **8** | −23 |
| MANUAL (diagnosed) | 0 | **25** | +25 |
| UNKNOWN | 2 | **0** | −2 |
| COUNTEREXAMPLE | 0 | 0 | — |

**Contract UNKNOWN = 0.** Monotone gate `PASS` — 25 `improved`
(`VERIFIED_TEMPLATE → MANUAL` ×23, `UNKNOWN → MANUAL` ×2), 0 regressions. The 8
entries left `VERIFIED_TEMPLATE` are R6 formalization-miss candidates (per the
plan: formalization miss ⇒ keep the baseline verdict, no baseline rewrite).
Non-Contract slices (VCG / Stackelberg / Shapley / Valuation / RL / Naive)
byte-identical. Full suite 416 passed / 1 skipped / 3 xfailed / 0 failed.

### Diagnose-only round — no new VERIFIED

The R1 LLM formalizer produces **0 valid ASTs for Contract** (the same wall R2
hit for VCG). The `--only Contract` sweep returned 38 UNKNOWN from the AST/LLM
path and `corpus.json` was byte-identical afterward. The 5 pre-existing
entry-specific VERIFIED entries (`2307_15975`, `Li2025bayesian_incentive`,
`Lim2020contract_healthcare`, `Sun2022coded`, `Tan2025renegotiable_contract`)
hold via `verify()`'s own LaTeX path, untouched.

### What Task 11-pre built (kept, non-flipping)

| Deliverable | What it does | Flips |
|---|---|---|
| `extract_contract_constraints` + `formalize_contract_entry` (`src/architect/formalize.py`) | LLM IC/IR extraction path for entries with an empty `ic_screening_latex`. Reachable only from the `architect.formalize` CLI, never from `verify()`. | 0 / 10 — `gpt-oss-20b` returns `confident:false` for every empty-IC PDF (these papers argue IC in prose, not as an explicit two-sided screening inequality). |
| `_strip_contract_prose` | Strips a leading `IC:`/`IR:` label, `\text{…}` lead-ins, trailing `\quad\forall…` quantifiers, and a second contract after `\qquad`. Contract-path only. | 0 (correct normalisation, no verdict change) |
| Bayesian `E[.]` bail-out (`_BAYESIAN_RE`) | `E_{…}[…]` / `\mathbb{E}` in a Contract IC/IR returns `None` so `verify()` falls through to the Track 4 Bayesian path instead of grid-checking a strictly stronger pointwise obligation. | 0 |
| Wen2025 revert (`95fd3cc`) | `_strip_call_args_on_powers` was unsound — it read `\theta_i^2 R_i^2` period indices as real squaring, discharging a different obligation. Helper fully removed from `src/` + tests; fail-closed pin restored. | −1 (reverted an unsound flip; `Wen2025diffusion_contract` back to `VERIFIED_TEMPLATE`, then MANUAL'd in Task 12) |

### MANUAL (25) — ceiling rows

| Entry | Track | Ceiling |
|---|---|---|
| `2102_03401` | 1 | Undefined opaque function `u_3(.)` in the utility — Z3 encoding rejects (`unsupported SymPy node u_{3}`); no grid obligation buildable |
| `2308_12502` | 1 | Population-coupled cost term (`kappa_j` sums over other agents' contracts) — single-agent substitution cannot represent it; `r_j^L` also carries a symbolic exponent |
| `2407_02845` | 1 | `log(theta_m R_m)` argument sign not established — Z3 rejects the transcendental |
| `2408_13223` | 1 | No adverse-selection screening IC — Nash action-choice equilibrium over {abstain, join, buy}, rewards assigned per platform-known type |
| `2505_02462` | 1 | No screening IC — graph-based reciprocal model-sharing, single self-reported-cost truthfulness, no discrete type set |
| `2505_05842` | 1 | No screening IC — dynamic Bayesian persuasion (signal over posterior + single uniform reward) |
| `2602_21844` | 4 | Expectation-form (Bayesian) IC integral — SymPy Track 4 cannot evaluate the multi-agent posterior expectation to a posynomial-checkable closed form |
| `2605_02935` | 1 | No screening IC — blockchain smart contracts, per-role strategy-proofness against a fixed deviation set; no type space |
| `Bornstein2023realistic_incentive` | 1 | No screening IC — moral hazard over a continuously self-chosen contribution `m_i`; paper explicitly distinguishes itself from contract theory |
| `Ding2020contract_multidim` | 1 | Utility `r_i - theta_i s_i` has no dependence on the contract variable `phi_i`; `phi_i → phi_j` yields an identical RHS — degenerate IC (data-quality gap) |
| `Han2025paid_models` | 1 | Undefined opaque valuation function `v(.)` inside `E[v(r_i)]` — Z3 rejects (`unsupported SymPy node v`) |
| `Huang2024aigc` | 1 | No screening IC — single uniform unit-data price with post-hoc behavioural type regions |
| `International_…Wan_…` | 1 | IC is an equilibrium-utility ordering (both sides at own type), not `U_i(contract_j)`; soundness gate correctly rejects |
| `Kang2019contract_mobile` | 3 | 9 free variables in IC / 11 in IR — interval box search intractable at δ=0.001 over [0.001, 1.0] |
| `Kang2019reliable_contract` | 1 | Shannon-capacity term `log(1 + rho h / N_0)` in the denominator — Z3 rejects (`log argument sign not established`) |
| `Kang2022blockchain_metaverse` | 1 | `R_{n-1}` parses as a single symbol, not an iterable index; needs adjacent-IC semantics in `_contract_check_core` — out of scope |
| `Karimireddy2022data_sharing` | 1 | No screening IC — moral hazard / continuous-action Nash with verifiable costs |
| `Li2026network` | 1 | No screening IC — per-type closed-form payment + 3-action (abstain/join/buy) equilibrium |
| `Nguyen2025right_reward` | 1 | Undefined opaque staleness function `h(t_k)` — Z3 rejects (`unsupported SymPy node h`) |
| `Tian2021contract` | 1 | Type-ordering unidentified — verifier cannot fix the single-crossing direction; IC counterexamples suppressed, neither IC nor IR decidable |
| `Wang2022motilearn_contract` | 1 | IR indexed by `a`, IC by `n`/`i`; `type_sub` never appears in the IC RHS — cannot equate indices without guessing |
| `Wen2025diffusion_contract` | 1 | Recorded IC/IR is PERIOD-2 static myopic only (`^2`/`^1` are period indices); the paper's true mechanism is a two-period intertemporal contract, not represented in the entry |
| `Yang2023async_contract` | 1 | IR's `E_{com}` communication-energy term is indistinguishable from a Bayesian expectation `E_{…}[.]`; the Bayesian bail-out fires and Track 1 declines |
| `Zhang2020fedserving` | 1 | No screening IC — Bayesian peer-prediction / Bayesian Truth Serum with BNE truthfulness, no discrete client type set |
| `Zhao2023truthful` | 1 | No screening IC — moral hazard (hidden action): one desired action assigned to every client, truthfulness proved as a Nash equilibrium |

Each MANUAL carries a `manual_diagnosis` in `corpus.json` (`round`, `track`,
`limit`, `mechanism`, `obstruction`, `human_task`, `date`) plus a paragraph in
`docs/superpowers/notes/MANUAL-backlog.md`.

### R6 candidates (8) — stay `VERIFIED_TEMPLATE`

Entries where the paper **does** state a screening IC but the LaTeX parser lacks
the tooling to build a sound obligation. Full table in
`docs/superpowers/notes/round-R3a-new-verified.md`.

| Entry | Tooling gap |
|---|---|
| `Lim2020contract` | Bundle-argument map (`\omega_{y,z}` actuals vs component formals) — must be read off the PDF |
| `Wu2021contract_DP` | Same bundle-arg map + a multidimensional-type (3-D) screening encoding |
| `Ma2023joint_pricing` | Reconcile `W_U^i` vs `U_i` naming + fix the RHS contract index (transcription repairs) |
| `Saputra2020fl_contract` | Algebraic form of the opaque function `G` |
| `Saputra2021iov_contract` | Algebraic form of the opaque function `C` |
| `Saputra2021straggling` | Algebraic form of the opaque function `S` |
| `2403_09153` | Prime-as-contract-index support in the subscript extractor + a conditional-bar rule |
| `2502_20882` | A predicate-form IC normaliser (weakest of the eight — re-route to MANUAL in R6 if the PDF cannot confirm report-space = type-space and a direct mechanism) |

### Baseline-edit rationale

For each `VERIFIED_TEMPLATE → MANUAL` entry, the `round-R3a-baseline.md` row was
rewritten `VERIFIED_TEMPLATE → UNKNOWN` with an inline
`<!-- R3a: template was a structural skeleton, no solver run on the entry's math
(program spec); sweep produced UNKNOWN; diagnosed MANUAL in Task 12 -->` comment.
Rationale: the monotone gate treats a bare `→ UNKNOWN` as a regression, so the
row must record the diagnosis alongside the downgrade. The 2 pre-existing
`UNKNOWN` entries (`Kang2019contract_mobile`, `Tian2021contract`) were not
rewritten. R6 candidates keep their `VERIFIED_TEMPLATE` baseline row unchanged.

### Deferred to R4 / R6

- 5-6 of the Group-D MANUALs (`2102_03401`, `2308_12502`, `2407_02845`,
  `Han2025paid_models`, `Kang2019reliable_contract`, `Nguyen2025right_reward`)
  are likely cheap R4 wins — each is discharged by supplying one undefined
  function's algebraic form or one positivity domain. The `human_task` field on
  each `manual_diagnosis` records the specific fix.
- Group C's "no screening IC" calls (10 entries) rest on Task 11-pre's PDF
  reading + corpus notes + a 0/10 LLM decline, not a fresh PDF re-read.
- The LLM IC-extraction path is in place for a stronger model or a
  keyword-targeted PDF window to flip the empty-IC entries later without further
  code change.

---

## Stackelberg (R3b)

_Pending — Part D, Tasks 14-16._

---

## Combined counts + R4 handoff

_Finalised by Task 16._
