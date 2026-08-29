from architect.eval.baselines.control import run_baseline
from architect.eval.benchmarks import BENCHMARKS


def test_control_baseline_row_shape():
    row = run_baseline("control", BENCHMARKS[0])
    assert {"name", "method", "status", "ic_regret", "family_match"} <= set(row)
    assert row["method"] == "control"
