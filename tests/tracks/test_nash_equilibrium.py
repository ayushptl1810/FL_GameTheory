import pytest
from tracks.track_nash import _parse_action_payoffs


def test_parse_action_payoffs_builds_full_map():
    raw = {
        "p1=join,p2=join": {"p1": 3.0, "p2": 3.0},
        "p1=join,p2=abstain": {"p1": 1.0, "p2": 0.0},
        "p1=abstain,p2=join": {"p1": 0.0, "p2": 1.0},
        "p1=abstain,p2=abstain": {"p1": 0.0, "p2": 0.0},
    }
    got = _parse_action_payoffs(raw, players=["p1", "p2"], actions=["join", "abstain"])
    assert got[("p1", ("join", "join"))] == 3.0
    assert got[("p2", ("join", "abstain"))] == 0.0


def test_parse_action_payoffs_missing_profile_raises():
    raw = {"p1=join,p2=join": {"p1": 3.0, "p2": 3.0}}  # 3 of 4 profiles missing
    with pytest.raises(ValueError, match="missing"):
        _parse_action_payoffs(raw, players=["p1", "p2"], actions=["join", "abstain"])


def test_parse_action_payoffs_missing_player_payoff_raises():
    raw = {
        "p1=join,p2=join": {"p1": 3.0},  # p2's payoff missing at this profile
        "p1=join,p2=abstain": {"p1": 1.0, "p2": 0.0},
        "p1=abstain,p2=join": {"p1": 0.0, "p2": 1.0},
        "p1=abstain,p2=abstain": {"p1": 0.0, "p2": 0.0},
    }
    with pytest.raises(ValueError, match="missing"):
        _parse_action_payoffs(raw, players=["p1", "p2"], actions=["join", "abstain"])


from tracks.track_nash import (
    _is_best_response, _check_all_best_responses, verify_nash_action_choice,
)

_SIMPLE_PAYOFFS_RAW = {
    "p1=join,p2=join": {"p1": 3.0, "p2": 3.0},
    "p1=join,p2=abstain": {"p1": 1.0, "p2": 0.0},
    "p1=abstain,p2=join": {"p1": 0.0, "p2": 1.0},
    "p1=abstain,p2=abstain": {"p1": 0.0, "p2": 0.0},
}


def test_is_best_response_true_at_mutual_join():
    from tracks.track_nash import _parse_action_payoffs
    payoffs = _parse_action_payoffs(_SIMPLE_PAYOFFS_RAW, ["p1", "p2"], ["join", "abstain"])
    assert _is_best_response(payoffs, ["p1", "p2"], ("join", "join"), ["join", "abstain"], "p1")
    assert _is_best_response(payoffs, ["p1", "p2"], ("join", "join"), ["join", "abstain"], "p2")


def test_is_best_response_false_when_deviation_profitable():
    from tracks.track_nash import _parse_action_payoffs
    payoffs = _parse_action_payoffs(_SIMPLE_PAYOFFS_RAW, ["p1", "p2"], ["join", "abstain"])
    # at (join, abstain), p2 deviating to join raises p2's payoff 0 -> 3: profitable.
    assert not _is_best_response(
        payoffs, ["p1", "p2"], ("join", "abstain"), ["join", "abstain"], "p2"
    )


def test_verify_nash_action_choice_full_pass():
    entry = {
        "paper_id": "x",
        "mechanism": {
            "action_set": ["join", "abstain"],
            "players": ["p1", "p2"],
            "action_payoffs": _SIMPLE_PAYOFFS_RAW,
            "stated_equilibrium_profile": {"p1": "join", "p2": "join"},
        },
    }
    r = verify_nash_action_choice(entry)
    assert r.verdict == "VERIFIED"
    assert r.entry_specific is True
    assert r.track == 6


def test_verify_nash_action_choice_counterexample_on_profitable_deviation():
    entry = {
        "paper_id": "x",
        "mechanism": {
            "action_set": ["join", "abstain"],
            "players": ["p1", "p2"],
            "action_payoffs": _SIMPLE_PAYOFFS_RAW,
            "stated_equilibrium_profile": {"p1": "join", "p2": "abstain"},  # not an eq.
        },
    }
    r = verify_nash_action_choice(entry)
    assert r.verdict == "COUNTEREXAMPLE"


def test_verify_nash_action_choice_missing_fields_is_manual():
    entry = {"paper_id": "x", "mechanism": {}}
    r = verify_nash_action_choice(entry)
    assert r.verdict == "MANUAL"
