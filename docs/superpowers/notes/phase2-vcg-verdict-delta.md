# Phase 2 VCG Verdict Delta (After Task 5)

Captured 2026-08-30, branch `phase2-vcg-real-check`. Diff of the per-VCG-entry
verdict vs. the Task 1 baseline (`phase2-vcg-baseline.md`) after wiring
`verify_vcg` to dispatch to the real finite-grid Z3 DSIC + IR check
(`verify_vcg_dsic`) first, with the old regex/template path demoted to
`VERIFIED_SHAPE`.

## What changed

`verify_vcg(entry)` now:

1. keeps the identically-zero-payment soundness gate first (unchanged);
2. calls `verify_vcg_dsic(entry)` — returns it iff its verdict is `VERIFIED`
   or `COUNTEREXAMPLE`;
3. otherwise (`UNKNOWN` / `UNSUPPORTED`) falls through to the regex path
   (`_classify_vcg_payment` → `_vcg_check_core`) and **post-maps** any
   `VERIFIED` / `VERIFIED_TEMPLATE` success to `VERIFIED_SHAPE`
   (`entry_specific` forced `False`).

Dispatcher wiring choice: **post-map the verdict in `verify_vcg`** (smaller,
safer diff — `_vcg_check_core` keeps its exact signature so the Approach C AST
caller `architect/ast_verify.py::verify_from_ast` is untouched until Phase 2
Task 7).

Result on the current corpus: **every** VCG entry fails the real DSIC check
closed (allocation/payment LaTeX does not parse into an encodable spec, or is
absent) and falls through to `VERIFIED_SHAPE`. Zero real DSIC proofs and zero
real counterexamples are produced from the corpus at this stage — the parser
coverage that turns these into real proofs lands in later Phase 2 work. This
task only wires the dispatcher and records the honest downgrade.

## Per-entry delta (all 33 VCG entries changed)

| paper_id | before | after | reason |
|----------|--------|-------|--------|
| 2404_13841 | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — payment formula an unparsed raw string |
| 2504_05563 | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — unencodable combo (ArgmaxWelfare objective raw string) |
| 3626307_3626311 | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — unencodable combo (ArgmaxWelfare objective raw string) |
| Ahmed2023frimfl | VERIFIED_TEMPLATE | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED_TEMPLATE — regex only); DSIC check UNKNOWN — allocation unparseable |
| Batool2022fl_mab | VERIFIED_TEMPLATE | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED_TEMPLATE — regex only); DSIC check UNKNOWN — allocation unparseable |
| Cheng2022uav | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — allocation unparseable |
| Cong2020vcg | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — allocation unparseable |
| Cui2024auction_market | VERIFIED_TEMPLATE | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED_TEMPLATE — regex only); DSIC check UNKNOWN — payment formula an unparsed raw string |
| Deng2020fmore_auction | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — allocation unparseable |
| GPS2023afl_recruit | VERIFIED_TEMPLATE | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED_TEMPLATE — regex only); DSIC check UNKNOWN — allocation unparseable (TopK.k symbolic/unknown) |
| Haupt2021auctions | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — allocation unparseable |
| Jiao2019auto_auction | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — payment formula an unparsed raw string |
| Jin2023bara_budget | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — payment formula an unparsed raw string |
| Le2021cellular_auction | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — unencodable combo (ArgmaxWelfare objective raw string) |
| Lim2020edge_collab | VERIFIED_TEMPLATE | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED_TEMPLATE — regex only); DSIC check UNSUPPORTED — no allocation/payment LaTeX |
| Liu2023reverse_auction | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — unencodable combo (ArgmaxWelfare objective raw string) |
| Lu2021cluster_auction | VERIFIED_TEMPLATE | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED_TEMPLATE — regex only); DSIC check UNKNOWN — allocation unparseable |
| Mai2022double_auction | VERIFIED_TEMPLATE | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED_TEMPLATE — regex only); DSIC check UNKNOWN — allocation unparseable |
| Model2024trading_fl | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — allocation unparseable |
| Ng2020uav_auction_coalition | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — unencodable combo (ArgmaxWelfare objective raw string) |
| Peng2023auction_medical | VERIFIED_TEMPLATE | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED_TEMPLATE — regex only); DSIC check UNSUPPORTED — no allocation/payment LaTeX |
| Seo2021sdn_fl | VERIFIED_TEMPLATE | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED_TEMPLATE — regex only); DSIC check UNKNOWN — allocation unparseable |
| Seo2022noniid_auction | VERIFIED_TEMPLATE | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED_TEMPLATE — regex only); DSIC check UNKNOWN — allocation unparseable |
| Tan2023hire | VERIFIED_TEMPLATE | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED_TEMPLATE — regex only); DSIC check UNKNOWN — payment formula an unparsed raw string |
| Tan2025longterm | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — unencodable combo (ArgmaxWelfare objective raw string) |
| Wei2024truthful_bandit | VERIFIED_TEMPLATE | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED_TEMPLATE — regex only); DSIC check UNKNOWN — allocation unparseable |
| Xia2026privacy_mfg | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — allocation unparseable (TopK.k symbolic/unknown) |
| Xiang2025esr_mhfl | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — unencodable combo (ArgmaxWelfare objective raw string) |
| Yang2023buyers_market | VERIFIED_TEMPLATE | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED_TEMPLATE — regex only); DSIC check UNKNOWN — allocation unparseable |
| Zhang2022expost_auction | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — allocation unparseable |
| Zhang2022online | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — allocation unparseable |
| Zhang2024auction_comm | VERIFIED | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED — regex only); DSIC check UNKNOWN — unencodable combo (allocation spec ArgmaxWelfare not encodable) |
| Zheng2023fl_market | VERIFIED_TEMPLATE | VERIFIED_SHAPE | now VERIFIED_SHAPE (was VERIFIED_TEMPLATE — regex only); DSIC check UNKNOWN — allocation unparseable |

