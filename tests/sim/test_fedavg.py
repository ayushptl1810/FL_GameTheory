from __future__ import annotations
import numpy as np
from sim.fedavg import make_data, dirichlet_partition, LogRegModel, run_fedavg, ClientReport


def test_make_data_shape_and_range():
    X, y = make_data(200, 8, 3, seed=0)
    assert X.shape == (200, 8)
    assert y.shape == (200,)
    assert set(np.unique(y)).issubset({0, 1, 2})


def test_dirichlet_partition_is_disjoint_cover():
    _, y = make_data(300, 6, 3, seed=1)
    parts = dirichlet_partition(y, n_clients=10, alpha=0.3, seed=1)
    assert len(parts) == 10
    allidx = np.concatenate(parts)
    assert np.array_equal(np.sort(allidx), np.arange(300))


def test_logreg_learns_iid():
    X, y = make_data(600, 8, 3, seed=2)
    m = LogRegModel(8, 3)
    start = m.accuracy(X, y)
    new = m.train_local(X, y, lr=0.5, epochs=40, batch=64, seed=2)
    m.set_params(new)
    assert m.accuracy(X, y) > start + 0.15


class _StubClient:
    def __init__(self, cid, idx):
        self.client_id = cid
        self.data_idx = idx
        self.seen = []

    def make_report(self, global_params, X, y, ctx):
        m = LogRegModel(X.shape[1], int(y.max()) + 1)
        m.set_params(global_params)
        new = m.train_local(X[self.data_idx], y[self.data_idx], lr=0.5, epochs=5, batch=32, seed=ctx.round_idx)
        return ClientReport(self.client_id, claimed_quality=1.0, claimed_samples=len(self.data_idx),
                            delta_params=new - global_params, true_samples=len(self.data_idx), true_cost=0.0)

    def observe(self, payoff, ctx):
        self.seen.append(payoff)


def test_run_fedavg_improves_accuracy_and_logs_rounds():
    X, y = make_data(800, 8, 3, seed=3)
    parts = dirichlet_partition(y, 8, alpha=10.0, seed=3)  # near-IID
    tX, tY = make_data(300, 8, 3, seed=99)
    clients = [_StubClient(i, p) for i, p in enumerate(parts)]
    log = run_fedavg(X=X, y=y, partition=parts, test_X=tX, test_y=tY, rounds=12,
                     clients_per_round=4, n_classes=3, clients=clients,
                     reward_hook=lambda reports, ctx: {r.client_id: 1.0 for r in reports},
                     budget=10.0, setting="unit", seed=3)
    assert len(log.rounds) == 12
    assert set(log.rounds[0]) == {"round_idx", "accuracy", "participation_rate", "payments", "reports"}
    assert log.rounds[-1]["accuracy"] > log.rounds[0]["accuracy"]
    assert 0.0 <= log.rounds[0]["participation_rate"] <= 1.0
