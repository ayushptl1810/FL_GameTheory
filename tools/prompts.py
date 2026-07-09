"""LLM prompts for classification and per-category field extraction."""

from __future__ import annotations

CLASSIFY_SYSTEM = """\
You are an expert in game theory and federated learning (FL) incentive mechanisms.
Classify the paper into exactly ONE category based on its PRIMARY incentive mechanism.

VCG       — Server runs auction; clients bid costs/values. Payment rule derived from social
            surplus (VCG formula). Includes reverse/procurement auctions (server pays lowest-
            cost workers), forward auctions, double auctions, combinatorial auctions.
Contract  — Server offers a menu of (effort, reward) pairs. Clients have hidden types (data
            quality, cost). IC screening constraint + IR participation constraint. Screening
            via contract theory / mechanism design under information asymmetry.
Stackelberg — Leader-follower game. Server announces pricing rule first; clients best-respond.
            Solution: Stackelberg equilibrium derived from follower's first-order condition.
Shapley   — Uses Shapley value payments AND formally proves IC (truthful reporting optimal)
            AND IR (payment >= participation cost). Pure contribution measurement without
            IC/IR proofs -> use Valuation instead.
RL        — Uses reinforcement learning (DQN, PPO, A3C, MARL, policy gradient) to determine
            payments or select clients. No closed-form rule -- policy is a neural network.
Valuation — Data valuation or pricing WITHOUT formal IC/IR proof. Includes Shapley approxi-
            mations (GTG-Shapley, WT-Shapley, FedToken), gradient-norm scoring, reputation
            scores, market equilibrium pricing lacking IC proof.
Naive     — Simple baseline rule: proportional payment (proportional to dataset size), equal
            split, FedAvg with no incentive modification. Also: papers studying free-rider
            attacks or failure modes of naive aggregation without proposing a new mechanism.

Return ONLY valid JSON:
{"category": "<VCG|Contract|Stackelberg|Shapley|RL|Valuation|Naive>", "reason": "<one sentence>"}
"""

EXTRACT_SYSTEM = """\
You are a mathematical extraction specialist for FL incentive mechanism papers.
Extract the specified fields precisely from the paper text.

Rules:
- LaTeX fields: write clean LaTeX math using double backslashes (\\\\) inside JSON strings.
  Example: "p_i = r(x^*) - \\\\sum_{k \\\\neq i} c(x_k^*, \\\\hat{\\\\gamma}_k)"
- Use null (JSON null, not the string "null") for fields not present in the paper.
- Do NOT use placeholder strings like "unspecified", "TBD", or "N/A" -- use null instead.
- For boolean fields (ic_proof_present, equilibrium_existence, etc.) use true/false.
- Return ONLY a valid JSON object -- no markdown fences, no commentary.
"""

