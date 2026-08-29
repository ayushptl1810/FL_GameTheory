"""Task G: eval rigor -- seed repetition, ablation knobs, summarize() variance.

All stubbed: no live API. Fixtures mirror the deps stub style of test_loop.py.
"""
import types as _t

import pytest

from architect.ast import Const, Sym, Sum, Mechanism
from architect.eval import evaluate, summarize


def _mech(cat="Contract"):
    return Mechanism(cat, utility=Sym("R_i"), payment=Sym("R_i"),
                     ic=Sum([Const(1)]), ir=Sum([Const(1)]),
                     params={}, type_space=["t"])


class _V:
    def __init__(self, verdict="VERIFIED", entry_specific=True):
        self.verdict = verdict
        self.entry_specific = entry_specific
        self.counterexample = None
        self.conditions = []
        self.category = "Contract"


def _stub_deps(*, ablation=None):
    """A deps namespace that always drives loop.run to VERIFIED in one iteration.

    Proposes in the spec's own expected_family so the family-fidelity guard
    never trips. `ablation` is accepted (and ignored) so evaluate() can pass it.
    """
    return _t.SimpleNamespace(
        retrieve=lambda spec, k, index=None: [],
        route=lambda spec, index=None: "Synthesis",
        propose=lambda spec, mode, hits, fb: _mech(spec.expected_family or "Contract"),
        synthesize=lambda m, c: m,
        make_constraints=lambda m: None,
        render=lambda m: ({"category": m.category, "ic_condition_latex": "x"}, "x"),
        mc_prefilter=lambda m: None,
        inspect=lambda m, meta: _V("VERIFIED", entry_specific=True),
        is_success=lambda r: r.verdict == "VERIFIED" and r.entry_specific,
    )


@pytest.fixture
def stub_index():
    return object()


@pytest.fixture
def stub_deps_factory():
    return _stub_deps


def test_evaluate_runs_multiple_seeds(stub_index, stub_deps_factory):
    rows = evaluate(index=stub_index, seeds=(0, 1, 2),
                    deps_factory=stub_deps_factory)
    names = {r["name"] for r in rows}
    for n in names:
        assert sum(1 for r in rows if r["name"] == n) == 3
    assert {r["seed"] for r in rows} == {0, 1, 2}
    summ = summarize(rows)
    assert all({"verified_rate", "wall_clock_mean"} <= set(s) for s in summ)


def test_summarize_keys_and_rates(stub_index, stub_deps_factory):
    rows = evaluate(index=stub_index, seeds=(0, 1), deps_factory=stub_deps_factory)
    summ = summarize(rows)
    keys = {"name", "verified_rate", "iters_mean", "iters_spread",
            "wall_clock_mean", "ic_regret_mean"}
    assert all(keys == set(s) for s in summ)
    assert {s["name"] for s in summ} == {r["name"] for r in rows}
    assert all(s["verified_rate"] == 1.0 for s in summ)
    assert all(s["iters_spread"] == 0 for s in summ)


def test_ablations_tag_rows(stub_index, stub_deps_factory):
    rows = evaluate(index=stub_index, seeds=(0,),
                    ablations=["no_rag", "cap2"], deps_factory=stub_deps_factory)
    tagged = [r for r in rows if "ablation" in r]
    assert {r["ablation"] for r in tagged} == {"no_rag", "cap2"}
    # base (untagged) rows are still emitted alongside the ablation rows
    assert any("ablation" not in r for r in rows)


def test_backward_compatible_default(stub_index, stub_deps_factory):
    rows = evaluate(index=stub_index, deps_factory=stub_deps_factory)
    from architect.eval.benchmarks import BENCHMARKS
    assert len(rows) == len(BENCHMARKS)
    assert all(r["seed"] == 0 and "ablation" not in r for r in rows)
