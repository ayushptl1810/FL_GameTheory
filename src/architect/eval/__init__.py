"""Evaluation harness: run the Architect loop over the benchmark set (spec S8)."""
from __future__ import annotations

import contextlib
import os
import statistics

from architect.types import ProblemSpec
import architect.loop as _loop
from architect.loop import run, _default_deps
from architect.eval.benchmarks import BENCHMARKS

ABLATIONS = ("no_rag", "cap2", "cap10", "no_mc", "force_family")


def _ic_regret(result) -> float:
    return 0.0 if result.status == "VERIFIED" else float("nan")


def _coalition_ic_regret(result, benchmark):
    """2-type coalition IC-regret for VERIFIED Contract rows with a numeric menu.

    0.0 when no profitable joint deviation, the reported gain on a
    COUNTEREXAMPLE, else None (not a Contract row / not VERIFIED / no menu).
    """
    if benchmark.get("expected_family") != "Contract" or result.status != "VERIFIED":
        return None
    menu = (result.mechanism_dict or {}).get("menu")
    if not isinstance(menu, dict) or not menu:
        return None
    if not all(isinstance(v, (int, float)) for v in menu.values()):
        return None
    from tracks.track1_z3 import verify_coalition_ic_contract
    n = result.mechanism_dict.get("num_types") or sum(
        1 for key in menu if key.startswith("theta_"))
    res = verify_coalition_ic_contract(
        {"menu": menu, "num_types": n, "paper_id": benchmark["name"]}, k=2)
    if res.verdict == "VERIFIED":
        return 0.0
    if res.verdict == "COUNTEREXAMPLE":
        try:
            return float(res.notes.rsplit("gain", 1)[1].strip())
        except (IndexError, ValueError):
            return float("nan")
    return None


def _forced_deps(index, force_mode):
    """Retrieval-only baseline: pin the router to force_mode, leave the rest default."""
    deps = _default_deps(index)
    deps.route = lambda spec, index=index: force_mode
    return deps


def _ablation_deps(index, ablation):
    """Live-path deps with one knob flipped. cap2/cap10 are handled by a
    context manager around run() (they patch loop.REPAIR_CAP), not here."""
    deps = _default_deps(index)
    if ablation == "no_rag":
        deps.retrieve = lambda spec, k, index=None: []
    elif ablation == "no_mc":
        deps.mc_prefilter = lambda m: None
    elif ablation == "force_family":
        deps.route = lambda spec, index=None: spec.expected_family or "Synthesis"
    return deps


@contextlib.contextmanager
def _repair_cap(ablation):
    """cap2 / cap10 temporarily override the loop's repair budget."""
    caps = {"cap2": 2, "cap10": 10}
    if ablation not in caps:
        yield
        return
    old = _loop.REPAIR_CAP
    _loop.REPAIR_CAP = caps[ablation]
    try:
        yield
    finally:
        _loop.REPAIR_CAP = old


def _row(b, r, *, seed, ablation=None) -> dict:
    row = {"name": b["name"], "mode": r.mode, "status": r.status,
           "iterations": r.iterations, "solver_calls": r.solver_calls,
           "wall_clock": round(r.wall_clock, 2), "ic_regret": _ic_regret(r),
           "expected_family": b.get("expected_family"),
           "family_match": r.family_match,
           "transcript_tail": r.transcript[-2:],
           "coalition_ic_regret": _coalition_ic_regret(r, b),
           "seed": seed}
    if ablation is not None:
        row["ablation"] = ablation
    return row


def evaluate(names=None, *, index=None, force_mode=None, seeds=(0,),
             model=None, ablations=None, deps_factory=None) -> list:
    """Run the Architect loop over the benchmark set.

    seeds        -- tuple of ints; each benchmark is run once per seed and every
                    row is tagged ``"seed"``. llm.py has no seed knob, so extra
                    seeds simply measure API nondeterminism.
    ablations    -- subset of ABLATIONS; for each, a second run per seed with
                    that knob flipped, tagged ``"ablation"``. Base (unablated)
                    rows are always emitted too.
    deps_factory -- callable ``deps_factory(*, ablation=None) -> deps``; when
                    given it fully replaces the live dependency wiring (used by
                    tests to stay off the network).
    model        -- if set, exported as ARCHITECT_LLM_MODEL for llm.py.
    """
    if model:
        os.environ["ARCHITECT_LLM_MODEL"] = model
    chosen = [b for b in BENCHMARKS if names is None or b["name"] in names]
    combos = [(s, None) for s in seeds]
    for s in seeds:
        combos += [(s, a) for a in (ablations or [])]

    rows = []
    for b in chosen:
        spec = ProblemSpec(raw_text=b["text"],
                           expected_family=b.get("expected_family"))
        for seed, ablation in combos:
            kw = {"index": index}
            if deps_factory is not None:
                kw["deps"] = deps_factory(ablation=ablation)
            elif ablation is not None:
                kw["deps"] = _ablation_deps(index, ablation)
            elif force_mode:
                kw["deps"] = _forced_deps(index, force_mode)
            with _repair_cap(ablation):
                r = run(spec, **kw)
            rows.append(_row(b, r, seed=seed, ablation=ablation))
    return rows


def _finite(xs):
    return [x for x in xs if isinstance(x, (int, float)) and x == x]


def summarize(rows) -> list:
    """Collapse repeated rows (over seeds / ablations) into one dict per name."""
    out = []
    for name in dict.fromkeys(r["name"] for r in rows):
        g = [r for r in rows if r["name"] == name]
        iters = [r["iterations"] for r in g]
        regrets = _finite(r["ic_regret"] for r in g)
        out.append({
            "name": name,
            "verified_rate": sum(r["status"] == "VERIFIED" for r in g) / len(g),
            "iters_mean": statistics.mean(iters),
            "iters_spread": max(iters) - min(iters),
            "wall_clock_mean": statistics.mean(r["wall_clock"] for r in g),
            "ic_regret_mean": statistics.mean(regrets) if regrets else float("nan"),
        })
    return out
