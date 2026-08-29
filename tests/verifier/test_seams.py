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
