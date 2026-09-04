# Round R5 — Coalition / Shapley Track — Delta

**Landed 2026-09-05.** Branch `round-R5-coalition-track`, 7 commits off `main` @ `773d417`
(`a78c800` baseline, `a8ccb87` Task 2 parse + Shapley identity, `152fdba` Task 3 Tier B,
`b355a9d` Task 4 Tier A + `verify_coalition` entry point, `ae9ef84` Task 5 wiring + notes,
`acc5939` Task 5 fix: `_classify_ast` Shapley -> track 5, `35d6388` Task 6 sweep + 4 MANUAL
diagnoses).
Plan: `docs/superpowers/plans/2026-09-05-R5-coalition-track.md`.
Merge commit `<merge-sha, filled by controller>`.

## Shapley slice (4 entries) — before / after

| Verdict | Baseline | After R5 | Δ |
|---|---|---|---|
| VERIFIED (entry-specific) | 0 | 0 | — |
| MANUAL | 0 | 4 | +4 |
| UNSUPPORTED | 4 | 0 | −4 |

## What shipped

- `src/tracks/track_coalition.py` — two-tier `verify_coalition` (`k <= 3`):
  - **Tier A** — structural Shapley-formula identity check. sympy `parse_latex` could
    not handle the factorial `\sum`, so Tier A uses a regex structural match against the
    Shapley-value shape with `\binom` / `\hat` / `K` rejection guards (a `K`-normalized or
    binomial-weighted formula is not exact Shapley -> rejected).
  - **Tier B** — enumerated core / IR / payment check over all `2^k` coalitions, runs only
    when a concrete finite `v(S)` is transcribed into `mechanism.coalition_values`.
  - Wired into `verify_shapley` (was an unconditional `UNSUPPORTED` stub), `_classify_ast`
    (`Shapley` category -> track 5), and `verify_from_ast` (`Coalition` branch).
  - 15 unit tests in `tests/tracks/test_coalition.py`.

## 0 flips — all 4 diagnosed MANUAL

The honest floor. No numeric `v(S)` instance exists in any of the four papers' PDFs, so
Tier B never had ground to run — the 3 well-formed entries (`2502_08248`, `2605_11889`,
`2606_18384`) stay `MANUAL` via Tier A, and `2405_13879` is mis-categorized (no `v(S)` /
no Shapley value in the paper at all). Per-entry:

- **`2405_13879`** — mis-categorized penalty-based free-riding truthfulness mechanism; no
  `v(S)` and no Shapley value anywhere in the paper. Human task: re-categorize (not a
  coalition track).
- **`2502_08248`** — standard Shapley formula confirmed by Tier A, but the paper gives no
  concrete numeric max-flow instance to run Tier B against.
- **`2605_11889`** — characteristic function is a transcendental Bayesian log-likelihood
  value; Tier A passes on the formula, no numeric instance for Tier B.
- **`2606_18384`** — the stated formula is a `K`-normalized OR-approximation (not exact
  Shapley, rejected by Tier A's guard) over an opaque model-utility value.

## R6 handoff

- **`2502_08248`** — closest to reclaimable. If a human constructs a concrete capacity
  network from the paper's model, Tier B runs as-is against the transcribed `v(S)`.
- **`2605_11889`, `2606_18384`** — need analytic work or the papers' own numeric runs
  before Tier B has anything to enumerate.
- **`2405_13879`** — needs re-categorization, not a coalition track.
