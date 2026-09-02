# LLM Formalizer — Round 1 (Pipeline + Tests) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and test the batch pipeline that formalizes corpus entries into `Mechanism` ASTs, verifies them with the real solver, adversarially self-checks each proof, and reconciles the result with the existing LaTeX-path verdict — without running the corpus sweep.

**Architecture:** A new `src/architect/formalize.py` batch tool: per entry, an LLM reads the corpus mechanism dict + source PDF text and emits a JSON AST; `verify_from_ast` runs the real Track 1/2/3/4 solver; a second LLM pass adversarially inspects the AST against the paper; one retry on a concern or a solver counterexample; still-flagged ⇒ `UNKNOWN` + human queue. Successful ASTs serialize into `corpus.json` (`formalized_ast` + `formalization_meta`). `verify(entry)` prefers a stored AST (deterministic, no API key) and reconciles it with the LaTeX path via a fixed conflict table. Round 1 runs the pipeline only against synthetic fixtures + a 5-entry smoke set.

**Tech Stack:** Python 3, pytest, existing `architect.llm.llm_complete` (OpenAI-wire, provider via env), `pdfminer.six` (already installed), the existing `architect.ast` / `architect.serialize` / `architect.ast_verify` / `verifier` modules.

**Spec:** `docs/superpowers/specs/2026-08-31-llm-formalizer-design.md` (R1 feature spec), nested under `docs/superpowers/specs/2026-09-02-zero-unknown-program-design.md` (the R1–R8 program). This plan is **Round 1 (R1)** of that program: it builds the formalization engine; R2/R3 run the corpus sweep.

## Global Constraints

- Run tests from repo root with `PYTHONPATH=src`. The suite is **262 passed / 3 xfailed / 0 failed** now and stays 0-failed at every task end.
- Tests marked `@pytest.mark.llm` are excluded from the default run and only execute when `ARCHITECT_LLM_SMOKE=1` and an API key are both set. Register the marker in `pyproject.toml` so an unmarked default run makes no network calls.
- `PYTHONPATH=src python -m verifier corpus.json` must stay reproducible with **no API key set** — the LLM is a build step, never invoked inside `verify(entry)`.
- Round 1 corpus movement is bounded to the ≤5 smoke entries and is **monotone**: a smoke entry may only move to a better-or-equal verdict versus the pre-round baseline (`VERIFIED` > `VERIFIED_TEMPLATE` / `VERIFIED_SHAPE` > `UNKNOWN` > `UNSUPPORTED`; `COUNTEREXAMPLE` is not "better" and only lands with a hand-checked justification). No non-smoke entry's verdict changes. Every smoke flip is hand-checked and recorded in `docs/superpowers/notes/formalize-run-<date>.md` before the commit that writes it.
- The formalizer **never guesses**: malformed LLM JSON, an `ASTSchemaError`, or an unknown node tag ⇒ return `None` ⇒ `UNKNOWN`. No partial AST is verified.
- The adversary pass is **one-directional**: it can block a `VERIFIED` (→ retry → `UNKNOWN`); it can never turn an `UNKNOWN`/`COUNTEREXAMPLE` into a `VERIFIED`.
- Commit after every task. Branch `llm-formalizer-round1` off `main` (already created; the spec commit `ecf3f12` is its first commit). Do not push, do not open a PR. Stop at the last green commit.
- The untracked `docs/superpowers/plans/2026-08-30-fl-simulation-validation.md` is **not** part of this work — never `git add` it.

## Conflict-rule table (single source of truth for `_reconcile`)

| LaTeX-path verdict | LLM-path verdict | `_reconcile` returns |
|---|---|---|
| `VERIFIED_TEMPLATE` / `VERIFIED_SHAPE` / `UNKNOWN` / `UNSUPPORTED` | `VERIFIED` (`entry_specific=True`) | `(llm, flagged=False)` — LLM wins, entry flips |
| `VERIFIED_TEMPLATE` / `VERIFIED_SHAPE` / `UNKNOWN` / `UNSUPPORTED` | `COUNTEREXAMPLE` | `(llm, flagged=True)` — LLM wins, listed for review |
| `VERIFIED` (`entry_specific=True`) | `VERIFIED` (`entry_specific=True`) | `(latex, flagged=False)` — agree, keep LaTeX result |
| `VERIFIED` (`entry_specific=True`) | `COUNTEREXAMPLE` / `UNKNOWN` / `UNSUPPORTED` | `(latex, flagged=True)` — existing proof stands, human decides |
| `COUNTEREXAMPLE` | `VERIFIED` (`entry_specific=True`) | `(latex, flagged=True)` — existing counterexample stands, human decides |
| `COUNTEREXAMPLE` | anything else | `(latex, flagged=False)` — no upgrade, keep LaTeX result |
| any | `UNKNOWN` (and LaTeX not `VERIFIED`/`COUNTEREXAMPLE`) | `(latex, flagged=False)` — no improvement, keep LaTeX result |

A non-entry-specific LLM `VERIFIED` is treated as no upgrade — keep the LaTeX result.

---

## File Structure

| File | Responsibility | This plan |
|---|---|---|
| `src/architect/ast.py` | AST node dataclasses | Task 1 — add `to_dict` / `from_dict` |
| `src/architect/pdf_text.py` | Resolve `paper_id` → PDF, extract text | Task 2 (new) |
| `src/architect/formalize.py` | Formalizer + adversary + retry driver + batch CLI | Tasks 3–6 (new) |
| `src/verifier.py` | `verify()` prefers stored AST; `_reconcile` | Task 7 |
| `tests/architect/test_ast_serde.py` | `to_dict`/`from_dict` round-trip | Task 1 (new) |
| `tests/architect/test_pdf_text.py` | id normalization + extraction | Task 2 (new) |
| `tests/architect/test_formalize.py` | formalizer/adversary/retry with stubbed LLM | Tasks 3–5 (new) |
| `tests/architect/test_formalize_cli.py` | batch CLI write-back + report, stubbed LLM | Task 6 (new) |
| `tests/verifier/test_reconcile.py` | every conflict-table row | Task 7 (new) |
| `tests/architect/test_formalize_smoke.py` | 5-entry end-to-end, `@pytest.mark.llm` | Task 8 (new) |
| `docs/superpowers/notes/formalize-run-<date>.md` | generated by the smoke run | Task 8 |
| `corpus.json` | ≤5 smoke entries gain `formalized_ast` + `formalization_meta` | Task 8 |

---

## Task 1: AST dict serialization (`to_dict` / `from_dict`)

**Files:**
- Modify: `src/architect/ast.py`
- Test: `tests/architect/test_ast_serde.py` (create)

**Interfaces:**
- Consumes: the existing node dataclasses `Const, Sym, Unknown, Sum, Prod, Pow, Func, IndexedFamily, AllocHighest, AllocTopK, AllocWeightedWelfare, Mechanism` and `validate_ast`, `validate_alloc`, `ASTSchemaError`.
- Produces:
  - `to_dict(node) -> dict` — JSON-safe. Every node dict carries a `"t"` key = the class name; child nodes recurse; lists map element-wise. `Mechanism` → `{"t": "Mechanism", "category": str, "utility": <node>, "payment": <node>, "ic": <node>, "ir": <node>, "params": dict, "type_space": list, "allocation": <alloc-node|null>, "meta": dict}` (drop `provenance`).
  - `from_dict(d) -> object` — inverse. Unknown `"t"` value ⇒ raise `ASTSchemaError`. After building a `Mechanism`, call `validate_ast` on `utility/payment/ic/ir` and `validate_alloc` on `allocation` when non-null; let those raise on bad input.

- [ ] **Step 1: Write the failing test**

```python
# tests/architect/test_ast_serde.py
import pytest
from architect.ast import (
    Const, Sym, Sum, Prod, Pow, Func, IndexedFamily,
    AllocHighest, AllocTopK, AllocWeightedWelfare, Mechanism,
    to_dict, from_dict, ASTSchemaError,
)


def _sample_mechanism():
    return Mechanism(
        category="Contract",
        utility=Sum([Prod([Sym("theta"), Sym("R")]), Func("ln", Sym("P"))]),
        payment=Sym("P"),
        ic=Sum([Sym("a"), Const(-1.0)]),
        ir=Sym("a"),
        params={"num_types": 3},
        type_space=[0.2, 0.5, 0.9],
        allocation=None,
        meta={"num_types": 3},
    )


def test_roundtrip_full_mechanism():
    m = _sample_mechanism()
    assert from_dict(to_dict(m)) == m


def test_roundtrip_every_node_type():
    m = Mechanism(
        category="VCG",
        utility=Pow(Sym("x"), 2),
        payment=IndexedFamily("p", "i", ["a", "b"]),
        ic=Const(0.0),
        ir=Const(0.0),
        allocation=AllocWeightedWelfare(["1", "2"]),
    )
    assert from_dict(to_dict(m)) == m
    m2 = Mechanism(category="VCG", utility=Const(0.0), payment=Const(0.0),
                   ic=Const(0.0), ir=Const(0.0), allocation=AllocTopK(3))
    assert from_dict(to_dict(m2)) == m2
    m3 = Mechanism(category="VCG", utility=Const(0.0), payment=Const(0.0),
                   ic=Const(0.0), ir=Const(0.0), allocation=AllocHighest())
    assert from_dict(to_dict(m3)) == m3


def test_to_dict_is_json_safe():
    import json
    d = to_dict(_sample_mechanism())
    assert json.loads(json.dumps(d)) == d


def test_from_dict_unknown_tag_raises():
    with pytest.raises(ASTSchemaError):
        from_dict({"t": "Bogus", "value": 1})


def test_from_dict_validates_mechanism_subtrees():
    bad = {
        "t": "Mechanism", "category": "Contract",
        "utility": {"t": "Sum", "terms": []},  # empty Sum -> validate_ast raises
        "payment": {"t": "Const", "value": 0.0},
        "ic": {"t": "Const", "value": 0.0},
        "ir": {"t": "Const", "value": 0.0},
        "params": {}, "type_space": [], "allocation": None, "meta": {},
    }
    with pytest.raises(ASTSchemaError):
        from_dict(bad)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/architect/test_ast_serde.py -v`
