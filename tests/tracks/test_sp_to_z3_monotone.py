import sympy as sp
import pytest
from tracks.track1_z3 import _sp_to_z3


def test_unrecognized_function_still_raises_without_monotone_functions():
    v = sp.Function("v")
    x = sp.Symbol("x", positive=True)
    with pytest.raises(ValueError, match="unsupported SymPy node"):
        _sp_to_z3(v(x), {})


def test_declared_monotone_function_becomes_opaque_real():
    v = sp.Function("v")
    x = sp.Symbol("x", positive=True)
    # Shared cache (as _contract_check_core uses it): distinct arguments get
    # distinct auxiliary reals; a repeated argument reuses the same one.
    cache: dict = {}
    z3_expr = _sp_to_z3(v(x), cache, monotone_functions={"v": "increasing"})
    z3_expr2 = _sp_to_z3(v(x + 1), cache, monotone_functions={"v": "increasing"})
    z3_expr_again = _sp_to_z3(v(x), cache, monotone_functions={"v": "increasing"})
    assert str(z3_expr) != str(z3_expr2)
    assert str(z3_expr) == str(z3_expr_again)


def test_monotone_function_threads_through_add_and_mul():
    v = sp.Function("v")
    x = sp.Symbol("x", positive=True)
    # v appears nested inside Add/Mul -- the recursive calls must forward
    # monotone_functions or this raises.
    expr = 2 * v(x) + v(x + 1) - 3
    z3_expr = _sp_to_z3(expr, {}, monotone_functions={"v": "increasing"})
    assert z3_expr is not None
