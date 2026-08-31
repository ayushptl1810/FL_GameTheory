import sympy
from architect.ast import Const, Sym, Unknown, Sum, Prod, Pow, Func, IndexedFamily
from architect.serialize import ast_to_sympy


def test_bridge_atoms():
    assert ast_to_sympy(Const(2.5)) == sympy.Rational(5, 2)
    assert ast_to_sympy(Sym("theta")) == sympy.Symbol("theta")
    assert ast_to_sympy(Unknown("a")) == sympy.Symbol("a")


def test_const_half_is_rational_not_float():
    # Fix #9: every Const rides the exact Rational path so the render / corpus
    # dict keeps \frac{1}{2}, never 0.5.
    assert ast_to_sympy(Const(0.5)) == sympy.Rational(1, 2)
    from architect.serialize import to_latex
    tex = to_latex(Prod([Const(0.5), Sym("c")]))
    assert "0.5" not in tex and ("frac" in tex or "1}{2" in tex)


def test_bridge_compound():
    e = ast_to_sympy(Sum([Prod([Sym("p"), Sym("e")]),
                          Prod([Const(-0.5), Sym("c"), Pow(Sym("e"), 2)])]))
    p, e_, c = sympy.symbols("p e c")
    assert sympy.simplify(e - (p * e_ - sympy.Rational(1, 2) * c * e_**2)) == 0


def test_bridge_funcs():
    assert ast_to_sympy(Func("ln", Sym("x"))) == sympy.log(sympy.Symbol("x"))
    assert ast_to_sympy(Func("exp", Sym("x"))) == sympy.exp(sympy.Symbol("x"))


def test_bridge_indexed_family_is_opaque_symbol():
    got = ast_to_sympy(IndexedFamily("R", "i", ["R_1", "R_2"]), opaque_families=True)
    assert got == sympy.Symbol("R")


def test_bridge_indexed_family_keeps_subscript_by_default():
    # Rendering path (flag-off): the index must survive so to_latex emits R_{i}.
    got = ast_to_sympy(IndexedFamily("R", "i", ["R_1", "R_2"]))
    assert got == sympy.Symbol("R_i")


def test_render_indexed_family_keeps_subscript():
    from architect.serialize import render, to_latex
    assert to_latex(IndexedFamily("R", "i", ["R_1", "R_2"])) == "R_{i}"
    m = Mechanism(
        category="Stackelberg",
        utility=IndexedFamily("R", "i", ["R_1", "R_2"]),
        payment=Sym("p_i"), ic=Sym("e_i"), ir=Sym("e_i"),
        type_space=[], meta={})
    _md, full = render(m, check_roundtrip=False)
    assert "R_{i}" in full


# ── verify_from_ast / _classify_ast orchestrator ────────────────────────────
from architect.ast import Mechanism, Sum, Prod, Const, Pow, Func  # noqa: E402
from architect.ast_verify import verify_from_ast, _classify_ast  # noqa: E402
from architect.inspect import inspect_mechanism  # noqa: E402


def _stackelberg_effort():
    # U_i = p_i*e_i - 1/2 * c * e_i^2  — the loop's canonical VERIFIED shape
    return Mechanism(
        category="Stackelberg",
        utility=Sum([Prod([Sym("p_i"), Sym("e_i")]),
                     Prod([Const(-0.5), Sym("c"), Pow(Sym("e_i"), 2)])]),
        payment=Sym("p_i"), ic=Sym("e_i"), ir=Sym("e_i"),
        type_space=[],
        meta={"follower_decision": r"\( e_i \)", "equilibrium_existence": True})


def test_inspect_uses_ast_path_when_flagged(monkeypatch):
    # _loop_stackelberg_fixture is the in-file fixture proven VERIFIED on BOTH
    # paths (see test_ast_path_matches_latex_path_on_loop_fixtures); the bare
    # _stackelberg_effort()'s trivial IC is UNSUPPORTED on the LaTeX path.
    m, meta = _loop_stackelberg_fixture()
    monkeypatch.setenv("ARCHITECT_AST_VERIFY", "1")
    assert inspect_mechanism(m, meta).verdict == "VERIFIED"
    monkeypatch.delenv("ARCHITECT_AST_VERIFY")
    assert inspect_mechanism(m, meta).verdict == "VERIFIED"   # LaTeX path still works


def test_classify_transcendental():
    m = _stackelberg_effort()
    m.utility = Func("ln", Sym("e_i"))
    assert _classify_ast(m) == 3


def test_classify_default_track1():
    assert _classify_ast(_stackelberg_effort()) == 1


