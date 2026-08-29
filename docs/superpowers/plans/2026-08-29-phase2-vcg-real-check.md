# Phase 2 — Real VCG Check + Constrained Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the VCG track's regex-shape verdict with a real finite-grid Z3 DSIC proof (`verify_vcg_dsic`), constrain VCG generation to Clarke-pivot payment + affine-maximizer weight search, and wire both into the AST path.

**Architecture:** New `verify_vcg_dsic(entry)` encodes allocation `x(b)`, payment `p(b)`, `u_i = Σ v_{i,a}·x_{i,a} − p_i` over a finite type/bid grid and Z3-proves `∀ i, ∀ b_i' on grid: u_i(truthful) ≥ u_i(b_i')` + IR. The dispatcher tries it first; the old regex path becomes a `VERIFIED_SHAPE` fallback (explicitly not a proof). Synthesis mode for VCG fixes the payment to Clarke-pivot and searches only the allocation rule + weights. A seam lets `verify_from_ast` call the real check.

**Tech Stack:** Python 3, pytest, Z3 (`z3-solver`), SymPy, NumPy.

**Spec:** `docs/superpowers/specs/2026-08-29-phase2-vcg-real-check-design.md`. Roadmap: `docs/superpowers/specs/2026-08-29-verifier-proper-checks.md` Phase 2.

## Global Constraints

- Run tests from repo root with `PYTHONPATH=src`. Suite currently **176 passed / 5 xfailed / 0 failed** — stays green (0 failed) at every task end; xfailed count may DROP (Task 6 un-xfails one).
- **VCG verdicts are EXPECTED to move.** The frozen gate for this plan is: **non-VCG verdicts unchanged** — `Contract entry-specific 5 / Contract template 31`, `Stackelberg 1 entry-specific / 28 template`, `SOS (Track 2) 4`, `Track 3 1`, `Track 4 1`. Any task that moves a non-VCG number is wrong.
- Every VCG verdict that changes vs. the Task 1 baseline gets a one-line reason in `docs/superpowers/notes/phase2-vcg-verdict-delta.md` (real proof / real counterexample / grid too big / allocation unparseable / multi-attribute impossible).
- Verdict enum is in `src/tracks/__init__.py`: adding `VERIFIED_SHAPE` (Task 2) also touches `finalize_verdict`, `VerificationResult.__str__`, `src/verifier.py::print_summary`, and `tools/corpus_schema.json` `z3_verdict`.
- New checks still route through `finalize_verdict` — no track hand-builds a verdict string except the documented `VERIFIED_SHAPE` fallback path.
- Fail closed: a parse ambiguity or an allocation cross-check disagreement returns `UNKNOWN`, never `COUNTEREXAMPLE` and never `VERIFIED`.
- Commit after every task (`feat:` / `refactor:` / `test:` / `docs:`). Do not push, do not open a PR. Stop at the last green commit.
- Branch: `phase2-vcg-real-check` off `main` before Task 1.

---

## File Structure

| File | Responsibility | This plan |
|---|---|---|
| `src/tracks/vcg_dsic.py` | **new** — grid encoder + `verify_vcg_dsic` | Tasks 3–4 |
| `src/tracks/__init__.py` | `Verdict` enum, `finalize_verdict`, `VerificationResult` | Task 2 (`VERIFIED_SHAPE`) |
| `src/tracks/track1_z3.py` | `verify_vcg` dispatcher, `_vcg_check_core` (regex fallback) | Task 5 |
| `src/verifier.py` | `print_summary` VCG breakdown | Task 2, Task 5 |
| `tools/corpus_schema.json` | `z3_verdict` enum | Task 2 |
| `src/architect/synthesize.py` | Synthesis mode VCG path | Task 8 |
| `src/architect/ast_verify.py` | `verify_from_ast` VCG branch | Task 7 |
| `tests/verifier/test_vcg_dsic.py` | **new** — unit + adversarial | Tasks 3–4, 6 |
| `docs/superpowers/notes/phase2-vcg-*.md` | baseline + verdict-delta | Tasks 1, 5, 9 |

---

## Task 1: Branch + VCG baseline

