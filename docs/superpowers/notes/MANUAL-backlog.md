# MANUAL Backlog

One paragraph per corpus entry that no automated track in the pipeline can decide.
Each names the mechanism, the obstruction (with the track and the specific limit hit),
and the concrete human task to close it. Regenerated from corpus.json — do not hand-edit;
edit the entry's manual_diagnosis and re-run scripts/build_manual_backlog.py.

**Total: 93 MANUAL entries.** Recurring obstruction families:

- **no-screening-IC** (10): 2408_13223, 2505_02462, 2505_05842, 2605_02935, Bornstein2023realistic_incentive, Huang2024aigc, Karimireddy2022data_sharing, Li2026network, Zhang2020fedserving, Zhao2023truthful
- **vector-follower-decision** (8): 2101_05628, 2101_12428, 2502_10765, Guo2023stackelberg_industrial, Li2025split, Liu2026fedbud, Wang2022blockchain, Yu2022multi_leader_fl
- **transcendental-FOC-no-closed-form** (2): Chu2023hierarchical, Pandey2019crowd
- **opaque-function-in-utility** (10): 2102_03401, 2605_11889, 2606_18384, Cheng2022uav, Han2025paid_models, Lim2020edge_collab, Model2024trading_fl, Nguyen2025right_reward, Peng2023auction_medical, Tan2023hire
- **no-follower-IR-stated** (11): 1811_12082, 2110_12876, 2203_00270, 2404_08261, 2508_07676, Cao2025service, Chen2023multifactor_iot, Hu2020trading, Hu2022truthful_FEL, Lee2024sfl_stackelberg, Li2025iiot_drl
- **coalition-value-not-instantiable** (2): 2405_13879, 2502_08248
- **budget-constrained-greedy-allocation** (6): 2404_13841, Ahmed2023frimfl, GPS2023afl_recruit, Jiao2019auto_auction, Jin2023bara_budget, Lu2021cluster_auction
- **non-polynomial-gap** (4): Haupt2021auctions, Seo2021sdn_fl, Seo2022noniid_auction, Wei2024truthful_bandit
- **continuous-bid-space-no-discretization** (3): Cui2024auction_market, Yang2023buyers_market, Zhang2022online
- **other** (37): 2103_05866, 2308_12502, 2403_09153, 2407_02845, 2412_05636, 2502_20882, 2602_21844, Batool2022fl_mab, Deng2020fmore_auction, Ding2020contract_multidim, FLamma2025stackelberg, International_Journal_of_Intelligent_Systems_-_2024_-_Wan_-_Hierarchical_Incentive_Mechanism_for_Federated_Learning__A, Javaherian2025stackelberg_ic, Kang2019contract_mobile, Kang2019reliable_contract, Kang2022blockchain_metaverse, Khan2019edge, Le2021cellular_auction, Lim2020contract, Liu2023reverse_auction, Luo2023unbiased, Ma2023joint_pricing, Mai2022double_auction, Ng2020uav_auction_coalition, Pang2025quality, Saputra2020fl_contract, Saputra2021iov_contract, Saputra2021straggling, Wang2022motilearn_contract, Wen2025diffusion_contract, Wu2021contract_DP, Xia2026privacy_mfg, Xiang2025esr_mhfl, Xiao2020stackelberg_twostage, Yang2023async_contract, Zhang2022expost_auction, Zhang2024auction_comm

## Family: no-screening-IC

### 2408_13223 (Contract) — R3a

**Mechanism:** Nash action-choice equilibrium over {abstain, join, buy} with rewards assigned directly per platform-known type.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- Nash action-choice equilibrium over {abstain, join, buy} with rewards assigned directly per platform-known type; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

### 2505_02462 (Contract) — R3a

**Mechanism:** Graph-based reciprocal model-sharing with a single self-reported-cost truthfulness property, no discrete type set and no (effort, reward) menu.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- graph-based reciprocal model-sharing with a single self-reported-cost truthfulness property, no discrete type set and no (effort, reward) menu; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

### 2505_05842 (Contract) — R3a

**Mechanism:** Dynamic Bayesian persuasion (signal over the posterior plus a single uniform reward), governed by Bayesian Consistency/Plausibility/Benefit, not by a type-indexed menu.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- dynamic Bayesian persuasion (signal over the posterior plus a single uniform reward), governed by Bayesian Consistency/Plausibility/Benefit, not by a type-indexed menu; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

### 2605_02935 (Contract) — R3a

**Mechanism:** Blockchain smart contracts with per-role strategy-proofness against a fixed deviation set; no type space, cost function, or contract menu.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- blockchain smart contracts with per-role strategy-proofness against a fixed deviation set; no type space, cost function, or contract menu; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

### Bornstein2023realistic_incentive (Contract) — R3a

**Mechanism:** Moral hazard over a continuously self-chosen contribution m_i (Nash equilibrium condition); the paper explicitly distinguishes itself from contract theory.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- moral hazard over a continuously self-chosen contribution m_i (Nash equilibrium condition); the paper explicitly distinguishes itself from contract theory; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

### Huang2024aigc (Contract) — R3a

**Mechanism:** A single uniform unit-data price with post-hoc behavioural type regions; the paper never states incentive compatibility, screening, or a menu.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- a single uniform unit-data price with post-hoc behavioural type regions; the paper never states incentive compatibility, screening, or a menu; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

### Karimireddy2022data_sharing (Contract) — R3a

**Mechanism:** Moral hazard / continuous-action Nash with verifiable costs; the paper's own 'incentive compatibility' theorem is a no-distortion property, not self-selection.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- moral hazard / continuous-action Nash with verifiable costs; the paper's own 'incentive compatibility' theorem is a no-distortion property, not self-selection; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

### Li2026network (Contract) — R3a

**Mechanism:** Per-type closed-form payment plus a 3-action (abstain/join/buy) equilibrium, not type-i-vs-type-j screening.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- per-type closed-form payment plus a 3-action (abstain/join/buy) equilibrium, not type-i-vs-type-j screening; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

### Zhang2020fedserving (Contract) — R3a

**Mechanism:** Bayesian peer-prediction / Bayesian Truth Serum with BNE truthfulness, no discrete client type space and no self-selected menu.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- Bayesian peer-prediction / Bayesian Truth Serum with BNE truthfulness, no discrete client type space and no self-selected menu; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

### Zhao2023truthful (Contract) — R3a

**Mechanism:** Moral hazard (hidden action): one desired action assigned to every client, truthfulness proved as a Nash equilibrium over actions.
**Obstruction:** The entry's ic_screening_latex is deliberately null: the paper states no two-sided type-i-vs-type-j self-selection constraint. The R3a LLM extraction pass over the PDF text also declined (confident=false, empty fields) -- the correct fail-closed outcome. The generic linear-cost VERIFIED_TEMPLATE verdict was never a statement about this paper's mechanism. (Track 1: no adverse-selection screening IC in the paper -- moral hazard (hidden action): one desired action assigned to every client, truthfulness proved as a Nash equilibrium over actions; template does not apply)
**Human task:** Decide whether this mechanism family warrants its own verification template (Nash-equilibrium action choice, peer prediction, or Bayesian persuasion feasibility); the screening-IC template will never apply to it.
**Diagnosed:** 2026-09-03

## Family: vector-follower-decision

### 2101_05628 (Stackelberg) — R4

**Mechanism:** OSPs (leaders) announce prices; each mobile device (follower) picks an offloading strategy vector alpha_i = (alpha_{i,1},...,alpha_{i,N}) splitting its task across N OSPs.
**Obstruction:** Both best_response_latex and follower_foc_latex are null, and the follower decision is an N-dimensional simplex-constrained vector coupled through the shared congestion term D_i(alpha_i, A_{-i}). _stackelberg_check_core's single-variable d(leader_utility)/d(follower_decision) FOC cannot express the stationarity system. (Track 1: vector follower decision -- single-variable FOC reduction does not apply)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round.
**Diagnosed:** 2026-09-04

### 2101_12428 (Stackelberg) — R4

**Mechanism:** Chains post block rewards R_m; each staker n allocates a stake vector s_n = (s_n^1,...,s_n^M) across M chains subject to a budget sum_m s_n^m <= B_n.
**Obstruction:** The recorded follower_foc_latex is a budget-eliminated *difference* of two per-chain derivatives (dU/ds_n^m - dU/ds_n^M = 0 for m=1..M-1), so the M-1 conditions are coupled to each other through the eliminated component s_n^M = B_n - sum_{m<M} s_n^m. It is not a single-variable stationarity equation and the components do not decouple, so the single-variable FOC path cannot consume it. (Track 1: vector follower decision -- single-variable FOC reduction does not apply)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round.
**Diagnosed:** 2026-09-04

### 2502_10765 (Stackelberg) — R4

**Mechanism:** Provider sets unit prices p_r and p_w; each user jointly chooses rendering resources x_i^r AND bandwidth resources x_i^w.
**Obstruction:** The follower decision is two variables chosen jointly; follower_foc_latex records two separate partial-derivative equations and best_response_latex two separate maximizers. The single-variable FOC path has no way to express a joint stationarity system, and the entry's own follower_decision field flags that the verifier's pipeline cannot yet handle this. (Track 1: vector follower decision -- single-variable FOC reduction does not apply)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round.
**Diagnosed:** 2026-09-04

### Guo2023stackelberg_industrial (Stackelberg) — R4

**Mechanism:** Leader allocates reward R_n and model size sigma; each follower jointly chooses data quantity |D'_n| AND compensation S_n (FS_n = (D'_n, S_n)).
**Obstruction:** Both best_response_latex and follower_foc_latex are null (fail-closed on human review) and the follower decision is an explicit two-component joint choice inside a multi-objective bi-level program. There is no recorded stationarity condition of any kind for Track 1 to discharge. (Track 1: vector follower decision -- single-variable FOC reduction does not apply)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round.
**Diagnosed:** 2026-09-04

### Li2025split (Stackelberg) — R4

