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
