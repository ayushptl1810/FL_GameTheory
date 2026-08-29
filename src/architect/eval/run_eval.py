"""Real-run entry point for the Architect evaluation harness (needs API + corpus)."""
from __future__ import annotations
import argparse
import json
import os
import pathlib

from architect.rag import build_index
from architect.eval import ABLATIONS, evaluate, summarize

_MAIN_HDR = ("| name | mode | status | iters | solver | wall_s | ic_regret | "
             "expected_family | family_match | coalition_ic_regret |")
_MAIN_SEP = "|" + "---|" * 10


def _main_table(rows) -> str:
    body = "\n".join(
        f"| {r['name']} | {r['mode']} | {r['status']} | {r['iterations']} | "
        f"{r['solver_calls']} | {r['wall_clock']} | {r['ic_regret']} | "
        f"{r.get('expected_family')} | {r.get('family_match')} | "
        f"{r.get('coalition_ic_regret')} |" for r in rows)
    return _MAIN_HDR + "\n" + _MAIN_SEP + "\n" + body


def _variance_table(rows) -> str:
    hdr = ("| name | verified_rate | iters_mean | iters_spread | "
           "wall_clock_mean | ic_regret_mean |")
    sep = "|" + "---|" * 6
    body = "\n".join(
        f"| {s['name']} | {s['verified_rate']:.2f} | {s['iters_mean']:.2f} | "
        f"{s['iters_spread']} | {s['wall_clock_mean']:.2f} | "
        f"{s['ic_regret_mean']} |" for s in summarize(rows))
    return hdr + "\n" + sep + "\n" + body


def _ablations_table(rows) -> str:
    hdr = "| name | ablation | seed | status | iters | wall_s | ic_regret |"
    sep = "|" + "---|" * 7
    body = "\n".join(
        f"| {r['name']} | {r['ablation']} | {r['seed']} | {r['status']} | "
        f"{r['iterations']} | {r['wall_clock']} | {r['ic_regret']} |"
        for r in rows)
    return hdr + "\n" + sep + "\n" + body


def _baselines_table(rows) -> str:
    hdr = "| name | method | status | ic_regret | family_match |"
    sep = "|" + "---|" * 5
    body = "\n".join(
        f"| {r['name']} | {r['method']} | {r['status']} | {r['ic_regret']} | "
        f"{r['family_match']} |" for r in rows)
    return hdr + "\n" + sep + "\n" + body


def _run_baselines() -> list:
    from architect.eval.benchmarks import BENCHMARKS
    from architect.eval.baselines.control import run_baseline as _control
    from architect.eval.baselines.regretnet import run_baseline as _regretnet
    from architect.eval.baselines.liu_amd_llm import run_baseline as _liu
    rows = []
    for method, fn in (("control", _control), ("regretnet", _regretnet),
                       ("liu_amd_llm", _liu)):
        for b in BENCHMARKS:
            rows.append(fn(method, b))
    return rows


def _model_table(rows, model) -> str:
    hdr = "| model | name | verified_rate | iters_mean | wall_clock_mean |"
    sep = "|" + "---|" * 5
    body = "\n".join(
        f"| {model} | {s['name']} | {s['verified_rate']:.2f} | "
        f"{s['iters_mean']:.2f} | {s['wall_clock_mean']:.2f} |"
        for s in summarize(rows))
    return hdr + "\n" + sep + "\n" + body


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=1,
                    help="run each benchmark this many times (seeds 0..N-1)")
    ap.add_argument("--model", type=str, default=None,
                    help="override ARCHITECT_LLM_MODEL for this run")
    ap.add_argument("--ablations", action="store_true",
                    help="also run the ablation knobs: " + ", ".join(ABLATIONS))
    ap.add_argument("--with-baselines", action="store_true",
                    help="also run the control / RegretNet / Liu-et-al baselines "
                         "over every benchmark and append a ## Baselines table")
    args = ap.parse_args(argv)

    if args.model:
        os.environ["ARCHITECT_LLM_MODEL"] = args.model

    idx = build_index()
    seeds = tuple(range(args.seeds))
    ablations = list(ABLATIONS) if args.ablations else None
    rows = evaluate(index=idx, seeds=seeds, ablations=ablations, model=args.model)

    base = [r for r in rows if "ablation" not in r]
    abl = [r for r in rows if "ablation" in r]

    pathlib.Path("eval-results.json").write_text(json.dumps(rows, indent=2))

    parts = ["# Architect Evaluation Results", "", _main_table(base),
             "", "## Seed variance", "", _variance_table(base)]
    if abl:
        parts += ["", "## Ablations", "", _ablations_table(abl)]
    if args.model:
        parts += ["", "## Model comparison", "", _model_table(base, args.model)]
    if args.with_baselines:
        parts += ["", "## Baselines", "", _baselines_table(_run_baselines())]

    pathlib.Path("docs").mkdir(exist_ok=True)
    pathlib.Path("docs/eval-results.md").write_text("\n".join(parts) + "\n")
    print(f"wrote docs/eval-results.md ({len(base)} base rows, {len(abl)} ablation rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
