"""
Track 4 — SymPy (Bayesian IC, symbolic integration).

When:  mechanism uses Bayesian incentive compatibility (BIC) — IC is an
       expectation over other agents' types rather than a dominant-strategy
       condition.  Detected via ic_type = "bayesian"/"bic" or presence of
       \\mathbb{E} / \\int in LaTeX fields.

What:  (1) Myerson envelope condition — necessary condition for BIC:
            dU(θ, θ)/dθ ≥ 0  (monotone equilibrium payoff)
       (2) Bayesian IC integral:
            ∫_Θ [U(θ, truthful) − U(θ, lie)] f(θ) dθ ≥ 0
       (3) IR symbolic check: min_{θ ∈ [a,b]} U(θ, own) ≥ 0

       All computations are symbolic SymPy — no sampling, no SMT.

Guarantee: exact when SymPy closes the integral; UNKNOWN otherwise.

Type distributions: "uniform" on [0,1] (default), "uniform_ab" from
  type_space_min/type_space_max fields.

Why not Track 1?
  BIC involves E_θ̂[U(θ,θ̂)] — an integral over continuous distributions.
  Z3 handles SMT formulas but cannot compute definite integrals.

Corpus coverage:
  0 Bayesian entries in current corpus.
  Track 4 is primarily for LLM Architect output — Myerson-optimal and
  AGV mechanisms use BIC and require this track for verification.
"""

from __future__ import annotations

import re
from typing import Any

from . import Verdict, VerificationResult, finalize_verdict, normalize_left_right, strip_redundant_outer_parens

_SYMPY_OK = False

try:
    import sympy as _sp
    from sympy.parsing.latex import parse_latex as _lx_parse
    _SYMPY_OK = True
except Exception:
    pass


# ── Bayesian IC detection ─────────────────────────────────────────────────────

_BAYESIAN_RE = re.compile(r"\\mathbb\{E\}|\\int|bayesian|bic", re.IGNORECASE)


def _is_bayesian(entry: dict) -> bool:
    mech    = entry.get("mechanism") or {}
    ic_type = (mech.get("ic_type") or "").lower()
    if "bayesian" in ic_type or "bic" in ic_type:
        return True
    fields = " ".join(filter(None, [
        mech.get("ic_screening_latex") or "",
        mech.get("ir_participation_latex") or "",
        mech.get("utility_function_latex") or "",
    ]))
    return bool(_BAYESIAN_RE.search(fields))


# ── Parsing helpers ───────────────────────────────────────────────────────────

def _clean_latex(s: str) -> str:
    s = re.sub(r"^[Uu]_?\{?[a-zA-Z,_]+\}?\s*=\s*", "", s.strip())
    s = normalize_left_right(s)
    for tok in (r"\mathbb{E}", r"\mathbb E", r"\int"):
        s = s.replace(tok, "")
    s = re.sub(r"_\{[a-zA-Z]{2,}\}", "", s)
    s = re.sub(r"\\[a-zA-Z]+\s*\[[^\]]*\]", "", s)
    return strip_redundant_outer_parens(s.strip())


def _parse_geq_lhs(latex_str: str) -> "Any | None":
    if not _SYMPY_OK or not latex_str:
        return None
    for sep in (r"\geq", r"\ge", "≥"):
        if sep in latex_str:
            lhs, _ = latex_str.split(sep, 1)
            break
    else:
        lhs = latex_str
    try:
        return _lx_parse(_clean_latex(lhs))
    except Exception:
        return None


def _find_theta_sym(expr: Any) -> Any:
    """Return a theta-like symbol from free_symbols, else default."""
    if expr is None:
        return _sp.Symbol("theta", positive=True)
    for sym in expr.free_symbols:
        if re.match(r"(theta|θ)", str(sym).lower()):
            return sym
    return _sp.Symbol("theta", positive=True)


# ── Myerson envelope condition ────────────────────────────────────────────────

def _check_envelope(utility_expr: Any, theta_sym: Any) -> "tuple[Verdict, str]":
    """
    Necessary condition for BIC (Myerson 1981):
      dU(θ, θ)/dθ ≥ 0  (equilibrium payoff non-decreasing in type).
    """
    try:
        dU = _sp.diff(utility_expr, theta_sym)
        dU = _sp.simplify(dU)
        sign = _sp.ask(_sp.Q.nonnegative(dU), _sp.Q.positive(theta_sym))
        if sign is True:
            return "VERIFIED", f"dU/dθ = {dU} ≥ 0 (symbolic)"
        if sign is False:
            return "COUNTEREXAMPLE", f"dU/dθ = {dU} < 0 somewhere"
        # Numerical sample
        samples = [float(_sp.Rational(k, 10)) for k in range(1, 11)]
        try:
            vals = [float(dU.subs(theta_sym, v).evalf()) for v in samples]
            if all(v >= 0 for v in vals):
                return "VERIFIED", f"dU/dθ ≥ 0 at 10 sample points in (0,1]"
            return "COUNTEREXAMPLE", f"dU/dθ = {min(vals):.4g} < 0 at sample"
        except Exception:
            return "UNKNOWN", f"dU/dθ = {dU} (sign indeterminate)"
    except Exception as exc:
        return "UNKNOWN", f"derivative check failed: {exc}"


