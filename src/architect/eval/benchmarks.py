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
]
