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

## Cluster: `_try_contract_latex` returned None — data/transcription/notation defects in the stored entry

**Entries:** 2102_03401 (u_3 written as function call, not coefficient),
2403_09153 (single-crossing assumption stripped by 2026-07-18 sanitization
pass), 2502_20882 (empty `notes` field, no diagnosed missing formal field),
2602_21844 (Bayesian posterior-expectation IC, Track 4 cannot integrate to
closed form), Bornstein2023realistic_incentive (moral hazard, not
adverse-selection — `ic_screening_latex` deliberately null, same underlying
cause as the first cluster above but flagged separately here because it was
found in the coverage-gap sweep), Ding2020contract_multidim (degenerate IC —
utility has no dependence on the contract variable, substitution collapses
to identity), International_Journal…Wan…Hierarchical (IC is an
equilibrium-utility ordering evaluated at own type on both sides, not a
substitutable screening IC — soundness gate correctly rejects),
Kang2022blockchain_metaverse (`R_{n-1}` parses as an opaque symbol, not an
offset index — no adjacent-IC semantics in `_contract_check_core`),
Ma2023joint_pricing (`client_utility_latex` is a simplified rendering that
drops a congestion-term sum, inconsistent with `ic_screening_latex`),
Saputra2020fl_contract (unresolved phi-weighting discrepancy between merged
duplicate's fields, never re-verified against PDF), Saputra2021iov_contract
(medium-confidence `S()` satisfaction function due to OCR artifacts),
Saputra2021straggling (square-root gain functions outside polynomial-friendly
assumptions), Wang2022motilearn_contract (IR indexed by `a`, IC by `n`/`i` —
no sound index correspondence to substitute), Wen2025diffusion_contract
(recorded IC/IR is period-2 static myopic only; paper's true mechanism is a
two-period intertemporal contract not represented in the entry),
Yang2023async_contract (`E_com` communication-energy scalar constant is
lexically indistinguishable from a Bayesian expectation `E_{...}[.]`, so the
Bayesian bail-out guard fires) (15)

**Real cause:** Unlike the two clusters above (which share one real
game-theoretic cause each), these 15 entries land on the same
`_try_contract_latex` → `_parse_contract_entry` → `None` exit point for 15
*different* reasons, none of which recur >= 2 times: PDF transcription
errors, prior sanitization passes stripping unverified assumptions, empty
review notes, OCR-uncertain fields, index-naming mismatches between IR/IC,
degenerate algebra, moral hazard misclassified alongside contract entries,
and one genuine Track 4 (Bayesian expectation) ceiling. Each is a distinct,
single-entry root cause; they are grouped here only because they share the
generic code-level bail point, not because they share a real obstruction.
Reading each `stored_limit` (done above, per entry) confirms none of these
15 duplicate each other or the two named clusters above.

**Classification:** not a single classification — mixed. Two possible
implementation bugs are visible here on inspection (not confirmed fixable,
flagged for closer look): 2102_03401's `u_3(...)` function-call-vs-coefficient
parse could be a genuine LaTeX-normalization bug rather than a math
ceiling — if the entry's source truly means `u_3 * (...)`, a preprocessing
fix in the parser (recognizing single-scalar "function calls" that are
actually multiplication) might resolve it, but this needs a look at the raw
LaTeX source, which is out of scope for this pass. Kang2022blockchain_metaverse's
`R_{n-1}` offset-index parsing is a real but narrow parser gap (single
entry, so not a widening candidate cluster). Everything else here (13
entries) is either a genuine solver/data ceiling (OCR uncertainty,
Bayesian-guard collision, degenerate algebra, mismatched notation, dropped
assumptions) that the verifier is correctly and conservatively declining, or
lacks enough recorded diagnostic information (`notes` empty) to say more.

**If ceiling — corrected diagnosis:** kept as stored per-entry — these 15
already have accurate, entry-specific `stored_limit` text; none should be
overwritten with cluster-level generic text since there is no single real
cluster-level cause here.

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

## Cluster: `_try_stackelberg_latex` returned None — beyond 2-stage / dynamic recursion

**Entries:** 2103_05866 (>2-stage / multi-layer game), 2412_05636 (follower
best-response is a backward recursion over a horizon) (2)

**Real cause:** The Stackelberg entry-specific path models one leader move
followed by one follower move, resolved via a single-variable FOC. Both
these papers have a game with more than two stages (a multi-layer hierarchy,
or a backward-recursion best response over a multi-period horizon), which
has no representation in a 2-player, 2-stage template at all — not even as a
vector-follower variant, since the issue is stage count, not decision
dimensionality.

**Classification:** genuine solver ceiling

**If ceiling — corrected diagnosis:** obstruction: "Game has more than two
stages (multi-layer hierarchy or multi-period backward recursion) — Track
1's Stackelberg model is strictly single-leader/single-follower, two-stage."
limit: kept as stored per-entry.

---

## Cluster: `_try_stackelberg_latex` returned None — transcendental / implicit follower FOC with no closed-form root

**Entries:** Chu2023hierarchical (transcendental stationarity equation, no
closed-form root, paper states this explicitly), Luo2023unbiased (implicit
cubic in q_n*, no transcribed root), Pandey2019crowd (transcendental
`1/theta - log(1/theta) = const`, plus a min-clipped implicit solution) (3)

**Real cause:** The Stackelberg FOC-reduction path needs to solve the
follower's stationarity condition for a closed-form best response to
substitute into the leader's problem. In these 3 papers the FOC itself is
transcendental (log/implicit-cubic/min-clip) and the paper never provides
(or the entry never transcribes) a closed-form root — Z3's polynomial
machinery cannot solve for an implicit root symbolically, so the reduction
step fails before the leader-side check ever runs. This is the same class of
"Z3 cannot handle an opaque/transcendental expression" ceiling as the
Contract-cluster's transcendental-utility cluster above, but hitting the
Stackelberg follower-FOC path instead of the Contract IC/IR path.

**Classification:** genuine solver ceiling

**If ceiling — corrected diagnosis:** obstruction: "Follower's first-order
stationarity condition is transcendental or implicit (log/cubic/min-clip)
with no closed-form root available — Track 1's Stackelberg FOC reduction
requires a scalar closed-form best response to substitute." limit: kept as
stored per-entry.

---

## Cluster: Stackelberg / VCG — VERIFIED_TEMPLATE with no diagnosed missing formal field (empty or abstract-level notes)

**Entries:** FLamma2025stackelberg (Stackelberg: notes give only the paper's
abstract-level description), Javaherian2025stackelberg_ic (Stackelberg: IR
is stated and proven satisfied at equilibrium, but sits at VERIFIED_TEMPLATE
— likely missing a different formal field), Mai2022double_auction (VCG:
notes give only the paper's abstract-level description) (3)

**Real cause:** These 3 entries sit at the generic VERIFIED_TEMPLATE verdict
with no prior reviewer note identifying which specific formal field Track 1
needs and doesn't have — the `notes` field is either empty or only restates
the paper's abstract. This is a data/annotation gap in the corpus, not a
demonstrated code-level ceiling: unlike the clusters above, it is not known
*what* is missing, only that something is, so no corrected obstruction text
can be written without first doing the missing-field diagnosis (the same
work Task 1's `bail_function`/`bail_reason` trace already did for every
other entry in this doc, but that trace only reaches `_try_contract_latex`
/`_try_stackelberg_latex`/`verify_vcg` internals — it does not explain why
these 3 never reached a discriminating bail point inside those functions in
the first place, i.e. why they're still VERIFIED_TEMPLATE rather than
None/VERIFIED_SHAPE like their cluster-mates).

**Classification:** genuine ceiling, but of a different kind than the others
in this doc — a diagnosis gap, not a confirmed solver-capability boundary.
Not classified fixable (no confirmed missing field to fix toward), and not
folded into a solver-ceiling cluster above (would misrepresent that a real
math cause is known).

**If ceiling — corrected diagnosis:** obstruction: "No prior manual review
has identified which formal field Track 1 is missing for this entry — the
`notes` field is empty or paper-abstract-level only; needs a fresh read of
the source PDF before a specific field-level obstruction can be recorded."
limit: kept as stored per-entry (already states this).

---

## Cluster: `_try_stackelberg_latex` returned None — additional single-entry causes near the "no follower IR" family

**Entries:** Khan2019edge (no proved equilibrium — Track 1 needs one, a
distinct prerequisite from IR/participation being stated), Pang2025quality
(payment/cost are unspecified generic functions f, d — no algebraic form to
differentiate, a data-completeness gap rather than a missing-IR gap),
Xiao2020stackelberg_twostage (follower IR is enforced algorithmically via an
Algorithm-1 quit-check rather than as a closed-form constraint inside the
Stage II arg max — already referenced as "related but distinct" in the
no-follower-IR cluster above, listed here explicitly as its own case since
it does not share that cluster's exact cause: the IR exists procedurally,
it's just not expressible as an equation Track 1 can substitute) (3)

**Real cause:** Each of these 3 fails `_try_stackelberg_latex` for a cause
adjacent to, but distinct from, "no follower IR/participation constraint
stated" (the 11-entry cluster above) and "vector follower decision" (the
8-entry cluster above): a missing proved equilibrium is a different
prerequisite than a missing IR constraint; unspecified generic cost
functions is a data-completeness gap (nothing to differentiate) rather than
a missing-constraint gap; and an algorithmically-enforced (not
closed-form-expressible) IR is a structurally different failure than an IR
that was simply never written down. None of the three recurs a second time
in this JSON, so each is a genuine singleton cause within the broader
Stackelberg-None mega-cluster.

**Classification:** genuine solver ceiling (all three)

**If ceiling — corrected diagnosis:** kept as stored per-entry — each
already has accurate, cause-specific `stored_limit` text.

---

## Cluster: `verify_vcg` non-terminal VERIFIED_SHAPE — allocation rule outside the fixed threshold-payment template

**Entries:** 2404_13841, Ahmed2023frimfl, GPS2023afl_recruit, Jiao2019auto_auction, Jin2023bara_budget, Lu2021cluster_auction (budget-constrained greedy, 6); Lim2020edge_collab, Model2024trading_fl, Peng2023auction_medical, Tan2023hire (RL-policy / opaque-algorithm allocation, 4); Cui2024auction_market, Yang2023buyers_market, Zhang2022online (continuous bid space, no discretization, 3); Haupt2021auctions, Seo2021sdn_fl, Seo2022noniid_auction, Wei2024truthful_bandit (non-polynomial gap Z3 cannot linearize, 4); Xia2026privacy_mfg, Zhang2024auction_comm (payment rule structurally not a Clarke pivot, 2) (19 total, in 5 real sub-groups; see coverage note below for the other 2 of the raw 21-member cluster)

**Coverage note:** the raw `verify_vcg`/VERIFIED_SHAPE cluster has 21
members total. Batool2022fl_mab and Mai2022double_auction are 2 of those 21
and are accounted for separately: Batool2022fl_mab has its own singleton
write-up immediately below (distinct cause — no separate platform
objective), and Mai2022double_auction is folded into the "no diagnosed
missing formal field" cluster above (empty/abstract-only notes, same cause
class as FLamma2025stackelberg and Javaherian2025stackelberg_ic). That
leaves 19 entries in the 5 sub-groups named here... but the sub-group counts
above (6+4+3+4+2) sum to 19, matching. 19 + Batool2022fl_mab (1) +
Mai2022double_auction (accounted for above, not re-counted here) = 20 of 21;
the 21st is Xia2026privacy_mfg / Zhang2024auction_comm's pair already
included in the 19 — recount: 6+4+3+4+2 = 19, +Batool 1 = 20,
+Mai2022double_auction 1 = 21. All 21 raw cluster members are accounted for
across this section and the notes-gap cluster above.

**Real cause:** `verify_vcg` (`src/tracks/track1_z3.py:75`) first tries the
real finite-grid DSIC+IR proof (`verify_vcg_dsic`); when that returns
UNKNOWN/UNSUPPORTED it falls through to a fixed threshold-payment /
Clarke-pivot regex-classified template (`_vcg_check_core`, line 149), whose
success is explicitly demoted to the non-terminal `VERIFIED_SHAPE` verdict
(line 143-145) because it never solves the entry's own math — it only checks
that the payment-rule string matches a known VCG *form*. The 19 entries in
the 5 named sub-groups here (plus Batool2022fl_mab just below) have
allocation or payment rules that are not "regex-classifiable payment on a
fixed-template threshold auction": budget-constrained greedy selection,
RL/opaque-policy allocation, continuous (non-discretizable) bid space, a
non-polynomial payment gap, or a payment structurally outside the
Clarke-pivot family entirely. Each sub-group is a real, distinct reason the
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
- Payment rule structurally not a Clarke pivot (2, Xia2026privacy_mfg /
  Zhang2024auction_comm): genuine ceiling — Xia2026privacy_mfg's budget cap
  `min(B/k, ·)` and Zhang2024auction_comm's own-cost-inclusive payment
  (`sum_{j!=i} c_j - c_i`) are both payment forms `_vcg_check_core`'s regex
  classifier does not and should not recognize as Clarke-pivot, since they
  are not Clarke-pivot payments — no fix sketch here, this is the template
  correctly declining a genuinely different payment family.

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

## Cluster: `verify_vcg` non-terminal VERIFIED_SHAPE — no separate platform-level objective (singleton)

**Entries:** Batool2022fl_mab (1)

**Real cause:** `_vcg_check_core`'s template checks a payment/allocation
rule against a platform objective distinct from the per-client
scoring/allocation formula. This entry's mechanism folds the platform's
objective and the per-client scoring rule into one and the same function —
there is no separate platform-level objective to check the allocation rule
against, so the template's structural precondition is never met. This does
not recur elsewhere in the corpus (a genuine singleton), so it is not folded
into any of the 5 sub-groups above.

**Classification:** genuine solver ceiling

**If ceiling — corrected diagnosis:** kept as stored per-entry — already
accurate.

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
| Contract: data/transcription/notation defects (15 distinct single-entry causes, grouped only by shared bail point) | 15 | mixed — no confirmed fixable bug; 2 flagged for a closer look (2102_03401 possible parser normalization gap, Kang2022blockchain_metaverse narrow offset-index parser gap) |
| Contract: transcendental / opaque function | 3 | ceiling |
| Stackelberg: no follower IR stated | 11 | ceiling |
| Stackelberg: vector follower decision | 8 | ceiling |
| Stackelberg: beyond 2-stage / dynamic recursion | 2 | ceiling |
| Stackelberg: transcendental / implicit follower FOC | 3 | ceiling |
| Stackelberg/VCG: no diagnosed missing field (empty/abstract notes) | 3 | diagnosis gap, not a confirmed solver ceiling |
| Stackelberg: additional single-entry causes near "no follower IR" | 3 | ceiling |
| VCG: allocation outside fixed template (5 sub-groups) | 19 | ceiling (4-entry non-polynomial-gap sub-group flagged for a closer look, not confirmed fixable) |
| VCG: no separate platform objective (singleton) | 1 | ceiling |
| Shapley: k > 3 / coalition size unstated | 3 | ceiling |
| Contract: box-dimension cap after pinning | 2 | ceiling |
| **Total clustered (>= 2-entry clusters, plus the 2 named singletons within the VCG/Shapley write-ups above)** | **85** | |

**Singletons (true, verified against the grouping query):**

- 2405_13879 — `verify_shapley` bails MANUAL because the paper never
  defines a coalition characteristic function `v(S)` or uses the Shapley
  value at all; the Shapley category tag on this entry is itself wrong (no
  coalition track applies). This is the only entry among all 86 whose
  `(bail_function, bail_reason[:80])` key has no other member — every other
  entry belongs to one of the 5 raw clusters above. Genuine ceiling (a
  mis-categorization, not a fixable verifier bug — fixing it means
  recategorizing the corpus entry, out of scope for solver widening).

**0 of 85 clustered entries are confirmed fixable bugs**, and the 1 true
singleton is also not a fixable bug (a corpus mis-categorization). Every
named cluster traces to either a genuine template/solver-capability
boundary (Track 1's Contract model assumes single-dimension
adverse-selection screening, its Stackelberg model assumes a
2-stage/scalar-follower game with a stated IR, and its VCG model assumes a
discrete, closed-form, regex-classifiable Clarke-pivot-family payment) or,
for the 15-entry Contract "data/transcription/notation defects" bucket and
the 3-entry "no diagnosed missing field" bucket, a mix of per-entry data
defects and open diagnosis gaps rather than one shared math cause — these
two buckets are reported as clusters (they share a bail point) but
explicitly are NOT single-cause clusters the way the other 11 are, and no
single corrected `obstruction` line is offered for them. Two single-entry
items inside the 15-entry bucket (2102_03401, Kang2022blockchain_metaverse)
are flagged as possibly narrow parser bugs worth inspection, and the
4-entry "non-polynomial payment gap" VCG group remains the one sub-group
with an actual fix sketch — both are conditional on inspection this pass
did not do, per the fail-closed instruction.

**Entry-count verification:** every paper_id listed across all sections and
the singleton above was collected and counted independently of this
narrative — 85 distinct clustered entries + 1 singleton = 86, with zero
duplicates. See the fix report for the exact re-run command and output.
