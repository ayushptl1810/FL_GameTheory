from __future__ import annotations
import numpy as np
import pytest
from sim.fedavg import ClientReport, RoundContext
from sim.mechanisms import build_reward_hook, zero_reward_hook


def _rep(cid, q=1.0, dnorm=1.0):
    d = np.zeros((3, 2)); d[0, 0] = dnorm
    return ClientReport(cid, claimed_quality=q, claimed_samples=10, delta_params=d,
                        true_samples=10, true_cost=0.0)


def _ctx(budget=5.0):
    return RoundContext(0, [0, 1], np.zeros((3, 2)), budget=budget, setting="unit")


def test_zero_hook_pays_nothing():
    assert zero_reward_hook([_rep(0), _rep(1)], _ctx()) == {}


def test_callable_mechanism_passthrough_and_budget_clamp():
    raw = lambda reports, ctx: {r.client_id: 10.0 for r in reports}
    hook = build_reward_hook(raw, "unit", budget=5.0)
    out = hook([_rep(0), _rep(1)], _ctx(budget=5.0))
    assert pytest.approx(sum(out.values())) == 5.0
    assert out[0] == out[1] == 2.5


def test_callable_negative_payment_clamped_to_zero():
    raw = lambda reports, ctx: {0: -3.0, 1: 4.0}
    hook = build_reward_hook(raw, "unit", budget=100.0)
    out = hook([_rep(0), _rep(1)], _ctx(budget=100.0))
    assert out[0] == 0.0 and out[1] == 4.0


def test_mechanism_dict_latex_builds_a_hook():
    mdict = {"payment_rule_latex": r"p_i = q_i", "client_utility_latex": r"u_i = q_i - p_i"}
    hook = build_reward_hook(mdict, "unit", budget=100.0)
    out = hook([_rep(0, q=1.0), _rep(1, q=3.0)], _ctx(budget=100.0))
    assert out[1] > out[0] > 0.0
