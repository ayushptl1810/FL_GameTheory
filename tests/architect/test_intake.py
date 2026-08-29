import json
from architect.intake import intake, INTAKE_SYSTEM_PROMPT


def _fake_complete(payload):
    def _c(system, user, **kw):
        return json.dumps(payload)
    return _c


def test_intake_parses_full_spec():
    spec = intake("100 cross-device clients, quadratic cost, private types",
                  complete=_fake_complete({
                      "n_clients": 100, "cost_structure": "quadratic",
                      "type_model": "private discrete", "observability": "none",
                      "budget": 1000.0, "failure_modes": ["non_iid"]}))
    assert spec.n_clients == 100 and spec.missing_fields == []


def test_intake_records_missing_fields():
    spec = intake("some FL thing", complete=_fake_complete({
        "n_clients": None, "cost_structure": None, "type_model": None,
        "observability": None, "budget": None, "failure_modes": []}))
    assert "n_clients" in spec.missing_fields and "budget" in spec.missing_fields


def test_prompt_mentions_failure_modes():
    assert "collusion" in INTAKE_SYSTEM_PROMPT


def test_prompt_mentions_expected_family():
    assert "expected_family" in INTAKE_SYSTEM_PROMPT
    for fam in ("VCG", "Contract", "Stackelberg"):
        assert fam in INTAKE_SYSTEM_PROMPT


_BASE = {"n_clients": None, "cost_structure": None, "type_model": None,
         "observability": None, "budget": None, "failure_modes": []}


def test_intake_extracts_expected_family():
    spec = intake("menu of contracts", complete=_fake_complete(
        {**_BASE, "expected_family": "Contract"}))
    assert spec.expected_family == "Contract"


def test_intake_expected_family_absent():
    spec = intake("some FL thing", complete=_fake_complete(dict(_BASE)))
    assert spec.expected_family is None


def test_intake_expected_family_garbage_coerced():
    spec = intake("an auction", complete=_fake_complete(
        {**_BASE, "expected_family": "Auction"}))
    assert spec.expected_family is None
