# Spec — Novelty Hardening for the Architect + Verifier Loop

**Date:** 2026-08-29
**Status:** Active. Targeted for the current round.
**Parent:** `2026-08-28-architect-cegis-loop-design.md`
**Trigger:** External-scope review (2026-08-29) found the loop works but the
research claims outrun what the system demonstrates, and the closest prior work
(LegoNE 2508.11874; Mittelmann et al., *Artif. Intell.* 2024; the LLM→SMT
counterexample-loop line — LEMUR / LaM4Inv / LORIS / 2508.00419) is close enough
that "we closed a CEGIS loop over an FL corpus" reads as incremental on its own.

This spec covers only work that needs **no new research result** — engineering,
evaluation, and honest claim-scoping. The research bets (a novel certified
mechanism, transcendental IC, collusion IC) live in
`2026-08-28-ast-native-verifier-future-scope.md`.

---

## Problem statement

Concrete gaps from the review, each independently fixable this round:

1. **Family reframing.** The loop's only success condition is
   `VERIFIED ∧ entry_specific`. It reaches that by reframing almost any input
   into whichever family it can certify fastest (Stackelberg follower-effort or a
   linear Contract menu). In the first eval, only `hierarchical_edge` matched its
   expected family. So "free text in → verified mechanism out" is really
   "free text in → verified *toy in a convenient family* out." The headline claim
   is not honestly supported.

2. **No baselines.** RegretNet and Liu et al. (2502.12203) on the FL benchmarks
   are still unrun. "4/5 VERIFIED, IC-regret 0" has nothing to compare against —
   a hardcoded "always emit follower-effort" scores identically.

3. **Verifier soundness is asserted, not measured.** Task.md's own history shows
   template tautologies (`p²/2 ≥ 0`) once passed as `VERIFIED` for all 62
   Stackelberg entries. There is no adversarial suite of known-broken mechanisms
   the verifier must *reject*, and no reported false-`VERIFIED` rate.

4. **Eval is a demo.** 5 benchmarks, one model (`gpt-oss-120b`), n=5; the
   "convergence" study is 10 runs of a single prompt. No seed variance, no
   ablations, no second model.

5. **Claims exceed delivery.** "produces a proof certificate or a counterexample
   for *any* proposed mechanism structure" (Key Differentiation, Task.md) is
   contradicted by the system's own numbers: 25/105 entry-specific `VERIFIED` on
   the *known-good* corpus; Tracks 2–4 fire ~7 times total. The paper framing
   needs to match the discrete-type / linear-Stackelberg fragment the verifier
   actually covers.

6. **Prior-art positioning is missing.** No related-work treatment of LegoNE,
   Mittelmann et al., the SMT-in-social-choice line (Brandl/Brandt; Barthe et
   al. 1502.04052), or the LLM+SMT invariant-synthesis loop papers.

---

## Scope — this round

### Task 1 — Family fidelity: decide, then enforce or own it

Pick **one** and implement it. Do not ship the current middle ground.

**Option A (constrain).** Router/prompt hard-bind the proposed family to the
intake's `expected_family`. If the loop cannot reach `VERIFIED` in that family
within the repair budget, it FAILs *in that family* — it may not silently switch
to Stackelberg follower-effort.
- `src/architect/loop.py`: pass `expected_family` into the propose prompt as a
  hard constraint; reject a proposal whose serialized category ≠ `expected_family`
  with a repair hint (counts against the budget).
- `src/architect/architect.py` / mode router: Synthesis/Hybrid stay available but
  only *within* the target family.
- Eval output gains a per-family `verified-in-expected-family` rate. A low number
  here is a **publishable finding** about what is automatically verifiable in FL,
  not a failure to hide.

**Option B (reframe the contribution).** Rename the contribution to
"cheapest-to-certify IC mechanism for a given FL setting." Then Task 1 is: add a
metric for how far the emitted family sits from `expected_family`, plus an
argument (or experiment) that the emitted mechanism is still Pareto-useful vs.
the hand design the setting's literature uses.

