# R6-R7 Phase 6 — second-pass sweep (raw run)

## Pinned model

**`nvidia/nemotron-3-super-120b-a12b`**

### Endpoint probe

`client.models.list()` on `https://integrate.api.nvidia.com/v1` returns ~85 ids,
but most large instruct models (`mistralai/mistral-large-2-instruct`,
`nvidia/llama-3.1-nemotron-70b-instruct`, `nvidia/llama-3.1-nemotron-51b-instruct`,
`nvidia/nemotron-4-340b-instruct`, `meta/llama2-70b`, `databricks/dbrx-instruct`,
`ai21labs/jamba-1.5-large-instruct`) return `404 … "Not found for account"` on an
actual `chat.completions` call — listed but not enabled for this API key.
`meta/llama-3.2-90b-vision-instruct` (the code's NVIDIA default) times out.

Chat models that actually answered a JSON-mode probe for this account:
- `nvidia/nemotron-3-super-120b-a12b` — 120B-class MoE instruct, clean JSON via `llm_complete` (json_mode + "return ONLY JSON" prompt)
- `openai/gpt-oss-20b` — the first-pass model

### Reasoning for the pick

`nvidia/nemotron-3-super-120b-a12b` is the largest instruct model actually
reachable on this account — roughly 6x the parameter budget of the first-pass
`gpt-oss-20b`, and it round-trips the formalize JSON contract cleanly. This is
the substantive model upgrade the brief asks for; combined with the Task-3
prior-reason hint injection (`--second-pass`), it is the real second-pass change.

---

## Sweep run

summary: {'selected': 25, 'verified': 0, 'counterexample': 0, 'unknown': 17, 'dict_only': 4} report: docs/superpowers/notes/formalize-run-2026-09-04.md

Command:

```
IDS="2403_09153,2502_20882,Lim2020contract,Ma2023joint_pricing,Saputra2020fl_contract,Saputra2021iov_contract,Saputra2021straggling,Wu2021contract_DP,1811_12082,2110_12876,2203_00270,2404_08261,2508_07676,Cao2025service,Chen2023multifactor_iot,FLamma2025stackelberg,Hu2020trading,Hu2022truthful_FEL,Javaherian2025stackelberg_ic,Lee2024sfl_stackelberg,Li2025iiot_drl,Xiao2020stackelberg_twostage,Batool2022fl_mab,Mai2022double_auction,Zheng2023fl_market"
ARCHITECT_LLM_MODEL="nvidia/nemotron-3-super-120b-a12b" ARCHITECT_LLM_TIMEOUT_S=300 \
  PYTHONPATH=src python -m architect.formalize corpus.json --second-pass --ids "$IDS" \
  --report-dir docs/superpowers/notes
```

Wall clock: ~45 min (nemotron-120b is slow; several entries hit the 300 s
per-call timeout + one retry).

## Per-entry outcome (from `formalize-run-2026-09-04.md`)

| paper_id | category | run verdict | note |
|---|---|---|---|
| 1811_12082 | Stackelberg | VERIFIED_TEMPLATE | AST built, category core returned no entry-specific result |
| 2110_12876 | Stackelberg | VERIFIED_TEMPLATE | AST built, no entry-specific result |
| 2203_00270 | Stackelberg | VERIFIED_TEMPLATE | AST built, no entry-specific result |
| 2403_09153 | Contract | UNKNOWN | LLM-extracted IC did not verify |
| 2404_08261 | Stackelberg | UNKNOWN | formalization returned no valid AST |
| 2502_20882 | Contract | UNKNOWN | LLM-extracted IC did not verify |
| 2508_07676 | Stackelberg | UNKNOWN | formalization returned no valid AST |
| Batool2022fl_mab | VCG | UNKNOWN | allocation/payment LaTeX did not parse (VCG path, no PDF, no hint) |
| Cao2025service | Stackelberg | UNKNOWN | formalization returned no valid AST |
| Chen2023multifactor_iot | Stackelberg | UNKNOWN | formalization returned no valid AST |
| FLamma2025stackelberg | Stackelberg | VERIFIED_TEMPLATE | AST built, no entry-specific result |
| Hu2020trading | Stackelberg | UNKNOWN | formalization returned no valid AST |
| Hu2022truthful_FEL | Stackelberg | VERIFIED_TEMPLATE | AST built, no entry-specific result |
| Javaherian2025stackelberg_ic | Stackelberg | VERIFIED_TEMPLATE | AST built, no entry-specific result |
| Lee2024sfl_stackelberg | Stackelberg | VERIFIED_TEMPLATE | AST built, no entry-specific result |
| Li2025iiot_drl | Stackelberg | UNKNOWN | formalization returned no valid AST |
| Lim2020contract | Contract | UNKNOWN | LLM could not confidently extract a screening IC |
| Ma2023joint_pricing | Contract | UNKNOWN | LLM could not confidently extract a screening IC |
| Mai2022double_auction | VCG | UNKNOWN | allocation/payment LaTeX did not parse |
| Saputra2020fl_contract | Contract | UNKNOWN | LLM could not confidently extract a screening IC |
| Saputra2021iov_contract | Contract | UNKNOWN | LLM could not confidently extract a screening IC |
| Saputra2021straggling | Contract | UNKNOWN | LLM could not confidently extract a screening IC |
| Wu2021contract_DP | Contract | UNKNOWN | LLM-extracted IC did not verify |
| Xiao2020stackelberg_twostage | Stackelberg | VERIFIED_TEMPLATE | AST built, no entry-specific result |
| Zheng2023fl_market | VCG | UNKNOWN | allocation/payment LaTeX did not parse |

## Flips: NONE

`verified: 0`, `counterexample: 0`. No entry reached `VERIFIED` or
`COUNTEREXAMPLE`, so `run_batch` persisted no `formalized_ast` / provenance for
any of the 25 (it only writes those on a VERIFIED/COUNTEREXAMPLE result). The
in-memory `UNKNOWN` verdicts above are transient — nothing was written to the
corpus. `corpus.json` was restored (the sweep's only on-disk change was the
trailing newline `run_batch` re-adds).

### Post-sweep keyless verifier — the 25 residuals

`PYTHONPATH=src python -m verifier corpus.json` after the sweep: summary counts
unchanged from `round-R6R7-baseline.md` — VERIFIED 11, VERIFIED_TEMPLATE 22,
VERIFIED_SHAPE 10, MANUAL 62. All 25 residual entries remain `VERIFIED_TEMPLATE`
(the verifier's per-entry detail section only expands MANUAL/UNKNOWN entries, so
none of the 25 appears there — they carry the same template verdict as baseline).

### Hand-checks

None required — 0 flips. `round-R6R7-new-verified.md` carries the single
no-flip line. All 25 proceed to Phase 7 diagnosis.

### Why the second pass reclaimed nothing

The Task-3 `--second-pass` hint is only injected on the **generic** Stackelberg
path (`formalize_entry` via `prior_reason`). The Contract path
(`formalize_contract_entry`) and the VCG path (`formalize_vcg_entry`) never
receive `prior_reason`, so for the 8 Contract + 3 VCG residuals the second pass
is a pure model swap (gpt-oss-20b → nemotron-120b) with no hint — and the walls
are structural (no screening IC stated in the paper; allocation rule not in the
{argmax, top-k, weighted-welfare} family), which a larger transcriber cannot
invent past. For the 14 Stackelberg residuals the bigger model + prior-reason
hint still could not produce an AST whose follower FOC solves to a closed-form
optimum with a decidable-sign IR: 6 built an AST that hit the template fallback
(`_stackelberg_check_core` returned None — unsolvable/again-transcendental FOC,
vector decision, or no `follower_decision` in `meta` for symbol resolution) and
8 produced no parseable AST at all. These match the Batch-C/D/E manual-review
notes: null FOC / no IR / multi-dimensional or transcendental follower problem.

