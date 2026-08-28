import pytest

from architect.ast import Const, Sym, Unknown, Sum, Prod, Pow, Mechanism
from architect.synthesize import synthesize, Constraints, collect_unknowns


def test_collect_unknowns():
    node = Sum([Unknown("a"), Prod([Unknown("b"), Sym("x")])])
    assert set(collect_unknowns(node)) == {"a", "b"}


def test_synthesize_finds_trivial_params():
    payment = Unknown("a")
    ir = Sum([Unknown("a"), Prod([Const(-1), Sym("theta")])])
    ic = Sum([Pow(Sym("theta"), 2)])  # always >= 0
    m = Mechanism("Contract", utility=ir, payment=payment, ic=ic, ir=ir,
                  params={}, type_space=["theta"])
    c = Constraints(ic=ic, ir=ir, budget_lhs=None, budget_rhs=None,
                    type_space=["theta"], param_bounds={"a": (0.0, 10.0)})
    out = synthesize(m, c)
    assert out != "UNSAT"
    assert not collect_unknowns(out.payment)


def test_synthesize_rejects_too_many_unknowns():
    payment = Sum([Unknown(x) for x in "abcdefg"])
    m = Mechanism("Contract", utility=Sym("u"), payment=payment,
                  ic=Sum([Const(1)]), ir=Sum([Const(1)]), params={}, type_space=["t"])
    c = Constraints(ic=Sum([Const(1)]), ir=Sum([Const(1)]), budget_lhs=None,
                    budget_rhs=None, type_space=["t"], param_bounds={})
    assert synthesize(m, c) == "UNSAT"


def test_synthesize_rejects_non_integer_exponent():
    # ic contains Pow(x, 1/2): must LOUD-FAIL, not silently truncate to RealVal(1)
    payment = Unknown("a")
    ir = Sum([Unknown("a")])
    frac = Pow(Sym("x"), 1)
    frac.exp = 0.5  # fractional exponent ast_to_sympy will preserve
    ic = Sum([frac])
    m = Mechanism("Contract", utility=ir, payment=payment, ic=ic, ir=ir,
                  params={}, type_space=["x"])
    c = Constraints(ic=ic, ir=ir, budget_lhs=None, budget_rhs=None,
                    type_space=["x"], param_bounds={"a": (0.0, 10.0)})
    with pytest.raises(ValueError):
        synthesize(m, c)
