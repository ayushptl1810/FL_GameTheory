# MANUAL Backlog

One paragraph per corpus entry that no automated track can decide. Appended to from R2 onward; the R7 honesty pass closes it out.

## 2404_13841 (VCG) — R2

**Mechanism:** Budget-split proportional payment B/(S(k-1)) to a threshold-index winning set; allocation LaTeX is an alpha-fairness share, not a selection rule.
**Obstruction:** Winner set is a budget-threshold cutoff k=min{k: b_k > B/(Sk)}; not argmax/top-k with fixed k, and the recorded allocation LaTeX is a share formula, so no grid-decidable allocation node exists. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** Extract the true winner-selection rule from the paper and decide whether the budget-threshold cutoff admits a finite-grid encoding.
**Diagnosed:** 2026-09-03

## Ahmed2023frimfl (VCG) — R2

**Mechanism:** Per-client indicator x_i=1 iff posted price p_i=B/r_i is under budget B; payment is a fixed posted price.
**Obstruction:** Allocation is a per-client budget-feasibility cases-threshold, not a welfare argmax, and the payment B/r_i is a posted price independent of others' reports, so no Groves pivot exists to prove. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** Decide whether the budget-feasibility threshold is monotone in the report and, if so, re-encode as a threshold mechanism outside the VCG family.
**Diagnosed:** 2026-09-03

## Haupt2021auctions (VCG) — R2

**Mechanism:** Score-comparison allocation w_i chosen by pairwise comparison b_i(s-hat - s_i) against a permuted rival, with a Punish() term in the payment.
**Obstruction:** The payment contains an opaque Punish(s_j - s_i) aggregate and the allocation is a pairwise-comparison cases rule over a permutation pi(i), which is neither argmax nor top-k and not linearizable on a finite grid. (Track 1: non-polynomial gap Z3 cannot linearize)
**Human task:** Define Punish() concretely and determine whether the pairwise-comparison allocation reduces to an argmax over a scoring function.
**Diagnosed:** 2026-09-03

## Jiao2019auto_auction (VCG) — R2

**Mechanism:** Budget-constrained greedy: n_t = argmax n s.t. cumulative proportional cost sum_{i<=n} (b_{n+1}/q_{n+1}) q_i <= B_t, with proportional-share payment r_{t,i}.
**Obstruction:** The allocation maximizes a COUNT subject to a budget constraint (a knapsack-style greedy), not a welfare argmax, and the payment is a proportional share of the critical unit price rather than a Clarke pivot. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** Encode the budget-greedy cutoff as a monotone-threshold mechanism and prove critical-payment truthfulness outside the VCG grid path.
**Diagnosed:** 2026-09-03

## Jin2023bara_budget (VCG) — R2

**Mechanism:** Identical budget-constrained greedy to Jiao2019: n_t = argmax n s.t. sum (b_{n+1}/q_{n+1}) q_i <= B_t with proportional critical-price payment; client_utility_latex is null.
**Obstruction:** Budget-knapsack allocation is out of the {argmax, top-k, weighted-welfare} family and the proportional-share payment is not a Clarke pivot; with no utility LaTeX the grid proof has no objective to check. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** Supply the client utility and re-encode as a monotone threshold mechanism; prove truthfulness via critical-value payment, not Groves.
**Diagnosed:** 2026-09-03

## Lim2020edge_collab (VCG) — R2

**Mechanism:** No allocation or payment rule recorded in the corpus entry; the paper's edge-collaboration mechanism is described only in prose.
**Obstruction:** Both allocation_rule_latex and payment_rule_latex are null, so there is no closed-form rule to classify or discharge on a grid. (Track 1: RL-policy or opaque-algorithm allocation, not a closed-form rule)
**Human task:** Re-extract the allocation and payment rules from the paper PDF before any solver attempt.
**Diagnosed:** 2026-09-03

## Lu2021cluster_auction (VCG) — R2

**Mechanism:** Select the K_j lowest bidders among clients passing a data-size filter s_min; payment is an affine 1/(N-K+1) + ((N-K)/(N-K+1)) c_i formula.
**Obstruction:** The eligible set JL is itself defined by a min over a previously-selected set (a fixed-point/filter dependency), so the allocation is not a plain top-k over reports, and the affine payment is not a Clarke pivot. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** Resolve the s_min fixed point and determine whether the filtered top-K selection is monotone in each client's bid.
**Diagnosed:** 2026-09-03

