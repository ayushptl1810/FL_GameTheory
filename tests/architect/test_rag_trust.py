# tests/architect/test_rag_trust.py
import numpy as np
from architect import rag
from architect.types import ProblemSpec


class _StubIndex:
    def __init__(self, entries, vectors):
        self.entries, self.vectors = entries, vectors
        self.embed = lambda texts: np.array([[1.0, 0.0]])


def test_rank_ignores_ic_proof_present_for_tiebreak():
    entries = [
        {"fl_setup": "x", "title": "A", "ic_proof_present": True, "z3_validated": False},
        {"fl_setup": "x", "title": "B", "ic_proof_present": False, "z3_validated": True},
    ]
    vectors = np.array([[1.0, 0.0], [1.0, 0.0]])
    idx = _StubIndex(entries, vectors)
    order, _ = rag._rank(ProblemSpec(raw_text="x"), idx)
    assert entries[order[0]]["title"] == "B", "z3_validated must win the tie, not ic_proof_present"


def test_rank_tiebreak_unaffected_when_ic_proof_present_flipped():
    entries = [
        {"fl_setup": "x", "title": "A", "ic_proof_present": False, "z3_validated": False},
        {"fl_setup": "x", "title": "B", "ic_proof_present": True, "z3_validated": False},
    ]
    vectors = np.array([[1.0, 0.0], [1.0, 0.0]])
    idx = _StubIndex(entries, vectors)
    order, _ = rag._rank(ProblemSpec(raw_text="x"), idx)
    assert order[0] == 0
