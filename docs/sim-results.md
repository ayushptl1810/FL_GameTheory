# FL Simulation Results

_Generated 2026-09-01T08:05:21+00:00_

Scope: settings [cross_device_quadratic, hierarchical_edge]; arms [generated, none, oracle]; 3 seed(s); populations [mixed_60_20_15_5].

Each arm runs the same FedAvg task (synthetic non-IID data, T=30 rounds, logistic-regression model) against a **mixed client population** — 60% honest, 20% data-quality misreporters, 15% dropout-threshold, 5% coalition — that violates the mechanism's formal assumptions. `none` pays nothing; `oracle` is a hand-designed reward rule; `generated` is the mechanism the Architect loop produced and the verifier certified for that setting.

**Reading the metrics.** `final acc` is near-flat across arms by construction: with a convex model every arm reaches the same optimum within T, so accuracy is not where a reward rule shows its effect — *participation*, *empirical IC-regret*, and *social welfare* are. `social welfare` = realised accuracy-gain value − real effort cost (payments are transfers and cancel); `budget ok` is the separate check that payments stayed within budget. Empirical IC-regret is the max realised gain any probed honest client got by deviating — it can be nonzero even when the formal certificate proves it is 0, and that gap is the point of this layer.

## cross_device_quadratic

| arm | participation | final acc | social welfare | emp. IC-regret | budget ok |
|---|---|---|---|---|---|
| generated | 0.877 ± 0.027 | 0.851 ± 0.004 | -247.346 ± 15.899 | 0.737 | yes |
| none | 0.874 ± 0.025 | 0.851 ± 0.004 | -246.721 ± 15.141 | 0.000 | yes |
| oracle | 1.000 ± 0.000 | 0.857 ± 0.006 | -296.650 ± 9.570 | 0.000 | yes |

- generated participation: ███▇███▇▇█▇▇▇▇▇▇▇▇▇▇▇▇▇▇█▆▇▇▇▇
- none participation: ███▇███▇▇█▇▇▇▇▇▇▇▇▇▇▇▇▇▇█▆▇▇▇▇
- oracle participation: ██████████████████████████████

Empirical IC-regret for `generated` is **0.737**, while its formal IC-regret is 0. The certificate holds in the stylized game; the sim shows a real deployment gap — a client in this population gains ≈0.74 by deviating from honest reporting (here by over-stating data quality, which the mechanism's verifiable-output assumption rules out). `generated` and `oracle` are statistically indistinguishable on final accuracy (0.851 vs 0.857). It attains **higher** social welfare than `oracle` (-247.3 vs -296.7): `oracle` buys full participation, but the marginal effort cost of the retained contributors outweighs their marginal accuracy value in this setting. `generated` does **not** lift participation over `none` (0.877 vs 0.874) — its reward at the certified IR-binding point is too small to retain the dropout-prone clients (IR is satisfied as ≥ 0, not > 0).

## hierarchical_edge

| arm | participation | final acc | social welfare | emp. IC-regret | budget ok |
|---|---|---|---|---|---|
| generated | 0.878 ± 0.027 | 0.851 ± 0.006 | -135.778 ± 7.191 | 0.000 | yes |
| none | 0.874 ± 0.025 | 0.851 ± 0.006 | -135.352 ± 6.830 | 0.000 | yes |
| oracle | 1.000 ± 0.000 | 0.856 ± 0.007 | -160.984 ± 3.969 | 0.000 | yes |

- generated participation: ███▇███▇▇█▇▇▇▇▇▇▇▇▇▇▇▇▇▇█▆▇▇▇▇
- none participation: ███▇███▇▇█▇▇▇▇▇▇▇▇▇▇▇▇▇▇█▆▇▇▇▇
- oracle participation: ██████████████████████████████

Empirical IC-regret for `generated` is 0.000 — effectively zero: the certificate's incentive guarantee held against the assumption-violating population, not only in the stylized game. `generated` and `oracle` are statistically indistinguishable on final accuracy (0.851 vs 0.856). It attains **higher** social welfare than `oracle` (-135.8 vs -161.0): `oracle` buys full participation, but the marginal effort cost of the retained contributors outweighs their marginal accuracy value in this setting. `generated` does **not** lift participation over `none` (0.878 vs 0.874) — its reward at the certified IR-binding point is too small to retain the dropout-prone clients (IR is satisfied as ≥ 0, not > 0).
