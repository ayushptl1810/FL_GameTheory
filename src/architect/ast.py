from __future__ import annotations
from dataclasses import dataclass, field


class ASTSchemaError(ValueError):
    pass


@dataclass
class Const:
    value: float


@dataclass
class Sym:
    name: str


@dataclass
class Unknown:
    name: str


@dataclass
class Sum:
    terms: list


@dataclass
class Prod:
    factors: list


@dataclass
class Pow:
    base: object
    exp: int


@dataclass
class Func:
    name: str
    arg: object


@dataclass
class IndexedFamily:
    name: str
    index: str
    over: list


_ALLOWED_FUNCS = {"ln", "exp"}

Node = "Const | Sym | Unknown | Sum | Prod | Pow | Func | IndexedFamily"


# --- VCG allocation-rule nodes (Alloc union) -------------------------------- #
# A typed allocation rule for a VCG mechanism, replacing the meta-carried
# allocation_rule_latex string. serialize.render(m) turns it into LaTeX; the
# payment_rule_latex emitted alongside is the Clarke pivot for THIS allocation.
@dataclass(frozen=True)
class AllocHighest:
    """Single item to the highest bidder: x_i = 1 iff b_i = max_j b_j."""


@dataclass(frozen=True)
class AllocTopK:
    """The k highest bidders win."""

    k: int


@dataclass(frozen=True)
class AllocWeightedWelfare:
    """Affine maximizer: x* maximizes sum_i w_i b_i x_i."""

    weights: list


Alloc = "AllocHighest | AllocTopK | AllocWeightedWelfare"


@dataclass
class Mechanism:
    category: str
    utility: object
    payment: object
    ic: object
    ir: object
    params: dict = field(default_factory=dict)
    type_space: list = field(default_factory=list)
    provenance: dict | None = None
    # Typed VCG allocation rule (Alloc union). When set, serialize/verify build
    # the allocation + Clarke-pivot payment from it instead of meta LaTeX.
    allocation: object | None = None
    # Open bag of verifier metadata keys (e.g. equilibrium_existence,
    # follower_decision, num_types) that are NOT LaTeX and are folded into the
    # rendered mechanism dict verbatim, bypassing the round-trip check.
    meta: dict = field(default_factory=dict)


def validate_ast(node) -> None:
    if isinstance(node, (Const, Sym, Unknown)):
        return
    if isinstance(node, Sum):
        if not node.terms:
            raise ASTSchemaError("empty Sum")
        for t in node.terms:
            validate_ast(t)
        return
    if isinstance(node, Prod):
        if not node.factors:
            raise ASTSchemaError("empty Prod")
        for f in node.factors:
            validate_ast(f)
        return
    if isinstance(node, Pow):
        if not isinstance(node.exp, int) or isinstance(node.exp, bool):
            raise ASTSchemaError(f"Pow.exp must be int, got {node.exp!r}")
        validate_ast(node.base)
        return
    if isinstance(node, Func):
        if node.name not in _ALLOWED_FUNCS:
            raise ASTSchemaError(f"Func.name {node.name!r} not in {_ALLOWED_FUNCS}")
        validate_ast(node.arg)
        return
    if isinstance(node, IndexedFamily):
        if not node.over:
            raise ASTSchemaError("IndexedFamily.over is empty")
        return
    raise ASTSchemaError(f"unknown node type {type(node).__name__}")


def validate_alloc(node) -> None:
    """Type-check an Alloc-union node (VCG allocation rule)."""
    if isinstance(node, AllocHighest):
        return
    if isinstance(node, AllocTopK):
        if not isinstance(node.k, int) or isinstance(node.k, bool):
            raise ASTSchemaError(f"AllocTopK.k must be int, got {node.k!r}")
        if node.k < 1:
            raise ASTSchemaError(f"AllocTopK.k must be >= 1, got {node.k}")
        return
    if isinstance(node, AllocWeightedWelfare):
        if not isinstance(node.weights, list) or not node.weights:
            raise ASTSchemaError("AllocWeightedWelfare.weights must be a non-empty list")
        if not all(isinstance(w, str) for w in node.weights):
            raise ASTSchemaError("AllocWeightedWelfare.weights must be a list of strings")
        return
    raise ASTSchemaError(f"unknown Alloc node type {type(node).__name__}")


_NODE_TAGS = {
    "Const": ("value",),
    "Sym": ("name",),
    "Unknown": ("name",),
    "Sum": ("terms",),
    "Prod": ("factors",),
    "Pow": ("base", "exp"),
    "Func": ("name", "arg"),
    "IndexedFamily": ("name", "index", "over"),
    "AllocHighest": (),
    "AllocTopK": ("k",),
    "AllocWeightedWelfare": ("weights",),
}
_TAG_TO_CLS = {
    "Const": Const, "Sym": Sym, "Unknown": Unknown, "Sum": Sum, "Prod": Prod,
    "Pow": Pow, "Func": Func, "IndexedFamily": IndexedFamily,
    "AllocHighest": AllocHighest, "AllocTopK": AllocTopK,
    "AllocWeightedWelfare": AllocWeightedWelfare,
}


def _enc(v):
    if type(v).__name__ in _NODE_TAGS:
        return to_dict(v)
    if isinstance(v, list):
        return [_enc(x) for x in v]
    return v


def to_dict(node):
    tag = type(node).__name__
    if tag == "Mechanism":
        return {
            "t": "Mechanism", "category": node.category,
            "utility": to_dict(node.utility), "payment": to_dict(node.payment),
            "ic": to_dict(node.ic), "ir": to_dict(node.ir),
            "params": dict(node.params), "type_space": list(node.type_space),
            "allocation": to_dict(node.allocation) if node.allocation is not None else None,
            "meta": dict(node.meta),
        }
    if tag not in _NODE_TAGS:
        raise ASTSchemaError(f"cannot serialize {tag}")
    out = {"t": tag}
    for f in _NODE_TAGS[tag]:
        out[f] = _enc(getattr(node, f))
    return out


def _dec(v):
    if isinstance(v, dict) and "t" in v:
        return from_dict(v)
    if isinstance(v, list):
        return [_dec(x) for x in v]
    return v


def from_dict(d):
    if not isinstance(d, dict) or "t" not in d:
        raise ASTSchemaError(f"not a node dict: {d!r}")
    tag = d["t"]
    if tag == "Mechanism":
        m = Mechanism(
            category=d["category"],
            utility=from_dict(d["utility"]), payment=from_dict(d["payment"]),
            ic=from_dict(d["ic"]), ir=from_dict(d["ir"]),
            params=dict(d.get("params", {})), type_space=list(d.get("type_space", [])),
            allocation=(from_dict(d["allocation"]) if d.get("allocation") is not None else None),
            meta=dict(d.get("meta", {})),
        )
        for sub in (m.utility, m.payment, m.ic, m.ir):
            validate_ast(sub)
        if m.allocation is not None:
            validate_alloc(m.allocation)
        return m
    if tag not in _TAG_TO_CLS:
        raise ASTSchemaError(f"unknown node tag {tag!r}")
    kwargs = {f: _dec(d[f]) for f in _NODE_TAGS[tag]}
    return _TAG_TO_CLS[tag](**kwargs)