**Files:** `docs/superpowers/notes/phase2-vcg-baseline.md` (create).

- [ ] **Step 1: Branch** — `git checkout main && git checkout -b phase2-vcg-real-check`
- [ ] **Step 2: Capture the VCG verdict baseline**

```bash
PYTHONPATH=src python -m verifier corpus.json | tee /tmp/p2-corpus.txt
PYTHONPATH=src python - <<'PY' | tee /tmp/p2-vcg-verdicts.txt
import json, sys; sys.path.insert(0, "src")
from verifier import verify
for e in json.load(open("corpus.json")):
    if e.get("category") == "VCG":
        r = verify(e)
        print(f"{e['paper_id']:40s} {r.verdict:18s} entry_specific={r.entry_specific}")
PY
PYTHONPATH=src pytest -q | tail -3
```

- [ ] **Step 3: Write `docs/superpowers/notes/phase2-vcg-baseline.md`** — paste the full VCG per-entry verdict table (33 rows) + the corpus summary block + `176 passed / 5 xfailed`. This is the "before" side of every later delta.
- [ ] **Step 4: Commit** — `git add docs/superpowers/notes/phase2-vcg-baseline.md && git commit -m "chore: VCG verdict baseline before Phase 2"`

---

## Task 2: `VERIFIED_SHAPE` verdict value (plumbing only)

**Files:**
- Modify: `src/tracks/__init__.py`, `src/verifier.py`, `tools/corpus_schema.json`
- Test: `tests/verifier/test_verdict_shape.py` (create)

**Interfaces:**
- Produces: `Verdict` literal gains `"VERIFIED_SHAPE"`. `finalize_verdict` unchanged in signature; a new helper `shape_verdict() -> "VERIFIED_SHAPE"` or a documented direct construction is what the regex fallback uses in Task 5. `VerificationResult.__str__` and `print_summary` render it as a non-proof (tick `·`, not `✓`).

- [ ] **Step 1: Write the failing test**

```python
# tests/verifier/test_verdict_shape.py
import typing
from tracks import Verdict, VerificationResult

def test_verified_shape_in_enum():
    assert "VERIFIED_SHAPE" in typing.get_args(Verdict)

def test_verified_shape_renders_as_non_proof():
    r = VerificationResult(verdict="VERIFIED_SHAPE", category="VCG",
                           paper_id="x", track=1, notes="regex form match only")
    s = str(r)
    assert "VERIFIED_SHAPE" in s
```

- [ ] **Step 2: Add `"VERIFIED_SHAPE"` to the `Verdict` literal** in `src/tracks/__init__.py`, with a comment: "regex/structural shape match only — NOT a proof about this entry's math; strictly weaker than VERIFIED_TEMPLATE in that it never ran a solver on the entry."
- [ ] **Step 3: `VerificationResult.__str__`** — treat `VERIFIED_SHAPE` like `COUNTEREXAMPLE`/`UNKNOWN` for the tick (`·`, not `✓`).
- [ ] **Step 4: `src/verifier.py::print_summary`** — add a `VERIFIED_SHAPE` bar line; in the VCG breakdown, "form-confirmed" entries that are `VERIFIED_SHAPE` print as "regex-shape only (not a proof)". Do not count them as entry-specific.
- [ ] **Step 5: `tools/corpus_schema.json`** — add `"VERIFIED_SHAPE"` to the `z3_verdict` enum. Run `PYTHONPATH=src python tools/validate.py corpus.json` — still 185/185 (no entry uses it yet).
- [ ] **Step 6: Gate + commit**

```bash
PYTHONPATH=src pytest -q | tail -3   # 178 passed / 5 xfailed (176 + 2 new)
PYTHONPATH=src python -m verifier corpus.json | grep -E "\((25|73|2|5)\)"  # unmoved — nothing emits VERIFIED_SHAPE yet
git add src/tracks/__init__.py src/verifier.py tools/corpus_schema.json tests/verifier/test_verdict_shape.py
git commit -m "feat: add VERIFIED_SHAPE verdict value (plumbing; no emitter yet)"
```

---

## Task 3: Grid + allocation/payment encoder

