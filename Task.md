# FL Incentive Mechanism Corpus — Task Document

## What This Project Is Building

**An AI system that automatically designs provably correct reward rules for Federated Learning.**

### The Problem

Federated Learning (FL) works by getting many devices or organizations to collaboratively train a shared model. But participants are rational and self-interested: they free-ride (let others do the work), lie about their data quality to get bigger rewards, or simply opt out if participation isn't worth it.

Solving this requires a **Game Theory expert** to manually design a reward system — an auction, a contract, or a Stackelberg pricing rule — that mathematically guarantees honest participation. This takes months, requires deep expertise, and has to be redone from scratch every time the setup changes (different number of clients, different cost structures, different trust models). It does not scale.

### Our Solution: Architect + Inspector

We pair an LLM with a formal verifier in a feedback loop:

```
Problem Description
      │
      ▼
┌─────────────┐     proposes mechanism     ┌──────────────────┐
│   LLM       │ ────────────────────────▶  │  Formal Verifier │
│ (Architect) │                            │  (Inspector)     │
│             │ ◀────────────────────────  │                  │
└─────────────┘  counterexample + fix hint └──────────────────┘
      │
      │ (when verifier says "cheat-free")
      ▼
  Verified Mechanism
```

1. **Architect (LLM):** Reads a description of the FL setup and proposes a reward rule (payment function, IC condition, IR condition).
2. **Inspector (Formal Verifier):** Tests the rule mathematically. If it finds a loophole, it returns a _specific_ counterexample: _"Client type B can cheat here and earn $5 extra by misreporting."_
3. **Architect** takes that exact feedback, patches the loophole, and tries again.
4. Loop continues until the Inspector certifies: **100% cheat-free**.

### How the Inspector Works — Multi-Track Verifier

The Formal Verifier is not a single tool. IC/IR conditions in FL mechanisms span several mathematical families, and no single solver handles all of them. The Inspector routes each proposed mechanism to the appropriate backend based on the structure of its utility functions:

```
LLM proposes mechanism
(utility functions + IC/IR conditions in LaTeX)
            │
     [ROUTER: classify utility structure]
            │
   ┌────────┼──────────┬──────────────┐
   │        │          │              │
   ▼        ▼          ▼              ▼
 Track 1  Track 2   Track 3        Track 4
  Z3       SOS       dReal          SymPy
   │        │          │              │
   └────────┴──────────┴──────────────┘
                   │
        PASS → verified mechanism
        FAIL → counterexample → LLM fixes → loop
```

**Track 1 — Z3 (exact, fast)**
- When: type space is finite and discrete (e.g., 3 client types: low/medium/high), utilities are linear
- What it does: enumerates all cases and proves no deviation exists
- Covers: all VCG/auction mechanisms, Contract theory with discrete type menus
- Guarantee: exact proof, complete

**Track 2 — SOS via CVXPY (exact certificate for polynomials)**
- When: utility is polynomial (quadratic costs `c·e²`, linear-quadratic contracts)
- What it does: finds a Sum-of-Squares certificate proving `u(truthful) - u(lie) ≥ 0` for all real θ in a bounded set. A sum of squares is always non-negative by construction — if this certificate exists, IC is proven.
- Covers: most Contract and Stackelberg entries with quadratic cost functions
- Guarantee: exact proof via semidefinite programming
- Library: CVXPY + SCS/MOSEK

**Track 3 — dReal (approximate, transcendental)**
- When: utility involves `ln`, `exp`, or sigmoid functions (e.g., `U_i = R_i · ln(1/θ_i)`)
- What it does: δ-satisfiability — proves IC holds up to a numerical tolerance δ
- Covers: log-linear Stackelberg entries, sigmoid-based leader objectives
- Guarantee: approximate (δ-correct, not exact). Strongest claim: "no counterexample within numerical precision δ"

**Track 4 — SymPy (symbolic integration)**
- When: Bayesian IC — utility is an expectation over a type distribution (integral form)
- What it does: symbolically integrates the IC condition over a known distribution (uniform, truncated Gaussian) and reduces it to a checkable algebraic condition
- Covers: Myerson-style optimal mechanisms, Bayesian Contract theory

> **Status (updated 2026-07-17): Track 3 no longer uses dReal.** dReal4 has no ARM64 binary and cannot be installed on Apple Silicon. Track 3 was reimplemented on `mpmath.iv` (rigorous interval arithmetic, pure Python, ARM-native) — same δ-soundness guarantee for the single-variable case. See `src/tracks/track3_dreal.py`.
>
> **Real usage on the corpus, measured by actually running the verifier (not estimated):** Track 2 (SOS) fires 0 times, Track 3 fires a handful of times, Track 4 (Bayesian) fires 0 times, across the 105 verifiable-tier entries (updated 2026-07-18; corpus is now 185 entries, see the corpus-quality note below). This is lower than the original ~10-15% estimate — see "Router bug" below. Option A (Track 1 + 2 only, mark the rest as future work) is closer to where the system actually is today than Option B's framing suggested.
>
> **Router bug fixed (2026-07-17):** `verifier.py`'s track classifier previously matched against a field named `utility_function_latex`, which does not exist in any of the 253 corpus entries — the corpus schema is category-specific (`client_utility_latex` for Contract, `follower_utility_latex`/`leader_objective_latex` for Stackelberg, `shapley_formula_latex` for Shapley). In practice this meant Track 2/3/4 were only ever reachable for Contract and VCG entries, regardless of a Stackelberg or Shapley entry's actual math. Fixed by scanning all string-valued `mechanism` fields instead of a fixed field list.

### Verdict Semantics: VERIFIED vs. VERIFIED_TEMPLATE

**Fixed 2026-07-17.** Every Track 1 verifier (VCG, Contract, Stackelberg) has two code paths: an *entry-specific* path that parses the paper's own LaTeX (utility function, payment rule, best response) and checks it, and a *generic template* fallback (a textbook VCG/contract/Stackelberg model with placeholder algebra) used when the entry-specific path can't parse the paper's fields. Previously, both paths reported the verdict `VERIFIED` — a reader (or the corpus's own `z3_validated` field, or a future paper) could not tell "this specific paper's mechanism was checked" apart from "a generic template that says nothing about this paper passed a sanity check." Measured before the fix: of 157 entries reporting `VERIFIED`, 133 (85%) were template-only — most damagingly, **all 62 passing Stackelberg entries were template-only**, via a fixed tautology (`p²/2 ≥ 0` for `p > 0`) that never read the paper's own fields at all and could not fail for any input.

