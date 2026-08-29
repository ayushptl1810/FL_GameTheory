"""Trivial control: emit the textbook follower-effort mechanism for every input.

No upstream repo -- this is a deliberate lower-bound baseline, not a port.
"""
from verifier import verify

FOLLOWER_EFFORT = {
    "category": "Stackelberg",
    "follower_utility_latex": r"U_i = p_i e_i - \tfrac{1}{2} c e_i^2",
    "follower_decision_latex": r"\( e_i \)",
    "best_response_latex": r"e_i^* = p_i / c",
}


def run_baseline(name, bench):
    res = verify(dict(FOLLOWER_EFFORT))
    return {"name": bench["name"], "method": "control", "mode": "n/a",
            "status": res.verdict, "iterations": 0, "solver_calls": 1,
            "wall_clock": 0.0,
            "ic_regret": 0.0 if res.verdict == "VERIFIED" else None,
            "family_match": bench["expected_family"] == "Stackelberg"}