def test_verify_from_ast_reaches_verified_stackelberg():
    r = verify_from_ast(_stackelberg_effort())
    assert r.verdict == "VERIFIED" and r.entry_specific is True


def test_verify_from_ast_stackelberg_without_equilibrium_existence_is_unsupported():
    m = _stackelberg_effort()
    m.meta.pop("equilibrium_existence")
    r = verify_from_ast(m)
    assert r.verdict == "UNSUPPORTED"


_VCG_HIGHEST = r"x_i = 1 \text{ if } b_i = \max_j b_j"
_VCG_LOWEST = r"x_i = 1 \text{ if } b_i = \min_j b_j"
_VCG_ALGO = r"x = \text{the output of Algorithm 3}"
_VCG_CLARKE = r"p_i = \max_{j \neq i} b_j"


def _vcg_mech(alloc_tex, *, payment_tex=None):
    meta = {"num_clients": 2, "allocation_rule_latex": alloc_tex}
    if payment_tex is not None:
        meta["payment_rule_latex"] = payment_tex
    return Mechanism(
        category="VCG",
        utility=Sym("u_i"), payment=Sym("v"), ic=Sym("v"), ir=Sym("v"),
        type_space=[], meta=meta)


def test_verify_from_ast_vcg_clarke_is_real_verified():
    # Well-formed single-item Clarke VCG: highest-bidder allocation + Clarke
    # payment -> verify_vcg_dsic proves DSIC + IR on the grid. Real, not a
    # template: entry_specific must be True.
    r = verify_from_ast(_vcg_mech(_VCG_HIGHEST, payment_tex=_VCG_CLARKE))
    assert r.verdict == "VERIFIED" and r.entry_specific is True


def test_verify_from_ast_vcg_wrong_allocation_is_counterexample():
    # Clarke-shaped payment computed off a lowest-bidder (non-welfare) rule is
    # not Groves: verify_vcg_dsic finds a profitable deviation.
    r = verify_from_ast(_vcg_mech(_VCG_LOWEST, payment_tex=_VCG_CLARKE))
    assert r.verdict == "COUNTEREXAMPLE"


def test_verify_from_ast_vcg_unparseable_allocation_is_unknown():
    # Allocation rule points at an opaque algorithm -> parse_allocation returns
    # None. The AST path must NOT fabricate a verdict off the fixed payment
    # template: honest UNKNOWN, never VERIFIED_TEMPLATE.
    r = verify_from_ast(_vcg_mech(_VCG_ALGO, payment_tex=_VCG_CLARKE))
    assert r.verdict == "UNKNOWN"


# ── Task 9: typed VCG allocation node (Alloc union) ─────────────────────────

from architect.ast import AllocHighest, AllocTopK, AllocWeightedWelfare  # noqa: E402
from architect.serialize import render as _render, _alloc_latex  # noqa: E402


def test_verify_from_ast_vcg_allocation_node_is_real_verified():
    # allocation carried as a typed node, NOT meta. verify_from_ast builds the
    # entry from m.allocation via render() -> VERIFIED, entry_specific.
    m = Mechanism(
        category="VCG", utility=Sym("u_i"), payment=Sym("v"),
        ic=Sym("v"), ir=Sym("v"), type_space=[],
        allocation=AllocHighest(), meta={"num_clients": 2})
    assert "allocation_rule_latex" not in m.meta
    r = verify_from_ast(m)
    assert r.verdict == "VERIFIED" and r.entry_specific is True


def test_vcg_allocation_node_latex_parity():
    # AST <-> LaTeX parity: the node renders to the same allocation/payment LaTeX
    # the meta path used, and parse_allocation reads it back to HighestBidder.
    from tracks.vcg_dsic import parse_allocation, HighestBidder, ClarkePivot, parse_payment
    m = Mechanism(
        category="VCG", utility=Sym("u_i"), payment=Sym("v"),
        ic=Sym("v"), ir=Sym("v"), type_space=[],
        allocation=AllocHighest(), meta={"num_clients": 2})
    md, _ = _render(m, check_roundtrip=False)
    alloc_tex, pay_tex = _alloc_latex(AllocHighest())
    assert md["allocation_rule_latex"] == alloc_tex
    assert md["payment_rule_latex"] == pay_tex
    assert isinstance(parse_allocation(md["allocation_rule_latex"]), HighestBidder)
    assert isinstance(parse_payment(md["payment_rule_latex"], None), ClarkePivot)


