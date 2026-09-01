# FL Simulation — methodology & analysis notes

Companion to the auto-generated [`sim-results.md`](sim-results.md). This file is
hand-written: it records what was run, the two verified mechanisms under test,
the findings, and the caveats that keep the numbers honest.

## What was run

- **Settings:** `cross_device_quadratic` (Contract family) and `hierarchical_edge`
  (Stackelberg family), matching the `src/architect/eval/benchmarks.py` names.
- **Arms:** `none` (no rewards) · `oracle` (hand-designed reward callable,
  `src/sim/oracle_mechanisms.py`) · `generated` (real Architect-loop output,
  verifier-certified — see below).
- **Population:** `mixed_60_20_15_5` — 60% `HonestBestResponse`, 20%
  `DataQualityMisreporter` (claims 1.5× quality, delivers 0.5× effort and a
  0.5×-scaled + noised gradient), 15% `DropoutThreshold` (leaves once mean recent
  payoff < 0), 5% `Coalition` (coordinated over-report).
- **FedAvg:** 50 clients, 10 sampled/round, T=30, Dirichlet α∈{0.3, 0.5},
  16-feature 3-class synthetic Gaussian blobs, multinomial logistic regression.
- **Seeds:** 0, 1, 2. Every sampling function takes an explicit seed.

Reproduce:

```bash
PYTHONPATH=src python -m sim.run --setting all --seeds 0 1 2 --out docs/sim-results.md
```

## The two verified mechanisms

Both were produced by the real Architect loop with `ARCHITECT_AST_VERIFY=1`
(AST-native verification, no LaTeX parser in the loop) and the Groq
`openai/gpt-oss-120b` model, then snapshotted verbatim into
`src/sim/fixtures/generated/`. Neither was hand-edited (spec honest-framing).

### `cross_device_quadratic` — Contract, VERIFIED in 3 iterations

    client utility   U_i = R_i - e_i^2 * theta_i
    IC (screening)   U_i(own) >= U_i(other) for both type pairs   [entry-specific]
    IR               U_i(own) >= 0                                [entry-specific]

Prompt: the `benchmarks.py` text — *"1000 cross-device FL clients, each has a
private cost type; effort cost is quadratic c·e²; server has a fixed reward
budget; wants truthful effort."*

Sim deployment reading: the mechanism gives a utility form, not a payment rule.
`mechanisms._payment_from_utility` solves `U_i = 0` for the reward symbol →
`R_i = e_i^2 * theta_i` (the IR-binding point the certificate already pins).
`e_i` is the submitted-update norm; `theta_i` is bound from the client's *claim*
(`1 / claimed_quality`) — the cost type the server infers from the report.

### `hierarchical_edge` — Stackelberg, VERIFIED in 1 iteration

    follower utility   U(e) = p*e - c*k*e^2
    FOC                dU/de = 0  =>  e*(p) = p / (2*c*k)
    IR                 U(e*) >= 0                                 [entry-specific]

Prompt (prescriptive — the generic benchmark text stalled at `VERIFIED_TEMPLATE`
across 12 iterations, twice, because the entry-specific Stackelberg check needs a
closed-form interior optimum): *"…the edge server (follower) chooses contribution
rate e ≥ 0 to maximise U(e) = p·e − k·c·e². …strictly concave with a unique
interior optimum e*(p) = p/(2kc). Give the follower utility as one closed-form
polynomial and set meta = {equilibrium_existence: true, equilibrium_uniqueness:
true, follower_decision: "e", num_types: 1}."*

Sim deployment reading: `mechanisms._payment_from_follower_utility` takes the
term linear in `e` (the leader's transfer `p·e`), sets the price symbol to 1, and
lets the budget renormalisation fix the scale → **pay in proportion to
contributed effort, capped at budget**. That is the structure the certificate
proves; nothing is added.

## Findings

| axis | cross_device_quadratic (Contract) | hierarchical_edge (Stackelberg) |
|---|---|---|
| **empirical IC-regret** (`generated`) | **0.74** vs formal 0 | **0.00** vs formal 0 |
| participation (`generated` vs `none`) | 0.88 vs 0.87 — no lift | 0.88 vs 0.87 — no lift |
| social welfare (`generated` vs `oracle`) | −247 vs −297 — higher | −136 vs −161 — higher |
| final accuracy (all arms) | ≈ 0.85 — flat | ≈ 0.85 — flat |

1. **The certificate's IC guarantee does not always survive deployment, and the
   mechanism *structure* decides whether it does.** The Contract mechanism prices
   on `theta_i`, which the sim infers from the client's quality *claim* — so a
   `DataQualityMisreporter` that over-states quality shifts its inferred type and
   extracts ≈0.74 of realised gain, against a certified IC-regret of 0. The
   verifiable-output assumption the proof rests on is exactly what the misreporter
   violates. The Stackelberg mechanism prices only on *contributed effort*
   (`p·e`), never on a self-reported signal, so the same misreporter gains
   nothing on the IC axis — empirical IC-regret stays 0.

2. **A verified, IR-satisfying mechanism deployed at its IR-binding point does
   not retain dropout-prone clients.** Both certified mechanisms satisfy IR as
   `U_i ≥ 0`, not `> 0`. Realised payoffs hover around zero with noise, the
   `DropoutThreshold` clients leave, and `generated` participation (~0.88) is
   indistinguishable from `none` (~0.87). `oracle`, which pays a flat positive
   share every round, holds participation at 1.0.

3. **Inducing full participation can cost more social welfare than it creates.**
   `oracle` retains everyone, but in this synthetic setting the marginal effort
   cost of the extra contributors exceeds their marginal accuracy value, so
   `oracle` welfare (−297 / −161) is *below* both `generated` and `none`. This is
   a property of the toy value proxy, not a claim about real FL — see caveats.

## Caveats (why particular numbers are not over-read)

- **Flat final accuracy is by construction.** Logistic regression is convex; with
  T=30 rounds every arm reaches the same optimum, so `final acc` cannot separate
  the arms. Difficulty is tuned (`centroid_scale=0.7`, `lr=0.05`,
  `local_epochs=2`) only so the *curve* is a visible ramp (0.32 → 0.85), not to
  manufacture an accuracy gap. A non-convex model (small MLP) would let data
  quantity/quality move the ceiling; that is future scope.
- **The IC-regret probe is a coarse single-round grid.** It re-scores one round's
  payment under `claimed_quality ∈ {0.5, 1, 1.5, 2} × grad_scale ∈ {0.5, 1}`,
  effort held at the honest 1.0, for ≤5 honest clients × ≤5 rounds. It is a lower
  bound on true best-response regret, not a solve. **Effort is deliberately held
  fixed:** folding effort-shirking into the grid makes even the `none` arm show
  "regret" (a costly-effort client always prefers to shirk when nothing rewards
  it), which is moral hazard, not report incentive-compatibility.
- **`theta` from the claim** (`1 / claimed_quality`) is the sim's model of what
  the server infers, not something the mechanism specifies. A different inference
  map would change the Contract IC-regret magnitude (not its sign).
- **The `oracle` callables are deliberately simple** (flat budget split /
  per-edge uniform pricing), standing in for "the closest corpus paper" rather
  than reproducing one.
- **`social_welfare` is a realised-accuracy-gain proxy**, not a utility from any
  mechanism's own value function. Payments are transfers and are not subtracted
  (an earlier draft subtracted them and wrongly ranked `none` as welfare-optimal).
- **Two settings, small models, ≤50 clients, T≤30.** Scope is "does the incentive
  translate", not "how good is our FL".
