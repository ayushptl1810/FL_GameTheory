"""Baseline mechanism-design adapters for the Architect eval harness.

Each submodule exposes ``run_baseline(name: str, bench: dict) -> dict`` returning
a row in the eval schema
``{name, mode, status, iterations, solver_calls, wall_clock, ic_regret}`` plus
``"method"`` and ``"family_match"``.  Adapters:

* ``control``      -- trivial: emit one fixed textbook mechanism for every input.
* ``regretnet``    -- Duetting et al. RegretNet, scoped 2-bidder/1-item uniform.
* ``liu_amd_llm``  -- Liu et al. LLM-AMD fix-process, Myerson + VCG-redistribution.

Shared here: ``auction_ic_regret`` -- empirical IC-regret as the max unilateral
utility gain over a sampled misreport grid; used by ``regretnet`` and
``liu_amd_llm``.
"""
from __future__ import annotations

import numpy as np

__all__ = [
    "MISREPORT_GRID",
    "auction_ic_regret",
    "uniform_value_profiles",
]

# Shared misreport grid: candidate reports each agent tries, on the unit range
# every benchmark here normalises to.
MISREPORT_GRID: tuple[float, ...] = tuple(
    round(float(x), 4) for x in np.linspace(0.0, 1.0, 21)
)


def uniform_value_profiles(n: int, samples: int = 64, seed: int = 0) -> np.ndarray:
    """`samples` i.i.d. uniform[0,1] true-value vectors of length `n`."""
    return np.random.default_rng(seed).random((samples, n))


def auction_ic_regret(alloc_fn, pay_fn, value_profiles,
                      misreport_grid=MISREPORT_GRID) -> float:
    """Empirical IC-regret for a single-item-style auction.

    ``alloc_fn`` / ``pay_fn`` map a length-n report vector to a length-n array of
    allocation probabilities / payments.  ``value_profiles`` is an iterable of
    true length-n value vectors.  Returns

        max(0, max over (profile, agent i, misreport b) of
                u_i(b, v_-i) - u_i(v))   with   u_i = alloc_i * v_i - pay_i.

    0.0 means no profitable unilateral deviation was found on the grid.
    """
    worst = 0.0
    for v in value_profiles:
        v = np.asarray(v, dtype=float)
        n = v.shape[0]
        a0 = np.asarray(alloc_fn(v), dtype=float)
        p0 = np.asarray(pay_fn(v), dtype=float)
        truth_u = a0 * v - p0
        for i in range(n):
            for b in misreport_grid:
                r = v.copy()
                r[i] = b
                a = np.asarray(alloc_fn(r), dtype=float)
                p = np.asarray(pay_fn(r), dtype=float)
                gain = float((a[i] * v[i] - p[i]) - truth_u[i])
                if gain > worst:
                    worst = gain
    return worst
