# FL Simulation — Empirical Validation Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small federated-learning simulator that runs a verified mechanism against clients that *violate* the mechanism's assumptions, and reports where deployment behaviour diverges from the formal certificate.

**Architecture:** A NumPy-only FedAvg loop (multinomial logistic regression on a synthetic non-IID classification task — no PyTorch, no dataset download) exposes a per-round *reward hook*. Six pluggable `Client` strategy classes each implement `decide()`. An adapter turns a mechanism (a plain callable, an `architect.ast.Mechanism`, or a `mechanism_dict`) into that reward hook by reusing `architect.serialize.ast_to_sympy` + `sympy.lambdify` exactly as `src/architect/mc.py` does. `run_setting()` executes one (setting, arm, population, seed) and returns a metrics dict; `report.py` aggregates seeds into `docs/sim-results.md`.

**Tech Stack:** Python 3.14, NumPy, SymPy (all already used by `src/architect`). No new dependencies. No `torch`/`torchvision` (not installed; spec explicitly says "training realism is not the point").

**Spec:** `docs/superpowers/specs/2026-08-30-fl-simulation-validation-design.md`

## Global Constraints

- **No new dependencies.** NumPy + SymPy only. If a step seems to need `torch`, `torchvision`, `sklearn`, or `matplotlib`, use the NumPy/text fallback specified in that task.
- **Package path:** all runtime code under `src/sim/`, all tests under `tests/sim/`. Match existing repo style: `from __future__ import annotations` header, dataclasses for records, module-level docstring naming the spec.
- **Deterministic:** every function that samples takes an explicit `seed: int`. No global RNG. Use `np.random.default_rng(seed)`.
- **Honest-framing (spec §"Honest-framing rules"):** client models are declared with their parameters in `POPULATIONS`; `generated` mechanism is whatever is loaded from its fixture, never edited to look good; a `VERIFIED` mechanism that underperforms `oracle` or shows nonzero empirical IC-regret is written to the report as-is.
- **Scope ceiling (spec §"Non-goals / ceiling"):** flat per-round cost only (no stragglers/bandwidth). No n−1 collusion, no adaptive adversaries, no Byzantine robustness. 1–2 settings, ≤50 clients, T≤30.
- **Mechanism-under-test is never modified by the sim** (spec §"What it is NOT"). The adapter is read-only over the mechanism.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/sim/__init__.py` | empty package marker |
| `src/sim/fedavg.py` | synthetic data, Dirichlet partition, `LogRegModel`, `run_fedavg` loop, `ClientReport`/`RoundContext`/`RunLog` records, `RewardHook` type |
| `src/sim/clients.py` | `Action`, `Client` base, the 6 strategy subclasses |
| `src/sim/mechanisms.py` | `build_reward_hook(mechanism, setting, budget) -> RewardHook`; `zero_reward_hook` |
| `src/sim/oracle_mechanisms.py` | hand-designed reward callables, one per setting, ported from the closest corpus paper |
| `src/sim/run.py` | `SETTINGS`, `POPULATIONS`, `build_population`, `get_mechanism`, `run_setting`, `main()` CLI |
| `src/sim/report.py` | `aggregate`, `write_report` → `docs/sim-results.md` (markdown table + text sparkline) |
| `src/sim/fixtures/generated/<setting>.json` | the mechanism the Architect loop produced for that setting (checked-in snapshot) |
| `tests/sim/__init__.py` | empty |
| `tests/sim/test_fedavg.py` | accuracy rises on IID synthetic data |
| `tests/sim/test_clients.py` | one hand-checked scenario per `decide` |
| `tests/sim/test_mechanisms.py` | callable passthrough + AST→hook on a trivial VCG mechanism + budget renormalisation |
| `tests/sim/test_report.py` | seed aggregation + sparkline + report writer |
| `tests/sim/test_smoke.py` | end-to-end `run_setting` (2–4 clients, 3 rounds) returns the full metrics dict shape |

---

## Task 1: FedAvg core (data, partition, model, loop)

**Files:**
- Create: `src/sim/__init__.py` (empty)
- Create: `src/sim/fedavg.py`
- Create: `tests/sim/__init__.py` (empty)
- Test: `tests/sim/test_fedavg.py`

**Interfaces:**
- Consumes: nothing (leaf task).
- Produces:
  - `make_data(n_samples: int, n_features: int, n_classes: int, seed: int) -> tuple[np.ndarray, np.ndarray]` — `X` shape `(n_samples, n_features)` float64, `y` shape `(n_samples,)` int in `[0, n_classes)`.
  - `dirichlet_partition(y: np.ndarray, n_clients: int, alpha: float, seed: int) -> list[np.ndarray]` — list of int index arrays into `y`, disjoint, union covers all rows. `alpha` small ⇒ skewed.
  - `class LogRegModel` with `__init__(self, n_features: int, n_classes: int)`, `get_params() -> np.ndarray` (shape `(n_features+1, n_classes)`, last row = bias), `set_params(self, w: np.ndarray) -> None`, `predict(self, X) -> np.ndarray`, `accuracy(self, X, y) -> float`, `train_local(self, X, y, *, lr: float, epochs: int, batch: int, seed: int) -> np.ndarray` (returns new params, does not mutate global).
  - `@dataclass RoundContext: round_idx: int; selected: list[int]; global_params: np.ndarray; budget: float; setting: str`
  - `@dataclass ClientReport: client_id: int; claimed_quality: float; claimed_samples: int; delta_params: np.ndarray; true_samples: int; true_cost: float`
  - `RewardHook = Callable[[list[ClientReport], RoundContext], dict[int, float]]` (payment per client id; ids absent ⇒ 0)
  - `@dataclass RunLog: rounds: list[dict]; final_params: np.ndarray` — each `rounds[i]` dict has keys `round_idx, accuracy, participation_rate, payments (dict[int,float]), reports (list[ClientReport])`.
  - `run_fedavg(*, X, y, partition, test_X, test_y, rounds: int, clients_per_round: int, n_classes: int, clients: list, reward_hook: RewardHook, budget: float, setting: str, seed: int) -> RunLog` — `clients` is a list of objects exposing `client_id: int`, `data_idx: np.ndarray`, `make_report(global_params, X, y, ctx) -> ClientReport | None` (None = abstained), `observe(payoff: float, ctx) -> None`. FedAvg aggregation weights each accepted client's `delta_params` by `claimed_samples / sum(claimed_samples)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/sim/test_fedavg.py
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/sim/test_fedavg.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sim'` (or import errors).

