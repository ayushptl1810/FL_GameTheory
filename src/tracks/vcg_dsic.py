"""VCG allocation / payment LaTeX parsers + Z3 grid context.

Phase 2, Task 3.  Classifies the diverse allocation/payment LaTeX found in the
VCG corpus into a small tagged union so Task 4's ``verify_vcg_dsic`` can prove
dominant-strategy IC on a finite bid grid instead of regex-matching the payment
shape.  Anything not confidently classified returns ``None`` -- the caller turns
that into UNKNOWN/UNSUPPORTED.  Never guess.
"""

from __future__ import annotations

import itertools
import re
from collections import namedtuple
from dataclasses import dataclass

from tracks import VerificationResult, finalize_verdict

try:  # only ArgmaxWelfare / ExplicitFormula objective parsing needs sympy
    import sympy
except Exception:  # pragma: no cover
    sympy = None

import z3

_PROFILE_CAP = 4096


# --------------------------------------------------------------------------- #
# AllocSpec tagged union                                                      #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class HighestBidder:
    """Single item to the highest bidder (b_i = max_j b_j)."""


@dataclass(frozen=True)
class TopK:
    """The k winners with the highest (or lowest) score / bid."""

    k: int | None = None
    lowest: bool = False  # True => k *lowest* bids win (reverse auction)


@dataclass(frozen=True)
class ProportionalShare:
    """Divisible allocation p_s = f_s^{a-1} / sum_s' f_s'^{a-1}."""

    exponent: object = None  # sympy expr or raw string for "a-1"


@dataclass(frozen=True)
class ArgmaxWelfare:
    """x* in argmax of a social-welfare objective."""

    objective_expr: object = None  # sympy expr if parseable, else raw string


AllocSpec = (HighestBidder, TopK, ProportionalShare, ArgmaxWelfare)


# --------------------------------------------------------------------------- #
# PaySpec tagged union                                                        #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ClarkePivot:
    """Payment is the Clarke pivot / externality, computed from the allocation."""


@dataclass(frozen=True)
class ExplicitFormula:
    """A closed-form payment purely in b / v."""

    expr: object = None  # sympy expr if parseable, else raw string


PaySpec = (ClarkePivot, ExplicitFormula)


# --------------------------------------------------------------------------- #
# allocation parser                                                           #
# --------------------------------------------------------------------------- #
_ALGO_RE = re.compile(r"\\text\{[^}]*\b(algorithm|procedure|output of)\b", re.I)
_ARGMAX_RE = re.compile(r"\\arg\s*\\?max|\bargmax\b", re.I)
_HIGHEST_RE = re.compile(
    r"b_\{?i\}?\s*=\s*\\max|\\max_?\{?j\}?\s*b_?\{?j\}?|highest\s+bid", re.I
)
_TOPK_RE = re.compile(
    r"top[-\s]?k|k[-\s]?(?:winners|clients|lowest)|"
    r"i\s*\\leq\s*k|lowest[-\s]*bid|lowest\s+bids|K_j\s+clients", re.I
)
_PROP_RE = re.compile(r"\\frac\{[^}]*\^\{?[^}]*-\s*1\}?[^}]*\}\{\s*\\sum", re.I)
# An explicit winner-count cue: "top-2", "top $k$", "K clients", "k winners",
# "k highest/lowest".  Checked BEFORE _HIGHEST_RE so a multi-winner rule that
# also says "highest bids" is not misclassified as single-item HighestBidder.
_WINNER_COUNT_RE = re.compile(
    r"top[-\s]?\$?\{?\s*(\d+|[kK])\b|"
    r"\b(\d+|[kK])\s+(?:winners|clients|bidders|agents)\b|"
    r"K_j\s+clients|"
    r"\b([kK])\s+(?:highest|lowest)\b",
    re.I,
)


def _extract_objective(latex: str):
    """Grab the expression after argmax; return sympy expr or raw string."""
    m = re.search(r"\[(?:[^\[\]]*?:?=)?\s*([^\[\]]+)\]", latex)
    raw = None
    if m:
        raw = m.group(1)
    else:
        m = re.search(r"\\arg\s*\\?max[_^]?\{?[^}]*\}?\s*(.+)", latex, re.I)
        if m:
            raw = m.group(1)
    if raw is None:
        return latex
    raw = re.split(r"\\quad|\\text\{s\.t\.|s\.t\.|\\;", raw)[0].strip()
    if sympy is not None:
        cleaned = re.sub(r"\\[a-zA-Z]+|[{}\\]", " ", raw).replace("^", "**")
        try:
            return sympy.sympify(cleaned)
        except Exception:
            pass
    return raw


