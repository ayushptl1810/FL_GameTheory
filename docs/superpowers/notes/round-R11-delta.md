# Round R11 — Vector/Multi-Dim Decision Extension — Delta

**Landed 2026-09-06.** No branch this round (program-level deviation, see
umbrella spec). Plan:
`docs/superpowers/plans/2026-09-05-R11-vector-multidim-extension.md`.
Execution findings: `docs/superpowers/notes/round-R11-findings.md`.

## Targeted entries — before / after

| paper_id | category | before | after | method |
|---|---|---|---|---|
| 2101_05628 | Stackelberg | MANUAL | MANUAL | n/a |
| 2101_12428 | Stackelberg | MANUAL | MANUAL | n/a |
| 2502_10765 | Stackelberg | MANUAL | MANUAL | n/a |
| Guo2023stackelberg_industrial | Stackelberg | MANUAL | MANUAL | n/a |
| Li2025split | Stackelberg | MANUAL | MANUAL | n/a |
| Liu2026fedbud | Stackelberg | MANUAL | MANUAL | n/a |
| Wang2022blockchain | Stackelberg | MANUAL | MANUAL | n/a |
| Yu2022multi_leader_fl | Stackelberg | MANUAL | MANUAL | n/a |
| Lim2020contract | Contract | MANUAL | MANUAL | n/a |
| Wu2021contract_DP | Contract | MANUAL | MANUAL | n/a |
| 2308_12502 | Contract | MANUAL | MANUAL | n/a |

**0 flips.** Valid per the umbrella spec ("a round that reclaims 0 entries
but lands correct, tested, fail-closed capability is still a valid
outcome").

## What shipped

- **`_numeric_solve_stationarity`** (`src/tracks/track1_z3.py`) — SciPy
  `fsolve` fallback for a joint stationarity system SymPy's exact solver
  returns nothing for. Fixed deterministic start points `0.1 / 1.0 / 10.0`;
  a root is accepted only if **>= 2 start points agree within `1e-6`** and
  the residual is `< 1e-8`; any un-pinned free parameter symbol, an
  unlambdifiable expression, or disagreeing start points -> `None`.
  `_solve_stationarity_system` now returns `(solution_map, method)` with
  `method` in `{"symbolic", "numeric:fsolve"}`; **> 1 distinct symbolic
  solutions -> fail closed** (no numeric guess). `_stackelberg_vector_check`
  threads the method into `notes`/`conditions`. 4 new tests
  (`tests/tracks/test_stackelberg_vector_numeric.py`).
- **`_contract_check_core_vector`** (`src/tracks/track1_z3.py`) — collapses
  a `> 1`-symbol `type_variable` to one effective scalar via a paper-stated
  `mechanism['type_reduction_map']`, then delegates to
  `_contract_check_core`. Fails closed on a non-single-entry map, an
  unparseable RHS, or any surviving original type symbol. Wired into
  `_try_contract_latex` ahead of the scalar call, guarded on
  `type_reduction_map` presence. 3 new tests
  (`tests/tracks/test_contract_multidim.py`).
- **Environment fix (F1):** installed `antlr4-python3-runtime==4.11` — the
  SymPy LaTeX parser dependency was absent, so every LaTeX-driven Track-1
  path silently failed closed. Independent of any R11 code change this
  moved the corpus from `VERIFIED 5 / VERIFIED_TEMPLATE 6 / UNKNOWN 1` to
  `VERIFIED 12 / VERIFIED_TEMPLATE 0 / UNKNOWN 0` (`MANUAL` unchanged at
  93). The R11 baseline was re-captured after the install. Also fixed a
  pre-existing failing test
  (`test_stackelberg_vector.py::test_two_variable_separable_stationarity_verifies`).
- 11 corrected `manual_diagnosis` entries + an R11 batch in
  `MANUAL-backlog.md`.

## Why 0 flips (F3 / F4)

1. **No source PDFs in the repo.** Tasks 3, 5, 6 need a paper's PDF to
   transcribe `follower_stationarity_system` / `type_reduction_map` /
   `fixed_constants`. Nothing was fabricated.
2. **The vector-Stackelberg path is unreachable from the live pipeline.**
   R11's Architecture paragraph assumed the 3 already-transcribed entries
   (`2502_10765`, `Liu2026fedbud`, `Yu2022multi_leader_fl`) reach
   `_solve_stationarity_system` and bail on the solve. They do not:
   `verify()` returns their R4 `verdict_override`, and even without it
   `_try_stackelberg_latex` extracts a *single* follower symbol and
   deliberately bails on multi-variable followers — it never builds the
   symbol tuple `_stackelberg_check_core`'s vector branch needs.
   `follower_stationarity_system` is read by nothing in the live pipeline.
   R11's numeric fallback sits in that unreached branch, correct and
   tested; routing prose/vector `follower_decision` into a symbol tuple is
   genuine additional work R11 did not scope and cannot validate here
   without the PDFs.

## Corpus totals

| verdict | R11 baseline (post-antlr4) | after R11 |
|---|---|---|
| VERIFIED | 12 | 12 |
| VERIFIED_TEMPLATE | 0 | 0 |
| MANUAL | 93 | 93 |
| UNKNOWN | 0 | 0 |

Both `--only Stackelberg` and `--only Contract` gates: `GATE: PASS`.
Full test suite: 476 passed, 2 skipped, 3 xfailed.

## R12 handoff (not applied to R12's plan file per instruction)

R12 was told not to be touched this run, so its plan's "Handoff from R11"
placeholders were left as-is. The values R12 needs when it starts:

- Tolerance constants: `1e-6` start-point agreement, `1e-8` residual.
- No numeric flip occurred, so no verdict metadata was written for one; the
  entry field for verdict metadata is `z3_verdict` (confirm against an
  existing VERIFIED entry).
- SciPy/parser gotcha: `sympy.parsing.latex.parse_latex` needs
  `antlr4-python3-runtime==4.11` installed or it raises `ImportError` and
  every LaTeX path fails closed silently. Install it before any sweep.
- Post-R11 corpus counts: VERIFIED 12, MANUAL 93 (105 in-scope).
