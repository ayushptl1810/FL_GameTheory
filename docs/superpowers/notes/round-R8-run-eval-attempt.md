# R8 — flagged `run_eval` attempt

**Date:** 2026-09-04/05 (two long-running real-LLM invocations, NVIDIA provider)

**Command(s):**

```bash
# Un-flagged (current default) run, for comparison
PYTHONPATH=src ARCHITECT_LLM_TIMEOUT_S=300 \
  python -m architect.eval.run_eval --seeds 1 2>&1 \
  | tee docs/superpowers/notes/round-R8-run-eval-baseline.log

# Flagged run — the actual R8 flip criterion
PYTHONPATH=src ARCHITECT_AST_VERIFY=1 ARCHITECT_LLM_TIMEOUT_S=300 \
  python -m architect.eval.run_eval --seeds 1 2>&1 \
  | tee docs/superpowers/notes/round-R8-run-eval-flagged.log
```

Both invocations used `--seeds 1`, no `--ablations`, no `--with-baselines`, per
budget. Each ran roughly 1.5-2 hours of real wall-clock time against 12
benchmarks (the full `BENCHMARKS` list) via the NVIDIA LLM provider configured
in `.env` (`ARCHITECT_LLM_PROVIDER=nvidia`, `NVIDIA_API_KEY` present).

## Outcome: REGRESSION

Both runs completed and each wrote `wrote docs/eval-results.md (12 base rows,
0 ablation rows)` -- no exception, no traceback, both produced
`docs/eval-results.md` + `docs/eval-results.json`.

**Un-flagged (baseline) result table** (reproduced verbatim below; the
`round-R8-run-eval-baseline.log` file is a one-line completion marker only —
the table itself is not saved anywhere else):

| name | mode | status | iters | solver | wall_s | ic_regret | expected_family | family_match |
|---|---|---|---|---|---|---|---|---|
| cross_device_quadratic | Synthesis | VERIFIED | 1 | 1 | 109.6 | 0.0 | Contract | True |
| hierarchical_edge | Hybrid | VERIFIED | 2 | 1 | 262.66 | 0.0 | Stackelberg | True |
| iiot_log_linear | Synthesis | FAILED | 4 | 1 | 647.74 | nan | Stackelberg | True |
| myerson_single_item | Synthesis | VERIFIED | 4 | 1 | 616.31 | 0.0 | VCG | True |
| vcg_redistribution | Synthesis | VERIFIED | 1 | 1 | 103.07 | 0.0 | VCG | True |
| contract_2type_screening | Synthesis | FAILED | 4 | 0 | 770.56 | nan | Contract | None |
| contract_3type_screening | Synthesis | FAILED | 4 | 0 | 702.05 | nan | Contract | None |
| stackelberg_linear_pricing | Hybrid | VERIFIED | 2 | 1 | 272.59 | 0.0 | Stackelberg | True |
| vcg_clarke_pivot | Synthesis | FAILED | 4 | 0 | 636.63 | nan | VCG | None |
| vcg_cavallo_redistribution | Synthesis | VERIFIED | 4 | 1 | 485.63 | 0.0 | VCG | True |
| contract_budget_balanced | Synthesis | VERIFIED | 4 | 1 | 588.15 | 0.0 | Contract | True |
| contract_linear_quadratic_effort | Synthesis | FAILED | 3 | 1 | 615.02 | nan | Contract | True |

7 VERIFIED: cross_device_quadratic, hierarchical_edge, myerson_single_item,
vcg_redistribution, stackelberg_linear_pricing, vcg_cavallo_redistribution,
contract_budget_balanced.

**Flagged (`ARCHITECT_AST_VERIFY=1`) result table** (verbatim from
`docs/eval-results.md` after the flagged run; `round-R8-run-eval-flagged.log`
is a one-line completion marker only, not a source of this table):

