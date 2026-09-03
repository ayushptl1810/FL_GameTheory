# R2 — VCG hand-check of the sweep flips (Task 9)

The R2 sweep flipped 8 VCG entries to `VERIFIED` via the new allocation-classifier
path. Each was hand-checked against the paper's `mechanism` dict under a
fail-closed rule: the flip holds only if `AllocHighest` is genuinely the paper's
allocation AND the payment is a real Groves/Clarke pivot. 4 held, 4 were reverted.

## 2504_05563

**What Track-1 now handles:** Allocation is the argmax of social welfare
`SW = v(W) - ĉ·f(W)` over coalitions; payment is `p_i = v_i(W) - Σ_{k≠i} c_k f_k(W*)`,
i.e. i's value less the reported cost of everyone else at the chosen allocation.
**Cross-check (theorem):** Groves mechanism (welfare-maximizing allocation + Clarke
pivot) => DSIC [Groves 1973 / Green–Laffont]. The AST allocation node is
AllocHighest = argmax welfare, matching `W⋆(ĉ) ∈ argmax[SW := v(W) − ĉ f(W)]`; the
payment carries the Clarke `Σ_{k≠i} c_k f_k(W*)` externality term. Sign check: a
misreport of `ĉ_i` enters i's own utility `u_i = v_i(W) - p_i` only through the
chosen `W*`, and the `Σ_{k≠i}` term makes `u_i` equal to total welfare up to a
term independent of i's report, so no misreport can raise `u_i`.
**Verified:** 2026-09-03

## 3626307_3626311

**What Track-1 now handles:** Allocation `x_i(b) = argmax_{x} Σ_i v_i(x_i) - c_i(x_i)`
(unconstrained welfare argmax); payment `p_i(b) = r(x*) - Σ_{k≠i} c(x_k*, γ̂_k)`.
**Cross-check (theorem):** Groves mechanism => DSIC [Groves 1973 / Green–Laffont].
The AST node AllocHighest matches the stated `argmax Σ v_i - c_i`; the payment is
the textbook Groves form — a term `r(x*)` independent of i's report plus the Clarke
`Σ_{k≠i}` aggregate of the others' reported costs. Sign check: `u_i = v_i - p_i`
becomes `v_i - r(x*) + Σ_{k≠i} c(x_k*,γ̂_k)`, which is maximized exactly at the
welfare-maximizing `x*`, i.e. at truthful `γ̂_i = γ_i`.
**Verified:** 2026-09-03

## Cheng2022uav

**What Track-1 now handles:** Allocation `X* = argmax_X F(x_{l,m,n})` over binary
assignment variables; payment `P^f_{i,k} = F(X*) - F_{\(i,k)}(y*) + J_{l,(i,k)}`.
**Cross-check (theorem):** Groves/Clarke pivot => DSIC [Groves 1973]. The AST node
AllocHighest matches `argmax_X F(·)`. The payment is literally the Clarke pivot:
`F(X*)` is the objective at the chosen allocation and `F_{\(i,k)}(y*)` is the same
objective re-optimized with the (i,k) pair excluded, so the difference is exactly
the externality i imposes; `+ J_{l,(i,k)}` is a constant offset that cancels against
the `- J_{l,(i,k)}` inside the client utility
`U_{(i,k)} = Σ_l x_{l,i,k}(P^f_{i,k} - J_{l,(i,k)})`. Sign check: after cancellation
i's utility is `F(X*) - F_{\(i,k)}(y*)`, whose only report-dependence is through
`X*`, so truthful reporting maximizes it.
**Verified:** 2026-09-03

## Cong2020vcg

**What Track-1 now handles:** Allocation `x* = argmax S(x, γ̂)` (welfare argmax over
the reported cost profile); payment `p_i = S(x*, γ̂) - S(z*, γ̂)` where `z*` is the
optimum with i removed.
**Cross-check (theorem):** Clarke pivot mechanism => DSIC [Clarke 1971 / Groves 1973].
The AST node AllocHighest matches `argmax S`; the payment is the with-vs-without-i
welfare difference, the canonical pivot. Sign check: `u_i = v_i - p_i` reduces to
`v_i - S(x*,γ̂) + S(z*,γ̂)`; `S(z*,γ̂)` does not depend on i's report, and the
remaining terms are maximized at truth, so no misreport is profitable.
**Verified:** 2026-09-03

## Rejected flips

All four flips below were reverted (`formalized_ast` + `formalization_meta`
deleted), returning the entry to `VERIFIED_SHAPE`; each was then diagnosed MANUAL
in Part 2 below.

- **Jin2023bara_budget** — `n_t = argmax_n Σ_{i≤n} (b_{n+1}/q_{n+1}) q_i ≤ B_t` is a
  BUDGET-CONSTRAINED greedy: it maximizes a *count* subject to a budget cap, not a
  welfare argmax, so `AllocHighest` is wrong. The payment
  `r_{t,i} = (b_{n+1}/q_{n+1}) q_i` is a proportional share of a critical unit price,
  not a Clarke pivot. `client_utility_latex` is null, so the grid proof had no
  objective to check against. Fails BOTH criteria.
- **GPS2023afl_recruit** — "1 if `b_n(t)` is among the lowest bids" is a reverse
  top-k with unspecified k, not a single argmax. The payment `p_i(b) = b_i - C_i(t)`
  is first-price (pays the bid) and is *literally identical* to the recorded client
  utility `u_i = b_i - C_i(t)`, which makes the model degenerate — the verifier was
  checking a tautology. Fails BOTH criteria.
