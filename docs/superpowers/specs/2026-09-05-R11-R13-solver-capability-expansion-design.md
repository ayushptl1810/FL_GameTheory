# R11–R13 — Solver Capability Expansion

**Status:** design approved 2026-09-05. Follow-on program to R9
(`docs/superpowers/specs/2026-09-05-R9-manual-root-cause-audit.md`), which
traced all 86 `MANUAL` entries to their real code-level bail point and found
**0 of 85 clustered entries confirmed fixable** — every cluster is a genuine
capability ceiling of Tracks 1-4 as currently built, not a parser bug.

## Motivation

The corpus sweep is not an academic exercise: it is the calibration test for
the same solver tracks the Architect loop uses to certify **newly
LLM-generated** FL incentive mechanisms. If Tracks 1-4 can only certify
12/105 *published, presumably-correct* mechanisms, that is strong evidence
the same tracks will fail to certify most *novel* Architect-proposed
mechanisms too — the loop's core trust promise ("LLM proposes, solver
proves, no fabricated verdicts") is bottlenecked exactly where R9 found the
ceiling.

R9's cluster analysis names three recurring capability gaps, each hit by
multiple corpus entries **and** each a shape a real FL mechanism naturally
has:

1. **Vector / multi-dimensional decisions** — Track 1's Stackelberg FOC
   reduction and Contract IC/IR substitution assume a single scalar to
   solve for. Real FL mechanisms routinely allocate resources across N
   clients (a vector decision) or screen a multi-attribute client type.
2. **Nash-equilibrium / action-set truthfulness** — no track today checks
   truthfulness proved as a best-response condition over a small discrete
   action set (`{abstain, join, buy}`) rather than type-vs-type screening
   IC. Moral-hazard and peer-prediction FL mechanisms are exactly this
   shape.
3. **Transcendental / implicit equations** — Z3's `_sp_to_z3` rejects any
   `log`/`exp`/implicit-root expression outright. Utility functions with
   exponential decay or logarithmic terms are common in FL incentive
   design.

Closing these raises the certification hit-rate on **future
Architect-generated mechanisms**, not just historical papers — that is the
actual trust gate this program serves.

## Scope

Three sequential rounds, one umbrella spec, each round's detailed plan
authored fresh — same dependency-driven pattern as R4 (authored from R2/R3's
catalogue) and R6-R7 (authored from R5's residual). This document names the
program, dependency order, and shared invariants; it does not pre-design
round internals past what's needed to sequence them.

- **R11 — Vector/multi-dim decision extension.** Targets the 13-entry
  Stackelberg vector/multi-stage cluster + 3-entry Contract multi-dim-type
  cluster (16 entries).
- **R12 — Nash-equilibrium / action-choice track.** Targets the 10-entry
  no-screening-IC family named in R9's own "R10" section (renumbered R12 to
  keep this program's rounds contiguous; same scope).
- **R13 — Transcendental/implicit root-finding fallback.** Targets the
  ~8-10 entry transcendental-FOC / opaque-log-argument cluster across
  Contract and Stackelberg.

Each round is independently shippable software with a corpus delta,
following every invariant R1-R9 already established.

**Dependency order:** R11 → R12 → R13, chosen because R11 lands the new
numeric-fallback pattern (SciPy alongside Z3/CVXPY/dReal) that R13 reuses
directly; R12 is architecturally independent (a new track, not an extension)
and could in principle run in parallel, but is sequenced after R11 so its
plan can be written with R11's actual implementation experience in hand
(numeric tolerance conventions, verdict metadata shape) rather than
guessing them twice.

## Numeric backend decision

R11 and R13 both need to move past Z3's exact-symbolic/linear-only
machinery. **Default: SciPy (`scipy.optimize.minimize`/`brentq`/`fsolve`)
with a stated error tolerance**, consistent with the original zero-UNKNOWN
spec's already-allowed VERIFIED category: "a δ-sound bound with the bound
stated" (the same discipline Track 3/dReal already uses). CVXPY (already a
Track 2 dependency) is used instead wherever a sub-problem is provably
convex, since a convex certificate is tighter and cheaper than a numeric
tolerance bound. Z3's nonlinear tactics (`nra`/`nlsat`) are rejected as the
default — known to struggle/timeout on the transcendental cases R13
specifically targets — but nothing stops a round from trying `nra` first
and falling back to SciPy if it fails fast.

