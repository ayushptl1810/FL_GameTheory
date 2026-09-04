# R5 — Phase 4: Coalition / Shapley Track — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `src/tracks/track_coalition.py` — a two-tier `verify_coalition` for `k <= 3` (symbolic Shapley-identity check + numeric core/IR grid) — wire it into the verifier and the AST path, then run a targeted sweep of the 4 Shapley corpus entries, hand-checking any flip and diagnosing every non-flip as `MANUAL`.

**Architecture:** R5 is a new-track round in the mold of R2's VCG allocation-classifier: it ships committed solver code + tests + PDF-grounded corpus data + a targeted sweep, and stays valuable at a low flip count because the track is standalone infra R6 and the Architect loop reuse. `verify_coalition` has two tiers. **Tier A (symbolic):** parse `shapley_formula_latex`, check via SymPy that it equals the Shapley value `sum_{S subseteq N\{i}} |S|!(n-|S|-1)!/n! * [v(S∪{i}) - v(S)]` as an identity in an abstract `v` (this subsumes efficiency / symmetry / dummy / additivity). **Tier B (numeric):** runs only when a concrete finite `mechanism.coalition_values` is transcribed from the PDF (`S -> numeric v(S)` for every `S subseteq N`, `|N| <= 3`) — enumerate all `2^k` coalitions, compute each `phi_i`, check the stated payment matches, check core (`sum_{i in S} phi_i >= v(S)` for all `S`) and IR (`phi_i >= v({i})`). **`VERIFIED` only on Tier B passing AND Tier A passing**, cross-checked. Tier A alone -> `MANUAL`. `k > 3` / non-enumerable / transcendental / opaque `v` -> `MANUAL` with the specific obstruction. Fail-closed default: not decidable. Branch `round-R5-coalition-track` off `main`, local merge only.

**Tech Stack:** Python 3.14, SymPy (`sympy.parsing.latex.parse_latex`, `sympy.Rational`, `sympy.simplify`), Z3 (unused this round). Tests: pytest, `PYTHONPATH=src:.`. Verifier/gate: `PYTHONPATH=src`. LLM sweep: `architect.formalize` against the `.env` NVIDIA endpoint (`openai/gpt-oss-20b`), `ARCHITECT_LLM_TIMEOUT_S=300`.

**Spec:** `docs/superpowers/specs/2026-09-02-zero-unknown-program-design.md` (§R5, §"The automation ceiling" row 5, §"Cross-round invariants").

## Global Constraints

Copied verbatim from the spec's §"Cross-round invariants" and §R5:

- **Monotone corpus gate.** After every task, `PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R5-baseline.md --only Shapley corpus.json` must print `GATE: PASS`. `VERIFIED` (entry-specific) count only rises or holds. No entry moves to a strictly-worse verdict. `UNSUPPORTED` -> `MANUAL` or `UNSUPPORTED` -> `VERIFIED` is the target; `UNSUPPORTED` -> `UNSUPPORTED` is acceptable mid-round but the round must end with Shapley `UNSUPPORTED` = 0; anything -> bare `UNKNOWN` is a regression.
- **Per-round baseline.** Task 1 captures `docs/superpowers/notes/round-R5-baseline.md` (full per-entry verdict table) before any change, via `scripts.snapshot_verdicts` with a required `--out`.
- **Every flip cross-checked.** Each new `VERIFIED` records in `docs/superpowers/notes/round-R5-new-verified.md`: entry id, what Tier A + Tier B now handle, and one independent check — hand-computed Shapley values `phi_i` from the transcribed `v(S)` with the core inequalities shown, OR a cited theorem (Shapley 1953 uniqueness / a convexity-implies-core-nonempty cite the paper makes). A new `VERIFIED` with no cross-check is a round failure and reverts to baseline.
- **`MANUAL` always carries a reason.** Any entry set `MANUAL` gets `verdict_override: "MANUAL"` + a `manual_diagnosis` dict (`round`, `track`, `limit`, `mechanism`, `obstruction`, `human_task`, `date`) in `corpus.json` and a paragraph in `docs/superpowers/notes/MANUAL-backlog.md`. `track` for coalition entries is `5`.
- **Formalizer is never a verify-time dependency.** `PYTHONPATH=src python -m verifier corpus.json` must run with **no API key** after every task. `src/tracks/track_coalition.py` must not `import architect.*` or any LLM client. `mechanism.coalition_values` is plain data read by the deterministic solver path.
- **Corpus data is declared, not inferred.** Every `coalition_values` / `coalition_n` field is transcribed from the entry's source PDF and the location (section / equation / page / worked example) is recorded in a sibling `coalition_values_source` note. A `v(S)` instance that cannot be found in the PDF is left absent and the entry stays `MANUAL`.
- **Fail closed.** Any parse ambiguity, undecidable fragment, unclean hand-check, or a corpus field that cannot be confirmed against the paper -> the entry goes to a diagnosed `MANUAL` — never a guessed `VERIFIED` / `COUNTEREXAMPLE`. `verify_coalition` returns `MANUAL` on anything it does not positively recognise.
- **Branch per round.** `round-R5-coalition-track` off `main`; merge to `main` on a clean whole-branch review before R6 branches. Local merges only, no push, no PR.
- **Out of scope, never touched:** the ~80 `Valuation` / `RL` / `Naive` entries; the 60 `MANUAL` entries from R2–R4 (R6 work); the 32 R6 formalization-miss candidates; every VCG / Contract / Stackelberg entry. R5 touches only the 4 `category == "Shapley"` entries and the new track file + its wiring.

---

## The 4 Shapley entries (from `corpus.json`, `category == "Shapley"`)