def parse_allocation(latex: str):
    """LaTeX allocation rule -> AllocSpec instance, or None if unclassifiable."""
    if not latex or not isinstance(latex, str):
        return None
    s = latex.strip()

    if _ALGO_RE.search(s):
        return None

    if _PROP_RE.search(s):
        m = re.search(r"\^\{?\s*([A-Za-z0-9]+)\s*-\s*1\s*\}?", s)
        exp_raw = f"{m.group(1)}-1" if m else "a-1"
        exp = exp_raw
        if sympy is not None:
            try:
                exp = sympy.sympify(exp_raw.replace("^", "**"))
            except Exception:
                exp = exp_raw
        return ProportionalShare(exponent=exp)

    mcount = _WINNER_COUNT_RE.search(s)
    if mcount:
        grp = next((g for g in mcount.groups() if g), None)
        lowest = bool(re.search(r"lowest", s, re.I))
        if grp and grp.isdigit():
            cnt = int(grp)
            if cnt != 1:
                return TopK(k=cnt, lowest=lowest)
        elif grp is not None or "k_j" in s.lower():
            # symbolic count (k / K / K_j) -> cardinality unknown -> downstream UNKNOWN
            return TopK(k=None, lowest=lowest)

    if _HIGHEST_RE.search(s):
        return HighestBidder()

    if _ARGMAX_RE.search(s):
        return ArgmaxWelfare(objective_expr=_extract_objective(s))

    if _TOPK_RE.search(s):
        lowest = bool(re.search(r"lowest", s, re.I))
        m = re.search(r"\btop[-\s]?(\d+)", s, re.I)
        k = int(m.group(1)) if m else None
        return TopK(k=k, lowest=lowest)

    return None


# --------------------------------------------------------------------------- #
# payment parser                                                              #
# --------------------------------------------------------------------------- #
_CLARKE_RE = re.compile(
    r"\\max_?\{?\s*j\s*\\neq\s*i\}?|"                       # max_{j != i} b_j (2nd price)
    r"\\sum_?\{?\s*[kj]\s*\\neq\s*i\}?|"                    # sum_{k != i} ... (externality)
    r"\(?K\s*\+\s*1\)?[- ]?th|_\{?k\s*\+\s*1\}?|v_\{?k\+1\}?|"  # (K+1)-th lowest / v_{k+1}
    r"W_?\{?-i\}?|\\phi\(W\)\s*-\s*\\phi\(W\s*\\setminus|"  # W_{-i} / phi(W)-phi(W\{i})
    r"r\(x\^?\*?\)\s*-\s*\\sum|S\(x\^?\*?\)\s*-\s*S\(",     # r(x*) - sum / S(x*)-S(z*)
    re.I,
)
_UNKNOWN_FN_RE = re.compile(
    r"Punish|Algorithm|\\setminus\(|F_\{?\\setminus|_\{?\\setminus|\\det|\\log", re.I
)


def parse_payment(latex: str, alloc):
    """LaTeX payment rule (+ parsed alloc) -> PaySpec instance, or None."""
    if not latex or not isinstance(latex, str):
        return None
    s = latex.strip()

    if _ALGO_RE.search(s):
        return None

    if _CLARKE_RE.search(s):
        return ClarkePivot()

    body = s.split("=", 1)[1] if "=" in s else s
    if _UNKNOWN_FN_RE.search(body):
        return None
    tokens = re.sub(r"\\[a-zA-Z]+|[{}\\()\[\]]", " ", body)
    has_bid_var = re.search(r"\b[bv]_", body) or re.search(r"\b[bv]\b", tokens)
    if not has_bid_var:
        return None
    expr = body.strip()
    if sympy is not None:
        cleaned = re.sub(r"\\[a-zA-Z]+|[{}\\]", " ", body).replace("^", "**")
        try:
            expr = sympy.sympify(cleaned)
        except Exception:
            expr = body.strip()
    return ExplicitFormula(expr=expr)


# --------------------------------------------------------------------------- #
# Z3 grid context                                                             #
# --------------------------------------------------------------------------- #
GridCtx = namedtuple(
    "GridCtx",
    ["v", "b", "points", "n_bidders", "n_attrs", "k", "profile_count"],
)


