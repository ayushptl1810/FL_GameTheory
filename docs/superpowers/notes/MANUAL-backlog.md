# MANUAL Backlog

One paragraph per corpus entry that no automated track can decide. Appended to from R2 onward; the R7 honesty pass closes it out.

## Haupt2021auctions (VCG) — R2

**Mechanism:** Score-comparison allocation w_i chosen by pairwise comparison b_i(s-hat - s_i) against a permuted rival, with a Punish() term in the payment.
**Obstruction:** The payment contains an opaque Punish(s_j - s_i) aggregate and the allocation is a pairwise-comparison cases rule over a permutation pi(i), which is neither argmax nor top-k and not linearizable on a finite grid. (Track 1: non-polynomial gap Z3 cannot linearize)
**Human task:** Define Punish() concretely and determine whether the pairwise-comparison allocation reduces to an argmax over a scoring function.
**Diagnosed:** 2026-09-03

## Lim2020edge_collab (VCG) — R2

**Mechanism:** No allocation or payment rule recorded in the corpus entry; the paper's edge-collaboration mechanism is described only in prose.
**Obstruction:** Both allocation_rule_latex and payment_rule_latex are null, so there is no closed-form rule to classify or discharge on a grid. (Track 1: RL-policy or opaque-algorithm allocation, not a closed-form rule)
**Human task:** Re-extract the allocation and payment rules from the paper PDF before any solver attempt.
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

## 2308_12502 (Contract) — R3a

**Mechanism:** Multidimensional-type (theta_j, xi_j) privacy/training contract menu {(d_j, r_j^L)}.
**Obstruction:** Two independent obstructions. (1) The entry's own notes record that kappa_j is itself a sum over OTHER agents' contract terms -- a population coupling the verifier's single-agent type-i-vs-type-j substitution cannot express. (2) Even ignoring that, r_j^L reads as r_j raised to a symbolic exponent L and _sp_to_z3 raises 'unsupported exponent L'; L is a layer label, not a power. (Track 1: population-coupled cost term (kappa_j sums over other agents' contracts) -- single-agent substitution cannot represent it; additionally r_j^L carries a symbolic superscript Z3 rejects as an exponent)
**Human task:** Re-transcribe r_j^L with the layer label distinguished from an exponent, and decide whether a population-coupled cost admits any single-agent encoding; if not, this needs a multi-agent equilibrium track.
**Diagnosed:** 2026-09-03

## Yang2023async_contract (Contract) — R3a

