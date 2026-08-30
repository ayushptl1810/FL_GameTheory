# Phase 2 Leftovers + Phase 3 — Verifier Widening & AST-Native Completion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the verifiers cover more of the corpus and the loop's output — cleanly, AST-native — WITHOUT a fail-close pass. Corpus verdicts may only improve (more real `VERIFIED`) or stay; no entry regresses, no non-target verdict moves.

**Architecture:** Three parts. (A) close the Phase-2 VCG encoder gaps so `verify_vcg_dsic` can prove more forms. (B) finish Approach C — make the Track 2/3/4 seams consume SymPy directly, wire real multi-track routing into `verify_from_ast`, and give VCG a real allocation AST node so the loop stops carrying LaTeX in `meta`. (C) widen the Track-1 entry-specific LaTeX parsers (`\sum_{i∈S}`, multi-subscript, function-call notation) and add multivariable transcendental IC. No `VERIFIED_TEMPLATE` → `UNKNOWN` fail-close this round (deferred by explicit decision). No Phase 4 (coalition / Shapley) this round.

**Tech Stack:** Python 3, pytest, Z3 (`z3-solver`), SymPy, CVXPY/SCS, mpmath, NumPy.

**Spec:** `docs/superpowers/specs/2026-08-29-verifier-proper-checks.md` (Phases 2b + 3), `docs/superpowers/specs/2026-08-29-phase2-vcg-real-check-design.md` (VCG encoder), `docs/superpowers/specs/2026-08-28-ast-native-verifier-future-scope.md` Part 1 (Approach C).

## Global Constraints

- Run tests from repo root with `PYTHONPATH=src`. Suite is **204 passed / 3 xfailed / 0 failed** on `main` now — stays 0-failed at every task end.
- **Corpus gate — monotone improvement only.** After every task, `PYTHONPATH=src python -m verifier corpus.json` must satisfy ALL of:
  - `VERIFIED` count ≥ 6 and only ever rises;
  - **no entry moves to a strictly-worse verdict** (VERIFIED→anything, VERIFIED_TEMPLATE→UNKNOWN/UNSUPPORTED, VERIFIED_SHAPE→UNKNOWN, …) — diff the per-entry verdict list against `docs/superpowers/notes/phase3-baseline.md` (Task 1);
  - the frozen non-target lines stay put unless a task's own brief says it touches them: `Contract entry-specific`, `Contract template`, `Stackelberg 1/28`, `Track 2 = 4`, `Track 3 = 1`, `Track 4 = 1`, `UNSUPPORTED = 5`.
- **Every newly-`VERIFIED` entry is cross-validated** — the task that flips it records in `docs/superpowers/notes/phase3-new-verified.md`: the entry id, what the parser/encoder now handles, and an independent check (hand-derivation of the IC gap, OR a second track agreeing, OR a Z3 model inspection, OR a cited theorem e.g. Roberts for affine maximizers). A new `VERIFIED` with no cross-validation is a plan failure.
- Fail closed: any parse ambiguity → `UNKNOWN`, never a guessed `VERIFIED`/`COUNTEREXAMPLE`.
- `verify(entry)` stays the corpus API; new checks route through `finalize_verdict`.
- Commit after every task. Do not push, do not open a PR. Stop at the last green commit.
- Branch: `phase3-verifier-widening` off `main` before Task 1.
- The untracked `docs/superpowers/plans/2026-08-30-fl-simulation-validation.md` is NOT part of this plan — never `git add` it.

---

## File Structure

| File | Responsibility | This plan |
|---|---|---|
| `src/tracks/vcg_dsic.py` | VCG grid encoder | Tasks 2–4 |
| `src/tracks/track2_sos.py` / `track3_dreal.py` / `track4_sympy.py` | `*_check_from_sympy` seams | Tasks 5–7 |
| `src/architect/ast.py` | AST node types | Task 9 (`Alloc` nodes) |
| `src/architect/serialize.py` | AST → mechanism dict + LaTeX | Tasks 9–10 |
| `src/architect/ast_verify.py` | `verify_from_ast` routing | Tasks 8–9 |
| `src/architect/synthesize.py` / `architect.py` | Synthesis-mode VCG | Tasks 2, 10 |
| `src/tracks/track1_z3.py` | entry-specific Contract/Stackelberg parsers | Tasks 11–14 |
| `docs/superpowers/notes/phase3-*.md` | baseline, new-verified log, delta | Tasks 1, 15 |

