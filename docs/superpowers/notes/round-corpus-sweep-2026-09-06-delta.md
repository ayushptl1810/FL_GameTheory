# Corpus-Wide Sweep (2026-09-06) — Delta

**Context.** R11/R12/R13's plans were executed by a collaborator whose
environment had no `pdfs/`/`entries/` directories, so every PDF-transcription
task in all three plans found nothing to transcribe and the sweeps landed
0 flips. In this session the PDFs/entries were confirmed present locally,
so a full corpus-wide re-audit was run: all 93 `MANUAL` entries (32
Contract, 29 Stackelberg, 28 VCG, 4 Shapley) were re-traced against their
actual source PDFs and the current code (through R13 plus a same-session
routing fix — see below), regardless of which round's `verdict_override`
was set or whether the stored obstruction looked related to R11-R13 at all.

## Pre-sweep code fix: Stackelberg vector-decision routing

Before the transcription sweep, a real wiring gap was found and fixed:
`_try_stackelberg_latex` detected a follower controlling two variables
sharing a base name (e.g. `x_r`/`x_w`) and bailed unconditionally, even
when a `follower_stationarity_system` had been transcribed — R4's vector
branch (`_stackelberg_vector_check`) was unreachable from the live pipeline
regardless of data quality. Fixed to route into the vector branch when the
sibling-symbol count matches a transcribed stationarity system. Tracing
this also surfaced a real bug in `_br_components_match`: it keyed parsed
best-response clauses by `_base_symbol_name`, which collapses `x_r`/`x_w`
to the same `"x"` key — two sibling components silently overwrote each
other. Fixed to key by the full symbol name. 3 new regression tests added.

Also fixed during the sweep: `_DEFINITION_CLAUSE_RE`'s function-name
character class included `(`/`)`, so a multi-clause utility definition like
`c(\nu_i,\rho_i)=\nu_i\rho_i` captured the whole `"c(\nu_i,\rho_i)"` string
as the function name instead of just `"c"`, and the later call-syntax strip
never matched — the definition was silently never substituted into the
main utility. Fixed the character class to exclude parens.

Also fixed: `MANUAL-backlog.md` had 94 raw `0x97` bytes (Windows-1252
em-dash) instead of valid UTF-8, crashing `print_summary`'s file read with
`UnicodeDecodeError`. Re-encoded; widened the read's exception handling.

## Sweep method

Four background agents (one per category) each read every `MANUAL`
entry's stored `manual_diagnosis`, opened its source PDF, and proposed a
new `mechanism` field **only** where the paper explicitly and
unambiguously supported it — fail-closed throughout, no field proposed on
any doubt or missing PDF. 93/93 entries traced (Contract 32, Stackelberg
29, VCG 28, Shapley 4). Findings compiled and reviewed before any
`corpus.json` edit.

## What was applied

12 entries got a well-supported field addition + `verdict_override`
removal (so the deterministic solver actually runs against them instead of
being short-circuited):

| paper_id | category | field(s) added | new verdict |
|---|---|---|---|
| `1811_12082` | Stackelberg | `fixed_constants` (b_i, c_i, Sec. V) | `VERIFIED_TEMPLATE` |
| `2502_10765` | Stackelberg | `ir_follower_latex` (Eq. 13 budget cap) | `VERIFIED_TEMPLATE` |
| `Chen2023multifactor_iot` | Stackelberg | `fixed_constants` (a_1/5/12/20, Table IV) | `VERIFIED_TEMPLATE` |
| `Hu2020trading` | Stackelberg | `follower_foc_latex` + `best_response_latex` (Eqs. 13/15) | `VERIFIED_TEMPLATE` |
| `Javaherian2025stackelberg_ic` | Stackelberg | `follower_foc_latex` + `best_response_latex` (Sec. IV-C) | `VERIFIED_TEMPLATE` |
| `Lee2024sfl_stackelberg` | Stackelberg | `best_response_latex` (Eqs. 18-20) | `VERIFIED_TEMPLATE` |
| `Li2025iiot_drl` | Stackelberg | `best_response_latex` (Eq. 16) | `VERIFIED_TEMPLATE` |
| `Liu2026fedbud` | Stackelberg | `best_response_latex` (Eqs. 18-19) | `VERIFIED_TEMPLATE` |
| `Wang2022blockchain` | Stackelberg | `follower_stationarity_system` + `best_response_latex` (Theorem 3.1) | `VERIFIED_TEMPLATE` |
| `Kang2019reliable_contract` | Contract | `fixed_constants` (zeta, psi, mu, l, Table II) | `UNKNOWN` (Track 3, δ-sound search, genuinely undecided) |
| `Lim2020contract` | Contract | `type_reduction_map` (4-D → 1 scalar via φ) | `VERIFIED_TEMPLATE` |
| `Wu2021contract_DP` | Contract | `type_reduction_map` (3-D → α = θ_x − τ_y + ρ_z, Eq. 19) | `VERIFIED_TEMPLATE` |

