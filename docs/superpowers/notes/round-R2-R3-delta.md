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

**Landed 2026-09-03.** Branch `round-R3-stackelberg-sweep`, 4 commits off `main` @ `24d18fb`
(`4a44a68` baseline, `c2b36cb` Task 14-pre, `8ebe16c` sweep, `27fcbe6` adjudication).

### Stackelberg slice (30 entries) — before / after

| Verdict | Baseline (`main`) | After R3b | Δ |
|---|---|---|---|
| VERIFIED (entry-specific) | 1 | **1** | — |
| VERIFIED_TEMPLATE | 28 | **14** | −14 |
| MANUAL (diagnosed) | 0 | **15** | +15 |
| UNKNOWN | 0 | **0** | — |
| UNSUPPORTED | 1 | **0** | −1 |
| COUNTEREXAMPLE | 0 | 0 | — |

**Stackelberg UNKNOWN = 0.** Monotone gate `PASS` — 15 `improved`
(`VERIFIED_TEMPLATE → MANUAL` ×14, `UNSUPPORTED → MANUAL` ×1), 0 regressions. The
14 entries left `VERIFIED_TEMPLATE` are R6 formalization-miss candidates (each has
a clean scalar closed-form follower best-response the sweep's AST path failed to
build). Non-Stackelberg slices (VCG / Contract / Shapley / Valuation / RL / Naive)
byte-identical. Full suite 420 passed / 1 skipped / 3 xfailed / 0 failed.

### Diagnose-only round — no new VERIFIED

The R1 LLM formalizer produces **0 valid ASTs for Stackelberg** (the same wall R2
and R3a hit). The `--only Stackelberg` sweep returned 14 UNKNOWN + 15
VERIFIED_TEMPLATE + 1 UNSUPPORTED from the AST path and `corpus.json` was
byte-identical afterward. `Sarikaya2019stackelberg_workers` (the 1 entry-specific
VERIFIED) held via `verify()`'s own path, untouched.

### Task 14-pre — fail-closed guard (the only `src/` change on the branch)

The first sweep crashed the whole batch: `_extract_follower_symbol` in the
Stackelberg AST-verify path did `_STACK_INLINE_MATH_RE.findall(follower_decision)`
where `follower_decision` was a **dict** — for ≥1 entry the LLM emitted
`m.meta["follower_decision"]` as a dict, not a LaTeX string, and
`verify_from_ast` merges `m.meta` into `meta`. Fix: a shared `_as_str` helper in
`src/tracks/track1_z3.py` coerces a non-`str` value to `""` at all 6 meta-field
readers reachable from the Stackelberg branch (`_extract_follower_symbol` reading
`follower_decision` / `follower_foc_latex` / `best_response_latex` /
`leader_objective_latex`; `_follower_decision_latex`; `_stackelberg_check_core`
reading `best_response_latex`). A malformed entry now degrades to
"follower symbol unresolved" → generic template → UNKNOWN, exactly the plan's
expected path for an un-formalizable Stackelberg entry. No behaviour change for a
normal LaTeX-string `follower_decision`. Commit `c2b36cb`, 4 RED→GREEN tests.

### MANUAL (15) — ceiling rows

| Entry | Track | Ceiling |
|---|---|---|
| `2101_05628` | 1 | Vector follower decision (offloading vector `alpha_i` across N OSPs) — single-variable FOC reduction does not apply |
| `2101_12428` | 1 | Vector follower decision — FOC is a budget-eliminated *difference* of per-chain derivatives; the M−1 conditions are coupled through the eliminated component and do not decouple |
| `2103_05866` | 1 | >2-stage / multi-layer game (protocol designer → users → miners) — the 2-player leader-follower FOC model does not apply |
| `2412_05636` | 1 | Follower best-response is a backward recursion over the horizon (`∏_{r=t+1}^{j-1} α_i^r`, terminal `α_i^T = 0`) — Track 1 single-shot FOC cannot encode it |
| `2502_10765` | 1 | Vector follower decision (rendering resources `x_i^r` AND bandwidth `x_i^w` jointly) — single-variable FOC reduction does not apply |
| `Chu2023hierarchical` | 1 | Follower FOC is transcendental with no closed-form root (the paper states this explicitly, p.21) — Track 1 cannot solve the stationarity equation |
| `Guo2023stackelberg_industrial` | 1 | Vector follower decision (`(D'_n, S_n)` jointly; explicit multi-objective bi-level; FOC/BR/IR all null) — single-variable FOC reduction does not apply |
| `Khan2019edge` | 1 | No proved equilibrium — position-paper (7-page IEEE magazine article), the Stackelberg game is described only qualitatively, no derived best-response or FOC; Track 1 Stackelberg needs a proved equilibrium |
| `Li2025split` | 1 | Vector follower decision (device participation vector `{q_{i,j}}` across all SFL tenants; KKT system) — single-variable FOC reduction does not apply |
| `Liu2026fedbud` | 1 | Vector follower decision (data volume `B_k^t` AND noise budget `ε_k^t` jointly; FOC null) — single-variable FOC reduction does not apply |
| `Luo2023unbiased` | 1 | Follower best-response is an implicit argmax over a box and the recorded FOC is an implicit cubic in `q_n*` with no transcribed root |
| `Pandey2019crowd` | 1 | Follower FOC is transcendental (`1/θ − log(1/θ) = const`, Lambert-W) with no closed-form root; the best response is a min-clipped implicit value |
| `Pang2025quality` | 1 | Payment and cost are unspecified generic functions `f, d` — no algebraic form to differentiate (only a log instantiation in the experiments section has a closed form; venue is viXra) |
| `Wang2022blockchain` | 1 | Vector follower decision (CPU cycles `q_{ti}` AND `q_{mi}` jointly); the stored best-response is additionally not an interior FOC solution (utility strictly decreasing in both → corner) and is inconsistent with the recorded utility — a latent corpus data error |
| `Yu2022multi_leader_fl` | 1 | Vector follower decision (task-accuracy vector `{ε_j^i}` for i=1..K simultaneously; piecewise constraint-active best response with a Lagrange multiplier) — single-variable FOC reduction does not apply |

