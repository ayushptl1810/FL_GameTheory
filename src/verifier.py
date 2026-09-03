#!/usr/bin/env python3
"""
Multi-track FL incentive mechanism verifier.

Routes each corpus entry to the appropriate verification track based on
the structure of its utility function:

  Track 1 — Z3          linear / discrete-type    (exact, fast)
  Track 2 — SOS/CVXPY   polynomial (deg ≥ 2)      (exact certificate)
  Track 3 — dReal        transcendental (ln, exp)  (δ-sound)
  Track 4 — SymPy        Bayesian IC (E[·] form)   (exact symbolic)

The router tries the highest-fidelity applicable track first and falls
back to Track 1 (Z3) for linear / unclassified utilities.

Usage:
    python src/verifier.py entries/Cong2020vcg.json
    python src/verifier.py entries/               # batch all entries
    python src/verifier.py entries/ --gold        # gold-tier only
    python src/verifier.py corpus.json            # full corpus list
    python src/verifier.py entries/ --verbose     # print every result
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Ensure src/ is on the path so `from tracks...` works when run as a script
sys.path.insert(0, str(Path(__file__).parent))

from tracks import VerificationResult
from tracks.track1_z3 import (
    verify_contract,
    verify_shapley,
    verify_stackelberg,
    verify_vcg,
    _VCG_FORM_CLAIMS,
)
from tracks.track2_sos import verify_track2
from tracks.track3_dreal import verify_track3
from tracks.track4_sympy import verify_track4

from architect.ast import from_dict, ASTSchemaError
from architect.ast_verify import verify_from_ast

_RAG_ONLY = frozenset({"RL", "Valuation", "Naive"})

# ── Utility-structure router ──────────────────────────────────────────────────

_TRANSCENDENTAL_RE = re.compile(
    r"\\(ln|log|exp|sigma|sin|cos|tan|sqrt|operatorname\{sigmoid\})"
)
_BAYESIAN_RE = re.compile(r"\\mathbb\{E\}|\\int|bayesian|bic", re.IGNORECASE)
_POLYNOMIAL_RE = re.compile(r"\^[2-6]")


def _classify_utility(entry: dict) -> int:
    """
    Return the preferred track number for this entry.

    Priority (highest fidelity first):
      4 — Bayesian IC (expectation/integral form)
      3 — transcendental (ln, exp, sigmoid)
      2 — polynomial degree ≥ 2
      1 — linear / discrete / default

    Scans every string-valued field on the mechanism object rather than a
    fixed list of field names. The corpus schema is category-specific --
    Contract uses ic_screening_latex/ir_participation_latex, VCG uses
    payment_rule_latex/ic_type, Stackelberg uses leader_objective_latex/
    follower_utility_latex/best_response_latex, Shapley uses
    shapley_formula_latex/characteristic_function_latex -- and a fixed
    field list (previously keyed on a "utility_function_latex" field that
    exists in zero corpus entries) silently classified every non-Contract,
    non-VCG entry as Track 1 regardless of its actual math content.
    """
    mech = entry.get("mechanism") or {}
    fields = " ".join(str(v) for v in mech.values() if isinstance(v, str))

    if _BAYESIAN_RE.search(fields):
        return 4
    if _TRANSCENDENTAL_RE.search(fields):
        return 3
    if _POLYNOMIAL_RE.search(fields):
        return 2
    return 1


# ── Dispatcher ────────────────────────────────────────────────────────────────

def _verify_latex(entry: dict) -> VerificationResult:
    """Route entry to the appropriate track and return a VerificationResult."""
    category = entry.get("category", "")
    paper_id = entry.get("paper_id", "<unknown>")

    if category in _RAG_ONLY:
        return VerificationResult(
            verdict="UNSUPPORTED",
            category=category,
            paper_id=paper_id,
            track=0,
            notes=f"'{category}' is RAG-only — no formal mechanism proofs expected.",
        )

    preferred = _classify_utility(entry)

    # Track 4: Bayesian IC — SymPy integration
    if preferred == 4:
        result = verify_track4(entry)
        if result is not None:
            return result

    # Track 3: transcendental — interval arithmetic
    elif preferred == 3:
        result = verify_track3(entry)
        if result is not None and result.verdict != "UNKNOWN":
            return result
        # Fall through on None (Track 3's own field scan found nothing to
        # check — e.g. classify_utility matched on a Stackelberg field Track 3
        # doesn't look at) AND on UNKNOWN (2026-07-19): an inconclusive box
        # search must not shadow Track 1's Contract path, which has the
        # type-ordering machinery and a VERIFIED-sound relaxed log/exp
        # encoding. If Track 1 is also indecisive, return Track 3's result
        # (its conditions explain *why* the box search failed). Track 1's
        # Stackelberg path parses transcendentals fine via SymPy
        # differentiation, no Z3 involved.
        if result is not None:
            t1_fn = {"VCG": verify_vcg, "Contract": verify_contract,
                     "Stackelberg": verify_stackelberg, "Shapley": verify_shapley}.get(category)
            if t1_fn is not None:
                t1_result = t1_fn(entry)
                if t1_result.verdict != "UNKNOWN":
                    t1_result.notes = (t1_result.notes +
                                       " | Track 3 interval search was inconclusive first")
                    return t1_result
            return result

    # Track 2: polynomial — SOS via CVXPY
    elif preferred == 2:
        result = verify_track2(entry)
        if result is not None:
            return result
        # Fallthrough to Z3 NRA for low-degree polynomials

    # Track 2 parametric certificate for Contract entries (2026-07-19): the
    # linear-vs-polynomial classifier distinction is irrelevant here — the
    # parametric path produces an exact symbolic positivity certificate
    # wherever the menu structure is solvable, which is a stronger, paper-
    # ready artifact than an SMT unsat trace. Try it before Z3; only a
    # VERIFIED certificate short-circuits, everything else falls through to
    # Track 1 (which can also produce counterexamples — Track 2 cannot).
    if category == "Contract":
        t2_result = verify_track2(entry)
        if t2_result is not None and t2_result.verdict == "VERIFIED":
            return t2_result

    # Track 1: Z3 (linear / discrete / fallback)
    dispatch = {
        "VCG":         verify_vcg,
        "Contract":    verify_contract,
        "Stackelberg": verify_stackelberg,
        "Shapley":     verify_shapley,
    }
    fn = dispatch.get(category)
    if fn is None:
        return VerificationResult(
            verdict="UNSUPPORTED",
            category=category,
            paper_id=paper_id,
            track=1,
            notes=f"No verifier for category '{category}'.",
        )
    return fn(entry)


_LATEX_WEAK = {"VERIFIED_TEMPLATE", "VERIFIED_SHAPE", "UNKNOWN", "UNSUPPORTED"}


def _flag(chosen: VerificationResult, latex: VerificationResult,
         llm: VerificationResult) -> VerificationResult:
    tag = f"RECONCILE-FLAG: LaTeX={latex.verdict} LLM={llm.verdict}"
    notes = f"{chosen.notes} | {tag}".strip(" |")
    return dataclasses.replace(chosen, notes=notes)


def _reconcile(llm: VerificationResult,
               latex: VerificationResult) -> tuple[VerificationResult, bool]:
    latex_is_verified = latex.verdict == "VERIFIED" and getattr(latex, "entry_specific", False)
    llm_is_verified = llm.verdict == "VERIFIED" and getattr(llm, "entry_specific", False)
    if latex.verdict in _LATEX_WEAK and llm_is_verified:
        return llm, False
    if latex.verdict in _LATEX_WEAK and llm.verdict == "COUNTEREXAMPLE":
        return _flag(llm, latex, llm), True
    if latex_is_verified and llm_is_verified:
        return latex, False
    if latex_is_verified and llm.verdict in ("COUNTEREXAMPLE", "UNKNOWN", "UNSUPPORTED"):
        return _flag(latex, latex, llm), True
    if latex.verdict == "COUNTEREXAMPLE" and llm_is_verified:
        return _flag(latex, latex, llm), True
    return latex, False


def _manual_note(entry: dict) -> str:
    d = entry.get("manual_diagnosis") or {}
    if not d:
        return "MANUAL: no diagnosis recorded"
    return (f"MANUAL ({d.get('round', '?')}): {d.get('obstruction', '')} "
            f"[Track {d.get('track', 0)}: {d.get('limit', '')}]")


def verify(entry: dict) -> VerificationResult:
    """Prefer a stored formalized_ast; reconcile with the LaTeX path."""
    if entry.get("verdict_override") == "MANUAL":
        d = entry.get("manual_diagnosis") or {}
        return VerificationResult(
            verdict="MANUAL",
            category=entry.get("category", ""),
            paper_id=entry.get("paper_id", ""),
            track=int(d.get("track", 0) or 0),
            notes=_manual_note(entry),
            entry_specific=False,
        )
    latex_res = _verify_latex(entry)
    fa = entry.get("formalized_ast")
    if not fa:
        return latex_res
    try:
        m = from_dict(fa)
    except ASTSchemaError:
        return latex_res
    llm_res = verify_from_ast(m, meta={"paper_id": entry.get("paper_id", "")})
    chosen, _flagged = _reconcile(llm_res, latex_res)
    return chosen


# ── Batch loader ──────────────────────────────────────────────────────────────

def verify_corpus(entries_dir: Path, gold_only: bool = False) -> list[VerificationResult]:
    results = []
    for path in sorted(entries_dir.glob("*.json")):
        entry = json.loads(path.read_text())
        if gold_only and entry.get("quality_tier") != "gold":
            continue
        if entry.get("category") in _RAG_ONLY:
            continue
        results.append(verify(entry))
    return results


# ── Summary printer ───────────────────────────────────────────────────────────

def print_summary(
    results: list[VerificationResult],
    backlog_path: str = "docs/superpowers/notes/MANUAL-backlog.md",
) -> None:
    counts: Counter[str] = Counter(r.verdict for r in results)
    total = len(results)

    # VERIFIED means entry_specific=True (checked against the paper's own
    # LaTeX); VERIFIED_TEMPLATE means only a generic structural template
    # for the category was checked -- see tracks/__init__.py:finalize_verdict.
    # Both are "passed" for the per-category breakdown below; the verdict
    # bars above keep them visually separate so this table never collapses
    # them back into one misleading "N verified" headline.
    passed = [r for r in results if r.verdict in ("VERIFIED", "VERIFIED_TEMPLATE")]
    # VERIFIED_SHAPE is a regex/structural shape match only -- never a proof and
    # never a solver run on the entry. It is deliberately NOT in `passed`, so it
    # cannot inflate the entry-specific / form-confirmed counts. Reported
    # separately below as "regex-shape only (not a proof)".
    shape_only = [r for r in results if r.verdict == "VERIFIED_SHAPE"]

    vcg_results = [r for r in passed if r.category == "VCG"]
    vcg_form_counts: Counter[str] = Counter()
    for r in vcg_results:
        for form in ("clarke_pivot", "marginal_welfare", "critical_bid",
                     "budget_split", "unclassified", "none"):
            label = _VCG_FORM_CLAIMS[form].split(" —")[0].split(" (")[0]
            if label in r.notes:
                vcg_form_counts[form] += 1
                break
        else:
            vcg_form_counts["none"] += 1

    vcg_confirmed      = sum(1 for r in vcg_results if r.entry_specific)
    vcg_grid_bounded   = sum(
        1 for r in results
        if r.verdict == "VERIFIED" and getattr(r, "grid_bounded", False)
    )
    stackelberg_passed = [r for r in passed if r.category == "Stackelberg"]
    stackelberg_specific = sum(1 for r in stackelberg_passed if r.entry_specific)
    dsic_entry_specific = sum(
        1 for r in passed if r.category != "Stackelberg" and r.entry_specific
    )
    contract_specific = sum(
        1 for r in passed if r.category == "Contract" and r.entry_specific
    )
    contract_template = sum(
        1 for r in passed if r.category == "Contract" and not r.entry_specific
    )
    sos_verified   = sum(1 for r in passed if r.track == 2)
    dreal_verified = sum(1 for r in passed if r.track == 3)
    bic_verified   = sum(1 for r in passed if r.track == 4)

    print(f"\n{'=' * 64}")
    print(f"  Multi-Track Verification Summary  ({total} entries checked)")
    print(f"{'=' * 64}")
    for v in ("VERIFIED", "VERIFIED_TEMPLATE", "VERIFIED_SHAPE",
              "COUNTEREXAMPLE", "UNKNOWN", "UNSUPPORTED"):
        n = counts[v]
        if n:
            bar = "█" * min(n, 40)
            print(f"  {v:<18} {bar}  ({n})")
    if counts["VERIFIED_TEMPLATE"]:
        print(f"  NOTE: VERIFIED_TEMPLATE checks a generic structural template for the")
        print(f"        category, not this entry's own math. It is not a proof about")
        print(f"        the specific paper. Only VERIFIED (entry_specific=True) is.")
    if passed:
        vcg_total = len(vcg_results)
        print(f"  ├─ Passed ({len(passed)} total, {dsic_entry_specific + stackelberg_specific} entry-specific):")
        if vcg_total:
            print(f"  │   VCG ({vcg_total}): {vcg_confirmed} form-confirmed"
                  f" [clarke={vcg_form_counts['clarke_pivot']}"
                  f" marginal={vcg_form_counts['marginal_welfare']}"
                  f" threshold={vcg_form_counts['critical_bid']}]"
                  f", {vcg_total - vcg_confirmed} template-only")
            if vcg_grid_bounded:
                print(f"  │   VCG DSIC (grid-exact): {vcg_grid_bounded}")
        if contract_specific or contract_template:
            print(f"  │   Contract entry-specific (LaTeX utility):   {contract_specific}")
            print(f"  │   Contract template (linear-cost model):     {contract_template}")
        if sos_verified:
            print(f"  │   SOS certificate (Track 2, poly degree≥2):  {sos_verified}")
        if bic_verified:
            print(f"  │   Bayesian IC (Track 4, symbolic integral):  {bic_verified}")
        if stackelberg_passed:
            print(f"  └─ Stackelberg equilibrium IR (NOT DSIC): {len(stackelberg_passed)}"
                  f" ({stackelberg_specific} entry-specific,"
                  f" {len(stackelberg_passed) - stackelberg_specific} template-only)")
        if dreal_verified:
            print(f"  dReal δ-verified (Track 3, transcendental):   {dreal_verified}")
    if shape_only:
        print(f"  ·  VCG regex-shape only (not a proof): {len(shape_only)}"
              f"  [structural form match; no solver run on the entry]")
    print(f"{'=' * 64}\n")

    for r in results:
        if r.verdict not in ("VERIFIED", "VERIFIED_TEMPLATE", "VERIFIED_SHAPE", "UNSUPPORTED"):
            print(r)
            print()

    manual = [r for r in results if r.verdict == "MANUAL"]
    if manual:
        bar = "█" * min(len(manual), 40)
        print(f"  MANUAL            {bar}  ({len(manual)})")
        print("\n  ## Diagnosed (MANUAL)")
        for r in manual:
            print(f"  - {r.paper_id}: {r.notes}")
        try:
            with open(backlog_path) as fh:
                blob = fh.read()
        except OSError:
            blob = ""
        missing = [r.paper_id for r in manual if r.paper_id not in blob]
        if missing:
            print(f"  ⚠️  MANUAL entries missing from MANUAL-backlog.md: "
                  f"{', '.join(missing)}")

    flagged = [r for r in results if "RECONCILE-FLAG" in (r.notes or "")]
    if flagged:
        print(f"\n  ## Needs review ({len(flagged)} LLM/LaTeX verdict conflicts)")
        for r in flagged:
            tag = r.notes[r.notes.index("RECONCILE-FLAG"):]
            print(f"  - {r.paper_id}: {tag}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-track FL incentive mechanism verifier"
    )
    parser.add_argument("input", type=Path,
                        help="Single entry .json, directory of entries, or corpus.json")
    parser.add_argument("--gold", action="store_true",
                        help="Batch: only verify gold-tier entries")
    parser.add_argument("--verbose", action="store_true",
                        help="Print full result for every entry")
    args = parser.parse_args()

    if not args.input.exists():
        sys.exit(f"Not found: {args.input}")

    if args.input.is_dir():
        results = verify_corpus(args.input, gold_only=args.gold)
        if args.verbose:
            for r in results:
                print(r)
                print()
        print_summary(results)

    else:
        data = json.loads(args.input.read_text())
        if isinstance(data, list):
            entries = data
            if args.gold:
                entries = [e for e in entries if e.get("quality_tier") == "gold"]
            results = [
                verify(e) for e in entries
                if e.get("category") not in _RAG_ONLY
            ]
            if args.verbose:
                for r in results:
                    print(r)
                    print()
            print_summary(results)
        else:
            result = verify(data)
            print(result)


if __name__ == "__main__":
    main()
