import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from diagnose_manual_root_cause import trace_entry, TraceResult


def _stackelberg_entry_multiclause():
    # Mirrors 1811_12082's real shape: a 3-clause utility substitution
    # chain that _resolve_stackelberg_utility cannot currently resolve.
    return {
        "paper_id": "test_multiclause",
        "category": "Stackelberg",
        "verdict_override": "MANUAL",
        "manual_diagnosis": {
            "round": "R7",
            "mechanism": "test mechanism",
            "obstruction": "ir_follower_latex null fail-closed",
            "track": 1,
            "limit": "Stackelberg: no follower IR / participation constraint",
            "human_task": "n/a",
            "date": "2026-09-05",
        },
        "mechanism": {
            "follower_decision": "size of training data purchased, s_i^d",
            "follower_utility_latex": (
                r"U(s^d, q) = f(s^d) - \sum_{i \in N^0} q_i s_i^d, "
                r"\quad f(s^d) = \sum_{i \in N^0} f_i(s_i^d), "
                r"\quad f_i(s_i^d) = a_i - b_i \exp(-c_i s_i^d)"
            ),
            "ir_follower_latex": None,
        },
    }


def test_trace_entry_returns_dataclass_with_bail_point():
    entry = _stackelberg_entry_multiclause()
    result = trace_entry(entry)
    assert isinstance(result, TraceResult)
    assert result.paper_id == "test_multiclause"
    assert result.category == "Stackelberg"
    assert result.stored_round == "R7"
    assert result.stored_obstruction == "ir_follower_latex null fail-closed"


def test_trace_entry_finds_real_bail_point_not_stored_reason():
    # The regression this task exists to catch: the stored diagnosis blames
    # a missing IR field, but ir_follower_latex is never read by any
    # Stackelberg code path -- the real bail is in utility resolution.
    entry = _stackelberg_entry_multiclause()
    result = trace_entry(entry)
    assert "ir_follower" not in result.bail_reason.lower()
    assert result.matches_stored is False


def test_trace_entry_full_corpus_produces_one_row_per_manual_entry():
    corpus = json.load(open(Path(__file__).resolve().parents[2] / "corpus.json"))
    rows = corpus["entries"] if isinstance(corpus, dict) else corpus
    manual = [e for e in rows if e.get("verdict_override") == "MANUAL"]
    assert len(manual) > 0
    results = [trace_entry(e) for e in manual]
    assert len(results) == len(manual)
    assert all(r.paper_id for r in results)
    assert all(r.bail_function for r in results)
