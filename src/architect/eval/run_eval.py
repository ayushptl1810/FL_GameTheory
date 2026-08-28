"""Real-run entry point for the Architect evaluation harness (needs API + corpus)."""
from __future__ import annotations
import json
import pathlib

from architect.rag import build_index
from architect.eval import evaluate


def main() -> int:
    idx = build_index()
    rows = evaluate(index=idx)
    pathlib.Path("eval-results.json").write_text(json.dumps(rows, indent=2))
    hdr = "| name | mode | status | iters | solver | wall_s | ic_regret |"
    sep = "|" + "---|" * 7
    body = "\n".join(
        f"| {r['name']} | {r['mode']} | {r['status']} | {r['iterations']} | "
        f"{r['solver_calls']} | {r['wall_clock']} | {r['ic_regret']} |" for r in rows)
    pathlib.Path("docs").mkdir(exist_ok=True)
    pathlib.Path("docs/eval-results.md").write_text(
        "# Architect Evaluation Results\n\n" + hdr + "\n" + sep + "\n" + body + "\n")
    print(f"wrote docs/eval-results.md ({len(rows)} benchmarks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
