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


_VCG_CLASSIFY_SYS = (
    'You classify a Federated-Learning auction ALLOCATION rule (given as LaTeX) '
    'into exactly one type. Return ONLY JSON: {"t":"AllocHighest"} OR '
    '{"t":"AllocTopK","k":<int>} OR {"t":"AllocWeightedWelfare",'
    '"weights":["<w1>","<w2>",...]} OR {"t":null}. AllocHighest: winner is the '
    'single argmax of a welfare/score/objective (reverse-auction: argmin cost). '
    'AllocTopK: the k highest are selected, k a fixed integer. '
    'AllocWeightedWelfare: winner maximizes a weighted sum of named terms; '
    'weights = the coefficient symbols in order. null: an opaque algorithm, a '
    'learned policy, a piecewise/threshold rule, or a rule none of the above '
    'fit. Do not guess.'
)


def classify_vcg_allocation(alloc_latex, *, complete=llm_complete):
    """Classify a VCG allocation-rule LaTeX string into a typed-node spec.

    Never raises: any failure path returns {"t": None}.
    """
    if not alloc_latex:
        return {"t": None}
    try:
        raw = complete(_VCG_CLASSIFY_SYS,
                       "allocation_rule_latex: " + repr(alloc_latex),
                       json_mode=True)
        d = json.loads(raw)
    except Exception:
        return {"t": None}
    if not isinstance(d, dict) or "t" not in d:
        return {"t": None}
    t = d["t"]
    if t is None:
        return {"t": None}
    if t == "AllocHighest":
        return d
    if t == "AllocTopK":
        return d if isinstance(d.get("k"), int) and not isinstance(d.get("k"), bool) else {"t": None}
    if t == "AllocWeightedWelfare":
        w = d.get("weights")
        return d if isinstance(w, list) and w else {"t": None}
    return {"t": None}


def formalize_vcg_entry(entry, *, complete=llm_complete):
    from architect.ast import (
        Mechanism, Sym, AllocHighest, AllocTopK, AllocWeightedWelfare,
    )
    m = entry.get("mechanism", {})
    cls = classify_vcg_allocation(m.get("allocation_rule_latex"), complete=complete)
    t = cls.get("t")
    if t == "AllocHighest":
        node = AllocHighest()
    elif t == "AllocTopK":
        node = AllocTopK(int(cls["k"]))
    elif t == "AllocWeightedWelfare":
        node = AllocWeightedWelfare([str(w) for w in cls["weights"]])
    else:
        node = None
    meta = {
        "num_clients": entry.get("num_clients"),
        "allocation_rule_latex": m.get("allocation_rule_latex"),
        "payment_rule_latex": m.get("payment_rule_latex"),
        "client_utility_latex": m.get("client_utility_latex"),
        "auction_type": m.get("auction_type", "reverse"),
    }
    mech = Mechanism(category="VCG", utility=Sym("u"), payment=Sym("v"),
                     ic=Sym("v"), ir=Sym("v"), type_space=[],
                     allocation=node, meta=meta)
    res = verify_from_ast(mech, meta={"paper_id": entry.get("paper_id", "")})
    return FormalizeResult(verdict=res.verdict, ast=mech, adversary_log=[],
                           retries=0, pdf_used=False,
                           notes=(getattr(res, "notes", "") or ""))


_CONTRACT_IC_SYS = (
    "You extract the screening incentive constraints of a Federated-Learning "
    "CONTRACT mechanism from the paper text. Return ONLY JSON: "
    '{"ic_screening_latex": "<LaTeX>", "ir_participation_latex": "<LaTeX>", '
    '"client_utility_latex": "<LaTeX>", "num_types": <int or null>, '
    '"confident": <bool>}. Rules: ic_screening_latex MUST be a two-sided '
    'inequality "U_i(own contract) >= U_i(deviating contract)" with the '
    "deviating-type utility on the RHS depending on the true type i "
    "(single-letter symbol bases, subscript for the type index, e.g. "
    "`\\theta_i R_i - c_i f_i \\geq \\theta_i R_j - c_i f_j`). "
    'ir_participation_latex is "U_i(own) >= 0". client_utility_latex is the '
    "inline algebraic utility (NOT a function-call reference). If the paper's "
    "contract is Bayesian (expected utility over others' types), still give the "
    "deterministic screening form and set confident=false. If you cannot find "
    'an explicit screening IC in the text, set every latex field to "" and '
    "confident=false. Do NOT invent constraint terms the paper does not state."
)

