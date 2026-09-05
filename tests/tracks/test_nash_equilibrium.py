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
