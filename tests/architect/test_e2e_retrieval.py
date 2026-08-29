"""End-to-end with a stub Architect: real serializer, MC, verify(); only LLM-backed
propose is replaced with a fixed textbook menu."""
import types as _t
from architect.types import ProblemSpec
from architect.loop import run
from architect.ast import Const, Sym, Sum, Prod, Pow, Mechanism
from architect.serialize import render
from architect.mc import mc_prefilter
from architect.inspect import inspect_mechanism, is_loop_success
from verifier import verify


def test_retrieval_mode_reaches_a_verdict():
    u = Sum([Sym("R_i"), Prod([Const(-1), Sym("theta_i"), Sym("e_i")])])
    # IC slack of a correctly-screened 2-type menu: a squared type/effort
    # difference, manifestly >= 0 so the MC pre-filter passes it through to
    # the real verify().
    ic = Pow(Sum([Sym("e_i"), Prod([Const(-1), Sym("e_j")])]), 2)
    m = Mechanism("Contract", utility=u, payment=Sym("R_i"), ic=ic, ir=u,
                  params={}, type_space=["lo", "hi"])
    deps = _t.SimpleNamespace(
        retrieve=lambda spec, k, index=None: [],
        route=lambda spec, index=None: "Retrieval",
        propose=lambda spec, mode, hits, fb: m,
        synthesize=lambda mm, c: mm,
        make_constraints=lambda mm: None,
        render=render, mc_prefilter=mc_prefilter,
        inspect=inspect_mechanism, is_success=is_loop_success)
    r = run(ProblemSpec(raw_text="two-type screening menu, private types"),
            index=object(), deps=deps, budget_s=120)
    # The fixture always re-proposes the same template-only mechanism, so the
    # loop repairs, exhausts the budget, and FAILs -- cleanly, with a transcript.
    assert r.status == "FAILED"
    assert any(e.get("verdict") == "VERIFIED_TEMPLATE" for e in r.transcript)


def test_e2e_retrieval_reaches_entry_specific_verified():
    """The CEGIS loop's ONLY success gate is is_loop_success(r) =
    (r.verdict == "VERIFIED" and r.entry_specific is True). This proves that
    a mechanism built as an AST, pushed through serialize.render() into the
    real verifier.verify(), can actually reach that state.

    Vehicle: a textbook Stackelberg follower-effort mechanism
        U_i(e_i) = p_i * e_i - (1/2) * c * e_i^2
    render() emits follower_utility_latex verbatim (utility is not wrapped
    in "... >= 0"); the entry-specific Stackelberg path parses it, derives
    e_i* = p_i/c by FOC, and certifies U*(e_i*) = p_i^2 / (2c) >= 0.

    The three keys added below (equilibrium_existence, follower_decision,
    num_types) are metadata that serialize.render() does NOT emit and
    loop.run()'s inspect_mechanism meta does NOT thread through today --
    see the report's "Fix round 1" for why the loop cannot yet reach this
    verdict on its own, and why the Contract entry-specific paths cannot
    reach it from render() output at all.
    """
    e_star_num = Prod([Const(-0.5), Sym("c"), Pow(Sym("e_i"), 2)])
    u = Sum([Prod([Sym("p_i"), Sym("e_i")]), e_star_num])
    # follower FOC as a one-sided ">= 0" node (loop passes it to render/MC;
    # the Stackelberg verifier ignores IC by design).
    ic = Sum([Sym("p_i"), Prod([Const(-1), Sym("c"), Sym("e_i")])])
    m = Mechanism("Stackelberg", utility=u, payment=Sym("p_i"), ic=ic, ir=u,
                  params={}, type_space=["lo", "hi"])

    mechanism_dict, latex = render(m)
    assert "follower_utility_latex" in mechanism_dict

    entry = {
        "paper_id": "architect-proposal",
        "category": "Stackelberg",
        "num_clients": 2,
        "mechanism": {
            **mechanism_dict,
            "equilibrium_existence": True,
            "follower_decision": r"effort level \( e_i \)",
            "num_types": 2,
        },
    }
    r = verify(entry)
    assert r.verdict == "VERIFIED", (r.verdict, r.notes)
    assert r.entry_specific is True, r.notes
    assert is_loop_success(r) is True


