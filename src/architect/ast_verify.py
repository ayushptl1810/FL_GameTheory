"""AST-native verification entry point (Approach C, Phase 1).

`verify_from_ast(m, meta)` dispatches on `m.category` straight into the
Track-1 "seam" cores extracted in Tasks 3-7, bypassing the LaTeX round-trip.
`_classify_ast(m)` reports which track *would* own the mechanism (1..4); in
Phase 1 the AST path always routes through the Track-1 core for the category
(Track 2/3/4 delegation is Phase 3).
"""
from __future__ import annotations

from architect.ast import Func, IndexedFamily, Mechanism, Pow, Sum
from architect.serialize import (
    OutsideParseableFragment,
    _strip_leading_neg,
    ast_to_sympy,
    render,
)
from tracks import VerificationResult
from tracks.track2_sos import track2_check_from_sympy
from tracks.track3_dreal import _DELTA, _bounds_for, track3_check_from_sympy
from tracks.track4_sympy import track4_check_from_sympy
from tracks.track1_z3 import (
    _contract_check_core,
    _extract_follower_symbol,
    _get_sub,
    _shapley_check_core,
    _stackelberg_check_core,
    _vcg_check_core,
)
from tracks.vcg_dsic import parse_allocation, verify_vcg_dsic


def _contains(node, kinds) -> bool:
    if isinstance(node, kinds):
        return True
    for attr in ("terms", "factors"):
        for c in getattr(node, attr, None) or []:
            if _contains(c, kinds):
                return True
    for attr in ("base", "arg"):
        c = getattr(node, attr, None)
        if c is not None and _contains(c, kinds):
            return True
    return False


def _is_continuous(m: Mechanism) -> bool:
    return bool(m.meta.get("continuous_type")) or (
        len(m.type_space) == 2
        and all(isinstance(x, (int, float)) for x in m.type_space)
    )


def _classify_ast(m: Mechanism) -> int:
    if m.meta.get("ic_type") in {"bayesian", "bic"} or _contains(m.ic, IndexedFamily):
        return 4
    if any(_contains(s, Func) for s in (m.utility, m.ic, m.ir, m.payment)):
        return 3
    if any(_contains(s, Pow) for s in (m.utility, m.ic, m.ir)) and _is_continuous(m):
        return 2
    if m.category == "Shapley":
        return 5
    return 1


def _template_fallback(category: str, pid: str, track: int) -> VerificationResult:
    """Mirror what verify_stackelberg / verify_contract return when their
    entry-specific LaTeX path yields None: a non-entry-specific template pass.
    Phase 3 replaces this with real Track 2/3/4 delegation."""
    return VerificationResult(
        verdict="VERIFIED_TEMPLATE",
        category=category,
        paper_id=pid,
        track=track,
        entry_specific=False,
        notes="AST path: category core returned no entry-specific result",
    )


def _contract_from_ast(m: Mechanism, meta: dict, pid: str, track: int) -> VerificationResult:
    """Reconstruct the 6-tuple `_parse_contract_entry` returns, from the AST.

    IR node is authored as "U_ir - RHS >= 0" -> U_ir = ast_to_sympy(m.ir).
    IC node is authored two-sided as Sum([U_own, Prod([Const(-1), U_rhs])]);
    U_rhs is the deviating-type utility. type_sub / contract_sub are the single
    subscripts carried by the IR and the (RHS minus type) symbol sets, exactly
    as `_parse_contract_entry` derives them. ir_from_ic_lhs is always False on
    this path (the AST always carries an explicit IR expression).
    """
    ic = m.ic
    rhs_node = None
    # Assumption (matches serialize._contract_ic_latex authoring contract):
    # a two-sided IC is Sum([U_i(own), Prod([Const(-1), U_i(other)])]), so
    # ic.terms[0] is the own-type utility and neg-stripped ic.terms[1] is the
    # deviating-type utility U_i(other).
    if isinstance(ic, Sum) and len(ic.terms) == 2:
        rhs_node = _strip_leading_neg(ic.terms[1])
    if rhs_node is None:
        # One-sided IC (>= 0): no deviating-type utility, so no contract
        # subscript to extract -- same situation _parse_contract_entry bails on.
        return VerificationResult(
            verdict="UNKNOWN", category="Contract", paper_id=pid, track=track,
            entry_specific=False,
            notes="AST path: IC is one-sided (>= 0); cannot recover the "
                  "deviating-type utility / contract subscript from the AST. "
                  "Author IC as Sum([U_own, Prod([Const(-1), U_other])]).",
        )

    U_ir = ast_to_sympy(m.ir, opaque_families=True)
    U_rhs = ast_to_sympy(rhs_node, opaque_families=True)
    lhs_subs = {s for s in (_get_sub(x) for x in U_ir.free_symbols) if s}
    rhs_subs = {s for s in (_get_sub(x) for x in U_rhs.free_symbols) if s}
    if len(lhs_subs) != 1:
        return VerificationResult(
            verdict="UNKNOWN", category="Contract", paper_id=pid, track=track,
            entry_specific=False,
            notes=f"AST path: IR expression carries {len(lhs_subs)} type "
                  f"subscripts (need exactly 1) -- cannot identify the type var.",
        )
    type_sub = next(iter(lhs_subs))
    contract_sub = list(rhs_subs - {type_sub})
    if len(contract_sub) != 1:
        return VerificationResult(
            verdict="UNKNOWN", category="Contract", paper_id=pid, track=track,
            entry_specific=False,
            notes=f"AST path: IC RHS carries {len(contract_sub)} non-type "
                  f"subscripts (need exactly 1) -- cannot identify the contract var.",
        )
    raw_n = meta.get("num_types") or (len(m.type_space) or 2)
    try:
        n = max(min(int(raw_n), 4), 2)
    except (TypeError, ValueError):
        n = 2

    res = _contract_check_core(
        U_ir, U_rhs, type_sub, contract_sub[0], n, False,
        paper_id=pid, meta=meta,
    )
    if res is None:
        return _template_fallback("Contract", pid, track)
    return res