def build_grid(n_bidders: int, n_attrs: int, k: int) -> GridCtx:
    """Z3 Real vars v[i][a], b[i][a] and a k-point grid on [0, 1]."""
    if k < 2:
        raise ValueError("need k >= 2 grid points")
    v = [[z3.Real(f"v_{i}_{a}") for a in range(n_attrs)] for i in range(n_bidders)]
    b = [[z3.Real(f"b_{i}_{a}") for a in range(n_attrs)] for i in range(n_bidders)]
    points = [i / (k - 1) for i in range(k)]
    profile_count = k ** (n_bidders * n_attrs)
    return GridCtx(v, b, points, n_bidders, n_attrs, k, profile_count)


# --------------------------------------------------------------------------- #
# utility encoder (minimal; Task 4 will exercise / extend)                    #
# --------------------------------------------------------------------------- #
def encode_utility(grid: GridCtx, alloc, pay):
    """Return f(i, bid_profile) -> z3 expr for bidder i's utility.

    bid_profile: list-of-lists of z3 numerals/exprs, shape [n_bidders][n_attrs].
    Minimal single-good VCG semantics: HighestBidder allocation with a
    second-price (ClarkePivot) payment.  Other specs raise NotImplementedError
    so Task 4 fills them in deliberately rather than silently mis-encoding.
    """

    def _scalar(row):
        return z3.Sum(*row) if len(row) > 1 else row[0]

    def utility(i, bid_profile):
        my_val = grid.v[i][0] if grid.n_attrs == 1 else z3.Sum(*grid.v[i])
        my_bid = _scalar(bid_profile[i])
        others = [_scalar(bid_profile[j]) for j in range(grid.n_bidders) if j != i]

        if isinstance(alloc, HighestBidder):
            if not others:
                return my_val
            max_other = others[0]
            for o in others[1:]:
                max_other = z3.If(o > max_other, o, max_other)
            # NOTE (I2): ties -> every tied bidder "wins" and pays the rule.
            # For ClarkePivot this is harmless (price == my_bid on a tie -> u==0).
            # For ExplicitFormula f(b) a real single-winner mechanism would give
            # 0 w.p. <1 on a tie; the all-win encoding could in principle
            # manufacture a false COUNTEREXAMPLE for some f. No such f found
            # among currently-accepted payment forms.  ponytail: tie-break to
            # lowest index + downgrade to UNKNOWN if a witness sits on a tie,
            # if a payment form ever exploits this.
            win = z3.And(*[my_bid >= o for o in others])
            if isinstance(pay, ClarkePivot):
                price = max_other
            elif isinstance(pay, ExplicitFormula):
                price = _explicit_price_z3(pay.expr, my_bid, my_val)
            else:
                raise NotImplementedError(f"payment spec {pay!r}: Task 4")
            return z3.If(win, my_val - price, z3.RealVal(0))

        raise NotImplementedError(f"allocation spec {alloc!r}: Task 4")

    return utility


# --------------------------------------------------------------------------- #
# sympy payment expr -> z3                                                     #
# --------------------------------------------------------------------------- #
def _salvage_scalar_expr(raw):
    """Best-effort: turn a raw payment string like ``b_i / 2 \\text{ if } x_i=1``
    into a sympy expr in {b_i, v_i}.  Returns the sympy expr, or the raw input
    unchanged if it cannot be parsed cleanly."""
    if sympy is None or not isinstance(raw, str):
        return raw
    head = re.split(r"\\text\{|\\quad|\\;|,|;|\bif\b|\botherwise\b", raw)[0]
    cleaned = re.sub(r"\\[a-zA-Z]+|[{}\\]", " ", head).replace("^", "**").strip()
    if not cleaned:
        return raw
    try:
        expr = sympy.sympify(cleaned)
    except Exception:
        return raw
    return expr if getattr(expr, "free_symbols", None) is not None else raw


_PRICE_SYMS = {"b_i", "b", "v_i", "v"}


