"""Mechanisms that are provably NOT IC/IR. verify() must never return VERIFIED*.

Every entry in BROKEN reaches an entry-specific verifier path (Stackelberg
FOC+IR, discrete-prior Bayesian IC, Contract screening, VCG payment gate) and
would be wrongly certified if that path were unsound. Each carries a
hand-computed `# why unsound:` note naming the profitable deviation / violated
constraint.

TEMPLATE_FALLBACK_HOLES are known-unsound mechanisms the verifier still lets
through as VERIFIED_TEMPLATE (or, for one VCG case, VERIFIED) because the
category's generic template path never inspects the entry's own math. Closing
that is a verifier redesign (it would flip ~60 corpus entries and several
architect e2e tests), so these are pinned as xfail, not folded into BROKEN.
See task-D-report.md.
"""

# -- mechanisms the verifier now handles soundly (UNKNOWN / COUNTEREXAMPLE) ----

BROKEN = [
    # Stackelberg: follower IR is violated at the follower's own optimum.
    # verify() derives e* by FOC and checks U_follower(e*) >= 0 symbolically /
    # by interval branch-and-bound; each of these has U*(e*) < 0.
    {"name": "stk_fixed_cost_K", "category": "Stackelberg",
     "mechanism": {"equilibrium_existence": True,
        "follower_utility_latex": r"U_i = p e_i - c e_i^2 - K",
        "leader_objective_latex": r"\max_p (1-p) e_i",
        "follower_decision": r"\( e_i \)"}},
    # why unsound: e* = p/(2c), U* = p^2/(4c) - K < 0 when K > p^2/(4c)
    #              (p=0.5,c=1,K=10 -> 0.0625 - 10); follower prefers U=0 (opt out).
    {"name": "stk_participation_fee", "category": "Stackelberg",
     "mechanism": {"equilibrium_existence": True,
        "follower_utility_latex": r"U_i = p e_i - \frac{1}{2} e_i^2 - F",
        "leader_objective_latex": r"\max_p (1-p) e_i",
        "follower_decision": r"\( e_i \)"}},
    # why unsound: e* = p, U* = p^2/2 - F < 0 for F > p^2/2; opting out dominates.
    {"name": "stk_scaled_fixed_cost", "category": "Stackelberg",
     "mechanism": {"equilibrium_existence": True,
        "follower_utility_latex": r"U_i = a p e_i - b e_i^2 - g",
        "leader_objective_latex": r"\max_p (1-p) e_i",
        "follower_decision": r"\( e_i \)"}},
    # why unsound: e* = a p/(2b), U* = a^2 p^2/(4b) - g < 0 for large g; opt out.
    {"name": "stk_convex_cost_minimum", "category": "Stackelberg",
     "mechanism": {"equilibrium_existence": True,
        "follower_utility_latex": r"U_i = c e_i^2 - p e_i",
        "leader_objective_latex": r"\max_p (1-p) e_i",
        "follower_decision": r"\( e_i \)"}},
    # why unsound: utility convex in e_i; critical point e* = p/(2c) is a MINIMUM
    #              with U* = -p^2/(4c) < 0, so IR fails at the stationary point.
    {"name": "stk_reward_minus_price", "category": "Stackelberg",
     "mechanism": {"equilibrium_existence": True,
        "follower_utility_latex": r"U_i = r e_i - k e_i^2 - r",
        "leader_objective_latex": r"\max_r (1-r) e_i",
        "follower_decision": r"\( e_i \)"}},
    # why unsound: e* = r/(2k), U* = r^2/(4k) - r < 0 for r < 4k; sunk fee r
    #              exceeds gross surplus, follower opts out.
    {"name": "stk_sunk_investment", "category": "Stackelberg",
     "mechanism": {"equilibrium_existence": True,
        "follower_utility_latex": r"U_i = p x_i - \frac{1}{2} x_i^2 - I",
        "leader_objective_latex": r"\max_p (1-p) x_i",
        "follower_decision": r"\( x_i \)"}},
    # why unsound: x* = p, U* = p^2/2 - I < 0 for I > p^2/2; non-participation
    #              is strictly better.
    {"name": "stk_fee_equals_price", "category": "Stackelberg",
     "mechanism": {"equilibrium_existence": True,
        "follower_utility_latex": r"U_i = \beta p e_i - e_i^2 - \beta",
        "leader_objective_latex": r"\max_p (1-p) e_i",
        "follower_decision": r"\( e_i \)"}},
    # why unsound: e* = beta p/2, U* = beta^2 p^2/4 - beta < 0 when beta p^2 < 4;
    #              follower deviates to non-participation.
    {"name": "stk_numeric_fixed_cost", "category": "Stackelberg",
     "mechanism": {"equilibrium_existence": True,
        "follower_utility_latex": r"U_i = 2 p e_i - 3 e_i^2 - 7",
        "leader_objective_latex": r"\max_p (1-p) e_i",
        "follower_decision": r"\( e_i \)"}},
    # why unsound: e* = p/3, U* = p^2/3 - 7 < 0 for p < sqrt(21) ~ 4.58; over the
    #              leader's price range p in (0,1), IR always fails.
    {"name": "stk_two_fixed_costs", "category": "Stackelberg",
     "mechanism": {"equilibrium_existence": True,
        "follower_utility_latex": r"U_i = p e_i - c e_i^2 - K - L",
        "leader_objective_latex": r"\max_p (1-p) e_i",
        "follower_decision": r"\( e_i \)"}},
    # why unsound: e* = p/(2c), U* = p^2/(4c) - (K+L) < 0 for K+L > p^2/(4c).
    {"name": "stk_price_proportional_fee", "category": "Stackelberg",
     "mechanism": {"equilibrium_existence": True,
        "follower_utility_latex": r"U_i = p e_i - c e_i^2 - m p",
        "leader_objective_latex": r"\max_p (1-p) e_i",
        "follower_decision": r"\( e_i \)"}},
    # why unsound: e* = p/(2c), U* = p(p/(4c) - m) < 0 for m > p/(4c); abstain.
    {"name": "stk_no_price_term", "category": "Stackelberg",
     "mechanism": {"equilibrium_existence": True,
        "follower_utility_latex": r"U_i = \alpha e_i - \beta e_i^2 - \delta",
        "leader_objective_latex": r"\max_p (1-p) e_i",
        "follower_decision": r"\( e_i \)"}},
    # why unsound: e* = alpha/(2 beta), U* = alpha^2/(4 beta) - delta < 0 for
    #              delta > alpha^2/(4 beta); IR fails at the optimum.

    # Bayesian IC (discrete prior): the interim IC gap is unsigned or negative
    # under the declared prior, so verify() must return UNKNOWN, not VERIFIED.
    {"name": "bayes_no_assumptions", "category": "Contract",
     "mechanism": {"ic_type": "bayesian",
        "ic_screening_latex": r"P_h \cdot R - C \geq P_m \cdot R - C",
        "ir_participation_latex": r"P_h \cdot R - C \geq 0",
        "bayesian_assumptions_latex": []}},
    # why unsound: IC gap (P_h - P_m) R has no sign without prior dominance; if
    #              P_h < P_m the low type mimics the high type for (P_m-P_h)R>0.
    {"name": "bayes_ic_reversed", "category": "Contract",
     "mechanism": {"ic_type": "bayesian",
        "ic_screening_latex": r"P_m \cdot R - C \geq P_h \cdot R - C",
        "ir_participation_latex": r"P_m \cdot R - C \geq 0",
        "bayesian_assumptions_latex": [r"P_h \geq P_m", r"R > \frac{C}{P_h}"]}},
    # why unsound: stated IC needs P_m >= P_h but the assumption is P_h >= P_m;
    #              gap (P_m - P_h) R <= 0, a type deviates for a strict gain.
    {"name": "bayes_missing_prior_dominance", "category": "Contract",
     "mechanism": {"ic_type": "bayesian",
        "ic_screening_latex": r"P_h \cdot R - C \geq P_m \cdot R - C",
        "ir_participation_latex": r"P_h \cdot R - C \geq 0",
        "bayesian_assumptions_latex": [r"R > \frac{C}{P_h}"]}},
    # why unsound: only an IR-supporting assumption is declared; (P_h - P_m) R
    #              stays unsigned so IC is not certifiable.
    {"name": "bayes_ir_large_fixed_cost", "category": "Contract",
     "mechanism": {"ic_type": "bayesian",
        "ic_screening_latex": r"P_h \cdot R - C \geq P_m \cdot R - C",
        "ir_participation_latex": r"P_h \cdot R - C - 100 \geq 0",
        "bayesian_assumptions_latex": [r"P_h \geq P_m"]}},
    # why unsound: IR needs P_h R - C >= 100 but nothing bounds R or C; with
    #              P_h R - C < 100 the high type's participation payoff is < 0.
    {"name": "bayes_reversed_no_assumptions", "category": "Contract",
     "mechanism": {"ic_type": "bayesian",
        "ic_screening_latex": r"P_m \cdot R - C \geq P_h \cdot R - C",
        "ir_participation_latex": r"P_m \cdot R - C \geq 0",
        "bayesian_assumptions_latex": []}},
    # why unsound: no prior assumption; gap (P_m - P_h) R unsigned, negative
    #              when P_h > P_m -> profitable misreport.
    {"name": "bayes_three_type_reversed", "category": "Contract",
     "mechanism": {"ic_type": "bayesian",
        "ic_screening_latex": r"P_l \cdot R - C \geq P_h \cdot R - C",
        "ir_participation_latex": r"P_l \cdot R - C \geq 0",
        "bayesian_assumptions_latex": [r"P_h \geq P_m", r"P_m \geq P_l"]}},
    # why unsound: assumptions give P_h >= P_l so (P_l - P_h) R <= 0; the P_l
    #              type strictly gains by claiming the P_h contract.
    {"name": "bayes_irrelevant_assumption", "category": "Contract",
     "mechanism": {"ic_type": "bayesian",
        "ic_screening_latex": r"P_h \cdot R - C \geq P_m \cdot R - C",
        "ir_participation_latex": r"P_h \cdot R - C \geq 0",
        "bayesian_assumptions_latex": [r"C > 0"]}},
    # why unsound: the only assumption (C > 0) constrains neither P_h vs P_m nor
    #              R; IC gap remains unsigned.
    {"name": "bayes_ir_flipped", "category": "Contract",
     "mechanism": {"ic_type": "bayesian",
        "ic_screening_latex": r"P_h \cdot R - C \geq P_m \cdot R - C",
        "ir_participation_latex": r"0 \geq P_h \cdot R - C",
        "bayesian_assumptions_latex": []}},
    # why unsound: the IR inequality is written backwards -- it asserts the
    #              participation payoff is <= 0, i.e. not individually rational.
    {"name": "bayes_ic_and_ir_reversed", "category": "Contract",
     "mechanism": {"ic_type": "bayesian",
        "ic_screening_latex": r"P_m \cdot R - C \geq P_h \cdot R - C",
        "ir_participation_latex": r"P_m \cdot R - C \geq 0",
        "bayesian_assumptions_latex": [r"P_h \geq P_m"]}},
    # why unsound: IC direction contradicts the P_h >= P_m assumption
    #              ((P_m - P_h) R <= 0); the high type deviates to the P_m menu.

    # Contract screening: the stated "IC" is not an incentive constraint, so
    # the entry-specific path fails closed to UNKNOWN.
    {"name": "contract_ambiguous_type_two_symbols", "category": "Contract",
     "mechanism": {
        "client_utility_latex": r"U_i = \theta_i e_i R_i - f_i - \frac{1}{2} c e_i^2",
        "ic_screening_latex": r"\theta_i e_i R_i - f_i - \frac{1}{2} c e_i^2 \geq "
                              r"\theta_i e_j R_j - f_i - \frac{1}{2} c e_j^2",
        "ir_participation_latex": r"\theta_i e_i R_i - f_i - \frac{1}{2} c e_i^2 \geq 0",
        "type_variable": r"\theta_i and e_i", "num_types": 2}},
    # why unsound: menu bilinearly couples private type theta_i with chosen
    #              effort e_i; type family / ordering direction is
    #              unidentifiable, the naive binding menu is manipulable by an
    #              off-diagonal (theta_i, e_j) choice.

    # VCG: identically-zero payment.
    {"name": "vcg_zero_payment", "category": "VCG",
     "mechanism": {
        "allocation_rule_latex": r"x_i = 1 \text{ if } b_i = \max_j b_j",
        "payment_rule_latex": r"p_i = 0",
        "client_utility_latex": r"u_i = v_i x_i - p_i"}},
    # why unsound: winner-take-all, zero payment -- a bidder with value v_i = 1
    #              reports b_i = 100, wins an item worth 1, pays 0, utility +1
    #              > 0 truthful; not dominant-strategy IC.

    # VCG: payment depends on the winner's own bid (Myerson violation).
    {"name": "vcg_payment_depends_on_own_bid", "category": "VCG",
     "mechanism": {
        "allocation_rule_latex": r"x_i = 1 \text{ if } b_i = \max_j b_j",
        "payment_rule_latex": r"p_i = b_i / 2"}},
    # why unsound: a DSIC payment cannot depend on the winner's own report
    #              except through the allocation. Phase 2: parse_payment reads
    #              this as ExplicitFormula(b_i/2), so the finite-grid DSIC check
    #              runs and returns a real COUNTEREXAMPLE -- a winner shades its
    #              bid down toward the second price, still wins, and pays
    #              strictly less than it would when truthful (price = b_i/2
    #              decreases with the report).

    # VCG: Clarke-shaped payment but non-welfare-maximising allocation.
    {"name": "vcg_clarke_shaped_payment_wrong_allocation", "category": "VCG",
     "mechanism": {
        "allocation_rule_latex": r"x_i = 1 \text{ if } b_i = \min_j b_j",
        "payment_rule_latex": r"p_i = \max_{j \neq i} b_j"}},
    # why unsound: the payment IS the second-price / Clarke-pivot form
    #              (parse_payment -> ClarkePivot), but the allocation gives the
    #              item to the LOWEST bidder, so Groves does not apply. Phase 2:
    #              verify_vcg_dsic parses "b_i = min_j b_j"
    #              (HighestBidder(lowest=True)) and the finite-grid check returns
    #              a real COUNTEREXAMPLE -- a winning low bidder pays the higher
    #              competing bid, so truthful participation nets < 0 (IR breaks).
    #              (A sum-externality payment here is now UNKNOWN, not a
    #              counterexample; the single-competing-bid form keeps the case
    #              decisive.)
]


