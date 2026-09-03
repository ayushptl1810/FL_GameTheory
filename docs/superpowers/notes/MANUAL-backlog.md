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
**Obstruction:** The payment subtracts the agent's OWN cost c_i from the sum of others' costs, so it is not a welfare-with-vs-without-i pivot and is directly decreasing in i's own report; the score S is also left undefined, so the argmax has no encodable objective. (Track 1: payment subtracts the agent's own reported cost (sum_{j!=i} c_j - c_i); not a Clarke pivot)
**Human task:** Define S and recheck the payment against the paper — as recorded it is not a Groves pivot and is likely a transcription error.
**Diagnosed:** 2026-09-03

## International_Journal_of_Intelligent_Systems_-_2024_-_Wan_-_Hierarchical_Incentive_Mechanism_for_Federated_Learning__A (Contract) — R3a

**Mechanism:** Hierarchical two-layer incentive mechanism; recorded IC reduces after prose-stripping to \varphi_m R_m - C V_m \geq \varphi_z R_z - C V_z.
**Obstruction:** Both sides of the recorded IC are evaluated at their own type, so the RHS carries no deviating-type dependence. The Task 11-pre soundness gate rejects it: certifying it would prove an ordering of equilibrium utilities, not incentive compatibility. (Track 1: IC is an equilibrium-utility ordering (both sides at own type), not U_i(contract_j); soundness gate correctly rejects -- no substitutable screening IC)
**Human task:** Re-extract the paper's true self-selection constraint U_m(contract_z) from the PDF so the RHS is the type-m agent's utility from contract z, then re-run Track 1.
**Diagnosed:** 2026-09-03

## Wang2022motilearn_contract (Contract) — R3a

**Mechanism:** MotiLearn contract menu with per-type effort/reward pairs.
**Obstruction:** The recorded IR uses subscript `a` while the IC uses `n`/`i`. The parser can identify a single type subscript from the IR but that subscript never appears in the IC RHS, so no sound (type, contract) index pair can be formed. Equating `a` with `n` would be an unverified guess. (Track 1: IR indexed by `a`, IC by `n`/`i`; `type_sub` never appears in the IC RHS -- cannot equate indices without guessing)
**Human task:** Re-transcribe IC and IR from the PDF under one consistent index convention, then re-run Track 1.
**Diagnosed:** 2026-09-03

## Ding2020contract_multidim (Contract) — R3a

**Mechanism:** Multidimensional-type contract with menu items phi_i = (s_i, r_i).
**Obstruction:** The recorded client utility r_i - \theta_i s_i contains no occurrence of the contract variable \phi_i, so the contract substitution \phi_i -> \phi_j leaves the RHS identical to the LHS. The IC gap is identically zero: a trivially-true obligation that certifies nothing about the paper's mechanism. (Track 1: utility r_i - theta_i s_i has no dependence on the contract variable phi_i; substituting phi_i->phi_j yields an identical RHS -- degenerate IC (data-quality gap, unprovable as recorded))
**Human task:** Correct the transcription of client_utility_latex so it depends on the contract bundle \phi_i (i.e. on s_i and r_i as menu items), then re-run Track 1.
**Diagnosed:** 2026-09-03

## Kang2022blockchain_metaverse (Contract) — R3a

**Mechanism:** Blockchain-metaverse contract stated as an adjacent (local) incentive constraint between neighbouring types.
**Obstruction:** The deviation index is n-1, which the SymPy layer reads as a single symbol named R_{n - 1} rather than as index n offset by one. The verifier's substitution machinery enumerates concrete integer indices and has no notion of an offset index, so the adjacent-IC form cannot be instantiated. (Track 1: R_{n-1} parses as a single symbol, not an iterable index; needs adjacent-IC semantics in _contract_check_core -- out of scope)
**Human task:** Add adjacent-IC (local downward/upward) semantics to _contract_check_core so an offset index n-1 instantiates to concrete neighbour pairs, or re-transcribe the paper's global IC if it states one.
**Diagnosed:** 2026-09-03

## Wen2025diffusion_contract (Contract) — R3a