- [ ] **Step 3: Implement `src/sim/fedavg.py`**

```python
"""Minimal NumPy FedAvg loop with a pluggable per-round reward hook.

Empirical-validation layer for docs/superpowers/specs/2026-08-30-fl-simulation-validation-design.md.
Training realism is deliberately not the point; client incentives are.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


def make_data(n_samples: int, n_features: int, n_classes: int, seed: int):
    """Gaussian blobs: one random class centroid per class, unit-variance noise."""
    rng = np.random.default_rng(seed)
    centroids = rng.normal(0.0, 2.5, size=(n_classes, n_features))
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
            "accuracy": model.accuracy(test_X, test_y),
            "participation_rate": len(reports) / len(selected) if selected else 0.0,
            "payments": {rep.client_id: float(payments.get(rep.client_id, 0.0)) for rep in reports},
            "reports": reports,
        })

    return RunLog(records, model.get_params())
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/sim/test_fedavg.py -v`
Expected: PASS (4 tests). If `test_logreg_learns_iid` is flaky, raise `epochs` to 60 — do not lower the `+0.15` threshold.

- [ ] **Step 5: Commit**

```bash
git add src/sim/__init__.py src/sim/fedavg.py tests/sim/__init__.py tests/sim/test_fedavg.py
git commit -m "feat(sim): NumPy FedAvg core with pluggable reward hook"
```

---

## Task 2: Client strategy models

**Files:**
- Create: `src/sim/clients.py`
- Test: `tests/sim/test_clients.py`