**Mechanism:** SFL tenants post price incentives P_i; each device j chooses a participation vector {q_{i,j}}_{i in [1,M]} across all M tenants simultaneously.
**Obstruction:** best_response_latex is a bare argmax placeholder (q*_{i,j} = argmax lambda_j) with no algebraic content, and follower_foc_latex is a full KKT system: M stationarity equations plus two complementary-slackness conditions, two primal feasibility conditions and two dual feasibility conditions for the simplex constraints phi_j^{(1)}, phi_j^{(2)}. That is a constrained multi-variable system, not a single-variable FOC. (Track 1: vector follower decision -- single-variable FOC reduction does not apply)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round.
**Diagnosed:** 2026-09-04

### Liu2026fedbud (Stackelberg) — R4

**Mechanism:** Server pays R^t to edge nodes; each node k jointly chooses data volume B_k^t AND privacy/noise budget epsilon_k^t.
**Obstruction:** The follower decision is two variables chosen jointly and follower_foc_latex is null (fail-closed). best_response_latex gives two separate maximizers but with no recorded stationarity conditions to differentiate against, so there is nothing for a d(leader_utility)/d(follower_decision) check to consume, and the single-variable path could not express the joint system in any case. (Track 1: vector follower decision -- single-variable FOC reduction does not apply)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round.
**Diagnosed:** 2026-09-04

### Wang2022blockchain (Stackelberg) — R4

**Mechanism:** Leader sets unit prices p_ti and p_mi; each miner i jointly chooses CPU cycles per second for training q_ti AND for mining q_mi.
**Obstruction:** Two obstructions compound. (1) The follower decision is two variables chosen jointly, while follower_foc_latex records only the single partial dU_i/dq_ti = p_ti - 2 rho_i q_ti = 0 -- there is no recorded condition for q_mi. (2) That FOC is inconsistent with the recorded utility (U_i has revenue mu_i p_ti / q_ti and cost rho_i mu_i q_ti^2, so the true derivative is strictly negative and the optimum is a corner, not an interior stationary point), and the stored best_response q_ti* = (p_ti/rho_i)^{1/3} is not the root of the recorded FOC either. Substituting it into a d(leader_utility)/d(follower_decision) check would certify a stationarity claim the entry's own algebra contradicts. (Track 1: vector follower decision -- single-variable FOC reduction does not apply; the stored best response is additionally not an interior FOC solution)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round. Also: the paper's own Sec 3.1.2 prints dU/dq < 0 for both variables then miscalls the objective concave; the real stationarity is a Lagrangian on the time constraint (Eqs. 30-31) matching NEITHER the stored follower_foc_latex NOR best_response_latex (corner solution) -- needs a full PDF re-derivation in R6.
**Diagnosed:** 2026-09-04

### Yu2022multi_leader_fl (Stackelberg) — R4

**Mechanism:** Multiple task leaders post reward rates p_i; each data owner j chooses a task-accuracy vector {epsilon_j^i} for tasks i = 1..K simultaneously under a shared resource budget.
**Obstruction:** Three compounding obstructions. The follower chooses a K-component vector coupled by the resource budget sum_i L_j^i <= tau_j^max; best_response_latex is a three-branch piecewise form whose active-constraint branch carries a Lagrange multiplier lambda_j found only by bisection search (Algorithm 1, Eq. 27); and both branch values bar-epsilon and hat-epsilon are defined implicitly as roots of the transcendental relation log(e^{1/eps} eps) = const, which the recorded follower_foc_latex also is. None of the three is expressible as a single-variable closed-form stationarity condition. (Track 1: vector follower decision -- single-variable FOC reduction does not apply)
**Human task:** R4 landed the _stackelberg_check_core vector-decision checker (+ transcribed the follower FOC system for entries where the paper prints one in closed form), but the checker is unreachable: the sibling-name guard at track1_z3.py:1610-1620 returns None before the vector branch, and _lx_parse collapses superscript components (x_i^r -> x_{i}**r). Unblocked by an R6 Stackelberg-parser round.
**Diagnosed:** 2026-09-04

## Family: transcendental-FOC-no-closed-form

### Chu2023hierarchical (Stackelberg) — R3b

**Mechanism:** Cloud server sets rewards to edge servers; each edge server chooses its number of local aggregations K_l.
**Obstruction:** best_response_latex is deliberately null: the paper states on p.21, immediately after the recorded FOC (Eq. 31), that there is 'a lack of the closed-form solution for the optimal edge aggregation strategies of the edge server l', and solves the equilibrium numerically by variational inequality / iterative updates instead. The recorded follower_foc_latex mixes Z_l = sqrt(A_l - F_l K_l / B_l) inside rational terms of degree 2 in Z_l and has no closed-form root in K_l, so there is no equilibrium point for the FOC check to substitute and verify. (Track 1: follower FOC is transcendental with no closed-form root (paper states this explicitly) -- Track 1 cannot solve the stationarity equation)
**Human task:** decide whether a numerically-certified equilibrium (interval enclosure of the FOC root) is acceptable evidence for this corpus, and if so add a numeric-root Track to the Stackelberg checker.
**Diagnosed:** 2026-09-03

### Pandey2019crowd (Stackelberg) — R3b

**Mechanism:** Server posts a uniform reward r; each client k chooses a local accuracy level theta_k.
**Obstruction:** follower_foc_latex is 1/theta_k - log(1/theta_k) = (r + nu_k T_k)/((1-nu_k) gamma_k) - 1, a transcendental equation in theta_k with no closed-form root (its solution is a Lambert-W branch the paper never writes down). best_response_latex is correspondingly implicit: theta_k*(r) = min{ hat-theta_k(r) | g_k(r) = log(e^{1/hat-theta_k} hat-theta_k), theta_th } -- it defines hat-theta_k only as 'the value satisfying' the transcendental relation, then clips at theta_th. Nothing algebraic can be substituted into a d(leader_utility)/d(follower_decision) check. (Track 1: follower FOC is transcendental (1/theta - log(1/theta) = const) with no closed-form root, and the best response is a min-clipped implicit solution -- Track 1 cannot solve the stationarity equation)
**Human task:** record the Lambert-W closed form if the branch can be pinned down soundly, and add transcendental/special-function support plus the min-clip to the checker.
**Diagnosed:** 2026-09-03

## Family: opaque-function-in-utility

### 2102_03401 (Contract) — R4

**Mechanism:** CAV data-quality contract menu {(P_m, R_m)}; utility theta_m R_m - u_3(kappa c phi^2 s-bar I + P_m t-hat).
**Obstruction:** corpus data transcription bug, not a math obstruction (Track 1: mechanism LaTeX writes the scalar unit-energy-cost u_3 as a function call u_3(...) instead of a coefficient u_3 * (...); the parser reads it as an opaque function and bails)
**Human task:** correct the mechanism IC/IR/utility LaTeX fields to write u_3 as a scalar coefficient (u_3 \cdot (...)) rather than u_3(...); confirmed from pdfs/2102.03401.pdf Eq. 21: 'u3 is the unit cost of the energy consumption'. Then Track 1 can build the obligation.
**Diagnosed:** 2026-09-04

### 2605_11889 (Shapley) — R5

**Mechanism:** Bayesian Shapley data valuation: phi_i is the exact Shapley value of a log-likelihood characteristic function over data subsets.
**Obstruction:** Tier A confirms the formula is the exact Shapley value, but v(S) is a Bayesian log-likelihood over a model+dataset the paper never instantiates numerically, so Tier B (core/IR) has nothing to enumerate over. (Track 5: transcendental / opaque characteristic function (Bayesian log-likelihood v(D_C) = log p(T=T*|D_C) - log p(T=T*|∅)); no numeric instance in the paper)
**Human task:** instantiate a concrete Bayesian model + validation set and compute v(S) for all S, or prove core/IR analytically from the log-likelihood's supermodularity.
**Diagnosed:** 2026-09-05

### 2606_18384 (Shapley) — R5

**Mechanism:** One-round reconstruction payment phi_j^OR approximating the Shapley value of a trained-model-accuracy characteristic function U(M_Sub).
**Obstruction:** Tier A rejects the formula: the 1/binom(|C|-1,|Sub|) weighting and the K factor are not the exact Shapley weights. Even granting the approximation, v(Sub)=U(M_Sub^(R)) is a trained-model accuracy — not symbolically or grid-computable. (Track 5: stated payment is a K-normalized one-round-reconstruction *approximation* of Shapley, not the exact value; value U(M_Sub) is opaque model accuracy)
**Human task:** bound the approximation error |phi_j^OR - phi_j^Shapley| from Algorithm 1, or run the paper's reconstruction to get numeric v(Sub) and verify core/IR empirically.
**Diagnosed:** 2026-09-05

### Cheng2022uav (VCG) — R-shape-cleanup

**Mechanism:** Three-sided matching: allocation X* = argmax_X F(x_{l,m,n}) over a 3-index binary assignment (buyer l, data-seller m, UAV-seller n); payment P_{i,k}^f = F(x*) - F_{\setminus(i,k)}(y^{t*}) + J_{l,(i,k)}, a Clarke-pivot-shaped payment on the opaque objective F.
**Obstruction:** F(.) is never given a closed algebraic form anywhere in the corpus's mechanism fields -- it is referenced only by name, same for the counterfactual F_{\setminus(i,k)}. No track's parser can substitute a numeric/symbolic value for an opaque function reference, and the allocation is additionally a 3-index multi-winner assignment (well beyond the 2-index bipartite case already out of reach). (Track 1: VCG: opaque coalition-value function F(.) with no closed form; 3-index multi-winner allocation (data-seller x UAV-seller x buyer))
**Human task:** Transcribe F(.)'s actual formula from the source paper's welfare objective (recorded separately as objective_latex: max sum_l sum_m sum_n x_{l,m,n}(v_{l,(m,n)} - q_{m,l} - s_{n,(m,l)})) into allocation_rule_latex/payment_rule_latex so a future formalizer pass has a concrete function to work with.
**Diagnosed:** 2026-09-05

### Han2025paid_models (Contract) — R4

**Mechanism:** Paid-model contract with private per-unit collection cost c_i; utility E[v(r_i)] - c_i m_i.
**Obstruction:** The IC parses (type subscript i, contract subscript j, soundness gate passes) but E[v(r_i)] is an expectation of an undefined valuation function. _sp_to_z3 raises 'unsupported SymPy node v'. Track 4's Bayesian path cannot help either, because v has no algebraic form to integrate. (Track 1: utility contains the undefined opaque valuation function v(.) inside an expectation E[v(r_i)] -- Z3 encoding rejects it ('unsupported SymPy node v'))
**Human task:** R4: no source PDF exists in pdfs/ and the entry's arxiv_id/source/notes are all null -- the opaque valuation v(.) inside E[v(r_i)] cannot be transcribed.
**Diagnosed:** 2026-09-04

