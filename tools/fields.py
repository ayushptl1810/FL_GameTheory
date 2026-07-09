"""Shared field definitions used by extract, normalize, and validate."""

from __future__ import annotations

RAG_CATEGORIES: frozenset[str] = frozenset({"RL", "Valuation", "Naive"})

GOLD_LATEX_FIELDS: dict[str, list[str]] = {
    "VCG": [
        "allocation_rule_latex", "payment_rule_latex", "client_utility_latex",
        "ic_condition_latex", "ir_condition_latex", "objective_latex",
    ],
    "Contract": [
        "client_utility_latex", "cost_function_latex", "contract_menu_latex",
        "ic_screening_latex", "ir_participation_latex", "server_objective_latex",
    ],
    "Stackelberg": [
        "leader_objective_latex", "follower_utility_latex",
        "follower_foc_latex", "best_response_latex", "ir_follower_latex",
    ],
    "Shapley": [
        "characteristic_function_latex", "shapley_formula_latex",
        "ic_condition_latex", "ir_condition_latex",
    ],
}

MECHANISM_FIELDS: dict[str, list[str]] = {
    "VCG": [
        "auction_type", "bid_space", "allocation_rule_latex", "payment_rule_latex",
        "client_utility_latex", "ic_type", "ic_condition_latex", "ir_condition_latex",
        "objective_latex", "budget_balance_type", "budget_balance_latex", "key_assumptions",
    ],
    "Contract": [
        "num_types", "type_variable", "type_distribution", "information_structure",
        "cost_function_form", "multidimensional_type", "client_utility_latex",
        "cost_function_latex", "contract_menu_latex", "ic_screening_latex",
        "ir_participation_latex", "server_objective_latex", "key_assumptions",
    ],
    "Stackelberg": [
        "leader", "follower", "leader_decision", "follower_decision",
        "equilibrium_existence", "equilibrium_uniqueness", "leader_objective_latex",
        "follower_utility_latex", "follower_foc_latex", "best_response_latex",
        "ir_follower_latex", "key_assumptions",
    ],
    "Shapley": [
        "valuation_metric", "exact_or_approx", "ic_proof_present", "ir_proof_present",
        "characteristic_function_latex", "shapley_formula_latex",
        "ic_condition_latex", "ir_condition_latex", "axioms_satisfied", "key_assumptions",
    ],
    "RL": [
        "rl_algorithm", "state_space", "action_space", "reward_function",
        "why_rl_needed", "convergence_claim", "ic_approximation", "key_assumptions",
    ],
    "Valuation": [
        "valuation_method", "computational_complexity", "ic_claimed",
        "valuation_function_latex", "why_not_shapley", "key_assumptions",
    ],
    "Naive": [
        "rule_type", "rule_definition_latex", "failure_modes", "benchmark_role", "key_assumptions",
    ],
}


def is_filled(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and value.strip() in ("", "null", "N/A", "unspecified", "TBD"):
        return False
    return True
