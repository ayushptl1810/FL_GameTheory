from architect.types import ProblemSpec
from architect.router import route


class _Idx:  # stand-in for rag.Index
    entries = [{"title": "close paper", "z3_validated": True}]


def test_close_match_routes_retrieval(monkeypatch):
    import architect.router as R
    monkeypatch.setattr(R, "nearest_distance", lambda s, i: 0.05)
    m = route(ProblemSpec(raw_text="x"), _Idx(), complete=lambda s, u, **k: "yes")
    assert m == "Retrieval"


def test_far_match_two_failure_modes_routes_hybrid(monkeypatch):
    import architect.router as R
    monkeypatch.setattr(R, "nearest_distance", lambda s, i: 0.9)
    spec = ProblemSpec(raw_text="x", failure_modes=["non_iid", "collusion"])
    m = route(spec, _Idx(), complete=lambda s, u, **k: "no")
    assert m == "Hybrid"


def test_far_match_default_synthesis(monkeypatch):
    import architect.router as R
    monkeypatch.setattr(R, "nearest_distance", lambda s, i: 0.9)
    m = route(ProblemSpec(raw_text="x"), _Idx(), complete=lambda s, u, **k: "no")
    assert m == "Synthesis"
