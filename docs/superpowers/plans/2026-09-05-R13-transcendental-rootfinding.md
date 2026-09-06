# R13 — Transcendental/Implicit Root-Finding Fallback — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Status (2026-09-06):** Executed as part of a same-day full corpus-wide
> sweep once `pdfs/`/`entries/` were confirmed present locally (R11/R12
> had run earlier the same day with neither directory available). See
> `docs/superpowers/notes/round-corpus-sweep-2026-09-06-delta.md` and the
> umbrella spec's "PDF sweep follow-up" note for the complete trace. This
> plan's own 6-entry target list (`2407_02845`, `Han2025paid_models`,
> `Nguyen2025right_reward`, `Chu2023hierarchical`, `Luo2023unbiased`,
> `Pandey2019crowd`) was covered by that sweep alongside the other 87
> `MANUAL` entries; none of R13's specific targets got a new field this
> pass (each stayed diagnosed for a genuine, confirmed reason — see the
> delta doc's Contract/Stackelberg batch notes).

## Handoff from R12 (read before starting)

**Filled in by R12's Task 8 Step 3 (R12 landed 2026-09-06).**

- **`track_nash.py` used `track=6`.** Confirmed — `track_coalition.py`
  already holds `track=5`, so R12's module took the next integer. R13 adds
  no new track, but if it writes any verdict metadata, `track` values 1–6
  are now in use.
- **Post-R12 corpus counts.** Unchanged by R12 (0 flips): in-scope totals
  are `VERIFIED 12`, `MANUAL 93` across 105 in-scope entries. Contract
  slice specifically: `VERIFIED 6`, `MANUAL 32` (38 Contract entries). The
  R13 baseline (Task 1) should re-capture and confirm this, not trust it.
- **Dispatch-wiring lesson — low relevance, as predicted.** R12 wired its
  new track by a `mechanism.action_set`-guarded pre-check at the *top* of
  `verifier._verify_latex` (not a new entry in the `dispatch` dict) and a
  mirror early-return in `ast_verify.verify_from_ast` before
  `_classify_ast`, using a function-local `from tracks.track_nash import …`
  to avoid an import cycle (same pattern as the coalition track). R13
  extends `_sp_to_z3` / adds a SciPy fallback *inside* `track1_z3.py`, so it
  touches no dispatch site — this pattern does not transfer. The one
  transferable note: a function-local import inside the branch is the
  established way to reach a sibling `tracks.*` module without a cycle.
- **No overlap with R13's target list.** R12's Task 2 re-trace
  (`round-R12-root-cause-recheck.md`) reclassified its 10 entries into
  shapes (a) finite-action Nash, (b) peer-prediction BNE
  (`Zhang2020fedserving`), (c) Bayesian persuasion (`2505_05842`),
  (d) continuous-action Nash / single-report truthfulness
  (`Bornstein2023realistic_incentive`, `Huang2024aigc`,
  `Karimireddy2022data_sharing`, `Zhao2023truthful`, `2505_02462`). None of
  these is a transcendental-equation / opaque-log-argument encoding case,
  and none appears in R13's target list (`2407_02845`,
  `Han2025paid_models`, `Nguyen2025right_reward`, `Chu2023hierarchical`,
  `Luo2023unbiased`, + 1). The shape-(d) continuous-FOC entries are
  `MANUAL` for a modelling reason (continuous action / no hidden type), not
  a solver-encoding limit R13 removes. Task 1's confirmation step can treat
  the R13 target list as unaffected by R12.

**This is the last round in this program.** R13's own Task 8 does not hand
off to a further plan — it writes the umbrella spec's final "Landed"
paragraph for all three rounds and closes the program (or names what's
left as a future round, per the umbrella spec's own honest-uncertainty
framing).

**Goal:** Add a Z3-encoding path for Contract entries whose opaque or
sign-ambiguous log/exp/unknown-function terms currently make `_sp_to_z3`
raise, and a SciPy root-finding fallback (reusing R11's
`_numeric_solve_stationarity` pattern) for Stackelberg entries whose
follower FOC is transcendental/implicit with no closed-form root.

**Architecture — two genuinely different sub-problems, confirmed against
the actual code at plan time (both parts of the umbrella spec's original
assumption hold here, unlike R11):**

