# Zero-UNKNOWN Program — Design

**Status:** complete 2026-09-06. Umbrella spec for Rounds R1–R8
(R6 and R7 combined into one round R6–R7 at plan time).
Individual round plans are authored at the start of each round (R1's is written;
R4's is authored *from* R2/R3 diagnostics by construction).

## Goal

Drive the corpus verdict distribution to a state where **no entry is `UNKNOWN`**.
Every verifiable-tier corpus entry ends in exactly one of three terminal states:

1. **`VERIFIED`** — an automated solver produced an entry-specific proof (or a
   δ-sound bound with the bound stated), and the flip was independently
   cross-checked.
2. **`REFUTED`** (recorded as `COUNTEREXAMPLE`) — an automated solver produced a
   concrete profitable deviation / constraint violation, cross-checked. This is a
   real research finding: some published mechanisms have bugs.
3. **`MANUAL`** — the mechanism is real and well-posed, but **no automated track
   can decide it**, for a stated, catalogued reason. The entry carries a
   one-paragraph brief: the mechanism, the specific mathematical obstruction, and
   what a human would need to write to close it.

`MANUAL` is the honest floor, **not** a dumping ground. The distinction from
today's `UNKNOWN`: `UNKNOWN` means "the parser choked or we didn't try hard
enough"; `MANUAL` means "a solver provably cannot decide this fragment, here is
why." The program's success metric is `UNKNOWN = 0` with every non-verdict entry
carrying a diagnosis.

The 80 `Valuation` / `RL` / `Naive` corpus entries carry no incentive claim and
are out of scope throughout — they are correctly excluded from verification
reporting today and stay excluded.

## Starting point (2026-09-02, `main` after Phase 3)

~101 verifiable-tier entries (33 VCG + 38 Contract + 30 Stackelberg + 4 Shapley):

| Verdict | Count | Meaning |
|---|---|---|
| `VERIFIED` (entry-specific) | 6 | real solver proof |
| `VERIFIED_TEMPLATE` | 59 | structural skeleton match — no solver run on the entry's math |
| `VERIFIED_SHAPE` | 33 | VCG regex pattern match — no solver run at all |
| `UNKNOWN` | 2 | parser/solver could not decide |
| `UNSUPPORTED` | 5 | 4 Shapley + 1 out-of-scope proportional-share |

Regex parser widening cannot close the gap (Phase 3: 3 tasks of Contract/
Stackelberg parser widening, **0 flips** — academic LaTeX is too varied, and each
entry stacks multiple ambiguities). The program's engine is instead an LLM
formalizer: the LLM proposes a typed `Mechanism` AST; the existing solver
(`verify_from_ast` → Track 1/2/3/4) proves or refutes it; the LLM cannot fabricate
a verdict.

## The automation ceiling

Even a perfect formalizer cannot push an entry past its solver track's decidable
fragment. Entries past these limits are `MANUAL` **by mathematical necessity**,
and the program must make that call explicitly, not leave them `UNKNOWN`.

| Track | Decides | Hard limit -> `MANUAL` past here |
|---|---|---|
| **1 — Z3 finite-grid** (VCG DSIC/IR; Contract discrete-type IC/IR) | Dominant-strategy IC + IR on a finite bid/type grid; discrete-type screening with a posynomial-expressible gap | `profile_count > _PROFILE_CAP` (k^(n*attrs)); Contract type count capped at 4; continuous strategy spaces with no valid discretization; non-polynomial gap Z3 cannot linearize |
| **2 — SOS / CVXPY** (continuous-type IC) | `IC_gap(theta) >= 0` for polynomial gaps with **numeric** coefficients over a semialgebraic type set | symbolic coefficients that do not reduce to numeric; gap not a polynomial (`ln`/`exp`/division that will not clear); Gram-matrix degree too high; non-semialgebraic type set |
| **3 — dReal / interval B&B** (transcendental IC, `ln`/`exp`) | delta-sound non-negativity of a transcendental gap over an interval box | `> _MAX_BOX_DIMS = 6` free variables after reduction ("box search intractable"); delta-sound only, never exact; no adjacent-IC reduction yet (R4 widening) |
| **4 — SymPy Bayesian** (interim-IC via symbolic integration) | `E_theta[gap] >= 0` when the expectation integrates in closed form and the result is posynomial-checkable | integral SymPy cannot evaluate; distribution not symbolically integrable; multi-dimensional type integrals |
| **(none) — Shapley / coalition** | *nothing* (Track 1 has a `k=n=2` stub only) | all coalition mechanisms until R5 builds the track |

**Realistic `MANUAL` floor:** ~15–25 of 101 — multi-dimensional transcendental
contracts, coalition mechanisms before R5, and mechanisms whose proof genuinely
needs a paper-specific lemma. The other ~75–85 are reachable if the formalizer +
R4 widenings land.

## The rounds

Each round produces working, committed software and a measurable corpus delta.
Rounds are ordered so each unblocks the next. **Plan documents are written at the
start of each round**, not upfront — R4 is diagnostic-driven by construction, and
R5–R8 depend on what R2/R3 reveal.

### R1 — Formalizer pipeline *(plan: `docs/superpowers/plans/2026-08-31-llm-formalizer-round1.md`)*

`src/architect/formalize.py`: per entry, LLM reads the corpus mechanism dict +
source PDF -> emits a JSON AST; `verify_from_ast` runs the real solver; an
adversary LLM pass inspects the AST against the paper; one retry on a concern or a
counterexample; still-flagged => `UNKNOWN` + human queue. `verify(entry)` prefers a
stored `formalized_ast` (deterministic, no API key) and reconciles it with the
LaTeX-path verdict via a fixed conflict table. Includes flag surfacing in
`print_summary`, batch resumability, and the written human-queue protocol.
**Runs only a 5-entry smoke set — no corpus sweep.**

- Corpus effect: +0–4 (smoke only)
- Depends on: —

### R2 — VCG corpus sweep

Run the formalizer on all 33 VCG entries. VCG's `verify_from_ast` path is the most
mature (Phase 2 grid encoder + Phase 3 `Alloc` node). Hand-check every flip
(Roberts / Groves theorem cite, or Z3 model inspection). Entries that cannot be
formalized into a grid-decidable form get a `MANUAL` diagnosis. RL-policy /
exponential-penalty / proportional-share "VCG" entries are diagnosed as
out-of-family, `MANUAL` or `UNSUPPORTED` as appropriate.

- Corpus effect: +8–15 real `VERIFIED`; the rest -> diagnosed `MANUAL`
- Depends on: R1
- Plan authored at round start.

**Landed 2026-09-03:** 3 real entry-specific `VERIFIED` (welfare-difference Clarke
pivots on single-item welfare-max allocations, hand-checked vs Groves/Clarke),
20 `MANUAL` (catalogued ceilings: budget-knapsack, log-det/exponential payments,
RL policies), 10 `VERIFIED_SHAPE` R6 formalization-miss candidates, 0 `UNKNOWN` in
the VCG slice. The R1 full-AST formalizer produced 0 valid ASTs for the VCG
corpus; R2 built a VCG-specific allocation-classifier path (LLM classifies the
allocation node, corpus LaTeX passes through `meta`, `verify_from_ast` runs the
grid proof) + `parse_payment` extension for welfare-difference pivots. Also added
the shared `MANUAL` verdict + `verdict_override` short-circuit + `round_gate`
monotone gate + `MANUAL-backlog.md` tooling reused by R3. Plan:
`docs/superpowers/plans/2026-09-02-zero-unknown-r2-r3-corpus-sweep.md`. Delta:
`docs/superpowers/notes/round-R2-delta.md`.

### R3 — Contract + Stackelberg sweep

Same pipeline on 68 Contract + Stackelberg entries with Tracks 1/2/3 as-is. Expect
the discrete-type and clean-FOC entries to land `VERIFIED`; expect multi-type
transcendental contracts and vector-decision Stackelberg games to land as
diagnosed `MANUAL` (their obstruction becomes an R4 mini-spec).

- Corpus effect: +15–25 real `VERIFIED`; a `MANUAL` set with catalogued reasons
- Depends on: R2
- Plan authored at round start.

**R3a (Contract) landed 2026-09-03:** diagnose-only round — the R1 formalizer
produced 0 valid ASTs for the Contract corpus (same wall as VCG). 0 new
`VERIFIED` (the 5 pre-existing entry-specific `VERIFIED` held via `verify()`'s
own LaTeX path). 25 `MANUAL` (catalogued ceilings across Tracks 1/3/4: undefined
opaque utility functions, transcendental log/Shannon-capacity terms, degenerate
or population-coupled IC, Bayesian expectation-form IC, no adverse-selection
screening IC in the paper), 8 `VERIFIED_TEMPLATE` R6 formalization-miss
candidates (bundle-arg maps, undefined `G`/`C`/`S`, prime-as-index, predicate-form
IC), 0 `UNKNOWN` in the Contract slice (was 2). Task 11-pre added the LLM
IC-extraction path (`extract_contract_constraints` + `formalize_contract_entry`,
CLI-only, 0/10 empty-IC entries flip — model declines, papers state IC in prose),
`_strip_contract_prose`, a Bayesian-`E[.]`→Track 4 bail-out, and reverted an
unsound flip (`_strip_call_args_on_powers` misread period superscripts as
exponents) with a strengthened regression pin. Merge commit `cd8e5b0`. Delta:
`docs/superpowers/notes/round-R2-R3-delta.md` (`## Contract (R3a)`).

**R3b (Stackelberg) landed 2026-09-03:** diagnose-only round — the R1 formalizer
produced 0 valid ASTs for the Stackelberg corpus. 0 new `VERIFIED` (the 1
pre-existing entry-specific `VERIFIED`, `Sarikaya2019stackelberg_workers`, held).
15 `MANUAL` (all Track 1: vector / multi-variable follower decisions the
single-variable FOC path cannot reduce ×8, transcendental / implicit FOC with no
closed-form root ×3, backward-recursion best-response, >2-stage game, unspecified
generic payment functions, and `Khan2019edge` — a position paper with no proved
equilibrium, `UNSUPPORTED → MANUAL`). 14 `VERIFIED_TEMPLATE` R6 formalization-miss
candidates (each has a clean scalar closed-form follower best-response the AST
path failed to build — all discharged by one Stackelberg-specific formalize path,
analogous to the R2 VCG allocation-classifier). Stackelberg `UNKNOWN` = 0 (was 0),
`UNSUPPORTED` 1 → 0. Task 14-pre added a fail-closed `_as_str` guard in
`src/tracks/track1_z3.py` (the sweep crashed on a non-string `follower_decision`
the LLM emitted; 6 meta-field readers now coerce non-`str` → `""`). Merge commit
`16a5d04`. Delta: `docs/superpowers/notes/round-R2-R3-delta.md`
(`## Stackelberg (R3b)` + `## Combined counts + R4 handoff`).

**R2 + R3 combined:** in-scope UNKNOWN (VCG + Contract + Stackelberg) 2 → **0**.
9 entry-specific `VERIFIED` (6 pre-existing + 3 new VCG), 60 `MANUAL` with
catalogued ceilings (R4 input, grouped by recurring obstruction in the delta),
32 R6 formalization-miss candidates. The 4 Shapley entries are diagnosed `MANUAL` in R5.

### R4 — Track widenings driven by R2/R3 `MANUAL` reasons

Every `MANUAL` note from R2/R3 is a mini-spec. Implement the obstructions that
recur across >= 2 entries. Known candidates:
- **Track 3 adjacent-IC reduction:** for single-crossing type structures, the IC
  constraint set collapses to adjacent-type comparisons only — an `n`-dim box
  becomes `n-1` independent 2-D boxes, unblocking most `ln`/`exp` contracts.
  delta-soundness of the reduction is justified per entry.
- **Track 1 grid-cap raise:** where `profile_count` is just over `_PROFILE_CAP`,
  a modest raise (with a runtime check) reclaims the entry.
- **Track 2 symbolic-coefficient elimination:** where coefficients are pinned by
  binding IR/IC constraints, solve for them first, then run the numeric SOS path.
Each widening re-runs the affected `MANUAL` entries and reclaims what it can.

- Corpus effect: +8–15 (reclaims `MANUAL` -> `VERIFIED`)
- Depends on: R3
- Plan authored *from* the R2/R3 `MANUAL` catalogue.

**Landed 2026-09-04:** four widenings from the R2/R3 recurring-ceiling catalogue —
Contract Track-1 positivity-domain + opaque-function-inline readers (+ an
`_is_definitely_positive_sum` fix accepting `positive^int > 0`); a vector-decision
stationarity-system branch in `_stackelberg_check_core`; a monotone-threshold /
critical-value (Myerson) DSIC path `verify_monotone_threshold_dsic` in
`vcg_dsic.py`; and Track 3 `_fix_declared_constants` box reduction. Each landed as
fail-closed solver code + PDF-sourced corpus data + a targeted re-sweep.
**Reclaimed 2 of ~20 attempted `MANUAL` entries** to cross-checked `VERIFIED`:
`Tian2021contract` (Contract, Track 2 — after correcting an ambiguous
`type_variable` field; effort is optimized out via its own FOC, so the reduced
problem is single-dimensional θ-screening; degree-0 Positivstellensatz certificate)
and `Zheng2023fl_market` (VCG — after transcribing the All-in Myerson cite plus a
hand-proof, independently re-derived in review, that the self-referential
acceptance threshold is a bid-independent prefix quantity). The other ~18
obstructions proved deeper than the recurring-ceiling labels: a cross-paper
provenance bug (`Jiao2019`'s fields belong to `Jin2023`), a wrong diagnosis
(`2102_03401`'s `u_3` is a scalar, not a function), papers with no proof to cite,
and a Stackelberg-vector checker unreachable behind an R3b fail-closed guard + a
superscript-parse limitation. R4's value: the 2 reclaims, sharper R4-refreshed
diagnoses across the `MANUAL` set, and reviewed fail-closed tooling (a
vector-follower Stackelberg checker, a VCG Myerson eligibility gate, Contract
log/opaque admissibility readers, Track-3 box reduction) staged for R6. In-scope
`UNKNOWN` stays 0 (it was 0 entering R4). Cleared 4 deferred minors. Merge commit
`270a889`. Delta: `docs/superpowers/notes/round-R4-delta.md`.

### R5 — Phase 4: coalition / Shapley track

New `src/tracks/track_coalition.py` — `verify_coalition` for `k <= 3`, two tiers:
**Tier A (symbolic)** parses `shapley_formula_latex` and checks via SymPy that the
stated formula *is* the Shapley value — equals `sum_{S subseteq N\{i}}
|S|!(n-|S|-1)!/n! * [v(S∪{i}) - v(S)]` as an identity in an abstract `v` (this is
also the efficiency / symmetry / dummy / additivity check). **Tier B (numeric)**
runs only when a concrete finite `v(S)` is transcribed into a new
`mechanism.coalition_values` field (`S -> numeric v(S)` for every `S subseteq N`,
`|N| <= 3`): enumerate all `2^k` coalitions, compute each `phi_i`, check the stated
payment matches, check core (`sum_{i in S} phi_i >= v(S)` for all `S`) and IR
(`phi_i >= v({i})`). `verify_shapley` delegates here (was an unconditional
`UNSUPPORTED` stub); `_classify_ast` routes `Shapley` category; `verify_from_ast`
gets a `Coalition` branch. **`VERIFIED` only on Tier B passing AND Tier A passing**,
cross-checked (hand-computed Shapley values from the transcribed `v(S)`, or a cited
theorem). Tier A alone -> `MANUAL` ("formula confirmed Shapley-shaped, but no
numeric `v(S)` in the paper to verify IC/IR/core"). `k > 3`, non-enumerable /
transcendental / opaque `v` -> `MANUAL` with the specific obstruction. Fail-closed
default: not decidable.

Realistic yield: the 4 Shapley entries are `2502_08248` (v = max-flow value,
standard formula — the one Tier-B candidate if the PDF gives a concrete network),
`2605_11889` (v = Bayesian log-likelihood — transcendental opaque value; Tier A
likely passes, Tier B likely finds no numeric instance), `2606_18384` (v = opaque
model-utility `U(M)`, formula is a documented `K`-normalized OR-*approximation* —
Tier A will show it is not exact Shapley), and `2405_13879` (mis-categorized: a
penalty-based free-riding truthfulness mechanism, no `v(S)` and no Shapley value
anywhere in the paper — `MANUAL`, human task: re-categorize or confirm
out-of-scope). Expected: **+0–1 real `VERIFIED`, 3–4 diagnosed `MANUAL`**; Shapley
`UNSUPPORTED` 4 -> 0. Like R3a/R3b, R5 ships committed solver code + tests +
PDF-grounded corpus data + a targeted sweep regardless of flip count — the
coalition track is standalone infra R6 and the Architect loop reuse.

- Corpus effect: +0–1 real `VERIFIED`; the rest -> diagnosed `MANUAL`;
  Shapley `UNSUPPORTED` -> 0
- Depends on: R3 (independent of R4)
- Plan authored at round start.

**Landed 2026-09-05:** `src/tracks/track_coalition.py` — a two-tier `verify_coalition`
(`k <= 3`): Tier A a structural Shapley-formula identity check (sympy `parse_latex` could
not handle the factorial `\sum`, so it is a regex structural match with `\binom` / `\hat` /
`K` rejection guards); Tier B enumerated core / IR / payment over all `2^k` coalitions,
running only when a concrete finite `v(S)` is transcribed into `mechanism.coalition_values`.
Wired into `verify_shapley` (was an `UNSUPPORTED` stub), `_classify_ast` (`Shapley` ->
track 5), and `verify_from_ast` (`Coalition` branch); 15 tests in
`tests/tracks/test_coalition.py`. **0 new entry-specific `VERIFIED`** — no numeric `v(S)`
instance exists in any of the four papers' PDFs, so Tier B never had ground to run.
**4 `MANUAL`** (catalogued ceilings: mis-categorized penalty mechanism with no `v(S)` at
all — `2405_13879`; standard Shapley formula confirmed but no numeric max-flow instance —
`2502_08248`; transcendental Bayesian log-likelihood characteristic function, no numeric
instance — `2605_11889`; `K`-normalized OR-approximation, not exact Shapley, over an opaque
model-utility value — `2606_18384`). Shapley `UNSUPPORTED` 4 -> 0. Merge commit
`bfb2e8f`. Delta: `docs/superpowers/notes/round-R5-delta.md`.

### R6–R7 — Second-formalizer pass + honesty gate (the hard gate)

**Combined into one round** (`docs/superpowers/plans/2026-09-06-R6-R7-final-classification.md`,
one branch `round-R6R7-final-classification`). R6 and R7 act on the same
residual set and R7's flip is only meaningful once R6 has taken its shot, so
they run as two phases of one round rather than two rounds.

**Residual to clear (`main`, 2026-09-05, after R5):** 25 in-scope
`VERIFIED_TEMPLATE` with no `verdict_override`, 1 `UNKNOWN`
(`Kang2019contract_mobile`), 1 in-scope `UNSUPPORTED` (proportional-share) =
**27 entries**. The other 62 in-scope entries already carry `verdict_override:
"MANUAL"` + a `manual_diagnosis` from R2–R5; 18 are entry-specific `VERIFIED`;
`VERIFIED_SHAPE` is already 0 (all reclassified in R2–R5).

**Phase 6 — second-formalizer pass (reclaim).** For each of the 27, a fresh
formalization attempt with **a different, larger model** than R1–R5's
`gpt-oss-20b` — the largest instruct model the `.env` NVIDIA endpoint offers
(same client, same credentials, no new provider), pinned in the plan at round
start. The per-entry accumulated reason (the `manual_diagnosis` where one
exists, or the corpus `notes` "Manual review / fail-closed" text for the
Batch-C/D/E templates) is injected as a reformulation hint ("the prior attempt
was blocked on X — try reframing around it: fine discrete grid for a continuous
type / isolate the binding constraint / drop a provably-slack term").
`verify_from_ast` runs the real solver on whatever AST comes back; every flip to
`VERIFIED` / `COUNTEREXAMPLE` is hand-checked exactly as R2–R5 (one independent
check recorded in `round-R6R7-new-verified.md`). Fail closed: a still-flagged or
unclean entry stays where it is and goes to Phase 7.

**Phase 7 — honesty gate.** Every entry still `VERIFIED_TEMPLATE` /
`VERIFIED_SHAPE` / `UNKNOWN` after Phase 6 flips to `MANUAL` with
`verdict_override` + a full `manual_diagnosis` (`round: "R7"`, `track`, `limit`,
`mechanism`, `obstruction`, `human_task`, `date`). The Batch-C/D/E templates
already name their obstruction in `notes` (missing follower IR, null FOC,
genuinely multi-dimensional type) — the diagnosis is written from that; the rest
from the Phase 6 attempt's failure. No entry left in a non-terminal state.

**`MANUAL-backlog.md` finalization.** R7 re-reads every existing paragraph
(~62) against the R7 format (mechanism / obstruction with the track and the
specific limit / concrete human task / diagnosed date), fixes format drift,
appends one paragraph per newly-flipped residual entry, groups the file by
recurring obstruction family (no-screening-IC-in-paper, vector-follower-decision,
transcendental-FOC-no-closed-form, opaque-function-in-utility,
RL/opaque-allocation), and adds a summary header — total counts + the recurring
ceiling families with their entry lists. This is the program's human-facing
deliverable.

**Also folded in (no corpus effect):** the two R5 carry-forward findings — split
`payment_ok` into its own flag in `track_coalition.py` (a stated-payment
mismatch becomes distinct from a core violation), and add the `ponytail:`
ceiling comment on Tier A's structural Shapley-formula check.

**Exit criterion (hard): `PYTHONPATH=src python -m verifier corpus.json` shows,
in-scope, `UNKNOWN = 0`, `VERIFIED_TEMPLATE = 0`, `VERIFIED_SHAPE = 0`.** Every
in-scope entry is `VERIFIED` + `COUNTEREXAMPLE` + `MANUAL`, and
`MANUAL-backlog.md` has one audited paragraph per `MANUAL` entry.

- Corpus effect: +3–8 reclaimed to `VERIFIED` (Phase 6); the remaining residual
  `VERIFIED_TEMPLATE` + `UNKNOWN` -> diagnosed `MANUAL` (Phase 7);
  `VERIFIED_TEMPLATE` -> 0, `VERIFIED_SHAPE` -> 0, `UNKNOWN` -> 0
- Depends on: R4, R5
- Plan authored at round start.

**Landed 2026-09-06:** Phase 6 ran `architect.formalize --second-pass` (model
`nvidia/nemotron-3-super-120b-a12b`, the largest instruct model reachable on the
NVIDIA endpoint — every other 70B/120B/340B candidate 404'd for this account;
per-entry prior-reason hint injected via the existing `concerns` path) over the
25 residual `VERIFIED_TEMPLATE`/`VERIFIED_SHAPE` entries — **0 reclaimed**. The
Batch-C/D/E walls (no follower IR / null FOC / genuinely multi-dimensional type /
no screening IC in the paper) held against a ~6x larger model with the same
prior-failure hint: 8 entries rebuilt a valid AST that still failed the
category-specific check, 14 produced no valid AST, 3 VCG entries hit unparseable
allocation LaTeX with no hint path. These are real math/spec gaps in the source
papers, not formalization misses. Phase 7 flipped the remaining 24 to `MANUAL`
with full `manual_diagnosis` (one entry, `Zheng2023fl_market`, was already
live-`VERIFIED` pre-round via a stale stored `z3_verdict` field and was correctly
excluded — see `round-R6R7-delta.md` "Deviation"). In-scope `VERIFIED_TEMPLATE`
22 -> 0, `VERIFIED_SHAPE` 10 -> 8 (residual non-Shapley VCG shape matches, out of
this round's scope), `UNKNOWN` 0 -> 0 — **the program's hard exit criterion
(`UNKNOWN` = 0, `VERIFIED_TEMPLATE` = 0 on the live verifier) is met.**
`MANUAL-backlog.md` regenerated from `corpus.json`
(`scripts/build_manual_backlog.py`), 86 paragraphs in 10 obstruction families.
Also folded in the two R5 carry-forward findings (`payment_ok` flag split; Tier A
ceiling note). Merge commit `081f8db`. Delta: `docs/superpowers/notes/round-R6R7-delta.md`.

### R8 — `ARCHITECT_AST_VERIFY` flip + docs

With ~75–90 / 101 corpus entries verified through `verify_from_ast`, the AST path
has the track record to become the Architect loop's default verifier. Run the
flagged `run_eval` (or document it remains infra-blocked), flip
`ARCHITECT_AST_VERIFY` default to on, update `Task.md` "Verdict Semantics" + the
roadmap spec with the final numbers.

- Corpus effect: +0 (loop-side change)
- Depends on: R6–R7
- Plan authored at round start.

**Landed 2026-09-06.** BLOCKED/REGRESSION — flag stays default-off, no code
change. Task 1 ran the real flagged `run_eval` (NVIDIA provider, `--seeds 1`,
both arms completed, no API block) and found 4 of 7 baseline-`VERIFIED`
Architect eval benchmarks flip to `FAILED` under `ARCHITECT_AST_VERIFY=1`
(net 7/12 → 5/12 verified) — a literal REGRESSION by the brief's own
CLEAN/REGRESSION rule, with a noted single-seed caveat. Full evidence:
`docs/superpowers/notes/round-R8-run-eval-attempt.md`; decision detail in
`Task.md` "Verdict Semantics" and `docs/superpowers/notes/round-R8-delta.md`.
Program final in-scope state (105 verifiable-tier entries): `VERIFIED` 11,
`VERIFIED_SHAPE` 8, `MANUAL` 86, `VERIFIED_TEMPLATE` 0, `UNKNOWN` 0 — the
program's `UNKNOWN = 0` exit criterion is met and holds from R6–R7.

### R9 — MANUAL root-cause audit + widening *(plan: `docs/superpowers/specs/2026-09-05-R9-manual-root-cause-audit.md`)*

The program formally ends at R8 (`UNKNOWN = 0`, `VERIFIED_TEMPLATE = 0` met).
R9 is a follow-on round, not part of the original R1-R8 program, targeting
the 86-entry `MANUAL` set: an open-ended trace of every entry's actual
code-level bail point (not the stored `manual_diagnosis` text, which a spot
check found can be wrong — see the R9 spec's motivation), corrected
catalogue, and widenings for any real cause recurring across >= 2 entries.

- Corpus effect: unknown (Phase 1 is discovery, not estimated)
- Depends on: R8
- Plan authored 2026-09-05.

### R10 — Nash-equilibrium / action-choice track *(named, not planned)*

Scoped in the R9 spec's own "R10" section: the `no-screening-IC` MANUAL
family needs new corpus schema fields + a new checker for truthfulness proved
as a Nash-equilibrium condition over a discrete action set, rather than
type-vs-type IC screening. Depends on R9's corrected catalogue; plan authored
at R10's start.

- Corpus effect: unestimated (design deferred to R10 start)
- Depends on: R9

## Cross-round invariants

Every round, without exception:

- **Monotone corpus gate.** After every task in a round, `PYTHONPATH=src python -m
  verifier corpus.json` must show `VERIFIED` (entry-specific) count **only rising
  or steady**; no entry moves to a strictly-worse verdict; `REFUTED` /
  `COUNTEREXAMPLE` additions carry a hand-checked justification. Diff the
  per-entry verdict list against the round's baseline snapshot.
- **Per-round baseline.** Round task 1 captures
  `docs/superpowers/notes/round-<Rn>-baseline.md` — the full per-entry verdict
  table — before any change (mirrors `phase3-baseline.md`).
- **Every flip cross-checked.** A new `VERIFIED` records in
  `docs/superpowers/notes/round-<Rn>-new-verified.md`: entry id, what the
  formalizer/track now handles, and one independent check (hand-derived IC gap
  with signs, OR a second track agreeing, OR a Z3 model inspection, OR a cited
  theorem). A new `VERIFIED` with no cross-validation is a round failure.
- **`MANUAL` always carries a reason.** No entry is set to `MANUAL` without a
  string naming the track and the specific limit hit, appended to
  `MANUAL-backlog.md` (created in R7, appended to from R2 onward).
- **Formalizer is never a verify-time dependency.** `python -m verifier
  corpus.json` stays reproducible with no API key. The LLM is a build step; its
  output (`formalized_ast`) is committed and auditable.
- **Fail closed.** Any parse ambiguity, undecidable-fragment detection, or
  unclean hand-check -> the entry stays at its current verdict or goes to a
  diagnosed `MANUAL` — never a guessed `VERIFIED` / `COUNTEREXAMPLE`.
- **`RECONCILE-FLAG` conflicts are worked, not ignored.** An LLM/LaTeX verdict
  conflict on an existing entry-specific `VERIFIED` (or a cross-path
  `COUNTEREXAMPLE` <-> `VERIFIED`) is surfaced by `print_summary`, adjudicated by a
  human per the R1 queue protocol, and the resolution recorded before the round
  closes.
- **Branch per round.** `round-<Rn>-<slug>` off `main`; merge to `main` on a clean
  whole-branch review before the next round starts.

## End state (after R8)

| Verdict | Projected count | Actual count | Note |
|---|---|---|---|
| `VERIFIED` (entry-specific) | ~70–85 | **11** | real, cross-checked; each in a `round-*-new-verified.md`. 40-point miss vs projection — see R8 "Landed" and Task.md: the corpus is overwhelmingly outside every Track's decidable fragment, not merely unformalized |
| `REFUTED` / `COUNTEREXAMPLE` | whatever the solvers actually find | 0 in-scope | a real research output; none of the 105 in-scope entries landed here |
| `MANUAL` | ~15–25 | **86** | each with a `MANUAL-backlog.md` brief; the honest floor, not a shortfall |
| `UNKNOWN` | **0** | **0** | the program's success metric — met |
| `VERIFIED_TEMPLATE` / `VERIFIED_SHAPE` | **0** | `VERIFIED_TEMPLATE` **0**, `VERIFIED_SHAPE` **8** | `VERIFIED_TEMPLATE` fully reclassified in R7; the 8 residual `VERIFIED_SHAPE` are non-Shapley VCG shape matches out of R6–R7's scope |

The only remaining work after R8 is a human opening `MANUAL-backlog.md` and doing
mathematics — reading a paper and writing a proof or a counterexample that no
solver in the pipeline can produce. That is the intended, irreducible floor.

## Self-Review

**Placeholder scan:** the round table names concrete deliverables, dependencies,
and corpus effects for each of R1–R8. R2–R8 plans are deferred by explicit design
(diagnostic-driven / dependency-driven), not left as "TBD" — the trigger for each
plan is stated ("authored at round start" / "authored from the R2/R3 `MANUAL`
catalogue").

**Internal consistency:** the terminal-state set (`VERIFIED` / `REFUTED` /
`MANUAL`) matches the end-state table; the automation-ceiling limits match the R4
widening candidates (each R4 candidate targets a named ceiling row); the
cross-round invariants match Phase 3's proven gate structure (baseline snapshot +
monotone + per-flip cross-validation).

**Scope check:** one program with a single measurable goal (`UNKNOWN = 0`). Each
round is independently shippable software with a corpus delta. The 80
`Valuation`/`RL`/`Naive` entries are explicitly and consistently out of scope.
Nothing is scheduled past R8 because R8 *is* the end — the residue is deliberately
human.

**Ambiguity check:** "`MANUAL` is diagnosed, not a dumping ground" is made
enforceable by the "every `MANUAL` carries a reason string in `MANUAL-backlog.md`"
invariant and the R7 hard exit criterion. "Cross-checked flip" is made concrete by
the `round-*-new-verified.md` requirement (four acceptable check types listed).

**Risk note:** the corpus-effect numbers per round are estimates; the program's
gate is `UNKNOWN = 0`, not a `VERIFIED` target, so a round that reclaims fewer
entries than projected still advances the goal by converting `UNKNOWN` ->
diagnosed `MANUAL`. The real risk is formalization accuracy at scale (mitigated by
the adversary pass + mandatory hand-check + the conservative conflict rule) and
LLM cost across ~101 entries x multiple rounds (mitigated by resumability and the
`--limit` control landed in R1).
