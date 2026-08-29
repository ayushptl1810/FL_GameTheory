# Spec — Verifier Proper-Check Roadmap

**Date:** 2026-08-29
**Status:** Planned. Sequenced; not yet started.
**Parent:** `2026-08-28-architect-cegis-loop-design.md`
**Supersedes (promotes):** `2026-08-28-ast-native-verifier-future-scope.md`
Part 1 (Approach C) and Part 2b (real VCG check) — those move here as Phases 1–2.
**Trigger:** the 2026-08-29 live eval (`docs/eval-results.md`, `gpt-oss-120b`,
12 benchmarks) — 8/12 VERIFIED, **all 4 failures VCG** — plus the Task D
adversarial soundness suite, which showed the VCG track does no real
entry-specific verification (regex-matches the payment-rule LaTeX shape and
returns a canned verdict) and that all three category verifiers fall back to a
generic template that returns `VERIFIED_TEMPLATE` regardless of the entry's own
math.

## Goal

Every family the Inspector claims to cover gets a **real solver-backed proof or
a real counterexample** — no regex-shape verdicts, no generic-template passes
reported as anything but `UNKNOWN`. Accept the added complexity; a smaller set
of families each genuinely proven beats a larger set half-proven.

## Why Approach C first

The Architect already emits a **typed AST** (`Const, Sym, Unknown, Sum, Prod,
Pow, Func{ln|exp}, IndexedFamily`). Today that AST is serialized to LaTeX and the
verifier **re-parses the LaTeX** with SymPy. Most failures in the eval and the
corpus audit are *parser* failures, not *math* failures: `\sum_{i \in S}`
unsupported, `c_i (P_i)` misread as a function call, `\mathcal{X}` mistokenised,
comma-subscripts rejected. Widening a per-family checker while the LaTeX parser
sits in the loop means fighting SymPy's parser for every notation in 185 papers —
unbounded. Consuming the AST directly makes each family checker a bounded,
one-time job: *encode ~8 known node types into Z3 / SOS / interval terms.*

---

## Phase 1 — Approach C: AST-native verify path

Remove LaTeX from the verify path. LaTeX stays a pure *output* format (paper,
corpus insertion).

```
now:      AST → render LaTeX → parse LaTeX → solver encoding → verdict
Phase 1:  AST ─────────────────────────────→ solver encoding → verdict
```

**Work**
- `verify_from_ast(ast, category, params) -> VerificationResult` alongside the
  existing `verify(entry)`. `verify(entry)` stays the corpus-facing API;
  `verify_from_ast` becomes the loop-facing API. Shared solver-level logic; only
  the front end differs.
- Per track, `build_encoding(ast_subtree)` walking AST nodes to solver terms:
  - Track 1 → Z3 expressions (reuses the `Unknown`→free-var machinery already in
    Synthesis mode — itself a partial AST-native encoding).
  - Track 2 → CVXPY polynomial for the SOS certificate.
  - Track 3 → `mpmath.iv` interval expression.
  - Track 4 → SymPy expression for symbolic integration.
- The serializer's round-trip gate (`parse(render(ast)) ≈ ast`) is retained only
  for the *corpus-insertion* path, not the verify path.

**Done when** the loop's `inspect` step calls `verify_from_ast` and no
`OutsideParseableFragment` rejection can occur for a well-formed AST;
`live_smoke` + the eval run with zero parse-error transcript entries.

**Risk** — re-touches all four tracks and the test suite. Mitigate by keeping
`verify(entry)` byte-identical (the corpus regression check must stay green:
VERIFIED 25 / VERIFIED_TEMPLATE 73 / UNKNOWN 2 / UNSUPPORTED 5).

---

## Phase 2 — Real VCG check + constrained VCG generation

**2a — Verifier.** A genuine Track-1 DSIC check for the discrete VCG fragment:
encode allocation `x(b)`, payment `p(b)`, `u_i = v_i · x_i − p_i` over a finite
bid grid; prove `∀ b_i' in grid: u_i(b_i = v_i) ≥ u_i(b_i')` and `u_i ≥ 0`
(IR). Same shape as Track 1's existing Contract screening proof.
- Continuous values / `argmax` allocation rules: discretise to a grid (exact on
  the grid, stated as such) or encode the argmax as a Z3 constraint set.
