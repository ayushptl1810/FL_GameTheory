"""Task 8: Synthesis mode constrains VCG to Clarke payment + weight search."""
from architect.ast import Const, Sym, Unknown, Sum, Prod, Mechanism
from architect.synthesize import synthesize, Constraints, collect_unknowns
from tracks.vcg_dsic import verify_vcg_dsic


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
        meta={},
    )


def _constraints(m):
    return Constraints(ic=m.ic, ir=m.ir, budget_lhs=None, budget_rhs=None,
                       type_space=m.type_space, param_bounds={})


def _entry_from_meta(out, n=2):
    return {
        "category": "VCG",
        "num_clients": n,
        "mechanism": {
            "allocation_rule_latex": out.meta["allocation_rule_latex"],
            "payment_rule_latex": out.meta["payment_rule_latex"],
        },
    }


def test_synthesize_vcg_injects_clarke_meta_and_verifies():
    m = _vcg_mechanism(payment=Unknown("w_i"))  # one free per-agent weight
    out = synthesize(m, _constraints(m))

    assert isinstance(out, Mechanism)
    alloc = out.meta["allocation_rule_latex"]
    pay = out.meta["payment_rule_latex"]
    assert r"\max_j b_j" in alloc                 # highest-bidder rule
    assert r"\max_{j \neq i} b_j" in pay          # Clarke pivot / second price
    # every weight Unknown resolved to a concrete Const
    assert collect_unknowns(out.payment) == []

    r = verify_vcg_dsic(_entry_from_meta(out))
    assert r.verdict == "VERIFIED", r.notes


def test_synthesize_vcg_no_unknowns_still_gets_clarke_meta():
    m = _vcg_mechanism(payment=Sym("p_i"))  # no free leaves -> unit weights
    out = synthesize(m, _constraints(m))

    assert out.meta["payment_rule_latex"] == r"p_i = \max_{j \neq i} b_j"
    assert verify_vcg_dsic(_entry_from_meta(out)).verdict == "VERIFIED"


def test_synthesize_vcg_overwrites_model_authored_payment():
    m = _vcg_mechanism(payment=Sym("p_i"))
    m.meta["payment_rule_latex"] = r"p_i = 0.5 b_i"  # bogus, must not survive
    out = synthesize(m, _constraints(m))
    assert out.meta["payment_rule_latex"] == r"p_i = \max_{j \neq i} b_j"


def test_synthesize_vcg_keeps_menu_allocation_else_defaults():
    m = _vcg_mechanism(payment=Sym("p_i"))
    m.meta["allocation_rule_latex"] = r"x = \text{the output of Algorithm 3}"
    out = synthesize(m, _constraints(m))
    assert r"\max_j b_j" in out.meta["allocation_rule_latex"]  # fell back
