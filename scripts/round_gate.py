from __future__ import annotations
import argparse
import re
import sys

RANK = {"VERIFIED": 0, "VERIFIED_TEMPLATE": 1, "VERIFIED_SHAPE": 1,
        "MANUAL": 2, "UNKNOWN": 3, "UNSUPPORTED": 4}


def parse_baseline(md_path: str) -> dict[str, str]:
    out = {}
    row = re.compile(r"^\|\s*\d+\s*\|\s*([^|]+?)\s*\|\s*[^|]+?\s*\|\s*([A-Z_]+)\s*\|")
    with open(md_path) as fh:
        for line in fh:
            m = row.match(line)
            if m:
                out[m.group(1)] = m.group(2)
    return out


def gate(baseline: dict[str, str], current: list[dict]) -> tuple[bool, list[str]]:
    msgs, ok = [], True
    for r in current:
        pid, v = r["paper_id"], r["verdict"]
        if pid not in baseline:
            continue
        b = baseline[pid]
        if v == "COUNTEREXAMPLE" and b != "COUNTEREXAMPLE":
            msgs.append(f"{pid}: -> COUNTEREXAMPLE (needs hand-checked justification)")
            continue
        # plan invariant: VERIFIED_TEMPLATE/SHAPE -> MANUAL is a diagnosis, an
        # improvement, not a regression (RANK alone can't express this).
        if v == "MANUAL" and b in ("VERIFIED_TEMPLATE", "VERIFIED_SHAPE"):
            msgs.append(f"improved {pid}: {b} -> {v}")
            continue
        rv, rb = RANK.get(v, 99), RANK.get(b, 99)
        if rv > rb:
            msgs.append(f"REGRESSION {pid}: {b} -> {v}")
            ok = False
        elif rv < rb:
            msgs.append(f"improved {pid}: {b} -> {v}")
    return ok, msgs


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m scripts.round_gate")
    ap.add_argument("corpus_path")
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--only", default=None)
    args = ap.parse_args(argv)
    from scripts.snapshot_verdicts import snapshot_verdicts
    base = parse_baseline(args.baseline)
    cur = snapshot_verdicts(args.corpus_path, only=args.only)
    ok, msgs = gate(base, cur)
    for m in msgs:
        print(m)
    print("GATE:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
