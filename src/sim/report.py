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
    """8-level block sparkline on an ABSOLUTE [0, 1] scale (participation and
    accuracy curves are both proportions). Absolute scaling -- rather than
    per-series min/max -- keeps a flat 100% curve reading as a full bar instead
    of an empty one, and stops a 0.7-0.9 wobble from being stretched to look
    like a full-range swing. Series longer than 40 points are evenly subsampled.
    """
    if not values:
        return ""
    take = min(len(values), 40)
    idx = [round(i * (len(values) - 1) / (take - 1)) if take > 1 else 0 for i in range(take)]
    span = len(_RAMP) - 1
    out = []
    for i in idx:
        v = min(1.0, max(0.0, float(values[i])))
        out.append(_RAMP[int(round(v * span))])
    return "".join(out)


def _cell(mean: float, std: float) -> str:
    return f"{mean:.3f} ± {std:.3f}"


# Empirical IC-regret at or below this is "effectively zero" -- the coarse-grid
# deviation probe has this much numerical slack.
_IC_MATERIAL = 0.05


def _materially_worse(a: float, b: float, sa: float, sb: float, floor: float) -> bool:
    """True iff a is worse (lower) than b by more than measurement noise:
    the gap must clear both an absolute floor and 2x the pooled seed std."""
    return (b - a) > max(floor, 2.0 * (sa ** 2 + sb ** 2) ** 0.5)


_PREAMBLE = (
    "Each arm runs the same FedAvg task (synthetic non-IID data, T=30 rounds, "
    "logistic-regression model) against a **mixed client population** — 60% "
    "honest, 20% data-quality misreporters, 15% dropout-threshold, 5% coalition "
    "— that violates the mechanism's formal assumptions. `none` pays nothing; "
    "`oracle` is a hand-designed reward rule; `generated` is the mechanism the "
    "Architect loop produced and the verifier certified for that setting.\n\n"
    "**Reading the metrics.** `final acc` is near-flat across arms by "
    "construction: with a convex model every arm reaches the same optimum "
    "within T, so accuracy is not where a reward rule shows its effect — "
    "*participation*, *empirical IC-regret*, and *social welfare* are. "
    "`social welfare` = realised accuracy-gain value − real effort cost "
    "(payments are transfers and cancel); `budget ok` is the separate check "
    "that payments stayed within budget. Empirical IC-regret is the max "
    "realised gain any probed honest client got by deviating — it can be "
    "nonzero even when the formal certificate proves it is 0, and that gap is "
    "the point of this layer."
)


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
    lines.append(_PREAMBLE)
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

        non = next((r for r in rows if r["arm"] == "none"), None)
        icr = gen["empirical_ic_regret_max"]
        para: list[str] = []

        # --- IC axis: does the certificate's guarantee survive deployment? ---
        if icr <= _IC_MATERIAL:
            para.append(
                f"Empirical IC-regret for `generated` is {icr:.3f} — effectively "
                f"zero: the certificate's incentive guarantee held against the "
                f"assumption-violating population, not only in the stylized game."
            )
        else:
            para.append(
                f"Empirical IC-regret for `generated` is **{icr:.3f}**, while its "
                f"formal IC-regret is 0. The certificate holds in the stylized "
                f"game; the sim shows a real deployment gap — a client in this "
                f"population gains ≈{icr:.2f} by deviating from honest reporting "
                f"(here by over-stating data quality, which the mechanism's "
                f"verifiable-output assumption rules out)."
            )

        # --- final accuracy: material gap vs seed noise ---
        ga, oa = gen["final_accuracy_mean"], ora["final_accuracy_mean"]
        if _materially_worse(ga, oa, gen["final_accuracy_std"], ora["final_accuracy_std"], 0.01):
            para.append(
                f"`generated` trails `oracle` on final accuracy "
                f"({ga:.3f} vs {oa:.3f}) — reported, not hidden."
            )
        else:
            para.append(
                f"`generated` and `oracle` are statistically indistinguishable on "
                f"final accuracy ({ga:.3f} vs {oa:.3f})."
            )

        # --- social welfare: which way, and is it material ---
        gw, ow = gen["social_welfare_mean"], ora["social_welfare_mean"]
        gws, ows = gen["social_welfare_std"], ora["social_welfare_std"]
        if _materially_worse(gw, ow, gws, ows, 1.0):
            para.append(f"It is **below** `oracle` on social welfare ({gw:.1f} vs {ow:.1f}).")
        elif _materially_worse(ow, gw, ows, gws, 1.0):
            para.append(
                f"It attains **higher** social welfare than `oracle` "
                f"({gw:.1f} vs {ow:.1f}): `oracle` buys full participation, but the "
                f"marginal effort cost of the retained contributors outweighs their "
                f"marginal accuracy value in this setting."
            )

        # --- participation vs the no-reward baseline ---
        if non is not None:
            gp, npp = gen["participation_rate_mean"], non["participation_rate_mean"]
            if _materially_worse(npp, gp, non["participation_rate_std"],
                                 gen["participation_rate_std"], 0.02):
                para.append(
                    f"`generated` lifts participation over `none` "
                    f"({gp:.3f} vs {npp:.3f})."
                )
            else:
                para.append(
                    f"`generated` does **not** lift participation over `none` "
                    f"({gp:.3f} vs {npp:.3f}) — its reward at the certified "
                    f"IR-binding point is too small to retain the dropout-prone "
                    f"clients (IR is satisfied as ≥ 0, not > 0)."
                )

        lines.append(" ".join(para))
        lines.append("")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")
