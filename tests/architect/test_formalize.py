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
