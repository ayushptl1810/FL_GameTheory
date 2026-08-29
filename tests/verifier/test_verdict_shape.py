import typing

from tracks import Verdict, VerificationResult


def test_verified_shape_in_enum():
    assert "VERIFIED_SHAPE" in typing.get_args(Verdict)


def test_verified_shape_renders_as_non_proof():
    r = VerificationResult(verdict="VERIFIED_SHAPE", category="VCG",
                           paper_id="x", track=1, notes="regex form match only")
    s = str(r)
    assert "VERIFIED_SHAPE" in s
