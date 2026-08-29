"""AST-native verification entry point (Approach C, Phase 1).

`verify_from_ast(m, meta)` dispatches on `m.category` straight into the
Track-1 "seam" cores extracted in Tasks 3-7, bypassing the LaTeX round-trip.
`_classify_ast(m)` reports which track *would* own the mechanism (1..4); in
Phase 1 the AST path always routes through the Track-1 core for the category
(Track 2/3/4 delegation is Phase 3).
"""
from __future__ import annotations

from architect.ast import Func, IndexedFamily, Mechanism, Pow, Sum
from architect.serialize import _strip_leading_neg, ast_to_sympy
from tracks import VerificationResult
from tracks.track1_z3 import (
    _contract_check_core,
    _extract_follower_symbol,
    _get_sub,
    _shapley_check_core,
    _stackelberg_check_core,
    _vcg_check_core,
)


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

    U_ir = ast_to_sympy(m.ir)
    U_rhs = ast_to_sympy(rhs_node)
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


def verify_from_ast(m: Mechanism, meta: dict | None = None) -> VerificationResult:
    meta = {**m.meta, **(meta or {})}
    pid = meta.get("paper_id", "architect-proposal")
    track = _classify_ast(m)

    if m.category == "VCG":
        # entry_specific=False: _vcg_check_core is a fixed threshold-payment
        # template that never inspects this proposal's payment. VCG
        # entry-specific verification is Phase 2; until then VERIFIED_TEMPLATE
        # is the honest ceiling (never VERIFIED for an unproven mechanism).
        return _vcg_check_core(
            "", "", entry_specific=False, paper_id=pid, meta=meta,
        )

    if m.category == "Contract":
        return _contract_from_ast(m, meta, pid, track)

    if m.category == "Stackelberg":
        util_expr = ast_to_sympy(m.utility)
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
        return _shapley_check_core(paper_id=pid)

    return VerificationResult(
        verdict="UNSUPPORTED", category=m.category, paper_id=pid, track=track,
        notes=f"no AST verifier for category {m.category!r}",
    )