def _vcg_from_ast(m: Mechanism, meta: dict, pid: str) -> VerificationResult:
    """Real entry-specific VCG check for the AST path.

    The Mechanism AST has no allocation node and cannot express a Clarke
    pivot, so the allocation rule (and, when the payment is not AST-expressible,
    the payment rule) ride on ``meta`` as LaTeX -- exactly what the generator
    supplies. Build a minimal ``entry`` and route through the finite-grid
    ``verify_vcg_dsic``:

      * VERIFIED / COUNTEREXAMPLE  -> return it (real, entry_specific honest).
      * missing / unparseable allocation -> UNKNOWN (never fabricate a verdict
        off the fixed payment template -- that would be dishonest here).
      * parseable allocation but the grid proof was inconclusive for another
        reason (grid too big, combo not encodable) -> fall back to the
        payment-shape template, demoted to VERIFIED_SHAPE (a structural match,
        never a proof about this entry's own math).
    """
    try:
        mech_dict, _ = render(m, check_roundtrip=False)
    except OutsideParseableFragment as exc:
        return VerificationResult(
            verdict="UNKNOWN", category="VCG", paper_id=pid, track=1,
            entry_specific=False,
            notes=f"AST path: VCG mechanism does not serialize ({exc}).",
        )

    # Typed allocation node (Task 9): render(m) put allocation_rule_latex + its
    # Clarke-pivot payment_rule_latex into mech_dict. meta is only a fallback for
    # m.allocation is None; if meta also lacks the allocation -> UNKNOWN below.
    # The PAPER's payment always wins: render() substitutes a canonical Clarke
    # pivot for a typed allocation node, and proving that template would prove a
    # textbook mechanism rather than this entry's own math.
    if m.allocation is not None:
        alloc_tex = mech_dict.get("allocation_rule_latex")
    else:
        alloc_tex = meta.get("allocation_rule_latex")
    pay_tex = meta.get("payment_rule_latex") or mech_dict.get("payment_rule_latex", "")
    util_tex = meta.get("client_utility_latex") or mech_dict.get("client_utility_latex", "")
    n = meta.get("num_clients") or (len(m.type_space) or 2)

    entry = {
        "paper_id": pid,
        "category": "VCG",
        "num_clients": n,
        "mechanism": {
            "client_utility_latex": util_tex,
            "payment_rule_latex": pay_tex,
            "allocation_rule_latex": alloc_tex,
        },
    }
    r = verify_vcg_dsic(entry)
    if r.verdict in ("VERIFIED", "COUNTEREXAMPLE"):
        return r

    if not alloc_tex or parse_allocation(alloc_tex) is None:
        return VerificationResult(
            verdict="UNKNOWN", category="VCG", paper_id=pid, track=1,
            entry_specific=False,
            notes=(
                "AST path: VCG allocation rule missing or unparseable "
                f"({r.notes}); no entry-specific DSIC proof. Supply "
                "meta['allocation_rule_latex'] in a form parse_allocation reads."
            ),
        )

    res = _vcg_check_core(
        pay_tex, util_tex, entry_specific=False, paper_id=pid,
        meta={"auction_type": meta.get("auction_type", "reverse")},
    )
    if res.verdict in ("VERIFIED", "VERIFIED_TEMPLATE"):
        res.verdict = "VERIFIED_SHAPE"
        res.entry_specific = False
    return res


