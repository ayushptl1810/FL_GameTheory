"""
Track 3 — δ-satisfiability via mpmath interval arithmetic.

When:  utility contains transcendental terms (ln, log, exp, sigmoid, sqrt)
       that Z3 cannot handle and SOS cannot represent as polynomial certificates.

What:  encodes the IC/IR violation condition as
         ∃θ ∈ [a, b]: f(θ) < 0
       then proves/refutes it using rigorous branch-and-bound over intervals.

Soundness guarantee: formally δ-sound, equivalent to dReal for 1D θ problems.
  δ-UNSAT → VERIFIED        (no violation within tolerance δ anywhere in domain)
  δ-SAT   → COUNTEREXAMPLE  (violation of magnitude > δ found; witness returned)

Why mpmath.iv instead of dReal:
  dReal4 has no ARM64 binary and cannot be installed on Apple Silicon via pip or
  brew.  mpmath.iv provides rigorous interval arithmetic (iv.log, iv.exp, iv.sqrt,
  etc.) natively in pure Python and gives the same formal guarantee for the
  single-variable case.

Install:  pip install sympy mpmath   (both pure-Python, ARM-native)
"""

from __future__ import annotations

import re
from typing import Any, Callable

from . import Verdict, VerificationResult, finalize_verdict, normalize_left_right, strip_redundant_outer_parens

_DEPS_OK = False

try:
    import sympy as _sp
    from sympy.parsing.latex import parse_latex as _lx_parse
    from mpmath import iv as _iv
    _DEPS_OK = True
except Exception:
    pass

_DELTA = 0.001

_THETA_SYM: Any = None
_IV_NS: dict = {}

if _DEPS_OK:
    _THETA_SYM = _sp.Symbol("_theta_")
    _IV_NS = {
        "log":  _iv.log,
        "exp":  _iv.exp,
        "sqrt": _iv.sqrt,
        "sin":  _iv.sin,
        "cos":  _iv.cos,
        "tan":  _iv.tan,
        "Abs":  _iv.fabs,
        "pi":   _iv.pi,
        "E":    _iv.e,
    }


# ── Transcendental detection ──────────────────────────────────────────────────

_TRANSCENDENTAL_RE = re.compile(
    r"\\(ln|log|exp|sigma|sin|cos|tan|sqrt|operatorname\{sigmoid\})"
)


def _has_transcendentals(latex_str: str) -> bool:
    return bool(_TRANSCENDENTAL_RE.search(latex_str or ""))


def _any_field_has_transcendentals(entry: dict) -> bool:
    mech = entry.get("mechanism") or {}
    return any(
        _has_transcendentals(mech.get(f) or "")
        for f in ("utility_function_latex", "ic_screening_latex",
                  "ir_participation_latex", "payment_rule_latex")
    )


# ── LaTeX parsing helpers ─────────────────────────────────────────────────────

def _clean_latex(s: str) -> str:
    s = re.sub(r"^[Uu]_?\{?[a-zA-Z,_]+\}?\s*=\s*", "", s.strip())
    s = normalize_left_right(s)
    s = re.sub(r"_\{[a-zA-Z]{2,}\}", "", s)
    return strip_redundant_outer_parens(s.strip())


def _unify_theta(sp_expr: Any) -> Any:
    """Replace all theta-like symbols with canonical _theta_."""
    subs = {}
    for sym in sp_expr.free_symbols:
        if re.match(r"(theta|θ)", str(sym).lower()):
            subs[sym] = _THETA_SYM
    return sp_expr.subs(subs)


def _to_iv_callable(sp_expr: Any) -> "Callable | None":
    """
    Build an mpmath.iv callable f(theta_interval) from a SymPy expression.
    Returns None if the expression contains unsupported operations.
    """
    try:
        f = _sp.lambdify(_THETA_SYM, sp_expr, modules=[_IV_NS])
        f(_iv.mpf([0.1, 0.9]))  # smoke-test: catches unsupported ops early
        return f
    except Exception:
        return None


# ── Branch-and-bound δ-verifier ───────────────────────────────────────────────