Expected: FAIL — `ImportError: cannot import name 'to_dict'`.

- [ ] **Step 3: Write minimal implementation**

Append to `src/architect/ast.py`:

```python
_NODE_TAGS = {
    "Const": ("value",),
    "Sym": ("name",),
    "Unknown": ("name",),
    "Sum": ("terms",),
    "Prod": ("factors",),
    "Pow": ("base", "exp"),
    "Func": ("name", "arg"),
    "IndexedFamily": ("name", "index", "over"),
    "AllocHighest": (),
    "AllocTopK": ("k",),
    "AllocWeightedWelfare": ("weights",),
}
_TAG_TO_CLS = {
    "Const": Const, "Sym": Sym, "Unknown": Unknown, "Sum": Sum, "Prod": Prod,
    "Pow": Pow, "Func": Func, "IndexedFamily": IndexedFamily,
    "AllocHighest": AllocHighest, "AllocTopK": AllocTopK,
    "AllocWeightedWelfare": AllocWeightedWelfare,
}


def _enc(v):
    if type(v).__name__ in _NODE_TAGS:
        return to_dict(v)
    if isinstance(v, list):
        return [_enc(x) for x in v]
    return v


def to_dict(node):
    tag = type(node).__name__
    if tag == "Mechanism":
        return {
            "t": "Mechanism", "category": node.category,
            "utility": to_dict(node.utility), "payment": to_dict(node.payment),
            "ic": to_dict(node.ic), "ir": to_dict(node.ir),
            "params": dict(node.params), "type_space": list(node.type_space),
            "allocation": to_dict(node.allocation) if node.allocation is not None else None,
            "meta": dict(node.meta),
        }
    if tag not in _NODE_TAGS:
        raise ASTSchemaError(f"cannot serialize {tag}")
    out = {"t": tag}
    for f in _NODE_TAGS[tag]:
        out[f] = _enc(getattr(node, f))
    return out


def _dec(v):
    if isinstance(v, dict) and "t" in v:
        return from_dict(v)
    if isinstance(v, list):
        return [_dec(x) for x in v]
    return v


def from_dict(d):
    if not isinstance(d, dict) or "t" not in d:
        raise ASTSchemaError(f"not a node dict: {d!r}")
    tag = d["t"]
    if tag == "Mechanism":
        m = Mechanism(
            category=d["category"],
            utility=from_dict(d["utility"]), payment=from_dict(d["payment"]),
            ic=from_dict(d["ic"]), ir=from_dict(d["ir"]),
            params=dict(d.get("params", {})), type_space=list(d.get("type_space", [])),
            allocation=(from_dict(d["allocation"]) if d.get("allocation") is not None else None),
            meta=dict(d.get("meta", {})),
        )
        for sub in (m.utility, m.payment, m.ic, m.ir):
            validate_ast(sub)
        if m.allocation is not None:
            validate_alloc(m.allocation)
        return m
    if tag not in _TAG_TO_CLS:
        raise ASTSchemaError(f"unknown node tag {tag!r}")
    kwargs = {f: _dec(d[f]) for f in _NODE_TAGS[tag]}
    return _TAG_TO_CLS[tag](**kwargs)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src pytest tests/architect/test_ast_serde.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Full suite + commit**

Run: `PYTHONPATH=src pytest -q | tail -3`
Expected: 267 passed / 3 xfailed / 0 failed (262 + 5 new).

```bash
git add src/architect/ast.py tests/architect/test_ast_serde.py
git commit -m "feat: AST to_dict/from_dict JSON serialization for stored formalized ASTs"
```

---

## Task 2: PDF text extraction (`pdf_text`)

**Files:**
- Create: `src/architect/pdf_text.py`
- Test: `tests/architect/test_pdf_text.py` (create)

**Interfaces:**
- Consumes: nothing from earlier tasks. `pdfminer.high_level.extract_text` (installed).
- Produces:
  - `pdf_path(paper_id: str, *, pdf_dir: str = "pdfs") -> str | None` — tries, in order: `<id>.pdf`, `<id with _→.>.pdf`, `<id with _→->.pdf`, all under `pdf_dir`. Returns the first existing path or `None`.
  - `pdf_text(paper_id: str, *, pdf_dir: str = "pdfs", max_chars: int = 24000) -> str | None` — `pdf_path` then `extract_text`; on any exception return `None`; empty text ⇒ `None`. Truncation: if the extracted text exceeds `max_chars`, return the first `max_chars // 2` chars, a `"\n...\n"` separator, and a `max_chars // 2`-char window starting `max_chars // 4` before the earliest case-insensitive hit of any of `"incentive compat"`, `"individual rational"`, `"payment rule"`, `"utility"`, `"best response"`; if no keyword hits, return the first `max_chars` chars.

- [ ] **Step 1: Write the failing test**

```python
# tests/architect/test_pdf_text.py
import os
import pytest
from architect.pdf_text import pdf_path, pdf_text


def test_pdf_path_exact_match(tmp_path):
    (tmp_path / "Cong2020vcg.pdf").write_bytes(b"%PDF-1.4\n")
    assert pdf_path("Cong2020vcg", pdf_dir=str(tmp_path)) == str(tmp_path / "Cong2020vcg.pdf")


def test_pdf_path_underscore_to_dot(tmp_path):
    (tmp_path / "1811.12082.pdf").write_bytes(b"%PDF-1.4\n")
    assert pdf_path("1811_12082", pdf_dir=str(tmp_path)) == str(tmp_path / "1811.12082.pdf")


def test_pdf_path_missing_returns_none(tmp_path):
    assert pdf_path("nope_nope", pdf_dir=str(tmp_path)) is None


def test_pdf_text_missing_returns_none(tmp_path):
    assert pdf_text("nope_nope", pdf_dir=str(tmp_path)) is None


def test_pdf_text_corrupt_returns_none(tmp_path):
    (tmp_path / "bad.pdf").write_bytes(b"not really a pdf")
    assert pdf_text("bad", pdf_dir=str(tmp_path)) is None


@pytest.mark.skipif(
    not os.path.isdir("pdfs") or not os.listdir("pdfs"),
    reason="no pdfs/ corpus locally",
)
def test_pdf_text_real_corpus_entry_nonempty():
    txt = pdf_text("1811_12082")
    assert txt is None or (isinstance(txt, str) and len(txt) > 200)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/architect/test_pdf_text.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'architect.pdf_text'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/architect/pdf_text.py
from __future__ import annotations
import os

_KEYWORDS = (
    "incentive compat", "individual rational", "payment rule",
    "utility", "best response",
)


def pdf_path(paper_id: str, *, pdf_dir: str = "pdfs") -> str | None:
    for name in (
        f"{paper_id}.pdf",
        f"{paper_id.replace('_', '.')}.pdf",
        f"{paper_id.replace('_', '-')}.pdf",
    ):
        p = os.path.join(pdf_dir, name)
        if os.path.isfile(p):
            return p
    return None


def pdf_text(paper_id: str, *, pdf_dir: str = "pdfs", max_chars: int = 24000) -> str | None:
    p = pdf_path(paper_id, pdf_dir=pdf_dir)
    if p is None:
        return None
    try:
        from pdfminer.high_level import extract_text
        txt = extract_text(p) or ""
    except Exception:
        return None
    if not txt.strip():
        return None
    if len(txt) <= max_chars:
        return txt
    half = max_chars // 2
    low = txt.lower()
    hits = [low.find(k) for k in _KEYWORDS if low.find(k) != -1]
    if not hits:
        return txt[:max_chars]
    start = max(0, min(hits) - max_chars // 4)
    return txt[:half] + "\n...\n" + txt[start:start + half]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src pytest tests/architect/test_pdf_text.py -v`
Expected: PASS (6 tests; the real-corpus one may skip).

- [ ] **Step 5: Full suite + commit**

Run: `PYTHONPATH=src pytest -q | tail -3`
Expected: 273 passed / 3 xfailed / 0 failed.

```bash
git add src/architect/pdf_text.py tests/architect/test_pdf_text.py
git commit -m "feat: pdf_text — id-normalized PDF resolution + keyword-windowed extraction"
```

---

## Task 3: Formalizer — `formalize_entry`

**Files:**
- Create: `src/architect/formalize.py`
- Test: `tests/architect/test_formalize.py` (create)

