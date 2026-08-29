"""
Shared types for the multi-track FL incentive mechanism verifier.

Track routing:
  Track 1 — Z3          linear / discrete-type mechanisms   (exact, fast)
  Track 2 — SOS/CVXPY   polynomial utilities (deg ≥ 2)      (exact certificate)
  Track 3 — dReal        transcendental (ln, exp, sigmoid)   (δ-sound)
  Track 4 — SymPy        Bayesian IC (expectation form)      (exact symbolic)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# VERIFIED          — the paper's own utility/payment/IC/IR LaTeX was parsed
#                      and checked; this is a proof about *this* mechanism.
# VERIFIED_TEMPLATE — no proof against the paper's own math was possible, so
#                      a generic structural template for the category was
#                      checked instead. Passing means the template is
#                      internally consistent — it says nothing about whether
#                      this specific paper's mechanism is IC/IR.
# COUNTEREXAMPLE    — a violation was found (entry-specific or template).
# UNKNOWN           — solver/parse inconclusive.
# UNSUPPORTED       — no verifier attempted for this category/track.
Verdict = Literal[
    "VERIFIED", "VERIFIED_TEMPLATE", "COUNTEREXAMPLE", "UNKNOWN", "UNSUPPORTED"
]


def strip_redundant_outer_parens(s: str) -> str:
    """Strip a matched outer "(...)" wrapping the whole string -- e.g.
    "(U_i - U_j)" -> "U_i - U_j" -- without touching a trailing ")" that
    closes an inner function call, e.g. "r_i \\ln(1/theta_i)" must be left
    alone (blind str.strip("()") corrupts it into "r_i \\ln(1/theta_i").
    """
    if not (s.startswith("(") and s.endswith(")")):
        return s
    depth = 0
    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and i != len(s) - 1:
                return s  # closes before the end -- not a single wrapping pair
    return s[1:-1]


def normalize_left_right(s: str) -> str:
    """Replace \\left(/\\right) and bracket/brace variants with their plain
    equivalents, instead of deleting them outright.

    Pre-existing bug found 2026-07-17: every track's LaTeX-cleaning helper
    did `s.replace(r"\\left(", "")` -- which deletes the "(" character
    along with the "\\left" prefix, not just the size-modifier. This
    silently destroys grouping: "A \\left(B + C\\right)" (a coefficient
    times a parenthesized sum -- extremely common) became "A B + C"
    instead of "A(B + C)", changing the parsed expression's meaning
    without raising any error. Caught via a best_response_latex
    cross-check disagreement on a live corpus entry.
    """
    for open_tok, open_ch in ((r"\left(", "("), (r"\left[", "["), (r"\left\{", "{")):
        s = s.replace(open_tok, open_ch)
    for close_tok, close_ch in ((r"\right)", ")"), (r"\right]", "]"), (r"\right\}", "}")):
        s = s.replace(close_tok, close_ch)
    # Bare \left / \right (e.g. before an invisible delimiter "\left.") --
    # no visible bracket character to preserve.
    return s.replace(r"\left", "").replace(r"\right", "")


def finalize_verdict(all_ok: bool, has_cex: bool, entry_specific: bool) -> Verdict:
    """Combine per-condition results and entry_specific status into one Verdict.

    Centralizes the entry_specific downgrade so no track can accidentally
    report VERIFIED for a generic template check that never touched the
    paper's own math.
    """
    if all_ok:
        return "VERIFIED" if entry_specific else "VERIFIED_TEMPLATE"
    if has_cex:
        return "COUNTEREXAMPLE"
    return "UNKNOWN"


@dataclass
class VerificationResult:
    verdict: Verdict
    category: str
    paper_id: str
    track: int = 0
    conditions: list[str] = field(default_factory=list)
    counterexample: dict[str, str] | None = None
    notes: str = ""
    entry_specific: bool = False
    coalition_ic_k: int | None = None

    def __str__(self) -> str:
        tick = "✓" if self.verdict in ("VERIFIED", "VERIFIED_TEMPLATE") else "·"
        lines = [
            f"{'─' * 60}",
            f"Paper    : {self.paper_id}",
            f"Category : {self.category}",
            f"Track    : {self.track}",
            f"Verdict  : {self.verdict}",
        ]
        for c in self.conditions:
            lines.append(f"  {tick} {c}")
        if self.counterexample:
            lines.append("Counterex:")
            for k, v in self.counterexample.items():
                lines.append(f"    {k} = {v}")
        if self.notes:
            lines.append(f"Notes    : {self.notes}")
        return "\n".join(lines)