def _check_violation(
    f: Callable,
    lo: float,
    hi: float,
    delta: float,
) -> "tuple[str, float | None]":
    """
    Check ∃θ ∈ [lo, hi]: f(θ) < 0 using rigorous interval arithmetic.

    At each sub-interval [a, b]:
      - compute the interval bound [f_lo, f_hi] = f([a, b]) via mpmath.iv
      - if f_lo ≥ 0:        entire interval satisfies f ≥ 0 → prune (no violation)
      - if f_hi < -delta:   entire interval violates f < -δ → counterexample found
      - if width < delta:   within δ resolution → prune (δ-sound boundary)
      - else:               split at midpoint and enqueue both halves

    Returns:
        ('verified',       None)     — δ-UNSAT: no violation anywhere in domain
        ('counterexample', witness)  — δ-SAT:   violation at θ≈witness
        ('unknown',        None)     — interval arithmetic raised an exception
    """
    stack: list[tuple[float, float]] = [(lo, hi)]

    while stack:
        a, b = stack.pop()
        width = b - a

        try:
            val = f(_iv.mpf([a, b]))
            val_lo = float(val.a)
            val_hi = float(val.b)
        except Exception:
            return "unknown", None

        if val_lo >= 0.0:
            continue

        if val_hi < -delta:
            return "counterexample", (a + b) / 2.0

        if width < delta:
            continue

        mid = (a + b) / 2.0
        stack.append((a, mid))
        stack.append((mid, b))

    return "verified", None


def check_nonneg_box(
    sp_expr: Any,
    bounds: "list[tuple[Any, float, float]]",
    delta: float = _DELTA,
    max_boxes: int = 50_000,
) -> "tuple[str, dict[str, str] | None]":
    """
    Rigorous multi-dimensional nonnegativity check:  ∀x ∈ box: f(x) ≥ 0 ?

    bounds: list of (sympy_symbol, lo, hi) — every free symbol of sp_expr
    must appear. Generalizes _check_violation by branch-and-bound splitting
    the widest dimension. Same δ-soundness guarantee, per box:
        'verified'       — no violation of magnitude > δ anywhere in the box
        'counterexample' — a sub-box provably violates (midpoint witness)
        'unknown'        — unsupported operation, or max_boxes budget hit
    Budget-limited: k-dimensional frontiers can explode, so exhausting
    max_boxes fails closed to 'unknown' rather than looping forever.
    """
    if not _DEPS_OK:
        return "unknown", None
    syms = [b[0] for b in bounds]
    try:
        f = _sp.lambdify(syms, sp_expr, modules=[_IV_NS])
        f(*[_iv.mpf([lo, hi]) for _, lo, hi in bounds])  # smoke-test
    except Exception:
        return "unknown", None

    stack: "list[tuple[tuple[float, float], ...]]" = [
        tuple((float(lo), float(hi)) for _, lo, hi in bounds)
    ]
    seen = 0
    while stack:
        box = stack.pop()
        seen += 1
        if seen > max_boxes:
            return "unknown", None
        try:
            val = f(*[_iv.mpf([a, b]) for a, b in box])
            try:
                val_lo, val_hi = float(val.a), float(val.b)
            except AttributeError:  # constant expression → plain number
                val_lo = val_hi = float(val)
        except Exception:
            return "unknown", None

        if val_lo >= 0.0:
            continue
        if val_hi < -delta:
            witness = {str(s): f"{(a + b) / 2:.6g}" for s, (a, b) in zip(syms, box)}
            return "counterexample", witness

        widths = [b - a for a, b in box]
        w = max(widths)
        if w < delta:
            continue
        i = widths.index(w)
        a, b = box[i]
        mid = (a + b) / 2.0
        for half in ((a, mid), (mid, b)):
            nb = list(box)
            nb[i] = half
            stack.append(tuple(nb))
    return "verified", None