**Interfaces:**
- Consumes: `architect.ast.from_dict`, `architect.ast.ASTSchemaError`, `architect.llm.llm_complete`.
- Produces:
  - `FORMALIZE_SYSTEM_PROMPT: str` — instructs the model to return ONLY a JSON object that is a serialized `Mechanism` (the `to_dict` shape: every node has `"t"`; allowed tags `Const, Sym, Unknown, Sum, Prod, Pow, Func, IndexedFamily, AllocHighest, AllocTopK, AllocWeightedWelfare`; `Func.name` ∈ `{"ln","exp"}`; `Pow.exp` an int). It must set `category` to the entry's category, put the client/follower utility in `utility`, the payment/transfer rule in `payment`, the IC constraint expression in `ic`, the IR constraint expression in `ir`, discrete type values in `type_space`, and copy verifier hints (`num_types`, `type_distribution`, `equilibrium_existence`, `follower_decision`, …) into `meta`. It must NOT invent terms the source does not state; anything genuinely absent → `Unknown("<name>")`.
  - `formalize_entry(entry: dict, pdf_text: str | None, *, complete=llm_complete, concerns: list[dict] | None = None) -> "Mechanism | None"` — builds the user message from `entry["mechanism"]` (JSON), `entry.get("category")`, `entry.get("key_assumptions")`, and `pdf_text` when non-`None`; when `concerns` is non-empty, appends a "The previous attempt had these problems, fix them:" block listing each `{field, issue}`. Calls `complete(FORMALIZE_SYSTEM_PROMPT, user, json_mode=True)`, `json.loads`, `from_dict`. Returns the `Mechanism`, or `None` on `json.JSONDecodeError`, `ASTSchemaError`, `KeyError`, or `TypeError`.

- [ ] **Step 1: Write the failing test**

```python
# tests/architect/test_formalize.py
import json
import pytest
from architect.ast import Mechanism, Sym, Sum, Const, to_dict
from architect.formalize import formalize_entry


def _entry():
    return {
        "paper_id": "synthetic_contract",
        "category": "Contract",
        "mechanism": {
            "client_utility_latex": r"U = \theta R - P",
            "ic_screening_latex": r"\theta R - P \geq \theta R' - P'",
            "ir_participation_latex": r"\theta R - P \geq 0",
            "num_types": 2,
        },
        "key_assumptions": ["linear cost", "discrete types"],
    }


def _good_ast_json():
    m = Mechanism(
        category="Contract",
        utility=Sum([Sym("thetaR"), Const(-1.0)]),
        payment=Sym("P"), ic=Sym("gap"), ir=Sym("u"),
        meta={"num_types": 2},
    )
    return json.dumps(to_dict(m))


def test_formalize_entry_happy_path():
    calls = []
    def fake_complete(system, user, *, json_mode=False):
        calls.append((system, user, json_mode))
        return _good_ast_json()
    m = formalize_entry(_entry(), "PAPER TEXT HERE", complete=fake_complete)
    assert isinstance(m, Mechanism)
    assert m.category == "Contract"
    assert calls[0][2] is True
    assert "PAPER TEXT HERE" in calls[0][1]


def test_formalize_entry_dict_only_when_pdf_none():
    seen = {}
    def fake_complete(system, user, *, json_mode=False):
        seen["user"] = user
        return _good_ast_json()
    formalize_entry(_entry(), None, complete=fake_complete)
    assert "ic_screening_latex" in seen["user"]
    assert "PAPER TEXT" not in seen["user"]


def test_formalize_entry_malformed_json_returns_none():
    m = formalize_entry(_entry(), None, complete=lambda s, u, *, json_mode=False: "not json{")
    assert m is None


def test_formalize_entry_schema_violation_returns_none():
    bad = json.dumps({"t": "Mechanism", "category": "Contract",
                      "utility": {"t": "Sum", "terms": []},
                      "payment": {"t": "Const", "value": 0.0},
                      "ic": {"t": "Const", "value": 0.0},
                      "ir": {"t": "Const", "value": 0.0}})
    m = formalize_entry(_entry(), None, complete=lambda s, u, *, json_mode=False: bad)
    assert m is None


def test_formalize_entry_passes_concerns_on_retry():
    seen = {}
    def fake_complete(system, user, *, json_mode=False):
        seen["user"] = user
        return _good_ast_json()
    formalize_entry(_entry(), None, complete=fake_complete,
                    concerns=[{"field": "ic", "issue": "dropped the upward IC term"}])
    assert "dropped the upward IC term" in seen["user"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/architect/test_formalize.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'architect.formalize'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/architect/formalize.py
from __future__ import annotations
import json
from architect.ast import from_dict, to_dict, ASTSchemaError
from architect.llm import llm_complete

FORMALIZE_SYSTEM_PROMPT = (
    "You convert a Federated Learning incentive mechanism into a typed AST. "
    "Return ONLY a JSON object: a serialized Mechanism. Every node is an object "
    'with a "t" field naming its type. Allowed types: '
    "Const{value:number}, Sym{name:string}, Unknown{name:string}, "
    "Sum{terms:[node]}, Prod{factors:[node]}, Pow{base:node,exp:int}, "
    'Func{name:"ln"|"exp",arg:node}, '
    "IndexedFamily{name:string,index:string,over:[string]}, "
    "AllocHighest{}, AllocTopK{k:int}, AllocWeightedWelfare{weights:[string]}. "
    'The Mechanism: {"t":"Mechanism","category":<the given category>,'
    '"utility":<client/follower utility>,"payment":<payment or transfer rule>,'
    '"ic":<incentive-compatibility constraint expression>,'
    '"ir":<participation constraint expression>,'
    '"params":{},"type_space":[<discrete type values as numbers>],'
    '"allocation":<AllocHighest/AllocTopK/AllocWeightedWelfare or null>,'
    '"meta":{<copy verifier hints: num_types, type_distribution, '
    "equilibrium_existence, follower_decision, ...>}}. "
    "Do NOT invent terms the source does not state. If a quantity is genuinely "
    'unspecified, use Unknown{"name":...}. Keep algebra simple: closed-form '
    "sums, explicit products, ln/exp only, integer powers."
)


def _user_message(entry, pdf_text, concerns):
    mech = json.dumps(entry.get("mechanism", {}), indent=1)
    parts = [
        f"category: {entry.get('category')}",
        f"mechanism dict:\n{mech}",
    ]
    ka = entry.get("key_assumptions")
    if ka:
        parts.append("key_assumptions: " + "; ".join(ka))
    if pdf_text:
        parts.append("paper text (excerpt):\n" + pdf_text)
    if concerns:
        lines = "\n".join(f"- {c.get('field')}: {c.get('issue')}" for c in concerns)
        parts.append("The previous attempt had these problems, fix them:\n" + lines)
    return "\n\n".join(parts)


def formalize_entry(entry, pdf_text, *, complete=llm_complete, concerns=None):
    user = _user_message(entry, pdf_text, concerns)
    try:
        raw = complete(FORMALIZE_SYSTEM_PROMPT, user, json_mode=True)
        return from_dict(json.loads(raw))
    except (json.JSONDecodeError, ASTSchemaError, KeyError, TypeError):
        return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src pytest tests/architect/test_formalize.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Full suite + commit**

Run: `PYTHONPATH=src pytest -q | tail -3`
Expected: 278 passed / 3 xfailed / 0 failed.

```bash
git add src/architect/formalize.py tests/architect/test_formalize.py
git commit -m "feat: formalize_entry — LLM mechanism-dict + PDF -> Mechanism AST, fail-closed"
```

---

## Task 4: Adversary check — `adversary_check`

**Files:**
- Modify: `src/architect/formalize.py`
- Test: `tests/architect/test_formalize.py` (extend)

**Interfaces:**
- Consumes: `architect.ast.to_dict` (already imported in Task 3), `architect.llm.llm_complete`.
- Produces:
  - `ADVERSARY_SYSTEM_PROMPT: str` — instructs the model to compare a serialized `Mechanism` AST against the paper's stated mechanism and return ONLY a JSON object `{"concerns": [{"field": "utility"|"payment"|"ic"|"ir"|"allocation"|"type_space", "issue": "<one sentence>"}]}`. Empty list ⇒ the AST faithfully represents the paper. Look specifically for: a dropped constraint term, a summation with the wrong index set, a flipped sign, a quantifier scoped over the wrong variable, a type value that contradicts the text.
  - `adversary_check(m, entry, pdf_text, *, complete=llm_complete) -> list[dict]` — builds a user message from `to_dict(m)` (JSON), `entry["mechanism"]` (JSON), and `pdf_text` when non-`None`; calls `complete(..., json_mode=True)`; `json.loads`; returns `data["concerns"]` if it is a list, else `[]`. Any exception ⇒ `[]` (a broken adversary must not block a proof the solver already verified).

- [ ] **Step 1: Write the failing test**

```python
# tests/architect/test_formalize.py  (append)
from architect.formalize import adversary_check
from architect.ast import Mechanism, Sym


def _m():
    return Mechanism(category="Contract", utility=Sym("u"), payment=Sym("P"),
                     ic=Sym("gap"), ir=Sym("u"))


def test_adversary_clean_returns_empty():
    out = adversary_check(_m(), _entry(), None,
                          complete=lambda s, u, *, json_mode=False: '{"concerns": []}')
    assert out == []


def test_adversary_reports_concerns():
    payload = '{"concerns": [{"field": "ic", "issue": "missing downward IC"}]}'
    out = adversary_check(_m(), _entry(), "PAPER",
                          complete=lambda s, u, *, json_mode=False: payload)
    assert out == [{"field": "ic", "issue": "missing downward IC"}]


def test_adversary_broken_output_returns_empty():
    out = adversary_check(_m(), _entry(), None,
                          complete=lambda s, u, *, json_mode=False: "garbage")
    assert out == []


