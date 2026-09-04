# Round R6–R7 — Second-formalizer pass + honesty gate — Delta

**Landed 2026-09-06.** Branch `round-R6R7-final-classification`, 7 commits off `main` @ `1c80b43`
(`608be15` Task 2 payment_ok split, `1360c49` Task 3 `--second-pass` mechanism,
`72914a2`+`cb93440` Task 4 second-pass sweep + formalized_ast persistence fix,
`67a2dea` Task 5 Phase 7 diagnosis flip, `1e813a0` Task 6 MANUAL-backlog.md finalization,
`7104b89` final-review golden-test fix).
Plan: `docs/superpowers/plans/2026-09-06-R6-R7-final-classification.md`.
Merge commit `081f8db`.

## In-scope distribution — before / after (live `verify()`, via `scripts.snapshot_verdicts`)

| Verdict | Baseline | After R6–R7 | Δ |
|---|---|---|---|
| VERIFIED (entry-specific) | 11 | 11 | — |
| MANUAL | 62 | 86 | +24 |
| VERIFIED_TEMPLATE | 22 | **0** | −22 |
| VERIFIED_SHAPE | 10 | 8 | −2 |
| UNKNOWN | 0 | 0 | — |

(22 Contract/Stackelberg `VERIFIED_TEMPLATE` + 2 VCG `VERIFIED_SHAPE` = the 24 flipped
Phase-7 entries; `Zheng2023fl_market`, the 25th residual entry, was already `VERIFIED`
via live `verify()` in the R6–R7 baseline itself — see "Deviation" below.)

## Phase 6 — reclaimed

- Model: `nvidia/nemotron-3-super-120b-a12b` — probed the NVIDIA endpoint's ~85 listed
  models directly against `chat.completions`; every other 70B/120B/340B-class instruct
  candidate 404'd for this account. This is the largest model actually reachable, ~6x
  the parameter budget of the R1–R5 `openai/gpt-oss-20b`.
- **0 entries reclaimed to VERIFIED.** Sweep summary: `{'selected': 25, 'verified': 0,
  'counterexample': 0, 'unknown': 17, 'dict_only': 4}`. Of the 25: 8 rebuilt a valid AST
  but the category-specific check (`_stackelberg_check_core`) still returned no
  entry-specific result (transcendental/unsolvable FOC, vector decision, or missing
  `follower_decision` metadata); 14 produced no valid AST; 3 VCG entries hit the
  no-hint dedicated VCG path with unparseable allocation LaTeX.
- The Batch-C/D/E walls (no follower IR / null FOC / genuinely multi-dimensional type /
  no screening IC in the paper) are real math/spec gaps in the source papers, not
  formalization misses — a larger model with the same prior-failure hint could not
  invent past them without fabricating content the papers don't contain. See
  `docs/superpowers/notes/round-R6R7-new-verified.md` (single no-flip line) and
  `docs/superpowers/notes/round-R6R7-sweep-raw.md` (full run + model-pin reasoning).
- Non-flip byproduct: the 8 entries that built a valid AST now carry `formalized_ast` +
  provenance in `corpus.json` regardless of verdict (Task 4 fix round 1), so their
  second-pass LLM output is auditable and doesn't need re-purchasing on a future round.

## Phase 7 — diagnosed

- 24 of the 25 residual entries flipped `VERIFIED_TEMPLATE`/`VERIFIED_SHAPE` → `MANUAL`
  with full `manual_diagnosis` (`round: "R7"`), via `scripts/r6r7_diagnose.py`.
- Recurring obstruction families across the full 86-entry backlog (not just this
  round's 24): `no-screening-IC` (10), `no-follower-IR-stated` (11),
  `vector-follower-decision` (8), `opaque-function-in-utility` (9),
  `budget-constrained-greedy-allocation` (6), `non-polynomial-gap` (4),
  `continuous-bid-space-no-discretization` (3), `transcendental-FOC-no-closed-form` (2),
  `coalition-value-not-instantiable` (2), `other` (31 genuine singletons).

## Deviation: `Zheng2023fl_market` excluded from Phase 7

The stored `z3_verdict` field on this VCG entry reads `VERIFIED_TEMPLATE` (stale), but
the live `verify()` path — the one `scripts.snapshot_verdicts` and `scripts.round_gate`
actually use — already returns `VERIFIED`, `entry_specific=True` for it (Appendix B,
Proposition 2, "All-in" baseline; cite: Zheng2023), and it was already counted as
`VERIFIED` in `round-R6R7-baseline.md` (row 105) before this round started. Overriding
it to `MANUAL` would have thrown away a real, cross-checked `VERIFIED` result — `round_gate`
caught this as a regression on the first diagnosis attempt. Ruling: leave the stale
`z3_verdict` field alone (correcting it is outside `write_manual_diagnosis`'s authorized
interface and is pre-existing corpus noise, not something this round introduced); the
plan's hard exit criterion is measured by the live verifier, which already shows this
entry as terminal. Parked as a deferred minor for a future data-hygiene pass.

## Deliverable

- `MANUAL-backlog.md` regenerated wholesale from `corpus.json`'s `manual_diagnosis`
  dicts — 86 paragraphs, grouped into 10 obstruction families (7 from the plan's
  stock list + 3 added after eyeballing the initial `other` bucket of 44), summary
  header with total + per-family entry-id lists. Reproducible:
  `python scripts/build_manual_backlog.py`. Spot-checked 5 paragraphs against
  pre-Task-6 wording — word-for-word identical content, only heading level changed.

## Carry-forward from R5 (folded in)

- `track_coalition.py`: `payment_ok` split from `core_ok` — a stated-payment mismatch
  now returns its own `COUNTEREXAMPLE` ("stated payment != Shapley value") distinct
  from a core violation. Tier A's structural-substring-check ceiling documented with a
  `ponytail:` comment (a numeric/other-letter scalar prefactor on the sum would pass;
  no corpus entry exercises it today).

## R8 handoff

- In-scope `VERIFIED` via `verify_from_ast`: 11 (unchanged this round — Phase 6
  reclaimed 0; the round's job was honesty, not new proofs).
- `UNKNOWN` = 0, `VERIFIED_TEMPLATE` = 0 — the program's hard exit criterion on the
  live verifier is met. `VERIFIED_SHAPE` = 8, all in the `Coalition`/VCG-shape family,
  covered by `MANUAL` overrides for the 4 Shapley entries plus 2 more this round;
  the remaining 8 are pre-existing non-Shapley VCG shape-only matches out of this
  round's scope.
- R8 is the `ARCHITECT_AST_VERIFY` default flip + docs — no corpus effect expected.