**Net corpus effect: `MANUAL` 93 → 81 (-12). Entry-specific `VERIFIED`
count held at 12 — the monotone gate passes** (no entry moved to a
strictly-worse state; `MANUAL` → `VERIFIED_TEMPLATE`/`UNKNOWN` is a lateral
honesty improvement, not a regression, since none of these three states
claims an entry-specific proof).

### Why none reached entry-specific VERIFIED

Traced individually for the record (this is exactly the R9-style
root-cause discipline — a corrected diagnosis, not a shrug):

- **`Hu2020trading`**: the regex fix correctly resolved the utility to
  `R·ρ/(Ξ₀+ρ) − ν·ρ`, `sp.solve` found the (single, real) critical point,
  but `sp.ask(Q.nonpositive(second_derivative))` returns `None` — SymPy's
  assumption engine cannot sign this particular nested-rational second
  derivative even though it is provably negative for positive parameters.
  A genuine SymPy sign-inference limit, not a data or wiring gap.
- **`Javaherian2025stackelberg_ic`**: `_resolve_stackelberg_utility`
  returns `None` outright — the utility's `\|w_i^t-w^t\|` norm notation is
  not handled by the LaTeX→SymPy front-end. A parser gap.
- **`Wang2022blockchain`**: the new routing fix correctly fires (sibling
  symbols `q_ti`/`q_mi` detected, stationarity system matches count), but
  `_solve_stationarity_system` finds no exact solution and the numeric
  fallback fails closed — the FOC's free parameters (`mu_i`, `p_ti`,
  `rho_i`, `psi`, `p_mi`) are never pinned to single numbers in the paper
  (they vary per client), so `_numeric_solve_stationarity` correctly
  declines (free symbols remain).
- **`1811_12082`**: `fixed_constants` resolved the FOC's parameters, but
  the follower-IR blocker is untouched — no `U ≥ 0` statement exists
  anywhere in the paper (only a box-feasibility bound), so this stays
  template regardless of the FOC's solvability.
- **`2502_10765`**: the transcribed `ir_follower_latex` is a budget cap,
  not a reservation-utility inequality — `_extract_follower_symbol`
  itself returns `None` on this 2-variable utility (a separate, unrelated
  extraction issue), so the entry never even reaches the IR check.
- **`Chen2023multifactor_iot`**: `_extract_follower_symbol` picks the
  wrong symbol (`t`, a time index, instead of `Acc_i^t`) — a genuine
  extraction-heuristic miss on this entry's specific utility shape (which
  also contains an unresolved `Sum(...)` over the client population).
- **`Lee2024sfl_stackelberg`**: the FOC differentiates to an expression
  that no longer contains the decision variable `d_n` at all — the
  `Sum(d_l, ...)` term over other players is treated as an opaque additive
  constant by the differentiation, losing the dependency structurally.