_EMPTY_EXTRACTION = {
    "confident": False,
    "ic_screening_latex": "",
    "ir_participation_latex": "",
    "client_utility_latex": "",
    "num_types": None,
}


def extract_contract_constraints(entry, pdf_text, *, complete=llm_complete):
    """Ask the model for a Contract entry's screening IC/IR from the paper.

    Only for entries whose own `ic_screening_latex` is empty. Never raises:
    any failure (LLMError, bad JSON, wrong shape) returns the all-empty,
    `confident: False` dict so the caller fails closed.
    """
    user = (
        f"mechanism dict:\n{json.dumps(entry.get('mechanism', {}), indent=1)}"
        f"\n\npaper text (excerpt):\n{(pdf_text or '')[:20000]}"
    )
    try:
        d = json.loads(complete(_CONTRACT_IC_SYS, user, json_mode=True))
    except Exception:
        return dict(_EMPTY_EXTRACTION)
    if not isinstance(d, dict):
        return dict(_EMPTY_EXTRACTION)
    out = dict(_EMPTY_EXTRACTION)
    for k in ("ic_screening_latex", "ir_participation_latex",
              "client_utility_latex"):
        v = d.get(k)
        out[k] = v if isinstance(v, str) else ""
    n = d.get("num_types")
    out["num_types"] = n if isinstance(n, int) and not isinstance(n, bool) else None
    # "confident" only means anything alongside an actual two-sided IC; a
    # confident-but-empty answer is an incoherent state, so normalize it away
    # here rather than relying on every caller to re-check.
    out["confident"] = d.get("confident") is True and bool(out["ic_screening_latex"])
    return out


def formalize_contract_entry(entry, pdf_text, *, complete=llm_complete):
    """LLM IC/IR extraction for a Contract entry with no usable IC latex.

    The paper's own transcription always wins: if `_parse_contract_entry`
    already succeeds there is nothing to extract and no model is called.
    A successfully-verifying extraction is stashed on the entry under
    `*_llm` mechanism keys (never overwriting the paper's fields) so
    `run_batch` can persist it as the auditable artifact.
    """
    from tracks.track1_z3 import _parse_contract_entry, _try_contract_latex

    if _parse_contract_entry(entry) is not None or not pdf_text:
        return FormalizeResult(
            "UNKNOWN", None, [], 0, bool(pdf_text),
            "contract: existing IC latex parseable or no PDF; nothing to extract",
        )

    ext = extract_contract_constraints(entry, pdf_text, complete=complete)
    if not ext["confident"] or not ext["ic_screening_latex"]:
        return FormalizeResult(
            "UNKNOWN", None, [], 0, True,
            "contract: LLM could not confidently extract a screening IC",
        )

    mech = entry.get("mechanism") or {}
    probe_mech = {
        **mech,
        "ic_screening_latex": ext["ic_screening_latex"],
        "ir_participation_latex": ext["ir_participation_latex"],
        "client_utility_latex": (
            ext["client_utility_latex"] or mech.get("client_utility_latex", "")
        ),
    }
    if not mech.get("num_types") and ext["num_types"]:
        probe_mech["num_types"] = ext["num_types"]
    res = _try_contract_latex({**entry, "mechanism": probe_mech})

    verdict = getattr(res, "verdict", None) or "UNKNOWN"
    if verdict in ("VERIFIED", "COUNTEREXAMPLE"):
        # Stash as FALLBACK keys only -- the paper's own latex is never
        # overwritten. run_batch persists these into the corpus.
        mech["ic_screening_latex_llm"] = ext["ic_screening_latex"]
        mech["ir_participation_latex_llm"] = ext["ir_participation_latex"]
        if ext["client_utility_latex"]:
            mech["client_utility_latex_llm"] = ext["client_utility_latex"]
        if not mech.get("num_types") and ext["num_types"]:
            mech["num_types"] = ext["num_types"]
        entry["mechanism"] = mech

    return FormalizeResult(
        verdict, None, [], 0, True,
        (getattr(res, "notes", "") or "") or "LLM-extracted IC did not verify",
    )