**Interfaces:**
- Consumes: `sim.fedavg.ClientReport`, `sim.fedavg.LogRegModel`, `sim.fedavg.RoundContext`.
- Produces:
  - `@dataclass Action: participate: bool; claimed_quality: float; effort: float; noise_sigma: float; grad_scale: float` — `effort ∈ [0,1]` scales local `epochs`; `grad_scale` multiplies the submitted `delta_params`; `noise_sigma` adds N(0,σ) noise to it.
  - `class Client` base: `__init__(self, client_id: int, data_idx: np.ndarray, cost_coeff: float, *, rng_seed: int)`. Attributes: `client_id`, `data_idx`, `cost_coeff`, `history: list[dict]` (each `{"payoff": float, "round": int}`), `cost_fn: Callable[[float], float]` (default quadratic `cost_coeff * e**2`; `run.py` may reassign), `peer_labels: dict[int,int]` (default `{}`). Methods:
    - `decide(self, ctx: RoundContext) -> Action` — overridden per subclass; base returns `Action(True, 1.0, 1.0, 0.0, 1.0)`.
    - `make_report(self, global_params, X, y, ctx) -> ClientReport | None` — calls `decide`; if `not action.participate` returns `None`; else trains locally with `epochs = max(1, round(BASE_EPOCHS * action.effort))`, applies `grad_scale` then adds `noise_sigma` noise to the delta, computes `true_cost = cost_fn(action.effort) * _interdependence_multiplier(ctx, y)`, sets `claimed_quality = action.claimed_quality`, `claimed_samples = max(1, round(len(data_idx) * action.claimed_quality))`, `true_samples = len(data_idx)`.
    - `_interdependence_multiplier(self, ctx, y) -> float` — base returns `1.0`.
    - `observe(self, payoff: float, ctx) -> None` — appends `{"payoff": float(payoff), "round": ctx.round_idx}`.
  - Subclasses (constructor kwargs after the base ones):
    - `HonestBestResponse` — no extra kwargs.
    - `DataQualityMisreporter(inflate: float = 1.5, grad_downscale: float = 0.5, noise_sigma: float = 0.1)` — `decide` → `Action(True, inflate, 0.5, noise_sigma, grad_downscale)`.
    - `DropoutThreshold(epsilon: float = 0.0)` — participates on round 0 or with empty history; thereafter participates iff `mean(last≤3 history payoffs) >= epsilon`, else `Action(False, 0,0,0,0)`.
    - `CoalitionController(member_ids: list[int], claimed_quality: float = 2.0)` with `action_for(client_id, ctx) -> Action(True, claimed_quality, 0.4, 0.0, 0.8)`.
    - `Coalition(controller: CoalitionController)` — `decide` → `controller.action_for(self.client_id, ctx)`.
    - `BoundedRational(epsilon: float = 0.1)` — with prob `epsilon` (own RNG) a random `Action` (`claimed_quality∈U[0.5,2]`, `effort∈U[0,1]`, `noise_sigma=0`, `grad_scale=1`), else honest.
    - `InterdependentValue(coupling: float = 0.5)` — honest `decide`; `_interdependence_multiplier` = `1 + coupling * overlap` where `overlap` = mean over `ctx.selected` peers (excluding self) of `peer_labels[peer] == peer_labels[self]`; `1.0` if `peer_labels` empty or no peers.
  - Module constant `BASE_EPOCHS = 8`.

- [ ] **Step 1: Write the failing test**

```python
# tests/sim/test_clients.py
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/sim/test_clients.py -v`
Expected: FAIL — `No module named 'sim.clients'`.

- [ ] **Step 3: Implement `src/sim/clients.py`**

```python
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
        n_classes = global_params.shape[1]
        model = LogRegModel(X.shape[1], n_classes)
        model.set_params(global_params)
        epochs = max(1, round(BASE_EPOCHS * action.effort))
        new = model.train_local(X[self.data_idx], y[self.data_idx],
                                lr=0.5, epochs=epochs, batch=32,
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
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/sim/test_clients.py -v`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add src/sim/clients.py tests/sim/test_clients.py
git commit -m "feat(sim): six client behavioural models (spec strategy table)"
```

---

## Task 3: Mechanism → reward-hook adapter

**Files:**
- Create: `src/sim/mechanisms.py`
- Test: `tests/sim/test_mechanisms.py`

**Interfaces:**
- Consumes: `sim.fedavg.RewardHook`, `sim.fedavg.ClientReport`, `sim.fedavg.RoundContext`; `architect.serialize.ast_to_sympy`; `architect.ast.Mechanism`.
- Produces:
  - `zero_reward_hook(reports, ctx) -> dict[int, float]` — returns `{}` (the `none` arm).
  - `_effort_proxy(report) -> float` — `float(np.linalg.norm(report.delta_params))`.
  - `_symbol_env(report, ctx, n_reports) -> dict[str,float]` — `{"q": claimed_quality, "v": claimed_quality, "e": _effort_proxy, "B": ctx.budget, "n": float(n_reports)}`.
  - `_renormalise(raw: dict[int,float], budget: float) -> dict[int,float]` — clamp negatives to 0; if `sum > budget > 0`, scale all by `budget/sum`.
  - `build_reward_hook(mechanism, setting: str, *, budget: float) -> RewardHook`. `mechanism` is one of:
    1. plain `callable` `(reports, ctx) -> dict[int,float]` (not a `Mechanism`) → wrapped so output goes through `_renormalise`.
    2. `architect.ast.Mechanism` → `node = mechanism.payment or mechanism.utility`; `ast_to_sympy(node)` → expr → `_hook_from_expr`.
    3. `dict` (`mechanism_dict`) → first present of `payment_rule_latex`, `ir_participation_latex`, `client_utility_latex` → `_rhs_expr(latex)` → `_hook_from_expr`.
  - `_rhs_expr(latex_or_ast) -> sympy expr` — AST → `ast_to_sympy`; str → take RHS of `=`, strip `_i`/`_j`/`\`, map `{}`→`()`, `sympy.sympify` with `q,e,B,n,v` symbols.
  - `_hook_from_expr(expr, budget) -> RewardHook` — `lambdify` over `sorted(expr.free_symbols, key=str)`; per report evaluate with `_symbol_env` (missing symbols → 0 with a one-time `warnings.warn`); return `_renormalise(raw, budget)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/sim/test_mechanisms.py
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/sim/test_mechanisms.py -v`
Expected: FAIL — `No module named 'sim.mechanisms'`.

- [ ] **Step 3: Implement `src/sim/mechanisms.py`**

```python
"""Adapter: a verified mechanism -> a per-round FedAvg reward hook.

Reuses the exact AST->SymPy->lambdify path that src/architect/mc.py uses, so the
sim scores payments with the same expression semantics the verifier saw. The
adapter is READ-ONLY over the mechanism (spec: "The sim never proposes or repairs
a mechanism").
"""
from __future__ import annotations