### VCG verdict distribution

| verdict | before | after |
|---------|--------|-------|
| VERIFIED (real DSIC, entry-specific) | 19 (regex form-confirmed) | 0 |
| VERIFIED_TEMPLATE | 14 | 0 |
| VERIFIED_SHAPE | 0 | 33 |
| COUNTEREXAMPLE | 0 | 0 |
| UNKNOWN | 0 | 0 |
| **total** | **33** | **33** |

## New corpus totals (`PYTHONPATH=src python -m verifier corpus.json`, 105 entries)

```
  VERIFIED           (6)      <- was 25  (19 VCG regex form-confirmed demoted to VERIFIED_SHAPE)
  VERIFIED_TEMPLATE  (59)     <- was 73  (14 VCG template demoted to VERIFIED_SHAPE)
  VERIFIED_SHAPE     (33)     <- new
  UNKNOWN            (2)      <- unchanged (both non-VCG: Kang2019contract_mobile, Tian2021contract)
  UNSUPPORTED        (5)      <- unchanged
  |- Passed (65 total, 6 entry-specific):
  |   Contract entry-specific (LaTeX utility):   5     FROZEN, unchanged
  |   Contract template (linear-cost model):     31    FROZEN, unchanged
  |   SOS certificate (Track 2, poly degree>=2): 4     FROZEN, unchanged
  |   Bayesian IC (Track 4, symbolic integral):  1     FROZEN, unchanged
  \- Stackelberg equilibrium IR (NOT DSIC): 29 (1 entry-specific, 28 template-only)   FROZEN, unchanged
  dReal delta-verified (Track 3, transcendental): 1    FROZEN, unchanged
  .  VCG regex-shape only (not a proof): 33
```

Non-VCG frozen gate: **all unmoved** — `verify_vcg_dsic` does not leak into any
non-VCG path.

## Test suite

`PYTHONPATH=src pytest -q` -> **190 passed, 3 xfailed, 0 failed**
(xfailed dropped 5 -> 3: the two VCG template-fallback holes moved to the
hard `BROKEN` list — they now honestly pass, returning `VERIFIED_SHAPE`, a
documented non-proof, instead of `VERIFIED`/`VERIFIED_TEMPLATE`).

`PYTHONPATH=src python tools/validate.py corpus.json` -> **185/185 valid**.

## VCG eval (Phase 2) — infra-blocked, deferred

The roadmap "done when" for Phase 2 is: ≥2 of the 4 VCG eval benchmarks
(`myerson_single_item`, `vcg_redistribution`, `vcg_clarke_pivot`,
`vcg_cavallo_redistribution`) reach entry-specific `VERIFIED` via
`verify_vcg_dsic` through the live loop.

**Not measured 2026-08-30.** Two consecutive fresh `python -m architect.eval.run_eval`
runs against `openai/gpt-oss-120b` (NVIDIA endpoint) hung — 0% CPU, empty log,
killed after 25 min each. `ARCHITECT_LLM_TIMEOUT_S=120` did not bound the stall.
Infra (unresponsive endpoint), not a Phase 2 code problem. `docs/eval-results.md`
still holds the pre-Phase-2 (2026-08-29) run — regenerate it when the API is
healthy: `run_eval` with a working model, then fill the 4 VCG rows here.

**What IS verified offline (no API):**
- `tests/verifier/test_vcg_dsic.py` — `verify_vcg_dsic` produces real DSIC
  proofs (single-item Clarke, second-price+reserve → `VERIFIED`), real
  counterexamples (non-pivotal payment, first-price, wrong-allocation Clarke →
  `COUNTEREXAMPLE`), and fails closed (multi-attribute / argmax-welfare /
  oversize grid / `n<2` → `UNKNOWN`).
- `tests/architect/test_synthesize_vcg.py` — Synthesis mode produces a
  highest-bidder + Clarke-pivot mechanism (= Vickrey) that `verify_vcg_dsic`
  then certifies `VERIFIED`. The constrained-generation → real-certificate path
  is proven end to end without the LLM.

So the Phase 2 mechanism works; only the through-the-live-loop benchmark count
is pending an API window.
