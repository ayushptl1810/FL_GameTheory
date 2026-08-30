"""Pure AST -> LaTeX serializer with a round-trip parseability check.

This is the load-bearing boundary of the Architect loop: no LaTeX parser sits
in the loop. ``render`` emits LaTeX for a Mechanism AST and then verifies (via
Stage 1's ``parse_only_*`` hooks) that what it emitted re-parses to the same
expression, raising ``OutsideParseableFragment`` otherwise.
"""
from __future__ import annotations

import sympy

from architect.ast import (
    Const, Sym, Unknown, Sum, Prod, Pow, Func, IndexedFamily,
    AllocHighest, AllocTopK, AllocWeightedWelfare,
    Mechanism, validate_ast, validate_alloc,
)
from tracks.track1_z3 import (
    parse_only_vcg, parse_only_contract, parse_only_stackelberg, ParseFailure,
)


class OutsideParseableFragment(Exception):
    def __init__(self, hint: str):
        super().__init__(hint)
        self.hint = hint


_PARSERS = {
    "VCG": parse_only_vcg,
    "Contract": parse_only_contract,
    "Stackelberg": parse_only_stackelberg,
}

# category -> {mechanism-dict field : Mechanism attribute}
#
# Field names are the ones each category's entry-specific verifier actually
# consumes (verified against src/tracks/track1_z3.py):
#   Contract  -> _parse_contract_entry reads mech["ir_participation_latex"]
#                (line ~338) and mech["ic_screening_latex"] (line ~339);
#                verify_contract gates on those same two keys (line ~660).
#                The generic *_condition_latex aliases are emitted too because
#                parse_only_contract also accepts them and downstream tooling
#                expects them.
#   VCG       -> verify_vcg reads mech["payment_rule_latex"] (line ~97) and
#                mech["client_utility_latex"]; parse_only_vcg round-trips
#                payment_rule_latex / client_utility_latex / *_condition_latex.
#   Stackelberg -> _try_stackelberg_latex reads mech["follower_utility_latex"]
#                (line ~1118); parse_only_stackelberg round-trips
#                follower_utility_latex among others.
_FIELD_MAP = {
    "Contract": {
        "client_utility_latex": "utility",
        "ic_screening_latex": "ic",
        "ir_participation_latex": "ir",
        "ic_condition_latex": "ic",
        "ir_condition_latex": "ir",
    },
    "VCG": {
        "client_utility_latex": "utility",
        "payment_rule_latex": "payment",
        "ic_condition_latex": "ic",
        "ir_condition_latex": "ir",
    },
    "Stackelberg": {
        "follower_utility_latex": "utility",
    },
}

_IC_IR_ATTRS = ("ic", "ir")

# Non-LaTeX verifier metadata keys allowed to ride on Mechanism.meta and be
# folded into the rendered dict without a round-trip check. Anything else in
# meta (notably any *_latex key) is silently dropped so model-authored JSON
# cannot overwrite a validated LaTeX field. Keys read by verify_stackelberg /
# _try_stackelberg_latex per task-12-report.md.
# ponytail: stray meta keys are ignored, not an error — the loop must not die on one.
_META_KEYS = frozenset({
    "equilibrium_existence", "follower_decision", "num_types", "type_variable",
})