import warnings

import numpy as np
import sympy

from sim.fedavg import ClientReport, RoundContext

try:
    from architect.serialize import ast_to_sympy
    from architect.ast import Mechanism
except Exception:  # pragma: no cover
    ast_to_sympy = None
    Mechanism = ()  # isinstance-safe


def zero_reward_hook(reports, ctx):
    return {}


def _effort_proxy(report: ClientReport) -> float:
    return float(np.linalg.norm(report.delta_params))


def _symbol_env(report: ClientReport, ctx: RoundContext, n_reports: int) -> dict:
    return {"q": report.claimed_quality, "v": report.claimed_quality,
            "e": _effort_proxy(report), "B": ctx.budget, "n": float(n_reports)}


def _renormalise(raw: dict[int, float], budget: float) -> dict[int, float]:
    clamped = {cid: max(0.0, float(p)) for cid, p in raw.items()}
    total = sum(clamped.values())
    if total > budget > 0:
        f = budget / total
        return {cid: p * f for cid, p in clamped.items()}
    return clamped


def _rhs_expr(latex_or_ast):
    if isinstance(latex_or_ast, str):
        s = latex_or_ast.split("=", 1)[-1]
        s = s.replace("_i", "").replace("_j", "").replace("\\", "")
        s = s.replace("{", "(").replace("}", ")")
        env = {k: sympy.Symbol(k) for k in ("q", "e", "B", "n", "v")}
        return sympy.sympify(s, locals=env)
    if ast_to_sympy is not None:
        return ast_to_sympy(latex_or_ast)
    raise TypeError(f"cannot build expr from {type(latex_or_ast)!r}")


def _hook_from_expr(expr, budget: float):
    syms = sorted(expr.free_symbols, key=str)
    f = sympy.lambdify([sympy.Symbol(str(s)) for s in syms], expr, "numpy")
    warned = {"done": False}

    def hook(reports, ctx):
        raw = {}
        for rep in reports:
            env = _symbol_env(rep, ctx, len(reports))
            missing = [str(s) for s in syms if str(s) not in env]
            if missing and not warned["done"]:
                warnings.warn(f"mechanism expr has unbound symbols {missing}; treating as 0")
                warned["done"] = True
            raw[rep.client_id] = float(f(*[env.get(str(s), 0.0) for s in syms]))
        return _renormalise(raw, budget)

    return hook


def build_reward_hook(mechanism, setting: str, *, budget: float):
    if callable(mechanism) and not (Mechanism and isinstance(mechanism, Mechanism)):
        def hook(reports, ctx, _inner=mechanism):
            return _renormalise(dict(_inner(reports, ctx)), budget)
        return hook

    if Mechanism and isinstance(mechanism, Mechanism):
        node = getattr(mechanism, "payment", None) or getattr(mechanism, "utility")
        return _hook_from_expr(_rhs_expr(node), budget)

    if isinstance(mechanism, dict):
        latex = (mechanism.get("payment_rule_latex")
                 or mechanism.get("ir_participation_latex")
                 or mechanism.get("client_utility_latex"))
        if latex is None:
            raise KeyError("mechanism_dict has no payment/utility latex field")
        return _hook_from_expr(_rhs_expr(latex), budget)

    raise TypeError(f"unsupported mechanism type {type(mechanism)!r}")