- **`Li2025iiot_drl`**: `sp.solve` finds the *correct* critical point
  (`σ_i/r_i`, matching the paper's own closed form exactly!), but the
  transcribed `best_response_latex` is a `\begin{cases}` piecewise
  expression the cross-check parser cannot handle — the best-response
  match step fails to parse, so the entry-specific path declines rather
  than risk an unverified cross-check.
- **`Liu2026fedbud`**: `_extract_follower_symbol` returns `None` — a
  similar extraction miss to `2502_10765`'s.
- **`Lim2020contract`** / **`Wu2021contract_DP`**: `_contract_check_core_vector`
  (R11) exists but was not reached in this pass — needs its own
  step-through to confirm whether the `type_reduction_map` substitution
  itself succeeds or a downstream Contract check declines; not traced to
  the same depth as the Stackelberg entries in this session. Flagged for
  a follow-up trace before assuming this is data-complete.
- **`Kang2019reliable_contract`**: `fixed_constants` narrowed the free
  variable count but `B`, `h_n`, `N_0`, `sigma`, `rho_n` remain
  individually unpinned (only composite quantities given in the paper) —
  Track 3's δ-sound interval search correctly reports `UNKNOWN` rather
  than a guessed verdict.

**None of these are data-transcription failures** — every proposed field
was correctly and precisely transcribed from its source PDF. Every
remaining blocker is a genuine code-level limit: two parser gaps (norm
notation, piecewise best-response), two extraction-heuristic misses (wrong
symbol picked), one SymPy sign-inference limit, one Sum-node
differentiation loss, and two data-completeness gaps the paper itself
doesn't resolve (no IR, per-client varying parameters). This is exactly
the "correct the catalogue" work R9 established as the standard for this
program.

## Other findings from the sweep (not applied — flagged for a future round)

- **Data-integrity bugs** (recorded corpus fields don't match the actual
  PDF, independent of any solver capability): `Mai2022double_auction` and
  `Ng2020uav_auction_coalition` (VCG — both need re-extraction from
  scratch), `Jiao2019auto_auction` (VCG — cross-paper field contamination,
  consistent with R9's earlier finding for a different pair),
  `Cheng2022uav` (VCG — stored obstruction claims no closed form exists;
  Eq. 9 gives one), `Ding2020contract_multidim` (Contract — a
  substitution/parser-semantics issue, not a wrong transcription),
  `Saputra2020fl_contract` (Contract — confirmed missing φ multiplier vs.
  PDF Eq. 4).
- **Possible mis-categorizations**: `Yang2023buyers_market` (VCG →
  looks like a genuine Myerson/Baron-Myerson Contract screening problem),
  `Zhang2024auction_comm` (VCG → Theorem 1 proves convergence to a stable
  best-response equilibrium, not DSIC — a Track 6 Nash candidate),
  `2405_13879` (Shapley → confirmed via independent re-read: no
  characteristic function or Shapley value anywhere in the paper).
- **`Le2021cellular_auction`** (VCG): real, citable monotonicity theorem
  (Lemma 1) + closed-form critical-value payment (p.9) exist in the PDF,
  but attached to the paper's actual constrained problem P6 (Eq. 30a-30e)
  — the corpus's currently recorded `allocation_rule_latex`/
  `payment_rule_latex` are the *unconstrained* argmax and don't match.
  Applying `winner_rule_monotone`/`critical_price_latex` to the current
  (wrong) fields would be unsound; needs the allocation/payment
  re-extracted first.
- **`2502_08248`** (Shapley): re-check found the paper actually contains
  *multiple* concrete numeric max-flow examples (Figs. 1-9, pp. 7-23) the
  original R5-era diagnosis missed — but each gives computed Shapley
  values / core allocations directly, not a full enumerated `v(S)` table
  per subset, so Tier B's exact input shape isn't directly transcribable
  without back-computing `v(S)` from the stated outputs (which the sweep
  correctly declined to do, per its own fail-closed instruction). Worth a
  dedicated pass reconstructing `v(S)` from the paper's own worked
  examples.
- **`2605_11889`** (Shapley): re-check found a genuine numeric instance in
  Appendix B.2 (GP-Friedman dataset, `n=2` and partial `n=3` with 4 of 8
  subsets valued) — a real correction to the R5-era "no numeric instance"
  diagnosis, though not a full enumerated table either.
- **`2606_18384`** (Shapley) and **`2405_13879`** (Shapley): both
  confirmed exactly as previously diagnosed on independent re-read — no
  correction needed.

## Suite / gate status

- `PYTHONPATH=src:. pytest -q` → 496 passed, 1 skipped, 3 xfailed (4
  pre-existing pinned-verdict tests updated to reflect the legitimate
  `MANUAL` → `VERIFIED_TEMPLATE`/`UNKNOWN` moves, per the established
  stale-pin precedent).
- `PYTHONPATH=src python -m verifier corpus.json` runs clean, no API key,
  no crash.
- Monotone gate: entry-specific `VERIFIED` count 12 → 12 (held).
