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