The verdict space now has six values (`src/tracks/__init__.py`): `VERIFIED` (entry_specific=True — a real check against this paper's own math), `VERIFIED_TEMPLATE` (generic template only — says nothing about this specific paper), `VERIFIED_SHAPE` (regex/structural payment-shape match only — strictly weaker than `VERIFIED_TEMPLATE`; no solver was ever run on the entry), `COUNTEREXAMPLE`, `UNKNOWN`, `UNSUPPORTED`. `finalize_verdict()` centralizes the downgrade so no track can accidentally report `VERIFIED` for a template-only result; `VERIFIED_SHAPE` is set explicitly on the VCG regex fallback path (see the Phase 2 note below).

Adversarial soundness suite (`tests/verifier/`): 22 known-unsound mechanisms, 0 false VERIFIED (`src/architect/eval/soundness_report.py`). Two entry-specific gates were added to close false positives it found — Contract IC RHS must depend on the deviating type (`track1_z3._parse_contract_entry`), the Track 2 parametric certificate must reject infeasible binding solutions (`track2_sos._parametric_contract_certificate`), and an identically-zero VCG payment now fails closed. Five residual holes where a category's generic template path ignores the entry's own math are pinned as `xfail` (see `.superpowers/sdd/2026-08-29-novelty-hardening/task-D-report.md`).
>
> **Re-measured 2026-07-18 (evening), after the Contract type-ordering fix:** **24/105 genuinely `VERIFIED`** (VCG 19, Contract 4, Stackelberg 1); 72 `VERIFIED_TEMPLATE`; **0 `COUNTEREXAMPLE`**; 4 `UNKNOWN`; 5 `UNSUPPORTED`. The five Contract `COUNTEREXAMPLE`s were confirmed artifacts of the missing type-ordering precondition (each "counterexample" sat in a parameter region the paper excludes, e.g. reversed type order). `_try_contract_latex` now: identifies the type family from the entry's own `type_variable` field (declared data, not a guess); resolves the value-vs-cost direction from the sign of dU/dθ under all-positive assumptions (sympy's assumption engine — sound); imposes the corresponding strict type ordering plus non-decreasing menu monotonicity on exactly the families subscripted by the contract index in the IC RHS (structurally identified menu variables — type-probability families like `f_i` are correctly untouched); and adds a vacuity gate (bindings+ordering must be jointly satisfiable, else fall back to template rather than report a vacuous VERIFIED). Fail-closed throughout: ambiguous type declarations (Tian2021contract declares two type symbols) get UNKNOWN with counterexamples suppressed, never asserted; indeterminate direction checks BOTH pairings and only asserts unanimous results. 4 of 5 flipped to entry-specific VERIFIED (Sun2022coded correctly detected as a *cost*-type, descending order); Tian2021contract is honestly UNKNOWN. 5 new tests in `tests/test_contract_ordering.py` (38 total, all passing).
>
> **Verifier wired into the corpus (2026-07-18):** every verifiable-tier entry now carries `z3_verdict` (5-value enum, schema updated in `tools/corpus_schema.json`) and `z3_validated` is `true` exactly for entry-specific VERIFIED entries (`null` for RAG-only). The Shapley trust gap flagged in category 4 below is closed mechanically — those entries carry an explicit `UNSUPPORTED` that no downstream consumer can mistake for a machine-checked IC proof.
>
> **Measured track usage (2026-07-18):** Track 1 (Z3) handled 102/105 entries; Track 3 got 3, all UNKNOWN; Tracks 2 and 4 fired **zero** times — at that point dead code with respect to the corpus.
>
> **Multi-track rebuild (2026-07-19) — all four tracks now genuinely fire: {Track 1: 98, Track 2: 4, Track 3: 2, Track 4: 1}, 25/105 entry-specific VERIFIED, 0 COUNTEREXAMPLE, 2 UNKNOWN.** What changed, per track:
> - **Track 2 (was: numeric SOS, needed numeric coefficients + continuous types — zero corpus matches).** New *parametric certificate* path for symbolic discrete-type screening menus: re-coordinates in ordered increments (type direction resolved from sign of dU/dθ), solves the binding equations for the reward family, and certifies every IC gap and IR value as a **posynomial** (all-nonnegative coefficients over positive coordinates — a degree-0 Positivstellensatz certificate, exact and human-readable, e.g. Lim2020's IC gap = `c·dq₁·dθ₁/(dθ₁+θ_lo)`). Dispatcher tries it before Z3 for Contract entries; only VERIFIED short-circuits. Now carries 4 entries, **independently cross-validating the Z3 proofs of the same entries by a completely different method**. Fail-closed: never emits counterexamples.
> - **Track 3 (was: single-variable interval arithmetic that collapsed every θ-like symbol into one — a silent soundness bug for multi-type IC — and returned UNKNOWN on all 3 of its entries).** New multi-dimensional interval branch-and-bound (`check_nonneg_box`, splits widest dimension, budget-limited, δ-sound). Two uses: (a) standalone transcendental Contract IC/IR over independent-symbol boxes (multi-symbol box counterexamples are suppressed to UNKNOWN — menu/type symbols are not free parameters, same lesson as the type-ordering fix); (b) **as the rigorous replacement for Track 1's Stackelberg IR sampling fallback, which used to report VERIFIED from 10 numeric sample points — unsound, and it was exactly what the single entry-specific Stackelberg VERIFIED (Sarikaya2019) rested on.** That entry is now proven by interval arithmetic over a parameter box and attributed to Track 3. Dispatcher also falls through on Track 3 UNKNOWN to Track 1 (2 entries thereby improved from UNKNOWN to honest VERIFIED_TEMPLATE).
> - **Track 4 (was: continuous-type integral BIC — zero corpus papers have that form).** New *discrete-prior Bayesian IC* path: the form BIC actually takes in this literature (expected utilities over a finite type/state space, proven conditional on declared assumptions). Paper-declared assumptions (`bayesian_assumptions_latex`, new schema field) are applied as slack substitutions, then the gap is certified with the shared posynomial machinery. First real entry: **Li2025bayesian_incentive** (Theorems 1–2 manually extracted from the PDF 2026-07-19: IC gap `(P_h−P_m)·R` under `P_h ≥ P_m`; IR under `R > C/P_h`) — VERIFIED with certificate, upgrading it from VERIFIED_TEMPLATE. Other Bayesian-adjacent corpus papers were checked and honestly left out (DaringFed: Bayesian persuasion, different framework; Zhang2020fedserving: Bayesian Truth Serum peer-prediction; Batool2022fl_mab: BNE claim with no closed-form condition).
> - **Honest framing for any writeup:** Track 1 remains the workhorse (98/105) because the literature's mechanisms live in the discrete-type symbolic fragment; Tracks 2–4 are load-bearing where they fire and are the designated verifiers for Architect-generated output (numeric SOS in synthesis mode, transcendental IR, Bayesian mechanisms). 13 new tests in `tests/test_multitrack.py` (51 total, all passing), including a cross-track consistency test (Track 2 certificate must agree with Z3 on the textbook menu).
>
> Pre-fix snapshot for history (2026-07-18, morning): 20/105 `VERIFIED`; 72 `VERIFIED_TEMPLATE`; 5 `COUNTEREXAMPLE` (all spurious, see above), 3 `UNKNOWN`, 5 `UNSUPPORTED`. Run `python -m verifier corpus.json` (from `src/`, or with `PYTHONPATH=src`) for the current breakdown. Per-category split: **VCG 19/33 entry-specific** (form-confirmed against a known Groves/Myerson payment shape); **Contract 4/38 entry-specific** (30 template, 4 unknown — the 5 previously-reported "genuine counterexamples" were type-ordering artifacts, see the evening update above; every template-stuck entry was individually root-caused, see below); **Stackelberg 1/30 entry-specific**; **Shapley 0/4** (the track is an intentional stub, see category 4 below).
>
> **Root-cause audit of the VERIFIED_TEMPLATE entries (2026-07-18):** rather than treat the template count as an opaque number, every stuck entry was traced to find out whether it's stuck because the paper genuinely lacks the relevant formula, or because the parser fails on data that's actually present.
> - **VCG (14 template-only):** 2 have no payment data at all (prose-only papers). 2 use a payment form the classifier correctly recognizes as non-standard (`budget_split` — Groves theorem doesn't apply). The remaining **10 have real `payment_rule_latex` data**, hand-checked against the classifier's known Clarke-pivot/marginal-welfare/critical-bid regex forms — none of them actually match one of those canonical forms (they're quality-based exponential rewards, proportional-share formulas, bandit-indicator payments, etc.). This is the classifier working as designed, not a parsing bug: claiming theorem-backed DSIC for a genuinely novel payment rule would need a real per-formula Z3 encoding, which is out of scope for a regex classifier (see the VCG rebuild note below).
> - **Contract (30 template-only):** 10 are genuinely missing IC/IR data (7 of these are confirmed-different mechanism families — moral hazard, Bayesian persuasion, peer prediction — correctly left null rather than forced). The other **20 have real IC+IR data present** but the entry-specific path (`_try_contract_latex`) still bails, for concrete, individually-diagnosed reasons: 5 hit an unsupported function call or a symbolic (non-numeric) exponent in `_sp_to_z3`; 9 have 2+ distinct type-subscripts where the code requires exactly 1 (some genuinely multi-dimensional types, some using `n-1` arithmetic instead of a second index symbol — a notation style the parser doesn't handle); 4 hit a real sympy LaTeX-parser limitation on `f_{sub}(\arg_{sub})` function-call notation; 1 uses neither `\geq` nor `\ge`; 1 (`Yang2023async_contract`) hits a deliberate soundness gate (`ir_from_ic_lhs` in `_try_contract_latex`) that reverts to template on purpose because its IR had to be inferred from the IC's LHS, which can silently drop cost terms.
> - **Stackelberg (28 template-only):** 5 are genuinely missing FOC/best-response data (papers solved numerically — genetic algorithm, variational inequality — with no closed form to extract). Of the other ~22, a diagnostic pass on 20 found: **10 fail because sympy's LaTeX parser doesn't understand `\sum_{i \in S}` / `\sum_{a \le i \le b}` set- or inequality-style summation bounds** (only `\sum_{i=1}^{n}` numeric-bound form) — the single largest concrete lever remaining, but deliberately not fixed yet because a safe fix requires correctly isolating the follower's own term from within the sum, and a wrong isolation would silently produce a wrong FOC; 5 fail on follower-symbol identification (2 are genuinely multi-variable followers, correctly deferred; 1 is a known limitation; 1 disagreement between the derived best-response and the paper's own stated one, correctly rejected rather than asserted); 2 correctly fail-closed on multi-variable followers; 1 hits a sympy solver limitation on a multi-exponential FOC; 1 uses `\|x\|` norm-bar notation sympy can't parse.
>
> **Three Stackelberg parser bugs fixed 2026-07-18** (all in `src/tracks/track1_z3.py`, all verified via the 33-test pytest suite plus a targeted regression check confirming no verdict changed from a previously-safe result to a wrong one): (1) `_DEFINITION_CLAUSE_RE`'s LHS regex didn't allow `,`/`()`/`-` inside braces or superscripts, rejecting common multi-index/time-index notation like `C_{i,t}` or `P_i^{(t)}` outright; (2) `_demote_stray_function_calls` crashed with `ValueError: substitution cannot create dummy dependencies` on a simultaneous multi-symbol substitution — now falls back to sequential substitution, then to a no-op, instead of raising; (3) font-styling LaTeX commands (`\mathcal{X}`, `\mathbf{X}`, `\boldsymbol{X}`) were not recognized by sympy's parser and got silently mistokenized as literal symbols, corrupting formulas into nonsense (e.g. an entire utility function collapsing to `U*mathcal`) instead of failing cleanly — this was a real soundness risk (a corrupted-but-"successful" parse is worse than an honest failure) and is now stripped before parsing. None of these three fixes changed the entry-specific VERIFIED count (still 1/30) — they fixed real bugs and made the pipeline safer for future entries, but the remaining blockers are the deeper `\sum`/comma-subscript sympy limitations above, deliberately not attempted given the risk of a silently wrong FOC.

> **Phase 2 — real VCG check wired in (2026-08-30, branch `phase2-vcg-real-check` Task 5).** `verify_vcg` now dispatches to `verify_vcg_dsic` (a real finite-bid-grid Z3 DSIC + IR proof, `src/tracks/vcg_dsic.py`) first; only its `VERIFIED` / `COUNTEREXAMPLE` short-circuit. The old regex payment-shape classifier is now a pure fallback and its success is post-mapped to the new `VERIFIED_SHAPE` verdict (never `VERIFIED` / `VERIFIED_TEMPLATE`), `entry_specific=False`. The identically-zero-payment soundness gate still runs first. **VCG verdict counts moved by design** (33 entries): VERIFIED (real DSIC) **0**, VERIFIED_SHAPE **33**, COUNTEREXAMPLE **0**, UNKNOWN **0** — every corpus VCG entry currently fails the real check closed (allocation/payment LaTeX not yet parseable into an encodable spec, or absent) and falls through to `VERIFIED_SHAPE`. Was: 19 entry-specific `VERIFIED` (regex form-confirmed) + 14 `VERIFIED_TEMPLATE`. Per-entry before→after→reason table: `docs/superpowers/notes/phase2-vcg-verdict-delta.md`. Corpus headline: `VERIFIED` 25→6, `VERIFIED_TEMPLATE` 73→59, `VERIFIED_SHAPE` 0→33; all non-VCG counts frozen (Contract 5 entry-specific / 31 template, Stackelberg 1/28, Track 2 SOS 4, Track 3 1, Track 4 1). `_vcg_check_core` itself is unchanged — the Approach C AST caller (`architect/ast_verify.py::verify_from_ast`) still gets the old verdicts until Phase 2 Task 7. The two VCG "template-fallback holes" moved from `xfail` to the hard `BROKEN` adversarial list (they now honestly return `VERIFIED_SHAPE`, a documented non-proof). Suite: 190 passed / 3 xfailed / 0 failed; `tools/validate.py` 185/185.
>
> **Phase 2 landed (2026-08-30).** VCG entry-specific proofs: **0** (real `verify_vcg_dsic`); 33 `VERIFIED_SHAPE` (regex shape, not a proof). Corpus real machine-checked proofs: **6** (Contract 5, Stackelberg 1). `verify_vcg_dsic` proves DSIC+IR over a finite bid grid for highest-/lowest-bidder allocation + Clarke-pivot or explicit-formula payment; multi-attribute & argmax-welfare → `UNKNOWN` (fail-closed). `verify_from_ast`'s VCG branch calls the real check (Approach C `entry_specific=False` stopgap removed).
>
> **Phase 3 — verifier widening + AST-native completion (2026-08-31, branch `phase3-verifier-widening`, b09cdfe..9a45926).** Widening + fail-closed hardening + AST-native completion — **not** corpus movement.
> - **Real entry-specific `VERIFIED` count is UNCHANGED at 6** (Contract 5, Stackelberg 1). Phase 3's parser widening flipped **0** entries — `docs/superpowers/notes/phase3-new-verified.md` is empty. Every widened Contract / Stackelberg parser hit a *second, independent* blocker on every corpus entry it could newly reach; each fails closed to the entry's existing verdict. This is the plan-permitted partial landing, not a regression. Corpus is byte-identical to the Task-1 baseline: VERIFIED 6 / VERIFIED_TEMPLATE 59 / VERIFIED_SHAPE 33 / UNKNOWN 2 / UNSUPPORTED 5. Full delta: `docs/superpowers/notes/phase3-delta.md`.
> - **AST-native routing is now real.** `verify_from_ast` routes to the Track 2/3/4 seams via `_classify_ast` (not everything funnelled through the Track-1 core); the seams (`track{2,3,4}_check_from_sympy`) take parsed SymPy exprs, not `entry` dicts. VCG has a real allocation AST node (`AllocHighest` / `AllocTopK` / `AllocWeightedWelfare` + `Mechanism.allocation`); Synthesis mode sets that node instead of injecting `meta["allocation_rule_latex"]`, and `verify_from_ast(synthesized VCG)` reaches genuine entry-specific `VERIFIED` with a 9-profile grid proof. Approach C is complete. `verify(entry)` — the corpus API — is untouched, which is why the corpus does not move.
> - **Transcendental coverage.** Track 3 box search extended with `max_ic_regret_over_box` (a rigorous δ-bounded IC-regret upper bound) + multi-symbol counterexample suppression; the Architect prompt now emits `Func("ln"/"exp")` for log/exp intake. **No new corpus entry verified**: `Kang2019contract_mobile` (the only transcendental Contract corpus entry) stays `UNKNOWN` (9/11 free vars → box-intractable); `iiot_log_linear` is an Architect eval benchmark, not a corpus entry, so `verify()` never touches it (its offline δ-regret ≈ 69.06 is a loose over-estimate over the fully-decoupled box — true menu regret 0).
> - **`ARCHITECT_AST_VERIFY` stays default OFF.** The flip is code-ready — Tasks 5–9 made the AST path strictly ≥ the LaTeX path on every existing test (`verify_from_ast` verdict `==` `inspect_mechanism` verdict on every parity fixture; AST-only additionally reaches Track 3 where the Track-1 core returns `UNKNOWN`) — and gated only on a clean full flagged `run_eval` with no verified-rate regression, currently API-blocked. See `docs/superpowers/specs/2026-08-29-verifier-proper-checks.md`.
> - **NOT this round (explicit decision):** the `VERIFIED_TEMPLATE` → `UNKNOWN` fail-close pass (~61 entries would drop — the honesty pass, separate round) and Phase 4 (coalition / small-Shapley).
> - Suite: 204 → **262 passed / 3 xfailed / 0 failed** (~58 tests added — widening pins, regression locks, fail-closed characterization).

**Stackelberg now has a real entry-specific path** (`_try_stackelberg_latex` in `src/tracks/track1_z3.py`): parses `follower_utility_latex` (resolving multi-clause "U = R - C, R = ..., C = ..." definitions), symbolically derives the follower's FOC and best response, and checks IR at that optimum — instead of the old placeholder. It fails closed by design (12 unit tests in `tests/test_stackelberg.py` cover the happy path, IR counterexamples, ambiguous-decision-variable cases, and a best-response cross-check that rejects rather than certifies when its own derived optimum disagrees with the paper's stated `best_response_latex`).

> **Updated 2026-07-18, after a full manual PDF-extraction pass on every Stackelberg entry missing data:** field coverage is now 29/30 `follower_utility_latex`, 26/30 `best_response_latex`, 23/30 `follower_foc_latex`, 6/30 `ir_follower_latex` (up from 36/63, 11/63, and 4/63 respectively when this was last measured against the pre-cleanup 63-entry Stackelberg set) — the sparse-fields blocker below is essentially resolved. `ir_follower_latex` stays low not because of missed extraction but because most Stackelberg FL papers genuinely never state a formal follower participation constraint (confirmed per-entry by manual PDF review, not assumed). **Real entry-specific coverage is now 1/30** (`Sarikaya2019stackelberg_workers`) — still small, but for a different reason than before: it's no longer a missing-data problem, it's a parser problem, root-caused in detail above (mainly: sympy's LaTeX parser doesn't understand `\sum_{i \in S}`-style summation bounds, which is the single biggest remaining lever).

Two concrete blockers originally found by exercising the entry-specific path against the corpus (both now addressed by the manual data pass and the three parser fixes above; kept here for history):

1. **Sparse fields** — now resolved, see above.
2. **Ambiguous notation.** LaTeX like `\kappa c_i (P_i)^2` (meant as κ·c_i·P_i², a coefficient times a squared term) is genuinely ambiguous to a standard LaTeX-math parser, which reads `c_i (P_i)` as a function call `c_i(P_i)` and then applies the exponent to the whole call, producing `c_i²·P_i²` instead. The pipeline's best-response cross-check caught exactly this on `Sarikaya2019stackelberg_workers` — and, unlike most entries, that one's derivation was clean enough to still verify correctly once caught, which is why it's the one entry-specific `VERIFIED` in this category today.

**Recommendation for the corpus extraction pipeline** (`tools/extract.py` / `tools/prompts.py`): have the LaTeX-extraction prompt insert explicit `\cdot` (or `*`) for multiplication rather than relying on juxtaposition, and prefer a single closed-form utility expression over multi-clause "shell + auxiliary definitions" form where the source paper allows it. Both would directly raise real (not template) coverage for Stackelberg and any future entry-specific track, without changing the verifier's logic at all.

### Three Modes of Operation

The system operates in one of three modes depending on how novel the input problem is:

| Mode | What happens | Output |
|---|---|---|
| **Retrieval** | RAG finds the closest corpus entry, LLM adapts it to the new FL setup | Known mechanism adapted, formally re-verified for new parameters |
| **Hybrid** | LLM combines elements from multiple corpus entries (e.g., VCG allocation + Contract-style payment), verifier certifies the combination | New mechanism instance not in any paper, formally proven IC/IR |
| **Synthesis** | LLM proposes a structural template with unknown parameters, Z3 finds parameter values satisfying IC + IR + budget balance simultaneously | Mechanism found by formal search, not human derivation |

> The mode selects *how* a mechanism is produced, not *which family*. Until spec Task 1 lands, the emitted family is emergent and often differs from the FL setting's natural family — see "What is left / Family fidelity".

**Retrieval** handles the 80% case — most FL deployments are close enough to existing literature that adaptation suffices.

**Hybrid** handles FL setups that sit between mechanism families. Many real deployments need properties from two families simultaneously. The verifier determines whether the combination is coherent.

**Synthesis** is the novel research contribution unique to this pipeline. Instead of asking the LLM to propose a complete mechanism, the LLM proposes a structural template with unknown parameters:

```
payment(θ) = a·θ² + b·θ + c      ← structure from LLM, unknowns: a, b, c
```

On the restricted type/outcome domains typical of FL, the affine-maximizer family is a sound but non-exhaustive subclass of DSIC mechanisms (Lavi–Mu'alem–Nisan 2003; Mishra–Sen 2012); Synthesis mode is "exhaustive search within the affine-maximizer class", not "complete over all DSIC mechanisms".

Z3 is then run in **synthesis mode** — given IC, IR, and budget constraints, it searches for values of `a`, `b`, `c` that satisfy all of them simultaneously:

```
∀θ, θ': u(θ, truthful) ≥ u(θ, lie)     ← IC
∀θ: u(θ, truthful) ≥ 0                  ← IR
Σ payment(θᵢ) ≤ Budget                   ← Budget Balance
```

If Z3 finds such values, the output is a formally certified mechanism within that structural family — derived by mathematical search, not human intuition. No FL mechanism paper has used Z3 in synthesis mode. This is automated mechanism design using formal methods applied to a domain-specific corpus.

> **Honest scope:** Synthesis works cleanly for polynomial payment rules with 3–5 unknown parameters. It becomes intractable for complex multi-variable templates. The LLM's role is to propose a tractable structural template; Z3 finds the parameters.

---

## Stage 2 — The Architect: Implementation Status (updated 2026-08-29)

**Stage 1 (corpus + multi-track verifier) is complete. Stage 2 (the Architect CEGIS loop) is now built, merged to `main`, and running end-to-end against a live LLM.** Code lives in `src/architect/` (14 modules); `tests/architect/` has 55 tests, full suite 109 passing.

### What was built

A Counterexample-Guided Inductive Synthesis (CEGIS) loop with the LLM as *learner* and the Stage 1 verifier as *teacher* — the design in the diagram at the top of this document, implemented:

```
free-text FL setup
      │
 Intake LLM  ──► ProblemSpec (records missing fields, fills documented defaults)
      │
 Mode router ──► Retrieval | Synthesis | Hybrid   (nearest-corpus cosine + LLM yes/no)
      │
 RAG index (flat numpy cosine over 185 corpus entries, z3_validated tie-break)
      │
 ARCHITECT (LLM)  ──► typed AST (never free-form LaTeX)
      │
 [Synthesis only] SYNTHESIZER: Z3 solve-mode over Unknown leaf nodes
      │
 SERIALIZER: AST → mechanism-dict LaTeX + round-trip parseability check
             (rejects with a repair hint if outside the parser's fragment)
      │
 MC pre-filter (VCG only — see below)
      │
 INSPECTOR: Stage 1 verify(entry) → 5-value verdict
      │
 LOOP CONTROLLER — per-verdict repair policy:
   VERIFIED ∧ entry_specific → STOP (emit mechanism + certificate + LaTeX)
   COUNTEREXAMPLE / parse error / propose error / synth-UNSAT
                              → feed exact reason back, re-propose;
                                cap 5, then 1 fresh restart, then 5 more, then FAIL
   UNKNOWN     → "simplify, same family", ≤2
   UNSUPPORTED → force a verifiable family, ≤1
   VERIFIED_TEMPLATE → FAIL (a generic-template pass is not a real proof)
   global wall-clock backstop over all caps
```

**Design decision — no LaTeX parser in the loop.** The Architect emits a typed AST
(`Const, Sym, Unknown, Sum, Prod, Pow, Func{ln|exp}, IndexedFamily`). A pure
serializer renders it two ways from one tree: LaTeX for the paper/corpus, and the
category-specific `mechanism` dict for `verify()`. A round-trip check
(`parse(render(ast)) ≈ ast`, using Stage 1's parsers in a new parse-only mode)
rejects anything outside the parseable fragment *before* verification, so the
loop never spends an iteration on a syntax error — the parser fragility
documented earlier in this file is not inherited by the generator.

### Verified capability

The loop's only success condition is `verdict == "VERIFIED" and entry_specific is True`.
That state is **reachable for a serialized-AST mechanism through the real
`verify()`**, proven by tests that drive the actual `loop.run()` (LLM stubbed at
`propose`, everything else real):

- **Stackelberg** — `test_loop_run_reaches_verified_via_stackelberg`: a textbook
  follower-effort mechanism `U_i = p_i·e_i − ½·c·e_i²` → FOC best response
  `e_i* = p_i/c` → IR certified by interval arithmetic → `VERIFIED`, `entry_specific=True`.
- **Contract** — `test_loop_run_reaches_verified_via_contract`: a 2-type screening
  menu, IC rendered in the two-sided `U_i(own) ≥ U_i(other)` form the Stage 1
  Contract parser needs → exact symbolic (degree-0 Positivstellensatz / posynomial)
  certificate → `VERIFIED`.
- VCG has the field plumbing but no end-to-end proof test yet.
- **Hybrid mode** is built (prompt + provenance) but not yet exercised end-to-end.

Two serializer/loop changes were needed to make Contract reachable at all:
`_contract_ic_latex()` emits the two-sided IC form (falls back to one-sided, i.e.
`VERIFIED_TEMPLATE`, if the AST shape differs — no regression); and `Mechanism.meta`
carries non-LaTeX verifier metadata (`equilibrium_existence`, `follower_decision`,
`num_types`, `type_variable`) through `render()` to `verify()` behind a key
allowlist so a model-authored proposal can't overwrite a validated LaTeX field.

### MC pre-filter scope (corrected)

The Monte-Carlo pre-filter samples every symbol independently in `[0.1, 1]` with
no structural constraints. That is a sound quick check only for **VCG**
(dominant-strategy, independent private values). For Contract it needs a type
ordering it does not impose → spurious "violations" on valid screening menus
(the same reason Stage 1's Z3 suppresses unordered Contract counterexamples to
UNKNOWN); for Stackelberg there is no IC to check. The pre-filter now runs for
**VCG only**; Contract/Stackelberg proposals go straight to the real verifier.

### LLM backend — NVIDIA API

`src/architect/llm.py` routes through the `openai` SDK against NVIDIA's
OpenAI-compatible endpoint (`https://integrate.api.nvidia.com/v1`). Provider is a
one-env-var switch (`ARCHITECT_LLM_PROVIDER` ∈ {nvidia, groq, openai};
`ARCHITECT_LLM_MODEL` overrides the model). `<think>…</think>` prefixes from
reasoning models are stripped so JSON parsing is unaffected. Embeddings
(`src/architect/rag.py`) use a remote-first fallback chain: NVIDIA embeddings API
→ HuggingFace Inference API (`HF_TOKEN`) → local sentence-transformers → a
deterministic hashing stub; a dead/EOL model degrades down the chain instead of
crashing.

Current working defaults (NVIDIA retires models frequently — verify against the
live catalog): LLM `meta/llama-3.2-90b-vision-instruct`, embeddings
`nvidia/llama-3.2-nv-embedqa-1b-v1`.

### Live end-to-end run — findings

Running `python -m architect.cli "<free-text FL setup>"` against the live NVIDIA
API exercised the full pipeline (corpus embedding → intake → routing → propose →
verify → repair). It surfaced and fixed four real bugs no unit test had caught:

1. **Model roster drift** — both model defaults chosen from Jan-2026 knowledge
   were EOL'd by NVIDIA in the days before the run; live-catalog probing + working
   defaults now in place.
2. **A malformed LLM proposal aborted the whole run** — `loop.run` treated any
   `propose()` exception as an immediate `FAILED`. Per the plan's own error table
   it must feed the decode error back and re-propose within the repair budget.
   Fixed; only exhausting the budget now FAILs.
3. **Schema adherence** — the model returned nested `IndexedFamily` nodes with a
   string `over`, `num_types: 1`, and a missing top-level `utility` key. Fixes: a
   full worked Mechanism-JSON example in the prompt, an instruction to prefer
   plain `Sym`, a clear "missing key(s): […]" decode error, and string→`[string]`
   coercion for `IndexedFamily.over`.
4. **`synthesize()` only collected `Unknown` leaves from the payment subtree** —
   a model that put a free coefficient in `ic`/`ir`/`utility` crashed with a
   `KeyError` during back-substitution. Now collects from all four subtrees.
5. **`VERIFIED_TEMPLATE` was an immediate hard-fail** — on a clean run it is the
   most common non-success outcome (the math parsed but the entry-specific
   verifier path didn't engage, usually a missing `meta` key or an FOC/IC the
   parser can't isolate) and it is *recoverable*. Now the loop hints ("that is a
   generic template, not a proof — add the missing metadata / simplify the
   algebra") and retries within the repair budget, FAILing only on exhaustion.

6. **`synthesize()` over-fought Stackelberg** — Synthesis mode ran the Z3
   `∀(ic≥0, ir≥0)` solve for Stackelberg (a category error — no screening IC),
   and reformulate-looped the model off parametric templates without converging.
   Now: a Stackelberg proposal has its `Unknown` nodes demoted to plain `Sym`
   (models routinely over-mark the *price* as `Unknown`) and goes straight to the
   verifier, which derives the follower FOC and checks IR at the optimum.
7. **`follower_decision` metadata format** — the Stage 1 Stackelberg parser reads
   `follower_decision` as inline LaTeX (`\( e_i \)`); the model emitted prose
   ("effort e_i") or a bare token, so symbol extraction failed and every run
   fell to `VERIFIED_TEMPLATE`. `mechanism_from_json` now normalises it to the
   `\( … \)` form.
8. **Speed** — `build_index()` caches the 185-entry corpus vector matrix to
   `.architect_cache/` keyed by (corpus text, embed model); a warm run is ~76s
   instead of ~4–13 min. `ARCHITECT_BUDGET_S` (default 300) caps a stuck run.

**Milestone (2026-08-29): the full CEGIS loop closed end-to-end against a live
LLM.** Prompt: *"server announces a per-unit price p for client effort; each
client maximises p·e − ½c·e²; ensure participation."* Model:
`openai/gpt-oss-120b` via the NVIDIA API. Result: `mode=Synthesis`,
`status=VERIFIED`, 1 iteration, 76 s. The verified mechanism is the follower
utility `p_i·e_i − ½c·e_i²` with certificate: `FOC ⇒ e_i* = p_i/c` (concavity
from the unique critical point), `IR: U(e_i*, ·) ≥ 0` — entry-specific, not a
template. Free text in, formally verified mechanism + certificate out, no stub
anywhere in the run.

### Convergence (2026-08-29): 10/10 VERIFIED on the Stackelberg prompt

Ran the same follower-effort prompt 10 times (`openai/gpt-oss-120b`, index built
once): **10/10 `VERIFIED`**, all Synthesis mode. Iterations-to-`VERIFIED`: min 1,
max 3, mean 1.4, median 1 (7/10 first-shot; the rest used the repair loop).
Wall-clock 13.7–102.9 s, mean 42.4 s. Reproducible, not a one-off.
(`scratchpad/convergence.py`; run `python -m architect.eval.live_smoke` for the
per-family breadth check.)

### Breadth (2026-08-29): `live_smoke.py` — 2/4 VERIFIED, first pass

`src/architect/eval/live_smoke.py` runs the real loop once per family
(auto-routed) plus a forced-Hybrid run, printing status + transcript tail.
First pass (`gpt-oss-120b`):

| Case | Result | Note |
|---|---|---|
| Stackelberg (effort) | **VERIFIED**, 1 iter | stable |
| Hybrid (forced) | **VERIFIED**, 5 iters | model proposed a Contract mechanism `p_i − θ_i` with two-sided IC → real posynomial certificate. Proves Contract works. |
| Contract (dedicated) | FAILED, 4 iters | model dropped the `ir` key once; mechanisms came back `UNKNOWN` (type-ordering unresolved) |
| VCG (auction) | FAILED, wall-clock | always `VERIFIED_TEMPLATE` — "payment rule does not match a standard VCG form" |

Fixes across three passes:
- Contract `meta.type_variable` auto-derived from the IC AST (the symbol on both
  sides of the two-term Sum) when the model omits it — the `UNKNOWN` cause.
- Prompt: "NEVER omit ir"; "for VCG the payment must be a recognised truthful
  form"; "for Contract author utility/ic/ir as fully CONCRETE closed forms, no
  Unknown nodes" (Synthesis mode's "use Unknowns" instruction was conflicting).
- `ARCHITECT_LLM_TIMEOUT_S` (default 150s) + 1 retry on the OpenAI client — a
  single hung call could otherwise block ~10 min past the wall-clock budget
  (VCG pass 2 ran 625 s / 0 iterations).

**Pass 3 (2026-08-29): 4/4 VERIFIED.**

| Case | Result | Certificate |
|---|---|---|
| Stackelberg | VERIFIED, 1 iter, 24 s | FOC `e* = p/c`; IR ≥ 0 |
| Contract | VERIFIED, 1 iter, 12 s | posynomial IC(0,1)/IC(1,0)/IR(0)/IR(1) ≥ 0 |
| VCG | VERIFIED, 8 iters, 179 s | model reframed the reverse-auction as a 3-type screening contract; 6 IC + 3 IR constraints ≥ 0 |
| Hybrid | VERIFIED, 1 iter, 12 s | Contract posynomial certificate |

Every verifiable family now produces a formally verified mechanism from free text
through the live loop.

### First eval run (2026-08-29): 4/5 VERIFIED, IC regret 0 on all four

`python -m architect.eval.run_eval`, `gpt-oss-120b`. See `docs/eval-results.md`.

| Benchmark | mode | status | iters | wall | mechanism family found |
|---|---|---|---|---|---|
| cross_device_quadratic | Hybrid | VERIFIED | 1 | 19 s | Stackelberg |
| hierarchical_edge | Hybrid | VERIFIED | 1 | 16 s | Stackelberg |
| iiot_log_linear | Synthesis | **FAILED** | 12 | 355 s | Contract (stuck VERIFIED_TEMPLATE) |
| myerson_single_item | Synthesis | VERIFIED | 7 | 176 s | Contract |
| vcg_redistribution | Hybrid | VERIFIED | 3 | 44 s | Stackelberg |

**Reads honestly:** the loop reliably produces a *formally verified, zero-IC-regret*
mechanism (4/5), but it does so by **reframing the problem into whichever family it
can verify fastest** — usually Stackelberg follower-effort or a linear Contract
menu. Only `hierarchical_edge` (expected Stackelberg) matched its natural family.
`iiot_log_linear` FAILED because the model kept proposing a linear-cost screening
menu for a problem whose utility is `R_i·ln(1/θ_i)` — the transcendental form the
model dodges and Track 3 can't confirm entry-specific.

### What is left

1. **Family fidelity** — Resolved (Option A): the loop is hard-constrained to
   `expected_family` and FAILs in-family rather than reframing. Per-family verify
   rate is now the eval's primary honesty metric — see docs/eval-results.md.
   The gate is currently exercised through the eval harness; having Intake
   extract `expected_family` from free text is future work.
2. **`ln`/transcendental utilities** — `iiot_log_linear` shows the loop can't yet
   handle log-linear settings; the model won't produce the `Func{ln}` form and
   Track 3 doesn't engage. Prompt work + possibly a Track 3 hint path.
3. **Second model** — everything is `gpt-oss-120b`. Re-run the eval with a
   stronger model (DeepSeek-v4, a frontier API) to show the result isn't
   model-specific.
4. **Baselines** — Liu et al. (2502.12203), RegretNet on the FL benchmarks. The
   long pole; scope in parallel.
5. Deferred, non-blocking: `\pi`/`\lambda` Greek-map collision; budget-constraint
   plumbing half-wired.
- **Eval harness** (`python -m architect.eval.run_eval`) → `docs/eval-results.md`
  (5 benchmarks × {verified-rate, iterations, wall-clock, IC regret}) — the
  paper's results table. Ready to run now that the loop closes.
- **Baselines**: Liu et al. (2502.12203) and RegretNet on the FL benchmarks.
- Deferred, non-blocking: `\pi`/`\lambda` Greek-map collision risk;
  budget-constraint plumbing half-wired.

### Verifier proper-check roadmap (planned 2026-08-29)

The 2026-08-29 live eval (`docs/eval-results.md`, `gpt-oss-120b`, 12 benchmarks)
came back **8/12 VERIFIED, all 4 failures VCG**. Combined with the Task D
adversarial soundness suite — which showed the VCG track does no real
entry-specific check (regex on the payment-rule LaTeX shape → canned verdict) and
that all three category verifiers fall back to a generic template that returns
`VERIFIED_TEMPLATE` regardless of the entry's own math — the decision is to give
every covered family a **real solver-backed proof or a real counterexample**.
Sequenced in `docs/superpowers/specs/2026-08-29-verifier-proper-checks.md`:

1. **Phase 1 — Approach C: landed 2026-08-29.** AST goes straight to the solvers; no LaTeX parser in
   the verify path. Most current failures are parser failures, not math failures;
   this makes each per-family checker a bounded job instead of a fight with
   SymPy's LaTeX parser. Flag: `ARCHITECT_AST_VERIFY` (default off). Result: verify_from_ast parity holds, corpus regression frozen 25/73/2/5, live_smoke 4/4 VERIFIED with zero parse entries.
2. **Phase 2 — real VCG check: landed 2026-08-30.** `verify_vcg_dsic`
   (`src/tracks/vcg_dsic.py`) is a finite-bid-grid Z3 proof of `∀ lie:
   u_i(honest) ≥ u_i(lie)` + IR, wired into `verify()` and `verify_from_ast`;
   the regex path was demoted to the new `VERIFIED_SHAPE` verdict (not a proof,
   kept as a fallback through Phase 3, delete in Phase 3b). Generation: Synthesis
   mode now fixes the VCG payment to Clarke-pivot form and searches only the
   affine-maximizer weights. Result: **0** corpus VCG entry-specific DSIC proofs
   (33 `VERIFIED_SHAPE`; parser widening to the corpus `\frac`/`argmax`
   allocation forms is Phase 3); a synthesized highest-bidder+Clarke mechanism is
   certified `VERIFIED` (Vickrey). Corpus real machine-checked proofs: **6**
   (Contract 5, Stackelberg 1).
3. **Phase 3 — widen the entry-specific parsers + AST-native completion: landed
   2026-08-31.** Track 2/3/4 seams SymPy-native; `verify_from_ast` does real
   multi-track routing (`_classify_ast`); VCG `Alloc` AST node + Synthesis emits
   it; Track 3 box search extended (`max_ic_regret_over_box`, δ-bounded IC-regret).
   **0 corpus flips** (plan-permitted partial landing — every widened parser
   dead-ends on a second blocker per corpus entry); corpus byte-identical to
   baseline 6/59/33/2/5; suite 204→262. `ARCHITECT_AST_VERIFY` stays default off,
   flip code-ready, gated on an API-blocked eval. The `VERIFIED_TEMPLATE` →
   `UNKNOWN` fail-close pass (~61 entries drop — the honest number) was **deferred
   by explicit decision** to a separate round.
4. **Phase 4 — bounded coalition / small-Shapley** (k ≤ 3): encode `v(S)`, prove
   IC for Shapley payments over the restricted coalition space. **NOT this round.**

Formal ceiling (named, not to be coded past): general Shapley IC (Roberts),
n−1 collusion, VCG under interdependent values, output-signal manipulability.

### Design docs

`docs/superpowers/specs/2026-08-28-architect-cegis-loop-design.md` (spec),
`docs/superpowers/specs/2026-08-29-verifier-proper-checks.md` (verifier
proper-check roadmap — active),
`docs/superpowers/specs/2026-08-28-ast-native-verifier-future-scope.md`
(research future-scope: novel certified mechanism, transcendental IC),
`docs/superpowers/specs/2026-08-29-novelty-hardening.md` (merged),
`docs/superpowers/plans/2026-08-28-architect-cegis-loop.md`,
`docs/superpowers/plans/2026-08-29-novelty-hardening.md`.

---

### Key Differentiation from Prior Work

> Full positioning against 2024–2026 work: see docs/related-work.md.

A February 2025 paper (Liu, Guo, Conitzer — arXiv 2502.12203) does LLM-based automated mechanism design but enforces IC **by construction** via template-specific structural fixing — Myerson monotonicity repair and critical-price construction for pre-specified auction templates (single-item VCG, multi-bidder redistribution). Their Monte Carlo simulation estimates expected revenue as a performance metric, not to verify IC. This approach does not generalise: the fixing procedures are hard-coded for a small number of known mechanism templates and produce no machine-checkable proof certificate for novel or arbitrary LLM-proposed forms.

This project verifies IC **formally** — the verifier either produces a mathematical proof certificate or a guaranteed counterexample for any mechanism expressible in the **discrete-type screening + single-parameter Stackelberg + standard-form VCG** fragment; outside this fragment the verifier returns `UNKNOWN` / `VERIFIED_TEMPLATE` and the loop reports non-success. On the 105-entry verifiable tier, 25/105 entries reach entry-specific `VERIFIED` today. "Provably correct" means something here that it does not in 2502.12203. This formal guarantee, combined with the FL-specific corpus, is the primary research contribution.

**What we adapt from Liu et al. (2502.12203) — applied differently:**

**1. Monte Carlo as a cheap pre-filter (not the final check)**

Liu et al. use Monte Carlo simulation to estimate expected revenue — a performance metric, not IC verification. IC in their pipeline is handled by hard-coded structural fixing, not sampling. We use Monte Carlo as a *pre-filter* before the formal verifier: a proposal that fails a quick sampling check gets rejected immediately without invoking Z3/SOS. This cuts compute — most bad proposals fail fast. The formal verifier then certifies the survivors with a proof certificate, which Liu et al.'s pipeline cannot produce.

```
LLM proposes mechanism
      │
Monte Carlo: sample 1000 client types, check if any profit from lying
      │
obvious fail → immediate counterexample, skip formal verifier
passes MC    → run Z3 / SOS / dReal for formal certification
```

**2. Constrained generation framing**

Liu et al. leave one mechanism component blank and ask the LLM to fill only that piece rather than generating everything from scratch. We apply the same principle: instead of prompting "design a complete FL incentive mechanism," we prompt "given this allocation rule retrieved from the corpus, propose a payment rule that maintains IC." One piece at a time is more reliable than full generation.

**3. IC regret as a quantitative metric**

IC regret measures the maximum utility gain any client type achieves by lying across all sampled types. For formally verified mechanisms this is exactly 0. For Track 3 (dReal, approximate), it gives a numerical bound when exact proof is unavailable. It also makes results directly comparable to Liu et al. and RegretNet on a shared scale.

**4. Classic benchmarks as baseline evaluation**

Their benchmarks — Myerson's virtual valuation (single item), VCG redistribution (multi-bidder), correlated bidder auctions — are standard test cases from the 1980s–2000s literature, not invented by their paper. We use these as baseline evaluation (known optimal solutions exist to check correctness against) and add FL-specific benchmarks their system has no corpus knowledge for: cross-device FL with quadratic costs, hierarchical FL with edge servers, IIoT FL with log-linear utilities.

### What Can Be Invented — and What Cannot

Deep research (July 2026, 45+ sources) established the theoretical boundaries for new mechanism generation.

**The complete family of DSIC mechanisms is known.**

Roberts' theorem (1979) proves that the only deterministic strategy-proof mechanisms on **unrestricted domains with three or more alternatives** are **Affine Maximizers**: rules that choose the outcome maximizing `Σ wᵢ·vᵢ(o) + γ(o)`, where `wᵢ` are per-agent weights and `γ(o)` are outcome-specific boosts. VCG is the unit-weight case (`wᵢ=1, γ=0`). This is the theoretical backbone for Synthesis mode — on unrestricted domains satisfying Roberts' conditions, searching over weight/boost parameters is exhaustive search over the complete space of truthful mechanisms, not trial-and-error.

> **Domain caveat (important for FL settings):** Roberts' completeness result requires an unrestricted type/outcome space. FL incentive settings typically operate on *restricted* domains (bounded type spaces, single-parameter bids, constrained outcome sets). On restricted domains, DSIC mechanisms are not fully characterised by Roberts; the AMA family is a sound and systematic subclass but not exhaustive (Lavi–Mu'alem–Nisan 2003; Mishra–Sen 2012). Synthesis mode should be described as "exhaustive search within the affine-maximizer class" for FL-specific settings, not "complete over all DSIC mechanisms." This distinction matters if a reviewer checks the domain assumptions.

**Three property combinations are provably impossible.**

| Impossibility | What it rules out | Escape |
|---|---|---|
| Green-Laffont | Efficiency + DSIC + Budget Balance simultaneously | Use Bayesian IC (AGV) or accept bounded subsidy |
| Myerson-Satterthwaite | Efficient bilateral trade + IR + BB without subsidy | Scale to many clients (impossibility vanishes asymptotically) |
| Multi-parameter | Deterministic truthful mechanism with finite approximation for multi-attribute bids | Domain restriction or randomization |

Any corpus entry or generated mechanism claiming all three properties of Green-Laffont simultaneously is technically suspect and should be flagged.

**Four FL-specific properties break standard mechanism proofs.**

Standard VCG and Contract theory were designed for general markets. FL violates four assumptions those proofs rely on:

1. **Non-IID data → interdependent values.** Client A's data value depends on what clients B, C, D have. VCG IC assumes independent private values — this breaks in non-IID FL. Z3 proofs remain valid *within the formal model* that assumes independence; they do not prove correctness in real heterogeneous deployments.
2. **Unverifiable data quality → contract theory breaks.** Contract theory conditions payment on verifiable output. Clients can submit fake gradients. The payment rule's IC proof holds mathematically; whether the output signal is manipulable is a deployment question.
3. **Shared bandwidth → communication externalities.** One client's participation raises costs for others. Any mechanism assuming independent participation costs is formally invalid under congestion.
4. **Collusion → individual IC proofs are insufficient.** Z3 proves ∀ individual deviations. A coordinated n-client coalition is a joint deviation requiring different constraint encoding. Z3 can encode 2–3 client coalitions; n-1 collusion is intractable.

Each corpus entry and each generated mechanism should state explicitly which of these four failure modes it has addressed and how.

**Existence result: FL-specific IC+IR+no-free-rider is achievable.**

FACT (NeurIPS 2024, arXiv:2405.13879) is the first mechanism formally proving IC + IR + no-free-rider simultaneously for FL without requiring observable data quality. It uses a penalty rule + sandwich competition technique — a new mechanism family not derived from VCG, Contract, or Stackelberg. It is in the corpus as `2405_13879` (previously also filed separately as `Fact2024freerider_fl`; the two were merged 2026-07-18 — see the corpus-quality note above and the open categorization question in category 4 below).

**Most valuable hybrid combination: Stackelberg + Contract.**

Contract theory resolves hidden client types (information asymmetry). Stackelberg handles sequential competition for reward budget. FL frequently needs both simultaneously. Their combination achieves IC + IR + Stackelberg Equilibrium in a single mechanism — formally proven in 2024 literature. Z3 can verify both the IC contract conditions and the Stackelberg equilibrium existence in a single pass.

### Why the Corpus Matters

The LLM Architect is not trained from scratch. It learns by reading existing FL incentive mechanism papers — **185 (setup, mechanism) pairs** (`corpus.json`, measured 2026-07-18; grows over time — check `len(json.load(open("corpus.json")))` for the current count rather than trusting this number) where experts already derived the correct rules. The corpus is the **ground truth knowledge base** the Architect draws on.

> **Corpus-quality pass (2026-07-17):** the corpus previously reported 253 entries. Two systemic problems were found and fixed:
> 1. **35 duplicate entries** — every paper stored under both its raw arXiv ID (e.g. `2304_04162`) and a human-readable name (e.g. `Chu2023hierarchical`) turned out to frequently have *both* names filed as separate corpus entries pointing at the byte-identical source PDF (32 duplicate groups found via PDF hash comparison). Reconciled into one entry per paper, preferring the more complete/accurate side where the two disagreed (a few pairs had genuinely different content, not just formatting — one pair's `budget_balance_type` disagreement traced back to a real mislabeling, corrected against the source PDF).
> 2. **23 miscategorized Stackelberg entries** — confirmed via direct PDF reads to be either not federated learning papers at all (2 were pure scraping contamination: satellite task allocation, autonomous racing), not actually Stackelberg games (symmetric Nash games with no price-setting leader), or fundamentally different structures (security/attacker games, abstract game theory with no FL content and no concrete formula ever instantiated). Removed rather than recategorized — none fit any of the corpus's other six categories either.
>
> Net effect: Stackelberg category went from 63 to 32 entries; total corpus from 253 to 195. The `num_types=10` pattern recurring identically across several unrelated duplicate pairs suggests an early corpus-generation pass had a bad default for unspecified type counts — worth checking `tools/extract.py` if this resurfaces in future entries.
>
> **Second corpus-quality pass (2026-07-18):** 195 → 185. Two more problems, both caught by re-checking "no local PDF" entries against the corpus by *title* rather than just filename (filename matching alone had missed them):
> 1. **7 entries removed** for having no source PDF anywhere, after confirming (by both filename and title/venue search) that no copy exists: `Care2025infocom_fl`, `Chen2025stackelberg_traffic`, `Li2024perf_pricing`, `Raim2025hierarchical_fl`, `Tang2024afl_survey`, plus `Chen2020wireless_auction` and `Le2020cellular_auction` — the latter two turned out to be duplicates (`Chen2020wireless_auction` was an empty-data, no-PDF third copy of `Le2020cellular_auction`/`Le2021cellular_auction`, which share an identical title and identical mechanism data; `Le2020cellular_auction`'s own stored `notes` field already declared itself a duplicate of `Le2021cellular_auction` from an earlier pass, but the actual removal had never been executed).
> 2. **1 merge:** `Fact2024freerider_fl` (VCG, no local PDF) and `2405_13879` (Shapley, gold-tier, has a PDF) turned out to be the same paper — "FACT or Fiction: Can Truthful Mechanisms Eliminate Federated Free Riding?" (NeurIPS 2024) — filed twice under different categories with overlapping `ic_condition_latex`/`ir_condition_latex` content. Merged into `2405_13879` (kept the PDF-backed, already-reviewed entry); `Fact2024freerider_fl`'s unique `payment_rule_latex` content is preserved there as `payment_mechanism_latex`. **`Fact2024freerider_fl` no longer exists as a corpus entry — any reference to it elsewhere in this document or in code refers to `2405_13879` now.** See the Shapley section (category 4 below) for the still-unresolved question of whether `2405_13879` even belongs in the Shapley category at all.
>
> **Manual PDF data-completion pass (2026-07-18):** separately from the removals above, every entry across VCG/Contract/Stackelberg/Shapley still missing a core relation field (payment rule, IC/IR constraint, follower utility/FOC/best-response, characteristic function, etc.) was individually read from its source PDF and either filled with an exact transcription or explicitly left null with a documented reason (paper solves numerically, different mechanism family, genuinely no formal constraint stated, etc.) — not just re-run through the original Groq extraction. Full field-coverage numbers are in the "Verdict Semantics" section above. This is a one-time catch-up; the ~80 entries in the RAG-only categories (RL 26, Valuation 48, Naive 6) were out of scope for this pass since they're never sent through the formal verifier in the first place.

> **Third corpus-quality pass (2026-07-18, evening):** 25 entries (13 Contract, 12 Stackelberg) had `key_assumptions` lists copied verbatim from the extraction-prompt *examples* in `tools/prompts.py` — prompt-anchoring contamination, 8 of them contradicting the entry's own stored math (e.g. "quadratic cost" on a paper whose utility is exponential). Sanitized fail-closed: only items corroborated by the entry's own formal fields were kept; everything else moved into `notes` with the reason. Lesson for future extraction prompts: never put concrete example values in a field the LLM fills — describe the field instead.
>
> ⚠️ **`entries/` is stale and dangerous:** it holds 253 files — the pre-cleanup corpus. The rebuild command in `tools/run.py` would resurrect every removed duplicate and miscategorized entry and erase the verdict wiring. `corpus.json` is the single source of truth; archive `entries/` or regenerate it from `corpus.json` before any rebuild.

This means the corpus must be:

- **Truthful** — every entry must reflect what the actual PDF says, not a hallucinated or misremembered title/field
- **Mathematically complete** — IC, IR, payment rule, and objective must be filled in from the paper, not left as "unspecified"
- **Formally aligned** — the math must be in a form the formal verifier can consume (LaTeX → SMT constraints)

A corrupt or sloppy corpus teaches the LLM the wrong patterns. Garbage in, garbage out — except here the output is a legally or economically consequential reward rule.

**Planned schema improvements (not yet implemented):**

1. **`failure_modes_addressed` field (per entry):** Each entry should state which of the four FL-specific mechanism breaks it handles — non-IID data, unverifiable quality, communication externalities, collusion — and how. Entries that don't address these breaks are formally incomplete for FL deployment contexts even if their math is correct within the model.

2. ~~**Green-Laffont validator check**~~ **Implemented 2026-07-17** (`_check_green_laffont` in `tools/validate.py`) — flags any VCG entry simultaneously claiming dominant-strategy IC, strong budget balance, and a Clarke-pivot-shaped payment, since Green-Laffont proves these three cannot coexist.

---

## The Seven Mechanism Families the Corpus Covers

The corpus is split into two tiers based on the Z3 Verifier's reach:

**Verifiable tier (categories 1–4):** The multi-track verifier can check these mathematically. The Architect's primary output must fall into one of these four families.

**RAG-only tier (categories 5–7):** The verifier cannot check these (RL policies are black-box; naive rules have no IC proof). They exist in the corpus so the Architect knows the full landscape — when a simpler or RL-based approach exists in the literature — and can justify its choice of a verifiable mechanism. `verifier.py`'s `_RAG_ONLY` filter excludes these categories from the Z3 pipeline entirely, before verification is even attempted — as of 2026-07-18 that's RL (26 entries), Valuation (48), Naive (6): 80 of the corpus's 185 entries, leaving 105 in the verifiable tier.

---

### 1. VCG / Auction

Server runs an auction; clients bid their costs/values. VCG payment rule makes truthful bidding a dominant strategy. Double auctions allow two-sided markets.

**Corpus role:** Primary output category for competitive client selection problems. Retrieved when the environment involves budget constraints, two-sided markets, or heterogeneous client valuations. Z3 verifies IC in dominant strategies directly from the bid and payment functions.

**Formal content required:** Bid space, allocation rule `x(b)`, payment rule `p(b)`, client utility function `u_i = v_i · x_i - p_i` (including valuation `v_i(·)` and cost `c_i(·)` in LaTeX), proof that `IC: u_i(b_i = v_i) ≥ u_i(b_i' ≠ v_i)` holds in dominant strategies, proof that `IR: u_i ≥ 0`, Budget Balance condition `BB: Σ p_i ≤ Revenue`.

**Key mathematical assumptions:** (e.g., independent private values, risk neutrality, finite type space, single-dimensional bids — extract explicitly from paper).

### 2. Contract Theory

Server offers a menu of (effort, reward) pairs to clients with privately known types. Each type self-selects its intended contract (screening IC). Client utility is non-negative (IR). Server maximizes profit under information asymmetry.

**Corpus role:** Primary output for private-type environments where the server cannot observe client costs or data quality. Retrieved when the problem involves information asymmetry and type screening. Z3 verifies the IC screening constraints and IR participation constraints algebraically over the contract menu.

**Formal content required:** Type distribution, contract menu `{(e_i, R_i)}`, client utility function `u_i = R_i - c_i(e_i)` (including cost function `c_i(·)` and any valuation `v_i(·)` in LaTeX), IC screening constraint `u_i(e_i, R_i) ≥ u_i(e_j, R_j)` for all `j ≠ i`, IR participation constraint `u_i ≥ 0`, server objective `max Σ[V(e_i) - R_i]`, Budget Balance condition `BB: Σ R_i ≤ Budget`.

**Key mathematical assumptions:** (e.g., convexity of cost function, risk neutrality, single-crossing condition (Spence-Mirrlees), finite discrete type space — extract explicitly from paper).

### 3. Stackelberg Game

Server (leader) announces a pricing rule; clients (followers) best-respond. The mechanism design question is: what pricing rule `p(·)` induces clients to exert socially optimal effort?

**Corpus role:** Primary output for leader-follower pricing problems where the server commits to a rule before clients decide. Retrieved when the problem involves sequential decisions, participation pricing, or edge computing cost structures. Z3 verifies equilibrium existence and follower IR over the best-response function.

**Formal content required:** Leader objective `max_{p} Π(p, e*(p))`, follower best-response `e_i*(p)` derived from Follower's First-Order Condition (FOC) `∂u_i/∂e_i = 0` in closed LaTeX form, client utility function `u_i(e_i, p) = p_i · e_i - c_i(e_i)` (including cost function `c_i(·)` and valuation `v_i(·)` in LaTeX), IR for followers `u_i(e_i*(p), p) ≥ 0`, Stackelberg equilibrium existence proof.

**Key mathematical assumptions:** (e.g., concavity of follower objective, differentiability of cost function, unique interior optimum, complete information on leader side — extract explicitly from paper).

### 4. Shapley-Based Payment *(verifiable in theory — 0 qualifying entries currently)*

Shapley value measures each client's marginal contribution to the global model, used as a payment rule. Acceptable only if the paper proves IC/IR properties or explicitly designs a payment mechanism — pure contribution measurement without mechanism analysis does not qualify.

**Current corpus status (updated 2026-07-18): 4 entries in this category** — `2405_13879` (gold), `2502_08248`, `2605_11889`, `2606_18384`. All four self-report `ic_proof_present: true` and `ir_proof_present: true`, which is what let them pass the schema's Shapley hard-gate (`tools/validate.py`). **These claims are not independently checked by the verifier** — `verify_shapley()` in `src/tracks/track1_z3.py` unconditionally returns `UNSUPPORTED` for every Shapley entry regardless of the flags ("Roberts' Theorem: Shapley IC/IR is intractable in Z3 for general domains"), by design. That's a defensible choice (general coalitional-game IC/IR is out of scope for Z3), but it means these 4 entries carry a paper-asserted IC/IR claim that has never been machine-checked, sitting in the "verifiable tier" alongside entries that have been. If the Architect or a RAG layer ever treats `ic_proof_present` as equivalent to `z3_validated`, that's a silent trust gap worth closing (e.g. flagging these 4 explicitly as "claimed, unverified" in any downstream consumer). The remaining Shapley-adjacent papers in the corpus (measurement-only, no IC/IR claim) are correctly reclassified to Valuation (RAG-only, category 6) by the hard-gate. The reasons Shapley mechanisms are rare in this literature at all:

> **Open question, flagged 2026-07-18, not yet resolved: `2405_13879` may not actually belong in this category.** A full read of the paper (all pages including appendices) found no coalition characteristic function `v(S)` and no reference to the Shapley value anywhere in the text — its actual mechanism (penalty rule + "sandwich" truthfulness competition against free-riding) has nothing to do with coalitional game theory. It's currently kept as Shapley only because that's where it already lived before this was noticed, and because it absorbed the merged `Fact2024freerider_fl` entry (see the corpus-quality note above) rather than being reclassified at the same time. This is the one remaining `tools/validate.py` failure on the corpus as of 2026-07-18 (a gold-tier Shapley entry with null `characteristic_function_latex`/`shapley_formula_latex` — correctly left null rather than fabricated, but the real fix is recategorizing the entry, not filling those fields). Needs a human decision on where it actually belongs — possibly a new or existing non-Shapley category, since its mechanism (penalty + sandwich competition) doesn't fit VCG/Contract/Stackelberg either. **Interim resolution 2026-07-18:** demoted gold→silver (with an explanatory note in the entry) so the gold-gate no longer demands Shapley-specific LaTeX fields the paper genuinely does not contain — `tools/validate.py` is now 185/185. Final categorization still needs the human decision.
- Shapley is O(2^N) to compute — impractical to base a real payment rule on it for large N
- Strategic manipulation of Shapley is hard to model formally, so authors skip the IC proof

**What would qualify for this category:** A paper that explicitly proves `u_i(truthful) ≥ u_i(misreport)` when payments are Shapley-based — e.g., by restricting to small coalitions, using approximations with formal IC bounds, or proving IC under specific FL data assumptions.

**Practical implication:** The Architect will not output a verifiable Shapley mechanism until such a paper exists. The 48 Valuation entries (category 6) teach it when contribution-fair measurement is appropriate and which approximation methods are tractable.

**Corpus role:** Retrieved for contribution-fair payment problems where marginal contribution is the natural basis for rewards. Only included when IC/IR is analyzed, making multi-track verifier certification possible.

**Formal content required:** Characteristic function `v(S)`, Shapley payment `φ_i = Σ_{S⊆N\{i}} [|S|!(|N|-|S|-1)!/|N|!][v(S∪{i})-v(S)]`, IC/IR proof or payment mechanism design.

**Key mathematical assumptions:** (e.g., superadditivity or monotonicity of `v(S)`, symmetry axiom, efficiency axiom, dummy player axiom — extract explicitly from paper).

---

### 5. RL-Based Incentive Mechanisms *(RAG-only)*

Papers that use DQN, PPO, or multi-agent RL to dynamically adjust client rewards without deriving a closed-form payment rule. The policy is a black-box neural network — Z3 cannot verify it. These papers exist in the corpus so the Architect knows when a GT mechanism is too complex for the environment and an RL fallback is the practical choice in the literature.

**Corpus role:** Retrieved as context when the problem has high dimensionality or non-stationary client populations where a closed-form rule is intractable.

**What to capture:** RL algorithm used, state/action/reward definition, convergence claim, any IC/IR approximation guarantees.

**Key mathematical assumptions:** (e.g., Markov property, stationarity of environment, discount factor bounds, finite action/state space — extract explicitly from paper).

### 6. Non-Shapley Data Valuation & Pricing *(RAG-only)*

Alternatives to Shapley for measuring client contribution: gradient-norm-based valuation, mutual information metrics, reputation scores, market equilibrium pricing, FedToken-style proportional rewards. Shapley is O(N!) — these exist because 10,000-client deployments need lightweight options.

**Corpus role:** Retrieved when the problem specifies large client count, latency constraints, or "fast valuation." The Architect learns to propose a lightweight mechanism instead of a Shapley-based one.

**What to capture:** Valuation function definition, computational complexity, any fairness or IC approximation claim.

**Key mathematical assumptions:** (e.g., independence of client contributions, monotonicity of valuation metric, i.i.d. data assumption if any — extract explicitly from paper).

### 7. Naive / Baseline Mechanisms *(RAG-only)*

Simple reward rules with no game-theoretic derivation: proportional payment (pay proportional to dataset size), equal split, or FedAvg with no incentive layer. These are the baselines every paper benchmarks against.

**Corpus role:** The Architect must know what "bad" looks like. If it retrieves naive baselines alongside sophisticated mechanisms, it understands the Pareto frontier of complexity vs. optimality and won't propose a VCG auction when a proportional rule already satisfies IC/IR for that environment.

**What to capture:** Rule definition, known failure modes (free-riding, collusion), environments where it surprisingly works.

**Key mathematical assumptions:** (e.g., homogeneous client types, fixed dataset sizes, no strategic behavior assumed — extract explicitly from paper, or note "no formal assumptions stated").
