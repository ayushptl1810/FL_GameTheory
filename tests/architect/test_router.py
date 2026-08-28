from architect.types import ProblemSpec
from architect.router import route


_NEAREST = {"title": "nearest paper", "z3_validated": True}


class _Idx:  # stand-in for rag.Index
    entries = [
        {"title": "first corpus paper", "z3_validated": True},
        _NEAREST,
    ]


def test_close_match_routes_retrieval(monkeypatch):
    import architect.router as R
    monkeypatch.setattr(R, "nearest_distance", lambda s, i: 0.05)
    monkeypatch.setattr(R, "retrieve", lambda spec, k, index: [_NEAREST])
    seen = {}

    def _complete(s, u, **k):
        seen["user"] = u
        return "yes"

    m = route(ProblemSpec(raw_text="x"), _Idx(), complete=_complete)
    assert m == "Retrieval"
    assert "nearest paper" in seen["user"]
    assert "first corpus paper" not in seen["user"]


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
