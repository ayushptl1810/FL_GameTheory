# FL Simulation Results

_Generated 2026-08-31T19:58:57+00:00_

Scope: settings [cross_device_quadratic]; arms [generated, none, oracle]; 3 seed(s); populations [mixed_60_20_15_5].

**⚠ placeholder mechanism** — the `generated` arm used a placeholder fixture; numbers below are not a real loop output.

## cross_device_quadratic

| arm | participation | final acc | social welfare | emp. IC-regret | budget ok |
|---|---|---|---|---|---|
| generated | 1.000 ± 0.000 | 1.000 ± 0.000 | -1793.640 ± 9.610 | 3.934 | yes |
| none | 0.874 ± 0.025 | 1.000 ± 0.000 | -243.631 ± 14.814 | 0.000 | yes |
| oracle | 1.000 ± 0.000 | 1.000 ± 0.000 | -1793.640 ± 9.610 | 0.000 | yes |

- generated participation: ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
- none participation: █▆█▅▆▆▆▅▄▆▃▃▄▄▅▄▅▄▄▅▅▅▄▃█▁▅▃▅▅
- oracle participation: ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁

The `generated` mechanism's empirical IC-regret is 3.934 over the run, while its formal IC-regret is 0 — the certificate holds in the stylized game; the sim shows the gap to a population that violates its assumptions.