## Model2024trading_fl (VCG) — R2

**Mechanism:** Allocation a_t = b_t * pi(s_t; theta) is the output of a learned RL policy pi; payment p_t = Delta G_t * b_t / k_{i+1}.
**Obstruction:** The allocation is a neural RL policy with no closed form, so it cannot be classified as argmax/top-k/weighted-welfare and admits no finite-grid encoding. (Track 1: RL-policy or opaque-algorithm allocation, not a closed-form rule)
**Human task:** Determine whether the trained policy's induced allocation is provably monotone, or bound truthfulness empirically; formal Track-1 proof is out of reach.
**Diagnosed:** 2026-09-03

## Peng2023auction_medical (VCG) — R2

**Mechanism:** No allocation or payment rule recorded in the corpus entry.
**Obstruction:** Both allocation_rule_latex and payment_rule_latex are null, so there is no rule to classify. (Track 1: RL-policy or opaque-algorithm allocation, not a closed-form rule)
**Human task:** Re-extract the allocation and payment rules from the paper PDF before any solver attempt.
**Diagnosed:** 2026-09-03

## Seo2021sdn_fl (VCG) — R2

**Mechanism:** Winner score R_win = sum alpha_i e_ni - p_n with an exponential payment zeta * e^{-(1-Q_m(m))} for winners.
**Obstruction:** The payment is an exponential of the quality score; Z3 cannot linearize e^{-(1-Q)} over a real grid, and the exponential payment is not a Clarke pivot in any case. (Track 1: non-polynomial gap Z3 cannot linearize)
**Human task:** Discretize Q_m to a fixed lookup table of rational payment values, or prove truthfulness analytically via monotonicity of the score.
**Diagnosed:** 2026-09-03

## Seo2022noniid_auction (VCG) — R2

**Mechanism:** Winner score beta_1 U_D(e_n) - p_n with exponential winner payment zeta * e^{-(1-U_{D_k})}.
**Obstruction:** Same exponential-payment obstruction as Seo2021: the payment is a transcendental function of the data-utility score, which Z3 cannot linearize, and it is not a Groves pivot. (Track 1: non-polynomial gap Z3 cannot linearize)
**Human task:** Tabulate the exponential payment over a finite quality grid, or prove monotonicity analytically.
**Diagnosed:** 2026-09-03

## Tan2023hire (VCG) — R2

**Mechanism:** Mode-switching selection: lowest-bid participants when a queue Q_f(t) <= 0, highest-reputation participants when Q_f(t) > 0; payment is first-price sum b_n P(n,t).
**Obstruction:** The allocation switches objective based on a time-varying queue state external to the report profile, so it is not a fixed argmax; and the payment is first-price (pays the bid), which is not a Clarke pivot. (Track 1: RL-policy or opaque-algorithm allocation, not a closed-form rule)
**Human task:** Fix the queue state and check whether each branch is separately monotone; a first-price payment cannot be DSIC, so a counterexample search may be the right target.
**Diagnosed:** 2026-09-03

## Wei2024truthful_bandit (VCG) — R2

**Mechanism:** Combinatorial subset selection S_t = argmax over 2^S of g_t(S) = log det(V_g,t(S)); payment is the critical cost c_{i,t}(M, D_{-i,t}).
**Obstruction:** The objective is a log-determinant over subsets: both the exponential subset space and the non-polynomial log-det make it impossible to encode as a grid-decidable argmax over per-client scores. (Track 1: non-polynomial gap Z3 cannot linearize)
**Human task:** Prove submodularity of log-det and use the greedy-approximation truthfulness argument analytically; the exact combinatorial argmax is out of solver reach.
**Diagnosed:** 2026-09-03

## Xia2026privacy_mfg (VCG) — R2