```

`# ponytail: the latex-string branch does crude cleanup (strip _i, braces) for hand-written fixtures. Real generated mechanisms should be passed as a Mechanism AST (run.py loads them that way), which uses ast_to_sympy directly.`

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/sim/test_mechanisms.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add src/sim/mechanisms.py tests/sim/test_mechanisms.py
git commit -m "feat(sim): mechanism->reward-hook adapter (callable / AST / dict)"
```

---

## Task 4: Settings, populations, and `run_setting`

**Files:**
- Create: `src/sim/oracle_mechanisms.py`
- Create: `src/sim/run.py`
- Create: `src/sim/fixtures/generated/cross_device_quadratic.json`
- Create: `src/sim/fixtures/generated/hierarchical_edge.json`

**Interfaces:**
- Consumes: everything from Tasks 1–3.
- Produces:
  - `SETTINGS: dict[str, dict]` — keys `"cross_device_quadratic"`, `"hierarchical_edge"`. Each value has keys `n_clients, clients_per_round, rounds, alpha, n_features, n_classes, n_samples, budget, cost ("quadratic"|"linear"), cost_coeff_range (tuple)`.
    - `cross_device_quadratic`: `n_clients=50, clients_per_round=10, rounds=30, alpha=0.3, n_features=16, n_classes=3, n_samples=6000, budget=50.0, cost="quadratic", cost_coeff_range=(0.5, 2.0)`.
    - `hierarchical_edge`: `n_clients=50` (5 edge × 10 device, modelled flat with `edge_id = client_id // 10`), `clients_per_round=10, rounds=30, alpha=0.5, n_features=16, n_classes=3, n_samples=6000, budget=50.0, cost="linear", cost_coeff_range=(0.3, 1.0)`.
  - `POPULATIONS: dict[str, list[tuple[float, type, dict]]]`:
    - `"mixed_60_20_15_5"` → `[(0.60, HonestBestResponse, {}), (0.20, DataQualityMisreporter, {"inflate":1.5,"grad_downscale":0.5,"noise_sigma":0.1}), (0.15, DropoutThreshold, {"epsilon":0.0}), (0.05, Coalition, {})]`.
    - `"all_honest"` → `[(1.0, HonestBestResponse, {})]`.
  - `build_population(setting: str, pop_name: str, seed: int) -> list[Client]` — counts by fraction via largest-remainder rounding to exactly `n_clients`; `cost_coeff` per client `~U(cost_coeff_range)`; `client.cost_fn` set to `lambda e: cc*e` (linear) or `lambda e: cc*e**2` (quadratic) per `SETTINGS[setting]["cost"]`; one shared `CoalitionController(member_ids=[ids assigned Coalition])` injected into each `Coalition`'s kwargs; `client.peer_labels` filled with `{cid: dominant label of that client's partition}` for every client. Clients returned ordered by `client_id` `0..n_clients-1`. `rng_seed` per client = `seed * 1000 + client_id`.
  - `get_mechanism(arm: str, setting: str)` — `"none"` → `zero_reward_hook`; `"oracle"` → `oracle_mechanisms.ORACLES[setting]`; `"generated"` → `load_generated(setting)` → reads `src/sim/fixtures/generated/<setting>.json` (`{"kind":"dict","mechanism_dict":{...}}`) and returns the inner `mechanism_dict`. Missing file → `FileNotFoundError("run the Architect loop for <setting> and snapshot ArchitectResult.mechanism_dict into <path>")`.
  - `load_generated(setting: str) -> dict` — also returns a second value? No: returns just the `mechanism_dict`. A module-level `GENERATED_IS_PLACEHOLDER: dict[str, bool]` is set as a side effect (`True` when the JSON has a `"note"` containing `"PLACEHOLDER"`), read by `report.write_report`.
  - `run_setting(setting: str, arm: str, population: str, seed: int) -> dict` — steps:
    1. `cfg = SETTINGS[setting]`; `X, y = make_data(cfg["n_samples"], cfg["n_features"], cfg["n_classes"], seed)`; `test_X, test_y = make_data(2000, cfg["n_features"], cfg["n_classes"], seed + 10_000)`.
    2. `partition = dirichlet_partition(y, cfg["n_clients"], cfg["alpha"], seed)`.
    3. `clients = build_population(setting, population, seed)`; set each `client.data_idx = partition[client.client_id]` (build_population made the clients; partition assigns their rows here — or build_population takes `partition` as an arg; choose one and keep it consistent). **Decision: `build_population` takes `partition` as a 4th arg** → signature `build_population(setting, pop_name, seed, partition)`.
    4. `hook = build_reward_hook(get_mechanism(arm, setting), setting, budget=cfg["budget"])`.
    5. `log = run_fedavg(X=X, y=y, partition=partition, test_X=test_X, test_y=test_y, rounds=cfg["rounds"], clients_per_round=cfg["clients_per_round"], n_classes=cfg["n_classes"], clients=clients, reward_hook=hook, budget=cfg["budget"], setting=setting, seed=seed)`.
    6. Metrics:
       - `participation_rate` = mean over rounds of `round["participation_rate"]`.
       - `final_accuracy` = `log.rounds[-1]["accuracy"]`.
       - `acc_gain[r]` = `acc[r] - acc[r-1]` (with `acc[-1] := log.rounds[0]` baseline = accuracy of the zero model on test set, computed once). `social_welfare` = `Σ_r acc_gain[r] * n_reports[r]`  (client value proxy)  `− Σ_r Σ_reports true_cost`  `− Σ_r Σ payments`  `+ Σ_r acc_gain[r] * 10` (server values accuracy 10×). Comment: "realised-accuracy-gain value proxy; not a utility from the mechanism's own value function."
       - `empirical_ic_regret` — pick up to 5 `HonestBestResponse` client ids and up to 5 rounds each where they appeared in `log.rounds[r]["reports"]`; for each (client, round) re-run just that round's payment: rebuild the reports list with that client's `ClientReport` recomputed under each `Action` on the grid `claimed_quality ∈ {0.5,1.0,1.5,2.0} × grad_scale ∈ {0.5,1.0}` (effort held at 1.0, noise 0), call `hook(alt_reports, ctx)`, compute `alt_payoff = payment − alt_true_cost`; `regret = max(0, max_alt_payoff − honest_payoff)`. Report `max` over all probes (`0.0` if none). `# ponytail: single-round coarse-grid deviation probe, not a full best-response solve.`
       - `budget_adherence` = `all(sum(r["payments"].values()) <= cfg["budget"] + 1e-6 for r in log.rounds)`.
       - `curve_participation` = `[r["participation_rate"] for r in log.rounds]`; `curve_accuracy` = `[r["accuracy"] for r in log.rounds]`.
    7. Return dict with exactly keys: `setting, arm, population, seed, participation_rate, final_accuracy, social_welfare, empirical_ic_regret, budget_adherence, curve_participation, curve_accuracy`.
  - `main(argv=None) -> int` — argparse: `--setting` (default `cross_device_quadratic`), `--arm` (`append`, default `["none","oracle","generated"]`), `--population` (default `mixed_60_20_15_5`), `--seeds` (`int` nargs=+, default `[0,1,2]`), `--out` (default `docs/sim-results.md`). Runs the grid, prints each metrics dict, calls `report.write_report(report.aggregate(all_results), path=out)`.
  - `oracle_mechanisms.ORACLES: dict[str, Callable]` (Task 4 Step 2 below).

