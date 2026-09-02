from __future__ import annotations
import argparse
import json
import os
import sys

sys.path.insert(0, "src")
from verifier import verify  # noqa: E402

_IN_SCOPE = {"VCG", "Contract", "Stackelberg", "Shapley"}
_ORDER = ["VERIFIED", "VERIFIED_TEMPLATE", "VERIFIED_SHAPE", "MANUAL", "UNKNOWN", "UNSUPPORTED"]


def snapshot_verdicts(corpus_path: str, *, only: str | None = None) -> list[dict]:
    with open(corpus_path) as fh:
        corpus = json.load(fh)
    rows = []
    for e in corpus:
        cat = e.get("category")
        if cat not in _IN_SCOPE:
            continue
        if only is not None and cat != only:
            continue
        r = verify(e)
        rows.append({
            "paper_id": e.get("paper_id", ""),
            "category": cat,
            "verdict": r.verdict,
            "entry_specific": bool(getattr(r, "entry_specific", False)),
        })
    rows.sort(key=lambda x: (x["category"], x["paper_id"]))
    return rows


def render_table(rows: list[dict], *, title: str = "Per-Entry Verdict Baseline") -> str:
    out = [f"# R2/R3 — {title}", "",
           "Captured before the sweep. Out-of-scope categories "
           "(`RL`, `Valuation`, `Naive`) are omitted.", "",
           "## Per-Entry Verdict Table", "",
           "| # | Paper ID | Category | Verdict | Entry-Specific |",
           "|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        out.append(f"| {i} | {r['paper_id']} | {r['category']} | "
                   f"{r['verdict']} | {r['entry_specific']} |")
    counts = {k: sum(1 for r in rows if r["verdict"] == k) for k in _ORDER}
    out += ["", "## Verdict Counts", ""]
    for k in _ORDER:
        out.append(f"- {k}: {counts[k]}")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m scripts.snapshot_verdicts")
    ap.add_argument("corpus_path")
    ap.add_argument("--only", default=None)
    ap.add_argument("--out", default="docs/superpowers/notes/round-R2-baseline.md")
    args = ap.parse_args(argv)
    rows = snapshot_verdicts(args.corpus_path, only=args.only)
    md = render_table(rows)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as fh:
        fh.write(md)
    counts = {k: sum(1 for r in rows if r["verdict"] == k) for k in _ORDER}
    print("counts:", counts, "->", args.out)


if __name__ == "__main__":
    main()
