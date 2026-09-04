# R6–R7 — Second-Formalizer Pass + Honesty Gate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring `corpus.json` to its terminal state — every in-scope entry `VERIFIED` / `COUNTEREXAMPLE` / `MANUAL`, with **0 `UNKNOWN`, 0 `VERIFIED_TEMPLATE`, 0 `VERIFIED_SHAPE`** — by (Phase 6) a fresh-model formalization retry on the 25 residual `VERIFIED_TEMPLATE` entries that reclaims what it can, then (Phase 7) flipping every non-reclaimed residual to a diagnosed `MANUAL` and finalizing `MANUAL-backlog.md` as the program's human-facing deliverable.

**Architecture:** One branch `round-R6R7-final-classification` off `main`, two phases of one round (R7's flip is only meaningful after R6 has taken its shot). **Phase 6:** `architect.formalize` gains a `--second-pass` mode — a different, larger model (largest instruct model on the existing `.env` NVIDIA endpoint, pinned at round start) plus the per-entry accumulated failure reason (`manual_diagnosis` where present, else the corpus `notes` "Manual review / fail-closed" text) injected as a synthetic `concerns` entry through the existing `_user_message` path. `verify_from_ast` runs the real solver; every flip is hand-checked exactly as R2–R5. **Phase 7:** every entry still `VERIFIED_TEMPLATE`/`VERIFIED_SHAPE`/`UNKNOWN` gets `write_manual_diagnosis(..., round_="R7", ...)` + `append_backlog_paragraph`. Then a full audit of all ~62 pre-existing backlog paragraphs for format consistency, grouping by recurring obstruction family, and a summary header. **Also folded in:** the two R5 carry-forward findings as one no-corpus-effect tooling task.

**Tech Stack:** Python 3.14, SymPy, Z3, CVXPY/dReal (unused this round). Tests: pytest, `PYTHONPATH=src:.`. Verifier/gate: `PYTHONPATH=src`. LLM sweep: `architect.formalize` against the `.env` NVIDIA endpoint; Phase 6 model pinned via `ARCHITECT_LLM_MODEL`, `ARCHITECT_LLM_TIMEOUT_S=300`.

**Spec:** `docs/superpowers/specs/2026-09-02-zero-unknown-program-design.md` (§"R6–R7 — Second-formalizer pass + honesty gate", §"Cross-round invariants", §"End state").

## Global Constraints

Copied verbatim from the spec's §"Cross-round invariants" and §"R6–R7":

- **Monotone corpus gate.** After every task, `PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R6R7-baseline.md corpus.json` must print `GATE: PASS`. `VERIFIED` (entry-specific) count only rises or holds. No entry moves to a strictly-worse verdict. `VERIFIED_TEMPLATE` → `VERIFIED` (Phase 6) and `VERIFIED_TEMPLATE`/`UNKNOWN` → `MANUAL` (Phase 7) are the targets. Anything → bare `UNKNOWN` is a regression.
- **Per-round baseline.** Task 1 captures `docs/superpowers/notes/round-R6R7-baseline.md` (full per-entry verdict table) before any change, via `scripts.snapshot_verdicts` with a required `--out`.
- **Every flip cross-checked.** Each new `VERIFIED`/`COUNTEREXAMPLE` records in `docs/superpowers/notes/round-R6R7-new-verified.md`: entry id, what the second-pass formalization now handles, and one independent check — hand-derived IC/FOC gap with signs, OR a second track agreeing, OR a Z3/SMT model inspection, OR a cited theorem. A new `VERIFIED` with no cross-check is a round failure and reverts to baseline.
- **`MANUAL` always carries a reason.** Any entry set `MANUAL` gets `verdict_override: "MANUAL"` + a `manual_diagnosis` dict (`round`, `track`, `limit`, `mechanism`, `obstruction`, `human_task`, `date`) via `architect.formalize.write_manual_diagnosis`, and a paragraph in `docs/superpowers/notes/MANUAL-backlog.md` via `append_backlog_paragraph`.
- **Formalizer is never a verify-time dependency.** `PYTHONPATH=src python -m verifier corpus.json` must run with **no API key** after every task. No Track file or `verifier.py` may import `architect.*` or an LLM client at module top. Phase 6 output is committed as `formalized_ast` and read by the deterministic path.
- **Fail closed.** Any parse ambiguity, undecidable fragment, unclean hand-check, or an adversary flag that survives the retry → the entry stays at its current verdict (Phase 6) or goes to a diagnosed `MANUAL` (Phase 7) — never a guessed `VERIFIED`/`COUNTEREXAMPLE`.
- **`RECONCILE-FLAG` conflicts are worked, not ignored.** An LLM/LaTeX verdict conflict on an existing entry-specific `VERIFIED` is surfaced by `print_summary`, adjudicated, and the resolution recorded before the round closes.
- **Branch per round.** `round-R6R7-final-classification` off `main`; merge to `main` on a clean whole-branch review before R8. Local merges only, no push, no PR.
- **Out of scope, never touched:** the ~80 `Valuation`/`RL`/`Naive` entries; the 62 in-scope entries already carrying `verdict_override: "MANUAL"` from R2–R5 (Phase 6 does NOT re-attempt them — the spec's "residual" is the 25 un-overridden `VERIFIED_TEMPLATE` only); the 18 entry-specific `VERIFIED`.

---

## The residual set (verified on `main`, 2026-09-05 after R5 merge `bfb2e8f`)

**25 in-scope `VERIFIED_TEMPLATE` with no `verdict_override`.** `VERIFIED_SHAPE` is already 0; `UNKNOWN` `Kang2019contract_mobile` already carries `verdict_override: "MANUAL"` (R4); all 5 `UNSUPPORTED` (4 Shapley + `Khan2019edge`) already carry `verdict_override: "MANUAL"` (R3b/R5). So the residual is exactly these 25:

| Category | paper_id |
|---|---|
| Contract (8) | `2403_09153`, `2502_20882`, `Lim2020contract`, `Ma2023joint_pricing`, `Saputra2020fl_contract`, `Saputra2021iov_contract`, `Saputra2021straggling`, `Wu2021contract_DP` |
| Stackelberg (14) | `1811_12082`, `2110_12876`, `2203_00270`, `2404_08261`, `2508_07676`, `Cao2025service`, `Chen2023multifactor_iot`, `FLamma2025stackelberg`, `Hu2020trading`, `Hu2022truthful_FEL`, `Javaherian2025stackelberg_ic`, `Lee2024sfl_stackelberg`, `Li2025iiot_drl`, `Xiao2020stackelberg_twostage` |
| VCG (3) | `Batool2022fl_mab`, `Mai2022double_auction`, `Zheng2023fl_market` |

Each has a `notes` string (mostly "Batch C/D/E manual review … left null (fail-closed)" naming the missing field — follower IR, follower FOC, multi-dim type) but **no `manual_diagnosis` dict**. Task 1 regenerates this list programmatically and writes it to `round-R6R7-residual.md` (id + category + verdict + the `notes` prefix that becomes the Phase-6 hint / Phase-7 diagnosis seed).

Spec estimate: Phase 6 reclaims +3–8 → `VERIFIED`; the rest → diagnosed `MANUAL` in Phase 7.

---

## File Structure

**Solver / carry-forward tooling (Task 2 — no corpus effect):**
- `src/tracks/track_coalition.py` — `_tier_b_numeric_core` returns `(core_ok, ir_ok, payment_ok, conditions)` (was a 3-tuple; `payment_ok` was folded into `core_ok`). `verify_coalition` routing: `core_ok and ir_ok and payment_ok` → `VERIFIED`; `not core_ok` → `COUNTEREXAMPLE` ("core violated"); `core_ok and ir_ok and not payment_ok` → `COUNTEREXAMPLE` ("stated payment ≠ Shapley value"); `not ir_ok` (core ok) → `MANUAL`. Add a `# ponytail:` comment on `_tier_a_symbolic_identity` naming the structural-check ceiling (a numeric/other-letter scalar prefactor on the sum passes; inherent to a substring check, no corpus entry exercises it).

**Formalizer (Task 3 — the Phase 6 mechanism):**
- `src/architect/formalize.py` — `formalize_with_retry` / `formalize_entry` gain a `prior_reason: str | None` kwarg. When set, it is prepended to `concerns` as a synthetic entry `{"field": "reformulation", "issue": "<prior_reason> — try reframing around this: fine discrete grid for a continuous type / isolate the binding constraint / drop a provably-slack term"}` so it threads through the existing `_user_message` "previous attempt had these problems" block. `main()` / `run_batch` gain `--second-pass` (reads each selected entry's `manual_diagnosis.obstruction` or, if absent, its `notes`, and passes it as `prior_reason`) and honor `ARCHITECT_LLM_MODEL` from the environment (already read at line ~383 for provenance — Task 3 wires it into the actual client call if `llm_complete` does not already honor it).

**Corpus data (Tasks 4, 5):**
- `corpus.json` — Task 4: `formalized_ast` + provenance on any Phase-6 entry that produces a valid AST (flip or not — an AST that verifies as `VERIFIED_TEMPLATE` again is still recorded). Task 5: `verdict_override: "MANUAL"` + `manual_diagnosis` on every residual entry not reclaimed.

**Notes / deliverable:**
- `docs/superpowers/notes/round-R6R7-baseline.md` (Task 1, generated)
- `docs/superpowers/notes/round-R6R7-residual.md` (Task 1, generated — the 25-entry work list)
- `docs/superpowers/notes/round-R6R7-sweep-raw.md` (Task 4, the raw second-pass run report)
- `docs/superpowers/notes/round-R6R7-new-verified.md` (Task 4, cross-checks — may be short)
- `docs/superpowers/notes/round-R6R7-delta.md` (Task 7)
- `docs/superpowers/notes/MANUAL-backlog.md` (Task 5 appends; Task 6 regenerates + groups + headers)

**Tests:**
- `tests/tracks/test_coalition.py` — Task 2 updates the `_tier_b_numeric_core` arity + adds a `payment_ok`-distinct-from-`core_ok` case.
- `tests/architect/test_formalize_second_pass.py` — Task 3, new: `prior_reason` threads into the user message; `--second-pass` selects the right entries; a stub `complete` produces the expected result.
- existing suites stay green; a stale-expected-value pin update is permitted only where a verdict legitimately moved.

---

## Task 1: Branch, baseline, residual work-list

**Files:**
- Create: `docs/superpowers/notes/round-R6R7-baseline.md` (generated), `docs/superpowers/notes/round-R6R7-residual.md` (generated)

**Interfaces:**
- Consumes: `scripts.snapshot_verdicts.main` (required `--out`), `scripts.round_gate.main` (`--baseline`).
- Produces: `round-R6R7-baseline.md` — the per-entry table every later task's gate runs against. `round-R6R7-residual.md` — the 25-entry Phase-6/7 work list.

- [ ] **Step 1: Branch off main**

```bash
git checkout main && git pull --ff-only 2>/dev/null; git checkout -b round-R6R7-final-classification
```

- [ ] **Step 2: Baseline snapshot**

```bash
PYTHONPATH=src python -m scripts.snapshot_verdicts corpus.json --out docs/superpowers/notes/round-R6R7-baseline.md
```

Confirm the effective in-scope distribution (override applied):

```bash
PYTHONPATH=src python -c "
import json, collections
c=json.load(open('corpus.json')); rows=c if isinstance(c,list) else c.get('entries',c)
eff=collections.Counter()
for e in rows:
    cat=str(e.get('category',''))
    if cat in ('Valuation','RL','Naive',''): continue
    eff[e.get('verdict_override') or e.get('z3_verdict') or e.get('verdict')]+=1
print(dict(eff))
"
```

Expected: `{'VERIFIED_TEMPLATE': 25, 'MANUAL': 62, 'VERIFIED': 18}`. If the numbers differ, STOP and reconcile against `git log` — the plan's residual list is keyed to this state.

- [ ] **Step 3: Generate the residual work-list**

```bash
PYTHONPATH=src python -c "
import json
c=json.load(open('corpus.json')); rows=c if isinstance(c,list) else c.get('entries',c)
out=['# R6-R7 residual work-list','','25 in-scope VERIFIED_TEMPLATE with no verdict_override. Each row: the Phase-6 hint / Phase-7 diagnosis seed is manual_diagnosis.obstruction if present, else the notes prefix.','','| paper_id | category | verdict | seed source | seed (truncated) |','|---|---|---|---|---|']
n=0
for e in sorted(rows, key=lambda x:(str(x.get('category')), str(x.get('paper_id')))):
    cat=str(e.get('category',''))
    if cat in ('Valuation','RL','Naive',''): continue
    if e.get('verdict_override'): continue
    v=e.get('z3_verdict') or e.get('verdict')
    if v not in ('VERIFIED_TEMPLATE','VERIFIED_SHAPE','UNKNOWN'): continue
    n+=1
    md=e.get('manual_diagnosis')
    if md: src, seed='manual_diagnosis.obstruction', md.get('obstruction','')
    else: src, seed='notes', (e.get('notes') or '')
    seed=seed.replace(chr(10),' ')[:160]
    out.append(f\"| {e.get('paper_id')} | {cat} | {v} | {src} | {seed} |\")
out.insert(2, f'({n} entries)')
open('docs/superpowers/notes/round-R6R7-residual.md','w').write(chr(10).join(out)+chr(10))
print(n, 'residual entries written')
"
```

Expected: `25 residual entries written`.

- [ ] **Step 4: Gate no-op check + commit**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R6R7-baseline.md corpus.json
```

Expected: `GATE: PASS`.

```bash
git add docs/superpowers/notes/round-R6R7-baseline.md docs/superpowers/notes/round-R6R7-residual.md
git commit -m "chore(R6-R7): branch + baseline + 25-entry residual work-list"
```

---

## Task 2: R5 carry-forward — `payment_ok` flag split + Tier A ceiling comment

**Files:**
- Modify: `src/tracks/track_coalition.py`
- Test: `tests/tracks/test_coalition.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `_tier_b_numeric_core(values, n, stated_payments) -> tuple[bool, bool, bool, list[str]]` — now `(core_ok, ir_ok, payment_ok, conditions)`. `core_ok` no longer folds in the payment check. `payment_ok` is `True` when `stated_payments is None` OR every `phi_i ≈ stated_payments[i]` (abs_tol 1e-6). `verify_coalition` consumes the 4-tuple.

- [ ] **Step 1: Update the failing tests**

In `tests/tracks/test_coalition.py`, the Tier B tests currently unpack a 3-tuple. Update them to 4-tuple and add one new case:

```python
def test_tier_b_returns_payment_ok_separately():
    # core + IR hold; stated payment is wrong -> core_ok stays True, payment_ok is False
    values = {
        frozenset(): 0.0, frozenset({1}): 1.0, frozenset({2}): 1.0,
        frozenset({1, 2}): 4.0,
    }
    core_ok, ir_ok, payment_ok, _ = _tier_b_numeric_core(
        values, n=2, stated_payments={1: 2.0, 2: 99.0})
    assert core_ok is True
    assert ir_ok is True
    assert payment_ok is False


def test_verify_coalition_payment_mismatch_is_counterexample_not_core():
    entry = {
        "paper_id": "x",
        "mechanism": {
            "shapley_formula_latex": _STD_SHAPLEY_LATEX,
            "coalition_n": 2,
            "coalition_values": {"": 0.0, "1": 1.0, "2": 1.0, "1,2": 4.0},
            "coalition_payments": {"1": 2.0, "2": 99.0},
        },
    }
    r = verify_coalition(entry)
    assert r.verdict == "COUNTEREXAMPLE"
    assert "payment" in r.notes.lower()
```

Also update the existing `test_tier_b_*` unpackings from `core_ok, ir_ok, conds = ...` to `core_ok, ir_ok, payment_ok, conds = ...`.

- [ ] **Step 2: Run — verify the arity change fails**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_coalition.py -k tier_b -v`
Expected: FAIL — `not enough values to unpack` / new tests undefined.

- [ ] **Step 3: Implement the split**

In `_tier_b_numeric_core` (`src/tracks/track_coalition.py`): stop doing `core_ok &= match` in the `stated_payments` loop; instead build a separate `payment_ok` (starts `True`, `&= match` per player), keep appending the payment condition lines to `conds`, and return `core_ok, ir_ok, payment_ok, conds`.

In `verify_coalition`:

```python
    core_ok, ir_ok, payment_ok, conds = _tier_b_numeric_core(values, n, stated_payments)
    tier_a_line = f"Tier A: {detail}"

    if core_ok and ir_ok and payment_ok:
        return VerificationResult(
            verdict="VERIFIED", category="Shapley", paper_id=pid, track=5,
            conditions=[tier_a_line, *conds], entry_specific=True,
            notes="Tier A (Shapley identity) + Tier B (core, IR, payment) all hold",
        )
    if not core_ok:
        violated = [c for c in conds if "VIOLATED" in c]
        return VerificationResult(
            verdict="COUNTEREXAMPLE", category="Shapley", paper_id=pid, track=5,
            conditions=[tier_a_line, *conds], entry_specific=True,
            notes="core violated: " + "; ".join(violated),
        )
    if not payment_ok:
        mism = [c for c in conds if "MISMATCH" in c]
        return VerificationResult(
            verdict="COUNTEREXAMPLE", category="Shapley", paper_id=pid, track=5,
            conditions=[tier_a_line, *conds], entry_specific=True,
            notes="stated payment != Shapley value: " + "; ".join(mism),
        )
    return _manual(pid, "core holds but individual rationality is violated — "
                        "check the paper's participation model")
```

Add above `_tier_a_symbolic_identity`:

```python
# ponytail: structural substring check — a numeric or other-letter scalar
# prefactor on the sum (e.g. "2\sum ...") passes the marginal-term + weight
# match. Inherent to a substring test; tighten to a parsed coefficient check
# only if a corpus entry ever exercises it. None does today.
```

- [ ] **Step 4: Run — all green**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_coalition.py -v`
Expected: all PASS (existing + 2 new).

- [ ] **Step 5: Gate + commit**

```bash
PYTHONPATH=src python -m verifier corpus.json | tail -3   # keyless, still runs
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R6R7-baseline.md corpus.json
```

Expected: `GATE: PASS` (no verdict moved — the 4 Shapley entries have no `coalition_payments`, so `payment_ok` is always `True` for them; they stay `MANUAL` via their override).

```bash
git add src/tracks/track_coalition.py tests/tracks/test_coalition.py
git commit -m "refactor(R6-R7): split payment_ok from core_ok in track_coalition; Tier A ceiling note"
```

---

## Task 3: Phase 6 mechanism — `prior_reason` hint injection + `--second-pass`

**Files:**
- Modify: `src/architect/formalize.py`
- Test: `tests/architect/test_formalize_second_pass.py` (new)

**Interfaces:**
- Consumes: `formalize._user_message`, `formalize.formalize_entry`, `formalize.formalize_with_retry`, `formalize.run_batch`, `formalize._select`.
- Produces:
  - `formalize_entry(entry, pdf_text, *, complete=llm_complete, concerns=None, prior_reason=None)` — when `prior_reason` is a non-empty string and `concerns` is falsy, it synthesizes `concerns = [{"field": "reformulation", "issue": f"{prior_reason} — try reframing around this: fine discrete grid for a continuous type / isolate the binding constraint / drop a provably-slack term"}]` before building the user message. If `concerns` is already set (the retry path), `prior_reason` is ignored.
  - `formalize_with_retry(entry, pdf_text, *, complete=llm_complete, prior_reason=None)` — threads `prior_reason` into its first `formalize_entry` call only (the retry already has real adversary concerns).
  - `run_batch(..., second_pass=False)` — when `True`, for each selected entry computes `pr = (entry.get("manual_diagnosis") or {}).get("obstruction") or entry.get("notes") or None` and passes it as `prior_reason`.
  - `main()` — `--second-pass` flag sets `second_pass=True`. `ARCHITECT_LLM_MODEL` env var already read at line ~383; confirm it reaches the `llm_complete` client (if `llm_complete` hard-codes a model, parameterize it from `os.environ.get("ARCHITECT_LLM_MODEL")`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/architect/test_formalize_second_pass.py
from architect import formalize


def test_prior_reason_threads_into_user_message():
    seen = {}
    def fake_complete(system, user, *, json_mode=False):
        seen["user"] = user
        return "{}"  # invalid AST -> formalize_entry returns None, fine for this assertion
    formalize.formalize_entry(
        {"category": "Stackelberg", "mechanism": {}},
        "paper text",
        complete=fake_complete,
        prior_reason="follower FOC is transcendental with no closed-form root",
    )
    assert "reformulation" in seen["user"]
    assert "transcendental with no closed-form root" in seen["user"]
    assert "provably-slack term" in seen["user"]


def test_prior_reason_ignored_when_concerns_present():
    seen = {}
    def fake_complete(system, user, *, json_mode=False):
        seen["user"] = user
        return "{}"
    formalize.formalize_entry(
        {"category": "Stackelberg", "mechanism": {}}, "t",
        complete=fake_complete,
        concerns=[{"field": "utility", "issue": "real concern"}],
        prior_reason="should not appear",
    )
    assert "real concern" in seen["user"]
    assert "should not appear" not in seen["user"]


def test_run_batch_second_pass_passes_notes_as_prior_reason(tmp_path, monkeypatch):
    import json
    corpus = [{"paper_id": "T1", "category": "Stackelberg",
               "notes": "Batch C: follower IR left null (fail-closed)",
               "mechanism": {}}]
    p = tmp_path / "c.json"
    p.write_text(json.dumps(corpus))
    captured = {}
    def fake_retry(entry, pdf_text, *, complete=None, prior_reason=None):
        captured["prior_reason"] = prior_reason
        return formalize.FormalizeResult("VERIFIED_TEMPLATE", None, [], 0, False, "")
    monkeypatch.setattr(formalize, "formalize_with_retry", fake_retry)
    monkeypatch.setattr(formalize, "pdf_text", lambda *_a, **_k: None)
    formalize.run_batch(str(p), ids="T1", second_pass=True, dry_run=False)
    assert "follower IR left null" in (captured["prior_reason"] or "")
```

- [ ] **Step 2: Run — verify failure**

Run: `PYTHONPATH=src:. pytest tests/architect/test_formalize_second_pass.py -v`
Expected: FAIL — `formalize_entry() got an unexpected keyword argument 'prior_reason'`.

- [ ] **Step 3: Implement**

`formalize_entry` — add the kwarg and the synthesis:

```python
def formalize_entry(entry, pdf_text, *, complete=llm_complete, concerns=None, prior_reason=None):
    if prior_reason and not concerns:
        concerns = [{
            "field": "reformulation",
            "issue": (f"{prior_reason} — try reframing around this: fine discrete "
                      "grid for a continuous type / isolate the binding constraint / "
                      "drop a provably-slack term"),
        }]
    user = _user_message(entry, pdf_text, concerns)
    try:
        raw = complete(FORMALIZE_SYSTEM_PROMPT, user, json_mode=True)
        return from_dict(json.loads(raw))
    except (json.JSONDecodeError, ASTSchemaError, KeyError, TypeError):
        return None
```

`formalize_with_retry` — add `prior_reason=None` to the signature; pass it to the FIRST `formalize_entry` call only (line ~299: `m = formalize_entry(entry, pdf_text, complete=complete, prior_reason=prior_reason)`). The VCG / Contract early-returns take no `prior_reason` (their dedicated paths don't use the generic user message) — document that in a one-line comment.

`run_batch` — add `second_pass=False` param; in the per-entry loop, before calling `formalize_with_retry`:

```python
        pr = None
        if second_pass:
            pr = (entry.get("manual_diagnosis") or {}).get("obstruction") or entry.get("notes") or None
        result = formalize_with_retry(entry, pt, complete=..., prior_reason=pr)
```

`main` — `ap.add_argument("--second-pass", action="store_true", help="inject each entry's prior failure reason as a reformulation hint")` and pass `second_pass=args.second_pass` to `run_batch`.

Model wiring: if `llm_complete` does not already honor `ARCHITECT_LLM_MODEL`, thread `os.environ.get("ARCHITECT_LLM_MODEL")` into the client construction. If it already does (check the `llm_complete` definition — likely in `src/architect/llm.py`), no change — just note it in the report.

- [ ] **Step 4: Run — all green**

Run: `PYTHONPATH=src:. pytest tests/architect/test_formalize_second_pass.py tests/architect/ -q`
Expected: PASS. Existing `tests/architect/` stays green.

- [ ] **Step 5: Keyless verifier + commit**

```bash
PYTHONPATH=src python -m verifier corpus.json | tail -3   # no API key, still runs
```

```bash
git add src/architect/formalize.py tests/architect/test_formalize_second_pass.py
git commit -m "feat(R6-R7): architect.formalize --second-pass with prior-reason hint injection"
```

---

## Task 4: Phase 6 — pin the model, run the second-pass sweep, hand-check flips

**Files:**
- Create: `docs/superpowers/notes/round-R6R7-sweep-raw.md`, `docs/superpowers/notes/round-R6R7-new-verified.md`
- Modify: `corpus.json` (`formalized_ast` + provenance on entries that produced an AST)

**Interfaces:**
- Consumes: `architect.formalize` CLI (`--second-pass`, `--ids`, `--report-dir`), `round_gate`, `round-R6R7-residual.md`.
- Produces: `formalized_ast` on Phase-6 entries; `round-R6R7-new-verified.md` (cross-checks); `round-R6R7-sweep-raw.md` (raw run).

- [ ] **Step 1: Probe the NVIDIA endpoint and pin the model**

```bash
PYTHONPATH=src python -c "
import os
from architect.llm import _client  # adjust to the actual OpenAI-compatible client factory
try:
    cl=_client()
    for m in cl.models.list().data: print(m.id)
except Exception as e:
    print('list unavailable:', e)
"
```

Pick the largest instruct model that is NOT `gpt-oss-20b` (e.g. a 70B/120B-class `*-instruct` / `llama-3.*-70b` / `nemotron` model the endpoint offers). Record the exact id and the reasoning in `round-R6R7-sweep-raw.md` header. If the endpoint serves only `gpt-oss-20b`, record "no larger model available on the endpoint; second pass runs gpt-oss-20b with hint injection only (weakened reclaim odds)" and proceed — the hint injection is still the substantive change.

- [ ] **Step 2: Run the second-pass sweep over the 25 residual entries**

```bash
IDS=$(PYTHONPATH=src python -c "
rows=[l for l in open('docs/superpowers/notes/round-R6R7-residual.md') if l.startswith('| ') and 'paper_id' not in l and '---' not in l]
print(','.join(l.split('|')[1].strip() for l in rows))
")
ARCHITECT_LLM_MODEL="<pinned-model-id>" ARCHITECT_LLM_TIMEOUT_S=300 \
  PYTHONPATH=src python -m architect.formalize corpus.json --second-pass --ids "$IDS" \
  --report-dir docs/superpowers/notes 2>&1 | tee docs/superpowers/notes/round-R6R7-sweep-raw.md
```

Record whatever it emits. Expected per the spec: a handful of flips, most entries still `VERIFIED_TEMPLATE` (the Batch-C/D/E "no IR / null FOC / multi-dim type" walls are real).

- [ ] **Step 3: Read the post-sweep verdicts for the 25**

```bash
PYTHONPATH=src python -m verifier corpus.json 2>/dev/null | grep -A2 -F -f <(echo "$IDS" | tr ',' '\n')
```

- [ ] **Step 4: Hand-check EVERY entry that flipped to `VERIFIED` or `COUNTEREXAMPLE`**

For each flip: derive the IC/FOC/IR gap by hand with signs, OR confirm a second track agrees, OR inspect the Z3/SMT model, OR cite the theorem. Append to `docs/superpowers/notes/round-R6R7-new-verified.md`:

```markdown
## <paper_id> (<category>) — R6-R7

**What the second pass now handles:** <what the new AST captured that R1-R5 missed — e.g. "the follower IR the Batch-C review left null is stated in Def 1; the larger model transcribed it, and the scalar FOC closes">
**Independent check:** <hand-derived gap with signs / second track / Z3 model / cited theorem>
```

If a hand-check is not clean → revert that entry to its baseline verdict (fail closed) and record why in the sweep-raw notes. If 0 entries flipped, write `round-R6R7-new-verified.md` with a single header line: `_No entries flipped in the R6 second pass. All 25 residual entries proceed to Phase 7 diagnosis._`

- [ ] **Step 5: Commit the reclaim**

```bash
PYTHONPATH=src python -m verifier corpus.json | tail -3       # keyless
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R6R7-baseline.md corpus.json
```

Expected: `GATE: PASS`, `VERIFIED` count up by the number of hand-checked flips.

```bash
git add corpus.json docs/superpowers/notes/round-R6R7-sweep-raw.md docs/superpowers/notes/round-R6R7-new-verified.md
git commit -m "feat(R6-R7): Phase 6 second-pass sweep — <N> reclaimed to VERIFIED (hand-checked)"
```

---

## Task 5: Phase 7 — flip every residual to diagnosed `MANUAL`

**Files:**
- Create: `scripts/r6r7_diagnose.py`
- Modify: `corpus.json` (`verdict_override` + `manual_diagnosis` on non-reclaimed residual entries), `docs/superpowers/notes/MANUAL-backlog.md` (append)

**Interfaces:**
- Consumes: `architect.formalize.write_manual_diagnosis(entry, *, round_, track, limit, mechanism, obstruction, human_task, today=None)`, `architect.formalize.append_backlog_paragraph(entry, *, backlog_path=MANUAL_BACKLOG_PATH)`.
- Produces: every in-scope entry terminal; `MANUAL-backlog.md` gains one paragraph per newly-flipped entry.

- [ ] **Step 1: List what is still non-terminal**

```bash
PYTHONPATH=src python -c "
import json
c=json.load(open('corpus.json')); rows=c if isinstance(c,list) else c.get('entries',c)
for e in rows:
    cat=str(e.get('category',''))
    if cat in ('Valuation','RL','Naive',''): continue
    if e.get('verdict_override'): continue
    v=e.get('z3_verdict') or e.get('verdict')
    if v in ('VERIFIED_TEMPLATE','VERIFIED_SHAPE','UNKNOWN'):
        print(e['paper_id'], cat, v, '::', (e.get('notes') or '')[:180].replace(chr(10),' '))
"
```

This is the Phase 7 work list (25 minus Task 4 flips).

- [ ] **Step 2: Write `scripts/r6r7_diagnose.py`**

A committed script holding one `DIAG` entry per Phase-7 residual so the diagnoses are reviewable as code. Each `limit` / `mechanism` / `obstruction` / `human_task` string is **derived from that entry's `notes` field and its source PDF** (the Batch-C/D/E reviews already name the missing field and why it was left null) — **not invented**. Shape (one worked example; fill the rest from each entry's notes/PDF):

```python
"""R6-R7 Phase 7: flip every non-reclaimed residual VERIFIED_TEMPLATE to diagnosed MANUAL.

Each DIAG value is transcribed from the entry's `notes` (Batch-C/D/E fail-closed
review) and its source PDF. Not invented. Run once: python scripts/r6r7_diagnose.py
"""
import json
from architect.formalize import write_manual_diagnosis, append_backlog_paragraph

DIAG = {
  "1811_12082": dict(
     track=1,
     mechanism="<one line: leader/follower roles + what the follower chooses>",
     limit="Stackelberg: no follower IR / participation constraint stated in the paper",
     obstruction="Batch-C review left ir_follower_latex null (fail-closed) — the paper "
                 "proves the leader's problem but never writes U_follower >= 0; the "
                 "generic template IR check is not a statement about this mechanism.",
     human_task="read <paper> §<x>; if a participation floor is implied by the outside "
                "option, transcribe it as ir_follower_latex, then Track 1's scalar FOC "
                "path can run."),
  # ... one entry per Phase-7 residual, every string from its notes + PDF
}

def main():
    c = json.load(open("corpus.json"))
    rows = c if isinstance(c, list) else c.get("entries", c)
    by = {e["paper_id"]: e for e in rows}
    for pid, d in DIAG.items():
        e = by[pid]
        assert not e.get("verdict_override"), f"{pid} already overridden"
        write_manual_diagnosis(e, round_="R7", today="2026-09-06", **d)
        append_backlog_paragraph(e)
    json.dump(c, open("corpus.json", "w"), indent=2, ensure_ascii=False)
    open("corpus.json", "a").write("\n")
    print(f"{len(DIAG)} entries flipped to diagnosed MANUAL")

if __name__ == "__main__":
    main()
```

`write_manual_diagnosis` raises `ValueError` on an empty `limit` / `obstruction` / `human_task`, so a half-filled `DIAG` entry fails loudly. Every `human_task` is concrete (which field to transcribe from which section, or which lemma to prove).

- [ ] **Step 3: Run + verify terminal + gate**

```bash
PYTHONPATH=src python scripts/r6r7_diagnose.py
PYTHONPATH=src python -c "
import json, collections
c=json.load(open('corpus.json')); rows=c if isinstance(c,list) else c.get('entries',c)
eff=collections.Counter()
for e in rows:
    cat=str(e.get('category',''))
    if cat in ('Valuation','RL','Naive',''): continue
    eff[e.get('verdict_override') or e.get('z3_verdict') or e.get('verdict')]+=1
print(dict(eff))
assert eff.get('VERIFIED_TEMPLATE',0)==0 and eff.get('VERIFIED_SHAPE',0)==0 and eff.get('UNKNOWN',0)==0, eff
print('TERMINAL: in-scope UNKNOWN=0, VERIFIED_TEMPLATE=0, VERIFIED_SHAPE=0')
"
PYTHONPATH=src python -m verifier corpus.json | tail -3            # keyless
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R6R7-baseline.md corpus.json
```

Expected: the assert passes; `GATE: PASS`; the verifier no longer prints any "missing from MANUAL-backlog.md" warning.

- [ ] **Step 4: Commit**

```bash
git add corpus.json docs/superpowers/notes/MANUAL-backlog.md scripts/r6r7_diagnose.py
git commit -m "feat(R6-R7): Phase 7 — flip <M> residual VERIFIED_TEMPLATE to diagnosed MANUAL; UNKNOWN/TEMPLATE/SHAPE -> 0"
```

---

## Task 6: `MANUAL-backlog.md` finalization — regenerate, group, summary header

**Files:**
- Create: `scripts/build_manual_backlog.py`
- Modify: `docs/superpowers/notes/MANUAL-backlog.md`

**Interfaces:**
- Consumes: the finished `corpus.json` (`manual_diagnosis` on every `MANUAL` entry).
- Produces: `MANUAL-backlog.md` — one paragraph per `MANUAL` entry, grouped by obstruction family, with a summary header, **reproducible from `corpus.json`**. This is the program deliverable.

- [ ] **Step 1: Write `scripts/build_manual_backlog.py`**

Regenerate the whole file from `corpus.json`'s `manual_diagnosis` dicts so format is uniform by construction, then group and add the header:

```python
"""Regenerate MANUAL-backlog.md from corpus.json's manual_diagnosis dicts.
Single source of truth: the corpus. Run: python scripts/build_manual_backlog.py
"""
import json, collections

c = json.load(open("corpus.json"))
rows = c if isinstance(c, list) else c.get("entries", c)
manual = [e for e in rows if e.get("verdict_override") == "MANUAL"]

FAMILIES = [
  ("no-screening-IC", lambda d: "no adverse-selection screening IC" in d["limit"]
       or "screening IC in the paper" in d["obstruction"]),
  ("vector-follower-decision", lambda d: "vector follower decision" in d["limit"]),
  ("transcendental-FOC-no-closed-form", lambda d: "transcendental" in d["limit"]
       and "closed-form" in d["limit"]),
  ("opaque-function-in-utility", lambda d: "unsupported SymPy node" in d["limit"]
       or "opaque" in d["limit"] or "undefined" in d["limit"]),
  ("RL-or-opaque-allocation", lambda d: "RL-policy" in d["limit"]
       or "opaque-algorithm allocation" in d["limit"]),
  ("no-follower-IR-stated", lambda d: "no follower IR" in d["limit"]
       or "participation constraint" in d["limit"]),
  ("coalition-value-not-instantiable", lambda d: d["track"] == 5),
]
def fam(d):
    for name, pred in FAMILIES:
        try:
            if pred(d):
                return name
        except KeyError:
            pass
    return "other"

buckets = collections.defaultdict(list)
for e in manual:
    buckets[fam(e["manual_diagnosis"])].append(e)

out = ["# MANUAL Backlog", "",
       "One paragraph per corpus entry that no automated track in the pipeline can decide.",
       "Each names the mechanism, the obstruction (with the track and the specific limit hit),",
       "and the concrete human task to close it. Regenerated from corpus.json — do not hand-edit;",
       "edit the entry's manual_diagnosis and re-run scripts/build_manual_backlog.py.", "",
       f"**Total: {len(manual)} MANUAL entries.** Recurring obstruction families:", ""]
order = [n for n, _ in FAMILIES] + ["other"]
for name in order:
    ids = sorted(e["paper_id"] for e in buckets.get(name, []))
    if ids:
        out.append(f"- **{name}** ({len(ids)}): {', '.join(ids)}")
out.append("")
for name in order:
    grp = buckets.get(name, [])
    if not grp:
        continue
    out.append(f"## Family: {name}\n")
    for e in sorted(grp, key=lambda x: x["paper_id"]):
        d = e["manual_diagnosis"]
        out += [f"### {e['paper_id']} ({e.get('category','')}) — {d['round']}", "",
                f"**Mechanism:** {d['mechanism']}",
                f"**Obstruction:** {d['obstruction']} (Track {d['track']}: {d['limit']})",
                f"**Human task:** {d['human_task']}",
                f"**Diagnosed:** {d['date']}", ""]
open("docs/superpowers/notes/MANUAL-backlog.md", "w").write("\n".join(out).rstrip() + "\n")
print(f"{len(manual)} entries, "
      f"{sum(1 for k in buckets if buckets[k])} families "
      f"(other: {len(buckets.get('other', []))})")
```

- [ ] **Step 2: Run + eyeball the `other` bucket**

```bash
PYTHONPATH=src python scripts/build_manual_backlog.py
grep -A20 "## Family: other" docs/superpowers/notes/MANUAL-backlog.md | head -40
```

If `other` is large (> ~8), add a family predicate for the next recurring `limit` phrasing and re-run. A few genuinely-singleton obstructions in `other` is fine.

- [ ] **Step 3: Spot-check 5 paragraphs against their pre-R6R7 wording**

```bash
git show HEAD~5:docs/superpowers/notes/MANUAL-backlog.md | grep -A5 "## 2408_13223\|## Khan2019edge\|## Lim2020edge_collab\|## Wang2022blockchain\|## 2102_03401"
```

The regenerated paragraphs are built from the same `manual_diagnosis` dicts the earlier `append_backlog_paragraph` calls wrote, so they should say the same thing. If a paragraph lost information that was in the old prose but NOT in the dict, patch that entry's `manual_diagnosis` in `corpus.json` and re-run Step 1 (the dict is the source of truth; the backlog must be reproducible from it).

- [ ] **Step 4: Gate + commit**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R6R7-baseline.md corpus.json
```

Expected: `GATE: PASS` (no corpus change — backlog-only).

```bash
git add docs/superpowers/notes/MANUAL-backlog.md scripts/build_manual_backlog.py
git commit -m "docs(R6-R7): finalize MANUAL-backlog.md — regenerated from corpus, grouped by obstruction family, summary header"
```

---

## Task 7: Delta note + spec "Landed" paragraph + merge

**Files:**
- Create: `docs/superpowers/notes/round-R6R7-delta.md`
- Modify: `docs/superpowers/specs/2026-09-02-zero-unknown-program-design.md` (§R6–R7 "Landed" paragraph; §"End state" table if the final numbers differ from the projection)

**Interfaces:**
- Consumes: `round-R6R7-baseline.md`, `round-R6R7-new-verified.md`, the final `verifier` output.
- Produces: `round-R6R7-delta.md` (mirrors `round-R5-delta.md` structure); the spec's terminal-state record.

- [ ] **Step 1: Write `round-R6R7-delta.md`**

Mirror `docs/superpowers/notes/round-R5-delta.md`:

```markdown
# Round R6–R7 — Second-formalizer pass + honesty gate — Delta

**Landed 2026-09-06.** Branch `round-R6R7-final-classification`, <k> commits off `main` @ `<sha>`.
Plan: `docs/superpowers/plans/2026-09-06-R6-R7-final-classification.md`.

## In-scope distribution — before / after

| Verdict | Baseline | After R6–R7 | Δ |
|---|---|---|---|
| VERIFIED (entry-specific) | 18 | <18+N> | +<N> |
| MANUAL | 62 | <62 + (25-N)> | +<25-N> |
| VERIFIED_TEMPLATE | 25 | **0** | −25 |
| UNKNOWN | 0 | 0 | — |
| VERIFIED_SHAPE | 0 | 0 | — |

## Phase 6 — reclaimed
- Model: `<pinned id>` (largest instruct model on the .env NVIDIA endpoint) / or "gpt-oss-20b, hint-injection only — no larger model available".
- <N> entries reclaimed to VERIFIED, each hand-checked (see round-R6R7-new-verified.md): <one-liners>
- <or "0 flips — the Batch-C/D/E walls (no IR / null FOC / multi-dim type) are real math/spec gaps, not formalization misses">

## Phase 7 — diagnosed
- <25-N> entries flipped VERIFIED_TEMPLATE → MANUAL with full manual_diagnosis.
- Recurring families: <the buckets from build_manual_backlog.py with counts>

## Deliverable
- `MANUAL-backlog.md` regenerated from corpus.json's manual_diagnosis dicts — <total> paragraphs, grouped into <F> obstruction families, summary header. Reproducible: `python scripts/build_manual_backlog.py`.

## Carry-forward from R5 (folded in)
- track_coalition.py: payment_ok split from core_ok (stated-payment mismatch → its own COUNTEREXAMPLE path); Tier A structural-check ceiling documented.

## R8 handoff
- In-scope VERIFIED via verify_from_ast: <count>. UNKNOWN = 0, VERIFIED_TEMPLATE = 0, VERIFIED_SHAPE = 0 — the program's hard exit criterion is met. R8 is the ARCHITECT_AST_VERIFY default flip + docs.
```

- [ ] **Step 2: Spec "Landed" paragraph**

Append to the spec's §R6–R7 section (mirroring the R2/R3/R4/R5 "Landed" paragraphs):

```markdown
**Landed 2026-09-06:** Phase 6 ran `architect.formalize --second-pass` (model
`<pinned>`, per-entry prior-reason hint injected via the existing `concerns`
path) over the 25 residual `VERIFIED_TEMPLATE` entries — **<N> reclaimed to
hand-checked `VERIFIED`** (<one-liners>). Phase 7 flipped the remaining <25-N> to
`MANUAL` with full `manual_diagnosis` (recurring families: <list>). In-scope
`VERIFIED_TEMPLATE` 25 → 0, `VERIFIED_SHAPE` 0 → 0, `UNKNOWN` 0 → 0 — **the
program's hard exit criterion is met.** `MANUAL-backlog.md` regenerated from
`corpus.json` (`scripts/build_manual_backlog.py`), <total> paragraphs in <F>
obstruction families. Also folded in the two R5 carry-forward findings
(`payment_ok` flag split; Tier A ceiling note). Merge commit `<sha>`. Delta:
`docs/superpowers/notes/round-R6R7-delta.md`.
```

Update the §"End state (after R8)" table only if the final `VERIFIED` / `MANUAL` counts land outside the projected `~70–85` / `~15–25` ranges — if so, replace the projection with the actual and add a one-line note.

- [ ] **Step 3: Whole-branch review + merge**

Invoke `superpowers:requesting-code-review` for the whole branch. Address CRITICAL/HIGH. Then (the merge is a controller action + a stop point — present it first):

```bash
git checkout main && git merge --no-ff round-R6R7-final-classification -m "Merge branch 'round-R6R7-final-classification' — R6–R7 second-formalizer pass + honesty gate

<N> reclaimed to VERIFIED, <25-N> diagnosed MANUAL. In-scope UNKNOWN/VERIFIED_TEMPLATE/VERIFIED_SHAPE all 0 — the zero-UNKNOWN program's hard exit criterion is met. MANUAL-backlog.md finalized as the human deliverable."
```

- [ ] **Step 4: Fill the merge SHA**

```bash
git rev-parse --short HEAD
```

Replace `<sha>` in `round-R6R7-delta.md` + the spec §R6–R7 Landed paragraph, commit:

```bash
git add docs/superpowers/notes/round-R6R7-delta.md docs/superpowers/specs/2026-09-02-zero-unknown-program-design.md
git commit -m "docs(R6-R7): fill merge commit SHA in delta + program-spec"
```

---

## Self-Review

**1. Spec coverage:**
- §R6–R7 "Phase 6 — fresh larger model + per-entry reason injected as reformulation hint, on the 25 residual" → Task 3 (mechanism) + Task 4 (pin model, sweep, hand-check).
- §R6–R7 "`verify_from_ast` runs the real solver; every flip hand-checked exactly as R2–R5" → Task 4 Step 4 + `round-R6R7-new-verified.md`.
- §R6–R7 "Phase 7 — every residual `VERIFIED_TEMPLATE`/`SHAPE`/`UNKNOWN` → `MANUAL` with full `manual_diagnosis`" → Task 5.
- §R6–R7 "`MANUAL-backlog.md` finalization — audit ~62, group by family, summary header" → Task 6.
- §R6–R7 "folded in: the two R5 carry-forward findings" → Task 2.
- §R6–R7 hard exit criterion (`UNKNOWN`/`VERIFIED_TEMPLATE`/`VERIFIED_SHAPE` all 0 in-scope) → Task 5 Step 3 assert + Task 7 delta.
- Cross-round invariants: baseline (Task 1), monotone gate (every task's final step), every-flip-cross-checked (Task 4 + `new-verified.md`), MANUAL-carries-a-reason (Task 5 via `write_manual_diagnosis`, which raises on empty `limit`/`obstruction`/`human_task`), formalizer-not-a-verify-dependency (Tasks 2–5 each end with a keyless `verifier` run; no `architect` import added to Track/verifier module tops), fail-closed (Task 4 Step 4 revert rule), branch-per-round (Task 1 Step 1, Task 7 Step 3).

**2. Placeholder scan:** `<pinned-model-id>` / `<N>` / `<25-N>` / `<sha>` are execution-time values, each paired with the command that produces it (Task 4 Step 1 probe; `git rev-parse`; the verdict count). The Task 5 `DIAG` dict is a *shape* with one worked example (`1811_12082`) and the explicit rule "text from its notes + PDF, not invented" — the per-entry strings are genuinely not knowable until the implementer reads each `notes` field and PDF, and inventing them here would violate the "declared not inferred" invariant. `write_manual_diagnosis` raises on an empty `limit`/`obstruction`/`human_task`, so a half-filled `DIAG` fails loudly rather than shipping a placeholder. No "TODO" / "add error handling" / "similar to Task N".

**3. Type consistency:** `_tier_b_numeric_core` 3-tuple → 4-tuple is applied in Task 2 at both the definition and the `verify_coalition` call site, and the existing test unpackings are updated in the same task. `formalize_entry(..., prior_reason=None)` / `formalize_with_retry(..., prior_reason=None)` / `run_batch(..., second_pass=False)` signatures introduced in Task 3 are consumed by the Task 4 CLI invocation (`--second-pass --ids`). `write_manual_diagnosis(entry, *, round_, track, limit, mechanism, obstruction, human_task, today=None)` and `append_backlog_paragraph(entry, *, backlog_path=...)` are used in Task 5 exactly as defined in `src/architect/formalize.py` (~lines 462, 490). `round_="R7"` is consistent across Task 5 and the family grouping in Task 6.

**4. Ambiguity:** "reclaim what it can" is made concrete by Task 4 Step 4's four acceptable hand-check types + the fail-closed revert. "Different larger model" is pinned by Task 4 Step 1's probe with an explicit fallback rule when the endpoint has nothing larger. "Audit the backlog" is made concrete by Task 6's regenerate-from-corpus approach (format uniform by construction) + the Step 3 spot-check against the pre-round wording so no information is silently lost.