- [ ] **Step 1: Create the generated-mechanism fixtures**

For each setting run the Architect loop once (entrypoint as used in `tests/architect/test_loop.py`) and copy its `ArchitectResult.mechanism_dict` into `src/sim/fixtures/generated/<setting>.json` as `{"kind": "dict", "mechanism_dict": {...}}`. If the loop is not runnable here, commit this **explicitly-labelled placeholder** and open a follow-up issue "replace placeholder sim mechanism fixtures":

```json
{
  "kind": "dict",
  "note": "PLACEHOLDER — replace with a real ArchitectResult.mechanism_dict snapshot before reporting. Fixtures must not be hand-tuned (spec honest-framing).",
  "mechanism_dict": {
    "payment_rule_latex": "p_i = q_i * B / n",
    "client_utility_latex": "u_i = q_i - p_i"
  }
}
```

- [ ] **Step 2: Implement `src/sim/oracle_mechanisms.py`**

```python
"""Hand-designed reward callables, one per setting, standing in for 'the closest
corpus paper' (spec comparison arm 'oracle'). Deliberately simple and open."""
from __future__ import annotations


def _cross_device_quadratic(reports, ctx):
    if not reports:
        return {}
    share = ctx.budget / len(reports)
    return {r.client_id: min(r.claimed_quality, 1.0) * share for r in reports}


def _hierarchical_edge(reports, ctx):
    if not reports:
        return {}
    by_edge: dict[int, list] = {}
    for r in reports:
        by_edge.setdefault(r.client_id // 10, []).append(r)
    edge_share = ctx.budget / len(by_edge)
    out = {}
    for members in by_edge.values():
        per = edge_share / len(members)
        for r in members:
            out[r.client_id] = per
    return out


ORACLES = {
    "cross_device_quadratic": _cross_device_quadratic,   # ref: flat quality-capped split
    "hierarchical_edge": _hierarchical_edge,             # ref: two-level per-edge uniform pricing
}
```

- [ ] **Step 3: Implement `src/sim/run.py`** — full implementation per the Interfaces block above. No placeholders; `build_population(setting, pop_name, seed, partition)`, `empirical_ic_regret` and `social_welfare` exactly as specified.

- [ ] **Step 4: Sanity-run the CLI**

Run: `python -m sim.run --setting cross_device_quadratic --arm none --seeds 0 --out /tmp/sim-smoke.md`
Expected: exits 0, writes `/tmp/sim-smoke.md`, prints the metrics dict for `(cross_device_quadratic, none, seed 0)`.

- [ ] **Step 5: Commit**