| name | mode | status | iters | solver | wall_s | ic_regret | expected_family | family_match |
|---|---|---|---|---|---|---|---|---|
| cross_device_quadratic | Synthesis | FAILED | 4 | 0 | 627.4 | nan | Contract | None |
| hierarchical_edge | Hybrid | VERIFIED | 1 | 1 | 61.92 | 0.0 | Stackelberg | True |
| iiot_log_linear | Synthesis | FAILED | 5 | 2 | 663.91 | nan | Stackelberg | True |
| myerson_single_item | Synthesis | FAILED | 5 | 0 | 654.0 | nan | VCG | True |
| vcg_redistribution | Synthesis | VERIFIED | 3 | 1 | 365.85 | 0.0 | VCG | True |
| contract_2type_screening | Synthesis | FAILED | 4 | 0 | 728.87 | nan | Contract | None |
| contract_3type_screening | Synthesis | FAILED | 3 | 0 | 670.67 | nan | Contract | None |
| stackelberg_linear_pricing | Synthesis | VERIFIED | 1 | 1 | 111.1 | 0.0 | Stackelberg | True |
| vcg_clarke_pivot | Synthesis | VERIFIED | 4 | 1 | 460.04 | 0.0 | VCG | True |
| vcg_cavallo_redistribution | Synthesis | FAILED | 5 | 0 | 686.26 | nan | VCG | True |
| contract_budget_balanced | Synthesis | FAILED | 3 | 0 | 645.19 | nan | Contract | None |
| contract_linear_quadratic_effort | Synthesis | VERIFIED | 4 | 1 | 636.91 | 0.0 | Contract | True |

5 VERIFIED: hierarchical_edge, vcg_redistribution, stackelberg_linear_pricing,
vcg_clarke_pivot, contract_linear_quadratic_effort.

**Per-benchmark diff against the brief's definition** (REGRESSION = any
benchmark that was un-flagged `VERIFIED` becomes non-`VERIFIED` flagged):

| name | baseline | flagged | verdict |
|---|---|---|---|
| cross_device_quadratic | VERIFIED | FAILED | REGRESSED |
| hierarchical_edge | VERIFIED | VERIFIED | held |
| myerson_single_item | VERIFIED | FAILED | REGRESSED |
| vcg_redistribution | VERIFIED | VERIFIED | held |
| stackelberg_linear_pricing | VERIFIED | VERIFIED | held |
| vcg_cavallo_redistribution | VERIFIED | FAILED | REGRESSED |
| contract_budget_balanced | VERIFIED | FAILED | REGRESSED |
| vcg_clarke_pivot | FAILED | VERIFIED | newly verified (not a regression) |
| contract_linear_quadratic_effort | FAILED | VERIFIED | newly verified (not a regression) |
| iiot_log_linear | FAILED | FAILED | held |
| contract_2type_screening | FAILED | FAILED | held |
| contract_3type_screening | FAILED | FAILED | held |

4 of the 7 baseline-VERIFIED benchmarks (cross_device_quadratic,
myerson_single_item, vcg_cavallo_redistribution, contract_budget_balanced)
flipped to FAILED under the flag. That meets the brief's literal REGRESSION
criterion.

## Verdict

Do not flip the flag's default on this evidence. By the brief's literal
CLEAN/REGRESSION rule, this run is a REGRESSION: 4 of 7 previously-VERIFIED
benchmarks failed when `ARCHITECT_AST_VERIFY=1` was set, while only 2
additional benchmarks newly verified. That is a net drop from 7/12 to 5/12
verified.

Caveat for Task 2's judgment call: both invocations used `--seeds 1` (a single
non-deterministic LLM seed per benchmark, no repeated-seed averaging), and the
two inline result tables above already show run-to-run variance independent
of the flag (mode flips between `Synthesis`/`Hybrid`, iteration counts differ)
for benchmarks that are identical between the two arms in every other respect
(e.g. `hierarchical_edge` and `stackelberg_linear_pricing`). Note: the raw log
files (`round-R8-run-eval-baseline.log`, `round-R8-run-eval-flagged.log`) are
each just a single completion line and are byte-identical to each other — the
variance is visible only in the inline tables above, not in the logs. A single seed
cannot cleanly separate "the flag causes worse verification" from "single-seed
LLM sampling noise is large enough to flip outcomes regardless of the flag."
Task 2 should treat this as inconclusive-but-literally-a-regression: either
re-run with more seeds before deciding, or take this single data point as
sufficient grounds to hold the flag off by default and not flip it in R8.
