# Novelty Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the gap between what the Architect + Verifier loop claims and what it demonstrates — honest claim-scoping, a family-fidelity decision, a verifier soundness suite, baselines, eval rigor, coalition IC, and a locked RAG-trust boundary.

**Architecture:** Mostly additive. New docs (`docs/related-work.md`), new eval columns and ablation flags on the existing `architect.eval` harness, one new Track-1 function (`verify_coalition_ic_contract`), new test files, and targeted rewrites of over-broad claims in `Task.md`. No change to the core CEGIS loop control flow except a family-constraint gate in `loop.run`.

**Tech Stack:** Python 3, pytest, Z3 (`z3-solver`), SymPy, NumPy, the NVIDIA OpenAI-compatible LLM endpoint via `src/architect/llm.py`, optional PyTorch for the RegretNet baseline.

**Spec:** `docs/superpowers/specs/2026-08-29-novelty-hardening.md` (this plan implements Tasks 1–8 of that spec). Companion: `docs/superpowers/specs/2026-08-28-ast-native-verifier-future-scope.md` (deferred parts).

## Global Constraints

- Python ≥ 3.10; run tests from repo root with `PYTHONPATH=src` (or `cd src`).
- Full suite is 109 tests today; every task ends with the full suite green:
  `PYTHONPATH=src pytest -q`.
- Verifier soundness is non-negotiable: no code path may return `VERIFIED` or
  `VERIFIED_TEMPLATE` for a mechanism that is not IC/IR. When in doubt, return
  `UNKNOWN`.
- `corpus.json` is the single source of truth; never rebuild from `entries/`.
- Verdict enum lives in `src/tracks/__init__.py`: `VERIFIED`, `VERIFIED_TEMPLATE`,
  `COUNTEREXAMPLE`, `UNKNOWN`, `UNSUPPORTED`.
- Eval row schema (from `src/architect/eval/run_eval.py`) is exactly:
  `{name, mode, status, iterations, solver_calls, wall_clock, ic_regret}`.
  New columns are added at the end, never reordered.
- Commit after every task with a `feat:` / `fix:` / `docs:` / `test:` prefix.
- Do not push. Do not open a PR. Stop at the last green commit.

---

## Task A (spec Task 5): Scope the claims in Task.md

**Files:**
- Modify: `Task.md` — "Key Differentiation from Prior Work" section (~line 410),
  "Synthesis" subsection (~line 141), "Three Modes of Operation" table (~line 131).
- Test: none (documentation). Verification is a manual grep.

**Interfaces:**
- Consumes: nothing.
- Produces: the phrase "discrete-type screening + single-parameter Stackelberg +
  standard-form VCG fragment" as the canonical scope string; later tasks (B, G)
  reuse it verbatim.

- [ ] **Step 1: Record the measured coverage number**

Run: `PYTHONPATH=src python -m verifier corpus.json` and note the entry-specific
`VERIFIED` count vs. verifiable-tier total (expected ≈ 25/105).

- [ ] **Step 2: Rewrite the "any proposed mechanism structure" claim**

In "Key Differentiation from Prior Work", replace every occurrence of "for *any*
proposed mechanism structure" (and equivalent phrasings) with:

> for any mechanism expressible in the **discrete-type screening +
> single-parameter Stackelberg + standard-form VCG** fragment; outside this
> fragment the verifier returns `UNKNOWN` / `VERIFIED_TEMPLATE` and the loop
> reports non-success. On the 105-entry verifiable tier, N/105 entries reach
> entry-specific `VERIFIED` today.

(substitute the real N from Step 1.)

- [ ] **Step 3: Move the affine-maximizer caveat inline**

In the "Synthesis" subsection, add a sentence right after the `a·θ² + b·θ + c`
example:

