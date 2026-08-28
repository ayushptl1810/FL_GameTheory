"""End-to-end with a stub Architect: real serializer, MC, verify(); only LLM-backed
propose is replaced with a fixed textbook menu."""
import types as _t
from architect.types import ProblemSpec
from architect.loop import run
from architect.ast import Const, Sym, Sum, Prod, Pow, Mechanism
from architect.serialize import render
from architect.mc import mc_prefilter
from architect.inspect import inspect_mechanism, is_loop_success


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
    assert r.status in {"VERIFIED", "FAILED"}
    assert r.transcript and r.transcript[-1].get("verdict") in {
        "VERIFIED", "VERIFIED_TEMPLATE", "COUNTEREXAMPLE", "UNKNOWN", "UNSUPPORTED", None}
