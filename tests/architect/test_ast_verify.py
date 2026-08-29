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
