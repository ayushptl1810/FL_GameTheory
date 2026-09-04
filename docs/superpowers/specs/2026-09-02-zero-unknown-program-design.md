# Zero-UNKNOWN Program — Design

**Status:** Program design approved 2026-09-02. Umbrella spec for Rounds R1–R8.
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
32 R6 formalization-miss candidates. The 4 Shapley entries stay `UNSUPPORTED` (R5).

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
`<R4-merge>`. Delta: `docs/superpowers/notes/round-R4-delta.md`.

### R5 — Phase 4: coalition / Shapley track

New `src/tracks/track_coalition.py` — `verify_coalition` for `k <= 3`: enumerate
all coalitions, compute the characteristic function `v(S)` from the mechanism's
allocation, check the stated Shapley payment against the marginal-contribution
definition (symbolically or on a grid), check core / individual rationality
(`sum_{i in S} p_i >= v(S)` for all `S`). `_classify_ast` routes `Shapley` category
to it. Entries with `k > 3` or non-enumerable coalition value -> `MANUAL`.

- Corpus effect: +2–4 (of the 4 Shapley entries)
- Depends on: R3 (independent of R4)
- Plan authored at round start.

### R6 — Second-formalizer pass on residual `MANUAL`

For every entry still `MANUAL` after R4/R5, a fresh formalization attempt with a
*different* model and the accumulated `MANUAL` reason injected as a hint ("the
prior attempt was blocked on X — try formulating around it, e.g. reframe the
continuous type as a fine discrete grid / isolate the binding constraint / drop a
provably-slack term"). Some `MANUAL`s are formalization failures, not math
failures. Each reclaimed entry is hand-checked as in R2/R3.

- Corpus effect: +3–8
- Depends on: R4, R5
- Plan authored at round start.

### R7 — Honesty pass + final classification (the hard gate)

Every remaining `VERIFIED_TEMPLATE` / `VERIFIED_SHAPE` that the formalizer could
not upgrade flips to `UNKNOWN`, then **immediately** receives a `MANUAL` diagnosis
naming why it is not automatically provable. Every remaining `UNKNOWN` (there
should be none from parser failures by now) likewise gets a `MANUAL` diagnosis.

**Exit criterion (hard): after R7 the corpus contains no `UNKNOWN` and no
unqualified `VERIFIED_TEMPLATE` / `VERIFIED_SHAPE`.** Commit
`docs/superpowers/notes/MANUAL-backlog.md`: one paragraph per `MANUAL` entry —
the mechanism, the obstruction (with the track and the specific limit it hit),
and the concrete human task to close it.

- Corpus effect: `VERIFIED_TEMPLATE` 59 -> 0, `VERIFIED_SHAPE` 33 -> 0, `UNKNOWN` -> 0;
  counts move to `VERIFIED` + `REFUTED` + `MANUAL`
- Depends on: R6
- Plan authored at round start.

### R8 — `ARCHITECT_AST_VERIFY` flip + docs

With ~75–90 / 101 corpus entries verified through `verify_from_ast`, the AST path
has the track record to become the Architect loop's default verifier. Run the
flagged `run_eval` (or document it remains infra-blocked), flip
`ARCHITECT_AST_VERIFY` default to on, update `Task.md` "Verdict Semantics" + the
roadmap spec with the final numbers.

- Corpus effect: +0 (loop-side change)
- Depends on: R7
- Plan authored at round start.

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

| Verdict | Projected count | Note |
|---|---|---|
| `VERIFIED` (entry-specific) | ~70–85 | real, cross-checked; each in a `round-*-new-verified.md` |
| `REFUTED` / `COUNTEREXAMPLE` | whatever the solvers actually find | a real research output |
| `MANUAL` | ~15–25 | each with a `MANUAL-backlog.md` brief |
| `UNKNOWN` | **0** | the program's success metric |
| `VERIFIED_TEMPLATE` / `VERIFIED_SHAPE` | **0** | all reclassified in R7 |

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
