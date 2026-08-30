r"""Phase 3 / Task 12 — Stackelberg parser widening: set/inequality \sum bounds.

`_try_stackelberg_latex` now pre-processes `\sum_{i \in S} f(i)` /
`\sum_{a \le i \le b} f(i)` bounds that SymPy's `parse_latex` cannot read,
isolating the follower's own term as `f(self) + \Xi_k` where `\Xi_k` is a
fresh OPAQUE symbol constant w.r.t. the follower's own decision.

The danger the widening must not realise: a wrong own-term isolation ->
a silently wrong FOC -> a false entry-specific VERIFIED. Two guards:

  1. The opaque split is only applied when the rest-of-sum is genuinely
     independent of `self` (separability of the summand).
  2. Whenever the split fires, an entry-specific VERIFIED additionally
     requires the paper's own `best_response_latex` to confirm the derived
     FOC (definite cross-check MATCH). No MATCH -> fall through.

Corpus outcome (see .superpowers/sdd/.../task-12-report.md): 0 corpus
Stackelberg entries flip to entry-specific VERIFIED -- every one fails a
soundness guard (vector decision, un-cross-checkable piecewise best
response, opaque auxiliary function, or nested/unparseable structure).
Widening + tests land with 0 clean flips, as the plan permits.
"""
import json
import pathlib

import pytest

from tracks.track1_z3 import (
    _LATEX_OK,
    _preprocess_stackelberg_sum_bounds,
    verify_stackelberg,
)

pytestmark = pytest.mark.skipif(
    not _LATEX_OK, reason="sympy latex parser unavailable"
)

_CORPUS = json.loads(
    (pathlib.Path(__file__).resolve().parents[2] / "corpus.json").read_text()
)

_UNSOUND = {"VERIFIED", "COUNTEREXAMPLE"}


def _entry(mechanism: dict, paper_id: str = "synthetic") -> dict:
    return {"paper_id": paper_id, "category": "Stackelberg", "mechanism": mechanism}


# ── transform unit checks ────────────────────────────────────────────────

def test_separable_set_sum_splits_off_own_term():
    raw = r"U_i = \sum_{j \in S} a_j x_j - b_i x_i"
    out, n = _preprocess_stackelberg_sum_bounds(raw, r"x_i")
    assert n == 1
    assert r"\sum" not in out
    assert "x_i" in out and "\\Xi_{0}" in out


def test_inequality_bound_is_handled():
    raw = r"U_i = \sum_{1 \le j \le J} a_j x_j"
    out, n = _preprocess_stackelberg_sum_bounds(raw, r"x_i")
    assert n == 1 and r"\sum" not in out


def test_self_inside_summand_unindexed_bails():
    # `self` (x_i) appears INSIDE the summand not carried by the sum index
    # -> the "rest" (j != i terms) still depends on x_i, so the opaque
    # split would drop a real x_i-dependence: must bail.
    raw = r"U_i = \sum_{j \in S} x_i x_j - k_i x_i^2"
    assert _preprocess_stackelberg_sum_bounds(raw, r"x_i") is None


def test_self_times_whole_sum_is_still_separable():
    # x_i * sum_j x_j = x_i^2 + x_i * (sum over j != i). The rest is still
    # constant w.r.t. x_i, so d/dx_i is exact -> the split is allowed.
    raw = r"U_i = x_i \sum_{j \in S} x_j"
    out, n = _preprocess_stackelberg_sum_bounds(raw, r"x_i")
    assert n == 1 and "\\Xi_{0}" in out and "x_i" in out


def test_share_denominator_keeps_self_explicit():
    # x_i / (sum_j x_j): x_i is in the denominator sum (i in S). The split
    # must keep x_i explicit in the denominator, not fold it into \Xi.
    raw = r"U_i = \frac{x_i}{\sum_{j \in S} x_j} R"
    out, n = _preprocess_stackelberg_sum_bounds(raw, r"x_i")
    assert n == 1
    assert r"\frac{x_i}{( ( x_i ) + \Xi_{0} )}" in out


def test_no_follower_symbol_bails():
    raw = r"U_i = \sum_{j \in S} a_j x_j"
    assert _preprocess_stackelberg_sum_bounds(raw, None) is None


def test_parenthesised_summand_bails():
    # `a_j (x_j + x_i)`: a top-level '+' inside the parens would truncate
    # the summand scan, hiding the x_i coupling term. Must bail (the true
    # FOC has an x_i-dependent rest-of-sum -> opaque split is unsound).
    raw = r"U_i = \sum_{j \in N} a_j (x_j + x_i) - k x_i^2"
    assert _preprocess_stackelberg_sum_bounds(raw, r"x_i") is None


def test_parenthesised_summand_entry_does_not_verify():
    entry = _entry({
        "equilibrium_existence": True,
        "follower_utility_latex":
            r"U_i = \sum_{j \in N} a_j (x_j + x_i) - k x_i^2",
        "follower_decision": r"contribution \( x_i \)",
        "best_response_latex": r"x_i^* = \frac{a_i + 1}{2 k}",
    })
    res = verify_stackelberg(entry)
    assert not (res.entry_specific and res.verdict in _UNSOUND), res.verdict
    assert res.verdict in {"VERIFIED_TEMPLATE", "UNKNOWN", "UNSUPPORTED"}


def test_literal_xi_in_utility_bails():
    # A pre-existing \Xi_{0} in the utility must not merge with the
    # injected rest-of-sum symbol.
    raw = r"U_i = \Xi_{0} x_i + \sum_{j \in S} a_j x_j - k x_i^2"
    assert _preprocess_stackelberg_sum_bounds(raw, r"x_i") is None


