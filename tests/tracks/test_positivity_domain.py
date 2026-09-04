from tracks.track1_z3 import _positivity_domain


def test_positivity_domain_parses_facts():
    mech = {"positivity_domain": ["rho > 0", "h > 0", "N_0 > 0"]}
    assert set(_positivity_domain(mech)) == {("rho", ">0"), ("h", ">0"), ("N_0", ">0")}


def test_positivity_domain_shorthand_expands():
    mech = {"positivity_domain": ["theta_m, R_m > 0"]}
    assert set(_positivity_domain(mech)) == {("theta_m", ">0"), ("R_m", ">0")}


def test_positivity_domain_absent_is_empty():
    assert _positivity_domain({}) == []


def test_positivity_domain_malformed_is_empty():
    assert _positivity_domain({"positivity_domain": ["not an inequality", 42]}) == []


# --- _is_definitely_positive_sum: integer-power factors (R4) ----------------

import sympy as sp

from tracks.track1_z3 import _is_definitely_positive_sum


def test_positive_sum_accepts_negative_integer_power():
    """rho*h/N_0 (Shannon capacity log argument minus 1) is provably > 0."""
    a, b, c = sp.symbols("a b c")
    assert _is_definitely_positive_sum(a * b / c) is True
    assert _is_definitely_positive_sum(1 + a * b / c - 1) is True


def test_positive_sum_accepts_positive_integer_power():
    a = sp.Symbol("a")
    assert _is_definitely_positive_sum(a**2) is True


def test_positive_sum_rejects_bare_symbol_minus_one():
    """x alone could be < 1, so log(x) stays inadmissible."""
    x = sp.Symbol("x")
    assert _is_definitely_positive_sum(x - 1) is False


def test_positive_sum_rejects_negative_coefficient():
    a, c = sp.symbols("a c")
    assert _is_definitely_positive_sum(-a / c) is False
