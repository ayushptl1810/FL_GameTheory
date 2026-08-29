"""Live breadth smoke: run the real Architect loop once per verifiable family
(auto-routed) plus one forced-Hybrid run, and print status + transcript tail so
per-family prompt problems are visible.

    PYTHONPATH=src python -m architect.eval.live_smoke

Env: ARCHITECT_LLM_MODEL / ARCHITECT_EMBED_MODEL / NVIDIA_API_KEY as usual,
ARCHITECT_BUDGET_S to cap each run (default 300).
"""
from __future__ import annotations

import json
import os

from architect.types import ProblemSpec
from architect.rag import build_index
from architect.loop import run, _default_deps

# One representative prompt per verifiable family. Kept short and explicit so
# routing is stable; extend as families get exercised.
CASES = [
    {"name": "stackelberg_effort", "force_mode": None, "expected_family": "Stackelberg",
     "text": ("The server (leader) announces a per-unit price p for client effort; "
              "each client (follower) chooses effort e to maximize p*e minus a "
              "quadratic effort cost c*e^2/2. Design the pricing rule so followers "
              "still participate (non-negative utility at their best response).")},
    {"name": "contract_screening", "force_mode": None, "expected_family": "Contract",
     "text": ("Cross-device FL with two client types, low and high cost theta. The "
              "server offers a menu of (effort e_i, reward R_i) pairs; each type "
              "self-selects. Client utility is R_i - theta_i * e_i. Design the menu "
              "so each type prefers its own contract (screening) and participates.")},
    {"name": "vcg_auction", "force_mode": None, "expected_family": "VCG",
     "text": ("The server runs an auction to select FL clients under a budget. Each "
              "client bids its cost b_i for its private true cost v_i. Design an "
              "allocation and payment rule so that bidding truthfully (b_i = v_i) is "
              "a dominant strategy and selected clients have non-negative utility.")},
    {"name": "hybrid_forced", "force_mode": "Hybrid", "expected_family": None,
     "text": ("FL setup that needs both an auction-style client selection and a "
              "contract-style payment conditioned on private cost type. Combine the "
              "two: VCG allocation, contract payment.")},
]


def main() -> int:
    budget = float(os.environ.get("ARCHITECT_BUDGET_S", "300"))
    index = build_index()
    rows = []
    for c in CASES:
        kw = {"index": index, "budget_s": budget}
        if c["force_mode"]:
            deps = _default_deps(index)
            deps.route = lambda spec, index=index, m=c["force_mode"]: m
            kw["deps"] = deps
        try:
            r = run(ProblemSpec(raw_text=c["text"],
                                expected_family=c["expected_family"]), **kw)
            row = {"name": c["name"], "expected_family": c["expected_family"],
                   "mode": r.mode, "status": r.status, "iterations": r.iterations,
                   "solver_calls": r.solver_calls, "wall_clock": round(r.wall_clock, 1),
                   "mechanism_latex": r.mechanism_latex[:400],
                   "certificate": r.certificate,
                   "transcript_tail": r.transcript[-3:]}
        except Exception as e:  # noqa: BLE001
            row = {"name": c["name"], "status": "ERROR", "error": str(e)[:300]}
        rows.append(row)
        print(f"\n=== {c['name']} (expect {c['expected_family']}) ===")
        print(f"  mode={row.get('mode')}  status={row.get('status')}  "
              f"iters={row.get('iterations')}  {row.get('wall_clock')}s")
        for e in row.get("transcript_tail", []):
            print(f"    {e}")
        if row.get("status") == "VERIFIED":
            for cond in row.get("certificate", []):
                print(f"    OK {cond}")

    print("\n\n=== JSON ===")
    print(json.dumps(rows, indent=1))
    n_ok = sum(1 for r in rows if r.get("status") == "VERIFIED")
    print(f"\nVERIFIED: {n_ok}/{len(rows)}")
    return 0 if n_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
