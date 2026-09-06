# R14–R19 — Proof-Assistant Verification Program

**Status:** design approved 2026-09-06. Follow-on program to R11–R13
(`docs/superpowers/specs/2026-09-05-R11-R13-solver-capability-expansion-design.md`),
which shipped four tested, fail-closed solver capabilities and reclaimed
**0 of 27 targeted entries** — every target blocked on a genuine capability
ceiling of Tracks 1–6 or on data no capability can synthesise.

Post-R13 state (105 in-scope verifiable-tier entries): **`VERIFIED` 12,
`MANUAL` 93**, `UNKNOWN` 0, `VERIFIED_TEMPLATE` 0. The 8 residual
`VERIFIED_SHAPE` VCG regex matches and the 80 Valuation/RL/Naive entries
stay out of scope, as in every prior round.

## Motivation

The corpus sweep is the calibration test for the same solver tracks the
Architect loop uses to certify newly LLM-generated FL incentive mechanisms.
The Architect's intended output contract is: a mechanism (possibly novel) +
a machine-checked proof it satisfies its incentive claim + citation to prior
corpus evidence. With only 12/105 published mechanisms carrying a
sound-kernel proof, the loop is forced to ship `MANUAL`-with-disclaimer,
which directly undermines the "LLM proposes, solver proves, no fabricated
verdicts" promise.

R9 traced all 86-then-93 `MANUAL` entries to their real code-level bail
point and found every recurring cluster to be a mathematical ceiling of
Tracks 1–4 (Z3 finite-grid, SOS/CVXPY, dReal interval, SymPy Bayesian) —
not a parser bug. R11–R13 added Tracks 5 (coalition), 6 (Nash finite
action) and numeric fallbacks and still reclaimed nothing, because the
stuck families are shapes those tracks structurally cannot represent:
transcendental FOCs with no closed-form root, exponential / log-det /
square-root payments Z3 cannot linearize, multi-dimensional screening,
coalition values with no numeric instance, peer-prediction BNE, Bayesian
persuasion.

**The one method not yet tried that can structurally reach these families:
an interactive theorem prover.** Lean 4 + Mathlib carries transcendental
real analysis (`Real.exp`, `Real.log`, convexity, `deriv`, `IsMaxOn`),
`Finset` summation machinery for coalition identities, and decision
procedures (`nlinarith`, `polyrith`, `positivity`) that dominate Z3 on
exactly these shapes. An LLM translates the mechanism into a Lean statement
and tactic proof; the Lean kernel checks it. **The verdict is the kernel's,
never the LLM's** — this program's hard invariant, unchanged from R1–R13.

This also builds the exact artifact the Architect needs downstream: an
LLM-writes / kernel-checks proof pipeline that works on novel mechanisms,
not just corpus replay.

## Goal & success metric

Raise the count of corpus entries carrying a **sound-kernel-checked**
incentive-compatibility proof from 12 toward the mathematical ceiling, by
adding a proof-assistant verification track (Track 7, Lean 4 + Mathlib)
alongside Tracks 1–6, plus targeted small tracks (R18) and a numeric-push
round (R17) for what Lean cannot reach.

**Not a flip count.** Every prior round refused to promise one; same here.
Success = every one of the 93 `MANUAL` entries ends R19 in exactly one of:

1. **`VERIFIED`** — Lean kernel accepts a proof term with no `sorry`, no
   added axioms, no `native_decide` trust hole, within a time budget;
   cross-checked by one of the four accepted check types.
2. **`VERIFIED_INSTANCE`** (new sub-tier, R17) — δ-sound numeric
   certification of the IC/IR gap at the paper's stated numerical
   parameters, with the bound and parameter box recorded. Licensed by the
   original zero-UNKNOWN spec's VERIFIED definition ("a δ-sound bound with
   the bound stated"). Weaker than `VERIFIED`; **never folded into the
   headline `VERIFIED` count**; the Architect cites it as instance-only.
3. **`MANUAL`** — with a *corrected* diagnosis (R14 re-audit) naming why
   even Lean + numeric cannot reach it: needs a genuine paper-specific
   lemma, or an open modeling question in the source paper.

`UNKNOWN` stays 0. Every `MANUAL` keeps a reason string in the regenerated
`MANUAL-backlog.md`.

**Out of scope, unchanged:** the 80 Valuation/RL/Naive entries; the 8
`VERIFIED_SHAPE` VCG regex-shape matches.

## Track 7 architecture

**New module `src/tracks/track_lean.py`**, `track=7`, fail-closed like every
other track.

