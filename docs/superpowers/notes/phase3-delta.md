# Phase 3 — Corpus Delta

**Branch:** `phase3-verifier-widening` (off `main` da6cfc3) · **Range:** b09cdfe..9a45926 (Tasks 1–14) · docs wrap: Task 15.

## Headline: zero corpus movement

The before/after corpus verdict table is **identical**. Not "roughly the same" —
byte-identical `python -m verifier corpus.json` output, and a per-entry verdict
diff vs `phase3-baseline.md` that comes back empty.

| verdict | baseline (Task 1) | after Phase 3 (Task 14) |
|---|---|---|
| VERIFIED (entry-specific) | 6 | 6 |
| VERIFIED_TEMPLATE | 59 | 59 |
| VERIFIED_SHAPE | 33 | 33 |
| UNKNOWN | 2 | 2 |
| UNSUPPORTED | 5 | 5 |
| **total checked** | 105 | 105 |

Per-category, also frozen: Contract 5 entry-specific / 31 template; Stackelberg
1 entry-specific / 28 template / 1 UNSUPPORTED; VCG 33 VERIFIED_SHAPE; Shapley 4
UNSUPPORTED. Track 2 SOS = 4, Track 3 = 1, Track 4 = 1.

The 6 entry-specific VERIFIED are unchanged: Contract — 2307_15975, Li2025bayesian_incentive,
Lim2020contract_healthcare, Sun2022coded, Tan2025renegotiable_contract; Stackelberg —
Sarikaya2019stackelberg_workers.

`docs/superpowers/notes/phase3-new-verified.md` has **0 entries** across all of
Part C. That is the plan-permitted partial-landing outcome, not a miss.

## Why capability landed without the corpus moving

Every widened parser / encoder hit a **second, independent blocker** on every
corpus entry it could newly reach the first blocker on. The widening removed
blocker #1; blocker #2 fails closed to the entry's existing verdict:

- **VCG encoder (Tasks 2–4):** `verify_vcg_dsic` now encodes weighted-welfare-max
  (affine maximizer) + Clarke pivot. Every argmax-welfare corpus VCG entry pairs
  that allocation with a sum-externality payment that `parse_payment` rejects →
  entry stays VERIFIED_SHAPE. The new capability is exercised only by synthetic
  fixtures and the synthesis menu.
- **Contract parser (Task 11):** 3 target classes (`\sum` menu aggregation, ≥2
  distinct type subscripts, `n−1` arithmetic, `f_{sub}(arg_{sub})` families).
  Each corpus entry that clears the targeted blocker then dead-ends on a *different*
  one — expectation notation, opaque multi-arg funcs, `^label` power ambiguity,
  `n−1` index arithmetic. The `\sum`-menu class has 0 corpus Contract entries at
  all. 0 flips; 5 fail-closed pins added.
- **Stackelberg parser (Task 12):** `_preprocess_stackelberg_sum_bounds` handles
  `\sum_{i∈S}` / `\sum_{a≤i≤b}` via own-term isolation + `require_br_match`.
  0 flips; 22 tests. One fix round: a paren-truncation bug produced a false
  entry-specific VERIFIED on a crafted input; caught by review, fixed with a
  conservative bail (`(` in summand → `None`).
- **Function-call notation (Task 13):** helper written, then **reverted** after
  review found it unsound (emitted names fragment on `parse_latex`; a no-op guard
  path gave a latent false VERIFIED). The existing
  `_demote_stray_function_calls` / `_insert_implicit_multiplication` /
  `_strip_call_syntax` already cover every corpus `f(arg)` case. Shipped: a
  comment + 5 characterization pins.
- **Track 3 transcendental (Task 14):** box search extended with
  `max_ic_regret_over_box` (rigorous δ-bounded IC-regret upper bound) + multi-symbol
  suppression. `Kang2019contract_mobile` (the only transcendental Contract corpus
  entry) has 9/11 free vars → box-intractable, honestly stays UNKNOWN.
  `iiot_log_linear` is an Architect **eval benchmark**, not a corpus entry —
  `verify()` never touches it. Its offline δ-regret ≈ 69.06 is a loose
  over-estimate over the fully-decoupled box (true menu regret 0).

And the AST / synthesis work (Tasks 5–10) is **off the corpus path** by
construction: `verify(entry)` is the corpus API and is untouched;
`verify_from_ast` runs only in the Architect loop.

## What each task shipped (capability, not corpus numbers)

| Task | Shipped |
|---|---|
| 1 | Branch + baseline capture (`phase3-baseline.md`), 204p/3xf. |
| 2 | `verify_vcg_dsic` encodes weighted-welfare-max + Clarke pivot; `_argmax_welfare_weights` extractor **fails closed** (symbolic / greek / subtraction / ratio / power / wrong-count → UNKNOWN). 1 fix round. |
| 3 | ProportionalShare (`_PROP_RE`, 1 corpus entry, no DSIC claim) → early honest UNKNOWN in `verify_vcg_dsic`; verify()-level stays VERIFIED_SHAPE. |
| 4 | `VerificationResult.grid_bounded` flag + `print_summary` sub-line; reserve-price encoded in a test fixture (encoder unchanged, brief-sanctioned). |
| 5–7 | `track{2,3,4}_check_from_sympy` are now SymPy-native (take parsed exprs, not `entry` dicts). Behavior-preserving; snapshot-locked. |
| 8 | `verify_from_ast` does **real** multi-track routing via `_classify_ast` — Track 2/3/4 seams, not everything funnelled through Track-1 core. 3 tests pin `r.track`. |
| 9 | `Alloc` AST node union (`AllocHighest` / `AllocTopK` / `AllocWeightedWelfare`) + `Mechanism.allocation`; `validate_alloc`; serializer emits Clarke-pivot payment from the node. |
| 10 | Synthesis mode sets `m.allocation` instead of injecting `meta["allocation_rule_latex"]`. `verify_from_ast(synthesized VCG)` → genuine entry-specific VERIFIED with a 9-profile grid proof. |
| 11 | Contract parser widening investigated; 3 target classes each dead-end. 0 flips, 5 fail-closed pins. |
| 12 | `_preprocess_stackelberg_sum_bounds` (`\sum_{i∈S}` / `\sum_{a≤i≤b}`) + `require_br_match`. 0 flips, 22 tests, 1 fix round. |
| 13 | Function-call helper written then reverted (unsound); existing helpers already cover the corpus. 5 characterization pins + comment. |
| 14 | Track 3 box search + `max_ic_regret_over_box` (rigorous δ-bounded upper bound) + multi-symbol suppression; Architect prompt emits `Func("ln"/"exp")` for log/exp intake. 7 tests. |

## Suite

204 passed / 3 xfailed (main) → **262 passed / 3 xfailed / 0 failed**. ~58 tests
added across Phase 3 — all widening pins, regression locks, and fail-closed
characterization. No corpus test changed.

## Explicitly NOT this round

- `VERIFIED_TEMPLATE` → `UNKNOWN` fail-close pass (deferred by explicit decision —
  it is the honesty pass, ~61 entries would drop; separate round).
- Phase 4 (coalition / Shapley, k ≤ 3).
- The live flagged `run_eval` needed to flip `ARCHITECT_AST_VERIFY` on
  (API-blocked infra).