**Mechanism:** Diffusion-model-generated two-period intertemporal contract; the entry records only the period-2 static myopic IC/IR.
**Obstruction:** Every ^2 / ^1 in the recorded IC/IR is a period index, confirmed by contract_menu_latex's superscript-before-subscript ordering and by the entry's own notes. Reading them as exponents yields a different proof obligation than the paper's (linear) utility u_n = theta_n R_n - c T_n - E, and the intertemporal linkage between periods is absent from the entry entirely. Any verdict on the recorded fields would certify a mechanism the paper does not claim. (Track 1: recorded IC/IR is PERIOD-2 static myopic only (^2/^1 are period indices, not exponents); the paper's true mechanism is a two-period intertemporal contract not represented in the entry)
**Human task:** Transcribe the paper's full two-period intertemporal contract (both periods plus the linking constraint) with period indices distinguished from exponents, then decide whether an intertemporal IC is expressible on the Track 1 grid.
**Diagnosed:** 2026-09-03

## 2602_21844 (Contract) — R3a

**Mechanism:** Bayesian contract with an IC stated as an expectation E_{c_{-k}}[...] over the other agents' private costs.
**Obstruction:** The IC carries a multi-agent posterior expectation. Track 1 correctly bails out (stripping the expectation and grid-checking pointwise would prove something strictly stronger than the paper claims), and Track 4's symbolic integrator cannot reduce the E_{c_{-k}} expectation over the joint type distribution to a closed form it can check. (Track 4: expectation-form (Bayesian) IC integral -- SymPy Track 4 cannot evaluate the multi-agent posterior expectation to a posynomial-checkable closed form)
**Human task:** Supply the closed-form (integrated) interim utility for the paper's type distribution, or extend Track 4 with a numeric-quadrature Bayesian-IC path with an explicit soundness argument.
**Diagnosed:** 2026-09-03

## 2408_13223 (Contract) — R3a

**Mechanism:** Nash action-choice equilibrium over {abstain, join, buy} with rewards assigned directly per platform-known type.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- Nash action-choice equilibrium over {abstain, join, buy} with rewards assigned directly per platform-known type; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

## 2505_02462 (Contract) — R3a

**Mechanism:** Graph-based reciprocal model-sharing with a single self-reported-cost truthfulness property, no discrete type set and no (effort, reward) menu.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- graph-based reciprocal model-sharing with a single self-reported-cost truthfulness property, no discrete type set and no (effort, reward) menu; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

## 2505_05842 (Contract) — R3a

**Mechanism:** Dynamic Bayesian persuasion (signal over the posterior plus a single uniform reward), governed by Bayesian Consistency/Plausibility/Benefit, not by a type-indexed menu.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- dynamic Bayesian persuasion (signal over the posterior plus a single uniform reward), governed by Bayesian Consistency/Plausibility/Benefit, not by a type-indexed menu; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

## 2605_02935 (Contract) — R3a

**Mechanism:** Blockchain smart contracts with per-role strategy-proofness against a fixed deviation set; no type space, cost function, or contract menu.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- blockchain smart contracts with per-role strategy-proofness against a fixed deviation set; no type space, cost function, or contract menu; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

## Bornstein2023realistic_incentive (Contract) — R3a

**Mechanism:** Moral hazard over a continuously self-chosen contribution m_i (Nash equilibrium condition); the paper explicitly distinguishes itself from contract theory.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- moral hazard over a continuously self-chosen contribution m_i (Nash equilibrium condition); the paper explicitly distinguishes itself from contract theory; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

## Huang2024aigc (Contract) — R3a

**Mechanism:** A single uniform unit-data price with post-hoc behavioural type regions; the paper never states incentive compatibility, screening, or a menu.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- a single uniform unit-data price with post-hoc behavioural type regions; the paper never states incentive compatibility, screening, or a menu; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

## Karimireddy2022data_sharing (Contract) — R3a

**Mechanism:** Moral hazard / continuous-action Nash with verifiable costs; the paper's own 'incentive compatibility' theorem is a no-distortion property, not self-selection.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- moral hazard / continuous-action Nash with verifiable costs; the paper's own 'incentive compatibility' theorem is a no-distortion property, not self-selection; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

## Li2026network (Contract) — R3a

**Mechanism:** Per-type closed-form payment plus a 3-action (abstain/join/buy) equilibrium, not type-i-vs-type-j screening.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- per-type closed-form payment plus a 3-action (abstain/join/buy) equilibrium, not type-i-vs-type-j screening; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