**Mechanism:** Asynchronous FL contract menu {(R_n, e_n)} with data-quality type theta_n.
**Obstruction:** The IR reads theta R - xi e c f^2 - E_com >= 0, where E_com is a scalar communication-energy constant. The Task 11-pre Bayesian guard (_BAYESIAN_RE) matches the E_{subscript} form and correctly bails Track 1 out rather than risk stripping a real expectation. The entry has no type distribution, so Track 4 cannot pick it up either, and the entry falls through to the generic template. (Track 1: IR's E_{com} communication-energy term is indistinguishable from a Bayesian expectation E_{...}[.]; the Bayesian bail-out fires and Track 1 declines, while Track 4 has no distribution to integrate)
**Human task:** Rename or re-transcribe E_com so it is not shaped like an expectation operator (e.g. E^{com} or Ecom), then re-run Track 1; the IC itself already parses.
**Diagnosed:** 2026-09-03

## Khan2019edge (Stackelberg) — R3b

**Mechanism:** Base station posts a reward; UEs choose a number of local iterations. Utilities are described in words only.
**Obstruction:** equilibrium_existence not established in the corpus entry -- position-paper (short IEEE magazine article), the Stackelberg game is described only qualitatively, and no explicit utility, derived best-response, FOC or IR constraint appears anywhere in the 7 pages. (Track 1: no proved equilibrium; Track 1 Stackelberg needs one)
**Human task:** a technical treatment with a derived Stackelberg equilibrium is needed; this venue does not provide one -- replace the entry with a full-length paper or drop it from the Stackelberg slice.
**Diagnosed:** 2026-09-03

## 2103_05866 (Stackelberg) — R3b

**Mechanism:** A three-stage game: the protocol designer sets fee-per-byte and a waiting-tax rate vector (Stage I), users choose transaction generation rates (Stage II), and miners choose which transactions to include (Stage III).
**Obstruction:** The entry is explicitly a THREE-STAGE Stackelberg game and the recorded follower_decision ('transaction generation rates and transaction selection') conflates two distinct player layers with different equilibrium concepts. best_response_latex is a prose note recording that the Stage-III miner NE is a discrete argmin over a queue set and the Stage-II user equilibrium is a multi-branch piecewise closed form built from M/M/1 auxiliary functions that was judged too OCR-risky to transcribe; follower_foc_latex is null. (Track 1: >2-stage / multi-layer game -- 2-player leader-follower FOC model does not apply)
**Human task:** split the entry into its two follower layers with separate equilibrium statements, transcribe the Stage-II piecewise equilibrium from Eqs. 16-19, and give the checker a multi-stage backward-induction model.
**Diagnosed:** 2026-09-03

## 2412_05636 (Stackelberg) — R3b

**Mechanism:** Server posts a reward R_t and sampling probability x_t; each client picks a correction factor alpha_i^t adjusting its privacy budget over a T-period horizon.
**Obstruction:** best_response_latex (Theorem 1, Eq. 21) is a genuine backward recursion: alpha_i^{t*} depends on alpha_i^r for all r > t via S(t) and the product prod_{r=t+1}^{j-1} alpha_i^r, terminated by alpha_i^T = 0. follower_foc_latex is the bare placeholder 'dU_i/dalpha_t^i = 0' with no algebraic content. Track 1's single-shot d(leader_utility)/d(follower_decision) check cannot encode a multi-period dynamic-programming recursion. (Track 1: follower best-response is a backward recursion over the horizon -- Track 1 single-shot FOC cannot encode it)
**Human task:** either unroll the recursion for a fixed small horizon T and record the resulting explicit closed form, or add a finite-horizon backward-induction mode to the Stackelberg checker.
**Diagnosed:** 2026-09-03

## Chu2023hierarchical (Stackelberg) — R3b

**Mechanism:** Cloud server sets rewards to edge servers; each edge server chooses its number of local aggregations K_l.
**Obstruction:** best_response_latex is deliberately null: the paper states on p.21, immediately after the recorded FOC (Eq. 31), that there is 'a lack of the closed-form solution for the optimal edge aggregation strategies of the edge server l', and solves the equilibrium numerically by variational inequality / iterative updates instead. The recorded follower_foc_latex mixes Z_l = sqrt(A_l - F_l K_l / B_l) inside rational terms of degree 2 in Z_l and has no closed-form root in K_l, so there is no equilibrium point for the FOC check to substitute and verify. (Track 1: follower FOC is transcendental with no closed-form root (paper states this explicitly) -- Track 1 cannot solve the stationarity equation)
**Human task:** decide whether a numerically-certified equilibrium (interval enclosure of the FOC root) is acceptable evidence for this corpus, and if so add a numeric-root Track to the Stackelberg checker.
**Diagnosed:** 2026-09-03

## Luo2023unbiased (Stackelberg) — R3b

**Mechanism:** Server sets customized per-client prices P_n; each client n chooses a participation probability q_n in [0, q_{n,max}].
**Obstruction:** best_response_latex is a bare argmax placeholder (q_n^{SE}(P) = argmax_{0<=q_n<=q_{n,max}} U_n(q_n,P_n)) with no algebraic content. follower_foc_latex is implicit in the unknown -- P_n + v_n (alpha/R) a_n^2 G_n^2 / q_n^{*2} - 2 c_n q_n^* = 0 is a cubic in q_n* whose root the entry never records -- and the true optimum is the box-clipped value, not the interior stationary point. There is no closed-form single-variable best response for the FOC check to verify against. (Track 1: follower best-response is an implicit argmax over a box and the recorded FOC is an implicit cubic in q_n* with no transcribed root -- Track 1 has no closed form to substitute)
**Human task:** record the explicit (clipped) root of the cubic from the paper, or add root-solving plus box-projection to the Stackelberg checker.
**Diagnosed:** 2026-09-03

## Pandey2019crowd (Stackelberg) — R3b

**Mechanism:** Server posts a uniform reward r; each client k chooses a local accuracy level theta_k.
**Obstruction:** follower_foc_latex is 1/theta_k - log(1/theta_k) = (r + nu_k T_k)/((1-nu_k) gamma_k) - 1, a transcendental equation in theta_k with no closed-form root (its solution is a Lambert-W branch the paper never writes down). best_response_latex is correspondingly implicit: theta_k*(r) = min{ hat-theta_k(r) | g_k(r) = log(e^{1/hat-theta_k} hat-theta_k), theta_th } -- it defines hat-theta_k only as 'the value satisfying' the transcendental relation, then clips at theta_th. Nothing algebraic can be substituted into a d(leader_utility)/d(follower_decision) check. (Track 1: follower FOC is transcendental (1/theta - log(1/theta) = const) with no closed-form root, and the best response is a min-clipped implicit solution -- Track 1 cannot solve the stationarity equation)
**Human task:** record the Lambert-W closed form if the branch can be pinned down soundly, and add transcendental/special-function support plus the min-clip to the checker.
**Diagnosed:** 2026-09-03

## Pang2025quality (Stackelberg) — R3b

**Mechanism:** Aggregator chooses payment functions evaluating agents' contributions; each agent k chooses an effort level e_k in [0,1].
**Obstruction:** Payment_k = f(Q / (Phi delta_k^2(e_k) + Phi delta_{k'}^2(e_{k'}) + Upsilon)) and Cost_k = c * d(|delta_k(0) - delta_k(e_k)|) are built from unspecified generic functions f and d, so the recorded follower_foc_latex (du_k/de_k = 0) and best_response_latex (a cases-form: 0 if the max is non-positive, else 'hat-e_k where du_k/de_k = 0') carry no algebraic content -- they restate the definition of a stationary point rather than solve it. Only an experiment-specific logarithmic instantiation (Sec. 6.2) has a closed form, and even that is in the Wasserstein variable delta_k rather than e_k. Venue is viXra (non-peer-reviewed). The entry's notes additionally flag that Appendix A.9 restates the same Theorem 4 in an inconsistent hat/no-hat notation, unresolved. (Track 1: payment/cost are unspecified generic functions f, d -- no algebraic form to differentiate)
**Human task:** pin f and d to the paper's actual instantiation (and resolve the Appendix A.9 notation conflict) before any obligation can be built; given the venue, verify the result independently first.
**Diagnosed:** 2026-09-03

