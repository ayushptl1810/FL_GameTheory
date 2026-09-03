# Round R3b — new VERIFIED / R6 candidates

Stackelberg slice. The R3b formalizer sweep produced **0 flips** (diagnose-only round, the same
formalizer wall hit in R2/VCG and R3a/Contract). Task 15 adjudicated the 29 non-VERIFIED entries.

## New VERIFIED this round

None; 0 flips; `Sarikaya2019stackelberg_workers` held (the single entry-specific Stackelberg
VERIFIED, untouched by this round).

## R6 candidates

The deciding test applied to every entry was mechanical: does the entry's `mechanism` dict carry a
**non-null, single-variable, closed-form** `best_response_latex` or `follower_foc_latex` that a
`d(leader_utility)/d(follower_decision)` FOC check could consume?

For the 14 entries below the answer is YES — the corpus already holds a clean scalar closed form,
and the only thing standing between them and an entry-specific verdict is tooling. They stay
`VERIFIED_TEMPLATE` (no baseline rewrite, no `formalized_ast`/`formalization_meta` written — the
sweep produced none) and are logged here as R6 input.

**The shared tooling gap for all 14:** the AST formalizer produced no valid AST though the corpus
has a clean closed-form single-variable follower best-response and/or FOC. What is needed is a
Stackelberg-specific formalize path analogous to the VCG allocation-classifier: parse
`follower_foc_latex` / `best_response_latex` into the typed AST, substitute the best response into
the stationarity condition, and discharge `d(follower_utility)/d(follower_decision) = 0` at the
claimed equilibrium plus the second-order condition. Each entry below is discharged by that one
piece of work; none needs new mathematics.

| Paper ID | Follower decision (scalar) | Deciding field |
|---|---|---|
| 1811_12082 | `s_i^d` training data size | both: FOC `-q_i + c_i b_i exp(-c_i s_i^d) = 0`, BR `s_i^{d*} = (1/c_i) ln(c_i b_i / q_i)` — exact root of the FOC |
| 2110_12876 | `f_i^j` computing resources | both: FOC linear in `f_i^j`, BR `f_i^{j*} = p_i^j d_i r^j / (2 kappa_i w^j)` |
| 2203_00270 | energy consumption `e_i^k` | both, from Appendix A/B, verified by direct PDF image read; scalar per branch |
| 2404_08261 | `rho_i^t` privacy budget | both: rational FOC in `rho_i^t`, explicit BR |
| 2508_07676 | `rho_i(t)` privacy budget | BR `rho_i^*(t) = (r(t)-b_i)/(2 a_i) - alpha N phi_i(t)`, linear closed form (FOC null, but BR alone suffices) |
| Cao2025service | `zeta_m` data contribution | both: FOC `tau (Z - zeta_m)/Z^2 - P_m = 0`, explicit BR |
| Chen2023multifactor_iot | `Acc_i^t` accuracy contribution | both: rational FOC, explicit BR |
| FLamma2025stackelberg | `tau_i` local epochs | both: FOC linear in `tau_i`, BR `tau_i^* = gamma(1 - ||w_i^t - w^t||)/(2 c_i)` — exact root |
| Hu2020trading | `rho_i` privacy budget | both: rational FOC, BR is a two-branch cases form whose non-degenerate branch is an explicit square root |
| Hu2022truthful_FEL | `s` reported data size | BR `s^* = rho(r_0 + A_d Theta)/(A_e Theta)`, closed form (FOC deliberately null — the paper never prints it; BR alone suffices) |
| Javaherian2025stackelberg_ic | `tau_i` local epochs | both: FOC linear in `tau_i`, BR is its exact root; `ir_follower_latex` also present |
| Lee2024sfl_stackelberg | `d_n` data contribution | both: rational FOC, BR is an explicit square-root closed form |
| Li2025iiot_drl | `theta_i` update cycle | both: FOC `sigma_i/theta_i^2 - r_i/theta_i = 0`, BR `theta_i^* = sigma_i / r_i` — exact root |
| Xiao2020stackelberg_twostage | `theta_i^{(t)}` local accuracy goal | both: FOC from Eq. 13 (`dU/dtheta = 0`), explicit BR; `ir_follower_latex` also present |

Note on the two BR-only entries (`2508_07676`, `Hu2022truthful_FEL`): both have a `null`
`follower_foc_latex` that is null by *deliberate fail-closed corpus policy* (the paper never
prints the first-order condition as a numbered equation), not because no stationarity condition
exists. Their `best_response_latex` is transcribed verbatim from the paper's own closed-form
maximizer, which is exactly what a `d(leader_utility)/d(follower_decision)` check consumes, so
they are R6 candidates rather than MANUAL.

## MANUAL this round

15 entries — see `MANUAL-backlog.md` for the per-entry paragraph. Summary of ceilings:

- **Vector / multi-variable follower decision (8):** `2101_05628`, `2101_12428`, `2502_10765`,
  `Guo2023stackelberg_industrial`, `Li2025split`, `Liu2026fedbud`, `Wang2022blockchain`,
  `Yu2022multi_leader_fl`
- **Transcendental / implicit FOC with no closed-form root (3):** `Chu2023hierarchical`,
  `Luo2023unbiased`, `Pandey2019crowd`
- **Backward recursion over a horizon (1):** `2412_05636`
- **Three-stage / multi-layer game (1):** `2103_05866`
- **Unspecified generic payment/cost functions (1):** `Pang2025quality`
- **No proved equilibrium (1):** `Khan2019edge` (`equilibrium_existence=False`)

## Rejected flips

None — the sweep produced 0 flips, so there was nothing to reject.
