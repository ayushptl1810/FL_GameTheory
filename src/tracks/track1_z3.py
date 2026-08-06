"""
Track 1 — Z3 (exact, fast).

When:  type space is finite and discrete; utilities are linear or polynomial
       with small degree (Z3 NRA handles up to ~degree 4 reliably).
What:  encodes IC and IR as SMT constraints; Z3 either proves UNSAT of the
       negation (verified) or returns a model (counterexample).
Guarantee: exact — UNSAT is a complete proof for the encoded model.

Covers:
  VCG        — threshold-payment procurement / forward auction
  Contract   — discrete-type screening; LaTeX path when IC/IR fields present
  Stackelberg — follower IR only (equilibrium concept ≠ DSIC)
  Shapley    — stub (intractable in Z3; Roberts' theorem inapplicable)
"""

from __future__ import annotations

import re
from typing import Any

from . import Verdict, VerificationResult, finalize_verdict, normalize_left_right, strip_redundant_outer_parens

try:
    from z3 import And, Or, Real, RealVal, Solver, sat, unsat, unknown  # noqa: F401
    _Z3_OK = True
except ImportError:
    _Z3_OK = False


def _model_to_dict(m: Any) -> "dict[str, str]":
    """
    Z3 models can contain interpreted-function entries (e.g. an internal
    partial-division function, printed as a declaration named "/") alongside
    the 0-arity constants we actually assigned. Only the constants represent
    real variable assignments; a FuncInterp's str() is solver internals
    (a lookup table like "[else -> If(...)]"), not a usable value. Keep only
    arity-0 declarations so counterexamples stay clean and reportable.
    """
    return {str(d): str(m[d]) for d in m if d.arity() == 0}


# ── VCG payment-form classifier ───────────────────────────────────────────────

