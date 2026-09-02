import pytest
from verifier import print_summary
from tracks import VerificationResult


def _r(verdict, pid, notes=""):
    return VerificationResult(verdict=verdict, category="Contract", paper_id=pid,
                              track=1, notes=notes, entry_specific=(verdict == "VERIFIED"))


def test_manual_bucket_and_block(capsys, tmp_path):
    bl = tmp_path / "MANUAL-backlog.md"
    bl.write_text("## m1\nTrack 3: box dims. ...\n")
    results = [_r("VERIFIED", "v1"),
               _r("MANUAL", "m1", "MANUAL (R3a): 7 free vars [Track 3: > _MAX_BOX_DIMS = 6]")]
    print_summary(results, backlog_path=str(bl))
    out = capsys.readouterr().out
    assert "MANUAL" in out
    assert "## Diagnosed (MANUAL)" in out
    assert "m1: MANUAL (R3a)" in out
    assert "missing from MANUAL-backlog.md" not in out


def test_manual_backlog_coverage_warning(capsys, tmp_path):
    bl = tmp_path / "MANUAL-backlog.md"
    bl.write_text("## someone-else\n...\n")
    print_summary([_r("MANUAL", "m2", "Track 1: X")], backlog_path=str(bl))
    out = capsys.readouterr().out
    assert "missing from MANUAL-backlog.md: m2" in out


def test_no_manual_no_block(capsys, tmp_path):
    print_summary([_r("VERIFIED", "v1")], backlog_path=str(tmp_path / "nope.md"))
    out = capsys.readouterr().out
    assert "## Diagnosed (MANUAL)" not in out
    assert "missing from MANUAL-backlog.md" not in out
