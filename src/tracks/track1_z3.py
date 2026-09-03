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

    # Soundness gate (adversarial suite, Task D): an identically-zero payment
    # rule is not a Groves/pivot payment -- with p_i = 0 every agent strictly
    # gains by over-reporting, so the mechanism is not dominant-strategy IC.
    # The fixed template checks below would still pass (they never look at the
    # entry's own payment rule), so fail closed here before they can.
    _pr_rhs = payment_rule.split("=", 1)[-1] if "=" in payment_rule else payment_rule
    if re.sub(r"[\s${}\\]", "", _pr_rhs) in ("0", "0.0"):
        return VerificationResult(
            verdict="UNKNOWN", category="VCG", paper_id=paper_id, track=1,
            notes="payment_rule_latex is identically zero -- not a Groves/pivot "
                  "payment; dominant-strategy IC fails (every agent over-reports). "
                  "Failing closed: no entry-specific DSIC proof available.",
        )

    # Phase 2: try the real finite-grid Z3 DSIC + IR proof first. Only its
    # decisive verdicts win; UNKNOWN / UNSUPPORTED fall through to the regex
    # shape path below, whose success is now VERIFIED_SHAPE (a structural
    # match, never a proof about this entry's own math).
    from tracks.vcg_dsic import verify_vcg_dsic

    r = verify_vcg_dsic(entry)
    if r.verdict in ("VERIFIED", "COUNTEREXAMPLE"):
        return r

    vcg_form       = _classify_vcg_payment(payment_rule)
    form_note      = _VCG_FORM_CLAIMS[vcg_form]
    form_confirmed = vcg_form in ("clarke_pivot", "marginal_welfare", "critical_bid")

    # Seam: the LaTeX front-end above has produced VCG's parsed representation
    # of the payment rule (the form classification -> form_confirmed / form_note).
    # Everything below is the parsed-payment-in / verdict-out back-half, moved
    # verbatim into _vcg_check_core. VCG's fixed template Z3 model does not read
    # the payment/utility exprs themselves, so they are accepted but unused here.
    client_utility_latex = mechanism.get("client_utility_latex") or ""
    result = _vcg_check_core(
        payment_rule, client_utility_latex,
        entry_specific=form_confirmed, paper_id=paper_id,
        meta={"form_note": form_note, "auction_type": auction_type, "ic_type": ic_type},
    )
    # The regex path is a payment-shape match only -- it never runs a solver
    # on the entry's own math. Demote its success to VERIFIED_SHAPE (strictly
    # weaker than VERIFIED_TEMPLATE). COUNTEREXAMPLE / UNKNOWN pass through.
    # (_vcg_check_core itself is unchanged -- the AST caller verify_from_ast
    # still gets the old verdicts until Phase 2 Task 7.)
    if result.verdict in ("VERIFIED", "VERIFIED_TEMPLATE"):
        result.verdict = "VERIFIED_SHAPE"
        result.entry_specific = False
    return result


def _vcg_check_core(
    payment_latex: str,
    utility_latex: str,
    *,
    entry_specific: bool,
    paper_id: str,
    meta: dict | None = None,
) -> VerificationResult:
    """Back-half of verify_vcg: parsed-payment-in -> Z3 solve -> verdict.

    Behavior-preserving seam extraction (Approach C). `payment_latex` /
    `utility_latex` carry VCG's parsed payment/utility representation; the
    fixed threshold-payment template below does not consult them (VCG
    classifies on the string in the front-end), so they are currently unused.
    `entry_specific` is the front-end's `form_confirmed` classification.
    """
    meta = meta or {}
    form_note      = meta.get("form_note", "")
    auction_type   = meta.get("auction_type", "reverse")
    ic_type        = meta.get("ic_type", "dominant-strategy")
    form_confirmed = entry_specific

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


_BAYESIAN_RE = re.compile(r"\\mathbb\{E\}|(?<![A-Za-z])E_\{|(?<![A-Za-z])E\\left\[")