**Mechanism:** Top-k indicator q_i=1 iff i<=k, with payment min(B/k, c(v_{k+1}, 1/(n-k))) capped by a per-winner budget share.
**Obstruction:** The payment is a min of a budget-share cap and a critical value; the budget cap makes it neither a Clarke pivot nor a pure critical-value payment, so the top-k allocation alone is not enough for a grid DSIC proof. (Track 1: payment budget cap min(B/k, ·) breaks the Clarke-pivot form; top-k allocation is fine but the payment is not Groves)
**Human task:** Determine whether the budget cap ever binds under the paper's assumptions; if it does not, the mechanism reduces to a critical-value top-k.
**Diagnosed:** 2026-09-03

## Yang2023buyers_market (VCG) — R2

**Mechanism:** Continuous quantity contract q_i* = lambda/(2(1+delta theta_i)) with reward R_i* = lambda^2/(2(1+delta theta_i)^2) as a function of reported efficiency theta_i.
**Obstruction:** This is a continuous screening/contract menu over theta_i in [0,1], not an auction allocation; the reward is a nonlinear rational function of the report with no finite grid that preserves the incentive constraints. (Track 1: continuous bid space with no valid discretization)
**Human task:** Verify the contract's incentive compatibility by the first-order/envelope condition analytically rather than on a grid.
**Diagnosed:** 2026-09-03

## Zhang2022online (VCG) — R2

**Mechanism:** Threshold acceptance x_i = 1 iff b_i <= rho*, payment min(rho*, b_i); utility is time-discounted p_i - c_i (T-t+1).
**Obstruction:** The threshold rho* is set online from an unbounded arrival stream and the utility scales with the remaining horizon (T-t+1), so a single-round finite grid cannot represent the mechanism's incentive structure. (Track 1: continuous bid space with no valid discretization)
**Human task:** Fix the horizon and threshold to prove per-round truthfulness, then argue the online composition separately.
**Diagnosed:** 2026-09-03

## Zheng2023fl_market (VCG) — R2

**Mechanism:** Sort by unit value v_i^unit ascending and include i while v_i^unit <= B / sum of included d_j eps_j; payment is a proportional share d_i eps_i p^unit of the budget.
**Obstruction:** The winner set is defined by a self-referential budget-density condition (the threshold depends on the set being built), a budget-greedy rather than argmax/top-k, and the payment is a proportional budget share rather than a Clarke pivot. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** Prove the greedy is monotone and identify the true critical unit price per client to get a critical-value truthfulness argument.
**Diagnosed:** 2026-09-03

## GPS2023afl_recruit (VCG) — R2

**Mechanism:** Selects participants 'among the lowest bids' (a reverse top-k with unspecified k) and pays p_i = b_i - C_i(t), which equals the stated client utility.
**Obstruction:** The winner count is not specified so the rule is not a fixed top-k, and the payment pays the bid minus own cost — a first-price form, not a Clarke pivot; the payment and utility LaTeX are literally identical, so the recorded model is degenerate. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** Recover k and the true payment from the paper; a first-price reverse auction is not DSIC and may warrant a counterexample search instead.
**Diagnosed:** 2026-09-03

## Cui2024auction_market (VCG) — R2

**Mechanism:** Allocation argmax_i b_{t,i} over reported bids; payment p_{i,j} = b_{t,j} * Delta G_{t,i}, a bid times a marginal model-gain term.
**Obstruction:** The payment multiplies another agent's bid by a continuous marginal-gain quantity Delta G_{t,i} produced by model training; it is a first-price-style product, not a Clarke pivot, and Delta G has no valid finite discretization tied to the reports. (Track 1: continuous bid space with no valid discretization)
**Human task:** Determine whether Delta G_{t,i} is the second-price critical value in disguise; if not, the mechanism is not Groves and needs its own truthfulness proof.
**Diagnosed:** 2026-09-03

## Zhang2024auction_comm (VCG) — R2

**Mechanism:** Allocation X = argmax_{i in K} S(s_i, p_i) over an unspecified score S; payment p_i = sum_{j != i} c_j - c_i.
**Obstruction:** The payment subtracts the agent's OWN cost c_i from the sum of others' costs, so it is not a welfare-with-vs-without-i pivot and is directly decreasing in i's own report; the score S is also left undefined, so the argmax has no encodable objective. (Track 1: non-polynomial gap Z3 cannot linearize)
**Human task:** Define S and recheck the payment against the paper — as recorded it is not a Groves pivot and is likely a transcription error.
**Diagnosed:** 2026-09-03