Each round's plan pins the exact method (`minimize` vs `brentq` vs CVXPY)
per its own target entries at round start, the same way R2 discovered its
VCG-specific allocation-classifier approach only once it started.

## New verdict semantics

A numeric flip is still `VERIFIED`, recorded with
`{solved_by: "numeric", method: <str>, tolerance: <float>}` in the entry's
`z3_verdict`/equivalent metadata field — no new verdict type. This is
already licensed by the original zero-UNKNOWN spec's VERIFIED definition
(exact proof OR stated δ-sound bound). A numeric non-convergence, a
converged-but-unverified-optimum (e.g. a saddle point — checked via a
second start point and, where cheap, a Hessian sign check), or any
ambiguity fails closed to the entry's current verdict — never a guessed
`VERIFIED`. This mirrors Track 3's existing δ-soundness discipline exactly.

## Cross-round invariants (inherited from R1-R9, unchanged)

- Baseline snapshot before any change in each round
  (`round-R11-baseline.md`, etc.)
- Monotone `VERIFIED` gate — count only rises or holds
- Every flip cross-checked and recorded in `round-<Rn>-new-verified.md`
  (hand-derived gap, second track/method agreeing, numeric/model
  inspection, or cited theorem — same four accepted check types)
- Every entry that stays `MANUAL` keeps (or gets a corrected) reason string
  in `MANUAL-backlog.md`
- Fail-closed on any non-convergence or ambiguity
- Formalizer/LLM stays a build-time-only dependency; `python -m verifier
  corpus.json` stays reproducible with no API key and no network numeric
  service (SciPy/CVXPY run fully local and deterministic given fixed seeds)
- Regression test per widening in `tests/tracks/`, pinned to the motivating
  entries
- **No branch-per-round this program** (explicit deviation from R1-R9): work
  lands directly against the current tree per user instruction; each
  round's plan still gets independent review before its commits, but there
  is no `round-<Rn>-<slug>` branch or merge step.
- **Plan handoff:** each round's plan document ends with an explicit
  instruction to update the *next* round's plan with any issues,
  discoveries, or scope corrections found while executing — mirrors the
  R2→R3, R4-from-R2/R3, R6R7-from-R5 pattern, made explicit inline this
  time since all three plans are being written up front rather than at
  each round's start.

## Exit criterion

R11: 16 targeted entries re-swept, every flip cross-checked, delta doc
written. R12: new track landed with tests, 10 targeted entries re-swept,
`MANUAL-backlog.md` regenerated for any reclassification. R13: transcendental
fallback landed, ~8-10 targeted entries re-swept. No round promises a flip
count — Phase-1-style discovery risk applies to all three, same as every
prior round's honest-uncertainty framing. The monotone `VERIFIED`-only-rises
gate applies throughout, and any round that reclaims 0 entries but lands
correct, tested, fail-closed capability is still a valid outcome (R3a/R3b/R5
precedent) — provided it also updates the next plan with what it learned.

## Self-Review

**Placeholder scan:** all three rounds have named targets, entry counts, and
a stated dependency order; no TBD sections. Round *internals* (exact
per-entry implementation) are deliberately deferred to each plan, per the
program's established R4/R6-R7 precedent — a stated deferral, not a gap.

**Internal consistency:** the numeric-backend decision applies consistently
to both R11 and R13; R12's independence from that decision (it's a new
finite-enumeration track, not a numeric-optimization extension) is stated
explicitly rather than left implicit.

**Scope check:** three rounds, one program, same invariant discipline as
R1-R9 with two explicit, called-out deviations (no branch-per-round; each
plan ends with a mandated handoff note) — both stated as deviations, not
silently assumed.

**Ambiguity check:** "fail-closed on numeric ambiguity" is made concrete
(second start point + Hessian sign check where cheap); "no new verdict type"
is grounded in the original spec's existing VERIFIED definition rather than
asserted new.

**Risk note:** same as R9's own risk framing — this is capability-building
against an already-audited ceiling, not a guessed estimate; corpus-effect
numbers name the *targeted* entry counts (16 / 10 / 8-10) but do not promise
flips, since numeric convergence and cross-check success are genuinely
unknown until each round runs.