def _explicit_price_z3(expr, my_bid, my_val):
    """sympy payment expr (symbols subset of {b_i,b,v_i,v}) -> z3 arithmetic."""
    if sympy is None or not hasattr(expr, "free_symbols"):
        raise NotImplementedError(f"payment expr not symbolic: {expr!r}")
    names = {str(s) for s in expr.free_symbols}
    if not names <= _PRICE_SYMS:
        raise NotImplementedError(f"payment expr symbols {names}: Task 4")
    env = {"b_i": my_bid, "b": my_bid, "v_i": my_val, "v": my_val}

    def rec(e):
        if e.is_Symbol:
            return env[str(e)]
        if e.is_Integer:
            return z3.RealVal(int(e))
        if e.is_Rational:
            return z3.RealVal(f"{e.p}/{e.q}")
        if e.is_Float:
            return z3.RealVal(float(e))
        if e.is_Add:
            return z3.Sum(*[rec(a) for a in e.args])
        if e.is_Mul:
            out = rec(e.args[0])
            for a in e.args[1:]:
                out = out * rec(a)
            return out
        if e.is_Pow:
            base, exp = e.args
            if exp.is_Integer and int(exp) >= 0:
                out = z3.RealVal(1)
                for _ in range(int(exp)):
                    out = out * rec(base)
                return out
        raise NotImplementedError(f"payment expr node {e!r}: Task 4")

    return rec(expr)


# --------------------------------------------------------------------------- #
# the real finite-grid DSIC + IR check                                        #
# --------------------------------------------------------------------------- #
def _n_attrs_from_value_latex(entry: dict) -> int:
    mech = entry.get("mechanism") or {}
    for key in ("value_latex", "client_value_latex", "valuation_latex",
                "client_utility_latex"):
        s = mech.get(key) or entry.get(key)
        if isinstance(s, str) and (
            re.search(r"\\mathbb\{R\}\^\{?\s*[dnDN]", s)
            or re.search(r"v_\{?i\s*,", s)
            or re.search(r"\\sum_\{?\s*a\b", s)
        ):
            return 2
    return 1


def _result(entry: dict, verdict: str, *, notes: str = "",
            entry_specific: bool = False, counterexample=None) -> VerificationResult:
    return VerificationResult(
        verdict=verdict,
        category=entry.get("category") or "VCG",
        paper_id=entry.get("paper_id") or "?",
        track=1,
        notes=notes,
        entry_specific=entry_specific,
        counterexample=counterexample,
    )


