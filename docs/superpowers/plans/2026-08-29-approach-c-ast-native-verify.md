# Approach C — AST-Native Verify Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the Architect loop a verification path that consumes the typed Mechanism AST directly (`verify_from_ast`), so the fragile LaTeX→SymPy parser is no longer in the loop — without changing `verify(entry)` or any corpus verdict.

**Architecture:** Every track already runs `LaTeX → SymPy expr → solver → verdict`. This plan keeps the SymPy→solver→verdict back-half of each track exactly as-is, extracts it behind a small shared seam, and adds a second front-half `AST → SymPy` (the bridge `ast_to_sympy`, which already exists in `src/architect/serialize.py` and is used by Synthesis mode). A new `verify_from_ast(m, meta)` orchestrates: build SymPy from the AST, classify the track structurally, dispatch to the seam, `finalize_verdict`. The CEGIS loop switches to it behind `ARCHITECT_AST_VERIFY=1`, default off.

**Tech Stack:** Python 3, pytest, Z3 (`z3-solver`), SymPy, CVXPY/SCS (Track 2), mpmath (Track 3), NumPy.

**Spec:** `docs/superpowers/specs/2026-08-29-verifier-proper-checks.md` — Phase 1. Companion context: `docs/superpowers/specs/2026-08-28-ast-native-verifier-future-scope.md` Part 1.

## Global Constraints

- Run tests from repo root with `PYTHONPATH=src`. Full suite currently **150 passed / 5 xfailed** — must stay green (0 failed; the 5 xfails remain xfail) at the end of every task.
- **Frozen regression gate, every task:** `PYTHONPATH=src python -m verifier corpus.json` must print exactly
  **VERIFIED 25 / VERIFIED_TEMPLATE 73 / UNKNOWN 2 / UNSUPPORTED 5**
  and the per-category breakdown line `VCG (33): 19 form-confirmed [clarke=9 marginal=3 threshold=7], 14 template-only` unchanged. If a task moves any of these numbers, it is wrong — revert and re-approach.
- `src/verifier.py::verify(entry)` and every `verify_vcg / verify_contract / verify_stackelberg / verify_shapley / verify_track2 / verify_track3 / verify_track4` keep their existing public signature `(entry: dict) -> VerificationResult` and existing behavior. Refactors that route them through a new shared helper are fine *only if* the regression gate is unmoved.
- New verdicts still go through `tracks.finalize_verdict(all_ok, has_cex, entry_specific)` — no track invents a verdict string.
- `ast_to_sympy` maps `Unknown` to a plain SymPy `Symbol` of the same name (this is what Synthesis mode already relies on — do not change it).
- Commit after every task (`feat:` / `refactor:` / `test:` / `docs:`). Do not push, do not open a PR. Stop at the last green commit.
- Branch: create `approach-c-ast-verify` off `main` before Task 1.

---

## File Structure

| File | Responsibility | This plan |
|---|---|---|
| `src/architect/serialize.py` | `ast_to_sympy(node)` — the AST→SymPy bridge (exists) | audit + harden `IndexedFamily`, `Func` |
| `src/architect/ast_verify.py` | **new** — `verify_from_ast(m, meta)`, `_classify_ast(m)` | Tasks 8–9 |
| `src/tracks/track1_z3.py` | Z3 checks; contains `_sp_to_z3`, `_parse_contract_entry`, `_try_stackelberg_latex`, `verify_*` | extract seams (Tasks 3–6) |
| `src/tracks/track2_sos.py` | SOS/CVXPY | extract seam (Task 7) |
| `src/tracks/track3_dreal.py` | interval arithmetic | extract seam (Task 7) |
| `src/tracks/track4_sympy.py` | Bayesian symbolic | extract seam (Task 7) |
| `src/architect/inspect.py` | `inspect_mechanism(m, meta)` — loop's verify call | flag cutover (Task 10) |
| `tests/architect/test_ast_verify.py` | **new** — bridge + orchestrator + parity | Tasks 2, 9, 11 |

---

## Task 1: Branch + baseline capture

**Files:** none (git + a committed baseline note).

- [ ] **Step 1: Branch**

```bash
git checkout main && git checkout -b approach-c-ast-verify
```

- [ ] **Step 2: Capture the frozen baseline**

```bash
PYTHONPATH=src python -m verifier corpus.json | tee /tmp/approach-c-baseline.txt
PYTHONPATH=src pytest -q | tail -3 | tee -a /tmp/approach-c-baseline.txt
```

