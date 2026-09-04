# R6-R7 residual work-list

(25 entries)
25 in-scope VERIFIED_TEMPLATE with no verdict_override. Each row: the Phase-6 hint / Phase-7 diagnosis seed is manual_diagnosis.obstruction if present, else the notes prefix.

| paper_id | category | verdict | seed source | seed (truncated) |
|---|---|---|---|---|
| 2403_09153 | Contract | VERIFIED_TEMPLATE | notes | key_assumptions sanitized 2026-07-18: original list matched the extraction-prompt example in tools/prompts.py verbatim (prompt-anchoring contamination). Kept on |
| 2502_20882 | Contract | VERIFIED_TEMPLATE | notes |  |
| Lim2020contract | Contract | VERIFIED_TEMPLATE | notes | Type is genuinely multi-dimensional (4-D cost vector reduced to an auxiliary 2-D (y,z) type) -- the verifier's single-dimension substitution machinery may not f |
| Ma2023joint_pricing | Contract | VERIFIED_TEMPLATE | notes | Added ic_screening_latex (2026-07-18), transcribed from the paper's own constraint labeled (IC) in Problem 1 (Server's Contract Design in Stage II), verified ag |
| Saputra2020fl_contract | Contract | VERIFIED_TEMPLATE | notes | DEDUPLICATED: merged from a duplicate corpus entry (2004_01828, same PDF). Minor phi-factor discrepancy in ir_participation_latex/server_objective_latex between |
| Saputra2021iov_contract | Contract | VERIFIED_TEMPLATE | notes | CORRECTED: private type is theta_j (VSP's budget level), not zeta_n(t) as previously listed -- zeta_n is a contract term offered by SVs, not the hidden type. Al |
| Saputra2021straggling | Contract | VERIFIED_TEMPLATE | notes | Role-reversed vs. the usual convention: the MAP (server) is the agent with the private type pi_i; the MUs (clients) act as principals designing the contract. In |
| Wu2021contract_DP | Contract | VERIFIED_TEMPLATE | notes | Type is genuinely 3-dimensional (theta_x, tau_y, rho_z) -- the verifier's single-dimension substitution machinery cannot capture this; a verdict here (if any) s |
| 1811_12082 | Stackelberg | VERIFIED_TEMPLATE | notes | Manual review (Batch C): no explicit IR/participation constraint for the follower (model owner) is stated anywhere in the paper. The only constraint on the foll |
| 2110_12876 | Stackelberg | VERIFIED_TEMPLATE | notes | Manual review (Batch C): no individual-rationality or participation constraint (U_i >= 0 or outside option) is stated anywhere in the paper for the follower (ve |
| 2203_00270 | Stackelberg | VERIFIED_TEMPLATE | notes | Manual review (Batch C): follower_foc_latex and best_response_latex extracted from Appendix A/B (the P3/P5 problem derivation), verified via direct image read o |
| 2404_08261 | Stackelberg | VERIFIED_TEMPLATE | notes | Manual review (Batch C): no individual-rationality or participation constraint is stated anywhere in the paper -- no 's.t.' / constraint block appears for the f |
| 2508_07676 | Stackelberg | VERIFIED_TEMPLATE | notes | Batch D manual review (2026-07-18): follower_foc_latex left null (fail-closed, overriding the extracting agent's initial derivation on human review) -- the cand |
| Cao2025service | Stackelberg | VERIFIED_TEMPLATE | notes | Batch D manual review (2026-07-18): ir_follower_latex reviewed, left null (fail-closed). The LMO's optimization problem (Eq. 9, Sec 3) is stated with no constra |
| Chen2023multifactor_iot | Stackelberg | VERIFIED_TEMPLATE | notes | Batch D manual review (2026-07-18): ir_follower_latex reviewed, left null (fail-closed). No constraint block or utility>=0 condition is stated anywhere for the  |
| FLamma2025stackelberg | Stackelberg | VERIFIED_TEMPLATE | notes | The paper proposes FLamma, a novel Federated Learning framework based on adaptive gamma-based Stackelberg game, designed to address the limitations of existing  |
| Hu2020trading | Stackelberg | VERIFIED_TEMPLATE | notes | Batch E (manual PDF review): Added best_response_latex, transcribed exactly as Eq. (15) in the paper (the closed-form maximizer of the FOC already recorded in f |
| Hu2022truthful_FEL | Stackelberg | VERIFIED_TEMPLATE | notes | Batch E (manual PDF review): follower_foc_latex left null (fail-closed, overriding the extracting agent's initial reconstruction on human review). The paper sta |
| Javaherian2025stackelberg_ic | Stackelberg | VERIFIED_TEMPLATE | notes | Batch E (manual PDF review): Added ir_follower_latex, transcribed exactly from Definition 1 (Individual Rationality (IR)) in the paper. The paper additionally p |
| Lee2024sfl_stackelberg | Stackelberg | VERIFIED_TEMPLATE | notes | Batch E (manual PDF review): ir_follower_latex left null (fail-closed). No formal IR constraint (U_n >= 0) is stated in the game formulation; the only constrain |
| Li2025iiot_drl | Stackelberg | VERIFIED_TEMPLATE | notes | Batch E (manual PDF review): ir_follower_latex left null (fail-closed). The node's optimization Problem P1 (Eq. 11) imposes only the feasibility constraint thet |
| Xiao2020stackelberg_twostage | Stackelberg | VERIFIED_TEMPLATE | notes | follower_foc_latex transcribed from Eq.(13) (verified against rendered PDF p.4): the stationarity condition d U_i^(t)/d theta_i^(t) = 0 that Theorem 1's Nash-eq |
| Batool2022fl_mab | VCG | VERIFIED_TEMPLATE | notes | Batool2022fl_mab: objective_latex left null (fail-closed). The paper defines only a per-client auction scoring function S(r_i,p_i)=alpha1 r1+alpha2 r2+alpha3 r3 |
| Mai2022double_auction | VCG | VERIFIED_TEMPLATE | notes | The paper proposes an iterative double auction (IDA) algorithm and a reinforcement learning-based double auction algorithm to achieve market efficiency and soci |
| Zheng2023fl_market | VCG | VERIFIED_TEMPLATE | notes | Zheng2023fl_market: objective_latex = 'Problem 2' (Budget-Limited Multi-Unit Multi-Item Procurement Auction), the paper's formally stated joint auction+aggregat |