## Zhang2020fedserving (Contract) — R3a

**Mechanism:** Bayesian peer-prediction / Bayesian Truth Serum with BNE truthfulness, no discrete client type space and no self-selected menu.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- Bayesian peer-prediction / Bayesian Truth Serum with BNE truthfulness, no discrete client type space and no self-selected menu; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

## Zhao2023truthful (Contract) — R3a

**Mechanism:** Moral hazard (hidden action): one desired action assigned to every client, truthfulness proved as a Nash equilibrium over actions.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- moral hazard (hidden action): one desired action assigned to every client, truthfulness proved as a Nash equilibrium over actions; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

## 2102_03401 (Contract) — R3a

**Mechanism:** CAV data-quality contract menu {(P_m, R_m)}; utility theta_m R_m - u_3(kappa c phi^2 s-bar I + P_m t-hat).
**Obstruction:** The IC and IR parse cleanly (type subscript m, contract subscript hat-m, soundness gate passes), but the cost term is wrapped in u_3(.), a function the entry never defines algebraically. _sp_to_z3 raises 'unsupported SymPy node u_{3}' at the first index pair, so Track 1 produces no obligation and the reported verdict is the generic linear-cost template only. (Track 1: utility contains the undefined opaque function u_3(.) -- Z3 encoding rejects it ('unsupported SymPy node u_{3}'), so no grid obligation can be built)
**Human task:** Supply the algebraic form of u_3(.) from the paper (or confirm it is affine and inline it), then re-run Track 1.
**Diagnosed:** 2026-09-03

## 2308_12502 (Contract) — R3a

**Mechanism:** Multidimensional-type (theta_j, xi_j) privacy/training contract menu {(d_j, r_j^L)}.
**Obstruction:** Two independent obstructions. (1) The entry's own notes record that kappa_j is itself a sum over OTHER agents' contract terms -- a population coupling the verifier's single-agent type-i-vs-type-j substitution cannot express. (2) Even ignoring that, r_j^L reads as r_j raised to a symbolic exponent L and _sp_to_z3 raises 'unsupported exponent L'; L is a layer label, not a power. (Track 1: population-coupled cost term (kappa_j sums over other agents' contracts) -- single-agent substitution cannot represent it; additionally r_j^L carries a symbolic superscript Z3 rejects as an exponent)
**Human task:** Re-transcribe r_j^L with the layer label distinguished from an exponent, and decide whether a population-coupled cost admits any single-agent encoding; if not, this needs a multi-agent equilibrium track.
**Diagnosed:** 2026-09-03

## 2407_02845 (Contract) — R3a

**Mechanism:** FedPot defence-data-quality contract menu {pi_m = (V_m, R_m)}; utility ln(theta_m R_m) - C_m.
**Obstruction:** The IC/IR parse and the soundness gate passes, but the log-utility encoding requires the argument theta_m R_m to be provably positive before _sp_to_z3 will admit it. The entry declares no positivity domain for theta_m or R_m, so the encoding raises and Track 1 yields nothing; the recorded verdict is the generic template only. (Track 1: log(theta_m R_m) argument sign not established -- Z3 encoding rejects the transcendental ('log argument sign not established'))
**Human task:** Record the paper's positivity domain for theta_m and R_m (or a general positivity precondition for log-utility Contract entries) so the transcendental can be admitted, then re-run Track 1.
**Diagnosed:** 2026-09-03

## Han2025paid_models (Contract) — R3a

**Mechanism:** Paid-model contract with private per-unit collection cost c_i; utility E[v(r_i)] - c_i m_i.
**Obstruction:** The IC parses (type subscript i, contract subscript j, soundness gate passes) but E[v(r_i)] is an expectation of an undefined valuation function. _sp_to_z3 raises 'unsupported SymPy node v'. Track 4's Bayesian path cannot help either, because v has no algebraic form to integrate. (Track 1: utility contains the undefined opaque valuation function v(.) inside an expectation E[v(r_i)] -- Z3 encoding rejects it ('unsupported SymPy node v'))
**Human task:** Supply v(.)'s algebraic form and the distribution the expectation is over, then route to Track 4 (Bayesian) rather than Track 1.
**Diagnosed:** 2026-09-03

## Kang2019reliable_contract (Contract) — R3a