def test_adversary_non_list_concerns_returns_empty():
    out = adversary_check(_m(), _entry(), None,
                          complete=lambda s, u, *, json_mode=False: '{"concerns": "nope"}')
    assert out == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/architect/test_formalize.py -k adversary -v`
Expected: FAIL — `ImportError: cannot import name 'adversary_check'`.

- [ ] **Step 3: Write minimal implementation**

Append to `src/architect/formalize.py`:

```python
ADVERSARY_SYSTEM_PROMPT = (
    "You are an adversarial reviewer. Compare a serialized Mechanism AST against "
    "the paper's stated mechanism. Return ONLY JSON: "
    '{"concerns": [{"field": "utility"|"payment"|"ic"|"ir"|"allocation"|"type_space", '
    '"issue": "<one sentence>"}]}. Return an empty list only if the AST faithfully '
    "represents the paper. Look for: a dropped constraint term, a summation over the "
    "wrong index set, a flipped sign, a quantifier over the wrong variable, a type "
    "value that contradicts the text. Do not nitpick notation or naming."
)


def adversary_check(m, entry, pdf_text, *, complete=llm_complete):
    ast_json = json.dumps(to_dict(m), indent=1)
    mech = json.dumps(entry.get("mechanism", {}), indent=1)
    parts = [f"AST:\n{ast_json}", f"paper mechanism dict:\n{mech}"]
    if pdf_text:
        parts.append("paper text (excerpt):\n" + pdf_text)
    try:
        raw = complete(ADVERSARY_SYSTEM_PROMPT, "\n\n".join(parts), json_mode=True)
        data = json.loads(raw)
        c = data.get("concerns")
        return c if isinstance(c, list) else []
    except Exception:
        return []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src pytest tests/architect/test_formalize.py -v`
Expected: PASS (9 tests total in the file).

- [ ] **Step 5: Full suite + commit**

Run: `PYTHONPATH=src pytest -q | tail -3`
Expected: 282 passed / 3 xfailed / 0 failed.

```bash
git add src/architect/formalize.py tests/architect/test_formalize.py
git commit -m "feat: adversary_check — one-directional AST-vs-paper review, fails toward accept"
```

---

## Task 5: Retry driver — `formalize_with_retry` + `FormalizeResult`

**Files:**
- Modify: `src/architect/formalize.py`
- Test: `tests/architect/test_formalize.py` (extend)

**Interfaces:**
- Consumes: `formalize_entry`, `adversary_check` (this module); `architect.ast_verify.verify_from_ast`.
- Produces:
  - `@dataclass FormalizeResult` — `verdict: str` (`"VERIFIED"|"COUNTEREXAMPLE"|"UNKNOWN"|"UNSUPPORTED"`), `ast: "Mechanism | None"`, `adversary_log: list` (one element per adversary round; each element is a concern-list, empty means "clean"), `retries: int` (0 or 1), `pdf_used: bool`, `notes: str`.
  - `formalize_with_retry(entry: dict, pdf_text: str | None, *, complete=llm_complete) -> FormalizeResult` — the state machine:
    1. `m = formalize_entry(entry, pdf_text, complete=complete)`. `m is None` ⇒ `FormalizeResult("UNKNOWN", None, [], 0, pdf_text is not None, "formalization returned no valid AST")`.
    2. `res = verify_from_ast(m, meta={"paper_id": entry.get("paper_id", "")})`.
    3. `res.verdict == "VERIFIED"` → `c = adversary_check(m, entry, pdf_text, complete=complete)`; `c == []` ⇒ `FormalizeResult("VERIFIED", m, [[]], 0, used, "")`; else retry with `concerns=c`, `adversary_log=[c]`.
    4. `res.verdict == "COUNTEREXAMPLE"` → retry with `concerns=None`, `adversary_log=[]`.
    5. else (`UNKNOWN`/`UNSUPPORTED`) ⇒ `FormalizeResult(res.verdict, m, [], 0, used, res.notes or "")`.
    6. **Retry (once):** `m2 = formalize_entry(entry, pdf_text, complete=complete, concerns=concerns)`. `m2 is None` ⇒ `FormalizeResult("UNKNOWN", m, adversary_log, 1, used, "retry formalization returned no valid AST")`. `res2 = verify_from_ast(m2, meta=...)`. `res2.verdict == "VERIFIED"` → `c2 = adversary_check(m2, ...)`; `c2 == []` ⇒ `FormalizeResult("VERIFIED", m2, adversary_log + [[]], 1, used, "")`; else ⇒ `FormalizeResult("UNKNOWN", m2, adversary_log + [c2], 1, used, "adversary still flagged after retry")`. `res2.verdict == "COUNTEREXAMPLE"` ⇒ `FormalizeResult("COUNTEREXAMPLE", m2, adversary_log, 1, used, "counterexample persists after retry")`. else ⇒ `FormalizeResult(res2.verdict, m2, adversary_log, 1, used, res2.notes or "")`.

- [ ] **Step 1: Write the failing test**

```python
# tests/architect/test_formalize.py  (append)
from architect.formalize import formalize_with_retry, FormalizeResult
import architect.formalize as F
from architect.ast import Mechanism, Sym


class _Res:
    def __init__(self, verdict, notes=""):
        self.verdict = verdict
        self.notes = notes


def _install(monkeypatch, *, asts, verdicts, adv):
    a_it, v_it, d_it = iter(asts), iter(verdicts), iter(adv)
    monkeypatch.setattr(F, "formalize_entry", lambda *a, **k: next(a_it))
    monkeypatch.setattr(F, "verify_from_ast", lambda *a, **k: _Res(next(v_it)))
    monkeypatch.setattr(F, "adversary_check", lambda *a, **k: next(d_it))


def _m(tag="u"):
    return Mechanism(category="Contract", utility=Sym(tag), payment=Sym("P"),
                     ic=Sym("g"), ir=Sym("u"))


def test_retry_verified_clean_first_pass(monkeypatch):
    _install(monkeypatch, asts=[_m()], verdicts=["VERIFIED"], adv=[[]])
    r = formalize_with_retry({"paper_id": "x"}, "pdf")
    assert r.verdict == "VERIFIED" and r.retries == 0 and r.pdf_used is True


def test_retry_none_ast_is_unknown(monkeypatch):
    _install(monkeypatch, asts=[None], verdicts=[], adv=[])
    r = formalize_with_retry({"paper_id": "x"}, None)
    assert r.verdict == "UNKNOWN" and r.ast is None and r.pdf_used is False


def test_retry_adversary_flags_then_clean(monkeypatch):
    _install(monkeypatch, asts=[_m("a"), _m("b")],
             verdicts=["VERIFIED", "VERIFIED"],
             adv=[[{"field": "ic", "issue": "dropped term"}], []])
    r = formalize_with_retry({"paper_id": "x"}, "pdf")
    assert r.verdict == "VERIFIED" and r.retries == 1
    assert r.adversary_log == [[{"field": "ic", "issue": "dropped term"}], []]


def test_retry_adversary_still_flags_is_unknown(monkeypatch):
    _install(monkeypatch, asts=[_m("a"), _m("b")],
             verdicts=["VERIFIED", "VERIFIED"],
             adv=[[{"field": "ic", "issue": "x"}], [{"field": "ic", "issue": "still x"}]])
    r = formalize_with_retry({"paper_id": "x"}, "pdf")
    assert r.verdict == "UNKNOWN" and r.retries == 1
    assert "still flagged" in r.notes


def test_retry_counterexample_then_verified(monkeypatch):
    _install(monkeypatch, asts=[_m("a"), _m("b")],
             verdicts=["COUNTEREXAMPLE", "VERIFIED"], adv=[[]])
    r = formalize_with_retry({"paper_id": "x"}, None)
    assert r.verdict == "VERIFIED" and r.retries == 1


def test_retry_counterexample_persists(monkeypatch):
    _install(monkeypatch, asts=[_m("a"), _m("b")],
             verdicts=["COUNTEREXAMPLE", "COUNTEREXAMPLE"], adv=[])
    r = formalize_with_retry({"paper_id": "x"}, None)
    assert r.verdict == "COUNTEREXAMPLE" and r.retries == 1


def test_retry_unknown_verdict_no_retry(monkeypatch):
    _install(monkeypatch, asts=[_m()], verdicts=["UNKNOWN"], adv=[])
    r = formalize_with_retry({"paper_id": "x"}, "pdf")
    assert r.verdict == "UNKNOWN" and r.retries == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/architect/test_formalize.py -k retry -v`
Expected: FAIL — `ImportError: cannot import name 'formalize_with_retry'`.

- [ ] **Step 3: Write minimal implementation**

Append to `src/architect/formalize.py`:

```python
from dataclasses import dataclass, field
from architect.ast_verify import verify_from_ast


@dataclass
class FormalizeResult:
    verdict: str
    ast: object | None
    adversary_log: list = field(default_factory=list)
    retries: int = 0
    pdf_used: bool = False
    notes: str = ""


def _verify(m, entry):
    return verify_from_ast(m, meta={"paper_id": entry.get("paper_id", "")})


