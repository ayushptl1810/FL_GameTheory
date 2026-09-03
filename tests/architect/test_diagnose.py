# tests/architect/test_diagnose.py
import pytest
from architect.formalize import write_manual_diagnosis, append_backlog_paragraph


def _entry():
    return {"paper_id": "m1", "category": "Stackelberg",
            "mechanism": {"leader_utility_latex": "R - p", "follower_best_response_latex": "e*"}}


def test_write_manual_diagnosis_mutates_entry():
    e = _entry()
    d = write_manual_diagnosis(
        e, round_="R3b", track=1,
        limit="no proved equilibrium; Track 1 Stackelberg needs one",
        mechanism="two-level Stackelberg game, vector follower decision",
        obstruction="equilibrium_existence=False in the corpus entry",
        human_task="prove or cite existence of the Stackelberg equilibrium",
        today="2026-09-12")
    assert e["verdict_override"] == "MANUAL"
    assert e["manual_diagnosis"]["track"] == 1
    assert e["manual_diagnosis"]["date"] == "2026-09-12"
    assert d is e["manual_diagnosis"]


@pytest.mark.parametrize("bad", [
    {"limit": "  "}, {"obstruction": ""}, {"human_task": "\t"}])
def test_write_manual_diagnosis_rejects_empty_reason(bad):
    kw = dict(round_="R3b", track=1, limit="L", mechanism="M",
              obstruction="O", human_task="H")
    kw.update(bad)
    with pytest.raises(ValueError):
        write_manual_diagnosis(_entry(), **kw)


def test_append_backlog_accepts_bare_filename(tmp_path, monkeypatch):
    # os.path.dirname("backlog.md") == "" -> makedirs("") raised FileNotFoundError
    monkeypatch.chdir(tmp_path)
    e = _entry()
    write_manual_diagnosis(e, round_="R3b", track=1, limit="L",
                           mechanism="M", obstruction="O", human_task="H",
                           today="2026-09-12")
    append_backlog_paragraph(e, backlog_path="backlog.md")
    assert (tmp_path / "backlog.md").read_text().startswith("# MANUAL Backlog")


def test_append_backlog_creates_and_is_idempotent(tmp_path):
    bp = str(tmp_path / "MANUAL-backlog.md")
    e = _entry()
    write_manual_diagnosis(e, round_="R3b", track=1, limit="L",
                           mechanism="M", obstruction="O", human_task="H",
                           today="2026-09-12")
    append_backlog_paragraph(e, backlog_path=bp)
    append_backlog_paragraph(e, backlog_path=bp)
    txt = open(bp).read()
    assert txt.count("## m1 (Stackelberg) — R3b") == 1
    assert "**Human task:** H" in txt
    assert txt.startswith("# MANUAL Backlog")