VCG_PROMPT = """\
Extract these fields from the VCG/auction FL paper. Return a single flat JSON object.

TOP-LEVEL fields:
- "title": full paper title
- "year": publication year as integer
- "venue": conference/journal (e.g. "IEEE INFOCOM 2020", "arXiv preprint", "IEEE TMC 2023")
- "fl_setup": 2-sentence description of the FL scenario and what resource is being auctioned
- "num_clients": number of clients as string (e.g. "N", "K", "up to 50")
- "notes": important design choices or unusual aspects (string or null)
- "paper_type": JSON array -- include "primary" if new mechanism, "comparison" if it benchmarks
  multiple mechanisms head-to-head, "application" if applied to specific domain (healthcare/IoT/etc.)

MECHANISM fields (inside a nested "mechanism" object):
- "auction_type": one of "forward"/"reverse"/"double"/"combinatorial"/"multi-unit"/"sequential"/"other"
    forward = clients bid for right to participate (server selects top bidders)
    reverse = server procures resources from clients (pays lowest-cost providers)
    double = both server-side buyers and client-side sellers bid
- "bid_space": what clients bid (e.g. "private cost parameter gamma_i in Gamma", "valuation v_i in [0,V_max]")
- "allocation_rule_latex": LaTeX for x*(b) -- allocation rule (argmax social surplus, or threshold)
- "payment_rule_latex": LaTeX for the VCG payment p_i(b) -- actual payment formula from the paper
- "client_utility_latex": LaTeX for u_i = value - payment (or payment - cost for reverse auction)
- "ic_type": "dominant-strategy" / "BNE" / "ex-post" / "approximate"
- "ic_condition_latex": LaTeX for IC constraint
- "ir_condition_latex": LaTeX for IR constraint (u_i >= 0 or payment >= cost)
- "objective_latex": LaTeX for server's objective (social surplus, revenue, or efficiency)
- "budget_balance_type": "strong" (sum p_i = 0), "weak" (sum p_i <= revenue), "deficit", or null
- "budget_balance_latex": LaTeX for BB condition (or null)
- "key_assumptions": JSON array of strings

COMPARISON block (only if "comparison" in paper_type):
- "comparison": {{"mechanisms_compared": [...], "comparison_metric": "...", "winning_condition": "...", "key_finding": "..."}}

APPLICATION block (only if "application" in paper_type):
- "application": {{"domain": "<healthcare/iot/mobile-edge/autonomous-vehicles/industrial/other>",
                  "domain_constraints": [...], "mechanism_modification": "..."}}

Paper text:
{text}
"""

CONTRACT_PROMPT = """\
Extract these fields from the contract theory FL paper. Return a single flat JSON object.

TOP-LEVEL fields: "title", "year", "venue", "fl_setup", "num_clients", "notes", "paper_type"

MECHANISM fields (inside "mechanism" object):
- "num_types": integer (e.g. 2, 5, 10) or "continuous" for continuous type space
- "type_variable": the private type variable (e.g. "data quality theta_i in {{theta_1,...,theta_I}}",
    "cost sensitivity c_i", "data coverage alpha_i")
- "type_distribution": probability over types (e.g. "discrete uniform beta_i = 1/I",
    "exponential distribution", "continuous U[0,1]")
- "information_structure": one of:
    "hidden-type"   = only theta is private (adverse selection, type screening)
    "hidden-action" = only effort e is unobservable (moral hazard)
    "both"          = theta AND e are both private (compound info asymmetry)
- "cost_function_form": algebraic form (e.g. "quadratic: (c/2)e_i^2", "linear: c_i*e_i")
- "multidimensional_type": true if type has >=2 dimensions (e.g. (theta, effort) pair), false otherwise
- "client_utility_latex": LaTeX for U_i (client's net payoff from participating)
- "cost_function_latex": LaTeX for C_i(e_i) or C_i(theta_i, e_i)
- "contract_menu_latex": LaTeX defining the contract menu (e.g. "\\\\{{(e_i, R_i)\\\\}}_{{i=1}}^I")
- "ic_screening_latex": LaTeX for IC screening constraint (type i shouldn't prefer type j's contract)
- "ir_participation_latex": LaTeX for IR constraint (U_i >= 0)
- "server_objective_latex": LaTeX for server's maximization objective
- "key_assumptions": JSON array of strings (e.g. ["quadratic cost", "single-crossing (Spence-Mirrlees)",
    "discrete finite type space", "risk neutral clients"])

COMPARISON / APPLICATION blocks -- same structure as VCG if applicable.

Paper text:
{text}
"""