def formalize_with_retry(entry, pdf_text, *, complete=llm_complete):
    used = pdf_text is not None
    m = formalize_entry(entry, pdf_text, complete=complete)
    if m is None:
        return FormalizeResult("UNKNOWN", None, [], 0, used,
                               "formalization returned no valid AST")
    res = _verify(m, entry)
    concerns, adversary_log = None, []
    if res.verdict == "VERIFIED":
        c = adversary_check(m, entry, pdf_text, complete=complete)
        if not c:
            return FormalizeResult("VERIFIED", m, [[]], 0, used, "")
        concerns, adversary_log = c, [c]
    elif res.verdict == "COUNTEREXAMPLE":
        concerns, adversary_log = None, []
    else:
        return FormalizeResult(res.verdict, m, [], 0, used, getattr(res, "notes", "") or "")

    m2 = formalize_entry(entry, pdf_text, complete=complete, concerns=concerns)
    if m2 is None:
        return FormalizeResult("UNKNOWN", m, adversary_log, 1, used,
                               "retry formalization returned no valid AST")
    res2 = _verify(m2, entry)
    if res2.verdict == "VERIFIED":
        c2 = adversary_check(m2, entry, pdf_text, complete=complete)
        if not c2:
            return FormalizeResult("VERIFIED", m2, adversary_log + [[]], 1, used, "")
        return FormalizeResult("UNKNOWN", m2, adversary_log + [c2], 1, used,
                               "adversary still flagged after retry")
    if res2.verdict == "COUNTEREXAMPLE":
        return FormalizeResult("COUNTEREXAMPLE", m2, adversary_log, 1, used,
                               "counterexample persists after retry")
    return FormalizeResult(res2.verdict, m2, adversary_log, 1, used,
                           getattr(res2, "notes", "") or "")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src pytest tests/architect/test_formalize.py -v`
Expected: PASS (16 tests total in the file).

- [ ] **Step 5: Full suite + commit**

Run: `PYTHONPATH=src pytest -q | tail -3`
Expected: 289 passed / 3 xfailed / 0 failed.

```bash
git add src/architect/formalize.py tests/architect/test_formalize.py
git commit -m "feat: formalize_with_retry — formalize/verify/adversary state machine, one retry"
```

---

## Task 6: Batch CLI — `run_batch` + `main` + run report

**Files:**
- Modify: `src/architect/formalize.py`
- Test: `tests/architect/test_formalize_cli.py` (create)

**Interfaces:**
- Consumes: `formalize_with_retry`, `FormalizeResult` (this module); `architect.pdf_text.pdf_text`; `architect.ast.to_dict`; `architect.llm.llm_complete`.
- Produces:
  - `run_batch(corpus_path: str, *, ids: list[str] | None = None, only: str | None = None, dry_run: bool = False, complete=llm_complete, today: str | None = None) -> dict` — loads `corpus_path` JSON (a list). Selects: `ids` (match `paper_id`) precedence; else `only` (match `category`); else all. Per selected entry: `txt = pdf_text(entry["paper_id"])`; `r = formalize_with_retry(entry, txt, complete=complete)`; if `r.ast is not None and r.verdict in {"VERIFIED", "COUNTEREXAMPLE"}` set `entry["formalized_ast"] = to_dict(r.ast)` and `entry["formalization_meta"] = {"model": <env ARCHITECT_LLM_MODEL or "default">, "verdict": r.verdict, "retries": r.retries, "adversary_rounds": len(r.adversary_log), "pdf_used": r.pdf_used, "flagged": False, "date": today or date.today().isoformat()}`. Collect a per-entry record `{paper_id, category, verdict, retries, adversary_rounds, pdf_used, notes}`. If not `dry_run`, write the mutated list back to `corpus_path` (`json.dump(..., indent=2, ensure_ascii=False)` + trailing newline). Always write `docs/superpowers/notes/formalize-run-<date>.md`. Return `{"records": [...], "report_path": str, "summary": {...}}`.
  - `main(argv=None)` — argparse: positional `corpus_path`; `--ids` (comma-separated); `--only`; `--dry-run`. Calls `run_batch`, prints the summary + report path.
  - Report format: `# Formalize run — <date>`; a table `| paper_id | category | verdict | retries | adversary_rounds | pdf_used | notes |`; a `## Human queue` section listing every record whose `verdict` is `UNKNOWN` or `COUNTEREXAMPLE` (`- <id> (<verdict>): <notes>`), or `- (empty)`; a `## Summary` section with `selected`, `verified`, `counterexample`, `unknown`, `dict_only`.

- [ ] **Step 1: Write the failing test**

```python
# tests/architect/test_formalize_cli.py
import json
import pytest
from architect.formalize import run_batch, FormalizeResult
import architect.formalize as F
from architect.ast import Mechanism, Sym


def _corpus(tmp_path):
    data = [
        {"paper_id": "aaa", "category": "Contract",
         "mechanism": {"ic_screening_latex": "x", "ir_participation_latex": "y"}},
        {"paper_id": "bbb", "category": "VCG",
         "mechanism": {"payment_rule_latex": "p"}},
    ]
    p = tmp_path / "corpus.json"
    p.write_text(json.dumps(data))
    return str(p)


def _stub_verified(monkeypatch):
    monkeypatch.setattr(F, "pdf_text", lambda *a, **k: None)
    m = Mechanism(category="Contract", utility=Sym("u"), payment=Sym("P"),
                  ic=Sym("g"), ir=Sym("u"))
    monkeypatch.setattr(
        F, "formalize_with_retry",
        lambda entry, txt, **k: FormalizeResult("VERIFIED", m, [[]], 0, False, ""),
    )


def test_run_batch_writes_ast_and_meta(tmp_path, monkeypatch):
    _stub_verified(monkeypatch)
    cp = _corpus(tmp_path)
    out = run_batch(cp, ids=["aaa"], today="2026-08-31")
    data = json.loads(open(cp).read())
    aaa = next(e for e in data if e["paper_id"] == "aaa")
    bbb = next(e for e in data if e["paper_id"] == "bbb")
    assert aaa["formalized_ast"]["t"] == "Mechanism"
    assert aaa["formalization_meta"]["verdict"] == "VERIFIED"
    assert aaa["formalization_meta"]["date"] == "2026-08-31"
    assert "formalized_ast" not in bbb
    assert out["summary"]["verified"] == 1


def test_run_batch_dry_run_does_not_write(tmp_path, monkeypatch):
    _stub_verified(monkeypatch)
    cp = _corpus(tmp_path)
    before = open(cp).read()
    run_batch(cp, ids=["aaa"], dry_run=True, today="2026-08-31")
    assert open(cp).read() == before


def test_run_batch_report_has_human_queue(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "pdf_text", lambda *a, **k: None)
    monkeypatch.setattr(
        F, "formalize_with_retry",
        lambda entry, txt, **k: FormalizeResult(
            "UNKNOWN", None, [], 1, False, "adversary still flagged after retry"),
    )
    cp = _corpus(tmp_path)
    out = run_batch(cp, only="Contract", today="2026-08-31")
    report = open(out["report_path"]).read()
    assert "## Human queue" in report
    assert "aaa" in report
    assert out["summary"]["unknown"] == 1


def test_run_batch_only_filters_by_category(tmp_path, monkeypatch):
    _stub_verified(monkeypatch)
    cp = _corpus(tmp_path)
    out = run_batch(cp, only="VCG", today="2026-08-31")
    assert out["summary"]["selected"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/architect/test_formalize_cli.py -v`
Expected: FAIL — `ImportError: cannot import name 'run_batch'`.

- [ ] **Step 3: Write minimal implementation**

Append to `src/architect/formalize.py`:

