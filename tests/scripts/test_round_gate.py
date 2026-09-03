import pytest
from scripts.round_gate import gate, RANK


def test_template_to_verified_is_improvement():
    ok, msgs = gate({"c1": "VERIFIED_TEMPLATE"}, [{"paper_id": "c1", "verdict": "VERIFIED"}])
    assert ok is True and any("improved c1" in m for m in msgs)


def test_shape_to_manual_is_improvement():
    ok, _ = gate({"v1": "VERIFIED_SHAPE"}, [{"paper_id": "v1", "verdict": "MANUAL"}])
    assert ok is True


def test_template_to_unknown_is_regression():
    ok, msgs = gate({"c1": "VERIFIED_TEMPLATE"}, [{"paper_id": "c1", "verdict": "UNKNOWN"}])
    assert ok is False and any("REGRESSION c1" in m for m in msgs)


def test_verified_to_anything_worse_is_regression():
    ok, _ = gate({"v1": "VERIFIED"}, [{"paper_id": "v1", "verdict": "MANUAL"}])
    assert ok is False


def test_counterexample_is_pass_with_note():
    ok, msgs = gate({"v1": "VERIFIED_TEMPLATE"}, [{"paper_id": "v1", "verdict": "COUNTEREXAMPLE"}])
    assert ok is True and any("needs hand-checked justification" in m for m in msgs)


def test_unrelated_entry_ignored():
    ok, _ = gate({"v1": "VERIFIED_SHAPE"}, [{"paper_id": "other", "verdict": "UNKNOWN"}])
    assert ok is True