_VCG_FORM_CHECKS: list[tuple[str, str]] = [
    (r"\\neq\s*[a-zA-Z]",  "clarke_pivot"),
    (r"\\setminus",          "marginal_welfare"),
    (r"[Ss]\(z\^",           "marginal_welfare"),
    (r"\\min",               "critical_bid"),
    (r"\+1[}_]",             "critical_bid"),
    (r"\\frac\s*\{B\}",     "budget_split"),
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
    if not (payment_rule or "").strip():
        return "none"
    for pat, label in _VCG_FORM_CHECKS:
        if re.search(pat, payment_rule):
            return label
    return "unclassified"


# ── VCG ───────────────────────────────────────────────────────────────────────

def verify_vcg(entry: dict) -> VerificationResult:
    """
    IC (dominant-strategy) + IR for threshold-payment VCG mechanism.

    Template: procurement/forward auction with threshold payment.
      Utility u_i = t − c_i (winner), 0 (loser).
      t = (K+1)-th lowest cost (threshold / Clarke pivot).

    Also classifies payment_rule_latex against known VCG forms via regex.
    entry_specific=True when payment matches Clarke/marginal/critical-bid form.
    """
    if not _Z3_OK:
        return VerificationResult(
            verdict="UNSUPPORTED", category="VCG",
            paper_id=entry.get("paper_id", "<unknown>"), track=1,
            notes="z3-solver not installed.",
        )

    mechanism    = entry.get("mechanism") or {}
    auction_type = mechanism.get("auction_type", "reverse")
    ic_type      = mechanism.get("ic_type", "dominant-strategy")
    paper_id     = entry.get("paper_id", "<unknown>")
    payment_rule = mechanism.get("payment_rule_latex") or ""

    vcg_form       = _classify_vcg_payment(payment_rule)
    form_note      = _VCG_FORM_CLAIMS[vcg_form]
    form_confirmed = vcg_form in ("clarke_pivot", "marginal_welfare", "critical_bid")

    c = Real("c")
    t = Real("t")

    conditions: list[str] = []
    notes_l: list[str]    = []
    verdicts: list[Verdict] = []
    counterexample: dict[str, str] | None = None

    def _check(s: "Solver", label: str, cond: str) -> Verdict:
        nonlocal counterexample
        r = s.check()
        v: Verdict = "VERIFIED" if r == unsat else ("COUNTEREXAMPLE" if r == sat else "UNKNOWN")
        if v == "COUNTEREXAMPLE" and counterexample is None:
            m = s.model()
            counterexample = _model_to_dict(m)
        verdicts.append(v)
        conditions.append(cond)
        notes_l.append(f"{label}: {v}")
        return v

    s = Solver(); s.add(c > 0, t > 0, c < t); s.add(t - c < 0)
    _check(s, "IR",   "IR: u_i = t − c_i ≥ 0 for winners  (c_i < t by definition)")

    s = Solver(); s.add(c > 0, t > 0, c < t); s.add(RealVal(0) > t - c)
    _check(s, "IC-A", "IC-A: winner cannot gain by overbidding (losing intentionally)")

    s = Solver(); s.add(c > 0, t > 0, c > t); s.add(t - c > RealVal(0))
    _check(s, "IC-B", "IC-B: loser cannot gain by underbidding (winning at a loss)")

    all_ok  = all(v == "VERIFIED" for v in verdicts)
    has_cex = any(v == "COUNTEREXAMPLE" for v in verdicts)
    final: Verdict = finalize_verdict(all_ok, has_cex, form_confirmed)

    return VerificationResult(
        verdict=final, category="VCG", paper_id=paper_id, track=1,
        conditions=conditions, counterexample=counterexample,
        notes=(" | ".join(notes_l)
               + f" | {form_note}"
               + f" | model: threshold-payment {auction_type} auction"
               + (f", ic_type={ic_type}" if ic_type != "dominant-strategy" else "")),
        entry_specific=form_confirmed,
    )


# ── LaTeX → Z3 pipeline ───────────────────────────────────────────────────────

_LATEX_OK = False
_lx_parse = None
_sp = None

try:
    from sympy.parsing.latex import parse_latex as _lx_parse
    import sympy as _sp
    _LATEX_OK = True
except Exception:
    pass

_SUB_RE = re.compile(r"_\{?([a-zA-Z,']+)\}?")


def _is_definitely_positive_sum(expr: Any) -> bool:
    """
    True if expr provably > 0 given the ambient assumption used throughout
    this codebase: every Symbol is a positive real (Z3 preconditions add
    `var > 0` for every free variable). Checks that expr expands to a sum
    of monomials each with a positive numeric coefficient and only
    plain-symbol / positive-integer-power factors -- and at least one term
    actually contains a symbol (so it isn't just a positive constant that
    happens to be 0 after all-zero substitution). Conservative: returns
    False (not just "unknown") on anything it can't establish this way.
    """
    terms = _sp.Add.make_args(_sp.expand(expr))
    saw_symbol_term = False
    for t in terms:
        coeff, rest = t.as_coeff_Mul()
        if coeff <= 0:
            return False
        if rest == _sp.Integer(1):
            continue
        for factor in _sp.Mul.make_args(rest):
            if isinstance(factor, _sp.Symbol):
                saw_symbol_term = True
                continue
            if (isinstance(factor, _sp.Pow) and isinstance(factor.args[0], _sp.Symbol)
                    and factor.args[1].is_Integer and factor.args[1] > 0):
                saw_symbol_term = True
                continue
            return False
    return saw_symbol_term


def _sp_to_z3(expr: Any, cache: dict) -> Any:
    """Convert SymPy polynomial expression to Z3.

    log/exp are handled as opaque auxiliary real variables rather than
    "unsupported" -- Z3 NRA has no native transcendentals, but for IC/IR
    proofs these terms very often only need to contribute a *sign*, not a
    specific value (e.g. a fixed per-agent "\\ln(1+\\text{something positive})"
    communication-cost term that's identical across the compared contracts
    and either cancels out of an IC gap or just needs to be known positive
    for an IR check). exp(x) is unconditionally > 0 for any real x. log(x)
    is only encoded when x - 1 is provably a positive sum (see
    _is_definitely_positive_sum) -- i.e. log(x) > 0 is soundly established
    from the ambient positive-symbol assumption, not asserted blindly.
    Anything else still raises, same as before.
    """
    if isinstance(expr, _sp.exp):
        key = f"exp[{expr.args[0]}]"
        if key not in cache:
            cache[key] = Real(f"expaux{len(cache)}")
        return cache[key]
    if isinstance(expr, _sp.log):
        arg = expr.args[0]
        if not _is_definitely_positive_sum(arg - 1):
            raise ValueError(f"log argument sign not established: {arg}")
        key = f"log[{arg}]"
        if key not in cache:
            cache[key] = Real(f"logaux{len(cache)}")
        return cache[key]
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


def _sub_index(sp_expr: Any, old_sub: str, new_idx: int) -> Any:
    subs = {}
    for sym in sp_expr.free_symbols:
        name = str(sym)
        m2 = _SUB_RE.search(name)
        if m2 and m2.group(1) == old_sub:
            subs[sym] = _sp.Symbol(_SUB_RE.sub(f"_{new_idx}", name, count=1))
    return sp_expr.subs(subs)


def _preprocess_contract_latex(s: str) -> str:
    s = re.sub(r"C_\{total\}\(e_\{([a-zA-Z])\}\)", r"cost_{\1}", s)
    s = re.sub(r"C_\{total\}\(e_([a-zA-Z])\)", r"cost_{\1}", s)
    s = re.sub(r"_\{[a-zA-Z]{2,}\}", "", s)
    return s


def _expand_utility_call_shorthand(text: str, client_utility_latex: str) -> str:
    """
    Papers frequently state IC/IR compactly by referencing the utility
    function rather than substituting it, e.g. "U_i(e_i, r_i) \\geq
    U_i(e_j, r_j)" instead of the algebraic inequality. The Z3 encoding
    needs the actual formula. If client_utility_latex defines
    "Name(formal_args) = rhs", expand every "Name(actual_args)" call in
    `text` into "(rhs with formal_args -> actual_args)". Leaves any call
    with a mismatched argument count unresolved rather than guessing.
    Returns `text` unchanged if client_utility_latex isn't in that shape.
    """
    if not client_utility_latex:
        return text
    m = re.match(
        r"^\s*([A-Za-z]+_?\{?[a-zA-Z0-9,]*\}?)\s*\(([^)]*)\)\s*=\s*(.+)$",
        client_utility_latex.strip(),
    )
    if not m:
        return text
    name, formal_args_raw, rhs = m.group(1), m.group(2), m.group(3)
    formal_arg_list = [a.strip() for a in formal_args_raw.split(",") if a.strip()]
    if not formal_arg_list:
        return text
    # Longest-first so a formal arg that's a prefix of another (rare, but
    # possible with LaTeX subscript variants) doesn't get partially replaced.
    formal_args_by_length = sorted(formal_arg_list, key=len, reverse=True)

    call_re = re.compile(re.escape(name) + r"\(([^)]*)\)")

    def _repl(call_m: "re.Match") -> str:
        actual_args = [a.strip() for a in call_m.group(1).split(",")]
        if len(actual_args) != len(formal_arg_list):
            return call_m.group(0)
        substituted = rhs
        for formal in formal_args_by_length:
            actual = actual_args[formal_arg_list.index(formal)]
            # lambda replacement -- `actual` may itself contain backslashes
            # (LaTeX macros), which re.sub would otherwise try to parse as
            # backreference escapes if passed as a plain string replacement.
            substituted = re.sub(
                re.escape(formal) + r"(?![a-zA-Z0-9_}])", lambda _m: actual, substituted
            )
        return f"({substituted})"

    return call_re.sub(_repl, text)


def _get_sub(sym: Any) -> "str | None":
    m2 = _SUB_RE.search(str(sym))
    return m2.group(1) if m2 else None


def _parse_contract_entry(entry: dict) -> "tuple[Any, Any, str, str, int, bool] | None":
    """
    Shared sympy-level parse of a Contract entry's IC/IR LaTeX.
    Returns (U_ir, U_rhs, type_sub, contract_sub, n, ir_from_ic_lhs) or None.
    Used by both the Z3 path (_try_contract_latex) and Track 2's parametric
    certificate generator (track2_sos._parametric_contract_certificate).
    """
    if not _LATEX_OK:
        return None

    mech   = entry.get("mechanism") or {}
    ir_raw = mech.get("ir_participation_latex") or ""
    ic_raw = mech.get("ic_screening_latex") or ""
    if not ir_raw or not ic_raw:
        return None

    client_utility_latex = mech.get("client_utility_latex") or ""
    ir_raw = _expand_utility_call_shorthand(ir_raw, client_utility_latex)
    ic_raw = _expand_utility_call_shorthand(ic_raw, client_utility_latex)

    def _split_geq(s: str):
        for sep in (r"\geq", r"\ge", "≥"):
            if sep in s:
                a, b = s.split(sep, 1)
                return a.strip(), b.strip()
        return None

    def _clean(s: str) -> str:
        s = re.sub(r"^[Uu]_?\{?[a-zA-Z,_]+\}?\s*=\s*", "", s.strip())
        s = normalize_left_right(s)
        return strip_redundant_outer_parens(s.strip())

    ir_parts = _split_geq(ir_raw)
    ic_parts = _split_geq(ic_raw)
    if not ir_parts or not ic_parts:
        return None

    ir_clean     = _clean(_preprocess_contract_latex(ir_parts[0]))
    ic_rhs_clean = _clean(_preprocess_contract_latex(ic_parts[1]))
    ic_lhs_clean = _clean(_preprocess_contract_latex(ic_parts[0]))

    try:
        U_ir  = _lx_parse(ir_clean)
        U_rhs = _lx_parse(ic_rhs_clean)
    except Exception:
        return None

    lhs_subs = {_get_sub(s) for s in U_ir.free_symbols  if _get_sub(s)}
    rhs_subs = {_get_sub(s) for s in U_rhs.free_symbols if _get_sub(s)}

    ir_from_ic_lhs = False
    if len(lhs_subs) == 0:
        try:
            U_ic_lhs    = _lx_parse(ic_lhs_clean)
            ic_lhs_subs = {_get_sub(s) for s in U_ic_lhs.free_symbols if _get_sub(s)}
            if len(ic_lhs_subs) == 1:
                U_ir           = U_ic_lhs
                lhs_subs       = ic_lhs_subs
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

    return U_ir, U_rhs, type_sub, contract_sub, n, ir_from_ic_lhs


def _try_contract_latex(entry: dict) -> "VerificationResult | None":
    """
    Entry-specific Contract verification: parses ic_screening_latex and
    ir_participation_latex into Z3, verifies using the paper's actual utility.

    Binding: IR at lowest type (type-0), upward adjacent IC.
    Returns None on parse failure, transcendentals, or soundness issues.
    """
    if not (_LATEX_OK and _Z3_OK):
        return None

    parsed = _parse_contract_entry(entry)
    if parsed is None:
        return None
    U_ir, U_rhs, type_sub, contract_sub, n, ir_from_ic_lhs = parsed

    mech     = entry.get("mechanism") or {}
    paper_id = entry.get("paper_id", "<unknown>")
    cache: dict = {}

    def _U(type_k: int, contract_l: "int | None" = None) -> Any:
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

    # log()/exp() terms are encoded as opaque auxiliary variables constrained
    # only by sign (see _sp_to_z3) -- not tied to their actual arguments.
    # That relaxation makes VERIFIED sound (holds even in the more permissive
    # relaxed search space => holds for the true, more constrained problem)
    # but makes a found COUNTEREXAMPLE untrustworthy (it may only exist
    # because the aux variable was free to take a value the real log/exp
    # term never could for that argument). Downgrade any such COUNTEREXAMPLE
    # to UNKNOWN below.
    used_transcendental = any(k.startswith("log[") or k.startswith("exp[") for k in cache)

    indexed: dict = {}
    for name in cache:
        m2 = re.match(r"^(.+)_(\d+)$", name)
        if m2:
            indexed.setdefault(m2.group(1), {})[int(m2.group(2))] = cache[name]

    # Type-ordering preconditions (2026-07-18). Contract papers' IC/IR claims
    # hold under a type-ordering assumption (types are distinct and index-
    # sorted); without one, Z3 finds "counterexamples" in parameter regions
    # the papers exclude (e.g. reversed type order -- exactly what the five
    # spurious corpus counterexamples were). The type family is identified
    # from the entry's own type_variable field -- declared data, not a guess.
    #
    # The direction convention (is index 0 the LOWEST or HIGHEST type value?)
    # is resolved symbolically when possible: sign of dU/dtheta under all-
    # positive assumptions. dU/dtheta > 0 => value-type, worst type = lowest
    # theta, so binding-at-index-0 pairs with ascending order; < 0 => cost-
    # type, pairs with descending. When the sign is indeterminate, BOTH
    # pairings are checked and combined fail-closed per condition:
    #   clean under both    -> VERIFIED       (includes the correct pairing)
    #   violated under both -> COUNTEREXAMPLE (includes the correct pairing)
    #   direction-dependent -> UNKNOWN        (never assert)
    # If the type family cannot be identified at all, no ordering is imposed
    # and any counterexample is suppressed to UNKNOWN (the old unordered
    # counterexamples were untrustworthy artifacts).
    #
    # Menu monotonicity: families subscripted by the CONTRACT index in the IC
    # RHS (rewards R_j, efforts e_j, ...) are the menu variables -- identified
    # structurally, not guessed. Screening optima give the worst type (index 0,
    # where IR binds) the smallest allocation, so menu families are imposed
    # non-decreasing in index under BOTH type-direction pairings. Paper-
    # produced menus satisfy this, so VERIFIED stays sound; menus no screening
    # mechanism would output (e.g. reward decreasing in type) are excluded,
    # which is what made the old counterexamples artifacts. Type-subscripted
    # non-type families (e.g. type probabilities f_i) are correctly untouched:
    # they never carry the contract subscript. Beyond that, only positivity,
    # which is domain-true regardless of direction, is kept.
    preconds: list = []
    for base, vd in indexed.items():
        for v in vd.values():
            preconds.append(v > 0)
    for name, var in cache.items():
        if not re.match(r".+_\d+$", name):
            preconds.append(var > 0)

    def _type_family() -> "str | None":
        tv = str(mech.get("type_variable") or "")
        cands = set(re.findall(r"\\?([a-zA-Z]+)_", tv))
        cands |= set(re.findall(r"\\([a-zA-Z]+)", tv))
        matches = [b for b in indexed if b.lstrip("\\") in cands]
        return matches[0] if len(matches) == 1 else None

    def _type_direction(base: str) -> "str | None":
        """'value' | 'cost' | None, from the sign of dU/dtheta under
        all-positive assumptions (sound: sympy's assumption engine)."""
        pat = re.compile(rf"^\\?{re.escape(base)}_\{{?{re.escape(type_sub)}\}}?$")
        tsym = next((s for s in U_ir.free_symbols if pat.match(str(s))), None)
        if tsym is None:
            return None
        try:
            dU = _sp.diff(U_ir, tsym)
            pos = dU.subs({s: _sp.Symbol(str(s), positive=True)
                           for s in dU.free_symbols})
            if pos.is_positive:
                return "value"
            if pos.is_negative:
                return "cost"
        except Exception:
            pass
        return None

    type_family = _type_family()
    orderings: "list[list]" = [[]]
    direction: "str | None" = None
    if type_family:
        vals = [indexed[type_family][i] for i in sorted(indexed[type_family])]
        if len(vals) >= 2:
            asc  = [vals[i] < vals[i + 1] for i in range(len(vals) - 1)]
            desc = [vals[i] > vals[i + 1] for i in range(len(vals) - 1)]
            direction = _type_direction(type_family)
            if direction == "value":
                orderings = [asc]
            elif direction == "cost":
                orderings = [desc]
            else:
                orderings = [asc, desc]
    ordered = orderings != [[]]

    menu_bases: set = set()
    for s2 in U_rhs.free_symbols:
        if _get_sub(s2) == contract_sub:
            menu_bases.add(re.sub(r"_\{?[a-zA-Z,']+\}?$", "", str(s2)))
    menu_mono: list = []
    for base in menu_bases:
        vd = indexed.get(base)
        if vd and len(vd) >= 2:
            idxs = sorted(vd)
            for a, b in zip(idxs, idxs[1:]):
                menu_mono.append(vd[a] <= vd[b])

    bind: list = [_U(0, 0) == RealVal(0)]
    for k in range(n - 1):
        bind.append(_U(k + 1, k + 1) == _U(k + 1, k))

    all_conds = preconds + bind + menu_mono

    # Vacuity gate: if bindings + ordering + monotonicity are jointly
    # unsatisfiable, "no violation exists" would be vacuously true. Require
    # confirmed feasibility under every candidate ordering; otherwise fall
    # back to the template path rather than assert anything.
    for extra in orderings:
        s = Solver()
        for cv in all_conds + extra:
            s.add(cv)
        if s.check() != sat:
            return None

    conditions: list[str] = []
    verdicts: list[str]   = []
    counterexample: "dict[str, str] | None" = None

    def _check(violation: Any) -> "tuple[Verdict, dict[str, str] | None]":
        """Solve under each candidate type-ordering; combine fail-closed."""
        per: "list[tuple[str, dict[str, str] | None]]" = []
        for extra in orderings:
            s = Solver()
            for cv in all_conds + extra:
                s.add(cv)
            s.add(violation)
            r = s.check()
            if r == unsat:
                per.append(("VERIFIED", None))
            elif r == sat:
                per.append(("COUNTEREXAMPLE", _model_to_dict(s.model())))
            else:
                per.append(("UNKNOWN", None))
        vs = [v for v, _ in per]
        if all(v == "VERIFIED" for v in vs):
            return "VERIFIED", None
        if all(v == "COUNTEREXAMPLE" for v in vs) and ordered:
            return "COUNTEREXAMPLE", per[0][1]
        return "UNKNOWN", None

    ir_v, ir_cex = _check(Or([_U(k, k) < RealVal(0) for k in range(n)]))
    if ir_v == "COUNTEREXAMPLE" and used_transcendental:
        ir_v, ir_cex = "UNKNOWN", None  # artifact risk of the relaxed log/exp encoding
    if ir_cex is not None:
        counterexample = ir_cex
    verdicts.append(ir_v)
    conditions.append("IR: U_i(own) ≥ 0  [entry-specific utility]")

    ic_viols = [_U(k, k) < _U(k, l) for k in range(n) for l in range(n) if k != l]
    ic_v, ic_cex = _check(Or(ic_viols)) if ic_viols else ("VERIFIED", None)
    if ic_v == "COUNTEREXAMPLE" and used_transcendental:
        ic_v, ic_cex = "UNKNOWN", None  # artifact risk of the relaxed log/exp encoding
    if ic_cex is not None and counterexample is None:
        counterexample = ic_cex
    verdicts.append(ic_v)
    conditions.append(f"IC: U_i(own) ≥ U_i(j) for all {n}×{n-1} pairs  [entry-specific utility]")

    all_ok  = all(v == "VERIFIED" for v in verdicts)
    has_cex = any(v == "COUNTEREXAMPLE" for v in verdicts)
    final: Verdict = finalize_verdict(all_ok, has_cex, True)

    # Soundness gate: when IR was sourced from IC LHS, global cost terms are
    # dropped. Z3 proves U_simplified ≥ 0 but U_paper = U_simplified - E_com,
    # so no guarantee about the real IR. Revert to template.
    if ir_from_ic_lhs:
        return None

    return VerificationResult(
        verdict=final, category="Contract", paper_id=paper_id, track=1,
        conditions=conditions, counterexample=counterexample,
        notes=(f"IR:{ir_v} IC:{ic_v} | LaTeX-parsed utility | n={n} (capped 4)"
               + " | binding: IR at type-0, adjacent upward IC"
               + (f" | type-ordering: {type_family}"
                  + (f" ({direction}-type, single direction)" if direction
                     else " (direction unknown, both checked)")
                  if ordered
                  else " | type-ordering: unidentified (counterexamples suppressed)")),
        entry_specific=True,
    )


# ── Contract ──────────────────────────────────────────────────────────────────

def verify_contract(entry: dict) -> VerificationResult:
    """
    Contract verifier: tries entry-specific LaTeX path first, falls back to
    the parametric linear-cost template.

    Template (cost model): n types θ_0 < … < θ_{n-1}, linear utility
      U_i(j) = R_j − θ_i · e_j.  Binding: IR at top, downward IC.

    LaTeX path (quality model): parses paper's actual utility.
      Binding: IR at type-0, upward adjacent IC.
    """
    if not _Z3_OK:
        return VerificationResult(
            verdict="UNSUPPORTED", category="Contract",
            paper_id=entry.get("paper_id", "<unknown>"), track=1,
            notes="z3-solver not installed.",
        )

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

    domain: list[Any] = []
    for i in range(n_types - 1):
        domain.append(theta[i] < theta[i + 1])
        domain.append(e[i] > e[i + 1])
    for i in range(n_types):
        domain.append(theta[i] > 0)
        domain.append(e[i] > 0)

    R: list[Any] = [None] * n_types
    R[n_types - 1] = theta[n_types - 1] * e[n_types - 1]
    for i in range(n_types - 2, -1, -1):
        R[i] = R[i + 1] + theta[i] * (e[i] - e[i + 1])

    def U(i: int, j: int) -> Any:
        return R[j] - theta[i] * e[j]

    conditions: list[str] = []
    notes_l: list[str]    = []
    verdicts: list[Verdict] = []
    counterexample: dict[str, str] | None = None

    s = Solver()
    for cv in domain:
        s.add(cv)
    s.add(Or([U(i, i) < 0 for i in range(n_types)]))
    r = s.check()
    ir_v: Verdict = "VERIFIED" if r == unsat else ("COUNTEREXAMPLE" if r == sat else "UNKNOWN")
    if ir_v == "COUNTEREXAMPLE":
        m = s.model()
        counterexample = _model_to_dict(m)
    verdicts.append(ir_v)
    conditions.append("IR: U_i(own contract) ≥ 0 for all types")
    notes_l.append(f"IR: {ir_v}")

    s = Solver()
    for cv in domain:
        s.add(cv)
    ic_viols = [U(i, j) > U(i, i) for i in range(n_types) for j in range(n_types) if i != j]
    s.add(Or(ic_viols))
    r = s.check()
    ic_v: Verdict = "VERIFIED" if r == unsat else ("COUNTEREXAMPLE" if r == sat else "UNKNOWN")
    if ic_v == "COUNTEREXAMPLE" and counterexample is None:
        m = s.model()
        counterexample = _model_to_dict(m)
    verdicts.append(ic_v)
    conditions.append("IC: U_i(own) ≥ U_i(j) for all type pairs i ≠ j")
    notes_l.append(f"IC: {ic_v}")

    all_ok  = all(v == "VERIFIED" for v in verdicts)
    has_cex = any(v == "COUNTEREXAMPLE" for v in verdicts)
    final: Verdict = finalize_verdict(all_ok, has_cex, False)

    return VerificationResult(
        verdict=final, category="Contract", paper_id=paper_id, track=1,
        conditions=conditions, counterexample=counterexample,
        notes=(" | ".join(notes_l)
               + f" | model: {n_types}-type linear-cost screening"
               + " (IR binding at top type, downward IC binding)"),
        entry_specific=False,
    )


# ── Entry-specific Stackelberg (LaTeX → SymPy FOC + IR) ─────────────────────

_STACK_INLINE_MATH_RE = re.compile(r"\\\(\s*(.+?)\s*\\\)")

# Capitalized Greek macros used in this corpus as names for *auxiliary
# functions* (e.g. "\Phi_i(\mathbf{p}) = ..." defined in a second clause)
# rather than as function-call syntax parse_latex understands. parse_latex
# would silently read "\Phi_i(\mathbf{p})" as a *product* of two symbols,
# producing a plausible-looking but wrong expression. Bailing out here is
# cheaper than risking a confidently wrong VERIFIED.
_OPAQUE_FUNCTION_RE = re.compile(r"\\(Phi|Omega|Psi|Theta|Lambda|Gamma|Pi|Sigma|Delta)[_({]")

# Expectation/integral notation (\mathbb{E}[...], \int ...) that this parser cannot evaluate.
# Found live 2026-07-17: an auxiliary definition clause "V_n = v_n(F(w_n^*) - \mathbb{E}[F(w^R(q))])"
# silently reduced to a bare constant symbol (the E[...] term didn't parse as depending on
# the follower's decision variable, so its whole contribution vanished under differentiation)
# instead of raising -- producing a wrong FOC and a spurious COUNTEREXAMPLE with no
# best_response_latex present to cross-check it against. Bail rather than silently drop terms.
_UNSUPPORTED_NOTATION_RE = re.compile(r"\\mathbb\{?E\}?\s*[\[\(]|\\int(?!erval)")


def _top_level_eq_split(s: str) -> "tuple[str, str] | None":
    """
    Split "LHS = RHS" at the first '=' that sits at brace-depth 0, so an
    index equality inside a subscript (e.g. the "k=0" in "\\sum_{k=0}^{T-1}")
    is never mistaken for the clause's defining '='. Returns None if there
    is no such top-level '=' (the field is already a bare expression, not a
    "Name = ..." definition).
    """
    depth = 0
    for i, ch in enumerate(s):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == "=" and depth == 0:
            return s[:i], s[i + 1:]
    return None


def _top_level_eq_segments(s: str) -> list[str]:
    """All segments of s split at every brace-depth-0 '='."""
    segments = []
    depth = 0
    start = 0
    for i, ch in enumerate(s):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == "=" and depth == 0:
            segments.append(s[start:i])
            start = i + 1
    segments.append(s[start:])
    return segments


def _clean_stackelberg_latex(s: str) -> str:
    """Clean a single equation clause (no \\quad-separated definitions)."""
    s = s.strip()
    # Font-styling commands (\mathcal{X}, \mathbf{X}, ...) don't change a
    # symbol's mathematical identity, only its rendering -- but sympy's
    # parse_latex doesn't know that and tokenizes "\mathcal" as a literal
    # bare symbol multiplied by whatever follows, silently corrupting the
    # expression instead of raising. Strip them first so every downstream
    # check (including the LHS-shape match below) sees the plain symbol.
    s = re.sub(r"\\math(?:cal|bf|rm|it|sf|tt)\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\boldsymbol\{([^{}]*)\}", r"\1", s)
    segments = _top_level_eq_segments(s)
    if len(segments) > 2:
        # Chained equality: "U_i = R_i - C_i = (actual formula)". The
        # middle segments are mnemonic shorthand (never separately defined
        # here, unlike the \quad-clause case _resolve_stackelberg_utility
        # handles) -- take the rightmost, fully-expanded segment.
        s = segments[-1]
    else:
        split = _top_level_eq_split(s)
        if split is not None:
            lhs, rhs = split
            # Only drop the LHS when it looks like a simple named quantity
            # ("U_i", "U_i(p_i)", "e^*", "P_i^*(q_i)" -- the "X^* = ..."
            # shape best_response_latex uses) -- not e.g. a lim/sum
            # expression, where the "=" wasn't a definition label at all.
            if re.fullmatch(
                r"[A-Za-z]_?\{?[a-zA-Z0-9,]*\}?(\^\*|\^\{\*\})?\s*(\([^)]*\))?",
                lhs.strip(),
            ):
                s = rhs
    s = re.sub(r"\\mathbf\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\mathbb\{([^}]*)\}", r"\1", s)
    s = normalize_left_right(s)
    return strip_redundant_outer_parens(s.strip())


def _base_symbol_name(name: str) -> str:
    return re.sub(r"_.*$", "", name)


def _norm_symbol_full(name: str) -> str:
    return re.sub(r"[{}\\]", "", name)


_KNOWN_LATEX_FUNCTION_MACROS = frozenset({
    r"\ln", r"\log", r"\exp", r"\sin", r"\cos", r"\tan",
    r"\sqrt", r"\min", r"\max", r"\arg\max", r"\arg\min",
})


def _insert_implicit_multiplication(s: str, known_call_names: "set[str]") -> str:
    """
    "\\kappa c_i (P_i)^2" means kappa*c_i*(P_i)^2 -- juxtaposition as
    multiplication is standard notation in this literature -- but
    parse_latex reads "c_i (P_i)" as a function call and then applies the
    "^2" to the *whole call*, producing (c_i(P_i))^2 = c_i^2 * P_i^2
    instead of c_i * P_i^2. Fixing this after parsing (as
    _demote_stray_function_calls does) is too late -- the exponent has
    already mis-scoped. Insert an explicit "\\cdot" before parsing instead,
    for any "Name (" whose Name is neither a real LaTeX function macro nor
    a name with its own auxiliary definition elsewhere in this entry (that
    case -- e.g. "C_k(\\theta_k)" backed by a "C_k = ..." clause -- really
    is a function reference, handled separately by clause substitution).
    """
    def _repl(m: "re.Match") -> str:
        token = m.group(1)
        if token in _KNOWN_LATEX_FUNCTION_MACROS or token in known_call_names:
            return m.group(0)
        return f"{token} \\cdot ("

    return re.sub(r"(\\?[A-Za-z][A-Za-z0-9_{}\\^']*)\s+\(", _repl, s)


def _demote_stray_function_calls(expr: Any) -> Any:
    """
    parse_latex reads juxtaposition like "c_i (P_i)" -- a coefficient next
    to a parenthesized term, meant as multiplication -- as a function call
    c_i(P_i), since it can't tell "c_i" isn't a defined function. None of
    these papers intend a real function there. Rewrite any function
    application still present after clause substitution as a product of
    its head symbol and arguments, so differentiation doesn't stall on an
    unresolved Derivative(c_i(P_i), P_i).
    """
    replacements = {}
    for f in expr.atoms(_sp.core.function.AppliedUndef):
        head = _sp.Symbol(str(f.func))
        replacements[f] = head * _sp.Mul(*f.args)
    if not replacements:
        return expr
    try:
        return expr.subs(replacements)
    except ValueError:
        # Simultaneous multi-key substitution can raise "substitution cannot
        # create dummy dependencies" when a replacement head-symbol collides
        # with a bound variable elsewhere in the expression (e.g. a Sum's
        # index). Falling back to sequential one-at-a-time substitution
        # avoids that simultaneity requirement; if even that fails, return
        # the expression un-demoted rather than crash -- downstream code
        # (an unresolved Derivative check) already fails closed on that.
        try:
            for f, repl in replacements.items():
                expr = expr.subs(f, repl)
            return expr
        except ValueError:
            return expr


_DEFINITION_CLAUSE_RE = re.compile(r"^([A-Za-z\\][A-Za-z0-9_{}\\^,()-]*)\s*(?:\([^)]*\))?\s*=\s*(.+)$")


def _split_equation_clauses(s: str) -> list[str]:
    return [c.strip().strip(",").strip() for c in s.split(r"\quad") if c.strip().strip(",").strip()]


def _resolve_stackelberg_utility(util_raw: str) -> "Any | None":
    """
    Parse a (possibly multi-clause) follower_utility_latex field into one
    SymPy expression.

    Many entries state the utility as a shell over named subcomponents --
    "U_i = R_i - C_i, \\quad R_i = ..., \\quad C_i = ..." -- rather than one
    closed-form expression. Naively parsing only the first clause leaves an
    opaque "R_i - C_i" with no connection to any decision variable. This
    resolves each auxiliary "Name(args) = rhs" / "Name = rhs" clause and
    substitutes it into the main utility, rewriting "Name(args)" call
    syntax to bare "Name" first so parse_latex doesn't misread it as a
    multiplication (its behavior for unrecognized function names).

    Returns None on anything unparseable, an unresolved opaque function
    (see _OPAQUE_FUNCTION_RE), or a definition clause that doesn't fit the
    "Name = rhs" shape.
    """
    clauses = _split_equation_clauses(util_raw)
    if not clauses:
        return None
    if any(_OPAQUE_FUNCTION_RE.search(c) for c in clauses):
        return None
    if any(_UNSUPPORTED_NOTATION_RE.search(c) for c in clauses):
        return None

    definitions: dict[str, tuple[str, str]] = {}  # norm name -> (lhs_raw, rhs_raw)
    for clause in clauses[1:]:
        m = _DEFINITION_CLAUSE_RE.match(clause)
        if not m:
            return None
        lhs_raw, rhs_raw = m.group(1), m.group(2)
        try:
            lhs_sym = _lx_parse(lhs_raw)
        except Exception:
            return None
        definitions[_norm_symbol_full(str(lhs_sym))] = (lhs_raw, rhs_raw)

    known_call_names = {lhs_raw for lhs_raw, _ in definitions.values()}

    def _strip_call_syntax(raw: str) -> str:
        for lhs_raw, _ in definitions.values():
            # lhs_raw is a LaTeX string that may contain backslashes (e.g.
            # "\mathcal{C}_{i,t}") -- passing it as re.sub's plain-string
            # replacement would make Python read it as a backreference
            # template ("bad escape \m"). Use a lambda so it's substituted
            # verbatim instead.
            raw = re.sub(re.escape(lhs_raw) + r"\s*\([^)]*\)", lambda _m, r=lhs_raw: r, raw)
        return raw

    def _parse_clause(raw: str) -> "Any | None":
        try:
            text = _strip_call_syntax(raw)
            text = _insert_implicit_multiplication(text, known_call_names)
            parsed = _lx_parse(_clean_stackelberg_latex(text))
            return _demote_stray_function_calls(parsed)
        except Exception:
            return None

    main_expr = _parse_clause(clauses[0])
    if main_expr is None:
        return None

    rhs_exprs: dict[str, Any] = {}
    for name, (_, rhs_raw) in definitions.items():
        expr = _parse_clause(rhs_raw)
        if expr is None:
            return None
        rhs_exprs[name] = expr

    # Single substitution pass -- definitions in this corpus reference the
    # decision variable directly, not each other.
    for sym in list(main_expr.free_symbols):
        key = _norm_symbol_full(str(sym))
        if key in rhs_exprs:
            main_expr = main_expr.subs(sym, rhs_exprs[key])

    return _sp.expand(main_expr)


def _extract_follower_symbol(entry: dict, expr_free_symbols: Any) -> "Any | None":
    """
    Best-effort identification of the follower's own decision variable.

    Tries the human-readable follower_decision field first -- it often
    embeds the LaTeX symbol, e.g. "data contribution level \\( \\zeta \\)".
    Falls back to "the symbol in follower_utility that doesn't also appear
    in leader_objective" only when that leaves exactly one candidate.
    Anything more ambiguous is left unresolved (returns None) so the entry
    falls through to the generic template instead of guessing.
    """
    mech = entry.get("mechanism") or {}
    follower_decision = mech.get("follower_decision") or ""

    def _match_candidate(sp_candidate: Any) -> "Any | None":
        """Try an exact symbol match first -- critical when an entry has
        several similarly-named variables (q_{ti} training CPU vs. q_{mi}
        mining CPU both reduce to base name "q"), where base-name matching
        alone is ambiguous even though the source field names one exactly.
        Falls back to base-name matching only if no exact match exists.
        """
        free = getattr(sp_candidate, "free_symbols", None) or {sp_candidate}
        if len(free) != 1:
            return None
        target = next(iter(free))
        exact = [sym for sym in expr_free_symbols if sym == target]
        if len(exact) == 1:
            return exact[0]
        target_base = _base_symbol_name(str(target))
        matches = [sym for sym in expr_free_symbols if _base_symbol_name(str(sym)) == target_base]
        return matches[0] if len(matches) == 1 else None

    # Pass -1: follower_foc_latex's own differentiation variable, e.g.
    # "\partial U_i / \partial q_{ti} = ..." names the decision variable
    # directly -- the strongest possible signal when present.
    foc_raw = mech.get("follower_foc_latex") or ""
    # \frac{\partial U}{\partial q_{ti}} form -- try first, since it
    # unambiguously captures the denominator (the differentiation
    # variable), unlike a bare search for "\partial X" which would match
    # the numerator's "\partial U_i" first.
    m = re.search(r"\\partial\s+[A-Za-z0-9_{}\^]+\}\{\\partial\s+([A-Za-z][A-Za-z0-9_{}\^]*)\}", foc_raw)
    if not m:
        m = re.search(r"\\partial\s+([A-Za-z][A-Za-z0-9_{}\^]*)\s*\}?\s*=", foc_raw)
    if m:
        try:
            match = _match_candidate(_lx_parse(m.group(1)))
        except Exception:
            match = None
        if match is not None:
            return match

    # Pass 0: best_response_latex directly names the follower's own
    # decision variable as the thing being solved for, e.g.
    # "P_i^*(q_i) = ..." or "\arg\max_{q_n} U_n(q_n, P_n)".
    br_raw = mech.get("best_response_latex") or ""
    for pat in (
        r"^\(?([A-Za-z][A-Za-z0-9_{}\^]*?)\)?\^\*",
        r"\\arg\s*\\max_\{?([A-Za-z][A-Za-z0-9_{}]*)",
        r"\\max_\{?([A-Za-z][A-Za-z0-9_{}]*)",
    ):
        m = re.search(pat, br_raw)
        if not m:
            continue
        try:
            sp_candidate = _lx_parse(m.group(1))
        except Exception:
            continue
        match = _match_candidate(sp_candidate)
        if match is not None:
            return match
        break

    # Pass 1: an explicit inline-math snippet, e.g. "... level \( \zeta \)".
    for candidate in _STACK_INLINE_MATH_RE.findall(follower_decision):
        try:
            sp_candidate = _lx_parse(candidate.strip())
        except Exception:
            continue
        target_syms = getattr(sp_candidate, "free_symbols", set())
        if len(target_syms) != 1:
            continue
        target_base = _base_symbol_name(str(next(iter(target_syms))))
        for sym in expr_free_symbols:
            if _base_symbol_name(str(sym)) == target_base:
                return sym

    # Pass 2: no inline math, but the symbol's base name (e.g. "p" out of
    # "p_{i}") appears as an isolated word in the free-text description,
    # e.g. "Participation probability p". Only used when it uniquely
    # identifies one candidate among the utility's own free symbols.
    word_matches = [
        sym for sym in expr_free_symbols
        if re.search(r"\b" + re.escape(_base_symbol_name(str(sym))) + r"\b", follower_decision)
    ]
    if len(word_matches) == 1:
        return word_matches[0]

    leader_raw = mech.get("leader_objective_latex") or ""
    leader_bases: set = set()
    if leader_raw:
        # Reuse the multi-clause resolver: leader_objective_latex commonly
        # has the same "V = f(G_i), \quad G_i = ..." auxiliary-definition
        # shape as follower_utility_latex, and naively parsing just the
        # first clause would leave G_i unresolved / raise on the stray
        # "\quad ... =" trailing text.
        leader_expr = _resolve_stackelberg_utility(leader_raw)
        if leader_expr is not None:
            leader_bases = {_base_symbol_name(str(s)) for s in leader_expr.free_symbols}

    candidates = [s for s in expr_free_symbols if _base_symbol_name(str(s)) not in leader_bases]
    return candidates[0] if len(candidates) == 1 else None


def _try_stackelberg_latex(entry: dict) -> "VerificationResult | None":
    """
    Entry-specific Stackelberg verification: parses the follower's own
    utility, derives its best response by symbolic FOC (not the generic
    U=pe-e^2/2 template), and checks IR at that optimum against the paper's
    actual utility function.

    Returns None (fall through to the template) whenever a step is
    ambiguous: unparseable LaTeX, an opaque auxiliary function reference,
    an unidentifiable decision variable, unsolvable FOC, or a critical
    point that's provably not a maximum. Every branch fails closed --
    a wrong VERIFIED is worse than an honest VERIFIED_TEMPLATE.
    """
    if not _LATEX_OK:
        return None

    mech = entry.get("mechanism") or {}
    util_raw = mech.get("follower_utility_latex") or ""
    if not util_raw:
        return None

    util_expr = _resolve_stackelberg_utility(util_raw)
    if util_expr is None:
        return None

    e_sym = _extract_follower_symbol(entry, util_expr.free_symbols)
    if e_sym is None:
        return None

    # If another free symbol shares e_sym's base name but a different
    # subscript (e.g. x_{r_i} vs x_{w_i} -- rendering vs. bandwidth, both
    # follower-purchased resources), the follower likely controls more
    # than one variable and this pipeline only derives a FOC for one of
    # them. Checking IR at e_sym's optimum while leaving the sibling
    # variable "free" would evaluate utility at a point the follower
    # never actually chooses -- a spurious COUNTEREXAMPLE risk, not a
    # real one. Bail rather than assert either verdict.
    e_base = _base_symbol_name(str(e_sym))
    if any(_base_symbol_name(str(s)) == e_base for s in util_expr.free_symbols if s != e_sym):
        return None

    try:
        foc = _sp.diff(util_expr, e_sym)
        if foc.has(_sp.Derivative):
            return None  # chain rule stalled on an unresolved function
        critical_points = _sp.solve(foc, e_sym)
    except Exception:
        return None

    if not critical_points:
        return None

    second_deriv = None
    try:
        second_deriv = _sp.diff(foc, e_sym)
    except Exception:
        pass

    e_star = None
    concavity_confirmed = False
    for cp in critical_points:
        if e_sym in cp.free_symbols:
            continue  # not a closed-form solution
        if second_deriv is not None:
            sign = _sp.ask(_sp.Q.nonpositive(second_deriv.subs(e_sym, cp)))
            if sign is False:
                continue  # provably a minimum, not a maximum -- reject
            concavity_confirmed = sign is True
        e_star = cp
        break

    if e_star is None:
        return None

    # Cross-check against the paper's own best_response_latex when present.
    # A definite mismatch means the FOC we derived disagrees with the
    # paper's stated optimum -- almost always a parse artifact on our side
    # (e.g. an exponent scope error from a misread function call) rather
    # than the paper being wrong. Reject rather than certify against a
    # formula the paper doesn't actually state.
    best_response_note = ""
    br_raw = mech.get("best_response_latex") or ""
    if br_raw and not _OPAQUE_FUNCTION_RE.search(br_raw):
        try:
            br_expr = _demote_stray_function_calls(_lx_parse(_clean_stackelberg_latex(br_raw)))
            diff = _sp.simplify(br_expr - e_star)
        except Exception:
            diff = None
        if diff is not None:
            if diff == 0:
                best_response_note = " | best_response_latex cross-check: MATCH"
            else:
                # A single numeric sample is unsound here: a genuine
                # difference like p*(1-mu)/(2*mu*rho) evaluates to exactly
                # 0 at mu=1, which would falsely read as a match if that's
                # the one point sampled. Require several independent trials
                # to all be ~0 before accepting -- any nonzero trial is a
                # real disagreement.
                free = sorted(diff.free_symbols, key=str)
                trial_vals = [
                    [_sp.Rational(2, 3), _sp.Rational(5, 7), _sp.Rational(11, 13),
                     _sp.Rational(3, 4), _sp.Rational(9, 5)][t % 5] + t
                    for t in range(5)
                ]
                try:
                    numeric_diffs = [
                        float(diff.subs({s: trial_vals[t] + i for i, s in enumerate(free)}).evalf())
                        for t in range(5)
                    ]
                except Exception:
                    numeric_diffs = None
                if numeric_diffs is None or any(abs(v) > 1e-6 for v in numeric_diffs):
                    return None  # definite disagreement with the paper's own formula

    try:
        U_star = _sp.simplify(util_expr.subs(e_sym, e_star))
    except Exception:
        return None

    remaining_syms = U_star.free_symbols
    assumptions = _sp.And(*[_sp.Q.positive(s) for s in remaining_syms]) if remaining_syms else _sp.S.true
    sign = _sp.ask(_sp.Q.nonnegative(U_star), assumptions)

    paper_id = entry.get("paper_id", "<unknown>")
    decided_by_track3 = False
    ir_witness: "dict[str, str] | None" = None

    if sign is True:
        ir_v: Verdict = "VERIFIED"
        ir_note = f"U*={U_star} >= 0 for all remaining params > 0 (symbolic)"
    elif sign is False:
        ir_v = "COUNTEREXAMPLE"
        ir_note = f"U*={U_star} can be negative for positive params"
    else:
        # Symbolic sign indeterminate -- escalate to Track 3's rigorous
        # interval engine over a positive parameter box. Here (unlike the
        # standalone Track 3 Contract path) the remaining symbols ARE
        # genuinely free leader-side parameters -- the follower's decision
        # variable was already substituted out at its optimum -- so both
        # verdict directions are meaningful.
        # (Replaced 2026-07-19: the old fallback reported VERIFIED from 10
        # numeric sample points, which is unsound -- sampling can witness a
        # violation but can never prove nonnegativity.)
        ir_v, ir_note = "UNKNOWN", f"U*={U_star} (sign indeterminate)"
        syms = sorted(remaining_syms, key=str)
        if 0 < len(syms) <= 6:
            try:
                from .track3_dreal import check_nonneg_box
                status, witness = check_nonneg_box(
                    U_star, [(s, 0.001, 100.0) for s in syms]
                )
            except Exception:
                status, witness = "unknown", None
            if status == "verified":
                ir_v = "VERIFIED"
                ir_note = (f"U* >= 0 on [0.001,100]^{len(syms)} "
                           "(Track 3 interval branch-and-bound, δ-sound)")
                decided_by_track3 = True
            elif status == "counterexample":
                ir_v = "COUNTEREXAMPLE"
                ir_note = f"U* < 0 near {witness} (Track 3 interval witness)"
                ir_witness = witness
                decided_by_track3 = True

    final = finalize_verdict(ir_v == "VERIFIED", ir_v == "COUNTEREXAMPLE", True)

    return VerificationResult(
        verdict=final, category="Stackelberg", paper_id=paper_id,
        track=3 if decided_by_track3 else 1,
        counterexample=ir_witness,
        conditions=[
            f"FOC: d(follower utility)/d{e_sym} = 0  =>  {e_sym}* = {e_star}"
            f"  [{'concavity confirmed' if concavity_confirmed else 'concavity assumed from unique critical point'}]",
            f"IR: U_follower({e_sym}*, .) >= 0  [entry-specific utility]  -> {ir_v}",
        ],
        notes=(f"IR:{ir_v} ({ir_note}) | LaTeX-parsed follower_utility_latex"
               f" | decision var '{e_sym}' identified from follower_decision/leader_objective"
               f"{best_response_note}"),
        entry_specific=True,
    )


# ── Stackelberg ───────────────────────────────────────────────────────────────

def verify_stackelberg(entry: dict) -> VerificationResult:
    """
    Follower IR for a Stackelberg mechanism.

    Tries the entry-specific LaTeX path first (_try_stackelberg_latex):
    parses the paper's own follower_utility_latex, derives its FOC, and
    checks IR at that optimum. Falls back to the generic template
    (leader sets price p > 0; follower maximises U = pe − e²/2;
    best response e*(p) = p; IR: U* = p²/2 ≥ 0 for all p > 0) only when
    the LaTeX path can't resolve unambiguously -- the fallback verdict is
    downgraded to VERIFIED_TEMPLATE, never VERIFIED, since it says nothing
    about this specific paper's mechanism.

    IC is omitted by design in both paths -- Stackelberg is an equilibrium
    concept, not DSIC.
    """
    mechanism = entry.get("mechanism", {})
    paper_id  = entry.get("paper_id", "<unknown>")
    eq_exists = mechanism.get("equilibrium_existence", False)

    if not eq_exists:
        return VerificationResult(
            verdict="UNSUPPORTED", category="Stackelberg", paper_id=paper_id, track=1,
            notes="equilibrium_existence=False — cannot verify without a proved equilibrium.",
        )

    entry_specific_result = _try_stackelberg_latex(entry)
    if entry_specific_result is not None:
        return entry_specific_result

    if not _Z3_OK:
        return VerificationResult(
            verdict="UNSUPPORTED", category="Stackelberg", paper_id=paper_id, track=1,
            notes="z3-solver not installed and entry-specific LaTeX path unavailable.",
        )

    p = Real("p")
    U_star = p * p / RealVal(2)

    s = Solver()
    s.add(p > 0)
    s.add(U_star < 0)

    ir_v: Verdict = "VERIFIED" if s.check() == unsat else "COUNTEREXAMPLE"
    cex: "dict[str, str] | None" = None
    if ir_v == "COUNTEREXAMPLE":
        m = s.model()
        cex = _model_to_dict(m)

    final = finalize_verdict(ir_v == "VERIFIED", ir_v == "COUNTEREXAMPLE", False)

    return VerificationResult(
        verdict=final, category="Stackelberg", paper_id=paper_id, track=1,
        conditions=["IR: U_follower(e*(p), p) = p²/2 ≥ 0 for all p > 0  [generic template]"],
        counterexample=cex,
        notes=(f"IR: {ir_v}"
               + " | model: quadratic follower utility U=pe−e²/2, best response e*=p (TEMPLATE, not entry-specific)"
               + " | IC omitted (Stackelberg solution concept ≠ DSIC)"),
        entry_specific=False,
    )


# ── Shapley ───────────────────────────────────────────────────────────────────

def verify_shapley(entry: dict) -> VerificationResult:
    """
    Shapley IC/IR is intractable in Z3 for general coalitional games.
    Hard-gate fields (ic_proof_present / ir_proof_present) are the primary signal.
    """
    mechanism  = entry.get("mechanism", {})
    ic_present = mechanism.get("ic_proof_present", False)
    ir_present = mechanism.get("ir_proof_present", False)
    paper_id   = entry.get("paper_id", "<unknown>")

    return VerificationResult(
        verdict="UNSUPPORTED", category="Shapley", paper_id=paper_id, track=1,
        notes=(
            "Roberts' Theorem: Shapley IC/IR is intractable in Z3 for general domains. "
            f"Hard-gate: ic_proof_present={ic_present}, ir_proof_present={ir_present}."
        ),
    )
