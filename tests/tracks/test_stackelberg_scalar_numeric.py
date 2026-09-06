"""Scalar numeric-root fallback in _stackelberg_check_core (R13).

When a follower FOC is a single transcendental/implicit equation SymPy's
exact solver cannot close, the scalar branch falls back to R11's multi-start
fail-closed SciPy solver (reused verbatim with a 1-element decision list).
"""
import sympy as sp
from tracks.track1_z3 import _stackelberg_check_core


def test_transcendental_foc_falls_back_to_numeric_root():
    e = sp.Symbol("e", positive=True)
    # FOC mixes a rational term (1/(e+1)), a linear term and exp(-e):
    #   sp.solve raises NotImplementedError("multiple generators [e, exp(e)]")
    # so the exact path yields nothing and the numeric fallback runs. The
    # unique real stationary point is e* ~= 3.8376, where U'' < 0 (a max) and
    # U(e*) ~= 2.039 > 0, so IR passes and the entry verifies.
    U = -e**2 / sp.Integer(40) - e / sp.Integer(5) + 2 * sp.log(e + 1) + sp.exp(-e)
    res = _stackelberg_check_core(
        U, follower_decision=e, meta={}, entry_specific=True, paper_id="synthetic",
    )
    assert res is not None
    assert res.verdict == "VERIFIED"


def test_free_parameter_left_unpinned_fails_closed():
    e, a = sp.symbols("e a", positive=True)
    # Same transcendental shape but with an un-pinned parameter `a`: the
    # numeric solver has nothing to evaluate and returns None -> no verdict.
    U = -a * e**2 - e / sp.Integer(5) + 2 * sp.log(e + 1) + sp.exp(-e)
    res = _stackelberg_check_core(
        U, follower_decision=e, meta={}, entry_specific=True, paper_id="synthetic",
    )
    assert res is None


def test_closed_form_foc_still_uses_exact_path():
    e = sp.Symbol("e", positive=True)
    # Purely rational FOC -> sp.solve returns a closed form; the numeric
    # fallback must not be reached (regression guard on the branch order).
    U = 2 * sp.log(e + 1) - e**2 / sp.Integer(10) - e / sp.Integer(3)
    res = _stackelberg_check_core(
        U, follower_decision=e, meta={}, entry_specific=True, paper_id="synthetic",
    )
    assert res is not None
    assert res.verdict == "VERIFIED"