**Mechanism:** Reliable-worker contract menu {(R_n, f_n)} with data-quality type theta_n = psi/log(1/epsilon_n).
**Obstruction:** The IC/IR parse and the soundness gate passes. The communication-cost term divides by a Shannon capacity B ln(1 + rho_n h_n / N_0); _sp_to_z3 will not admit the log without an established argument sign, and the entry declares no positivity domain for rho_n, h_n or N_0. No Track 1 obligation is built. (Track 1: Shannon-capacity term log(1 + rho h / N_0) in the denominator -- Z3 encoding rejects it ('log argument sign not established'))
**Human task:** Declare the positivity domain for the channel parameters (rho, h, N_0 > 0) so the capacity log is admissible, then re-run Track 1.
**Diagnosed:** 2026-09-03

## Nguyen2025right_reward (Contract) — R3a

**Mechanism:** Joint capability/joining-time contract phi_k = {e_k, t_k, r_k} with multidimensional type (theta_k, t_k).
**Obstruction:** The IC parses via utility-call expansion (type subscript k, contract subscript k-prime, soundness gate passes), but the staleness weight h(t_k) is an undefined function and _sp_to_z3 raises 'unsupported SymPy node h'. The type is also genuinely two-dimensional, which the single-type-subscript machinery does not model even once h is supplied. (Track 1: utility contains the undefined opaque staleness function h(t_k) -- Z3 encoding rejects it ('unsupported SymPy node h'))
**Human task:** Supply h(.)'s algebraic form from the paper, and separately decide whether the joint (capability, joining-time) type needs a two-dimensional screening encoding.
**Diagnosed:** 2026-09-03

## Yang2023async_contract (Contract) — R3a

**Mechanism:** Asynchronous FL contract menu {(R_n, e_n)} with data-quality type theta_n.
**Obstruction:** The IR reads theta R - xi e c f^2 - E_com >= 0, where E_com is a scalar communication-energy constant. The Task 11-pre Bayesian guard (_BAYESIAN_RE) matches the E_{subscript} form and correctly bails Track 1 out rather than risk stripping a real expectation. The entry has no type distribution, so Track 4 cannot pick it up either, and the entry falls through to the generic template. (Track 1: IR's E_{com} communication-energy term is indistinguishable from a Bayesian expectation E_{...}[.]; the Bayesian bail-out fires and Track 1 declines, while Track 4 has no distribution to integrate)
**Human task:** Rename or re-transcribe E_com so it is not shaped like an expectation operator (e.g. E^{com} or Ecom), then re-run Track 1; the IC itself already parses.
**Diagnosed:** 2026-09-03

## Kang2019contract_mobile (Contract) — R3a

**Mechanism:** Mobile-device contract; routed to Track 3 (mpmath.iv branch-and-bound, delta-sound).
**Obstruction:** Track 1 does not apply and Track 3's interval branch-and-bound cannot cover the box: the IC carries 9 free variables and the IR 11, so the branch count is beyond the search budget at the configured delta. The verifier reports UNKNOWN honestly rather than a partial-coverage result. (Track 3: 9 free variables in IC and 11 in IR -- interval box search is intractable at delta=0.001 over [0.001, 1.0])
**Human task:** Reduce the free-variable count by fixing paper-declared constants to their stated values (or narrowing their domains), then re-run Track 3; alternatively transcribe the IC/IR in a form Track 1 can encode symbolically.
**Diagnosed:** 2026-09-03

## Tian2021contract (Contract) — R3a

**Mechanism:** Contract with a LaTeX-parsed entry-specific utility; n=2 types, IR binding at type-0 with adjacent upward IC.
**Obstruction:** _type_family() cannot match the entry's type_variable to any indexed symbol family in the parsed utility, so no type-ordering precondition is imposed. Without an ordering, Z3's counterexamples fall in parameter regions (reversed type order) the paper excludes, and the verifier correctly suppresses them to UNKNOWN rather than report an artifact. Both IC and IR come back UNKNOWN. (Track 1: type-ordering unidentified -- verifier cannot fix the single-crossing direction, so IC counterexamples are suppressed and neither IC nor IR is decidable)
**Human task:** Correct the entry's type_variable field so it names the indexed type family appearing in the utility, letting the verifier impose the single-crossing ordering; then re-run Track 1.
**Diagnosed:** 2026-09-03
