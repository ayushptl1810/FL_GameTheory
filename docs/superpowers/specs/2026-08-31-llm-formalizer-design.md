# LLM Formalizer — Corpus's Primary Verification Path — Design

**Status:** Design approved 2026-08-31. This is **Round 1 (R1)** of the
Zero-UNKNOWN Program (`docs/superpowers/specs/2026-09-02-zero-unknown-program-design.md`).
R1 = pipeline + tests + a 5-entry smoke run. No corpus batch — the sweep is R2/R3.

## Where this fits

The Zero-UNKNOWN Program drives every verifiable corpus entry to `VERIFIED` /
`REFUTED` / diagnosed `MANUAL`, eliminating `UNKNOWN`. R1 builds the formalization
engine every later round uses. R1's own corpus effect is limited to the smoke set;
R2 (VCG sweep) and R3 (Contract + Stackelberg sweep) run this engine across the
full ~101 entries. The program spec owns the round structure, the automation
ceiling, and the cross-round invariants; this spec owns the R1 pipeline design.

## Problem

Of ~101 verifiable-tier corpus entries (33 VCG + 38 Contract + 30 Stackelberg + 4 Shapley;
the 80 `Valuation`/`RL`/`Naive` entries carry no incentive claim and are out of scope),
only **6** carry a real solver proof (`VERIFIED`, entry-specific). The other ~95 sit at
`VERIFIED_TEMPLATE` (structural skeleton match — no solver run on the entry's own math) or
`VERIFIED_SHAPE` (VCG regex pattern match — no solver run at all).

Regex parser widening cannot close this gap. Phase 3 spent three tasks widening the
Contract and Stackelberg LaTeX parsers (`_parse_contract_entry`, `_try_stackelberg_latex`,
function-call notation) and flipped **zero** entries, because academic LaTeX is too varied:
every paper writes `c_i(P_i)`, `E_{θ_{-i}}[·]`, `R_i^L`, `\sum_{j∈S}` its own way, and each
corpus entry stacks two or three such ambiguities. Clearing one blocker per entry buys
nothing.

An LLM *can* read `E_{θ_{-i}}[U_i(P_i, θ_i)]` in the context of the paper's stated setup and
emit a typed AST. The existing solver (`verify_from_ast` → Track 1/2/3/4) then proves or
refutes that AST. The LLM proposes a formalization; the **solver** decides the verdict — the
LLM cannot fabricate a `VERIFIED`.

## Goal

Build a batch tool that formalizes corpus entries into `Mechanism` ASTs, verifies them with
the real solver, adversarially self-checks each proof, and commits the AST + verdict back to
`corpus.json` so `verify(entry)` is deterministic and reproducible at verify time.

**Long-run target (Round 2+):** ~55–70 real `VERIFIED` out of ~101, vs 6 today.
**Round 1 target (this spec):** the pipeline, tested against synthetic fixtures + a 5-entry
smoke set. No corpus sweep.

## Non-goals

- **Round 1 does not run the corpus batch.** Only the 5-entry `--ids` smoke set touches real
  entries, and only after hand-check.
- No change to the Architect generation loop or `ARCHITECT_AST_VERIFY` default.
- No new verifier track. Shapley entries (4) still need Phase 4; the formalizer will emit
  their ASTs but `verify_from_ast` returns `UNSUPPORTED` for them until that track exists.
- No live LLM call inside `verify(entry)`. The LLM is a build step.
- No PDF OCR. The corpus already carries hand-checked LaTeX in structured mechanism dicts;
  the PDF is a disambiguation source, read as extracted text.

## Approach

A batch tool `python -m architect.formalize` that, per entry:

1. **Formalize.** LLM reads the corpus mechanism dict + source PDF text → emits a
   `Mechanism` AST (the typed structure in `src/architect/ast.py`).
2. **Verify.** `verify_from_ast(m)` runs the real Track 1/2/3/4 solver.
3. **Adversary.** A separate LLM pass inspects the AST against the paper for dropped
   constraints, wrong summation scope, sign flips, mis-scoped quantifiers.
4. **Retry once.** An adversary concern *or* a solver `COUNTEREXAMPLE` feeds back into the
   formalizer → corrected AST → re-verify → re-run adversary once.
5. **Record.** Clean → `VERIFIED`, AST + adversary log written to `corpus.json`. Still
   flagged after the retry → `UNKNOWN`, listed in the human queue.

At verify time, `verify(entry)` prefers `entry["formalized_ast"]` (deterministic, no API
key), falling through to the existing LaTeX path when absent.

### Conflict rule (LLM verdict vs existing LaTeX-path verdict on the same entry)

| LaTeX path | LLM path | Result |
|---|---|---|
| `TEMPLATE` / `SHAPE` / `UNKNOWN` | `VERIFIED` | **LLM wins — entry flips.** (the point of the round) |
| `TEMPLATE` / `SHAPE` / `UNKNOWN` | `COUNTEREXAMPLE` | LLM wins — entry becomes `COUNTEREXAMPLE`, listed for review |
| `VERIFIED` (entry-specific) | `VERIFIED` | agree — no action |
| `VERIFIED` (entry-specific) | `COUNTEREXAMPLE` / `UNKNOWN` | **existing `VERIFIED` stands, `flagged=True`, human decides** |
| `COUNTEREXAMPLE` | `VERIFIED` | **existing `COUNTEREXAMPLE` stands, `flagged=True`, human decides** |

Rationale: the LLM path is the more capable but *less proven* path (Phase 3's automated
formalization produced two false `VERIFIED`s caught only by review). It trumps LaTeX
everywhere it matters — the ~95 upgrades — and holds back only on the ~6 existing real
proofs and cross-path counterexample disagreements, where a human spends minutes per entry.
Once a batch's human queue comes back near-empty, revisit letting the LLM auto-overturn.

## Components (Round 1 deliverables)

| Component | File | Responsibility |
|---|---|---|
| Formalizer | `src/architect/formalize.py` — `formalize_entry(entry, pdf_text, *, complete=llm_complete, concerns=None) -> Mechanism \| None` | Prompt + JSON→AST parse + `validate_ast`. Returns `None` (never a guess) on unparseable output or schema violation. `concerns` is the retry feedback list. |
| Adversary | `src/architect/formalize.py` — `adversary_check(m, entry, pdf_text, *, complete=llm_complete) -> list[dict]` | Prompt returns a list of `{field, issue}` concern dicts. Empty = clean. Can block a `VERIFIED`; never creates one. |
| Retry driver | `src/architect/formalize.py` — `formalize_with_retry(entry, pdf_text, *, complete=llm_complete) -> FormalizeResult` | Orchestrates formalize → verify → adversary → (one retry) → verdict. |
| Result type | `src/architect/formalize.py` — `@dataclass FormalizeResult` | `verdict: str`, `ast: Mechanism \| None`, `adversary_log: list[list[dict]]` (one per round), `retries: int`, `pdf_used: bool`, `notes: str`. |
| PDF text | `src/architect/pdf_text.py` — `pdf_text(paper_id, *, pdf_dir="pdfs") -> str \| None` | id normalization (`_`↔`.`↔`-`) + extraction via `pdfminer.high_level.extract_text` (already installed). `None` when no PDF matches. Truncates to a token budget (head + the section matching mechanism keywords). |
| Deserialize | `src/architect/serialize.py` — `mechanism_from_dict(d: dict) -> Mechanism` | Inverse of `render` for the AST node union (`Const`/`Sym`/`Unknown`/`Sum`/`Prod`/`Pow`/`Func`/`IndexedFamily`, `Alloc*`, `Mechanism`). Round-trips with `render`. |
| Batch CLI | `src/architect/formalize.py` — `main()` — `python -m architect.formalize corpus.json [--only VCG] [--ids a,b,c] [--dry-run] [--out PATH]` | Iterates entries, writes `formalized_ast` + `formalization_meta` back (unless `--dry-run`), emits `docs/superpowers/notes/formalize-run-<date>.md`. **Round 1: invoked only with `--ids <smoke5>`.** |
| Corpus integration | `src/verifier.py::verify` | If `entry.get("formalized_ast")`: `mechanism_from_dict` → `verify_from_ast` → `_reconcile` with the LaTeX-path verdict. Else: existing path unchanged. |
| Conflict resolver | `src/verifier.py` — `_reconcile(llm: VerificationResult, latex: VerificationResult) -> tuple[VerificationResult, bool]` | Applies the conflict-rule table. Returns `(chosen, flagged)`. |

### `corpus.json` schema additions (per entry, optional)

```json
"formalized_ast": { "...serialized Mechanism (same shape render() consumes)..." },
"formalization_meta": {
  "model": "meta/llama-3.2-90b-vision-instruct",
  "verdict": "VERIFIED",
  "retries": 0,
  "adversary_rounds": 1,
  "pdf_used": true,
  "flagged": false,
  "date": "2026-08-31"
}
```

`date` is `YYYY-MM-DD`. Both keys absent on every entry after Round 1 except the 5 smoke
entries.

## Data Flow

### Batch tool (`python -m architect.formalize`, API key required)

```
for each selected entry:
  pdf_text(paper_id) ─────────────► str | None        (id normalized; None → dict-only)
  formalize_entry(entry, pdf_text)
      LLM: mechanism dict + PDF ──► JSON ─► Mechanism AST
      JSON bad / validate_ast fails ─────► None ─► verdict=UNKNOWN, next entry
  verify_from_ast(m) ─────────────► VERIFIED | COUNTEREXAMPLE | UNKNOWN   (real solver)
  if VERIFIED:
      adversary_check(m, entry, pdf) ─► [] | [concerns]
      [] ─────────────────────────────► record VERIFIED
      [concerns] ─► retry once:
          formalize_entry(..., concerns=concerns) ─► m'
          verify_from_ast(m') + adversary_check(m') ─► clean VERIFIED → record VERIFIED
                                                     └─ else → record UNKNOWN + human queue
  if COUNTEREXAMPLE:
      retry once (formalization may have mis-stated a constraint)
      still COUNTEREXAMPLE ─► record COUNTEREXAMPLE + human queue
      now clean VERIFIED  ─► record VERIFIED
      now UNKNOWN         ─► record UNKNOWN
  write back (unless --dry-run):
      entry["formalized_ast"]      = serialized m
      entry["formalization_meta"]  = {model, verdict, retries, adversary_rounds, pdf_used, flagged, date}

emit docs/superpowers/notes/formalize-run-<date>.md:
  per entry — verdict, retries, adversary_log, conflict-with-LaTeX?, in human queue?
  summary — flip count, adversary catch rate, retry rate, human-queue size, dict-only count
```

### Verify time (`verify(entry)`, deterministic, no LLM)

```
verify(entry):
  entry.get("formalized_ast")?
    yes → mechanism_from_dict(d) → verify_from_ast → llm_result
          latex_result = <existing LaTeX path, computed as today>
          (chosen, flagged) = _reconcile(llm_result, latex_result)
          flagged → chosen stands; entry appears in the "needs-review" section of print_summary
          return chosen
    no  → existing LaTeX path, unchanged
```

## Error Handling / Fail-Closed

- **Formalizer never guesses.** Bad JSON, a schema violation, or a node type outside the AST
  union → `None` → `UNKNOWN`. No partial AST is verified.
- **PDF missing / extraction fails** → formalize dict-only; `formalization_meta.pdf_used =
  false` marks it lower-confidence for Round 2 triage.
- **Adversary is one-directional.** It can block a `VERIFIED` (→ retry → `UNKNOWN`); it can
  never turn an `UNKNOWN`/`COUNTEREXAMPLE` into a `VERIFIED`.
- **Solver `unknown` / timeout** inside `verify_from_ast` → `UNKNOWN` (existing behavior).
- **`_reconcile` never silently overturns.** On a flagged conflict the stronger existing
  verdict stands and the entry is surfaced for a human. Round 1 exercises this only on the
  smoke set.
- **Write-back is idempotent.** Re-running the batch replaces an entry's `formalized_ast`.
  `--dry-run` computes and reports without writing.
- **Round 1 acceptance gate.** After the smoke-5 write-back:
  - `PYTHONPATH=src python -m verifier corpus.json` — the 5 smoke entries may only move to a
    **better or equal** verdict vs the pre-round baseline; no other entry moves; `VERIFIED`
    count rises by exactly the number of smoke entries that legitimately flipped.
  - Each smoke flip is hand-checked (AST read against the paper, solver model/FOC inspected)
    and recorded in `docs/superpowers/notes/formalize-run-<date>.md` before the commit.
  - Full pytest suite stays 0-failed (currently 262 passed / 3 xfailed).

## Testing (Round 1)

- **`tests/architect/test_formalize.py`** (stubbed `complete`):
  - clean synthetic Contract dict → expected `Mechanism` AST; `verify_from_ast` → `VERIFIED`.
  - dict with a deliberately dropped IC term → `adversary_check` returns a concern → retry
    with `concerns` → corrected AST → `VERIFIED`.
  - malformed LLM JSON → `formalize_entry` returns `None` → `FormalizeResult.verdict ==
    "UNKNOWN"`.
  - adversary still flags after the retry → `verdict == "UNKNOWN"`, entry in the human queue.
  - solver `COUNTEREXAMPLE` on first pass → retry → still `COUNTEREXAMPLE` → recorded, queued.
- **`tests/architect/test_pdf_text.py`**: id normalization resolves the ~99 matchable corpus
  ids; a bogus id → `None`; extraction of one real small PDF returns non-empty text
  containing a known phrase.
- **`tests/architect/test_serialize_roundtrip.py`** (extend): `mechanism_from_dict(render(m))
  == m` for a Mechanism covering every node type including `Alloc*`.
- **`tests/verifier/test_reconcile.py`**: every row of the conflict-rule table.
- **`tests/architect/test_formalize_smoke.py`** — `@pytest.mark.llm`, skipped unless
  `ARCHITECT_LLM_SMOKE=1` and an API key present. Runs the 5-entry smoke set end to end,
  asserts the pipeline completes and writes a run report; does not assert specific verdicts
  (records them).

### Smoke set (5 entries, hand-picked)

Chosen to exercise all four solver tracks + the dict-only fallback:
- `Cong2020vcg` — VCG, clean Clarke pivot (Track 1 grid).
- `2102_03401` — Contract, linear cost, discrete types, no PDF in `pdfs/` → dict-only path.
- `1811_12082` — Stackelberg, `exp` follower utility, stated best response (Track 3 / FOC).
- one Contract entry with `ln` utility (e.g. `Kang2019contract_mobile`) — Track 3
  transcendental, expected `UNKNOWN` (too many free vars) — exercises the honest-UNKNOWN
  path, not a flip.
- one VCG entry with `\begin{cases}` allocation (e.g. `Deng2020fmore_auction`) — exercises
  the formalizer producing an `Alloc` node the regex parser can't.

## File Structure

| File | Change |
|---|---|
| `src/architect/formalize.py` | **new** — `formalize_entry`, `adversary_check`, `formalize_with_retry`, `FormalizeResult`, `main` |
| `src/architect/pdf_text.py` | **new** — `pdf_text`, id normalization |
| `src/architect/serialize.py` | add `mechanism_from_dict` (inverse of `render`) |
| `src/verifier.py` | `verify` prefers `formalized_ast`; add `_reconcile` |
| `src/architect/ast.py` | no change (schema already covers what the formalizer emits) |
| `tests/architect/test_formalize.py` | **new** |
| `tests/architect/test_pdf_text.py` | **new** |
| `tests/architect/test_serialize_roundtrip.py` | extend for `mechanism_from_dict` |
| `tests/verifier/test_reconcile.py` | **new** |
| `tests/architect/test_formalize_smoke.py` | **new**, `@pytest.mark.llm` |
| `docs/superpowers/notes/formalize-run-<date>.md` | **generated** by the smoke run |
| `corpus.json` | 5 smoke entries gain `formalized_ast` + `formalization_meta` |

## Global Constraints

- Run tests from repo root with `PYTHONPATH=src`. Suite stays 0-failed (262 passed / 3
  xfailed now). `@pytest.mark.llm` tests are excluded from the default run.
- `python -m verifier corpus.json` must stay reproducible with **no API key** — the LLM is a
  build step, never invoked at verify time.
- Round 1 corpus movement is bounded to the 5 smoke entries and is monotone (better-or-equal
  verdict only), each flip hand-checked and logged before commit.
- Commit after each task. Branch `llm-formalizer-round1` off `main`. Do not push, do not open
  a PR. Stop at the last green commit.
- The untracked `docs/superpowers/plans/2026-08-30-fl-simulation-validation.md` is not part
  of this work — never `git add` it.

## Rounds R2–R8 (out of scope here)

The corpus sweep and everything after it live in the program spec
(`2026-09-02-zero-unknown-program-design.md`): R2 = VCG sweep, R3 = Contract +
Stackelberg sweep, R4 = track widenings from R2/R3 `MANUAL` diagnostics, R5 =
coalition/Shapley track, R6 = second-formalizer pass on residual `MANUAL`, R7 =
honesty pass + `MANUAL-backlog.md` (the hard `UNKNOWN = 0` gate), R8 =
`ARCHITECT_AST_VERIFY` flip. R1's smoke-run report (adversary catch rate,
human-queue size, per-entry cost) is the input to R2's planning — including
whether to relax the conflict rule to let the LLM auto-overturn existing verdicts.

## Self-Review

**Placeholder scan:** none — every component has a signature, every test a concrete
fixture, the smoke set is enumerated.

**Internal consistency:** `formalize_entry` returns `Mechanism | None`; `formalize_with_retry`
wraps it in `FormalizeResult`; `main` writes `render`-serialized ASTs; `verify` reads them
back via `mechanism_from_dict`; round-trip is a tested invariant. The conflict-rule table is
the single source for `_reconcile`.

**Scope check:** Round 1 is pipeline + tests + a 5-entry smoke run. The 101-entry sweep,
the human-queue workflow, and the conflict-rule relaxation are all explicitly Round 2. One
implementation plan covers Round 1.

**Ambiguity check:** "the LLM trumps LaTeX" is made precise by the conflict-rule table —
upgrades always, existing `VERIFIED`/counterexample disagreements never (flagged instead).
"Formalizer never guesses" is `None` → `UNKNOWN` on any parse/schema failure. Adversary is
explicitly one-directional (blocks, never creates, a `VERIFIED`).

**Risk note:** the pipeline machinery is mechanical and testable with stubbed LLM calls.
The real risk lives in Round 2 (formalization accuracy at scale, human-queue volume, token
cost) — Round 1 exists to measure those on 5 entries before committing to 101.
