from tracks.vcg_dsic import parse_allocation, parse_payment, HighestBidder, ClarkePivot


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
