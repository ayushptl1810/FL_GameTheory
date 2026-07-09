#!/usr/bin/env python3
"""
FL corpus auto-growth pipeline.

Searches arXiv and Semantic Scholar for new FL incentive mechanism papers,
downloads their PDFs to pdfs/, and optionally triggers extraction.

State is tracked in tools/seen_ids.json so each run only downloads
papers not seen before.

Usage (from project root):
    python tools/run.py                # search + download new papers
    python tools/run.py --dry-run      # show what would be downloaded
    python tools/run.py --extract      # also run tools/extract.py after download
    python tools/run.py --limit 20     # cap downloads per run (default: 50)
    python tools/run.py --reset        # clear seen_ids and re-scan everything
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(TOOLS_DIR))

from search import search_all      # noqa: E402
from download import download_pdf  # noqa: E402

CONFIG_PATH   = TOOLS_DIR / "config.json"
SEEN_IDS_PATH = TOOLS_DIR / "seen_ids.json"
PROJECT_ROOT  = TOOLS_DIR.parent
PDFS_DIR      = PROJECT_ROOT / "pdfs"
ENTRIES_DIR   = PROJECT_ROOT / "entries"


def load_seen_ids() -> set[str]:
    if SEEN_IDS_PATH.exists():
        return set(json.loads(SEEN_IDS_PATH.read_text()))
    return set()


def save_seen_ids(seen: set[str]) -> None:
    SEEN_IDS_PATH.write_text(json.dumps(sorted(seen), indent=2))


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def main() -> None:
    parser = argparse.ArgumentParser(description="FL corpus auto-growth pipeline")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Show new papers without downloading")
    parser.add_argument("--extract",  action="store_true",
                        help="Run schema/extract.py on pdfs/ after downloading")
    parser.add_argument("--limit",    type=int, default=50,
                        help="Max PDFs to download per run (default 50)")
    parser.add_argument("--reset",    action="store_true",
                        help="Clear seen_ids.json and re-scan everything")
    parser.add_argument("--category", type=str, default=None, metavar="CAT",
                        help="Target a single category: Shapley, VCG, Contract, Stackelberg, RL, Valuation")
    args = parser.parse_args()

    PDFS_DIR.mkdir(exist_ok=True)

    if args.reset and SEEN_IDS_PATH.exists():
        SEEN_IDS_PATH.unlink()
        print("[preloader] seen_ids reset.")

    config   = load_config()
    seen_ids = load_seen_ids()

    print("\n=== FL Corpus Preloader ===")
    print(f"Already tracked : {len(seen_ids)} paper IDs")
    print(f"Searching...\n")

    candidates  = search_all(config, category=args.category)
    new_papers  = [p for p in candidates if p["arxiv_id"] not in seen_ids]

    if not new_papers:
        print("\nNo new papers -- corpus is up to date.")
        return

    to_process = new_papers[:args.limit]
    print(f"\n{len(new_papers)} new paper(s) found, processing {len(to_process)}:\n")

    downloaded: list[dict] = []
    failed:     list[dict] = []

    for i, paper in enumerate(to_process, 1):
        safe_id  = paper["arxiv_id"].replace("/", "_")
        pdf_path = PDFS_DIR / f"{safe_id}.pdf"
        tag      = f"[{i:02d}/{len(to_process):02d}]"

        print(f"{tag} {paper['title'][:72]}")
        print(f"       {paper['arxiv_id']}  {paper['published'][:10]}  [{paper['source']}]")

        seen_ids.add(paper["arxiv_id"])

        if args.dry_run:
            print()
            continue

        if pdf_path.exists():
            print(f"       -> skip (PDF already exists)\n")
            continue

        ok = download_pdf(paper["pdf_url"], pdf_path)
        if ok:
            kb = pdf_path.stat().st_size // 1024
            print(f"       -> {pdf_path.name} ({kb} KB)\n")
            downloaded.append(paper)
        else:
            print(f"       -> FAILED (paywalled or network error)\n")
            failed.append(paper)

        time.sleep(1.5)

    # Save seen_ids so re-runs skip already-seen papers
    save_seen_ids(seen_ids)

    if args.dry_run:
        print(f"[DRY RUN] Would have processed {len(to_process)} papers.")
        return

    print("=" * 50)
    print(f"Downloaded : {len(downloaded)} new PDFs -> preloader/pdfs/")
    if failed:
        print(f"Failed     : {len(failed)} (paywalled / network)")

    if not downloaded:
        return

    if args.extract:
        print("\nRunning extractor...\n")
        result = subprocess.run(
            [sys.executable, "tools/extract.py", "pdfs/", "--out", "entries/"],
            cwd=str(PROJECT_ROOT),
        )
        status = "complete" if result.returncode == 0 else "finished with errors"
        print(f"\nExtraction {status}.")
    else:
        print("\nNext steps:")
        print("  python tools/extract.py pdfs/ --out entries/")
        print("  # fix any schema errors, then rebuild corpus:")
        print("  python -c \"import json,glob; e=[json.load(open(p)) for p in sorted(glob.glob('entries/*.json'))]; json.dump(e,open('corpus_new.json','w'),indent=2)\"")


if __name__ == "__main__":
    main()