1. **Contract (`2407_02845`, `Han2025paid_models`, `Nguyen2025right_reward`):**
   `_sp_to_z3` (`src/tracks/track1_z3.py:267-328`) already treats `log`/`exp`
   as opaque Z3 auxiliary reals when a term's sign is established
   (`_is_definitely_positive_sum`, confirmed present at line 289) — this is
   not a numeric-optimization problem, it's an **encoding-admissibility**
   problem. `2407_02845` fails because the log argument's sign genuinely
   isn't provable from the declared positivity domain (R11's
   `_positivity_domain` reader may already fix this if the missing fact is
   simply untranscribed — check first, in Task 2, before writing new code).
   `Han2025paid_models`/`Nguyen2025right_reward` fail at the final
   `raise ValueError(f"unsupported SymPy node...")` (line 328) because `v`/`h`
   are opaque `Function` nodes Z3 has never seen — R4's `_opaque_inline`
   reader (in `_contract_check_core`, confirmed wired) already handles this
   *if* the entry supplies `opaque_function_forms`; if the paper genuinely
   never gives a closed form, this is a real ceiling no solver widening can
   close (Z3 cannot reason about a function it's never told the shape of),
   and R13's actual code contribution for Contract is narrower: extending
   `_sp_to_z3` to treat a **declared-monotone** opaque function symbol as an
   auxiliary Z3 real *with a stated monotonicity fact* (e.g. "v is
   increasing in its argument") when the IC/IR proof only needs the sign of
   a difference, not the function's exact value — this is a genuine new
   capability, not a re-application of R4's tools.

2. **Stackelberg (`Chu2023hierarchical`, `Luo2023unbiased`,
   `Pandey2019crowd`):** the follower's FOC itself (not a joint vector
   system — these are scalar, single-variable cases) is transcendental or
   implicit (`log`, an implicit cubic, a min-clip) with no closed-form root.
   This is the same numeric-root-finding shape as R11's rational/log joint
   systems, but on the **scalar** FOC path (`_stackelberg_check_core`'s
   non-vector branch, `track1_z3.py:1829-1838`, `critical_points =
   _sp.solve(foc, e_sym)`) rather than the vector path. R13 extends this
   scalar branch with the same `_numeric_solve_stationarity`-style fallback
   R11 built, adapted to a single equation — **reuse R11's helper directly**
   (generalize it to accept 1 equation as a special case) rather than
   duplicating the fail-closed start-point-agreement logic.

**Tech Stack:** Python 3.14, SymPy (existing), Z3 (existing), SciPy
(`scipy.optimize.brentq` for the scalar bracketed-root case — preferred
over `fsolve` for a single equation with a knowable sign-change bracket;
falls back to `fsolve` if no bracket can be established) — reuses R11's
already-added SciPy usage, no new dependency decision needed.

**Spec:** `docs/superpowers/specs/2026-09-05-R11-R13-solver-capability-expansion-design.md`
(§R13).

## Global Constraints

- **Monotone corpus gate.** After every task, `PYTHONPATH=src python -m
  scripts.round_gate --baseline docs/superpowers/notes/round-R13-baseline.md
  --only Contract corpus.json` and `--only Stackelberg corpus.json` must
  print `GATE: PASS`.
- **Per-round baseline.** Task 1 captures `round-R13-baseline.md`.
- **Every flip cross-checked.** Recorded in
  `docs/superpowers/notes/round-R13-new-verified.md` — for a numeric root,
  a residual check at the reported root done independently (not re-calling
  the same solver code) plus the Hessian/second-derivative sign; for a
  monotone-opaque-function flip, a hand-derived sign argument showing the
  IC/IR proof only needed the monotonicity fact, not the function's value.
- **`MANUAL` always carries a reason.** Every non-flip among the 6 targeted
  entries gets `manual_diagnosis.round` bumped to `"R13"` with the specific
  reason (no closed-form root even numerically bracketable, no monotonicity
  stated in the paper, etc.).
- **Formalizer is never a verify-time dependency.** No `architect.*` import
  in any touched Track file; SciPy runs local and deterministic.
- **Fail closed.** No bracket found for `brentq`, `fsolve` non-convergence,
  a monotonicity claim not explicitly stated+cited in the paper, or any
  ambiguity — stays `MANUAL`.
- **No branch for this round** (program-level deviation).
- **This is the program's last round** — Task 8 writes the umbrella spec's
  final summary across R11+R12+R13 instead of handing off to a further
  plan.

---

## File Structure

**Solver code:**
- `src/tracks/track1_z3.py` — extend `_sp_to_z3` (line 267) with a
  `monotone_functions: dict[str, str]` parameter (default `{}`) that, for a
  `_sp.Function` call node whose name is a key in `monotone_functions` with
  value `"increasing"` or `"decreasing"`, returns an opaque Z3 auxiliary
  real tagged with that monotonicity — used only where the IC/IR proof's Z3
  query is itself monotonicity-based (see Task 3 for the exact guard);
  extend `_stackelberg_check_core`'s scalar branch (`track1_z3.py:1829`,
  `critical_points = _sp.solve(foc, e_sym)`) with a numeric fallback when
  `critical_points` is empty, reusing a generalized
  `_numeric_solve_stationarity` from R11 (now imported/called with a
  1-element `decision_syms` list — confirm R11's function signature
  supports this without modification before generalizing it further).

