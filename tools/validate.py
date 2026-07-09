"""
Validates a corpus entry (or all entries in corpus.json) against the FL corpus schema.

Usage:
    python schema/validate.py corpus.json          # validate all entries
    python schema/validate.py --entry entry.json   # validate a single entry
    python schema/validate.py corpus.json --strict # gold-tier completeness check too
"""

import json
import sys
import argparse
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

    # paper_type / extension block consistency
    paper_type = entry.get("paper_type", [])
    if "application" in paper_type and "application" not in entry:
        errors.append("[paper_type] paper_type includes 'application' but 'application' block is missing")
    if "comparison" in paper_type and "comparison" not in entry:
        errors.append("[paper_type] paper_type includes 'comparison' but 'comparison' block is missing")

    return errors


def validate_file(path: Path, strict: bool) -> dict[str, list[str]]:
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

    return results


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
    args = parser.parse_args()

    target = args.entry or args.corpus
    if not target:
        parser.print_help()
        sys.exit(1)

    if not target.exists():
        sys.exit(f"File not found: {target}")

    results = validate_file(target, strict=args.strict)
    sys.exit(print_report(results))


if __name__ == "__main__":
    main()