def ast_to_sympy(node, opaque_families: bool = False):
    # opaque_families: an IndexedFamily collapses to Symbol(name) (the
    # verify_from_ast / seam consumer wants one opaque symbol). Default False
    # keeps the subscripted Symbol(f"{name}_{index}") so the LaTeX render path
    # (to_latex / _check_roundtrip) still emits `R_{i}`, not bare `R`.
    # Symbols are built assumption-free (no positive=True): sympy treats
    # Symbol('x', positive=True) and Symbol('x') as distinct, so keeping
    # assumptions here would break equality against a plain sympify(...) form.
    if isinstance(node, Const):
        # Every Const rides the exact Rational path: both z3 converters
        # (_sympy_to_z3, _sp_to_z3) take Rational fine, and the render path
        # (to_latex / mechanism_latex / corpus dict) must emit \frac{1}{2},
        # not 0.5. str(value) so a float literal like 0.1 rationalises from
        # its decimal text, not its binary expansion.
        return sympy.Rational(str(node.value)).limit_denominator(10 ** 6)
    if isinstance(node, (Sym, Unknown)):
        return sympy.Symbol(node.name)
    if isinstance(node, Sum):
        return sympy.Add(*[ast_to_sympy(t, opaque_families) for t in node.terms])
    if isinstance(node, Prod):
        return sympy.Mul(*[ast_to_sympy(f, opaque_families) for f in node.factors])
    if isinstance(node, Pow):
        return ast_to_sympy(node.base, opaque_families) ** node.exp
    if isinstance(node, Func):
        return {"ln": sympy.log, "exp": sympy.exp}[node.name](
            ast_to_sympy(node.arg, opaque_families))
    if isinstance(node, IndexedFamily):
        # Rendering path (default): keep the subscripted name so to_latex emits
        # `R_{i}`. Verify/seam path (opaque_families=True): collapse to one
        # symbol; per-index expansion over node.over is that caller's job.
        if opaque_families:
            return sympy.Symbol(node.name)
        return sympy.Symbol(f"{node.name}_{node.index}")
    raise OutsideParseableFragment(f"cannot serialize node {type(node).__name__}")


def _norm(expr):
    """Drop assumptions and brace-decorated subscripts so an AST expr and its
    parse_latex round-trip compare structurally."""
    subs = {
        s: sympy.Symbol(s.name.replace("{", "").replace("}", ""))
        for s in expr.free_symbols
    }
    return expr.xreplace(subs)


# Greek base names -> their LaTeX command. `\theta` is the conventional type
# variable across contract-theory / Stackelberg FL, so `Sym("theta_i")` must
# render as `\theta_{i}` or every realistic proposal is rejected at this gate.
_GREEK = frozenset({
    "theta", "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta",
    "lambda", "mu", "nu", "xi", "rho", "sigma", "tau", "phi", "chi", "psi",
    "omega", "pi", "kappa",
})


def _latex_name(sym_name: str) -> str:
    """LaTeX rendering of a single symbol name that sympy's latex parser reads
    straight back. Greek base -> backslash command; multi-letter non-Greek base
    has no round-trippable form (parse_latex splits it into a product)."""
    base, _, sub = sym_name.partition("_")
    if base in _GREEK:
        base = "\\" + base
    elif len(base) > 1:
        raise OutsideParseableFragment(
            f"symbol {sym_name!r} has a multi-letter base; use a single-letter "
            f"symbol base with a subscript (e.g. `e_h` not `e_high`)"
        )
    return f"{base}_{{{sub}}}" if sub else base


def to_latex(node) -> str:
    expr = ast_to_sympy(node)
    names = {s: _latex_name(s.name) for s in expr.free_symbols}
    return sympy.latex(expr, symbol_names=names)


def _ineq_latex(lhs_node) -> str:
    # IC / IR nodes are authored as "LHS - RHS" and asserted >= 0.
    return f"{to_latex(lhs_node)} \\geq 0"


def _strip_leading_neg(node):
    """Prod([Const(-1), *rest]) -> the rest as a node; else None."""
    if (isinstance(node, Prod) and node.factors
            and isinstance(node.factors[0], Const) and node.factors[0].value == -1):
        rest = node.factors[1:]
        return rest[0] if len(rest) == 1 else Prod(rest)
    return None


def _contract_ic_latex(ic_node) -> str:
    r"""Contract screening IC as the two-sided ``U_i(own) \geq U_i(other)`` form
    that Stage 1's ``_parse_contract_entry`` needs to extract the contract
    subscript. Expects ``ic`` authored as
    ``Sum([<own utility>, Prod([Const(-1), <other utility>])])``.
    Falls back to the one-sided ``>= 0`` form (mechanism stays
    VERIFIED_TEMPLATE, no regression) when the shape differs.
    """
    if isinstance(ic_node, Sum) and len(ic_node.terms) == 2:
        rhs = _strip_leading_neg(ic_node.terms[1])
        if rhs is not None:
            return f"{to_latex(ic_node.terms[0])} \\geq {to_latex(rhs)}"
    return _ineq_latex(ic_node)