**Entry point:** `verify_lean(mechanism: dict, *, timeout_s: int) -> Verdict`.
Called from `verifier._verify_latex` and `ast_verify.verify_from_ast` as a
fallback **after** Tracks 1–6 decline, gated on `mechanism["lean_proof"]`
being present (same pattern as `action_set` gating Track 6). No
`architect.*` import.

**The `lean_proof` corpus field** — a build-time artifact, committed and
auditable, exactly like `formalized_ast`:

```
lean_proof: {
  statement:  "<Lean theorem signature: the IC/IR claim as a Prop>",
  proof:      "<Lean tactic block>",
  imports:    ["Mathlib.Analysis.SpecialFunctions.Log.Basic", ...],
  cross_check:"<second independent proof | cited Mathlib lemma | hand-derivation ref>",
  authored:   "<YYYY-MM-DD>",
  model:      "<llm id>"
}
```

**Verification procedure** (pure, no network, no API key):

1. Assemble a `.lean` file: `imports` + `statement` + ` := by ` + `proof`.
2. Run `lake env lean --json <file>` in a pinned toolchain
   (`lean-toolchain` + a vendored `lakefile` with a fixed Mathlib rev).
3. Parse JSON diagnostics. **Reject** if any of: `sorry` in source or a
   `declaration uses 'sorry'` warning; `axiom` declarations beyond
   Mathlib's; `native_decide` / `Lean.ofReduceBool` in the proof; any
   elaboration error; wall-clock > `timeout_s`.
4. **Accept only** on clean elaboration, zero errors, zero `sorry`, within
   budget.

**Statement schema — what "the mechanism is IC" means in Lean.** A fixed
per-family template the LLM fills; the full schema lives in
`docs/superpowers/notes/lean-statement-schemas.md`, pinned at R15.

- **Contract IC/IR:**
  `∀ θ θ', U θ (contract θ) ≥ U θ (contract θ')` and `∀ θ, U θ (contract θ) ≥ 0`,
  with `U`, `contract` the paper's concrete functions over `ℝ`.
- **Stackelberg:**
  `IsMaxOn (follower_util θ) Set.univ (best_response θ)` + the leader
  payoff at that point.
- **Coalition:** the stated payment `= ∑` over subsets as a Mathlib
  `Finset` identity.
- **VCG DSIC:**
  `∀ i bᵢ bᵢ', utility i (bᵢ ::ᵥ b₋ᵢ) ≥ utility i (bᵢ' ::ᵥ b₋ᵢ)`.

**Cross-check requirement** (program invariant): every Lean `VERIFIED`
carries one of the four accepted check types — for Lean the natural ones
are a *second, structurally different* proof (e.g. an `nlinarith` version
and a manual `calc` version both passing) or a citation to the exact
Mathlib lemma discharging the core step.

**Reproducibility:** `python -m verifier corpus.json` stays green with no
API key. The Lean **toolchain** becomes a verify-time dependency (like z3,
dReal); CI and dev setup install it. If `lake` is absent, Track 7 fails
closed to the entry's current verdict and prints one line
("Lean toolchain not found") — never a crash, never a pass. A `--skip-lean`
flag exists for environments without it. The stored `lean_proof` + recorded
kernel result means re-verification does not re-run `lake` unless the proof
text changed (mirrors `formalized_ast`).

**LLM formalizer:** `src/architect/formalize_lean.py`, CLI-only, build-time,
never imported by the verify path. Emits the `lean_proof` field for a
batch of entries; resumable; `--limit`.

## The rounds

Same discipline as R1–R13: per-round `round-<Rn>-baseline.md` full
per-entry verdict table before any change; monotone `VERIFIED` gate (count
only rises or holds, no entry to a strictly-worse verdict); every flip
cross-checked and recorded in `round-<Rn>-new-verified.md`; every `MANUAL`
keeps a reason string; formalizer/LLM is build-time only; fail-closed on
any ambiguity; **no branch-per-round** (R11–13 deviation, retained); each
round's plan authored at its start and **ends by updating the next round's
plan** with discoveries and scope corrections.

### R14 — Fresh MANUAL re-audit

Do not trust R9's labels (a spot check in R9's own motivation found the
stored diagnosis can be wrong; R11/R13 found several more). Re-trace all
93 `MANUAL` entries to the real code-level bail point — extend
`scripts/diagnose_manual_root_cause.py` (exists from R9). For each entry
add a `reachability_tag`: `lean` / `numeric-instance` /
`new-small-track:<name>` / `needs-paper-lemma` / `modeling-open`. Output
`docs/superpowers/notes/round-R14-reachability-audit.md`, one row per
entry (id, category, real bail point, corrected diagnosis, tag). This
sizes R15–R19. No solver code changes.

