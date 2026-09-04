"""R4 Task 6: monotone-threshold / critical-value DSIC path for VCG."""

from tracks.vcg_dsic import verify_monotone_threshold_dsic


def _entry(**over):
    e = {
        "category": "VCG",
        "mechanism": {
            "allocation_rule_latex": r"greedy by b_i until budget B exhausted",
            "payment_rule_latex": r"p_i = c_i^* \cdot q_i",
            "winner_rule_monotone": {"value": True, "cite": "Thm 2, monotone in b_i"},
            "critical_price_latex": r"c_i^* = \inf\{b_i : i \in W(b_i, b_{-i})\}",
        },
    }
    e["mechanism"].update(over)
    return e


def test_monotone_threshold_verifies():
    res = verify_monotone_threshold_dsic(_entry(), k=3)
    assert res.verdict == "VERIFIED" and res.entry_specific is True


def test_no_cite_is_unknown():
    e = _entry()
    e["mechanism"]["winner_rule_monotone"] = {"value": True}
    assert verify_monotone_threshold_dsic(e, k=3).verdict == "UNKNOWN"


def test_no_critical_price_is_unknown():
    e = _entry()
    del e["mechanism"]["critical_price_latex"]
    assert verify_monotone_threshold_dsic(e, k=3).verdict == "UNKNOWN"


def test_grid_monotonicity_failure_not_verified():
    # anti-monotone toy rule: client wins iff its own bid is BELOW the grid
    # midpoint, so raising its bid moves it winner->loser -> grid check fails.
    e = _entry(
        allocation_rule_latex=r"i wins iff b_i < 1/2 (anti-monotone toy rule)",
    )
    res = verify_monotone_threshold_dsic(e, k=3)
    assert res.verdict != "VERIFIED"
