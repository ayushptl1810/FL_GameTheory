"""Trace every MANUAL corpus entry through its real verifier code path to
find where it actually bails, independent of the stored manual_diagnosis
text. verify()/verify_from_ast() short-circuit MANUAL entries before ever
running the solver -- this script bypasses that short-circuit by calling
each category's entry point directly, the same call the entry would get
if verdict_override were not set.

Run: PYTHONPATH=src python scripts/diagnose_manual_root_cause.py corpus.json
Writes: docs/superpowers/notes/round-R9-root-cause-audit.md
        docs/superpowers/notes/round-R9-root-cause-audit.json
"""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tracks.track1_z3 import (
    _try_contract_latex,
    _try_stackelberg_latex,
    verify_vcg,
    verify_shapley,
)
from tracks.track_coalition import verify_coalition
from tracks.track2_sos import verify_track2
from tracks.track3_dreal import verify_track3
from tracks.track4_sympy import verify_track4


@dataclasses.dataclass
class TraceResult:
    paper_id: str
    category: str
    stored_round: str
    stored_obstruction: str
    stored_limit: str
    bail_function: str
    bail_reason: str
    matches_stored: bool


# Category -> ordered list of (function_name, callable) to try, approximating
# _verify_latex's own routing in src/verifier.py (Track 4 -> 3 -> 2 -> 1).
# Each callable takes `entry: dict` and returns `VerificationResult | None`
# except verify_vcg/verify_shapley/verify_coalition which never return None
# (they fall back to VERIFIED_TEMPLATE/UNKNOWN internally) -- for those,
# "bail" means the returned verdict is not VERIFIED/COUNTEREXAMPLE.
#
# KNOWN LIMITATION: this table calls _try_contract_latex and
# _try_stackelberg_latex directly, but the real pipeline (verify_contract /
# verify_stackelberg in src/tracks/track1_z3.py) guards each behind a
# precondition gate that can reject an entry one frame earlier -- Contract
# requires both ic_screening_latex and ir_participation_latex truthy before
# ever calling _try_contract_latex; Stackelberg returns UNSUPPORTED
# immediately when equilibrium_existence is False, without calling
# _try_stackelberg_latex. For the 11 entries affected by these gates,
# bail_function names a function the real pipeline never actually invokes --
# the recorded bail_reason text is still accurate, only the function name is
# one frame too deep. See the caveat near the top of the generated
# docs/superpowers/notes/round-R9-root-cause-audit.md for the affected list.
_ENTRY_POINTS = {
    "Contract": [
        ("verify_track4", verify_track4),
        ("verify_track3", verify_track3),
        ("verify_track2", verify_track2),
        ("_try_contract_latex", _try_contract_latex),
    ],
    "Stackelberg": [
        ("verify_track3", verify_track3),
        ("_try_stackelberg_latex", _try_stackelberg_latex),
    ],
    "VCG": [
        ("verify_vcg", verify_vcg),
    ],
    "Shapley": [
        ("verify_coalition", verify_coalition),
        ("verify_shapley", verify_shapley),
    ],
}

_TERMINAL_VERDICTS = {"VERIFIED", "COUNTEREXAMPLE"}


def trace_entry(entry: dict) -> TraceResult:
    category = entry.get("category", "")
    paper_id = entry.get("paper_id", "<unknown>")
    diag = entry.get("manual_diagnosis") or {}
    stored_round = str(diag.get("round", "?"))
    stored_obstruction = str(diag.get("obstruction", ""))
    stored_limit = str(diag.get("limit", ""))

    bail_function = "no-entry-point-for-category"
    bail_reason = f"no verification entry point registered for category '{category}'"

    for fn_name, fn in _ENTRY_POINTS.get(category, []):
        try:
            result = fn(entry)
        except Exception as exc:  # fail closed: an exception IS the bail point
            bail_function = fn_name
            bail_reason = f"raised {type(exc).__name__}: {exc}"
            break
        if result is None:
            bail_function = fn_name
            bail_reason = "returned None"
            continue
        if getattr(result, "verdict", None) in _TERMINAL_VERDICTS:
            bail_function = fn_name
            bail_reason = f"did not bail -- returned {result.verdict} (re-check why this is still MANUAL)"
            break
        # Non-terminal but non-None (e.g. VERIFIED_TEMPLATE, UNKNOWN) --
        # record it and keep trying the next entry point, since
        # _verify_latex's own routing does the same (falls through).
        bail_function = fn_name
        bail_reason = f"returned non-terminal verdict {getattr(result, 'verdict', '?')}: {getattr(result, 'notes', '')}"

    matches_stored = _reason_matches_stored(bail_reason, stored_obstruction, stored_limit)

    return TraceResult(
        paper_id=paper_id,
        category=category,
        stored_round=stored_round,
        stored_obstruction=stored_obstruction,
        stored_limit=stored_limit,
        bail_function=bail_function,
        bail_reason=bail_reason,
        matches_stored=matches_stored,
    )


def _reason_matches_stored(bail_reason: str, stored_obstruction: str, stored_limit: str) -> bool:
    """Heuristic overlap check -- not a proof of correctness, a triage
    signal. A human reviews every 'False' row in Phase 2; this just sorts
    the 86 entries into 'probably fine' vs 'look at this' buckets.
    """
    stored = (stored_obstruction + " " + stored_limit).lower()
    reason = bail_reason.lower()
    key_terms = [w for w in reason.replace("_", " ").split() if len(w) > 5]
    return any(term in stored for term in key_terms[:5])


def main(corpus_path: str) -> None:
    corpus = json.load(open(corpus_path))
    rows = corpus["entries"] if isinstance(corpus, dict) else corpus
    manual = [e for e in rows if e.get("verdict_override") == "MANUAL"]

    results = [trace_entry(e) for e in sorted(manual, key=lambda e: e.get("paper_id", ""))]

    json_path = Path("docs/superpowers/notes/round-R9-root-cause-audit.json")
    json_path.write_text(json.dumps([dataclasses.asdict(r) for r in results], indent=2))

    md_lines = [
        "# R9 — Root-Cause Audit",
        "",
        f"Traced {len(results)} MANUAL entries through their real verifier code path.",
        "`matches_stored` is a heuristic triage signal, not a proof -- every `False` row",
        "needs a human read in Phase 2 to confirm the real obstruction.",
        "",
        f"**Mismatches found: {sum(1 for r in results if not r.matches_stored)} / {len(results)}**",
        "",
        "| Paper ID | Category | Stored Round | Stored Obstruction (truncated) | Real Bail Function | Real Bail Reason (truncated) | Match? |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        so = (r.stored_obstruction[:60] + "...") if len(r.stored_obstruction) > 60 else r.stored_obstruction
        br = (r.bail_reason[:60] + "...") if len(r.bail_reason) > 60 else r.bail_reason
        md_lines.append(
            f"| {r.paper_id} | {r.category} | {r.stored_round} | {so} | {r.bail_function} | {br} | {r.matches_stored} |"
        )
    Path("docs/superpowers/notes/round-R9-root-cause-audit.md").write_text("\n".join(md_lines) + "\n")

    print(f"Traced {len(results)} entries. Mismatches: {sum(1 for r in results if not r.matches_stored)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "corpus.json")
