from tracks.vcg_dsic import (
    parse_allocation,
    parse_payment,
    verify_vcg_dsic,
    HighestBidder,
    ClarkePivot,
)

_SINGLE_ITEM_CLARKE = {  # 2nd-price single-item auction, done right
    "paper_id": "synthetic_clarke_ok", "category": "VCG",
    "mechanism": {
        "allocation_rule_latex": r"x_i(b) = 1 \text{ if } b_i = \max_j b_j",
        "payment_rule_latex": r"p_i = \max_{j \neq i} b_j \text{ if } x_i = 1, \text{ else } 0",
        "client_utility_latex": r"u_i = v_i x_i - p_i",
        "auction_type": "forward", "num_clients": 2}}

_NON_PIVOTAL = {  # winner pays half its own bid -> not DSIC
    **_SINGLE_ITEM_CLARKE, "paper_id": "synthetic_bad_payment",
    "mechanism": {**_SINGLE_ITEM_CLARKE["mechanism"],
                  "payment_rule_latex": r"p_i = b_i / 2 \text{ if } x_i = 1"}}


_SECOND_PRICE_RESERVE = {  # 2nd-price single item + reserve r, done right
    "paper_id": "synthetic_clarke_reserve", "category": "VCG",
    "mechanism": {
        "allocation_rule_latex": r"x_i = 1 \text{ if } b_i = \max_j b_j",
        "payment_rule_latex": r"p_i = \max(\max_{j \neq i} b_j, r) "
                              r"\text{ if } x_i = 1, \text{ else } 0",
        "client_utility_latex": r"u_i = v_i x_i - p_i", "num_clients": 2}}

_FIRST_PRICE = {  # winner pays its OWN bid -> first-price, not DSIC
    "paper_id": "synthetic_first_price", "category": "VCG",
    "mechanism": {
        "allocation_rule_latex": r"x_i = 1 \text{ if } b_i = \max_j b_j",
        "payment_rule_latex": r"p_i = b_i \text{ if } x_i = 1, \text{ else } 0",
        "client_utility_latex": r"u_i = v_i x_i - p_i", "num_clients": 2}}

_MULTI_ATTR = {  # value is a 2-vector; deterministic multi-parameter allocation
    "paper_id": "synthetic_multi_attr", "category": "VCG",
    "mechanism": {
        "value_latex": r"v_i \in \mathbb{R}^2",
        "allocation_rule_latex": r"x^*(b) \in \arg\max_x \sum_i \langle b_i, x_i \rangle",
        "payment_rule_latex": r"p_i = \max_{j \neq i} b_j",
        "client_utility_latex": r"u_i = v_i x_i - p_i", "num_clients": 2}}


def test_second_price_reserve_done_right_verified():
    # reserve is regex-collapsed to the plain Clarke pivot in the grid model;
    # the mechanism is DSIC + IR either way -> entry-specific VERIFIED.
    r = verify_vcg_dsic(_SECOND_PRICE_RESERVE, k=4)
    assert r.verdict == "VERIFIED" and r.entry_specific is True


def test_first_price_pay_own_bid_is_counterexample():
    # first-price: a winner with v_i > b_i = 2nd price can LOWER its bid, keep
    # winning, and pay less -> profitable deviation, genuine witness.
    r = verify_vcg_dsic(_FIRST_PRICE, k=4)
    assert r.verdict == "COUNTEREXAMPLE"
    assert r.counterexample is not None and r.counterexample["violation"] == "DSIC"


def test_multi_attribute_deterministic_is_unknown():
    # n_attrs=2 argmax-welfare allocation: the grid encoder has no sound
    # multi-parameter model (a deterministic truthful multi-attribute VCG
    # generally cannot exist), so it fails closed to UNKNOWN -- never VERIFIED.
    assert verify_vcg_dsic(_MULTI_ATTR, k=3).verdict == "UNKNOWN"


def test_multi_attribute_highest_bidder_fails_closed():  # I1: n_attrs!=1 guard
    # Even with a fully-encodable highest-bidder + Clarke-pivot rule, a value
    # in R^2 means the encoder would silently assume additivity across
    # attributes. verify_vcg_dsic must fail closed to UNKNOWN.
    e = {**_SINGLE_ITEM_CLARKE, "paper_id": "synthetic_multi_attr_hb",
         "mechanism": {**_SINGLE_ITEM_CLARKE["mechanism"],
                       "value_latex": r"v_i \in \mathbb{R}^2", "num_clients": 3}}
    r = verify_vcg_dsic(e, k=3)
    assert r.verdict == "UNKNOWN"
    assert "multi-attribute" in r.notes