**Files:**
- Create: `src/tracks/vcg_dsic.py`
- Test: `tests/verifier/test_vcg_dsic.py` (create)

**Interfaces:**
- Consumes: an `entry` dict with `mechanism.allocation_rule_latex` /
  `payment_rule_latex` / `bid_space` / `auction_type` / `num_clients` (or
  `num_bidders`); SymPy, Z3.
- Produces:
  - `parse_allocation(latex: str) -> AllocSpec | None` — `AllocSpec` is a tagged
    union: `HighestBidder`, `TopK(k)`, `ProportionalShare(exponent)`,
    `ArgmaxWelfare(objective_expr)`, or `None` (unparseable).
  - `parse_payment(latex: str, alloc: AllocSpec) -> PaySpec | None` —
    `ClarkePivot` (computed from `alloc`), `ExplicitFormula(expr)`, or `None`.
  - `build_grid(n_bidders, n_attrs, k) -> GridCtx` — Z3 real/int vars for
    `v[i][a]`, `b[i][a]` on `k` points in `[0,1]`; `profile_count = k**(n_bidders*n_attrs)`.
  - `encode_utility(grid, alloc, pay) -> callable(i, bid_profile) -> z3 expr`.

- [ ] **Step 1: Write tests for the parsers first**

```python
# tests/verifier/test_vcg_dsic.py
from tracks.vcg_dsic import parse_allocation, parse_payment, HighestBidder, ClarkePivot

def test_parse_highest_bidder():
    a = parse_allocation(r"x_i(b) = 1 \text{ if } b_i = \max_j b_j")
    assert isinstance(a, HighestBidder)

def test_parse_argmax_welfare():
    a = parse_allocation(r"W^\star(\hat c) \in \arg\max [SW := v(W) - \hat c f(W)]")
    assert a is not None and a.__class__.__name__ == "ArgmaxWelfare"

def test_parse_clarke_payment():
    a = parse_allocation(r"x_i(b) = 1 \text{ if } b_i = \max_j b_j")
    p = parse_payment(r"p_i = \max_{j \neq i} b_j", a)
    assert p.__class__.__name__ in ("ClarkePivot", "ExplicitFormula")

def test_unparseable_allocation_returns_none():
    assert parse_allocation(r"x = \text{the output of Algorithm 3}") is None
```

- [ ] **Step 2: Run — RED.** `pytest tests/verifier/test_vcg_dsic.py -v`
- [ ] **Step 3: Implement the parsers + grid.** Regex/SymPy classification of the
  allocation LaTeX into the `AllocSpec` union above; `\arg\max`/`argmax` +
  an objective → `ArgmaxWelfare(objective)`. Payment: `\max_{j\neq i}` /
  `(K+1)`-th lowest / `W_{-i} - Σ_{k≠i}` → `ClarkePivot`; a closed formula in
  `b` → `ExplicitFormula`; else `None`. `build_grid` makes Z3 vars; cap
  `profile_count` at a module constant `_PROFILE_CAP = 4096` (raise per-benchmark
  later). Everything unparseable → `None` (caller turns that into `UNSUPPORTED`).
- [ ] **Step 4: Green + non-VCG gate**

```bash
PYTHONPATH=src pytest tests/verifier/test_vcg_dsic.py -v
PYTHONPATH=src pytest -q | tail -3        # 0 failed
PYTHONPATH=src python -m verifier corpus.json | grep -E "Contract entry|Stackelberg equil|SOS certificate|Track 3|Bayesian IC"
```

(`vcg_dsic.py` not wired into `verify()` yet → all verdicts, VCG included, unmoved.)

- [ ] **Step 5: Commit** — `feat: VCG allocation/payment LaTeX parsers + Z3 grid context`

---

## Task 4: `verify_vcg_dsic` — the real DSIC check

**Files:**
- Modify: `src/tracks/vcg_dsic.py`
- Test: `tests/verifier/test_vcg_dsic.py` (extend)

