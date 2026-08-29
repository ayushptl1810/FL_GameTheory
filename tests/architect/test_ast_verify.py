import sympy
from architect.ast import Const, Sym, Unknown, Sum, Prod, Pow, Func, IndexedFamily
from architect.serialize import ast_to_sympy


def test_bridge_atoms():
    assert ast_to_sympy(Const(2.5)) == sympy.Float(2.5)
    assert ast_to_sympy(Sym("theta")) == sympy.Symbol("theta")
    assert ast_to_sympy(Unknown("a")) == sympy.Symbol("a")


def test_bridge_compound():
    e = ast_to_sympy(Sum([Prod([Sym("p"), Sym("e")]),
                          Prod([Const(-0.5), Sym("c"), Pow(Sym("e"), 2)])]))
    p, e_, c = sympy.symbols("p e c")
    assert sympy.simplify(e - (p * e_ - sympy.Rational(1, 2) * c * e_**2)) == 0


def test_bridge_funcs():
    assert ast_to_sympy(Func("ln", Sym("x"))) == sympy.log(sympy.Symbol("x"))
    assert ast_to_sympy(Func("exp", Sym("x"))) == sympy.exp(sympy.Symbol("x"))


def test_bridge_indexed_family_is_opaque_symbol():
    got = ast_to_sympy(IndexedFamily("R", "i", ["R_1", "R_2"]))
    assert got == sympy.Symbol("R")


# ── verify_from_ast / _classify_ast orchestrator ────────────────────────────
from architect.ast import Mechanism, Sum, Prod, Const, Pow, Func  # noqa: E402
from architect.ast_verify import verify_from_ast, _classify_ast  # noqa: E402


def _stackelberg_effort():
    # U_i = p_i*e_i - 1/2 * c * e_i^2  — the loop's canonical VERIFIED shape
    return Mechanism(
        category="Stackelberg",
        utility=Sum([Prod([Sym("p_i"), Sym("e_i")]),
                     Prod([Const(-0.5), Sym("c"), Pow(Sym("e_i"), 2)])]),
        payment=Sym("p_i"), ic=Sym("e_i"), ir=Sym("e_i"),
        type_space=[], meta={"follower_decision": r"\( e_i \)"})


def test_classify_transcendental():
    m = _stackelberg_effort()
    m.utility = Func("ln", Sym("e_i"))
    assert _classify_ast(m) == 3


def test_classify_default_track1():
    assert _classify_ast(_stackelberg_effort()) == 1


def test_verify_from_ast_reaches_verified_stackelberg():
    r = verify_from_ast(_stackelberg_effort())
    assert r.verdict == "VERIFIED" and r.entry_specific is True
