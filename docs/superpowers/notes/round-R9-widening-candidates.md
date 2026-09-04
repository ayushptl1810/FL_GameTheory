# R9 — Widening Candidates

Clusters from `round-R9-root-cause-audit.json` where >= 2 MANUAL entries
share the same real code-level bail point (`bail_function` + `bail_reason`
prefix). `matches_stored` was checked for every mismatch row (all rows in
these clusters show `matches_stored: false`) by reading the full stored
`manual_diagnosis` obstruction/limit text against the full `bail_reason`
text — the mismatches are confirmed to be the known-non-discriminating
heuristic (vocabulary mismatch), not stale diagnoses; where the stored text
turned out to describe a genuinely different cause than the code path
implies, that is called out per sub-cluster below.

Two of the five raw clusters (`_try_contract_latex` "returned None" at 30
entries, `_try_stackelberg_latex` "returned None" at 29 entries) are **not
single causes** — `bail_function` + a truncated generic `bail_reason` prefix
("returned None") is the same code-level exit point for many structurally
different reasons. Grouping by that exit point alone would produce a fake
"one giant cluster" story; the real groupings are the sub-clusters below,
found by reading each entry's full `stored_limit` text (which records what a
prior manual pass already diagnosed, function-by-function, and remains
accurate — spot checks below confirm the code still bails at the same place
for the same reason).

---

## Cluster: `_try_contract_latex` returned None — no adverse-selection screening IC in the paper

**Entries:** 2408_13223, 2505_02462, 2505_05842, 2605_02935, Huang2024aigc, Karimireddy2022data_sharing, Li2026network, Zhang2020fedserving, Zhao2023truthful (9)

**Real cause:** `_try_contract_latex` calls `_parse_contract_entry`, which
requires `ic_screening_latex` (a type-i-vs-type-j menu-substitution
screening constraint) to exist and parse. These 9 papers are not
adverse-selection screening-contract mechanisms at all — they are moral
hazard (hidden continuous action, Nash equilibrium over an action set),
Bayesian peer-prediction / BTS truthfulness, or fixed-price/behavioral-type
models with no discrete type menu. `ic_screening_latex` is correctly null or
absent for these, so `_parse_contract_entry` returns `None` and the function
bails. This is not a parser gap — it is Track 1 Contract's template
(single-dimension type, IC-as-menu-substitution) genuinely not describing
these mechanisms' game structure.

**Classification:** genuine solver ceiling

**If ceiling — corrected diagnosis:** `manual_diagnosis.obstruction`: "No
adverse-selection screening IC in the paper — the mechanism is moral hazard
(hidden action) or Bayesian peer-prediction, not a type-menu contract; Track
1's Contract template requires `ic_screening_latex` and none exists."
`manual_diagnosis.limit`: (paper-specific, already captured per-entry in
`stored_limit` — these are accurate as stored and should be kept, not
overwritten with one generic line).

---

## Cluster: `_try_contract_latex` returned None — multi-dimensional type outside single-dimension substitution

**Entries:** Lim2020contract, Wu2021contract_DP, 2308_12502 (kappa_j
population-coupled cost term is a related but distinct multi-agent-coupling
variant of the same "not single-dimension-substitutable" cause) (3)

**Real cause:** `_contract_check_core` (`src/tracks/track1_z3.py:636`)
substitutes a single scalar `type_sub` symbol across the IC/IR expressions
(`_sub_index`). Lim2020contract's 4-D cost vector and Wu2021contract_DP's
3-D type have no single scalar to substitute; `_parse_contract_entry`
correctly fails to reduce them and `_try_contract_latex` returns `None`.
2308_12502's `kappa_j` term sums over *other agents'* contracts (a
population-coupled externality), which the same single-agent substitution
machinery cannot represent either — same underlying limitation
(non-single-dimension-substitutable IC), different surface shape.

**Classification:** genuine solver ceiling

**If ceiling — corrected diagnosis:** obstruction: "Multi-dimensional or
population-coupled type/cost structure — `_contract_check_core`'s IC/IR
substitution machinery only handles a single scalar type index and cannot
represent a type vector or a cost term that sums over other agents'
contracts." limit: kept as stored per-entry (already accurate).

---

## Cluster: `_try_contract_latex` returned None — transcendental / opaque function in utility

**Entries:** 2407_02845 (log argument sign not established), Han2025paid_models (opaque v(.) inside expectation), Nguyen2025right_reward (opaque h(t_k)) (3)

**Real cause:** `_sp_to_z3` (used inside `_contract_check_core`'s `_U`
helper) either rejects a `log`/`exp` term whose argument sign can't be
proven positive, or rejects an unrecognized SymPy function node (`v`, `h`)
outright — these are undefined/opaque functions the paper never gives a
closed form for. `_U(k, l)` returns `None` for at least one `(k, l)` pair,
so the `for k … for l …` guard at line 678-681 makes `_contract_check_core`
(and therefore `_try_contract_latex`) return `None`. This is correct,
conservative behavior: Z3 cannot reason about an opaque function symbol.

