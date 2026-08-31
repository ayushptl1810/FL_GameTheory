"""Settings, populations, and the single-run driver for the FL empirical-
validation sim (docs/superpowers/specs/2026-08-30-fl-simulation-validation-design.md).

`run_setting(setting, arm, population, seed) -> metrics dict` executes one
(setting, arm, population, seed) cell of the grid; `main()` sweeps the grid over
seeds and hands the results to `report.write_report`.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from sim.clients import (
    Action, Client, Coalition, CoalitionController, DataQualityMisreporter,
    DropoutThreshold, HonestBestResponse,
)
from sim.fedavg import LogRegModel, dirichlet_partition, make_data, run_fedavg
from sim.mechanisms import build_reward_hook, zero_reward_hook
from sim import oracle_mechanisms

SETTINGS: dict[str, dict] = {
    "cross_device_quadratic": {
        "n_clients": 50, "clients_per_round": 10, "rounds": 30, "alpha": 0.3,
        "n_features": 16, "n_classes": 3, "n_samples": 6000, "budget": 50.0,
        "cost": "quadratic", "cost_coeff_range": (0.5, 2.0),
    },
    # 5 edge x 10 device, modelled flat with edge_id = client_id // 10.
    "hierarchical_edge": {
        "n_clients": 50, "clients_per_round": 10, "rounds": 30, "alpha": 0.5,
        "n_features": 16, "n_classes": 3, "n_samples": 6000, "budget": 50.0,
        "cost": "linear", "cost_coeff_range": (0.3, 1.0),
    },
}

POPULATIONS: dict[str, list[tuple[float, type, dict]]] = {
    "mixed_60_20_15_5": [
        (0.60, HonestBestResponse, {}),
        (0.20, DataQualityMisreporter,
         {"inflate": 1.5, "grad_downscale": 0.5, "noise_sigma": 0.1}),
        (0.15, DropoutThreshold, {"epsilon": 0.0}),
        (0.05, Coalition, {}),
    ],
    "all_honest": [(1.0, HonestBestResponse, {})],
}

# Set as a side effect of load_generated: setting -> True iff its fixture JSON is
# an explicitly-labelled placeholder. report.write_report reads this to decide
# whether to stamp the "placeholder mechanism" banner.
GENERATED_IS_PLACEHOLDER: dict[str, bool] = {}

_IC_GRID_QUALITY = (0.5, 1.0, 1.5, 2.0)
_IC_GRID_GRAD_SCALE = (0.5, 1.0)


def _largest_remainder(fractions: list[float], total: int) -> list[int]:
    raw = [f * total for f in fractions]
    base = [int(np.floor(x)) for x in raw]
    short = total - sum(base)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - base[i], reverse=True)
    for i in order[:short]:
        base[i] += 1
    return base


def build_population(setting: str, pop_name: str, seed: int,
                     partition: list[np.ndarray], y: np.ndarray) -> list[Client]:
    cfg = SETTINGS[setting]
    n = cfg["n_clients"]
    spec = POPULATIONS[pop_name]
    counts = _largest_remainder([frac for frac, _, _ in spec], n)

    # contiguous type blocks over client ids 0..n-1, in POPULATIONS order
    assign: list[tuple[type, dict]] = []
    for (_, cls, kw), cnt in zip(spec, counts):
        assign.extend([(cls, kw)] * cnt)
    assert len(assign) == n

    coalition_ids = [cid for cid, (cls, _) in enumerate(assign) if cls is Coalition]
    controller = CoalitionController(member_ids=coalition_ids)

    coeff_rng = np.random.default_rng(seed)
    lo, hi = cfg["cost_coeff_range"]
    coeffs = coeff_rng.uniform(lo, hi, n)
    linear = cfg["cost"] == "linear"

    clients: list[Client] = []
    for cid in range(n):
        cls, kw = assign[cid]
        kw = dict(kw)
        if cls is Coalition:
            kw["controller"] = controller
        c = cls(cid, partition[cid], float(coeffs[cid]), rng_seed=seed * 1000 + cid, **kw)
        cc = float(coeffs[cid])
        c.cost_fn = (lambda e, _cc=cc: _cc * e) if linear else (lambda e, _cc=cc: _cc * e ** 2)
        clients.append(c)

    labels = {cid: int(np.bincount(y[partition[cid]]).argmax()) for cid in range(n)}
    for c in clients:
        c.peer_labels = dict(labels)
    return clients


def load_generated(setting: str) -> dict:
    path = Path(__file__).parent / "fixtures" / "generated" / f"{setting}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"run the Architect loop for {setting} and snapshot "
            f"ArchitectResult.mechanism_dict into {path}"
        )
    data = json.loads(path.read_text())
    GENERATED_IS_PLACEHOLDER[setting] = "PLACEHOLDER" in str(data.get("note", ""))
    return data["mechanism_dict"]


def get_mechanism(arm: str, setting: str):
    if arm == "none":
        return zero_reward_hook
    if arm == "oracle":
        return oracle_mechanisms.ORACLES[setting]
    if arm == "generated":
        return load_generated(setting)
    raise ValueError(f"unknown arm {arm!r}")


def _empirical_ic_regret(clients, log, hook, X, y) -> float:
    by_id = {c.client_id: c for c in clients}
    honest_ids = [c.client_id for c in clients if type(c) is HonestBestResponse][:5]
    worst = 0.0
    probed = False
    for cid in honest_ids:
        appears = [r for r, rec in enumerate(log.rounds)
                   if any(rep.client_id == cid for rep in rec["reports"])][:5]
        for r in appears:
            rec = log.rounds[r]
            ctx = log.contexts[r]
            gp = ctx.global_params
            honest_rep = next(rep for rep in rec["reports"] if rep.client_id == cid)
            honest_payoff = rec["payments"].get(cid, 0.0) - honest_rep.true_cost
            best_alt = honest_payoff
            for q in _IC_GRID_QUALITY:
                for gs in _IC_GRID_GRAD_SCALE:
                    alt_action = Action(True, q, 1.0, 0.0, gs)
                    alt_rep = by_id[cid].report_for_action(alt_action, gp, X, y, ctx)
                    alt_reports = [alt_rep if rep.client_id == cid else rep
                                   for rep in rec["reports"]]
                    alt_pay = hook(alt_reports, ctx).get(cid, 0.0)
                    best_alt = max(best_alt, alt_pay - alt_rep.true_cost)
            probed = True
            worst = max(worst, max(0.0, best_alt - honest_payoff))
    # ponytail: single-round coarse-grid deviation probe, not a full best-response solve.
    return worst if probed else 0.0


def run_setting(setting: str, arm: str, population: str, seed: int) -> dict:
    cfg = SETTINGS[setting]
    X, y = make_data(cfg["n_samples"], cfg["n_features"], cfg["n_classes"], seed)
    test_X, test_y = make_data(2000, cfg["n_features"], cfg["n_classes"], seed + 10_000)
    partition = dirichlet_partition(y, cfg["n_clients"], cfg["alpha"], seed)
    clients = build_population(setting, population, seed, partition, y)
    hook = build_reward_hook(get_mechanism(arm, setting), setting, budget=cfg["budget"])

    log = run_fedavg(
        X=X, y=y, partition=partition, test_X=test_X, test_y=test_y,
        rounds=cfg["rounds"], clients_per_round=cfg["clients_per_round"],
        n_classes=cfg["n_classes"], clients=clients, reward_hook=hook,
        budget=cfg["budget"], setting=setting, seed=seed,
    )

    curve_accuracy = [rec["accuracy"] for rec in log.rounds]
    curve_participation = [rec["participation_rate"] for rec in log.rounds]

    # realised-accuracy-gain value proxy; not a utility from the mechanism's own
    # value function. acc[r] is recorded at the START of round r, so rounds[0] is
    # the zero-init baseline already -- acc_prev shifts by one with that same
    # baseline pinned in front.
    zero_baseline = LogRegModel(cfg["n_features"], cfg["n_classes"]).accuracy(test_X, test_y)
    acc_prev = [zero_baseline] + curve_accuracy[:-1]
    acc_gain = [a - p for a, p in zip(curve_accuracy, acc_prev)]
    n_reports = [len(rec["reports"]) for rec in log.rounds]
    sum_client_value = sum(g * n for g, n in zip(acc_gain, n_reports))
    sum_true_cost = sum(rep.true_cost for rec in log.rounds for rep in rec["reports"])
    sum_payments = sum(sum(rec["payments"].values()) for rec in log.rounds)
    server_value = sum(g * 10 for g in acc_gain)
    social_welfare = sum_client_value - sum_true_cost - sum_payments + server_value

    # final_accuracy is the fully-updated model (RunLog.final_params); the last
    # curve entry is pre-update for round T-1, one aggregation behind.
    final_model = LogRegModel(cfg["n_features"], cfg["n_classes"])
    final_model.set_params(log.final_params)
    final_accuracy = final_model.accuracy(test_X, test_y)

    budget_adherence = all(
        sum(rec["payments"].values()) <= cfg["budget"] + 1e-6 for rec in log.rounds
    )

    return {
        "setting": setting,
        "arm": arm,
        "population": population,
        "seed": seed,
        "participation_rate": float(np.mean(curve_participation)) if curve_participation else 0.0,
        "final_accuracy": float(final_accuracy),
        "social_welfare": float(social_welfare),
        "empirical_ic_regret": float(_empirical_ic_regret(clients, log, hook, X, y)),
        "budget_adherence": bool(budget_adherence),
        "curve_participation": curve_participation,
        "curve_accuracy": curve_accuracy,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="FL empirical-validation sim runner")
    ap.add_argument("--setting", default="cross_device_quadratic", choices=list(SETTINGS))
    ap.add_argument("--arm", action="append", default=None,
                    help="repeatable; default: none oracle generated")
    ap.add_argument("--population", default="mixed_60_20_15_5", choices=list(POPULATIONS))
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--out", default="docs/sim-results.md")
    args = ap.parse_args(argv)
    arms = args.arm or ["none", "oracle", "generated"]

    from sim import report

    all_results = []
    for arm in arms:
        for seed in args.seeds:
            m = run_setting(args.setting, arm, args.population, seed)
            print(m)
            all_results.append(m)

    report.write_report(report.aggregate(all_results), path=args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
