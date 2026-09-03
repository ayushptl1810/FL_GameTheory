# tests/verifier/test_manual_override.py
import pytest
from verifier import verify


def _manual_entry():
    return {
        "paper_id": "m1", "category": "Contract",
        "mechanism": {"ic_screening_latex": "x", "ir_participation_latex": "y"},
        "verdict_override": "MANUAL",
        "manual_diagnosis": {
            "round": "R3a", "track": 3,
            "limit": "> _MAX_BOX_DIMS = 6 free variables after reduction",
            "mechanism": "multi-type transcendental contract with log effort cost",
            "obstruction": "7 free vars after reduction; interval B&B intractable",
            "human_task": "apply adjacent-IC reduction by hand and re-run Track 3 per pair",
            "date": "2026-09-10",
        },
    }


def test_manual_override_returns_manual_verdict():
    r = verify(_manual_entry())
    assert r.verdict == "MANUAL"
    assert r.category == "Contract" and r.paper_id == "m1"
    assert r.track == 3
    assert "_MAX_BOX_DIMS" in r.notes
    assert r.entry_specific is False


def test_manual_override_ignores_stored_ast_and_latex(monkeypatch):
    import verifier as V
    called = {"latex": False, "ast": False}
    monkeypatch.setattr(V, "_verify_latex", lambda e: called.__setitem__("latex", True))
    monkeypatch.setattr(V, "verify_from_ast", lambda *a, **k: called.__setitem__("ast", True))
    e = _manual_entry()
    e["formalized_ast"] = {"t": "Mechanism"}
    r = verify(e)
    assert r.verdict == "MANUAL"
    assert called == {"latex": False, "ast": False}


def test_non_manual_override_is_ignored():
    e = _manual_entry()
    e["verdict_override"] = "SOMETHING_ELSE"
    e.pop("formalized_ast", None)
    r = verify(e)
    assert r.verdict != "MANUAL"
