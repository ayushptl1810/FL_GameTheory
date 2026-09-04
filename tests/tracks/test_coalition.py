import math
from itertools import combinations
import pytest
from tracks.track_coalition import _parse_coalition_values, _shapley_from_values, _tier_b_numeric_core


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


def test_tier_b_convex_game_core_nonempty():
    # convex (supermodular) game -> Shapley value is in the core
    values = {
        frozenset(): 0.0, frozenset({1}): 1.0, frozenset({2}): 1.0,
        frozenset({3}): 1.0, frozenset({1, 2}): 4.0, frozenset({1, 3}): 4.0,
        frozenset({2, 3}): 4.0, frozenset({1, 2, 3}): 10.0,
    }
    core_ok, ir_ok, conds = _tier_b_numeric_core(values, n=3, stated_payments=None)
    assert core_ok and ir_ok
    assert any("core" in c.lower() for c in conds)


def test_tier_b_empty_core_fails():
    # 3-player majority game: v(S)=1 for any |S|>=2, v(N)=1, singletons 0.
    # Shapley = (1/3,1/3,1/3); for S={1,2}: 2/3 < v(S)=1 -> core violated.
    values = {
        frozenset(): 0.0, frozenset({1}): 0.0, frozenset({2}): 0.0,
        frozenset({3}): 0.0, frozenset({1, 2}): 1.0, frozenset({1, 3}): 1.0,
        frozenset({2, 3}): 1.0, frozenset({1, 2, 3}): 1.0,
    }
    core_ok, ir_ok, _ = _tier_b_numeric_core(values, n=3, stated_payments=None)
    assert not core_ok
    assert ir_ok  # phi_i = 1/3 >= v({i}) = 0


def test_tier_b_stated_payment_mismatch_fails_core():
    values = {
        frozenset(): 0.0, frozenset({1}): 1.0, frozenset({2}): 1.0,
        frozenset({1, 2}): 4.0,
    }
    core_ok, _, _ = _tier_b_numeric_core(values, n=2, stated_payments={1: 2.0, 2: 99.0})
    assert not core_ok


from tracks.track_coalition import verify_coalition, _tier_a_symbolic_identity

_STD_SHAPLEY_LATEX = (
    r"\phi_i = \sum_{S \subseteq N \setminus \{i\}} "
    r"\frac{|S|!(n-|S|-1)!}{n!} \left( v(S \cup \{i\}) - v(S) \right)"
)


def test_tier_a_accepts_standard_formula():
    ok, _ = _tier_a_symbolic_identity(_STD_SHAPLEY_LATEX, n=3)
    assert ok


def test_tier_a_rejects_binom_normalized_approximation():
    approx = r"\phi_j = K \sum_{S} \frac{U(S \cup \{j\}) - U(S)}{\binom{n-1}{|S|}}"
    ok, detail = _tier_a_symbolic_identity(approx, n=3)
    assert not ok
    assert "binom" in detail.lower() or "not" in detail.lower()


def test_verify_coalition_no_formula_is_manual():
    entry = {"mechanism": {"shapley_formula_latex": None}, "paper_id": "x"}
    r = verify_coalition(entry)
    assert r.verdict == "MANUAL"
    assert "no Shapley formula" in r.notes


def test_verify_coalition_tier_a_only_is_manual():
    entry = {
        "paper_id": "x",
        "mechanism": {"shapley_formula_latex": _STD_SHAPLEY_LATEX, "coalition_n": 3},
    }
    r = verify_coalition(entry)
    assert r.verdict == "MANUAL"
    assert "no numeric v(S)" in r.notes
    assert r.entry_specific is False


def test_verify_coalition_full_pass_is_verified():
    entry = {
        "paper_id": "x",
        "mechanism": {
            "shapley_formula_latex": _STD_SHAPLEY_LATEX,
            "coalition_n": 3,
            "coalition_values": {
                "": 0.0, "1": 1.0, "2": 1.0, "3": 1.0,
                "1,2": 4.0, "1,3": 4.0, "2,3": 4.0, "1,2,3": 10.0,
            },
        },
    }
    r = verify_coalition(entry)
    assert r.verdict == "VERIFIED"
    assert r.entry_specific is True
    assert r.track == 5


def test_verify_coalition_core_violation_is_counterexample():
    entry = {
        "paper_id": "x",
        "mechanism": {
            "shapley_formula_latex": _STD_SHAPLEY_LATEX,
            "coalition_n": 3,
            "coalition_values": {
                "": 0.0, "1": 0.0, "2": 0.0, "3": 0.0,
                "1,2": 1.0, "1,3": 1.0, "2,3": 1.0, "1,2,3": 1.0,
            },
        },
    }
    r = verify_coalition(entry)
    assert r.verdict == "COUNTEREXAMPLE"


def test_verify_coalition_k_over_3_is_manual():
    entry = {
        "paper_id": "x",
        "mechanism": {"shapley_formula_latex": _STD_SHAPLEY_LATEX, "coalition_n": 5},
    }
    r = verify_coalition(entry)
    assert r.verdict == "MANUAL"
    assert "k > 3" in r.notes or "coalition size" in r.notes