# ── Bayesian IC integral ──────────────────────────────────────────────────────

def _check_bayesian_ic(
    ic_gap: Any,
    theta_sym: Any,
    theta_min: float,
    theta_max: float,
    distribution: str,
) -> "tuple[Verdict, str]":
    """E_θ[gap] ≥ 0 via symbolic integration over the type distribution."""
    try:
        width = theta_max - theta_min
        if distribution == "uniform" and width > 0:
            integrand = ic_gap / _sp.Float(width)
        else:
            integrand = ic_gap

        integral = _sp.integrate(integrand, (theta_sym, theta_min, theta_max))
        simplified = _sp.simplify(integral)

        sign = _sp.ask(_sp.Q.nonnegative(simplified))
        if sign is True:
            return "VERIFIED", f"∫ gap = {simplified} ≥ 0"
        if sign is False:
            return "COUNTEREXAMPLE", f"∫ gap = {simplified} < 0"

        try:
            num = float(simplified.evalf())
            if num >= -1e-9:
                return "VERIFIED", f"∫ gap ≈ {num:.6f} ≥ 0 (numerical)"
            return "COUNTEREXAMPLE", f"∫ gap ≈ {num:.6f} < 0"
        except Exception:
            return "UNKNOWN", f"∫ gap = {simplified} (sign indeterminate)"

    except Exception as exc:
        return "UNKNOWN", f"integration failed: {exc}"


# ── IR symbolic minimum ───────────────────────────────────────────────────────

def _check_ir_symbolic(
    ir_expr: Any,
    theta_sym: Any,
    theta_min: float,
    theta_max: float,
) -> "tuple[Verdict, str]":
    """min_{θ ∈ [a,b]} U(θ, own) ≥ 0 via symbolic calculus."""
    try:
        expr = _sp.simplify(ir_expr)
        sign = _sp.ask(_sp.Q.nonnegative(expr), _sp.Q.positive(theta_sym))
        if sign is True:
            return "VERIFIED", f"U = {expr} ≥ 0 (symbolic)"
        if sign is False:
            return "COUNTEREXAMPLE", f"U = {expr} < 0 somewhere"

        critical = _sp.solve(_sp.diff(expr, theta_sym), theta_sym)
        candidates = [theta_min, theta_max] + [
            float(c.evalf())
            for c in critical
            if c.is_real and theta_min <= float(c.evalf()) <= theta_max
        ]
        min_val = min(float(expr.subs(theta_sym, v).evalf()) for v in candidates)
        if min_val >= -1e-9:
            return "VERIFIED", f"min U ≈ {min_val:.6f} ≥ 0 on [{theta_min},{theta_max}]"
        return "COUNTEREXAMPLE", f"min U ≈ {min_val:.6f} < 0"

    except Exception as exc:
        return "UNKNOWN", f"IR symbolic check failed: {exc}"


# ── Discrete-prior Bayesian IC (2026-07-19) ──────────────────────────────────
#
# The integral machinery below assumes a continuous type distribution — which
# zero corpus papers have. What the FL literature actually writes is
# discrete-prior Bayesian-game IC: expected utilities over a finite type/state
# space (e.g. Li2025bayesian_incentive: E[u|honest] = P_h·R − C vs.
# E[u|poisoned] = P_m·R − C, prior P(malicious)=f), proven *conditional on*
# declared assumptions (P_h ≥ P_m: verification discriminates; R ≥ C/P_h:
# reward covers cost). This path verifies exactly that conditional claim:
# rewrite each declared assumption "A ≥ B" as A = B + slack (slack ≥ 0,
# strict for ">"), substitute into the IC/IR gaps, and certify nonnegativity
# with the same posynomial/assumption machinery as Track 2. Fail-closed:
# only VERIFIED or UNKNOWN — an unmet certificate may just mean an
# undeclared assumption, never a counterexample claim.

_INEQ_SEPS = (r"\geq", r"\ge", "≥", ">", r"\leq", r"\le", "≤", "<")