def _strip_contract_prose(s: str) -> str:
    """Strip editorial scaffolding papers wrap around an IC/IR inequality.

    Corpus IC/IR strings are transcribed from papers and frequently carry a
    label ("IC: "), a \\text{...} prose lead-in naming the equation, a
    trailing "\\quad \\forall i, k \\in I" quantifier, and -- for papers
    stating two contracts at once -- a second inequality after a \\qquad.

    Keeps only the FIRST "LHS \\geq RHS" inequality (the primary contract)
    and drops surrounding prose. Purely textual: if nothing matches, the
    string is returned unchanged and the caller's own parse gates still
    decide. Never invents or reorders terms.
    """
    if not s:
        return s
    # A second contract is introduced by \qquad after the first inequality.
    for sep in (r"\geq", r"\ge", "≥"):
        i = s.find(sep)
        if i != -1:
            j = s.find(r"\qquad", i)
            if j != -1:
                s = s[:j]
            break
    s = re.sub(r"^\s*(IC|IR)\s*:\s*", "", s)
    # Leading prose: one or more \text{...} runs, each optionally colon-tailed.
    s = re.sub(r"^\s*(?:\\text\s*\{[^{}]*\}\s*:?\s*)+", "", s)
    # Trailing quantifier / commentary.
    s = re.sub(r",?\s*\\(?:quad|qquad)\s*(?:\\forall|\\text\s*\{).*$", "", s)
    s = re.sub(r",\s*\\forall\b.*$", "", s)
    return s.strip().rstrip(",.")


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
    client_utility_latex = mech.get("client_utility_latex") or ""

    # LLM-extracted latex is a FALLBACK only: the paper's own transcription
    # always wins when present. These `_llm` keys are committed corpus data
    # (written by architect.formalize), so verify() stays deterministic and
    # API-key-free -- nothing here calls a model.
    if not ic_raw or not ir_raw:
        ic_raw = ic_raw or mech.get("ic_screening_latex_llm") or ""
        ir_raw = ir_raw or mech.get("ir_participation_latex_llm") or ""
        client_utility_latex = (
            client_utility_latex or mech.get("client_utility_latex_llm") or ""
        )
    if not ir_raw or not ic_raw:
        return None

    # Bayesian expectation wrappers (E_{c_{-k}}[.], \mathbb{E}[.]) state an
    # EX-ANTE constraint. Stripping the expectation and grid-checking the
    # inside would prove something strictly stronger than the paper claims,
    # so fail closed and let verify() fall through to the Track 4 Bayesian
    # path, which handles the quantifier properly.
    if _BAYESIAN_RE.search(ic_raw) or _BAYESIAN_RE.search(ir_raw):
        return None

    ir_raw = _strip_contract_prose(ir_raw)
    ic_raw = _strip_contract_prose(ic_raw)
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

    # Soundness gate (adversarial suite, Task D): the IC RHS is the deviating
    # type's utility from *another* contract, U_i(contract_j) -- it MUST depend
    # on the deviating type i. If no symbol in U_rhs carries the type
    # subscript (e.g. the condition was stated as U_j(contract_j) >= 0, an
    # equilibrium-utility ordering rather than an incentive constraint, or as
    # a bare constant), certifying it says nothing about incentive
    # compatibility. Fail closed rather than hand a structurally-wrong proof
    # obligation to Z3 / the parametric certificate.
    if not any(_get_sub(s) == type_sub for s in U_rhs.free_symbols):
        return None

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
    return _contract_check_core(
        U_ir, U_rhs, type_sub, contract_sub, n, ir_from_ic_lhs,
        paper_id=paper_id, meta=mech,
    )


def _contract_check_core(
    U_ir: Any, U_rhs: Any, type_sub: str, contract_sub: str, n: int,
    ir_from_ic_lhs: bool, *, paper_id: str, meta: "dict | None" = None,
) -> "VerificationResult | None":
    """Back-half of _try_contract_latex: parsed IC/IR SymPy exprs in ->
    Z3 solve under type-ordering / menu-monotonicity preconditions -> verdict.

    Behavior-preserving seam extraction (Approach C). Inputs are exactly the
    tuple _parse_contract_entry returns; `meta` is the entry's mechanism dict
    (only `type_variable` is read, by _type_family).
    """
    mech = meta or {}
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


