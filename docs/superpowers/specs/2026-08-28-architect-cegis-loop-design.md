# Stage 2 — The Architect: CEGIS Loop for FL Incentive Mechanism Design

**Date:** 2026-08-28
**Status:** Design approved, pending implementation plan
**Depends on:** Stage 1 (corpus + multi-track verifier), complete.

---

## 1. Purpose

Stage 1 built the **Inspector**: `verify(entry: dict) -> VerificationResult`, a
multi-track formal verifier over a 185-entry FL incentive-mechanism corpus.

Stage 2 builds the **Architect**: an LLM-driven system that takes a natural-language
description of a Federated Learning deployment and produces a **formally verified**
reward rule (payment function + IC + IR conditions), by looping with the Inspector
in a Counterexample-Guided Inductive Synthesis (CEGIS) cycle.

The working tool is the substance; the research paper is its writeup. The loop must
run end-to-end on realistic FL configurations, not toy cases.

### Novelty (what the paper claims)

The *system* is the contribution: CEGIS with a **formal verifier as the teacher**
(not an evolutionary metric), specialized to FL via the corpus and the four
FL-specific mechanism failure modes, with **Z3 used in synthesis mode** to solve for
mechanism parameters. Closest prior work, Liu–Guo–Conitzer (arXiv:2502.12203),
uses an evolutionary loop with Monte-Carlo revenue as the objective and enforces
strategy-proofness by hard-coded per-template construction — it produces no proof
certificate for arbitrary proposed structures. The defensible moat is the **FL
domain specialization**, not "we used a verifier" (LLM+verifier loops are now an
active area: AutoCedar, property-guided LLM synthesis, 2026 CEGIS+LLM work).

### Empirical basis for loop parameters

LLM self-repair literature (2025–2026) converges: 2–4 repair iterations capture
76–95% of achievable gains; later iterations can *reduce* quality via overfitting
to accumulated context; reasoning models keep improving longer than non-reasoning
models. Loop behavior depends more on orchestration, validation strategy, and
feedback formatting than on the backbone model. We use a repair cap of **5** (the
backbone model is not fixed; 5 accommodates a reasoning model) plus a single
fresh restart to escape context overfitting.

---

## 2. Modes

All three modes are built completely. They share one loop and one representation
(the typed AST, §4); they differ only in the Architect's prompt and inputs.

| Mode | Architect input | Architect output | Handles |
|---|---|---|---|
| **Retrieval** | problem spec + top-k corpus entries | adapt nearest entry's mechanism to new params | ~80% of deployments close to existing literature |
| **Synthesis** | problem spec + structural template family | AST with `Unknown` leaf nodes; Z3 solves for them | novel settings; the headline research contribution |
| **Hybrid** | problem spec + k corpus entries | AST merging subtrees from multiple entries | deployments between mechanism families (e.g. VCG allocation + Contract payment) |

Build order: Retrieval (proves the plumbing) → Synthesis (the paper) → Hybrid
(cheap once the AST exists). All shipped, none stubbed.

---

## 3. System architecture