| paper_id | tier | `characteristic_function_latex` | `shapley_formula_latex` | R5 expected outcome |
|---|---|---|---|---|
| `2502_08248` | silver | `v(S) = F(c)` (max-flow value) | standard Shapley formula (`Sh_i = sum_{S: i in S} (|S|-1)!(|N|-|S|)!/|N|! (v(S) - v(S\{i}))`) | **Tier-B candidate.** `VERIFIED` if the PDF gives a concrete capacity network; else `MANUAL`. |
| `2605_11889` | silver | `v(D_C) = log p(T=T*|D_C) - log p(T=T*|emptyset)` | standard formula (`phi_i = sum_{C subseteq N\{i}} |C|!(n-|C|-1)!/n! [v(C∪{i}) - v(C)]`) | Tier A likely passes; Tier B: attempt transcription, expect no numeric instance (transcendental log-likelihood value) -> **`MANUAL`**. |
| `2606_18384` | bronze | `v(Sub) := U(M_Sub^(R))` (opaque model-utility) | `phi_j = K * sum_{Sub} [U(M_{Sub∪{j}}) - U(M_Sub)] / binom(|C|-1, |Sub|)` — a `K`-normalized OR-**approximation** | Tier A shows formula != exact Shapley (the `1/binom` weighting and `K` factor); Tier B: opaque NN-accuracy value, no numeric instance -> **`MANUAL`** (documented approximation). |
| `2405_13879` | silver | `null` | `null` | No `v(S)`, no Shapley value anywhere in the paper (corpus `notes` establish this, fail-closed). **`MANUAL`** — mis-categorized: penalty-based free-riding truthfulness (`P_fr` Eq 4, `P_ct` Eq 10). Human task: re-categorize as Contract/penalty-mechanism or confirm out-of-scope. No `verify_coalition` run — diagnosed from corpus notes. |

Net expected: **+0–1 real `VERIFIED`, 3–4 diagnosed `MANUAL`**; Shapley `UNSUPPORTED` 4 -> 0.

---

## File Structure

**Solver code (new file):**
- `src/tracks/track_coalition.py` — the whole track. `verify_coalition(entry: dict) -> VerificationResult`; helpers `_parse_coalition_values`, `_shapley_from_values`, `_tier_a_symbolic_identity`, `_tier_b_numeric_core`. ~200 lines. No `import architect.*`, no Z3.