def _alloc_latex(alloc) -> "tuple[str, str]":
    """Alloc node -> (allocation_rule_latex, payment_rule_latex).

    payment_rule_latex is the Clarke pivot for THAT allocation:
      * AllocHighest / AllocTopK -> standard second- / (k+1)-price pivot
      * AllocWeightedWelfare(w)  -> affine-maximizer pivot
                                    p_i = \\max_{k \\neq i} w_k b_k / w_i
    """
    validate_alloc(alloc)
    if isinstance(alloc, AllocHighest):
        return (
            r"x_i = 1 \text{ if } b_i = \max_j b_j",
            r"p_i = \max_{j \neq i} b_j",
        )
    if isinstance(alloc, AllocTopK):
        k = alloc.k
        return (
            rf"x_i = 1 \text{{ if }} b_i \text{{ is among the top-{k} bids}}",
            rf"p_i = b_{{({k}+1)}} \text{{ (the }}({k}+1)\text{{-th highest bid)}}",
        )
    if isinstance(alloc, AllocWeightedWelfare):
        w = alloc.weights
        num = " + ".join(rf"{wi} b_{i + 1} x_{i + 1}" for i, wi in enumerate(w))
        return (
            rf"x^* \in \arg\max \left[ {num} \right]",
            r"p_i = \frac{\max_{k \neq i} w_k b_k}{w_i}",
        )
    raise OutsideParseableFragment(f"cannot serialize alloc {type(alloc).__name__}")


def render(m: Mechanism, *, check_roundtrip: bool = True):
    if m.category not in _FIELD_MAP:
        raise OutsideParseableFragment(
            f"category {m.category!r} has no entry-specific verifier; "
            f"propose a VCG, Contract, or Stackelberg mechanism"
        )
    for sub in (m.utility, m.payment, m.ic, m.ir):
        validate_ast(sub)

    md = {}
    for field, attr in _FIELD_MAP[m.category].items():
        node = getattr(m, attr)
        if attr == "ic" and m.category == "Contract":
            md[field] = _contract_ic_latex(node)
        elif attr in _IC_IR_ATTRS:
            md[field] = _ineq_latex(node)
        else:
            md[field] = to_latex(node)

    # The re-parse / structural-compare block is the only LaTeX parse in this
    # function. ``check_roundtrip=False`` skips it entirely (used by the
    # AST-native verify path, which must run no LaTeX parser in the loop); the
    # "cannot serialize node" / missing-field raises above still fire — those are
    # "can't even produce LaTeX", not "parse-back disagreed".
    if check_roundtrip:
        parser = _PARSERS[m.category]
        try:
            reparsed = parser(md)
        except ParseFailure as pf:
            raise OutsideParseableFragment(
                f"field {pf.field} did not parse ({pf.reason}); use simpler algebra: "
                f"closed-form sums with numeric bounds, explicit products, ln/exp only"
            ) from pf

        for field, attr in _FIELD_MAP[m.category].items():
            if attr in _IC_IR_ATTRS:
                continue  # v1: inequality fields are not structurally round-tripped
            want = _norm(ast_to_sympy(getattr(m, attr)))
            got = reparsed.get(field)
            if got is None or sympy.simplify(_norm(got) - want) != 0:
                raise OutsideParseableFragment(
                    f"round-trip mismatch on {field}: rendered LaTeX does not "
                    f"re-parse to the proposed expression; simplify the {attr} term"
                )

    # Fold in ONLY the allowlisted non-LaTeX metadata keys, AFTER the round-trip
    # check. This stops model-authored meta from overwriting a validated LaTeX
    # field with unchecked content.
    md.update({k: v for k, v in m.meta.items() if k in _META_KEYS})

    # Typed VCG allocation node: emit allocation_rule_latex + its Clarke-pivot
    # payment_rule_latex, overriding the payment-node render above. These LaTeX
    # forms (a \max_{j!=i} pivot, an \arg\max objective) are not AST-expressible,
    # so they ride here, past the round-trip block, like meta.
    if m.category == "VCG" and m.allocation is not None:
        alloc_tex, pay_tex = _alloc_latex(m.allocation)
        md["allocation_rule_latex"] = alloc_tex
        md["payment_rule_latex"] = pay_tex

    full = "\n".join(f"{k}: {v}" for k, v in md.items())
    return md, full
