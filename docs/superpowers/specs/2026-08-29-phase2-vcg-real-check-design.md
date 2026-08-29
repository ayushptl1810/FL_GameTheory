# Phase 2 — Real VCG Check + Constrained Generation (design)

**Date:** 2026-08-29
**Status:** Design. Awaiting review, then writing-plans.
**Parent:** `2026-08-29-verifier-proper-checks.md` (Phase 2)
**Scope calls (2026-08-29):** 2a + 2b in one plan; VCG fragment = **broad**
(single-item, multi-unit demand, multi-attribute bids) — with the honest
caveat below.

---

## Problem

The VCG track does no real entry-specific verification: `verify_vcg` /
`_vcg_check_core` regex-match the payment-rule LaTeX against known Clarke /
marginal-welfare / critical-bid shapes and return a fixed template verdict.
A Clarke-shaped payment with a *wrong allocation* still passes as entry-specific
`VERIFIED` (`vcg_clarke_shaped_payment_wrong_allocation`, currently `xfail`).
The 2026-08-29 eval failed 4/4 VCG benchmarks. The corpus's "19 form-confirmed
VCG" are regex matches, not proofs.

## 2a — `verify_vcg_dsic`: a real finite-grid Z3 DSIC check

**Encoding.** For an entry with `n` bidders, `m` value attributes each, and a
per-attribute type grid of `k` points:

- Types/bids live on the grid: `v_{i,a} ∈ {g_1..g_k}`, bid `b_{i,a}` likewise.
- Allocation `x(b)` — parsed from `allocation_rule_latex`:
  - closed form (`x_i = 1 if b_i = max_j b_j`, top-k, proportional-share) →
    encode directly;
  - stated as an optimization (`x = argmax Σ …`) → encode "the chosen outcome
    maximizes the stated objective over the finite outcome set", with ties
    broken by a fixed rule (lowest index) that the check also assumes of the
    mechanism.
  - unparseable → `UNSUPPORTED` (no silent template pass).
- Payment `p(b)` — parsed from `payment_rule_latex`; for a Clarke/pivot form,
  `p_i = W_{-i}(b_{-i}) − Σ_{j≠i} v_j(x(b))` computed from the *same* encoded
  allocation, not from the LaTeX shape.
- Utility `u_i = Σ_a v_{i,a}·x_{i,a}(b) − p_i(b)`.
- **DSIC obligation:** `∀ i, ∀ b_i' on the grid: u_i(b_i = v_i, b_{-i}) ≥
  u_i(b_i', b_{-i})` for all `b_{-i}` on the grid. Z3 `∀`-quantified over
  `v`, `b_{-i}`; `b_i'` enumerated (grid is finite).
- **IR obligation:** `∀: u_i(truthful) ≥ 0`.
- `UNSAT` of the negation → `VERIFIED` (entry_specific=True), exact **on the
  grid** (stated as such). `SAT` → `COUNTEREXAMPLE` with the witness profile +
  gain. Grid size `k^(n·m)` over a budget cap → `UNKNOWN` (record the blown
  dimension).

**Broad-fragment caveat (must be in the writeup).** For **multi-attribute
deterministic** mechanisms, Task.md's impossibility table already records that a
deterministic truthful mechanism with finite approximation does not exist in
general (multi-parameter impossibility). `verify_vcg_dsic` will therefore
legitimately return `COUNTEREXAMPLE` or `UNSUPPORTED` for many multi-attribute
entries — that is the correct answer, not a gap. Single-item and multi-unit
single-attribute are where `VERIFIED` is reachable.

**Dispatcher.** `verify_vcg` tries `verify_vcg_dsic` first. On its `UNKNOWN` /
unparseable-allocation, fall back to the old regex path, whose verdict is
**renamed `VERIFIED_SHAPE`** (a new 6th verdict value, or a flag on
`VerificationResult` — decided in the plan) — explicitly *not* a proof. Delete
the regex path entirely once 2a covers the corpus VCG set.