- Corpus effect: 0 (audit only); corrects stale diagnoses in
  `MANUAL-backlog.md` at R19.
- Depends on: —

### R15 — Lean track infra + smoke

Build `track_lean.py`, the toolchain vendoring (`lean-toolchain`, vendored
`lakefile`, pinned Mathlib rev), the statement schemas doc, and
`src/architect/formalize_lean.py`. Smoke on 5 `reachability_tag: lean`
entries hand-picked for variety: one exponential-payment Contract, one
square-root-gain, one coalition `Finset` identity, one Stackelberg FOC,
one multi-dim screening. Ship even at 0/5 flips — tested infra is the
deliverable (R3a/R3b/R5 precedent). 10+ tests in `tests/tracks/test_lean.py`
(a known-good proof passes; a `sorry` proof fails closed; a
`native_decide` proof fails closed; missing toolchain fails closed; a
timeout fails closed).

- Corpus effect: +0–5.
- Depends on: R14.

### R16 — Lean sweep on transcendental + coalition families

Run `formalize_lean` over every `lean`-tagged entry. Families in scope:
exponential-payment (`Seo2021sdn_fl`, `Seo2022noniid_auction`, and the
other `non-polynomial gap Z3 cannot linearize` entries), square-root-gain
(`Saputra2021straggling`), log-det (`Wei2024truthful_bandit`),
Shannon-capacity terms, the 4 Shapley entries, multi-dim screening. Every
QED cross-checked (second structurally-different proof, or Mathlib lemma
citation). Land incrementally: one family, re-sweep that family's entries,
cross-check every flip, commit, move to the next.

- Corpus effect: whatever lands — the program's primary payload round; no
  number promised.
- Depends on: R15.

### R17 — Numeric-push

For `numeric-instance`-tagged entries: transcribe each paper's stated
numerical setup into `fixed_constants` / `coalition_values`, then run
dReal + SciPy interval certification of the IC/IR gap over the stated
parameter box (the R11/R13 capabilities — `_numeric_solve_stationarity`,
Track 3 box reduction — finally fed real data). Flips land as
`VERIFIED_INSTANCE` with `{solved_by: "numeric", method, tolerance,
param_box}` recorded. Only lands when the paper states concrete numbers;
a converged-but-unverified optimum (saddle point — second start point +
Hessian sign check where cheap) or any non-convergence fails closed.

- Corpus effect: +5–20 `VERIFIED_INSTANCE` (not `VERIFIED`).
- Depends on: R14 (independent of R15/R16).

### R18 — Small new tracks

For `new-small-track`-tagged residuals:

- `src/tracks/track_peer_prediction.py` — proper-scoring-rule / Bayesian
  Truth Serum properness feasibility check (`Zhang2020fedserving`).
- `src/tracks/track_persuasion.py` — Bayesian-persuasion signal-scheme
  feasibility (`2505_05842`).
- **continuous-action Nash** — fold into the Stackelberg FOC path, **not**
  a new module (`Zhao2023truthful`; R12 shape-(d) ×5).

Each fail-closed, tested in `tests/tracks/`, pinned to its motivating
entries.

- Corpus effect: +0–10.
- Depends on: R14.

### R19 — Parser fix + finalize

The `E[·]` opaque-expectation parser fix: represent `\mathbb{E}[·]` / `E[·]`
as a dedicated opaque operator instead of folding it into Euler's `e`,
then reason about when it inherits monotonicity / sign from its argument.
Re-sweep affected entries (`Han2025paid_models`, `Luo2023unbiased`). Full
`PYTHONPATH=src python -m verifier corpus.json` re-sweep. Regenerate
`MANUAL-backlog.md` via `scripts/build_manual_backlog.py` — R14's corrected
paragraphs replace stale ones, reclaimed entries drop out. Wire Track 7
into the Architect generation loop behind `ARCHITECT_LEAN_VERIFY` (default
on/off decided by the observed R16 hit-rate — R8 precedent). Write
`docs/superpowers/notes/program-R14-R19-summary.md` (targeted vs reclaimed
per round; where the count moved; process lessons; residual gaps named).

- Corpus effect: +0–3 plus the loop-side flag change.
- Depends on: R16, R17, R18.

## New verdict semantics