**Corpus data:**
- `corpus.json` — Task 2: `positivity_domain` additions for `2407_02845` if
  the fix is purely a missing R4-era fact (checked first, before new code);
  Task 4: `opaque_function_monotonicity` (new field,
  `{"v": "increasing"}`-shaped) for `Han2025paid_models` /
  `Nguyen2025right_reward` if the paper states monotonicity without a
  closed form; Task 6: `fixed_constants` for the 3 Stackelberg entries if
  the numeric root-finder needs parameters pinned.

**Notes:**
- `docs/superpowers/notes/round-R13-baseline.md` (Task 1)
- `docs/superpowers/notes/round-R13-new-verified.md` (Task 7)
- `docs/superpowers/notes/round-R13-delta.md` (Task 8)
- `docs/superpowers/notes/MANUAL-backlog.md` (appended)

**Tests:**
- `tests/tracks/test_sp_to_z3_monotone.py` (Task 3, new)
- `tests/tracks/test_stackelberg_scalar_numeric.py` (Task 5, new)

---

## Task 1: Baseline snapshot + confirm the 6 target entries are unchanged by R11/R12

**Files:**
- Create: `docs/superpowers/notes/round-R13-baseline.md`

- [ ] **Step 1: Capture the baseline**

```bash
PYTHONPATH=src python -m scripts.snapshot_verdicts corpus.json --out docs/superpowers/notes/round-R13-baseline.md
```

- [ ] **Step 2: Confirm the 6 target entries' current state**

```bash
PYTHONPATH=src python3 -c "
import json
d = json.load(open('corpus.json'))
entries = d if isinstance(d, list) else d.get('entries', d)
by_id = {e.get('paper_id'): e for e in entries}
for t in ['2407_02845','Han2025paid_models','Nguyen2025right_reward','Chu2023hierarchical','Luo2023unbiased','Pandey2019crowd']:
    e = by_id.get(t)
    print(t, '|', e.get('category') if e else 'NOT FOUND', '|', e.get('verdict_override') if e else '')
"
```

Expected (per plan-time check): all 6 still `MANUAL` (Contract: `2407_02845`,
`Han2025paid_models`, `Nguyen2025right_reward`; Stackelberg:
`Chu2023hierarchical`, `Luo2023unbiased`, `Pandey2019crowd`). If R11 or R12
already reclaimed any of these (cross-check against the R12 handoff note
above, which was asked to flag overlap), update this plan's target list
before proceeding — do not attempt an entry that's already `VERIFIED`.

- [ ] **Step 3: Gate no-op + commit**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R13-baseline.md --only Contract corpus.json
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R13-baseline.md --only Stackelberg corpus.json
git add docs/superpowers/notes/round-R13-baseline.md
git commit -m "chore(R13): baseline snapshot"
```

---

## Task 2: Check whether `2407_02845` is simply a missing `positivity_domain` fact (R4/R11 tooling, no new code)

**Files:**
- Modify: `corpus.json` — `positivity_domain` for `2407_02845` if the PDF
  supports it.

**Interfaces:**
- Consumes: `_positivity_domain` (R4), `_is_definitely_positive_sum`
  (existing, `track1_z3.py`).

- [ ] **Step 1: Read `2407_02845`'s stored diagnosis and the log term**

```bash
PYTHONPATH=src python3 -c "
import json
d = json.load(open('corpus.json'))
entries = d if isinstance(d, list) else d.get('entries', d)
e = next(x for x in entries if x.get('paper_id') == '2407_02845')
print(json.dumps(e.get('manual_diagnosis', {}), indent=2))
print('positivity_domain already present:', 'positivity_domain' in e.get('mechanism', {}))
"
```

- [ ] **Step 2: If no `positivity_domain` is present, check the PDF for the missing positivity fact**

If the paper states the log argument's underlying quantity is positive
(e.g. a channel gain, a probability, a rate) and this simply wasn't
transcribed in R4, add it:

```json
"positivity_domain": ["<symbol> > 0"],
"positivity_domain_source": "2407_02845, Sec. X: <symbol> is a <physical quantity>, positive by definition"
```

- [ ] **Step 3: Re-run the verifier and check if this alone flips the entry**

```bash
PYTHONPATH=src python -m verifier corpus.json 2>/dev/null | grep -A3 2407_02845
```

If it flips to `VERIFIED`, this is a genuine reclaim via existing R4
tooling — hand-check it in Task 7 alongside the new-code flips, and skip
Task 3's monotone-function work for this entry (it's Contract, but the real
fix was a missing fact, not a Z3-encoding gap — note this distinction in
the delta doc). If it does NOT flip (the sign genuinely cannot be
established even with this fact — e.g. the argument is `x - 1` and `x`'s
positivity alone doesn't prove `x - 1 > 0`), the log-argument sign is a
genuine algebraic gap, not a missing corpus field — leave it `MANUAL` with
that refined diagnosis in Task 7, and do not attempt Task 3's monotone
mechanism for this entry (it is a sign-provability problem, not an
opaque-function problem — a different shape than `Han2025`/`Nguyen2025`).

- [ ] **Step 4: Gate + commit**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R13-baseline.md --only Contract corpus.json
PYTHONPATH=src:. pytest -q
git add corpus.json
git commit -m "feat(R13): check 2407_02845 against existing positivity-domain tooling before new code"
```

