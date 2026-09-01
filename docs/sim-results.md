# FL Simulation Results

_Generated 2026-09-01T07:53:16+00:00_

Scope: settings [cross_device_quadratic, hierarchical_edge]; arms [generated, none, oracle]; 3 seed(s); populations [mixed_60_20_15_5].

## cross_device_quadratic

| arm | participation | final acc | social welfare | emp. IC-regret | budget ok |
|---|---|---|---|---|---|
| generated | 0.877 ± 0.027 | 0.851 ± 0.004 | -281.209 ± 18.006 | 0.737 | yes |
| none | 0.874 ± 0.025 | 0.851 ± 0.004 | -246.721 ± 15.141 | 0.000 | yes |
| oracle | 1.000 ± 0.000 | 0.857 ± 0.006 | -1796.650 ± 9.570 | 0.000 | yes |

- generated participation: █▆█▅▆▇▆▅▄▆▃▃▄▄▅▄▅▄▄▅▅▅▄▃█▁▅▃▅▅
- none participation: █▆█▅▆▆▆▅▄▆▃▃▄▄▅▄▅▄▄▅▅▅▄▃█▁▅▃▅▅
- oracle participation: ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁

The `generated` mechanism's empirical IC-regret is 0.737 over the run, while its formal IC-regret is 0 — the certificate holds in the stylized game; the sim shows the gap to a population that violates its assumptions. It also **underperforms** `oracle` — it is **below** `oracle` on final accuracy (honest-framing: reported, not hidden).

## hierarchical_edge

**⚠ placeholder mechanism** — this setting's `generated` arm used a placeholder fixture, not a real loop output; its row is not evidence.

| arm | participation | final acc | social welfare | emp. IC-regret | budget ok |
|---|---|---|---|---|---|
| generated | 1.000 ± 0.000 | 0.856 ± 0.007 | -1660.984 ± 3.969 | 3.934 | yes |
| none | 0.874 ± 0.025 | 0.851 ± 0.006 | -135.352 ± 6.830 | 0.000 | yes |
| oracle | 1.000 ± 0.000 | 0.856 ± 0.007 | -1660.984 ± 3.969 | 0.000 | yes |

- generated participation: ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
- none participation: █▆█▅▆▆▆▅▄▆▃▃▄▄▅▄▅▄▄▅▅▅▄▃█▁▅▃▅▅
- oracle participation: ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁

The `generated` mechanism's empirical IC-regret is 3.934 over the run, while its formal IC-regret is 0 — the certificate holds in the stylized game; the sim shows the gap to a population that violates its assumptions.