## 2101_05628 (Stackelberg) — R4

**Mechanism:** OSPs (leaders) announce prices; each mobile device (follower) picks an offloading strategy vector alpha_i = (alpha_{i,1},...,alpha_{i,N}) splitting its task across N OSPs.
**Obstruction:** Both best_response_latex and follower_foc_latex are null, and the follower decision is an N-dimensional simplex-constrained vector coupled through the shared congestion term D_i(alpha_i, A_{-i}). _stackelberg_check_core's single-variable d(leader_utility)/d(follower_decision) FOC cannot express the stationarity system. (Track 1: vector follower decision -- single-variable FOC reduction does not apply)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round.
**Diagnosed:** 2026-09-04

## 2101_12428 (Stackelberg) — R4

**Mechanism:** Chains post block rewards R_m; each staker n allocates a stake vector s_n = (s_n^1,...,s_n^M) across M chains subject to a budget sum_m s_n^m <= B_n.
**Obstruction:** The recorded follower_foc_latex is a budget-eliminated *difference* of two per-chain derivatives (dU/ds_n^m - dU/ds_n^M = 0 for m=1..M-1), so the M-1 conditions are coupled to each other through the eliminated component s_n^M = B_n - sum_{m<M} s_n^m. It is not a single-variable stationarity equation and the components do not decouple, so the single-variable FOC path cannot consume it. (Track 1: vector follower decision -- single-variable FOC reduction does not apply)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round.
**Diagnosed:** 2026-09-04