- Retire the regex-shape path: rename its verdict `VERIFIED_SHAPE` until 2a
  lands, then delete it. Recompute the corpus VCG entry-specific count against
  the real check (expect it to drop well below the current 19).

**2b — Generator.** In Synthesis mode for VCG, do not let the LLM freehand the
payment. Fix the payment to the Clarke-pivot form and let the search choose only
the **allocation rule** and per-agent **weights** — the affine-maximizer family
`Σ wᵢ·vᵢ(o) + γ(o)`. Roberts' theorem: on unrestricted domains this *is* the
complete truthful family, so this is principled search, not a heuristic. On the
restricted FL domains, state it as "exhaustive within the affine-maximizer
class" (already the wording in `Task.md` after novelty-hardening Task A).

**Done when** at least 2 of the 4 VCG eval benchmarks reach entry-specific
`VERIFIED` with a Z3 certificate, and `vcg_clarke_shaped_payment_wrong_allocation`
(currently `xfail` in `tests/verifier/`) returns `COUNTEREXAMPLE`.

---

## Phase 3 — Fail-close the template fallbacks; widen the entry-specific parsers

**3a — Fail-close.** The generic Contract / Stackelberg / VCG template paths
return `VERIFIED_TEMPLATE` for any entry regardless of its own math. Make them
return `UNKNOWN`. This is a soundness fix, not a feature. Accept the consequence:
~61 corpus entries drop from `VERIFIED_TEMPLATE` to `UNKNOWN`, and several
`tests/architect/` e2e tests need their expected verdicts updated. That lower
number is the honest one — it is what the system can actually prove.

**3b — Widen entry-specific coverage (now AST-fed, per Phase 1).** Cover the
cases the LaTeX parser used to bail on, encoded from AST nodes instead:
- Contract: `\sum`-style menu aggregation, ≥2 distinct type subscripts,
  `n−1`-arithmetic notation, `f_{sub}(arg_{sub})` families.
- Stackelberg: set/inequality summation bounds (`\sum_{i \in S}`,
  `\sum_{a \le i \le b}`), multi-variable followers (fail-closed for now,
  documented), norm notation.

**Done when** the 5 `xfail`'d fixtures in `tests/verifier/` are re-triaged —
each either passes (real check now engages) or carries a concrete, current
reason; and the corpus verdict breakdown is re-published in `Task.md` with the
post-fail-close numbers.

---

## Phase 4 — Bounded coalition / small-Shapley checks

- Generalise `verify_coalition_ic_contract` (novelty-hardening Task F, 2-type
  Contract) to k ∈ {2, 3} and to VCG allocations.
- Shapley: restrict to k ≤ 3, encode the characteristic function `v(S)`, prove
  IC for Shapley payments over that restricted coalition space. Retire the
  unconditional `UNSUPPORTED` only for entries that carry a `v(S)`.

**Done when** ≥1 Shapley corpus entry and ≥1 VCG benchmark carry a
machine-checked `coalition_ic_2` (or `_3`) result.

---

## Non-goals — the formal ceiling

A "proper check" is a real solver proof **within a stated formal model**, not
correctness in every deployment. Out of scope because they are provably
intractable or break the model's assumptions, not because they are unbuilt:

- General Shapley-value IC on unrestricted coalitional domains (Roberts).
- n−1 collusion (only k ≤ 3 is tractable).
- VCG IC under interdependent client values (non-IID FL breaks the independent
  private values the proof needs).
- Real-deployment manipulability of the output signal (fake gradients) —
  a deployment question, not a mechanism-proof question.

These are named explicitly in `Task.md` ("Four FL-specific properties…") and any
writeup must keep them named.

---

## Sequencing

1. Phase 1 (Approach C) — unblocks everything else; no user-visible verdict
   change if `verify(entry)` is held byte-identical.
2. Phase 2 (VCG) — the concrete gap the eval exposed.
3. Phase 3 (fail-close + widen) — the honesty pass; expect the headline
   VERIFIED-template count to fall.
4. Phase 4 (coalition / small-Shapley) — the bounded extension.

`2026-08-28-ast-native-verifier-future-scope.md` Part 2 (a novel certified FL
mechanism) and Part 3 (multivariable transcendental IC) remain research
future-scope — not part of this roadmap.
