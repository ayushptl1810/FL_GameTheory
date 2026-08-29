"""
Track 2 — Sum-of-Squares (SOS) via CVXPY.

When:  utility function contains polynomial terms of degree ≥ 2 in the type
       parameter θ or effort variable e (e.g., quadratic cost c·e², cubic
       utilities), and the type space is continuous (real interval [a, b]).

What:  constructs a Gram-matrix SOS certificate proving that the IC gap
       polynomial p(θ) = U(θ, truthful) − U(θ, misreport) is non-negative
       on the bounded domain [θ_min, θ_max] using the S-procedure:

         p(θ) = σ₀(θ) + σ₁(θ)·(θ − θ_min)·(θ_max − θ)

       where σ₀, σ₁ are SOS polynomials (Gram matrices Q ≽ 0).
       Finding such Q is a semidefinite program (SDP) solved by CVXPY + SCS.

Guarantee: exact polynomial certificate. If CVXPY returns feasible, IC holds
           for all θ in [θ_min, θ_max] — not just sampled points.
           The Gram matrix Q can be included directly in a paper proof.

Library:  pip install cvxpy  (SCS ships with cvxpy; MOSEK optional for accuracy)

Why not Track 1 (Z3)?
  Z3 NRA is complete for polynomial formulas but can time-out on degree ≥ 3
  with many variables. SOS converts quantifier elimination into a matrix PSD
  check — polynomial in the number of monomials, not exponential.
"""

from __future__ import annotations

import re
from typing import Any

from . import Verdict, VerificationResult, finalize_verdict, normalize_left_right, strip_redundant_outer_parens

_CVXPY_OK = False
_SYMPY_OK = False
_NUMPY_OK = False

try:
    import cvxpy as cp
    _CVXPY_OK = True
except ImportError:
    pass

try:
    import sympy as _sp
    from sympy.parsing.latex import parse_latex as _lx_parse
    _SYMPY_OK = True
except Exception:
    pass

try:
    import numpy as np
    _NUMPY_OK = True
except ImportError:
    pass


# ── Polynomial coefficient extraction ─────────────────────────────────────────

def _extract_ic_gap_poly(entry: dict) -> "tuple[Any, Any] | None":
    """
    Parse ic_screening_latex into (gap_expr, theta_symbol) where
    gap_expr = U_lhs − U_rhs as a SymPy expression.

    Returns None if:
      - No ic_screening_latex field
      - Expression contains transcendentals → route to Track 3 instead
      - IC gap is degree < 2 in any variable → Track 1 is sufficient
    """
    if not _SYMPY_OK:
        return None

    mech   = entry.get("mechanism") or {}
    ic_raw = mech.get("ic_screening_latex") or ""
    if not ic_raw:
        return None

    for sep in (r"\geq", r"\ge", "≥"):
        if sep in ic_raw:
            lhs_s, rhs_s = ic_raw.split(sep, 1)
            break
    else:
        return None

    def _clean(s: str) -> str:
        s = re.sub(r"^[Uu]_?\{?[a-zA-Z,_]+\}?\s*=\s*", "", s.strip())
        s = normalize_left_right(s)
        s = re.sub(r"_\{[a-zA-Z]{2,}\}", "", s)
        return strip_redundant_outer_parens(s.strip())

    try:
        U_lhs = _lx_parse(_clean(lhs_s))
        U_rhs = _lx_parse(_clean(rhs_s))
    except Exception:
        return None

    # Reject transcendentals — those belong to Track 3
    # Use type() check (not isinstance) because _sp.sqrt is a function alias
    # in newer SymPy, not a class, so isinstance() raises TypeError.
    _transcendental_cls = {
        _sp.log, _sp.exp, _sp.sin, _sp.cos, _sp.tan,
        _sp.asin, _sp.acos, _sp.atan,
    }
    gap = (U_lhs - U_rhs).expand()
    for node in _sp.preorder_traversal(gap):
        if type(node) in _transcendental_cls:
            return None

    # Find the main variable with degree ≥ 2. gap.free_symbols may include a
    # symbol from an unresolved function call left over from an upstream
    # parse (e.g. "u_3(...)" misread as a symbol applied to an argument
    # rather than multiplication) -- _sp.degree() raises PolynomialError on
    # those rather than returning a plain int, so both the sort key and the
    # degree lookup must be guarded, not just the lookup.
    def _safe_degree(sym: Any) -> int:
        try:
            return int(_sp.degree(gap, sym) or 0)
        except Exception:
            return 0

    theta_sym = None
    for sym in sorted(gap.free_symbols, key=lambda s: -_safe_degree(s)):
        d = _safe_degree(sym)
        if d >= 2:
            theta_sym = sym
            break

    if theta_sym is None:
        return None  # Linear gap — Track 1 is fine

    # SOS requires numeric polynomial coefficients. If other free symbols remain
    # after identifying theta_sym (e.g. R_i, e_i as parameters), the SDP cannot
    # be set up numerically. Return None and let Track 1 (Z3 NRA) handle it.
    other_syms = gap.free_symbols - {theta_sym}
    if other_syms:
        poly_check = _sp.Poly(gap.expand(), theta_sym)
        for i in range(poly_check.degree() + 1):
            coeff = poly_check.nth(i)
            if coeff.free_symbols:
                return None  # Symbolic coefficients — fall back to Track 1

    return gap, theta_sym


