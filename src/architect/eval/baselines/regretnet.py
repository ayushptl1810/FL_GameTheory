"""RegretNet baseline adapter.

Method: Duetting, Feng, Golowich, Narasimhan, Parkes, Ravindranath,
"Optimal Auctions through Deep Learning", ICML 2019 -- an allocation net + a
payment net trained to maximise revenue under an augmented-Lagrangian penalty on
empirical ex-post regret.

Upstream survey (Step 1, 2026-08-29):
  gh search repos "RegretNet optimal auctions" --language=Python
    -> currymj/certified-regretnet, Cherten/pytorch_regretNet,
       Irene-Berezin/regretnet-pytorch, gzh111/Implementation-of-Automated-
       Mechanism-Design-RegretNet-with-reserve-price
  gh search code "RegretNet" --language=Python -> nothing importable
The reference implementation (saisrivatsan/deep-opt-auctions) is TensorFlow 1.x;
none of the PyTorch ports ship an importable package or a pinned release.
Decision: NONE USABLE -> reimplement here, scoped to the 2-bidder / 1-item
i.i.d. uniform[0,1] setting, ~70-line torch training loop below.

torch is imported lazily; if it is missing the adapter returns a row with
status="SKIPPED_NO_TORCH".
"""
from __future__ import annotations

import time

from architect.eval.baselines import (
    MISREPORT_GRID,
    auction_ic_regret,
    uniform_value_profiles,
)

_N_BIDDERS = 2


def _row(bench, status, ic_regret, wall):
    return {"name": bench["name"], "method": "regretnet", "mode": "n/a",
            "status": status, "iterations": 0, "solver_calls": 0,
            "wall_clock": round(wall, 2), "ic_regret": ic_regret,
            "family_match": bench.get("expected_family") == "VCG"}


def run_baseline(name, bench):
    t0 = time.time()
    try:
        import torch
        import torch.nn as nn
    except ModuleNotFoundError:
        return _row(bench, "SKIPPED_NO_TORCH", None, time.time() - t0)

    torch.manual_seed(0)
    n = _N_BIDDERS
    grid = torch.tensor(MISREPORT_GRID, dtype=torch.float32)

    def mlp(out):
        return nn.Sequential(nn.Linear(n, 64), nn.Tanh(),
                             nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, out))

    alloc_body, pay_body = mlp(n + 1), mlp(n)
    params = list(alloc_body.parameters()) + list(pay_body.parameters())
    opt = torch.optim.Adam(params, lr=1e-3)

    def alloc(b):                       # softmax over bidders + dummy, drop dummy
        return torch.softmax(alloc_body(b), dim=-1)[..., :n]

    def pay(b):                         # fraction in [0,1] of expected value -> IR
        a = alloc(b)
        return torch.sigmoid(pay_body(b)) * (a * b).sum(-1, keepdim=True)

    lam = torch.zeros(n)
    rho = 1.0
    for it in range(1, 4001):
        b = torch.rand(256, n)
        a, p = alloc(b), pay(b)
        util = a * b - p                                    # (batch, n)
        revenue = p.sum(-1).mean()
        regret = torch.zeros(n)
        for i in range(n):
            best = torch.full((b.shape[0],), -1e9)
            for m in grid:
                bb = b.clone()
                bb[:, i] = m
                dev_u = alloc(bb)[:, i] * b[:, i] - pay(bb)[:, i]
                best = torch.maximum(best, dev_u)
            regret[i] = torch.relu(best - util[:, i]).mean()
        loss = -revenue + (lam * regret).sum() + 0.5 * rho * (regret ** 2).sum()
        opt.zero_grad()
        loss.backward()
        opt.step()
        if it % 200 == 0:                                   # dual update
            with torch.no_grad():
                lam += rho * regret
                rho = min(rho * 1.05, 50.0)

    with torch.no_grad():
        def alloc_np(r):
            t = torch.tensor(r, dtype=torch.float32).unsqueeze(0)
            return alloc(t).squeeze(0).numpy()

        def pay_np(r):
            t = torch.tensor(r, dtype=torch.float32).unsqueeze(0)
            return pay(t).squeeze(0).numpy()

        profiles = uniform_value_profiles(n, samples=128, seed=1)
        ic_regret = auction_ic_regret(alloc_np, pay_np, profiles)

    return _row(bench, "TRAINED", ic_regret, time.time() - t0)
