# Future Scope — AST-Native Verifier Paths (Approach C)

**Date:** 2026-08-28
**Status:** Deferred. Not part of Stage 2 v1.
**Parent:** `2026-08-28-architect-cegis-loop-design.md`

---

## What this is

In the Stage 2 design, the Architect emits a typed AST, and Unit 5 (Serializer)
renders it to the `mechanism` LaTeX dict that the Stage 1 tracks parse. A
round-trip check (`parse(render(ast)) ≈ ast`) guarantees the LaTeX that reaches
the verifier is in a fragment the existing parsers handle. LaTeX still passes
*through* the verify path; it is just constrained.

**Approach C removes LaTeX from the verify path entirely.** Each track gains an
entry point that consumes the AST directly and builds its solver encoding
(Z3 / SOS / interval / SymPy) from AST nodes, with no LaTeX parsing anywhere in
the loop. LaTeX becomes a pure *output* format — rendered only for the paper and
for adding verified mechanisms to the corpus.

```
Approach B (v1):   AST → render LaTeX → parse LaTeX → solver encoding → verdict
Approach C (later): AST ─────────────────────────────→ solver encoding → verdict
```

---

## Why it is deferred

- **It re-touches all four tracks** and the hard-won 51-test Stage 1 suite. Weeks
  of work, most of it re-validating behavior that already works.
- **Approach B already closes the parser-in-the-loop risk.** The round-trip check
  means a proposal that would break a parser is rejected *before* verification,
  with a repair hint — the generator never wastes an iteration on a syntax error.
- The only thing Approach B cannot do is represent a mechanism that is *checkable
  in principle* but *not expressible in the parseable LaTeX fragment*. Whether such
  mechanisms matter in practice is unknown until v1 runs on real benchmarks.

---

## Trigger to revisit

Promote Approach C to active scope if, during Stage 2 evaluation, either:

1. **The parseable fragment is materially restrictive** — a meaningful share of
   Architect proposals hit `OutsideParseableFragment` for forms that are
   genuinely verifiable (not just malformed), and the repair loop cannot route
   around it; or
2. **The round-trip check is a maintenance sink** — keeping the serializer's
   output aligned with four independently-evolving track parsers costs more than
   an AST-native encoding would.

Track the `OutsideParseableFragment` rejection rate in the Unit 8 transcript as
the primary signal.

---

## Sketch, if built

- Add `verify_from_ast(ast, category, params) -> VerificationResult` alongside the
  existing `verify(entry)`.
- Per track, a `build_encoding(ast_subtree)` that walks AST nodes to solver terms:
  - Track 1: AST → Z3 expressions (reuses the `Unknown`→free-var machinery from
    Stage 2 Unit 7, which is itself a partial AST-native encoding).
  - Track 2: AST → CVXPY polynomial for the SOS certificate.
  - Track 3: AST → `mpmath.iv` interval expression.
  - Track 4: AST → SymPy expression for symbolic integration.
- `verify(entry)` stays as the corpus-facing API; `verify_from_ast` becomes the
  loop-facing API. Both share the solver-level logic; only the front end differs.
- The LaTeX renderer stays exactly as in Approach B — it is still needed for
  paper output and corpus insertion.

---

## Related deferred item

Feeding verified synthesized mechanisms back into `corpus.json` for future RAG
retrieval pairs naturally with Approach C: once mechanisms live natively as ASTs,
persisting a verified one is just serializing its AST plus the certificate, with
no LaTeX-extraction round-trip. Revisit the two together.
