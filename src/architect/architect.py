"""Architect: proposes a Mechanism as a JSON AST.

AST JSON: every node is {"t": TypeName, ...fields}
  Const{value}  Sym{name}  Unknown{name}
  Sum{terms:[node]}  Prod{factors:[node]}  Pow{base:node, exp:int}
  Func{name:"ln"|"exp", arg:node}  IndexedFamily{name, index, over:[str]}
Mechanism JSON: {category, utility, payment, ic, ir, params:{}, type_space:[str],
                 provenance:{}|null}
"""
from __future__ import annotations
import json
from architect.llm import llm_complete
from architect.types import ProblemSpec, Feedback
from architect.ast import (Const, Sym, Unknown, Sum, Prod, Pow, Func,
                           IndexedFamily, Mechanism, validate_ast)


class ASTDecodeError(ValueError):
    pass


def ast_from_json(obj):
    if not isinstance(obj, dict) or "t" not in obj:
        raise ASTDecodeError(f"not a node: {obj!r}")
    t = obj["t"]
    if t == "Const": return Const(float(obj["value"]))
    if t == "Sym": return Sym(str(obj["name"]))
    if t == "Unknown": return Unknown(str(obj["name"]))
    if t == "Sum": return Sum([ast_from_json(x) for x in obj["terms"]])
    if t == "Prod": return Prod([ast_from_json(x) for x in obj["factors"]])
    if t == "Pow": return Pow(ast_from_json(obj["base"]), int(obj["exp"]))
    if t == "Func": return Func(str(obj["name"]), ast_from_json(obj["arg"]))
    if t == "IndexedFamily":
        return IndexedFamily(str(obj["name"]), str(obj["index"]), list(obj["over"]))
    raise ASTDecodeError(f"unknown node type {t!r}")


def mechanism_from_json(obj) -> Mechanism:
    m = Mechanism(
        category=obj["category"],
        utility=ast_from_json(obj["utility"]),
        payment=ast_from_json(obj["payment"]),
        ic=ast_from_json(obj["ic"]),
        ir=ast_from_json(obj["ir"]),
        params=dict(obj.get("params") or {}),
        type_space=list(obj.get("type_space") or []),
        provenance=obj.get("provenance"),
        meta=dict(obj.get("meta") or {}))
    for sub in (m.utility, m.payment, m.ic, m.ir):
        validate_ast(sub)
    return m


_AST_RULES = (
    "Return ONLY a JSON object for the Mechanism. Every algebra node is "
    '{"t":TypeName,...}. Allowed: Const{value}, Sym{name}, Unknown{name}, '
    "Sum{terms}, Prod{factors}, Pow{base,exp:int}, Func{name:ln|exp,arg}, "
    "IndexedFamily{name,index,over}. Write ic and ir as the single expression "
    "that must be >= 0 (i.e. u_truthful - u_deviation for ic; u for ir). "
    "Use explicit Prod with Const -1 for subtraction. category must be one of "
    "VCG, Contract, Stackelberg. "
    "For a Contract mechanism, author ic as exactly a two-term "
    'Sum: {"t":"Sum","terms":[<type i utility at its OWN contract i>, '
    '{"t":"Prod","factors":[{"t":"Const","value":-1},<type i utility at '
    "contract j>]}]} -- keep the two menu items distinguished by subscript i "
    "vs j. Also set meta.num_types to the number of discrete types and "
    'meta.type_variable to the subscripted type symbol you used (e.g. "theta_i"). '
    "Every Sym or Unknown base (the part before any underscore) must be a "
    "single Latin letter or a standard Greek letter name (theta, alpha, beta, "
    "gamma, delta, epsilon, lambda, mu, sigma, phi, psi, omega, tau, rho, pi, "
    "kappa, ...), and any subscript must be one short single token such as e_i "
    "or theta_h -- never a word like e_high or cost. "
    'For a Stackelberg mechanism you MUST also include "meta": '
    '{"equilibrium_existence": true, "follower_decision": '
    '"<the follower\'s decision variable, e.g. effort e_i>", "num_types": <int>}.'
)
RETRIEVAL_PROMPT = ("You adapt the closest known FL incentive mechanism to a new "
                    "setup, changing only what the new parameters require. " + _AST_RULES)
SYNTHESIS_PROMPT = ("You propose a STRUCTURAL TEMPLATE for an FL incentive "
                    "mechanism. Mark each free payment coefficient as "
                    '{"t":"Unknown","name":...}; use 3 to 5 Unknown nodes total, '
                    "only inside the payment subtree. A solver will fill them. " + _AST_RULES)
HYBRID_PROMPT = ("You combine elements from multiple known FL incentive "
                 "mechanisms into one. Set provenance to a map of subtree->paper_id. "
                 + _AST_RULES)
_PROMPTS = {"Retrieval": RETRIEVAL_PROMPT, "Synthesis": SYNTHESIS_PROMPT,
            "Hybrid": HYBRID_PROMPT}


def _feedback_block(fb: Feedback | None) -> str:
    if fb is None:
        return ""
    if fb.kind == "restart":
        return f"\n\nPREVIOUS ATTEMPTS FAILED for these families: {fb.hint}. Try a different structure."
    parts = [f"\n\nThe previous proposal failed ({fb.kind})."]
    if fb.counterexample:
        parts.append(f"Counterexample: {fb.counterexample}.")
    if fb.conditions:
        parts.append(f"Checked conditions: {fb.conditions}.")
    if fb.hint:
        parts.append(f"Fix hint: {fb.hint}.")
    return " ".join(parts)


def propose(spec: ProblemSpec, mode, rag_hits, feedback, *, complete=llm_complete) -> Mechanism:
    user = (f"FL setup: {spec.raw_text}\n"
            f"Structured: n_clients={spec.n_clients}, cost={spec.cost_structure}, "
            f"types={spec.type_model}, observability={spec.observability}, "
            f"budget={spec.budget}, failure_modes={spec.failure_modes}\n"
            f"Retrieved: {json.dumps([{'paper_id': h.get('paper_id'), 'mechanism': h.get('mechanism')} for h in rag_hits])[:4000]}"
            + _feedback_block(feedback))
    raw = complete(_PROMPTS[mode], user, json_mode=True)
    return mechanism_from_json(json.loads(raw))
