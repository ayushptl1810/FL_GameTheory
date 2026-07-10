#!/usr/bin/env python3
"""
Normalize corpus entries in-place: coerce enum fields, fill required nulls,
strip disallowed fields, then rebuild corpus.json.

Usage:
    python schema/normalize.py entries/ --merge corpus.json
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ── Enum coercions ────────────────────────────────────────────────────────────

_FL_SETUP_KEYWORDS = [
    ("vertical", "vertical"),
    ("hierarchical", "hierarchical"),
    ("split-learning", "split"),
    ("split learning", "split"),
    ("split", "split"),
    ("cross-silo", "cross-silo"),
    ("cross silo", "cross-silo"),
    ("organization", "cross-silo"),
    ("institution", "cross-silo"),
    ("hospital", "cross-silo"),
    ("company", "cross-silo"),
    ("enterprise", "cross-silo"),
    ("silo", "cross-silo"),
    ("cross-device", "cross-device"),
    ("cross device", "cross-device"),
    ("mobile device", "cross-device"),
    ("mobile user", "cross-device"),
    ("iot", "cross-device"),
    ("internet of things", "cross-device"),
    ("vehicle", "cross-device"),
    ("uav", "cross-device"),
    ("sensor", "cross-device"),
    ("edge device", "cross-device"),
    ("edge server", "cross-device"),
    ("mobile edge", "cross-device"),
    ("mobile", "cross-device"),
]

_FL_SETUP_VALID = {"cross-device", "cross-silo", "vertical", "hierarchical", "split", "unspecified"}


def _coerce_fl_setup(value: object) -> str:
    if value in _FL_SETUP_VALID:
        return value  # type: ignore[return-value]
    if not value:
        return "unspecified"
    lower = str(value).lower()
    for keyword, mapped in _FL_SETUP_KEYWORDS:
        if keyword in lower:
            return mapped
    return "unspecified"


_NUM_CLIENTS_VALID = {"finite-small", "finite-large", "continuous", "unspecified"}


def _coerce_num_clients(value: object) -> str:
    if value in _NUM_CLIENTS_VALID:
        return value  # type: ignore[return-value]
    if value is None:
        return "unspecified"
    s = str(value).lower().strip()
    if re.match(r"^[a-z]$", s):
        return "finite-large"
    m = re.search(r"\d+", s)
    if m:
        n = int(m.group())
        return "finite-small" if n < 20 else "finite-large"
    if "continuum" in s or "infinite" in s:
        return "continuous"
    return "unspecified"


_COST_FORM_VALID = {"linear", "quadratic", "convex-general", "other"}


def _coerce_cost_form(value: object) -> str:
    if value in _COST_FORM_VALID:
        return value  # type: ignore[return-value]
    if not value:
        return "other"
    lower = str(value).lower()
    if "quadratic" in lower:
        return "quadratic"
    if "linear" in lower:
        return "linear"
    if "convex" in lower:
        return "convex-general"
    return "other"


_IC_TYPE_VALID = {"dominant-strategy", "BNE", "ex-post", "approximate"}


def _coerce_ic_type(value: object) -> str:
    if value in _IC_TYPE_VALID:
        return value  # type: ignore[return-value]
    if not value:
        return "BNE"
    lower = str(value).lower()
    if "dominant" in lower:
        return "dominant-strategy"
    if "ex-post" in lower or "ex post" in lower:
        return "ex-post"
    if "approx" in lower:
        return "approximate"
    return "BNE"


_VALUATION_METHOD_VALID = {
    "gradient-norm", "mutual-information", "reputation",
    "fedtoken", "leave-one-out", "market-equilibrium",
    "bandit", "data-market", "shapley-approximation", "other",
}


def _coerce_valuation_method(value: object) -> str:
    if value in _VALUATION_METHOD_VALID:
        return value  # type: ignore[return-value]
    if not value:
        return "other"
    lower = str(value).lower()
    if "shapley" in lower:
        return "shapley-approximation"
    if "gradient" in lower:
        return "gradient-norm"
    if "mutual" in lower or "information" in lower:
        return "mutual-information"
    if "reputation" in lower:
        return "reputation"
    if "bandit" in lower:
        return "bandit"
    if "market" in lower:
        return "market-equilibrium"
    if "leave" in lower:
        return "leave-one-out"
    return "other"


_APP_DOMAIN_VALID = {
    "IoT", "UAV", "healthcare", "blockchain", "metaverse",
    "industrial", "vehicular", "SDN", "medical", "crowdsourcing",
    "edge", "mobile", "other",
}


def _coerce_app_domain(value: object) -> str:
    if value in _APP_DOMAIN_VALID:
        return value  # type: ignore[return-value]
    if not value:
        return "other"
    lower = str(value).lower()
    for v in sorted(_APP_DOMAIN_VALID, key=len, reverse=True):
        if v.lower() in lower:
            return v
    return "other"


def _sanitize_paper_id(pid: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", pid)


# ── Allowed fields per category ───────────────────────────────────────────────

_ALLOWED_BY_CATEGORY: dict[str, set[str]] = {
    "VCG": {
        "auction_type", "bid_space", "allocation_rule_latex", "payment_rule_latex",
        "client_utility_latex", "valuation_function_latex", "cost_function_latex",
        "ic_condition_latex", "ic_type", "ir_condition_latex", "objective_latex",
        "budget_balance_latex", "budget_balance_type", "multi_round",
        "privacy_mechanism", "non_iid_handling", "key_assumptions",
    },
    "Contract": {
        "num_types", "type_variable", "type_distribution", "client_utility_latex",
        "cost_function_form", "cost_function_latex", "contract_menu_latex",
        "ic_screening_latex", "ir_participation_latex", "server_objective_latex",
        "information_structure", "spence_mirrlees", "multidimensional_type",
        "dynamic_contract", "key_assumptions",
    },
    "Stackelberg": {
        "leader", "follower", "leader_decision", "follower_decision",
        "leader_objective_latex", "follower_utility_latex", "cost_function_latex",
        "follower_foc_latex", "best_response_latex", "ir_follower_latex",
        "equilibrium_existence", "equilibrium_uniqueness", "hierarchical_levels",
        "multi_leader", "drl_solver", "key_assumptions",
    },
    "Shapley": {
        "characteristic_function_latex", "shapley_formula_latex", "valuation_metric",
        "exact_or_approx", "computational_complexity", "ic_proof_present",
        "ir_proof_present", "ic_condition_latex", "ir_condition_latex",
        "payment_mechanism_latex", "axioms_satisfied", "key_assumptions",
    },
    "RL": {
        "rl_algorithm", "state_space", "action_space", "reward_function",
        "convergence_claim", "ic_approximation", "ir_approximation",
        "why_rl_needed", "key_assumptions",
    },
    "Valuation": {
        "valuation_method", "valuation_formula_latex", "computational_complexity",
        "ic_claimed", "fairness_properties", "why_not_shapley", "key_assumptions",
    },
    "Naive": {
        "rule_type", "rule_definition_latex", "failure_modes",
        "when_it_works", "benchmark_role", "key_assumptions",
    },
}


# ── Main normalization ────────────────────────────────────────────────────────

_RULE_TYPE_MAP = {
    "fedavg-default": "fedavg-no-incentive",
    "fedavg": "fedavg-no-incentive",
    "fed-avg": "fedavg-no-incentive",
}
_RULE_TYPE_VALID = {"proportional", "equal-split", "size-based", "accuracy-based", "fedavg-no-incentive", "other"}
_BENCHMARK_ROLE_VALID = {"lower-bound", "strawman", "surprisingly-competitive", "attack-target"}
_RL_ALGO_VALID = {"DQN", "PPO", "DDPG", "MARL", "MAB", "actor-critic", "Q-learning", "other"}
_CONV_CLAIM_VALID = {"theoretical", "empirical", "none"}
_INFO_STRUCT_VALID = {"hidden-type", "hidden-action", "both"}


def normalize_entry(e: dict) -> dict:
    e["paper_id"] = _sanitize_paper_id(e.get("paper_id", ""))
    e["fl_setup"] = _coerce_fl_setup(e.get("fl_setup"))
    e["num_clients"] = _coerce_num_clients(e.get("num_clients"))

    # Year out of range → try to recover from paper_id
    year = e.get("year")
    if not isinstance(year, int) or not (2017 <= year <= 2030):
        m_yr = re.search(r"(20[1-2]\d)", e.get("paper_id", ""))
        if m_yr:
            e["year"] = int(m_yr.group(1))

    cat = e.get("category", "")
    m = e.get("mechanism") or {}

    # Strip fields not in this category's schema
    allowed = _ALLOWED_BY_CATEGORY.get(cat, set())
    for key in list(m.keys()):
        if key not in allowed:
            del m[key]

    # Null key_assumptions → empty list (schema no longer requires minItems:1)
    if m.get("key_assumptions") is None:
        m["key_assumptions"] = []

    if cat == "VCG":
        if not m.get("budget_balance_type"):
            m["budget_balance_type"] = "not-stated"
        if "ic_type" in m:
            m["ic_type"] = _coerce_ic_type(m["ic_type"])

    if cat == "Contract":
        nt = m.get("num_types")
        if nt is None:
            m["num_types"] = "continuous"
        elif isinstance(nt, str) and nt != "continuous":
            try:
                m["num_types"] = int(nt)
            except (ValueError, TypeError):
                m["num_types"] = "continuous"
        if not m.get("type_distribution"):
            m["type_distribution"] = "not-stated"
        if not m.get("type_variable"):
            m["type_variable"] = "unspecified"
        cf = m.get("cost_function_form")
        if cf not in _COST_FORM_VALID:
            m["cost_function_form"] = _coerce_cost_form(cf)
        if m.get("information_structure") not in _INFO_STRUCT_VALID:
            m["information_structure"] = "hidden-type"  # most common default

    if cat == "Stackelberg":
        for field in ("leader_decision", "follower_decision"):
            if not m.get(field):
                m[field] = "unspecified"
        if m.get("equilibrium_existence") is None:
            m["equilibrium_existence"] = False

    # ic_approximation / ir_approximation must be bool or null, not a string
    for bool_field in ("ic_approximation", "ir_approximation"):
        v = m.get(bool_field)
        if isinstance(v, str):
            m[bool_field] = v.lower() not in ("false", "no", "0", "")

    if cat == "RL":
        algo = m.get("rl_algorithm")
        if algo not in _RL_ALGO_VALID:
            lower = (algo or "").lower()
            if "drl" in lower or "deep" in lower:
                m["rl_algorithm"] = "other"
            elif "marl" in lower or "multi" in lower:
                m["rl_algorithm"] = "MARL"
            elif "dqn" in lower:
                m["rl_algorithm"] = "DQN"
            elif "ppo" in lower:
                m["rl_algorithm"] = "PPO"
            elif "ddpg" in lower:
                m["rl_algorithm"] = "DDPG"
            elif "actor" in lower:
                m["rl_algorithm"] = "actor-critic"
            elif "mab" in lower or "bandit" in lower:
                m["rl_algorithm"] = "MAB"
            else:
                m["rl_algorithm"] = "other"
        if m.get("convergence_claim") not in _CONV_CLAIM_VALID:
            m["convergence_claim"] = "none"

    if cat == "Valuation":
        vm = m.get("valuation_method")
        if vm not in _VALUATION_METHOD_VALID:
            m["valuation_method"] = _coerce_valuation_method(vm)

    if cat == "Naive":
        rt = m.get("rule_type")
        if rt in _RULE_TYPE_MAP:
            m["rule_type"] = _RULE_TYPE_MAP[rt]
        elif rt not in _RULE_TYPE_VALID:
            m["rule_type"] = "other"
        br = m.get("benchmark_role")
        if br not in _BENCHMARK_ROLE_VALID:
            m["benchmark_role"] = "strawman"
        if m.get("failure_modes") is None:
            m["failure_modes"] = []

    app = e.get("application")
    if isinstance(app, dict) and "domain" in app:
        if app["domain"] not in _APP_DOMAIN_VALID:
            app["domain"] = _coerce_app_domain(app["domain"])

    e["mechanism"] = m
    return e


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize corpus entry files in-place")
    parser.add_argument("entries_dir", type=Path)
    parser.add_argument("--merge", type=Path, default=None)
    parser.add_argument("--exclude-stubs", action="store_true",
                        help="Exclude entries with 'deduplicated' in notes from --merge output")
    args = parser.parse_args()

    if not args.entries_dir.is_dir():
        sys.exit(f"Not a directory: {args.entries_dir}")

    files = sorted(args.entries_dir.glob("*.json"))
    fixed = 0
    all_normalized = []

    for f in files:
        original = f.read_text()
        raw = json.loads(original)
        normed = normalize_entry(raw)
        out = json.dumps(normed, indent=2, ensure_ascii=False)
        if out != original:
            f.write_text(out)
            fixed += 1
        notes = normed.get("notes") or ""
        if args.exclude_stubs and "deduplicated" in notes:
            continue
        all_normalized.append(normed)

    print(f"Normalized {fixed}/{len(files)} entry files.")

    if args.merge:
        args.merge.write_text(json.dumps(all_normalized, indent=2, ensure_ascii=False))
        print(f"[merge] wrote {len(all_normalized)} entries -> {args.merge}")


if __name__ == "__main__":
    main()