Each MANUAL carries a `manual_diagnosis` in `corpus.json` plus a paragraph in
`docs/superpowers/notes/MANUAL-backlog.md`.

### R6 candidates (14) — stay `VERIFIED_TEMPLATE`

Every one has a non-null, single-variable, closed-form `best_response_latex` or
`follower_foc_latex` the corpus already holds; the only thing missing is a
Stackelberg-specific formalize path (analogous to the R2 VCG allocation-classifier)
to parse it into the typed AST and discharge `d(follower_utility)/d(follower_decision)=0`
plus the SOC. Full table in `docs/superpowers/notes/round-R3b-new-verified.md`.

`1811_12082`, `2110_12876`, `2203_00270`, `2404_08261`, `2508_07676`,
`Cao2025service`, `Chen2023multifactor_iot`, `FLamma2025stackelberg`,
`Hu2020trading`, `Hu2022truthful_FEL`, `Javaherian2025stackelberg_ic`,
`Lee2024sfl_stackelberg`, `Li2025iiot_drl`, `Xiao2020stackelberg_twostage`.

Weakest two (pre-flagged for R6): `2203_00270` (vague `energy consumption`
decision, two-branch piecewise BR, `lim` time-average leader utility — may bounce
to MANUAL when R6 builds the AST) and `Hu2020trading` (BR has a `−∞` degenerate
branch needing a guard).

### Baseline-edit rationale

Same as R3a: each `VERIFIED_TEMPLATE → MANUAL` entry's `round-R3b-baseline.md` row
was rewritten to `UNKNOWN` with an inline
`<!-- R3b: template/shape was not a proof (program spec); sweep produced UNKNOWN;
diagnosed MANUAL in Task 15 -->` comment (the gate treats a bare `→ UNKNOWN` as a
regression). `Khan2019edge` (already `UNSUPPORTED`) was not rewritten. R6
candidates keep their `VERIFIED_TEMPLATE` baseline row.

---

## Combined counts + R4 handoff

### Verdict counts — in-scope entries (101: VCG 33 + Contract 38 + Stackelberg 30; Shapley 4 excluded, R5)

| Verdict | Pre-R2 (`main` after Phase 3) | After R2 + R3 | Δ |
|---|---|---|---|
| VERIFIED (entry-specific) | 6 | **9** | +3 |
| VERIFIED_TEMPLATE | 59 | **22** | −37 |
| VERIFIED_SHAPE | 33 | **10** | −23 |
| MANUAL | 0 | **60** | +60 |
| UNKNOWN | 2 | **0** | −2 |
| UNSUPPORTED (in-scope) | 1 | **0** | −1 |

**UNKNOWN across VCG + Contract + Stackelberg: 0.** (The 4 Shapley entries remain
`UNSUPPORTED` — R5 builds the coalition track.) The 3 new entry-specific VERIFIED
are all VCG (welfare-difference Clarke pivots, hand-checked vs Groves/Clarke);
R3a and R3b were diagnose-only.

### Per-slice

