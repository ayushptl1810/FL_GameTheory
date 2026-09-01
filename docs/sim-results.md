# FL Simulation Results

_Generated 2026-09-01T07:16:05+00:00_

Scope: settings [cross_device_quadratic]; arms [generated, none, oracle]; 3 seed(s); populations [mixed_60_20_15_5].

**⚠ placeholder mechanism** — the `generated` arm used a placeholder fixture; numbers below are not a real loop output.

## cross_device_quadratic

| arm | participation | final acc | social welfare | emp. IC-regret | budget ok |
|---|---|---|---|---|---|
| generated | 1.000 ± 0.000 | 0.857 ± 0.006 | -1796.650 ± 9.570 | 3.934 | yes |
| none | 0.874 ± 0.025 | 0.851 ± 0.004 | -246.721 ± 15.141 | 0.000 | yes |
| oracle | 1.000 ± 0.000 | 0.857 ± 0.006 | -1796.650 ± 9.570 | 0.000 | yes |

- generated participation: ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
- none participation: █▆█▅▆▆▆▅▄▆▃▃▄▄▅▄▅▄▄▅▅▅▄▃█▁▅▃▅▅
- oracle participation: ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁

The `generated` mechanism's empirical IC-regret is 3.934 over the run, while its formal IC-regret is 0 — the certificate holds in the stylized game; the sim shows the gap to a population that violates its assumptions.