**Wiring (small edits to existing files):**
- `src/tracks/track1_z3.py` — `verify_shapley` (currently returns `_shapley_check_core`'s unconditional `UNSUPPORTED`) delegates to `track_coalition.verify_coalition` when `entry["mechanism"].get("shapley_formula_latex")` is a non-empty string; otherwise returns a `MANUAL` `VerificationResult` (not the old `UNSUPPORTED` stub) with `notes` from `entry.get("manual_diagnosis")`. `_shapley_check_core` stays as a private fallback but is no longer the public path.
- `src/architect/ast_verify.py:326` — the `if m.category == "Shapley": return _shapley_check_core(paper_id=pid)` line becomes a `verify_coalition({"mechanism": meta, "paper_id": pid})` call.
- `src/architect/ast_verify.py:54` `_classify_ast` — add `if m.category == "Shapley": return 5` so `track` is reported correctly (currently falls through to a default). Confirm no existing branch keys on `track == 5`.
- `src/verifier.py:135,168` dispatch dicts — no change needed (`"Shapley": verify_shapley` already routes; `verify_shapley`'s new body does the delegation).

**Corpus data (transcribed from PDFs — new `mechanism` fields, one commit):**
- `corpus.json` — Task 5: `coalition_values` (map `"" | "1" | "2" | "1,2" | "1,2,3" | ...` -> float), `coalition_n` (int <= 3), `coalition_values_source` (str: section/eq/page) for whichever of `2502_08248` / `2605_11889` / `2606_18384` have a concrete numeric `v(S)` instance in their source PDF. Absent for entries with no instance.
- `corpus.json` — Task 6: `verdict_override: "MANUAL"` + `manual_diagnosis` for every non-flip; `2405_13879` gets its mis-categorization diagnosis in Task 6 too.

**Notes:**
- `docs/superpowers/notes/round-R5-baseline.md` (Task 1, generated)
- `docs/superpowers/notes/round-R5-new-verified.md` (Task 6, created — may be empty-with-header if 0 flips)
- `docs/superpowers/notes/round-R5-sweep-raw.md` (Task 6, raw run report)
- `docs/superpowers/notes/round-R5-delta.md` (Task 7)
- `docs/superpowers/notes/MANUAL-backlog.md` (appended in Task 6)

**Tests:**
- `tests/tracks/test_coalition.py` (Tasks 2–5)
- existing suites (`tests/verifier/*`, `tests/tracks/*`, `tests/architect/*`) stay green; a stale-expected-value pin update is permitted only where a Shapley verdict legitimately moved (`UNSUPPORTED` -> `MANUAL` / `VERIFIED`).

---

## Task 1: Branch + baseline

**Files:**
- Create: `docs/superpowers/notes/round-R5-baseline.md` (generated)

**Interfaces:**
- Consumes: `scripts.snapshot_verdicts.main` (required `--out`), `scripts.round_gate.main` (`--baseline`, `--only`).
- Produces: `round-R5-baseline.md` — the per-entry verdict table every later task's gate runs against.

- [ ] **Step 1: Branch off main**

```bash
git checkout main && git pull --ff-only 2>/dev/null; git checkout -b round-R5-coalition-track
```

- [ ] **Step 2: Capture the baseline snapshot**

```bash
PYTHONPATH=src python -m scripts.snapshot_verdicts corpus.json --out docs/superpowers/notes/round-R5-baseline.md
```

Expected: file written with the full per-entry verdict table. Confirm the 4 Shapley rows all read `UNSUPPORTED`:

```bash
grep -iE "2502_08248|2605_11889|2606_18384|2405_13879" docs/superpowers/notes/round-R5-baseline.md
```

Expected: 4 lines, each ending `UNSUPPORTED`.

- [ ] **Step 3: Verify the gate passes against its own baseline (no-op check)**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R5-baseline.md --only Shapley corpus.json
```

Expected: `GATE: PASS`.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/notes/round-R5-baseline.md
git commit -m "chore(R5): branch + Shapley-slice baseline snapshot"
```

---

## Task 2: `track_coalition.py` skeleton + `_parse_coalition_values` + `_shapley_from_values`

**Files:**
- Create: `src/tracks/track_coalition.py`
- Test: `tests/tracks/test_coalition.py`

**Interfaces:**
- Consumes: `tracks.VerificationResult` (dataclass: `verdict`, `category`, `paper_id`, `track`, `conditions: list[str]`, `notes: str`, `entry_specific: bool`).
- Produces:
  - `_parse_coalition_values(raw: dict, n: int) -> dict[frozenset[int], float]` — `raw` maps a comma-joined member string (`""`, `"1"`, `"1,2"`, …) to a number; returns a map keyed by `frozenset` of 1-based player ints. Raises `ValueError` if any of the `2**n` subsets of `{1..n}` is missing, if `n > 3`, or if a value is non-numeric.
  - `_shapley_from_values(values: dict[frozenset[int], float], n: int) -> dict[int, float]` — exact Shapley value per player via the marginal-contribution sum over all `n!` orderings (`math.factorial`; `n <= 3` so brute force is fine).

- [ ] **Step 1: Write the failing tests**

```python
# tests/tracks/test_coalition.py
import math
from itertools import combinations
import pytest
from tracks.track_coalition import _parse_coalition_values, _shapley_from_values


def _all_subsets(n):
    for k in range(n + 1):
        for c in combinations(range(1, n + 1), k):
            yield c


def test_parse_coalition_values_builds_frozenset_map():
    raw = {"": 0.0, "1": 1.0, "2": 2.0, "1,2": 4.0}
    got = _parse_coalition_values(raw, n=2)
    assert got[frozenset()] == 0.0
    assert got[frozenset({1})] == 1.0
    assert got[frozenset({1, 2})] == 4.0


def test_parse_coalition_values_missing_subset_raises():
    with pytest.raises(ValueError, match="missing"):
        _parse_coalition_values({"": 0.0, "1": 1.0, "1,2": 4.0}, n=2)  # no "2"


def test_parse_coalition_values_rejects_n_over_3():
    with pytest.raises(ValueError, match="n <= 3"):
        _parse_coalition_values({}, n=4)


def test_parse_coalition_values_rejects_non_numeric():
    with pytest.raises(ValueError, match="numeric"):
        _parse_coalition_values({"": 0.0, "1": "x", "2": 2.0, "1,2": 4.0}, n=2)


def test_shapley_from_values_glove_game():
    # 3-player: players 1,2 hold a left glove, player 3 a right glove.
    # v(S)=1 iff S contains 3 and at least one of {1,2}; else 0.
    def v(s):
        return 1.0 if (3 in s and ({1, 2} & s)) else 0.0
    values = {frozenset(c): v(set(c)) for c in _all_subsets(3)}
    phi = _shapley_from_values(values, n=3)
    assert math.isclose(phi[1], 1 / 6, abs_tol=1e-9)
    assert math.isclose(phi[2], 1 / 6, abs_tol=1e-9)
    assert math.isclose(phi[3], 2 / 3, abs_tol=1e-9)
    assert math.isclose(sum(phi.values()), 1.0, abs_tol=1e-9)  # efficiency
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_coalition.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tracks.track_coalition'`.

- [ ] **Step 3: Write the minimal implementation**

```python
# src/tracks/track_coalition.py
"""Track 5 — coalition / Shapley verification (k <= 3).

Tier A: symbolic — the stated shapley_formula_latex *is* the Shapley value.
Tier B: numeric — core / IR / payment on an enumerated characteristic function.

VERIFIED only when Tier A and Tier B both pass. Anything unrecognised or
undecidable -> MANUAL. Fail-closed default. No architect/LLM imports.
"""
from __future__ import annotations

import math
from itertools import combinations, permutations

from tracks import VerificationResult

_MAX_N = 3


def _all_subsets(n: int):
    for k in range(n + 1):
        for c in combinations(range(1, n + 1), k):
            yield frozenset(c)


def _parse_coalition_values(raw: dict, n: int) -> dict[frozenset[int], float]:
    if n > _MAX_N:
        raise ValueError(f"coalition_n={n}: need n <= 3")
    parsed: dict[frozenset[int], float] = {}
    for key, val in (raw or {}).items():
        members = frozenset(int(p) for p in str(key).split(",") if p.strip())
        try:
            parsed[members] = float(val)
        except (TypeError, ValueError):
            raise ValueError(f"coalition value for {key!r} is not numeric: {val!r}")
    for s in _all_subsets(n):
        if s not in parsed:
            raise ValueError(f"coalition_values missing subset {sorted(s)}")
    return parsed


def _shapley_from_values(values: dict[frozenset[int], float], n: int) -> dict[int, float]:
    phi = {i: 0.0 for i in range(1, n + 1)}
    for order in permutations(range(1, n + 1)):
        prefix: set[int] = set()
        for i in order:
            before = frozenset(prefix)
            after = frozenset(prefix | {i})
            phi[i] += values[after] - values[before]
            prefix.add(i)
    fact = math.factorial(n)
    return {i: phi[i] / fact for i in phi}
```

- [ ] **Step 4: Run to verify it passes**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_coalition.py -v`
Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/tracks/track_coalition.py tests/tracks/test_coalition.py
git commit -m "feat(R5): track_coalition — coalition-value parse + exact Shapley"
```

---

## Task 3: Tier B — `_tier_b_numeric_core`

**Files:**
- Modify: `src/tracks/track_coalition.py`
- Test: `tests/tracks/test_coalition.py`

**Interfaces:**
- Consumes: `_parse_coalition_values`, `_shapley_from_values` (Task 2).
- Produces: `_tier_b_numeric_core(values: dict[frozenset[int], float], n: int, stated_payments: dict[int, float] | None) -> tuple[bool, bool, list[str]]` — returns `(core_ok, ir_ok, conditions)`. `core_ok`: `sum_{i in S} phi_i >= v(S) - 1e-9` for every non-empty `S`. `ir_ok`: `phi_i >= v({i}) - 1e-9` for every `i`. `conditions`: human-readable check lines. If `stated_payments` is given, an extra condition checks `phi_i ≈ stated_payments[i]` (`abs_tol=1e-6`) and folds into `core_ok`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/tracks/test_coalition.py — append
from tracks.track_coalition import _tier_b_numeric_core


def test_tier_b_convex_game_core_nonempty():
    # convex (supermodular) game -> Shapley value is in the core
    values = {
        frozenset(): 0.0, frozenset({1}): 1.0, frozenset({2}): 1.0,
        frozenset({3}): 1.0, frozenset({1, 2}): 4.0, frozenset({1, 3}): 4.0,
        frozenset({2, 3}): 4.0, frozenset({1, 2, 3}): 10.0,
    }
    core_ok, ir_ok, conds = _tier_b_numeric_core(values, n=3, stated_payments=None)
    assert core_ok and ir_ok
    assert any("core" in c.lower() for c in conds)


def test_tier_b_empty_core_fails():
    # 3-player majority game: v(S)=1 for any |S|>=2, v(N)=1, singletons 0.
    # Shapley = (1/3,1/3,1/3); for S={1,2}: 2/3 < v(S)=1 -> core violated.
    values = {
        frozenset(): 0.0, frozenset({1}): 0.0, frozenset({2}): 0.0,
        frozenset({3}): 0.0, frozenset({1, 2}): 1.0, frozenset({1, 3}): 1.0,
        frozenset({2, 3}): 1.0, frozenset({1, 2, 3}): 1.0,
    }
    core_ok, ir_ok, _ = _tier_b_numeric_core(values, n=3, stated_payments=None)
    assert not core_ok
    assert ir_ok  # phi_i = 1/3 >= v({i}) = 0


def test_tier_b_stated_payment_mismatch_fails_core():
    values = {
        frozenset(): 0.0, frozenset({1}): 1.0, frozenset({2}): 1.0,
        frozenset({1, 2}): 4.0,
    }
    core_ok, _, _ = _tier_b_numeric_core(values, n=2, stated_payments={1: 2.0, 2: 99.0})
    assert not core_ok
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_coalition.py -k tier_b -v`
Expected: FAIL — `_tier_b_numeric_core` not defined.

- [ ] **Step 3: Add the implementation**

```python
# append to src/tracks/track_coalition.py

def _tier_b_numeric_core(
    values: dict[frozenset[int], float],
    n: int,
    stated_payments: dict[int, float] | None,
) -> tuple[bool, bool, list[str]]:
    phi = _shapley_from_values(values, n)
    conds: list[str] = []
    tol = 1e-9

    core_ok = True
    for s in _all_subsets(n):
        if not s:
            continue
        payoff = sum(phi[i] for i in s)
        vs = values[s]
        ok = payoff >= vs - tol
        core_ok &= ok
        conds.append(
            f"core S={sorted(s)}: sum phi={payoff:.6g} >= v(S)={vs:.6g} -> "
            f"{'ok' if ok else 'VIOLATED'}"
        )

    ir_ok = True
    for i in range(1, n + 1):
        vi = values[frozenset({i})]
        ok = phi[i] >= vi - tol
        ir_ok &= ok
        conds.append(
            f"IR i={i}: phi={phi[i]:.6g} >= v({{{i}}})={vi:.6g} -> "
            f"{'ok' if ok else 'VIOLATED'}"
        )

    if stated_payments is not None:
        for i in range(1, n + 1):
            match = math.isclose(phi[i], stated_payments.get(i, float("nan")), abs_tol=1e-6)
            core_ok &= match
            conds.append(
                f"payment i={i}: stated={stated_payments.get(i)} vs Shapley={phi[i]:.6g} -> "
                f"{'match' if match else 'MISMATCH'}"
            )

    return core_ok, ir_ok, conds
```

- [ ] **Step 4: Run to verify it passes**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_coalition.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/tracks/track_coalition.py tests/tracks/test_coalition.py
git commit -m "feat(R5): Tier B — enumerated core / IR / payment check"
```

---

## Task 4: Tier A + `verify_coalition` entry point

**Files:**
- Modify: `src/tracks/track_coalition.py`
- Test: `tests/tracks/test_coalition.py`

**Interfaces:**
- Consumes: `_parse_coalition_values`, `_tier_b_numeric_core` (Tasks 2–3); `sympy`, `sympy.parsing.latex.parse_latex`.
- Produces:
  - `_tier_a_symbolic_identity(shapley_latex: str, n: int) -> tuple[bool, str]` — builds the reference Shapley expression for `n` players over one `sympy.Symbol` per subset, parses `shapley_latex`, returns `(is_shapley, detail)` where `is_shapley` is `sympy.simplify(parsed - reference) == 0` for player `i=1`. On any parse failure or a formula that references a `\binom` / `\hat` / `K`-normalization not in the reference, returns `(False, <reason>)` — fail closed.
  - `verify_coalition(entry: dict) -> VerificationResult` — the public path. Reads `entry["mechanism"]`. Routing:
    1. `shapley_formula_latex` empty/null -> `MANUAL` ("no Shapley formula in the paper").
    2. `coalition_n` absent, not an int, `< 1`, or `> 3` -> `MANUAL` ("k > 3 or coalition size not stated").
    3. Run Tier A. `not is_shapley` -> `MANUAL` ("formula is not the exact Shapley value: <detail>").
    4. `coalition_values` absent -> `MANUAL` ("Tier A passed — formula confirmed Shapley-shaped — but no numeric v(S) in the paper to verify IC/IR/core"). `entry_specific=False`.
    5. Run Tier B. `core_ok and ir_ok` -> `VERIFIED` (`entry_specific=True`, `track=5`, `conditions` = Tier A detail + Tier B conds). Core violated -> `COUNTEREXAMPLE` with the violating `S` in `notes`. IR violated but core ok -> `MANUAL` ("core holds, individual rationality violated").
  - All `MANUAL` returns carry `category="Shapley"`, `track=5`, and a `notes` string naming the obstruction (this string seeds the Task 6 `manual_diagnosis.obstruction`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/tracks/test_coalition.py — append
from tracks.track_coalition import verify_coalition, _tier_a_symbolic_identity

_STD_SHAPLEY_LATEX = (
    r"\phi_i = \sum_{S \subseteq N \setminus \{i\}} "
    r"\frac{|S|!(n-|S|-1)!}{n!} \left( v(S \cup \{i\}) - v(S) \right)"
)


def test_tier_a_accepts_standard_formula():
    ok, _ = _tier_a_symbolic_identity(_STD_SHAPLEY_LATEX, n=3)
    assert ok


def test_tier_a_rejects_binom_normalized_approximation():
    approx = r"\phi_j = K \sum_{S} \frac{U(S \cup \{j\}) - U(S)}{\binom{n-1}{|S|}}"
    ok, detail = _tier_a_symbolic_identity(approx, n=3)
    assert not ok
    assert "binom" in detail.lower() or "not" in detail.lower()


def test_verify_coalition_no_formula_is_manual():
    entry = {"mechanism": {"shapley_formula_latex": None}, "paper_id": "x"}
    r = verify_coalition(entry)
    assert r.verdict == "MANUAL"
    assert "no Shapley formula" in r.notes


def test_verify_coalition_tier_a_only_is_manual():
    entry = {
        "paper_id": "x",
        "mechanism": {"shapley_formula_latex": _STD_SHAPLEY_LATEX, "coalition_n": 3},
    }
    r = verify_coalition(entry)
    assert r.verdict == "MANUAL"
    assert "no numeric v(S)" in r.notes
    assert r.entry_specific is False


def test_verify_coalition_full_pass_is_verified():
    entry = {
        "paper_id": "x",
        "mechanism": {
            "shapley_formula_latex": _STD_SHAPLEY_LATEX,
            "coalition_n": 3,
            "coalition_values": {
                "": 0.0, "1": 1.0, "2": 1.0, "3": 1.0,
                "1,2": 4.0, "1,3": 4.0, "2,3": 4.0, "1,2,3": 10.0,
            },
        },
    }
    r = verify_coalition(entry)
    assert r.verdict == "VERIFIED"
    assert r.entry_specific is True
    assert r.track == 5


def test_verify_coalition_core_violation_is_counterexample():
    entry = {
        "paper_id": "x",
        "mechanism": {
            "shapley_formula_latex": _STD_SHAPLEY_LATEX,
            "coalition_n": 3,
            "coalition_values": {
                "": 0.0, "1": 0.0, "2": 0.0, "3": 0.0,
                "1,2": 1.0, "1,3": 1.0, "2,3": 1.0, "1,2,3": 1.0,
            },
        },
    }
    r = verify_coalition(entry)
    assert r.verdict == "COUNTEREXAMPLE"


def test_verify_coalition_k_over_3_is_manual():
    entry = {
        "paper_id": "x",
        "mechanism": {"shapley_formula_latex": _STD_SHAPLEY_LATEX, "coalition_n": 5},
    }
    r = verify_coalition(entry)
    assert r.verdict == "MANUAL"
    assert "k > 3" in r.notes or "coalition size" in r.notes
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_coalition.py -k "tier_a or verify_coalition" -v`
Expected: FAIL — `_tier_a_symbolic_identity` / `verify_coalition` not defined.

- [ ] **Step 3: Add the implementation**

```python
# append to src/tracks/track_coalition.py
import sympy as sp
from sympy.parsing.latex import parse_latex


def _reference_shapley_symbols(n: int):
    """One sympy Symbol per coalition; the exact Shapley expr for player 1."""
    subset_sym = {s: sp.Symbol(f"v_{'_'.join(map(str, sorted(s))) or 'empty'}")
                  for s in _all_subsets(n)}
    i = 1
    others = [p for p in range(1, n + 1) if p != i]
    expr = sp.Integer(0)
    for k in range(len(others) + 1):
        for c in combinations(others, k):
            s = frozenset(c)
            w = sp.Rational(math.factorial(k) * math.factorial(n - k - 1),
                            math.factorial(n))
            expr += w * (subset_sym[s | {i}] - subset_sym[s])
    return subset_sym, sp.expand(expr)


def _tier_a_symbolic_identity(shapley_latex: str, n: int) -> tuple[bool, str]:
    if not shapley_latex or not str(shapley_latex).strip():
        return False, "empty formula"
    low = str(shapley_latex).lower()
    # Fail-closed structural guards: tokens the exact Shapley value never contains.
    for bad in ("\\binom", "\\hat", "approx", " k \\sum", "k \\sum"):
        if bad in low:
            return False, f"formula contains {bad.strip()!r} — not the exact Shapley value"
    _subset_sym, reference = _reference_shapley_symbols(n)
    try:
        parsed = parse_latex(str(shapley_latex))
    except Exception as e:  # noqa: BLE001 — parse_latex raises broadly
        return False, f"latex parse failed: {e}"
    try:
        diff = sp.simplify(sp.expand(parsed) - reference)
    except Exception as e:  # noqa: BLE001
        return False, f"symbolic comparison failed: {e}"
    if diff == 0:
        return True, "formula matches the exact Shapley value (player 1 identity)"
    return False, f"formula does not reduce to the Shapley value (residual: {diff})"


def _manual(pid: str, note: str, *, entry_specific: bool = False) -> VerificationResult:
    return VerificationResult(
        verdict="MANUAL", category="Shapley", paper_id=pid, track=5,
        notes=note, entry_specific=entry_specific,
    )


def verify_coalition(entry: dict) -> VerificationResult:
    pid = entry.get("paper_id", "<unknown>")
    m = entry.get("mechanism") or {}
    formula = m.get("shapley_formula_latex")

    if not formula or not str(formula).strip():
        return _manual(pid, "no Shapley formula in the paper — cannot verify a "
                            "coalition mechanism without a stated payment rule")

    n = m.get("coalition_n")
    if not isinstance(n, int) or n > _MAX_N or n < 1:
        return _manual(pid, f"k > 3 or coalition size not stated (coalition_n={n!r}) "
                            "— enumeration intractable")

    is_shapley, detail = _tier_a_symbolic_identity(formula, n)
    if not is_shapley:
        return _manual(pid, f"formula is not the exact Shapley value: {detail}")

    raw_values = m.get("coalition_values")
    if not raw_values:
        return _manual(
            pid,
            "Tier A passed — formula confirmed Shapley-shaped — but no numeric "
            "v(S) in the paper to verify IC/IR/core",
        )

    try:
        values = _parse_coalition_values(raw_values, n)
    except ValueError as e:
        return _manual(pid, f"coalition_values unusable: {e}")

    stated = m.get("coalition_payments")  # optional {"1": float, ...}
    stated_payments = ({int(k): float(v) for k, v in stated.items()} if stated else None)

    core_ok, ir_ok, conds = _tier_b_numeric_core(values, n, stated_payments)
    tier_a_line = f"Tier A: {detail}"

    if core_ok and ir_ok:
        return VerificationResult(
            verdict="VERIFIED", category="Shapley", paper_id=pid, track=5,
            conditions=[tier_a_line, *conds], entry_specific=True,
            notes="Tier A (Shapley identity) + Tier B (core, IR) both hold",
        )
    if not core_ok:
        violated = [c for c in conds if "VIOLATED" in c or "MISMATCH" in c]
        return VerificationResult(
            verdict="COUNTEREXAMPLE", category="Shapley", paper_id=pid, track=5,
            conditions=[tier_a_line, *conds], entry_specific=True,
            notes="core / payment violated: " + "; ".join(violated),
        )
    return _manual(pid, "core holds but individual rationality is violated — "
                        "check the paper's participation model")
```

- [ ] **Step 4: Run to verify it passes**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_coalition.py -v`
Expected: all tests PASS. If `test_tier_a_accepts_standard_formula` fails because `parse_latex` cannot handle the `\sum` / `|S|!` factorial notation (it often can't), switch Tier A's positive check to a **structural match**: confirm the raw string contains the marginal term `v(S \cup \{i\}) - v(S)` (modulo whitespace) AND the weight pattern `|S|!(n-|S|-1)!/n!` or `(|S|-1)!(n-|S|)!/n!`, with the `\binom`/`\hat`/`K` guards still rejecting. Record the fallback in a code comment. Do NOT loosen to "contains the word Shapley" or "has a \sum".

- [ ] **Step 5: Commit**

```bash
git add src/tracks/track_coalition.py tests/tracks/test_coalition.py
git commit -m "feat(R5): Tier A symbolic identity + verify_coalition entry point"
```

---

## Task 5: Wire into `verify_shapley` + `ast_verify.py`; corpus data transcription

**Files:**
- Modify: `src/tracks/track1_z3.py` (`verify_shapley`, ~line 2060)
- Modify: `src/architect/ast_verify.py` (`_classify_ast` ~line 54; `Shapley` branch ~line 326)
- Modify: `corpus.json` (`coalition_values` / `coalition_n` / `coalition_values_source` for entries with a PDF instance)
- Test: `tests/tracks/test_coalition.py`; existing `tests/verifier/`, `tests/architect/` (pin updates only where a verdict legitimately moved)

**Interfaces:**
- Consumes: `tracks.track_coalition.verify_coalition` (Task 4).
- Produces: `verify_shapley(entry)` returns `verify_coalition(entry)` when a formula is present, else a `MANUAL` `VerificationResult`. `_classify_ast` returns `5` for `Shapley`. `verify_from_ast` `Shapley` branch calls `verify_coalition({"mechanism": meta, "paper_id": pid})`.

- [ ] **Step 1: Write the failing wiring tests**

```python
# tests/tracks/test_coalition.py — append
def test_verify_shapley_delegates_to_coalition():
    from tracks.track1_z3 import verify_shapley
    entry = {
        "paper_id": "x", "category": "Shapley",
        "mechanism": {"shapley_formula_latex": None},
    }
    r = verify_shapley(entry)
    assert r.verdict == "MANUAL"  # was UNSUPPORTED before R5
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_coalition.py -k delegates -v`
Expected: FAIL — `verify_shapley` returns `UNSUPPORTED`.

- [ ] **Step 3: Edit `verify_shapley` in `src/tracks/track1_z3.py`**

Replace the body of `verify_shapley` (keep `_shapley_check_core` unchanged below it):

```python
def verify_shapley(entry: dict) -> VerificationResult:
    """R5: delegate to the Track 5 coalition verifier when the entry states a
    Shapley payment formula; otherwise MANUAL (was an UNSUPPORTED stub)."""
    from tracks.track_coalition import verify_coalition  # local: avoid import cycle

    m = entry.get("mechanism") or {}
    if m.get("shapley_formula_latex"):
        return verify_coalition(entry)
    pid = entry.get("paper_id", "<unknown>")
    d = entry.get("manual_diagnosis") or {}
    return VerificationResult(
        verdict="MANUAL", category="Shapley", paper_id=pid, track=5,
        notes=(f"MANUAL ({d.get('round', 'R5')}): "
               f"{d.get('obstruction', 'no coalition characteristic function / Shapley formula in the paper')}"),
    )
```

- [ ] **Step 4: Edit `src/architect/ast_verify.py`**

In `_classify_ast`, before the final `return`:

```python
    if m.category == "Shapley":
        return 5
```

Replace the `Shapley` branch in `verify_from_ast` (currently `return _shapley_check_core(paper_id=pid)`):

```python
    if m.category == "Shapley":
        from tracks.track_coalition import verify_coalition
        return verify_coalition({"mechanism": meta, "paper_id": pid})
```

- [ ] **Step 5: Run the wiring test + full existing suites**

```bash
PYTHONPATH=src:. pytest tests/tracks/test_coalition.py tests/verifier/ tests/architect/ -q
```

Expected: PASS. A `tests/verifier/` or `tests/architect/` case that pinned a Shapley verdict to `UNSUPPORTED` may now legitimately read `MANUAL` — update that one pin and note it in the commit body. Any other failure is a real break — fix it, do not repin.

- [ ] **Step 6: Transcribe `coalition_values` where a PDF instance exists**

For each of `2502_08248`, `2605_11889`, `2606_18384`: open the source PDF (`pdfs/<...>.pdf`). Look for a **concrete numeric worked example** of the characteristic function — a capacity network with numbers (`2502_08248`), a numeric log-likelihood table (`2605_11889`), a numeric utility/accuracy table (`2606_18384`). If found, add to that entry's `mechanism` object in `corpus.json` (values below are a **synthetic placeholder shape** — use the paper's actual numbers):

```json
"coalition_n": 3,
"coalition_values": {"": 0.0, "1": 0.3, "2": 0.5, "3": 0.4, "1,2": 0.7, "1,3": 0.6, "2,3": 0.8, "1,2,3": 1.0},
"coalition_values_source": "Sec 5.2 / Fig 3 worked example, p.9 — capacities c=(...)"
```

If **no** concrete instance is in the PDF, add nothing — the entry stays `MANUAL` via Tier A. Record `"no numeric v(S) instance in PDF, checked §X"` in the entry's `notes`.

- [ ] **Step 7: Gate + commit**

```bash
PYTHONPATH=src python -m verifier corpus.json | tail -5   # must run, no API key
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R5-baseline.md --only Shapley corpus.json
```

Expected: `GATE: PASS` (no entry strictly worse; `UNSUPPORTED` -> `MANUAL`/`VERIFIED` allowed).

```bash
git add src/tracks/track1_z3.py src/architect/ast_verify.py corpus.json tests/
git commit -m "feat(R5): wire verify_coalition into verify_shapley + AST path; transcribe coalition_values"
```

---

## Task 6: Targeted sweep, hand-check, MANUAL diagnoses

**Files:**
- Create: `docs/superpowers/notes/round-R5-sweep-raw.md`, `docs/superpowers/notes/round-R5-new-verified.md`
- Modify: `corpus.json` (`verdict_override` + `manual_diagnosis` for non-flips), `docs/superpowers/notes/MANUAL-backlog.md`

**Interfaces:**
- Consumes: `architect.formalize` CLI (`--only`, `--report-dir`), `scripts.round_gate`.
- Produces: `manual_diagnosis` dicts on all non-flip Shapley entries; `round-R5-new-verified.md` (cross-checks); `round-R5-sweep-raw.md` (raw run).

- [ ] **Step 1: Run the LLM formalizer sweep on the Shapley slice**

```bash
ARCHITECT_LLM_TIMEOUT_S=300 PYTHONPATH=src python -m architect.formalize corpus.json \
  --only Shapley --report-dir docs/superpowers/notes 2>&1 | tee docs/superpowers/notes/round-R5-sweep-raw.md
```

Expected (per §R5): the full-AST formalizer likely produces 0 valid ASTs for the Shapley corpus (VCG/Contract/Stackelberg precedent). That is fine — the deterministic `verify_coalition` path decides these. Record whatever it emits.

- [ ] **Step 2: Run the deterministic verifier and read the 4 verdicts**

```bash
PYTHONPATH=src python -m verifier corpus.json 2>/dev/null | grep -A3 -iE "2502_08248|2605_11889|2606_18384|2405_13879"
```

- [ ] **Step 3: Hand-check every entry that flipped to `VERIFIED`**

For each `VERIFIED` Shapley entry: by hand, compute `phi_i` from the transcribed `coalition_values` (marginal-contribution average over the `n!` orderings — for `n=3`, 6 orderings), write out the core inequalities `sum_{i in S} phi_i >= v(S)` for all non-empty `S`, confirm they hold. Append to `docs/superpowers/notes/round-R5-new-verified.md`:

```markdown
## <paper_id> (Shapley) — R5

**What R5 now handles:** Tier A confirmed `shapley_formula_latex` is the exact
Shapley value. Tier B enumerated the transcribed v(S) (n=<n>, source: <section>):
core and IR hold.

**Independent check (hand-derived):**
- phi_1 = <...>, phi_2 = <...>, phi_3 = <...>  (sum = v(N) = <...>, efficiency OK)
- core S={1,2}: <p1+p2> >= v({1,2})=<...> OK
- ... (all non-empty S)
- IR: phi_i >= v({i}) for all i OK
```

If a hand-check does **not** cleanly hold, revert the entry to `MANUAL` (fail closed) and record why. If 0 entries flipped, write the file with just a header line: `_No entries flipped to VERIFIED in R5. Coalition track shipped; all 4 Shapley entries diagnosed MANUAL — see MANUAL-backlog.md._`

- [ ] **Step 4: Write `verdict_override` + `manual_diagnosis` for every non-flip**

For each Shapley entry not `VERIFIED`, add to its `corpus.json` object:

```json
"verdict_override": "MANUAL",
"manual_diagnosis": {
  "round": "R5",
  "track": 5,
  "limit": "<the specific ceiling>",
  "mechanism": "<one line>",
  "obstruction": "<why no automated coalition track decides it>",
  "human_task": "<concrete thing a human must write/read>",
  "date": "2026-09-05"
}
```

Concrete content per entry:

- **`2605_11889`** — `limit`: `"transcendental / opaque characteristic function (Bayesian log-likelihood v(D_C) = log p(T=T*|D_C) - log p(T=T*|∅)); no numeric instance in the paper"`. `obstruction`: `"Tier A confirms the formula is the exact Shapley value, but v(S) is a Bayesian log-likelihood over a model+dataset the paper never instantiates numerically, so Tier B (core/IR) has nothing to enumerate over."` `human_task`: `"instantiate a concrete Bayesian model + validation set and compute v(S) for all S, or prove core/IR analytically from the log-likelihood's supermodularity."`
- **`2606_18384`** — `limit`: `"stated payment is a K-normalized one-round-reconstruction *approximation* of Shapley, not the exact value; value U(M_Sub) is opaque model accuracy"`. `obstruction`: `"Tier A rejects the formula: the 1/binom(|C|-1,|Sub|) weighting and the K factor are not the exact Shapley weights. Even granting the approximation, v(Sub)=U(M_Sub^(R)) is a trained-model accuracy — not symbolically or grid-computable."` `human_task`: `"bound the approximation error |phi_j^OR - phi_j^Shapley| from Algorithm 1, or run the paper's reconstruction to get numeric v(Sub) and verify core/IR empirically."`
- **`2405_13879`** — `limit`: `"mis-categorized: no coalition characteristic function and no Shapley value anywhere in the paper"`. `mechanism`: `"PFL/FACT — a penalty-based free-riding truthfulness mechanism (free-riding penalty P_fr Eq 4, competition penalty P_ct Eq 10), per-agent local/federated loss."` `obstruction`: `"The paper never defines v(S) over agent subsets and never uses the Shapley value; the Shapley category tag is wrong. No coalition track applies."` `human_task`: `"re-categorize this entry as Contract/penalty-mechanism and route it through the R3 Contract path, or confirm it is out-of-scope (no verifiable-tier incentive claim)."`
- **`2502_08248`** — only if it did **not** flip: `limit`: `"no concrete numeric max-flow instance in the paper"`. `obstruction`: `"Tier A confirms the standard Shapley formula, but the paper states v(S)=F(c) abstractly with no numeric capacity network, so Tier B cannot enumerate."` `human_task`: `"transcribe or construct a concrete capacity network from the paper's model, compute F(S) for all S<=3, verify core/IR."`

- [ ] **Step 5: Append one paragraph per MANUAL entry to `MANUAL-backlog.md`**

Follow the existing format in the file: header `## <paper_id> (Shapley) — R5`, then `**Mechanism:**`, `**Obstruction:**`, `**Human task:**`, `**Diagnosed:** 2026-09-05`.

- [ ] **Step 6: Gate + verify UNSUPPORTED cleared + commit**

```bash
PYTHONPATH=src python -m verifier corpus.json | tail -5
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R5-baseline.md --only Shapley corpus.json
PYTHONPATH=src python -m verifier corpus.json 2>/dev/null | grep -iE "2502_08248|2605_11889|2606_18384|2405_13879" | grep -c UNSUPPORTED
```

Expected: `GATE: PASS`; the last command prints `0`.

```bash
git add corpus.json docs/superpowers/notes/round-R5-sweep-raw.md docs/superpowers/notes/round-R5-new-verified.md docs/superpowers/notes/MANUAL-backlog.md
git commit -m "feat(R5): Shapley sweep — <N> VERIFIED + <M> MANUAL diagnoses; UNSUPPORTED 4->0"
```

---

## Task 7: Delta note + spec "Landed" paragraph + merge

**Files:**
- Create: `docs/superpowers/notes/round-R5-delta.md`
- Modify: `docs/superpowers/specs/2026-09-02-zero-unknown-program-design.md` (§R5 "Landed" paragraph; line ~43 / line ~165 `UNSUPPORTED` counts)

**Interfaces:**
- Consumes: `round-R5-baseline.md`, `round-R5-new-verified.md`, the final `verifier` output.
- Produces: `round-R5-delta.md` (mirrors `round-R4-delta.md`: "Landed" header with branch + commits, per-slice before/after table for the Shapley slice, the reclaim narrative, the `UNKNOWN`/`UNSUPPORTED` line).

- [ ] **Step 1: Write `round-R5-delta.md`**

Copy the section shape from `docs/superpowers/notes/round-R4-delta.md`:

```markdown
# Round R5 — Coalition / Shapley Track — Delta

**Landed 2026-09-05.** Branch `round-R5-coalition-track`, <k> commits off `main` @ `<sha>`.
Plan: `docs/superpowers/plans/2026-09-05-R5-coalition-track.md`.

## Shapley slice (4 entries) — before / after

| Verdict | Baseline | After R5 | Δ |
|---|---|---|---|
| VERIFIED (entry-specific) | 0 | <n> | +<n> |
| MANUAL | 0 | <m> | +<m> |
| UNSUPPORTED | 4 | 0 | -4 |

## What shipped
- `src/tracks/track_coalition.py` — Tier A (symbolic Shapley-identity) + Tier B
  (enumerated core / IR / payment, k<=3). Wired into `verify_shapley`,
  `_classify_ast` (-> 5), `verify_from_ast`.
- <flip narrative, or "0 flips — all 4 diagnosed MANUAL">
- MANUAL diagnoses: <per-entry one-liners>

## R6 handoff
- <which Shapley entries R6 could revisit and with what hint>
```

- [ ] **Step 2: Add the "Landed" paragraph to spec §R5**

After the existing §R5 body in the program-design spec, add (mirroring the R2/R3/R4 "Landed" paragraphs):

```markdown
**Landed 2026-09-05:** `src/tracks/track_coalition.py` — a two-tier `verify_coalition`
(Tier A symbolic Shapley-identity check via sympy; Tier B enumerated core/IR/payment
for k<=3), wired into `verify_shapley` (was an `UNSUPPORTED` stub), `_classify_ast`
(Shapley -> track 5), and `verify_from_ast`. <N> new entry-specific `VERIFIED`
(<which, cross-check>), <M> `MANUAL` (catalogued ceilings: transcendental Bayesian
characteristic function, K-normalized OR-approximation not exact Shapley,
mis-categorized penalty mechanism). Shapley `UNSUPPORTED` 4 -> 0. Merge commit
`<sha>`. Delta: `docs/superpowers/notes/round-R5-delta.md`.
```

Update line ~43 (`| UNSUPPORTED | 5 | 4 Shapley + 1 ... |`) and line ~165 (`The 4 Shapley entries stay UNSUPPORTED (R5).`) to reflect the post-R5 state.

- [ ] **Step 3: Whole-branch review + merge**

Invoke `superpowers:requesting-code-review` for the whole branch. Address CRITICAL/HIGH. Then:

```bash
git checkout main && git merge --no-ff round-R5-coalition-track -m "Merge branch 'round-R5-coalition-track' — R5 coalition/Shapley track (<N> VERIFIED, UNSUPPORTED 4->0, track staged for R6)"
```

- [ ] **Step 4: Fill the merge SHA into the spec**

```bash
git rev-parse --short HEAD   # the merge commit
```

Edit the spec's §R5 "Landed" paragraph — replace `<sha>` with the merge commit — and commit:

```bash
git add docs/superpowers/specs/2026-09-02-zero-unknown-program-design.md
git commit -m "docs(R5): fill merge commit SHA in program-spec R5 line"
```

---

## Self-Review

**1. Spec coverage:**
- §R5 "two tiers, Tier A symbolic identity, Tier B numeric core/IR for k<=3" → Tasks 2 (parse + Shapley), 3 (Tier B), 4 (Tier A + entry point).
- §R5 "`verify_shapley` delegates; `_classify_ast` routes Shapley; `verify_from_ast` Coalition branch" → Task 5.
- §R5 "VERIFIED only on Tier B AND Tier A" → Task 4 Step 3 routing rule + Task 6 Step 3 hand-check.
- §R5 "the 4 named entries with expected outcomes" → the entry table + Task 6 Step 4 per-entry diagnoses.
- §R5 "transcribe `coalition_values` from the PDF, declared not inferred" → Task 5 Step 6 (with the "add nothing if no instance" fail-closed rule).
- §R5 "`2405_13879` mis-categorized → MANUAL, human task re-categorize" → Task 6 Step 4 `2405_13879` bullet.
- §"automation ceiling" row 5 ("all coalition mechanisms until R5 builds the track") → the track now exists; `k>3`/opaque → MANUAL (Task 4 routing).
- Cross-round invariants: baseline (Task 1), monotone gate (every task's final step), every-flip-cross-checked (Task 6 Step 3 + `round-R5-new-verified.md`), MANUAL-carries-a-reason (Task 6 Steps 4–5), formalizer-not-a-verify-dependency (Task 5 Step 7 `verify` runs with no API key; `track_coalition.py` has no `architect` import), fail-closed (Task 4 `_manual` default + Task 6 Step 3 revert rule), branch-per-round (Task 1 Step 1, Task 7 Step 3).

**2. Placeholder scan:** The `coalition_values` JSON in Task 5 Step 6 is explicitly labelled "synthetic placeholder shape — use the paper's actual numbers", with the fail-closed "add nothing if no instance" rule stated. Task 6/7 notes carry `<N>` / `<sha>` fill-ins — values only knowable at execution time, each paired with the command that produces it. No "TODO" / "add error handling" / "similar to Task N" — every code step has the actual code.

**3. Type consistency:** `_parse_coalition_values(raw, n) -> dict[frozenset[int], float]` (Task 2) is consumed with that exact signature in Tasks 3 and 4. `_tier_b_numeric_core(values, n, stated_payments) -> (bool, bool, list[str])` (Task 3) is called with that shape in Task 4. `_tier_a_symbolic_identity(shapley_latex, n) -> (bool, str)` (Task 4) — consistent. `verify_coalition(entry: dict) -> VerificationResult` — the single public entry point, called from `verify_shapley` and `verify_from_ast` in Task 5 with a `{"mechanism": ..., "paper_id": ...}` dict, matching what `verify_coalition` reads. `track=5` is used consistently in `_manual`, the `VERIFIED`/`COUNTEREXAMPLE` returns, `_classify_ast`, and every `manual_diagnosis`.

**4. Ambiguity:** "VERIFIED only on both tiers" — Task 4 Step 3 makes the routing explicit (Tier A fail → MANUAL; Tier A pass + no values → MANUAL; both pass → VERIFIED; core fail → COUNTEREXAMPLE; IR-only fail → MANUAL). "concrete numeric instance" for transcription — Task 5 Step 6 names what to look for per paper and says "add nothing" otherwise.