def max_ic_regret_over_box(
    sp_expr: Any,
    bounds: "list[tuple[Any, float, float]]",
    max_depth: int = 6,
) -> "float | None":
    """Rigorous UPPER bound on the worst-case IC-regret (max of −f) over the box.

    ``check_nonneg_box`` answers yes/no; this returns a number: how negative the
    gap ``f`` can get anywhere in the box (0.0 if provably ≥ 0). It is used only
    after the caller has already ruled the multi-symbol box "counterexample" a
    structural artifact — it lets the verdict still carry an honest
    "δ-IC on the box for δ ≥ <this>" statement instead of a bare UNKNOWN.

    Depth-bounded (not δ-resolved): k-dim B&B to δ-resolution is intractable, so
    this splits the widest dimension at most ``max_depth`` levels. ``-f_lo`` from
    mpmath.iv on any enclosing sub-box is already a rigorous over-estimate of the
    true regret inside it; deeper splits only tighten it. The returned value is
    therefore always ≥ the exact regret (safe to quote as a δ bound).

    Returns a float ≥ 0, or None on an unsupported op.
    """
    if not _DEPS_OK:
        return None
    syms = [b[0] for b in bounds]
    try:
        f = _sp.lambdify(syms, sp_expr, modules=[_IV_NS])
        f(*[_iv.mpf([lo, hi]) for _, lo, hi in bounds])
    except Exception:
        return None

    root = tuple((float(lo), float(hi)) for _, lo, hi in bounds)
    stack: "list[tuple[tuple[tuple[float, float], ...], int]]" = [(root, 0)]
    worst = 0.0
    while stack:
        box, depth = stack.pop()
        try:
            val = f(*[_iv.mpf([a, b]) for a, b in box])
            try:
                val_lo = float(val.a)
            except AttributeError:
                val_lo = float(val)
        except Exception:
            return None

        if val_lo >= 0.0:
            continue
        if depth >= max_depth:
            worst = max(worst, -val_lo)
            continue
        widths = [b - a for a, b in box]
        i = widths.index(max(widths))
        a, b = box[i]
        mid = (a + b) / 2.0
        for half in ((a, mid), (mid, b)):
            nb = list(box)
            nb[i] = half
            stack.append((tuple(nb), depth + 1))
    return worst


# ── Violation-function builders ───────────────────────────────────────────────

def _build_ic_expr(entry: dict) -> "tuple[Any | None, str]":
    """
    Build gap(x) = U(truthful) − U(misreport) from ic_screening_latex as a
    SymPy expression over ALL its free symbols. A violation exists where
    gap < 0.

    NOTE (2026-07-19): the old single-variable path unified every θ-like
    symbol into one canonical variable — for a screening IC that mentions
    both θ_n and θ_m that silently changed the condition being checked.
    Symbols are now kept independent; the multi-dim box engine handles them.
    """
    mech   = entry.get("mechanism") or {}
    ic_raw = mech.get("ic_screening_latex") or ""
    if not ic_raw:
        return None, "no ic_screening_latex field"

    for sep in (r"\geq", r"\ge", "≥"):
        if sep in ic_raw:
            lhs_s, rhs_s = ic_raw.split(sep, 1)
            break
    else:
        return None, "no ≥ separator in ic_screening_latex"

    try:
        sp_lhs = _lx_parse(_clean_latex(lhs_s))
        sp_rhs = _lx_parse(_clean_latex(rhs_s))
        return sp_lhs - sp_rhs, ""
    except Exception as exc:
        return None, f"parse error: {exc}"


def _build_ir_expr(entry: dict) -> "tuple[Any | None, str]":
    """
    Build f(x) = U(truthful) from ir_participation_latex as a SymPy
    expression over all its free symbols. A violation exists where f < 0.
    """
    mech   = entry.get("mechanism") or {}
    ir_raw = mech.get("ir_participation_latex") or ""
    if not ir_raw:
        return None, "no ir_participation_latex field"

    for sep in (r"\geq", r"\ge", "≥"):
        if sep in ir_raw:
            lhs_s, _ = ir_raw.split(sep, 1)
            break
    else:
        lhs_s = ir_raw

    try:
        return _lx_parse(_clean_latex(lhs_s)), ""
    except Exception as exc:
        return None, f"parse error: {exc}"


_MAX_BOX_DIMS = 6


def _fix_declared_constants(mech: dict, bounds: dict, subs: dict) -> "tuple[dict, dict]":
    """Pin paper-declared constants so they drop out of the interval box.

    For each ``name -> value`` in ``mech["fixed_constants"]`` (name a str,
    value an int/float), remove ``name`` from ``bounds`` and record
    ``name -> float(value)`` in ``subs``. Absent/malformed field → the
    inputs are returned unchanged.
    """
    fc = mech.get("fixed_constants")
    if not isinstance(fc, dict):
        return bounds, subs
    nb, ns = dict(bounds), dict(subs)
    for name, val in fc.items():
        if not isinstance(name, str) or isinstance(val, bool) or not isinstance(val, (int, float)):
            continue
        nb.pop(name, None)
        ns[name] = float(val)
    return nb, ns