### Lim2020edge_collab (VCG) — R2

**Mechanism:** No allocation or payment rule recorded in the corpus entry; the paper's edge-collaboration mechanism is described only in prose.
**Obstruction:** Both allocation_rule_latex and payment_rule_latex are null, so there is no closed-form rule to classify or discharge on a grid. (Track 1: RL-policy or opaque-algorithm allocation, not a closed-form rule)
**Human task:** Re-extract the allocation and payment rules from the paper PDF before any solver attempt.
**Diagnosed:** 2026-09-03

### Model2024trading_fl (VCG) — R2

**Mechanism:** Allocation a_t = b_t * pi(s_t; theta) is the output of a learned RL policy pi; payment p_t = Delta G_t * b_t / k_{i+1}.
**Obstruction:** The allocation is a neural RL policy with no closed form, so it cannot be classified as argmax/top-k/weighted-welfare and admits no finite-grid encoding. (Track 1: RL-policy or opaque-algorithm allocation, not a closed-form rule)
**Human task:** Determine whether the trained policy's induced allocation is provably monotone, or bound truthfulness empirically; formal Track-1 proof is out of reach.
**Diagnosed:** 2026-09-03

### Nguyen2025right_reward (Contract) — R4

**Mechanism:** Joint capability/joining-time contract phi_k = {e_k, t_k, r_k} with multidimensional type (theta_k, t_k).
**Obstruction:** The IC parses via utility-call expansion (type subscript k, contract subscript k-prime, soundness gate passes), but the staleness weight h(t_k) is an undefined function and _sp_to_z3 raises 'unsupported SymPy node h'. The type is also genuinely two-dimensional, which the single-type-subscript machinery does not model even once h is supplied. (Track 1: utility contains the undefined opaque staleness function h(t_k) -- Z3 encoding rejects it ('unsupported SymPy node h'))
**Human task:** R4 checked pdfs/Nguyen2025right_reward.pdf: h(t_k) is defined (Eq. 2) but 2-branch piecewise (1 + vartheta ln(2 t_k) if t_k in CLPs, else 1); opaque_function_forms maps one name to one form and cannot represent a piecewise function.
**Diagnosed:** 2026-09-04

### Peng2023auction_medical (VCG) — R2

**Mechanism:** No allocation or payment rule recorded in the corpus entry.
**Obstruction:** Both allocation_rule_latex and payment_rule_latex are null, so there is no rule to classify. (Track 1: RL-policy or opaque-algorithm allocation, not a closed-form rule)
**Human task:** Re-extract the allocation and payment rules from the paper PDF before any solver attempt.
**Diagnosed:** 2026-09-03

### Tan2023hire (VCG) — R2

**Mechanism:** Mode-switching selection: lowest-bid participants when a queue Q_f(t) <= 0, highest-reputation participants when Q_f(t) > 0; payment is first-price sum b_n P(n,t).
**Obstruction:** The allocation switches objective based on a time-varying queue state external to the report profile, so it is not a fixed argmax; and the payment is first-price (pays the bid), which is not a Clarke pivot. (Track 1: RL-policy or opaque-algorithm allocation, not a closed-form rule)
**Human task:** Fix the queue state and check whether each branch is separately monotone; a first-price payment cannot be DSIC, so a counterexample search may be the right target.
**Diagnosed:** 2026-09-03

## Family: no-follower-IR-stated

### 1811_12082 (Stackelberg) — R7

**Mechanism:** Leader (data requester) sets rewards/prices; follower (model owner) chooses computing/data resource contribution s_i^d over a box domain.
**Obstruction:** Batch-C review left ir_follower_latex null (fail-closed) -- the only constraint on s_i^d is the box domain s_i^d in [0, s_i^{d,u}] (Sec. III.1), a feasibility bound, not a U_follower >= 0 / outside-option IR. (Track 1: Stackelberg: no follower IR / participation constraint stated in the paper)
**Human task:** Re-read Sec. III.1-III.2 of 1811_12082 for any implicit participation floor tied to the outside option; if none exists in the paper, this stays MANUAL -- Track 1's IR check has no statement to encode.
**Diagnosed:** 2026-09-06

### 2110_12876 (Stackelberg) — R7

**Mechanism:** Leader (parking-lot operator) sets reward r_j; follower (vehicle) chooses participation rho_i^j subject to parking-capacity and budget caps.
**Obstruction:** Batch-C review left ir_follower_latex null (fail-closed) -- the only stated constraints are the parking-capacity cap (sum_i rho_i^j <= n^j) and the leader-side budget cap r_j^max <= g_j; no U_i >= 0 or outside option appears for the vehicle follower. (Track 1: Stackelberg: no follower IR / participation constraint stated in the paper)
**Human task:** Re-read the vehicle (follower) problem statement for any implicit U_i >= 0 condition; if none exists, transcribing one would fabricate a constraint the paper never states, so this stays MANUAL.
**Diagnosed:** 2026-09-06

### 2203_00270 (Stackelberg) — R7

**Mechanism:** Follower's FOC/best-response derived case-by-case (tp_i^k<0 / >0 branches) from the P3/P5 problem in Appendix A/B; leader sets prices p_b^k, p_s^k.
**Obstruction:** Batch-C review transcribed follower_foc_latex/best_response_latex from Appendix A/B (verified against pp.12-13 image) but the fully optimal e_i^{k,*} requires selecting among {e_{i,1}^{k,*}, e_{i,2}^{k,*}, RP_i^k-D_i^k} via a 3-scenario comparison (Fig. 12/App. B) that is not itself a closed-form expression; ir_follower_latex left null fail-closed (no IR statement in the paper). (Track 1: Stackelberg: no follower IR / participation constraint; case-selection logic is qualitative, not closed-form)
**Human task:** Formalize the Fig. 12/Appendix B case-selection (relative ordering of p_s^k, p_b^k, delta_i^k) as a piecewise closed form usable by Track 1, or confirm no IR constraint exists so this stays MANUAL.
**Diagnosed:** 2026-09-06

### 2404_08261 (Stackelberg) — R7

**Mechanism:** Leader (server) sets a privacy-budget-linked incentive; follower (client) chooses privacy budget epsilon_i maximizing its own utility.
**Obstruction:** Batch-C review left ir_follower_latex null (fail-closed) -- no 's.t.' or constraint block appears for the follower's privacy-budget optimization problem beyond the bare utility definition itself; no U_i >= 0 or outside-option condition is stated anywhere. (Track 1: Stackelberg: no follower IR / participation constraint stated in the paper)
**Human task:** Re-read the client's privacy-budget optimization problem statement in full (including any domain restrictions on epsilon_i) for an implicit participation floor; if none exists, this stays MANUAL.
**Diagnosed:** 2026-09-06

### 2508_07676 (Stackelberg) — R7

**Mechanism:** Leader (server) sets an incentive schedule; follower (client) chooses contribution rate rho_i(t) maximizing utility U_i-hat (Eq. 5).
**Obstruction:** Batch D review left follower_foc_latex null fail-closed -- the paper's Proof Sketch of Theorem 3 only narrates 'setting the first-order derivative to zero' and never prints the FOC itself, even though a reconstructed derivative does reproduce the paper's own Eq. (6) (best_response_latex). ir_follower_latex also left null: the paper critiques prior work's 'unconditional participation' assumption but imposes no formal IR constraint of its own. (Track 1: Stackelberg: no follower IR; follower FOC only described narratively, never printed as a numbered equation)
**Human task:** Confirm in the Proof Sketch of Theorem 3 whether the FOC is ever printed as a standalone numbered equation anywhere else in the paper (e.g. an appendix); if truly absent, this entry stays MANUAL since Track 1 needs a printed FOC, not a reconstructed one.
**Diagnosed:** 2026-09-06

### Cao2025service (Stackelberg) — R7

**Mechanism:** Leader = Task Publisher (TP); follower = Local Model Owners (LMOs) competing via Eq. 9's unconstrained optimization problem.
**Obstruction:** Batch D review left ir_follower_latex null fail-closed -- the LMO's problem (Eq. 9) has no constraints at all; Definition 1 is a Nash-equilibrium condition among LMOs, not an IR statement. The paper's 'base participation reward' Rbase (Eq. 6) incentivizes the Worker (a different, lower-tier actor who collects data for an LMO), not the LMO follower itself. (Track 1: Stackelberg: no follower IR / participation constraint stated for the LMO)
**Human task:** Confirm no IR statement exists anywhere else in the paper for the LMO (the follower already modeled in this entry, leader=TP); if Rbase truly only applies to the Worker sub-actor, this entry stays MANUAL as there is no follower-level IR to transcribe.
**Diagnosed:** 2026-09-06

### Chen2023multifactor_iot (Stackelberg) — R7

**Mechanism:** Leader sets reward Ii^t; follower (data owner) chooses effort/accuracy contribution Acci^t under a reputation-linked reward.
**Obstruction:** Batch D review left ir_follower_latex null fail-closed -- no constraint block or utility>=0 condition appears anywhere for the data owner's optimization problem. Theorem 2 (Ii^t monotonic in reputation Ri^t and accuracy Acci^t) is a fairness result, and Definition 7 (Optimal Equilibrium) is the standard best-response equilibrium definition -- neither is an IR statement. (Track 1: Stackelberg: no follower IR / participation constraint stated for the data owner)
**Human task:** Re-scan the data owner's optimization problem statement and any footnotes/remarks for an implicit non-negativity condition; absent one, this stays MANUAL.
**Diagnosed:** 2026-09-06

### Hu2020trading (Stackelberg) — R7