---

## PART A — Phase 2 VCG encoder gaps

## Task 1: Branch + baseline

**Files:** `docs/superpowers/notes/phase3-baseline.md`, `docs/superpowers/notes/phase3-new-verified.md` (create).

- [ ] **Step 1: Branch** — `git checkout main && git checkout -b phase3-verifier-widening`
- [ ] **Step 2: Capture the per-entry verdict baseline**

```bash
PYTHONPATH=src python -m verifier corpus.json | tee /tmp/p3-corpus.txt
PYTHONPATH=src python - <<'PY' | tee /tmp/p3-verdicts.txt
import json, sys; sys.path.insert(0, "src")
from verifier import verify
for e in json.load(open("corpus.json")):
    if e.get("category") in ("RL", "Valuation", "Naive"): continue
    r = verify(e)
    print(f"{e.get('paper_id','?'):40s} {e.get('category',''):12s} {r.verdict:18s} es={r.entry_specific}")
PY
PYTHONPATH=src pytest -q | tail -3
```

- [ ] **Step 3: Write `docs/superpowers/notes/phase3-baseline.md`** — the full per-entry table (all ~105 verifiable-tier entries), the summary block, `204 passed / 3 xfailed`. Also create `docs/superpowers/notes/phase3-new-verified.md` with header `| entry | now handles | cross-validation |`.
- [ ] **Step 4: Commit** — `git add docs/superpowers/notes/phase3-baseline.md docs/superpowers/notes/phase3-new-verified.md && git commit -m "chore: per-entry verdict baseline before Phase 3"`

---

## Task 2: VCG encoder — `WeightedWelfareMax` allocation + Clarke pivot

**Files:**
- Modify: `src/tracks/vcg_dsic.py` (`encode_utility`, `_pick_vcg_allocation` if referenced)
- Modify: `src/architect/synthesize.py` + `src/architect/architect.py` (re-add the menu option Phase 2 removed — now proof-reachable)
- Test: `tests/verifier/test_vcg_dsic.py` (extend)

**Interfaces:**
- `parse_allocation` already returns `ArgmaxWelfare(objective_expr=...)` for `\arg\max`. Task 2 adds a **grid encoding** for it: `encode_utility` handles `ArgmaxWelfare` where the objective is (or reduces to) `\sum_i w_i v_i(x)` with numeric/`Unknown` weights → winner = `argmax_x Σ w_i v_i(x)`, Clarke pivot = `W_{-i}(x*_{-i}) − Σ_{k≠i} w_k v_k(x*)`. Raw-string / not weighted-welfare-shaped → keep raising `NotImplementedError` → `UNKNOWN`.

- [ ] **Step 1: Test** — synthetic single-item, `alloc = \arg\max \sum_i w_i v_i(x)` with `w_i = 1`, Clarke payment → `verify_vcg_dsic` → `VERIFIED` entry_specific=True. A version with `w_1 = 2, w_2 = 1` (affine maximizer) → also `VERIFIED`. A raw-string objective → `UNKNOWN`.
- [ ] **Step 2: RED.**
- [ ] **Step 3: Implement** the `ArgmaxWelfare` branch in `encode_utility`. Winner via Z3: chosen `x` maximises `Σ w_i v_i(x)` over the finite outcome set (`And(obj(x*) >= obj(x'))` for each grid `x'`). Payment: the affine-maximizer Clarke pivot from those weights. A symbolic (unsolved) weight → `UNKNOWN`.
- [ ] **Step 4: Re-add `weighted-welfare-max`** to `_VCG_ALLOC_MENU` (`synthesize.py`) and the VCG Synthesis prompt (`architect.py`). Prompt: "highest-bidder (recommended) or weighted-welfare-max with non-negative per-agent weights; payment fixed to the affine-maximizer Clarke pivot."
- [ ] **Step 5: Corpus check** — recompute; any corpus VCG entry that now reaches real `VERIFIED` → log in `phase3-new-verified.md` (cross-validation: Roberts — the affine-maximizer family is truthful by construction). Non-target verdicts frozen; no entry regresses.
- [ ] **Step 6: Commit** — `feat: verify_vcg_dsic encodes weighted-welfare-max (affine maximizer) + Clarke pivot`

