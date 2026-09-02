# tests/architect/test_formalize_cli.py
import json
import pytest
from architect.formalize import run_batch, FormalizeResult
import architect.formalize as F
from architect.ast import Mechanism, Sym


def _corpus(tmp_path):
    data = [
        {"paper_id": "aaa", "category": "Contract",
         "mechanism": {"ic_screening_latex": "x", "ir_participation_latex": "y"}},
        {"paper_id": "bbb", "category": "VCG",
         "mechanism": {"payment_rule_latex": "p"}},
    ]
    p = tmp_path / "corpus.json"
    p.write_text(json.dumps(data))
    return str(p)


def _stub_verified(monkeypatch):
    monkeypatch.setattr(F, "pdf_text", lambda *a, **k: None)
    m = Mechanism(category="Contract", utility=Sym("u"), payment=Sym("P"),
                  ic=Sym("g"), ir=Sym("u"))
    monkeypatch.setattr(
        F, "formalize_with_retry",
        lambda entry, txt, **k: FormalizeResult("VERIFIED", m, [[]], 0, False, ""),
    )


def test_run_batch_writes_ast_and_meta(tmp_path, monkeypatch):
    _stub_verified(monkeypatch)
    cp = _corpus(tmp_path)
    out = run_batch(cp, ids=["aaa"], today="2026-08-31")
    data = json.loads(open(cp).read())
    aaa = next(e for e in data if e["paper_id"] == "aaa")
    bbb = next(e for e in data if e["paper_id"] == "bbb")
    assert aaa["formalized_ast"]["t"] == "Mechanism"
    assert aaa["formalization_meta"]["verdict"] == "VERIFIED"
    assert aaa["formalization_meta"]["date"] == "2026-08-31"
    assert "formalized_ast" not in bbb
    assert out["summary"]["verified"] == 1


def test_run_batch_dry_run_does_not_write(tmp_path, monkeypatch):
    _stub_verified(monkeypatch)
    cp = _corpus(tmp_path)
    before = open(cp).read()
    run_batch(cp, ids=["aaa"], dry_run=True, today="2026-08-31")
    assert open(cp).read() == before


def test_run_batch_report_has_human_queue(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "pdf_text", lambda *a, **k: None)
    monkeypatch.setattr(
        F, "formalize_with_retry",
        lambda entry, txt, **k: FormalizeResult(
            "UNKNOWN", None, [], 1, False, "adversary still flagged after retry"),
    )
    cp = _corpus(tmp_path)
    out = run_batch(cp, only="Contract", today="2026-08-31")
    report = open(out["report_path"]).read()
    assert "## Human queue" in report
    assert "aaa" in report
    assert out["summary"]["unknown"] == 1


def test_run_batch_only_filters_by_category(tmp_path, monkeypatch):
    _stub_verified(monkeypatch)
    cp = _corpus(tmp_path)
    out = run_batch(cp, only="VCG", today="2026-08-31")
    assert out["summary"]["selected"] == 1