# -- known-unsound mechanisms the verifier still passes (documented xfail) -----

TEMPLATE_FALLBACK_HOLES = [
    {"name": "contract_ic_compares_equilibrium_utilities", "category": "Contract",
     "expected_bad": "VERIFIED_TEMPLATE",
     "mechanism": {
        "client_utility_latex": r"u_i = R_i - \theta_i e_i",
        "ic_screening_latex": r"R_i - \theta_i e_i \geq R_j - \theta_j e_j",
        "ir_participation_latex": r"R_i - \theta_i e_i \geq 0",
        "type_variable": r"\theta_i", "num_types": 3}},
    # why unsound: RHS is U_j(contract_j), not U_i(contract_j); U_i(i) >= U_j(j)
    #              for all i,j does NOT rule out U_i(j) > U_i(i). Entry-specific
    #              path now fails closed, but verify() then returns the generic
    #              linear-cost template as VERIFIED_TEMPLATE.
    {"name": "contract_ic_inequality_flipped", "category": "Contract",
     "expected_bad": "VERIFIED_TEMPLATE",
     "mechanism": {
        "client_utility_latex": r"u_i = R_i - \theta_i e_i",
        "ic_screening_latex": r"R_j - \theta_i e_j \geq R_i - \theta_i e_i",
        "ir_participation_latex": r"R_i - \theta_i e_i \geq 0",
        "type_variable": r"\theta_i", "num_types": 3}},
    # why unsound: IC written with the inequality reversed -- asserts every type
    #              prefers some OTHER contract. Parser cannot isolate a contract
    #              index, bails, generic template is returned.
    {"name": "contract_additive_type", "category": "Contract",
     "expected_bad": "VERIFIED_TEMPLATE",
     "mechanism": {
        "client_utility_latex": r"U_i = \theta_i + R_i",
        "ic_screening_latex": r"\theta_i + R_i \geq \theta_i + R_j",
        "ir_participation_latex": r"\theta_i + R_i \geq 0",
        "type_variable": r"\theta_i", "num_types": 2}},
    # why unsound: additive (no single-crossing) -- IC reduces to R_i >= R_j for
    #              all j, forcing a constant menu that ignores type. Both
    #              entry-specific tracks now bail (vacuity / feasibility gate);
    #              the generic template still reports VERIFIED_TEMPLATE.
]