## 2502_10765 (Stackelberg) — R4

**Mechanism:** Provider sets unit prices p_r and p_w; each user jointly chooses rendering resources x_i^r AND bandwidth resources x_i^w.
**Obstruction:** The follower decision is two variables chosen jointly; follower_foc_latex records two separate partial-derivative equations and best_response_latex two separate maximizers. The single-variable FOC path has no way to express a joint stationarity system, and the entry's own follower_decision field flags that the verifier's pipeline cannot yet handle this. (Track 1: vector follower decision -- single-variable FOC reduction does not apply)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round.
**Diagnosed:** 2026-09-04

## Guo2023stackelberg_industrial (Stackelberg) — R4

**Mechanism:** Leader allocates reward R_n and model size sigma; each follower jointly chooses data quantity |D'_n| AND compensation S_n (FS_n = (D'_n, S_n)).
**Obstruction:** Both best_response_latex and follower_foc_latex are null (fail-closed on human review) and the follower decision is an explicit two-component joint choice inside a multi-objective bi-level program. There is no recorded stationarity condition of any kind for Track 1 to discharge. (Track 1: vector follower decision -- single-variable FOC reduction does not apply)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round.
**Diagnosed:** 2026-09-04

## Li2025split (Stackelberg) — R4

**Mechanism:** SFL tenants post price incentives P_i; each device j chooses a participation vector {q_{i,j}}_{i in [1,M]} across all M tenants simultaneously.
**Obstruction:** best_response_latex is a bare argmax placeholder (q*_{i,j} = argmax lambda_j) with no algebraic content, and follower_foc_latex is a full KKT system: M stationarity equations plus two complementary-slackness conditions, two primal feasibility conditions and two dual feasibility conditions for the simplex constraints phi_j^{(1)}, phi_j^{(2)}. That is a constrained multi-variable system, not a single-variable FOC. (Track 1: vector follower decision -- single-variable FOC reduction does not apply)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round.
**Diagnosed:** 2026-09-04

## Liu2026fedbud (Stackelberg) — R4

**Mechanism:** Server pays R^t to edge nodes; each node k jointly chooses data volume B_k^t AND privacy/noise budget epsilon_k^t.
**Obstruction:** The follower decision is two variables chosen jointly and follower_foc_latex is null (fail-closed). best_response_latex gives two separate maximizers but with no recorded stationarity conditions to differentiate against, so there is nothing for a d(leader_utility)/d(follower_decision) check to consume, and the single-variable path could not express the joint system in any case. (Track 1: vector follower decision -- single-variable FOC reduction does not apply)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round.
**Diagnosed:** 2026-09-04

## Wang2022blockchain (Stackelberg) — R4

**Mechanism:** Leader sets unit prices p_ti and p_mi; each miner i jointly chooses CPU cycles per second for training q_ti AND for mining q_mi.
**Obstruction:** Two obstructions compound. (1) The follower decision is two variables chosen jointly, while follower_foc_latex records only the single partial dU_i/dq_ti = p_ti - 2 rho_i q_ti = 0 -- there is no recorded condition for q_mi. (2) That FOC is inconsistent with the recorded utility (U_i has revenue mu_i p_ti / q_ti and cost rho_i mu_i q_ti^2, so the true derivative is strictly negative and the optimum is a corner, not an interior stationary point), and the stored best_response q_ti* = (p_ti/rho_i)^{1/3} is not the root of the recorded FOC either. Substituting it into a d(leader_utility)/d(follower_decision) check would certify a stationarity claim the entry's own algebra contradicts. (Track 1: vector follower decision -- single-variable FOC reduction does not apply; the stored best response is additionally not an interior FOC solution)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round. Also: the paper's own Sec 3.1.2 prints dU/dq < 0 for both variables then miscalls the objective concave; the real stationarity is a Lagrangian on the time constraint (Eqs. 30-31) matching NEITHER the stored follower_foc_latex NOR best_response_latex (corner solution) -- needs a full PDF re-derivation in R6.
**Diagnosed:** 2026-09-04