**Mechanism:** Leader sets price beta_i; follower (user i) chooses contribution rho_i maximizing utility, with a corner solution rho_i = -infty when unprofitable (Eq. 15).
**Obstruction:** Batch E review left ir_follower_latex null fail-closed -- the paper never states U_i >= 0 formally. It only notes informally, right after Eq. (15), that a user sets rho_i = -infty to avoid a deficit when the best strategy beta_i(rho_{-i}) is non-positive -- a behavioral description of the corner solution already embedded in best_response_latex, not a separately stated IR constraint. (Track 1: Stackelberg: no follower IR / participation constraint stated as a formal inequality)
**Human task:** Confirm whether the corner-solution description near Eq. (15) can be formalized as an equivalent IR inequality without adding content beyond what the paper states; if it cannot be done without fabricating a constraint the paper doesn't write, this stays MANUAL.
**Diagnosed:** 2026-09-06

### Hu2022truthful_FEL (Stackelberg) — R7

**Mechanism:** Leader/device-side Stackelberg incentive; follower's utility U_d (integrand H_d, Eq. 3) yields an optimal s* via an Euler-Lagrange argument analogous to r*(s).
**Obstruction:** Batch E review left follower_foc_latex null fail-closed -- the paper states only that s* is derived 'using the similar method' as r*(s) and reports the resulting second-order condition d^2Hd/ds^2 = -A_eTheta/rho < 0 (verbatim) plus the resulting s* (already recorded as best_response_latex), but never prints the FOC itself. ir_follower_latex also left null: Section IV.D 'Truthfulness Analysis' proves incentive-compatibility only, not U_d >= 0. (Track 1: Stackelberg: follower FOC never printed as a numbered equation; no follower IR/participation constraint stated)
**Human task:** Check Section IV or any appendix for a printed first-order condition for s* (not just the stated second-order condition); if absent, this stays MANUAL since Track 1 needs a transcribed FOC, not a reconstruction.
**Diagnosed:** 2026-09-06

### Lee2024sfl_stackelberg (Stackelberg) — R7

**Mechanism:** Leader (server) sets baseline S; follower (client n) chooses decision d_n subject only to the box constraint 0 <= d_n <= D_n (Problem 13).
**Obstruction:** Batch E review left ir_follower_latex null fail-closed -- no formal U_n >= 0 constraint appears in the game formulation; the only follower constraint is the box bound on d_n. The paper's baseline constant S = 10^6 (Section V, footnote 5) is set purely as a plotting convenience 'to ensure U_n is greater than zero' when computing the Price-of-Anarchy ratio (Eq. 28) -- an experimental/numerical artifact, not a declared mechanism-design IR constraint. (Track 1: Stackelberg: no follower IR / participation constraint stated in the game formulation)
**Human task:** Confirm the footnote-5 baseline S is never promoted to a formal constraint anywhere in the main game formulation (Problem 13 or surrounding text); if it stays purely numerical, this entry remains MANUAL.
**Diagnosed:** 2026-09-06

### Li2025iiot_drl (Stackelberg) — R7

**Mechanism:** Leader sets reward; follower (IIoT node i) chooses update cycle theta_i subject only to the feasibility bound theta_i >= theta_i^min (Problem P1, Eq. 11).
**Obstruction:** Batch E review left ir_follower_latex null fail-closed -- Problem P1 imposes only the lower-bound feasibility constraint theta_i >= theta_i^min on the update-cycle decision variable, not a utility-based U_i >= 0 condition; no IR/participation constraint appears anywhere else in the paper. (Track 1: Stackelberg: no follower IR / participation constraint stated in the paper)
**Human task:** Re-check any DRL-training-loop description (Section on the DRL agent) for an implicit participation/dropout rule that could be formalized as IR; absent that, this entry stays MANUAL.
**Diagnosed:** 2026-09-06

## Family: coalition-value-not-instantiable

### 2405_13879 (Shapley) — R5

**Mechanism:** PFL/FACT — a penalty-based free-riding truthfulness mechanism (free-riding penalty P_fr Eq 4, competition penalty P_ct Eq 10), per-agent local/federated loss.
**Obstruction:** The paper never defines v(S) over agent subsets and never uses the Shapley value; the Shapley category tag is wrong. No coalition track applies. (Track 5: mis-categorized: no coalition characteristic function and no Shapley value anywhere in the paper)
**Human task:** re-categorize this entry as Contract/penalty-mechanism and route it through the R3 Contract path, or confirm it is out-of-scope (no verifiable-tier incentive claim).
**Diagnosed:** 2026-09-05

### 2502_08248 (Shapley) — R5

**Mechanism:** Max-flow-based Shapley value: phi_i is the exact Shapley value of a network max-flow characteristic function v(S)=F(c).
**Obstruction:** Tier A confirms the standard Shapley formula, but the paper states v(S)=F(c) abstractly with no numeric capacity network, so Tier B cannot enumerate. (Track 5: no concrete numeric max-flow instance in the paper)
**Human task:** transcribe or construct a concrete capacity network from the paper's model, compute F(S) for all S<=3, verify core/IR.
**Diagnosed:** 2026-09-05

## Family: budget-constrained-greedy-allocation

### 2404_13841 (VCG) — R4

**Mechanism:** Budget-split proportional payment B/(S(k-1)) to a threshold-index winning set; allocation LaTeX is an alpha-fairness share, not a selection rule.
**Obstruction:** Winner set is a budget-threshold cutoff k=min{k: b_k > B/(Sk)}; not argmax/top-k with fixed k, and the recorded allocation LaTeX is a share formula, so no grid-decidable allocation node exists. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** R4 checked the PDF: no monotonicity, critical-payment, or Myerson content; the recorded payment is a budget/proportional share, not a critical value.
**Diagnosed:** 2026-09-04

### Ahmed2023frimfl (VCG) — R4

**Mechanism:** Per-client indicator x_i=1 iff posted price p_i=B/r_i is under budget B; payment is a fixed posted price.
**Obstruction:** Allocation is a per-client budget-feasibility cases-threshold, not a welfare argmax, and the payment B/r_i is a posted price independent of others' reports, so no Groves pivot exists to prove. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** R4 checked the PDF: no monotonicity, critical-payment, or Myerson content; the recorded payment is a budget/proportional share, not a critical value.
**Diagnosed:** 2026-09-04

### GPS2023afl_recruit (VCG) — R4

**Mechanism:** Selects participants 'among the lowest bids' (a reverse top-k with unspecified k) and pays p_i = b_i - C_i(t), which equals the stated client utility.
**Obstruction:** The winner count is not specified so the rule is not a fixed top-k, and the payment pays the bid minus own cost — a first-price form, not a Clarke pivot; the payment and utility LaTeX are literally identical, so the recorded model is degenerate. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** R4: payment p_i = b_i - C_i(t) is first-price (increasing in own bid) and literally identical to client_utility_latex (degenerate model); not DSIC but no source PDF to construct a rigorous counterexample; R6 corpus re-extraction or paper authors.
**Diagnosed:** 2026-09-04

### Jiao2019auto_auction (VCG) — R4

**Mechanism:** Budget-constrained greedy: n_t = argmax n s.t. cumulative proportional cost sum_{i<=n} (b_{n+1}/q_{n+1}) q_i <= B_t, with proportional-share payment r_{t,i}.
**Obstruction:** The allocation maximizes a COUNT subject to a budget constraint (a knapsack-style greedy), not a welfare argmax, and the payment is a proportional share of the critical unit price rather than a Clarke pivot. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** R4: cross-paper provenance bug -- the entry's allocation_rule_latex and payment_rule_latex are byte-identical to Jin2023bara_budget's and absent from pdfs/Jiao2019auto_auction.pdf. The Jiao2019 paper does prove winner-monotonicity + critical payment (Theorem 1 + Proposition 1, for its RMA mechanism), but for a rule the entry does not record. Needs an R6 corpus re-extraction of the RMA fields.
**Diagnosed:** 2026-09-04

### Jin2023bara_budget (VCG) — R4

**Mechanism:** Identical budget-constrained greedy to Jiao2019: n_t = argmax n s.t. sum (b_{n+1}/q_{n+1}) q_i <= B_t with proportional critical-price payment; client_utility_latex is null.
**Obstruction:** Budget-knapsack allocation is out of the {argmax, top-k, weighted-welfare} family and the proportional-share payment is not a Clarke pivot; with no utility LaTeX the grid proof has no objective to check. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** R4 checked pdfs/Jin2023bara_budget.pdf: zero theorems/lemmas/proofs; BARA is a budget-allocation algorithm explicitly 'orthogonal to incentive mechanisms', the auction is recapped as background prose. No monotonicity or critical-payment result to cite.
**Diagnosed:** 2026-09-04

### Lu2021cluster_auction (VCG) — R4

**Mechanism:** Select the K_j lowest bidders among clients passing a data-size filter s_min; payment is an affine 1/(N-K+1) + ((N-K)/(N-K+1)) c_i formula.
**Obstruction:** The eligible set JL is itself defined by a min over a previously-selected set (a fixed-point/filter dependency), so the allocation is not a plain top-k over reports, and the affine payment is not a Clarke pivot. (Track 1: budget-constrained greedy allocation not in the {argmax, top-k, weighted-welfare} family)
**Human task:** R4 checked pdfs/Lu2021cluster_auction.pdf: the greedy has a fixed-point eviction (provisional set -> s_min threshold -> reselect), so the winner set is not monotone in a client's own report; the payment is a BNE bidding strategy, not a critical value.
**Diagnosed:** 2026-09-04

## Family: non-polynomial-gap

### Haupt2021auctions (VCG) — R2

**Mechanism:** Score-comparison allocation w_i chosen by pairwise comparison b_i(s-hat - s_i) against a permuted rival, with a Punish() term in the payment.
**Obstruction:** The payment contains an opaque Punish(s_j - s_i) aggregate and the allocation is a pairwise-comparison cases rule over a permutation pi(i), which is neither argmax nor top-k and not linearizable on a finite grid. (Track 1: non-polynomial gap Z3 cannot linearize)
**Human task:** Define Punish() concretely and determine whether the pairwise-comparison allocation reduces to an argmax over a scoring function.
**Diagnosed:** 2026-09-03

### Seo2021sdn_fl (VCG) — R2

**Mechanism:** Winner score R_win = sum alpha_i e_ni - p_n with an exponential payment zeta * e^{-(1-Q_m(m))} for winners.
**Obstruction:** The payment is an exponential of the quality score; Z3 cannot linearize e^{-(1-Q)} over a real grid, and the exponential payment is not a Clarke pivot in any case. (Track 1: non-polynomial gap Z3 cannot linearize)
**Human task:** Discretize Q_m to a fixed lookup table of rational payment values, or prove truthfulness analytically via monotonicity of the score.
**Diagnosed:** 2026-09-03

