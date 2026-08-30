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

## Phase 1 — Approach C: AST-native verify path  ✅ landed 2026-08-29

Remove LaTeX from the verify path. LaTeX stays a pure *output* format (paper,
corpus insertion).

```
now:      AST → render LaTeX → parse LaTeX → solver encoding → verdict
Phase 1:  AST ─────────────────────────────→ solver encoding → verdict
```

**Design refinement (2026-08-29, approved).** Every track already runs in two
halves: **LaTeX → SymPy expression → solver encoding → verdict** (Track 1
`_sp_to_z3`, Track 2 SymPy→CVXPY Gram, Track 3 SymPy→`mpmath.iv` lambdify,
Track 4 stays symbolic). Approach C therefore is **not** four new solver
encoders — it is **one new bridge plus reuse of every existing back-half**:

- `ast_to_sympy(node) -> sympy.Expr` — new, the only genuinely new logic. Maps
  the 8 node types (`Const, Sym, Unknown, Sum, Prod, Pow, Func{ln|exp},
  IndexedFamily`). `Unknown` → a distinguished free symbol (same treatment
  Synthesis mode already gives it). The entire "parser fragility" problem
  collapses to this one bounded function.
- **Track seams** — extract the "SymPy exprs → solver → verdict" back-half of
  `verify_vcg` / `verify_contract` / `verify_stackelberg` / `verify_track2` /
  `verify_track3` / `verify_track4` into helpers that the existing LaTeX path
  *also* calls. Behavior-preserving refactor — no verdict moves.
- `_classify_ast(m) -> int` — structural track picker over AST nodes, mirroring
  today's regex `_classify_utility` (Func{ln|exp} → 3; Pow deg≥2 + continuous
  type space → 2; expectation/`IndexedFamily` IC → 4; else 1).
- `verify_from_ast(m: Mechanism, meta) -> VerificationResult` — build SymPy from
  the AST, classify, dispatch to the seams, `finalize_verdict`. Sits alongside
  `verify(entry)`; `verify(entry)` stays the corpus-facing API and is untouched.
- **Loop cutover** — `architect/inspect.py:inspect_mechanism` calls
  `verify_from_ast(m, meta)` when `ARCHITECT_AST_VERIFY=1`; default **off**.
  `render(m)` still runs for LaTeX output either way. Flip the default on in a
  follow-up once the eval shows zero `parse` / `OutsideParseableFragment`
  transcript entries.
- The serializer's round-trip gate (`parse(render(ast)) ≈ ast`) is retained for
  the *corpus-insertion* path; it no longer gates verification.

**Done when** `verify_from_ast` is reachable from the loop behind the flag, a
parity test shows it agrees with `verify(entry)` on every loop-reachable
Mechanism shape (incl. the existing `test_loop_run_reaches_verified_via_*`
fixtures), and a flagged `live_smoke` + eval run produces zero parse-error
transcript entries.

**Risk** — the seam extraction is behavior-preserving surgery on solver code.
Frozen regression gate on every task: `python -m verifier corpus.json` must stay
**VERIFIED 25 / VERIFIED_TEMPLATE 73 / UNKNOWN 2 / UNSUPPORTED 5**, and the full
`pytest` suite green.

**Result** — `ast_to_sympy` covers all 8 node types; SymPy→solver→verdict back-half extracted behind a seam in every track. New `verify_from_ast(m, meta)` + `_classify_ast(m)` in `src/architect/ast_verify.py`; `inspect_mechanism` calls it when `ARCHITECT_AST_VERIFY=1` (default off). Parity test: matches LaTeX path on loop's VERIFIED fixtures (Stackelberg-effort + 2-type Contract), no fix needed. Regression frozen: 25/73/2/5 unchanged. Live `live_smoke` (gpt-oss-120b): 4/4 VERIFIED, zero parse-family transcript entries. Flag default stays off; Track 2 & Track 3 seam helpers still re-parse LaTeX internally (Phase 3 work).

---

## Phase 2 — Real VCG check + constrained generation  ✅ landed 2026-08-30

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

**Progress (2026-08-30, Task 5 — dispatcher wired):** `verify_vcg` now calls
`verify_vcg_dsic` (Tasks 3–4, `src/tracks/vcg_dsic.py`) first; the regex path is
a pure fallback whose success is post-mapped to `VERIFIED_SHAPE`. Corpus VCG
distribution (33 entries), before → after:

| verdict | before | after |
|---------|--------|-------|
| VERIFIED (real DSIC) | 19 (regex form-confirmed) | **0** |
| VERIFIED_TEMPLATE | 14 | **0** |
| VERIFIED_SHAPE | 0 | **33** |
| COUNTEREXAMPLE | 0 | **0** |
| UNKNOWN | 0 | **0** |

Every corpus VCG entry currently fails the real check closed (allocation/payment
LaTeX not yet parseable into an encodable spec, or absent — see
`docs/superpowers/notes/phase2-vcg-verdict-delta.md` for the per-entry reason).
Non-VCG counts all frozen. The two `xfail` VCG holes moved to the hard `BROKEN`
adversarial list (they now return `VERIFIED_SHAPE`, a documented non-proof).
Still open for "Done when": widen `vcg_dsic.py`'s allocation/payment parsers so
real entries reach `VERIFIED` / `COUNTEREXAMPLE`, and wire the AST caller
(`verify_from_ast`) — Phase 2 Task 7.

### Result (2026-08-30)

- **`verify_vcg_dsic`** (`src/tracks/vcg_dsic.py`) — finite-grid Z3 DSIC + IR
  proof. Encodable combos today: highest-bidder / lowest-bidder allocation +
  Clarke-pivot or explicit-formula payment. Multi-attribute values and
  argmax-welfare allocation → `UNKNOWN` (fail-closed).
- **Regex path retired to `VERIFIED_SHAPE`** — a new 6th verdict, explicitly not
  a proof (regex-matches the payment-rule LaTeX shape only). Kept as a fallback
  through Phase 3; delete in Phase 3b.
- **Corpus:** 0/33 VCG entries reach a real DSIC proof today — the 19 old
  "form-confirmed" VERIFIED were regex only. Parser widening to cover the
  corpus's `\frac` / `argmax` allocation forms is Phase 3. New corpus totals:
  VERIFIED 25→6 (Contract 5 + Stackelberg 1), VERIFIED_TEMPLATE 73→59,
  VERIFIED_SHAPE 33. Non-VCG FROZEN throughout.
- **Generation:** Synthesis mode now fixes the VCG payment to the Clarke pivot
  and searches only affine-maximizer weights. A synthesized
  highest-bidder + Clarke mechanism is certified `VERIFIED` by `verify_vcg_dsic`
  (Vickrey).
- **AST path:** `verify_from_ast`'s VCG branch calls the real check; the
  Approach C `entry_specific=False` stopgap is removed. Limitation: the
  `Mechanism` AST has no allocation node, so allocation/payment LaTeX ride on
  `meta` — a real VCG allocation node is Phase 3.

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