def test_loop_run_reaches_verified_via_stackelberg():
    """The REAL loop.run closes end to end: the Stackelberg metadata keys ride
    on Mechanism.meta, get folded into the mechanism dict by serialize.render(),
    and reach verify() through the untouched inspect/loop call chain."""
    e_star_num = Prod([Const(-0.5), Sym("c"), Pow(Sym("e_i"), 2)])
    u = Sum([Prod([Sym("p_i"), Sym("e_i")]), e_star_num])
    # Stackelberg ignores IC by design; use a manifestly non-negative node so
    # the real MC pre-filter passes it through to verify().
    ic = Pow(Sum([Sym("p_i"), Prod([Const(-1), Sym("c"), Sym("e_i")])]), 2)
    m = Mechanism("Stackelberg", utility=u, payment=Sym("p_i"), ic=ic, ir=u,
                  params={}, type_space=["lo", "hi"],
                  meta={"equilibrium_existence": True,
                        "follower_decision": r"effort level \( e_i \)",
                        "num_types": 2})
    deps = _t.SimpleNamespace(
        retrieve=lambda spec, k, index=None: [],
        route=lambda spec, index=None: "Retrieval",
        propose=lambda spec, mode, hits, fb: m,
        synthesize=lambda mm, c: mm,
        make_constraints=lambda mm: None,
        render=render, mc_prefilter=mc_prefilter,
        inspect=inspect_mechanism, is_success=is_loop_success)
    r = run(ProblemSpec(raw_text="follower effort, quadratic cost, leader sets price"),
            index=object(), deps=deps, budget_s=120)
    assert r.status == "VERIFIED", (r.status, r.transcript)
    assert r.transcript[-1]["verdict"] == "VERIFIED", r.transcript


def test_loop_run_reaches_verified_via_contract():
    """Contract now closes end to end: the serializer renders `ic` in the
    two-sided ``U_i(own) >= U_i(other)`` form the Stage 1 Contract verifier
    needs, and meta.num_types / meta.type_variable ride through to it.
    """
    def U(r, th, e):
        return Sum([Sym(r), Prod([Const(-1), Sym(th), Sym(e)])])

    own = U("R_i", "theta_i", "e_i")
    other = U("R_j", "theta_i", "e_j")
    ic = Sum([own, Prod([Const(-1), other])])  # U_i(own) - U_i(other)
    m = Mechanism("Contract", utility=own, payment=Sym("R_i"), ic=ic,
                  ir=U("R_i", "theta_i", "e_i"), params={},
                  type_space=["lo", "hi"],
                  meta={"num_types": 2, "type_variable": "theta_i"})

    md, _ = render(m)
    assert "\\geq" in md["ic_screening_latex"]
    assert md["ic_screening_latex"].split("\\geq")[1].strip()  # two-sided, RHS != ""

    deps = _t.SimpleNamespace(
        retrieve=lambda spec, k, index=None: [],
        route=lambda spec, index=None: "Retrieval",
        propose=lambda spec, mode, hits, fb: m,
        synthesize=lambda mm, c: mm,
        make_constraints=lambda mm: None,
        render=render, mc_prefilter=mc_prefilter,
        inspect=inspect_mechanism, is_success=is_loop_success)
    r = run(ProblemSpec(raw_text="two-type screening menu, private cost types"),
            index=object(), deps=deps, budget_s=120)
    assert r.status == "VERIFIED", (r.status, r.transcript)
    assert r.transcript[-1]["verdict"] == "VERIFIED", r.transcript


def test_non_vcg_skips_mc_prefilter():
    """The MC pre-filter (IC-based) must not run for Stackelberg — a one-sided
    FOC node that MC would bounce should reach verify() untouched."""
    called = []

    def _spy_mc(mm):
        called.append(mm.category)
        return {"type": "x=1", "ic_gap": "-1"}  # would fail every non-Stackelberg

    u = Sum([Prod([Sym("p_i"), Sym("e_i")]),
             Prod([Const(-0.5), Sym("c"), Pow(Sym("e_i"), 2)])])
    ic = Sum([Sym("p_i"), Prod([Const(-1), Sym("c"), Sym("e_i")])])  # one-sided FOC
    m = Mechanism("Stackelberg", utility=u, payment=Sym("p_i"), ic=ic, ir=u,
                  params={}, type_space=["lo", "hi"],
                  meta={"equilibrium_existence": True,
                        "follower_decision": r"effort level \( e_i \)",
                        "num_types": 2})
    deps = _t.SimpleNamespace(
        retrieve=lambda spec, k, index=None: [],
        route=lambda spec, index=None: "Retrieval",
        propose=lambda spec, mode, hits, fb: m,
        synthesize=lambda mm, c: mm, make_constraints=lambda mm: None,
        render=render, mc_prefilter=_spy_mc,
        inspect=inspect_mechanism, is_success=is_loop_success)
    r = run(ProblemSpec(raw_text="follower effort"), index=object(), deps=deps,
            budget_s=120)
    assert called == [], "mc_prefilter should not be called for Stackelberg"
    assert r.status == "VERIFIED", (r.status, r.transcript)
