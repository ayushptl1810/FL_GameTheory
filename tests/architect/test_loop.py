import types as _t

from architect.types import ProblemSpec, Feedback
from architect.ast import Const, Sym, Sum, Mechanism
from architect.architect import _feedback_block
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


def test_verified_template_is_failure():
    r = run(ProblemSpec(raw_text="x"), index=object(),
            deps=_deps([_V("VERIFIED", entry_specific=False)]))
    assert r.status == "FAILED"


def test_feedback_block_distinguishes_restart_from_counterexample():
    restart_txt = _feedback_block(Feedback(kind="restart", hint="VCG, Contract"))
    cex_txt = _feedback_block(
        Feedback(kind="counterexample", counterexample={"type": "t=1", "ic_gap": "-0.5"}))
    assert restart_txt != cex_txt
    assert "VCG, Contract" in restart_txt
    assert "t=1" in cex_txt
    assert "restart" not in cex_txt.lower()