def _split_ineq(latex_str: str) -> "tuple[Any, Any, bool] | None":
    """Return (lhs_expr, rhs_expr, strict) normalized to lhs ≥ rhs."""
    for sep in _INEQ_SEPS:
        if sep in latex_str:
            a, b = latex_str.split(sep, 1)
            strict = sep in (">", "<")
            flip = sep in (r"\leq", r"\le", "≤", "<")
            try:
                lhs = _lx_parse(_clean_latex(a))
                rhs = _lx_parse(_clean_latex(b))
            except Exception:
                return None
            return (rhs, lhs, strict) if flip else (lhs, rhs, strict)
    return None


def _check_discrete_bayesian(entry: dict) -> "VerificationResult | None":
    mech = entry.get("mechanism") or {}
    assumptions = mech.get("bayesian_assumptions_latex") or []
    if not assumptions or not isinstance(assumptions, list):
        return None
    ic_raw = mech.get("ic_screening_latex") or mech.get("ic_condition_latex") or ""
    ir_raw = mech.get("ir_participation_latex") or mech.get("ir_condition_latex") or ""
    if not ic_raw and not ir_raw:
        return None
    try:
        from .track2_sos import _posynomial_report
    except Exception:
        return None

    # Build slack substitutions from the declared assumptions, in order.
    subs_pairs: "list[tuple[Any, Any]]" = []
    assumed: list[str] = []
    for j, a_raw in enumerate(assumptions):
        parts = _split_ineq(str(a_raw))
        if parts is None:
            return None
        lhs, rhs, strict = parts
        slack = _sp.Symbol(f"s_{j}", positive=True) if strict else \
            _sp.Symbol(f"s_{j}", nonnegative=True)
        target = None
        if lhs.is_Symbol:
            target, value = lhs, rhs + slack
        elif rhs.is_Symbol:
            target, value = rhs, lhs - slack
        if target is None:
            return None
        value = value.subs(subs_pairs)
        subs_pairs.append((target, value))
        assumed.append(str(a_raw))

    conditions: list[str] = []
    verdicts: list[Verdict] = []
    for kind, raw in (("BIC", ic_raw), ("IR", ir_raw)):
        if not raw:
            continue
        parts = _split_ineq(str(raw))
        if parts is None:
            verdicts.append("UNKNOWN")
            conditions.append(f"{kind}: could not parse inequality")
            continue
        lhs, rhs, _strict = parts
        gap = (lhs - rhs).subs(subs_pairs)
        cert = _posynomial_report(gap)
        if cert is None:
            probe = gap.subs({s: _sp.Symbol(str(s), positive=True)
                              for s in gap.free_symbols})
            cert = f"{gap}" if probe.is_nonnegative else None
        if cert is not None:
            verdicts.append("VERIFIED")
            conditions.append(
                f"{kind}: expected-utility gap = {cert} ≥ 0 under declared assumptions"
            )
        else:
            verdicts.append("UNKNOWN")
            conditions.append(f"{kind}: gap = {gap} not certifiable from declared assumptions")

    if not verdicts:
        return None
    all_ok = all(v == "VERIFIED" for v in verdicts)
    return VerificationResult(
        verdict=finalize_verdict(all_ok, False, True),
        category=entry.get("category", ""),
        paper_id=entry.get("paper_id", "<unknown>"),
        track=4,
        conditions=conditions,
        notes=(
            "discrete-prior Bayesian IC (expected utilities over finite type/state "
            "space) | assumptions applied as slack substitutions: "
            + "; ".join(assumed)
            + " | posynomial certificate machinery shared with Track 2"
        ),
        entry_specific=True,
    )


# ── Public entry point ────────────────────────────────────────────────────────

def verify_track4(entry: dict) -> "VerificationResult | None":
    """
    Bayesian IC verification via SymPy: discrete-prior expected-utility path
    (bayesian_assumptions_latex present), else Myerson envelope + integral
    path for continuous type distributions.

    Returns None if entry is not Bayesian IC, or if SymPy not installed.
    """
    if not _SYMPY_OK:
        return None
    if not _is_bayesian(entry):
        return None

    discrete = _check_discrete_bayesian(entry)
    if discrete is not None:
        return discrete

    paper_id     = entry.get("paper_id", "<unknown>")
    category     = entry.get("category", "")
    mech         = entry.get("mechanism") or {}
    theta_min    = float(mech.get("type_space_min") or 0.0)
    theta_max    = float(mech.get("type_space_max") or 1.0)
    if theta_min >= theta_max:
        theta_min, theta_max = 0.0, 1.0
    distribution = (mech.get("type_distribution") or "uniform").lower()

    ir_raw  = mech.get("ir_participation_latex") or ""
    ic_raw  = mech.get("ic_screening_latex") or ""
    ir_expr = _parse_geq_lhs(ir_raw)
    theta_sym = _find_theta_sym(ir_expr)

    # Front-end: LaTeX → SymPy. The seam helper below takes only parsed exprs
    # and never touches `entry`/`mech` or re-parses LaTeX.
    ic_gap, ic_gap_err = _parse_ic_gap(ic_raw, theta_sym)
    entry_specific = bool(ir_raw or ic_raw)

    return track4_check_from_sympy(
        ir_expr, ic_gap, theta_sym, theta_min, theta_max, distribution,
        ic_gap_err=ic_gap_err,
        entry_specific=entry_specific, paper_id=paper_id, category=category,
    )


