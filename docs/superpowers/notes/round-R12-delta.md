# Round R12 — Nash-Equilibrium / Action-Choice Track — Delta

**Landed 2026-09-06.** No branch this round (program-level deviation, see
umbrella spec). Plan:
`docs/superpowers/plans/2026-09-05-R12-nash-equilibrium-track.md`.
Re-trace: `docs/superpowers/notes/round-R12-root-cause-recheck.md`.
Flip cross-check: `docs/superpowers/notes/round-R12-new-verified.md`.

## Targeted entries — before / after

| paper_id | category | before | after | Task 2 shape | method |
|---|---|---|---|---|---|
| 2408_13223 | Contract | MANUAL | MANUAL | a (finite-action Nash) | no payoff table |
| 2605_02935 | Contract | MANUAL | MANUAL | a (finite-action Nash) | no payoff table |
| Li2026network | Contract | MANUAL | MANUAL | a (finite-action Nash) | no payoff table |
| Zhang2020fedserving | Contract | MANUAL | MANUAL | b (peer-prediction BNE) | out of Track 6 scope |
| 2505_05842 | Contract | MANUAL | MANUAL | c (Bayesian persuasion) | out of Track 6 scope |
| Bornstein2023realistic_incentive | Contract | MANUAL | MANUAL | d (continuous-action Nash) | out of Track 6 scope |
| Huang2024aigc | Contract | MANUAL | MANUAL | d (continuous-action Nash) | out of Track 6 scope |
| Karimireddy2022data_sharing | Contract | MANUAL | MANUAL | d (continuous-action Nash) | out of Track 6 scope |
| Zhao2023truthful | Contract | MANUAL | MANUAL | d (continuous-action Nash) | out of Track 6 scope |
| 2505_02462 | Contract | MANUAL | MANUAL | d (single-report truthfulness) | out of Track 6 scope |

**0 flips.** Valid per the umbrella spec ("a round that reclaims 0 entries
but lands correct, tested, fail-closed capability is still a valid
outcome").

## What shipped

- **`src/tracks/track_nash.py`** — new Track 5b module,
  `verify_nash_action_choice(entry) -> VerificationResult` with helpers
  `_parse_action_payoffs`, `_is_best_response`, `_check_all_best_responses`.
  Finite enumeration over an explicit `action_set`: for the paper's
  `stated_equilibrium_profile`, every player's every alternative action is
  checked against their current payoff; a strictly-improving deviation ->
  `COUNTEREXAMPLE`, none for any player -> `VERIFIED` (`entry_specific=True`),
  any missing field or unparseable payoff table -> `MANUAL`. No
  `architect.*` import. Uses **`track=6`** (`track_coalition.py` already
  claims `track=5`). 8 unit tests + 2 wiring tests
  (`tests/tracks/test_nash_equilibrium.py`).
- **Wiring — `src/verifier.py`** — a pre-check at the top of `_verify_latex`
  (there is no standalone `dispatch_contract`): when
  `entry["mechanism"]["action_set"]` is present, try
  `verify_nash_action_choice` first; only a `VERIFIED`/`COUNTEREXAMPLE`
  short-circuits, `MANUAL` falls through to the normal screening-IC path.
- **Wiring — `src/architect/ast_verify.py`** — an early branch in
  `verify_from_ast` (before `_classify_ast`): `if meta.get("action_set")`
  route to `verify_nash_action_choice`, mirroring the Shapley/coalition
  local-import pattern.
- **10 corrected `manual_diagnosis` entries** + an R12 batch in
  `MANUAL-backlog.md`, replacing the generic "no-screening-IC" text with the
  Task 2 shape-specific obstruction (a / b / c / d).

## Task 2 finding — the family is not homogeneous

R9's `no-screening-IC` family label bundled four distinct shapes. Re-tracing
against stored PDF-derived evidence (no PDFs in the repo; the R3a extraction
pass had already declined for all 10):

- **(a) finite-action Nash** — `2408_13223`, `2605_02935`, `Li2026network`.
  Track 6's real target. All three lack a transcribable numeric payoff
  table, so they stay `MANUAL` via the "shape confirmed, nothing to
  enumerate" path (mirrors `track_coalition.py`'s Tier-A-only `MANUAL`).
- **(b) peer-prediction / Bayesian Truth Serum BNE** — `Zhang2020fedserving`.
  Needs a proper-scoring-rule track (future round).
- **(c) Bayesian persuasion** — `2505_05842`. Needs a signal-scheme
  feasibility track (future round).
- **(d) continuous-action Nash / other** — `Bornstein2023realistic_incentive`,
  `Huang2024aigc`, `Karimireddy2022data_sharing`, `Zhao2023truthful`
  (continuous best-response / FOC, closer to the Stackelberg track), and
  `2505_02462` (a single self-reported-cost truthfulness property, no action
  set at all).

## Why 0 flips

No paper PDFs in the repo, and the R3a LLM extraction over the PDF text had
already declined (`confident=false`) for every one of the three shape-(a)
entries. `verify_nash_action_choice` needs a concrete numeric payoff at
every joint action profile; none exists in any `mechanism` dict and nothing
was fabricated. Per the plan's fail-closed rule the fields are left absent
and the entries stay `MANUAL`.

## Corpus totals

| verdict | R12 baseline | after R12 |
|---|---|---|
| VERIFIED | 12 | 12 |
| VERIFIED_TEMPLATE | 0 | 0 |
| MANUAL | 93 | 93 |
| UNKNOWN | 0 | 0 |

`--only Contract` gate: `GATE: PASS`. Full test suite: 486 passed,
2 skipped, 3 xfailed.
