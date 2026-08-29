"""
Validates a corpus entry (or all entries in corpus.json) against the FL corpus schema.

Usage:
    python schema/validate.py corpus.json          # validate all entries
    python schema/validate.py --entry entry.json   # validate a single entry
    python schema/validate.py corpus.json --strict # gold-tier completeness check too
"""

import json
import re
import sys
import argparse
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    import jsonschema
except ImportError:
    sys.exit("Install jsonschema:  pip install jsonschema")

from fields import GOLD_LATEX_FIELDS, is_filled

SCHEMA_PATH = Path(__file__).parent / "corpus_schema.json"

HARD_GATES: dict[str, dict[str, object]] = {
    "Shapley": {
        "ic_proof_present": True,
        "ir_proof_present": True,
    }
}

# Same payment-form regex family as src/tracks/track1_z3.py's
# _classify_vcg_payment (duplicated rather than imported so tools/ stays
# decoupled from src/'s Z3/CVXPY/mpmath dependencies). Matches the classic
# Groves/Clarke-pivot payment forms, which are efficient (welfare-maximizing)
# by construction -- Groves' theorem.
_VCG_EFFICIENT_FORM_RE = re.compile(r"\\neq\s*[a-zA-Z]|\\setminus|[Ss]\(z\^")


def _check_green_laffont(entry: dict) -> list[str]:
    """
    Green-Laffont: Efficiency + DSIC + strict Budget Balance cannot coexist
    generically. Flags VCG entries claiming dominant-strategy IC AND strong
    (exact) budget balance AND a payment form that is a classic efficient
    Groves/Clarke-pivot mechanism -- the textbook contradiction.

    This is a heuristic on the three fields the schema actually has
    (ic_type, budget_balance_type, payment_rule_latex), not a formal
    proof -- "strong" budget balance combined with a Clarke-pivot-shaped
    payment could still be correct in some restricted/quasi-linear model
    the paper sets up, so treat a hit here as "verify this wasn't a
    labeling slip," not "this paper contains an error."
    """
    if entry.get("category") != "VCG":
        return []
    mech = entry.get("mechanism") or {}
    if mech.get("ic_type") != "dominant-strategy":
        return []
    if mech.get("budget_balance_type") != "strong":
        return []
    if not _VCG_EFFICIENT_FORM_RE.search(mech.get("payment_rule_latex") or ""):
        return []
    return [
        "[green-laffont] claims dominant-strategy IC, strong (exact) budget "
        "balance, and an efficient Groves/Clarke-pivot payment form "
        "simultaneously -- Green-Laffont proves these three cannot coexist "
        "generically. Check ic_type/budget_balance_type/payment_rule_latex "
        "against what the paper actually proves."
    ]


def validate_entry(entry: dict, validator: jsonschema.Validator, strict: bool = False) -> list[str]:
    errors: list[str] = []

    # JSON Schema structural validation
    for err in validator.iter_errors(entry):
        path = " -> ".join(str(p) for p in err.absolute_path) or "(root)"
        errors.append(f"[schema] {path}: {err.message}")

    category = entry.get("category", "")
    mechanism = entry.get("mechanism", {})
    tier = entry.get("quality_tier", "")

    # Hard gates (Shapley IC/IR must be proved)
    if category in HARD_GATES:
        for field, expected in HARD_GATES[category].items():
            actual = mechanism.get(field)
            if actual != expected:
                errors.append(
                    f"[hard-gate] Shapley entry must have mechanism.{field}={expected}. "
                    f"Got {actual!r}. Reclassify to Valuation if IC/IR is not proved."
                )

    errors.extend(_check_green_laffont(entry))

    # Gold-tier LaTeX completeness (enforced always for gold, or when --strict)
    if strict or tier == "gold":
        required_latex = GOLD_LATEX_FIELDS.get(category, [])
        for field in required_latex:
            if not is_filled(mechanism.get(field)):
                errors.append(
                    f"[gold] mechanism.{field} is empty/null -- "
                    f"gold-tier {category} entries must have this field filled"
                )

    # z3_validated consistency
    rag_categories = {"RL", "Valuation", "Naive"}
    z3 = entry.get("z3_validated")
    if category in rag_categories and z3 is not None:
        errors.append(
            f"[z3] z3_validated must be null for RAG-only category '{category}', got {z3!r}"
        )
    if category not in rag_categories and tier == "gold" and z3 is None:
        errors.append(
            f"[z3] gold-tier '{category}' entry should have z3_validated set (true or false), not null"
        )
    verdict = entry.get("z3_verdict")
    if z3 is True and verdict not in (None, "VERIFIED"):
        errors.append(
            f"[z3] z3_validated is true but z3_verdict is {verdict!r} "
            f"(expected VERIFIED) for '{entry.get('id') or category}'")

    # paper_type / extension block consistency
    paper_type = entry.get("paper_type", [])
    if "application" in paper_type and "application" not in entry:
        errors.append("[paper_type] paper_type includes 'application' but 'application' block is missing")
    if "comparison" in paper_type and "comparison" not in entry:
        errors.append("[paper_type] paper_type includes 'comparison' but 'comparison' block is missing")

    return errors


