"""Evaluation harness: run the Architect loop over the benchmark set (spec S8)."""
from __future__ import annotations

from architect.types import ProblemSpec
from architect.loop import run, _default_deps
from architect.eval.benchmarks import BENCHMARKS


def _ic_regret(result) -> float:
    return 0.0 if result.status == "VERIFIED" else float("nan")


def _forced_deps(index, force_mode):
    """Retrieval-only baseline: pin the router to force_mode, leave the rest default."""
    deps = _default_deps(index)
    deps.route = lambda spec, index=index: force_mode
    return deps


def evaluate(names=None, *, index=None, force_mode=None) -> list:
    chosen = [b for b in BENCHMARKS if names is None or b["name"] in names]
    rows = []
    for b in chosen:
        kw = {"index": index}
        if force_mode:
            kw["deps"] = _forced_deps(index, force_mode)
        r = run(ProblemSpec(raw_text=b["text"],
                            expected_family=b.get("expected_family")), **kw)
        rows.append({"name": b["name"], "mode": r.mode, "status": r.status,
                     "iterations": r.iterations, "solver_calls": r.solver_calls,
                     "wall_clock": round(r.wall_clock, 2), "ic_regret": _ic_regret(r),
                     "expected_family": b.get("expected_family"),
                     "family_match": r.family_match,
                     "transcript_tail": r.transcript[-2:]})
    return rows
