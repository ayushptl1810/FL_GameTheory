import types as _t

from architect.types import ProblemSpec, Feedback
from architect.ast import Const, Sym, Sum, Mechanism
from architect.architect import _feedback_block
from architect.serialize import OutsideParseableFragment
from architect.loop import run


def _mech(cat="Contract"):
    return Mechanism(cat, utility=Sym("R_i"), payment=Sym("R_i"),
                     ic=Sum([Const(1)]), ir=Sum([Const(1)]), params={}, type_space=["t"])


class _V:
    def __init__(self, verdict, entry_specific=False, cex=None, conds=None):
        self.verdict = verdict
        self.entry_specific = entry_specific
        self.counterexample = cex
        self.conditions = conds or []
        self.category = "Contract"


def _deps(verdicts):
    seq = iter(verdicts)
    return _t.SimpleNamespace(
        retrieve=lambda spec, k, index: [],
        route=lambda spec, index: "Synthesis",
        propose=lambda spec, mode, hits, fb: _mech(),
        synthesize=lambda m, c: m,
        make_constraints=lambda m: None,
        render=lambda m: ({"ic_condition_latex": "x"}, "x"),
        mc_prefilter=lambda m: None,
        inspect=lambda m, meta: next(seq),
        is_success=lambda r: r.verdict == "VERIFIED" and r.entry_specific,
    )


def test_success_on_first_verified():
    r = run(ProblemSpec(raw_text="x"), index=object(),
            deps=_deps([_V("VERIFIED", entry_specific=True)]))
    assert r.status == "VERIFIED" and r.iterations == 1


def test_counterexample_repairs_then_succeeds():
    r = run(ProblemSpec(raw_text="x"), index=object(),
            deps=_deps([_V("COUNTEREXAMPLE", cex={"type": "t=1"}),
                        _V("COUNTEREXAMPLE", cex={"type": "t=2"}),
                        _V("VERIFIED", entry_specific=True)]))
    assert r.status == "VERIFIED" and r.iterations == 3


def test_counterexample_exhausts_then_restarts_then_fails():
    r = run(ProblemSpec(raw_text="x"), index=object(),
            deps=_deps([_V("COUNTEREXAMPLE", cex={"type": "t"})] * 12))
    assert r.status == "FAILED"
    assert sum(1 for e in r.transcript if e.get("note") == "restart") == 1


def test_unknown_reformulates_twice_then_fails():
    r = run(ProblemSpec(raw_text="x"), index=object(),
            deps=_deps([_V("UNKNOWN")] * 3))
    assert r.status == "FAILED" and r.iterations == 3


def test_unsupported_forces_family_once_then_fails():
    r = run(ProblemSpec(raw_text="x"), index=object(),
            deps=_deps([_V("UNSUPPORTED"), _V("UNSUPPORTED")]))
    assert r.status == "FAILED" and r.iterations == 2


def test_verified_non_entry_specific_falls_through_to_fail():
    r = run(ProblemSpec(raw_text="x"), index=object(),
            deps=_deps([_V("VERIFIED", entry_specific=False)]))
    assert r.status == "FAILED"


def test_verified_template_verdict_fails_with_note():
    r = run(ProblemSpec(raw_text="x"), index=object(),
            deps=_deps([_V("VERIFIED_TEMPLATE")]))
    assert r.status == "FAILED"
    assert any(e.get("note") == "verified_template_rejected" for e in r.transcript)


def _scripted_deps(*, verdicts, render=None, mc_prefilter=None, propose=None):
    """Per-call scriptable deps. `render`/`mc_prefilter`/`propose` may be a list
    (one entry consumed per call; a value is returned, an Exception is raised)."""
    vseq = iter(verdicts)

    def _step(script, default):
        if script is None:
            return default
        it = iter(script)

        def _call(*_a, **_k):
            try:
                out = next(it)
            except StopIteration:
                return default(*_a, **_k) if callable(default) else default
            if isinstance(out, Exception):
                raise out
            return out
        return _call

    return _t.SimpleNamespace(
        retrieve=lambda spec, k, index: [],
        route=lambda spec, index: "Synthesis",
        propose=_step(propose, lambda *_a, **_k: _mech()),
        synthesize=lambda m, c: m,
        make_constraints=lambda m: None,
        render=_step(render, lambda *_a, **_k: ({"ic_condition_latex": "x"}, "x")),
        mc_prefilter=_step(mc_prefilter, lambda *_a, **_k: None),
        inspect=lambda m, meta: next(vseq),
        is_success=lambda r: r.verdict == "VERIFIED" and r.entry_specific,
    )


def test_wall_clock_exceeded():
    r = run(ProblemSpec(raw_text="x"), index=object(), budget_s=-1.0,
            deps=_deps([_V("VERIFIED", entry_specific=True)]))
    assert r.status == "FAILED"
    assert any(e.get("note") == "wall_clock_exceeded" for e in r.transcript)


def test_propose_error_fails():
    deps = _scripted_deps(verdicts=[_V("VERIFIED", entry_specific=True)],
                          propose=[RuntimeError("boom")])
    r = run(ProblemSpec(raw_text="x"), index=object(), deps=deps)
    assert r.status == "FAILED"
    assert any(str(e.get("note", "")).startswith("propose_error:") for e in r.transcript)


def test_mc_hit_does_not_increment_solver_calls():
    # MC pre-filter only runs for VCG, so the proposal must be a VCG mechanism.
    deps = _scripted_deps(
        verdicts=[_V("VERIFIED", entry_specific=True)],
        propose=[_mech("VCG"), _mech("VCG")],
        mc_prefilter=[{"type": "t=1", "ic_gap": "-0.2"}])
    r = run(ProblemSpec(raw_text="x"), index=object(), deps=deps)
    assert r.status == "VERIFIED"
    assert r.iterations == 2
    assert r.solver_calls == 1


def test_outside_parseable_fragment_triggers_repair():
    deps = _scripted_deps(
        verdicts=[_V("VERIFIED", entry_specific=True)],
        render=[OutsideParseableFragment("use simpler algebra")])
    r = run(ProblemSpec(raw_text="x"), index=object(), deps=deps)
    assert r.status == "VERIFIED"
    assert r.iterations == 2
    assert any(e.get("verdict") == "PARSE" or e.get("note") == "use simpler algebra"
               for e in r.transcript)


def test_synthesize_exception_flows_into_syn_unsat_path():
    def _boom(m, c):
        raise ValueError("cannot translate log(x)")

    deps = _deps([_V("VERIFIED", entry_specific=True)] * 20)
    deps.synthesize = _boom
    r = run(ProblemSpec(raw_text="x"), index=object(), deps=deps)
    assert r.status == "FAILED"
    syn = [e for e in r.transcript if e.get("verdict") == "SYN_UNSAT"]
    assert syn and any("cannot translate log(x)" in str(e.get("note", "")) for e in syn)
    assert sum(1 for e in r.transcript if e.get("note") == "restart") == 1


def test_feedback_block_distinguishes_restart_from_counterexample():
    restart_txt = _feedback_block(Feedback(kind="restart", hint="VCG, Contract"))
    cex_txt = _feedback_block(
        Feedback(kind="counterexample", counterexample={"type": "t=1", "ic_gap": "-0.5"}))
    assert restart_txt != cex_txt
    assert "VCG, Contract" in restart_txt
    assert "t=1" in cex_txt
    assert "restart" not in cex_txt.lower()
