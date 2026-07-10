#!/usr/bin/env python3
"""
Z3-based verifier for FL incentive mechanism IC/IR conditions.

Two verification modes per entry:
  1. Entry-specific (LaTeX): Parses ic_screening_latex / ir_participation_latex
     from the corpus and converts to Z3 constraints.  Triggered whenever both
     fields are present.  Binding direction: IR at lowest type (type-0), upward
     adjacent IC — consistent with papers that treat θ as a quality/ability
     parameter (higher index = higher quality).
  2. Template (parametric): Symbolic parametric model for the mechanism class.
     Verifies that the structural properties hold for all parameter values.
     Binding direction for Contract: IR at highest-cost type, downward IC —
     consistent with the cost-heterogeneity model (higher θ = higher cost).

Supported categories:
  VCG        — threshold-payment procurement/forward auction (DSIC by
               construction; template verifies IR + IC-A + IC-B for all c,t)
  Contract   — discrete-type screening; LaTeX path when both IC/IR fields
               present, else parametric linear-cost template
  Stackelberg — leader/follower backward induction; verifies follower IR only
               (NOT DSIC — Stackelberg is an equilibrium concept, not DSIC)
  Shapley    — stub (Roberts' Theorem makes Z3 verification intractable)

Usage:
    python src/verifier.py entries/Cong2020vcg.json
    python src/verifier.py entries/Kang2019contract_mobile.json
    python src/verifier.py entries/             # batch all entries
    python src/verifier.py entries/ --gold      # gold-tier only
    python src/verifier.py corpus.json          # full corpus list
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

try:
    from z3 import (
        And, Or, Real, RealVal, Solver,
        sat, unsat, unknown,
    )
except ImportError:
    sys.exit("Install z3-solver:  .venv/bin/pip install z3-solver")

Verdict = Literal["VERIFIED", "COUNTEREXAMPLE", "UNKNOWN", "UNSUPPORTED"]
_RAG_ONLY = frozenset({"RL", "Valuation", "Naive"})


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class VerificationResult:
    verdict: Verdict
    category: str
    paper_id: str
    conditions: list[str] = field(default_factory=list)
    counterexample: dict[str, str] | None = None
    notes: str = ""
    entry_specific: bool = False  # True when verified from extracted LaTeX fields

    def __str__(self) -> str:
        tick = "✓" if self.verdict == "VERIFIED" else "·"
        lines = [
            f"{'─' * 56}",
            f"Paper    : {self.paper_id}",
            f"Category : {self.category}",
            f"Verdict  : {self.verdict}",
        ]
        for c in self.conditions:
            lines.append(f"  {tick} {c}")
        if self.counterexample:
            lines.append("Counterex:")
            for k, v in self.counterexample.items():
                lines.append(f"    {k} = {v}")
        if self.notes:
            lines.append(f"Notes    : {self.notes}")
        return "\n".join(lines)


# ── Dispatcher ────────────────────────────────────────────────────────────────

def verify(entry: dict) -> VerificationResult:
    """Verify IC/IR for a corpus entry. Dispatches by category."""
    category = entry.get("category", "")
    paper_id = entry.get("paper_id", "<unknown>")

    if category in _RAG_ONLY:
        return VerificationResult(
            verdict="UNSUPPORTED",
            category=category,
            paper_id=paper_id,
            notes=f"'{category}' is RAG-only — no formal mechanism proofs expected.",
        )

    dispatch = {
        "VCG": _verify_vcg,
        "Contract": _verify_contract,
        "Stackelberg": _verify_stackelberg,
        "Shapley": _verify_shapley,
    }
    fn = dispatch.get(category)
    if fn is None:
        return VerificationResult(
            verdict="UNSUPPORTED", category=category, paper_id=paper_id,
            notes=f"No verifier for '{category}'.",
        )
    return fn(entry)


# ── VCG payment-form classifier ───────────────────────────────────────────────

import re as _re_vcg  # noqa: E402 (used before LaTeX section)

# Each pattern group maps a regex to a VCG payment form label.
# Matched in order; first match wins.
_VCG_FORM_CHECKS: list[tuple[str, str]] = [
    # Clarke pivot / Groves: externality sum ∑_{j≠i} or ∑_{k≠i}
    (r'\\neq\s*[a-zA-Z]',          "clarke_pivot"),
    # Marginal welfare: set-minus operator or SW difference (x* vs z*)
    (r'\\setminus',                 "marginal_welfare"),
    (r'[Ss]\(z\^',                  "marginal_welfare"),
    # Critical bid / threshold: \min or next-rank subscript (+1)
    (r'\\min',                      "critical_bid"),
    (r'\+1[}_]',                    "critical_bid"),
    # Budget-split: fixed budget B divided by performance
    (r'\\frac\s*\{B\}',            "budget_split"),
]

_VCG_FORM_CLAIMS: dict[str, str] = {
    "clarke_pivot":     "Clarke pivot / Groves scheme — DSIC by Groves theorem",
    "marginal_welfare": "marginal welfare / VCG procurement form — DSIC by Groves theorem",
    "critical_bid":     "critical-bid / threshold pricing — DSIC by Myerson characterization",
    "budget_split":     "budget-split payment (non-standard VCG; Groves theorem does not apply)",
    "unclassified":     "payment rule does not match a standard VCG form; DSIC is paper-asserted",
    "none":             "no payment_rule_latex extracted; DSIC verified via template model only",
}


def _classify_vcg_payment(payment_rule: str) -> str:
    """Return the VCG payment form label for this payment_rule_latex string."""
    if not (payment_rule or "").strip():
        return "none"
    for pat, label in _VCG_FORM_CHECKS:
        if _re_vcg.search(pat, payment_rule):
            return label
    return "unclassified"


# ── VCG ───────────────────────────────────────────────────────────────────────

def _verify_vcg(entry: dict) -> VerificationResult:
    """
    Verify IC (dominant-strategy) and IR for a threshold-payment VCG mechanism.

    Template model: procurement/forward auction with threshold payment.
      - Client i has private cost c_i > 0.
      - Winners pay threshold t (the (K+1)-th lowest cost).
      - Utility: u_i = t − c_i  (winner), 0  (loser).

    Additionally classifies the payment_rule_latex against known VCG forms
    (Clarke pivot, marginal welfare, critical bid) via regex.  When a form is
    confirmed, entry_specific=True signals that the paper's actual payment rule
    was checked — not just the template.

    Z3 checks (all via UNSAT of negation):
      IR   : t − c_i ≥ 0  when c_i < t  (winner by definition has c_i < t).
      IC-A : Winner cannot gain by overbidding (losing). Gain = 0 < t − c_i.
      IC-B : Loser cannot gain by underbidding (winning). Gain = t − c_i < 0.
    """
    mechanism    = entry.get("mechanism") or {}
    auction_type = mechanism.get("auction_type", "reverse")
    ic_type      = mechanism.get("ic_type", "dominant-strategy")
    paper_id     = entry.get("paper_id", "<unknown>")
    payment_rule = mechanism.get("payment_rule_latex") or ""

    vcg_form     = _classify_vcg_payment(payment_rule)
    form_note    = _VCG_FORM_CLAIMS[vcg_form]
    # Form confirmed = payment rule matches a standard VCG/Groves/Myerson form
    form_confirmed = vcg_form in ("clarke_pivot", "marginal_welfare", "critical_bid")

    c = Real("c")   # client's true cost
    t = Real("t")   # threshold payment

    conditions: list[str] = []
    notes: list[str]      = []
    verdicts: list[Verdict] = []
    counterexample: dict[str, str] | None = None

    def _check(solver: Solver, label: str, condition: str) -> Verdict:
        nonlocal counterexample
        result = solver.check()
        if result == unsat:
            v: Verdict = "VERIFIED"
        elif result == sat:
            v = "COUNTEREXAMPLE"
            if counterexample is None:
                m = solver.model()
                counterexample = {str(x): str(m[x]) for x in m}
        else:
            v = "UNKNOWN"
        verdicts.append(v)
        conditions.append(condition)
        notes.append(f"{label}: {v}")
        return v

    # IR
    s = Solver()
    s.add(c > 0, t > 0, c < t)   # winner (c_i < threshold)
    s.add(t - c < 0)              # violation attempt
    _check(s, "IR", "IR: u_i = t − c_i ≥ 0 for winners  (c_i < t by definition)")

    # IC-A: winner misreports high → loses → gains 0 instead of t−c > 0
    s = Solver()
    s.add(c > 0, t > 0, c < t)
    s.add(RealVal(0) > t - c)    # can losing be strictly better?
    _check(s, "IC-A", "IC-A: winner cannot gain by overbidding (losing intentionally)")

    # IC-B: loser misreports low → wins → gains t−c < 0
    s = Solver()
    s.add(c > 0, t > 0, c > t)   # loser (c_i > threshold)
    s.add(t - c > RealVal(0))    # can winning be profitable for a loser?
    _check(s, "IC-B", "IC-B: loser cannot gain by underbidding (winning at a loss)")

    all_ok  = all(v == "VERIFIED" for v in verdicts)
    has_cex = any(v == "COUNTEREXAMPLE" for v in verdicts)
    final: Verdict = "VERIFIED" if all_ok else ("COUNTEREXAMPLE" if has_cex else "UNKNOWN")

    return VerificationResult(
        verdict=final,
        category="VCG",
        paper_id=paper_id,
        conditions=conditions,
        counterexample=counterexample,
        notes=(" | ".join(notes)
               + f" | {form_note}"
               + f" | model: threshold-payment {auction_type} auction"
               + (f", ic_type={ic_type}" if ic_type != "dominant-strategy" else "")),
        entry_specific=form_confirmed,
    )



# ── LaTeX → Z3 pipeline (entry-specific Contract verification) ────────────────

import re as _re

_LATEX_OK = False
try:
    from sympy.parsing.latex import parse_latex as _lx_parse
    import sympy as _sp
    _LATEX_OK = True
except Exception:
    pass

_SUB_RE = _re.compile(r'_\{?([a-zA-Z,]+)\}?')


def _sp_to_z3(expr, cache: dict):
    """Convert SymPy polynomial expression to Z3 (no transcendentals)."""
    if isinstance(expr, _sp.core.numbers.Integer):
        return RealVal(int(expr))
    if isinstance(expr, (_sp.core.numbers.Float, _sp.core.numbers.Rational,
                          _sp.core.numbers.Half, _sp.core.numbers.One,
                          _sp.core.numbers.NegativeOne)):
        return RealVal(float(expr))
    if isinstance(expr, _sp.Symbol):
        name = str(expr)
        if name not in cache:
            cache[name] = Real(name)
        return cache[name]
    if isinstance(expr, _sp.Add):
        parts = [_sp_to_z3(a, cache) for a in expr.args]
        return sum(parts[1:], parts[0])
    if isinstance(expr, _sp.Mul):
        parts = [_sp_to_z3(a, cache) for a in expr.args]
        r = parts[0]
        for p in parts[1:]:
            r = r * p
        return r
    if isinstance(expr, _sp.Pow):
        b = _sp_to_z3(expr.args[0], cache)
        e2 = expr.args[1]
        if e2 == _sp.Integer(2):
            return b * b
        if e2 == _sp.Integer(-1):
            return RealVal(1) / b
        if isinstance(e2, _sp.Integer) and int(e2) > 0:
            r = RealVal(1)
            for _ in range(int(e2)):
                r = r * b
            return r
        raise ValueError(f"unsupported exponent {e2}")
    raise ValueError(f"unsupported SymPy node {type(expr).__name__}")


def _sub_index(sp_expr, old_sub: str, new_idx: int):
    """Replace all symbols with subscript old_sub with subscript new_idx."""
    subs = {}
    for sym in sp_expr.free_symbols:
        name = str(sym)
        m2 = _SUB_RE.search(name)
        if m2 and m2.group(1) == old_sub:
            subs[sym] = _sp.Symbol(_SUB_RE.sub(f'_{new_idx}', name, count=1))
    return sp_expr.subs(subs)


def _preprocess_contract_latex(s: str) -> str:
    """
    Normalise Contract LaTeX before cleaning and SymPy parsing.

    Must be called BEFORE _clean so that closing parens are still present.

    Transforms applied in order:
    1. C_{total}(e_{X}) → cost_{X}   (abstract total cost as indexed symbol)
    2. Multi-letter word subscripts like E_{com}, C_{total} (leftovers) are
       removed — they are label constants, not type indices.  Single-letter
       subscripts are untouched.
    """
    # 1. Replace C_{total}(e_{X}) before the closing ) can be stripped
    s = _re.sub(r'C_\{total\}\(e_\{([a-zA-Z])\}\)', r'cost_{\1}', s)
    s = _re.sub(r'C_\{total\}\(e_([a-zA-Z])\)', r'cost_{\1}', s)
    # 2. Drop subscript labels with 2+ letters: E_{com} → E, C_{total} → C
    #    Single-letter subscripts (the type/contract indices) are preserved.
    s = _re.sub(r'_\{[a-zA-Z]{2,}\}', '', s)
    return s


def _try_contract_latex(entry: dict) -> "VerificationResult | None":
    """
    Entry-specific Contract verification: parses ic_screening_latex and
    ir_participation_latex into Z3, then verifies IC/IR using the paper's
    actual utility form (not the generic linear-cost template).

    Pre-processing:
      • C_{total}(e_k) → cost_k  (indexed abstract cost symbol)

    Subscript identification:
      • type_sub   : single subscript present in IR LHS (or IC LHS as fallback)
      • contract_sub: extra subscript present only in IC RHS

    Fallback: when IR LHS has no subscripts but IC LHS does (e.g. generic IR
    template + subscripted IC), IC LHS is used as the utility template and IR
    is verified without global constant terms that appear only in the IR field.

    Binding direction: IR at lowest type (type-0), adjacent upward IC.
    Returns None if parsing fails or the utility contains transcendentals.
    """
    if not _LATEX_OK:
        return None

    mech = entry.get("mechanism") or {}
    ir_raw = mech.get("ir_participation_latex") or ""
    ic_raw = mech.get("ic_screening_latex") or ""
    if not ir_raw or not ic_raw:
        return None

    def _split_geq(s: str):
        for sep in [r'\geq', r'\ge', '≥']:
            if sep in s:
                a, b = s.split(sep, 1)
                return a.strip(), b.strip()
        return None

    def _clean(s: str) -> str:
        s = _re.sub(r'^[Uu]_?\{?[a-zA-Z,_]+\}?\s*=\s*', '', s.strip())
        for tok in (r'\left(', r'\right)', r'\left', r'\right'):
            s = s.replace(tok, '')
        return s.strip().strip('()')

    ir_parts = _split_geq(ir_raw)
    ic_parts = _split_geq(ic_raw)
    if not ir_parts or not ic_parts:
        return None

    # Pre-process BEFORE _clean so closing parens in C_{total}(e_X) are intact
    ir_clean = _clean(_preprocess_contract_latex(ir_parts[0]))
    ic_rhs_clean = _clean(_preprocess_contract_latex(ic_parts[1]))
    ic_lhs_clean = _clean(_preprocess_contract_latex(ic_parts[0]))

    try:
        U_ir  = _lx_parse(ir_clean)
        U_rhs = _lx_parse(ic_rhs_clean)
    except Exception:
        return None

    def _get_sub(sym) -> "str | None":
        m2 = _SUB_RE.search(str(sym))
        return m2.group(1) if m2 else None

    lhs_subs = {_get_sub(s) for s in U_ir.free_symbols  if _get_sub(s)}
    rhs_subs = {_get_sub(s) for s in U_rhs.free_symbols if _get_sub(s)}

    # Fallback: IR LHS has no subscripts (generic template), use IC LHS instead
    ir_from_ic_lhs = False
    if len(lhs_subs) == 0:
        try:
            U_ic_lhs = _lx_parse(ic_lhs_clean)
            ic_lhs_subs = {_get_sub(s) for s in U_ic_lhs.free_symbols if _get_sub(s)}
            if len(ic_lhs_subs) == 1:
                U_ir = U_ic_lhs
                lhs_subs = ic_lhs_subs
                ir_from_ic_lhs = True
        except Exception:
            pass

    if len(lhs_subs) != 1:
        return None

    type_sub     = list(lhs_subs)[0]
    contract_sub = list(rhs_subs - {type_sub})
    if len(contract_sub) != 1:
        return None
    contract_sub = contract_sub[0]

    raw_n = mech.get("num_types")
    try:
        n = min(int(raw_n) if raw_n and str(raw_n).isdigit() else 3, 4)
    except (ValueError, TypeError):
        n = 3
    n = max(n, 2)

    paper_id = entry.get("paper_id", "<unknown>")
    cache: dict = {}

    def _U(type_k: int, contract_l: "int | None" = None):
        l = contract_l if contract_l is not None else type_k
        sp_expr = (
            _sub_index(U_ir, type_sub, type_k)
            if l == type_k
            else _sub_index(_sub_index(U_rhs, type_sub, type_k), contract_sub, l)
        )
        try:
            return _sp_to_z3(sp_expr, cache)
        except ValueError:
            return None

    for k in range(n):
        for l in range(n):
            if _U(k, l) is None:
                return None

    # Group indexed Z3 vars: base → {idx: z3.Real}
    indexed: dict = {}
    for name in cache:
        m2 = _re.match(r'^(.+)_(\d+)$', name)
        if m2:
            indexed.setdefault(m2.group(1), {})[int(m2.group(2))] = cache[name]

    # Positivity + strict ascending order for all indexed variable families
    preconds: list = []
    for base, vd in indexed.items():
        for v in vd.values():
            preconds.append(v > 0)
        for i in range(n - 1):
            if i in vd and i + 1 in vd:
                preconds.append(vd[i] < vd[i + 1])
    for name, var in cache.items():
        if not _re.match(r'.+_\d+$', name):
            preconds.append(var > 0)

    # Binding conditions: IR at lowest type, upward adjacent IC binding
    bind: list = [_U(0, 0) == RealVal(0)]
    for k in range(n - 1):
        bind.append(_U(k + 1, k + 1) == _U(k + 1, k))

    all_conds = preconds + bind
    conditions: list[str] = []
    verdicts:   list[str] = []
    counterexample: "dict[str, str] | None" = None

    # IR
    s = Solver()
    for c in all_conds:
        s.add(c)
    s.add(Or([_U(k, k) < RealVal(0) for k in range(n)]))
    r = s.check()
    ir_v: Verdict = "VERIFIED" if r == unsat else ("COUNTEREXAMPLE" if r == sat else "UNKNOWN")
    if ir_v == "COUNTEREXAMPLE":
        mdl = s.model()
        counterexample = {str(x): str(mdl[x]) for x in mdl}
    verdicts.append(ir_v)
    conditions.append("IR: U_i(own) ≥ 0  [entry-specific utility]")

    # IC
    s = Solver()
    for c in all_conds:
        s.add(c)
    ic_viols = [_U(k, k) < _U(k, l) for k in range(n) for l in range(n) if k != l]
    if ic_viols:
        s.add(Or(ic_viols))
    r = s.check()
    ic_v: Verdict = "VERIFIED" if r == unsat else ("COUNTEREXAMPLE" if r == sat else "UNKNOWN")
    if ic_v == "COUNTEREXAMPLE" and counterexample is None:
        mdl = s.model()
        counterexample = {str(x): str(mdl[x]) for x in mdl}
    verdicts.append(ic_v)
    conditions.append(f"IC: U_i(own) ≥ U_i(j) for all {n}×{n-1} pairs  [entry-specific utility]")

    all_ok  = all(v == "VERIFIED" for v in verdicts)
    has_cex = any(v == "COUNTEREXAMPLE" for v in verdicts)
    final: Verdict = "VERIFIED" if all_ok else ("COUNTEREXAMPLE" if has_cex else "UNKNOWN")

    # Soundness gate: when the IR utility was sourced from the IC LHS, global
    # cost terms present in the paper's actual IR (e.g. E_{com}) were silently
    # dropped.  Z3 proved U_simplified ≥ 0, but U_paper = U_simplified - E_com,
    # so the result gives no guarantee about the real IR.  Revert to template.
    if ir_from_ic_lhs:
        return None

    return VerificationResult(
        verdict=final,
        category="Contract",
        paper_id=paper_id,
        conditions=conditions,
        counterexample=counterexample,
        notes=(f"IR:{ir_v} IC:{ic_v} | LaTeX-parsed utility | n={n} (capped 4)"
               + " | binding: IR at type-0, adjacent upward IC"),
        entry_specific=True,
    )

# ── Contract ──────────────────────────────────────────────────────────────────

def _verify_contract(entry: dict) -> VerificationResult:
    """
    Template Contract verifier (cost-heterogeneity model).

    Model: n discrete types θ_0 < θ_1 < ... < θ_{n-1} (higher index = higher cost).
    Server offers menu {(e_i, R_i)}.  Linear utility: U_i(j) = R_j − θ_i · e_j.
    Effort ordering: e_0 > e_1 > ... > e_{n-1} (lower-cost type exerts more effort).

    Binding direction (cost model):
      IR  binds at highest-cost type:  R_{n-1} = θ_{n-1} · e_{n-1}
      IC  binds downward:              R_i = R_{i+1} + θ_i · (e_i − e_{i+1})

    Note: papers where higher type means higher ability/quality use the opposite
    binding direction (IR at type-0, upward IC).  Those entries are handled by
    _try_contract_latex when ic_screening_latex / ir_participation_latex are present.
    """
    # Try entry-specific LaTeX-based verification first whenever both fields exist.
    # The LaTeX path uses IR-at-type-0 + upward adjacent IC binding (quality model:
    # higher index = higher ability).  The template below uses IR-at-top + downward
    # IC binding (cost model: higher θ = higher cost).  These are complementary
    # models; the LaTeX path is preferred when the paper's own conditions are present.
    mech_fields = entry.get("mechanism", {})
    if mech_fields.get("ic_screening_latex") and mech_fields.get("ir_participation_latex"):
        result = _try_contract_latex(entry)
        if result is not None:
            return result

    mechanism = entry.get("mechanism", {})
    paper_id  = entry.get("paper_id", "<unknown>")

    raw_n   = mechanism.get("num_types", 3)
    n_types = 3 if not isinstance(raw_n, int) else min(max(raw_n, 2), 4)

    theta = [Real(f"θ{i}") for i in range(n_types)]
    e     = [Real(f"e{i}") for i in range(n_types)]

    # Domain: ordered types, positive values, monotone effort
    domain: list[Any] = []
    for i in range(n_types - 1):
        domain.append(theta[i] < theta[i + 1])
        domain.append(e[i] > e[i + 1])
    for i in range(n_types):
        domain.append(theta[i] > 0)
        domain.append(e[i] > 0)

    # Build reward schedule from binding conditions
    R: list[Any] = [None] * n_types
    R[n_types - 1] = theta[n_types - 1] * e[n_types - 1]          # IR binds at top
    for i in range(n_types - 2, -1, -1):
        R[i] = R[i + 1] + theta[i] * (e[i] - e[i + 1])            # downward IC binds

    def U(i: int, j: int) -> Any:
        return R[j] - theta[i] * e[j]

    conditions: list[str] = []
    notes: list[str]      = []
    verdicts: list[Verdict] = []
    counterexample: dict[str, str] | None = None

    # IR: all types get non-negative utility on own contract
    s = Solver()
    for c in domain:
        s.add(c)
    s.add(Or([U(i, i) < 0 for i in range(n_types)]))
    r = s.check()
    ir_v: Verdict = "VERIFIED" if r == unsat else ("COUNTEREXAMPLE" if r == sat else "UNKNOWN")
    if ir_v == "COUNTEREXAMPLE":
        m = s.model()
        counterexample = {str(x): str(m[x]) for x in m}
    verdicts.append(ir_v)
    conditions.append("IR: U_i(own contract) ≥ 0 for all types")
    notes.append(f"IR: {ir_v}")

    # IC: every type prefers own contract over every other
    s = Solver()
    for c in domain:
        s.add(c)
    ic_viols = [U(i, j) > U(i, i) for i in range(n_types) for j in range(n_types) if i != j]
    s.add(Or(ic_viols))
    r = s.check()
    ic_v: Verdict = "VERIFIED" if r == unsat else ("COUNTEREXAMPLE" if r == sat else "UNKNOWN")
    if ic_v == "COUNTEREXAMPLE" and counterexample is None:
        m = s.model()
        counterexample = {str(x): str(m[x]) for x in m}
    verdicts.append(ic_v)
    conditions.append("IC: U_i(own) ≥ U_i(j) for all type pairs i ≠ j")
    notes.append(f"IC: {ic_v}")

    all_ok  = all(v == "VERIFIED" for v in verdicts)
    has_cex = any(v == "COUNTEREXAMPLE" for v in verdicts)
    final: Verdict = "VERIFIED" if all_ok else ("COUNTEREXAMPLE" if has_cex else "UNKNOWN")

    return VerificationResult(
        verdict=final,
        category="Contract",
        paper_id=paper_id,
        conditions=conditions,
        counterexample=counterexample,
        notes=(" | ".join(notes)
               + f" | model: {n_types}-type linear-cost screening"
               + " (IR binding at top type, downward IC binding)"),
    )


# ── Stackelberg ───────────────────────────────────────────────────────────────

def _verify_stackelberg(entry: dict) -> VerificationResult:
    """
    Verify follower IR for a Stackelberg mechanism via Z3.

    Model: leader sets price p > 0; follower maximises quadratic utility
    U(e, p) = p·e − (1/2)·e².  Best response: e*(p) = p (from FOC p − e = 0).
    IR: U(e*(p), p) = (1/2)·p² ≥ 0 for all p > 0.

    Note: Stackelberg proves equilibrium existence, not DSIC. IC is omitted by design.
    """
    mechanism = entry.get("mechanism", {})
    paper_id  = entry.get("paper_id", "<unknown>")
    eq_exists = mechanism.get("equilibrium_existence", False)

    if not eq_exists:
        return VerificationResult(
            verdict="UNSUPPORTED",
            category="Stackelberg",
            paper_id=paper_id,
            notes="equilibrium_existence=False — cannot verify without a proved equilibrium.",
        )

    p = Real("p")
    U_star = p * p / RealVal(2)    # U(e*(p), p) = p² / 2

    s = Solver()
    s.add(p > 0)
    s.add(U_star < 0)              # try to violate IR

    ir_v: Verdict = "VERIFIED" if s.check() == unsat else "COUNTEREXAMPLE"
    cex: dict[str, str] | None = None
    if ir_v == "COUNTEREXAMPLE":
        m = s.model()
        cex = {str(x): str(m[x]) for x in m}

    return VerificationResult(
        verdict=ir_v,
        category="Stackelberg",
        paper_id=paper_id,
        conditions=["IR: U_follower(e*(p), p) = p²/2 ≥ 0 for all p > 0"],
        counterexample=cex,
        notes=(f"IR: {ir_v}"
               + " | model: quadratic follower utility U=pe−e²/2, best response e*=p"
               + " | IC omitted (Stackelberg solution concept ≠ DSIC)"),
    )


# ── Shapley (stub) ────────────────────────────────────────────────────────────

def _verify_shapley(entry: dict) -> VerificationResult:
    """
    Shapley IC/IR verification is intractable for general coalitional games
    (Roberts' Theorem: DSIC over arbitrary domains requires affine maximisers,
    which Shapley payments cannot satisfy in general).

    The extractor hard-gate (ic_proof_present / ir_proof_present) is the
    primary quality signal. Manual proof review is required for gold upgrade.
    """
    mechanism   = entry.get("mechanism", {})
    ic_present  = mechanism.get("ic_proof_present", False)
    ir_present  = mechanism.get("ir_proof_present", False)
    paper_id    = entry.get("paper_id", "<unknown>")

    return VerificationResult(
        verdict="UNSUPPORTED",
        category="Shapley",
        paper_id=paper_id,
        notes=(
            "Roberts' Theorem: Shapley IC/IR is intractable in Z3 for general domains. "
            f"Hard-gate: ic_proof_present={ic_present}, ir_proof_present={ir_present}."
        ),
    )


# ── Batch + CLI ───────────────────────────────────────────────────────────────

def verify_corpus(entries_dir: Path, gold_only: bool = False) -> list[VerificationResult]:
    results = []
    for path in sorted(entries_dir.glob("*.json")):
        entry = json.loads(path.read_text())
        if gold_only and entry.get("quality_tier") != "gold":
            continue
        if entry.get("category") in _RAG_ONLY:
            continue
        results.append(verify(entry))
    return results


def print_summary(results: list[VerificationResult]) -> None:
    counts: Counter[str] = Counter(r.verdict for r in results)
    total = len(results)

    # VCG breakdown by payment form
    vcg_results = [r for r in results if r.category == "VCG" and r.verdict == "VERIFIED"]
    vcg_form_counts: Counter[str] = Counter()
    for r in vcg_results:
        for form in ("clarke_pivot", "marginal_welfare", "critical_bid",
                     "budget_split", "unclassified", "none"):
            if _VCG_FORM_CLAIMS[form].split(" —")[0].split(" (")[0] in r.notes:
                vcg_form_counts[form] += 1
                break
        else:
            vcg_form_counts["none"] += 1
    vcg_confirmed = sum(
        1 for r in vcg_results if r.entry_specific
    )

    stackelberg_verified = sum(
        1 for r in results if r.verdict == "VERIFIED" and r.category == "Stackelberg"
    )
    dsic_verified = sum(
        1 for r in results if r.verdict == "VERIFIED" and r.category != "Stackelberg"
    )
    contract_specific = sum(
        1 for r in results
        if r.verdict == "VERIFIED" and r.category == "Contract" and r.entry_specific
    )
    contract_template = sum(
        1 for r in results
        if r.verdict == "VERIFIED" and r.category == "Contract" and not r.entry_specific
    )

    print(f"\n{'=' * 64}")
    print(f"  Z3 Verification Summary  ({total} entries checked)")
    print(f"{'=' * 64}")
    for v in ("VERIFIED", "COUNTEREXAMPLE", "UNKNOWN", "UNSUPPORTED"):
        n = counts[v]
        if n:
            bar = "█" * min(n, 40)
            print(f"  {v:<16} {bar}  ({n})")
    if counts["VERIFIED"]:
        vcg_total = len(vcg_results)
        print(f"  ├─ DSIC verified ({dsic_verified} total):")
        print(f"  │   VCG ({vcg_total}): {vcg_confirmed} form-confirmed"
              f" [clarke={vcg_form_counts['clarke_pivot']}"
              f" marginal={vcg_form_counts['marginal_welfare']}"
              f" threshold={vcg_form_counts['critical_bid']}]"
              f", {vcg_total - vcg_confirmed} template-only")
        if contract_specific:
            print(f"  │   Contract entry-specific (LaTeX utility): {contract_specific}")
        print(f"  │   Contract template (linear-cost model):    {contract_template}")
        print(f"  └─ Stackelberg equilibrium IR (NOT DSIC): {stackelberg_verified}")
        if stackelberg_verified:
            print(f"       [p²/2 ≥ 0 for p > 0 — structural, not entry-specific]")
    print(f"{'=' * 64}\n")
    for r in results:
        if r.verdict not in ("VERIFIED", "UNSUPPORTED"):
            print(r)
            print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify IC/IR for FL corpus entries using Z3"
    )
    parser.add_argument("input", type=Path,
                        help="Single entry .json or directory of entries")
    parser.add_argument("--gold", action="store_true",
                        help="Batch: only verify gold-tier entries")
    parser.add_argument("--verbose", action="store_true",
                        help="Print full result for every entry")
    args = parser.parse_args()

    if not args.input.exists():
        sys.exit(f"Not found: {args.input}")

    if args.input.is_dir():
        results = verify_corpus(args.input, gold_only=args.gold)
        if args.verbose:
            for r in results:
                print(r)
                print()
        print_summary(results)
    else:
        data = json.loads(args.input.read_text())
        if isinstance(data, list):
            entries = data
            if args.gold:
                entries = [e for e in entries if e.get("quality_tier") == "gold"]
            results = [verify(e) for e in entries if e.get("category") not in _RAG_ONLY]
            if args.verbose:
                for r in results:
                    print(r)
                    print()
            print_summary(results)
        else:
            result = verify(data)
            print(result)


if __name__ == "__main__":
    main()