> On the restricted type/outcome domains typical of FL, the affine-maximizer
> family is a sound but non-exhaustive subclass of DSIC mechanisms
> (Lavi–Mu'alem–Nisan 2003; Mishra–Sen 2012); Synthesis mode is "exhaustive
> search within the affine-maximizer class", not "complete over all DSIC
> mechanisms".

- [ ] **Step 4: Add a family-emergence note to the Three Modes table**

Add a footnote under the modes table:

> The mode selects *how* a mechanism is produced, not *which family*. Until spec
> Task 1 lands, the emitted family is emergent and often differs from the FL
> setting's natural family — see "What is left / Family fidelity".

- [ ] **Step 5: Verify no over-broad claim remains**

Run: `grep -n "any proposed mechanism\|for any mechanism structure\|complete over all DSIC" Task.md`
Expected: no matches, or only matches inside the new scoped phrasing.

- [ ] **Step 6: Commit**

```bash
git add Task.md
git commit -m "docs: scope verifier claims to the fragment the tracks actually cover"
```

---

## Task B (spec Task 6): Related-work / positioning note

**Files:**
- Create: `docs/related-work.md`
- Modify: `Task.md` ("Key Differentiation" — add a pointer line)
- Test: none (documentation).

**Interfaces:**
- Consumes: the scope string from Task A.
- Produces: `docs/related-work.md` with subsections `## LegoNE`,
  `## Strategy-Logic mechanism synthesis`, `## SMT in social choice`,
  `## LLM + SMT counterexample loops`, `## Open categorization question — 2405_13879`
  (last one consumed by Task H's human-decision note).

- [ ] **Step 1: Create the file**

```markdown
# Related Work and Positioning

## LegoNE (Li, Li, Deng — arXiv 2508.11874, Aug 2025)
LLM "architect" proposes approximate-Nash-equilibrium algorithms from a symbolic
building-block language; the LegoNE analyzer compiles each candidate into a
finite optimization problem that formally certifies its worst-case guarantee;
a reasoning LLM iterates on quantitative feedback. It discovered a new 3-player
ANE algorithm beating the only known human paradigm. Our loop shares this shape
(LLM proposer + formal certifier + feedback). **Distinction:** our contribution
must be a novel *FL-mechanism* result (future-scope Part 2) or the honest
per-family verifiability finding from spec Task 1 — not the architecture itself.

## Strategy-Logic mechanism synthesis (Mittelmann, Maubert, Murano, Perrussel — Artif. Intell. 2024)
A quantitative Strategy Logic + model checking to both verify mechanism
properties (strategy-proofness, budget balance) and synthesize mechanisms from a
logical spec, domain-general. **Distinction:** we operate on the real-valued
utility fragment via SMT / SOS / interval arithmetic rather than finite model
checking; we use an LLM proposer; we carry an FL-specific corpus prior.

## SMT in social choice (Brandl & Brandt et al., JACM; Barthe, Gaboardi et al., arXiv 1502.04052)
Computer-aided impossibility proofs and formal Bayesian-IC verification via SMT
and proof assistants, ~10 years old. **Distinction:** we claim only the
LLM-in-the-loop synthesis and the FL application, not "SMT can check IC".

## LLM + SMT counterexample loops (LEMUR; LaM4Inv; LORIS, TOPLAS 2026; arXiv 2508.00419)
The propose -> solver -> counterexample -> repair loop, with iteration caps and
restarts, is the standard template in LLM-assisted program verification.
**Distinction:** we claim only the mechanism-design instantiation (typed
mechanism AST, five-value IC verdict, FL corpus RAG), not the loop mechanics.

## Open categorization question — 2405_13879
`2405_13879` ("FACT or Fiction", NeurIPS 2024) is filed under Shapley but has no
characteristic function and no Shapley formula; its mechanism is a penalty rule +
"sandwich" truthfulness competition. Needs a human decision: new
"penalty + sandwich" family, or a documented reason it stays under Shapley. It is
currently silver-tier so `tools/validate.py` passes 185/185.
```

- [ ] **Step 2: Reference it from Task.md**

In `Task.md`, under "Key Differentiation from Prior Work", add as the first line:
`> Full positioning against 2024–2026 work: see docs/related-work.md.`

- [ ] **Step 3: Commit**

```bash
git add docs/related-work.md Task.md
git commit -m "docs: add related-work positioning vs LegoNE, Strategy-Logic MD, SMT social choice, LLM-SMT loops"
```

---

## Task C (spec Task 8): Lock the RAG-trust boundary

**Files:**
- Create: `tests/architect/test_rag_trust.py`
- Modify: `tools/validate.py` (add one check near the `z3_validated consistency`
  block, ~line 109)
- Test: `tests/architect/test_rag_trust.py`

**Interfaces:**
- Consumes: `architect.rag._rank`, `architect.types.ProblemSpec`.
- Produces: test-enforced guarantee that `_rank` ordering depends only on
  `(cosine, z3_validated)` and never on `ic_proof_present`.

- [ ] **Step 1: Write the failing test**

```python
# tests/architect/test_rag_trust.py
import numpy as np
from architect import rag
from architect.types import ProblemSpec


class _StubIndex:
    def __init__(self, entries, vectors):
        self.entries, self.vectors = entries, vectors
        self.embed = lambda texts: np.array([[1.0, 0.0]])


def test_rank_ignores_ic_proof_present_for_tiebreak():
    entries = [
        {"fl_setup": "x", "title": "A", "ic_proof_present": True, "z3_validated": False},
        {"fl_setup": "x", "title": "B", "ic_proof_present": False, "z3_validated": True},
    ]
    vectors = np.array([[1.0, 0.0], [1.0, 0.0]])
    idx = _StubIndex(entries, vectors)
    order, _ = rag._rank(ProblemSpec(raw_text="x"), idx)
    assert entries[order[0]]["title"] == "B", "z3_validated must win the tie, not ic_proof_present"


def test_rank_tiebreak_unaffected_when_ic_proof_present_flipped():
    entries = [
        {"fl_setup": "x", "title": "A", "ic_proof_present": False, "z3_validated": False},
        {"fl_setup": "x", "title": "B", "ic_proof_present": True, "z3_validated": False},
    ]
    vectors = np.array([[1.0, 0.0], [1.0, 0.0]])
    idx = _StubIndex(entries, vectors)
    order, _ = rag._rank(ProblemSpec(raw_text="x"), idx)
    assert order[0] == 0
```

- [ ] **Step 2: Run the test**

Run: `PYTHONPATH=src pytest tests/architect/test_rag_trust.py -v`
Expected: PASS already (current `_rank` keys on `z3_validated is not True`). If a
test FAILS, fix `architect/rag.py:_rank` so the sort key is exactly
`(-round(sim, 3), entry.get("z3_validated") is not True)` and nothing else; re-run.

- [ ] **Step 3: Add the validator consistency check**

In `tools/validate.py`, inside the `z3_validated consistency` block, add:

```python
    verdict = entry.get("z3_verdict")
    if z3 is True and verdict not in (None, "VERIFIED"):
        errors.append(
            f"[z3] z3_validated is true but z3_verdict is {verdict!r} "
            f"(expected VERIFIED) for '{entry.get('id') or category}'")
```

- [ ] **Step 4: Run validator + full suite**

Run: `PYTHONPATH=src python tools/validate.py corpus.json` -> expect 185/185.
Run: `PYTHONPATH=src pytest -q` -> all green.

- [ ] **Step 5: Commit**

```bash
git add tests/architect/test_rag_trust.py tools/validate.py
git commit -m "test: lock RAG tie-break to z3_validated; validate z3_validated<->z3_verdict consistency"
```

---

## Task D (spec Task 3): Adversarial verifier soundness suite

**Files:**
- Create: `tests/verifier/__init__.py` (empty), `tests/verifier/broken_mechanisms.py`,
  `tests/verifier/test_adversarial_soundness.py`
- Create: `src/architect/eval/soundness_report.py`
- Modify: track files under `src/tracks/` only if a false `VERIFIED` is found
- Modify: `Task.md` ("Verdict Semantics" — cite the number)
- Test: `tests/verifier/test_adversarial_soundness.py`

**Interfaces:**
- Consumes: `verifier.verify(entry: dict)` -> object with `.verdict: str`,
  `.entry_specific: bool`, `.track: int | None`.
- Produces: `architect.eval.soundness_report.run() -> dict` with keys
  `{total, false_verified, by_track: {1..4: int}, failures: [str]}`.

- [ ] **Step 1: Write the broken-mechanism fixtures**

```python
# tests/verifier/broken_mechanisms.py
"""Mechanisms that are provably NOT IC/IR. verify() must never return VERIFIED*."""

BROKEN = [
    {"name": "contract_reversed_order", "category": "Contract",
     "mechanism": {
        "client_utility_latex": r"U_i = R_i - \theta_i e_i",
        "ic_condition_latex": r"R_1 - \theta_1 e_1 \geq R_2 - \theta_1 e_2",
        "ir_condition_latex": r"R_i - \theta_i e_i \geq 0",
        "type_variable": r"\theta", "num_types": 2},
     "params": {"theta_1": 2.0, "theta_2": 1.0, "e_1": 1.0, "e_2": 3.0,
                "R_1": 2.5, "R_2": 4.0}},
    {"name": "vcg_zero_payment", "category": "VCG",
     "mechanism": {
        "allocation_rule_latex": r"x_i = 1 \text{ if } b_i = \max_j b_j",
        "payment_rule_latex": r"p_i = 0",
        "client_utility_latex": r"u_i = v_i x_i - p_i"}},
    {"name": "stackelberg_ir_violated", "category": "Stackelberg",
     "mechanism": {
        "follower_utility_latex": r"U_i = p e_i - c e_i^2 - K",
        "leader_objective_latex": r"\max_p (1-p) e_i",
        "follower_decision_latex": r"\( e_i \)"},
     "params": {"p": 0.5, "c": 1.0, "K": 10.0}},
]
```

Extend `BROKEN` to **>= 20** entries. Additional patterns to include, one fixture
each: reversed single-crossing; VCG payment that depends on own bid
(`p_i = b_i / 2`); negative reserve price; Contract menu with `R` decreasing in
effort; non-monotone menu; Stackelberg whose stated `best_response_latex`
contradicts the FOC of `follower_utility_latex`; Bayesian entry whose IC gap is
negative under the declared prior; Contract with the IC inequality pointing the
wrong way; VCG with allocation to a non-max bidder; over-priced menu item that
breaks IR for the high type.

- [ ] **Step 2: Write the failing test**

```python
# tests/verifier/test_adversarial_soundness.py
import pytest
from verifier import verify
from tests.verifier.broken_mechanisms import BROKEN

UNSOUND = {"VERIFIED", "VERIFIED_TEMPLATE"}


@pytest.mark.parametrize("case", BROKEN, ids=[c["name"] for c in BROKEN])
def test_broken_mechanism_is_never_verified(case):
    entry = {"category": case["category"], **case["mechanism"]}
    if "params" in case:
        entry["eval_params"] = case["params"]
    res = verify(entry)
    assert res.verdict not in UNSOUND, (
        f"{case['name']}: verifier returned {res.verdict} for an unsound mechanism")
```

- [ ] **Step 3: Run it**

Run: `PYTHONPATH=src pytest tests/verifier/test_adversarial_soundness.py -v`
Expected: it runs. Record every FAIL: which case, which track returned the false
`VERIFIED`.

- [ ] **Step 4: Fix each false VERIFIED at its track**

For every failing case, add a fail-closed gate in the relevant
`src/tracks/track*.py` path: when the precondition the entry-specific path relies
on (type ordering, pivot-payment shape, IR-at-optimum) is not established, return
`UNKNOWN`, never `VERIFIED`. Re-run Step 3 until green. If a case cannot fail-close
without a large redesign, mark it `@pytest.mark.xfail(reason="...")` with a
one-line reason and list it in the report — do not delete it.

- [ ] **Step 5: Write the soundness report**

```python
# src/architect/eval/soundness_report.py
from __future__ import annotations
from verifier import verify


def run() -> dict:
    from tests.verifier.broken_mechanisms import BROKEN
    out = {"total": len(BROKEN), "false_verified": 0,
           "by_track": {1: 0, 2: 0, 3: 0, 4: 0}, "failures": []}
    for case in BROKEN:
        entry = {"category": case["category"], **case["mechanism"]}
        if "params" in case:
            entry["eval_params"] = case["params"]
        res = verify(entry)
        if res.verdict in ("VERIFIED", "VERIFIED_TEMPLATE"):
            out["false_verified"] += 1
            out["failures"].append(case["name"])
            tr = getattr(res, "track", None)
            if tr in out["by_track"]:
                out["by_track"][tr] += 1
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
```

- [ ] **Step 6: Run report + full suite**

Run: `PYTHONPATH=src python -m architect.eval.soundness_report` -> `"false_verified": 0`.
Run: `PYTHONPATH=src pytest -q` -> all green.

- [ ] **Step 7: Cite the number in Task.md**

Under "Verdict Semantics", add: `Adversarial soundness suite (tests/verifier/):
N known-unsound mechanisms, 0 false VERIFIED (src/architect/eval/soundness_report.py).`

- [ ] **Step 8: Commit**

```bash
git add tests/verifier src/architect/eval/soundness_report.py Task.md
git commit -m "test: adversarial verifier soundness suite; fail-close any false VERIFIED"
```

---

## Task E (spec Task 1): Family fidelity — constrain to expected_family (Option A)

**Files:**
- Modify: `src/architect/types.py` (add fields), `src/architect/loop.py`
  (family gate + `_finish`), `src/architect/architect.py` (`propose` prompt)
- Modify: `src/architect/eval/__init__.py` (`evaluate` records `family_match`),
  `src/architect/eval/run_eval.py` (2 new columns)
- Create: `tests/architect/test_loop_family_constraint.py`
- Modify: `Task.md` ("What is left / Family fidelity")
- Test: `tests/architect/test_loop_family_constraint.py`

**Interfaces:**
- Consumes: `benchmarks.BENCHMARKS[i]["expected_family"]`.
- Produces: `ProblemSpec.expected_family: str | None`;
  `ArchitectResult.emitted_family: str | None`,
  `ArchitectResult.family_match: bool | None`; `evaluate` rows gain
  `{"expected_family": str, "family_match": bool | None}`.

- [ ] **Step 1: Add the fields**

In `src/architect/types.py`: add `expected_family: str | None = None` to
`ProblemSpec`; add `emitted_family: str | None = None` and
`family_match: bool | None = None` to `ArchitectResult`.

- [ ] **Step 2: Write the failing test**

```python
# tests/architect/test_loop_family_constraint.py
from architect import loop
from architect.types import ProblemSpec
# Build stub deps in the style of tests/architect/test_loop.py: LLM stubbed at
# propose(), everything else real. propose() here always returns a mechanism
# whose serialized category is "Stackelberg".


def test_loop_rejects_off_family_proposal_and_feeds_back(stub_deps_stackelberg):
    spec = ProblemSpec(raw_text="a 2-type screening problem",
                       expected_family="Contract")
    res = loop.run(spec, index=None, budget_s=5.0, deps=stub_deps_stackelberg)
    assert res.status == "FAILED"
    assert res.emitted_family == "Stackelberg"
    assert res.family_match is False
    assert any("Contract" in (e.get("hint", "") or "") for e in res.transcript)
```

Add a `stub_deps_stackelberg` fixture in the test file mirroring `test_loop.py`'s
existing stub construction.

- [ ] **Step 3: Run it**

Run: `PYTHONPATH=src pytest tests/architect/test_loop_family_constraint.py -v`
Expected: FAIL (loop accepts any family today).

- [ ] **Step 4: Implement the family gate in `loop.run`**

After the proposal is rendered and its category is known, before `deps.inspect`:

```python
        emitted_family = getattr(m, "category", None) or (mech_dict or {}).get("category")
        if spec.expected_family and emitted_family != spec.expected_family:
            fb = Feedback(kind="wrong_family",
                          hint=(f"You proposed a {emitted_family} mechanism, but "
                                f"this FL setting requires a {spec.expected_family} "
                                f"mechanism. Re-propose in the {spec.expected_family} "
                                f"family."))
            transcript.append({"iter": iterations, "family": emitted_family,
                               "hint": fb.hint})
            if _repair(fb) == "fail":
                return _finish("FAILED", None, None, None)
            continue
```

Thread `emitted_family` into `_finish` and set
`family_match = (emitted_family == spec.expected_family)` when `expected_family`
is set, else `None`.

- [ ] **Step 5: Add the constraint to the propose prompt**

In `src/architect/architect.py` `propose`, when `spec.expected_family` is set,
prepend to the instruction text:
`"You MUST propose a mechanism in the {expected_family} family. Do not switch families."`
Ensure Synthesis/Hybrid routing stays within that family.

- [ ] **Step 6: Run the new test + full suite**

Run: `PYTHONPATH=src pytest tests/architect/test_loop_family_constraint.py -v` -> PASS
Run: `PYTHONPATH=src pytest -q` -> green (fix any `ProblemSpec(...)` /
`ArchitectResult(...)` call sites the new fields break).

- [ ] **Step 7: Wire `family_match` into the eval harness**

In `src/architect/eval/__init__.py` `evaluate`: build each `ProblemSpec` with
`expected_family=bench["expected_family"]`; add to the row dict
`"expected_family": bench["expected_family"]`, `"family_match": result.family_match`.
In `run_eval.py`: extend `hdr`, the `sep` count (7 -> 9), and the `body` f-string
with the two columns.

- [ ] **Step 8: Commit**

```bash
git add src/architect tests/architect/test_loop_family_constraint.py
git commit -m "feat: constrain Architect output to expected_family; report family_match in eval"
```

- [ ] **Step 9: Update Task.md**

In "What is left / Family fidelity", replace the open-question text with:
"Resolved (Option A): the loop is hard-constrained to `expected_family` and FAILs
in-family rather than reframing. Per-family verify rate is now the eval's primary
honesty metric — see docs/eval-results.md." Commit:
`docs: mark family-fidelity resolved via expected_family constraint`.

---

## Task F (spec Task 7): Coalition IC for discrete Contract menus

**Files:**
- Modify: `src/tracks/track1_z3.py` (add `verify_coalition_ic_contract`),
  `src/tracks/__init__.py` (`VerificationResult` gains `coalition_ic_k`)
- Create: `tests/verifier/test_coalition_ic.py`
- Modify: `src/architect/eval/__init__.py` (report `coalition_ic_regret`),
  `src/architect/eval/run_eval.py` (1 new column)
- Test: `tests/verifier/test_coalition_ic.py`

**Interfaces:**
- Consumes: numeric `entry["menu"]` with keys `theta_i`, `e_i`, `R_i` for
  `i in 1..num_types`.
- Produces: `verify_coalition_ic_contract(entry: dict, k: int = 2) ->
  VerificationResult` with `.verdict in {VERIFIED, COUNTEREXAMPLE, UNKNOWN,
  UNSUPPORTED}` and `.coalition_ic_k: int | None`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/verifier/test_coalition_ic.py
from tracks.track1_z3 import verify_coalition_ic_contract

_SAFE = {
    "category": "Contract", "num_types": 2, "type_variable": r"\theta",
    "menu": {"theta_1": 1.0, "theta_2": 2.0, "e_1": 2.0, "e_2": 1.0,
             "R_1": 2.0, "R_2": 1.0},
}
_BREAKABLE = {**_SAFE,
    "menu": {"theta_1": 1.0, "theta_2": 2.0, "e_1": 2.0, "e_2": 1.9,
             "R_1": 2.0, "R_2": 1.99}}


def test_coalition_safe_menu_verifies():
    res = verify_coalition_ic_contract(_SAFE, k=2)
    assert res.verdict == "VERIFIED"
    assert res.coalition_ic_k == 2


def test_coalition_breakable_menu_is_counterexample():
    res = verify_coalition_ic_contract(_BREAKABLE, k=2)
    assert res.verdict == "COUNTEREXAMPLE"


def test_k_larger_than_menu_is_unsupported():
    assert verify_coalition_ic_contract(_SAFE, k=5).verdict == "UNSUPPORTED"
```

Before trusting `_BREAKABLE`, compute `u(1,2)+u(2,1)` vs `u(1,1)+u(2,2)` by hand;
adjust `R_2`/`e_2` until types 1 and 2 strictly gain by swapping contracts.

- [ ] **Step 2: Run the tests**

Run: `PYTHONPATH=src pytest tests/verifier/test_coalition_ic.py -v`
Expected: FAIL (`ImportError` / `AttributeError`).

- [ ] **Step 3: Implement `verify_coalition_ic_contract`**

```python
def verify_coalition_ic_contract(entry: dict, k: int = 2):
    from tracks import VerificationResult
    menu = entry.get("menu") or {}
    n = int(entry.get("num_types") or 0)
    if not menu or n == 0 or k > n:
        return VerificationResult(verdict="UNSUPPORTED", category="Contract",
            track=1, details=f"coalition size {k} vs {n} types / no numeric menu")
    if k != 2 or n != 2:
        return VerificationResult(verdict="UNSUPPORTED", category="Contract",
            track=1, details="only k=n=2 supported in this round")

    def u(i, r):
        return menu[f"R_{r}"] - menu[f"theta_{i}"] * menu[f"e_{r}"]

    truthful = u(1, 1) + u(2, 2)
    for r1 in (1, 2):
        for r2 in (1, 2):
            if (r1, r2) == (1, 2):
                continue
            if u(1, r1) + u(2, r2) > truthful + 1e-9:
                return VerificationResult(verdict="COUNTEREXAMPLE",
                    category="Contract", track=1, coalition_ic_k=k,
                    details=f"types (1,2) jointly report ({r1},{r2}); gain "
                            f"{u(1, r1) + u(2, r2) - truthful:.4g}")
    return VerificationResult(verdict="VERIFIED", category="Contract", track=1,
        coalition_ic_k=k, entry_specific=True,
        details="no profitable 2-type joint deviation")
```

Add `coalition_ic_k: int | None = None` to the `VerificationResult` dataclass in
`src/tracks/__init__.py`.

- [ ] **Step 4: Run tests + full suite**

Run: `PYTHONPATH=src pytest tests/verifier/test_coalition_ic.py -v` -> PASS
Run: `PYTHONPATH=src pytest -q` -> all green.

- [ ] **Step 5: Add coalition IC-regret to the eval**

In `src/architect/eval/__init__.py`: for a benchmark with
`expected_family == "Contract"` that reached `VERIFIED` and whose emitted
mechanism carries a numeric menu, call `verify_coalition_ic_contract`; set
`row["coalition_ic_regret"] = 0.0` on `VERIFIED`, the reported gain on
`COUNTEREXAMPLE`, else `None`. Add one column to `run_eval.py`.

- [ ] **Step 6: Commit**

```bash
git add src/tracks src/architect/eval tests/verifier/test_coalition_ic.py
git commit -m "feat: 2-type coalition IC check for discrete Contract menus + eval column"
```

---

## Task G (spec Task 4): Eval rigor — seeds, ablations, second model

**Files:**
- Modify: `src/architect/eval/__init__.py` (`evaluate` gains `seeds`,
  `ablations`, `deps_factory`; add `summarize`)
- Modify: `src/architect/eval/run_eval.py` (`argparse`: `--seeds`, `--model`,
  `--ablations`; extra output tables)
- Modify: `src/architect/eval/benchmarks.py` (grow to >= 12)
- Create: `tests/architect/test_eval_rigor.py`
- Test: `tests/architect/test_eval_rigor.py`

**Interfaces:**
- Consumes: `loop.run(spec, index=, budget_s=, deps=)`.
- Produces: `evaluate(index, *, seeds=(0,), model=None, ablations=None,
  deps_factory=None)` -> rows tagged with `seed` (and `ablation` when set);
  `summarize(rows) -> list[dict]` with keys
  `{name, verified_rate, iters_mean, iters_spread, wall_clock_mean, ic_regret_mean}`.

- [ ] **Step 1: Grow the benchmark set**

Add >= 7 dicts to `BENCHMARKS` (total >= 12), each with `name`, `text`,
`expected_family`, `reference`. Cover: 2-type and 3-type screening contracts; a
single-parameter Stackelberg pricing game with a stated FOC; a Clarke-pivot VCG;
a redistribution VCG; a budget-balanced contract. For `reference == "hand-derived"`
put the reference mechanism in an adjacent `# ref:` comment.

- [ ] **Step 2: Write the shape test**

```python
# tests/architect/test_eval_rigor.py
from architect.eval import evaluate, summarize


def test_evaluate_runs_multiple_seeds(stub_index, stub_deps_factory):
    rows = evaluate(index=stub_index, seeds=(0, 1, 2),
                    deps_factory=stub_deps_factory)
    names = {r["name"] for r in rows}
    for n in names:
        assert sum(1 for r in rows if r["name"] == n) == 3
    summ = summarize(rows)
    assert all({"verified_rate", "wall_clock_mean"} <= set(s) for s in summ)
```

Provide `stub_index` / `stub_deps_factory` fixtures in the test file, mirroring
`tests/architect/test_loop.py`. No live API calls in tests.

- [ ] **Step 3: Run it**

Run: `PYTHONPATH=src pytest tests/architect/test_eval_rigor.py -v`
Expected: FAIL (`evaluate` has no `seeds`; no `summarize`).

- [ ] **Step 4: Implement `seeds`, `ablations`, `summarize`**

- `evaluate(...)`: loop over `seeds`; for each, if `llm.py` accepts a seed pass
  it, else record `seed` and accept nondeterminism; tag each row `"seed": s`.
- `ablations`: list drawn from
  `{"no_rag", "cap2", "cap10", "no_mc", "force_family"}`; for each, build `deps`
  with that knob flipped (`deps_factory(ablation=...)`), tag rows `"ablation": a`.
- `summarize(rows)`: group by `name`; emit the six-key dict above
  (`verified_rate` = fraction of that name's rows with `status == "VERIFIED"`).

- [ ] **Step 5: CLI flags + extra tables**

`run_eval.py`: `argparse` with `--seeds` (int, default 1), `--model` (str,
forwarded via `ARCHITECT_LLM_MODEL` / `llm.py`), `--ablations` (store_true).
After the main table, append `## Seed variance` (from `summarize`); with
`--ablations`, also `## Ablations`; when `--model` != default, also
`## Model comparison`.

- [ ] **Step 6: Run tests + full suite**

Run: `PYTHONPATH=src pytest tests/architect/test_eval_rigor.py -v` -> PASS
Run: `PYTHONPATH=src pytest -q` -> all green.

- [ ] **Step 7: Commit**

```bash
git add src/architect/eval tests/architect/test_eval_rigor.py
git commit -m "feat: eval seeds, ablation knobs, model flag, summarize() with variance"
```

- [ ] **Step 8: Note the manual step in the commit body**

The actual multi-seed / second-model runs (`python -m architect.eval.run_eval
--seeds 3 --ablations`, then a `--model <frontier>` pass) are executed by the
human against the live API; their output is pasted into `docs/eval-results.md`.
The plan delivers the harness, not the API spend.

---

## Task H (spec Task 2): Baselines — control + RegretNet + Liu et al. adapters

**Files:**
- Create: `src/architect/eval/baselines/__init__.py` (+ shared misreport-grid
  helper), `.../control.py`, `.../regretnet.py`, `.../liu_amd_llm.py`
- Modify: `src/architect/eval/run_eval.py` (`--with-baselines`)
- Create: `tests/architect/test_baselines.py`
- Test: `tests/architect/test_baselines.py`

**Interfaces:**
- Consumes: `benchmarks.BENCHMARKS`, `verifier.verify`, guarded `import torch`.
- Produces: `run_baseline(name: str, bench: dict) -> dict` — a row in the eval
  schema plus `"method": name`; `name in {"control", "regretnet", "liu_amd_llm"}`.

- [ ] **Step 1: Research & Reuse (no code)**

`gh search repos "RegretNet optimal auctions" --language=Python`;
`gh search code "RegretNet" --language=Python`;
`gh search repos "automated mechanism design LLM"` for a 2502.12203 release.
Record the chosen upstream repo + commit hash in each module's docstring. If no
usable RegretNet repo exists, scope `regretnet.py` to the 2x2 uniform
single-item case with a ~50-line training loop and state that in the docstring.

- [ ] **Step 2: Control baseline + test**

```python
# src/architect/eval/baselines/control.py
"""Trivial control: emit the textbook follower-effort mechanism for every input."""
from verifier import verify

FOLLOWER_EFFORT = {
    "category": "Stackelberg",
    "follower_utility_latex": r"U_i = p_i e_i - \tfrac{1}{2} c e_i^2",
    "follower_decision_latex": r"\( e_i \)",
    "best_response_latex": r"e_i^* = p_i / c",
}


def run_baseline(name, bench):
    res = verify(dict(FOLLOWER_EFFORT))
    return {"name": bench["name"], "method": "control", "mode": "n/a",
            "status": res.verdict, "iterations": 0, "solver_calls": 1,
            "wall_clock": 0.0,
            "ic_regret": 0.0 if res.verdict == "VERIFIED" else None,
            "family_match": bench["expected_family"] == "Stackelberg"}
```

```python
# tests/architect/test_baselines.py
from architect.eval.baselines.control import run_baseline
from architect.eval.benchmarks import BENCHMARKS


def test_control_baseline_row_shape():
    row = run_baseline("control", BENCHMARKS[0])
    assert {"name", "method", "status", "ic_regret", "family_match"} <= set(row)
    assert row["method"] == "control"
```

Run: `PYTHONPATH=src pytest tests/architect/test_baselines.py -v` -> PASS.

- [ ] **Step 3: RegretNet adapter**

`regretnet.py`: guarded `import torch`; if absent, `run_baseline` returns a row
with `status="SKIPPED_NO_TORCH"`. Otherwise train the scoped model for the
benchmark's setting, compute empirical IC-regret as the max utility gain over a
sampled misreport grid (shared helper in `baselines/__init__.py`), return the
row with `method="regretnet"`. Training loop < 100 lines; cite the upstream repo
from Step 1.

- [ ] **Step 4: Liu et al. adapter**

`liu_amd_llm.py`: handles `myerson_single_item` and `vcg_redistribution` only.
Call the upstream repo if vendored under `third_party/`, else reimplement their
fix-process (Myerson monotonicity repair + critical-price construction) in ~150
lines for those two templates. Return the row with `method="liu_amd_llm"` and
IC-regret from the same shared misreport grid.

- [ ] **Step 5: Wire `--with-baselines`**

In `run_eval.py`: when set, after the Architect rows, run each baseline over all
benchmarks and append a `## Baselines` table with columns
`| name | method | status | ic_regret | family_match |`.

- [ ] **Step 6: Full suite**

Run: `PYTHONPATH=src pytest -q` -> all green (only the control row-shape test
runs; no training in the test suite).

- [ ] **Step 7: Commit**

```bash
git add src/architect/eval/baselines src/architect/eval/run_eval.py tests/architect/test_baselines.py
git commit -m "feat: control + RegretNet + Liu-et-al baseline adapters, --with-baselines"
```

---

## Self-Review

**Spec coverage:**
- spec Task 1 -> Task E; Task 2 -> Task H; Task 3 -> Task D; Task 4 -> Task G;
  Task 5 -> Task A; Task 6 -> Task B; Task 7 -> Task F; Task 8 -> Task C.
  All eight covered.
- spec "Suggested order" (5, 6, 8, 3, 1, 7, 4, 2) == plan order A, B, C, D, E, F, G, H. ✓

**Placeholder scan:** the `BROKEN` fixtures (Task D Step 1) and the extra
benchmarks (Task G Step 1) are given by *pattern* with >= 3 concrete examples
each and an explicit count target — the executor must still write all 20 / all
12. The RegretNet/Liu training bodies (Task H Steps 3–4) are scoped by size +
upstream-repo citation rather than literal code, because the upstream choice is
made in Step 1 — a deliberate, flagged exception, not an accidental TODO. No
"TBD" / "add error handling" / "similar to Task N" strings elsewhere.

**Type consistency:** `VerificationResult.coalition_ic_k` (Task F) — referenced
only in Task F. `ProblemSpec.expected_family` and
`ArchitectResult.{emitted_family, family_match}` (Task E) are consumed by Task
G's `evaluate` and Task H's `run_baseline` (`family_match`). Eval row schema
grows monotonically: base 7 -> +`expected_family`, +`family_match` (E) ->
+`coalition_ic_regret` (F); baselines emit a subset plus `method`.
`run_baseline(name, bench) -> dict` is identical across control/regretnet/liu.
`summarize(rows) -> list[dict]` keys are fixed in Task G's Interfaces block. ✓

---

## Execution Handoff

Chosen by the user: **Subagent-Driven**. Proceed with
superpowers:subagent-driven-development — fresh subagent per task (A -> H),
two-stage review between tasks, full `PYTHONPATH=src pytest -q` green before each
commit. Stop at the last green commit; do not push, do not open a PR.
