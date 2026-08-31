from __future__ import annotations
import numpy as np
from sim.fedavg import make_data, RoundContext
from sim.clients import (
    Action, HonestBestResponse, DataQualityMisreporter, DropoutThreshold,
    Coalition, CoalitionController, BoundedRational, InterdependentValue,
)

X, Y = make_data(400, 6, 3, seed=0)
IDX = np.arange(0, 40)


def _ctx(rnd=0, selected=(0,)):
    return RoundContext(rnd, list(selected), np.zeros((7, 3)), budget=10.0, setting="unit")


def test_honest_participates_truthfully():
    c = HonestBestResponse(0, IDX, 1.0, rng_seed=0)
    a = c.decide(_ctx())
    assert a.participate and a.claimed_quality == 1.0 and a.grad_scale == 1.0
    rep = c.make_report(np.zeros((7, 3)), X, Y, _ctx())
    assert rep.claimed_samples == rep.true_samples


def test_misreporter_inflates_quality_and_downscales_gradient():
    c = DataQualityMisreporter(0, IDX, 1.0, rng_seed=0, inflate=1.5, grad_downscale=0.5)
    rep = c.make_report(np.zeros((7, 3)), X, Y, _ctx())
    assert rep.claimed_quality == 1.5
    assert rep.claimed_samples > rep.true_samples


def test_dropout_leaves_after_negative_payoffs():
    c = DropoutThreshold(0, IDX, 1.0, rng_seed=0, epsilon=0.0)
    assert c.decide(_ctx(rnd=0)).participate is True
    for r in range(1, 4):
        c.observe(-1.0, _ctx(rnd=r))
    assert c.decide(_ctx(rnd=4)).participate is False


def test_dropout_stays_when_payoff_above_epsilon():
    c = DropoutThreshold(0, IDX, 1.0, rng_seed=0, epsilon=0.0)
    for r in range(1, 4):
        c.observe(2.0, _ctx(rnd=r))
    assert c.decide(_ctx(rnd=4)).participate is True


def test_coalition_members_all_over_report_same_quality():
    ctrl = CoalitionController(member_ids=[0, 1], claimed_quality=2.0)
    a0 = Coalition(0, IDX, 1.0, rng_seed=0, controller=ctrl).decide(_ctx(selected=(0, 1)))
    a1 = Coalition(1, IDX, 1.0, rng_seed=1, controller=ctrl).decide(_ctx(selected=(0, 1)))
    assert a0.claimed_quality == a1.claimed_quality == 2.0


def test_bounded_rational_is_honest_when_epsilon_zero():
    c = BoundedRational(0, IDX, 1.0, rng_seed=0, epsilon=0.0)
    assert c.decide(_ctx()) == Action(True, 1.0, 1.0, 0.0, 1.0)


def test_interdependent_value_raises_cost_with_label_overlap():
    hi = InterdependentValue(0, IDX, 1.0, rng_seed=0, coupling=1.0)
    hi.peer_labels = {0: 1, 1: 1, 2: 1}
    rep = hi.make_report(np.zeros((7, 3)), X, Y, _ctx(selected=(0, 1, 2)))
    lo = InterdependentValue(0, IDX, 1.0, rng_seed=0, coupling=1.0)
    lo.peer_labels = {0: 1, 1: 2, 2: 2}
    rep0 = lo.make_report(np.zeros((7, 3)), X, Y, _ctx(selected=(0, 1, 2)))
    assert rep.true_cost > rep0.true_cost