def test_vcg_allocation_node_none_no_meta_is_unknown():
    # Fail closed: no allocation node AND no meta allocation -> UNKNOWN.
    m = Mechanism(
        category="VCG", utility=Sym("u_i"), payment=Sym("v"),
        ic=Sym("v"), ir=Sym("v"), type_space=[], meta={"num_clients": 2})
    r = verify_from_ast(m)
    assert r.verdict == "UNKNOWN"


def test_validate_alloc_rejects_bad_nodes():
    from architect.ast import validate_alloc, ASTSchemaError
    validate_alloc(AllocHighest())
    validate_alloc(AllocTopK(k=2))
    validate_alloc(AllocWeightedWelfare(weights=["1", "2"]))
    with pytest.raises(ASTSchemaError):
        validate_alloc(AllocTopK(k=0))
    with pytest.raises(ASTSchemaError):
        validate_alloc(AllocWeightedWelfare(weights=[]))
    with pytest.raises(ASTSchemaError):
        validate_alloc(AllocWeightedWelfare(weights=[1, 2]))


def test_verify_from_ast_reaches_verified_contract():
    # Two-type screening menu, two-sided IC U_i(own) >= U_i(other).
    def U(r, th, e):
        return Sum([Sym(r), Prod([Const(-1), Sym(th), Sym(e)])])

    own = U("R_i", "theta_i", "e_i")
    other = U("R_j", "theta_i", "e_j")
    m = Mechanism(
        category="Contract",
        utility=own, payment=Sym("R_i"),
        ic=Sum([own, Prod([Const(-1), other])]),
        ir=U("R_i", "theta_i", "e_i"),
        type_space=["lo", "hi"],
        meta={"num_types": 2, "type_variable": "theta_i"})
    r = verify_from_ast(m)
    assert r is not None
    assert r.verdict == "VERIFIED" and r.entry_specific is True


# ── Task 8: verify_from_ast routes to Track 2/3/4 seams by _classify_ast ─────


def _continuous_contract(ic_node, ir_node):
    # continuous type space (numeric pair) so _classify_ast sees track 2/3
    return Mechanism(
        category="Contract",
        utility=ir_node, payment=Sym("R_i"),
        ic=ic_node, ir=ir_node,
        type_space=[0.1, 1.0],
        meta={"num_types": 2, "type_variable": "theta"})


def test_verify_from_ast_transcendental_reaches_track3():
    # IC gap = ln(1 + theta) >= 0 on [0.1, 1.0]; IR = theta.  The Track-1
    # Contract core cannot encode ln here (UNKNOWN); Track 3's interval seam
    # proves it delta-UNSAT -> entry-specific VERIFIED on track 3.
    ic = Func("ln", Sum([Const(1), Sym("theta")]))
    ir = Sym("theta")
    m = _continuous_contract(ic, ir)
    assert _classify_ast(m) == 3
    r = verify_from_ast(m)
    assert r.track == 3
    assert r.verdict == "VERIFIED" and r.entry_specific is True


def test_verify_from_ast_poly_deg2_reaches_track2():
    # IC gap = theta^2 >= 0, IR = theta^2, continuous [0.1, 1.0] -> track 2.
    ic = Pow(Sym("theta"), 2)
    m = _continuous_contract(ic, Pow(Sym("theta"), 2))
    assert _classify_ast(m) == 2
    r = verify_from_ast(m)
    assert r.track == 2


def test_verify_from_ast_matches_inspect_on_transcendental(monkeypatch):
    # Parity: the AST-native path and the AST -> LaTeX -> verify() path agree
    # on a transcendental fixture.
    ic = Func("ln", Sum([Const(1), Sym("theta")]))
    m = _continuous_contract(ic, Sym("theta"))
    meta = {"paper_id": "architect-proposal", "num_clients": 2}

    latex_verdict = inspect_mechanism(m, meta).verdict
    monkeypatch.setenv("ARCHITECT_AST_VERIFY", "1")
    ast_verdict = inspect_mechanism(m, meta).verdict
    assert ast_verdict == latex_verdict, (ast_verdict, latex_verdict)


# ── parity: AST-native path vs AST -> LaTeX -> verify() on the loop fixtures ──
# Builders copied verbatim from tests/architect/test_e2e_retrieval.py
# (test_loop_run_reaches_verified_via_stackelberg / ..._via_contract): the exact
# Mechanism + meta the real CEGIS loop drives to an entry-specific VERIFIED.


