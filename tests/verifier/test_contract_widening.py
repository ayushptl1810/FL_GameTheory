r"""Phase 3 / Task 11 — Contract parser widening for entry-specific LaTeX.

Task 11 scoped three widening classes for `_parse_contract_entry` /
`_contract_check_core`:

  (a) >=2 distinct type-subscripts on the IR LHS,
  (b) `\sum_{j}`-style aggregation over the contract menu,
  (c) `n-1` index arithmetic in the IC RHS instead of a 2nd index symbol.

Investigation outcome (see .superpowers/sdd/.../task-11-report.md): NO corpus
Contract entry can be flipped to a cross-validated VERIFIED through any of
these three classes without loosening a soundness gate:

  * `\sum` menu aggregation  -> 0 corpus Contract entries use it in IC/IR.
  * `n-1` arithmetic         -> exactly one entry (Kang2022blockchain_metaverse),
                                and it states ADJACENT-only IC; certifying it
                                needs adjacent-IC semantics + subscript index
                                arithmetic, a soundness-sensitive rework.
  * >=2 subscripts           -> every affected entry independently fails closed
                                on expectation notation (E[...]), opaque
                                multi-argument functions, spurious function-call
                                args, or superscript-label ambiguity (`R_i^2`,
                                `r_i^L`).

So Task 11 lands as "widening investigation + regression pins, 0 clean flips"
(explicitly permitted by the plan). These tests pin the CURRENT fail-closed
behavior on one representative entry per class, with real IC/IR verdict
assertions, so Tasks 12/13 (which also touch track1_z3.py) cannot silently
regress them into a guessed VERIFIED / COUNTEREXAMPLE.

Task 11-pre CONFIRMED all three pins after a failed attempt to lift the
Wen2025diffusion_contract one. Stripping its `(\theta_k^1)` call args as a
"menu-item indexation tag" does make the entry parse and report VERIFIED --
but on the WRONG obligation: the paper's utility (Eq. 6) is linear
(`u_n = theta_n R_n - c T_n - E`) and every `^2`/`^1` in its IC/IR is a
PERIOD index, not an exponent. The widening was reverted. Treat a superscript
in this corpus as a period/stage label until the paper says otherwise.
"""
import json
import pathlib

from verifier import verify

_CORPUS = json.loads(
    (pathlib.Path(__file__).resolve().parents[2] / "corpus.json").read_text()
)


def _entry(paper_id: str) -> dict:
    for e in _CORPUS:
        if e.get("paper_id") == paper_id:
            return e
    raise AssertionError(f"corpus entry {paper_id!r} not found")


# A guessed positive verdict on any of these would be a soundness failure.
_UNSOUND = {"VERIFIED", "COUNTEREXAMPLE"}
_ACCEPTED_FALLBACK = {"VERIFIED_TEMPLATE", "UNKNOWN", "UNSUPPORTED"}


def test_n_minus_1_arithmetic_ic_does_not_produce_guessed_verdict():
    """(c) `R_{n-1} - 1/theta_{n-1}` on the IC RHS: no separate menu index
    symbol, adjacent-only IC. The parser must NOT emit an entry-specific
    VERIFIED/COUNTEREXAMPLE (it currently bails to the linear-cost template)."""
    res = verify(_entry("Kang2022blockchain_metaverse"))
    if res.entry_specific:
        assert res.verdict not in _UNSOUND, (
            "n-1 arithmetic IC produced a guessed entry-specific verdict "
            f"({res.verdict}); expected fail-closed"
        )
    assert res.verdict in _ACCEPTED_FALLBACK, res.verdict


def test_two_subscript_ir_with_expectation_notation_fails_closed():
    """(a) IR `E_{c_{-i}}[U_i(c_i, c_{-i})]` -> {c, i} subscripts AND
    unparseable expectation notation. Must fail closed."""
    res = verify(_entry("2602_21844"))
    if res.entry_specific:
        assert res.verdict not in _UNSOUND, (
            f"expectation-notation IR produced {res.verdict}; expected fail-closed"
        )
    assert res.verdict in _ACCEPTED_FALLBACK, res.verdict


def test_two_subscript_ir_with_superscript_label_fails_closed():
    """(a) Wen2025: IR LHS `\\theta_i^2 R_i^2(\\theta_k^1) - cT_i^2(...) - E`
    -> {i, k} subscripts, plus `^2` stage-index / power ambiguity and
    spurious function-call args. Must fail closed.

    The superscripts here are PERIOD indices, not exponents: the paper's
    utility (Eq. 6) is the LINEAR `u_n = theta_n R_n - c T_n - E`, and Eqs.
    13-14 restate it under the headings "IR/IC Constraints in Period 2",
    so `theta_i^2 R_i^2` means "period-2 theta times period-2 R". The
    corpus `contract_menu_latex` uses the same superscript-before-subscript
    period ordering, and this entry's `notes` field records that the
    transcription is "the PERIOD-2 static myopic IC/IR only".

    Reading those `^2`s as squaring would hand Z3
    `theta_i^2 R_i^2 - c T_i^2 >= theta_i^2 R_j^2 - c T_j^2`, a DIFFERENT
    proof obligation from the paper's linear
    `theta_i R_i - c T_i >= theta_i R_j - c T_j`. A VERIFIED on that would
    not certify the paper's contract, so the parse must decline.
    """
    res = verify(_entry("Wen2025diffusion_contract"))
    if res.entry_specific:
        assert res.verdict not in _UNSOUND, (
            f"superscript-label IR produced {res.verdict}; expected fail-closed"
        )
    assert res.verdict in _ACCEPTED_FALLBACK, res.verdict


def test_sum_menu_aggregation_absent_from_contract_corpus():
    """(b) Guard: if a future corpus revision adds `\\sum`-style menu
    aggregation to a Contract IC/IR field, this test fails so the `\\sum`
    widening (expand the finite sum symbolically before `_sp_to_z3`) gets
    implemented and cross-validated rather than silently mis-parsed."""
    offenders = []
    for e in _CORPUS:
        if e.get("category") != "Contract":
            continue
        m = e.get("mechanism") or {}
        for field in ("ic_screening_latex", "ir_participation_latex"):
            if r"\sum" in (m.get(field) or ""):
                offenders.append((e.get("paper_id"), field))
    assert not offenders, (
        "Contract entries now carry \\sum in IC/IR; implement the symbolic "
        f"finite-sum expansion widening (Task 11 class b): {offenders}"
    )


def test_baseline_entry_specific_verified_still_hold():
    """The five Contract entry-specific VERIFIEDs from the Task 11 baseline
    must not regress while track1_z3.py is being widened in Phase 3."""
    expected = {
        "2307_15975",
        "Li2025bayesian_incentive",
        "Lim2020contract_healthcare",
        "Sun2022coded",
        "Tan2025renegotiable_contract",
    }
    got = {
        e["paper_id"]
        for e in _CORPUS
        if e.get("category") == "Contract"
        and (r := verify(e)).entry_specific
        and r.verdict == "VERIFIED"
    }
    assert expected <= got, f"regressed entry-specific VERIFIEDs: {expected - got}"
