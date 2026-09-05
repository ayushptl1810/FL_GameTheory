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

## F2 — pre-existing failing test fixed by F1

`tests/tracks/test_stackelberg_vector.py::test_two_variable_separable_stationarity_verifies`
was failing on `main` before R11 (same `_lx_parse` ImportError root cause).
Installing the antlr4 runtime fixes it; no test change needed.
