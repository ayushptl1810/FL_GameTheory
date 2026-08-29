"""Bounded 2-client coalition IC for discrete Contract menus (k=n=2 only)."""
from tracks.track1_z3 import verify_coalition_ic_contract

# u(i, r) = R_r - theta_i * e_r
_SAFE = {
    "category": "Contract", "num_types": 2, "type_variable": r"\theta",
    "menu": {"theta_1": 1.0, "theta_2": 2.0, "e_1": 2.0, "e_2": 1.0,
             "R_1": 2.0, "R_2": 1.0},
}

# Hand-check of the swap deviation (types 1 and 2 exchange contracts):
#   truthful = u(1,1) + u(2,2) = (2.0 - 1*2.0) + (1.99 - 2*2.5)
#            = 0.0 + (-3.01) = -3.01
#   swapped  = u(1,2) + u(2,1) = (1.99 - 1*2.5) + (2.0 - 2*2.0)
#            = (-0.51) + (-2.0) = -2.51
#   swapped - truthful = +0.50  > 0  -> types 1 and 2 strictly gain by swapping.
# (The check also catches the both-report-type-1 deviation, gain +1.01;
#  either way the menu is a COUNTEREXAMPLE.)
_BREAKABLE = {**_SAFE,
    "menu": {"theta_1": 1.0, "theta_2": 2.0, "e_1": 2.0, "e_2": 2.5,
             "R_1": 2.0, "R_2": 1.99}}


def test_coalition_safe_menu_verifies():
    res = verify_coalition_ic_contract(_SAFE, k=2)
    assert res.verdict == "VERIFIED"
    assert res.coalition_ic_k == 2


def test_coalition_breakable_menu_is_counterexample():
    res = verify_coalition_ic_contract(_BREAKABLE, k=2)
    assert res.verdict == "COUNTEREXAMPLE"


def test_k_larger_than_menu_is_unsupported():
    assert verify_coalition_ic_contract(_SAFE, k=5).verdict == "UNSUPPORTED"
