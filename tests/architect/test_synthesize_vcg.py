"""Task 10: Synthesis mode sets the VCG allocation AST node (no meta LaTeX)."""
from architect.ast import (
    Const, Sym, Unknown, Sum, Prod, Mechanism,
    AllocHighest, AllocTopK, AllocWeightedWelfare,
)
from architect.synthesize import synthesize, Constraints, collect_unknowns
from architect.ast_verify import verify_from_ast

_ALLOC = (AllocHighest, AllocTopK, AllocWeightedWelfare)


def _client_utility():
    # v_i * x_i - p_i, with x_i folded to 1 (single-item winner)
    return Sum([Sym("v_i"), Prod([Const(-1), Sym("p_i")])])


def _vcg_mechanism(payment):
    u = _client_utility()
    return Mechanism(
        category="VCG",
        utility=u,
        payment=payment,
        ic=u,
        ir=u,
        type_space=["v_i"],
        meta={"num_clients": 2},
    )


def _constraints(m):
    return Constraints(ic=m.ic, ir=m.ir, budget_lhs=None, budget_rhs=None,
                       type_space=m.type_space, param_bounds={})


def test_synthesize_vcg_sets_alloc_node_and_verifies():
    m = _vcg_mechanism(payment=Unknown("w_i"))  # one free per-agent weight
    out = synthesize(m, _constraints(m))

    assert isinstance(out, Mechanism)
    assert isinstance(out.allocation, _ALLOC)
    assert isinstance(out.allocation, AllocHighest)  # default / recommended rule
    assert "allocation_rule_latex" not in out.meta
    assert "payment_rule_latex" not in out.meta

    assert verify_from_ast(out).verdict == "VERIFIED"


def test_synthesize_vcg_no_unknowns_sets_alloc_node():
    m = _vcg_mechanism(payment=Sym("p_i"))  # no free leaves
    out = synthesize(m, _constraints(m))

    assert isinstance(out.allocation, AllocHighest)
    assert "allocation_rule_latex" not in out.meta
    assert "payment_rule_latex" not in out.meta
    assert verify_from_ast(out).verdict == "VERIFIED"


def test_synthesize_vcg_drops_model_authored_meta_latex():
    m = _vcg_mechanism(payment=Sym("p_i"))
    m.meta["payment_rule_latex"] = r"p_i = 0.5 b_i"       # bogus
    m.meta["allocation_rule_latex"] = r"x = \text{the output of Algorithm 3}"
    out = synthesize(m, _constraints(m))

    assert "payment_rule_latex" not in out.meta
    assert "allocation_rule_latex" not in out.meta
    assert isinstance(out.allocation, AllocHighest)      # unparseable -> default


def test_synthesize_vcg_keeps_menu_allocation():
    m = _vcg_mechanism(payment=Sym("p_i"))
    m.meta["allocation_rule_latex"] = r"x_i = 1 \text{ if } b_i = \max_j b_j"
    out = synthesize(m, _constraints(m))
    assert isinstance(out.allocation, AllocHighest)
    assert collect_unknowns(out.payment) == []
