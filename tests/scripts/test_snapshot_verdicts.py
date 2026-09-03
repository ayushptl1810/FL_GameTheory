import json
import pytest
from scripts.snapshot_verdicts import snapshot_verdicts, render_table


def _corpus(tmp_path):
    data = [
        {"paper_id": "v1", "category": "VCG",
         "mechanism": {"payment_rule_latex": "p_i = h - S", "client_utility_latex": "u = v - p",
                       "allocation_rule_latex": "x = argmax S"}},
        {"paper_id": "c1", "category": "Contract",
         "mechanism": {"ic_screening_latex": "x", "ir_participation_latex": "y"}},
        {"paper_id": "rl1", "category": "RL", "mechanism": {}},   # out of scope
    ]
    p = tmp_path / "corpus.json"
    p.write_text(json.dumps(data))
    return str(p)


def test_snapshot_excludes_out_of_scope(tmp_path):
    rows = snapshot_verdicts(_corpus(tmp_path))
    assert sorted(r["paper_id"] for r in rows) == ["c1", "v1"]
    assert all("verdict" in r and "entry_specific" in r for r in rows)


def test_snapshot_only_filters_by_category(tmp_path):
    rows = snapshot_verdicts(_corpus(tmp_path), only="VCG")
    assert [r["paper_id"] for r in rows] == ["v1"]


def test_render_table_has_counts_block(tmp_path):
    md = render_table(snapshot_verdicts(_corpus(tmp_path), only="VCG"))
    assert "| # | Paper ID | Category | Verdict | Entry-Specific |" in md
    assert "## Verdict Counts" in md
    assert "v1" in md


def test_out_is_required():
    import subprocess, sys, os
    r = subprocess.run(
        [sys.executable, "-m", "scripts.snapshot_verdicts", "corpus.json", "--only", "VCG"],
        capture_output=True, text=True, env={"PYTHONPATH": "src", **os.environ},
    )
    assert r.returncode != 0
    assert "--out" in (r.stderr + r.stdout)