def _bounds_for(sp_expr: Any, theta_min: float, theta_max: float) -> "list[tuple[Any, float, float]]":
    """θ-like symbols get the entry's declared type domain; every other
    free symbol gets a generic positive box [0.001, 100]."""
    bounds = []
    for s in sorted(sp_expr.free_symbols, key=str):
        if re.match(r"(theta|θ)", str(s).lower()):
            bounds.append((s, theta_min, theta_max))
        else:
            bounds.append((s, 0.001, 100.0))
    return bounds


# ── Public entry point ────────────────────────────────────────────────────────

def verify_track3(entry: dict) -> "VerificationResult | None":
    """
    δ-satisfiability for transcendental IC/IR via mpmath interval arithmetic.

    Returns None if no transcendental functions are detected (not a Track 3 entry).
    Returns UNSUPPORTED if sympy or mpmath are not installed.
    """
    if not _any_field_has_transcendentals(entry):
        return None

    paper_id = entry.get("paper_id", "<unknown>")
    category = entry.get("category", "")

    if not _DEPS_OK:
        return VerificationResult(
            verdict="UNSUPPORTED",
            category=category,
            paper_id=paper_id,
            track=3,
            notes=(
                "Transcendental utility detected — requires sympy and mpmath. "
                "Install: pip install sympy mpmath"
            ),
        )

    mech      = entry.get("mechanism") or {}
    theta_min = float(mech.get("type_space_min") or 0.001)
    theta_max = float(mech.get("type_space_max") or 1.0)
    if theta_min <= 0:
        theta_min = 0.001   # guard against log(0)
    if theta_min >= theta_max:
        theta_min, theta_max = 0.001, 1.0

    # Front-end: LaTeX → SymPy + bound extraction. The seam helper below takes
    # only parsed exprs + bounds and never touches `entry`.
    ic_expr, ic_err = _build_ic_expr(entry)
    ir_expr, ir_err = _build_ir_expr(entry)
    ic_bounds = _bounds_for(ic_expr, theta_min, theta_max) if ic_expr is not None else []
    ir_bounds = _bounds_for(ir_expr, theta_min, theta_max) if ir_expr is not None else []

    has_latex = bool(
        mech.get("ic_screening_latex") or
        mech.get("ir_participation_latex")
    )

    return track3_check_from_sympy(
        ic_expr, ir_expr, ic_bounds, ir_bounds, _DELTA,
        ic_err=ic_err, ir_err=ir_err,
        entry_specific=has_latex, paper_id=paper_id, category=category,
        theta_min=theta_min, theta_max=theta_max, mech=mech,
    )


