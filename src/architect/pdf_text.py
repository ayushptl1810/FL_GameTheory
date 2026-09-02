from __future__ import annotations
import os

_KEYWORDS = (
    "incentive compat", "individual rational", "payment rule",
    "utility", "best response",
)


def pdf_path(paper_id: str, *, pdf_dir: str = "pdfs") -> str | None:
    for name in (
        f"{paper_id}.pdf",
        f"{paper_id.replace('_', '.')}.pdf",
        f"{paper_id.replace('_', '-')}.pdf",
    ):
        p = os.path.join(pdf_dir, name)
        if os.path.isfile(p):
            return p
    return None


def pdf_text(paper_id: str, *, pdf_dir: str = "pdfs", max_chars: int = 24000) -> str | None:
    p = pdf_path(paper_id, pdf_dir=pdf_dir)
    if p is None:
        return None
    try:
        from pdfminer.high_level import extract_text
        txt = extract_text(p) or ""
    except Exception:
        return None
    if not txt.strip():
        return None
    if len(txt) <= max_chars:
        return txt
    half = max_chars // 2
    low = txt.lower()
    hits = [low.find(k) for k in _KEYWORDS if low.find(k) != -1]
    if not hits:
        return txt[:max_chars]
    start = max(0, min(hits) - max_chars // 4)
    return txt[:half] + "\n...\n" + txt[start:start + half]