def _loop_stackelberg_fixture():
    e_star_num = Prod([Const(-0.5), Sym("c"), Pow(Sym("e_i"), 2)])
    u = Sum([Prod([Sym("p_i"), Sym("e_i")]), e_star_num])
    ic = Pow(Sum([Sym("p_i"), Prod([Const(-1), Sym("c"), Sym("e_i")])]), 2)
    m = Mechanism("Stackelberg", utility=u, payment=Sym("p_i"), ic=ic, ir=u,
                  params={}, type_space=["lo", "hi"],
                  meta={"equilibrium_existence": True,
                        "follower_decision": r"effort level \( e_i \)",
                        "num_types": 2})
    return m, {"paper_id": "architect-proposal", "num_clients": 2}


def _loop_contract_fixture():
    def U(r, th, e):
        return Sum([Sym(r), Prod([Const(-1), Sym(th), Sym(e)])])

    own = U("R_i", "theta_i", "e_i")
    other = U("R_j", "theta_i", "e_j")
    ic = Sum([own, Prod([Const(-1), other])])
    m = Mechanism("Contract", utility=own, payment=Sym("R_i"), ic=ic,
                  ir=U("R_i", "theta_i", "e_i"), params={},
                  type_space=["lo", "hi"],
                  meta={"num_types": 2, "type_variable": "theta_i"})
    return m, {"paper_id": "architect-proposal", "num_clients": 2}


def _loop_verified_fixtures():
    return [_loop_stackelberg_fixture(), _loop_contract_fixture()]


def test_ast_path_matches_latex_path_on_loop_fixtures():
    for m, meta in _loop_verified_fixtures():
        latex_verdict = inspect_mechanism(m, meta).verdict   # AST -> LaTeX -> verify()
        ast_result = verify_from_ast(m, meta)
        assert ast_result.verdict == latex_verdict, (
            m.category, ast_result.verdict, latex_verdict)
        assert ast_result.verdict == "VERIFIED" and ast_result.entry_specific is True


def test_ast_path_matches_latex_path_on_vcg_clarke():
    # Well-formed single-item VCG: pay-your-value payment (AST-expressible as
    # Sym("v")) + highest-bidder allocation carried on meta. Both the AST-native
    # path and AST -> LaTeX -> verify() must reach the same entry-specific
    # VERIFIED via verify_vcg_dsic.
    m = Mechanism(
        category="VCG",
        utility=Sym("u_i"), payment=Sym("v"), ic=Sym("v"), ir=Sym("v"),
        type_space=[], meta={})
    meta = {
        "paper_id": "architect-proposal",
        "num_clients": 2,
        "allocation_rule_latex": _VCG_HIGHEST,
    }
    latex_verdict = inspect_mechanism(m, meta).verdict
    ast_result = verify_from_ast(m, meta)
    assert ast_result.verdict == latex_verdict, (ast_result.verdict, latex_verdict)
    assert ast_result.verdict == "VERIFIED" and ast_result.entry_specific is True


def test_ast_path_matches_latex_path_on_non_verified():
    # Fix #10: the VERIFIED fixtures can't catch a divergence in the
    # non-VERIFIED directions. A Stackelberg mechanism whose meta LACKS
    # equilibrium_existence lands UNSUPPORTED on BOTH paths (AST path gates in
    # verify_from_ast; LaTeX path gates in verify_stackelberg).
    m, meta = _loop_stackelberg_fixture()
    m.meta.pop("equilibrium_existence")
    latex_verdict = inspect_mechanism(m, meta).verdict
    ast_verdict = verify_from_ast(m, meta).verdict
    assert ast_verdict == latex_verdict, (ast_verdict, latex_verdict)
    assert ast_verdict != "VERIFIED"


# ── render(check_roundtrip=False): no LaTeX parse in the AST-verify loop path ──
import pytest  # noqa: E402
from architect import serialize as _serialize  # noqa: E402
from architect.serialize import render as _render  # noqa: E402


def test_render_skip_roundtrip_returns_dict_str():
    m, _ = _loop_contract_fixture()
    md, full = _render(m, check_roundtrip=False)
    assert isinstance(md, dict) and isinstance(full, str) and md


def test_render_skip_roundtrip_does_not_call_parser(monkeypatch):
    """check_roundtrip=False skips the re-parse step; check_roundtrip=True still
    runs it (poisoned parser proves which path executes)."""
    m, _ = _loop_contract_fixture()

    def _boom(*a, **k):
        raise RuntimeError("round-trip parser ran despite check_roundtrip=False")

    for name in list(_serialize._PARSERS):
        monkeypatch.setitem(_serialize._PARSERS, name, _boom)

    md, _full = _render(m, check_roundtrip=False)   # no raise
    assert isinstance(md, dict)
    with pytest.raises(RuntimeError):               # default path still parses
        _render(m, check_roundtrip=True)
