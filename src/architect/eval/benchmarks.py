"""FL + classic benchmark set for the Architect evaluation harness (spec S8)."""

BENCHMARKS = [
    {"name": "cross_device_quadratic",
     "text": "1000 cross-device FL clients, each has a private cost type; effort cost is quadratic c*e^2; server has a fixed reward budget; wants truthful effort.",
     "expected_family": "Contract", "reference": "none"},
    {"name": "hierarchical_edge",
     "text": "Hierarchical FL: 20 edge servers each aggregate 50 devices; edge servers price participation to devices; server prices participation to edge servers; leader-follower.",
     "expected_family": "Stackelberg", "reference": "none"},
    {"name": "iiot_log_linear",
     "text": "Industrial IoT FL, client utility is R_i * ln(1/theta_i) minus a linear cost; server sets reward R_i; wants participation from all types.",
     "expected_family": "Stackelberg", "reference": "none"},
    {"name": "myerson_single_item",
     "text": "Single item allocated to one of n bidders with i.i.d. uniform private values; design a truthful revenue-maximizing auction.",
     "expected_family": "VCG", "reference": "known-optimum"},
    {"name": "vcg_redistribution",
     "text": "Multi-bidder single-item allocation with VCG payments, redistribute as much surplus as possible while keeping dominant-strategy truthfulness.",
     "expected_family": "VCG", "reference": "known-optimum"},

    # --- Task G additions ---
    {"name": "contract_2type_screening",
     "text": "FL data provider with two equally likely private quality types theta in {theta_L=1, theta_H=2}. Provider utility is w - theta*e where e is contributed effort and w the payment. Server value is 3*e. Design an IC + IR menu {(e_L, w_L), (e_H, w_H)}.",
     "expected_family": "Contract", "reference": "hand-derived"},
    # ref: efficient effort e_H = 3/(2*theta_H) = 0.75, e_L distorted down by the
    # standard screening rule; w_H = theta_H*e_H + theta_L*e_L (info rent to high
    # type), w_L = theta_L*e_L. Low type IR binds, high type IC binds.

    {"name": "contract_3type_screening",
     "text": "FL client with three equally likely private cost types theta in {1, 2, 3}. Client utility w - theta*e^2. Server value 4*e. Design an IC + IR three-item screening menu {(e_k, w_k)}_{k=1..3}.",
     "expected_family": "Contract", "reference": "hand-derived"},
    # ref: downward-adjacent IC binds, lowest-cost type IR binds; e_1 efficient
    # (e_1 = 2/theta_1), e_2 and e_3 distorted down by the hazard-rate term:
    # 4 = 2*theta_k*e_k + 2*(theta_k - theta_{k-1})*e_k*(mass of types above k);
    # w_k = theta_k*e_k^2 + sum of downstream information rents.

    {"name": "stackelberg_linear_pricing",
     "text": "FL server (leader) sets a per-unit price p >= 0 for model updates. A single representative client (follower) chooses contribution q >= 0 to maximize p*q - 0.5*q^2. Server profit is (v - p)*q with v = 1. Find the subgame-perfect price.",
     "expected_family": "Stackelberg", "reference": "hand-derived"},
    # ref: follower FOC p - q = 0  =>  q*(p) = p. Leader maximizes (v - p)*p,
    # dPi/dp = v - 2p = 0  =>  p* = v/2 = 0.5, q* = 0.5, server profit 0.25.

    {"name": "vcg_clarke_pivot",
     "text": "Allocate a single indivisible FL compute slot among n bidders with private values; use the Clarke pivot (VCG with the pivotal externality as payment) so the mechanism is efficient, dominant-strategy truthful, and individually rational.",
     "expected_family": "VCG", "reference": "known-optimum"},

    {"name": "vcg_cavallo_redistribution",
     "text": "Single-item VCG allocation among n >= 2 symmetric bidders; apply the Cavallo redistribution rule, returning to each bidder 1/n of the second-highest reported value among the others, keeping dominant-strategy truthfulness and feasibility.",
     "expected_family": "VCG", "reference": "known-optimum"},

    {"name": "contract_budget_balanced",
     "text": "FL aggregator with two private effort-cost types theta in {1, 2}, prior (0.5, 0.5), client utility w - theta*e, server value 2*e. Design an IC + IR menu whose expected payment equals a fixed budget B = 1 (ex-ante budget balance).",
     "expected_family": "Contract", "reference": "hand-derived"},
    # ref: same screening structure as contract_2type_screening (high-type IC
    # binds, low-type IR binds) with payments scaled so that
    # 0.5*w_L + 0.5*w_H = B = 1; feasible iff B >= expected client effort cost.

    {"name": "contract_linear_quadratic_effort",
     "text": "FL client with private marginal-cost type theta drawn uniformly on [1, 2]. Client utility is w(theta) - 0.5*theta*e(theta)^2; server value is 5*e(theta). Design a continuous IC + IR screening contract e(.), w(.).",
     "expected_family": "Contract", "reference": "hand-derived"},
    # ref: virtual surplus 5*e - 0.5*theta*e^2 - (theta-1)*e (hazard rate 1/(theta-1)
    # for U[1,2]); FOC => e(theta) = (5 - (theta-1)) / theta = (6-theta)/theta,
    # monotone decreasing; w(theta) = 0.5*theta*e(theta)^2 + integral_theta^2 0.5*e(s)^2 ds
    # (info rent), top type theta=2 gets zero rent, IR binds there.
]
