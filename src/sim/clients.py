"""Client behavioural models for the FL empirical-validation sim.

Each class maps to one row of the spec's strategy table
(docs/superpowers/specs/2026-08-30-fl-simulation-validation-design.md). The value
of the sim is ONLY in the assumption-violating rows; HonestBestResponse is the
sanity baseline.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from sim.fedavg import ClientReport, LogRegModel, RoundContext

BASE_EPOCHS = 8


@dataclass(eq=True)
class Action:
    participate: bool
    claimed_quality: float
    effort: float
    noise_sigma: float
    grad_scale: float


class Client:
    def __init__(self, client_id: int, data_idx: np.ndarray, cost_coeff: float, *, rng_seed: int):
        self.client_id = client_id
        self.data_idx = np.asarray(data_idx, dtype=int)
        self.cost_coeff = cost_coeff
        self.rng = np.random.default_rng(rng_seed)
        self.history: list[dict] = []
        self.cost_fn = lambda e: self.cost_coeff * e ** 2
        self.peer_labels: dict[int, int] = {}
        # Local-training hyperparameters. Defaults preserve the original loop;
        # run.build_population overrides them per-setting so the accuracy curve
        # is a gradual ramp instead of a one-round jump to the model's ceiling.
        self.lr: float = 0.5
        self.base_epochs: int = BASE_EPOCHS

    def decide(self, ctx: RoundContext) -> Action:
        return Action(True, 1.0, 1.0, 0.0, 1.0)

    def _dominant_label(self, y) -> int:
        labels = y[self.data_idx]
        return int(np.bincount(labels).argmax()) if len(labels) else 0

    def _interdependence_multiplier(self, ctx: RoundContext, y) -> float:
        return 1.0

    def make_report(self, global_params, X, y, ctx: RoundContext) -> ClientReport | None:
        action = self.decide(ctx)
        if not action.participate:
            return None
        return self.report_for_action(action, global_params, X, y, ctx)

    def report_for_action(self, action: Action, global_params, X, y,
                          ctx: RoundContext) -> ClientReport:
        """Build the report this client would submit under a GIVEN action, skipping
        ``decide``. Used by the sim's empirical-IC-regret probe to score
        counterfactual deviations for an otherwise-honest client."""
        n_classes = global_params.shape[1]
        model = LogRegModel(X.shape[1], n_classes)
        model.set_params(global_params)
        epochs = max(1, round(self.base_epochs * action.effort))
        new = model.train_local(X[self.data_idx], y[self.data_idx],
                                lr=self.lr, epochs=epochs, batch=32,
                                seed=ctx.round_idx + self.client_id)
        delta = (new - global_params) * action.grad_scale
        if action.noise_sigma > 0:
            delta = delta + self.rng.normal(0.0, action.noise_sigma, size=delta.shape)
        true_cost = self.cost_fn(action.effort) * self._interdependence_multiplier(ctx, y)
        return ClientReport(
            client_id=self.client_id,
            claimed_quality=action.claimed_quality,
            claimed_samples=max(1, round(len(self.data_idx) * action.claimed_quality)),
            delta_params=delta,
            true_samples=len(self.data_idx),
            true_cost=float(true_cost),
        )

    def observe(self, payoff: float, ctx: RoundContext) -> None:
        self.history.append({"payoff": float(payoff), "round": ctx.round_idx})


class HonestBestResponse(Client):
    pass


class DataQualityMisreporter(Client):
    def __init__(self, *args, inflate: float = 1.5, grad_downscale: float = 0.5,
                 noise_sigma: float = 0.1, **kw):
        super().__init__(*args, **kw)
        self.inflate, self.grad_downscale, self.noise_sigma = inflate, grad_downscale, noise_sigma

    def decide(self, ctx):
        return Action(True, self.inflate, 0.5, self.noise_sigma, self.grad_downscale)


class DropoutThreshold(Client):
    def __init__(self, *args, epsilon: float = 0.0, **kw):
        super().__init__(*args, **kw)
        self.epsilon = epsilon

    def decide(self, ctx):
        if ctx.round_idx == 0 or not self.history:
            return Action(True, 1.0, 1.0, 0.0, 1.0)
        recent = [h["payoff"] for h in self.history[-3:]]
        if float(np.mean(recent)) >= self.epsilon:
            return Action(True, 1.0, 1.0, 0.0, 1.0)
        return Action(False, 0.0, 0.0, 0.0, 0.0)


class CoalitionController:
    def __init__(self, member_ids: list[int], claimed_quality: float = 2.0):
        self.member_ids = list(member_ids)
        self.claimed_quality = claimed_quality

    def action_for(self, client_id: int, ctx: RoundContext) -> Action:
        # ponytail: static coordinated over-report, not a solved coalition BR;
        # upgrade to a summed-utility argmax over a joint grid if a finding needs it.
        return Action(True, self.claimed_quality, 0.4, 0.0, 0.8)


class Coalition(Client):
    def __init__(self, *args, controller: CoalitionController, **kw):
        super().__init__(*args, **kw)
        self.controller = controller

    def decide(self, ctx):
        return self.controller.action_for(self.client_id, ctx)


class BoundedRational(Client):
    def __init__(self, *args, epsilon: float = 0.1, **kw):
        super().__init__(*args, **kw)
        self.epsilon = epsilon

    def decide(self, ctx):
        if self.rng.random() < self.epsilon:
            return Action(True, float(self.rng.uniform(0.5, 2.0)),
                          float(self.rng.uniform(0.0, 1.0)), 0.0, 1.0)
        return Action(True, 1.0, 1.0, 0.0, 1.0)


class InterdependentValue(Client):
    def __init__(self, *args, coupling: float = 0.5, **kw):
        super().__init__(*args, **kw)
        self.coupling = coupling

    def _interdependence_multiplier(self, ctx, y) -> float:
        # ponytail: label-overlap proxy for non-IID interdependence; not a true
        # interdependent-value model.
        if not self.peer_labels:
            return 1.0
        mine = self.peer_labels.get(self.client_id, self._dominant_label(y))
        peers = [p for p in ctx.selected if p != self.client_id]
        if not peers:
            return 1.0
        overlap = float(np.mean([self.peer_labels.get(p) == mine for p in peers]))
        return 1.0 + self.coupling * overlap