**Recommendation:** Option A. Less writing, cleaner claim, and the honest failure
rates are themselves a result.

**Done when:** eval report shows a `family_match` column and either a
target-family verify rate (A) or a family-distance metric + usefulness argument
(B); Task.md's "Three Modes" and "What is left" sections updated to match.

### Task 2 — Baselines on the FL benchmarks

- `src/architect/eval/baselines/regretnet.py` — RegretNet (or GemNet) trained per
  benchmark; report IC-regret, revenue/welfare.
- `src/architect/eval/baselines/liu_amd_llm.py` — port or reimplement the
  2502.12203 fix-process pipeline for the auction-shaped benchmarks
  (`myerson_single_item`, `vcg_redistribution`). Check for released code first
  (Research & Reuse).
- Shared eval table row per method: `{verified/valid, IC-regret, welfare or
  revenue, wall-clock}` on the identical benchmark set.
- A trivial control baseline ("always emit the textbook follower-effort
  mechanism") goes in the table too — it should expose how much the loop adds.

**Done when:** `python -m architect.eval.run_eval --with-baselines` emits a
combined table; `docs/eval-results.md` has it.

### Task 3 — Adversarial verifier soundness suite

- `tests/verifier/test_adversarial_soundness.py`: ≥20 mechanisms that are
  provably NOT IC/IR (reversed type order with a real profitable deviation,
  under-priced menu item, VCG with a non-pivotal payment, Stackelberg with IR
  violated at the true optimum, …). Each must return `COUNTEREXAMPLE` or
  `UNKNOWN` / `UNSUPPORTED` — **never** `VERIFIED` / `VERIFIED_TEMPLATE`.
- `src/architect/eval/soundness_report.py`: runs the suite, prints
  false-`VERIFIED` rate and per-track breakdown. Target: 0 false `VERIFIED`.
- Wire into CI alongside the existing 109-test suite.

**Done when:** report exists, false-`VERIFIED` rate is 0 (or every exception is
documented as a known unsound path with a gate), and Task.md cites the number.

### Task 4 — Eval rigor

- **Second model:** re-run the full eval with one stronger model
  (DeepSeek-v4 / a frontier API). Provider switch already exists
  (`ARCHITECT_LLM_PROVIDER`).
- **Seeds:** ≥3 seeds per benchmark; report mean ± spread on verify-rate,
  iterations, wall-clock, IC-regret.
- **Ablations:** RAG on/off; repair-cap ∈ {2, 5, 10}; MC pre-filter on/off;
  router on/off (force each family). One table.
- **Benchmark set:** grow from 5 to ≥12 — add the FL-specific settings named in
  Task.md (cross-device quadratic, hierarchical edge, IIoT log-linear) plus
  2–3 per verifiable family, each with a known or hand-derived reference
  mechanism.

**Done when:** `docs/eval-results.md` carries the model-comparison table, the
seed-variance table, and the ablation table.

### Task 5 — Claim scoping in Task.md and any draft

- Rewrite the "Key Differentiation" paragraph: the formal guarantee holds for the
  **discrete-type screening + single-parameter Stackelberg + standard-form VCG**
  fragment; outside it the system returns `UNKNOWN` / `VERIFIED_TEMPLATE` and
  says so. Quote the entry-specific coverage number.
- Replace "for *any* proposed mechanism structure" with the fragment description
  everywhere it appears.
- State the affine-maximizer / restricted-domain caveat inline in the Synthesis
  section, not only in the deep-research appendix.

**Done when:** no sentence in Task.md claims verifier generality the measured
numbers don't back.

### Task 6 — Related work / positioning note

`docs/related-work.md` — one paragraph each, with the distinction line:
- **LegoNE (2508.11874):** LLM architect + formal worst-case certifier loop for
  ANE algorithms; *discovered a new result*. Our loop is the same shape; our
  distinction must be a novel *FL-mechanism* result (see future-scope) or the
  honest-verifiability finding from Task 1 — not the architecture.
- **Mittelmann et al. 2024:** Strategy-Logic model checking for mechanism
  verification *and* synthesis, domain-general. We differ in: real-valued
  utility fragment via SMT / SOS / interval rather than finite model checking;
  LLM proposer; FL corpus prior.
- **SMT in social choice (Brandl/Brandt; Barthe et al. 1502.04052):**
  computer-aided IC / impossibility proofs predate us by ~10 years — cite as the
  foundation, claim only the LLM-in-the-loop + FL application.
- **LLM+SMT invariant synthesis (LEMUR, LaM4Inv, LORIS, 2508.00419):** identical
  propose→solver→counterexample→repair loop. Cite; claim only the
  mechanism-design instantiation, not the loop.

**Done when:** `docs/related-work.md` exists and the paper outline references it.

### Task 7 — Coalition IC for discrete Contract menus

Scoped tight: 2-client joint deviation on discrete screening menus only. Not
Stackelberg (no screening IC), not transcendental. Self-contained addition to
Track 1; must not disturb the existing suite.

- `src/tracks/track1_z3.py`: add `verify_coalition_ic_contract(entry, k=2)` —
  enumerate the joint k-type profile, encode a joint misreport, assert
  `Σ_i u_i(truthful) ≥ Σ_i u_i(joint deviation)` for every joint deviation,
  reusing `_sp_to_z3` and the type-ordering machinery from `_try_contract_latex`.
  Returns a `VerificationResult` with a new `coalition_ic_k` field.
- `tests/verifier/test_coalition_ic.py`: (a) a menu that IS individually IC and
  coalition-safe → pass; (b) a menu that is individually IC but 2-client
  coalition-breakable → must return `COUNTEREXAMPLE`, never `VERIFIED`;
  (c) a k>menu-size request → clean `UNSUPPORTED`.
- Eval: `run_eval` reports `coalition_ic_regret` for Contract benchmarks.

**Done when:** the three tests pass, ≥1 Contract benchmark carries a certified
`coalition_ic_2` result, and the eval table has the column.

### Task 8 — Corpus trust-gap: lock the RAG boundary

Most of this is already in place (`z3_verdict=UNSUPPORTED` and
`z3_validated=False` on all 4 Shapley entries; `rag.py:_rank` keys on
`z3_validated is not True`). Two concrete gaps remain.

- `tests/architect/test_rag_trust.py`: assert `_rank` / `retrieve` never read
  `ic_proof_present` as a proof signal — construct a synthetic entry with
  `ic_proof_present=True, z3_validated=False` and confirm it does **not** win the
  tie-break over a true `z3_validated` entry at equal cosine.
- `tools/validate.py`: add a check that any entry with `z3_validated is True`
  also has `z3_verdict == "VERIFIED"` (catches a future desync).
- `2405_13879` recategorization is a **human decision** (new "penalty + sandwich
  competition" family vs. documented stay) — the plan raises it; it does not
  resolve it in code.

**Done when:** both tests/checks pass; the `2405_13879` question is written into
`docs/related-work.md` or an issue for the human call.

---

## Explicitly out of scope this round

In `2026-08-28-ast-native-verifier-future-scope.md`:

- A novel certified FL mechanism / impossibility (the LegoNE-bar result) — Part 2.
- Multivariable δ-sound transcendental IC (`ln` / exponential utilities) — Part 3;
  needed for `iiot_log_linear` and most real FL utility forms.
- AST-native verify path (Approach C) and verified-mechanism corpus write-back —
  Part 1.

---

## Suggested order

1. Task 5 + Task 6 (writing, no code, unblocks honest framing immediately).
2. Task 8 (RAG-trust test — cheap, protects the corpus claim).
3. Task 3 (soundness suite — protects every later number).
4. Task 1 (family decision — changes what the eval measures).
5. Task 7 (coalition IC — self-contained).
6. Task 4 (rigor) and Task 2 (baselines) in parallel; both feed the results table.
