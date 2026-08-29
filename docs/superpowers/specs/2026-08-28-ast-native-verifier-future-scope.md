# Future Scope — Architect + Verifier

**Date:** 2026-08-28 (Part 1); merged 2026-08-29 (Parts 2–5)
**Status:** Partially promoted. See below.
**Parent:** `2026-08-28-architect-cegis-loop-design.md`
**Sibling:** `2026-08-29-novelty-hardening.md` (merged), `2026-08-29-verifier-proper-checks.md` (the active roadmap)

**PROMOTED 2026-08-29:** Part 1 (Approach C) and Part 2b (real VCG check) moved
into `2026-08-29-verifier-proper-checks.md` as Phases 1–2 of a sequenced
verifier proper-check plan, after the live eval failed 4/4 VCG benchmarks. What
remains genuine research future-scope here: **Part 2** (a novel certified FL
mechanism) and **Part 3** (multivariable transcendental IC). Parts 1 and 2b
below are kept for their detailed sketches, which the roadmap references.

The original Parts 4 "coalition IC" and 5 "corpus trust-gap" were small and
self-contained — they shipped in `2026-08-29-novelty-hardening.md` as Tasks 7–8
(the 2-type Contract coalition check is now in `track1_z3.py`).

---

## Part 1 — AST-Native Verifier Paths (Approach C)

### What this is

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

### Why it is deferred

- **It re-touches all four tracks** and the hard-won Stage 1 test suite. Weeks of
  work, most of it re-validating behavior that already works.
- **Approach B already closes the parser-in-the-loop risk.** The round-trip check
  means a proposal that would break a parser is rejected *before* verification,
  with a repair hint — the generator never wastes an iteration on a syntax error.
- The only thing Approach B cannot do is represent a mechanism that is *checkable
  in principle* but *not expressible in the parseable LaTeX fragment*. Whether such
  mechanisms matter in practice is unknown until v1 runs on real benchmarks.

### Trigger to revisit

Promote Approach C to active scope if, during evaluation, either:

1. **The parseable fragment is materially restrictive** — a meaningful share of
   Architect proposals hit `OutsideParseableFragment` for forms that are
   genuinely verifiable (not just malformed), and the repair loop cannot route
   around it; or
2. **The round-trip check is a maintenance sink** — keeping the serializer's
   output aligned with four independently-evolving track parsers costs more than
   an AST-native encoding would.

Track the `OutsideParseableFragment` rejection rate in the Unit 8 transcript as
the primary signal.

### Sketch, if built

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
- The LaTeX renderer stays exactly as in Approach B — still needed for paper
  output and corpus insertion.

### Related deferred item

Feeding verified synthesized mechanisms back into `corpus.json` for future RAG
retrieval pairs naturally with Approach C: once mechanisms live natively as ASTs,
persisting a verified one is just serializing its AST plus the certificate, with
no LaTeX-extraction round-trip. Revisit the two together.

---

## Part 2 — A novel certified FL-mechanism result (the LegoNE bar)

**Why this is the one that matters.** LegoNE (arXiv 2508.11874) set the bar: an
LLM-architect + formal-certifier loop is only a headline contribution if it
*produces a result a human has not published* — a new mechanism, a new
impossibility, or a certified parameter boundary. "We closed the loop" is not
enough on its own.

**Concrete target.** Pick one FL setting where the optimal IC mechanism is
genuinely open, e.g. **non-IID / interdependent client values with budget
balance** (Green–Laffont applies to the IID case; the interdependent case is not
characterized). Drive Synthesis mode over an affine-maximizer-style template and
have Z3 either (a) return a certified new mechanism in that family, or (b) return
UNSAT across the template family, which — with the domain assumptions written
down — is a certified *local impossibility* and equally publishable.

**Blockers to resolve first.**
- Synthesis is limited to 3–5 polynomial parameters. A meaningful FL template
  likely exceeds that — needs either a smarter template decomposition or a
  bounded-integer encoding.
- The affine-maximizer class is a *subclass* of DSIC on restricted domains
  (Lavi–Mu'alem–Nisan 2003; Mishra–Sen 2012). Any impossibility claim must be
  scoped to "within the AMA family" unless the domain meets Roberts' conditions.

**Done when:** one benchmark has a mechanism (or impossibility) with a
machine-checked certificate that is not in the corpus and not in the cited
literature, plus a short proof-readable rendering of the certificate.

---

## Part 2b — VCG entry-specific verification (found by the Task D soundness suite)

**Why.** The 2026-08-29 adversarial soundness suite (`tests/verifier/`) showed the
VCG track does **no** entry-specific check: it regex-matches the shape of
`payment_rule_latex` and, on a match, flips its fixed template verdict to
`VERIFIED`. A Clarke-pivot-shaped payment with the item allocated to the *lowest*
bidder still returns entry-specific `VERIFIED`
(`vcg_clarke_shaped_payment_wrong_allocation`, currently `xfail`). Every
"entry-specific VERIFIED" VCG number in Task.md rests on this regex.

**Work.** A real DSIC check for the discrete VCG fragment: encode allocation
rule `x(b)` + payment rule `p(b)` + `u_i = v_i x_i − p_i` in Z3 and prove
`∀ b_i': u_i(v_i) ≥ u_i(b_i')` over the finite type grid, exactly as Track 1
already does for Contract screening. Until then the VCG "entry-specific" verdict
should be renamed `VERIFIED_SHAPE` so no reader mistakes it for a proof.

**Done when:** the xfail'd fixture returns `UNKNOWN`/`COUNTEREXAMPLE`, and the
VCG entry-specific count in Task.md is recomputed against the real check.

---

## Part 3 — Transcendental IC (`ln` / exponential utilities)

**Why.** `iiot_log_linear` FAILED in the first eval because the model kept
proposing linear-cost screening menus for a `R_i·ln(1/θ_i)` utility, and Track 3
cannot confirm it entry-specific. Log-utility and exponential-reward forms are
where a large share of real FL incentive papers actually live, so the system
currently cannot handle the interesting FL cases — only the textbook-quadratic
ones.

**Work.**
- Extend Track 3's multi-dimensional interval branch-and-bound (`check_nonneg_box`)
  to the multi-type transcendental IC case with δ-sound guarantees, not just the
  single-symbol box.
- Add an Architect prompt path that will actually emit `Func{ln}` / `Func{exp}`
  nodes for log-linear settings instead of dodging to a linear menu.
- A Track 3 "hint" path the loop controller can invoke when `expected_family`
  implies a transcendental utility.

**Done when:** `iiot_log_linear` (and ≥2 more log-linear benchmarks) reach
`VERIFIED` entry-specific, or return an honest δ-bounded IC-regret number.

---

## Priority

Part 2 is the contribution. Part 3 widens the fragment enough that Part 2 has
somewhere interesting to run (log-linear FL settings). Part 1 (Approach C) stays
lowest priority — only if the this-round eval shows the parseable fragment is the
actual bottleneck.

(Coalition IC and corpus trust-gap closure moved to the this-round spec,
`2026-08-29-novelty-hardening.md` Tasks 7–8.)
