import types as _t
from architect.eval.benchmarks import BENCHMARKS
from architect.eval import evaluate


def test_benchmarks_cover_spec_set():
    names = {b["name"] for b in BENCHMARKS}
    assert {"cross_device_quadratic", "hierarchical_edge", "iiot_log_linear",
            "myerson_single_item", "vcg_redistribution"} <= names


def test_evaluate_returns_one_row_per_benchmark(monkeypatch):
    import architect.eval as E
    monkeypatch.setattr(E, "run", lambda spec, **kw: _t.SimpleNamespace(
        mode="Synthesis", status="FAILED", iterations=1, solver_calls=1,
        wall_clock=0.1, transcript=[]))
    rows = evaluate(names=["cross_device_quadratic"], index=object())
    assert len(rows) == 1 and rows[0]["name"] == "cross_device_quadratic"