Confirm it shows `VERIFIED 25 / VERIFIED_TEMPLATE 73 / UNKNOWN 2 / UNSUPPORTED 5` and `150 passed, 5 xfailed`. Every later task diffs against this file.

- [ ] **Step 3: Commit the baseline note**

```bash
mkdir -p docs/superpowers/notes
cp /tmp/approach-c-baseline.txt docs/superpowers/notes/approach-c-baseline.txt
git add docs/superpowers/notes/approach-c-baseline.txt
git commit -m "chore: capture verifier baseline before Approach C"
```

---

## Task 2: `ast_to_sympy` coverage audit + hardening

**Files:**
- Modify: `src/architect/serialize.py` (`ast_to_sympy` only)
- Test: `tests/architect/test_ast_verify.py` (create)

**Interfaces:**
- Consumes: `architect.ast.{Const,Sym,Unknown,Sum,Prod,Pow,Func,IndexedFamily}`.
- Produces: `ast_to_sympy(node) -> sympy.Expr` covering **all 8** node types.
  `Unknown("x")` → `sympy.Symbol("x")`. `Func("ln", a)` → `sympy.log(...)`,
  `Func("exp", a)` → `sympy.exp(...)`. `IndexedFamily(name, index, over)` →
  `sympy.Symbol(name)` placeholder (documented: opaque at bridge level;
  per-index expansion is the consumer's job).

- [ ] **Step 1: Write the failing tests**

```python
# tests/architect/test_ast_verify.py
import sympy
from architect.ast import Const, Sym, Unknown, Sum, Prod, Pow, Func, IndexedFamily
from architect.serialize import ast_to_sympy


def test_bridge_atoms():
    assert ast_to_sympy(Const(2.5)) == sympy.Float(2.5)
    assert ast_to_sympy(Sym("theta")) == sympy.Symbol("theta")
    assert ast_to_sympy(Unknown("a")) == sympy.Symbol("a")


def test_bridge_compound():
    e = ast_to_sympy(Sum([Prod([Sym("p"), Sym("e")]),
                          Prod([Const(-0.5), Sym("c"), Pow(Sym("e"), 2)])]))
    p, e_, c = sympy.symbols("p e c")
    assert sympy.simplify(e - (p * e_ - sympy.Rational(1, 2) * c * e_**2)) == 0


def test_bridge_funcs():
    assert ast_to_sympy(Func("ln", Sym("x"))) == sympy.log(sympy.Symbol("x"))
    assert ast_to_sympy(Func("exp", Sym("x"))) == sympy.exp(sympy.Symbol("x"))


def test_bridge_indexed_family_is_opaque_symbol():
    got = ast_to_sympy(IndexedFamily("R", "i", ["R_1", "R_2"]))
    assert got == sympy.Symbol("R")
```

- [ ] **Step 2: Run — see which already pass**

```bash
PYTHONPATH=src pytest tests/architect/test_ast_verify.py -v
```

`ast_to_sympy` already exists; atoms/compound/funcs likely pass. Note which fail
(most likely `IndexedFamily`).

- [ ] **Step 3: Harden `ast_to_sympy` for the gaps**

In `src/architect/serialize.py`, extend `ast_to_sympy` so every node type in
Step 1 is handled. For `IndexedFamily`, return `sympy.Symbol(node.name)` with a
one-line comment that per-index expansion belongs to the caller. Do not touch
the `Const/Sym/Unknown/Sum/Prod/Pow/Func` branches if they already pass.

- [ ] **Step 4: Green + regression gate**

```bash
PYTHONPATH=src pytest tests/architect/test_ast_verify.py -v
PYTHONPATH=src pytest -q | tail -3
PYTHONPATH=src python -m verifier corpus.json | grep -E "VERIFIED|VCG \("
```

Suite green; corpus line matches the baseline.

- [ ] **Step 5: Commit**

```bash
git add src/architect/serialize.py tests/architect/test_ast_verify.py
git commit -m "feat: ast_to_sympy covers all 8 node types (IndexedFamily as opaque symbol)"
```

---

## Task 3: Track 1 VCG seam

**Files:**
- Modify: `src/tracks/track1_z3.py` (`verify_vcg` + new `_vcg_check_core`)
- Test: `tests/verifier/test_seams.py` (create)

**Interfaces:**
- Produces: `_vcg_check_core(payment_expr, utility_expr, *, entry_specific, paper_id, meta=None) -> VerificationResult` — the SymPy-expr-in, verdict-out back-half of `verify_vcg`. `verify_vcg(entry)` becomes: clean + `parse_latex` the entry's `payment_rule_latex` / `client_utility_latex` → SymPy exprs → `_vcg_check_core(...)`.
- Consumes: whatever `verify_vcg` currently computes after it has the parsed SymPy expressions (the `_VCG_FORM_CLAIMS` regex classification, `_sp_to_z3`, the Z3 solve).

- [ ] **Step 1: Read `verify_vcg` end to end** (`src/tracks/track1_z3.py:75`+). Identify the exact line where it first holds parsed SymPy expressions (or, if VCG classifies on the raw LaTeX string, where it holds the cleaned string). That line is the seam.

- [ ] **Step 2: Write the characterization test first**

```python
# tests/verifier/test_seams.py
import json
from verifier import verify

CORPUS = json.load(open("corpus.json"))
VCG = [e for e in CORPUS if e.get("category") == "VCG"][:8]


def test_vcg_verdicts_unchanged_after_seam_extraction():
    # Snapshot: fill `expected` in Step 3 by running verify() on these 8 once
    # and pasting {paper_id: (verdict, entry_specific)}. This locks behavior
    # before the refactor.
    expected = {}  # paper_id -> (verdict, entry_specific)
    for e in VCG:
        r = verify(e)
        if e["paper_id"] in expected:
            v, es = expected[e["paper_id"]]
            assert (r.verdict, r.entry_specific) == (v, es)
```

- [ ] **Step 3: Fill the snapshot, then extract `_vcg_check_core`** — run the 8
entries once, paste the `{paper_id: (verdict, entry_specific)}` map into
`expected`. Then move the post-parse body of `verify_vcg` into
`_vcg_check_core(payment_expr, utility_expr, *, entry_specific, paper_id,
meta=None)`. `verify_vcg(entry)` keeps its LaTeX front-end and calls the core.
**No logic change** — pure move + parameterize.

- [ ] **Step 4: Green + regression gate**

```bash
PYTHONPATH=src pytest tests/verifier/test_seams.py -v
PYTHONPATH=src pytest -q | tail -3
PYTHONPATH=src python -m verifier corpus.json | grep -E "VERIFIED |VCG \("
```

All three must match the baseline exactly.

- [ ] **Step 5: Commit**

```bash
git add src/tracks/track1_z3.py tests/verifier/test_seams.py
git commit -m "refactor: extract _vcg_check_core seam from verify_vcg (no behavior change)"
```

---

## Task 4: Track 1 Contract seam

**Files:**
- Modify: `src/tracks/track1_z3.py` (`verify_contract`, `_try_contract_latex`, new `_contract_check_core`)
- Test: `tests/verifier/test_seams.py` (extend)

**Interfaces:**
- Produces: `_contract_check_core(ic_expr, ir_expr, *, type_variable, num_types, entry_specific, paper_id, meta=None) -> VerificationResult` — the back-half of the Contract entry-specific path (`_try_contract_latex` after `_parse_contract_entry` returns its SymPy exprs). `verify_contract(entry)` and `_try_contract_latex(entry)` keep their LaTeX front-ends (`_parse_contract_entry`) and call the core.

- [ ] **Step 1: Read `_parse_contract_entry` (`:341`) + `_try_contract_latex` (`:433`).** `_parse_contract_entry` already returns a tuple of SymPy exprs + metadata — that return value *is* the seam boundary.

- [ ] **Step 2: Snapshot test** — add to `tests/verifier/test_seams.py`: 8 Contract entries (include all 5 entry-specific + 3 template), lock `(verdict, entry_specific)` the same way as Task 3.

- [ ] **Step 3: Extract `_contract_check_core`** — everything `_try_contract_latex` does *after* `_parse_contract_entry` returns, parameterized on the parsed exprs + `(type_variable, num_types, entry_specific)`. Pure move.

- [ ] **Step 4: Green + regression gate** — same three commands; the
`Contract entry-specific (LaTeX utility): 5` / `Contract template (linear-cost model): 31`
lines and the `25 / 73 / 2 / 5` line unmoved.

- [ ] **Step 5: Commit** — `refactor: extract _contract_check_core seam (no behavior change)`

---

## Task 5: Track 1 Stackelberg seam

**Files:**
- Modify: `src/tracks/track1_z3.py` (`verify_stackelberg`, `_try_stackelberg_latex`, new `_stackelberg_check_core`)
- Test: `tests/verifier/test_seams.py` (extend)

**Interfaces:**
- Produces: `_stackelberg_check_core(follower_utility_expr, *, follower_decision, best_response_expr=None, meta=None, entry_specific, paper_id) -> VerificationResult` — the FOC-derivation + IR-at-optimum back-half of `_try_stackelberg_latex`. `verify_stackelberg` / `_try_stackelberg_latex` keep the LaTeX front-end (multi-clause `U = R - C, R = ..., C = ...` resolution stays in the front-end).

- [ ] **Step 1: Read `_try_stackelberg_latex` (`:1126`) + `verify_stackelberg` (`:1310`).** The seam is right after `follower_utility_latex` (and any `best_response_latex`) is parsed to a SymPy expr, before the `sympy.diff` FOC step.

- [ ] **Step 2: Snapshot test** — the 1 entry-specific Stackelberg entry (`Sarikaya2019stackelberg_workers`) + 5 template ones; lock `(verdict, entry_specific)`.

- [ ] **Step 3: Extract `_stackelberg_check_core`** — FOC derivation, best-response solve, best-response cross-check (keep the guard that *rejects* rather than certifies on disagreement), IR at optimum. Pure move.

- [ ] **Step 4: Green + regression gate** — `Stackelberg equilibrium IR (NOT DSIC): 29 (1 entry-specific, 28 template-only)` unmoved.

- [ ] **Step 5: Commit** — `refactor: extract _stackelberg_check_core seam (no behavior change)`

---

## Task 6: Track 1 Shapley seam (trivial)

**Files:** Modify `src/tracks/track1_z3.py` (`verify_shapley`).

**Interfaces:**
- Produces: `_shapley_check_core(*, paper_id) -> VerificationResult` returning the same unconditional `UNSUPPORTED` `verify_shapley` returns today. Exists only so the orchestrator (Task 8) has a uniform seam to call; Phase 4 fills it in.

- [ ] **Step 1:** Extract the body. `verify_shapley(entry)` calls `_shapley_check_core(paper_id=entry.get("paper_id","<unknown>"))`.
- [ ] **Step 2:** `PYTHONPATH=src pytest -q` green; regression gate unmoved.
- [ ] **Step 3: Commit** — `refactor: extract _shapley_check_core stub seam`

---

## Task 7: Track 2 / 3 / 4 seams

**Files:**
- Modify: `src/tracks/track2_sos.py`, `src/tracks/track3_dreal.py`, `src/tracks/track4_sympy.py`
- Test: `tests/verifier/test_seams.py` (extend)

**Interfaces:**
- Produces, one per track (final signatures are whatever the post-parse body needs — pin them in this task):
  - `track2_check_from_sympy(ic_gap_expr, theta_symbol, theta_min, theta_max, *, entry_specific, paper_id) -> VerificationResult`
  - `track3_check_from_sympy(condition_exprs, symbol_bounds: dict, *, delta, entry_specific, paper_id) -> VerificationResult`
  - `track4_check_from_sympy(u_truthful_expr, u_lie_expr, ir_expr, dist, type_bounds, *, entry_specific, paper_id) -> VerificationResult`
- Each is the post-parse back-half of the existing `verify_track2/3/4(entry)`; the `verify_track*` functions keep their LaTeX front-end and call the new helper.

- [ ] **Step 1:** For each track, read `verify_track2` / `verify_track3` / `verify_track4`, find the line where it first holds parsed SymPy exprs, extract the remainder into the helper above. These tracks fire on ≤7 corpus entries total — lock the `(verdict, entry_specific)` of every corpus entry that currently routes to Track 2 (4), Track 3 (2), Track 4 (1) in `test_seams.py`.

- [ ] **Step 2:** Extract all three helpers (pure moves).

- [ ] **Step 3: Green + regression gate** — `SOS certificate (Track 2 ...): 4`, `dReal δ-verified (Track 3 ...): 1`, `Bayesian IC (Track 4 ...): 1` all unmoved; `25 / 73 / 2 / 5` unmoved.

- [ ] **Step 4: Commit** — `refactor: extract SymPy-in seams for Track 2/3/4 (no behavior change)`

---

## Task 8: `_classify_ast` + `verify_from_ast` orchestrator

**Files:**
- Create: `src/architect/ast_verify.py`
- Test: `tests/architect/test_ast_verify.py` (extend)

**Interfaces:**
- Consumes: `architect.ast.Mechanism`; `architect.serialize.ast_to_sympy`; the seven seams from Tasks 3–7; `tracks.finalize_verdict`, `tracks.VerificationResult`.
- Produces:
  - `_classify_ast(m: Mechanism) -> int` — 4 if `m.meta.get("ic_type") in {"bayesian","bic"}` or the IC subtree contains an `IndexedFamily`; 3 if any subtree contains `Func`; 2 if any subtree contains a `Pow` **and** the type space is a continuous 2-number range (or `m.meta["continuous_type"]`); else 1.
  - `verify_from_ast(m: Mechanism, meta: dict | None = None) -> VerificationResult`.

- [ ] **Step 1: Write the orchestrator tests** (fail — module absent)

```python
# tests/architect/test_ast_verify.py  (append)
from architect.ast import Mechanism, Sym, Sum, Prod, Const, Pow, Func
from architect.ast_verify import verify_from_ast, _classify_ast


def _stackelberg_effort():
    # U_i = p_i*e_i - 1/2 * c * e_i^2  — the loop's canonical VERIFIED shape
    return Mechanism(
        category="Stackelberg",
        utility=Sum([Prod([Sym("p_i"), Sym("e_i")]),
                     Prod([Const(-0.5), Sym("c"), Pow(Sym("e_i"), 2)])]),
        payment=Sym("p_i"), ic=Sym("e_i"), ir=Sym("e_i"),
        type_space=[], meta={"follower_decision": r"\( e_i \)"})


def test_classify_transcendental():
    m = _stackelberg_effort()
    m.utility = Func("ln", Sym("e_i"))
    assert _classify_ast(m) == 3


def test_classify_default_track1():
    assert _classify_ast(_stackelberg_effort()) == 1


def test_verify_from_ast_reaches_verified_stackelberg():
    r = verify_from_ast(_stackelberg_effort())
    assert r.verdict == "VERIFIED" and r.entry_specific is True
```

- [ ] **Step 2: Implement `src/architect/ast_verify.py`**

Skeleton (align the seam calls to the *actual* signatures Tasks 3–7 produced —
the implementer must open those seven functions and match parameter names):

```python
from __future__ import annotations
from architect.ast import Mechanism, Func, Pow, IndexedFamily
from architect.serialize import ast_to_sympy
from tracks import VerificationResult
from tracks.track1_z3 import (
    _vcg_check_core, _contract_check_core, _stackelberg_check_core, _shapley_check_core,
)


def _contains(node, kinds) -> bool:
    if isinstance(node, kinds):
        return True
    for attr in ("terms", "factors"):
        for c in getattr(node, attr, []) or []:
            if _contains(c, kinds):
                return True
    for attr in ("base", "arg"):
        c = getattr(node, attr, None)
        if c is not None and _contains(c, kinds):
            return True
    return False


def _is_continuous(m: Mechanism) -> bool:
    return bool(m.meta.get("continuous_type")) or (
        len(m.type_space) == 2 and all(isinstance(x, (int, float)) for x in m.type_space))


def _classify_ast(m: Mechanism) -> int:
    if m.meta.get("ic_type") in {"bayesian", "bic"} or _contains(m.ic, IndexedFamily):
        return 4
    if any(_contains(s, Func) for s in (m.utility, m.ic, m.ir, m.payment)):
        return 3
    if any(_contains(s, Pow) for s in (m.utility, m.ic, m.ir)) and _is_continuous(m):
        return 2
    return 1


def verify_from_ast(m: Mechanism, meta: dict | None = None) -> VerificationResult:
    meta = {**m.meta, **(meta or {})}
    pid = meta.get("paper_id", "architect-proposal")
    track = _classify_ast(m)
    es = True  # an AST proposal is always about "this" mechanism
    if m.category == "VCG":
        return _vcg_check_core(ast_to_sympy(m.payment), ast_to_sympy(m.utility),
                               entry_specific=es, paper_id=pid, meta=meta)
    if m.category == "Contract":
        return _contract_check_core(
            ast_to_sympy(m.ic), ast_to_sympy(m.ir),
            type_variable=meta.get("type_variable"),
            num_types=meta.get("num_types", len(m.type_space) or 2),
            entry_specific=es, paper_id=pid, meta=meta)
    if m.category == "Stackelberg":
        return _stackelberg_check_core(
            ast_to_sympy(m.utility),
            follower_decision=meta.get("follower_decision"),
            meta=meta, entry_specific=es, paper_id=pid)
    if m.category == "Shapley":
        return _shapley_check_core(paper_id=pid)
    return VerificationResult(verdict="UNSUPPORTED", category=m.category,
                              paper_id=pid, track=track,
                              notes=f"no AST verifier for category {m.category!r}")
```

For Track 2/3/4 delegation (Contract→Track 2 parametric certificate;
transcendental utilities→Track 3 first, fall through to Track 1) mirror the
fall-through order in `src/verifier.py::verify` — wire it only where `track != 1`.

- [ ] **Step 3: Green + regression gate** (`verify(entry)` untouched → 25/73/2/5 unmoved; new tests pass).

- [ ] **Step 4: Commit** — `feat: verify_from_ast orchestrator + _classify_ast (AST-native verify path)`

---

## Task 9: Parity test against `verify(entry)`

**Files:** `tests/architect/test_ast_verify.py` (extend).

**Interfaces:** consumes `verify_from_ast`, `architect.inspect.inspect_mechanism`, `verifier.verify`, and the loop's existing e2e fixtures.

- [ ] **Step 1: Locate the loop's VERIFIED fixtures** — in
`tests/architect/test_loop.py`, find
`test_loop_run_reaches_verified_via_stackelberg` and `..._via_contract`. Copy
their exact `Mechanism` + `meta` builders into `test_ast_verify.py` (or import
if they're module-level).

- [ ] **Step 2: Write the parity test**

```python
def test_ast_path_matches_latex_path_on_loop_fixtures():
    for m, meta in _loop_verified_fixtures():   # stackelberg-effort + 2-type contract
        latex_verdict = inspect_mechanism(m, meta).verdict        # AST -> LaTeX -> verify()
        ast_result = verify_from_ast(m, meta)
        assert ast_result.verdict == latex_verdict, (m.category, ast_result.verdict, latex_verdict)
        assert ast_result.verdict == "VERIFIED" and ast_result.entry_specific is True
```

- [ ] **Step 3: Run**

```bash
PYTHONPATH=src pytest tests/architect/test_ast_verify.py -v
```

If a parity case disagrees: a seam was extracted with a hidden dependency on a
LaTeX-front-end side effect. Fix the seam call / parameter list in
`ast_verify.py` — do **not** weaken the assertion.

- [ ] **Step 4: Green + regression gate. Commit** — `test: verify_from_ast parity with verify(entry) on loop fixtures`

---

## Task 10: Loop cutover behind `ARCHITECT_AST_VERIFY`

**Files:**
- Modify: `src/architect/inspect.py`
- Test: `tests/architect/test_ast_verify.py` (extend)

**Interfaces:** `inspect_mechanism(m, meta)` unchanged signature; internal dispatch on `os.environ.get("ARCHITECT_AST_VERIFY") == "1"`.

- [ ] **Step 1: Failing test**

```python
def test_inspect_uses_ast_path_when_flagged(monkeypatch):
    m, meta = _stackelberg_effort(), {}
    monkeypatch.setenv("ARCHITECT_AST_VERIFY", "1")
    assert inspect_mechanism(m, meta).verdict == "VERIFIED"
    monkeypatch.delenv("ARCHITECT_AST_VERIFY")
    assert inspect_mechanism(m, meta).verdict == "VERIFIED"   # LaTeX path still works
```

- [ ] **Step 2: Implement**

```python
# src/architect/inspect.py
import os
from architect.ast_verify import verify_from_ast

def inspect_mechanism(m, meta):
    if os.environ.get("ARCHITECT_AST_VERIFY") == "1":
        return verify_from_ast(m, meta)
    mechanism_dict, _ = render(m)          # unchanged LaTeX path below
    ...
```

Confirm `loop.py::_finish` renders `mechanism_latex` from `render(m)`
independently of `inspect` (it does). If not, keep a `render(m)` call in the
flagged branch for the LaTeX string only.

- [ ] **Step 3: Green + full suite + regression gate. Commit** — `feat: inspect_mechanism uses verify_from_ast when ARCHITECT_AST_VERIFY=1 (default off)`

---

## Task 11: Flagged live_smoke + eval; parse-error audit

**Files:** `docs/eval-results-ast.md` (generated), `docs/superpowers/notes/approach-c-parse-audit.md` (new).

- [ ] **Step 1: Run `live_smoke` with the flag**

```bash
set -a && . ./.env && set +a
PYTHONPATH=src ARCHITECT_AST_VERIFY=1 ARCHITECT_LLM_MODEL=openai/gpt-oss-120b \
  python -m architect.eval.live_smoke 2>&1 | tee /tmp/ast-live-smoke.log
```

- [ ] **Step 2: Run the eval with the flag** (long — background it)

```bash
PYTHONPATH=src ARCHITECT_AST_VERIFY=1 ARCHITECT_LLM_MODEL=openai/gpt-oss-120b \
  ARCHITECT_BUDGET_S=300 nohup python -m architect.eval.run_eval > /tmp/ast-eval.log 2>&1 &
```

- [ ] **Step 3: Audit the transcripts** — from `eval-results.json`, count transcript entries whose `verdict` is a parse/fragment error or whose `note` mentions round-trip / parse. Write `docs/superpowers/notes/approach-c-parse-audit.md`: count with the flag ON vs. the 2026-08-29 baseline (`vcg_redistribution` `PARSE` at iter 11; `vcg_cavallo_redistribution` `PARSE` at iter 12). Expected with flag on: **zero**.
- [ ] **Step 4: Copy the flagged eval table to `docs/eval-results-ast.md`.**
- [ ] **Step 5: Commit** — `docs: flagged AST-verify eval + parse-error audit`

---

## Task 12: Docs — mark Phase 1 landed

**Files:** `docs/superpowers/specs/2026-08-29-verifier-proper-checks.md`, `Task.md`.

- [ ] **Step 1:** In the roadmap spec, change the Phase 1 heading to
`## Phase 1 — Approach C: AST-native verify path  ✅ landed <date>` and add a
one-line result (parse-error count before/after from Task 11).
- [ ] **Step 2:** In `Task.md`, update the "Verifier proper-check roadmap"
item 1 to past tense with the same result line; document the flag
`ARCHITECT_AST_VERIFY`. Leave the default **off** unless Task 11 showed a clean
run AND the flagged eval verified-rate did not regress vs. `docs/eval-results.md`
(8/12) — if it regressed, keep off and log why. (`git add -f Task.md`.)
- [ ] **Step 3: Commit** — `docs: Approach C / Phase 1 landed`

---

## Self-Review

**Spec coverage** (roadmap spec Phase 1 → task):
- `ast_to_sympy` bridge → Task 2.
- track seams (seven) → Tasks 3–7.
- `_classify_ast` → Task 8. `verify_from_ast` → Task 8.
- loop cutover behind `ARCHITECT_AST_VERIFY` → Task 10.
- round-trip gate retained for corpus-insertion only → Task 10 bypasses it for
  *verification* only; `render`'s round-trip still runs for the LaTeX output
  path. ✓
- "Done when": parity test → Task 9; flagged live_smoke + eval, zero parse
  entries → Task 11. ✓
- Frozen regression gate (25/73/2/5) → in Global Constraints and every task's
  "Green" step. ✓

**Placeholder scan:** Task 3/4/5/7 leave `expected = {}` for the implementer to
fill from a live baseline run — deliberate (must be captured, not guessed), and
each names its source. Task 8 Step 2's skeleton says "align seam calls to the
actual signatures Tasks 3–7 produced" — unavoidable; the Interfaces blocks in
3–7 pin the intended shapes and Task 9's parity test catches any mismatch.

**Type consistency:** the seven seams —
`_vcg_check_core`, `_contract_check_core`, `_stackelberg_check_core`,
`_shapley_check_core` (Track 1), `track2_check_from_sympy`,
`track3_check_from_sympy`, `track4_check_from_sympy` — are signature-pinned in
Tasks 3–7 and imported by name in Task 8. `verify_from_ast(m, meta=None) ->
VerificationResult` consumed by Task 10 `inspect_mechanism` with that signature.
`_classify_ast(m) -> int` used only in Task 8. ✓

---

## Execution Handoff

Subagent-driven. Tasks 3–7 (seam extractions) are the risk core — each writes a
snapshot test *before* the move and runs the frozen regression gate after. A
task that moves any baseline number is reverted, not patched. Tasks 1–2 and
8–12 can run on a mid-tier model; 3–7 on a standard model with careful review.
