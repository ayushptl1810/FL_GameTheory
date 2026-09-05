# Round R11 — execution findings (running log)

## F1 — Missing LaTeX-parser runtime dependency (discovered Task 2)

`sympy.parsing.latex.parse_latex` requires `antlr4-python3-runtime==4.11`.
It was **not installed** in the execution environment, so `_lx_parse`
raised `ImportError` on every call and every LaTeX-driven Track-1 path
(`_solve_stationarity_system`, `_contract_check_core` LaTeX front-end,
`_try_stackelberg_latex`, ...) silently failed closed.

Effect of installing it (`pip install antlr4-python3-runtime==4.11`),
before any R11 code change:

| metric | pre-install | post-install |
|---|---|---|
| VERIFIED | 5 | 12 |
| VERIFIED_TEMPLATE | 6 | 0 |
| UNKNOWN | 1 | 0 |
| MANUAL | 93 | 93 |

Entries that improved purely from the dependency (no code change):
`Sarikaya2019stackelberg_workers`, `2307_15975`, `Li2025bayesian_incentive`
(UNKNOWN->VERIFIED), `Lim2020contract_healthcare`, `Sun2022coded`,
`Tan2025renegotiable_contract`, `Tian2021contract`.

The R11 monotone gate still passes against the original baseline (VERIFIED
only rose). The committed `round-R11-baseline.md` was **re-captured after
the install** so later gate checks run against the correct environment.
None of the 11 R11 target entries moved — they still require the numeric
fallback + PDF transcription this round adds.

**Handoff note for R12/R13:** the environment needs
`antlr4-python3-runtime==4.11` alongside sympy for any LaTeX path to work.
The repo has no dependency manifest; this is recorded here rather than
adding one against that project convention.

## F3 — no source PDFs in the repo (blocks Tasks 3, 5, 6 transcription)

`git ls-files` shows no `*.pdf` anywhere; there is no `papers/` directory.
R11 Tasks 3, 5 and 6 all require reading a paper's PDF to transcribe
`follower_stationarity_system`, `type_reduction_map`, or `fixed_constants`.
Per the plan's own fail-closed / "corpus data is declared, not inferred"
constraint, **nothing was transcribed** — fabricating equations from the
stored prose obstructions would be exactly the guessed-VERIFIED the plan
forbids. Each affected entry's diagnosis is refreshed in Task 7 instead.

## F4 — the vector Stackelberg path is unreachable from the real pipeline

R11's Architecture paragraph assumed the 3 already-transcribed entries
(`2502_10765`, `Liu2026fedbud`, `Yu2022multi_leader_fl`) reach
`_solve_stationarity_system` and bail there on a non-closed-form solve.
They do not. Traced against the current code:

- All 3 carry `verdict_override: "MANUAL"` (human review, R4/R7) — `verify()`
  returns that without running Track 1 at all.
- Even with the override removed, `_try_stackelberg_latex` extracts a
  **single** follower symbol (`_extract_follower_symbol` returns one symbol)
  and *deliberately bails* (track1_z3.py ~1619) when it detects the follower
  controls more than one variable — it never builds the symbol tuple that
  `_stackelberg_check_core`'s vector branch needs.
- `follower_stationarity_system` is therefore read by nothing in the live
  pipeline; `_stackelberg_vector_check` / `_solve_stationarity_system` are
  reachable only from their direct unit tests.

So R11's numeric fallback (Task 2) is **correct and tested but not yet
wired to a corpus entry** — routing prose/vector `follower_decision` into
`_stackelberg_check_core` as a symbol tuple is a genuine additional piece
of work the plan did not scope, and it cannot be validated here without the
PDFs (F3). The 3 overrides are left in place; their diagnoses are refreshed
in Task 7 to state this precisely.

Net R11 corpus effect: **0 flips** — a valid outcome per the umbrella
spec ("a round that reclaims 0 entries but lands correct, tested,
fail-closed capability is still valid"). What shipped: the SciPy numeric
fallback + its fail-closed guards (Task 2) and the Contract multi-dim
type-reduction path (Task 4), both tested, both dormant until a future
round wires the routing / transcribes the corpus fields.

## F2 — pre-existing failing test fixed by F1

`tests/tracks/test_stackelberg_vector.py::test_two_variable_separable_stationarity_verifies`
was failing on `main` before R11 (same `_lx_parse` ImportError root cause).
Installing the antlr4 runtime fixes it; no test change needed.