STACKELBERG_PROMPT = """\
Extract these fields from the Stackelberg game FL paper. Return a single flat JSON object.

TOP-LEVEL fields: "title", "year", "venue", "fl_setup", "num_clients", "notes", "paper_type"

MECHANISM fields (inside "mechanism" object):
- "leader": who moves first (typically "server", "model owner", "platform", or "aggregator")
- "follower": who best-responds (typically "clients", "workers", "organizations", "devices")
- "leader_decision": what the leader announces (e.g. "unit price q_i per CPU cycle",
    "reward schedule R(e_i)", "data purchasing price p")
- "follower_decision": what followers optimize (e.g. "CPU power P_i in [0, P_max]",
    "effort level e_i", "data contribution fraction d_i")
- "equilibrium_existence": true if paper proves Stackelberg equilibrium exists, false if not proved
- "equilibrium_uniqueness": true if uniqueness proved, false if not (null if not discussed)
- "leader_objective_latex": LaTeX for leader's optimization problem
- "follower_utility_latex": LaTeX for U_i(follower_var, leader_var) -- follower's payoff function
- "follower_foc_latex": LaTeX for first-order condition dU_i/d(follower_var) = 0
- "best_response_latex": LaTeX for closed-form best response derived from FOC
- "ir_follower_latex": LaTeX showing U_i at best response >= 0 (IR condition)
- "key_assumptions": JSON array (e.g. ["quadratic cost", "concave follower objective",
    "unique interior optimum", "complete information on leader side"])

COMPARISON / APPLICATION blocks if applicable.

Paper text:
{text}
"""

SHAPLEY_PROMPT = """\
Extract these fields from the Shapley-based FL paper. Return a single flat JSON object.

CRITICAL HARD GATE: Set ic_proof_present=true ONLY if the paper contains a formal THEOREM or
PROPOSITION with proof showing truthful reporting is optimal (i.e. misreporting Shapley inputs
cannot increase payment). Set ir_proof_present=true ONLY if there is a formal proof that
payment >= participation cost for all clients. Informal claims or intuitions do NOT qualify.
If either is false, add a "reclassify_note" field explaining what is missing.

TOP-LEVEL fields: "title", "year", "venue", "fl_setup", "num_clients", "notes", "paper_type"

MECHANISM fields (inside "mechanism" object):
- "valuation_metric": what V(S) measures (e.g. "test accuracy improvement on server dataset",
    "loss reduction", "gradient cosine similarity")
- "exact_or_approx": "exact" (full factorial permutation) or "approximate" (sampling/truncation)
- "ic_proof_present": boolean -- formal IC proof present? (see CRITICAL note above)
- "ir_proof_present": boolean -- formal IR proof present? (see CRITICAL note above)
- "characteristic_function_latex": LaTeX for V(S) definition
- "shapley_formula_latex": LaTeX for phi_i formula
- "ic_condition_latex": LaTeX for IC constraint (null if ic_proof_present is false)
- "ir_condition_latex": LaTeX for IR constraint (null if ir_proof_present is false)
- "axioms_satisfied": JSON array from ["efficiency", "symmetry", "dummy", "additivity", "monotonicity"]
- "key_assumptions": JSON array of mathematical assumptions
- "reclassify_note": explanation if IC or IR proof is absent (string or null)

Paper text:
{text}
"""

RL_PROMPT = """\
Extract these fields from the RL-based FL incentive mechanism paper. Return a single flat JSON object.

TOP-LEVEL fields: "title", "year", "venue", "fl_setup", "num_clients", "notes", "paper_type"

MECHANISM fields (inside "mechanism" object):
- "rl_algorithm": the RL algorithm -- one of:
    "DQN" / "DDPG" / "PPO" / "A3C" / "MAPPO" / "MADDPG" / "SAC" / "TD3" / "other"
    Use "other" for custom algorithms (e.g. MPGD) and explain in notes.
- "state_space": what the agent observes (e.g. "model accuracy P^[t], client costs C_n,
    communication overhead E_n"; describe concisely in 1-2 sentences)
- "action_space": what the agent controls (e.g. "payment amount r_i in [0, B]",
    "binary client selection x_i in {{0,1}}", "data contribution fraction d_n in [0,1]")
- "reward_function": LaTeX or description of reward r_t (copy the formula if available)
- "why_rl_needed": one sentence explaining why closed-form game theory is intractable here
    (e.g. "precision function P(.) is unknown and varies dynamically",
    "client type distribution is non-stationary and unobservable")
- "convergence_claim": convergence guarantee stated in paper (string or null)
- "ic_approximation": any approximate IC or fairness guarantee mentioned (string or null)
- "key_assumptions": JSON array (e.g. ["POMDP Markov property", "discount factor gamma in [0,1]",
    "stationary environment within episodes"])

Paper text:
{text}
"""

