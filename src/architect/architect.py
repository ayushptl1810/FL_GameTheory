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
import re
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
        over = obj["over"]
        over = [over] if isinstance(over, str) else list(over)
        return IndexedFamily(str(obj["name"]), str(obj["index"]), over)
    raise ASTDecodeError(f"unknown node type {t!r}")


_REQUIRED_MECH_KEYS = ("category", "utility", "payment", "ic", "ir")


def _sym_names(node) -> set:
    if isinstance(node, (Sym, Unknown)):
        return {node.name}
    if isinstance(node, Sum):
        return set().union(*(_sym_names(t) for t in node.terms)) if node.terms else set()
    if isinstance(node, Prod):
        return set().union(*(_sym_names(f) for f in node.factors)) if node.factors else set()
    if isinstance(node, Pow):
        return _sym_names(node.base)
    if isinstance(node, Func):
        return _sym_names(node.arg)
    return set()


def _guess_type_variable(ic) -> str | None:
    """For a two-term screening IC Sum([own, -other]), the type symbol is the one
    that appears in BOTH terms (each menu item is evaluated at the SAME type)."""
    if not (isinstance(ic, Sum) and len(ic.terms) == 2):
        return None
    a, b = _sym_names(ic.terms[0]), _sym_names(ic.terms[1])
    common = sorted(a & b)
    return common[0] if len(common) == 1 else None


def mechanism_from_json(obj) -> Mechanism:
    if not isinstance(obj, dict):
        raise ASTDecodeError(f"Mechanism must be a JSON object, got {type(obj).__name__}")
    missing = [k for k in _REQUIRED_MECH_KEYS if k not in obj]
    if missing:
        raise ASTDecodeError(
            f"Mechanism JSON is missing required key(s): {missing}. "
            f"Expected top-level keys: category, utility, payment, ic, ir "
            f"(and optional params, type_space, meta). Got keys: {sorted(obj)}"
        )
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
    # Models routinely omit the verifier metadata even when the prompt asks for
    # it. Fill sane defaults so the entry-specific verifier path can still
    # engage; the verifier still does the real FOC/IR/IC math.
    if m.category == "Stackelberg":
        m.meta.setdefault("equilibrium_existence", True)
        m.meta.setdefault("num_types", len(m.type_space) or 2)
        # The Stage 1 Stackelberg parser reads follower_decision as inline LaTeX
        # (\( ... \)). Pull the symbol token out of whatever the model gave
        # ("effort e_i", "e_i", "\( e_i \)") and re-wrap it.
        fd = str(m.meta.get("follower_decision", "")) or "e_i"
        tok = re.search(r"[A-Za-z]+_[A-Za-z0-9]+|[A-Za-z]", fd)
        m.meta["follower_decision"] = f"\\( {tok.group(0) if tok else 'e_i'} \\)"
    elif m.category == "Contract":
        m.meta.setdefault("num_types", len(m.type_space) or 2)
        # The Stage 1 Contract parser keys type-ordering off type_variable (the
        # subscripted type symbol, e.g. "theta_i"). If the model didn't give it,
        # derive it: the symbol that appears on BOTH sides of the two-term IC
        # Sum is the type; the one only on the RHS is the other contract.
        if "type_variable" not in m.meta:
            tv = _guess_type_variable(m.ic)
            if tv:
                m.meta["type_variable"] = tv

    for sub in (m.utility, m.payment, m.ic, m.ir):
        validate_ast(sub)
    return m


_EXAMPLE_MECHANISM = (
    '{"category":"Stackelberg",'
    '"utility":{"t":"Sum","terms":['
    '{"t":"Prod","factors":[{"t":"Sym","name":"p_i"},{"t":"Sym","name":"e_i"}]},'
    '{"t":"Prod","factors":[{"t":"Const","value":-0.5},{"t":"Sym","name":"c"},'
    '{"t":"Pow","base":{"t":"Sym","name":"e_i"},"exp":2}]}]},'
    '"payment":{"t":"Sym","name":"p_i"},'
    '"ic":{"t":"Sum","terms":[{"t":"Sym","name":"p_i"},'
    '{"t":"Prod","factors":[{"t":"Const","value":-1},{"t":"Sym","name":"c"},'
    '{"t":"Sym","name":"e_i"}]}]},'
    '"ir":{"t":"Sum","terms":['
    '{"t":"Prod","factors":[{"t":"Sym","name":"p_i"},{"t":"Sym","name":"e_i"}]},'
    '{"t":"Prod","factors":[{"t":"Const","value":-0.5},{"t":"Sym","name":"c"},'
    '{"t":"Pow","base":{"t":"Sym","name":"e_i"},"exp":2}]}]},'
    '"params":{},"type_space":["lo","hi"],'
    '"meta":{"equilibrium_existence":true,"follower_decision":"effort e_i","num_types":2}}'
)

