"""Adversarial verifier-soundness report.

Runs verify() over tests/verifier/broken_mechanisms.BROKEN -- mechanisms that
are provably NOT IC/IR -- and counts how many the verifier wrongly certified
(VERIFIED or VERIFIED_TEMPLATE). A sound verifier scores false_verified == 0.

The known template-fallback holes (TEMPLATE_FALLBACK_HOLES) are excluded from
BROKEN by design and tracked as xfail in test_adversarial_soundness.py; see
.superpowers/sdd/2026-08-29-novelty-hardening/task-D-report.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from verifier import verify


def run() -> dict:
    from tests.verifier.broken_mechanisms import BROKEN
    out = {"total": len(BROKEN), "false_verified": 0,
           "by_track": {1: 0, 2: 0, 3: 0, 4: 0}, "failures": []}
    for case in BROKEN:
        entry = {"category": case["category"], "paper_id": case["name"],
                 "mechanism": dict(case["mechanism"])}
        if "params" in case:
            entry["mechanism"].setdefault("eval_params", case["params"])
        res = verify(entry)
        if res.verdict in ("VERIFIED", "VERIFIED_TEMPLATE"):
            out["false_verified"] += 1
            out["failures"].append(case["name"])
            tr = getattr(res, "track", None)
            if tr in out["by_track"]:
                out["by_track"][tr] += 1
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
