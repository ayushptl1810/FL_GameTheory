# Approach C — parse-error audit

> **See the "Post-Task-13 re-measurement" section at the bottom for the current
> result.** Everything between here and that section is the pre-Task-13 scoped
> measurement (HEAD ab12a8a) and is **SUPERSEDED** — kept for history only.

---

# Approach C — parse-error audit (scoped) — SUPERSEDED

Date: 2026-08-29
Branch: `approach-c-ast-verify` (HEAD ab12a8a)
Task 11 (scoped: live_smoke breadth harness only; the full 12-benchmark flagged
eval is **pending** and run separately by the controller).

Model: `openai/gpt-oss-120b`, `ARCHITECT_LLM_TIMEOUT_S=120`, `ARCHITECT_BUDGET_S=300`.
Harness: `python -m architect.eval.live_smoke` (one loop per family + one forced-Hybrid).

Note: live_smoke prints only `transcript[-3:]` per family and the LLM is
non-deterministic, so routing/mode differs run-to-run and earlier transcript
entries are not captured. Counts below are over what each run printed.

## FLAGGED — `ARCHITECT_AST_VERIFY=1`  (`/tmp/ast-live-smoke.log`)

| family | status | iters | note |
|---|---|---|---|
| stackelberg_effort | VERIFIED | 2 | Synthesis; VERIFIED_TEMPLATE -> VERIFIED via AST path |
| contract_screening | VERIFIED | 3 | Synthesis; AST path, entry-specific IC/IR |
| vcg_auction | VERIFIED | 9 | routed **Hybrid**; iter 8 = `PARSE` (round-trip mismatch on `client_utility_latex`), recovered by iter 9 |
| hybrid_forced | VERIFIED | 2 | Hybrid; UNKNOWN -> VERIFIED |

VERIFIED: 4/4.
Parse-family transcript entries (verdict `PARSE` / OutsideParseableFragment / round-trip): **1**
 - vcg_auction, iter 8, `verdict: PARSE` — "round-trip mismatch on client_utility_latex:
   rendered LaTeX does not re-parse to the proposed expression".

## UNFLAGGED baseline  (`/tmp/latex-live-smoke.log`)

| family | status | iters | note |
|---|---|---|---|
| stackelberg_effort | VERIFIED | 1 | Synthesis |
| contract_screening | VERIFIED | 2 | Synthesis; 2-type linear-cost screening |
| vcg_auction | **FAILED** | 11 | Synthesis; iter 9 MC_COUNTEREXAMPLE, iter 10 PROPOSE_ERROR, iter 11 UNKNOWN |
| hybrid_forced | VERIFIED | 2 | Hybrid |

VERIFIED: 3/4.
Parse-family transcript entries (printed tails + whole-log grep): **0**
(baseline vcg_auction failed via counterexample + PROPOSE_ERROR, not a parse error,
and never routed to the Hybrid LaTeX path this run.)

## Flagged vs unflagged parse-error counts

| | flagged (AST_VERIFY=1) | unflagged baseline |
|---|---|---|
| VERIFIED families | 4/4 | 3/4 |
| parse-family transcript entries | 1 | 0 (visible) |

Per family: the only parse-family entry in either run is **vcg_auction / flagged / iter 8**.

## Verdict

**The scoped run did NOT show the flag eliminating parse-family transcript entries** —
flagged produced 1 `PARSE` entry, unflagged produced 0. Two caveats:

1. The comparison is confounded by non-determinism: unflagged `vcg_auction` ran in
   Synthesis and failed via counterexample/PROPOSE_ERROR (never reaching a LaTeX
   round-trip), while flagged `vcg_auction` routed to **Hybrid**.
2. The residual `PARSE` in the flagged run originates in `serialize.py` (the LaTeX
   round-trip check done while *rendering* the mechanism for the transcript), which
   is **outside** the `inspect.inspect_mechanism` -> `verify_from_ast` path that
   `ARCHITECT_AST_VERIFY=1` controls. The flag removes the LaTeX parser from the
   *verification* step, not from Hybrid's LaTeX serialization/output step.

So the payoff claim ("parse-error transcript entries drop to zero") is **not
demonstrated by this scoped breadth run**. Whether it holds needs the full
12-benchmark flagged eval (`eval-results.json` transcript audit), which the
controller runs separately. Expectation per the brief remains zero; this note
flags that the Hybrid serialization path can still emit `PARSE` even with the flag on.

---

## Post-Task-13 re-measurement

Date: 2026-08-29
Branch: `approach-c-ast-verify` (post-Task-13; round-trip skip on the flagged
`inspect_mechanism` -> `verify_from_ast` path is in effect).
Harness: `python -m architect.eval.live_smoke`, `ARCHITECT_AST_VERIFY=1`.
Log: `ast_smoke_postT13.log` (scratchpad).

| family | expected | mode | status | iters | note |
|---|---|---|---|---|---|
| stackelberg_effort | Stackelberg | Synthesis | VERIFIED | 1 | FOC + follower IR, entry-specific |
| contract_screening | Contract | Synthesis | VERIFIED | 1 | entry-specific IC/IR, 2×1 pairs |
| vcg_auction | VCG | Synthesis | VERIFIED | 7 | iter 6 MC_COUNTEREXAMPLE + restart; reframed to **Contract**, VERIFIED iter 7 |
| hybrid_forced | (none) | Hybrid | VERIFIED | 2 | VERIFIED_TEMPLATE (AST path, no entry-specific result) -> VERIFIED iter 2 |

VERIFIED: 4/4.
Parse-family transcript entries (verdict `PARSE` / OutsideParseableFragment /
round-trip mismatch), printed tails + whole-log grep: **0**.

**This supersedes the pre-Task-13 scoped measurement above.** With Task 13's
round-trip skip on the flagged loop path, the flagged loop produces **zero
parse-family transcript entries** — the residual `PARSE` seen pre-Task-13
(vcg_auction / Hybrid / iter 8, from `serialize.render`'s round-trip check) no
longer appears, because that check is now skipped when the AST-verify flag is on.
