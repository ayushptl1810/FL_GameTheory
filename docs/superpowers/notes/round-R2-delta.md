# Round R2 — VCG Corpus Sweep — Delta

**Landed 2026-09-03.** Branch `round-R2-vcg-sweep`, 16 commits off `main` @ `937dc43`.
Plan: `docs/superpowers/plans/2026-09-02-zero-unknown-r2-r3-corpus-sweep.md`.

## VCG slice (33 entries) — before / after

| Verdict | Baseline (`main`) | After R2 | Δ |
|---|---|---|---|
| VERIFIED (entry-specific) | 0 | **3** | +3 |
| VERIFIED_SHAPE | 33 | 10 | −23 |
| MANUAL (diagnosed) | 0 | **20** | +20 |
| UNKNOWN | 0 | **0** | — |
| COUNTEREXAMPLE | 0 | 0 | — |

**VCG UNKNOWN = 0.** Monotone gate `PASS` — every moved entry `improved`
(`VERIFIED_SHAPE → VERIFIED` ×3, `VERIFIED_SHAPE → MANUAL` ×20). No regression.
Non-VCG slice (Contract/Stackelberg/Shapley) byte-identical: 6 VERIFIED /
59 VERIFIED_TEMPLATE / 2 UNKNOWN / 5 UNSUPPORTED unchanged. Full suite
381 passed / 1 skipped / 3 xfailed / 0 failed.

## What R2 built (shared tooling — reused by R3a/R3b)

| Deliverable | Commit |
|---|---|
| `MANUAL` added to the `Verdict` literal | `18f1cae` |
| `verify()` short-circuits on `verdict_override:"MANUAL"` (deterministic, no API key) | `dec9971` |
| `print_summary` MANUAL bucket + `MANUAL-backlog.md` coverage warning | `3e7452e` |
| `scripts/round_gate.py` — monotone verdict-movement gate vs a slice baseline | `278c47e` |
| `write_manual_diagnosis` + `append_backlog_paragraph` (rejects reason-less MANUAL) | `7c53d3e` |
| `architect.llm` auto-loads `.env` on import (`override=False`) | `b016b63` |
| `scripts/snapshot_verdicts.py` — slice-aware per-entry verdict baseline | `d1f2d42` |

## Unscheduled R1-fix work (the formalizer did not work out of the box)

**`.env` model was dead.** NVIDIA end-of-lifed `meta/llama-3.2-90b-vision-instruct`
on 2026-08-26; it still lists in `/v1/models` but the backend hangs with 0 bytes
forever. Switched to `openai/gpt-oss-120b` (`.env`, gitignored — not in the branch
diff). Root-caused with raw `curl`, zero Python.

**The R1 full-AST formalizer produces 0 valid ASTs for the VCG corpus.** With any
model, the LLM puts a placeholder `Sym{name:"ic"}` in the `Mechanism.ic` field
instead of an IC expression, and uses multi-letter symbol names the LaTeX
serializer rejects. `FORMALIZE_SYSTEM_PROMPT` has no worked example.

**Replacement for VCG: an allocation-classifier path** (`9355cac`, `e99bcf6`).
`classify_vcg_allocation` asks the LLM only to classify `allocation_rule_latex`
into `AllocHighest` / `AllocTopK{k}` / `AllocWeightedWelfare{weights}` / `null`;
`formalize_vcg_entry` builds a `Mechanism` skeleton with that typed node + the
corpus's real payment/utility LaTeX in `meta`; `verify_from_ast` runs the real
finite-grid DSIC proof. Contract/Stackelberg still take the old path (Tasks 11/14
will need their own).

**Critical bug found in whole-branch review + fixed** (`b26ee6f`, `800ef6a`,
`abd1a01`). A typed allocation node made `serialize.render()` OVERWRITE
`payment_rule_latex` with the canonical Clarke pivot for that node
(`AllocHighest → p_i = max_{j≠i} b_j`), so the grid proved the textbook
second-price mechanism regardless of what the paper actually pays. First sweep's
8 "flips" were caught only by the Task 9 hand-check (4 held, 4 reverted). Fix:
(1) `parse_payment` now reads welfare-difference Clarke pivots
(`S(x*)−S(z*)`, `r(x*)−Σ_{k≠i}c_k`) — but ONLY for single-item welfare-max
allocations, where the Groves externality is provably the second price;
fail-closed for TopK / non-unit weights / opaque. (2) `_vcg_from_ast` now
prefers the paper's real `meta["payment_rule_latex"]` over the rendered
canonical. (3) Regression test: `p_i = 42 b_i + 7` + `AllocHighest` is NOT
`VERIFIED`. Corpus re-swept clean under the fix.

