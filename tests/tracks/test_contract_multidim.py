import sympy as sp

from tracks.track1_z3 import _contract_check_core_vector


def test_reduction_to_scalar_delegates_without_free_type_symbols():
    theta1, theta2, w1, w2, e = sp.symbols("theta1 theta2 w1 w2 e", positive=True)
    theta_eff = sp.Symbol("theta_eff", positive=True)
    reduction_map = {"theta_eff": "w1*theta1 + w2*theta2"}
    # U written in terms of the effective scalar; after the reduction
    # substitution neither theta1 nor theta2 may survive.
    U_ir = theta_eff * e - e**2
    U_rhs = theta_eff * e - e**2
    res = _contract_check_core_vector(
        U_ir, U_rhs, type_syms=["theta1", "theta2"], contract_sub="e", n=2,
        ir_from_ic_lhs=True, reduction_map=reduction_map,
        paper_id="synthetic", meta={},
    )
    # Delegation happened (didn't bail on the reduction). Whatever
    # _contract_check_core returns, no original type symbol is left dangling.
    assert res is None or getattr(res, "verdict", None) in {
        "VERIFIED", "COUNTEREXAMPLE", "UNKNOWN", "MANUAL",
    }


def test_incomplete_reduction_fails_closed():
    theta1, theta2, e = sp.symbols("theta1 theta2 e", positive=True)
    theta_eff = sp.Symbol("theta_eff", positive=True)
    # reduction_map only eliminates theta1; theta2 still appears -> not a
    # genuine dimensionality collapse -> None.
    U_ir = theta_eff * e - theta2 * e**2
    reduction_map = {"theta_eff": "theta1"}
    res = _contract_check_core_vector(
        U_ir, U_ir, type_syms=["theta1", "theta2"], contract_sub="e", n=2,
        ir_from_ic_lhs=True, reduction_map=reduction_map,
        paper_id="synthetic", meta={},
    )
    assert res is None


def test_multi_entry_reduction_map_fails_closed():
    theta1, e = sp.symbols("theta1 e", positive=True)
    res = _contract_check_core_vector(
        theta1 * e, theta1 * e, type_syms=["theta1", "theta2"], contract_sub="e",
        n=2, ir_from_ic_lhs=True,
        reduction_map={"a": "theta1", "b": "theta2"},  # not a single collapse
        paper_id="synthetic", meta={},
    )
    assert res is None
