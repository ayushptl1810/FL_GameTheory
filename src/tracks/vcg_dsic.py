"""VCG allocation / payment LaTeX parsers + Z3 grid context.

Phase 2, Task 3.  Classifies the diverse allocation/payment LaTeX found in the
VCG corpus into a small tagged union so Task 4's ``verify_vcg_dsic`` can prove
dominant-strategy IC on a finite bid grid instead of regex-matching the payment
shape.  Anything not confidently classified returns ``None`` -- the caller turns
that into UNKNOWN/UNSUPPORTED.  Never guess.
"""

from __future__ import annotations

import re
from collections import namedtuple
from dataclasses import dataclass

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
            win = z3.And(*[my_bid >= o for o in others])
            if isinstance(pay, ClarkePivot):
                price = max_other
            else:
                raise NotImplementedError(f"payment spec {pay!r}: Task 4")
            return z3.If(win, my_val - price, z3.RealVal(0))

        raise NotImplementedError(f"allocation spec {alloc!r}: Task 4")

    return utility


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