## The 3 real VERIFIED (cross-checked)

Each: welfare-maximizing `argmax` allocation + a welfare-difference Clarke pivot,
now verified against the paper's ACTUAL payment (not a substitute) on the k=3
9-profile grid; cross-checked by hand against Groves 1973 / Clarke 1971.
See `round-R2-new-verified.md`.

- **Cong2020vcg** — `x* = argmax S(x,γ̂)`, `p_i = S(x*,γ̂) − S(z*,γ̂)`.
- **3626307_3626311** — `x_i = argmax Σ v_i − c_i`, `p_i = r(x*) − Σ_{k≠i} c(x_k*,γ̂_k)`.
- **2504_05563** — `W* ∈ argmax[v(W) − ĉf(W)]`, `p_i = v_i(W) − Σ_{k≠i} c_k f_k(W*)`.

## MANUAL catalogue (20 entries — feeds R4) — see `MANUAL-backlog.md`

Grouped by the ceiling that blocks a grid-decidable proof:

| Ceiling | Entries |
|---|---|
| budget-constrained greedy / knapsack allocation (out of {argmax, top-k, weighted-welfare}) | Jiao2019auto_auction, Jin2023bara_budget, Lu2021cluster_auction, Zheng2023fl_market, 2404_13841, Ahmed2023frimfl |
| non-polynomial / transcendental payment (exponential, log-det) Z3 cannot linearize | Seo2021sdn_fl, Seo2022noniid_auction, Wei2024truthful_bandit, Haupt2021auctions |
| RL-policy / opaque-algorithm allocation, no closed form | Model2024trading_fl, Lim2020edge_collab, Peng2023auction_medical, Tan2023hire |
| continuous bid space with no valid discretization | Yang2023buyers_market, Zhang2022online, Cui2024auction_market |
| payment not a Clarke pivot (first-price product / own-cost subtraction / budget cap) | GPS2023afl_recruit, Xia2026privacy_mfg, Zhang2024auction_comm |

**R4 widening candidates** (ceiling hit by ≥2 entries): budget-greedy →
critical-value / monotone-threshold encoding (6 entries); transcendental payment
→ finite lookup-table discretization (4 entries); opaque-allocation → monotonicity
argument or empirical bound (4 entries).

## R6 candidates (10 entries — formalization miss, left at VERIFIED_SHAPE)

Their allocation genuinely is (or reduces to) a grid-decidable argmax with a
Groves-shaped payment; the sweep's parser or classifier failed on surface syntax,
not substance. **Not diagnosed MANUAL.** See `round-R2-new-verified.md` for the
per-entry gap. Highlights:

- **≥4 are classifier flakiness on the canonical Groves form** (Tan2025longterm,
  Xiang2025esr_mhfl, Le2021cellular_auction, Liu2023reverse_auction) — R6 should
  add a deterministic regex/sympy pre-pass for the canonical form before the LLM
  call.
- Le2021 / Liu2023 / Zhang2022expost have subset-valued `argmax_{S⊆N}`
  allocations — the AST has no set-valued allocation node (a tooling gap).
- Cheng2022uav has a 3-index `x_{l,m,n}` allocation — needs a combinatorial
  encoding.
- Deng2020 / Mai2022 / Batool2022 have extraction failures (allocation LaTeX is
  an opaque cases block, an aggregate utility definition, or a score with no
  stated argmax).

## Deferred (R4 cleanup / final honesty pass)

- `z3_verdict` corpus field is stale/disused — does not match live `verify()`.
- `parse_payment` trusts the classifier's `AllocHighest` label without
  re-checking single-item-ness — a multi-item mechanism the classifier mislabels
  would slip through. The classifier is the trust boundary.
- Unused `import pytest` in 4 R2 test files; `snapshot_verdicts` recomputes counts
  3×; `round_gate.parse_baseline` has no unit test; `print_summary` warning
  hardcodes the backlog basename; `--dry-run` writes a stray `formalize-run-*.md`
  (pre-existing R1 bug).

## Honest assessment

R2's headline number is small: **3 of 33 VCG entries got a real entry-specific
proof.** 20 are genuine ceilings (log-det objectives, RL policies, budget
knapsacks, transcendental payments — R4 mini-specs). 10 are formalization misses
R6 should reclaim. The VCG `verify_from_ast` path, billed by the spec as "the most
mature," verifies only clean single-item welfare-max Groves mechanisms; the FL
auction literature is mostly not that. R3 (Contract + Stackelberg) will hit the
same formalizer wall and need its own per-category classifier path.
