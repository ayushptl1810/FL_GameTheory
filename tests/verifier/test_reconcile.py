import pytest
from verifier import _reconcile, VerificationResult


def _r(verdict, *, entry_specific=False, notes=""):
    return VerificationResult(verdict=verdict, category="Contract",
                              paper_id="x", track=1, notes=notes,
                              entry_specific=entry_specific)


@pytest.mark.parametrize("latex_v", ["VERIFIED_TEMPLATE", "VERIFIED_SHAPE",
                                     "UNKNOWN", "UNSUPPORTED"])
def test_llm_verified_upgrades(latex_v):
    chosen, flagged = _reconcile(_r("VERIFIED", entry_specific=True), _r(latex_v))
    assert chosen.verdict == "VERIFIED" and flagged is False


@pytest.mark.parametrize("latex_v", ["VERIFIED_TEMPLATE", "UNKNOWN"])
def test_llm_counterexample_upgrades_flagged(latex_v):
    chosen, flagged = _reconcile(_r("COUNTEREXAMPLE"), _r(latex_v))
    assert chosen.verdict == "COUNTEREXAMPLE" and flagged is True


def test_agree_on_verified():
    chosen, flagged = _reconcile(_r("VERIFIED", entry_specific=True),
                                 _r("VERIFIED", entry_specific=True))
    assert chosen.verdict == "VERIFIED" and flagged is False


@pytest.mark.parametrize("llm_v", ["COUNTEREXAMPLE", "UNKNOWN", "UNSUPPORTED"])
def test_existing_verified_sticky_flagged(llm_v):
    chosen, flagged = _reconcile(_r(llm_v), _r("VERIFIED", entry_specific=True))
    assert chosen.verdict == "VERIFIED" and flagged is True
    assert "RECONCILE-FLAG" in chosen.notes


def test_existing_counterexample_vs_llm_verified_flagged():
    chosen, flagged = _reconcile(_r("VERIFIED", entry_specific=True),
                                 _r("COUNTEREXAMPLE"))
    assert chosen.verdict == "COUNTEREXAMPLE" and flagged is True


def test_llm_unknown_no_improvement_keeps_latex():
    chosen, flagged = _reconcile(_r("UNKNOWN"), _r("VERIFIED_TEMPLATE"))
    assert chosen.verdict == "VERIFIED_TEMPLATE" and flagged is False


def test_latex_counterexample_llm_unknown_keeps_latex():
    chosen, flagged = _reconcile(_r("UNKNOWN"), _r("COUNTEREXAMPLE"))
    assert chosen.verdict == "COUNTEREXAMPLE" and flagged is False


from architect.ast import Mechanism, Sym, to_dict
from verifier import verify


def test_verify_uses_stored_ast(monkeypatch):
    import verifier as V
    m = Mechanism(category="Contract", utility=Sym("u"), payment=Sym("P"),
                  ic=Sym("g"), ir=Sym("u"))
    entry = {"paper_id": "z", "category": "Contract",
             "mechanism": {"ic_screening_latex": "x", "ir_participation_latex": "y"},
             "formalized_ast": to_dict(m)}
    monkeypatch.setattr(V, "_verify_latex", lambda e: _r("VERIFIED_TEMPLATE"))
    monkeypatch.setattr(V, "verify_from_ast",
                        lambda *a, **k: _r("VERIFIED", entry_specific=True))
    out = verify(entry)
    assert out.verdict == "VERIFIED"


def test_verify_corrupt_stored_ast_falls_back(monkeypatch):
    import verifier as V
    entry = {"paper_id": "z", "category": "Contract",
             "mechanism": {"ic_screening_latex": "x", "ir_participation_latex": "y"},
             "formalized_ast": {"t": "Bogus"}}
    monkeypatch.setattr(V, "_verify_latex", lambda e: _r("VERIFIED_TEMPLATE"))
    out = verify(entry)
    assert out.verdict == "VERIFIED_TEMPLATE"


from verifier import print_summary


def test_print_summary_lists_reconcile_flags(capsys):
    flagged = _r("VERIFIED", entry_specific=True,
                 notes="grid-exact | RECONCILE-FLAG: LaTeX=COUNTEREXAMPLE LLM=VERIFIED")
    flagged.paper_id = "conflict_entry"
    clean = _r("VERIFIED", entry_specific=True, notes="grid-exact")
    print_summary([flagged, clean])
    out = capsys.readouterr().out
    assert "Needs review" in out
    assert "conflict_entry" in out
    assert "RECONCILE-FLAG" in out


def test_print_summary_no_flag_block_when_none(capsys):
    print_summary([_r("VERIFIED", entry_specific=True, notes="grid-exact")])
    out = capsys.readouterr().out
    assert "Needs review" not in out