---

## Task 3: VCG encoder — `ProportionalShare` honest handling

**Files:** `src/tracks/vcg_dsic.py`, `tests/verifier/test_vcg_dsic.py`.

**Context:** `_PROP_RE` matches `\frac{f^{α-1}}{\sum f^{α-1}}` — a *fractional* allocation (each bidder gets a share), not a single-winner VCG mechanism; typically a data-valuation payout with no DSIC claim.

- [ ] **Step 1:** Read the corpus entries that hit `_PROP_RE`. Is any claiming DSIC/IC for a Groves payment over a fractional allocation?
  - If **no** (expected): `verify_vcg_dsic` returns `UNSUPPORTED` for `ProportionalShare` with note "fractional-share allocation — not a single-winner VCG mechanism; no DSIC claim". Confirm the corpus gate still passes — `UNSUPPORTED` for a genuinely-out-of-scope mechanism is not "worse" than `VERIFIED_SHAPE` (which was also not a proof); if a reviewer disagrees, use `UNKNOWN` instead.
  - If **yes**: encode expected utility `E[v_i · share_i(b) − p_i]` over the grid and check IC. Only if a concrete entry needs it.
- [ ] **Step 2:** Test — a `ProportionalShare` entry → the chosen verdict, never `VERIFIED` unless genuinely proven.
- [ ] **Step 3:** Corpus check + `phase3-new-verified.md` if anything flipped. Commit — `feat: verify_vcg_dsic handles proportional-share allocation honestly`

---

## Task 4: VCG encoder minor cleanups

**Files:** `src/tracks/vcg_dsic.py`, its tests; `src/tracks/__init__.py` + `src/verifier.py` for the verdict-scope flag.

- [ ] **Step 1: `grid_bounded` scope flag.** A `verify_vcg_dsic` `VERIFIED` is exact *on the grid*, not a general DSIC proof — today that caveat lives only in `.notes`. Add `VerificationResult.grid_bounded: bool = False`; `verify_vcg_dsic` sets it `True` on its `VERIFIED`. `print_summary` prints grid-bounded VERIFIEDs on their own sub-line ("VCG DSIC (grid-exact): N"). `inspect.is_success` still treats it as success (it IS an entry-specific proof, just scoped) — but the flag is machine-readable for a future consumer.
- [ ] **Step 2:** `_SECOND_PRICE_RESERVE` test fixture — encode the reserve `r` for real (`price = max(2nd-highest, r)`), so it proves *second-price-with-reserve*, not plain second-price. Fix the `_MULTI_ATTR` test comment to name the real fail-closed reason. Rename the shadowed `c` in `_synthesize_vcg`.
- [ ] **Step 3:** Gates + `git commit -m "feat: grid_bounded verdict flag; encode reserve price; test cleanups"`

---

## PART B — Approach C completion

## Task 5: Track 2 SOS seam — SymPy-native

**Files:** `src/tracks/track2_sos.py`, `tests/verifier/test_seams.py`.

**Interface:** `track2_check_from_sympy(gap_expr, theta_sym, theta_min, theta_max, *, entry_specific, paper_id) -> VerificationResult` — takes a SymPy IC-gap expression and bounds, NOT `entry: dict`. `verify_track2(entry)` keeps its LaTeX front-end and calls the new signature; everything the old helper re-parsed from `entry` (`_verify_ir_sos`, `_build_*_expr`) is done in the front-end and passed as SymPy exprs.

- [ ] **Step 1:** Read `track2_check_from_sympy` (~line 550) — enumerate every `entry`/`mech` field it reads. Move each read into `verify_track2`'s front-end; pass parsed SymPy results as new params.
- [ ] **Step 2:** Snapshot lock: `tests/verifier/test_seams.py` — the 4 Track-2 corpus entries' `(verdict, entry_specific)` before the refactor.
- [ ] **Step 3:** Refactor (behavior-preserving). `SOS certificate (Track 2): 4` unmoved.
- [ ] **Step 4:** Gates + `git commit -m "refactor: track2_check_from_sympy takes SymPy exprs, no entry re-parse"`