### Seo2022noniid_auction (VCG) — R2

**Mechanism:** Winner score beta_1 U_D(e_n) - p_n with exponential winner payment zeta * e^{-(1-U_{D_k})}.
**Obstruction:** Same exponential-payment obstruction as Seo2021: the payment is a transcendental function of the data-utility score, which Z3 cannot linearize, and it is not a Groves pivot. (Track 1: non-polynomial gap Z3 cannot linearize)
**Human task:** Tabulate the exponential payment over a finite quality grid, or prove monotonicity analytically.
**Diagnosed:** 2026-09-03

### Wei2024truthful_bandit (VCG) — R2

**Mechanism:** Combinatorial subset selection S_t = argmax over 2^S of g_t(S) = log det(V_g,t(S)); payment is the critical cost c_{i,t}(M, D_{-i,t}).
**Obstruction:** The objective is a log-determinant over subsets: both the exponential subset space and the non-polynomial log-det make it impossible to encode as a grid-decidable argmax over per-client scores. (Track 1: non-polynomial gap Z3 cannot linearize)
**Human task:** Prove submodularity of log-det and use the greedy-approximation truthfulness argument analytically; the exact combinatorial argmax is out of solver reach.
**Diagnosed:** 2026-09-03

## Family: continuous-bid-space-no-discretization

### Cui2024auction_market (VCG) — R2

**Mechanism:** Allocation argmax_i b_{t,i} over reported bids; payment p_{i,j} = b_{t,j} * Delta G_{t,i}, a bid times a marginal model-gain term.
**Obstruction:** The payment multiplies another agent's bid by a continuous marginal-gain quantity Delta G_{t,i} produced by model training; it is a first-price-style product, not a Clarke pivot, and Delta G has no valid finite discretization tied to the reports. (Track 1: continuous bid space with no valid discretization)
**Human task:** Determine whether Delta G_{t,i} is the second-price critical value in disguise; if not, the mechanism is not Groves and needs its own truthfulness proof.
**Diagnosed:** 2026-09-03

### Yang2023buyers_market (VCG) — R2

**Mechanism:** Continuous quantity contract q_i* = lambda/(2(1+delta theta_i)) with reward R_i* = lambda^2/(2(1+delta theta_i)^2) as a function of reported efficiency theta_i.
**Obstruction:** This is a continuous screening/contract menu over theta_i in [0,1], not an auction allocation; the reward is a nonlinear rational function of the report with no finite grid that preserves the incentive constraints. (Track 1: continuous bid space with no valid discretization)
**Human task:** Verify the contract's incentive compatibility by the first-order/envelope condition analytically rather than on a grid.
**Diagnosed:** 2026-09-03

### Zhang2022online (VCG) — R2

**Mechanism:** Threshold acceptance x_i = 1 iff b_i <= rho*, payment min(rho*, b_i); utility is time-discounted p_i - c_i (T-t+1).
**Obstruction:** The threshold rho* is set online from an unbounded arrival stream and the utility scales with the remaining horizon (T-t+1), so a single-round finite grid cannot represent the mechanism's incentive structure. (Track 1: continuous bid space with no valid discretization)
**Human task:** Fix the horizon and threshold to prove per-round truthfulness, then argue the online composition separately.
**Diagnosed:** 2026-09-03

## Family: other

### 2103_05866 (Stackelberg) — R3b

**Mechanism:** A three-stage game: the protocol designer sets fee-per-byte and a waiting-tax rate vector (Stage I), users choose transaction generation rates (Stage II), and miners choose which transactions to include (Stage III).
**Obstruction:** The entry is explicitly a THREE-STAGE Stackelberg game and the recorded follower_decision ('transaction generation rates and transaction selection') conflates two distinct player layers with different equilibrium concepts. best_response_latex is a prose note recording that the Stage-III miner NE is a discrete argmin over a queue set and the Stage-II user equilibrium is a multi-branch piecewise closed form built from M/M/1 auxiliary functions that was judged too OCR-risky to transcribe; follower_foc_latex is null. (Track 1: >2-stage / multi-layer game -- 2-player leader-follower FOC model does not apply)
**Human task:** split the entry into its two follower layers with separate equilibrium statements, transcribe the Stage-II piecewise equilibrium from Eqs. 16-19, and give the checker a multi-stage backward-induction model.
**Diagnosed:** 2026-09-03

### 2308_12502 (Contract) — R3a

**Mechanism:** Multidimensional-type (theta_j, xi_j) privacy/training contract menu {(d_j, r_j^L)}.
**Obstruction:** Two independent obstructions. (1) The entry's own notes record that kappa_j is itself a sum over OTHER agents' contract terms -- a population coupling the verifier's single-agent type-i-vs-type-j substitution cannot express. (2) Even ignoring that, r_j^L reads as r_j raised to a symbolic exponent L and _sp_to_z3 raises 'unsupported exponent L'; L is a layer label, not a power. (Track 1: population-coupled cost term (kappa_j sums over other agents' contracts) -- single-agent substitution cannot represent it; additionally r_j^L carries a symbolic superscript Z3 rejects as an exponent)
**Human task:** Re-transcribe r_j^L with the layer label distinguished from an exponent, and decide whether a population-coupled cost admits any single-agent encoding; if not, this needs a multi-agent equilibrium track.
**Diagnosed:** 2026-09-03

### 2403_09153 (Contract) — R7

**Mechanism:** Contract-theoretic FL incentive design; principal offers a menu of contracts to agents of private cost/type.
**Obstruction:** The 2026-07-18 sanitization pass removed 'single-crossing (Spence-Mirrlees)' from key_assumptions because it matched the extraction-prompt's verbatim example rather than being independently corroborated by this entry's own formal fields, and removed 'quadratic cost' as contradicted by the entry's own math -- Track 1's IC/IR check needs a confirmed single-crossing assumption to run. (Track 1: Contract: key_assumptions list was sanitized (prompt-anchoring contamination) and single-crossing (Spence-Mirrlees) removed as unverified)
**Human task:** Re-read the paper's own statement of the contract-design problem to confirm (or refute) single-crossing directly from its constraints/cost function, then re-add it to key_assumptions only if independently verified against the PDF text (not the extraction-prompt template).
**Diagnosed:** 2026-09-06

### 2407_02845 (Contract) — R4

**Mechanism:** FedPot defence-data-quality contract menu {pi_m = (V_m, R_m)}; utility ln(theta_m R_m) - C_m.
**Obstruction:** The IC/IR parse and the soundness gate passes, but the log-utility encoding requires the argument theta_m R_m to be provably positive before _sp_to_z3 will admit it. The entry declares no positivity domain for theta_m or R_m, so the encoding raises and Track 1 yields nothing; the recorded verdict is the generic template only. (Track 1: log(theta_m R_m) argument sign not established -- Z3 encoding rejects the transcendental ('log argument sign not established'))
**Human task:** R4 checked pdfs/2407.02845.pdf: admitting log(theta_m R_m) needs theta_m R_m >= 1, which the paper never states (only C5: R_m > 0, a type ordering theta_1 <= ... <= theta_M, and a budget cap). Genuine ceiling absent a domain lower bound.
**Diagnosed:** 2026-09-04

### 2412_05636 (Stackelberg) — R3b

**Mechanism:** Server posts a reward R_t and sampling probability x_t; each client picks a correction factor alpha_i^t adjusting its privacy budget over a T-period horizon.
**Obstruction:** best_response_latex (Theorem 1, Eq. 21) is a genuine backward recursion: alpha_i^{t*} depends on alpha_i^r for all r > t via S(t) and the product prod_{r=t+1}^{j-1} alpha_i^r, terminated by alpha_i^T = 0. follower_foc_latex is the bare placeholder 'dU_i/dalpha_t^i = 0' with no algebraic content. Track 1's single-shot d(leader_utility)/d(follower_decision) check cannot encode a multi-period dynamic-programming recursion. (Track 1: follower best-response is a backward recursion over the horizon -- Track 1 single-shot FOC cannot encode it)
**Human task:** either unroll the recursion for a fixed small horizon T and record the resulting explicit closed form, or add a finite-horizon backward-induction mode to the Stackelberg checker.
**Diagnosed:** 2026-09-03

### 2502_20882 (Contract) — R7

**Mechanism:** Contract-theoretic FL incentive design between a server/platform and clients of private type.
**Obstruction:** This entry has no `notes` explaining why it sits at VERIFIED_TEMPLATE; the field is blank, meaning no prior Batch-C/D/E reviewer diagnosed the specific missing formal field, so Track 1 has nothing confirmed to run an IC/IR check against. (Track 1: Contract: notes field is empty -- no manual-review record of what is missing)
**Human task:** Open pdfs/2502_20882.pdf and the corpus.json formal fields for this entry side by side; identify which of ic_screening_latex / ir_participation_latex / server_objective_latex is null or unverified, transcribe it from the paper's own constraint labels, and only then attempt Track 1.
**Diagnosed:** 2026-09-06

### 2602_21844 (Contract) — R3a

**Mechanism:** Bayesian contract with an IC stated as an expectation E_{c_{-k}}[...] over the other agents' private costs.
**Obstruction:** The IC carries a multi-agent posterior expectation. Track 1 correctly bails out (stripping the expectation and grid-checking pointwise would prove something strictly stronger than the paper claims), and Track 4's symbolic integrator cannot reduce the E_{c_{-k}} expectation over the joint type distribution to a closed form it can check. (Track 4: expectation-form (Bayesian) IC integral -- SymPy Track 4 cannot evaluate the multi-agent posterior expectation to a posynomial-checkable closed form)
**Human task:** Supply the closed-form (integrated) interim utility for the paper's type distribution, or extend Track 4 with a numeric-quadrature Bayesian-IC path with an explicit soundness argument.
**Diagnosed:** 2026-09-03

### Batool2022fl_mab (VCG) — R7