```
User FL setup (free text)
      │
 ┌────▼─────────┐   structured problem spec + missing_fields
 │ 1 Intake LLM │   {n_clients, cost_structure, type_model, observability,
 └────┬─────────┘    budget, failure_modes[], ...}
      │
 ┌────▼─────────┐   mode ∈ {Retrieval, Synthesis, Hybrid}
 │ 2 Mode router│   nearest-corpus cosine distance + one LLM yes/no
 └────┬─────────┘
      │
 ┌────▼─────────┐   top-k corpus entries (Retrieval / Hybrid)
 │ 3 RAG index  │   flat numpy cosine over embed(fl_setup + title),
 └────┬─────────┘   tie-break toward z3_validated == true
      │
 ┌────▼──────────────────────────────────────┐
 │ 4 ARCHITECT  (CEGIS learner)              │
 │   emits a typed AST (§4)                  │
 └────┬──────────────────────────────────────┘
      │ AST
 ┌────▼──────────────────────────────┐
 │ 7 SYNTHESIZER  (Synthesis mode)   │  AST w/ Unknown leaves + IC+IR+BB
 │   Z3 solve → concrete AST | UNSAT │  → concrete AST (skipped in Retrieval)
 └────┬──────────────────────────────┘
      │ concrete AST
 ┌────▼─────────┐  render mechanism dict; per-track dry-run parse;
 │ 5 Serializer │  assert structural round-trip; reject-with-hint if
 └────┬─────────┘  outside the parseable fragment
      │ entry dict
 ┌────▼─────────┐  1000 sampled types, ε threshold
 │ MC pre-filter│  sampled violation → cheap COUNTEREXAMPLE, skip solver
 └────┬─────────┘
      │
 ┌────▼─────────┐  verify(entry) -> VerificationResult
 │ 6 INSPECTOR  │  (Stage 1, unchanged except a parse-only hook, §5)
 └────┬─────────┘
      │ verdict
      ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ 8 LOOP CONTROLLER — verdict policy (Option 1 + 3)            │
 │   VERIFIED ∧ entry_specific → STOP: emit mechanism +        │
 │                               certificate + rendered LaTeX  │
 │   COUNTEREXAMPLE  → repair (counterexample → re-propose),    │
 │                     ≤5; then 1 fresh restart (discard        │
 │                     context, pass "families tried" summary), │
 │                     ≤5 more; then FAIL                       │
 │   UNKNOWN         → reformulate: "simplify utility, same     │
 │                     family", ≤2; then FAIL                   │
 │   UNSUPPORTED     → re-propose forcing a verifiable family,  │
 │                     ≤1; then FAIL                            │
 │   VERIFIED_TEMPLATE → FAIL + log (legitimate on multi-type   │
 │                       proposals; not a bug)                  │
 │   Global wall-clock budget per request — hard backstop above │
 │   all caps (Z3 can hang).                                    │
 └─────────────────────────────────────────────────────────────┘
```

---

## 4. Representation: the typed AST

The Architect emits a typed AST, never free-form LaTeX. One serializer (§5) renders
it two ways from the same tree: LaTeX (for the paper and for adding to the corpus)
and the `mechanism` dict (for `verify()`). No LaTeX parser sits in the generation
loop — this is the single most important design decision, because Stage 1's
measured entry-specific verification rate is limited largely by *parser* failures
(`\sum_{i∈S}` bounds, multiplication-by-juxtaposition, multi-clause utility
definitions), and those must not be inherited by the generator.

### Node set

Derived in **Step 0** from an audit of every `mechanism` field across the four
verifiable categories (VCG, Contract, Stackelberg, Shapley). Minimum viable set:

