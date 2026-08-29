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


def test_verify_from_ast_vcg_is_template_not_verified():
    # VCG has no entry-specific check yet (Phase 2); the AST path must not
    # fabricate VERIFIED off the fixed threshold template.
    m = Mechanism(
        category="VCG",
        utility=Sym("u_i"), payment=Sym("p_i"), ic=Sym("v_i"), ir=Sym("v_i"),
        type_space=[], meta={})
    r = verify_from_ast(m)
    assert r.verdict == "VERIFIED_TEMPLATE" and r.entry_specific is False


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