`VERIFIED_INSTANCE` is the only new tier. No new verdict type otherwise: a
Lean flip is `VERIFIED`, recorded with
`{solved_by: "lean", mathlib_rev: <str>, cross_check: <str>}` in the
entry's `z3_verdict`/equivalent metadata field. A Lean non-elaboration,
any `sorry`/axiom/`native_decide`, or a timeout fails closed to the
entry's current verdict — never a guessed `VERIFIED`.

## Cross-round invariants (inherited from R1–R13, unchanged)

- Baseline snapshot before any change each round
  (`round-R14-baseline.md`, …).
- Monotone `VERIFIED` gate — count only rises or holds.
- Every flip cross-checked and recorded in `round-<Rn>-new-verified.md`
  (four accepted check types: hand-derived gap with signs; a second
  track/method agreeing; a kernel/model inspection; a cited theorem).
- Every entry that stays `MANUAL` keeps (or gets a corrected) reason
  string in `MANUAL-backlog.md`.
- Fail-closed on any non-elaboration, non-convergence, timeout, or
  ambiguity.
- Formalizer/LLM stays build-time only; `python -m verifier corpus.json`
  reproducible with no API key. The Lean toolchain is a local,
  deterministic verify-time dependency (like z3/dReal); `--skip-lean`
  for environments without it, fail-closed if absent.
- Regression test per widening in `tests/tracks/`, pinned to the
  motivating entries.
- **No branch-per-round** (explicit deviation from R1–R9, retained from
  R11–R13): work lands directly against the current tree; each round's
  plan still gets independent review before its commits.
- **Plan handoff:** each round's plan document ends with an explicit
  instruction to update the *next* round's plan with issues,
  discoveries, or scope corrections found while executing.

## Exit criterion

R14: `round-R14-reachability-audit.md` has one row per `MANUAL` entry with
a real bail point and a `reachability_tag`. R15: `track_lean.py` landed
with tests, toolchain vendored, 5-entry smoke run. R16: every
`lean`-tagged entry re-swept, every flip cross-checked, delta doc written.
R17: numeric-instance entries re-swept, every `VERIFIED_INSTANCE` carries a
recorded bound + param box. R18: the small tracks landed with tests, their
tagged entries re-swept. R19: parser fix landed, full re-sweep,
`MANUAL-backlog.md` regenerated, Architect-loop flag set, program summary
written. No round promises a flip count — Phase-1-style discovery risk
applies throughout, same honest-uncertainty framing as every prior round.
The monotone `VERIFIED`-only-rises gate applies throughout, and any round
that reclaims 0 entries but lands correct, tested, fail-closed capability
is still a valid outcome (R3a/R3b/R5/R11/R12/R13 precedent) — provided it
also updates the next plan with what it learned.

## Self-Review

**Placeholder scan:** every round has named targets, a stated dependency,
and a corpus-effect range (ranges, not promises — consistent with the
program's established honest-uncertainty framing). Round internals (exact
per-entry Lean statements) are deferred to each round's plan, per the
R4/R6-R7/R11-R13 precedent — a stated deferral, not a gap.

**Internal consistency:** the hard invariant (kernel verdict, never LLM)
is stated in Motivation, Goal, Track 7 architecture, and New verdict
semantics identically. `VERIFIED_INSTANCE`'s exclusion from the headline
count is stated in Goal and repeated in New verdict semantics. R17's
independence from R15/R16 is stated explicitly in its Depends-on line.

**Scope check:** six rounds, one program, one measurable goal (raise the
sound-kernel-checked count; every `MANUAL` ends terminal with a corrected
reason). Same invariant discipline as R1–R13 with the one retained
deviation (no branch-per-round) called out. The 80 out-of-family and 8
`VERIFIED_SHAPE` entries stay excluded as in every prior round.

**Ambiguity check:** "verified by a solver, not an LLM" is made concrete
by Track 7's step-3 reject list (`sorry` / added axioms / `native_decide`
/ any error / timeout) and step-4 accept condition. "δ-sound instance" is
made concrete by the recorded `{tolerance, param_box}` and the
"only when the paper states concrete numbers" gate.

**Risk note:** the LLM→Lean formalization hit rate is genuinely unknown
until R15's smoke runs — R15 is a real go/no-go, and R16 narrows to
Mathlib-citable families if the smoke is weak. Mathlib version drift is
mitigated by a pinned rev whose upgrade is its own reviewed re-sweep.
`VERIFIED_INSTANCE` over-claim is mitigated by the concrete-numbers gate
and its exclusion from the `VERIFIED` count. If R14 merely re-confirms
R9's ceiling, the honest program end is the corrected catalogue plus a
tier-aware Architect citation policy — still a valid outcome.