# Task 13 (function-call notation `f_{sub}(arg_{sub})`, e.g. `c_i(P_i)`):
# investigated, no code needed. SymPy's parse_latex reads `c_i(P_i)` as a
# Function application, but `_demote_stray_function_calls` (below) already
# rewrites any residual AppliedUndef to `head * Mul(*args)` -- the correct
# coefficient reading, with the argument's variable dependence retained and
# no spurious free symbol. The *space* form `c_i (P_i)^2` is handled one
# step earlier by `_insert_implicit_multiplication` (exponent scoping);
# clause-backed `C_k(...)` refs by `_strip_call_syntax`. A pre-parse
# string fold to an "opaque symbol" was tried and reverted: no name
# reliably round-trips through parse_latex as a single Symbol across the
# subscript shapes in play (`c_i_of_P_i` tokenizes as `c_{i_o} * f_{P_i}`).
# See tests/verifier/test_funcall_widening.py for the characterization pins.


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


# Fresh opaque symbol for the "rest of sum" (j != self) after own-term
# isolation. "\Xi" is a single LaTeX symbol parse_latex reads atomically
# and is NOT in _OPAQUE_FUNCTION_RE's bail list (Phi/Omega/Psi/Theta/...).
_SIGMA_OTHERS_PREFIX = "\\Xi"


def _as_str(v: Any) -> str:
    """Fail-closed coercion for LLM-populated meta fields the string-consuming
    Stackelberg readers expect as LaTeX. The formalizer has emitted a dict (not
    a string) under e.g. ``follower_decision`` for at least one corpus entry;
    a non-``str`` value is treated as absent so the entry degrades to
    UNKNOWN/generic-template instead of raising ``TypeError`` mid-sweep.
    """
    return v if isinstance(v, str) else ""


def _follower_decision_latex(entry: dict) -> "str | None":
    """Raw LaTeX of the follower's own decision symbol, e.g. ``s_i^d``.

    Reads the last ``\\(...\\)`` inline-math group of ``follower_decision``
    that parses to a single-symbol SymPy expression. Returns None if none
    does (so the \\sum pre-processor is skipped and the entry falls through
    exactly as before this widening).
    """
    mech = entry.get("mechanism") or {}
    fd = _as_str(mech.get("follower_decision"))
    best: "str | None" = None
    for cand in _STACK_INLINE_MATH_RE.findall(fd):
        cand = cand.strip()
        # A trailing superscript "label" (e.g. the "d" in "s_i^d" -- device,
        # not a power) makes parse_latex read a 2-symbol power. Strip one
        # such suffix so the follower's own token is recognised as a single
        # symbol; the un-stripped form is still tried first.
        for probe in (cand, re.sub(r"\^\{?[A-Za-z]\}?$", "", cand)):
            try:
                p = _lx_parse(probe)
            except Exception:
                continue
            free = getattr(p, "free_symbols", set())
            if len(free) == 1 and not p.has(_sp.Sum):
                best = cand  # keep the ORIGINAL latex for index/base parsing
                break
    return best


_SUM_SET_BOUND_RE = re.compile(
    r"\\sum_\{\s*([a-zA-Z])\s*\\in\s*[^}]+\}"
)
_SUM_INEQ_BOUND_RE = re.compile(
    r"\\sum_\{\s*[^}]*?\\le\s*([a-zA-Z])\s*\\le[^}]*\}"
)


def _latex_index_of(sym_latex: str) -> "str | None":
    """Subscript index letter of a symbol LaTeX token: ``s_i^d`` -> ``i``,
    ``\\rho_i`` -> ``i``. None if the subscript isn't a single letter."""
    m = re.search(r"_\{?([a-zA-Z])\}?", sym_latex)
    return m.group(1) if m else None