def test_literal_xi_entry_does_not_verify():
    entry = _entry({
        "equilibrium_existence": True,
        "follower_utility_latex":
            r"U_i = \Xi_{0} x_i + \sum_{j \in S} a_j x_j - k x_i^2",
        "follower_decision": r"contribution \( x_i \)",
        "best_response_latex": r"x_i^* = \frac{a_i + \Xi_{0}}{2 k}",
    })
    res = verify_stackelberg(entry)
    assert not (res.entry_specific and res.verdict in _UNSOUND), res.verdict


def test_ordinary_numeric_bound_is_left_untouched():
    raw = r"U_i = \sum_{j=1}^{M} a_j x_j"
    out, n = _preprocess_stackelberg_sum_bounds(raw, r"x_i")
    assert n == 0 and out == raw


# ── end-to-end verdicts on synthetic fixtures ───────────────────────────

def test_separable_set_sum_with_matching_best_response_verifies():
    r"""Follower i picks x_i to maximise
        U_i = p_i x_i - k_i x_i^2 + \sum_{j \in S} c_j x_j
    The sum over j is separable; its j != i part is an opaque POSITIVE
    constant (\Xi_0) to follower i, its j=i part contributes + c_i x_i.
    FOC: p_i + c_i - 2 k_i x_i = 0  =>  x_i* = (p_i + c_i) / (2 k_i),
    stated verbatim as best_response_latex (cross-check MATCHes), and
    U*(x_i*) = (p_i + c_i)^2 / (4 k_i) + \Xi_0 >= 0 for positive params.
    -> a real entry-specific VERIFIED."""
    entry = _entry({
        "equilibrium_existence": True,
        "follower_utility_latex":
            r"U_i = p_i x_i - k_i x_i^2 + \sum_{j \in S} c_j x_j",
        "follower_decision": r"contribution level \( x_i \)",
        "best_response_latex": r"x_i^* = \frac{p_i + c_i}{2 k_i}",
    })
    res = verify_stackelberg(entry)
    assert res.entry_specific is True
    assert res.verdict == "VERIFIED"
    assert "cross-check: MATCH" in res.notes


def test_coupled_rest_of_sum_never_verifies():
    r"""Here the 'rest of the sum' genuinely depends on x_i:
        U_i = \sum_{j \in S} x_i x_j - k_i x_i^2
    An opaque split (rest independent of x_i) would give a WRONG FOC and a
    spurious verdict. The transform must bail -> no entry-specific
    VERIFIED/COUNTEREXAMPLE."""
    entry = _entry({
        "equilibrium_existence": True,
        "follower_utility_latex": r"U_i = \sum_{j \in S} x_i x_j - k_i x_i^2",
        "follower_decision": r"contribution level \( x_i \)",
        "best_response_latex": r"x_i^* = \frac{S_{tot}}{2 k_i}",
    })
    res = verify_stackelberg(entry)
    if res.entry_specific:
        assert res.verdict not in _UNSOUND, res.verdict
    assert res.verdict in {"VERIFIED_TEMPLATE", "UNKNOWN", "UNSUPPORTED"}


def test_opaque_split_without_cross_check_falls_through():
    """Same separable utility as the positive case but NO best_response_latex
    to confirm the FOC. The opaque-sum widening requires a definite
    cross-check MATCH, so this must NOT produce an entry-specific verdict."""
    entry = _entry({
        "equilibrium_existence": True,
        "follower_utility_latex":
            r"U_i = p_i x_i - k_i x_i^2 - \sum_{j \in S} c_j x_j",
        "follower_decision": r"contribution level \( x_i \)",
    })
    res = verify_stackelberg(entry)
    assert not (res.entry_specific and res.verdict in _UNSOUND)
    assert res.verdict in {"VERIFIED_TEMPLATE", "UNKNOWN", "UNSUPPORTED"}


# ── corpus regression pins ──────────────────────────────────────────────

_SET_INEQ_SUM_ENTRIES = [
    "1811_12082", "2101_12428", "2110_12876", "2101_05628",
    "2103_05866", "Hu2020trading", "Li2025split",
]


@pytest.mark.parametrize("paper_id", _SET_INEQ_SUM_ENTRIES)
def test_corpus_set_ineq_sum_entries_fail_closed(paper_id):
    """No corpus Stackelberg entry with a set/inequality \\sum bound may be
    certified via the widening without a cross-validated best response.
    Currently every one fails a soundness guard -> template / no verdict."""
    entry = next((e for e in _CORPUS if e.get("paper_id") == paper_id), None)
    if entry is None:
        pytest.skip(f"{paper_id} not in corpus")
    res = verify_stackelberg(entry)
    if res.entry_specific:
        assert res.verdict not in _UNSOUND, (
            f"{paper_id} produced a guessed entry-specific {res.verdict}"
        )


def test_stackelberg_entry_specific_count_not_below_baseline():
    """Task 12 baseline: exactly 1 Stackelberg entry-specific pass. The
    widening may only raise this; a drop means a regression."""
    n = sum(
        1
        for e in _CORPUS
        if "stackelberg" in json.dumps(e).lower()
        and e.get("mechanism", {}).get("equilibrium_existence")
        and (r := verify_stackelberg(e)).entry_specific
        and r.verdict in {"VERIFIED", "COUNTEREXAMPLE"}
    )
    assert n >= 1, f"Stackelberg entry-specific passes dropped to {n}"