- `Const(value)` — numeric literal
- `Sym(name)` — a named symbol (client type `θ_i`, param, etc.)
- `Unknown(name)` — a free parameter for Synthesis mode; a `Const` everywhere else
- `Sum(terms)`, `Prod(factors)` — n-ary
- `Pow(base, exponent)` — exponent restricted to integer `Const` (matches the
  tracks' polynomial handling)
- `Func(name, arg)` — `name ∈ {ln, exp}` only (Track 3 transcendental fragment)
- `IndexedFamily(name, index, over)` — a menu / per-type family `{R_i}` (Contract);
  `over` names the finite index set

Nodes outside this set are a Step-0 finding to extend deliberately, not an
open-ended grammar. `IndexedFamily` with a non-finite `over` is rejected at
serialization (matches the tracks' inability to parse set-indexed sums).

### Mode ↔ AST

- **Retrieval:** Architect parses the retrieved entry's mechanism into an AST
  (offline, one-time, allowed to use the full Stage-1 parser since it is not in
  the loop), then edits leaves/params for the new setup.
- **Synthesis:** Architect emits an AST whose payment-rule subtree contains
  `Unknown` leaves; unit 7 solves for them.
- **Hybrid:** Architect emits an AST whose subtrees are tagged with their source
  `paper_id`; the serializer and certificate record provenance.

---

## 5. Units

Eight units, each with one purpose, a defined interface, and an isolated test.

### Step 0 — AST schema from corpus audit
**Does:** enumerate the algebraic forms present in the 4 verifiable categories'
`mechanism` fields; finalize the §4 node set; write a corpus-coverage report
(what fraction of entry-specific-VERIFIED entries the AST can represent).
**Output:** `src/architect/ast.py` node definitions + `docs/ast-coverage.md`.
**Test:** parse every entry-specific-VERIFIED corpus mechanism into the AST;
assert ≥ 90% round-trip; list the misses with reasons.

### Unit 1 — Intake LLM
**Interface:** `intake(text: str) -> ProblemSpec` where `ProblemSpec` has
`n_clients`, `cost_structure`, `type_model`, `observability`, `budget`,
`failure_modes: list[str]` (subset of the four FL breaks), and
`missing_fields: list[str]`.
**Behavior:** never guesses silently; anything absent from the text goes in
`missing_fields`. The controller (interactive) prompts the user, or (batch) fills
documented defaults recorded in the run log.
**Test:** fixed input transcripts → expected `ProblemSpec` JSON, including the
`missing_fields` list.

### Unit 2 — Mode router
**Interface:** `route(spec: ProblemSpec, rag_hits: list[Entry]) -> Mode`.
**Behavior:** if nearest corpus cosine distance < τ_retrieval → Retrieval; if the
spec's `failure_modes` or family needs cross two corpus categories → Hybrid;
otherwise → Synthesis. One LLM yes/no confirms ("is entry X a close structural
match for this setup?").
**Test:** known-retrieval fixture (near-duplicate of a corpus setup),
known-novel fixture, known-hybrid fixture.

### Unit 3 — RAG index
**Interface:** `retrieve(spec: ProblemSpec, k: int) -> list[Entry]`.
**Behavior:** flat numpy cosine over `embed(entry.fl_setup + " " + entry.title)`
for all 185 entries; return top-k, tie-broken toward `z3_validated == true` so
Retrieval targets entries that were themselves entry-specifically verified.
185 entries — no vector DB.
`ponytail: flat index, swap for FAISS only if the corpus passes ~10k entries.`
**Test:** query with a paraphrase of a known entry's setup → that entry in top-3.

### Unit 4 — Architect
**Interface:** `propose(spec, mode, rag_hits, feedback: Feedback | None) -> AST`.
**Behavior:** three prompt templates (one per mode). `feedback` carries the last
`VerificationResult.counterexample` + `conditions` + a natural-language repair
hint. On a fresh restart, `feedback` instead carries only a "these structural
families failed: [...]" summary and no accumulated transcript.
**Test:** mocked LLM responses → assert the AST is well-formed and, for Synthesis,
contains `Unknown` leaves only in the payment subtree.

### Unit 5 — Serializer + round-trip checker
**Interface:** `render(ast) -> tuple[MechanismDict, LatexStr]`; raises
`OutsideParseableFragment(hint)` if any track's parse-only pass fails or the
re-parsed structure is not equal to the input AST.
**Behavior:** pure, no LLM. The "parseable fragment" is defined *operationally* by
this check, not by a static list: render → for the target category, run the
track's parse in a **dry-run mode** (parse only, no solving) → structurally
compare. This requires a small `parse_only` entry point added to each Track-1
category function (VCG/Contract/Stackelberg) and Track 3 — the one change to
Stage 1 code, additive, covered by new tests against the existing 51-test suite.
**Test:** hand-built ASTs that render inside the fragment (round-trip equal) and
outside it (raise with a hint); property test: `parse(render(ast)) ≈ ast` for
random ASTs over the node set.

### Unit 6 — Inspector (Stage 1)
Unchanged except the `parse_only` hook above. Consumed via `verify(entry_dict)`.
Success condition for the loop: `verdict == "VERIFIED" and entry_specific`.
`VERIFIED_TEMPLATE` is a loop failure.

### Unit 7 — Synthesizer (Synthesis mode)
**Interface:** `synthesize(ast, constraints: Constraints) -> AST | UNSAT` where
`constraints` = IC (∀θ,θ′: u(θ,truthful) ≥ u(θ,lie)), IR (∀θ: u(θ) ≥ 0),
Budget Balance (Σ payment(θ_i) ≤ B).
**Behavior:** reuses the AST→Z3 translation from Unit 5's fragment, but declares
each `Unknown` leaf as a Z3 free variable and issues `solve` for a model
satisfying all constraints simultaneously (rather than `prove` no deviation
exists). On SAT, substitute the model's values back into the AST → concrete AST,
which then flows through Serializer → MC → Inspector for an *independent*
confirmation (the certificate must come from the checker, not the solver that
built it). On UNSAT, return `UNSAT` and the controller reports "no mechanism in
this template family satisfies the constraints" — the Architect proposes a
different template.
**Scope (from Task.md, stated as a limitation in the paper):** polynomial payment
rules with 3–5 `Unknown` parameters. Multi-variable templates are out of scope.
**Test:** a template with a known closed-form solution (textbook linear screening
menu) → synthesizer recovers parameter values that the Inspector then VERIFIES;
an over-constrained template → `UNSAT`.

### Unit 8 — Loop controller
**Interface:** `run(spec: ProblemSpec) -> ArchitectResult` with
`ArchitectResult = {status: VERIFIED|FAILED, mechanism_latex, mechanism_dict,
certificate, mode, iterations, solver_calls, wall_clock, transcript}`.
**Behavior:** implements the §3 verdict policy exactly. Owns the MC pre-filter,
the caps (5 repair / 1 restart / 2 UNKNOWN / 1 UNSUPPORTED), and the global
wall-clock backstop. Records every proposal, verdict, and counterexample in the
transcript for the paper's iteration analysis.
**Test:** mock Inspector returning a scripted verdict sequence; assert the
controller transitions, respects every cap, performs exactly one restart, and
terminates on the wall-clock backstop when the mock hangs.

---

## 6. Data flow

1. `text → intake() → ProblemSpec (+ missing_fields resolved)`
2. `retrieve(spec, k) → rag_hits` (always computed; used by router regardless of mode)
3. `route(spec, rag_hits) → mode`
4. loop:
   a. `propose(spec, mode, rag_hits, feedback) → ast`
   b. if `mode == Synthesis`: `synthesize(ast, constraints) → ast | UNSAT`
      (UNSAT → feedback = "template infeasible", back to 4a)
   c. `render(ast) → (mechanism_dict, latex)`
      (`OutsideParseableFragment` → feedback = hint, back to 4a, counts as an iteration)
   d. `mc_prefilter(mechanism_dict) → ok | sampled_counterexample`
      (violation → feedback, back to 4a, no solver call)
   e. `verify({**spec_meta, "category": mode_category, "mechanism": mechanism_dict})
       → result`
   f. verdict policy → STOP with `ArchitectResult` | set `feedback`, back to 4a
5. on STOP-VERIFIED: certificate = `result.conditions` + the Z3/SOS artifact +
   provenance (Hybrid); emit `ArchitectResult`.

---

## 7. Error handling

| Failure | Handling |
|---|---|
| Intake can't extract a required field | `missing_fields`; interactive prompt or logged default |
| Architect emits malformed AST | schema-validate before serialize; malformed → immediate re-propose, counts as an iteration, cap applies |
| AST outside parseable fragment | `OutsideParseableFragment(hint)` → feedback, re-propose |
| Synthesizer UNSAT | report template-infeasible; Architect changes template |
| Inspector `UNKNOWN` | reformulate ≤2, then FAIL with the last conditions |
| Inspector `UNSUPPORTED` | force verifiable family ≤1, then FAIL |
| Inspector `VERIFIED_TEMPLATE` | FAIL + log (multi-type proposal likely) |
| Z3 hang / runaway loop | global per-request wall-clock backstop → FAIL with partial transcript |
| Repair budget exhausted | FAIL; `ArchitectResult` carries the full transcript and the closest counterexample |

Every FAIL is a first-class, reported outcome with the transcript attached — never
a silent empty result.

---

## 8. Evaluation (the paper's results section)

**Baselines:** Retrieval-only (Approach A as an ablation of this system);
Liu et al. (arXiv:2502.12203) re-run on the FL benchmarks; RegretNet where the
setting admits it.

**Metrics:** IC regret (0 for entry-specific VERIFIED; numeric bound from Track 3
otherwise); verified-rate per mode; iterations-to-verify (distribution, and the
diminishing-returns curve vs. the literature's 2–4); wall-clock; solver-call count
(quantifies MC pre-filter savings).

**Benchmark set:** the three FL-specific benchmarks named in Task.md — cross-device
FL with quadratic costs, hierarchical FL with edge servers, IIoT FL with
log-linear utilities — plus classic Myerson virtual-valuation and VCG-redistribution
as correctness anchors with known optima.

---

## 9. Explicitly deferred (YAGNI for v1)

- **AST-native verifier paths** (LaTeX removed from the verify path entirely) —
  separate future-scope doc `2026-08-28-ast-native-verifier-future-scope.md`.
  Revisit only if Unit 5's parseable fragment proves too restrictive in practice.
- **Collusion / 2–3 client coalition encoding** — Task.md flags it largely
  intractable; stated as a limitation, not built.
- **Feeding verified synthesized mechanisms back into the corpus** for future RAG —
  one-line hook point, deferred.
- **Web UI** — the demo is `architect "my FL setup..."` on the CLI; the paper needs
  numbers.
- **Rich novelty scoring** — cosine distance + one LLM yes/no is sufficient for
  mode selection.

---

## 10. Module layout

```
src/architect/
  ast.py            # Step 0 — node definitions, schema validation
  intake.py         # Unit 1
  router.py         # Unit 2
  rag.py            # Unit 3
  architect.py      # Unit 4 — the three prompt templates + propose()
  serialize.py      # Unit 5 — render() + round-trip checker
  synthesize.py     # Unit 7
  loop.py           # Unit 8 — controller, verdict policy, MC pre-filter
  mc.py             # Monte-Carlo pre-filter (shared)
  cli.py            # `architect "<free text>"`
src/tracks/         # Stage 1 — + parse_only hooks (additive)
tests/architect/    # one test module per unit
docs/
  ast-coverage.md   # Step 0 output
```

---

## 11. Build sequence

1. **Step 0** — AST schema + corpus-coverage audit. Gate: ≥ 90% round-trip on
   entry-specific-VERIFIED mechanisms.
2. **Unit 5 + `parse_only` hooks** — serializer and round-trip checker first; it
   is the load-bearing boundary and everything downstream depends on it.
3. **Unit 6 wiring** — call `verify()` on a serialized AST end-to-end (no LLM yet,
   hand-built ASTs).
4. **Unit 8 skeleton + MC pre-filter** — controller with a mock Architect;
   verdict policy fully tested against mocks.
5. **Units 1–4** — Intake, router, RAG, Architect. Retrieval mode working
   end-to-end.
6. **Unit 7** — Synthesizer. Synthesis mode working end-to-end.
7. **Hybrid** — Architect prompt + provenance in serializer/certificate.
8. **Evaluation harness** — benchmarks, baselines, metrics collection.

Each step ships with its tests green before the next begins.
