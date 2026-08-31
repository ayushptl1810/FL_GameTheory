"""Minimal NumPy FedAvg loop with a pluggable per-round reward hook.

Empirical-validation layer for docs/superpowers/specs/2026-08-30-fl-simulation-validation-design.md.
Training realism is deliberately not the point; client incentives are.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


def make_data(n_samples: int, n_features: int, n_classes: int, seed: int):
    """Gaussian blobs: one class centroid per class, unit-variance noise.

    The centroids are fixed by ``(n_features, n_classes)`` alone (a dedicated
    generator seeded independently of ``seed``) so that every ``make_data`` call
    with the same shape samples the *same* distribution -- a train split and a
    held-out test split drawn with different ``seed`` values stay comparable.
    ``seed`` controls only which points are drawn.
    """
    centroid_rng = np.random.default_rng(1_000_003 * n_classes + n_features)
    centroids = centroid_rng.normal(0.0, 2.5, size=(n_classes, n_features))
    rng = np.random.default_rng(seed)
    y = rng.integers(0, n_classes, size=n_samples)
    X = centroids[y] + rng.normal(0.0, 1.0, size=(n_samples, n_features))
    return X.astype(np.float64), y.astype(int)


def dirichlet_partition(y: np.ndarray, n_clients: int, alpha: float, seed: int):
    """Label-skewed split: for each class, draw a Dirichlet(alpha) split over clients."""
    rng = np.random.default_rng(seed)
    n_classes = int(y.max()) + 1
    buckets: list[list[int]] = [[] for _ in range(n_clients)]
    for c in range(n_classes):
        idx = np.where(y == c)[0]
        rng.shuffle(idx)
        props = rng.dirichlet(np.full(n_clients, alpha))
        cuts = (np.cumsum(props) * len(idx)).astype(int)[:-1]
        for cli, chunk in enumerate(np.split(idx, cuts)):
            buckets[cli].extend(chunk.tolist())
    # any client left empty steals one row from the largest bucket
    for cli in range(n_clients):
        if not buckets[cli]:
            big = max(range(n_clients), key=lambda k: len(buckets[k]))
            buckets[cli].append(buckets[big].pop())
    return [np.array(sorted(b), dtype=int) for b in buckets]


def _softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


class LogRegModel:
    def __init__(self, n_features: int, n_classes: int):
        self.n_features = n_features
        self.n_classes = n_classes
        self.w = np.zeros((n_features + 1, n_classes))

    def get_params(self) -> np.ndarray:
        return self.w.copy()

    def set_params(self, w: np.ndarray) -> None:
        self.w = np.asarray(w, dtype=np.float64).reshape(self.n_features + 1, self.n_classes).copy()

    def _logits(self, X):
        Xb = np.hstack([X, np.ones((len(X), 1))])
        return Xb @ self.w

    def predict(self, X):
        return np.argmax(self._logits(X), axis=1)

    def accuracy(self, X, y) -> float:
        return float(np.mean(self.predict(X) == y))

    def train_local(self, X, y, *, lr: float, epochs: int, batch: int, seed: int) -> np.ndarray:
        rng = np.random.default_rng(seed)
        w = self.w.copy()
        Xb = np.hstack([X, np.ones((len(X), 1))])
        Y = np.eye(self.n_classes)[y]
        n = len(X)
        for _ in range(epochs):
            order = rng.permutation(n)
            for s in range(0, n, batch):
                bi = order[s:s + batch]
                p = _softmax(Xb[bi] @ w)
                grad = Xb[bi].T @ (p - Y[bi]) / len(bi)
                w -= lr * grad
        return w


@dataclass
class RoundContext:
    round_idx: int
    selected: list[int]
    global_params: np.ndarray
    budget: float
    setting: str


@dataclass
class ClientReport:
    client_id: int
    claimed_quality: float
    claimed_samples: int
    delta_params: np.ndarray
    true_samples: int
    true_cost: float


RewardHook = Callable[[list["ClientReport"], RoundContext], dict[int, float]]


@dataclass
class RunLog:
    rounds: list[dict]
    final_params: np.ndarray


def run_fedavg(*, X, y, partition, test_X, test_y, rounds: int, clients_per_round: int,
               n_classes: int, clients: list, reward_hook: RewardHook, budget: float,
               setting: str, seed: int) -> RunLog:
    rng = np.random.default_rng(seed)
    n_features = X.shape[1]
    model = LogRegModel(n_features, n_classes)
    by_id = {c.client_id: c for c in clients}
    records: list[dict] = []

    for r in range(rounds):
        pick = rng.choice(len(clients), size=min(clients_per_round, len(clients)), replace=False)
        selected = [clients[i].client_id for i in pick]
        gp = model.get_params()
        ctx = RoundContext(r, selected, gp, budget, setting)
        # Accuracy is recorded at the START of the round -- the model the clients
        # actually saw this round. rounds[0]["accuracy"] is therefore the
        # zero-init baseline (spec: "acc[-1] := log.rounds[0] = accuracy of the
        # zero model"); the fully-updated model lives in RunLog.final_params.
        round_accuracy = model.accuracy(test_X, test_y)

        reports: list[ClientReport] = []
        for cid in selected:
            rep = by_id[cid].make_report(gp, X, y, ctx)
            if rep is not None:
                reports.append(rep)

        if reports:
            wsum = sum(max(rep.claimed_samples, 0) for rep in reports) or len(reports)
            agg = np.zeros_like(gp)
            for rep in reports:
                wt = (max(rep.claimed_samples, 0) or 1) / wsum
                agg += wt * rep.delta_params
            model.set_params(gp + agg)

        payments = reward_hook(reports, ctx)
        for rep in reports:
            pay = float(payments.get(rep.client_id, 0.0))
            by_id[rep.client_id].observe(pay - rep.true_cost, ctx)

        records.append({
            "round_idx": r,
            "accuracy": round_accuracy,
            "participation_rate": len(reports) / len(selected) if selected else 0.0,
            "payments": {rep.client_id: float(payments.get(rep.client_id, 0.0)) for rep in reports},
            "reports": reports,
        })

    return RunLog(records, model.get_params())