```python
import os
import argparse
from datetime import date
from architect.pdf_text import pdf_text


def _select(corpus, ids, only):
    if ids:
        want = set(ids)
        return [e for e in corpus if e.get("paper_id") in want]
    if only:
        return [e for e in corpus if e.get("category") == only]
    return list(corpus)


def _report_md(records, today):
    lines = [f"# Formalize run — {today}", "",
             "| paper_id | category | verdict | retries | adversary_rounds | pdf_used | notes |",
             "|---|---|---|---|---|---|---|"]
    for r in records:
        lines.append(
            f"| {r['paper_id']} | {r['category']} | {r['verdict']} | {r['retries']} "
            f"| {r['adversary_rounds']} | {r['pdf_used']} | {r['notes']} |")
    queue = [r for r in records if r["verdict"] in ("UNKNOWN", "COUNTEREXAMPLE")]
    lines += ["", "## Human queue", ""]
    if queue:
        for r in queue:
            lines.append(f"- {r['paper_id']} ({r['verdict']}): {r['notes']}")
    else:
        lines.append("- (empty)")
    n = len(records)
    summary = {
        "selected": n,
        "verified": sum(1 for r in records if r["verdict"] == "VERIFIED"),
        "counterexample": sum(1 for r in records if r["verdict"] == "COUNTEREXAMPLE"),
        "unknown": sum(1 for r in records if r["verdict"] == "UNKNOWN"),
        "dict_only": sum(1 for r in records if not r["pdf_used"]),
    }
    lines += ["", "## Summary", ""]
    for k, v in summary.items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines) + "\n", summary


def run_batch(corpus_path, *, ids=None, only=None, dry_run=False,
              complete=llm_complete, today=None):
    today = today or date.today().isoformat()
    with open(corpus_path) as fh:
        corpus = json.load(fh)
    model = os.environ.get("ARCHITECT_LLM_MODEL", "default")
    records = []
    for entry in _select(corpus, ids, only):
        pid = entry.get("paper_id", "")
        txt = pdf_text(pid)
        r = formalize_with_retry(entry, txt, complete=complete)
        if r.ast is not None and r.verdict in ("VERIFIED", "COUNTEREXAMPLE"):
            entry["formalized_ast"] = to_dict(r.ast)
            entry["formalization_meta"] = {
                "model": model, "verdict": r.verdict, "retries": r.retries,
                "adversary_rounds": len(r.adversary_log), "pdf_used": r.pdf_used,
                "flagged": False, "date": today,
            }
        records.append({
            "paper_id": pid, "category": entry.get("category", ""),
            "verdict": r.verdict, "retries": r.retries,
            "adversary_rounds": len(r.adversary_log), "pdf_used": r.pdf_used,
            "notes": r.notes,
        })
    if not dry_run:
        with open(corpus_path, "w") as fh:
            json.dump(corpus, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    md, summary = _report_md(records, today)
    report_path = os.path.join("docs", "superpowers", "notes",
                               f"formalize-run-{today}.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as fh:
        fh.write(md)
    return {"records": records, "report_path": report_path, "summary": summary}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m architect.formalize")
    ap.add_argument("corpus_path")
    ap.add_argument("--ids", default=None, help="comma-separated paper_id list")
    ap.add_argument("--only", default=None, help="restrict to one category")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    ids = args.ids.split(",") if args.ids else None
    out = run_batch(args.corpus_path, ids=ids, only=args.only, dry_run=args.dry_run)
    print("summary:", out["summary"], "report:", out["report_path"])


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src pytest tests/architect/test_formalize_cli.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Full suite + commit**

Run: `PYTHONPATH=src pytest -q | tail -3`
Expected: 293 passed / 3 xfailed / 0 failed.

```bash
git add src/architect/formalize.py tests/architect/test_formalize_cli.py
git commit -m "feat: architect.formalize batch CLI — write-back + run report + human queue"
```

---

## Task 7: `verify()` prefers a stored AST; `_reconcile`

**Files:**
- Modify: `src/verifier.py`
- Test: `tests/verifier/test_reconcile.py` (create)

**Interfaces:**
- Consumes: `architect.ast.from_dict`, `architect.ast.ASTSchemaError`; `architect.ast_verify.verify_from_ast`; the existing `verify(entry)` body and `VerificationResult`.
- Produces:
  - `_verify_latex(entry) -> VerificationResult` — the existing `verify(entry)` body, extracted verbatim (pure move) if it is not already separable.
  - `_reconcile(llm: VerificationResult, latex: VerificationResult) -> tuple[VerificationResult, bool]` — implements the conflict-rule table verbatim. "`latex` is `VERIFIED`" means `latex.verdict == "VERIFIED" and getattr(latex, "entry_specific", False)`. On a flagged return, append `" | RECONCILE-FLAG: LaTeX=<v> LLM=<v>"` to `chosen.notes`.
  - `verify(entry)` — unchanged when no `formalized_ast`. When present: `latex_res = _verify_latex(entry)`; `llm_res = verify_from_ast(from_dict(entry["formalized_ast"]), meta={"paper_id": entry.get("paper_id", "")})`; `chosen, _ = _reconcile(llm_res, latex_res)`; return `chosen`. `from_dict` raising `ASTSchemaError` ⇒ return `latex_res`.

- [ ] **Step 1: Write the failing test**

```python
# tests/verifier/test_reconcile.py
import pytest
from verifier import _reconcile, VerificationResult


def _r(verdict, *, entry_specific=False, notes=""):
    return VerificationResult(verdict=verdict, category="Contract",
                              paper_id="x", track=1, notes=notes,
                              entry_specific=entry_specific)


@pytest.mark.parametrize("latex_v", ["VERIFIED_TEMPLATE", "VERIFIED_SHAPE",
                                     "UNKNOWN", "UNSUPPORTED"])
def test_llm_verified_upgrades(latex_v):
    chosen, flagged = _reconcile(_r("VERIFIED", entry_specific=True), _r(latex_v))
    assert chosen.verdict == "VERIFIED" and flagged is False


@pytest.mark.parametrize("latex_v", ["VERIFIED_TEMPLATE", "UNKNOWN"])
def test_llm_counterexample_upgrades_flagged(latex_v):
    chosen, flagged = _reconcile(_r("COUNTEREXAMPLE"), _r(latex_v))
    assert chosen.verdict == "COUNTEREXAMPLE" and flagged is True


def test_agree_on_verified():
    chosen, flagged = _reconcile(_r("VERIFIED", entry_specific=True),
                                 _r("VERIFIED", entry_specific=True))
    assert chosen.verdict == "VERIFIED" and flagged is False


@pytest.mark.parametrize("llm_v", ["COUNTEREXAMPLE", "UNKNOWN", "UNSUPPORTED"])
def test_existing_verified_sticky_flagged(llm_v):
    chosen, flagged = _reconcile(_r(llm_v), _r("VERIFIED", entry_specific=True))
    assert chosen.verdict == "VERIFIED" and flagged is True
    assert "RECONCILE-FLAG" in chosen.notes


def test_existing_counterexample_vs_llm_verified_flagged():
    chosen, flagged = _reconcile(_r("VERIFIED", entry_specific=True),
                                 _r("COUNTEREXAMPLE"))
    assert chosen.verdict == "COUNTEREXAMPLE" and flagged is True


def test_llm_unknown_no_improvement_keeps_latex():
    chosen, flagged = _reconcile(_r("UNKNOWN"), _r("VERIFIED_TEMPLATE"))
    assert chosen.verdict == "VERIFIED_TEMPLATE" and flagged is False


def test_latex_counterexample_llm_unknown_keeps_latex():
    chosen, flagged = _reconcile(_r("UNKNOWN"), _r("COUNTEREXAMPLE"))
    assert chosen.verdict == "COUNTEREXAMPLE" and flagged is False
```

Integration tests:

```python
# tests/verifier/test_reconcile.py  (append)
from architect.ast import Mechanism, Sym, to_dict
from verifier import verify


def test_verify_uses_stored_ast(monkeypatch):
    import verifier as V
    m = Mechanism(category="Contract", utility=Sym("u"), payment=Sym("P"),
                  ic=Sym("g"), ir=Sym("u"))
    entry = {"paper_id": "z", "category": "Contract",
             "mechanism": {"ic_screening_latex": "x", "ir_participation_latex": "y"},
             "formalized_ast": to_dict(m)}
    monkeypatch.setattr(V, "_verify_latex", lambda e: _r("VERIFIED_TEMPLATE"))
    monkeypatch.setattr(V, "verify_from_ast",
                        lambda *a, **k: _r("VERIFIED", entry_specific=True))
    out = verify(entry)
    assert out.verdict == "VERIFIED"


def test_verify_corrupt_stored_ast_falls_back(monkeypatch):
    import verifier as V
    entry = {"paper_id": "z", "category": "Contract",
             "mechanism": {"ic_screening_latex": "x", "ir_participation_latex": "y"},
             "formalized_ast": {"t": "Bogus"}}
    monkeypatch.setattr(V, "_verify_latex", lambda e: _r("VERIFIED_TEMPLATE"))
    out = verify(entry)
    assert out.verdict == "VERIFIED_TEMPLATE"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/verifier/test_reconcile.py -v`
Expected: FAIL — `ImportError: cannot import name '_reconcile'`.

- [ ] **Step 3: Write minimal implementation**

In `src/verifier.py`:

1. If `verify(entry)`'s body is not already a separable function, extract it verbatim into `def _verify_latex(entry): ...` and have `verify` call it. Pure move.
2. Add near the top: `from architect.ast import from_dict, ASTSchemaError` and `from architect.ast_verify import verify_from_ast`. If a module-level import causes a circular import (run the suite to check), move both imports inside `verify`.
3. Add:

```python
_LATEX_WEAK = {"VERIFIED_TEMPLATE", "VERIFIED_SHAPE", "UNKNOWN", "UNSUPPORTED"}


def _flag(chosen, latex, llm):
    tag = f"RECONCILE-FLAG: LaTeX={latex.verdict} LLM={llm.verdict}"
    chosen.notes = f"{chosen.notes} | {tag}".strip(" |")
    return chosen


def _reconcile(llm, latex):
    latex_is_verified = latex.verdict == "VERIFIED" and getattr(latex, "entry_specific", False)
    if latex.verdict in _LATEX_WEAK and llm.verdict == "VERIFIED":
        return llm, False
    if latex.verdict in _LATEX_WEAK and llm.verdict == "COUNTEREXAMPLE":
        return _flag(llm, latex, llm), True
    if latex_is_verified and llm.verdict == "VERIFIED":
        return latex, False
    if latex_is_verified and llm.verdict in ("COUNTEREXAMPLE", "UNKNOWN", "UNSUPPORTED"):
        return _flag(latex, latex, llm), True
    if latex.verdict == "COUNTEREXAMPLE" and llm.verdict == "VERIFIED":
        return _flag(latex, latex, llm), True
    return latex, False
```

4. Rewrite `verify`:

```python
def verify(entry):
    latex_res = _verify_latex(entry)
    fa = entry.get("formalized_ast")
    if not fa:
        return latex_res
    try:
        m = from_dict(fa)
    except ASTSchemaError:
        return latex_res
    llm_res = verify_from_ast(m, meta={"paper_id": entry.get("paper_id", "")})
    chosen, _flagged = _reconcile(llm_res, latex_res)
    return chosen
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src pytest tests/verifier/test_reconcile.py -v`
Expected: PASS (all rows + 2 integration tests).

- [ ] **Step 5: Corpus + full suite + commit**

Run: `PYTHONPATH=src python -m verifier corpus.json | tail -12`
Expected: **byte-identical to baseline** — 6 / 59 / 33 / 2 / 5 — no corpus entry has `formalized_ast` yet.

Run: `PYTHONPATH=src pytest -q | tail -3`
Expected: 302 passed / 3 xfailed / 0 failed.

```bash
git add src/verifier.py tests/verifier/test_reconcile.py
git commit -m "feat: verify() prefers stored formalized_ast; _reconcile conflict rule"
```

---

## Task 8: Smoke test + pytest marker + first real run

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/architect/test_formalize_smoke.py`
- Generated / committed (Steps 5–7, needs an API key): `docs/superpowers/notes/formalize-run-<date>.md`, `corpus.json`

