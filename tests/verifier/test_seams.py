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


_STACKELBERG_IDS = [
    # the 1 currently entry-specific VERIFIED
    "Sarikaya2019stackelberg_workers",
    # 5 template-only entries
    "1811_12082",
    "2101_05628",
    "2101_12428",
    "2103_05866",
    "2110_12876",
]
STACKELBERG = [e for e in CORPUS if e.get("paper_id") in _STACKELBERG_IDS]


def test_stackelberg_verdicts_unchanged_after_seam_extraction():
    # Behavior lock for Task 5: snapshot of verify() on 6 corpus Stackelberg
    # entries, captured before extracting _stackelberg_check_core from
    # _try_stackelberg_latex.
    expected_stackelberg = {
        "Sarikaya2019stackelberg_workers": ("VERIFIED", True),
        "1811_12082": ("VERIFIED_TEMPLATE", False),
        "2101_05628": ("VERIFIED_TEMPLATE", False),
        "2101_12428": ("VERIFIED_TEMPLATE", False),
        "2103_05866": ("VERIFIED_TEMPLATE", False),
        "2110_12876": ("VERIFIED_TEMPLATE", False),
    }
    assert len(STACKELBERG) == len(expected_stackelberg)
    for e in STACKELBERG:
        r = verify(e)
        assert e["paper_id"] in expected_stackelberg
        assert (r.verdict, r.entry_specific) == expected_stackelberg[e["paper_id"]]


# Behavior lock for Task 7: every corpus entry that currently routes to
# Track 2 (SOS, 4), Track 3 (interval, 2), or Track 4 (Bayesian, 1), captured
# before extracting track{2,3,4}_check_from_sympy from verify_track{2,3,4}.
# {paper_id: (verdict, entry_specific, track)}
_EXPECTED_T234 = {
    "2307_15975": ("VERIFIED", True, 2),
    "Lim2020contract_healthcare": ("VERIFIED", True, 2),
    "Sun2022coded": ("VERIFIED", True, 2),
    "Tan2025renegotiable_contract": ("VERIFIED", True, 2),
    "Kang2019contract_mobile": ("UNKNOWN", True, 3),
    "Sarikaya2019stackelberg_workers": ("VERIFIED", True, 3),
    "Li2025bayesian_incentive": ("VERIFIED", True, 4),
}


def test_track234_verdicts_unchanged_after_seam_extraction():
    seen = {}
    for e in CORPUS:
        r = verify(e)
        if getattr(r, "track", None) in (2, 3, 4):
            seen[e["paper_id"]] = (r.verdict, r.entry_specific, r.track)
    assert seen == _EXPECTED_T234