**Interfaces:**
- Produces: `verify_vcg_dsic(entry: dict, *, k: int = 3) -> VerificationResult`.
  Verdict: `VERIFIED` (entry_specific=True, note "exact on grid k=N") on UNSAT;
  `COUNTEREXAMPLE` (+ witness profile + max gain) on SAT; `UNKNOWN` if
  `profile_count > _PROFILE_CAP`, allocation unparseable, or the allocation
  cross-check disagrees; `UNSUPPORTED` if no `allocation_rule_latex` /
  `payment_rule_latex` at all.

- [ ] **Step 1: Write the check tests**

```python
# tests/verifier/test_vcg_dsic.py  (extend)
from tracks.vcg_dsic import verify_vcg_dsic

_SINGLE_ITEM_CLARKE = {  # 2nd-price single-item auction, done right
    "paper_id": "synthetic_clarke_ok", "category": "VCG",
    "mechanism": {
        "allocation_rule_latex": r"x_i(b) = 1 \text{ if } b_i = \max_j b_j",
        "payment_rule_latex": r"p_i = \max_{j \neq i} b_j \text{ if } x_i = 1, \text{ else } 0",
        "client_utility_latex": r"u_i = v_i x_i - p_i",
        "auction_type": "forward", "num_clients": 2}}

_NON_PIVOTAL = {  # winner pays half its own bid -> not DSIC
    **_SINGLE_ITEM_CLARKE, "paper_id": "synthetic_bad_payment",
    "mechanism": {**_SINGLE_ITEM_CLARKE["mechanism"],
                  "payment_rule_latex": r"p_i = b_i / 2 \text{ if } x_i = 1"}}


def test_single_item_clarke_verified():
    r = verify_vcg_dsic(_SINGLE_ITEM_CLARKE, k=4)
    assert r.verdict == "VERIFIED" and r.entry_specific is True

def test_non_pivotal_payment_is_counterexample():
    r = verify_vcg_dsic(_NON_PIVOTAL, k=4)
    assert r.verdict == "COUNTEREXAMPLE"
    assert r.counterexample is not None

def test_oversize_grid_is_unknown():
    big = {**_SINGLE_ITEM_CLARKE, "mechanism": {**_SINGLE_ITEM_CLARKE["mechanism"],
           "num_clients": 6}}
    assert verify_vcg_dsic(big, k=6).verdict == "UNKNOWN"
```

- [ ] **Step 2: Run — RED.**
- [ ] **Step 3: Implement `verify_vcg_dsic`.**
  - `n = entry["mechanism"].get("num_clients") or entry.get("num_clients") or 2`;
    `n_attrs` from the value LaTeX (default 1).
  - `alloc = parse_allocation(...)`, `pay = parse_payment(..., alloc)`; either
    `None` and both LaTeX fields present → `UNKNOWN` (parse gap); both fields
    absent → `UNSUPPORTED`.
  - `grid = build_grid(n, n_attrs, k)`; `profile_count > _PROFILE_CAP` →
    `UNKNOWN` naming the blown dimension.
  - **Allocation cross-check:** on ~8 random grid profiles, compare the encoded
    allocation's chosen winner(s) against a direct evaluation of
    `allocation_rule_latex` (SymPy `lambdify` where the form allows). Any
    disagreement → `UNKNOWN` (do not proceed to a possibly-wrong counterexample).
  - DSIC: for each `i`, Z3 `ForAll(v_i, b_{-i})` with `b_i = v_i`, enumerate
    every grid `b_i'`, assert `u_i(truthful) >= u_i(b_i')`. IR: `u_i(truthful) >= 0`.
  - Solve the conjunction's negation. `unsat` → `VERIFIED`,
    `entry_specific=True`, note `"DSIC + IR exact on grid k={k}, {profile_count} profiles"`.
    `sat` → `COUNTEREXAMPLE`, `counterexample = {profile, deviator, gain}`.
  - Return via `finalize_verdict(all_ok, has_cex, entry_specific=True)`.
- [ ] **Step 4: Green + non-VCG gate** (same grep as Task 3 Step 4 — non-VCG unmoved; `vcg_dsic` still not wired into `verify()`).
- [ ] **Step 5: Commit** — `feat: verify_vcg_dsic — finite-grid Z3 DSIC + IR proof for VCG`

---

## Task 5: Dispatcher + corpus delta

