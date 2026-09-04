from tracks.track1_z3 import _stackelberg_check_core, _opaque_inline
import sympy as sp


def test_two_variable_separable_stationarity_verifies():
    x, y, a, b = sp.symbols("x y a b", positive=True)
    U = a * x - x**2 + b * y - y**2  # max at x=a/2, y=b/2
    mech = {
        "follower_stationarity_system": [
            r"\partial U / \partial x = a - 2 x = 0",
            r"\partial U / \partial y = b - 2 y = 0",
        ],
        "best_response_latex": r"x^* = a/2,\; y^* = b/2",
        "ir_follower_latex": r"U \ge 0",
    }
    res = _stackelberg_check_core(
        U, follower_decision=(x, y), meta=mech, entry_specific=True, paper_id="synthetic"
    )
    assert res is not None and res.verdict == "VERIFIED"


def test_unsolvable_system_fails_closed():
    x, y = sp.symbols("x y")
    U = x * y  # saddle, no interior max
    mech = {"follower_stationarity_system": [r"y = 0", r"x = 0"]}
    res = _stackelberg_check_core(
        U, follower_decision=(x, y), meta=mech, entry_specific=True, paper_id="synthetic"
    )
    assert res is None


def test_component_count_mismatch_fails_closed():
    x, y = sp.symbols("x y")
    mech = {"follower_stationarity_system": [r"x = 0"]}  # 1 eq, 2 vars
    res = _stackelberg_check_core(
        x + y, follower_decision=(x, y), meta=mech, entry_specific=True, paper_id="synthetic"
    )
    assert res is None


def test_missing_system_fails_closed():
    x, y = sp.symbols("x y")
    res = _stackelberg_check_core(
        x + y, follower_decision=(x, y), meta={}, entry_specific=True, paper_id="synthetic"
    )
    assert res is None


def test_br_mismatch_fails_closed():
    x, y, a, b = sp.symbols("x y a b", positive=True)
    U = a * x - x**2 + b * y - y**2
    mech = {
        "follower_stationarity_system": [
            r"\partial U / \partial x = a - 2 x = 0",
            r"\partial U / \partial y = b - 2 y = 0",
        ],
        "best_response_latex": r"x^* = a,\; y^* = b",  # wrong
    }
    res = _stackelberg_check_core(
        U, follower_decision=(x, y), meta=mech, entry_specific=True, paper_id="synthetic"
    )
    assert res is None


def test_unsignable_hessian_fails_closed():
    x, y, k = sp.symbols("x y k")  # k has NO sign assumption
    U = k * x**2 + k * y**2 + x + y
    mech = {"follower_stationarity_system": [r"2 k x + 1 = 0", r"2 k y + 1 = 0"]}
    res = _stackelberg_check_core(
        U, follower_decision=(x, y), meta=mech, entry_specific=True, paper_id="synthetic"
    )
    assert res is None


def test_opaque_inline_scalar_guard_leaves_text_unchanged():
    # "u_3" is a scalar (declared form has no symbol from the call args) ->
    # substituting would drop the operand and produce an unsound encoding.
    out = _opaque_inline(
        {"opaque_function_forms": {"u_3": r"\gamma"}}, r"R_i - u_3(\theta_i) - E"
    )
    assert out == r"R_i - u_3(\theta_i) - E"