## Yu2022multi_leader_fl (Stackelberg) — R4

**Mechanism:** Multiple task leaders post reward rates p_i; each data owner j chooses a task-accuracy vector {epsilon_j^i} for tasks i = 1..K simultaneously under a shared resource budget.
**Obstruction:** Three compounding obstructions. The follower chooses a K-component vector coupled by the resource budget sum_i L_j^i <= tau_j^max; best_response_latex is a three-branch piecewise form whose active-constraint branch carries a Lagrange multiplier lambda_j found only by bisection search (Algorithm 1, Eq. 27); and both branch values bar-epsilon and hat-epsilon are defined implicitly as roots of the transcendental relation log(e^{1/eps} eps) = const, which the recorded follower_foc_latex also is. None of the three is expressible as a single-variable closed-form stationarity condition. (Track 1: vector follower decision -- single-variable FOC reduction does not apply)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round.
**Diagnosed:** 2026-09-04

## Kang2019reliable_contract (Contract) — R4

**Mechanism:** Reliable-worker contract menu {(R_n, f_n)} with data-quality type theta_n = psi/log(1/epsilon_n).
**Obstruction:** The IC/IR parse and the soundness gate passes. The communication-cost term divides by a Shannon capacity B ln(1 + rho_n h_n / N_0); _sp_to_z3 will not admit the log without an established argument sign, and the entry declares no positivity domain for rho_n, h_n or N_0. No Track 1 obligation is built. (Track 1: Shannon-capacity term log(1 + rho h / N_0) in the denominator -- Z3 encoding rejects it ('log argument sign not established'))
**Human task:** R4 admitted the Shannon-capacity log(1 + rho_n h_n / N_0) via a positivity_domain field (Sec III-C: rho_n, h_n, N_0 > 0) + the _is_definitely_positive_sum integer-power fix, but Z3 still returns UNKNOWN on both IC and IR -- the obstruction is not the log admissibility.
**Diagnosed:** 2026-09-04

## 2407_02845 (Contract) — R4

**Mechanism:** FedPot defence-data-quality contract menu {pi_m = (V_m, R_m)}; utility ln(theta_m R_m) - C_m.
**Obstruction:** The IC/IR parse and the soundness gate passes, but the log-utility encoding requires the argument theta_m R_m to be provably positive before _sp_to_z3 will admit it. The entry declares no positivity domain for theta_m or R_m, so the encoding raises and Track 1 yields nothing; the recorded verdict is the generic template only. (Track 1: log(theta_m R_m) argument sign not established -- Z3 encoding rejects the transcendental ('log argument sign not established'))
**Human task:** R4 checked pdfs/2407.02845.pdf: admitting log(theta_m R_m) needs theta_m R_m >= 1, which the paper never states (only C5: R_m > 0, a type ordering theta_1 <= ... <= theta_M, and a budget cap). Genuine ceiling absent a domain lower bound.
**Diagnosed:** 2026-09-04

## Nguyen2025right_reward (Contract) — R4

**Mechanism:** Joint capability/joining-time contract phi_k = {e_k, t_k, r_k} with multidimensional type (theta_k, t_k).
**Obstruction:** The IC parses via utility-call expansion (type subscript k, contract subscript k-prime, soundness gate passes), but the staleness weight h(t_k) is an undefined function and _sp_to_z3 raises 'unsupported SymPy node h'. The type is also genuinely two-dimensional, which the single-type-subscript machinery does not model even once h is supplied. (Track 1: utility contains the undefined opaque staleness function h(t_k) -- Z3 encoding rejects it ('unsupported SymPy node h'))
**Human task:** R4 checked pdfs/Nguyen2025right_reward.pdf: h(t_k) is defined (Eq. 2) but 2-branch piecewise (1 + vartheta ln(2 t_k) if t_k in CLPs, else 1); opaque_function_forms maps one name to one form and cannot represent a piecewise function.
**Diagnosed:** 2026-09-04

