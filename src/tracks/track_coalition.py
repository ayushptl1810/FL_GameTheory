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


def _tier_b_numeric_core(
    values: dict[frozenset[int], float],
    n: int,
    stated_payments: dict[int, float] | None,
) -> tuple[bool, bool, list[str]]:
    phi = _shapley_from_values(values, n)
    conds: list[str] = []
    tol = 1e-9

    core_ok = True
    for s in _all_subsets(n):
        if not s:
            continue
        payoff = sum(phi[i] for i in s)
        vs = values[s]
        ok = payoff >= vs - tol
        core_ok &= ok
        conds.append(
            f"core S={sorted(s)}: sum phi={payoff:.6g} >= v(S)={vs:.6g} -> "
            f"{'ok' if ok else 'VIOLATED'}"
        )

    ir_ok = True
    for i in range(1, n + 1):
        vi = values[frozenset({i})]
        ok = phi[i] >= vi - tol
        ir_ok &= ok
        conds.append(
            f"IR i={i}: phi={phi[i]:.6g} >= v({{{i}}})={vi:.6g} -> "
            f"{'ok' if ok else 'VIOLATED'}"
        )

    if stated_payments is not None:
        for i in range(1, n + 1):
            match = math.isclose(phi[i], stated_payments.get(i, float("nan")), abs_tol=1e-6)
            core_ok &= match
            conds.append(
                f"payment i={i}: stated={stated_payments.get(i)} vs Shapley={phi[i]:.6g} -> "
                f"{'match' if match else 'MISMATCH'}"
            )

    return core_ok, ir_ok, conds