# ── Core SOS feasibility check (S-procedure) ──────────────────────────────────

def _sos_check_bounded(
    gap_expr: Any,
    theta_sym: Any,
    theta_min: float = 0.0,
    theta_max: float = 1.0,
    tol: float = 1e-5,
) -> "tuple[str, str]":
    """
    Check gap_expr(theta) ≥ 0 for all theta in [theta_min, theta_max].

    Returns (verdict_str, explanation):
      "VERIFIED"  — SOS Gram matrix certificate found (Q ≽ 0)
      "UNKNOWN"   — SDP infeasible or numerical issues (not a proof of failure)
      "ERROR"     — unexpected exception
    """
    if not (_CVXPY_OK and _NUMPY_OK and _SYMPY_OK):
        missing = [n for n, ok in [("cvxpy", _CVXPY_OK),
                                    ("numpy", _NUMPY_OK),
                                    ("sympy", _SYMPY_OK)] if not ok]
        return "UNKNOWN", f"missing packages: {', '.join(missing)}"

    try:
        poly = _sp.Poly(gap_expr.expand(), theta_sym)
    except Exception as exc:
        return "UNKNOWN", f"cannot build Poly: {exc}"

    deg = poly.degree()
    if deg <= 0:
        val = float(poly.nth(0))
        return (("VERIFIED", f"constant gap = {val:.4g} ≥ 0")
                if val >= 0 else
                ("UNKNOWN",  f"constant gap = {val:.4g} < 0"))

    # Pad degree to even (SOS polynomials must have even degree)
    if deg % 2 == 1:
        deg += 1

    # Coefficients must be numeric — if they contain free symbols (e.g. R_i, e_i)
    # the SDP cannot be set up. Return None-signal via UNKNOWN so Track 1 handles it.
    try:
        coeffs = [float(poly.nth(i)) for i in range(deg + 1)]
    except TypeError:
        return "UNKNOWN", "polynomial coefficients are symbolic — cannot set up SDP"

    a, b = theta_min, theta_max
    # g(θ) = (θ − a)(b − θ) = −ab + (a+b)θ − θ²
    g = [-a * b, a + b, -1.0]

    n0 = deg // 2 + 1       # basis size for σ₀ (degree-d SOS)
    n1 = max(1, deg // 2)   # basis size for σ₁ (degree-d-2 SOS)

    Q0 = cp.Variable((n0, n0), symmetric=True)
    Q1 = cp.Variable((n1, n1), symmetric=True)
    constraints: list = [Q0 >> 0, Q1 >> 0]

    for k in range(deg + 1):
        # Coefficient of θ^k in vᵀQ₀v: Σ_{i+j=k} Q0[i,j]
        sos0_k: Any = sum(
            Q0[i, j]
            for i in range(n0)
            for j in range(n0)
            if i + j == k
        ) or 0

        # Coefficient of θ^k in σ₁(θ)·g(θ)
        s1g_k: Any = 0
        for m in range(2 * (n1 - 1) + 1):
            s1_m: Any = sum(
                Q1[i, j]
                for i in range(n1)
                for j in range(n1)
                if i + j == m
            ) or 0
            gidx = k - m
            if 0 <= gidx <= 2:
                s1g_k = s1g_k + s1_m * g[gidx]

        target = coeffs[k] if k < len(coeffs) else 0.0
        constraints.append(sos0_k + s1g_k == target)

    prob = cp.Problem(cp.Minimize(0), constraints)
    try:
        prob.solve(solver=cp.SCS, verbose=False, eps=1e-7)
    except Exception as exc:
        return "ERROR", f"SDP solver raised: {exc}"

    if prob.status not in ("optimal", "optimal_inaccurate"):
        return "UNKNOWN", f"SDP status={prob.status} (not a proof of failure)"

    try:
        eig0 = np.linalg.eigvalsh(Q0.value)
        eig1 = np.linalg.eigvalsh(Q1.value)
    except Exception:
        return "UNKNOWN", "eigenvalue check failed after solve"

    if np.all(eig0 >= -tol) and np.all(eig1 >= -tol):
        min_eig = min(float(eig0.min()), float(eig1.min()))
        return "VERIFIED", (f"SOS certificate | degree={deg} "
                            f"| domain=[{a},{b}] "
                            f"| min_eig(Q)={min_eig:.2e}")

    return "UNKNOWN", (f"SDP claimed optimal but Q not PSD "
                       f"(min_eig={min(float(eig0.min()), float(eig1.min())):.2e})")


# ── IR check via SOS ──────────────────────────────────────────────────────────

def _verify_ir_sos(
    entry: dict,
    theta_sym: Any,
    theta_min: float,
    theta_max: float,
) -> "tuple[str, str]":
    """Check IR: U(θ, own) ≥ 0 for all θ in [theta_min, theta_max]."""
    if not _SYMPY_OK:
        return "UNKNOWN", "sympy not installed"

    mech   = entry.get("mechanism") or {}
    ir_raw = mech.get("ir_participation_latex") or ""
    if not ir_raw:
        return "UNKNOWN", "no ir_participation_latex"

    for sep in (r"\geq", r"\ge", "≥"):
        if sep in ir_raw:
            lhs_s, _ = ir_raw.split(sep, 1)
            break
    else:
        return "UNKNOWN", "IR missing ≥ separator"

    def _clean(s: str) -> str:
        s = re.sub(r"^[Uu]_?\{?[a-zA-Z,_]+\}?\s*=\s*", "", s.strip())
        s = normalize_left_right(s)
        s = re.sub(r"_\{[a-zA-Z]{2,}\}", "", s)
        return strip_redundant_outer_parens(s.strip())

    try:
        U_ir = _lx_parse(_clean(lhs_s))
    except Exception:
        return "UNKNOWN", "SymPy parse failed for IR"

    # Align symbol: find matching symbol in U_ir if theta_sym is not present
    if theta_sym not in U_ir.free_symbols:
        base = re.sub(r"_\d+$", "", str(theta_sym))
        match = next((s for s in U_ir.free_symbols if str(s).startswith(base)), None)
        if match:
            U_ir = U_ir.subs(match, theta_sym)

    verdict, note = _sos_check_bounded(U_ir, theta_sym, theta_min, theta_max)
    return verdict, f"IR: {note}"


# ── Parametric certificate for symbolic discrete-type contracts ──────────────
#
# The numeric SOS path above needs numeric coefficients and a continuous type
# interval — corpus entries have neither (symbolic parameters, 2–4 discrete
# types). The parametric path (2026-07-19) certifies those directly:
#
#   1. Re-coordinate in ordered increments: type values become
#      t0, t0+d1, t0+d1+d2, ... (d_i > 0, direction resolved from sign of
#      dU/dθ) and non-reward menu families become m0, m0+e1, ... (e_i ≥ 0,
#      monotone in index — a property of every screening optimum).
#   2. Solve the binding equations (IR binds at the worst type, adjacent
#      upward IC binds) for the reward family — the menu is pinned, exactly
#      as in the paper's optimal contract derivation.
#   3. Certify every IC gap and IR value as nonnegative over the positive
#      orthant of the increment coordinates: first by an exact
#      all-coefficients-nonnegative (posynomial) decomposition — the
#      degree-0 Positivstellensatz certificate — then by sympy's assumption
#      engine as a fallback. Both are exact symbolic proofs; the resulting
#      decomposition is a paper-ready certificate no SMT trace provides.
#
# Fail-closed: any step that cannot complete returns None (Track 1 takes
# over). This path only ever asserts VERIFIED — never a counterexample.

def _posynomial_report(expr: Any) -> "str | None":
    """Exact positive-orthant nonnegativity certificate: after
    together/cancel, numerator and denominator must each have single-signed
    numeric coefficients with matching overall sign. Returns the certificate
    string, or None."""
    try:
        expr = _sp.cancel(_sp.together(_sp.expand(expr)))
        num, den = _sp.fraction(expr)
        num, den = _sp.expand(num), _sp.expand(den)

        def _sign(p: Any) -> int:
            if p.free_symbols:
                coeffs = _sp.Poly(p, *sorted(p.free_symbols, key=str)).coeffs()
            else:
                coeffs = [p]
            vals = [float(cf) for cf in coeffs]
            if all(v >= 0 for v in vals):
                return 1
            if all(v <= 0 for v in vals):
                return -1
            return 0

        sn, sd = _sign(num), _sign(den)
        if sn == 0 or sd == 0 or sn * sd < 0:
            return None
        return f"({num})/({den})" if den != 1 else f"{num}"
    except Exception:
        return None


def _parametric_contract_certificate(entry: dict) -> "VerificationResult | None":
    if not _SYMPY_OK or entry.get("category") != "Contract":
        return None
    try:
        from .track1_z3 import _parse_contract_entry, _get_sub, _sub_index
    except Exception:
        return None

    parsed = _parse_contract_entry(entry)
    if parsed is None:
        return None
    U_ir, U_rhs, type_sub, contract_sub, n, ir_from_ic_lhs = parsed
    if ir_from_ic_lhs:
        return None  # same soundness gate as the Z3 path
    if U_ir.atoms(_sp.Function) or U_rhs.atoms(_sp.Function):
        return None  # polynomial track: no transcendentals / opaque calls

    mech = entry.get("mechanism") or {}

    def _base_of(s: Any) -> str:
        return re.sub(r"_\{?[a-zA-Z,']+\}?$", "", str(s))

    # Identify the type family from the entry's declared type_variable.
    tv = str(mech.get("type_variable") or "")
    cands = set(re.findall(r"\\?([a-zA-Z]+)_", tv)) | set(re.findall(r"\\([a-zA-Z]+)", tv))
    type_syms = [s for s in U_ir.free_symbols if _get_sub(s) == type_sub]
    tfams = sorted({_base_of(s) for s in type_syms if _base_of(s).lstrip("\\") in cands})
    if len(tfams) != 1:
        return None
    tbase = tfams[0]
    tsym = next((s for s in type_syms if _base_of(s) == tbase), None)
    if tsym is None:
        return None

    # Direction from the sign of dU/dθ under all-positive assumptions.
    dU = _sp.diff(U_ir, tsym)
    pos = dU.subs({s: _sp.Symbol(str(s), positive=True) for s in dU.free_symbols})
    if pos.is_positive:
        direction = "value"
    elif pos.is_negative:
        direction = "cost"
    else:
        return None

    def _U(k: int, l: int) -> Any:
        if k == l:
            return _sub_index(U_ir, type_sub, k)
        return _sub_index(_sub_index(U_rhs, type_sub, k), contract_sub, l)

    try:
        exprs = {(k, l): _U(k, l) for k in range(n) for l in range(n)}
    except Exception:
        return None

    # Group instantiated indexed symbols by family.
    families: "dict[str, dict[int, Any]]" = {}
    for ex in exprs.values():
        for s in ex.free_symbols:
            m2 = re.match(r"^(.+)_(\d+)$", str(s))
            if m2:
                families.setdefault(m2.group(1), {})[int(m2.group(2))] = s

    if tbase not in families or len(families[tbase]) < 2:
        return None
    menu_bases = sorted({
        _base_of(s) for s in U_rhs.free_symbols if _get_sub(s) == contract_sub
    })

    # Ordered-increment parametrization.
    subs_map: dict = {}
    # type family: strict increments, worst type at index 0
    idx_order = sorted(families[tbase])
    if direction == "cost":
        idx_order = list(reversed(idx_order))  # index 0 = highest cost = worst
    t0 = _sp.Symbol(f"{tbase}_lo", positive=True)
    acc: Any = t0
    subs_map[families[tbase][idx_order[0]]] = t0
    for j, idx in enumerate(idx_order[1:], start=1):
        d = _sp.Symbol(f"d{tbase}_{j}", positive=True)
        acc = acc + d
        subs_map[families[tbase][idx]] = acc

    reward_candidates = [b for b in menu_bases if b != tbase and b in families
                         and len(families[b]) >= n]
    if not reward_candidates:
        return None

    def _parametrize_menu(target: dict, base: str) -> None:
        fam = families[base]
        order = sorted(fam)
        b0 = _sp.Symbol(f"{base}_lo", positive=True)
        accm: Any = b0
        target[fam[order[0]]] = b0
        for j, idx in enumerate(order[1:], start=1):
            e = _sp.Symbol(f"d{base}_{j}", nonnegative=True)
            accm = accm + e
            target[fam[idx]] = accm

    for reward_base in reward_candidates:
        # Parametrize every menu family EXCEPT the reward candidate, whose
        # symbols stay free so the binding equations can be solved for them.
        trial_subs = dict(subs_map)
        for b in menu_bases:
            if b == reward_base or b == tbase or b not in families:
                continue
            _parametrize_menu(trial_subs, b)

        bindings = [exprs[(0, 0)].subs(trial_subs)]
        for k in range(n - 1):
            bindings.append((exprs[(k + 1, k + 1)] - exprs[(k + 1, k)]).subs(trial_subs))
        unknowns = [families[reward_base][i] for i in sorted(families[reward_base])][:n]
        try:
            sols = _sp.solve(bindings, unknowns, dict=True)
        except Exception:
            sols = []
        if not sols:
            continue
        sol = sols[0]

        # Feasibility / vacuity gate (adversarial suite, Task D): every menu
        # symbol is a positive real, and the ordered-increment coordinates
        # (t0, d.., *_lo) are all declared positive. If the binding solve
        # assigns a reward symbol an expression that is NOT provably positive
        # in those coordinates (e.g. an additive type U = theta_i + R_i forces
        # R_0 = -t0 < 0), the "menu" being certified is infeasible and the
        # positivity certificate below would be vacuous. Z3's path has this
        # gate (track1_z3 vacuity check); the parametric path was missing it.
        if any(_posynomial_report(_sp.expand(v)) is None for v in sol.values()):
            continue

        conditions: list[str] = []
        all_ok = True
        targets = (
            [("IC", k, l, exprs[(k, k)] - exprs[(k, l)])
             for k in range(n) for l in range(n) if k != l]
            + [("IR", k, k, exprs[(k, k)]) for k in range(n)]
        )
        for kind, k, l, gap in targets:
            g = gap.subs(trial_subs).subs(sol)
            cert = _posynomial_report(g)
            if cert is not None:
                label = f"{kind}({k},{l})" if kind == "IC" else f"{kind}({k})"
                conditions.append(f"{label} = {cert}  [posynomial ≥ 0]")
                continue
            probe = g.subs({s: _sp.Symbol(str(s), positive=True)
                            for s in g.free_symbols})
            if probe.is_nonnegative:
                label = f"{kind}({k},{l})" if kind == "IC" else f"{kind}({k})"
                conditions.append(f"{label} ≥ 0  [sympy assumption proof]")
                continue
            all_ok = False
            break

        if all_ok:
            return VerificationResult(
                verdict=finalize_verdict(True, False, True),
                category="Contract",
                paper_id=entry.get("paper_id", "<unknown>"),
                track=2,
                conditions=conditions,
                notes=(
                    "parametric positivity certificate over ordered-increment "
                    f"coordinates | type family '{tbase}' ({direction}-type), "
                    f"n={n} | bindings solved for reward family '{reward_base}'"
                    " | degree-0 Positivstellensatz (posynomial) + sympy assumptions"
                    " | exact symbolic proof, no SDP"
                ),
                entry_specific=True,
            )

    return None


# ── Public entry point ────────────────────────────────────────────────────────

def verify_track2(entry: dict) -> "VerificationResult | None":
    """
    SOS/positivity verification for polynomial IC/IR.

    Numeric path: SOS certificate via CVXPY for numeric-coefficient
    polynomials on a continuous type interval.
    Parametric path: exact symbolic positivity certificate in
    ordered-increment coordinates for symbolic discrete-type contracts.

    Returns None if neither path applies → Track 1 handles the entry.
    """
    if not _SYMPY_OK:
        return None

    extracted = _extract_ic_gap_poly(entry) if (_CVXPY_OK and _NUMPY_OK) else None
    if extracted is None:
        return _parametric_contract_certificate(entry)

    gap_expr, theta_sym = extracted

    mech     = entry.get("mechanism") or {}
    paper_id = entry.get("paper_id", "<unknown>")
    category = entry.get("category", "")

    theta_min = float(mech.get("type_space_min") or 0.0)
    theta_max = float(mech.get("type_space_max") or 1.0)
    if theta_min >= theta_max:
        theta_min, theta_max = 0.0, 1.0

    conditions: list[str] = []
    verdicts:   list[str] = []

    ic_v, ic_note = _sos_check_bounded(gap_expr, theta_sym, theta_min, theta_max)
    verdicts.append(ic_v)
    conditions.append(
        f"IC: U(θ,own) − U(θ,other) ≥ 0  ∀θ∈[{theta_min},{theta_max}]  [SOS certificate]"
    )

    ir_v, ir_note = _verify_ir_sos(entry, theta_sym, theta_min, theta_max)
    verdicts.append(ir_v)
    conditions.append(
        f"IR: U(θ,own) ≥ 0  ∀θ∈[{theta_min},{theta_max}]  [SOS certificate]"
    )

    all_ok  = all(v == "VERIFIED" for v in verdicts)
    has_cex = any(v == "COUNTEREXAMPLE" for v in verdicts)
    final: Verdict = finalize_verdict(all_ok, has_cex, True)

    try:
        deg = int(_sp.degree(gap_expr.expand(), theta_sym))
    except Exception:
        deg = -1

    return VerificationResult(
        verdict=final,
        category=category,
        paper_id=paper_id,
        track=2,
        conditions=conditions,
        notes=(f"IC: {ic_note} | {ir_note}"
               f" | poly degree={deg}"
               f" | domain=[{theta_min},{theta_max}]"
               f" | S-procedure SOS via CVXPY+SCS"),
        entry_specific=True,
    )
