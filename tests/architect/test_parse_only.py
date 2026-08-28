import pytest
from tracks.track1_z3 import parse_only_contract, ParseFailure


def test_parse_only_contract_parses_clean_fields():
    mech = {
        "client_utility_latex": "R_i - c_i \\cdot e_i^2",
        "ic_condition_latex": "R_i - c_i \\cdot e_i^2 \\geq R_j - c_i \\cdot e_j^2",
        "ir_condition_latex": "R_i - c_i \\cdot e_i^2 \\geq 0",
    }
    out = parse_only_contract(mech)
    assert set(out) == set(mech)


def test_parse_only_contract_raises_on_unparseable():
    mech = {"ic_condition_latex": "\\sum_{i \\in S} R_i \\geq 0"}
    with pytest.raises(ParseFailure) as ei:
        parse_only_contract(mech)
    assert ei.value.field == "ic_condition_latex"