def test_sum_externality_payment_is_unknown():  # C1: not the 2nd-price form
    # A sum-of-others payment is Groves but NOT the single-competing-bid form
    # encode_utility can price; for n>=3 pricing it as max-of-others would give
    # a FALSE VERIFIED. parse_payment must return None -> caller UNKNOWN.
    assert parse_payment(r"p_i = \sum_{j \neq i} b_j", None) is None
    e = {"paper_id": "synthetic_sum_externality", "category": "VCG",
         "mechanism": {
             "allocation_rule_latex": r"x_i = 1 \text{ if } b_i = \max_j b_j",
             "payment_rule_latex": r"p_i = \sum_{j \neq i} b_j",
             "client_utility_latex": r"u_i = v_i x_i - p_i",
             "num_clients": 3}}
    assert verify_vcg_dsic(e, k=3).verdict == "UNKNOWN"


def test_single_item_clarke_verified():
    r = verify_vcg_dsic(_SINGLE_ITEM_CLARKE, k=4)
    assert r.verdict == "VERIFIED" and r.entry_specific is True


def test_non_pivotal_payment_is_counterexample():
    r = verify_vcg_dsic(_NON_PIVOTAL, k=4)
    assert r.verdict == "COUNTEREXAMPLE"
    assert r.counterexample is not None


def test_oversize_grid_is_unknown():
    big = {**_SINGLE_ITEM_CLARKE, "mechanism": {**_SINGLE_ITEM_CLARKE["mechanism"],
           "num_clients": 6}}
    assert verify_vcg_dsic(big, k=6).verdict == "UNKNOWN"


def test_unit_weight_welfare_max_clarke_verified():  # Task 2: plain VCG via argmax
    # \arg\max_x \sum_i v_i x_i  (all weights 1) + Clarke pivot == second-price
    # single-item auction -> DSIC + IR exact on the grid.
    e = {**_SINGLE_ITEM_CLARKE, "paper_id": "synthetic_argmax_unit",
         "mechanism": {**_SINGLE_ITEM_CLARKE["mechanism"],
                       "allocation_rule_latex": r"x^* \in \arg\max_x \sum_i v_i x_i",
                       "payment_rule_latex":
                           r"p_i = \max_{j \neq i} b_j \text{ if } x_i = 1, \text{ else } 0"}}
    r = verify_vcg_dsic(e, k=4)
    assert r.verdict == "VERIFIED" and r.entry_specific is True


def test_affine_maximizer_numeric_weights_verified():  # Task 2: Roberts affine max
    # w_1 = 2, w_2 = 1 affine maximizer + affine-maximizer Clarke pivot.
    # Winner = argmax_i w_i b_i, price = (max_{k!=i} w_k b_k) / w_i.  DSIC by
    # construction (Roberts 1979); Z3 grid unsat confirms.
    e = {**_SINGLE_ITEM_CLARKE, "paper_id": "synthetic_affine_max",
         "mechanism": {**_SINGLE_ITEM_CLARKE["mechanism"],
                       "allocation_rule_latex":
                           r"x^* \in \arg\max_x [ 2 v_1 x_1 + 1 v_2 x_2 ]",
                       "payment_rule_latex":
                           r"p_i = \max_{j \neq i} b_j \text{ if } x_i = 1, \text{ else } 0"}}
    r = verify_vcg_dsic(e, k=3)
    assert r.verdict == "VERIFIED" and r.entry_specific is True


def test_argmax_welfare_raw_string_objective_is_unknown():  # C1: fail closed
    e = {**_SINGLE_ITEM_CLARKE, "paper_id": "synthetic_argmax_raw",
         "mechanism": {**_SINGLE_ITEM_CLARKE["mechanism"],
                       "allocation_rule_latex":
                           r"W^\star(\hat c) \in \arg\max [SW := v(W) - \hat c f(W)]"}}
    assert verify_vcg_dsic(e, k=3).verdict == "UNKNOWN"


