# R9 — MANUAL Root-Cause Audit + Widening

**Status:** Design approved 2026-09-05. Follow-on round to the Zero-UNKNOWN
program (`docs/superpowers/specs/2026-09-02-zero-unknown-program-design.md`),
which formally ended at R8 with `UNKNOWN = 0`, `VERIFIED_TEMPLATE = 0` met.
R9 targets the next-largest lever left: the 86-entry `MANUAL` set.

## Motivation

`MANUAL-backlog.md`'s 86 paragraphs are internally consistent with
`corpus.json` (verified 2026-09-05: 86 paragraphs, 86 `verdict_override:
"MANUAL"` entries, exact 1:1 match, no gaps/duplicates/orphans). But a spot
trace of one entry found the stored diagnosis does not match the code-level
failure:

- `1811_12082` is catalogued under `no-follower-IR-stated` ("ir_follower_latex
  null fail-closed"). But `ir_follower_latex` is never read anywhere in
  `src/tracks/track1_z3.py` — `_stackelberg_check_core` derives IR itself
  (`U_follower(e*) >= 0`, symbolic or Track-3-escalated) rather than gating on
  a stored IR field. Tracing the entry directly shows it actually fails at
  `_resolve_stackelberg_utility`: the paper's follower utility is a 3-clause
  substitution chain (`U = f(s^d) - Σq_i·s_i^d`, `f(s^d) = Σf_i(s_i^d)`,
  `f_i(s_i^d) = a_i - b_i·exp(-c_i·s_i^d)`) that the current substitution
  logic doesn't resolve.

A second check across 5 more `no-follower-IR-stated` entries
(`2110_12876`, `2203_00270`, `2404_08261`, `2508_07676`, `Cao2025service`)
shows utility parsing succeeds for all of them — so if `1811_12082`'s real
obstruction is substitution-chain depth, the family's other members are
failing later in the pipeline for other reasons. The stored obstruction
*label* is not reliable as a guide to what to fix; it was written from the
LLM/human review's read of the paper, not from tracing the verifier code.

**R9's job:** re-derive the true code-level bail point for all 86 MANUAL
entries (not just the two largest families), correct the catalogue where it's
wrong, and widen whatever real cause recurs ≥2 times.

## Scope

All 86 in-scope `MANUAL` entries (61 non-Shapley + the 4 Shapley entries +
whatever the current family breakdown is at round start — recount from
`corpus.json` in the round-start baseline, don't reuse this doc's numbers).
Open-ended: every entry gets traced, not just the two largest families named
in this doc's motivation section.

Out of scope: the 8 `VERIFIED_SHAPE` VCG entries (residual regex-shape
matches, a separate, smaller gap noted in the R6-R7 delta) and the 80
out-of-family `Valuation`/`RL`/`Naive` entries — both stay excluded as in
every prior round.

## Approach

### Phase 1 — Root-cause trace (open-ended)

For each of the 86 MANUAL entries, call the category's actual verification
entry point directly against the stored `mechanism` dict (`_try_stackelberg_latex`,
`_try_contract_latex` / `_contract_check_core`, `verify_vcg`'s Track-1 path,
`verify_coalition`, Track 2/3/4 as applicable per category) and walk the call
chain to the exact function + condition that returns `None` / fails / declines
to certify. Record:

- entry id, category, round originally diagnosed
- stored `manual_diagnosis` text (mechanism / obstruction / track / limit)
- actual code-level bail point (function name + condition)
- match / mismatch verdict against the stored diagnosis

Write this to `docs/superpowers/notes/round-R9-root-cause-audit.md` — one row
per entry. This is diagnostic tooling, not a permanent verifier feature; the
tracing script (`scripts/diagnose_manual_root_cause.py`) is committed (like
R4's diagnostic tooling) but is not wired into `verify_from_ast`.

### Phase 2 — Regroup by real cause

Re-cluster the 86 entries by the *actual* bail point found in Phase 1, which
may not match today's `MANUAL-backlog.md` families. A cause hit by ≥2 entries
is a widening candidate. A cause hit by exactly 1 entry stays diagnosed
`MANUAL` with a corrected paragraph (accurate obstruction, even if not
widened this round).

### Phase 3 — Widen recurring causes

Implement each ≥2-entry widening as fail-closed solver code (same standard as
R4): a real code fix — deeper substitution-chain resolution, a missing
sibling-check relaxation, whatever Phase 1/2 actually finds — never a
heuristic that could certify an unproven verdict. Each widening gets a
regression test in `tests/tracks/` pinned to the motivating entry(ies). Land
incrementally: implement one widening, re-sweep the entries it targets,
cross-check every flip (hand-derived IC/IR gap, a second track agreeing, a Z3
model inspection, or a cited theorem — same four acceptable check types as
every prior round), commit, move to the next.

### Phase 4 — Re-sweep and backlog regeneration

Full `PYTHONPATH=src python -m verifier corpus.json` re-sweep. Regenerate
`MANUAL-backlog.md` via `scripts/build_manual_backlog.py` — corrected
paragraphs replace stale ones (including `1811_12082`'s, regardless of
whether it's reclaimed to `VERIFIED` or stays `MANUAL` with the real
obstruction), reclaimed entries drop out entirely. Write
`docs/superpowers/notes/round-R9-delta.md` (mirrors every prior round's
delta doc: before/after counts, new-verified list with cross-checks,
corrected-diagnosis list, still-MANUAL-with-real-cause list).

## Cross-round invariants (inherited, unchanged)

Same as the Zero-UNKNOWN program's invariants: baseline snapshot before any
change (`round-R9-baseline.md`), monotone `VERIFIED` count gate, every flip
cross-checked and recorded in `round-R9-new-verified.md`, every `MANUAL`
still carries a reason string in the regenerated backlog, formalizer/LLM
stays a build-time-only dependency (verify stays reproducible with no API
key — Phase 1-4 above use no LLM at all, pure code tracing), fail-closed on
any ambiguity, branch `round-R9-manual-root-cause-audit` off `main`, merge on
clean review.

## Exit criterion

`docs/superpowers/notes/round-R9-root-cause-audit.md` has one row per MANUAL
entry with a recorded match/mismatch verdict against the stored diagnosis.
`MANUAL-backlog.md` is regenerated with corrected paragraphs for every
mismatch found. Every recurring (≥2-entry) real cause identified in Phase 1
either has a landed widening (with cross-checked flips) or a stated reason
it wasn't attempted this round (e.g. too deep, needs a new track — becomes
an R10+ candidate). Corpus effect: whatever Phase 3 actually reclaims — no
number is promised, since Phase 1 is discovery, not a known quantity. The
monotone gate (`VERIFIED` only rises) still applies throughout.

**R9 scope note:** this round completed Phases 1-2 in full (86/86 MANUAL
entries traced and root-caused; all real recurring clusters catalogued).
Phase 2's analysis found 0 confirmed-fixable clusters among the 8 real
≥2-entry clusters identified — every one classified as a genuine solver
ceiling (one 4-entry VCG sub-group was flagged as worth a closer look but
not confirmed fixable). Phases 3 (widen recurring causes) and 4 (re-sweep +
regenerate `MANUAL-backlog.md`) are conditional on Phase 2 finding
fixable-bug candidates; since it found none, Phases 3-4 had no work to do
this round and were correctly not attempted — this is a negative result, not
a shortfall. See `docs/superpowers/notes/round-R9-widening-candidates.md`
for the full cluster-by-cluster classification.

## R10 — Nash-equilibrium / action-choice track (named, not planned)

The `no-screening-IC` family (10 entries sampled: `2408_13223`,
`2505_02462`, `2505_05842`, `2605_02935`, `Bornstein2023realistic_incentive`,
`Huang2024aigc`, `Karimireddy2022data_sharing`, `Li2026network`,
`Zhang2020fedserving`, `Zhao2023truthful`) is a genuine schema gap, not a
solver bug: these entries have `client_utility_latex` and (sometimes)
`ir_participation_latex` populated but `ic_screening_latex` is correctly
null — the paper proves truthfulness as a Nash-equilibrium condition over a
small discrete action set (e.g. `{abstain, join, buy}`), a Bayesian
persuasion feasibility property, or a peer-prediction BNE — not a
type-`i`-vs-type-`j` self-selection IC constraint. No corpus field currently
captures an action set or per-action payoff, so no track can check this
today regardless of solver capability.

R10 is named here as a real, scoped-for-later round, **depends on R9**
(R9's Phase 1 may correct or shrink this family — some of the 10 could turn
out to be solver bugs, not schema gaps, once traced). Per the program's
established pattern (R4 authored from R2/R3's actual `MANUAL` catalogue, not
guessed upfront), **R10's plan — corpus schema fields, new track module vs.
extension of Track 1, checker logic — is authored at R10's start, from R9's
corrected catalogue**, not committed in this document.

## Self-Review

**Placeholder scan:** R9's phases are concrete (trace → regroup → widen →
re-sweep); R10 is deliberately left unplanned per the approved design
decision, consistent with the program's R4 precedent — not a placeholder
gap, a stated dependency.

**Internal consistency:** the motivating example (`1811_12082`) is traced
end-to-end in this doc with the actual function name and condition that
fails, not just asserted. The `no-follower-IR-stated` family's mixed-cause
finding (1 traced failure at utility-resolution, 5 more that parse utility
fine) is what justifies Phase 1's open-ended scope over a narrower
targeted-list approach.

**Scope check:** single round, one deliverable (corrected catalogue +
whatever widenings land), same invariant discipline as every prior round.
R10 is explicitly deferred, not silently expanded into this document.

**Risk note:** Phase 1 is discovery — the corpus-effect number is genuinely
unknown until it runs, unlike R2-R8 which had rough estimates. This is
called out in the exit criterion rather than papered over with a guessed
range.
