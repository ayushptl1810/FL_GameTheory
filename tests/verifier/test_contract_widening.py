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

Task 11-pre UPDATE: one of the three class-(a) pins -- Wen2025diffusion_contract
-- was re-examined and found NOT to be a genuine ambiguity. Its sole blocker was
the `(\theta_k^1)` menu-item indexation tag, identical on every term and
carrying no functional dependence. Stripping it (`_strip_call_args_on_powers`)
yields the textbook screening shape, and the entry is now a legitimate
entry-specific VERIFIED; its test asserts that structure instead of a
fail-closed pin. The expectation-notation and `n-1`-arithmetic pins stand
unchanged, and both remain genuine fail-closed cases.
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


def test_superscript_label_ir_parses_after_arg_stripping():
    """(a) Wen2025: IR LHS `\\theta_i^2 R_i^2(\\theta_k^1) - cT_i^2(...) - E`.

    Task 11 pinned this fail-closed because of an apparent `^2`
    stage-index / power ambiguity. Task 11-pre resolved it: the only real
    blocker was the `(\\theta_k^1)` menu-item indexation tag, which appears
    IDENTICALLY on every second-stage term and is not a functional
    dependence (`_strip_call_args_on_powers`). With it removed the entry
    parses to the textbook screening shape -- type `i` held fixed on both
    sides, contract index varying `i` -> `j`:

        IR  : theta_i^2 R_i^2 - c T_i^2 - E
        RHS : theta_i^2 R_j^2 - c T_j^2 - E

    The `^2` is a genuine squaring, applied uniformly to both sides, so the
    IC gap is preserved under either reading. The soundness gate still
    applies: the RHS must carry the deviating type's subscript.
    """
    from tracks.track1_z3 import _parse_contract_entry

    parsed = _parse_contract_entry(_entry("Wen2025diffusion_contract"))
    assert parsed is not None, "expected the arg-stripped IR/IC to parse"
    _U_ir, U_rhs, type_sub, contract_sub, _n, _from_lhs = parsed
    assert type_sub != contract_sub, (type_sub, contract_sub)
    # Soundness: the deviating-contract utility must still depend on the
    # TRUE type, else the obligation says nothing about incentives.
    assert any(
        str(s).startswith("theta_") and type_sub in str(s)
        for s in U_rhs.free_symbols
    ), sorted(map(str, U_rhs.free_symbols))

    res = verify(_entry("Wen2025diffusion_contract"))
    assert res.verdict == "VERIFIED", res.verdict


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