```bash
git add src/sim/run.py src/sim/oracle_mechanisms.py src/sim/fixtures/
git commit -m "feat(sim): settings, populations, run_setting + oracle mechanisms"
```

---

## Task 5: Seed aggregation and Markdown report

**Files:**
- Create: `src/sim/report.py`
- Test: `tests/sim/test_report.py`

**Interfaces:**
- Consumes: the metrics dicts from `run_setting` (Task 4); `sim.run.GENERATED_IS_PLACEHOLDER` (optional, defaults to empty).
- Produces:
  - `aggregate(results: list[dict]) -> list[dict]` — group by `(setting, arm, population)`; per group emit `{setting, arm, population, n_seeds, participation_rate_mean, participation_rate_std, final_accuracy_mean, final_accuracy_std, social_welfare_mean, social_welfare_std, empirical_ic_regret_max, budget_adherence_all, curve_participation_mean, curve_accuracy_mean}`. `*_mean/_std` via `statistics`; `empirical_ic_regret_max` = `max` over seeds; `budget_adherence_all` = `all` over seeds; `curve_*_mean` = elementwise mean (assume equal length; if not, truncate to min length).
  - `sparkline(values: list[float]) -> str` — `""` for empty; else 8-char string over the block ramp `▁▂▃▄▅▆▇█` scaled `min..max` (constant → all `▁`); length = `min(len(values), 8)` sampled evenly, or just map each value if `len<=8`. Keep it: map every value, so `len(out) == len(values)` capped at... **Decision: `len(out) == min(len(values), 40)`**, evenly subsampled. Test only asserts charset + non-empty for a known list.
  - `write_report(agg: list[dict], path: str = "docs/sim-results.md") -> None` — writes:
    1. `# FL Simulation Results` + ISO timestamp + one scope line (settings, arms, seed count, population names present).
    2. If any `sim.run.GENERATED_IS_PLACEHOLDER` value is `True`: a bold `**⚠ placeholder mechanism** — the \`generated\` arm used a placeholder fixture; numbers below are not a real loop output.` line.
    3. Per setting: a Markdown table, columns `arm | participation | final acc | social welfare | emp. IC-regret | budget ok`; cells `f"{mean:.3f} ± {std:.3f}"` (regret cell = `f"{max:.3f}"`, budget cell = `"yes"/"no"`).
    4. Per setting, per arm: a line `- {arm} participation: {sparkline(curve_participation_mean)}`.
    5. Closing paragraph, data-driven: for the `generated` arm state `empirical_ic_regret_max` and contrast with "formal IC-regret is 0"; if `generated.final_accuracy_mean < oracle.final_accuracy_mean` or `generated.social_welfare_mean < oracle.social_welfare_mean`, add a sentence naming which metric it is **below**/**underperforms** on (spec honest-framing). If no `generated` or no `oracle` group, say the comparison was not run.

- [ ] **Step 1: Write the failing test**

```python
# tests/sim/test_report.py
from __future__ import annotations
from sim.report import aggregate, sparkline, write_report


def _res(arm, seed, acc, regret):
    return {"setting": "s1", "arm": arm, "population": "p", "seed": seed,
            "participation_rate": 0.9, "final_accuracy": acc, "social_welfare": 1.0,
            "empirical_ic_regret": regret, "budget_adherence": True,
            "curve_participation": [0.5, 0.7, 0.9], "curve_accuracy": [0.3, 0.5, acc]}


def test_aggregate_groups_and_takes_regret_max():
    rows = aggregate([_res("generated", 0, 0.80, 0.1), _res("generated", 1, 0.90, 0.4)])
    assert len(rows) == 1
    r = rows[0]
    assert r["n_seeds"] == 2
    assert abs(r["final_accuracy_mean"] - 0.85) < 1e-9
    assert r["empirical_ic_regret_max"] == 0.4
    assert len(r["curve_accuracy_mean"]) == 3


def test_sparkline_charset_and_empty():
    s = sparkline([1, 2, 3, 4, 5, 6, 7, 8])
    assert s and set(s).issubset(set("▁▂▃▄▅▆▇█"))
    assert sparkline([]) == ""


def test_write_report_flags_generated_below_oracle(tmp_path):
    p = tmp_path / "r.md"
    agg = aggregate([_res("generated", 0, 0.7, 0.3), _res("oracle", 0, 0.9, 0.0)])
    write_report(agg, path=str(p))
    text = p.read_text().lower()
    assert "generated" in text and "ic-regret" in text
    assert "underperform" in text or "below" in text
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/sim/test_report.py -v`
Expected: FAIL — `No module named 'sim.report'`.

- [ ] **Step 3: Implement `src/sim/report.py`** per the Interfaces block (full, no placeholders).

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/sim/test_report.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/sim/report.py tests/sim/test_report.py
git commit -m "feat(sim): seed aggregation + docs/sim-results.md writer"
```

---

## Task 6: End-to-end smoke test and MVP run

**Files:**
- Create: `tests/sim/test_smoke.py`
- Create: `docs/sim-results.md` (generated artifact, committed)

**Interfaces:**
- Consumes: `sim.run.run_setting`, `sim.run.SETTINGS`, `sim.report`.
- Produces: no new API. The smoke test monkeypatches `sim.run.SETTINGS["cross_device_quadratic"]` to a tiny config.

- [ ] **Step 1: Write the failing test**

```python
# tests/sim/test_smoke.py
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/sim/test_smoke.py -v`
Expected: FAIL — import error or `KeyError` until `run.py` is complete.

- [ ] **Step 3: Make it pass**

Fix any real defects surfaced in `run.py` (symbol env, largest-remainder rounding, `generated` fixture load, `build_population` partition wiring). Do not weaken the assertions.

- [ ] **Step 4: Run the full sim suite**

Run: `python -m pytest tests/sim/ -v`
Expected: PASS (5 files, ~22 tests).

- [ ] **Step 5: Produce the MVP report**

Run: `python -m sim.run --setting cross_device_quadratic --seeds 0 1 2 --out docs/sim-results.md`
Expected: `docs/sim-results.md` has the 3-arm table, three participation sparklines, and the generated-vs-oracle / IC-regret paragraph. If fixtures are placeholders, the report carries the **⚠ placeholder mechanism** banner — acceptable for this milestone; the tracked follow-up replaces the fixtures.

- [ ] **Step 6: Commit**

```bash
git add tests/sim/test_smoke.py docs/sim-results.md
git commit -m "test(sim): end-to-end smoke + MVP cross_device_quadratic report"
```

---

## Self-Review

**1. Spec coverage**

| Spec section | Task |
|---|---|
| Client behavioral models (6-row table) | Task 2 (all 6 classes, one test each) |
| Mixed population (60/20/15/5) | Task 4 `POPULATIONS["mixed_60_20_15_5"]`, largest-remainder `build_population` |
| FedAvg, T rounds, C sampled, small model+data | Task 1 `run_fedavg`, synthetic blobs (torch/MNIST swapped out per Global Constraints + spec "training realism is not the point") |
| non-IID Dirichlet split + IID ablation | Task 1 `dirichlet_partition`; Task 4 `alpha` per setting + `POPULATIONS["all_honest"]`; IID test set in `run_setting` |
| Mechanism application per round | Task 1 hook call site; Task 3 adapter |
| Settings: cross_device_noniid, hierarchical_edge | Task 4 `SETTINGS` (named `cross_device_quadratic` / `hierarchical_edge` to match `src/architect/eval/benchmarks.py`) |
| Comparison arms none / generated / oracle | Task 4 `get_mechanism`, `oracle_mechanisms.py`, fixtures |
| Metrics: participation, accuracy, social welfare, empirical IC-regret, budget adherence | Task 4 `run_setting` step 6 |
| Per-round curve + final table | Task 4 `curve_*`; Task 5 `write_report` |
| Honest-framing rules | Global Constraints; Task 5 closing paragraph + placeholder banner |
| Structure table (fedavg/clients/mechanisms/run/report + tests/sim) | File Structure; Tasks 1–6 |
| MVP milestone (cross_device, 3 arms, 3 seeds, 60/20/15/5, T=30) | Task 6 Step 5 |
| Non-goals / ceiling | Global Constraints; ponytail comments in Tasks 2 & 4 |

One deliberate deviation, flagged in three places: synthetic NumPy data instead of MNIST/PyTorch (no `torch` in env; spec sanctions it). MNIST loader can drop in behind `make_data` later without touching any other task.

**2. Placeholder scan:** the only "placeholder" is the explicitly-labelled `generated` fixture JSON (Task 4 Step 1) — a *data* stand-in with a tracked follow-up and a report-level warning banner, not a plan placeholder. All code steps carry full implementations or a precise Interfaces spec.

**3. Type consistency:** `ClientReport`, `RoundContext`, `RunLog`, `RewardHook`, `Action` defined once (Tasks 1–2), same field names throughout. `build_reward_hook(mechanism, setting, *, budget)` identical in Tasks 3, 4, 6. `build_population(setting, pop_name, seed, partition)` — 4-arg form fixed in Task 4 and used in Task 4 step 3 / Task 6. `run_setting(setting, arm, population, seed)` identical in Tasks 4, 6. Metrics key set stated once (Task 4) and asserted verbatim in Task 6 (`EXPECTED_KEYS`).

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-30-fl-simulation-validation.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