---

## Task 3: `_sp_to_z3` monotone-opaque-function extension (code, TDD)

**Files:**
- Modify: `src/tracks/track1_z3.py:267-328` (`_sp_to_z3`)
- Test: `tests/tracks/test_sp_to_z3_monotone.py` (create)

**Interfaces:**
- Consumes: the existing `_sp_to_z3(expr, cache) -> Any` signature.
- Produces: `_sp_to_z3(expr, cache, monotone_functions: dict | None = None)`
  — new optional third parameter, default `None` (preserves every existing
  call site unchanged). For an `_sp.Function` call node `f(arg)` where
  `str(f.func)` is a key in `monotone_functions`, returns a fresh opaque Z3
  auxiliary real (same pattern as the existing `log`/`exp` handling) — the
  monotonicity fact itself is not encoded as a Z3 constraint here (Z3 has
  no way to state "this opaque real increases with an unconstrained
  argument" usefully); instead, the **caller** (`_contract_check_core`) is
  responsible for only invoking this path when the specific IC/IR proof
  being checked is a **difference-of-the-same-function-at-two-points**
  whose sign follows from monotonicity alone (see Step 4) — `_sp_to_z3`
  itself only removes the "unsupported node" bail; it does not (and cannot)
  smuggle in unsound reasoning about the function's actual behavior.

- [ ] **Step 1: Write the failing test**

```python
# tests/tracks/test_sp_to_z3_monotone.py
import sympy as sp
import pytest
from tracks.track1_z3 import _sp_to_z3

def test_unrecognized_function_still_raises_without_monotone_functions():
    v = sp.Function("v")
    x = sp.Symbol("x", positive=True)
    with pytest.raises(ValueError, match="unsupported SymPy node"):
        _sp_to_z3(v(x), {})


def test_declared_monotone_function_becomes_opaque_real():
    v = sp.Function("v")
    x = sp.Symbol("x", positive=True)
    z3_expr = _sp_to_z3(v(x), {}, monotone_functions={"v": "increasing"})
    # It's some Z3 real expression -- not a Python exception, and distinct
    # calls with syntactically different args get distinct auxiliary vars.
    z3_expr2 = _sp_to_z3(v(x + 1), {}, monotone_functions={"v": "increasing"})
    assert str(z3_expr) != str(z3_expr2)
```

- [ ] **Step 2: Run, verify fail**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_sp_to_z3_monotone.py -v`
Expected: FAIL — `_sp_to_z3` doesn't accept a third argument yet, and
currently raises on any `Function` node regardless.

- [ ] **Step 3: Implement**

Add a branch before the final `raise` at line 328, and thread the new
parameter through the two recursive call sites that matter
(`_sp.Add`/`_sp.Mul` already pass `cache` recursively — extend those calls
to also pass `monotone_functions`):

```python
def _sp_to_z3(expr: Any, cache: dict, monotone_functions: "dict | None" = None) -> Any:
    """... (existing docstring, append:)

    monotone_functions: optional {func_name: "increasing"|"decreasing"} --
    an opaque Function node whose name is a key here becomes a fresh Z3
    auxiliary real (same treatment as log/exp), IF AND ONLY IF the caller
    has already confirmed the specific IC/IR check being run only needs
    the function's monotonicity, not its value (see _contract_check_core's
    guard). This function does not encode the monotonicity fact itself --
    it only stops the earlier "unsupported node" bail so the caller's own
    sign-of-a-difference reasoning can proceed.
    """
    monotone_functions = monotone_functions or {}
    if isinstance(expr, _sp.exp):
        ...  # unchanged
    if isinstance(expr, _sp.log):
        ...  # unchanged
    ...  # unchanged Integer/Float/Symbol/Add/Mul/Pow branches, but Add/Mul
         # recursive calls become:
         # parts = [_sp_to_z3(a, cache, monotone_functions) for a in expr.args]
    if isinstance(expr, _sp.Function) and str(expr.func) in monotone_functions:
        key = f"{expr.func}[{expr.args[0]}]"
        if key not in cache:
            cache[key] = Real(f"opaquefn{len(cache)}")
        return cache[key]
    raise ValueError(f"unsupported SymPy node {type(expr).__name__}")
```

Update the `_sp.Add` and `_sp.Mul` branches' recursive calls to pass
`monotone_functions` through (currently `_sp_to_z3(a, cache)` — becomes
`_sp_to_z3(a, cache, monotone_functions)`).

- [ ] **Step 4: Wire the guard in `_contract_check_core` — only for a difference-of-same-function-at-two-points shape**

In `_contract_check_core`, before calling `_sp_to_z3` on the IC/IR
expressions, check whether the expression's only unrecognized `Function`
occurrences are of the exact shape `f(a) - f(b)` (or `f(a) >= f(b)`) for the
**same** function `f` — this is the only shape where monotonicity alone
(without a closed form) proves a sign. Add:

```python
def _monotone_difference_functions(expr: Any, declared: dict) -> dict:
    """Return the subset of `declared` (mechanism.opaque_function_monotonicity)
    that actually appears in `expr` ONLY as a same-function difference/comparison
    -- i.e. every occurrence of f is paired with another occurrence of f at a
    different argument, never f alone combined with unrelated terms in a way
    that would need its actual value. Conservative: returns {} (no function
    is monotone-usable) unless this shape is confirmed structurally.
    """
    usable = {}
    for fname in declared:
        calls = [a for a in expr.atoms(_sp.Function) if str(a.func) == fname]
        if len(calls) < 2:
            continue  # a single occurrence needs a value, not just monotonicity
        # Structural check: expr, with every call to f replaced by a fresh
        # placeholder symbol per distinct argument, must remain expressible
        # as a linear combination of those placeholders (i.e. f only ever
        # appears bare, added/subtracted -- never inside another function,
        # multiplied by a non-constant, etc., which WOULD need its value).
        distinct_args = {c.args for c in calls}
        placeholders = {a: _sp.Symbol(f"__mono_{fname}_{i}") for i, a in enumerate(distinct_args)}
        substituted = expr
        for c in calls:
            substituted = substituted.subs(c, placeholders[c.args])
        if not substituted.is_polynomial(*placeholders.values()) or \
           _sp.degree(_sp.Poly(substituted, *placeholders.values())) > 1:
            continue  # f's value matters beyond a linear appearance -- unsafe
        usable[fname] = declared[fname]
    return usable
```

Call this before the `_sp_to_z3` invocation, passing only the confirmed-safe
subset:

```python
    declared_mono = (meta or {}).get("opaque_function_monotonicity") or {}
    safe_mono = _monotone_difference_functions(U_ir, declared_mono) if declared_mono else {}
    # ... pass safe_mono as _sp_to_z3(..., monotone_functions=safe_mono)
```

- [ ] **Step 5: Run new + existing Contract suites**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_sp_to_z3_monotone.py tests/tracks/test_contract_parse_gaps.py tests/tracks/test_opaque_inline.py tests/tracks/test_positivity_domain.py -q`
Expected: all PASS. No existing entry has `opaque_function_monotonicity`,
so no verdict moves yet.

- [ ] **Step 6: Verifier no-key + full suite + commit**

```bash
env -u NVIDIA_API_KEY -u ANTHROPIC_API_KEY -u OPENAI_API_KEY PYTHONPATH=src python -m verifier corpus.json | tail -5
PYTHONPATH=src:. pytest -q
```

```bash
git add src/tracks/track1_z3.py tests/tracks/test_sp_to_z3_monotone.py
git commit -m "feat(R13): _sp_to_z3 monotone-opaque-function extension, gated by a same-function-difference structural check"
```

---

## Task 4: Transcribe `opaque_function_monotonicity` for `Han2025paid_models` / `Nguyen2025right_reward`

**Files:**
- Modify: `corpus.json`

**Interfaces:**
- Consumes: `_monotone_difference_functions` + the `_sp_to_z3` extension
  (Task 3).

- [ ] **Step 1: Check each entry's IC/IR expression shape**

Confirm the opaque function (`v` in `Han2025paid_models`, `h` in
`Nguyen2025right_reward`) actually appears as a same-function difference in
the IC/IR gap (not, e.g., multiplied by another type-dependent term) — if
it doesn't have this shape, Task 3's structural guard will correctly reject
it and no field should be added (the entry stays `MANUAL` via the existing
opaque-function ceiling, unchanged from its R4/R9 diagnosis).

- [ ] **Step 2: Read the PDF for an explicit monotonicity statement + cite**

Only add the field if the paper explicitly states the function is
monotone (e.g. "buyer valuation `v(r)` is increasing in reported quality
`r`") with a citable location:

```json
"opaque_function_monotonicity": {"v": "increasing"},
"opaque_function_monotonicity_source": "Han2025paid_models, Sec. III: 'v(r) is strictly increasing in r' (Assumption 2)"
```

If the paper does not state monotonicity (only gives the function's name
with no property), leave the entry untouched — it stays `MANUAL`.

- [ ] **Step 3: Gate + suite + commit**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R13-baseline.md --only Contract corpus.json
PYTHONPATH=src:. pytest -q
git add corpus.json
git commit -m "feat(R13): transcribe opaque_function_monotonicity for Contract entries (from PDFs)"
```

---

## Task 5: Scalar numeric-root fallback in `_stackelberg_check_core` (code, TDD, reuses R11's helper)

**Files:**
- Modify: `src/tracks/track1_z3.py:1829-1838` (the scalar FOC branch of
  `_stackelberg_check_core`)
- Test: `tests/tracks/test_stackelberg_scalar_numeric.py` (create)

**Interfaces:**
- Consumes: R11's `_numeric_solve_stationarity(eqs, decision_syms) ->
  tuple[dict, str] | None` — confirm at plan/execution time it already
  accepts a 1-element `decision_syms` list without modification (its
  implementation iterates generically over `decision_syms`, so it should;
  verify with a quick manual check before assuming).
- Produces: when `_sp.solve(foc, e_sym)` returns an empty list (the
  existing `if not critical_points: return None` guard at line 1837), try
  the numeric fallback before giving up: wrap `foc` as a single-equation
  list (`[_sp.Eq(foc, 0)]`) and call `_numeric_solve_stationarity(eqs,
  [e_sym])`. On success, the resulting root is treated exactly like an
  exact critical point would be by the existing downstream code (second-
  order check, best-response cross-check, IR) — **no new downstream logic,
  only a new way to produce a candidate `critical_points` entry**.

- [ ] **Step 1: Write the failing test**

```python
# tests/tracks/test_stackelberg_scalar_numeric.py
import sympy as sp
from tracks.track1_z3 import _stackelberg_check_core

def test_transcendental_foc_falls_back_to_numeric_root():
    e, a = sp.symbols("e a", positive=True)
    # U = log(1+e) - e**2/10 - e/3 -- this FOC has no closed-form root
    # SymPy solves exactly (transcendental + polynomial mixed); confirmed
    # at Step 3 before relying on this in the implementation step.
    U = sp.log(1 + e) - e**2 / sp.Integer(10) - e / sp.Integer(3)
    mech = {}
    res = _stackelberg_check_core(
        U, follower_decision=e, meta=mech, entry_specific=True, paper_id="synthetic",
    )
    # This test targets only the numeric fallback's REACHABILITY, not a
    # guaranteed VERIFIED verdict -- the downstream IR/best-response checks
    # are unrelated to R13's actual change. Tighten this assertion at
    # Step 5 once the real numeric outcome for this specific U is known.
    assert res is None or res.verdict == "VERIFIED"
```

Note: this test's exact assertion is deliberately loose ("reachability, not
a guaranteed VERIFIED") because the full downstream Hessian/IR checks are
unrelated to R13's actual change; Step 5 below tightens it to a concrete
assertion once the real numeric behavior is confirmed.

- [ ] **Step 2: Run, verify fail or loosely pass (confirm which)**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_stackelberg_scalar_numeric.py -v`
Expected: today `not critical_points` returns `None` unconditionally with
no fallback attempt — if this `U`'s FOC has no exact SymPy solution
(confirm in Step 3), the loose assertion (`res is None or ...`) will
actually PASS trivially today, which is a weak/uninformative test until
Step 4's implementation exists. Do not treat a trivial pass here as "done"
— proceed to Step 3/4 regardless.

- [ ] **Step 3: Confirm `_sp.solve(foc, e)` is actually empty for the test's `U` before proceeding**

```bash
PYTHONPATH=src:. python3 -c "
import sympy as sp
e = sp.Symbol('e', positive=True)
U = sp.log(1+e) - e**2/sp.Integer(10) - e/sp.Integer(3)
foc = sp.diff(U, e)
print('FOC:', foc)
print('solve:', sp.solve(foc, e))
"
```

If `solve` unexpectedly returns a closed form, pick a harder `U` (e.g. add
another transcendental term, such as `+ sp.exp(-e)`) until the exact solve
genuinely fails — the test must exercise the numeric path, not accidentally
validate the existing exact path. Update the test file's `U` to match
whatever expression is confirmed to force the numeric branch.

- [ ] **Step 4: Implement the fallback**

At `track1_z3.py:1829-1838`, change:

```python
    try:
        foc = _sp.diff(util_expr, e_sym)
        if foc.has(_sp.Derivative):
            return None  # chain rule stalled on an unresolved function
        critical_points = _sp.solve(foc, e_sym)
    except Exception:
        return None

    if not critical_points:
        return None
```

to:

```python
    try:
        foc = _sp.diff(util_expr, e_sym)
        if foc.has(_sp.Derivative):
            return None  # chain rule stalled on an unresolved function
        critical_points = _sp.solve(foc, e_sym)
    except Exception:
        critical_points = []

    if not critical_points:
        numeric = _numeric_solve_stationarity([_sp.Eq(foc, 0)], [e_sym])
        if numeric is None:
            return None
        sol_map, _method = numeric
        critical_points = [sol_map[e_sym]]
```

(`_numeric_solve_stationarity` is defined earlier in this same module by
R11's Task 2 — no import needed, it's already module-local.)

- [ ] **Step 5: Tighten the test from Step 1 now that the real behavior is known**

Re-run the confirmation script from Step 3, this time also manually running
`_numeric_solve_stationarity([_sp.Eq(foc, 0)], [e])` (with `e` matching the
symbol used) to see the actual root found (if any), then update the test
to assert the concrete, real outcome (either a specific `VERIFIED` with the
exact numeric root, or a specific `None` if the fallback itself fails
closed for this particular `U`).

**Check this scalar-vs-vector edge case explicitly:** R11's
`_numeric_solve_stationarity` requires >=2 of 3 fixed start points to
converge to the *same* point within `1e-6` before accepting a root. For a
single well-behaved scalar equation, all 3 start points (`0.1`, `1.0`,
`10.0`) converging to the same root is the normal, expected case — so this
check should not be over-strict for 1D. If, in practice, it turns out a
genuinely correct scalar root gets rejected because the fixed start points
happen to bracket a discontinuity or a second root, note that finding here
and consider whether the scalar case needs its own `brentq`-based bracket
search instead of reusing `fsolve`'s multi-start check verbatim — if so,
add a scalar-specific helper rather than loosening R11's vector-case
fail-closed logic (do not weaken R11's existing test guarantees to
accommodate this).

- [ ] **Step 6: Run new + existing Stackelberg suites**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_stackelberg_scalar_numeric.py tests/tracks/test_stackelberg_vector_numeric.py tests/tracks/test_stackelberg_vector.py -q`
Expected: all PASS, including R11's existing tests (unaffected — this task
only touches the scalar, non-tuple `follower_decision` branch).

- [ ] **Step 7: Verifier no-key + full suite + commit**

```bash
env -u NVIDIA_API_KEY -u ANTHROPIC_API_KEY -u OPENAI_API_KEY PYTHONPATH=src python -m verifier corpus.json | tail -5
PYTHONPATH=src:. pytest -q
```

```bash
git add src/tracks/track1_z3.py tests/tracks/test_stackelberg_scalar_numeric.py
git commit -m "feat(R13): scalar numeric-root fallback for transcendental/implicit follower FOC, reusing R11's numeric solver"
```

---

## Task 6: Fixed constants for the 3 Stackelberg entries, if needed

**Files:**
- Modify: `corpus.json` — `fixed_constants` for `Chu2023hierarchical`,
  `Luo2023unbiased`, `Pandey2019crowd` if their FOC has free parameter
  symbols beyond the follower's own decision variable.

- [ ] **Step 1: Check each entry's FOC for free parameter symbols**

Same investigation style as R11 Task 6 — identify every symbol in the FOC
that is not the decision variable, and determine whether it's a leader
variable (already numeric by the time this check runs) or a true paper
constant needing `fixed_constants`.

- [ ] **Step 2: Add only genuine paper-declared constants; leave absent otherwise**

```json
"fixed_constants": {"<param>": <value>},
"fixed_constants_source": "<paper>, Sec. X numerical setup"
```

- [ ] **Step 3: Gate + suite + commit**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R13-baseline.md --only Stackelberg corpus.json
PYTHONPATH=src:. pytest -q
git add corpus.json
git commit -m "feat(R13): transcribe fixed_constants for transcendental-FOC Stackelberg entries (from PDFs)"
```

---

## Task 7: Sweep, hand-check every flip, refresh every non-flip diagnosis

**Files:**
- Create: `docs/superpowers/notes/round-R13-new-verified.md`
- Modify: `corpus.json`, `docs/superpowers/notes/MANUAL-backlog.md`

- [ ] **Step 1: Run the verifier, read all 6 targeted entries' verdicts**

```bash
PYTHONPATH=src python -m verifier corpus.json 2>/dev/null | grep -A3 -iE "2407_02845|Han2025paid_models|Nguyen2025right_reward|Chu2023hierarchical|Luo2023unbiased|Pandey2019crowd"
```

- [ ] **Step 2: Hand-check every flip**

For a monotone-opaque-function Contract flip: hand-derive the sign
argument — show that the IC/IR gap reduces to `f(a) - f(b)` for `a`
compared against `b` in the direction the monotonicity fact fixes, cite the
paper's own monotonicity assumption. For a numeric Stackelberg flip:
independently re-evaluate the FOC residual at the reported root (fresh
script, not reusing `_numeric_solve_stationarity`) and independently check
the second-order condition. Append to `round-R13-new-verified.md` in the
same format as R11/R12's delta notes.

- [ ] **Step 3: Refresh `manual_diagnosis` for every non-flip**

Same discipline as R11 Task 7 Step 3 — `round: "R13"`, corrected
`obstruction`/`human_task` reflecting exactly what R13 tried and why it
still fails (e.g. "monotonicity not stated in the paper", "no bracket for
`brentq`, `fsolve` did not converge to a consistent root").

- [ ] **Step 4: Append MANUAL-backlog.md paragraphs; gate + suite + commit**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R13-baseline.md --only Contract corpus.json
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R13-baseline.md --only Stackelberg corpus.json
PYTHONPATH=src:. pytest -q
git add corpus.json docs/superpowers/notes/round-R13-new-verified.md docs/superpowers/notes/MANUAL-backlog.md
git commit -m "feat(R13): sweep + hand-check flips + refresh diagnoses for 6 transcendental-cluster entries"
```

---

## Task 8: Delta doc + program-closing spec update (no further handoff — last round)

**Files:**
- Create: `docs/superpowers/notes/round-R13-delta.md`
- Modify: `docs/superpowers/specs/2026-09-05-R11-R13-solver-capability-expansion-design.md`

- [ ] **Step 1: Write `round-R13-delta.md`**

Same shape as R11/R12's delta docs — before/after table for the 6 targeted
entries, what shipped, flips with cross-checks, refreshed diagnoses.

- [ ] **Step 2: Write the umbrella spec's final program-summary paragraph**

Add a closing `## Program summary (post-R13)` section to
`docs/superpowers/specs/2026-09-05-R11-R13-solver-capability-expansion-design.md`
with:

- Total entries targeted across R11+R12+R13 (11 + up to 10 + 6 = up to 27)
  vs. total actually reclaimed (sum of the three rounds' real flip counts).
- The corrected-scope finding from R11 (Stackelberg vector-decision already
  existed; the real new capability was the numeric fallback) as the
  program's single most important process lesson — future rounds should
  re-verify a spec's assumption about what already exists in the codebase
  before planning against it, exactly as this program's own umbrella spec
  now recommends implicitly via this finding.
- Post-R13 corpus counts: `VERIFIED`, `MANUAL` totals across the whole
  105-entry in-scope corpus (not just this program's targeted 27), so the
  program's actual contribution to the top-line count is visible against
  the R9-era 12/105 starting point this program was launched to address.
- Whether any residual capability gap remains worth a future round (e.g.
  if R13's monotone-opaque-function mechanism generalizes beyond the 2
  entries it targeted, or if R12's shape-(b)/(c) peer-prediction/Bayesian-
  persuasion entries are large enough in number to warrant their own
  future round) — name it explicitly rather than silently letting the
  program just stop, per the umbrella spec's own risk-note discipline.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/notes/round-R13-delta.md \
        docs/superpowers/specs/2026-09-05-R11-R13-solver-capability-expansion-design.md
git commit -m "docs(R13): delta note + program-closing summary for R11-R13"
```

---

## Self-Review

**1. Spec coverage:** §R13 "transcendental/implicit root-finding fallback,
~8-10 target entries" — corrected to the 6 entries R9's own cluster doc
actually names (`2407_02845`, `Han2025paid_models`, `Nguyen2025right_reward`,
`Chu2023hierarchical`, `Luo2023unbiased`, `Pandey2019crowd`) — the spec's
"8-10" was an estimate range, and this plan uses the real R9-catalogued
count rather than padding to match the estimate. The two genuinely
different sub-problems (Contract encoding-admissibility vs. Stackelberg
root-finding) are both covered, each with its own TDD task (Tasks 3-4 vs.
Tasks 5-6). The "reuse R11's numeric backend" instruction from the umbrella
spec is honored literally (Task 5 imports/calls R11's function directly,
does not reimplement it).

**2. Placeholder scan:** every code step has complete code. Task 5's test
is explicitly flagged as intentionally loose at first (Step 1) with a
concrete, mandatory tightening step (Step 5) once real behavior is known —
this is not a permanent placeholder, it is a stated two-phase TDD process
appropriate for exploratory numeric behavior, with an explicit instruction
not to leave the loose version as final.

**3. Type consistency:** `_sp_to_z3(expr, cache, monotone_functions=None)`
— the new parameter is optional with a safe default, so no existing call
site breaks; Task 3 Step 3 explicitly requires updating the two recursive
call sites (`Add`/`Mul`) to thread it through, which is checked in Step 5's
test run against the existing suite. `_numeric_solve_stationarity`'s
signature is reused, not redefined — Task 5 Step 1 explicitly instructs
confirming its generic behavior over `decision_syms` handles a 1-element
list before relying on it.

**4. Ambiguity check:** "only when the IC/IR proof needs monotonicity, not
value" is made concrete and checkable via
`_monotone_difference_functions`'s structural (polynomial-degree-1-in-
placeholders) test, not asserted by prose alone. The scalar-vs-vector
fail-closed tolerance question (Task 5 Step 5) is explicitly flagged as an
edge case to verify rather than assumed to just work, with an explicit
instruction not to weaken R11's existing guarantees to accommodate it.

**5. Program-closing responsibility:** as the last round, Task 8 explicitly
writes the program-wide summary rather than a further plan handoff,
matching the "Handoff from R12" section's own statement at the top of this
plan that R13 is the program's end. This mirrors the umbrella spec's R8
precedent (the original zero-UNKNOWN program's R8 also closed with a
summary, not a further round handoff) as the established pattern for a
program's final round.
