#!/usr/bin/env python3
"""
Extract structured corpus entries from FL incentive mechanism PDFs using Groq API.

Usage:
    python tools/extract.py pdfs/Cong2020vcg.pdf
    python tools/extract.py pdfs/Cong2020vcg.pdf --category VCG
    python tools/extract.py pdfs/Cong2020vcg.pdf --out entries/
    python tools/extract.py pdfs/ --out entries/   # batch all PDFs
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from fields import GOLD_LATEX_FIELDS, MECHANISM_FIELDS, RAG_CATEGORIES, is_filled
from prompts import CLASSIFY_SYSTEM, EXTRACT_PROMPTS, EXTRACT_SYSTEM

MAX_PDF_CHARS = 28_000


# ── PDF text extraction ───────────────────────────────────────────────────────

def extract_pdf_text(pdf_path: Path, max_chars: int = MAX_PDF_CHARS) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            chunks: list[str] = []
            total = 0
            for page in pdf.pages:
                text = page.extract_text() or ""
                chunks.append(text)
                total += len(text)
                if total >= max_chars:
                    break
            return "\n\n".join(chunks)[:max_chars]
    except ImportError:
        sys.exit("Install pdfplumber:  .venv/bin/pip install pdfplumber")


# ── Groq API helpers ──────────────────────────────────────────────────────────

def load_groq_key() -> str:
    key = os.environ.get("GROQ_API_KEY", "")
    if key:
        return key
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GROQ_API_KEY="):
                key = line.split("=", 1)[1].strip().strip("\"'")
                if key:
                    return key
    sys.exit("GROQ_API_KEY not found. Set it in .env or export the variable.")


class RateLimitReached(Exception):
    pass


class RequestTooLarge(Exception):
    pass


def groq_chat(
    key: str,
    system: str,
    user: str,
    model: str = "llama-3.3-70b-versatile",
    max_tokens: int = 4096,
) -> str:
    try:
        from groq import Groq, RateLimitError
    except ImportError:
        sys.exit("Install groq:  .venv/bin/pip install groq")
    client = Groq(api_key=key)
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.0,
            max_tokens=max_tokens,
        )
    except RateLimitError as exc:
        raise RateLimitReached(str(exc)) from exc
    except Exception as exc:
        msg = str(exc)
        if "413" in msg or "Request too large" in msg or "please reduce your message size" in msg:
            raise RequestTooLarge(msg) from exc
        raise
    return resp.choices[0].message.content.strip()


def parse_json_from_llm(text: str) -> dict[str, Any]:
    """Extract JSON object from LLM response, handling markdown fences and nested objects."""
    # Strip markdown fences so raw_decode can find the opening brace
    cleaned = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    start = cleaned.find("{")
    if start == -1:
        raise ValueError(f"No JSON object in LLM response:\n{text[:600]}")
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(cleaned, start)
    if isinstance(obj, dict):
        return obj
    raise ValueError(f"Parsed JSON is not a dict: {type(obj)}")


# ── Classification ────────────────────────────────────────────────────────────

def classify_paper(text: str, key: str) -> str:
    response = groq_chat(key, CLASSIFY_SYSTEM, f"Classify this FL paper:\n\n{text[:8000]}")
    result = parse_json_from_llm(response)
    cat = str(result.get("category", "")).strip()
    if cat not in MECHANISM_FIELDS:
        raise ValueError(f"Invalid category from LLM: {cat!r}  (response: {response[:200]})")
    print(f"  [classify] -> {cat}  ({result.get('reason', '')})")
    return cat



# ── Field extraction ──────────────────────────────────────────────────────────

def extract_fields(text: str, category: str, key: str) -> dict[str, Any]:
    prompt = EXTRACT_PROMPTS[category].replace("{text}", text)
    response = groq_chat(key, EXTRACT_SYSTEM, prompt, max_tokens=4096)
    return parse_json_from_llm(response)


# ── Entry construction ────────────────────────────────────────────────────────

def _determine_quality_tier(category: str, mechanism: dict[str, Any]) -> str:
    if category in RAG_CATEGORIES:
        filled = sum(1 for v in mechanism.values() if is_filled(v))
        total = max(len(mechanism), 1)
        return "silver" if filled / total >= 0.6 else "bronze"

    latex_fields = GOLD_LATEX_FIELDS.get(category, [])
    if not latex_fields:
        return "silver"
    filled_count = sum(1 for f in latex_fields if is_filled(mechanism.get(f)))
    ratio = filled_count / len(latex_fields)
    if ratio == 1.0:
        return "gold"
    if ratio >= 0.5:
        return "silver"
    return "bronze"


def _build_mechanism(category: str, raw: dict[str, Any]) -> dict[str, Any]:
    # LLM may return mechanism fields at top level OR nested under "mechanism"
    nested = raw.get("mechanism") or {}
    merged: dict[str, Any] = {**raw, **nested}
    fields = MECHANISM_FIELDS.get(category, [])
    return {f: merged.get(f) for f in fields}


def _shapley_to_valuation(shapley_mech: dict[str, Any], reclassify_note: str) -> dict[str, Any]:
    """Convert a Shapley mechanism dict to Valuation when the hard gate fails."""
    return {
        "valuation_method": "shapley-approximation",
        "computational_complexity": None,
        "ic_claimed": bool(shapley_mech.get("ic_proof_present", False)),
        "valuation_function_latex": shapley_mech.get("shapley_formula_latex"),
        "why_not_shapley": reclassify_note or "IC/IR not formally proved",
        "key_assumptions": shapley_mech.get("key_assumptions") or [],
    }


_VALID_PAPER_TYPES = {"primary", "comparison", "application"}


def _coerce_paper_type(raw_pt: Any) -> list[str]:
    """Normalize and filter paper_type to only valid enum values."""
    if isinstance(raw_pt, str):
        raw_pt = [raw_pt]
    if not isinstance(raw_pt, list):
        return ["primary"]
    filtered = [t for t in raw_pt if t in _VALID_PAPER_TYPES]
    return filtered if filtered else ["primary"]


def _year_from_filename(stem: str) -> int | None:
    """Fallback: parse 4-digit year from filename like 'Kang2019contract_mobile'."""
    match = re.search(r"(\d{4})", stem)
    if match:
        yr = int(match.group(1))
        if 1990 <= yr <= 2030:
            return yr
    return None


def build_entry(pdf_path: Path, category: str, raw: dict[str, Any]) -> dict[str, Any]:
    paper_id = pdf_path.stem
    mechanism = _build_mechanism(category, raw)

    # Shapley hard gate: auto-reclassify to Valuation if IC or IR not proved
    if category == "Shapley":
        ic_ok = mechanism.get("ic_proof_present") is True
        ir_ok = mechanism.get("ir_proof_present") is True
        if not ic_ok or not ir_ok:
            note = (
                mechanism.get("reclassify_note")
                or raw.get("reclassify_note")
                or "ic_proof_present or ir_proof_present is False -- reclassified Shapley -> Valuation"
            )
            print(f"  [hard-gate] Shapley -> Valuation  ({note})")
            category = "Valuation"
            mechanism = _shapley_to_valuation(mechanism, note)

    tier = _determine_quality_tier(category, mechanism)
    z3_validated: bool | None = None if category in RAG_CATEGORIES else False

    paper_type = _coerce_paper_type(raw.get("paper_type"))

    # Year fallback: parse from filename if LLM returned null
    year = raw.get("year")
    if not year:
        year = _year_from_filename(pdf_path.stem)

    entry: dict[str, Any] = {
        "paper_id": paper_id,
        "title": raw.get("title") or paper_id,
        "year": year,
        "venue": raw.get("venue"),
        "category": category,
        "paper_type": paper_type,
        "fl_setup": raw.get("fl_setup"),
        "num_clients": str(raw.get("num_clients") or "unspecified"),
        "quality_tier": tier,
        "z3_validated": z3_validated,
        "notes": raw.get("notes"),
        "mechanism": mechanism,
    }

    if "comparison" in paper_type:
        comp = raw.get("comparison") or (raw.get("mechanism") or {}).get("comparison")
        if comp:
            entry["comparison"] = comp

    if "application" in paper_type:
        app = raw.get("application") or (raw.get("mechanism") or {}).get("application")
        if app:
            entry["application"] = app

    return entry


# ── Lightweight post-extraction validation ────────────────────────────────────

def _validate_entry_inline(entry: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    required_top = ["paper_id", "title", "year", "category", "paper_type",
                    "fl_setup", "quality_tier", "mechanism"]
    for f in required_top:
        if not is_filled(entry.get(f)):
            errors.append(f"[missing] top-level field '{f}' is null/empty")

    category = entry.get("category", "")
    mech = entry.get("mechanism", {})

    if category == "Shapley":
        for gate_field in ("ic_proof_present", "ir_proof_present"):
            if mech.get(gate_field) is not True:
                errors.append(
                    f"[hard-gate] mechanism.{gate_field} must be true for Shapley category"
                )

    if category in RAG_CATEGORIES and entry.get("z3_validated") is not None:
        errors.append(f"[z3] z3_validated must be null for RAG-only category '{category}'")

    paper_type = entry.get("paper_type", [])
    if "application" in paper_type and "application" not in entry:
        errors.append("[paper_type] 'application' in paper_type but 'application' block missing")
    if "comparison" in paper_type and "comparison" not in entry:
        errors.append("[paper_type] 'comparison' in paper_type but 'comparison' block missing")

    return errors


# ── Main processing pipeline ──────────────────────────────────────────────────

def process_pdf(
    pdf_path: Path,
    key: str,
    force_category: str | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    print(f"\n{'─'*60}")
    print(f"Processing: {pdf_path.name}")

    text = extract_pdf_text(pdf_path)
    print(f"  [pdf] extracted {len(text):,} chars")

    category = force_category or classify_paper(text, key)
    print(f"  [extract] running {category} extraction prompt ...")
    try:
        raw = extract_fields(text, category, key)
    except RequestTooLarge:
        fallback_chars = 16_000
        print(f"  [413] request too large; retrying with {fallback_chars:,} chars ...")
        raw = extract_fields(text[:fallback_chars], category, key)

    entry = build_entry(pdf_path, category, raw)
    print(f"  [build] quality_tier={entry['quality_tier']}  category={entry['category']}")

    errors = _validate_entry_inline(entry)
    if errors:
        print(f"  [warn] {len(errors)} validation issue(s):")
        for e in errors:
            print(f"    {e}")
    else:
        print(f"  [ok] entry passes inline validation")

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"{entry['paper_id']}.json"
        out_path.write_text(json.dumps(entry, indent=2, ensure_ascii=False))
        print(f"  [save] -> {out_path}")
    else:
        print(json.dumps(entry, indent=2, ensure_ascii=False))

    return entry


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract FL corpus entries from PDFs using Groq API"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to a single PDF file or a directory of PDFs (batch mode)",
    )
    parser.add_argument(
        "--category",
        choices=list(MECHANISM_FIELDS.keys()),
        help="Force a specific category instead of auto-classifying",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory for per-paper JSON files (defaults to stdout)",
    )
    parser.add_argument(
        "--merge",
        type=Path,
        default=None,
        help="If set, merge all extracted entries into this JSON array file",
    )
    args = parser.parse_args()

    key = load_groq_key()
    pdfs: list[Path] = []

    if args.input.is_dir():
        pdfs = sorted(args.input.glob("*.pdf"))
        if not pdfs:
            sys.exit(f"No PDF files found in {args.input}")
    elif args.input.is_file() and args.input.suffix.lower() == ".pdf":
        pdfs = [args.input]
    else:
        sys.exit(f"Input must be a .pdf file or a directory: {args.input}")

    entries: list[dict[str, Any]] = []
    failed: list[str] = []

    for pdf_path in pdfs:
        # Resume support: skip PDFs whose output file already exists
        if args.out:
            out_file = args.out / f"{pdf_path.stem}.json"
            if out_file.exists():
                print(f"  [skip] {pdf_path.name} (already extracted)")
                try:
                    entries.append(json.loads(out_file.read_text()))
                except Exception:
                    pass
                continue

        try:
            entry = process_pdf(pdf_path, key, args.category, args.out)
            entries.append(entry)
        except RateLimitReached as exc:
            print(f"\n  [RATE LIMIT] Groq rate limit reached: {exc}")
            print("  Stopping. Re-run the same command to resume from where it left off.")
            break
        except Exception as exc:
            print(f"  [ERROR] {pdf_path.name}: {exc}")
            failed.append(pdf_path.name)

    if args.merge and entries:
        args.merge.write_text(json.dumps(entries, indent=2, ensure_ascii=False))
        print(f"\n[merge] wrote {len(entries)} entries -> {args.merge}")

    print(f"\n{'='*60}")
    print(f"Done. Processed: {len(entries)}  Failed: {len(failed)}")
    if failed:
        print("Failed files:")
        for f in failed:
            print(f"  {f}")


if __name__ == "__main__":
    main()
