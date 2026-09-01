"""The cross_device_quadratic generated fixture is a real verified snapshot
(not the placeholder) and the adapter turns it into a working reward hook."""
from __future__ import annotations
import numpy as np
from sim.fedavg import ClientReport, RoundContext
from sim.mechanisms import build_reward_hook
from sim.run import load_generated, GENERATED_IS_PLACEHOLDER


def _rep(cid, q=1.0, dnorm=1.0):
    d = np.zeros((3, 2)); d[0, 0] = dnorm
    return ClientReport(cid, claimed_quality=q, claimed_samples=10,
                        delta_params=d, true_samples=10, true_cost=0.0)


def test_cross_device_generated_is_real_and_usable():
    md = load_generated("cross_device_quadratic")
    assert not GENERATED_IS_PLACEHOLDER.get("cross_device_quadratic", False)
    # verified Contract shape: a client-utility form, no explicit payment rule
    assert "client_utility_latex" in md
    hook = build_reward_hook(md, "cross_device_quadratic", budget=50.0)
    ctx = RoundContext(0, [0, 1], np.zeros((3, 2)), budget=50.0,
                       setting="cross_device_quadratic")
    out = hook([_rep(0, q=1.0, dnorm=0.5), _rep(1, q=1.0, dnorm=2.0)], ctx)
    assert all(p >= 0.0 for p in out.values())
    assert out[1] > out[0]           # more effort -> larger IR-binding reward
    assert sum(out.values()) <= 50.0 + 1e-6


def test_hierarchical_edge_generated_is_real_stackelberg():
    md = load_generated("hierarchical_edge")
    assert not GENERATED_IS_PLACEHOLDER.get("hierarchical_edge", False)
    # verified Stackelberg shape: a follower-utility form p*e - c*k*e^2
    assert "follower_utility_latex" in md
    hook = build_reward_hook(md, "hierarchical_edge", budget=50.0)
    ctx = RoundContext(0, [0, 1, 2], np.zeros((3, 2)), budget=50.0,
                       setting="hierarchical_edge")
    out = hook([_rep(0, q=1.0, dnorm=0.5), _rep(1, q=1.0, dnorm=2.0)], ctx)
    # pay in proportion to contributed effort (the p*e transfer), budget-capped
    assert out[1] > out[0] > 0.0
    assert sum(out.values()) <= 50.0 + 1e-6


def test_generated_ic_regret_contrast(monkeypatch):
    # The headline finding: the Contract mechanism's IC breaks under a quality
    # misreporter (regret > 0); the Stackelberg per-effort price does not.
    import sim.run as run
    tiny = {"n_clients": 12, "clients_per_round": 6, "rounds": 6, "alpha": 0.5,
            "n_features": 8, "n_classes": 3, "n_samples": 600, "budget": 12.0,
            "cost": "quadratic", "cost_coeff_range": (0.5, 1.0),
            "centroid_scale": 0.7, "lr": 0.05, "local_epochs": 2}
    monkeypatch.setitem(run.SETTINGS, "cross_device_quadratic", dict(tiny))
    monkeypatch.setitem(run.SETTINGS, "hierarchical_edge", {**tiny, "cost": "linear"})
    contract = run.run_setting("cross_device_quadratic", "generated", "mixed_60_20_15_5", 0)
    stack = run.run_setting("hierarchical_edge", "generated", "mixed_60_20_15_5", 0)
    assert contract["empirical_ic_regret"] > stack["empirical_ic_regret"]
    assert stack["empirical_ic_regret"] == 0.0