def _balanced_summand(s: str, start: int) -> "tuple[str, int] | None":
    """From just past a ``\\sum_{...}`` header at index ``start``, take the
    summand: everything up to the first brace-depth-0 ``+``, ``-`` (not a
    leading sign), top-level ``,``, ``\\quad``, or end of string. Returns
    (summand, end_index) or None if it is empty, contains a nested ``\\sum``,
    or contains any parenthesis.

    Parentheses are a hard bail: a top-level ``+``/``-`` *inside* ``(...)``
    would end the scan early, so the separability/coupling check downstream
    would run on a truncated summand and could miss a term that depends on
    the follower's own decision (reviewer-reproduced false VERIFIED).
    Tracking ``(``/``)`` alongside ``\\left(``/``\\right)`` is fiddly and
    rare in these summands, so bail instead.
    """
    depth = 0
    i = start
    while i < len(s) and s[i] == " ":
        i += 1
    begin = i
    while i < len(s):
        ch = s[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                break  # summand ended at the enclosing brace (e.g. \frac{}{ \sum ... })
        elif depth == 0:
            if ch == ",":
                break
            if ch in "+-" and i > begin:
                break
            if s.startswith(r"\quad", i):
                break
        i += 1
    summand = s[begin:i].strip()
    if not summand or r"\sum" in summand:
        return None
    if "(" in summand or ")" in summand:
        return None  # conservative bail -- see docstring
    return summand, i


def _preprocess_stackelberg_sum_bounds(
    raw: str, self_latex: "str | None"
) -> "tuple[str, int] | None":
    """Rewrite ``\\sum_{i \\in S} f(i)`` / ``\\sum_{a \\le i \\le b} f(i)`` that
    SymPy's ``parse_latex`` cannot handle into ``f(self) + SigmaOthers_k``,
    where ``self`` is the follower's own decision symbol and ``SigmaOthers_k``
    is a fresh OPAQUE symbol, constant w.r.t. the follower's own decision.

    The opaque split is sound ONLY when the rest-of-sum is genuinely
    independent of the follower's own decision. This is enforced by
    requiring the summand to be *separable*: after stripping the terms that
    carry the follower's own symbol under this sum's index, the follower's
    own symbol token must be gone (a residual occurrence signals a coupling
    such as ``self / \\sum_j x_j``).

    Returns (rewritten_latex, n_rewrites), or None if any set/inequality
    bound is present but cannot be safely rewritten (ambiguous ``self``
    membership, coupled summand, nested sum, no follower symbol) -- caller
    then fails closed.
    """
    if r"\sum" not in raw:
        return raw, 0
    has_set = bool(_SUM_SET_BOUND_RE.search(raw))
    has_ineq = bool(_SUM_INEQ_BOUND_RE.search(raw))
    if not (has_set or has_ineq):
        return raw, 0  # only ordinary \sum_{j=1}^{M} bounds -- not our job
    if _SIGMA_OTHERS_PREFIX in raw:
        # A literal \Xi_{k} already in the utility would MERGE with the
        # rest-of-sum symbol we inject (both parse to the same SymPy
        # Symbol), silently shifting the FOC. Bail rather than collide.
        return None
    if self_latex is None:
        return None
    self_idx = _latex_index_of(self_latex)
    self_base_m = re.match(r"\\?[A-Za-z]+", self_latex)
    self_base_tok = self_base_m.group(0) if self_base_m else None

    out = raw
    n = 0
    guard = 0
    while guard < 20:
        guard += 1
        m = _SUM_SET_BOUND_RE.search(out) or _SUM_INEQ_BOUND_RE.search(out)
        if not m:
            break
        sum_idx = m.group(1)
        body = _balanced_summand(out, m.end())
        if body is None:
            return None
        summand, end = body

        # Does the follower's own decision participate in this sum? Two
        # ways: the sum index literally equals `self`'s subscript, OR the
        # summand contains `self`'s base symbol indexed by the sum index
        # (e.g. `\sum_{j \in U} \rho_j` -- the follower i is one of U, so
        # `\rho_i` IS a term even though the summand is written `\rho_j`).
        indexed_self = (
            self_base_tok is not None
            and re.search(
                re.escape(self_base_tok) + r"_\{?" + re.escape(sum_idx) + r"[}\s^]",
                summand + " ",
            )
            is not None
        )
        self_participates = (self_idx is not None and self_idx == sum_idx) or indexed_self

        if self_base_tok:
            # Remove ONLY the terms legitimately carried by THIS sum's index
            # (`self_base`_<sum_idx>). If the follower's own base token still
            # appears afterwards -- e.g. `self_i` inside `\sum_j self_i x_j`,
            # or `self` un-subscripted -- then the rest-of-sum is not
            # independent of the follower's decision and the opaque split
            # would silently drop that dependence: bail.
            stripped = re.sub(
                re.escape(self_base_tok) + r"_\{?" + re.escape(sum_idx)
                + r"\}?(\^\{?[A-Za-z0-9]+\}?)?",
                "",
                summand,
            )
            if self_base_tok in stripped:
                return None

        if not self_participates:
            # Summand shares no symbol family with `self` -> whole sum is
            # opaque and constant w.r.t. the follower's decision.
            replacement = f"( {_SIGMA_OTHERS_PREFIX}_{{{n}}} )"
        else:
            # `self`'s own term = summand with the sum index -> `self`'s
            # concrete subscript; the remaining j != self terms are opaque.
            # This is exact for a SEPARABLE summand -- guaranteed by the
            # residual check above -- so d/d(self) of the objective is
            # unaffected by the opaque part.
            si = self_idx if self_idx is not None else sum_idx
            own_term = re.sub(
                rf"(?<![A-Za-z]){re.escape(sum_idx)}(?![A-Za-z])",
                si,
                summand,
            )
            replacement = f"( ( {own_term} ) + {_SIGMA_OTHERS_PREFIX}_{{{n}}} )"
        out = out[: m.start()] + replacement + out[end:]
        n += 1
    if guard >= 20:
        return None
    if _SUM_SET_BOUND_RE.search(out) or _SUM_INEQ_BOUND_RE.search(out):
        return None
    return out, n


def _resolve_stackelberg_utility(util_raw: str, self_latex: "str | None" = None) -> "Any | None":
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
    # Widening (Task 12): rewrite set/inequality \sum bounds parse_latex
    # can't read into own-term + opaque-rest BEFORE anything else touches
    # the string. A set/ineq bound that can't be safely split -> None
    # (fail closed), never a silently truncated sum.
    pre = _preprocess_stackelberg_sum_bounds(util_raw, self_latex)
    if pre is None:
        return None
    util_raw = pre[0]

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
    follower_decision = _as_str(mech.get("follower_decision"))

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
    foc_raw = _as_str(mech.get("follower_foc_latex"))
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
    br_raw = _as_str(mech.get("best_response_latex"))
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

    leader_raw = _as_str(mech.get("leader_objective_latex"))
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

    self_latex = _follower_decision_latex(entry)
    # Did this entry carry a set/inequality \sum bound that the widening
    # rewrote via own-term isolation + opaque rest? If so, the opaque split
    # is only sound when the paper's own best_response_latex confirms the
    # derived FOC -- so require a definite cross-check MATCH downstream.
    _pp = _preprocess_stackelberg_sum_bounds(util_raw, self_latex)
    widened_via_opaque_sum = _pp is not None and _pp[1] > 0

    util_expr = _resolve_stackelberg_utility(util_raw, self_latex=self_latex)
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

    # Seam (Approach C): the LaTeX front-end above has resolved the paper's
    # follower utility to `util_expr` and identified the follower's decision
    # variable `e_sym`. Everything below -- FOC derivation, best-response
    # solve + cross-check, IR at optimum -- is the parsed-exprs-in ->
    # verdict-out back-half, moved verbatim into _stackelberg_check_core.
    return _stackelberg_check_core(
        util_expr,
        follower_decision=e_sym,
        best_response_expr=None,
        meta=mech,
        entry_specific=True,
        paper_id=entry.get("paper_id", "<unknown>"),
        require_br_match=widened_via_opaque_sum,
    )


def _stackelberg_check_core(
    follower_utility_expr: Any,
    *,
    follower_decision: Any,
    best_response_expr: Any = None,
    meta: "dict | None" = None,
    entry_specific: bool,
    paper_id: str,
    require_br_match: bool = False,
) -> "VerificationResult | None":
    """Back-half of _try_stackelberg_latex: parsed follower-utility expr +
    decision variable in -> symbolic FOC -> best-response solve and
    cross-check against the paper's stated optimum (rejecting on a definite
    disagreement) -> IR at that optimum -> verdict.

    Behavior-preserving seam extraction (Approach C). `follower_utility_expr`
    is the resolved multi-clause follower utility; `follower_decision` is the
    follower's own decision symbol. `meta` is the entry's mechanism dict
    (only `best_response_latex` is read). `best_response_expr` is accepted for
    a future pre-parsed cross-check and is currently unused -- the check
    below still parses `meta["best_response_latex"]` itself, verbatim.
    """
    util_expr = follower_utility_expr
    e_sym = follower_decision
    mech = meta or {}

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
    br_raw = _as_str(mech.get("best_response_latex"))
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
                best_response_note = " | best_response_latex cross-check: MATCH (numeric)"

    if require_br_match and "MATCH" not in best_response_note:
        # The follower utility was widened via an opaque \sum split. That
        # split is only sound when the paper's own best_response_latex
        # confirms the derived FOC. No definite MATCH (missing / opaque /
        # unparseable best_response, or a piecewise \begin{cases} form) ->
        # fail closed rather than certify a possibly-wrong own-term
        # isolation.
        return None

    try:
        U_star = _sp.simplify(util_expr.subs(e_sym, e_star))
    except Exception:
        return None

    remaining_syms = U_star.free_symbols
    assumptions = _sp.And(*[_sp.Q.positive(s) for s in remaining_syms]) if remaining_syms else _sp.S.true
    sign = _sp.ask(_sp.Q.nonnegative(U_star), assumptions)

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

    final = finalize_verdict(ir_v == "VERIFIED", ir_v == "COUNTEREXAMPLE", entry_specific)

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
        entry_specific=entry_specific,
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

def _shapley_check_core(*, paper_id: str) -> VerificationResult:
    """
    Stub seam for Shapley verification.
    Currently returns unconditional UNSUPPORTED.
    Phase 4 will fill in the actual verification logic.
    """
    return VerificationResult(
        verdict="UNSUPPORTED", category="Shapley", paper_id=paper_id, track=1,
        notes=(
            "Roberts' Theorem: Shapley IC/IR is intractable in Z3 for general domains. "
            "Hard-gate: ic_proof_present and ir_proof_present are the primary signals."
        ),
    )


def verify_shapley(entry: dict) -> VerificationResult:
    """
    Shapley IC/IR is intractable in Z3 for general coalitional games.
    Hard-gate fields (ic_proof_present / ir_proof_present) are the primary signal.
    """
    paper_id = entry.get("paper_id", "<unknown>")
    return _shapley_check_core(paper_id=paper_id)


# ── Coalition IC (bounded, discrete Contract menus) ──────────────────────────

def verify_coalition_ic_contract(entry: dict, k: int = 2) -> VerificationResult:
    """Bounded joint-deviation IC for a numeric discrete Contract menu.

    Every other IC check in this project is against *individual* deviations.
    This adds a k=n=2 coalition check: do types 1 and 2 have a profitable
    *joint* misreport (both picking some other pair of menu items)?

    Numeric-menu-only: needs entry["menu"] with theta_i / e_i / R_i for
    i in 1..num_types. No numeric menu -> UNSUPPORTED (never a false VERIFIED).

    Assumes linear-cost quasilinear utility u = R - theta * e; does not read
    the entry's own utility_latex and does not check IR.
    """
    paper_id = entry.get("paper_id", "<unknown>")
    menu = entry.get("menu") or {}
    n = int(entry.get("num_types") or 0)
    if not menu or n == 0 or k > n:
        return VerificationResult(
            verdict="UNSUPPORTED", category="Contract", paper_id=paper_id, track=1,
            notes=f"coalition size {k} vs {n} types / no numeric menu")
    if k != 2 or n != 2:
        return VerificationResult(
            verdict="UNSUPPORTED", category="Contract", paper_id=paper_id, track=1,
            notes="only k=n=2 supported in this round")

    try:
        def u(i: int, r: int) -> float:
            return menu[f"R_{r}"] - menu[f"theta_{i}"] * menu[f"e_{r}"]

        truthful = u(1, 1) + u(2, 2)
    except (KeyError, TypeError):
        return VerificationResult(
            verdict="UNSUPPORTED", category="Contract", paper_id=paper_id, track=1,
            notes="menu is not fully numeric (theta_i / e_i / R_i)")

    for r1 in (1, 2):
        for r2 in (1, 2):
            if (r1, r2) == (1, 2):
                continue
            if u(1, r1) + u(2, r2) > truthful + 1e-9:
                gain = u(1, r1) + u(2, r2) - truthful
                return VerificationResult(
                    verdict="COUNTEREXAMPLE", category="Contract", paper_id=paper_id,
                    track=1, coalition_ic_k=k,
                    notes=f"types (1,2) jointly report ({r1},{r2}); gain {gain:.4g}")
    return VerificationResult(
        verdict="VERIFIED", category="Contract", paper_id=paper_id, track=1,
        coalition_ic_k=k,
        notes="no profitable 2-type joint deviation")


# ── Parse-only hooks (Stage 2 serializer round-trip) ─────────────────────────
#
# These do NOT solve. They re-run the same sympy-latex front-end the
# entry-specific verifiers use (normalize_left_right -> parse_latex) so a
# serializer can confirm generated LaTeX is parseable before it reaches the
# verifier. Additive: no existing function above is modified.

class ParseFailure(Exception):
    def __init__(self, field: str, reason: str):
        super().__init__(f"{field}: {reason}")
        self.field = field
        self.reason = reason


def _parse_latex_field(field: str, latex: str) -> Any:
    """Parse one LaTeX string with the same front-end the entry-specific
    verifier uses, but do no solving. Raise ParseFailure on any error."""
    try:
        from sympy.parsing.latex import parse_latex
        cleaned = normalize_left_right(latex)
        expr = parse_latex(cleaned)
        if expr is None:
            raise ValueError("parse_latex returned None")
        return expr
    except Exception as exc:  # noqa: BLE001
        raise ParseFailure(field, str(exc)) from exc


def _parse_only(mechanism: dict, fields: "tuple[str, ...]") -> dict:
    out: dict = {}
    for f in fields:
        v = mechanism.get(f)
        if isinstance(v, str) and v.strip():
            out[f] = _parse_latex_field(f, v)
    return out


# Field names below are the ones the z3_validated corpus actually uses
# (see docs/ast-coverage.md), plus the generic *_condition_latex aliases a
# serializer emits. Only fields Stage 1 turns into a proof obligation
# (utility / IC / IR / payment linear part / cost) are listed; structural
# fields (allocation_rule / objective, which carry \arg\max / \begin{cases})
# are excluded — the audit shows Stage 1 never symbolically parses them.

def parse_only_vcg(mechanism: dict) -> dict:
    return _parse_only(mechanism, (
        "payment_rule_latex", "client_utility_latex",
        "ic_condition_latex", "ir_condition_latex",
    ))


def parse_only_contract(mechanism: dict) -> dict:
    return _parse_only(mechanism, (
        "client_utility_latex", "cost_function_latex",
        "ic_screening_latex", "ir_participation_latex",
        "ic_condition_latex", "ir_condition_latex",
    ))


def parse_only_stackelberg(mechanism: dict) -> dict:
    return _parse_only(mechanism, (
        "follower_utility_latex", "best_response_latex",
        "follower_foc_latex", "leader_objective_latex",
    ))
