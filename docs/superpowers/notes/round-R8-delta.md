# Round R8 — ARCHITECT_AST_VERIFY flip + docs — Delta

**Landed 2026-09-06.** Branch `round-R8-ast-verify-flip`, off `main` @ `637d58d`.
Plan: `docs/superpowers/plans/2026-09-06-R8-ast-verify-flip.md`.

## Flip decision

BLOCKED/REGRESSION — not flipped. Task 1 ran the real flagged `run_eval`
(NVIDIA provider, `--seeds 1`, no `--ablations`, no `--with-baselines`, both
arms completed against the full 12-benchmark `BENCHMARKS` list, no API/infra
block). Result, by the brief's own literal CLEAN/REGRESSION rule: 4 of the 7
baseline-`VERIFIED` benchmarks (`cross_device_quadratic`, `myerson_single_item`,
`vcg_cavallo_redistribution`, `contract_budget_balanced`) flipped to `FAILED`
under `ARCHITECT_AST_VERIFY=1`; 2 additional benchmarks newly verified
(`vcg_clarke_pivot`, `contract_linear_quadratic_effort`). Net: 7/12 → 5/12
verified. That is a literal REGRESSION, so per the plan's own text ("Do not
flip the flag on unclean evidence") the flag stays default-off — no code
change to `src/architect/inspect.py` or `src/architect/loop.py`, no test
changes. Caveat: both arms used `--seeds 1` with no repeated-seed averaging,
and the raw logs already show run-to-run mode/iteration-count variance
independent of the flag on benchmarks otherwise identical between arms, so a
single seed cannot cleanly separate "the flag causes worse verification" from
"single-seed LLM sampling noise flips outcomes regardless of the flag." Full
evidence and tables: `docs/superpowers/notes/round-R8-run-eval-attempt.md`.

## Corpus effect

None (loop-side change only, no flip). Final in-scope state, unchanged from
R6–R7: `VERIFIED` 11, `VERIFIED_SHAPE` 8, `MANUAL` 86, `VERIFIED_TEMPLATE` 0,
`UNKNOWN` 0.

## Program summary (R1–R8)

| Round | What shipped | Corpus effect |
|---|---|---|
| R1 | Formalizer pipeline, smoke-tested | +0-4 (smoke only) |
| R2 | VCG corpus sweep | +3 VERIFIED (entry-specific), 20 MANUAL, VERIFIED_SHAPE 33→10, UNKNOWN 2→0 (VCG slice) |
| R3a/R3b | Contract + Stackelberg sweep | +0 VERIFIED (diagnose-only both slices), 40 MANUAL (Contract 25 + Stackelberg 15), VERIFIED_TEMPLATE 59→22 combined; UNKNOWN 0 across VCG+Contract+Stackelberg after R2+R3. Source: `round-R2-R3-delta.md` |
| R4 | Track widenings | +2 VERIFIED (`Tian2021contract`, `Zheng2023fl_market`), −2 MANUAL (reclaimed); in-scope UNKNOWN held at 0. Source: `round-R4-delta.md` |
| R5 | Coalition/Shapley track | +0 VERIFIED, 4 MANUAL |
| R6-R7 | Second-formalizer pass + honesty gate | +0 VERIFIED, +24 MANUAL; UNKNOWN/VERIFIED_TEMPLATE -> 0 |
| R8 | ARCHITECT_AST_VERIFY flip + docs | +0 (loop-side; flip BLOCKED/REGRESSION, not flipped) |

**Final:** VERIFIED 11 / VERIFIED_SHAPE 8 / MANUAL 86 / VERIFIED_TEMPLATE 0 /
UNKNOWN 0, of 105 in-scope entries. `UNKNOWN = 0` — the program's success
metric — is met. `MANUAL-backlog.md` (86 entries, 10 obstruction families) is
the deliverable: the honest floor, not a dumping ground, per the program's
own definition in the roadmap spec's Goal section.

## What's left

Per the roadmap spec's closing line: "The only remaining work after R8 is a
human opening `MANUAL-backlog.md` and doing mathematics." No further rounds
are scheduled under the original R1–R8 program (R9/R10 are named follow-on
rounds outside this program's scope, per the roadmap spec).
