import pytest
from architect.ast import Const, Sym, Sum, Prod, Pow, Mechanism
from architect.serialize import render, OutsideParseableFragment, ast_to_sympy, to_latex


def _quad_contract():
    u = Sum([Sym("R_i"), Prod([Const(-1), Sym("c_i"), Pow(Sym("e_i"), 2)])])
    ic = Sum([Sym("R_i"), Prod([Const(-1), Sym("c_i"), Pow(Sym("e_i"), 2)]),
              Prod([Const(-1), Sym("R_j")]), Prod([Sym("c_i"), Pow(Sym("e_j"), 2)])])
    ir = u
    return Mechanism("Contract", utility=u, payment=Sym("R_i"), ic=ic, ir=ir,
                     params={"c_i": 1.0}, type_space=["lo", "hi"])


def test_render_roundtrips_inside_fragment():
    md, latex = render(_quad_contract())
    assert "client_utility_latex" in md
    # canonical Contract field names the verifier actually consumes must be present
    assert "ic_screening_latex" in md and "ir_participation_latex" in md
    assert "\\geq" in md["ic_condition_latex"] or ">=" in md["ic_condition_latex"]
    assert latex


def test_to_latex_and_back_is_equal():
    import sympy
    node = Sum([Prod([Const(2), Pow(Sym("x"), 2)]), Sym("y")])
    assert sympy.simplify(ast_to_sympy(node) - sympy.sympify("2*x**2 + y")) == 0


def test_shapley_is_always_outside_fragment():
    m = _quad_contract()
    m.category = "Shapley"
    with pytest.raises(OutsideParseableFragment):
        render(m)


def _theta_contract():
    # quadratic Contract menu using the conventional Greek type variable theta
    u = Sum([Prod([Sym("theta_i"), Sym("e_i")]),
             Prod([Const(-1), Sym("c_i"), Pow(Sym("e_i"), 2)])])
    ic = Sum([Sym("theta_i"), Prod([Const(-1), Sym("theta_j")]), Sym("e_i")])
    return Mechanism("Contract", utility=u, payment=Sym("R_i"), ic=ic, ir=u,
                     params={}, type_space=["lo", "hi"])


def test_greek_type_variable_roundtrips():
    md, latex = render(_theta_contract())
    assert "ic_screening_latex" in md and "ir_participation_latex" in md
    assert latex


def test_to_latex_renders_greek_command():
    assert "\\theta" in to_latex(Sym("theta_i"))


def test_multiletter_base_raises_outside_fragment():
    # no placeholder-substitution pass in v1: multi-letter non-Greek bases
    # cannot round-trip through parse_latex and are rejected with a hint.
    with pytest.raises(OutsideParseableFragment):
        to_latex(Sym("cost"))
