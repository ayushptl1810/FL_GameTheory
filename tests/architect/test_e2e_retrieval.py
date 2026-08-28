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
    assert r.status == "FAILED"
    assert any(e.get("note") == "verified_template_rejected" for e in r.transcript)


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
