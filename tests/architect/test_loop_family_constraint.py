import types as _t

import pytest

from architect import loop
from architect.ast import Const, Sym, Sum, Mechanism
from architect.types import ProblemSpec


def _mech(cat="Stackelberg"):
    return Mechanism(cat, utility=Sym("R_i"), payment=Sym("R_i"),
                     ic=Sum([Const(1)]), ir=Sum([Const(1)]), params={}, type_space=["t"])


class _V:
    def __init__(self, verdict="VERIFIED"):
        self.verdict = verdict
        self.entry_specific = True
        self.counterexample = None
        self.conditions = []
        self.category = "Stackelberg"


@pytest.fixture
def stub_deps_stackelberg():
    """LLM stubbed at propose(); everything else real-ish. propose() always
    returns a mechanism whose serialized category is 'Stackelberg'."""
    return _t.SimpleNamespace(
        retrieve=lambda spec, k, index: [],
        route=lambda spec, index: "Retrieval",
        propose=lambda spec, mode, hits, fb: _mech("Stackelberg"),
        synthesize=lambda m, c: m,
        make_constraints=lambda m: None,
        render=lambda m: ({"ic_condition_latex": "x"}, "x"),
        mc_prefilter=lambda m: None,
        inspect=lambda m, meta: _V("VERIFIED"),
        is_success=lambda r: r.verdict == "VERIFIED" and r.entry_specific,
    )


def test_loop_rejects_off_family_proposal_and_feeds_back(stub_deps_stackelberg):
    spec = ProblemSpec(raw_text="a 2-type screening problem",
                       expected_family="Contract")
    res = loop.run(spec, index=None, budget_s=5.0, deps=stub_deps_stackelberg)
    assert res.status == "FAILED"
    assert res.emitted_family == "Stackelberg"
    assert res.family_match is False
    assert any("Contract" in (e.get("hint", "") or "") for e in res.transcript)


def test_loop_accepts_in_family_proposal(stub_deps_stackelberg):
    spec = ProblemSpec(raw_text="a follower-effort problem",
                       expected_family="Stackelberg")
    res = loop.run(spec, index=None, budget_s=5.0, deps=stub_deps_stackelberg)
    assert res.status == "VERIFIED"
    assert res.emitted_family == "Stackelberg"
    assert res.family_match is True


def test_loop_family_match_none_when_unconstrained(stub_deps_stackelberg):
    res = loop.run(ProblemSpec(raw_text="x"), index=None, budget_s=5.0,
                   deps=stub_deps_stackelberg)
    assert res.status == "VERIFIED"
    assert res.family_match is None
