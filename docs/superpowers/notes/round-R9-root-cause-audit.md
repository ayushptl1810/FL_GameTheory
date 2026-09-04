# R9 — Root-Cause Audit

Traced 86 MANUAL entries through their real verifier code path.
`matches_stored` is a heuristic triage signal, not a proof -- every `False` row
needs a human read in Phase 2 to confirm the real obstruction.

**Mismatches found: 86 / 86**

| Paper ID | Category | Stored Round | Stored Obstruction (truncated) | Real Bail Function | Real Bail Reason (truncated) | Match? |
|---|---|---|---|---|---|---|
| 1811_12082 | Stackelberg | R7 | Batch-C review left ir_follower_latex null (fail-closed) -- ... | _try_stackelberg_latex | returned None | False |
| 2101_05628 | Stackelberg | R4 | Both best_response_latex and follower_foc_latex are null, an... | _try_stackelberg_latex | returned None | False |
| 2101_12428 | Stackelberg | R4 | The recorded follower_foc_latex is a budget-eliminated *diff... | _try_stackelberg_latex | returned None | False |
| 2102_03401 | Contract | R4 | corpus data transcription bug, not a math obstruction | _try_contract_latex | returned None | False |
| 2103_05866 | Stackelberg | R3b | The entry is explicitly a THREE-STAGE Stackelberg game and t... | _try_stackelberg_latex | returned None | False |
| 2110_12876 | Stackelberg | R7 | Batch-C review left ir_follower_latex null (fail-closed) -- ... | _try_stackelberg_latex | returned None | False |
| 2203_00270 | Stackelberg | R7 | Batch-C review transcribed follower_foc_latex/best_response_... | _try_stackelberg_latex | returned None | False |
| 2308_12502 | Contract | R3a | Two independent obstructions. (1) The entry's own notes reco... | _try_contract_latex | returned None | False |
| 2403_09153 | Contract | R7 | The 2026-07-18 sanitization pass removed 'single-crossing (S... | _try_contract_latex | returned None | False |
| 2404_08261 | Stackelberg | R7 | Batch-C review left ir_follower_latex null (fail-closed) -- ... | _try_stackelberg_latex | returned None | False |
| 2404_13841 | VCG | R4 | Winner set is a budget-threshold cutoff k=min{k: b_k > B/(Sk... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| 2405_13879 | Shapley | R5 | The paper never defines v(S) over agent subsets and never us... | verify_shapley | returned non-terminal verdict MANUAL: MANUAL (R5): The paper... | False |
| 2407_02845 | Contract | R4 | The IC/IR parse and the soundness gate passes, but the log-u... | _try_contract_latex | returned None | False |
| 2408_13223 | Contract | R3a | The entry's ic_screening_latex is deliberately null: the pap... | _try_contract_latex | returned None | False |
| 2412_05636 | Stackelberg | R3b | best_response_latex (Theorem 1, Eq. 21) is a genuine backwar... | _try_stackelberg_latex | returned None | False |
| 2502_08248 | Shapley | R5 | Tier A confirms the standard Shapley formula, but the paper ... | verify_shapley | returned non-terminal verdict MANUAL: k > 3 or coalition siz... | False |
| 2502_10765 | Stackelberg | R4 | The follower decision is two variables chosen jointly; follo... | _try_stackelberg_latex | returned None | False |
| 2502_20882 | Contract | R7 | This entry has no `notes` explaining why it sits at VERIFIED... | _try_contract_latex | returned None | False |
| 2505_02462 | Contract | R3a | The entry's ic_screening_latex is deliberately null: the pap... | _try_contract_latex | returned None | False |
| 2505_05842 | Contract | R3a | The entry's ic_screening_latex is deliberately null: the pap... | _try_contract_latex | returned None | False |
| 2508_07676 | Stackelberg | R7 | Batch D review left follower_foc_latex null fail-closed -- t... | _try_stackelberg_latex | returned None | False |
| 2602_21844 | Contract | R3a | The IC carries a multi-agent posterior expectation. Track 1 ... | _try_contract_latex | returned None | False |
| 2605_02935 | Contract | R3a | The entry's ic_screening_latex is deliberately null: the pap... | _try_contract_latex | returned None | False |
| 2605_11889 | Shapley | R5 | Tier A confirms the formula is the exact Shapley value, but ... | verify_shapley | returned non-terminal verdict MANUAL: k > 3 or coalition siz... | False |
| 2606_18384 | Shapley | R5 | Tier A rejects the formula: the 1/binom(|C|-1,|Sub|) weighti... | verify_shapley | returned non-terminal verdict MANUAL: k > 3 or coalition siz... | False |
| Ahmed2023frimfl | VCG | R4 | Allocation is a per-client budget-feasibility cases-threshol... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Batool2022fl_mab | VCG | R7 | objective_latex left null fail-closed -- the paper only ever... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Bornstein2023realistic_incentive | Contract | R3a | The entry's ic_screening_latex is deliberately null: the pap... | _try_contract_latex | returned None | False |
| Cao2025service | Stackelberg | R7 | Batch D review left ir_follower_latex null fail-closed -- th... | _try_stackelberg_latex | returned None | False |
| Chen2023multifactor_iot | Stackelberg | R7 | Batch D review left ir_follower_latex null fail-closed -- no... | _try_stackelberg_latex | returned None | False |
| Chu2023hierarchical | Stackelberg | R3b | best_response_latex is deliberately null: the paper states o... | _try_stackelberg_latex | returned None | False |
| Cui2024auction_market | VCG | R2 | The payment multiplies another agent's bid by a continuous m... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Ding2020contract_multidim | Contract | R3a | The recorded client utility r_i - \theta_i s_i contains no o... | _try_contract_latex | returned None | False |
| FLamma2025stackelberg | Stackelberg | R7 | This entry's notes never went through a Batch-C/D/E field-le... | _try_stackelberg_latex | returned None | False |
| GPS2023afl_recruit | VCG | R4 | The winner count is not specified so the rule is not a fixed... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Guo2023stackelberg_industrial | Stackelberg | R4 | Both best_response_latex and follower_foc_latex are null (fa... | _try_stackelberg_latex | returned None | False |
| Han2025paid_models | Contract | R4 | The IC parses (type subscript i, contract subscript j, sound... | _try_contract_latex | returned None | False |
| Haupt2021auctions | VCG | R2 | The payment contains an opaque Punish(s_j - s_i) aggregate a... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Hu2020trading | Stackelberg | R7 | Batch E review left ir_follower_latex null fail-closed -- th... | _try_stackelberg_latex | returned None | False |
| Hu2022truthful_FEL | Stackelberg | R7 | Batch E review left follower_foc_latex null fail-closed -- t... | _try_stackelberg_latex | returned None | False |
| Huang2024aigc | Contract | R3a | The entry's ic_screening_latex is deliberately null: the pap... | _try_contract_latex | returned None | False |
| International_Journal_of_Intelligent_Systems_-_2024_-_Wan_-_Hierarchical_Incentive_Mechanism_for_Federated_Learning__A | Contract | R3a | Both sides of the recorded IC are evaluated at their own typ... | _try_contract_latex | returned None | False |
| Javaherian2025stackelberg_ic | Stackelberg | R7 | Batch E review added ir_follower_latex, transcribed exactly ... | _try_stackelberg_latex | returned None | False |
| Jiao2019auto_auction | VCG | R4 | The allocation maximizes a COUNT subject to a budget constra... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Jin2023bara_budget | VCG | R4 | Budget-knapsack allocation is out of the {argmax, top-k, wei... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Kang2019contract_mobile | Contract | R4 | Track 1 does not apply. The R4 fixed_constants field removes... | _try_contract_latex | returned non-terminal verdict UNKNOWN: IR:UNKNOWN IC:UNKNOWN... | False |
| Kang2019reliable_contract | Contract | R4 | The IC/IR parse and the soundness gate passes. The communica... | _try_contract_latex | returned non-terminal verdict UNKNOWN: IR:UNKNOWN IC:UNKNOWN... | False |
| Kang2022blockchain_metaverse | Contract | R3a | The deviation index is n-1, which the SymPy layer reads as a... | _try_contract_latex | returned None | False |
| Karimireddy2022data_sharing | Contract | R3a | The entry's ic_screening_latex is deliberately null: the pap... | _try_contract_latex | returned None | False |
| Khan2019edge | Stackelberg | R3b | equilibrium_existence not established in the corpus entry --... | _try_stackelberg_latex | returned None | False |
| Lee2024sfl_stackelberg | Stackelberg | R7 | Batch E review left ir_follower_latex null fail-closed -- no... | _try_stackelberg_latex | returned None | False |
| Li2025iiot_drl | Stackelberg | R7 | Batch E review left ir_follower_latex null fail-closed -- Pr... | _try_stackelberg_latex | returned None | False |
| Li2025split | Stackelberg | R4 | best_response_latex is a bare argmax placeholder (q*_{i,j} =... | _try_stackelberg_latex | returned None | False |
| Li2026network | Contract | R3a | The entry's ic_screening_latex is deliberately null: the pap... | _try_contract_latex | returned None | False |
| Lim2020contract | Contract | R7 | The corpus note flags that Track 1's single-dimension substi... | _try_contract_latex | returned None | False |
| Lim2020edge_collab | VCG | R2 | Both allocation_rule_latex and payment_rule_latex are null, ... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Liu2026fedbud | Stackelberg | R4 | The follower decision is two variables chosen jointly and fo... | _try_stackelberg_latex | returned None | False |
| Lu2021cluster_auction | VCG | R4 | The eligible set JL is itself defined by a min over a previo... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Luo2023unbiased | Stackelberg | R3b | best_response_latex is a bare argmax placeholder (q_n^{SE}(P... | _try_stackelberg_latex | returned None | False |
| Ma2023joint_pricing | Contract | R7 | The 2026-07-18 review transcribed ic_screening_latex directl... | _try_contract_latex | returned None | False |
| Mai2022double_auction | VCG | R7 | This entry's notes never went through a Batch-C/D/E field-le... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Model2024trading_fl | VCG | R2 | The allocation is a neural RL policy with no closed form, so... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Nguyen2025right_reward | Contract | R4 | The IC parses via utility-call expansion (type subscript k, ... | _try_contract_latex | returned None | False |
| Pandey2019crowd | Stackelberg | R3b | follower_foc_latex is 1/theta_k - log(1/theta_k) = (r + nu_k... | _try_stackelberg_latex | returned None | False |
| Pang2025quality | Stackelberg | R3b | Payment_k = f(Q / (Phi delta_k^2(e_k) + Phi delta_{k'}^2(e_{... | _try_stackelberg_latex | returned None | False |
| Peng2023auction_medical | VCG | R2 | Both allocation_rule_latex and payment_rule_latex are null, ... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Saputra2020fl_contract | Contract | R7 | The dedup note flags a minor phi-weighting discrepancy betwe... | _try_contract_latex | returned None | False |
| Saputra2021iov_contract | Contract | R7 | The correction note fixes the private-type identification (t... | _try_contract_latex | returned None | False |
| Saputra2021straggling | Contract | R7 | The note flags that the role-reversed contract (MUs as princ... | _try_contract_latex | returned None | False |
| Seo2021sdn_fl | VCG | R2 | The payment is an exponential of the quality score; Z3 canno... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Seo2022noniid_auction | VCG | R2 | Same exponential-payment obstruction as Seo2021: the payment... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Tan2023hire | VCG | R2 | The allocation switches objective based on a time-varying qu... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Wang2022blockchain | Stackelberg | R4 | Two obstructions compound. (1) The follower decision is two ... | _try_stackelberg_latex | returned None | False |
| Wang2022motilearn_contract | Contract | R3a | The recorded IR uses subscript `a` while the IC uses `n`/`i`... | _try_contract_latex | returned None | False |
| Wei2024truthful_bandit | VCG | R2 | The objective is a log-determinant over subsets: both the ex... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Wen2025diffusion_contract | Contract | R3a | Every ^2 / ^1 in the recorded IC/IR is a period index, confi... | _try_contract_latex | returned None | False |
| Wu2021contract_DP | Contract | R7 | The corpus note states the verifier's single-dimension subst... | _try_contract_latex | returned None | False |
| Xia2026privacy_mfg | VCG | R2 | The payment is a min of a budget-share cap and a critical va... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Xiao2020stackelberg_twostage | Stackelberg | R7 | follower_foc_latex was transcribed from Eq. (13) (verified a... | _try_stackelberg_latex | returned None | False |
| Yang2023async_contract | Contract | R3a | The IR reads theta R - xi e c f^2 - E_com >= 0, where E_com ... | _try_contract_latex | returned None | False |
| Yang2023buyers_market | VCG | R2 | This is a continuous screening/contract menu over theta_i in... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Yu2022multi_leader_fl | Stackelberg | R4 | Three compounding obstructions. The follower chooses a K-com... | _try_stackelberg_latex | returned None | False |
| Zhang2020fedserving | Contract | R3a | The entry's ic_screening_latex is deliberately null: the pap... | _try_contract_latex | returned None | False |
| Zhang2022online | VCG | R2 | The threshold rho* is set online from an unbounded arrival s... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Zhang2024auction_comm | VCG | R2 | The payment subtracts the agent's OWN cost c_i from the sum ... | verify_vcg | returned non-terminal verdict VERIFIED_SHAPE: IR: VERIFIED |... | False |
| Zhao2023truthful | Contract | R3a | The entry's ic_screening_latex is deliberately null: the pap... | _try_contract_latex | returned None | False |

## Regrouped by real cause

Task 1's table above is one row per entry (86 rows). Grouping those rows by
`bail_function` + `bail_reason` prefix (>= 2 entries per group) and reading
each mismatch row's full stored obstruction/limit text against the real
`bail_reason` produced 8 real clusters covering 60 entries, all classified
as genuine solver ceilings (0 fixable bugs found) — full detail, entry
lists, real-cause writeups, and per-cluster corrected diagnosis text are in
`docs/superpowers/notes/round-R9-widening-candidates.md`. Summary:

| Cluster | Entries | Classification |
|---|---|---|
| Contract: no adverse-selection IC in paper | 9 | ceiling |
| Contract: multi-dim / population-coupled type | 3 | ceiling |
| Contract: transcendental / opaque function | 3 | ceiling |
| Stackelberg: no follower IR stated | 11 | ceiling |
| Stackelberg: vector follower decision | 8 | ceiling |
| VCG: allocation outside fixed template (4 sub-groups) | 21 | ceiling (1 sub-group of 4 flagged for closer inspection) |
| Shapley: k > 3 / coalition size unstated | 3 | ceiling |
| Contract: box-dimension cap after pinning | 2 | ceiling |

`matches_stored == false` on every one of these 60 rows is the known
non-discriminating heuristic (lexical mismatch between real bail_reason and
stored obstruction text), not evidence of a stale diagnosis — confirmed by
reading full text for each row. See `round-R9-widening-candidates.md` for
the per-cluster reasoning.
