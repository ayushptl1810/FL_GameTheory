from __future__ import annotations
from sim.report import aggregate, sparkline, write_report


def _res(arm, seed, acc, regret):
    return {"setting": "s1", "arm": arm, "population": "p", "seed": seed,
            "participation_rate": 0.9, "final_accuracy": acc, "social_welfare": 1.0,
            "empirical_ic_regret": regret, "budget_adherence": True,
            "curve_participation": [0.5, 0.7, 0.9], "curve_accuracy": [0.3, 0.5, acc]}


def test_aggregate_groups_and_takes_regret_max():
    rows = aggregate([_res("generated", 0, 0.80, 0.1), _res("generated", 1, 0.90, 0.4)])
    assert len(rows) == 1
    r = rows[0]
    assert r["n_seeds"] == 2
    assert abs(r["final_accuracy_mean"] - 0.85) < 1e-9
    assert r["empirical_ic_regret_max"] == 0.4
    assert len(r["curve_accuracy_mean"]) == 3


def test_sparkline_charset_and_empty():
    s = sparkline([1, 2, 3, 4, 5, 6, 7, 8])
    assert s and set(s).issubset(set("▁▂▃▄▅▆▇█"))
    assert sparkline([]) == ""


def test_write_report_flags_generated_below_oracle(tmp_path):
    p = tmp_path / "r.md"
    agg = aggregate([_res("generated", 0, 0.7, 0.3), _res("oracle", 0, 0.9, 0.0)])
    write_report(agg, path=str(p))
    text = p.read_text().lower()
    assert "generated" in text and "ic-regret" in text
    assert "underperform" in text or "below" in text


def test_placeholder_banner_is_per_setting(tmp_path):
    p = tmp_path / "r.md"
    rows = aggregate([
        {"setting": "real1", "arm": "generated", "population": "p", "seed": 0,
         "participation_rate": 0.9, "final_accuracy": 0.8, "social_welfare": 1.0,
         "empirical_ic_regret": 0.1, "budget_adherence": True,
         "curve_participation": [0.9], "curve_accuracy": [0.8]},
        {"setting": "fake2", "arm": "generated", "population": "p", "seed": 0,
         "participation_rate": 0.9, "final_accuracy": 0.8, "social_welfare": 1.0,
         "empirical_ic_regret": 0.1, "budget_adherence": True,
         "curve_participation": [0.9], "curve_accuracy": [0.8]},
    ])
    write_report(rows, path=str(p), placeholder={"fake2": True, "real1": False})
    body = p.read_text()
    fake_section = body.split("## fake2", 1)[1]
    real_section = body.split("## real1", 1)[1].split("##", 1)[0]
    assert "placeholder mechanism" in fake_section
    assert "placeholder mechanism" not in real_section
