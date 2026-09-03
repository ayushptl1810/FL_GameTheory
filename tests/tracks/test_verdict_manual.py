import typing
from tracks import Verdict, finalize_verdict, VerificationResult


def test_manual_is_an_allowed_verdict():
    assert "MANUAL" in typing.get_args(Verdict)


def test_verificationresult_accepts_manual():
    r = VerificationResult(verdict="MANUAL", category="Contract", paper_id="x", track=1,
                           notes="Track 1: Contract type count capped at 4")
    assert r.verdict == "MANUAL"


def test_finalize_verdict_still_never_returns_manual():
    for all_ok in (True, False):
        for has_cex in (True, False):
            for es in (True, False):
                assert finalize_verdict(all_ok, has_cex, es) != "MANUAL"