_LLM_MECH_KEYS = (
    "ic_screening_latex_llm",
    "ir_participation_latex_llm",
    "client_utility_latex_llm",
)


def formalize_with_retry(entry, pdf_text, *, complete=llm_complete):
    if entry.get("category") == "VCG":
        return formalize_vcg_entry(entry, complete=complete)
    if entry.get("category") == "Contract":
        return formalize_contract_entry(entry, pdf_text, complete=complete)
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


import os
import argparse
from datetime import date
from architect.pdf_text import pdf_text


def _select(corpus, ids, only):
    if ids:
        want = set(ids)
        return [e for e in corpus if e.get("paper_id") in want]
    if only:
        return [e for e in corpus if e.get("category") == only]
    return list(corpus)


def _report_md(records, today):
    lines = [f"# Formalize run — {today}", "",
             "| paper_id | category | verdict | retries | adversary_rounds | pdf_used | notes |",
             "|---|---|---|---|---|---|---|"]
    for r in records:
        lines.append(
            f"| {r['paper_id']} | {r['category']} | {r['verdict']} | {r['retries']} "
            f"| {r['adversary_rounds']} | {r['pdf_used']} | {r['notes']} |")
    queue = [r for r in records if r["verdict"] in ("UNKNOWN", "COUNTEREXAMPLE")]
    lines += ["", "## Human queue", ""]
    if queue:
        for r in queue:
            lines.append(f"- {r['paper_id']} ({r['verdict']}): {r['notes']}")
    else:
        lines.append("- (empty)")
    n = len(records)
    summary = {
        "selected": n,
        "verified": sum(1 for r in records if r["verdict"] == "VERIFIED"),
        "counterexample": sum(1 for r in records if r["verdict"] == "COUNTEREXAMPLE"),
        "unknown": sum(1 for r in records if r["verdict"] == "UNKNOWN"),
        "dict_only": sum(1 for r in records if not r["pdf_used"]),
    }
    lines += ["", "## Summary", ""]
    for k, v in summary.items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines) + "\n", summary


