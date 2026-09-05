import sympy as sp

from tracks.track1_z3 import _solve_stationarity_system


def test_rational_term_system_returns_symbolic_when_sympy_can_close_it():
    x, y, mu, p = sp.symbols("x y mu p", positive=True)
    # mu/(1+x) - p = 0  and  mu/(1+y) - 2p = 0 -- SymPy solves the *system*
    # exactly (x = mu/p - 1, y = mu/(2p) - 1); parameter symbols mu, p are
    # not decision symbols, so the solution is accepted.
    mech = {
        "follower_stationarity_system": [
            r"\partial P / \partial x = \frac{mu}{1+x} - p = 0",
            r"\partial P / \partial y = \frac{mu}{1+y} - 2 p = 0",
        ]
    }
    result = _solve_stationarity_system(mech, [x, y])
    assert result is not None
    sol, method = result
    assert method == "symbolic"
    assert set(sol) == {x, y}


def test_numeric_fallback_solves_a_system_sympy_cannot():
    x, y = sp.symbols("x y", positive=True)
    # x^2 + log(1+x) mixes polynomial and transcendental generators -> SymPy's
    # exact solver raises "no algorithms" -> numeric fallback runs. Each
    # equation is decoupled with a single positive root, so all three fixed
    # start points converge to the same point.
    mech = {
        "follower_stationarity_system": [
            r"x^2 + \log(1 + x) - 5 = 0",
            r"y^2 + \log(1 + y) - 12 = 0",
        ]
    }
    result = _solve_stationarity_system(mech, [x, y])
    assert result is not None
    sol, method = result
    assert method == "numeric:fsolve"
    # residual at the reported root is ~0
    rx = float(sol[x]) ** 2 + float(sp.log(1 + float(sol[x]))) - 5
    ry = float(sol[y]) ** 2 + float(sp.log(1 + float(sol[y]))) - 12
    assert abs(rx) < 1e-6 and abs(ry) < 1e-6


def test_multiple_symbolic_solutions_fail_closed():
    # Two decoupled quadratics -> SymPy finds 4 solutions -> genuine multi-root
    # ambiguity -> fail closed, no numeric guess.
    x, y = sp.symbols("x y")
    mech = {"follower_stationarity_system": [r"x^2 - 4 = 0", r"y^2 - 9 = 0"]}
    assert _solve_stationarity_system(mech, [x, y]) is None


def test_numeric_fallback_bails_on_unpinned_parameter():
    # SymPy cannot solve x^2 + log(1+x) - k exactly, and a free parameter
    # symbol (k) remains -> nothing to evaluate numerically -> fail closed.
    x, y, k = sp.symbols("x y k", positive=True)
    mech = {
        "follower_stationarity_system": [
            r"x^2 + \log(1 + x) - k = 0",
            r"y^2 + \log(1 + y) - 12 = 0",
        ]
    }
    assert _solve_stationarity_system(mech, [x, y]) is None