**Mechanism:** VCG-style auction: platform scores/ranks bidders via a per-client scoring function S(r_i,p_i)=alpha1 r1+alpha2 r2+alpha3 r3-p_i (Eq. 3).
**Obstruction:** objective_latex left null fail-closed -- the paper only ever states the per-client scoring function used to rank/select bidders (already recorded as allocation_rule_latex); it never separately writes a platform-level welfare-maximization or cost-minimization objective, which Track 1's VCG DSIC/efficiency check requires as a distinct field. (Track 1: VCG: no separate platform-level objective distinct from the per-client scoring/allocation rule)
**Human task:** Check whether the paper anywhere states an aggregate objective (e.g. sum of S(r_i,p_i) over selected bidders, or a welfare/cost expression) outside Eq. 3; if the scoring rule genuinely doubles as the only stated objective, this stays MANUAL since Track 1 needs objective and allocation rule as separate fields.
**Diagnosed:** 2026-09-06

### Deng2020fmore_auction (VCG) — R-shape-cleanup

**Mechanism:** Forward auction: allocation is a piecewise indicator (x_i(b) = 1 if i in K, 0 otherwise, where K is an unspecified winner set); payment p_i(b) = sum_{j!=i} c(x_j*, gamma_hat_j) - theta_i, a sum-externality form.
**Obstruction:** parse_allocation has no AllocSpec case for a bare \begin{cases} set-membership rule with an unspecified winner set K (K's selection criterion, e.g. a welfare-max or greedy rule, is never given in allocation_rule_latex) -- there is no argmax expression to classify. Even if K's definition were transcribed, the payment's c(.) is an opaque cost function with no closed form. (Track 1: VCG: piecewise/set-membership allocation (x_i = 1 iff i in K) does not parse as any known AllocSpec shape)
**Human task:** Transcribe K's actual selection rule (likely stated elsewhere in the paper as an optimization over K) into allocation_rule_latex as an explicit argmax, and c(.)'s closed form into payment_rule_latex, before any track can attempt this entry.
**Diagnosed:** 2026-09-05

### Ding2020contract_multidim (Contract) — R3a

**Mechanism:** Multidimensional-type contract with menu items phi_i = (s_i, r_i).
**Obstruction:** The recorded client utility r_i - \theta_i s_i contains no occurrence of the contract variable \phi_i, so the contract substitution \phi_i -> \phi_j leaves the RHS identical to the LHS. The IC gap is identically zero: a trivially-true obligation that certifies nothing about the paper's mechanism. (Track 1: utility r_i - theta_i s_i has no dependence on the contract variable phi_i; substituting phi_i->phi_j yields an identical RHS -- degenerate IC (data-quality gap, unprovable as recorded))
**Human task:** Correct the transcription of client_utility_latex so it depends on the contract bundle \phi_i (i.e. on s_i and r_i as menu items), then re-run Track 1.
**Diagnosed:** 2026-09-03

### FLamma2025stackelberg (Stackelberg) — R7

**Mechanism:** Adaptive gamma-based Stackelberg game between server (leader) and clients (followers) intended to promote fairness in FL incentives.
**Obstruction:** This entry's notes never went through a Batch-C/D/E field-level review -- they only restate the paper's stated purpose ('address limitations of existing methods and promote fairness'), so no specific null field (follower_foc_latex / ir_follower_latex / best_response_latex) has been identified yet for Track 1 to consume. (Track 1: Stackelberg: notes give only the paper's abstract-level description, no diagnosed missing formal field)
**Human task:** Open pdfs/FLamma2025stackelberg.pdf, locate the leader/follower optimization problems and any stated IR/FOC, and transcribe whichever formal fields are printed; if the gamma-based mechanism lacks a follower IR statement (as with the sibling Stackelberg entries in this batch), record that explicitly and leave this MANUAL.
**Diagnosed:** 2026-09-06

### International_Journal_of_Intelligent_Systems_-_2024_-_Wan_-_Hierarchical_Incentive_Mechanism_for_Federated_Learning__A (Contract) — R3a

**Mechanism:** Hierarchical two-layer incentive mechanism; recorded IC reduces after prose-stripping to \varphi_m R_m - C V_m \geq \varphi_z R_z - C V_z.
**Obstruction:** Both sides of the recorded IC are evaluated at their own type, so the RHS carries no deviating-type dependence. The Task 11-pre soundness gate rejects it: certifying it would prove an ordering of equilibrium utilities, not incentive compatibility. (Track 1: IC is an equilibrium-utility ordering (both sides at own type), not U_i(contract_j); soundness gate correctly rejects -- no substitutable screening IC)
**Human task:** Re-extract the paper's true self-selection constraint U_m(contract_z) from the PDF so the RHS is the type-m agent's utility from contract z, then re-run Track 1.
**Diagnosed:** 2026-09-03

### Javaherian2025stackelberg_ic (Stackelberg) — R7

**Mechanism:** Leader sets gamma; follower (client i) chooses reporting/participation level tau_i, with Definition 1 stating a formal IR constraint and Lemma 5 proving the Nash equilibrium tau* satisfies it.
**Obstruction:** Batch E review added ir_follower_latex, transcribed exactly from Definition 1 (Individual Rationality), and noted Lemma 5 proves U_i(gamma,tau_i*,tau_{-i}*) >= 0 at the client-level Nash equilibrium -- IR is the one field this notes entry confirms is present, so the remaining VERIFIED_TEMPLATE gap must be in another field (e.g. follower_foc_latex or best_response_latex) not covered by this note. (Track 1: Stackelberg: IR is stated and proven satisfied at equilibrium, but the entry still sits at VERIFIED_TEMPLATE -- likely missing a different formal field for Track 1)
**Human task:** Diff this entry's formal fields against Track 1's required-field list to find which field besides ir_follower_latex is still null/unverified, then transcribe it from the paper (Definition 1's surrounding section is already confirmed correct and needs no further work).
**Diagnosed:** 2026-09-06

### Kang2019contract_mobile (Contract) — R4

**Mechanism:** Mobile-device contract; routed to Track 3 (mpmath.iv branch-and-bound, delta-sound).
**Obstruction:** Track 1 does not apply. The R4 fixed_constants field removes the three numerically-declared constants from the box (mu, c_n, s_n), but zeta (effective capacitance, never given a number) and the transmission-energy sub-symbols sigma/rho_n/B/h_n (paper only fixes the composite E^com=20, not the parts) stay free. IC is 6-dim but the branch-and-bound is inconclusive over the generic positive box; IR is still 8-dim, above the cap. The verifier reports UNKNOWN honestly rather than a partial-coverage result. (Track 3: after pinning the 3 paper-declared constants (mu=1, c_n=5, s_n=20) the IC drops from 9 to 6 free vars but the interval search over the generic [0.001,100] parameter box is still inconclusive (unsupported op / budget); the IR drops from 11 to 8 free vars and remains > box-dim cap -- neither IC nor IR is decidable at delta=0.001)
**Human task:** R4 pinned the 3 paper-declared constants (mu=1, c_n=5, s_n=20) via fixed_constants, dropping the IC box from 9 to 6 free vars and the IR box from 11 to 8, but IR is still over _MAX_BOX_DIMS and IC comes back inconclusive. zeta and the transmission sub-symbols (sigma, rho_n, B, h_n) have no per-symbol numeric values in the paper -- only the composite E^com = 20 -- so they were left free (fail-closed). Needs a tighter Track 3 or a symbolic reduction (R6).
**Diagnosed:** 2026-09-04

### Kang2019reliable_contract (Contract) — R4

**Mechanism:** Reliable-worker contract menu {(R_n, f_n)} with data-quality type theta_n = psi/log(1/epsilon_n).
**Obstruction:** The IC/IR parse and the soundness gate passes. The communication-cost term divides by a Shannon capacity B ln(1 + rho_n h_n / N_0); _sp_to_z3 will not admit the log without an established argument sign, and the entry declares no positivity domain for rho_n, h_n or N_0. No Track 1 obligation is built. (Track 1: Shannon-capacity term log(1 + rho h / N_0) in the denominator -- Z3 encoding rejects it ('log argument sign not established'))
**Human task:** R4 admitted the Shannon-capacity log(1 + rho_n h_n / N_0) via a positivity_domain field (Sec III-C: rho_n, h_n, N_0 > 0) + the _is_definitely_positive_sum integer-power fix, but Z3 still returns UNKNOWN on both IC and IR -- the obstruction is not the log admissibility.
**Diagnosed:** 2026-09-04

### Kang2022blockchain_metaverse (Contract) — R3a

**Mechanism:** Blockchain-metaverse contract stated as an adjacent (local) incentive constraint between neighbouring types.
**Obstruction:** The deviation index is n-1, which the SymPy layer reads as a single symbol named R_{n - 1} rather than as index n offset by one. The verifier's substitution machinery enumerates concrete integer indices and has no notion of an offset index, so the adjacent-IC form cannot be instantiated. (Track 1: R_{n-1} parses as a single symbol, not an iterable index; needs adjacent-IC semantics in _contract_check_core -- out of scope)
**Human task:** Add adjacent-IC (local downward/upward) semantics to _contract_check_core so an offset index n-1 instantiates to concrete neighbour pairs, or re-transcribe the paper's global IC if it states one.
**Diagnosed:** 2026-09-03

### Khan2019edge (Stackelberg) — R3b

**Mechanism:** Base station posts a reward; UEs choose a number of local iterations. Utilities are described in words only.
**Obstruction:** equilibrium_existence not established in the corpus entry -- position-paper (short IEEE magazine article), the Stackelberg game is described only qualitatively, and no explicit utility, derived best-response, FOC or IR constraint appears anywhere in the 7 pages. (Track 1: no proved equilibrium; Track 1 Stackelberg needs one)
**Human task:** a technical treatment with a derived Stackelberg equilibrium is needed; this venue does not provide one -- replace the entry with a full-length paper or drop it from the Stackelberg slice.
**Diagnosed:** 2026-09-03

### Le2021cellular_auction (VCG) — R-shape-cleanup

**Mechanism:** Reverse auction: allocation x* = argmax_{x_i} sum_i b_i x_i over an unconstrained-looking x in {0,1}^N; payment is the standard VCG externality form p_i = sum_{j!=i} b_j x_j(b_{-i}) - sum_{j!=i} b_j x_j(b).
**Obstruction:** No budget, cardinality, or other constraint on the winner set is recorded anywhere in the corpus's mechanism fields (bid_space, key_assumptions, objective_latex all omit it) -- argmax_{x_i} sum b_i x_i with x_i in {0,1} and no constraint is maximized by x_i=1 for every bidder (since b_i >= 0), i.e. every bidder wins unconditionally. Under that reading the externality payment is identically zero (removing bidder i changes no one else's allocation, since everyone already wins) -- the same identically-zero payment the solver's own soundness gate already flags as non-DSIC (every agent strictly gains by over-reporting when payment never binds). (Track 1: VCG: feasible set X for the multi-winner welfare-max allocation is never stated in the corpus (or, per the payment computing to zero, possibly the paper itself))
**Human task:** Re-read the source paper for the actual constraint set X (a budget cap, a cardinality k, or similar) that the corpus extraction dropped -- without it, the recorded mechanism is not a well-posed single-winner-or-more VCG auction, and no solver can prove or refute DSIC for math the paper's LaTeX (as transcribed) does not actually specify.
**Diagnosed:** 2026-09-05

### Lim2020contract (Contract) — R7

**Mechanism:** Contract-theoretic FL incentive design where the private type is a 4-dimensional cost vector, reduced by the paper to an auxiliary 2-dimensional (y, z) type.
**Obstruction:** The corpus note flags that Track 1's single-dimension substitution machinery may not fully capture a 4-D-reduced-to-2-D type space, so any resulting verdict must be treated with caution -- this is a structural mismatch between the paper's multidimensional screening model and the verifier's current type-substitution capability, not a missing field. (Track 1: Contract: genuinely multi-dimensional type (4-D cost vector -> 2-D auxiliary type) outside the verifier's single-dimension substitution machinery)
**Human task:** Confirm whether the (y, z) auxiliary reduction genuinely collapses to an equivalent single-crossing scalar type (in which case it could be reformalized for Track 1) or is irreducibly 2-D screening (in which case this needs a genuinely multidimensional mechanism-design proof, i.e. stays MANUAL); read Section on the contract-type reduction to decide.
**Diagnosed:** 2026-09-06

### Liu2023reverse_auction (VCG) — R-shape-cleanup

**Mechanism:** Reverse auction: winning coalition W = argmax_{W subseteq N} phi(W) - sum_j c_{MEC_j} - c_cloud - sum_{i in W} c_{user_i} - sum_{i in W} b_i (a coalition-selection welfare max mixing bidder costs with fixed infrastructure costs c_{MEC_j}/c_cloud); payment p_i = phi(W) - phi(W \ {i}) - b_i, the Clarke pivot on the coalition value phi.
**Obstruction:** This is a genuine multi-winner (coalition subset) allocation, which the current encoder's ArgmaxWelfare path cannot express at all (single-item/single-winner semantics only). Even a general multi-winner welfare-max encoder would need phi(W) -- an opaque coalition-value function never given a closed form in the corpus -- and the objective's non-bidder-indexed terms (c_{MEC_j}, c_cloud) mean 'welfare without bidder i' is not a simple sum-minus-one-term operation the way it is for a clean sum_i v_i x_i objective. (Track 1: VCG: multi-winner coalition allocation with a welfare objective containing non-bidder cost terms -- externality payment cannot be priced generically)
**Human task:** Transcribe phi(W)'s actual closed form from the source paper (if one exists) and hand-derive the Clarke-pivot DSIC/IR proof directly -- a coalition value with embedded infrastructure costs is outside any current track's decidable fragment.
**Diagnosed:** 2026-09-05

### Luo2023unbiased (Stackelberg) — R3b

**Mechanism:** Server sets customized per-client prices P_n; each client n chooses a participation probability q_n in [0, q_{n,max}].
**Obstruction:** best_response_latex is a bare argmax placeholder (q_n^{SE}(P) = argmax_{0<=q_n<=q_{n,max}} U_n(q_n,P_n)) with no algebraic content. follower_foc_latex is implicit in the unknown -- P_n + v_n (alpha/R) a_n^2 G_n^2 / q_n^{*2} - 2 c_n q_n^* = 0 is a cubic in q_n* whose root the entry never records -- and the true optimum is the box-clipped value, not the interior stationary point. There is no closed-form single-variable best response for the FOC check to verify against. (Track 1: follower best-response is an implicit argmax over a box and the recorded FOC is an implicit cubic in q_n* with no transcribed root -- Track 1 has no closed form to substitute)
**Human task:** record the explicit (clipped) root of the cubic from the paper, or add root-solving plus box-projection to the Stackelberg checker.
**Diagnosed:** 2026-09-03

### Ma2023joint_pricing (Contract) — R7

**Mechanism:** Server (Stage II) offers a menu of contracts phi_j=(d_j,r_j) to clients of private type theta_j; client payoff W_U^i (Eq. 6).
**Obstruction:** The 2026-07-18 review transcribed ic_screening_latex directly from Problem 1's own (IC) constraint label (verified against PDF p.5), but flagged that the existing client_utility_latex field simplifies W_U^i by dropping the explicit sum over k in I inside the congestion term -- left untouched per instructions, so the two fields are not on the same footing for Track 1's consistency check. (Track 1: Contract: ic_screening_latex was added from the paper's own (IC) label, but client_utility_latex is a simplified rendering of the same W_U^i that drops the congestion-term sum over k in I)
**Human task:** Rewrite client_utility_latex to include the full sum-over-k congestion term matching W_U^i (Eq. 6) exactly, so it is consistent with the already-verified ic_screening_latex before re-attempting Track 1.
**Diagnosed:** 2026-09-06

### Mai2022double_auction (VCG) — R7

**Mechanism:** Iterative double auction (IDA) and an RL-based double-auction variant matching buyers and sellers to maximize market efficiency and social welfare.
**Obstruction:** This entry's notes never went through a Batch-C/D/E field-level review -- they only restate the paper's stated contribution (an IDA algorithm and an RL-based double-auction algorithm), so no specific null field (objective_latex / allocation_rule_latex / payment_rule_latex) has been identified yet for Track 1's DSIC/efficiency check to consume. (Track 1: VCG: notes give only the paper's abstract-level description, no diagnosed missing formal field)
**Human task:** Open pdfs/Mai2022double_auction.pdf, locate the formal auction-clearing objective and price-setting rule for the IDA algorithm specifically (not the RL variant, which likely has no closed form), and transcribe them into the missing formal fields.
**Diagnosed:** 2026-09-06

### Ng2020uav_auction_coalition (VCG) — R-shape-cleanup

**Mechanism:** Forward auction: allocation x* = argmax_{x in X} sum_i v_i x_i (unit-weight welfare-max, feasible set X unspecified); payment p_i(b) = v_i x_i - (1/(N-1)) sum_{j!=i} v_j x_j.
**Obstruction:** The payment is not of the Clarke-pivot form (winner pays the externality caused by their presence) nor the standard Groves externality-difference form (p_i = W_{-i}(x*_{-i}) - W_{-i}(x*)) that encode_utility's welfare-difference path prices -- the (1/(N-1)) normalization constant is characteristic of a redistribution/rebate mechanism layered on top of a VCG payment (à la Cavallo/Bailey redistribution), not the base Groves payment itself. Even with a general multi-winner welfare-max encoder, this formula has no known closed-form DSIC proof the pipeline's tracks can produce. (Track 1: VCG: payment formula is not a Clarke/Groves externality payment -- it is an (N-1)-normalized redistribution rule, a different mechanism family)
**Human task:** Identify the specific redistribution-mechanism theorem this payment rule instantiates (if the paper cites one) and hand-verify DSIC + IR against that theorem's stated conditions -- this needs a paper-specific lemma, not a generic VCG grid proof.
**Diagnosed:** 2026-09-05

### Pang2025quality (Stackelberg) — R3b

**Mechanism:** Aggregator chooses payment functions evaluating agents' contributions; each agent k chooses an effort level e_k in [0,1].
**Obstruction:** Payment_k = f(Q / (Phi delta_k^2(e_k) + Phi delta_{k'}^2(e_{k'}) + Upsilon)) and Cost_k = c * d(|delta_k(0) - delta_k(e_k)|) are built from unspecified generic functions f and d, so the recorded follower_foc_latex (du_k/de_k = 0) and best_response_latex (a cases-form: 0 if the max is non-positive, else 'hat-e_k where du_k/de_k = 0') carry no algebraic content -- they restate the definition of a stationary point rather than solve it. Only an experiment-specific logarithmic instantiation (Sec. 6.2) has a closed form, and even that is in the Wasserstein variable delta_k rather than e_k. Venue is viXra (non-peer-reviewed). The entry's notes additionally flag that Appendix A.9 restates the same Theorem 4 in an inconsistent hat/no-hat notation, unresolved. (Track 1: payment/cost are unspecified generic functions f, d -- no algebraic form to differentiate)
**Human task:** pin f and d to the paper's actual instantiation (and resolve the Appendix A.9 notation conflict) before any obligation can be built; given the venue, verify the result independently first.
**Diagnosed:** 2026-09-03