def run_batch(corpus_path, *, ids=None, only=None, dry_run=False,
              complete=llm_complete, today=None, resume=False, limit=None,
              report_dir="docs/superpowers/notes"):
    today = today or date.today().isoformat()
    with open(corpus_path) as fh:
        corpus = json.load(fh)
    model = os.environ.get("ARCHITECT_LLM_MODEL", "default")
    selected = _select(corpus, ids, only)
    if resume:
        selected = [e for e in selected if not e.get("formalized_ast")]
    if limit is not None:
        selected = selected[:limit]
    records = []
    for entry in selected:
        pid = entry.get("paper_id", "")
        txt = pdf_text(pid)
        r = formalize_with_retry(entry, txt, complete=complete)
        # `formalization_meta` is written in exactly ONE place, on whichever
        # artifact this entry actually produced: an AST (the usual path) or
        # the Contract `_llm` mechanism keys stashed by
        # formalize_contract_entry. Keeping the two branches mutually
        # exclusive stops the AST write from clobbering the Contract
        # provenance, which records that the IC latex came from a model
        # rather than the paper's own transcription.
        if r.verdict in ("VERIFIED", "COUNTEREXAMPLE"):
            if r.ast is not None:
                entry["formalized_ast"] = to_dict(r.ast)
                entry["formalization_meta"] = {
                    "model": model, "verdict": r.verdict, "retries": r.retries,
                    "adversary_rounds": len(r.adversary_log),
                    "pdf_used": r.pdf_used, "flagged": False, "date": today,
                }
            elif any(k in (entry.get("mechanism") or {}) for k in _LLM_MECH_KEYS):
                entry["formalization_meta"] = {
                    "model": model, "verdict": r.verdict,
                    "source": "llm_ic_extraction", "date": today,
                }
        records.append({
            "paper_id": pid, "category": entry.get("category", ""),
            "verdict": r.verdict, "retries": r.retries,
            "adversary_rounds": len(r.adversary_log), "pdf_used": r.pdf_used,
            "notes": r.notes,
        })
    if not dry_run:
        with open(corpus_path, "w") as fh:
            json.dump(corpus, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    md, summary = _report_md(records, today)
    report_path = os.path.join(report_dir, f"formalize-run-{today}.md")
    if not dry_run:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as fh:
            fh.write(md)
    return {"records": records, "report_path": report_path, "summary": summary}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m architect.formalize")
    ap.add_argument("corpus_path")
    ap.add_argument("--ids", default=None, help="comma-separated paper_id list")
    ap.add_argument("--only", default=None, help="restrict to one category")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true",
                    help="skip entries that already have formalized_ast")
    ap.add_argument("--limit", type=int, default=None,
                    help="process at most N entries after selection/resume")
    ap.add_argument("--report-dir", default="docs/superpowers/notes",
                    help="directory for the run report markdown")
    args = ap.parse_args(argv)
    ids = args.ids.split(",") if args.ids else None
    out = run_batch(args.corpus_path, ids=ids, only=args.only,
                    dry_run=args.dry_run, resume=args.resume, limit=args.limit,
                    report_dir=args.report_dir)
    print("summary:", out["summary"], "report:", out["report_path"])


if __name__ == "__main__":
    main()


import re as _re

MANUAL_BACKLOG_PATH = "docs/superpowers/notes/MANUAL-backlog.md"


def write_manual_diagnosis(entry, *, round_, track, limit, mechanism,
                           obstruction, human_task, today=None):
    for name, val in (("limit", limit), ("obstruction", obstruction),
                      ("human_task", human_task)):
        if not str(val).strip():
            raise ValueError(f"MANUAL diagnosis requires a non-empty {name!r}")
    diag = {
        "round": round_, "track": int(track), "limit": limit,
        "mechanism": mechanism, "obstruction": obstruction,
        "human_task": human_task,
        "date": today or date.today().isoformat(),
    }
    entry["verdict_override"] = "MANUAL"
    entry["manual_diagnosis"] = diag
    return diag


def _backlog_section(entry):
    d = entry["manual_diagnosis"]
    return (
        f"## {entry.get('paper_id','')} ({entry.get('category','')}) — {d['round']}\n\n"
        f"**Mechanism:** {d['mechanism']}\n"
        f"**Obstruction:** {d['obstruction']} (Track {d['track']}: {d['limit']})\n"
        f"**Human task:** {d['human_task']}\n"
        f"**Diagnosed:** {d['date']}\n"
    )


def append_backlog_paragraph(entry, *, backlog_path=MANUAL_BACKLOG_PATH):
    pid = entry.get("paper_id", "")
    section = _backlog_section(entry)
    header = ("# MANUAL Backlog\n\nOne paragraph per corpus entry that no "
              "automated track can decide.\n")
    try:
        with open(backlog_path) as fh:
            body = fh.read()
    except OSError:
        body = header
    pat = _re.compile(rf"(?ms)^## {_re.escape(pid)} .*?(?=^## |\Z)")
    body = pat.sub("", body).rstrip() + "\n"
    if not body.startswith("# MANUAL Backlog"):
        body = header + "\n" + body
    body = body.rstrip() + "\n\n" + section
    d = os.path.dirname(backlog_path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(backlog_path, "w") as fh:
        fh.write(body.rstrip() + "\n")
