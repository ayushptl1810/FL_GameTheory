# Round R3a — new VERIFIED / R6 candidates

## New VERIFIED this round

None. The R3a Contract sweep produced **0 verdict flips**; the 5 entry-specific
Contract VERIFIED entries (`2307_15975`, `Li2025bayesian_incentive`,
`Lim2020contract_healthcare`, `Sun2022coded`, `Tan2025renegotiable_contract`)
all held unchanged.

## R6 candidates

Eight Contract entries where the paper **does** state a screening IC, but the
LaTeX parser lacks the tooling to build a sound proof obligation from it. These
stay `VERIFIED_TEMPLATE` (no `verdict_override`, no MANUAL diagnosis, no
baseline rewrite): the obstruction is a fixable tooling gap, not a property of
the paper's mechanism. None carried a partial `formalized_ast` /
`formalization_meta`, so nothing needed deleting.

Distinguished from the Task 12 MANUALs by this test: a MANUAL's obstruction
survives any amount of parser work (the paper has no screening IC, the recorded
math is degenerate or population-coupled, or the encoding target itself cannot
express the term). An R6 candidate is discharged by one concrete, nameable piece
of tooling.

| Entry | Parser / tooling gap | What R6 needs |
|---|---|---|
| `Lim2020contract` | Utility formal args are component symbols (`\theta_j^n`) while the IC's actual args are **bundle symbols** `\omega_{y,z}`; `_expand_utility_call_shorthand` cannot bind one to the other. | A bundle -> component mapping. The entry never states it, so it must be read off the PDF and recorded as corpus data before the parser can use it. |
| `Wu2021contract_DP` | Same bundle-argument class (`(D,R)` formals vs bundle actuals), and the type is genuinely 3-dimensional. | The same bundle map, plus a multidimensional-type screening encoding (the current machinery carries a single type subscript). |
| `Ma2023joint_pricing` | The IC references `W_U^i`, a function the entry never defines — its `client_utility_latex` defines `U_i` instead. The IC RHS also keeps `t_i` where the contract index should be `t_k`. | Reconcile the two utility names against the PDF and fix the RHS contract index; both are transcription repairs, after which the existing expansion path applies. |
| `Saputra2020fl_contract` | `G` is an undefined opaque multi-argument function in the utility. | `G`'s algebraic form from the paper. Once inlined the IC is an ordinary screening inequality. |
| `Saputra2021iov_contract` | `C` is an undefined opaque multi-argument function. | `C`'s algebraic form (same class as above). |
| `Saputra2021straggling` | `S` is an undefined opaque multi-argument function. | `S`'s algebraic form (same class as above). |
| `2403_09153` | Prime notation `\gamma'` used as the contract index, plus a conditional bar `|\gamma`. `_get_sub` does not treat a prime as an index-distinguishing mark in this position, and the bar is not parsed at all. | Prime-as-contract-index support in the subscript extractor and a rule for the conditional bar. |
| `2502_20882` | The deviation is stated as a **predicate** (`\hat\theta_i \neq \theta_i`) rather than as a substitutable contract index, so there is no index for the parser to substitute. | A predicate-form IC normalizer that rewrites "for all reports differing from the truth" into the indexed two-sided form the substitution machinery expects. |

### Note on `2502_20882`

This is the weakest of the eight. The predicate form is a genuine parser gap,
but rewriting it soundly requires knowing that the paper's report space is the
type space and that the mechanism is direct — assumptions the entry does not
record. If R6 cannot confirm both from the PDF, this entry should be re-routed
to MANUAL rather than given a normalizer that guesses.
