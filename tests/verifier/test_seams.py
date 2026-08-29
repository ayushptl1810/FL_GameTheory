import json

from verifier import verify

CORPUS = json.load(open("corpus.json"))
VCG = [e for e in CORPUS if e.get("category") == "VCG"][:8]


def test_vcg_verdicts_unchanged_after_seam_extraction():
    # Behavior lock for Task 3: snapshot of verify() on the first 8 corpus VCG
    # entries, captured before extracting _vcg_check_core from verify_vcg.
    expected = {
        "2404_13841": ("VERIFIED", True),
        "2504_05563": ("VERIFIED", True),
        "3626307_3626311": ("VERIFIED", True),
        "Ahmed2023frimfl": ("VERIFIED_TEMPLATE", False),
        "Batool2022fl_mab": ("VERIFIED_TEMPLATE", False),
        "Cheng2022uav": ("VERIFIED", True),
        "Cong2020vcg": ("VERIFIED", True),
        "Cui2024auction_market": ("VERIFIED_TEMPLATE", False),
    }
    for e in VCG:
        r = verify(e)
        assert e["paper_id"] in expected
        assert (r.verdict, r.entry_specific) == expected[e["paper_id"]]


_CONTRACT_IDS = [
    # all 5 currently entry-specific VERIFIED
    "2307_15975",
    "Li2025bayesian_incentive",
    "Lim2020contract_healthcare",
    "Sun2022coded",
    "Tan2025renegotiable_contract",
    # 3 template (linear-cost model) entries
    "2102_03401",
    "2308_12502",
    "2403_09153",
]
CONTRACT = [e for e in CORPUS if e.get("paper_id") in _CONTRACT_IDS]


def test_contract_verdicts_unchanged_after_seam_extraction():
    # Behavior lock for Task 4: snapshot of verify() on 8 corpus Contract
    # entries, captured before extracting _contract_check_core from
    # _try_contract_latex.
    expected_contract = {
        "2307_15975": ("VERIFIED", True),
        "Li2025bayesian_incentive": ("VERIFIED", True),
        "Lim2020contract_healthcare": ("VERIFIED", True),
        "Sun2022coded": ("VERIFIED", True),
        "Tan2025renegotiable_contract": ("VERIFIED", True),
        "2102_03401": ("VERIFIED_TEMPLATE", False),
        "2308_12502": ("VERIFIED_TEMPLATE", False),
        "2403_09153": ("VERIFIED_TEMPLATE", False),
    }
    assert len(CONTRACT) == len(expected_contract)
    for e in CONTRACT:
        r = verify(e)
        assert e["paper_id"] in expected_contract
        assert (r.verdict, r.entry_specific) == expected_contract[e["paper_id"]]