## Han2025paid_models (Contract) — R4

**Mechanism:** Paid-model contract with private per-unit collection cost c_i; utility E[v(r_i)] - c_i m_i.
**Obstruction:** The IC parses (type subscript i, contract subscript j, soundness gate passes) but E[v(r_i)] is an expectation of an undefined valuation function. _sp_to_z3 raises 'unsupported SymPy node v'. Track 4's Bayesian path cannot help either, because v has no algebraic form to integrate. (Track 1: utility contains the undefined opaque valuation function v(.) inside an expectation E[v(r_i)] -- Z3 encoding rejects it ('unsupported SymPy node v'))
**Human task:** R4: no source PDF exists in pdfs/ and the entry's arxiv_id/source/notes are all null -- the opaque valuation v(.) inside E[v(r_i)] cannot be transcribed.
**Diagnosed:** 2026-09-04

## Jiao2019auto_auction (VCG) — R4

**Mechanism:** Budget-constrained greedy: n_t = argmax n s.t. cumulative proportional cost sum_{i<=n} (b_{n+1}/q_{n+1}) q_i <= B_t, with proportional-share payment r_{t,i}.
**Obstruction:** The allocation maximizes a COUNT subject to a budget constraint (a knapsack-style greedy), not a welfare argmax, and the payment is a proportional share of the critical unit price rather than a Clarke pivot. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** R4: cross-paper provenance bug -- the entry's allocation_rule_latex and payment_rule_latex are byte-identical to Jin2023bara_budget's and absent from pdfs/Jiao2019auto_auction.pdf. The Jiao2019 paper does prove winner-monotonicity + critical payment (Theorem 1 + Proposition 1, for its RMA mechanism), but for a rule the entry does not record. Needs an R6 corpus re-extraction of the RMA fields.
**Diagnosed:** 2026-09-04

## Jin2023bara_budget (VCG) — R4

**Mechanism:** Identical budget-constrained greedy to Jiao2019: n_t = argmax n s.t. sum (b_{n+1}/q_{n+1}) q_i <= B_t with proportional critical-price payment; client_utility_latex is null.
**Obstruction:** Budget-knapsack allocation is out of the {argmax, top-k, weighted-welfare} family and the proportional-share payment is not a Clarke pivot; with no utility LaTeX the grid proof has no objective to check. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** R4 checked pdfs/Jin2023bara_budget.pdf: zero theorems/lemmas/proofs; BARA is a budget-allocation algorithm explicitly 'orthogonal to incentive mechanisms', the auction is recapped as background prose. No monotonicity or critical-payment result to cite.
**Diagnosed:** 2026-09-04

## Ahmed2023frimfl (VCG) — R4

**Mechanism:** Per-client indicator x_i=1 iff posted price p_i=B/r_i is under budget B; payment is a fixed posted price.
**Obstruction:** Allocation is a per-client budget-feasibility cases-threshold, not a welfare argmax, and the payment B/r_i is a posted price independent of others' reports, so no Groves pivot exists to prove. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** R4 checked the PDF: no monotonicity, critical-payment, or Myerson content; the recorded payment is a budget/proportional share, not a critical value.
**Diagnosed:** 2026-09-04

## 2404_13841 (VCG) — R4

**Mechanism:** Budget-split proportional payment B/(S(k-1)) to a threshold-index winning set; allocation LaTeX is an alpha-fairness share, not a selection rule.
**Obstruction:** Winner set is a budget-threshold cutoff k=min{k: b_k > B/(Sk)}; not argmax/top-k with fixed k, and the recorded allocation LaTeX is a share formula, so no grid-decidable allocation node exists. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** R4 checked the PDF: no monotonicity, critical-payment, or Myerson content; the recorded payment is a budget/proportional share, not a critical value.
**Diagnosed:** 2026-09-04