def _argmax_entry(alloc_latex, num_clients=2):
    return {**_SINGLE_ITEM_CLARKE, "paper_id": "synthetic_aw",
            "mechanism": {**_SINGLE_ITEM_CLARKE["mechanism"],
                          "allocation_rule_latex": alloc_latex,
                          "payment_rule_latex":
                              r"p_i = \max_{j \neq i} b_j \text{ if } x_i = 1, "
                              r"\text{ else } 0",
                          "num_clients": num_clients}}


def test_symbolic_letter_weight_welfare_is_unknown():  # fix round 1: fail closed
    # \sum_i w_i v_i x_i -- literal w_i, the STANDARD affine-maximizer notation.
    # The extractor must NOT read this as unit-weight.
    e = _argmax_entry(r"x^* \in \arg\max_x \sum_i w_i v_i x_i")
    assert verify_vcg_dsic(e, k=3).verdict == "UNKNOWN"


def test_subtraction_objective_is_unknown():  # not a welfare fn
    e = _argmax_entry(r"x^* \in \arg\max_x [2 v_1 x_1 - 3 v_2 x_2]")
    assert verify_vcg_dsic(e, k=3).verdict == "UNKNOWN"


def test_ratio_objective_is_unknown():  # not linear
    e = _argmax_entry(r"x^* \in \arg\max_x [v_1/q_1 + v_2/q_2]")
    assert verify_vcg_dsic(e, k=3).verdict == "UNKNOWN"


def test_quadratic_objective_is_unknown():  # not linear
    e = _argmax_entry(r"x^* \in \arg\max_x [2 v_1^2 x_1 + v_2 x_2]")
    assert verify_vcg_dsic(e, k=3).verdict == "UNKNOWN"


def test_topk_highest_not_verified():  # C3: multi-winner must not be HighestBidder
    e = {**_SINGLE_ITEM_CLARKE, "paper_id": "synthetic_top2",
         "mechanism": {**_SINGLE_ITEM_CLARKE["mechanism"],
                       "allocation_rule_latex":
                           r"the top-2 clients with the highest bids win"}}
    a = parse_allocation(e["mechanism"]["allocation_rule_latex"])
    assert a.__class__.__name__ == "TopK"
    assert verify_vcg_dsic(e, k=3).verdict == "UNKNOWN"


def test_single_bidder_is_unknown():  # I3: n<2 is vacuous
    e = {**_SINGLE_ITEM_CLARKE, "paper_id": "synthetic_n1",
         "mechanism": {**_SINGLE_ITEM_CLARKE["mechanism"], "num_clients": 1}}
    assert verify_vcg_dsic(e, k=4).verdict == "UNKNOWN"


def test_parse_highest_bidder():
    a = parse_allocation(r"x_i(b) = 1 \text{ if } b_i = \max_j b_j")
    assert isinstance(a, HighestBidder)


def test_parse_argmax_welfare():
    a = parse_allocation(r"W^\star(\hat c) \in \arg\max [SW := v(W) - \hat c f(W)]")
    assert a is not None and a.__class__.__name__ == "ArgmaxWelfare"


def test_parse_clarke_payment():
    a = parse_allocation(r"x_i(b) = 1 \text{ if } b_i = \max_j b_j")
    p = parse_payment(r"p_i = \max_{j \neq i} b_j", a)
    assert p.__class__.__name__ in ("ClarkePivot", "ExplicitFormula")


def test_unparseable_allocation_returns_none():
    assert parse_allocation(r"x = \text{the output of Algorithm 3}") is None


def test_proportional_share_allocation_is_unknown():
    # Fractional / divisible allocation (every bidder gets a share) -- not a
    # single-winner VCG mechanism, so there is no dominant-strategy property to
    # prove. Must be UNKNOWN (never VERIFIED), and never a COUNTEREXAMPLE.
    # Mirrors corpus entry 2404_13841, which states no DSIC claim for a Groves
    # payment over the fractional allocation.
    e = {
        "paper_id": "synthetic_prop_share", "category": "VCG",
        "mechanism": {
            "allocation_rule_latex":
                r"p = \frac{f_s^{\alpha-1}}{\sum_{s' \in S} f_{s'}^{\alpha-1}}",
            "payment_rule_latex": r"p_{i,s} = \frac{B}{S(k-1)}",
            "client_utility_latex": r"u_i = v_i p_i - c_i", "num_clients": 2}}
    r = verify_vcg_dsic(e, k=3)
    assert r.verdict == "UNKNOWN"
    assert "fractional-share" in r.notes