### Saputra2020fl_contract (Contract) — R7

**Mechanism:** Server offers a menu of contracts to clients of private type; merged from a duplicate corpus entry (2004_01828, same PDF).
**Obstruction:** The dedup note flags a minor phi-weighting discrepancy between the two merged copies' ir_participation_latex and server_objective_latex fields that was never independently re-checked against the source PDF, so Track 1 would be running against a field of uncertain fidelity. (Track 1: Contract: possible phi-factor discrepancy between the merged duplicate's ir_participation_latex / server_objective_latex, not independently re-verified against the PDF)
**Human task:** Open pdfs/Saputra2020fl_contract.pdf, locate the phi weighting term in both ir_participation_latex and server_objective_latex, and confirm (or correct) it directly against the printed equations before trusting a Track 1 verdict on this entry.
**Diagnosed:** 2026-09-06

### Saputra2021iov_contract (Contract) — R7

**Mechanism:** SVs (principals) offer contracts to VSPs (agents) whose private type is theta_j (budget level); zeta_n(t) is a contract term offered by SVs, not the hidden type -- roles reversed vs. the usual server-designs-contract convention.
**Obstruction:** The correction note fixes the private-type identification (theta_j, not zeta_n(t)) and the role-reversal (VSP is the agent, SVs are principals), but flags that the exact form of the satisfaction function S() is only medium-confidence because of OCR artifacts in the source PDF -- Track 1 needs a verified S() to run the IC/IR check. (Track 1: Contract: medium-confidence satisfaction function S() due to OCR artifacts in the source PDF)
**Human task:** Open pdfs/Saputra2021iov_contract.pdf directly (image view, not OCR text-extraction) at the page defining S(), and transcribe the exact functional form to replace the OCR-uncertain version before re-running Track 1.
**Diagnosed:** 2026-09-06

