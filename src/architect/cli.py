from __future__ import annotations
import os
import sys
from architect.intake import intake
from architect.rag import build_index
from architect.loop import run


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print('usage: architect "<free-text FL setup>"'); return 2
    index = build_index()
    spec = intake(argv[0])
    if spec.missing_fields:
        print(f"[intake] missing (using defaults): {spec.missing_fields}")
    budget_s = float(os.environ.get("ARCHITECT_BUDGET_S", "300"))
    result = run(spec, index=index, budget_s=budget_s)
    print(f"\nmode={result.mode}  status={result.status}  "
          f"iterations={result.iterations}  solver_calls={result.solver_calls}  "
          f"wall_clock={result.wall_clock:.1f}s")
    if result.status == "VERIFIED":
        print("\n--- verified mechanism (LaTeX) ---\n" + result.mechanism_latex)
        print("\n--- certificate conditions ---")
        for c in result.certificate:
            print(f"  OK {c}")
        return 0
    print("\nFAILED. Last transcript entries:")
    for e in result.transcript[-3:]:
        print(f"  {e}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