VALUATION_PROMPT = """\
Extract these fields from the data valuation / pricing FL paper. Return a single flat JSON object.

This category covers: Shapley approximations WITHOUT IC/IR proof (GTG-Shapley, WT-Shapley,
FedToken, Chen-UCB), gradient-norm scoring, mutual information metrics, reputation systems,
market equilibrium pricing lacking formal IC proof.

TOP-LEVEL fields: "title", "year", "venue", "fl_setup", "num_clients", "notes", "paper_type"

MECHANISM fields (inside "mechanism" object):
- "valuation_method": one of "gradient-norm" / "mutual-information" / "reputation" /
    "shapley-approximation" / "market-equilibrium" / "loss-reduction" / "cosine-similarity" / "other"
- "computational_complexity": asymptotic complexity per round (e.g. "O(N log N)", "O(M log M)",
    "O(N^2)", "O(T*N)" where T=rounds, M=selected clients, N=total clients)
- "ic_claimed": boolean -- does paper claim IC informally (without proof)?
- "valuation_function_latex": LaTeX defining the score or valuation u_n or V(S) (or null)
- "why_not_shapley": one sentence explaining why this is Valuation not Shapley cat 4
    (e.g. "No IC/IR proof provided; truncated Shapley approximation without mechanism design")
- "key_assumptions": JSON array of mathematical assumptions

Paper text:
{text}
"""

NAIVE_PROMPT = """\
Extract these fields from the naive/baseline FL mechanism paper. Return a single flat JSON object.

This category covers: proportional payment (proportional to data size), equal split, FedAvg
(weighted average with no incentive modification), and papers that STUDY free-rider attacks or
failure modes of naive aggregation schemes.

TOP-LEVEL fields: "title", "year", "venue", "fl_setup", "num_clients", "notes", "paper_type"

MECHANISM fields (inside "mechanism" object):
- "rule_type": one of "proportional" / "equal-split" / "fedavg-default" / "reputation-heuristic" / "other"
    proportional = payment proportional to dataset size or CPU contribution
    equal-split = all participants get equal reward
    fedavg-default = FedAvg weighted averaging (M_i/N) with no incentive layer
    reputation-heuristic = reputation-based without formal game theory
- "rule_definition_latex": LaTeX for the aggregation/payment rule (or null)
- "failure_modes": JSON array of failure modes the paper identifies or studies
    (e.g. ["free-riding", "Sybil attack", "collusion", "data poisoning", "disguised free-riding"])
- "benchmark_role": one of:
    "negative-baseline" = used as lower bound (sophisticated mechanisms beat it)
    "attack-target"     = paper studies attacks on this naive scheme
    "performance-ceiling" = surprisingly competitive in some settings
    "cost-floor"        = cheapest mechanism for low-stakes environments
- "key_assumptions": JSON array (or ["no formal assumptions stated"] if paper has none)

COMPARISON block (if paper compares mechanisms or attack strategies):
- "comparison": {{"mechanisms_compared": [...], "comparison_metric": "...",
                 "winning_condition": "...", "key_finding": "..."}}

Paper text:
{text}
"""

EXTRACT_PROMPTS: dict[str, str] = {
    "VCG": VCG_PROMPT,
    "Contract": CONTRACT_PROMPT,
    "Stackelberg": STACKELBERG_PROMPT,
    "Shapley": SHAPLEY_PROMPT,
    "RL": RL_PROMPT,
    "Valuation": VALUATION_PROMPT,
    "Naive": NAIVE_PROMPT,
}