## Task 6: Track 3 interval seam — SymPy-native

Same shape as Task 5 for `track3_check_from_sympy` (`track3_dreal.py` ~line 338). `dReal δ-verified (Track 3): 1` unmoved. Commit — `refactor: track3_check_from_sympy takes SymPy exprs`.

## Task 7: Track 4 Bayesian seam — SymPy-native

Same for `track4_check_from_sympy` (`track4_sympy.py` ~line 355). `Bayesian IC (Track 4): 1` unmoved. Commit — `refactor: track4_check_from_sympy takes SymPy exprs`.

---

## Task 8: `verify_from_ast` — real multi-track routing

**Files:** `src/architect/ast_verify.py`, `tests/architect/test_ast_verify.py`.

**Context:** `_classify_ast(m)` returns 1–4 but `verify_from_ast` routes everything through the Track-1 core. Tasks 5–7 made the seams SymPy-native — wire the real dispatch.

- [ ] **Step 1:** `verify_from_ast` — after `_classify_ast(m)`:
  - track 2 (Pow deg≥2 + continuous) → `ast_to_sympy` the IC gap → `track2_check_from_sympy(...)`.
  - track 3 (Func ln/exp) → `ast_to_sympy` → `track3_check_from_sympy(...)`.
  - track 4 (IndexedFamily / bayesian meta) → `ast_to_sympy` → `track4_check_from_sympy(...)`.
  - else / on `None`/`UNKNOWN` from a non-Track-1 track → fall through to the Track-1 core (mirror `src/verifier.py::verify`'s fall-through order).
- [ ] **Step 2:** Tests — a `Func("ln", ...)` Contract Mechanism the Track-1 core would `UNKNOWN` now reaches Track 3; a `Pow` deg-2 continuous Mechanism reaches Track 2. Parity: `verify_from_ast` verdict == `inspect_mechanism` (LaTeX path) verdict on a transcendental fixture.
- [ ] **Step 3:** Gates — corpus untouched (`verify_from_ast` not on corpus path); non-VCG frozen. `git commit -m "feat: verify_from_ast routes to Track 2/3/4 seams by _classify_ast (real multi-track)"`

---

## Task 9: VCG allocation AST node

**Files:** `src/architect/ast.py`, `src/architect/serialize.py`, `src/architect/ast_verify.py`, tests.

- [ ] **Step 1:** `ast.py` — add `Alloc` union: `AllocHighest()`, `AllocTopK(k: int)`, `AllocWeightedWelfare(weights: list[str])`. Add `Mechanism.allocation: object | None = None`. `validate_ast` covers them.
- [ ] **Step 2:** `serialize.py` — `render(m)` for VCG emits `allocation_rule_latex` from `m.allocation` (`AllocHighest` → `x_i = 1 \text{ if } b_i = \max_j b_j`, etc.) and `payment_rule_latex` = the Clarke pivot for that allocation. Round-trip check for the allocation node.
- [ ] **Step 3:** `ast_verify.py` VCG branch — build the `entry` dict from `m.allocation` + the rendered payment, NOT from `meta`. Keep the `meta` fallback only for a Mechanism with `allocation is None` (→ `UNKNOWN` if `meta` also lacks it).
- [ ] **Step 4:** Tests — a `Mechanism(category="VCG", allocation=AllocHighest())` → `verify_from_ast` → `VERIFIED` with NO `meta` allocation key. AST↔LaTeX parity on it.
- [ ] **Step 5:** Gates + `git commit -m "feat: VCG allocation AST node (AllocHighest/TopK/WeightedWelfare); verify_from_ast builds from the node"`

## Task 10: Synthesis emits the allocation node

**Files:** `src/architect/synthesize.py`, `src/architect/architect.py`, tests.

- [ ] **Step 1:** `synthesize` VCG branch — set `m.allocation` to an `Alloc` node (from the menu) instead of injecting `meta["allocation_rule_latex"]`. Weight `Unknown`s for `AllocWeightedWelfare` solved as before. `m.meta` no longer carries the VCG LaTeX.
- [ ] **Step 2:** Update `test_synthesize_vcg.py` — assert `out.allocation` is an `Alloc` node, `out.meta` has no `allocation_rule_latex`, `verify_from_ast(out)` → `VERIFIED`.
- [ ] **Step 3:** Gates + `git commit -m "feat: Synthesis mode sets the VCG allocation AST node (drops meta LaTeX injection)"`

---

## PART C — Track-1 parser widening (RISKY — partial landing acceptable, every new VERIFIED cross-validated)

## Task 11: Contract parser — `\sum` menu aggregation + multi-subscript

**Files:** `src/tracks/track1_z3.py` (`_parse_contract_entry`, `_try_contract_latex`), new `tests/verifier/test_contract_widening.py`.

**Context (Task.md):** ~9 Contract entries with real IC+IR data bail because they have ≥2 distinct type-subscripts, use `n−1` arithmetic instead of a second index symbol, or use `\sum`-style menu aggregation.

- [ ] **Step 1:** Identify the exact bail branches in `_parse_contract_entry` for (a) ≥2 type subscripts, (b) `\sum_{j}`-style aggregation over the menu, (c) `n−1` arithmetic.
- [ ] **Step 2:** Widen ONE class at a time, each behind its own test. ≥2 subscripts: resolve the type family per `type_variable` (declared data) and the menu family per the contract index; the existing type-ordering + posynomial machinery then applies. `\sum` aggregation: expand the finite sum symbolically before `_sp_to_z3`.
- [ ] **Step 3:** For EVERY entry that flips to `VERIFIED`: hand-derive its IC gap, confirm the sign, log in `phase3-new-verified.md`. If the derivation is not clean → leave it `UNKNOWN`.
- [ ] **Step 4:** Corpus gate — `Contract entry-specific` may only RISE; `Contract template` falls by the same amount; nothing else moves. `git commit -m "feat: Contract parser handles multi-subscript + \\sum menu aggregation (N new entry-specific)"`

## Task 12: Stackelberg parser — set/inequality summation bounds

**Files:** `src/tracks/track1_z3.py` (`_try_stackelberg_latex`), new `tests/verifier/test_stackelberg_widening.py`.

**Context (Task.md):** ~10 Stackelberg entries fail because SymPy's LaTeX parser doesn't understand `\sum_{i \in S}` / `\sum_{a \le i \le b}` bounds; the risk is isolating the follower's own term wrong → a silently wrong FOC.

- [ ] **Step 1:** Pre-process `\sum_{i \in S} f(i)` → `f(self) + \sum_{j \in S, j \ne self} f(j)` BEFORE `parse_latex`, where `self` is the follower symbol from `follower_decision`. Treat the rest-of-sum as an opaque symbol `Σ_others` (constant w.r.t. the follower's own decision) so `∂/∂e_i` is exact.
- [ ] **Step 2:** Keep the best-response cross-check (reject on disagreement with `best_response_latex`); any disagreement → `UNKNOWN`, not `VERIFIED`.
- [ ] **Step 3:** Every new `VERIFIED`: confirm the FOC by hand against the paper's stated best response, log it. `Stackelberg entry-specific` may only rise. `git commit -m "feat: Stackelberg parser handles set/inequality \\sum bounds via own-term isolation (N new)"`

## Task 13: Function-call notation `f_{sub}(arg_{sub})`

**Files:** `src/tracks/track1_z3.py` (the `_sp_to_z3` / pre-parse layer), tests.

**Context (Task.md):** ~4 Contract + several Stackelberg entries hit a SymPy limitation on `f_{sub}(\arg_{sub})` function-call notation (it misreads `c_i (P_i)` as a call).

- [ ] **Step 1:** In the pre-parse cleaning layer, rewrite recognised parametric-function calls `c_{i}(e_{i})` → a single symbol `c_i_of_e_i`. Demote to `c_i * e_i` ONLY where a `\cdot`/`*` disambiguates it as a coefficient; otherwise prefer the opaque-symbol rewrite (ambiguous → conservative).
- [ ] **Step 2:** Tests + hand-check every flip. `git commit -m "feat: parser rewrites f_{sub}(arg_{sub}) function-call notation to opaque symbols (N new)"`

## Task 14: Multivariable transcendental IC (Track 3 widen + prompt)

**Files:** `src/tracks/track3_dreal.py` (`check_nonneg_box` / the multi-dim branch), `src/architect/architect.py` (prompt), tests.

**Context:** `iiot_log_linear` and most FL log-utility settings can't be verified entry-specific; the model dodges `Func{ln}` and Track 3's multi-type box search is limited.

- [ ] **Step 1:** Track 3 — extend the interval branch-and-bound to a multi-type transcendental Contract IC box (`R_i·ln(1/θ_i)` shape) over independent type/reward boxes, δ-sound; multi-symbol box counterexamples suppressed to `UNKNOWN` (menu/type symbols are not free params).
- [ ] **Step 2:** Architect prompt — a path that emits `Func("ln", ...)` / `Func("exp", ...)` for a setting whose intake `utility` mentions log/exponential, instead of reframing to a linear menu.
- [ ] **Step 3:** `iiot_log_linear` (and ≥1 more log-linear corpus entry) → `VERIFIED` entry-specific OR an honest δ-bounded IC-regret number. Cross-validate the δ bound. `git commit -m "feat: Track 3 multivariable transcendental Contract IC; Architect emits Func{ln} for log settings"`

---

## PART D — Wrap

## Task 15: Flag-default decision + docs

**Files:** `docs/superpowers/specs/2026-08-29-verifier-proper-checks.md`, `Task.md`, `docs/superpowers/notes/phase3-*.md`.

- [ ] **Step 1:** `ARCHITECT_AST_VERIFY` — keep default **off**; document the flip criteria (a clean full flagged `run_eval` with no verified-rate regression) and that the eval is currently API-blocked. If Tasks 5–9 made the AST path strictly ≥ the LaTeX path on every existing test, note the flip is code-ready and gated only on the eval.
- [ ] **Step 2:** `docs/superpowers/notes/phase3-delta.md` — before/after corpus table, every entry that improved with the reason, the new totals.
- [ ] **Step 3:** Roadmap spec — mark Phase 2 encoder gaps + Phase 3 (parser widening + AST completion) with `✅` and the numbers; note the deferred fail-close and Phase 4 explicitly as NOT in this round.
- [ ] **Step 4:** `Task.md` "Verdict Semantics" — the new real-`VERIFIED` count (VCG + Contract + Stackelberg), the AST-native routing state, transcendental coverage.
- [ ] **Step 5:** `git commit -m "docs: Phase 3 landed — verifier widening + AST-native completion; corpus delta"`

---

## Self-Review

**Spec coverage:** VCG encoder gaps → Tasks 2–4; Approach C completion → Tasks 5–10; Track-1 parser widening → Tasks 11–13; transcendental IC → Task 14; flag default → Task 15. **Excluded by decision:** `VERIFIED_TEMPLATE`→`UNKNOWN` fail-close; Phase 4 coalition/Shapley; the live eval (infra — noted in Task 15). ✓

**Placeholder scan:** Tasks 11–14's parser bodies are described by classification-target + the fail-closed rule + a mandatory per-entry hand-check, not literal regex — deliberate and bounded, same approach that worked for the Phase 2 parsers. Tasks 5–7 are behavior-preserving refactors with snapshot locks. Tasks 2–4, 8–10 have concrete test fixtures.

**Type consistency:** `track{2,3,4}_check_from_sympy` signatures change in Tasks 5–7, consumed by Task 8. `Alloc` node union added in Task 9, consumed by Tasks 9–10 + `serialize`/`ast_verify`. `VerificationResult.grid_bounded` added in Task 4, read only by `print_summary`. `Mechanism.allocation` added in Task 9, set in Task 10. ✓

**Risk note:** Parts A–B are mechanical and low-risk. Part C (Tasks 11–14) is the historically-hard parser work Task.md deliberately deferred; **partial landing is acceptable** — a task that widens the parser but flips 0 entries to a *cross-validated* `VERIFIED` still ships (the widening + tests), any entry it can't cleanly verify stays `UNKNOWN`. The corpus monotone-improvement gate makes a wrong `VERIFIED` a plan failure, caught before commit.

---

## Execution Handoff

Subagent-driven. Tasks 2–10 mid-tier. Tasks 11–14 standard model with careful review — each new `VERIFIED` needs its cross-validation entry in `phase3-new-verified.md` verified by the reviewer, not just the implementer. Task 1 setup, Task 15 docs.
