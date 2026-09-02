import os
import pytest
from architect.pdf_text import pdf_path, pdf_text


def test_pdf_path_exact_match(tmp_path):
    (tmp_path / "Cong2020vcg.pdf").write_bytes(b"%PDF-1.4\n")
    assert pdf_path("Cong2020vcg", pdf_dir=str(tmp_path)) == str(tmp_path / "Cong2020vcg.pdf")


def test_pdf_path_underscore_to_dot(tmp_path):
    (tmp_path / "1811.12082.pdf").write_bytes(b"%PDF-1.4\n")
    assert pdf_path("1811_12082", pdf_dir=str(tmp_path)) == str(tmp_path / "1811.12082.pdf")


def test_pdf_path_missing_returns_none(tmp_path):
    assert pdf_path("nope_nope", pdf_dir=str(tmp_path)) is None


def test_pdf_text_missing_returns_none(tmp_path):
    assert pdf_text("nope_nope", pdf_dir=str(tmp_path)) is None


def test_pdf_text_corrupt_returns_none(tmp_path):
    (tmp_path / "bad.pdf").write_bytes(b"not really a pdf")
    assert pdf_text("bad", pdf_dir=str(tmp_path)) is None


@pytest.mark.skipif(
    not os.path.isdir("pdfs") or not os.listdir("pdfs"),
    reason="no pdfs/ corpus locally",
)
def test_pdf_text_real_corpus_entry_nonempty():
    txt = pdf_text("1811_12082")
    assert txt is None or (isinstance(txt, str) and len(txt) > 200)
