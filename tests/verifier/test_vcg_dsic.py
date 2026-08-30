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


def test_argmax_welfare_clarke_is_unknown_not_crash():  # C1: closure raises at call time
    e = {**_SINGLE_ITEM_CLARKE, "paper_id": "synthetic_argmax",
         "mechanism": {**_SINGLE_ITEM_CLARKE["mechanism"],
                       "allocation_rule_latex": r"x^* \in \arg\max_x \sum_i v_i x_i"}}
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
