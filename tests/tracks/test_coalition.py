import math
from itertools import combinations
import pytest
from tracks.track_coalition import _parse_coalition_values, _shapley_from_values


def _all_subsets(n):
    for k in range(n + 1):
        for c in combinations(range(1, n + 1), k):
            yield c


def test_parse_coalition_values_builds_frozenset_map():
    raw = {"": 0.0, "1": 1.0, "2": 2.0, "1,2": 4.0}
    got = _parse_coalition_values(raw, n=2)
    assert got[frozenset()] == 0.0
    assert got[frozenset({1})] == 1.0
    assert got[frozenset({1, 2})] == 4.0


def test_parse_coalition_values_missing_subset_raises():
    with pytest.raises(ValueError, match="missing"):
        _parse_coalition_values({"": 0.0, "1": 1.0, "1,2": 4.0}, n=2)  # no "2"


def test_parse_coalition_values_rejects_n_over_3():
    with pytest.raises(ValueError, match="n <= 3"):
        _parse_coalition_values({}, n=4)


def test_parse_coalition_values_rejects_non_numeric():
    with pytest.raises(ValueError, match="numeric"):
        _parse_coalition_values({"": 0.0, "1": "x", "2": 2.0, "1,2": 4.0}, n=2)


def test_shapley_from_values_glove_game():
    # 3-player: players 1,2 hold a left glove, player 3 a right glove.
    # v(S)=1 iff S contains 3 and at least one of {1,2}; else 0.
    def v(s):
        return 1.0 if (3 in s and ({1, 2} & s)) else 0.0
    values = {frozenset(c): v(set(c)) for c in _all_subsets(3)}
    phi = _shapley_from_values(values, n=3)
    assert math.isclose(phi[1], 1 / 6, abs_tol=1e-9)
    assert math.isclose(phi[2], 1 / 6, abs_tol=1e-9)
    assert math.isclose(phi[3], 2 / 3, abs_tol=1e-9)
    assert math.isclose(sum(phi.values()), 1.0, abs_tol=1e-9)  # efficiency