**Interfaces:**
- Consumes: `architect.formalize.run_batch`.
- Produces: the `llm` marker; the smoke test; the first real batch artifacts.

Smoke set (`SMOKE_IDS`): `["Cong2020vcg", "2102_03401", "1811_12082", "Kang2019contract_mobile", "Deng2020fmore_auction"]`.

- [ ] **Step 1: Register the marker**

In `pyproject.toml` under `[tool.pytest.ini_options]` (create the table if absent):

```toml
[tool.pytest.ini_options]
markers = [
    "llm: end-to-end test that calls a real LLM; skipped unless ARCHITECT_LLM_SMOKE=1",
]
```

- [ ] **Step 2: Write the smoke test**

```python
# tests/architect/test_formalize_smoke.py
import os
import pytest
from architect.formalize import run_batch

SMOKE_IDS = ["Cong2020vcg", "2102_03401", "1811_12082",
             "Kang2019contract_mobile", "Deng2020fmore_auction"]


@pytest.mark.llm
@pytest.mark.skipif(
    os.environ.get("ARCHITECT_LLM_SMOKE") != "1"
    or not (os.environ.get("ARCHITECT_LLM_API_KEY")
            or os.environ.get("NVIDIA_API_KEY")
            or os.environ.get("GROQ_API_KEY")
            or os.environ.get("OPENAI_API_KEY")),
    reason="set ARCHITECT_LLM_SMOKE=1 and an API key to run the LLM smoke test",
)
def test_formalize_smoke_dry_run(tmp_path):
    import shutil
    cp = str(tmp_path / "corpus.json")
    shutil.copy("corpus.json", cp)
    out = run_batch(cp, ids=SMOKE_IDS, dry_run=True)
    assert out["summary"]["selected"] == len(SMOKE_IDS)
    assert os.path.isfile(out["report_path"])
    print("SMOKE SUMMARY:", out["summary"])
```

- [ ] **Step 3: Run the default suite — marker + skip work, no network**

Run: `PYTHONPATH=src pytest -q | tail -3`
Expected: 302 passed / 3 xfailed / 1 skipped / 0 failed.

- [ ] **Step 4: Commit the harness**

```bash
git add pyproject.toml tests/architect/test_formalize_smoke.py
git commit -m "test: register llm marker; formalize smoke test (skipped without API key)"
```

- [ ] **Step 5: Run the real batch on the smoke set (requires an API key)**

Needs `ARCHITECT_LLM_API_KEY` (or a provider key). **If no key is available, STOP here** and record in the execution notes that Steps 5–7 are blocked on an API key — the harness (Steps 1–4) is complete and committed.

```bash
PYTHONPATH=src python -m architect.formalize corpus.json --ids Cong2020vcg,2102_03401,1811_12082,Kang2019contract_mobile,Deng2020fmore_auction
```

- [ ] **Step 6: Hand-check every flip**

Open `docs/superpowers/notes/formalize-run-<date>.md`. For each entry whose `verdict` is `VERIFIED` or `COUNTEREXAMPLE` and that now has `formalized_ast` in `corpus.json`:
- Read the stored AST against the paper's mechanism dict (and PDF if present). Confirm every IC/IR term, sum scope, and sign.
- Run `PYTHONPATH=src python -c "import json,sys; sys.path.insert(0,'src'); from verifier import verify; e=[x for x in json.load(open('corpus.json')) if x['paper_id']=='<id>'][0]; r=verify(e); print(r.verdict, r.entry_specific, r.notes)"` and confirm the reconciled verdict.
- For a Track-1/2 grid `VERIFIED`, dump the Z3 model / SymPy FOC and confirm no profitable deviation. For a Track-3 δ result, confirm the δ bound.
- Append a justification paragraph per flip under a new `## Hand-check` section of the run report.
- Any flip that does NOT check out: delete that entry's `formalized_ast` + `formalization_meta` from `corpus.json` by hand; note it as rejected in the report.

- [ ] **Step 7: Corpus gate + commit the run**

Run: `PYTHONPATH=src python -m verifier corpus.json | tail -14`
Expected: `VERIFIED` count = 6 + (smoke entries that legitimately flipped to `VERIFIED`); every other summary line changed only by those flips leaving their prior bucket; no entry moved to a strictly-worse verdict.

Run: `PYTHONPATH=src pytest -q | tail -3`
Expected: still 0-failed.

```bash
git add corpus.json docs/superpowers/notes/formalize-run-<date>.md
git commit -m "feat: formalizer smoke run — <N> corpus entries flipped to real VERIFIED (hand-checked)"
```

---

## Task 9: `print_summary` surfaces `RECONCILE-FLAG` entries

**Files:**
- Modify: `src/verifier.py` (`print_summary`)
- Test: `tests/verifier/test_reconcile.py` (extend)

**Interfaces:**
- Consumes: `VerificationResult.notes` (a flagged entry carries `"RECONCILE-FLAG: LaTeX=<v> LLM=<v>"` in `notes`, appended by `_flag` in Task 7).
- Produces: a new `## Needs review` block in `print_summary` output, printed only when ≥1 result's `notes` contains `"RECONCILE-FLAG"`: a count line and one bullet per flagged entry (`- <paper_id>: <the RECONCILE-FLAG substring>`).

- [ ] **Step 1: Write the failing test**

```python
# tests/verifier/test_reconcile.py  (append)
from verifier import print_summary


def test_print_summary_lists_reconcile_flags(capsys):
    flagged = _r("VERIFIED", entry_specific=True,
                 notes="grid-exact | RECONCILE-FLAG: LaTeX=COUNTEREXAMPLE LLM=VERIFIED")
    flagged.paper_id = "conflict_entry"
    clean = _r("VERIFIED", entry_specific=True, notes="grid-exact")
    print_summary([flagged, clean])
    out = capsys.readouterr().out
    assert "Needs review" in out
    assert "conflict_entry" in out
    assert "RECONCILE-FLAG" in out


def test_print_summary_no_flag_block_when_none(capsys):
    print_summary([_r("VERIFIED", entry_specific=True, notes="grid-exact")])
    out = capsys.readouterr().out
    assert "Needs review" not in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/verifier/test_reconcile.py -k reconcile_flags -v`
Expected: FAIL — `assert "Needs review" in out` fails (block not emitted).

- [ ] **Step 3: Write minimal implementation**

At the end of `print_summary` (after the existing output, before the function returns):

```python
    flagged = [r for r in results if "RECONCILE-FLAG" in (r.notes or "")]
    if flagged:
        print(f"\n  ## Needs review ({len(flagged)} LLM/LaTeX verdict conflicts)")
        for r in flagged:
            tag = r.notes[r.notes.index("RECONCILE-FLAG"):]
            print(f"  - {r.paper_id}: {tag}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src pytest tests/verifier/test_reconcile.py -v`
Expected: PASS.

- [ ] **Step 5: Corpus + full suite + commit**

Run: `PYTHONPATH=src python -m verifier corpus.json | tail -6`
Expected: no `## Needs review` block (no corpus entry has a stored AST yet), summary otherwise byte-identical to baseline.

Run: `PYTHONPATH=src pytest -q | tail -3`
Expected: 304 passed / 3 xfailed / 0 failed.

```bash
git add src/verifier.py tests/verifier/test_reconcile.py
git commit -m "feat: print_summary surfaces RECONCILE-FLAG conflicts as a Needs-review block"
```

---

## Task 10: Batch resumability — `--resume` and `--limit`

**Files:**
- Modify: `src/architect/formalize.py` (`run_batch`, `main`)
- Test: `tests/architect/test_formalize_cli.py` (extend)

**Interfaces:**
- Consumes: `run_batch` (Task 6).
- Produces:
  - `run_batch(..., resume: bool = False, limit: int | None = None)` — two new kwargs.
    - `resume=True`: after selecting entries (by `ids`/`only`/all), drop any entry that already has a non-empty `entry.get("formalized_ast")`.
    - `limit=N`: after the resume filter, keep only the first `N` remaining entries.
    - Both default off ⇒ Task 6 behaviour is unchanged.
  - `main` argparse gains `--resume` (store_true) and `--limit` (int, default `None`).

- [ ] **Step 1: Write the failing test**

