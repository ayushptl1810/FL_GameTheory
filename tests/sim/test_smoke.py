from __future__ import annotations
import sim.run as run

TINY = {"n_clients": 4, "clients_per_round": 2, "rounds": 3, "alpha": 0.5,
        "n_features": 8, "n_classes": 3, "n_samples": 200, "budget": 10.0,
        "cost": "quadratic", "cost_coeff_range": (0.5, 1.0)}

EXPECTED_KEYS = {"setting", "arm", "population", "seed", "participation_rate",
                 "final_accuracy", "social_welfare", "empirical_ic_regret",
                 "budget_adherence", "curve_participation", "curve_accuracy"}


def test_run_setting_smoke_all_arms(monkeypatch):
    monkeypatch.setitem(run.SETTINGS, "cross_device_quadratic", TINY)
    for arm in ("none", "oracle", "generated"):
        m = run.run_setting("cross_device_quadratic", arm, "mixed_60_20_15_5", seed=0)
        assert set(m) == EXPECTED_KEYS
        assert 0.0 <= m["participation_rate"] <= 1.0
        assert 0.0 <= m["final_accuracy"] <= 1.0
        assert len(m["curve_accuracy"]) == 3
        assert m["empirical_ic_regret"] >= 0.0
        assert isinstance(m["budget_adherence"], bool)


def test_none_arm_is_budget_ok(monkeypatch):
    monkeypatch.setitem(run.SETTINGS, "cross_device_quadratic", TINY)
    m = run.run_setting("cross_device_quadratic", "none", "all_honest", seed=1)
    assert m["budget_adherence"] is True
