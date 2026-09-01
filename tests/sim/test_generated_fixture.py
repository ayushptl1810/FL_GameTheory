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