```python
# tests/architect/test_formalize_cli.py  (append)
def test_run_batch_resume_skips_already_formalized(tmp_path, monkeypatch):
    _stub_verified(monkeypatch)
    data = [
        {"paper_id": "aaa", "category": "Contract",
         "mechanism": {"ic_screening_latex": "x", "ir_participation_latex": "y"},
         "formalized_ast": {"t": "Mechanism"}},
        {"paper_id": "bbb", "category": "Contract",
         "mechanism": {"ic_screening_latex": "x", "ir_participation_latex": "y"}},
    ]
    cp = tmp_path / "corpus.json"
    cp.write_text(json.dumps(data))
    out = run_batch(str(cp), only="Contract", resume=True, today="2026-09-02")
    assert out["summary"]["selected"] == 1
    assert out["records"][0]["paper_id"] == "bbb"


def test_run_batch_limit_caps_selection(tmp_path, monkeypatch):
    _stub_verified(monkeypatch)
    data = [
        {"paper_id": f"p{i}", "category": "VCG",
         "mechanism": {"payment_rule_latex": "p"}} for i in range(5)
    ]
    cp = tmp_path / "corpus.json"
    cp.write_text(json.dumps(data))
    out = run_batch(str(cp), only="VCG", limit=2, today="2026-09-02")
    assert out["summary"]["selected"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/architect/test_formalize_cli.py -k "resume or limit" -v`
Expected: FAIL — `run_batch() got an unexpected keyword argument 'resume'`.

- [ ] **Step 3: Write minimal implementation**

Restructure `run_batch` to compute the selection list before the loop:

```python
def run_batch(corpus_path, *, ids=None, only=None, dry_run=False,
              complete=llm_complete, today=None, resume=False, limit=None):
    today = today or date.today().isoformat()
    with open(corpus_path) as fh:
        corpus = json.load(fh)
    model = os.environ.get("ARCHITECT_LLM_MODEL", "default")
    selected = _select(corpus, ids, only)
    if resume:
        selected = [e for e in selected if not e.get("formalized_ast")]
    if limit is not None:
        selected = selected[:limit]
    records = []
    for entry in selected:
        ...   # body unchanged
```

In `main`:

```python
    ap.add_argument("--resume", action="store_true",
                    help="skip entries that already have formalized_ast")
    ap.add_argument("--limit", type=int, default=None,
                    help="process at most N entries after selection/resume")
    ...
    out = run_batch(args.corpus_path, ids=ids, only=args.only,
                    dry_run=args.dry_run, resume=args.resume, limit=args.limit)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src pytest tests/architect/test_formalize_cli.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Full suite + commit**

Run: `PYTHONPATH=src pytest -q | tail -3`
Expected: 306 passed / 3 xfailed / 0 failed.

```bash
git add src/architect/formalize.py tests/architect/test_formalize_cli.py
git commit -m "feat: formalize batch --resume (skip done) + --limit (cost cap)"
```

---

## Appendix: Human-queue protocol (written process, no code)

R2/R3 run the formalizer at corpus scale and will produce two kinds of entry that
need a human:

1. **`UNKNOWN` + human queue** — the formalizer + one retry could not produce a
   solver-accepted AST whose adversary pass is clean. Listed in the run report's
   `## Human queue` section.
2. **`RECONCILE-FLAG`** — the LLM verdict conflicts with an existing entry-specific
   `VERIFIED` or a cross-path `COUNTEREXAMPLE`↔`VERIFIED`. Surfaced by
   `print_summary`'s `## Needs review` block (Task 9).

**The protocol (applied in R2 onward, established here):**

- **Owner:** the round's controller works the queue before the round's final
  whole-branch review. The queue is not deferred across rounds.
- **`UNKNOWN` queue item — decide one of:**
  - *Formalization gap* — the AST was wrong/incomplete in a way a better prompt or
    a different model would fix. Note it; it becomes an R6 (second-formalizer)
    candidate. Entry stays `UNKNOWN` for now.
  - *Solver-track ceiling* — the mechanism is past the decidable fragment (name the
    track + the specific limit from the program spec's ceiling table). Set the
    entry to `MANUAL` and append a `MANUAL-backlog.md` paragraph.
  - *Genuinely unclear* — leave `UNKNOWN`, note "needs a human read of the paper to
    classify" — this is itself an R7 backlog item.
- **`RECONCILE-FLAG` item — decide one of:**
  - *LaTeX proof is right, LLM formalization is wrong* — discard the
    `formalized_ast` for that entry (delete both keys from `corpus.json` by hand),
    note why. Entry keeps its LaTeX verdict.
  - *LLM formalization is right, the LaTeX-path proof was over-claiming* — a real
    finding. Record it, keep the LLM verdict, open a follow-up note to fix the
    LaTeX path. Requires a hand-derivation confirming the LLM side.
  - *Both plausible, cannot decide from the material* — leave the existing verdict
    (the conservative side), keep the flag, escalate to a paper read. R7 backlog
    item.
- **Recording:** every queue resolution is logged in the round's
  `round-<Rn>-new-verified.md` (for flips), `MANUAL-backlog.md` (for `MANUAL`
  reclassifications), or the round's execution notes (for "stays as-is,
  escalated"). A queue item is not "done" until its resolution is written
  somewhere durable.
- **Round exit:** a round may not merge to `main` with unresolved `RECONCILE-FLAG`
  items on entries that round touched. `UNKNOWN`-queue items may carry forward
  (they are the R6 input) but each must have a written disposition.

---

## Self-Review

**Spec coverage:**
- Formalizer (dict + PDF → AST, fail-closed) → Task 3. ✓
- PDF text with id normalization → Task 2. ✓
- Adversary one-directional check → Task 4. ✓
- Retry-once state machine + `FormalizeResult` → Task 5. ✓
- Batch CLI, write-back, run report, human queue → Task 6. ✓
- `corpus.json` schema additions (`formalized_ast`, `formalization_meta`) → written in Task 6, consumed in Task 7, populated in Task 8. ✓
- `verify()` prefers stored AST + `_reconcile` conflict table → Task 7. ✓
- The spec's `mechanism_from_dict` (inverse of serialization) → delivered as `architect.ast.from_dict` (Task 1). The formalizer emits the `to_dict` JSON shape directly, so no LaTeX re-parse is needed — simpler than the spec's sketch, same guarantee (schema-validated on load). Documented here so an executor reading the spec is not surprised. ✓
- Deterministic `verify(corpus.json)` with no API key → Task 7 gate + Task 8 marker skip. ✓
- 5-entry smoke set exercising all tracks + dict-only fallback → Task 8. ✓
- Monotone Round-1 corpus movement, hand-checked flips, run report → Task 8 Steps 6–7. ✓
- Program-spec R1.5 item — `print_summary` surfaces `RECONCILE-FLAG` → Task 9. ✓
- Program-spec R1.5 item — batch resumability (`--resume`, `--limit` cost cap) → Task 10. ✓
- Program-spec R1.5 item — written human-queue protocol for R2 onward → Appendix. ✓
- Program-spec invariant — a `RECONCILE-FLAG` conflict is visible, not buried in one entry's `.notes` → Task 9 (`## Needs review` block) + Appendix (how it is worked). ✓

**Placeholder scan:** every code step has a full code block; every test step has runnable assertions; the smoke set is enumerated; the report format is specified field-by-field. Task 8 Step 5 has an explicit "blocked on API key → stop and record" branch, not a TODO. The Appendix is a written process, not code, and names every decision branch. No "add error handling" / "similar to Task N". ✓

**Type consistency:**
- `to_dict` / `from_dict` (Task 1) — used by `formalize_entry` (Task 3), `adversary_check` (Task 4), `run_batch` (Task 6), `verify` (Task 7). Same names throughout.
- `FormalizeResult` fields (`verdict, ast, adversary_log, retries, pdf_used, notes`) defined in Task 5, consumed in Task 6 (`r.ast`, `r.verdict`, `r.retries`, `len(r.adversary_log)`, `r.pdf_used`, `r.notes`). Match.
- `formalize_entry(entry, pdf_text, *, complete, concerns)` (Task 3) — called by `formalize_with_retry` (Task 5) with exactly those kwargs.
- `adversary_check(m, entry, pdf_text, *, complete)` (Task 4) — called by `formalize_with_retry` (Task 5) with those args.
- `_reconcile(llm, latex) -> (VerificationResult, bool)` (Task 7) — tested row-by-row against the conflict table in the plan header; `verify` uses the returned `chosen`.
- `run_batch(corpus_path, *, ids, only, dry_run, complete, today)` (Task 6) — called by `main` (Task 6) and the smoke test (Task 8) with matching kwargs.
- `verify_from_ast(m, meta=...)` — existing signature in `src/architect/ast_verify.py:285`, called from Tasks 5 and 7. Match.
- `adversary_log` — Task 5 defines it as a list of concern-lists; Task 6 reads `len(r.adversary_log)` as `adversary_rounds`; Task 6 test asserts on the count only. Consistent.
- `run_batch` gains `resume` / `limit` kwargs in Task 10 with defaults that preserve Task 6 behaviour; the smoke test (Task 8) and Task 6 tests do not pass them, so they stay green. `_reconcile`'s `_flag` (Task 7) writes the exact `"RECONCILE-FLAG: LaTeX=... LLM=..."` substring that Task 9's `print_summary` block and its test both match on. Consistent.

**Scope check:** one subsystem (the formalization pipeline + its operational surface). No corpus sweep, no loop changes, no new solver track. R2–R8 explicitly out (program spec). The R1.5 items folded in (Tasks 9–10, Appendix) are the minimum needed to make R1's output *usable* by R2 without an immediate follow-up round. Single plan. ✓

**Risk note:** Tasks 1–7, 9, 10 and Task 8 Steps 1–4 are mechanical and fully covered by stubbed-LLM tests — no API key needed to reach a green, committed pipeline. Only Task 8 Steps 5–7 need a real key and human judgement; the plan makes that boundary explicit and lets execution stop cleanly at the last key-free commit if no key is available. The Appendix protocol is exercised for real only in R2 onward.