| Slice | Entries | → VERIFIED (new) | → COUNTEREXAMPLE | → MANUAL | R6 candidates (held at baseline) |
|---|---|---|---|---|---|
| VCG (R2) | 33 | 3 | 0 | 20 | 10 (`VERIFIED_SHAPE`) |
| Contract (R3a) | 38 | 0 | 0 | 25 | 8 (`VERIFIED_TEMPLATE`) |
| Stackelberg (R3b) | 30 | 0 | 0 | 15 | 14 (`VERIFIED_TEMPLATE`) |
| **Total** | **101** | **3** | **0** | **60** | **32** |

(Slice VERIFIED totals including pre-existing entry-specific: VCG 3, Contract 5,
Stackelberg 1 = 9.)

### New VERIFIED (all cross-checked — see `round-R2-new-verified.md`)

- `2504_05563` — VCG — welfare-difference Clarke pivot, Z3 grid model inspected (no type wants another's allocation)
- `3626307_3626311` — VCG — welfare-difference Clarke pivot vs Groves 1973
- `Cong2020vcg` — VCG — welfare-difference Clarke pivot vs Clarke 1971

R3a / R3b produced no new VERIFIED (`round-R3a-new-verified.md`,
`round-R3b-new-verified.md` both record "None; 0 flips").

### MANUAL catalogue (feeds R4) — grouped by ceiling row

Rows hit by **≥2 entries** are R4 widening candidates.

| Ceiling row | Track | Entries | R4 candidate? |
|---|---|---|---|
| Budget-constrained greedy allocation not in {argmax, top-k, weighted-welfare} | 1 | `2404_13841`, `Ahmed2023frimfl`, `GPS2023afl_recruit`, `Jiao2019auto_auction`, `Jin2023bara_budget`, `Lu2021cluster_auction`, `Zheng2023fl_market` (VCG ×7) | **yes** — a budget-knapsack allocation encoding |
| RL-policy / opaque-algorithm allocation, not a closed-form rule | 1 | `Lim2020edge_collab`, `Model2024trading_fl`, `Peng2023auction_medical`, `Tan2023hire` (VCG ×4) | no — genuinely no closed form |
| Non-polynomial gap Z3 cannot linearize (exponential/log payment) | 1 | `Haupt2021auctions`, `Seo2021sdn_fl`, `Seo2022noniid_auction`, `Wei2024truthful_bandit` (VCG ×4) | **yes** — a transcendental-payment track (dReal-style) |
| Continuous bid space with no valid discretization | 1 | `Cui2024auction_market`, `Yang2023buyers_market`, `Zhang2022online` (VCG ×3) | **yes** — a continuous-type auction seam |
| Payment not a Clarke pivot (own-cost subtraction / budget cap) | 1 | `Xia2026privacy_mfg`, `Zhang2024auction_comm` (VCG ×2) | **yes** — a non-Groves payment classifier |
| No adverse-selection screening IC in the paper (moral hazard / persuasion / peer-prediction / Nash action-choice) | 1 | `2408_13223`, `2505_02462`, `2505_05842`, `2605_02935`, `Bornstein2023realistic_incentive`, `Huang2024aigc`, `Karimireddy2022data_sharing`, `Li2026network`, `Zhang2020fedserving`, `Zhao2023truthful` (Contract ×10) | no — the paper has no screening IC; out of the verifier's scope by design |
| Undefined opaque function in the utility (Z3 `unsupported SymPy node`) | 1 | `2102_03401`, `Han2025paid_models`, `Nguyen2025right_reward` (Contract ×3) | **yes** — the R4 "supply one function's algebraic form" fix; `human_task` carries the exact form per entry |
| Transcendental log / Shannon-capacity term, argument sign not established | 1 | `2407_02845`, `Kang2019reliable_contract` (Contract ×2) | **yes** — a positivity-domain declaration + Track 3 route |
| Degenerate / population-coupled / mis-transcribed IC | 1 | `2308_12502`, `Ding2020contract_multidim`, `Wang2022motilearn_contract`, `Wen2025diffusion_contract`, `Yang2023async_contract` (Contract ×5) | partly — `2308_12502` needs population-coupled substitution; the rest are data-quality / transcription |
| Adjacent-IC / single-symbol-index parsing | 1 | `Kang2022blockchain_metaverse` (Contract ×1) | (R4 adjacent-IC reduction, shared with other rounds) |
| Type-ordering unidentified / box-search intractable | 1, 3 | `Tian2021contract`, `Kang2019contract_mobile` (Contract ×2) | **yes** — single-crossing direction inference; box-dim reduction |
| Bayesian expectation-form IC integral | 4 | `2602_21844` (Contract ×1) | (R4 Track 4 multi-dim integral) |
| Vector / multi-variable follower decision — single-variable FOC reduction does not apply | 1 | `2101_05628`, `2101_12428`, `2502_10765`, `Guo2023stackelberg_industrial`, `Li2025split`, `Liu2026fedbud`, `Wang2022blockchain`, `Yu2022multi_leader_fl` (Stackelberg ×8) | **yes** — a multi-variable / KKT stationarity-system checker |
| Transcendental / implicit FOC with no closed-form root | 1 | `Chu2023hierarchical`, `Luo2023unbiased`, `Pandey2019crowd` (Stackelberg ×3) | **yes** — a numeric-root Stackelberg seam |
| Backward-recursion / horizon best-response | 1 | `2412_05636` (Stackelberg ×1) | (R4 dynamic-game encoding) |
| >2-stage / multi-layer game | 1 | `2103_05866` (Stackelberg ×1) | no — out of the 2-player model by design |
| Unspecified generic payment/cost functions | 1 | `Pang2025quality` (Stackelberg ×1) | (data-quality; also corpus-hygiene — viXra, unresolved notation conflict) |
| No proved equilibrium | 1 | `Khan2019edge` (Stackelberg ×1) | no — position paper, no math |

### R6 candidates (formalization misses — entry left at baseline verdict)

- **VCG (10, `VERIFIED_SHAPE`):** `Cheng2022uav`, `Le2021cellular_auction`,
  `Tan2025longterm`, `Xiang2025esr_mhfl`, `Liu2023`, and 5 more — see
  `round-R2-new-verified.md` "R6 candidates". Several are the canonical Groves
  form the classifier fumbled on surface syntax.
- **Contract (8, `VERIFIED_TEMPLATE`):** `Lim2020contract`, `Wu2021contract_DP`,
  `Ma2023joint_pricing`, `Saputra2020fl_contract`, `Saputra2021iov_contract`,
  `Saputra2021straggling`, `2403_09153`, `2502_20882` — bundle-arg maps, undefined
  `G`/`C`/`S`, prime-as-index, predicate-form IC. See `round-R3a-new-verified.md`.
- **Stackelberg (14, `VERIFIED_TEMPLATE`):** listed above; all discharged by one
  Stackelberg-specific formalize path. See `round-R3b-new-verified.md`.

### Baseline edits

Entries whose slice-baseline row was rewritten to the true post-sweep automated
verdict (`UNKNOWN`, or `UNSUPPORTED` for Khan2019edge which was already there)
before the MANUAL diagnosis, because the pre-sweep template/shape verdict was not
a solver result (program spec). VCG: 20 `VERIFIED_SHAPE → MANUAL` rows carried
their diagnosis. Contract (R3a): 23 `VERIFIED_TEMPLATE → UNKNOWN` + 2 pre-existing
`UNKNOWN`. Stackelberg (R3b): 14 `VERIFIED_TEMPLATE → UNKNOWN` + `Khan2019edge`
left `UNSUPPORTED`. R6 candidates keep their baseline rows. Rationale: a diagnosis
is strictly more honest than a structural match that never ran a solver.

### Monotone gate

All three slice gates → `GATE: PASS`. No entry moved to a strictly-worse verdict
relative to its slice baseline (`VERIFIED_TEMPLATE`/`VERIFIED_SHAPE`/`UNSUPPORTED`
→ `MANUAL` is an improvement). Out-of-scope (`Valuation`/`RL`/`Naive`) and Shapley
entries unchanged.

### Handoff to R4

The MANUAL catalogue above is R4's input. R4's plan is authored from the
ceiling-row groupings — implement the obstructions recurring across ≥2 entries.
Highest-value R4 targets by entry count:

1. **Budget-knapsack allocation encoding** (VCG ×7) — the single biggest reclaim.
2. **Vector / KKT follower-decision stationarity system** (Stackelberg ×8) — plus
   it unblocks the 14 R6 Stackelberg candidates once a Stackelberg formalize path
   exists.
3. **Transcendental-payment / continuous-type auction seams** (VCG ×3 + ×4).
4. **"Supply one function's algebraic form"** (Contract ×3 + Stackelberg ×1) —
   cheapest per entry; each `human_task` already records the exact form.
5. **Transcendental / implicit-FOC numeric-root seam** (Stackelberg ×3 + Contract
   ×2 log-term).

R6 (formalization second pass) input: 32 R6 candidates across the three slices,
each with a named tooling gap. R6's biggest single lever is the
Stackelberg-specific formalize path (unblocks 14).

Deferred minors for R4 cleanup (from the round ledgers): `_BAYESIAN_RE` name
collision (`verifier.py:59` vs `track1_z3.py:343`); `Yang2023async_contract`'s
`E_{com}` spurious Bayesian bail-out; `scripts.snapshot_verdicts` writes
`round-R2-baseline.md` ignoring `--only` (needs an `--out` requirement); `z3_verdict`
corpus field is stale/disused; unused `pytest` imports in ~4 test files.
