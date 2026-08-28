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