def track3_check_from_sympy(
    ic_expr: "Any | None",
    ir_expr: "Any | None",
    ic_bounds: "list[tuple[Any, float, float]]",
    ir_bounds: "list[tuple[Any, float, float]]",
    delta: float,
    *,
    ic_err: str = "",
    ir_err: str = "",
    entry_specific: bool,
    paper_id: str,
    category: str = "",
    theta_min: float = 0.001,
    theta_max: float = 1.0,
    mech: "dict | None" = None,
) -> "VerificationResult":
    """SymPy-in seam: interval back-half of verify_track3.

    Given the parsed IC/IR SymPy expressions and their per-symbol bound lists
    (``[(sympy_symbol, lo, hi), ...]``), run the mpmath.iv branch-and-bound
    δ-check over the type box and finalize the verdict. Does no ``entry`` or
    LaTeX parsing. δ-soundness semantics unchanged: δ-UNSAT → VERIFIED,
    δ-SAT (1-D) → COUNTEREXAMPLE.
    """
    conditions: list[str] = []
    verdicts:   list[Verdict] = []
    counterexample: "dict[str, str] | None" = None

    # NOTE on counterexample policy (2026-07-19): in a screening IC/IR the
    # indexed symbols (menu rewards R_n, the other type's θ_m, ...) are NOT
    # free parameters — they are pinned by the paper's menu and its type
    # ordering. A box violation that ignores those couplings can be exactly
    # the kind of artifact the Contract Z3 track had before its type-ordering
    # fix. So the standalone Track 3 path asserts VERIFIED (sound: proven on
    # a SUPERSET of the coupled domain) but suppresses box counterexamples
    # to UNKNOWN when the expression has more than one free symbol.

    def _run(kind: str, expr: Any, err: str, bounds: "list[tuple[Any, float, float]]") -> None:
        nonlocal counterexample
        if expr is None:
            verdicts.append("UNKNOWN")
            conditions.append(f"{kind}: could not build formula — {err}")
            return
        if not bounds:
            verdicts.append("UNKNOWN")
            conditions.append(f"{kind}: constant expression — nothing to check")
            return
        # Pin paper-declared constants: they leave the box and are substituted
        # into the expression, shrinking the branch-and-bound search.
        bmap = {str(s): (s, lo, hi) for s, lo, hi in bounds}
        nb, ns = _fix_declared_constants(mech or {}, bmap, {})
        if ns:
            expr = expr.subs({bmap[n][0]: v for n, v in ns.items() if n in bmap})
            bounds = [bmap[n] for n in nb if n in bmap]
            conditions.append(
                f"{kind}: pinned declared constants "
                + ", ".join(f"{n}={v}" for n, v in sorted(ns.items()))
            )
        if not bounds:
            verdicts.append("UNKNOWN")
            conditions.append(f"{kind}: all free variables pinned — nothing to check")
            return
        if len(bounds) > _MAX_BOX_DIMS:
            verdicts.append("UNKNOWN")
            conditions.append(f"{kind}: {len(bounds)} free variables — box search intractable")
            return
        status, witness = check_nonneg_box(expr, bounds, delta)
        dims = len(bounds)
        if status == "verified":
            verdicts.append("VERIFIED")
            conditions.append(
                f"{kind}: δ-UNSAT (no violation within δ={delta}) over "
                f"{dims}-dim box, θ∈[{theta_min},{theta_max}]  [mpmath.iv]"
            )
        elif status == "counterexample":
            if dims > 1:
                verdicts.append("UNKNOWN")
                regret = max_ic_regret_over_box(expr, bounds)
                if regret is not None and regret > 0.0:
                    conditions.append(
                        f"{kind}: box violation found but suppressed — indexed menu/type "
                        "symbols are not free parameters (ordering-artifact risk). "
                        f"Honest δ-bounded IC-regret over the {dims}-dim independent "
                        f"type/reward box: max gap deficit ≈ {regret:.4g} "
                        f"(mechanism is δ-IC on the box for δ ≥ {regret:.4g})"
                    )
                else:
                    conditions.append(
                        f"{kind}: box violation found but suppressed — indexed menu/type "
                        "symbols are not free parameters (ordering-artifact risk)"
                    )
            else:
                verdicts.append("COUNTEREXAMPLE")
                if counterexample is None:
                    counterexample = witness
                conditions.append(f"{kind}: δ-SAT — counterexample at {witness}")
        else:
            verdicts.append("UNKNOWN")
            conditions.append(f"{kind}: interval search inconclusive (unsupported op or budget)")

    _run("IC", ic_expr, ic_err, ic_bounds)
    _run("IR", ir_expr, ir_err, ir_bounds)

    all_ok  = all(v == "VERIFIED"       for v in verdicts)
    has_cex = any(v == "COUNTEREXAMPLE" for v in verdicts)

    final: Verdict = finalize_verdict(all_ok, has_cex, entry_specific)

    return VerificationResult(
        verdict=final,
        category=category,
        paper_id=paper_id,
        track=3,
        conditions=conditions,
        counterexample=counterexample,
        notes=(
            f"δ={delta} | domain=[{theta_min},{theta_max}]"
            " | mpmath.iv branch-and-bound | guarantee: δ-sound, not exact"
        ),
        entry_specific=entry_specific,
    )


# ── Parse-only hook (Stage 2 serializer round-trip) ──────────────────────────
# Additive: reuses track1_z3._parse_only. Covers the transcendental-carrying
# fields (ln / exp) — same IC/IR/utility fields, routed here when Track 1's
# polynomial path cannot represent them.

def parse_only_transcendental(mechanism: dict) -> dict:
    from tracks.track1_z3 import _parse_only
    return _parse_only(mechanism, (
        "follower_utility_latex", "client_utility_latex",
        "ic_screening_latex", "ir_participation_latex",
        "ic_condition_latex", "ir_condition_latex",
    ))