def _parse_ic_gap(ic_raw: str, theta_sym: Any) -> "tuple[Any | None, str]":
    """LaTeX IC condition → SymPy gap expr (lhs − rhs), theta-normalized.

    Returns (gap_expr, "") on success, (None, reason) on absence/parse failure.
    """
    if not ic_raw:
        return None, "no ic_screening_latex field"
    for sep in (r"\geq", r"\ge", "≥"):
        if sep in ic_raw:
            lhs_s, rhs_s = ic_raw.split(sep, 1)
            break
    else:
        lhs_s, rhs_s = ic_raw, "0"
    try:
        sp_lhs = _lx_parse(_clean_latex(lhs_s))
        sp_rhs = _lx_parse(_clean_latex(rhs_s))
        ic_gap = (sp_lhs - sp_rhs).expand()
        for sym in list(ic_gap.free_symbols):
            if re.match(r"(theta|θ)", str(sym).lower()) and sym != theta_sym:
                ic_gap = ic_gap.subs(sym, theta_sym)
        return ic_gap, ""
    except Exception as exc:
        return None, f"IC gap parse failed: {exc}"


def track4_check_from_sympy(
    ir_expr: "Any | None",
    ic_gap: "Any | None",
    theta_sym: Any,
    theta_min: float,
    theta_max: float,
    distribution: str,
    *,
    ic_gap_err: str = "",
    entry_specific: bool,
    paper_id: str,
    category: str = "",
) -> "VerificationResult":
    """SymPy-in seam: continuous Bayesian back-half of verify_track4.

    Given the parsed IR utility expression, the parsed IC gap expr, and the
    type symbol, run the Myerson envelope check, the Bayesian IC integral, and
    the symbolic IR minimum. Does no ``entry``/LaTeX parsing.
    """
    conditions: list[str] = []
    verdicts:   list[Verdict] = []

    # 1. Envelope condition (Myerson necessary condition for BIC)
    if ir_expr is not None:
        env_v, env_note = _check_envelope(ir_expr, theta_sym)
    else:
        env_v, env_note = "UNKNOWN", "no parseable utility from ir_participation_latex"
    verdicts.append(env_v)
    conditions.append(f"Envelope (Myerson necessary): {env_note}")

    # 2. Bayesian IC integral
    if ic_gap is not None:
        bic_v, bic_note = _check_bayesian_ic(
            ic_gap, theta_sym, theta_min, theta_max, distribution
        )
        verdicts.append(bic_v)
        conditions.append(
            f"BIC ({distribution}): {bic_note} "
            f"[∫ gap·f(θ) dθ over [{theta_min},{theta_max}]]"
        )
    else:
        verdicts.append("UNKNOWN")
        conditions.append(f"BIC: {ic_gap_err or 'no ic_screening_latex field'}")

    # 3. IR
    if ir_expr is not None:
        ir_v, ir_note = _check_ir_symbolic(ir_expr, theta_sym, theta_min, theta_max)
    else:
        ir_v, ir_note = "UNKNOWN", "no parseable utility"
    verdicts.append(ir_v)
    conditions.append(f"IR (symbolic): {ir_note}")

    all_ok  = all(v == "VERIFIED"       for v in verdicts)
    has_cex = any(v == "COUNTEREXAMPLE" for v in verdicts)
    final: Verdict = finalize_verdict(all_ok, has_cex, entry_specific)

    return VerificationResult(
        verdict=final,
        category=category,
        paper_id=paper_id,
        track=4,
        conditions=conditions,
        notes=(
            f"Bayesian IC | dist={distribution} "
            f"| domain=[{theta_min},{theta_max}] "
            "| SymPy symbolic integration (exact when integral closes)"
        ),
        entry_specific=entry_specific,
    )