def validate_file(path: Path, strict: bool) -> tuple[dict[str, list[str]], list[dict]]:
    with open(path) as f:
        data = json.load(f)

    with open(SCHEMA_PATH) as f:
        schema = json.load(f)

    validator = jsonschema.Draft7Validator(schema)

    entries = data if isinstance(data, list) else [data]
    results: dict[str, list[str]] = {}

    for entry in entries:
        pid = entry.get("paper_id", "<unknown>")
        errs = validate_entry(entry, validator, strict=strict)
        results[pid] = errs

    return results, entries


def print_metadata_completeness_report(entries: list[dict]) -> None:
    """
    fl_setup/num_clients = "unspecified" is schema-valid (it's a real enum
    value, not an error) but a corpus where most entries don't say what FL
    setup they're for silently breaks Retrieval mode, which is supposed to
    find "the closest corpus entry" by matching on exactly that. This is a
    visibility report, not a pass/fail gate -- see Task.md "Why the Corpus
    Matters" for the retrieval-mode dependency this is protecting.
    """
    total = len(entries)
    if total == 0:
        return

    fl_setup_unspecified = sum(1 for e in entries if e.get("fl_setup") == "unspecified")
    num_clients_unspecified = sum(1 for e in entries if e.get("num_clients") == "unspecified")

    by_tier: dict[str, list[dict]] = {}
    for e in entries:
        by_tier.setdefault(e.get("quality_tier", "<unknown>"), []).append(e)

    print(f"{'='*60}")
    print("  Metadata Completeness Report (not a pass/fail gate)")
    print(f"{'='*60}")
    print(f"  fl_setup unspecified:    {fl_setup_unspecified}/{total} "
          f"({100*fl_setup_unspecified/total:.0f}%)")
    print(f"  num_clients unspecified: {num_clients_unspecified}/{total} "
          f"({100*num_clients_unspecified/total:.0f}%)")
    print(f"  By quality tier (fl_setup unspecified rate):")
    for tier in ("gold", "silver", "bronze"):
        tier_entries = by_tier.get(tier, [])
        if not tier_entries:
            continue
        n_unspecified = sum(1 for e in tier_entries if e.get("fl_setup") == "unspecified")
        print(f"    {tier:<8} {n_unspecified}/{len(tier_entries)} "
              f"({100*n_unspecified/len(tier_entries):.0f}%)")
    print(f"{'='*60}\n")


def print_report(results: dict[str, list[str]]) -> int:
    total = len(results)
    failed = {pid: errs for pid, errs in results.items() if errs}
    passed = total - len(failed)

    print(f"\n{'='*60}")
    print(f"  FL Corpus Validation Report")
    print(f"{'='*60}")
    print(f"  Entries checked : {total}")
    print(f"  Passed          : {passed}")
    print(f"  Failed          : {len(failed)}")
    print(f"{'='*60}\n")

    for pid, errs in sorted(failed.items()):
        print(f"FAIL  {pid}")
        for e in errs:
            print(f"      {e}")
        print()

    if not failed:
        print("All entries valid.\n")

    return 1 if failed else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate FL corpus entries against schema")
    parser.add_argument("corpus", nargs="?", type=Path, help="Path to corpus.json (list or single entry)")
    parser.add_argument("--entry", type=Path, help="Path to a single entry JSON file")
    parser.add_argument("--strict", action="store_true", help="Enforce gold-tier LaTeX completeness on all entries")
    parser.add_argument("--metadata", action="store_true",
                        help="Also print the fl_setup/num_clients completeness report")
    args = parser.parse_args()

    target = args.entry or args.corpus
    if not target:
        parser.print_help()
        sys.exit(1)

    if not target.exists():
        sys.exit(f"File not found: {target}")

    results, entries = validate_file(target, strict=args.strict)
    exit_code = print_report(results)
    if args.metadata:
        print_metadata_completeness_report(entries)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
