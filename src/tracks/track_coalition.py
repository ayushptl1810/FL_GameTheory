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


# --- Tier A: symbolic identity -------------------------------------------------
# NOTE: sympy's parse_latex cannot handle `\sum_{...}` with `|S|!` factorial
# notation (verified: LaTeXParsingError on the standard Shapley formula). So the
# POSITIVE check below is STRUCTURAL, per the task-4 brief Step 4 fallback:
#   - the marginal term  v(S \cup \{i\}) - v(S)   (whitespace-insensitive), AND
#   - a Shapley weight    |S|!(n-|S|-1)!/n!  or  (|S|-1)!(n-|S|)!/n!
# The fail-closed rejection guards (\binom / \hat / K-normalization / approx)
# still run first, so a binom-normalized approximation returns (False, ...).
import re

_MARGINAL_RE = re.compile(
    r"v\(S\\cup\\?\{[ij]\\?\}\)-v\(S\)"
)
_WEIGHT_RES = (
    re.compile(r"\|S\|!\(n-\|S\|-1\)!\}?\{?n!"),          # |S|!(n-|S|-1)! / n!
    re.compile(r"\(\|S\|-1\)!\(n-\|S\|\)!\}?\{?n!"),       # (|S|-1)!(n-|S|)! / n!
)


def _tier_a_symbolic_identity(shapley_latex: str, n: int) -> tuple[bool, str]:
    if not shapley_latex or not str(shapley_latex).strip():
        return False, "empty formula"
    raw = str(shapley_latex)
    low = raw.lower()
    # Fail-closed structural guards: tokens the exact Shapley value never has.
    for bad in ("\\binom", "\\hat", "approx", "k \\sum", r"k\sum"):
        if bad in low:
            return False, f"formula contains {bad.strip()!r} — not the exact Shapley value"
    compact = re.sub(r"\s+", "", raw)
    if not _MARGINAL_RE.search(compact):
        return False, "no marginal-contribution term v(S ∪ {i}) − v(S) found"
    if not any(rx.search(compact) for rx in _WEIGHT_RES):
        return False, "no exact Shapley weight |S|!(n−|S|−1)!/n! found"
    return True, "formula matches the exact Shapley value (structural: marginal term + Shapley weight)"


def _manual(pid: str, note: str, *, entry_specific: bool = False) -> VerificationResult:
    return VerificationResult(
        verdict="MANUAL", category="Shapley", paper_id=pid, track=5,
        notes=note, entry_specific=entry_specific,
    )


def verify_coalition(entry: dict) -> VerificationResult:
    pid = entry.get("paper_id", "<unknown>")
    m = entry.get("mechanism") or {}
    formula = m.get("shapley_formula_latex")

    if not formula or not str(formula).strip():
        return _manual(pid, "no Shapley formula in the paper — cannot verify a "
                            "coalition mechanism without a stated payment rule")

    n = m.get("coalition_n")
    if not isinstance(n, int) or n > _MAX_N or n < 1:
        return _manual(pid, f"k > 3 or coalition size not stated (coalition_n={n!r}) "
                            "— enumeration intractable")

    is_shapley, detail = _tier_a_symbolic_identity(formula, n)
    if not is_shapley:
        return _manual(pid, f"formula is not the exact Shapley value: {detail}")

    raw_values = m.get("coalition_values")
    if not raw_values:
        return _manual(
            pid,
            "Tier A passed — formula confirmed Shapley-shaped — but no numeric "
            "v(S) in the paper to verify IC/IR/core",
        )

    try:
        values = _parse_coalition_values(raw_values, n)
    except ValueError as e:
        return _manual(pid, f"coalition_values unusable: {e}")

    stated = m.get("coalition_payments")
    stated_payments = ({int(k): float(v) for k, v in stated.items()} if stated else None)

    core_ok, ir_ok, conds = _tier_b_numeric_core(values, n, stated_payments)
    tier_a_line = f"Tier A: {detail}"

    if core_ok and ir_ok:
        return VerificationResult(
            verdict="VERIFIED", category="Shapley", paper_id=pid, track=5,
            conditions=[tier_a_line, *conds], entry_specific=True,
            notes="Tier A (Shapley identity) + Tier B (core, IR) both hold",
        )
    if not core_ok:
        violated = [c for c in conds if "VIOLATED" in c or "MISMATCH" in c]
        return VerificationResult(
            verdict="COUNTEREXAMPLE", category="Shapley", paper_id=pid, track=5,
            conditions=[tier_a_line, *conds], entry_specific=True,
            notes="core / payment violated: " + "; ".join(violated),
        )
    return _manual(pid, "core holds but individual rationality is violated — "
                        "check the paper's participation model")