## Lu2021cluster_auction (VCG) — R4

**Mechanism:** Select the K_j lowest bidders among clients passing a data-size filter s_min; payment is an affine 1/(N-K+1) + ((N-K)/(N-K+1)) c_i formula.
**Obstruction:** The eligible set JL is itself defined by a min over a previously-selected set (a fixed-point/filter dependency), so the allocation is not a plain top-k over reports, and the affine payment is not a Clarke pivot. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** R4 checked pdfs/Lu2021cluster_auction.pdf: the greedy has a fixed-point eviction (provisional set -> s_min threshold -> reselect), so the winner set is not monotone in a client's own report; the payment is a BNE bidding strategy, not a critical value.
**Diagnosed:** 2026-09-04

## Kang2019contract_mobile (Contract) — R4

**Mechanism:** Mobile-device contract; routed to Track 3 (mpmath.iv branch-and-bound, delta-sound).
**Obstruction:** Track 1 does not apply. The R4 fixed_constants field removes the three numerically-declared constants from the box (mu, c_n, s_n), but zeta (effective capacitance, never given a number) and the transmission-energy sub-symbols sigma/rho_n/B/h_n (paper only fixes the composite E^com=20, not the parts) stay free. IC is 6-dim but the branch-and-bound is inconclusive over the generic positive box; IR is still 8-dim, above the cap. The verifier reports UNKNOWN honestly rather than a partial-coverage result. (Track 3: after pinning the 3 paper-declared constants (mu=1, c_n=5, s_n=20) the IC drops from 9 to 6 free vars but the interval search over the generic [0.001,100] parameter box is still inconclusive (unsupported op / budget); the IR drops from 11 to 8 free vars and remains > box-dim cap -- neither IC nor IR is decidable at delta=0.001)
**Human task:** R4 pinned the 3 paper-declared constants (mu=1, c_n=5, s_n=20) via fixed_constants, dropping the IC box from 9 to 6 free vars and the IR box from 11 to 8, but IR is still over _MAX_BOX_DIMS and IC comes back inconclusive. zeta and the transmission sub-symbols (sigma, rho_n, B, h_n) have no per-symbol numeric values in the paper -- only the composite E^com = 20 -- so they were left free (fail-closed). Needs a tighter Track 3 or a symbolic reduction (R6).
**Diagnosed:** 2026-09-04

## GPS2023afl_recruit (VCG) — R4

**Mechanism:** Selects participants 'among the lowest bids' (a reverse top-k with unspecified k) and pays p_i = b_i - C_i(t), which equals the stated client utility.
**Obstruction:** The winner count is not specified so the rule is not a fixed top-k, and the payment pays the bid minus own cost — a first-price form, not a Clarke pivot; the payment and utility LaTeX are literally identical, so the recorded model is degenerate. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** R4: payment p_i = b_i - C_i(t) is first-price (increasing in own bid) and literally identical to client_utility_latex (degenerate model); not DSIC but no source PDF to construct a rigorous counterexample; R6 corpus re-extraction or paper authors.
**Diagnosed:** 2026-09-04

## 2102_03401 (Contract) — R4

**Mechanism:** CAV data-quality contract menu {(P_m, R_m)}; utility theta_m R_m - u_3(kappa c phi^2 s-bar I + P_m t-hat).
**Obstruction:** corpus data transcription bug, not a math obstruction (Track 1: mechanism LaTeX writes the scalar unit-energy-cost u_3 as a function call u_3(...) instead of a coefficient u_3 * (...); the parser reads it as an opaque function and bails)
**Human task:** correct the mechanism IC/IR/utility LaTeX fields to write u_3 as a scalar coefficient (u_3 \cdot (...)) rather than u_3(...); confirmed from pdfs/2102.03401.pdf Eq. 21: 'u3 is the unit cost of the energy consumption'. Then Track 1 can build the obligation.
**Diagnosed:** 2026-09-04