## 2b — Constrained VCG generation (Synthesis mode)

Stop letting the LLM freehand the VCG payment. In Synthesis mode for VCG:

- Payment is **fixed** to the Clarke-pivot form derived from the allocation.
- The search (Z3 solve-mode or bounded grid) chooses only:
  - the **allocation rule** from a small menu (highest-bidder, top-k,
    proportional, weighted-welfare-max), and
  - per-agent **weights `w_i ≥ 0`** and outcome **boosts `γ(o)`** — the
    affine-maximizer family `Σ w_i·v_i(o) + γ(o)`.
- Roberts: on unrestricted domains this *is* the complete truthful family →
  principled search. On the restricted FL domains, the writeup says "exhaustive
  within the affine-maximizer class" (wording already in `Task.md`).
- Output is validated by `verify_vcg_dsic` (2a) before the loop accepts it.

## AST path (closes an Approach C deferred item)

Give `verify_vcg_dsic` an AST/SymPy seam so `verify_from_ast`'s VCG branch calls
the **real** check instead of the current honest-but-blind `VERIFIED_TEMPLATE`.
Once this lands, the VCG AST path can return real `entry_specific=True VERIFIED`
(the `entry_specific=False` stopgap from Approach C Task 8 is removed).

## Corpus regression — this MOVES the numbers

Unlike Approach C, Phase 2 is *expected* to change the frozen
`VERIFIED 25 / VERIFIED_TEMPLATE 73 / UNKNOWN 2 / UNSUPPORTED 5`. The VCG
entry-specific count (currently 19 regex "form-confirmed") will drop, some
entries move to `COUNTEREXAMPLE` / `UNKNOWN` / `UNSUPPORTED`, and a few
genuinely-Clarke entries may reach real `VERIFIED`.

**New gate:** produce a before/after table; **every VCG entry whose verdict
changes gets a one-line reason** (real proof / real counterexample / grid too
big / allocation unparseable / multi-attribute impossible). Non-VCG verdicts
(Contract 5/31, Stackelberg 1/29, Track 2/3/4) stay frozen — those are the
regression gate for "2a didn't leak".

## Tests

- Un-`xfail` `vcg_clarke_shaped_payment_wrong_allocation` → must now return
  `COUNTEREXAMPLE` (real deviation: low-value bidder overreports, wins, Clarke
  payment doesn't cover the lie because the allocation was wrong).
- New adversarial: correct single-item Clarke → `VERIFIED` entry-specific;
  non-pivotal payment (`p_i = b_i/2`) → `COUNTEREXAMPLE`; second-price with
  reserve done right → `VERIFIED`; multi-attribute deterministic → `UNSUPPORTED`
  citing the impossibility.
- 2b: a synthesis run for a single-item benchmark produces a mechanism that
  `verify_vcg_dsic` then certifies `VERIFIED` — end to end.
- Eval: `run_eval` — ≥2 of the 4 VCG benchmarks reach entry-specific `VERIFIED`
  with a Z3 certificate (the roadmap's "done when").

## Risks

- **Grid blowup.** `k^(n·m)` — a 3-bidder 2-attribute entry at `k=5` is 5^6 ≈
  15k profiles per deviation check. Budget cap + `UNKNOWN` fallback; start `k`
  small (3–4) and raise only where a benchmark needs it.
- **Allocation parsing.** `argmax`/optimization-form allocations are the hard
  case; the "chosen outcome maximizes stated objective over finite set"
  encoding is the mitigation, but a mis-parse could produce a wrong
  `COUNTEREXAMPLE`. Cross-check: if the derived allocation disagrees with an
  entry's stated `allocation_rule_latex` on a sampled profile, return
  `UNKNOWN`, not `COUNTEREXAMPLE` (same fail-closed discipline as the
  Stackelberg best-response cross-check).
- **`VERIFIED_SHAPE` as a new verdict value** touches `finalize_verdict`, the
  summary printer, `z3_verdict` schema, and any consumer that enums the
  verdict — plan it as its own task with its own regression check.
