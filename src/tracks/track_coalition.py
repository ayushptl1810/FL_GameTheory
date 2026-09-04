"""Track 5 — coalition / Shapley verification (k <= 3).

Tier A: symbolic — the stated shapley_formula_latex *is* the Shapley value.
Tier B: numeric — core / IR / payment on an enumerated characteristic function.

VERIFIED only when Tier A and Tier B both pass. Anything unrecognised or
undecidable -> MANUAL. Fail-closed default. No architect/LLM imports.
"""
from __future__ import annotations

import math
from itertools import combinations, permutations

from tracks import VerificationResult

_MAX_N = 3


def _all_subsets(n: int):
    for k in range(n + 1):
        for c in combinations(range(1, n + 1), k):
            yield frozenset(c)


def _parse_coalition_values(raw: dict, n: int) -> dict[frozenset[int], float]:
    if n > _MAX_N:
        raise ValueError(f"coalition_n={n}: need n <= 3")
    parsed: dict[frozenset[int], float] = {}
    for key, val in (raw or {}).items():
        members = frozenset(int(p) for p in str(key).split(",") if p.strip())
        try:
            parsed[members] = float(val)
        except (TypeError, ValueError):
            raise ValueError(f"coalition value for {key!r} is not numeric: {val!r}")
    for s in _all_subsets(n):
        if s not in parsed:
            raise ValueError(f"coalition_values missing subset {sorted(s)}")
    return parsed


def _shapley_from_values(values: dict[frozenset[int], float], n: int) -> dict[int, float]:
    phi = {i: 0.0 for i in range(1, n + 1)}
    for order in permutations(range(1, n + 1)):
        prefix: set[int] = set()
        for i in order:
            before = frozenset(prefix)
            after = frozenset(prefix | {i})
            phi[i] += values[after] - values[before]
            prefix.add(i)
    fact = math.factorial(n)
    return {i: phi[i] / fact for i in phi}
