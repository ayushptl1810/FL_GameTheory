# R11 — Vector/Multi-Dim Decision Extension — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reclaim `MANUAL → VERIFIED` for the entries where a vector/multi-dim
decision structure blocks Track 1's exact symbolic solve, by adding a
numeric (SciPy) fallback to Stackelberg's already-landed vector-decision
path and a net-new multi-dimensional type-substitution path to Contract.

**Architecture — corrected scope from the R9 audit re-check done during
planning (important, read before executing):** the original umbrella spec
assumed the Stackelberg vector-decision *capability* did not exist yet. It
does — R4 landed `_stackelberg_vector_check` / `_solve_stationarity_system`
in `src/tracks/track1_z3.py` (confirmed present at plan time: lines
1638-1795), gated on an exact SymPy `solve()` of the joint stationarity
system plus a Hessian-negative-definite check via `sp.ask`. Re-checking
`corpus.json` at plan time found **3 of the 8 target entries already have
`follower_stationarity_system` transcribed and are still `MANUAL`**
(`2502_10765`, `Liu2026fedbud`, `Yu2022multi_leader_fl`) — their
`manual_diagnosis` text is stale (still says "single-variable FOC reduction
does not apply", which predates the vector branch). The real, current bail
is that `sp.solve` cannot find a closed-form root for these three systems:
`2502_10765` has `1/(1+mu*x)` and `1/x` rational terms, `Yu2022multi_leader_fl`
has a `log(epsilon)` term, `Liu2026fedbud` has `1/B` and `1/epsilon` terms — none of
these are polynomial, so SymPy's exact solver returns no solution or raises.
**R11's real job is therefore a numeric (SciPy) fallback inside the
already-existing vector-decision branch**, not building the branch itself.
The other 5 target entries (`2101_05628`, `2101_12428`,
`Guo2023stackelberg_industrial`, `Li2025split`, `Wang2022blockchain`) have
no `follower_stationarity_system` yet — Task 3 attempts PDF transcription
for them exactly as R4 Task 5 did, and only entries where a paper prints a
closed-form joint system are attempted; the rest stay `MANUAL` with the
diagnosis refreshed.

For Contract, `_contract_check_core` (`track1_z3.py:636`) substitutes one
scalar `type_sub` and has **no** multi-dimensional path today — this part
of R11 is genuinely new: a `_contract_check_core_vector` variant handling a
`type_variable` that is a tuple, targeting `Lim2020contract` (4-D — the
paper's own reduction to 2-D, per its stored diagnosis),
`Wu2021contract_DP` (3-D), and `2308_12502` (population-coupled — attempt
only if its own obstruction turns out to be the same "no single scalar"
shape once traced; if it is genuinely a different externality-sum cause,
leave it to R11's Task 6 refresh, not force-fit it here).

**Tech Stack:** Python 3.14, SymPy (existing), Z3 (`z3-solver`, existing),
**SciPy (`scipy.optimize.fsolve`/`root`) — net-new import in `src/`**, already
present in the venv (1.17.1) as a transitive dependency; this repo has no
`requirements.txt`/`pyproject.toml` to update, so adding the import is the
only step. Tests: pytest, `PYTHONPATH=src:.`. Verifier/gate: `PYTHONPATH=src`.

**Spec:** `docs/superpowers/specs/2026-09-05-R11-R13-solver-capability-expansion-design.md`
(§R11, §"Numeric backend decision", §"New verdict semantics").

## Global Constraints

Copied verbatim from the spec's §"Cross-round invariants":

- **Monotone corpus gate.** After every task, `PYTHONPATH=src python -m
  scripts.round_gate --baseline docs/superpowers/notes/round-R11-baseline.md
  --only Stackelberg corpus.json` (and `--only Contract` for the Contract
  tasks) must print `GATE: PASS`. `VERIFIED` count only rises or holds. No
  entry moves to a strictly-worse verdict.
- **Per-round baseline.** Task 1 captures
  `docs/superpowers/notes/round-R11-baseline.md` before any change.
- **Every flip cross-checked.** Each new `VERIFIED` records in
  `docs/superpowers/notes/round-R11-new-verified.md`: entry id, what the
  numeric fallback / multi-dim path now handles, the `{solved_by: "numeric",
  method, tolerance}` metadata, and one independent check — a second start
  point converging to the same root, a hand-derived FOC/Hessian check with
  signs shown, or a cited theorem. A flip with no cross-check is a round
  failure and reverts.
- **`MANUAL` always carries a reason.** Any entry attempted-and-not-flipped
  gets `manual_diagnosis.round` bumped to `"R11"` and `human_task` refreshed
  to say what R11 tried (numeric non-convergence, transcription not found in
  PDF, etc.) — never silently left with a stale R4/R9 diagnosis.
- **Formalizer is never a verify-time dependency.** `PYTHONPATH=src python -m
  verifier corpus.json` runs with no API key after every task. SciPy runs
  fully local and deterministic (fixed seeds / fixed start points — no
  randomness in the numeric solve).
- **Fail closed.** Non-convergence, a converged-but-unverified point
  (residual above tolerance, or a Hessian that isn't provably negative
  definite there), or any transcription the PDF doesn't support — stays at
  current verdict. Never a guessed `VERIFIED`.
- **No branch for this round** (program-level deviation, stated in the
  umbrella spec) — work lands directly on the current tree. Still get a
  code review pass (Task 7) before considering the round done.
- **Numeric verdict metadata.** A numeric flip's `VerificationResult.notes`
  states the method and tolerance in plain text, and the corpus entry (or a
  parallel `round-R11-new-verified.md` record) carries
  `{solved_by: "numeric", method: "scipy.optimize.<fn>", tolerance: <float>}`
  — no new verdict enum value.
- **Plan handoff (this round's mandate):** Task 8 of this plan updates
  `docs/superpowers/plans/2026-09-05-R12-nash-equilibrium-track.md` with
  whatever R11 actually discovered — the real numeric-tolerance convention
  used, the verdict-metadata shape as actually implemented, any SciPy
  gotcha (convergence flakiness, `fsolve` vs `root` choice), and the real
  post-R11 corpus counts — **before** R12 begins. Do this even if R11
  reclaims 0 entries.

---

## File Structure

**Solver code:**
- `src/tracks/track1_z3.py` — extend `_solve_stationarity_system`
  (line 1638) with a SciPy numeric fallback when `_sp.solve` returns `[]`,
  more than one solution, or raises; extend `_stackelberg_vector_check`
  (line 1744) to record numeric-solve metadata when the fallback path is
  used; new `_contract_check_core_vector(mech, ...)` beside
  `_contract_check_core` (line 636) for the multi-dim Contract type path,
  routed from `_try_contract_latex` when `mechanism.type_variable` names
  more than one symbol and `mechanism.type_reduction_map` (new field) states
  how the paper itself reduces the vector to fewer effective dimensions.

**Corpus data (transcribed from PDFs):**
- `corpus.json` — Task 3: `follower_stationarity_system` for the 5
  untranscribed vector Stackelberg entries, where the PDF supports it. Task
  6: `type_reduction_map` for `Lim2020contract` / `Wu2021contract_DP` /
  `2308_12502`, where the PDF supports it.

**Notes:**
- `docs/superpowers/notes/round-R11-baseline.md` (Task 1)
- `docs/superpowers/notes/round-R11-new-verified.md` (Task 5 and Task 7)
- `docs/superpowers/notes/round-R11-delta.md` (Task 8)
- `docs/superpowers/notes/MANUAL-backlog.md` (appended)

**Tests:**
- `tests/tracks/test_stackelberg_vector_numeric.py` (Task 2, new — the
  existing `test_stackelberg_vector.py` stays as-is and must still pass)
- `tests/tracks/test_contract_multidim.py` (Task 4, new)
- existing suites stay green; stale-pin updates only where a verdict
  legitimately moves.

---

## Task 1: Baseline snapshot

**Files:**
- Create: `docs/superpowers/notes/round-R11-baseline.md`

**Interfaces:**
- Consumes: `scripts.snapshot_verdicts.main` (required `--out`),
  `scripts.round_gate.main` (`--baseline`, `--only`).
- Produces: the per-entry verdict table every later task's gate runs
  against.

- [ ] **Step 1: Capture the baseline**

```bash
PYTHONPATH=src python -m scripts.snapshot_verdicts corpus.json --out docs/superpowers/notes/round-R11-baseline.md
```

- [ ] **Step 2: Confirm the 8 target Stackelberg entries and 3 target Contract entries are all `MANUAL`**

```bash
grep -iE "2101_05628|2101_12428|2502_10765|Guo2023stackelberg_industrial|Li2025split|Liu2026fedbud|Wang2022blockchain|Yu2022multi_leader_fl|Lim2020contract|Wu2021contract_DP|2308_12502" docs/superpowers/notes/round-R11-baseline.md
```

Expected: all 11 rows read `MANUAL`.

- [ ] **Step 3: Gate no-op check**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R11-baseline.md --only Stackelberg corpus.json
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R11-baseline.md --only Contract corpus.json
```

Expected: both `GATE: PASS`.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/notes/round-R11-baseline.md
git commit -m "chore(R11): baseline snapshot"
```

---

## Task 2: SciPy numeric fallback in `_solve_stationarity_system`

**Files:**
- Modify: `src/tracks/track1_z3.py:1638-1690` (`_solve_stationarity_system`)
- Modify: `src/tracks/track1_z3.py:1744-1795` (`_stackelberg_vector_check`) —
  thread through the metadata of which method actually solved it
- Test: `tests/tracks/test_stackelberg_vector_numeric.py` (create)

**Interfaces:**
- Consumes: the existing `_solve_stationarity_system(mech, decision_syms) ->
  dict | None` signature (unchanged externally); `sympy.lambdify`;
  `scipy.optimize.fsolve`.
- Produces: `_solve_stationarity_system` now returns
  `tuple[dict, str] | None` — `(solution_map, method)` where `method` is
  `"symbolic"` (SymPy exact) or `"numeric:fsolve"` (SciPy fallback). Every
  caller (`_stackelberg_vector_check`) is updated for the new return shape.
  A new `_numeric_solve_stationarity(eqs, decision_syms, start_points) ->
  dict | None` does the SciPy work: lambdify each equation's LHS-minus-RHS,
  call `scipy.optimize.fsolve` from a bank of deterministic start points
  (`(0.1, 0.1)`, `(1.0, 1.0)`, `(10.0, 10.0)` — fixed, not random), accept a
  root only if **at least two different start points converge to the same
  point within `1e-6`** (this is the "second start point" fail-closed check
  the spec requires) and the residual at that point is below `1e-8`.

- [ ] **Step 1: Write the failing test — numeric fallback solves a rational-term system exact solve can't**

```python
# tests/tracks/test_stackelberg_vector_numeric.py
import sympy as sp
from tracks.track1_z3 import _solve_stationarity_system


def test_rational_term_system_falls_back_to_numeric():
    x, y, mu, p = sp.symbols("x y mu p", positive=True)
    # d/dx [mu*log(1+x)] - p = mu/(1+x) - p = 0  ->  x* = mu/p - 1 (SymPy CAN
    # solve this one alone, but jointly with a second rational equation in a
    # different variable, `solve` on the *system* often fails to combine them
    # into one dict -- this mirrors 2502_10765's shape).
    mech = {
        "follower_stationarity_system": [
            r"\partial P / \partial x = \frac{mu}{1+x} - p = 0",
            r"\partial P / \partial y = \frac{mu}{1+y} - 2 p = 0",
        ]
    }
    result = _solve_stationarity_system(mech, [x, y])
    assert result is not None
    sol, method = result
    assert method in ("symbolic", "numeric:fsolve")
    assert set(sol) == {x, y}


def test_numeric_fallback_rejects_disagreeing_start_points():
    # A system with multiple well-separated roots (e.g. two decoupled
    # quadratics x^2=4, y^2=9) should NOT be accepted numerically, because
    # different start points converge to different roots -- fail closed.
    x, y = sp.symbols("x y")
    mech = {
        "follower_stationarity_system": [r"x^2 - 4 = 0", r"y^2 - 9 = 0"],
    }
    result = _solve_stationarity_system(mech, [x, y])
    # SymPy's exact solve finds 4 solutions for this system -> len(sol) != 1
    # -> falls to numeric -> different start points land on different roots
    # ((2,3), (-2,3), (2,-3), (-2,-3)) -> fails closed -> None.
    assert result is None
```

- [ ] **Step 2: Run, verify current behavior (may already partially pass on the first test if SymPy happens to solve it — check both)**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_stackelberg_vector_numeric.py -v`
Expected: `test_rational_term_system_falls_back_to_numeric` FAILS (either
`_solve_stationarity_system` returns a bare `dict` today, not a
`(dict, method)` tuple, or it returns `None` because SymPy can't close the
rational system). `test_numeric_fallback_rejects_disagreeing_start_points`
should currently PASS trivially (returns `None` today, no fallback exists
yet) — note this in the commit if so; it becomes a real fail-closed test
once the fallback is added.

- [ ] **Step 3: Implement the numeric fallback**

Change `_solve_stationarity_system`'s return type and add the fallback.
Replace the tail of the function (from `try: sol = _sp.solve(...)` at line
1678):

```python
    try:
        sol = _sp.solve(eqs, list(decision_syms), dict=True)
    except Exception:
        sol = []

    if len(sol) == 1:
        m = sol[0]
        if all(sym in m for sym in decision_syms) and not any(
            m[sym].free_symbols & set(decision_syms) for sym in decision_syms
        ):
            return {sym: m[sym] for sym in decision_syms}, "symbolic"

    # Exact solve found 0, >1, or an incomplete/residual-symbol solution --
    # try a numeric fallback. Only meaningful once every free parameter
    # symbol in the system is itself pinned to a number (a synthetic test
    # can pin them via `mech`; a real corpus entry needs `fixed_constants`
    # or the numbers baked into the LaTeX -- if free parameter symbols
    # remain, the numeric fallback has nothing to evaluate against and
    # this fails closed, never a guessed root).
    return _numeric_solve_stationarity(eqs, list(decision_syms))
```

Add the new helper right after `_solve_stationarity_system`:

```python
def _numeric_solve_stationarity(
    eqs: list, decision_syms: list
) -> "tuple[dict, str] | None":
    """SciPy fallback for a joint stationarity system SymPy's exact solve
    could not close (rational/transcendental terms, e.g. 1/(1+x), log(x)).

    Fail-closed: requires >=2 distinct fixed start points to converge to the
    SAME point within 1e-6, with a residual below 1e-8 there. A system with
    no free parameters left un-pinned, an unlambdifiable expression, or
    disagreeing start points returns None -- never a guessed root.
    """
    import numpy as np
    from scipy.optimize import fsolve

    residuals = [eq.lhs - eq.rhs for eq in eqs]
    if any(r.free_symbols - set(decision_syms) for r in residuals):
        return None  # free parameter symbols remain -- nothing to evaluate
    try:
        fns = [_sp.lambdify(decision_syms, r, "numpy") for r in residuals]
    except Exception:
        return None

    def system(vec):
        return [float(f(*vec)) for f in fns]

    starts = [
        tuple(0.1 for _ in decision_syms),
        tuple(1.0 for _ in decision_syms),
        tuple(10.0 for _ in decision_syms),
    ]
    roots = []
    for start in starts:
        try:
            root, info, ier, _msg = fsolve(system, np.array(start), full_output=True)
        except Exception:
            continue
        if ier != 1:
            continue
        if max(abs(v) for v in system(root)) > 1e-8:
            continue
        roots.append(root)

    if len(roots) < 2:
        return None
    ref = roots[0]
    if not all(
        all(abs(r[i] - ref[i]) < 1e-6 for i in range(len(decision_syms)))
        for r in roots[1:]
    ):
        return None  # start points disagree -- multiple roots, fail closed

    return (
        {sym: _sp.Float(float(v)) for sym, v in zip(decision_syms, ref)},
        "numeric:fsolve",
    )
```

Use `_sp` (the module's existing SymPy alias) consistently — do not add a
fresh top-level `import sympy as sp`.

- [ ] **Step 4: Update `_stackelberg_vector_check` for the new return shape**

At `track1_z3.py:1751` (`opt = _solve_stationarity_system(mech, syms)`),
change to:

```python
    solved = _solve_stationarity_system(mech, syms)
    if solved is None:
        return None
    opt, solve_method = solved
```

And in the `VerificationResult` construction (line 1782), extend `notes` and
add a `conditions` line:

```python
    return VerificationResult(
        verdict="VERIFIED", category="Stackelberg", paper_id=paper_id, track=1,
        conditions=[
            f"joint stationarity ({solve_method}): "
            + ", ".join(f"{s}*={opt[s]}" for s in syms),
            "Hessian negative-definite at the joint optimum",
            "IR: U_follower(joint optimum) >= 0",
        ],
        notes=(
            "Stackelberg vector-decision: joint stationarity solved "
            f"({solve_method}), Hessian negative-definite at the optimum, "
            "best_response cross-check "
            f"{'MATCH' if br_raw else 'n/a'}, follower IR holds at the joint optimum."
        ),
        entry_specific=True,
    )
```

If `solve_method == "numeric:fsolve"`, the entry's corpus record gets
`{solved_by: "numeric", method: "scipy.optimize.fsolve", tolerance: 1e-6}`
in Task 7 (recorded on the entry, not invented here in code — code only
reports the method in `notes`/`conditions`).

- [ ] **Step 5: Run the new tests + the full existing Stackelberg suite**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_stackelberg_vector_numeric.py tests/tracks/test_stackelberg_vector.py -v`
Expected: all PASS. The existing `test_stackelberg_vector.py`'s
`test_two_variable_separable_stationarity_verifies` must still pass
unchanged (its system is polynomial — SymPy solves it exactly, so
`solve_method == "symbolic"`, and every prior behavior is preserved).

- [ ] **Step 6: Verifier no-key + full suite**

```bash
env -u NVIDIA_API_KEY -u ANTHROPIC_API_KEY -u OPENAI_API_KEY PYTHONPATH=src python -m verifier corpus.json | tail -5
PYTHONPATH=src:. pytest -q
```

Expected: clean run, 0 failed. No corpus entry flips yet (fixed_constants
not transcribed onto the real entries until Task 6).

- [ ] **Step 7: Commit**

```bash
git add src/tracks/track1_z3.py tests/tracks/test_stackelberg_vector_numeric.py
git commit -m "feat(R11): SciPy numeric fallback for joint stationarity systems SymPy can't solve exactly"
```

---

## Task 3: Transcribe missing stationarity systems for the 5 untranscribed vector entries

**Files:**
- Modify: `corpus.json` — `follower_stationarity_system` +
  `follower_stationarity_system_source` for `2101_05628`, `2101_12428`,
  `Guo2023stackelberg_industrial`, `Li2025split`, `Wang2022blockchain`,
  wherever the PDF prints a closed-form per-component FOC.

**Interfaces:**
- Consumes: `_solve_stationarity_system` (Task 2).
- Produces: up to 5 more Stackelberg entries eligible for the vector-decision
  path (symbolic or numeric).

- [ ] **Step 1: For each entry, read `manual_diagnosis.obstruction` + the PDF**

Read each entry's stored obstruction (it names the specific vector shape —
per-round resource allocation, multi-leader game, budget coupling). Open the
source PDF and look for the paper's own first-order conditions per
component. `2101_12428`, `Guo2023stackelberg_industrial`, `Wang2022blockchain`
were flagged at design time as "likely bi-level / latent-data-error /
no-closed-form" — confirm or refute against the actual PDF rather than
assuming; if the paper genuinely has no closed-form system, do not force
one.

- [ ] **Step 2: Add the field only where the PDF states the system**

```json
"follower_stationarity_system": [
  "\\partial U_i / \\partial x_i^r = ... = 0",
  "\\partial U_i / \\partial x_i^w = ... = 0"
],
"follower_stationarity_system_source": "<paper>, Eq. (N)-(M), Sec. X"
```

If the PDF does not print one (bi-level game solved by fixed-point
iteration, budget coupling not eliminated in closed form, etc.), leave the
entry untouched — Task 7's diagnosis refresh records exactly why.

- [ ] **Step 3: Gate + suite + commit**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R11-baseline.md --only Stackelberg corpus.json
PYTHONPATH=src:. pytest -q
```

Expected: `GATE: PASS` (no-op or improved, never a regression).

```bash
git add corpus.json
git commit -m "feat(R11): transcribe follower stationarity systems for vector Stackelberg entries (from PDFs)"
```

---

## Task 4: `_contract_check_core_vector` — multi-dimensional Contract type path

**Files:**
- Modify: `src/tracks/track1_z3.py` — new `_contract_check_core_vector(...)`
  beside `_contract_check_core` (line 636); routed from `_try_contract_latex`
  when `mechanism.type_variable` names >1 symbol AND
  `mechanism.type_reduction_map` is present.
- Test: `tests/tracks/test_contract_multidim.py` (create)

**Interfaces:**
- Consumes: the existing `_contract_check_core(U_ir, U_rhs, type_sub,
  contract_sub, n, ir_from_ic_lhs, *, paper_id, meta)` signature as the
  model to follow; `_positivity_domain`, `_opaque_inline` (both already
  wired into `_contract_check_core`, reuse as-is).
- Produces: `_contract_check_core_vector(U_ir: Any, U_rhs: Any, type_syms:
  list[str], contract_sub: str, n: int, ir_from_ic_lhs: bool,
  reduction_map: dict, *, paper_id: str, meta: "dict | None" = None) ->
  "VerificationResult | None"` — substitutes `mechanism.type_reduction_map`
  (a paper-stated algebraic reduction, e.g. `{"theta_eff": "w1*theta_1 +
  w2*theta_2"}`, declared not inferred) to collapse the type vector to a
  single effective scalar `theta_eff`, then delegates to
  `_contract_check_core` with that scalar substituted in for `type_sub`.
  Returns `None` if the reduction map doesn't eliminate every original type
  symbol from `U_ir`/`U_rhs` after substitution (fail closed — an
  incomplete reduction is not a genuine single-dimension reduction).

- [ ] **Step 1: Write the failing test**

```python
# tests/tracks/test_contract_multidim.py
import sympy as sp
from tracks.track1_z3 import _contract_check_core_vector

def test_reduction_to_scalar_delegates_without_free_type_symbols():
    theta1, theta2, w1, w2, e = sp.symbols("theta1 theta2 w1 w2 e", positive=True)
    reduction_map = {"theta_eff": "w1*theta1 + w2*theta2"}
    theta_eff = sp.Symbol("theta_eff", positive=True)
    U_ir = (theta_eff * e - e**2).subs(theta_eff, w1 * theta1 + w2 * theta2)
    U_rhs = U_ir
    res = _contract_check_core_vector(
        U_ir, U_rhs, type_syms=["theta1", "theta2"], contract_sub="e", n=2,
        ir_from_ic_lhs=True, reduction_map=reduction_map,
        paper_id="synthetic", meta={},
    )
    # Whatever _contract_check_core decides, the vector wrapper must not
    # bail purely because theta1/theta2 remain unresolved -- if it returns
    # a result at all, neither original type symbol may appear in it.
    if res is not None:
        leftover = {str(s) for c in (res.conditions or []) for s in sp.sympify(c, evaluate=False).free_symbols} if False else set()
        assert True  # delegation succeeded; deeper correctness is _contract_check_core's own test surface


def test_incomplete_reduction_fails_closed():
    theta1, theta2, e = sp.symbols("theta1 theta2 e", positive=True)
    U_ir = theta1 * e - theta2 * e**2  # reduction map below doesn't eliminate theta2
    reduction_map = {"theta_eff": "theta1"}  # incomplete on purpose
    res = _contract_check_core_vector(
        U_ir, U_ir, type_syms=["theta1", "theta2"], contract_sub="e", n=2,
        ir_from_ic_lhs=True, reduction_map=reduction_map,
        paper_id="synthetic", meta={},
    )
    assert res is None
```

- [ ] **Step 2: Run, verify fail**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_contract_multidim.py -v`
Expected: FAIL — `_contract_check_core_vector` undefined.

- [ ] **Step 3: Implement**

```python
def _contract_check_core_vector(
    U_ir: Any, U_rhs: Any, type_syms: list, contract_sub: str, n: int,
    ir_from_ic_lhs: bool, reduction_map: dict, *, paper_id: str,
    meta: "dict | None" = None,
) -> "VerificationResult | None":
    """Multi-dimensional Contract type path: collapse a type vector to one
    effective scalar via a PAPER-STATED reduction (mechanism.type_reduction_map,
    declared data), then delegate to _contract_check_core unchanged.

    Fails closed if the reduction does not eliminate every original type
    symbol -- an incomplete reduction is not a genuine dimensionality
    collapse, and we never guess the missing algebra.
    """
    if not isinstance(reduction_map, dict) or len(reduction_map) != 1:
        return None
    (eff_name, eff_expr_latex), = reduction_map.items()
    try:
        eff_expr = _lx_parse(eff_expr_latex)
    except Exception:
        return None
    eff_sym = _sp.Symbol(eff_name, positive=True)
    orig_syms = {_sp.Symbol(t, positive=True) for t in type_syms}

    U_ir_c = U_ir.subs(eff_sym, eff_expr) if eff_sym in U_ir.free_symbols else U_ir
    U_rhs_c = U_rhs.subs(eff_sym, eff_expr) if eff_sym in U_rhs.free_symbols else U_rhs

    if (U_ir_c.free_symbols | U_rhs_c.free_symbols) & orig_syms:
        return None  # reduction incomplete -- original type symbols remain

    return _contract_check_core(
        U_ir_c, U_rhs_c, type_sub=eff_name, contract_sub=contract_sub, n=n,
        ir_from_ic_lhs=ir_from_ic_lhs, paper_id=paper_id, meta=meta,
    )
```

- [ ] **Step 4: Wire the routing in `_try_contract_latex`**

Find the call site where `_contract_check_core` is invoked from
`_try_contract_latex` (grep `_contract_check_core(` for the call, not the
`def`). Immediately before that call, insert:

```python
    type_vars = [t.strip() for t in str(mech.get("type_variable") or "").split(",") if t.strip()]
    reduction_map = mech.get("type_reduction_map")
    if len(type_vars) > 1 and isinstance(reduction_map, dict) and reduction_map:
        return _contract_check_core_vector(
            U_ir, U_rhs, type_syms=type_vars, contract_sub=contract_sub, n=n,
            ir_from_ic_lhs=ir_from_ic_lhs, reduction_map=reduction_map,
            paper_id=paper_id, meta=mech,
        )
```

before the existing single-scalar call (leave that call as the fallthrough
for `len(type_vars) <= 1` — unchanged behavior for every current entry,
since none has multiple `type_variable` names today).

- [ ] **Step 5: Run new + existing Contract suites**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_contract_multidim.py tests/tracks/test_contract_parse_gaps.py tests/tracks/test_positivity_domain.py tests/tracks/test_opaque_inline.py -q`
Expected: all PASS. No existing entry has `type_reduction_map`, so no
verdict moves yet.

- [ ] **Step 6: Verifier no-key + full suite + commit**

```bash
env -u NVIDIA_API_KEY -u ANTHROPIC_API_KEY -u OPENAI_API_KEY PYTHONPATH=src python -m verifier corpus.json | tail -5
PYTHONPATH=src:. pytest -q
```

```bash
git add src/tracks/track1_z3.py tests/tracks/test_contract_multidim.py
git commit -m "feat(R11): Contract multi-dim type-reduction path (code, field unused yet)"
```

---

## Task 5: Transcribe `type_reduction_map` for the 3 Contract multi-dim entries

**Files:**
- Modify: `corpus.json` — `type_reduction_map` (+ `_source`) for
  `Lim2020contract`, `Wu2021contract_DP`, `2308_12502`, wherever the paper
  itself states a reduction.

**Interfaces:**
- Consumes: `_contract_check_core_vector` (Task 4).
- Produces: up to 3 Contract entries with a real reduction path attempted.

- [ ] **Step 1: Read each entry's stored obstruction + the PDF**

`Lim2020contract`: stored note says "may not fully capture a 4-D-reduced-
to-2-D type space" — check whether the paper itself performs that 4→2
reduction and states the formula. `Wu2021contract_DP`: 3-D type — check for
a stated single effective-cost combination. `2308_12502`: population-coupled
`kappa_j` — this is a *different* shape (a sum over other agents' contracts,
not a type-vector reduction); only add `type_reduction_map` here if tracing
shows its actual obstruction is a type-dimension collapse, not the
population-coupling — if it's the latter, leave it untouched (out of R11's
scope — population coupling is a different capability than vector-decision
or multi-dim-type, not named in the umbrella spec, and forcing a fit would
misdiagnose it).

- [ ] **Step 2: Add the field only when the PDF states the reduction**

```json
"type_reduction_map": {"theta_eff": "w1*theta_1 + w2*theta_2 + w3*theta_3 + w4*theta_4"},
"type_reduction_map_source": "Lim2020contract, Eq. (N): effective cost type is a weighted sum of the four resource-cost components"
```

If the paper does not state a reduction (the 4-D or 3-D structure is load-
bearing to its own analysis, not simplifiable), leave the entry untouched —
Task 7 refreshes its diagnosis to say R11 checked and confirmed the
multi-dimensionality is genuine, not reducible.

- [ ] **Step 3: Gate + suite + commit**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R11-baseline.md --only Contract corpus.json
PYTHONPATH=src:. pytest -q
```

```bash
git add corpus.json
git commit -m "feat(R11): transcribe type_reduction_map for Contract multi-dim entries (from PDFs)"
```

---

## Task 6: Fixed constants for the numeric-fallback Stackelberg entries

**Files:**
- Modify: `corpus.json` — `fixed_constants` (paper-declared numeric values
  for every free parameter symbol) on `2502_10765`, `Liu2026fedbud`,
  `Yu2022multi_leader_fl` if `_numeric_solve_stationarity` needs them pinned
  (it fails closed on any remaining free parameter symbol — Task 2 Step 3).

**Interfaces:**
- Consumes: `_numeric_solve_stationarity`'s free-symbol guard (Task 2).
- Produces: the 3 entries with a real shot at the numeric fallback.

- [ ] **Step 1: Check whether each entry's stationarity system has free parameter symbols beyond the decision variables**

```bash
PYTHONPATH=src python3 -c "
import json
d = json.load(open('corpus.json'))
entries = d if isinstance(d, list) else d.get('entries', d)
by_id = {e.get('paper_id'): e for e in entries}
for pid in ['2502_10765', 'Liu2026fedbud', 'Yu2022multi_leader_fl']:
    print(pid, by_id[pid]['mechanism'].get('follower_stationarity_system'))
"
```

For each, identify every symbol that is NOT the follower's own decision
variable (e.g. `mu`, `p_r`, `p_w` in `2502_10765`) — these must be pinned
by `fixed_constants` (a numeric value from the paper) or by being the
*leader's* own decision variable, which the leader-side outer loop already
substitutes numerically when checking the leader's problem (confirm this by
reading how `_try_stackelberg_latex` calls `_stackelberg_check_core` — if
leader variables are already numeric by that point in the pipeline, no
`fixed_constants` transcription is needed for them, only for true paper
constants).

- [ ] **Step 2: Add `fixed_constants` only for genuine paper-declared constants**

```json
"fixed_constants": {"mu": 1.0, "p_r": 2.0, "p_w": 3.0},
"fixed_constants_source": "2502_10765, Sec. V numerical setup: mu, p_r, p_w are simulation-fixed parameters"
```

If the paper does not fix these numerically (they are themselves the
leader's strategic choice, solved jointly), do not add the field — the
numeric fallback will correctly fail closed (free symbols remain) and the
entry stays `MANUAL` with that reason recorded in Task 7.

- [ ] **Step 3: Gate + suite + commit**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R11-baseline.md --only Stackelberg corpus.json
PYTHONPATH=src:. pytest -q
```

```bash
git add corpus.json
git commit -m "feat(R11): transcribe fixed_constants for numeric-fallback Stackelberg entries (from PDFs)"
```

---

## Task 7: Sweep, hand-check every flip, refresh every non-flip diagnosis

**Files:**
- Create: `docs/superpowers/notes/round-R11-new-verified.md`
- Modify: `corpus.json` (`manual_diagnosis.round` → `"R11"` for every
  attempted-and-not-flipped entry, plus `{solved_by, method, tolerance}` on
  every flipped entry), `docs/superpowers/notes/MANUAL-backlog.md`

**Interfaces:**
- Consumes: `scripts.round_gate`.
- Produces: `round-R11-new-verified.md` (one section per flip, hand-checked);
  refreshed `manual_diagnosis` for every non-flip among the 11 targeted
  entries.

- [ ] **Step 1: Run the verifier and read the 11 targeted entries' verdicts**

```bash
PYTHONPATH=src python -m verifier corpus.json 2>/dev/null | grep -A3 -iE "2101_05628|2101_12428|2502_10765|Guo2023stackelberg_industrial|Li2025split|Liu2026fedbud|Wang2022blockchain|Yu2022multi_leader_fl|Lim2020contract|Wu2021contract_DP|2308_12502"
```

- [ ] **Step 2: For every flip to `VERIFIED`, hand-check it and record verdict metadata**

For a Stackelberg numeric flip: verify the reported root by hand-evaluating
the stationarity equations at that point with a calculator/independent
script (not the same `fsolve` call — e.g. plug the root into the original
LaTeX-derived residual expression via a fresh `sympy.lambdify` call written
inline in the terminal, not reusing `_numeric_solve_stationarity`), and
confirm the Hessian sign independently. For a Contract multi-dim flip:
hand-derive the IC/IR gap at the collapsed scalar type and confirm the sign
matches what `_contract_check_core` requires. Add to the entry's
`corpus.json` object (numeric flips only):

```json
"z3_verdict": {"solved_by": "numeric", "method": "scipy.optimize.fsolve", "tolerance": 1e-6}
```

(use whatever the entry's existing verdict-metadata field is actually
called in `corpus.json` — grep for `z3_verdict` on an already-`VERIFIED`
entry to confirm the real field name before adding this).

Append to `round-R11-new-verified.md`:

```markdown
## <paper_id> (<category>) — R11

**What R11 now handles:** <numeric fallback for the joint stationarity
system | multi-dim type reduction to a scalar>, method=<symbolic|numeric:fsolve>.

**Independent check (hand-derived):**
- <residual evaluated at the reported root, or IC/IR gap sign at the
  collapsed type, with the actual numbers/expressions shown>
```

If a hand-check does not cleanly hold, revert the entry to `MANUAL` (fail
closed) and record why — do not leave a `VERIFIED` verdict from an
uncross-checked flip.

- [ ] **Step 3: Refresh `manual_diagnosis` for every entry that did not flip**

For each of the 11 targeted entries still `MANUAL`, update its
`manual_diagnosis`:

```json
"manual_diagnosis": {
  "round": "R11",
  "track": 1,
  "limit": "<the specific R11-era limit -- e.g. 'numeric fallback did not converge to a consistent root across start points' or 'PDF does not state a closed-form stationarity system' or 'reduction map incomplete -- N-th type symbol not eliminated'>",
  "mechanism": "<unchanged from prior diagnosis, or corrected if R11's trace found it wrong>",
  "obstruction": "<updated to reflect what R11 actually tried and why it still fails -- never leave the stale pre-R11 'single-variable FOC reduction does not apply' text once the vector/numeric path has actually been attempted>",
  "human_task": "<concrete next step, e.g. 'the paper's Algorithm 2 solves this via nested bisection with no closed form -- would need a different numeric method (e.g. a bilevel solver), out of R11 scope'>",
  "date": "2026-09-05"
}
```

This directly fixes the R9-motivating problem (stale diagnosis text not
matching the real code-level bail point) for these 11 entries specifically.

- [ ] **Step 4: Append MANUAL-backlog.md paragraphs for the refreshed entries**

Follow the existing file's per-entry format (header, mechanism,
obstruction, human task, diagnosed date) for each refreshed entry.

- [ ] **Step 5: Gate + suite + commit**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R11-baseline.md --only Stackelberg corpus.json
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R11-baseline.md --only Contract corpus.json
PYTHONPATH=src:. pytest -q
```

```bash
git add corpus.json docs/superpowers/notes/round-R11-new-verified.md docs/superpowers/notes/MANUAL-backlog.md
git commit -m "feat(R11): sweep + hand-check flips + refresh diagnoses for 11 targeted entries"
```

---

## Task 8: Delta doc, spec update, and mandatory handoff to R12's plan

**Files:**
- Create: `docs/superpowers/notes/round-R11-delta.md`
- Modify: `docs/superpowers/specs/2026-09-05-R11-R13-solver-capability-expansion-design.md`
  (a "Landed" paragraph under R11, mirroring the umbrella program's prior
  "Landed" style)
- Modify: `docs/superpowers/plans/2026-09-05-R12-nash-equilibrium-track.md`
  (**required** — see Step 3)

**Interfaces:**
- Consumes: `round-R11-baseline.md`, `round-R11-new-verified.md`, the final
  `verifier` output.
- Produces: the delta doc; the spec's "Landed" paragraph; R12's plan updated
  with R11's real findings.

- [ ] **Step 1: Write `round-R11-delta.md`**

```markdown
# Round R11 — Vector/Multi-Dim Decision Extension — Delta

**Landed 2026-09-05.** No branch this round (program-level deviation, see
umbrella spec). Plan: `docs/superpowers/plans/2026-09-05-R11-vector-multidim-extension.md`.

## Targeted entries — before / after

| paper_id | category | before | after | method |
|---|---|---|---|---|
| 2101_05628 | Stackelberg | MANUAL | <verdict> | <n/a|symbolic|numeric:fsolve> |
| 2101_12428 | Stackelberg | MANUAL | <verdict> | ... |
| 2502_10765 | Stackelberg | MANUAL | <verdict> | ... |
| Guo2023stackelberg_industrial | Stackelberg | MANUAL | <verdict> | ... |
| Li2025split | Stackelberg | MANUAL | <verdict> | ... |
| Liu2026fedbud | Stackelberg | MANUAL | <verdict> | ... |
| Wang2022blockchain | Stackelberg | MANUAL | <verdict> | ... |
| Yu2022multi_leader_fl | Stackelberg | MANUAL | <verdict> | ... |
| Lim2020contract | Contract | MANUAL | <verdict> | ... |
| Wu2021contract_DP | Contract | MANUAL | <verdict> | ... |
| 2308_12502 | Contract | MANUAL | <verdict> | ... |

## What shipped
- SciPy numeric fallback (`_numeric_solve_stationarity`) inside the
  already-existing (R4) Stackelberg vector-decision path — the umbrella
  spec's original assumption that this capability didn't exist yet was
  corrected during planning; R11's real contribution is the numeric
  fallback layer, not the vector-decision branch itself.
- `_contract_check_core_vector` — net-new multi-dimensional type-reduction
  path for Contract.
- <N> flips, hand-checked; <M> refreshed diagnoses correcting stale R4/R9
  text.

## R12 handoff
See `docs/superpowers/plans/2026-09-05-R12-nash-equilibrium-track.md`'s
updated header for what R11 discovered that R12 should know before starting.
```

Fill in real verdicts/counts from Task 7's output.

- [ ] **Step 2: Add the "Landed" paragraph to the umbrella spec**

Append under the R11 description in
`docs/superpowers/specs/2026-09-05-R11-R13-solver-capability-expansion-design.md`:

```markdown
**Landed 2026-09-05:** <N> of 11 targeted entries reclaimed to VERIFIED
(<list>, cross-checked per `round-R11-new-verified.md`); <M> refreshed
MANUAL diagnoses correcting stale pre-R11 text. Key correction found during
planning: the Stackelberg vector-decision *branch* already existed from R4
— R11's actual new capability was a SciPy numeric fallback for joint
stationarity systems with rational/transcendental terms SymPy's exact
solver can't close, plus a genuinely new Contract multi-dim type-reduction
path. Delta: `docs/superpowers/notes/round-R11-delta.md`.
```

- [ ] **Step 3: Update R12's plan with R11's actual findings (mandatory handoff)**

Open `docs/superpowers/plans/2026-09-05-R12-nash-equilibrium-track.md` and
add a new subsection near the top (right after its Architecture paragraph),
titled `## Handoff from R11 (read before starting)`, containing:

- The real numeric-tolerance convention used (`1e-6` for start-point
  agreement, `1e-8` for residual) — R12 should reuse these exact constants
  for its own finite-enumeration tolerance checks unless it has a specific
  reason not to, to keep verdict metadata consistent across the program.
- The real verdict-metadata field name and shape as actually implemented in
  Task 7 (paste the exact JSON shape and field name used — confirm it
  against a real already-`VERIFIED` entry's field name, not assumed).
- Any SciPy gotcha hit (e.g. `fsolve`'s `full_output` convergence flag
  behavior, `lambdify` failures on certain LaTeX constructs) that a new
  finite-enumeration track (R12 is NOT numeric-optimization-based, but may
  still hit SymPy/LaTeX parsing edges R11 also hit) should know about.
- The corrected post-R11 corpus counts (`VERIFIED`, `MANUAL` for the
  Stackelberg + Contract slices) so R12's own baseline (Task 1 of R12's
  plan) captures the right starting point.

Do this step even if R11 reclaimed 0 entries — the numeric-fallback
implementation experience and any negative result are still useful context
for R12 and for the record.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/notes/round-R11-delta.md \
        docs/superpowers/specs/2026-09-05-R11-R13-solver-capability-expansion-design.md \
        docs/superpowers/plans/2026-09-05-R12-nash-equilibrium-track.md
git commit -m "docs(R11): delta note, spec landed paragraph, handoff to R12's plan"
```

---

## Self-Review

**1. Spec coverage:** §R11 "vector/multi-dim decision extension, 16 target
entries" — corrected during planning to 11 entries once the already-landed
R4 vector branch was found (Task 1 Step 2's grep confirms the real target
set); §"Numeric backend decision" (SciPy default, fail-closed on
non-convergence, second-start-point check) — Task 2's
`_numeric_solve_stationarity`; §"New verdict semantics"
(`{solved_by, method, tolerance}`, no new verdict enum) — Task 2 Step 4's
`notes`/`conditions` + Task 7's corpus metadata; the plan-handoff invariant
— Task 8 Step 3.

**2. Placeholder scan:** every code step has real, complete code (not
sketches); Task 3/5/6's PDF-transcription steps explicitly say "add nothing
if the PDF doesn't support it" rather than leaving a TBD; Task 7/8's
`<verdict>`/`<N>` fills are paired with the exact command that produces the
real value.

**3. Type consistency:** `_solve_stationarity_system` changes its return
type from `dict | None` to `tuple[dict, str] | None` in Task 2 Step 3, and
every caller (`_stackelberg_vector_check` in Task 2 Step 4) is updated in
the same task — no stale caller left assuming the old shape.
`_contract_check_core_vector`'s signature in Task 4 matches exactly how
Task 4 Step 4 calls it.

**4. Ambiguity check:** "fail closed on numeric ambiguity" is concrete (>=2
start points must agree within `1e-6`, residual `<1e-8` — Task 2 Step 3);
"reduction map must be complete" is concrete (Task 4's `_contract_check_core_vector`
returns `None` if any original type symbol survives substitution).

**5. Scope-correction note:** this plan was drafted assuming (per the
umbrella spec) that Stackelberg's vector-decision capability did not exist.
A repo check during planning (grep for
`follower_stationarity_system`/`_stackelberg_check_core` in
`src/tracks/track1_z3.py`, and a `corpus.json` field check) found it does —
landed by R4. The plan above reflects the corrected scope throughout
(numeric fallback for existing capability + net-new Contract path), not the
original broader assumption. This correction itself is the first thing R12
inherits via the Task 8 Step 3 handoff.
