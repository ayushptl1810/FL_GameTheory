from __future__ import annotations
import json
from architect.ast import from_dict, to_dict, ASTSchemaError
from architect.llm import llm_complete

FORMALIZE_SYSTEM_PROMPT = (
    "You convert a Federated Learning incentive mechanism into a typed AST. "
    "Return ONLY a JSON object: a serialized Mechanism. Every node is an object "
    'with a "t" field naming its type. Allowed types: '
    "Const{value:number}, Sym{name:string}, Unknown{name:string}, "
    "Sum{terms:[node]}, Prod{factors:[node]}, Pow{base:node,exp:int}, "
    'Func{name:"ln"|"exp",arg:node}, '
    "IndexedFamily{name:string,index:string,over:[string]}, "
    "AllocHighest{}, AllocTopK{k:int}, AllocWeightedWelfare{weights:[string]}. "
    'The Mechanism: {"t":"Mechanism","category":<the given category>,'
    '"utility":<client/follower utility>,"payment":<payment or transfer rule>,'
    '"ic":<incentive-compatibility constraint expression>,'
    '"ir":<participation constraint expression>,'
    '"params":{},"type_space":[<discrete type values as numbers>],'
    '"allocation":<AllocHighest/AllocTopK/AllocWeightedWelfare or null>,'
    '"meta":{<copy verifier hints: num_types, type_distribution, '
    "equilibrium_existence, follower_decision, ...>}}. "
    "Do NOT invent terms the source does not state. If a quantity is genuinely "
    'unspecified, use Unknown{"name":...}. Keep algebra simple: closed-form '
    "sums, explicit products, ln/exp only, integer powers."
)


def _user_message(entry, pdf_text, concerns):
    mech = json.dumps(entry.get("mechanism", {}), indent=1)
    parts = [
        f"category: {entry.get('category')}",
        f"mechanism dict:\n{mech}",
    ]
    ka = entry.get("key_assumptions")
    if ka:
        parts.append("key_assumptions: " + "; ".join(ka))
    if pdf_text:
        parts.append("paper text (excerpt):\n" + pdf_text)
    if concerns:
        lines = "\n".join(f"- {c.get('field')}: {c.get('issue')}" for c in concerns)
        parts.append("The previous attempt had these problems, fix them:\n" + lines)
    return "\n\n".join(parts)


def formalize_entry(entry, pdf_text, *, complete=llm_complete, concerns=None):
    user = _user_message(entry, pdf_text, concerns)
    try:
        raw = complete(FORMALIZE_SYSTEM_PROMPT, user, json_mode=True)
        return from_dict(json.loads(raw))
    except (json.JSONDecodeError, ASTSchemaError, KeyError, TypeError):
        return None


ADVERSARY_SYSTEM_PROMPT = (
    "You are an adversarial reviewer. Compare a serialized Mechanism AST against "
    "the paper's stated mechanism. Return ONLY JSON: "
    '{"concerns": [{"field": "utility"|"payment"|"ic"|"ir"|"allocation"|"type_space", '
    '"issue": "<one sentence>"}]}. Return an empty list only if the AST faithfully '
    "represents the paper. Look for: a dropped constraint term, a summation over the "
    "wrong index set, a flipped sign, a quantifier over the wrong variable, a type "
    "value that contradicts the text. Do not nitpick notation or naming."
)


def adversary_check(m, entry, pdf_text, *, complete=llm_complete):
    ast_json = json.dumps(to_dict(m), indent=1)
    mech = json.dumps(entry.get("mechanism", {}), indent=1)
    parts = [f"AST:\n{ast_json}", f"paper mechanism dict:\n{mech}"]
    if pdf_text:
        parts.append("paper text (excerpt):\n" + pdf_text)
    try:
        raw = complete(ADVERSARY_SYSTEM_PROMPT, "\n\n".join(parts), json_mode=True)
        data = json.loads(raw)
        c = data.get("concerns")
        return c if isinstance(c, list) else []
    except Exception:
        return []


from dataclasses import dataclass, field
from architect.ast_verify import verify_from_ast


@dataclass
class FormalizeResult:
    verdict: str
    ast: object | None
    adversary_log: list = field(default_factory=list)
    retries: int = 0
    pdf_used: bool = False
    notes: str = ""


def _verify(m, entry):
    return verify_from_ast(m, meta={"paper_id": entry.get("paper_id", "")})


def formalize_with_retry(entry, pdf_text, *, complete=llm_complete):
    used = pdf_text is not None
    m = formalize_entry(entry, pdf_text, complete=complete)
    if m is None:
        return FormalizeResult("UNKNOWN", None, [], 0, used,
                               "formalization returned no valid AST")
    res = _verify(m, entry)
    concerns, adversary_log = None, []
    if res.verdict == "VERIFIED":
        c = adversary_check(m, entry, pdf_text, complete=complete)
        if not c:
            return FormalizeResult("VERIFIED", m, [[]], 0, used, "")
        concerns, adversary_log = c, [c]
    elif res.verdict == "COUNTEREXAMPLE":
        concerns, adversary_log = None, []
    else:
        return FormalizeResult(res.verdict, m, [], 0, used, getattr(res, "notes", "") or "")

    m2 = formalize_entry(entry, pdf_text, complete=complete, concerns=concerns)
    if m2 is None:
        return FormalizeResult("UNKNOWN", m, adversary_log, 1, used,
                               "retry formalization returned no valid AST")
    res2 = _verify(m2, entry)
    if res2.verdict == "VERIFIED":
        c2 = adversary_check(m2, entry, pdf_text, complete=complete)
        if not c2:
            return FormalizeResult("VERIFIED", m2, adversary_log + [[]], 1, used, "")
        return FormalizeResult("UNKNOWN", m2, adversary_log + [c2], 1, used,
                               "adversary still flagged after retry")
    if res2.verdict == "COUNTEREXAMPLE":
        return FormalizeResult("COUNTEREXAMPLE", m2, adversary_log, 1, used,
                               "counterexample persists after retry")
    return FormalizeResult(res2.verdict, m2, adversary_log, 1, used,
                           getattr(res2, "notes", "") or "")
