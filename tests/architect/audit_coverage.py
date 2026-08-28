"""Manual audit: how many z3_validated corpus mechanisms fit the AST node set?
Run: PYTHONPATH=src python tests/architect/audit_coverage.py
Writes docs/ast-coverage.md.
"""
import json, collections, pathlib

corpus = json.load(open("corpus.json"))
validated = [e for e in corpus if e.get("z3_validated") is True]
by_cat = collections.Counter(e["category"] for e in validated)

lines = ["# AST Coverage Audit", "",
         f"z3_validated entries: {len(validated)}",
         f"by category: {dict(by_cat)}", "",
         "## Per-entry mechanism field inventory", ""]
seen_forms = collections.Counter()
for e in validated:
    mech = e.get("mechanism") or {}
    lines.append(f"### {e['paper_id']} ({e['category']})")
    for k, v in mech.items():
        if isinstance(v, str) and v.strip():
            lines.append(f"- `{k}`: `{v[:200]}`")
            for tok in ("\\ln", "\\exp", "\\sum", "\\int", "\\frac", "^2", "^3", "\\mathbb{E}"):
                if tok in v:
                    seen_forms[tok] += 1
    lines.append("")
lines.append("## Algebraic tokens seen across validated mechanisms")
lines.append(f"{dict(seen_forms)}")
lines.append("")
lines.append("## Verdict")
lines.append("- [ ] node set covers >= 90% of the above (fill in after manual read)")
lines.append("- List misses and the node that would be needed:")
pathlib.Path("docs/ast-coverage.md").write_text("\n".join(lines))
print("wrote docs/ast-coverage.md")
