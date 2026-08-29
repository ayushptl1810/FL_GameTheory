# Architect Evaluation Results

| name | mode | status | iters | solver | wall_s | ic_regret | expected_family | family_match |
|---|---|---|---|---|---|---|---|---|
| cross_device_quadratic | Hybrid | VERIFIED | 1 | 1 | 27.12 | 0.0 | Contract | True |
| hierarchical_edge | Hybrid | VERIFIED | 1 | 1 | 18.26 | 0.0 | Stackelberg | True |
| iiot_log_linear | Synthesis | VERIFIED | 5 | 5 | 123.81 | 0.0 | Stackelberg | True |
| myerson_single_item | Synthesis | FAILED | 13 | 1 | 264.42 | nan | VCG | True |
| vcg_redistribution | Hybrid | FAILED | 12 | 3 | 298.59 | nan | VCG | True |
| contract_2type_screening | Synthesis | VERIFIED | 2 | 2 | 67.95 | 0.0 | Contract | True |
| contract_3type_screening | Synthesis | VERIFIED | 1 | 1 | 45.06 | 0.0 | Contract | True |
| stackelberg_linear_pricing | Synthesis | VERIFIED | 1 | 1 | 16.3 | 0.0 | Stackelberg | True |
| vcg_clarke_pivot | Synthesis | FAILED | 14 | 2 | 277.95 | nan | VCG | True |
| vcg_cavallo_redistribution | Hybrid | FAILED | 12 | 0 | 399.68 | nan | VCG | True |
| contract_budget_balanced | Synthesis | VERIFIED | 2 | 2 | 50.92 | 0.0 | Contract | True |
| contract_linear_quadratic_effort | Synthesis | VERIFIED | 1 | 1 | 20.24 | 0.0 | Contract | True |

## Seed variance

| name | verified_rate | iters_mean | iters_spread | wall_clock_mean | ic_regret_mean |
|---|---|---|---|---|---|
| cross_device_quadratic | 1.00 | 1.00 | 0 | 27.12 | 0.0 |
| hierarchical_edge | 1.00 | 1.00 | 0 | 18.26 | 0.0 |
| iiot_log_linear | 1.00 | 5.00 | 0 | 123.81 | 0.0 |
| myerson_single_item | 0.00 | 13.00 | 0 | 264.42 | nan |
| vcg_redistribution | 0.00 | 12.00 | 0 | 298.59 | nan |
| contract_2type_screening | 1.00 | 2.00 | 0 | 67.95 | 0.0 |
| contract_3type_screening | 1.00 | 1.00 | 0 | 45.06 | 0.0 |
| stackelberg_linear_pricing | 1.00 | 1.00 | 0 | 16.30 | 0.0 |
| vcg_clarke_pivot | 0.00 | 14.00 | 0 | 277.95 | nan |
| vcg_cavallo_redistribution | 0.00 | 12.00 | 0 | 399.68 | nan |
| contract_budget_balanced | 1.00 | 2.00 | 0 | 50.92 | 0.0 |
| contract_linear_quadratic_effort | 1.00 | 1.00 | 0 | 20.24 | 0.0 |