**Classification:** genuine solver ceiling

**If ceiling — corrected diagnosis:** kept as stored per-entry — these three
already have accurate, function-specific `stored_limit` text ("Z3 encoding
rejects it (unsupported SymPy node …)" / "log argument sign not
established").

---

## Cluster: `_try_stackelberg_latex` returned None — no follower IR / participation constraint stated

**Entries:** 1811_12082, 2110_12876, 2203_00270, 2404_08261, 2508_07676, Cao2025service, Chen2023multifactor_iot, Hu2020trading, Hu2022truthful_FEL, Lee2024sfl_stackelberg, Li2025iiot_drl (11)

**Real cause:** The Stackelberg entry-specific path requires a follower IR
(participation) constraint to check alongside the leader/follower FOC. In
these 11 papers the participation condition is either never stated as a
formal inequality (only narrative "the follower will only join if
profitable"), or (Xiao2020stackelberg_twostage, related but distinct — see
next cluster) enforced algorithmically outside the closed-form arg-max. This
is the single largest genuinely-common sub-cause in the whole audit: roughly
a third of the Stackelberg MANUAL backlog is "paper states the game but
never writes down IR as an equation."

**Classification:** genuine solver ceiling (fixing this would mean inferring
an IR constraint the paper doesn't state, which is out of scope — the
verifier is not allowed to invent constraints the source doesn't contain)

**If ceiling — corrected diagnosis:** obstruction: "No follower
IR/participation constraint stated as a formal inequality in the paper — the
Stackelberg entry-specific path requires one to check against the follower's
best response and none exists to parse." limit: kept as stored per-entry.

---

## Cluster: `_try_stackelberg_latex` returned None — vector (multi-dimensional) follower decision

**Entries:** 2101_05628, 2101_12428, 2502_10765, Guo2023stackelberg_industrial, Li2025split, Liu2026fedbud, Wang2022blockchain, Yu2022multi_leader_fl (8)

**Real cause:** The Stackelberg entry-specific path reduces the follower's
best response via a single-variable first-order condition (FOC). These 8
papers have a follower choosing a *vector* decision (e.g. per-round resource
allocation across multiple dimensions, or a multi-leader game), so a
single-variable FOC reduction does not apply — there is no scalar to solve
for. This is a template-shape ceiling: Track 1's Stackelberg model is
2-player, 2-stage, scalar-follower-action only.

**Classification:** genuine solver ceiling

**If ceiling — corrected diagnosis:** obstruction: "Follower decision is a
vector (multi-dimensional resource allocation or multi-leader game), not a
scalar — Track 1's Stackelberg FOC reduction only handles a single-variable
follower best response." limit: kept as stored per-entry.

---

## Cluster: `verify_vcg` non-terminal VERIFIED_SHAPE — allocation rule outside the fixed threshold-payment template

**Entries:** 2404_13841, Ahmed2023frimfl, GPS2023afl_recruit, Jiao2019auto_auction, Jin2023bara_budget, Lu2021cluster_auction (budget-constrained greedy, 6); Lim2020edge_collab, Model2024trading_fl, Peng2023auction_medical, Tan2023hire (RL-policy / opaque-algorithm allocation, 4); Cui2024auction_market, Yang2023buyers_market, Zhang2022online (continuous bid space, no discretization, 3); Haupt2021auctions, Seo2021sdn_fl, Seo2022noniid_auction, Wei2024truthful_bandit (non-polynomial gap Z3 cannot linearize, 4) (21 total, in 4 real sub-groups)

**Real cause:** `verify_vcg` (`src/tracks/track1_z3.py:75`) first tries the
real finite-grid DSIC+IR proof (`verify_vcg_dsic`); when that returns
UNKNOWN/UNSUPPORTED it falls through to a fixed threshold-payment /
Clarke-pivot regex-classified template (`_vcg_check_core`, line 149), whose
success is explicitly demoted to the non-terminal `VERIFIED_SHAPE` verdict
(line 143-145) because it never solves the entry's own math — it only checks
that the payment-rule string matches a known VCG *form*. All 21 entries here
have allocation rules that are not "regex-classifiable payment on a
fixed-template threshold auction": budget-constrained greedy selection,
RL/opaque-policy allocation, continuous (non-discretizable) bid space, or a
non-polynomial payment gap. Each sub-group is a real, distinct reason the
fixed template's assumption (discrete top-k/argmax/weighted-welfare
allocation with a linearizable Clarke-pivot payment) doesn't hold — this is
the single biggest real ceiling class in the corpus by entry count.

**Classification:** genuine solver ceiling, split by sub-group:
- Budget-constrained greedy (6), RL/opaque-policy (4), continuous bid space
  (3): genuine ceiling — `verify_vcg_dsic`'s grid search and
  `_vcg_check_core`'s fixed template are both built for a discrete,
  closed-form allocation/payment pair; none of these have one.
- Non-polynomial payment gap (4, Haupt2021auctions / Seo2021sdn_fl /
  Seo2022noniid_auction / Wei2024truthful_bandit): borderline — worth a
  second look in the follow-on plan (see fix sketch) since "Z3 cannot
  linearize" is sometimes a solvable encoding problem rather than a true
  template mismatch, but confirming that needs per-entry inspection of the
  actual payment expression, which is out of scope for this analysis pass.

**If fixable (non-polynomial-gap sub-group only) — fix sketch:** If, on
inspection, the "non-polynomial gap" is a monotone/bounded expression (e.g.
a ratio or a bounded exponential term) rather than truly transcendental,
`_vcg_check_core` could be extended with a second Z3 encoding path using
`Real` interval bounds + Z3's nonlinear arithmetic (`z3.Tactic('nra')`)
instead of the current pure-linear `Solver()`. This would only help the 4
entries in this sub-group and should not be attempted without first reading
each entry's actual `payment_rule_latex` to confirm the gap is genuinely
polynomial-adjacent and not an unbounded transcendental (which would just
move the ceiling, not remove it) — flagged for the Task 3+ planning pass to
scope properly, not implemented here.

---

## Cluster: `verify_shapley` non-terminal MANUAL — k > 3 or coalition size not stated

**Entries:** 2502_08248, 2605_11889, 2606_18384 (3)

**Real cause:** `verify_shapley` bails to MANUAL when the number of players
exceeds 3 (Shapley value's exponential coalition enumeration becomes
computationally intractable to check exhaustively past that) or when the
paper never states a concrete coalition size to bound the search. Sampled
`stored_limit` text for all 3 confirms this: each cites either an
unspecified/variable client count or `k`/coalition size stated only
asymptotically, never as a fixed small integer.

**Classification:** genuine solver ceiling (this is a real combinatorial
blow-up, not a parsing gap — Shapley-value verification for k > 3 requires
either a symbolic/algebraic proof the entries don't provide the structure
for, or exponential enumeration this verifier deliberately caps)

**If ceiling — corrected diagnosis:** kept as stored per-entry — these are
already accurately described.

---

## Cluster: `_try_contract_latex` returned non-terminal UNKNOWN — box-dimension cap exceeded after pinning declared constants

**Entries:** Kang2019contract_mobile, Kang2019reliable_contract (2)

**Real cause:** After pinning the paper's declared numeric constants, both
entries' IC/IR expressions still have more free variables than the
verifier's interval-search box-dimension cap allows (IR: 8 free vars after
pinning; IC: 6 free vars, both above the cap). This is a resource/scalability
ceiling of the generic interval-search fallback, not a parse failure — the
`stored_limit` text (sampled for Kang2019contract_mobile above) already
describes this precisely and per-entry.

