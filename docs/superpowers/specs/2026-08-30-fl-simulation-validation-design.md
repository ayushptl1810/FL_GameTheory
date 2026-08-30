# FL Simulation — Empirical Validation Layer (design)

**Date:** 2026-08-30
**Status:** Design. Deferred — starts after Phase 2 (real VCG check) lands.
**Parent:** `2026-08-29-verifier-proper-checks.md` (a sibling workstream, not a phase)
**Pairs with:** the deferred baselines item (RegretNet / Liu et al. need a
performance axis to compare on — this provides it).

---

## Why this exists

The formal verifier proves `u_i(truthful) ≥ u_i(lie)` and `u_i ≥ 0` **inside a
stylized game** that assumes independent private values, verifiable output, no
communication congestion, and no collusion. `Task.md` already lists those four as
"FL-specific properties that break standard mechanism proofs." Today the project
has **zero empirical evidence** that a verified mechanism does anything useful for
an actual FL system. This layer closes that: verified → rational clients
participate → the model trains — and it **measures where the formal model's
assumptions bite**.

Secondary: it produces performance numbers (participation rate, final accuracy,
social welfare) so the loop's output can sit in a results table next to
RegretNet and Liu et al. (2502.12203), which today it cannot.

## What it is NOT

- **Not a design layer.** Mechanisms are still produced by the Architect loop and
  gated by the formal verifier. The sim never proposes or repairs a mechanism.
- **Not a replacement for the verifier or the Monte Carlo pre-filter.** The
  certificate is the guarantee. The sim is downstream evidence.
- **Not a general FL benchmark.** 1–2 fixed settings, small models, small client
  counts. Scope is "does the incentive translate", not "how good is our FL".

## The load-bearing decision: client behavioral models

A sim where every client plays its **formal best response** adds nothing over the
Monte Carlo pre-filter — it re-derives the proof numerically. The value is
**only** in modelling clients that violate the mechanism's assumptions. The sim
ships with these strategy models, each a `Client.decide(mechanism, history) ->
Action`:

| Model | Behaviour | Assumption it stresses |
|---|---|---|
| `HonestBestResponse` | plays the mechanism's intended equilibrium action | baseline / sanity |
| `DataQualityMisreporter` | reports a higher data-quality / effort signal than it delivers; submits down-scaled or noised gradients | verifiable output |
| `DropoutThreshold` | participates iff realised `u_i ≥ ε`; leaves otherwise | individual rationality under real (not modelled) costs |
| `Coalition(k)` | 2–3 clients coordinate reports to maximise summed utility | individual-deviation-only IC |
| `BoundedRational(ε)` | ε-greedy around best response | equilibrium selection / convergence |
| `InterdependentValue` | its marginal value depends on the realised data of others (non-IID) | independent private values |

A run mixes these per a configurable population (e.g. 60% honest, 20%
misreporter, 15% dropout-threshold, 5% coalition).

## Setup

- **Training:** FedAvg, `T` rounds, `C` clients sampled per round. Small model +
  dataset (MNIST or a 2-class CIFAR slice) — training realism is not the point,
  client incentives are.
- **Data partition:** non-IID Dirichlet split (α controls skew) for the primary
  setting; IID for an ablation.
- **Mechanism application:** each round, the server computes rewards via the
  mechanism-under-test from the clients' reports; clients update their strategy
  state from the realised payoff.
- **Settings (start with 2):**
  1. `cross_device_noniid` — 50 clients, Dirichlet α=0.3, quadratic effort cost,
     fixed reward budget. Matches the `cross_device_quadratic` eval benchmark.
  2. `hierarchical_edge` — 5 edge servers × 10 devices, two-level pricing.
     Matches the `hierarchical_edge` benchmark.

## Comparison arms (per setting)

| Arm | Mechanism |
|---|---|
| `none` | FedAvg, no rewards |
| `generated` | the mechanism the Architect loop produced + verified for this setting |
| `oracle` | a hand-designed mechanism from the closest corpus paper |

## Metrics (logged per round, reported as final + curve)

- **participation rate** — fraction of sampled clients that actually contribute
- **final model accuracy** on a held-out test set
- **social welfare** — `Σ (v_i(outcome) − cost_i − payment_i) + server_utility`
- **empirical IC-regret** — max realised gain any client got by deviating from
  honest, measured over the run (this is the number that can be nonzero even
  when the formal IC-regret is 0, and that is the point)
- **budget adherence** — did total payments stay within the stated budget

## Honest-framing rules (non-negotiable)

- A mechanism that is formally `VERIFIED` but underperforms `oracle` or shows
  nonzero empirical IC-regret in the sim is a **reported finding**, not a hidden
  one. The writeup states: the certificate holds in the formal model; the sim
  shows the gap to deployment.
- The sim's client models are **stated explicitly** with their parameters. No
  silent tuning to make `generated` look good.
- `generated` is whatever the loop actually produced for that setting (including
  a reframed family) — not cherry-picked.

## Structure (when built)

| File | Responsibility |
|---|---|
| `src/sim/fedavg.py` | minimal FedAvg loop, pluggable reward hook |
| `src/sim/clients.py` | the 6 strategy models above, one class each |
| `src/sim/mechanisms.py` | adapter: mechanism-dict / AST → per-round reward function |
| `src/sim/run.py` | `run_setting(setting, arm, population, seed) -> metrics dict` |
| `src/sim/report.py` | aggregate seeds, emit `docs/sim-results.md` (curves + final table) |
| `tests/sim/` | each client model's `decide` is unit-tested against a hand-checked scenario; one end-to-end smoke run (2 clients, 3 rounds, asserts metrics dict shape) |

## Minimum viable milestone

`cross_device_noniid`, all 3 arms, 3 seeds, a 60/20/15/5 population, MNIST,
T=30 rounds. Deliverable: `docs/sim-results.md` with the final metric table and
one participation-rate curve per arm, plus a paragraph on where `generated`'s
empirical IC-regret diverges from its formal 0.

## Non-goals / ceiling

- Not modelling network/system dynamics (stragglers, bandwidth) beyond a flat
  per-round cost.
- Not claiming the sim *proves* anything — it is evidence about assumption
  violation, framed as such.
- n−1 collusion, adaptive adversaries, and Byzantine-robustness are out of scope
  (they are their own literature).