**Files:**
- Modify: `src/tracks/track1_z3.py` (`verify_vcg`)
- Create: `docs/superpowers/notes/phase2-vcg-verdict-delta.md`
- Modify: `Task.md` (VCG numbers), `docs/superpowers/specs/2026-08-29-verifier-proper-checks.md`

**Interfaces:**
- `verify_vcg(entry)`: try `verify_vcg_dsic(entry)` first. If its verdict is
  `VERIFIED` / `COUNTEREXAMPLE` → return it. If `UNKNOWN` / `UNSUPPORTED` → fall
  back to the existing regex path (`_classify_vcg_payment` → `_vcg_check_core`),
  but map its `form_confirmed` success to **`VERIFIED_SHAPE`**. The
  identically-zero-payment soundness gate stays first.

- [ ] **Step 1: Wire the dispatcher** in `verify_vcg`. Keep `_vcg_check_core`
  and its Approach C seam intact (the AST path still calls it until Task 7); the
  change is: (a) try `verify_vcg_dsic` first, (b) `_vcg_check_core`'s
  `form_confirmed` branch now yields `VERIFIED_SHAPE`. Do this via a new
  `shape_only: bool = False` kwarg on `_vcg_check_core` (default keeps old
  behavior for the AST caller until Task 7) OR by post-mapping the verdict in
  `verify_vcg` — pick the smaller diff, note which in the report.
- [ ] **Step 2: Recompute the corpus**

```bash
PYTHONPATH=src python - <<'PY' | tee /tmp/p2-vcg-after.txt
import json, sys; sys.path.insert(0, "src")
from verifier import verify
for e in json.load(open("corpus.json")):
    if e.get("category") == "VCG":
        r = verify(e); print(f"{e['paper_id']:40s} {r.verdict:18s} es={r.entry_specific}  {r.notes[:70]}")
PY
PYTHONPATH=src python -m verifier corpus.json | tee /tmp/p2-corpus-after.txt
```

- [ ] **Step 3: Write `docs/superpowers/notes/phase2-vcg-verdict-delta.md`** — a
  table `paper_id | before | after | reason`. Every changed row gets a reason
  from {real DSIC proof, real counterexample, grid too big → UNKNOWN, allocation
  unparseable → UNKNOWN, multi-attribute impossible → COUNTEREXAMPLE/UNSUPPORTED,
  now VERIFIED_SHAPE (was VERIFIED — regex only)}. Note the new corpus totals.
- [ ] **Step 4: Non-VCG frozen check** — `Contract entry-specific 5 / template 31`,
  `Stackelberg 1/28`, `Track 2 4`, `Track 3 1`, `Track 4 1` UNMOVED. If any moved,
  `verify_vcg_dsic` is leaking into a non-VCG path — BLOCKED.
- [ ] **Step 5: Full suite** — `PYTHONPATH=src pytest -q | tail -3`. Fix any
  `tests/architect/` or `tests/verifier/` test that asserted an old VCG verdict
  (expected — update to the new honest verdict, note each in the report).
- [ ] **Step 6: Update `Task.md`** — "Verdict Semantics" VCG line + roadmap
  Phase 2 status: new totals, `VERIFIED_SHAPE` count, `verify_vcg_dsic`
  entry-specific count.
- [ ] **Step 7: Commit** — `git add -A && git commit -m "feat: verify_vcg dispatches to verify_vcg_dsic; regex path -> VERIFIED_SHAPE; corpus delta documented"` (`git add -f Task.md`).

---

## Task 6: Adversarial VCG suite

**Files:**
- Modify: `tests/verifier/broken_mechanisms.py`, `tests/verifier/test_adversarial_soundness.py`
- Test: those + `tests/verifier/test_vcg_dsic.py`

- [ ] **Step 1: Un-`xfail` `vcg_clarke_shaped_payment_wrong_allocation`.** In
  `tests/verifier/test_adversarial_soundness.py`, remove the `xfail` for this
  fixture and assert `verify(entry).verdict == "COUNTEREXAMPLE"` (Clarke-shaped
  payment + allocation to the lowest bidder → a low-value bidder overreports,
  wins, and the Clarke payment computed from the *wrong* allocation doesn't
  cover the lie). If it still doesn't produce `COUNTEREXAMPLE`, that's a real gap
  in `verify_vcg_dsic`'s allocation encoding — fix `vcg_dsic.py`, do not
  re-`xfail`.