### Saputra2021straggling (Contract) — R7

**Mechanism:** MUs (clients, principals) design a contract for the MAP (server, agent) whose private type is pi_i -- roles reversed vs. the usual server-designs-contract convention; involves square-root gain functions G_o, G_l.
**Obstruction:** The note flags that the role-reversed contract (MUs as principals, MAP as agent) is structurally fine but its square-root gain functions (G_o, G_l) are likely outside Track 1's polynomial-friendly assumption set, so even a correctly transcribed IC/IR pair may not resolve under the current solver encoding. (Track 1: Contract: square-root gain functions likely fall outside the verifier's polynomial-friendly assumptions)
**Human task:** Check whether Track 1's Z3 encoding can handle sqrt-form gain functions (e.g. via a polynomial relaxation or bound); if not, this stays MANUAL as a solver-capability gap rather than a missing-field gap.
**Diagnosed:** 2026-09-06

### Wang2022motilearn_contract (Contract) — R3a

**Mechanism:** MotiLearn contract menu with per-type effort/reward pairs.
**Obstruction:** The recorded IR uses subscript `a` while the IC uses `n`/`i`. The parser can identify a single type subscript from the IR but that subscript never appears in the IC RHS, so no sound (type, contract) index pair can be formed. Equating `a` with `n` would be an unverified guess. (Track 1: IR indexed by `a`, IC by `n`/`i`; `type_sub` never appears in the IC RHS -- cannot equate indices without guessing)
**Human task:** Re-transcribe IC and IR from the PDF under one consistent index convention, then re-run Track 1.
**Diagnosed:** 2026-09-03

### Wen2025diffusion_contract (Contract) — R3a

**Mechanism:** Diffusion-model-generated two-period intertemporal contract; the entry records only the period-2 static myopic IC/IR.
**Obstruction:** Every ^2 / ^1 in the recorded IC/IR is a period index, confirmed by contract_menu_latex's superscript-before-subscript ordering and by the entry's own notes. Reading them as exponents yields a different proof obligation than the paper's (linear) utility u_n = theta_n R_n - c T_n - E, and the intertemporal linkage between periods is absent from the entry entirely. Any verdict on the recorded fields would certify a mechanism the paper does not claim. (Track 1: recorded IC/IR is PERIOD-2 static myopic only (^2/^1 are period indices, not exponents); the paper's true mechanism is a two-period intertemporal contract not represented in the entry)
**Human task:** Transcribe the paper's full two-period intertemporal contract (both periods plus the linking constraint) with period indices distinguished from exponents, then decide whether an intertemporal IC is expressible on the Track 1 grid.
**Diagnosed:** 2026-09-03

### Wu2021contract_DP (Contract) — R7

**Mechanism:** Contract-theoretic FL incentive design with differential privacy, private type genuinely 3-dimensional (theta_x, tau_y, rho_z).
**Obstruction:** The corpus note states the verifier's single-dimension substitution machinery cannot capture a genuinely 3-D type space, so any verdict produced here should not be trusted as covering the paper's actual multidimensional screening claim -- this is a structural solver-capability gap, not a missing-field gap. (Track 1: Contract: genuinely 3-dimensional type outside the verifier's single-dimension substitution machinery)
**Human task:** Confirm whether (theta_x, tau_y, rho_z) can be reduced to a single monotone scalar index preserving the paper's IC ordering (as some sibling multi-dim entries attempt); if genuinely irreducible, this needs a hand-proved multidimensional screening argument and stays MANUAL.
**Diagnosed:** 2026-09-06

### Xia2026privacy_mfg (VCG) — R2

**Mechanism:** Top-k indicator q_i=1 iff i<=k, with payment min(B/k, c(v_{k+1}, 1/(n-k))) capped by a per-winner budget share.
**Obstruction:** The payment is a min of a budget-share cap and a critical value; the budget cap makes it neither a Clarke pivot nor a pure critical-value payment, so the top-k allocation alone is not enough for a grid DSIC proof. (Track 1: payment budget cap min(B/k, ·) breaks the Clarke-pivot form; top-k allocation is fine but the payment is not Groves)
**Human task:** Determine whether the budget cap ever binds under the paper's assumptions; if it does not, the mechanism reduces to a critical-value top-k.
**Diagnosed:** 2026-09-03

### Xiang2025esr_mhfl (VCG) — R-shape-cleanup

**Mechanism:** Bipartite client-to-computing-server matching: allocation maximizes sum_{cl_i,CS_j} x_ij v_ij (a two-index assignment, not a single-index unit-weight welfare sum); payment is the welfare-difference Groves pivot r(x*) - sum_{k!=i} c(x_k*, gamma_hat_k).
**Obstruction:** The payment text matches the welfare-difference Groves-pivot pattern (same text as Tan2025longterm, which IS provable), but the allocation is a two-index bipartite assignment (x_ij, over clients cl_i AND servers CS_j), not the single-index unit-weight welfare max (sum_i v_i x_i) that makes a welfare-difference pivot algebraically equal to the second price. _argmax_welfare_weights correctly returns None -- the equivalence proved for the single-index case does not generalize to bipartite matching. (Track 1: VCG: non-unit-weight bipartite allocation -- welfare-difference Groves pivot equivalence to second price does not hold)
**Human task:** A bipartite-matching VCG proof needs a different equivalence argument (e.g. that the pivot payment for a bipartite assignment problem is DSIC by the general Groves theorem, independent of the second-price shortcut) -- this is a genuinely different proof obligation than the encoder's current single-index welfare-max path, not a parser gap.
**Diagnosed:** 2026-09-05

### Xiao2020stackelberg_twostage (Stackelberg) — R7

**Mechanism:** Two-stage Stackelberg: server (leader, Stage I) and worker (follower, Stage II) choose local accuracy theta_i^(t); follower FOC is Eq. (13), solved by best_response_latex (Theorem 1's NE local accuracy).
**Obstruction:** follower_foc_latex was transcribed from Eq. (13) (verified against rendered PDF p.4). ir_follower_latex: the paper DOES state an explicit participation condition, but enforces it algorithmically -- Algorithm 1 Steps 7-8 say 'if any worker's utility < 0 then the worker quits from this round and Goto Step 3' -- transcribed as U_i^(t) >= 0, but this is a post-hoc per-round check outside the Stage II arg max in Eq. (11), not a constraint appearing inside the optimization problem itself (Steps 4-5 apply the symmetric check to the server's own utility). (Track 1: Stackelberg: follower IR is enforced algorithmically (Algorithm 1 quit-check) rather than as a constraint inside the Stage II arg max)
**Human task:** Decide whether Track 1's IR check can accept an algorithmically-enforced (outside-the-arg-max) participation condition as equivalent to an inline constraint; if the check requires the constraint to appear inside the Stage II optimization problem itself, this entry stays MANUAL as a genuine structural mismatch, not a missing transcription.
**Diagnosed:** 2026-09-06

### Yang2023async_contract (Contract) — R3a

**Mechanism:** Asynchronous FL contract menu {(R_n, e_n)} with data-quality type theta_n.
**Obstruction:** The IR reads theta R - xi e c f^2 - E_com >= 0, where E_com is a scalar communication-energy constant. The Task 11-pre Bayesian guard (_BAYESIAN_RE) matches the E_{subscript} form and correctly bails Track 1 out rather than risk stripping a real expectation. The entry has no type distribution, so Track 4 cannot pick it up either, and the entry falls through to the generic template. (Track 1: IR's E_{com} communication-energy term is indistinguishable from a Bayesian expectation E_{...}[.]; the Bayesian bail-out fires and Track 1 declines, while Track 4 has no distribution to integrate)
**Human task:** Rename or re-transcribe E_com so it is not shaped like an expectation operator (e.g. E^{com} or Ecom), then re-run Track 1; the IC itself already parses.
**Diagnosed:** 2026-09-03

### Zhang2022expost_auction (VCG) — R-shape-cleanup

**Mechanism:** Reverse auction with a weak budget-balance constraint (sum_i p_i <= B): winning set S = argmax_{S subseteq N} sum_{i in S} R_i - b_i; payment p_i = min(p_i^up, p_i'), where p_i^up = Re_i * rho* and p_i' = Re_i * max(B*re_i / sum_{j in S} re_j, rho*).
**Obstruction:** The payment is a 3-level nested piecewise formula (min of two terms, one of which is itself a max, scaled by a ratio over the winning set) tied to a global per-mechanism budget B and a market-clearing price rho* -- none of parse_payment's PaySpec cases (ClarkePivot / ExplicitFormula) can represent this, and it is not a Groves payment in any standard form (the budget cap and proportional-share terms make it a budget-feasible mechanism, a different design family with its own IC/IR proof obligations). (Track 1: VCG: piecewise min(.,.) payment with a nested max(.,.) and a global budget constraint -- not a Clarke pivot or any parseable payment shape)
**Human task:** This is a budget-constrained proportional-payment mechanism, not a Groves/VCG payment -- DSIC (if it holds at all) would need a paper-specific proof technique for budget-feasible mechanism design (e.g. a Singer-style budget-feasible mechanism argument), outside every current track's scope.
**Diagnosed:** 2026-09-05

### Zhang2024auction_comm (VCG) — R2

**Mechanism:** Allocation X = argmax_{i in K} S(s_i, p_i) over an unspecified score S; payment p_i = sum_{j != i} c_j - c_i.
**Obstruction:** The payment subtracts the agent's OWN cost c_i from the sum of others' costs, so it is not a welfare-with-vs-without-i pivot and is directly decreasing in i's own report; the score S is also left undefined, so the argmax has no encodable objective. (Track 1: payment subtracts the agent's own reported cost (sum_{j!=i} c_j - c_i); not a Clarke pivot)
**Human task:** Define S and recheck the payment against the paper — as recorded it is not a Groves pivot and is likely a transcription error.
**Diagnosed:** 2026-09-03
