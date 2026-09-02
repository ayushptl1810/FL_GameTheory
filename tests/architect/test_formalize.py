import json
import pytest
from architect.ast import Mechanism, Sym, Sum, Const, to_dict
from architect.formalize import formalize_entry


def _entry():
    return {
        "paper_id": "synthetic_contract",
        "category": "Contract",
        "mechanism": {
            "client_utility_latex": r"U = \theta R - P",
            "ic_screening_latex": r"\theta R - P \geq \theta R' - P'",
            "ir_participation_latex": r"\theta R - P \geq 0",
            "num_types": 2,
        },
        "key_assumptions": ["linear cost", "discrete types"],
    }


def _good_ast_json():
    m = Mechanism(
        category="Contract",
        utility=Sum([Sym("thetaR"), Const(-1.0)]),
        payment=Sym("P"), ic=Sym("gap"), ir=Sym("u"),
        meta={"num_types": 2},
    )
    return json.dumps(to_dict(m))


def test_formalize_entry_happy_path():
    calls = []
    def fake_complete(system, user, *, json_mode=False):
        calls.append((system, user, json_mode))
        return _good_ast_json()
    m = formalize_entry(_entry(), "PAPER TEXT HERE", complete=fake_complete)
    assert isinstance(m, Mechanism)
    assert m.category == "Contract"
    assert calls[0][2] is True
    assert "PAPER TEXT HERE" in calls[0][1]


def test_formalize_entry_dict_only_when_pdf_none():
    seen = {}
    def fake_complete(system, user, *, json_mode=False):
        seen["user"] = user
        return _good_ast_json()
    formalize_entry(_entry(), None, complete=fake_complete)
    assert "ic_screening_latex" in seen["user"]
    assert "PAPER TEXT" not in seen["user"]


def test_formalize_entry_malformed_json_returns_none():
    m = formalize_entry(_entry(), None, complete=lambda s, u, *, json_mode=False: "not json{")
    assert m is None


def test_formalize_entry_schema_violation_returns_none():
    bad = json.dumps({"t": "Mechanism", "category": "Contract",
                      "utility": {"t": "Sum", "terms": []},
                      "payment": {"t": "Const", "value": 0.0},
                      "ic": {"t": "Const", "value": 0.0},
                      "ir": {"t": "Const", "value": 0.0}})
    m = formalize_entry(_entry(), None, complete=lambda s, u, *, json_mode=False: bad)
    assert m is None


def test_formalize_entry_passes_concerns_on_retry():
    seen = {}
    def fake_complete(system, user, *, json_mode=False):
        seen["user"] = user
        return _good_ast_json()
    formalize_entry(_entry(), None, complete=fake_complete,
                    concerns=[{"field": "ic", "issue": "dropped the upward IC term"}])
    assert "dropped the upward IC term" in seen["user"]


from architect.formalize import adversary_check
from architect.ast import Mechanism, Sym


def _m():
    return Mechanism(category="Contract", utility=Sym("u"), payment=Sym("P"),
                     ic=Sym("gap"), ir=Sym("u"))


def test_adversary_clean_returns_empty():
    out = adversary_check(_m(), _entry(), None,
                          complete=lambda s, u, *, json_mode=False: '{"concerns": []}')
    assert out == []


def test_adversary_reports_concerns():
    payload = '{"concerns": [{"field": "ic", "issue": "missing downward IC"}]}'
    out = adversary_check(_m(), _entry(), "PAPER",
                          complete=lambda s, u, *, json_mode=False: payload)
    assert out == [{"field": "ic", "issue": "missing downward IC"}]


def test_adversary_broken_output_returns_empty():
    out = adversary_check(_m(), _entry(), None,
                          complete=lambda s, u, *, json_mode=False: "garbage")
    assert out == []


def test_adversary_non_list_concerns_returns_empty():
    out = adversary_check(_m(), _entry(), None,
                          complete=lambda s, u, *, json_mode=False: '{"concerns": "nope"}')
    assert out == []


from architect.formalize import formalize_with_retry, FormalizeResult
import architect.formalize as F
from architect.ast import Mechanism, Sym


class _Res:
    def __init__(self, verdict, notes=""):
        self.verdict = verdict
        self.notes = notes


def _install(monkeypatch, *, asts, verdicts, adv):
    a_it, v_it, d_it = iter(asts), iter(verdicts), iter(adv)
    monkeypatch.setattr(F, "formalize_entry", lambda *a, **k: next(a_it))
    monkeypatch.setattr(F, "verify_from_ast", lambda *a, **k: _Res(next(v_it)))
    monkeypatch.setattr(F, "adversary_check", lambda *a, **k: next(d_it))


def _m(tag="u"):
    return Mechanism(category="Contract", utility=Sym(tag), payment=Sym("P"),
                     ic=Sym("g"), ir=Sym("u"))


def test_retry_verified_clean_first_pass(monkeypatch):
    _install(monkeypatch, asts=[_m()], verdicts=["VERIFIED"], adv=[[]])
    r = formalize_with_retry({"paper_id": "x"}, "pdf")
    assert r.verdict == "VERIFIED" and r.retries == 0 and r.pdf_used is True


def test_retry_none_ast_is_unknown(monkeypatch):
    _install(monkeypatch, asts=[None], verdicts=[], adv=[])
    r = formalize_with_retry({"paper_id": "x"}, None)
    assert r.verdict == "UNKNOWN" and r.ast is None and r.pdf_used is False


def test_retry_adversary_flags_then_clean(monkeypatch):
    _install(monkeypatch, asts=[_m("a"), _m("b")],
             verdicts=["VERIFIED", "VERIFIED"],
             adv=[[{"field": "ic", "issue": "dropped term"}], []])
    r = formalize_with_retry({"paper_id": "x"}, "pdf")
    assert r.verdict == "VERIFIED" and r.retries == 1
    assert r.adversary_log == [[{"field": "ic", "issue": "dropped term"}], []]


def test_retry_adversary_still_flags_is_unknown(monkeypatch):
    _install(monkeypatch, asts=[_m("a"), _m("b")],
             verdicts=["VERIFIED", "VERIFIED"],
             adv=[[{"field": "ic", "issue": "x"}], [{"field": "ic", "issue": "still x"}]])
    r = formalize_with_retry({"paper_id": "x"}, "pdf")
    assert r.verdict == "UNKNOWN" and r.retries == 1
    assert "still flagged" in r.notes


def test_retry_counterexample_then_verified(monkeypatch):
    _install(monkeypatch, asts=[_m("a"), _m("b")],
             verdicts=["COUNTEREXAMPLE", "VERIFIED"], adv=[[]])
    r = formalize_with_retry({"paper_id": "x"}, None)
    assert r.verdict == "VERIFIED" and r.retries == 1


def test_retry_counterexample_persists(monkeypatch):
    _install(monkeypatch, asts=[_m("a"), _m("b")],
             verdicts=["COUNTEREXAMPLE", "COUNTEREXAMPLE"], adv=[])
    r = formalize_with_retry({"paper_id": "x"}, None)
    assert r.verdict == "COUNTEREXAMPLE" and r.retries == 1


def test_retry_unknown_verdict_no_retry(monkeypatch):
    _install(monkeypatch, asts=[_m()], verdicts=["UNKNOWN"], adv=[])
    r = formalize_with_retry({"paper_id": "x"}, "pdf")
    assert r.verdict == "UNKNOWN" and r.retries == 0