def verify_vcg_dsic(entry: dict, *, k: int = 3) -> VerificationResult:
    """Finite-grid Z3 proof of dominant-strategy IC + IR for a VCG entry.

    Fail-closed: anything not confidently encodable returns UNKNOWN/UNSUPPORTED,
    never VERIFIED or COUNTEREXAMPLE.
    """
    mech = entry.get("mechanism") or {}
    alloc_tex = mech.get("allocation_rule_latex") or entry.get("allocation_rule_latex")
    pay_tex = mech.get("payment_rule_latex") or entry.get("payment_rule_latex")

    if not alloc_tex and not pay_tex:
        return _result(entry, "UNSUPPORTED", notes="no allocation/payment LaTeX")
    if not alloc_tex or not pay_tex:
        return _result(entry, "UNKNOWN",
                       notes="only one of allocation/payment LaTeX present")

    n = int(mech.get("num_clients") or entry.get("num_clients") or 2)
    n_attrs = _n_attrs_from_value_latex(entry)
    if n < 2:
        return _result(entry, "UNKNOWN",
                       notes="DSIC vacuous / unencodable for n<2 (payment never binds)")

    alloc = parse_allocation(alloc_tex)
    pay = parse_payment(pay_tex, alloc)
    if alloc is None or pay is None:
        return _result(entry, "UNKNOWN",
                       notes="allocation/payment LaTeX did not parse")

    # salvage a raw-string ExplicitFormula payment into a sympy expr
    if isinstance(pay, ExplicitFormula) and isinstance(pay.expr, str):
        salvaged = _salvage_scalar_expr(pay.expr)
        if isinstance(salvaged, str):
            return _result(entry, "UNKNOWN",
                           notes="payment formula is an unparsed raw string")
        pay = ExplicitFormula(expr=salvaged)

    # reject specs that still carry raw-string / unknown parameters
    if isinstance(alloc, TopK) and alloc.k is None:
        return _result(entry, "UNKNOWN", notes="TopK.k unknown")
    if isinstance(alloc, ProportionalShare) and isinstance(alloc.exponent, str):
        return _result(entry, "UNKNOWN", notes="ProportionalShare exponent raw string")
    if isinstance(alloc, ArgmaxWelfare) and isinstance(alloc.objective_expr, str):
        return _result(entry, "UNKNOWN", notes="ArgmaxWelfare objective raw string")

    grid = build_grid(n, n_attrs, k)
    if grid.profile_count > _PROFILE_CAP:
        return _result(
            entry, "UNKNOWN",
            notes=(f"grid too big: k={k}^(n_bidders={n}*n_attrs={n_attrs}) = "
                   f"{grid.profile_count} > {_PROFILE_CAP}"),
        )

    # encode_utility is a factory; the NotImplementedError for an unsupported
    # combo is raised by the returned closure at call time, inside the loop below.
    utility = encode_utility(grid, alloc, pay)
    pts = grid.points

    def dom(var):
        return z3.Or(*[var == p for p in pts])

    # every vector of concrete grid deviations for one bidder's bid
    deviations = [list(c) for c in itertools.product(pts, repeat=n_attrs)]

    has_cex = False
    cex = None
    try:
        for i in range(n):
            s = z3.Solver()
            for a in range(n_attrs):
                s.add(dom(grid.v[i][a]))
            for j in range(n):
                if j == i:
                    continue
                for a in range(n_attrs):
                    s.add(dom(grid.b[j][a]))
            truthful = [
                [grid.v[i][a] for a in range(n_attrs)] if j == i
                else [grid.b[j][a] for a in range(n_attrs)]
                for j in range(n)
            ]
            # utility() is the encode_utility closure; NotImplementedError for an
            # unencodable alloc/pay combo fires HERE, at call time -> fail closed.
            u_true = utility(i, truthful)

            # IR: u_i(truthful) >= 0 on the whole grid
            s.push()
            s.add(u_true < 0)
            r = s.check()
            if r == z3.sat:
                m = s.model()
                cex = {
                    "deviator": str(i),
                    "violation": "IR",
                    "profile": {str(d): str(m[d]) for d in m.decls()},
                }
                has_cex = True
                s.pop()
                break
            if r != z3.unsat:
                s.pop()
                return _result(entry, "UNKNOWN",
                               notes=f"z3 returned {r} for bidder {i} IR check")
            s.pop()

            # DSIC: no concrete grid deviation beats truthful
            for dev in deviations:
                dev_profile = [
                    [z3.RealVal(f"{v}") for v in dev] if j == i
                    else [grid.b[j][a] for a in range(n_attrs)]
                    for j in range(n)
                ]
                u_dev = utility(i, dev_profile)
                s.push()
                s.add(u_true < u_dev)
                r = s.check()
                if r == z3.sat:
                    m = s.model()
                    gain = m.eval(u_dev - u_true, model_completion=True)
                    cex = {
                        "deviator": str(i),
                        "violation": "DSIC",
                        "deviation_bid": str(dev),
                        "gain": str(gain),
                        "profile": {str(d): str(m[d]) for d in m.decls()},
                    }
                    has_cex = True
                    s.pop()
                    break
                if r != z3.unsat:
                    s.pop()
                    return _result(
                        entry, "UNKNOWN",
                        notes=f"z3 returned {r} for bidder {i} DSIC check")
                s.pop()
            if has_cex:
                break
    except NotImplementedError as exc:
        return _result(entry, "UNKNOWN",
                       notes=f"allocation/payment combo not encodable: {exc}")

    all_ok = not has_cex
    verdict = finalize_verdict(all_ok, has_cex, entry_specific=True)
    notes = (f"DSIC + IR exact on grid k={k}, {grid.profile_count} profiles"
             if all_ok else
             f"profitable deviation found on grid k={k}, "
             f"{grid.profile_count} profiles")
    return _result(entry, verdict, notes=notes, entry_specific=True,
                   counterexample=cex)


if __name__ == "__main__":  # tiny self-check
    assert isinstance(parse_allocation(r"b_i = \max_j b_j"), HighestBidder)
    assert parse_allocation(
        r"W \in \arg\max [SW := v(W) - c f(W)]"
    ).__class__.__name__ == "ArgmaxWelfare"
    assert isinstance(
        parse_allocation(r"p = \frac{f_s^{\alpha-1}}{\sum_{s'} f_{s'}^{\alpha-1}}"),
        ProportionalShare,
    )
    assert isinstance(
        parse_allocation(r"K_j \text{ clients with the lowest bids}"), TopK
    )
    assert parse_allocation(r"x = \text{the output of Algorithm 3}") is None
    assert isinstance(parse_payment(r"p_i = \max_{j \neq i} b_j", None), ClarkePivot)
    assert isinstance(
        parse_payment(r"p_i = v_i(W) - \sum_{k \neq i} c_k f_k", None), ClarkePivot
    )
    assert isinstance(parse_payment(r"p_i = \min(\rho^*, b_i)", None), ExplicitFormula)
    g = build_grid(2, 1, 3)
    assert g.profile_count == 9 and g.points == [0.0, 0.5, 1.0]
    print("vcg_dsic self-check OK")