- [ ] **Step 2: Add fixtures** to `broken_mechanisms.py` / `test_vcg_dsic.py`:
  second-price + reserve done right → `VERIFIED`; `p_i = b_i` (pay your own bid)
  → `COUNTEREXAMPLE`; a 2-attribute deterministic allocation → `UNSUPPORTED` or
  `COUNTEREXAMPLE` with a note citing the multi-parameter impossibility.
- [ ] **Step 3: Gate** — `PYTHONPATH=src pytest -q | tail -3` (xfailed count now
  4, was 5); non-VCG frozen; `PYTHONPATH=src python -m architect.eval.soundness_report`
  → `false_verified: 0`.
- [ ] **Step 4: Commit** — `test: real VCG adversarial cases; un-xfail wrong-allocation Clarke`

---

## Task 7: AST path calls the real check

**Files:**
- Modify: `src/architect/ast_verify.py`, `src/tracks/vcg_dsic.py` (add an
  entry-dict-from-Mechanism helper if useful)
- Test: `tests/architect/test_ast_verify.py`

**Interfaces:**
- `verify_from_ast`'s VCG branch: build a minimal `entry` dict from the
  Mechanism (`allocation_rule_latex` / `payment_rule_latex` from
  `serialize.render(m)`'s VCG dict, `num_clients` from `meta`/`type_space`) and
  call `verify_vcg_dsic(entry)`. Remove the `entry_specific=False` stopgap — the
  real check now sets `entry_specific` honestly.

- [ ] **Step 1: Update the VCG orchestrator test.** `test_ast_verify.py` has
  `test_verify_from_ast_vcg_is_template_not_verified` (Approach C Task 8 fix).
  Change it: a well-formed single-item Clarke VCG `Mechanism` → `verify_from_ast`
  returns `VERIFIED` `entry_specific=True`; a wrong-allocation one →
  `COUNTEREXAMPLE`; an unparseable-allocation one → `UNKNOWN` (not a fabricated
  verdict).
- [ ] **Step 2: Implement** the VCG branch rewrite in `ast_verify.py`. Route
  through `verify_vcg_dsic`. On its `UNKNOWN`/`UNSUPPORTED`, fall back to
  `_vcg_check_core(..., shape_only=True)` → `VERIFIED_SHAPE`, NOT
  `VERIFIED_TEMPLATE`.
- [ ] **Step 3: Parity** — extend `test_ast_path_matches_latex_path_on_*` with a
  VCG fixture; AST path verdict must equal the LaTeX path verdict.
- [ ] **Step 4: Gate + commit** — full suite green; non-VCG frozen;
  `feat: verify_from_ast VCG branch calls verify_vcg_dsic (real entry-specific)`

---

## Task 8: Constrained VCG generation (Synthesis mode)

**Files:**
- Modify: `src/architect/synthesize.py`, `src/architect/architect.py` (VCG
  Synthesis prompt)
- Test: `tests/architect/test_synthesize_vcg.py` (create)

**Interfaces:**
- `synthesize(m, c)` for `m.category == "VCG"`: (a) force the payment subtree to
  the Clarke-pivot form built from the allocation, (b) expose `Unknown` only for
  per-agent weights `w_i` and outcome boosts `γ(o)`, (c) Z3-search `w_i ≥ 0`,
  `γ` s.t. the affine-maximizer allocation + Clarke payment satisfy IC + IR +
  budget on a small grid, (d) return the concrete Mechanism, which the loop then
  sends to `verify_vcg_dsic`.

- [ ] **Step 1: Test** — a synthetic single-item VCG `ProblemSpec` → `synthesize`
  returns a Mechanism whose payment is Clarke-pivot and whose weights are
  concrete; `verify_vcg_dsic` on the serialized result → `VERIFIED`.
- [ ] **Step 2: Implement** the VCG branch in `synthesize`. Reuse the existing
  `_sympy_to_z3` / solve-mode machinery; the new part is the fixed payment form +
  restricting the search to `w`/`γ`.
- [ ] **Step 3: Prompt** — `architect.py` VCG Synthesis instruction: "propose
  only an allocation rule (from: highest-bidder, top-k, proportional,
  weighted-welfare-max) and per-agent weights; the payment is fixed to the
  Clarke pivot — do not author it."
- [ ] **Step 4: Gate + commit** — full suite green; non-VCG frozen;
  `feat: Synthesis mode constrains VCG to Clarke payment + affine-maximizer weight search`

---

## Task 9: Eval + docs

**Files:** `docs/eval-results.md`, `Task.md`, roadmap spec, `docs/superpowers/notes/phase2-vcg-verdict-delta.md`.

- [ ] **Step 1: Run the VCG eval** (live API — background it):

```bash
set -a && . ./.env && set +a
PYTHONPATH=src ARCHITECT_LLM_MODEL=openai/gpt-oss-120b ARCHITECT_LLM_TIMEOUT_S=120 \
  ARCHITECT_BUDGET_S=300 nohup python -m architect.eval.run_eval > /tmp/p2-eval.log 2>&1 &
```

- [ ] **Step 2: Check the "done when"** — ≥2 of {myerson_single_item,
  vcg_redistribution, vcg_clarke_pivot, vcg_cavallo_redistribution} reach
  `VERIFIED` with a `verify_vcg_dsic` certificate. If <2, record which failed and
  why (grid cap? allocation parse? genuinely not affine-maximizable?) — a
  documented honest shortfall is acceptable; a silent one is not.
- [ ] **Step 3: Update `docs/eval-results.md`** with the new VCG rows.
- [ ] **Step 4: Roadmap spec Phase 2 → `## Phase 2 … ✅ landed <date>`** with:
  new corpus VCG totals, `verify_vcg_dsic` entry-specific count, eval VCG
  verified count, and the decision on the regex path (recommend: keep as
  `VERIFIED_SHAPE` fallback through Phase 3, delete in Phase 3b).
- [ ] **Step 5: `Task.md`** — "Verdict Semantics" + roadmap item 2 to past tense
  with the numbers.
- [ ] **Step 6: Commit** — `docs: Phase 2 landed — real VCG check + constrained generation, corpus + eval delta`

---

## Self-Review

**Spec coverage:** 2a verifier → Tasks 3–4; dispatcher + `VERIFIED_SHAPE` →
Tasks 2, 5; broad fragment (multi-unit/multi-attribute) → Task 3's `AllocSpec`
union + Task 4's `n_attrs`, with the impossibility caveat surfaced in Task 6's
multi-attribute fixture; 2b generation → Task 8; AST seam → Task 7; corpus delta
accounting → Tasks 1, 5, 9; eval "done when" → Task 9. ✓

**Placeholder scan:** Task 3/4 test fixtures are concrete; the `AllocSpec` /
`PaySpec` union members are named. The parser implementations (Task 3 Step 3,
Task 4 Step 3) are described by classification-target rather than literal regex —
unavoidable given the corpus's LaTeX diversity (33 entries, forms range from
`\frac{f^{α-1}}{Σ}` to `\arg\max Σ v_i - c_i`); the tests pin the required
behavior and the fail-closed rule (`None` → `UNKNOWN`/`UNSUPPORTED`, never a
guess) bounds the risk.

**Type consistency:** `verify_vcg_dsic(entry, *, k=3) -> VerificationResult`
consumed by Task 5 (`verify_vcg`) and Task 7 (`ast_verify`).
`parse_allocation` / `parse_payment` / `build_grid` from Task 3 consumed by
Task 4. `VERIFIED_SHAPE` added in Task 2, emitted only in Tasks 5/7 via the
documented fallback. `_vcg_check_core` gains an optional `shape_only: bool =
False` (Task 5) — default preserves the Approach C AST caller until Task 7. ✓

---

## Execution Handoff

Subagent-driven. Tasks 3 and 4 are the core (the parsers + the Z3 encoding);
Task 5 is where the corpus numbers move and needs the delta doc + the non-VCG
frozen check as its gate. Tasks 2, 6, 7, 9 are mid-tier; Task 1 is setup.