def _theta_like(expr):
    """First θ-like free symbol of a SymPy expr, else None."""
    import re as _re
    for s in sorted(expr.free_symbols, key=str):
        if _re.match(r"(theta|θ)", str(s).lower()):
            return s
    return None


def _type_bounds(m: Mechanism, meta: dict) -> "tuple[float, float]":
    """(min, max) type-space bounds: numeric type_space pair, else meta, else 0..1."""
    ts = m.type_space
    if len(ts) == 2 and all(isinstance(x, (int, float)) for x in ts):
        lo, hi = float(ts[0]), float(ts[1])
    else:
        lo = float(meta.get("type_space_min") or 0.0)
        hi = float(meta.get("type_space_max") or 1.0)
    if lo >= hi:
        lo, hi = 0.0, 1.0
    return lo, hi


def _route_continuous_seam(
    m: Mechanism, meta: dict, pid: str, track: int
) -> "VerificationResult | None":
    """Dispatch a track-2/3/4-classified Mechanism straight to its SymPy-native
    seam (Tasks 5-7). Returns the seam's result unless it is inconclusive
    (``None`` build failure or an ``UNKNOWN`` verdict), in which case this
    returns ``None`` and ``verify_from_ast`` falls through to the Track-1 core
    — mirroring ``verifier.verify``'s fall-through order. Never guesses a
    VERIFIED: any parse ambiguity ends in the fall-through.
    """
    try:
        ic_gap = ast_to_sympy(m.ic, opaque_families=True)
        ir_expr = ast_to_sympy(m.ir, opaque_families=True)
    except OutsideParseableFragment:
        return None

    tmin, tmax = _type_bounds(m, meta)
    theta_sym = _theta_like(ic_gap) or _theta_like(ir_expr)
    if theta_sym is None:
        return None

    if track == 2:
        res = track2_check_from_sympy(
            ic_gap, theta_sym, tmin, tmax,
            ir_expr=ir_expr, entry_specific=True, paper_id=pid,
            category=m.category,
        )
    elif track == 3:
        tlo = tmin if tmin > 0 else 0.001   # guard log(0)
        thi = tmax if tmax > tlo else 1.0
        res = track3_check_from_sympy(
            ic_gap, ir_expr,
            _bounds_for(ic_gap, tlo, thi), _bounds_for(ir_expr, tlo, thi),
            _DELTA, entry_specific=True, paper_id=pid, category=m.category,
            theta_min=tlo, theta_max=thi,
        )
    elif track == 4:
        distribution = (meta.get("type_distribution") or "uniform").lower()
        res = track4_check_from_sympy(
            ir_expr, ic_gap, theta_sym, tmin, tmax, distribution,
            entry_specific=True, paper_id=pid, category=m.category,
        )
    else:
        return None

    return None if res is None or res.verdict == "UNKNOWN" else res


def verify_from_ast(m: Mechanism, meta: dict | None = None) -> VerificationResult:
    meta = {**m.meta, **(meta or {})}
    pid = meta.get("paper_id", "architect-proposal")
    track = _classify_ast(m)

    if track in (2, 3, 4):
        routed = _route_continuous_seam(m, meta, pid, track)
        if routed is not None:
            return routed

    if m.category == "VCG":
        return _vcg_from_ast(m, meta, pid)

    if m.category == "Contract":
        return _contract_from_ast(m, meta, pid, track)

    if m.category == "Stackelberg":
        # Mirror verify_stackelberg (track1_z3): no proved equilibrium -> no
        # verification, before reaching _stackelberg_check_core.
        if not meta.get("equilibrium_existence"):
            return VerificationResult(
                verdict="UNSUPPORTED", category="Stackelberg", paper_id=pid, track=1,
                notes="equilibrium_existence=False — cannot verify without a "
                      "proved equilibrium.",
            )
        util_expr = ast_to_sympy(m.utility, opaque_families=True)
        e_sym = _extract_follower_symbol({"mechanism": meta}, util_expr.free_symbols)
        res = _stackelberg_check_core(
            util_expr,
            follower_decision=e_sym,
            best_response_expr=None,
            meta=meta,
            entry_specific=True,
            paper_id=pid,
        )
        if res is None:
            return _template_fallback("Stackelberg", pid, track)
        return res

    if m.category == "Shapley":
        from tracks.track_coalition import verify_coalition
        return verify_coalition({"mechanism": meta, "paper_id": pid})

    return VerificationResult(
        verdict="UNSUPPORTED", category=m.category, paper_id=pid, track=track,
        notes=f"no AST verifier for category {m.category!r}",
    )
