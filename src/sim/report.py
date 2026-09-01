"""Seed aggregation + Markdown writer for the FL empirical-validation sim.

Consumes the per-run metrics dicts from `sim.run.run_setting`, groups them by
(setting, arm, population), and emits `docs/sim-results.md`: a per-setting final
table, one participation sparkline per arm, and an honest-framing closing
paragraph contrasting the `generated` arm's empirical IC-regret with its formal 0.
"""
from __future__ import annotations

import statistics
from datetime import datetime, timezone

_RAMP = "▁▂▃▄▅▆▇█"


def _mean(xs: list[float]) -> float:
    return float(statistics.mean(xs)) if xs else 0.0


def _std(xs: list[float]) -> float:
    return float(statistics.stdev(xs)) if len(xs) >= 2 else 0.0


def _curve_mean(curves: list[list[float]]) -> list[float]:
    curves = [c for c in curves if c]
    if not curves:
        return []
    n = min(len(c) for c in curves)
    return [float(statistics.mean(c[i] for c in curves)) for i in range(n)]


def aggregate(results: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for r in results:
        groups.setdefault((r["setting"], r["arm"], r["population"]), []).append(r)

    out: list[dict] = []
    for (setting, arm, population), rs in groups.items():
        out.append({
            "setting": setting,
            "arm": arm,
            "population": population,
            "n_seeds": len(rs),
            "participation_rate_mean": _mean([r["participation_rate"] for r in rs]),
            "participation_rate_std": _std([r["participation_rate"] for r in rs]),
            "final_accuracy_mean": _mean([r["final_accuracy"] for r in rs]),
            "final_accuracy_std": _std([r["final_accuracy"] for r in rs]),
            "social_welfare_mean": _mean([r["social_welfare"] for r in rs]),
            "social_welfare_std": _std([r["social_welfare"] for r in rs]),
            "empirical_ic_regret_max": max((r["empirical_ic_regret"] for r in rs), default=0.0),
            "budget_adherence_all": all(r["budget_adherence"] for r in rs),
            "curve_participation_mean": _curve_mean([r["curve_participation"] for r in rs]),
            "curve_accuracy_mean": _curve_mean([r["curve_accuracy"] for r in rs]),
        })
    return out


def sparkline(values: list[float]) -> str:
    if not values:
        return ""
    take = min(len(values), 40)
    # evenly subsample down to `take` points
    idx = [round(i * (len(values) - 1) / (take - 1)) if take > 1 else 0 for i in range(take)]
    sampled = [float(values[i]) for i in idx]
    lo, hi = min(sampled), max(sampled)
    if hi - lo < 1e-12:
        return _RAMP[0] * take
    span = len(_RAMP) - 1
    return "".join(_RAMP[int(round((v - lo) / (hi - lo) * span))] for v in sampled)


def _cell(mean: float, std: float) -> str:
    return f"{mean:.3f} ± {std:.3f}"


def write_report(agg: list[dict], path: str = "docs/sim-results.md",
                 placeholder: dict | None = None) -> None:
    # `placeholder` is {setting: bool}. main() passes it explicitly because
    # `python -m sim.run` makes `sim.run` and `__main__` distinct module objects
    # -- the GENERATED_IS_PLACEHOLDER the runner mutated is not the one a bare
    # `from sim.run import ...` here would see. Fall back to the import when the
    # caller (e.g. a unit test) does not pass it.
    if placeholder is None:
        try:
            from sim.run import GENERATED_IS_PLACEHOLDER as placeholder
        except Exception:  # pragma: no cover
            placeholder = {}
    GENERATED_IS_PLACEHOLDER = placeholder

    settings = sorted({row["setting"] for row in agg})
    arms = sorted({row["arm"] for row in agg})
    populations = sorted({row["population"] for row in agg})
    n_seeds = max((row["n_seeds"] for row in agg), default=0)

    lines: list[str] = []
    lines.append("# FL Simulation Results")
    lines.append("")
    lines.append(f"_Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}_")
    lines.append("")
    lines.append(
        f"Scope: settings [{', '.join(settings) or '(none)'}]; "
        f"arms [{', '.join(arms) or '(none)'}]; {n_seeds} seed(s); "
        f"populations [{', '.join(populations) or '(none)'}]."
    )
    lines.append("")

    for setting in settings:
        rows = [r for r in agg if r["setting"] == setting]
        lines.append(f"## {setting}")
        lines.append("")
        if GENERATED_IS_PLACEHOLDER.get(setting):
            lines.append(
                "**⚠ placeholder mechanism** — this setting's `generated` arm used a "
                "placeholder fixture, not a real loop output; its row is not evidence."
            )
            lines.append("")
        lines.append("| arm | participation | final acc | social welfare | emp. IC-regret | budget ok |")
        lines.append("|---|---|---|---|---|---|")
        for r in sorted(rows, key=lambda r: r["arm"]):
            lines.append(
                f"| {r['arm']} "
                f"| {_cell(r['participation_rate_mean'], r['participation_rate_std'])} "
                f"| {_cell(r['final_accuracy_mean'], r['final_accuracy_std'])} "
                f"| {_cell(r['social_welfare_mean'], r['social_welfare_std'])} "
                f"| {r['empirical_ic_regret_max']:.3f} "
                f"| {'yes' if r['budget_adherence_all'] else 'no'} |"
            )
        lines.append("")
        for r in sorted(rows, key=lambda r: r["arm"]):
            lines.append(f"- {r['arm']} participation: {sparkline(r['curve_participation_mean'])}")
        lines.append("")

        gen = next((r for r in rows if r["arm"] == "generated"), None)
        ora = next((r for r in rows if r["arm"] == "oracle"), None)
        if gen is None or ora is None:
            lines.append(
                "_The generated-vs-oracle comparison was not run for this setting "
                "(one of the two arms is missing)._"
            )
            lines.append("")
            continue

        para = [
            f"The `generated` mechanism's empirical IC-regret is "
            f"{gen['empirical_ic_regret_max']:.3f} over the run, while its formal "
            f"IC-regret is 0 — the certificate holds in the stylized game; the sim "
            f"shows the gap to a population that violates its assumptions."
        ]
        below: list[str] = []
        if gen["final_accuracy_mean"] < ora["final_accuracy_mean"]:
            below.append("final accuracy")
        if gen["social_welfare_mean"] < ora["social_welfare_mean"]:
            below.append("social welfare")
        if below:
            para.append(
                f"It also **underperforms** `oracle` — it is **below** `oracle` on "
                f"{' and '.join(below)} (honest-framing: reported, not hidden)."
            )
        lines.append(" ".join(para))
        lines.append("")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")
