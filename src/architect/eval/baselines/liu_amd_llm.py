"""Liu et al. LLM automated-mechanism-design baseline adapter.

Method: an LLM proposes an allocation rule, then a deterministic "fix-process"
makes it strategyproof -- (1) monotonicity repair of each agent's allocation in
its own report, (2) payments reconstructed from the Myerson payment identity
(a.k.a. critical-price construction).  Here the LLM-proposal step is replaced by
the textbook efficient allocation, so only the fix-process is exercised.

Upstream survey (Step 1, 2026-08-29):
  gh search repos "automated mechanism design LLM" / "LLM mechanism design
  Conitzer" -> no public release found (arXiv 2502.12203 ships no code repo).
  Nothing vendored under third_party/.
Decision: NO VENDORED UPSTREAM -> reimplement the fix-process below (~110 lines)
for the only two templates in scope: ``myerson_single_item`` and
``vcg_redistribution``.  Any other benchmark returns status
"UNSUPPORTED_TEMPLATE".  IC-regret is measured with the shared misreport grid.
"""
from __future__ import annotations

import time

import numpy as np

from architect.eval.baselines import (
    MISREPORT_GRID,
    auction_ic_regret,
    uniform_value_profiles,
)

_TEMPLATES = {"myerson_single_item", "vcg_redistribution"}
_N_BIDDERS = 3
_RESERVE = {"myerson_single_item": 0.5, "vcg_redistribution": 0.0}  # phi(r)=0 for U[0,1]
_GRID = np.asarray(MISREPORT_GRID, dtype=float)
_trapz = getattr(np, "trapezoid", None) or np.trapz  # numpy>=2 renamed trapz


def _sub(r, i, value):
    r = np.array(r, dtype=float)
    r[i] = value
    return r


def _efficient_alloc(r, reserve=0.0):
    """Give the item to the highest report, subject to a reserve price."""
    r = np.asarray(r, dtype=float)
    a = np.zeros_like(r)
    if r.size and r.max() >= reserve and r.max() > 0.0:
        a[int(np.argmax(r))] = 1.0
    return a


def _fix_process(base_alloc, n):
    """Monotonicity repair + Myerson-payment-identity (critical-price) rebuild.

    For each agent i and fixed opponent reports, sweep its own report over the
    shared grid, iron the allocation to be non-decreasing (cumulative max), then
        p_i(v_i) = v_i * x_i(v_i) - integral_0^{v_i} x_i(t) dt.
    """
    def _ironed_curve(r, i):
        xs = np.array([base_alloc(_sub(r, i, g))[i] for g in _GRID])
        return np.maximum.accumulate(xs)                     # monotonicity repair

    def alloc_fn(r):
        r = np.asarray(r, dtype=float)
        out = np.zeros(n)
        for i in range(n):
            out[i] = np.interp(r[i], _GRID, _ironed_curve(r, i))
        return out

    def pay_fn(r):
        r = np.asarray(r, dtype=float)
        out = np.zeros(n)
        for i in range(n):
            xs = _ironed_curve(r, i)
            xi = np.interp(r[i], _GRID, xs)
            mask = _GRID <= r[i]
            integral = _trapz(xs[mask], _GRID[mask]) if mask.sum() > 1 else 0.0
            out[i] = r[i] * xi - integral                    # critical-price identity
        return out

    return alloc_fn, pay_fn


def _cavallo_rebate(r, n):
    """Return 1/n of the second-highest report among the *other* bidders."""
    r = np.asarray(r, dtype=float)
    reb = np.zeros(n)
    for i in range(n):
        others = np.sort(np.delete(r, i))[::-1]
        reb[i] = (others[1] if others.size >= 2 else 0.0) / n
    return reb


def run_baseline(name, bench):
    t0 = time.time()
    bn = bench["name"]
    fam_match = bench.get("expected_family") == "VCG"
    if bn not in _TEMPLATES:
        return {"name": bn, "method": "liu_amd_llm", "mode": "n/a",
                "status": "UNSUPPORTED_TEMPLATE", "iterations": 0,
                "solver_calls": 0, "wall_clock": round(time.time() - t0, 2),
                "ic_regret": None, "family_match": fam_match}

    n = _N_BIDDERS
    reserve = _RESERVE[bn]
    base = lambda r: _efficient_alloc(r, reserve=reserve)
    alloc_fn, pay_fn = _fix_process(base, n)
    if bn == "vcg_redistribution":
        _core_pay = pay_fn
        pay_fn = lambda r: _core_pay(r) - _cavallo_rebate(r, n)

    profiles = uniform_value_profiles(n, samples=64, seed=2)
    ic_regret = auction_ic_regret(alloc_fn, pay_fn, profiles)
    return {"name": bn, "method": "liu_amd_llm", "mode": "n/a",
            "status": "REPAIRED", "iterations": 0, "solver_calls": 0,
            "wall_clock": round(time.time() - t0, 2),
            "ic_regret": ic_regret, "family_match": fam_match}