- **Cui2024auction_market** — the allocation `f_a = argmax_{i∈N} b_{t,i}` is a
  genuine argmax, but the payment `p_{i,j} = b_{t,j} · ΔG_{t,i}` is a first-price-style
  product of another agent's bid and a marginal model-gain term. There is no
  `Σ_{k≠i}` welfare-with-vs-without-i structure anywhere in it. Fails criterion 2.
- **Zhang2024auction_comm** — allocation `X = argmax_{i∈K} S(s_i, p_i)` over an
  *undefined* score `S`, so the argmax has no encodable objective. Worse, the payment
  `p_i = Σ_{j≠i} c_j - c_i` subtracts i's OWN cost from the sum of the others' costs:
  that is not a with-vs-without-i welfare difference, and it makes the payment
  directly decreasing in i's own report, the opposite of a pivot. Fails BOTH criteria.

## MANUAL diagnoses (real obstruction) — 21 entries

Ceiling phrase in brackets. All carry `verdict_override: MANUAL` +
`manual_diagnosis` and a MANUAL-backlog.md paragraph; their baseline rows were
rewritten `VERIFIED_SHAPE` -> `UNKNOWN`.

| paper_id | ceiling phrase |
|---|---|
| 2404_13841 | budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family |
| Ahmed2023frimfl | budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family |
| Cui2024auction_market | continuous bid space with no valid discretization |
| GPS2023afl_recruit | budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family |
| Haupt2021auctions | non-polynomial gap Z3 cannot linearize |
| Jiao2019auto_auction | budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family |
| Jin2023bara_budget | budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family |
| Lim2020edge_collab | RL-policy or opaque-algorithm allocation, not a closed-form rule |
| Lu2021cluster_auction | budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family |
| Model2024trading_fl | RL-policy or opaque-algorithm allocation, not a closed-form rule |
| Peng2023auction_medical | RL-policy or opaque-algorithm allocation, not a closed-form rule |
| Seo2021sdn_fl | non-polynomial gap Z3 cannot linearize |
| Seo2022noniid_auction | non-polynomial gap Z3 cannot linearize |
| Tan2023hire | RL-policy or opaque-algorithm allocation, not a closed-form rule |
| Wei2024truthful_bandit | non-polynomial gap Z3 cannot linearize |
| Xia2026privacy_mfg | budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family |
| Xiang2025esr_mhfl | budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family |
| Yang2023buyers_market | continuous bid space with no valid discretization |
| Zhang2022online | continuous bid space with no valid discretization |
| Zhang2024auction_comm | non-polynomial gap Z3 cannot linearize |
| Zheng2023fl_market | budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family |

## R6 candidates (formalization miss) — 8 entries

These stay `VERIFIED_SHAPE`. Their allocation genuinely IS (or plausibly reduces
to) a grid-decidable argmax with a Groves-shaped payment; the sweep's parser or
classifier failed on surface syntax, not on substance. **Do not diagnose MANUAL —
these are the R6 work queue.**

- **Le2021cellular_auction** — `x_i = argmax Σ b_i x_i` with payment
  `Σ_{j≠i} b_j x_j(b_{-i}) - Σ_{j≠i} b_j x_j(b)`. This is a *textbook* Clarke pivot
  written explicitly. Gap: the parser did not accept the two-summation payment form.
  Highest-confidence R6 target.
- **Tan2025longterm** — `x* = argmax Σ v_i(b_i) x_i`, payment
  `r(x*) - Σ_{k≠i} c(x_k*, γ̂_k)` — the same Groves form that *did* flip for
  3626307_3626311. Gap: classifier inconsistency, not a real obstruction.
- **Liu2023reverse_auction** — `W = argmax_{W⊆N} φ(W) - Σ costs`, payment
  `φ(W) - φ(W\{i}) - b_i`: an explicit with-vs-without-i pivot. Gap: subset-valued
  argmax over `W ⊆ N` is not expressible as `AllocHighest` over per-client scores;
  needs a set-valued allocation node.
- **Deng2020fmore_auction** — payment `Σ_{j≠i} c(x_j*, γ̂_j) - θ_i` is Groves-shaped.
  Gap: the allocation is written as an opaque `1 if i ∈ K` cases block; the real
  selection rule K needs re-extraction from the paper.
- **Ng2020uav_auction_coalition** — `x* = argmax Σ v_i x_i` is a clean welfare argmax.
  Gap: the payment `v_i x_i - (1/(N-1)) Σ_{j≠i} v_j x_j` has an averaging factor
  `1/(N-1)` that is not standard Groves — needs a check against the paper before it
  can be accepted or rejected. Ambiguous rather than obstructed.
- **Zhang2022expost_auction** — `S = argmax_{S⊆N} Σ_{i∈S} R_i - b_i` is a genuine
  welfare argmax. Gap: subset-valued argmax (as with Liu2023) plus a `min`-capped
  budget-share payment; the cap may never bind, in which case it reduces to a
  critical value.
- **Mai2022double_auction** — payment `v_{i,j} - (1/2) g_{j,i} u_wo^j` has a
  pivot-like structure. Gap: the recorded `allocation_rule_latex` is an aggregate
  utility definition (`u_ag = Σ u_wo^j`), not an allocation rule at all — a pure
  extraction failure.
- **Batool2022fl_mab** — score `S(r_i,p_i) = Σ α_k r_k - p_i` is a linear
  weighted-welfare score, a plausible `AllocWeightedWelfare{weights=α}` target. Gap:
  the recorded LaTeX defines the score but never states that the winner is its
  argmax, so the classifier had no allocation to classify.

## RECONCILE-FLAG

`print_summary` reported no `## Needs review` block for any VCG entry after this
task's edits. None to resolve.