_AST_RULES = (
    "Output MUST be exactly one JSON object and nothing else: no ```json fence, "
    "no explanation before or after, no trailing text. "
    "It MUST have all of these top-level keys: category, utility, payment, ic, "
    "ir, params, type_space, meta. NEVER omit ir -- if the participation "
    "constraint equals the utility, repeat the utility node there. Here is a "
    "complete valid example, copy its shape exactly:\n" + _EXAMPLE_MECHANISM + "\n"
    'Every algebra node is {"t":TypeName,...}. Allowed: Const{value}, '
    "Sym{name}, Unknown{name}, Sum{terms}, Prod{factors}, Pow{base,exp:int}, "
    "Func{name:ln|exp,arg}. Use plain Sym like e_i / p_i / theta_i for every "
    "quantity; do NOT use IndexedFamily unless the paper gives an explicit "
    "finite menu, and if you do, its `over` must be a JSON array of strings. "
    "Keep every expression a SIMPLE closed form -- the verifier only checks "
    "polynomial and ln/exp algebra, so a follower/client utility should look "
    "like `p_i*e_i - 0.5*c*e_i^2` or `R_i - theta_i*e_i`, one line, no nested "
    "cases or sums over sets. "
    "Write ic and ir as the single expression "
    "that must be >= 0 (i.e. u_truthful - u_deviation for ic; u for ir). "
    "Use explicit Prod with Const -1 for subtraction. category must be one of "
    "VCG, Contract, Stackelberg. "
    "For a VCG mechanism the payment must be a RECOGNISED truthful form -- a "
    "critical-bid / threshold payment (the lowest losing bid), a Clarke-pivot "
    "externality payment, or a second-price payment. The verifier only certifies "
    "DSIC for these canonical shapes; a novel payment formula only passes as a "
    "template. Give payment as p_i = <that closed form> and client utility as "
    "v_i*x_i - p_i. "
    "For a Contract mechanism, author ic as exactly a two-term "
    'Sum: {"t":"Sum","terms":[<type i utility at its OWN contract i>, '
    '{"t":"Prod","factors":[{"t":"Const","value":-1},<type i utility at '
    "contract j>]}]} -- keep the two menu items distinguished by subscript i "
    "vs j. Also set meta.num_types to the number of discrete types and "
    'meta.type_variable to the subscripted type symbol you used (e.g. "theta_i"). '
    "For Contract, author utility, ic AND ir as fully CONCRETE closed forms "
    "(no Unknown nodes anywhere) -- a linear screening menu like "
    "utility = R_i - theta_i*e_i, ir = R_i - theta_i*e_i >= 0. "
    "Every Sym or Unknown base (the part before any underscore) must be a "
    "single Latin letter or a standard Greek letter name (theta, alpha, beta, "
    "gamma, delta, epsilon, lambda, mu, sigma, phi, psi, omega, tau, rho, pi, "
    "kappa, ...), and any subscript must be one short single token such as e_i "
    "or theta_h -- never a word like e_high or cost. "
    'For a Stackelberg mechanism you MUST also include "meta": '
    '{"equilibrium_existence": true, "follower_decision": "e_i", '
    '"num_types": <int>}, use NO Unknown nodes (the follower utility is a '
    "closed form in the price symbol p_i and the cost symbol c), and set "
    'follower_decision to just the bare symbol like "e_i".'
)
RETRIEVAL_PROMPT = ("You adapt the closest known FL incentive mechanism to a new "
                    "setup, changing only what the new parameters require. " + _AST_RULES)
SYNTHESIS_PROMPT = ("You propose a STRUCTURAL TEMPLATE for an FL incentive "
                    "mechanism. Mark each free payment coefficient as "
                    '{"t":"Unknown","name":...}; use 3 to 5 Unknown nodes total, '
                    "only inside the payment subtree. A solver will fill them. "
                    "For VCG, propose an allocation rule -- highest-bidder "
                    "(recommended) or weighted-welfare-max with non-negative "
                    "per-agent weights; payment fixed to the affine-maximizer "
                    "Clarke pivot. A top-k rule (author the LaTeX) is also "
                    "certifiable. Do NOT author the payment. " + _AST_RULES)
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
    system = _PROMPTS[mode]
    if spec.expected_family:
        system = (f"You MUST propose a mechanism in the {spec.expected_family} "
                  f"family. Do not switch families. "
                  f"Any Synthesis or Hybrid routing must stay within the "
                  f"{spec.expected_family} family. " + system)
    raw = complete(system, user, json_mode=True)
    return mechanism_from_json(json.loads(_extract_json(raw)))


def _extract_json(text: str) -> str:
    """Pull the JSON object out of a reply that may be wrapped in a ```json
    fence or have leading/trailing prose."""
    t = text.strip()
    if "```" in t:
        seg = t.split("```", 2)
        t = seg[1] if len(seg) >= 2 else t
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
    a, b = t.find("{"), t.rfind("}")
    return t[a:b + 1] if 0 <= a < b else t