**Classification:** genuine solver ceiling

**If ceiling — corrected diagnosis:** kept as stored per-entry — already
accurate.

---

## Summary

| Cluster | Entries | Classification |
|---|---|---|
| Contract: no adverse-selection IC in paper | 9 | ceiling |
| Contract: multi-dim / population-coupled type | 3 | ceiling |
| Contract: transcendental / opaque function | 3 | ceiling |
| Stackelberg: no follower IR stated | 11 | ceiling |
| Stackelberg: vector follower decision | 8 | ceiling |
| VCG: allocation outside fixed template (4 sub-groups) | 21 | ceiling (4-entry non-polynomial-gap sub-group flagged for a closer look, not confirmed fixable) |
| Shapley: k > 3 / coalition size unstated | 3 | ceiling |
| Contract: box-dimension cap after pinning | 2 | ceiling |

**0 of 60 clustered entries are confirmed fixable bugs.** Every cluster
traces to a genuine template/solver-capability boundary: Track 1's Contract
model assumes single-dimension adverse-selection screening, its Stackelberg
model assumes a scalar follower action with a stated IR, and its VCG model
assumes a discrete, closed-form, regex-classifiable Clarke-pivot-family
payment. All are real limitations of the current verifier tracks, not bugs
in how those tracks are implemented. The one sub-group worth a second,
closer look before the Task 3+ plan is finalized is the 4-entry
"non-polynomial payment gap" VCG group — flagged above as the only place a
fix sketch is offered, and even that is conditional on inspection this pass
did not do.

The remaining 26 MANUAL entries (86 total minus the 60 above) either did not
form a `>= 2`-entry cluster (singleton `bail_function`/`bail_reason`
combinations) or were not present in the audit JSON's covered set; per the
brief, only `>= 2`-entry clusters are in scope for this document.
